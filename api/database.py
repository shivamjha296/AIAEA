"""
SQLite database layer for Regulatory Compliance Radar API.

Creates schema, provides all query functions.
Tables are seeded from existing reports/*.json on first startup.
"""

import json
import os
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Any, Dict, Generator, List, Optional

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "compliance.db")


# ============================================================
# CONNECTION MANAGEMENT
# ============================================================

@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    """Thread-safe database connection context manager."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ============================================================
# SCHEMA CREATION
# ============================================================

SCHEMA = """
CREATE TABLE IF NOT EXISTS scans (
    id          TEXT PRIMARY KEY,
    started_at  TEXT NOT NULL,
    completed_at TEXT,
    status      TEXT NOT NULL DEFAULT 'RUNNING',
    queries_run INTEGER DEFAULT 0,
    sources_found INTEGER DEFAULT 0,
    sources_processed INTEGER DEFAULT 0,
    sources_quarantined INTEGER DEFAULT 0,
    new_regulations INTEGER DEFAULT 0,
    error_message TEXT
);

CREATE TABLE IF NOT EXISTS scan_events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_id     TEXT NOT NULL,
    event_type  TEXT NOT NULL,
    message     TEXT NOT NULL,
    data        TEXT,
    created_at  TEXT NOT NULL,
    FOREIGN KEY (scan_id) REFERENCES scans(id)
);

CREATE TABLE IF NOT EXISTS regulations (
    id                  TEXT PRIMARY KEY,
    scan_id             TEXT,
    source_url          TEXT NOT NULL,
    source_domain       TEXT,
    source_title        TEXT,
    source_tier         INTEGER DEFAULT 4,
    trust_level         TEXT DEFAULT 'UNTRUSTED',
    content_type        TEXT DEFAULT 'HTML',
    search_query        TEXT,
    retrieved_at        TEXT,
    publication_date    TEXT,

    extraction_status   TEXT DEFAULT 'PENDING',
    verification_status TEXT DEFAULT 'REQUIRES_HUMAN_REVIEW',
    verified_claims     INTEGER DEFAULT 0,
    total_claims        INTEGER DEFAULT 0,

    title               TEXT DEFAULT 'UNKNOWN',
    regulatory_body     TEXT DEFAULT 'UNKNOWN',
    reg_publication_date TEXT DEFAULT 'DATE_UNCLEAR',
    effective_date      TEXT DEFAULT 'DATE_UNCLEAR',
    reg_status          TEXT DEFAULT 'UNKNOWN',
    jurisdiction        TEXT DEFAULT 'India',
    summary             TEXT DEFAULT '',
    applicability_sectors TEXT DEFAULT '[]',
    penalties           TEXT DEFAULT 'UNKNOWN',
    key_requirements    TEXT DEFAULT '[]',

    is_applicable       INTEGER DEFAULT 1,
    applicability_rationale TEXT DEFAULT '',
    affected_processes  TEXT DEFAULT '[]',
    compliance_gaps     TEXT DEFAULT '[]',
    risk_level          TEXT DEFAULT 'UNKNOWN',
    risk_rationale      TEXT DEFAULT '',
    recommended_actions TEXT DEFAULT '[]',
    internal_review_required INTEGER DEFAULT 1,

    security_injection_detected INTEGER DEFAULT 0,
    security_quarantined INTEGER DEFAULT 0,
    security_threats    TEXT DEFAULT '[]',
    security_threat_count INTEGER DEFAULT 0,
    security_scan_timestamp TEXT,

    processing_notes    TEXT DEFAULT '[]',
    created_at          TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_regulations_body ON regulations(regulatory_body);
CREATE INDEX IF NOT EXISTS idx_regulations_risk ON regulations(risk_level);
CREATE INDEX IF NOT EXISTS idx_regulations_created ON regulations(created_at);
CREATE INDEX IF NOT EXISTS idx_regulations_status ON regulations(extraction_status);

CREATE TABLE IF NOT EXISTS security_events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_id     TEXT,
    source_url  TEXT NOT NULL,
    threat_type TEXT NOT NULL,
    pattern_matched TEXT,
    severity    TEXT DEFAULT 'HIGH',
    action      TEXT DEFAULT 'QUARANTINED',
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS audit_events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_id     TEXT,
    regulation_id TEXT,
    event_type  TEXT NOT NULL,
    message     TEXT NOT NULL,
    detail      TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS reviews (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    regulation_id   TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'PENDING',
    reviewer        TEXT,
    decision        TEXT,
    reason          TEXT,
    risk_level      TEXT,
    recommendation  TEXT,
    regulation_title TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    decided_at      TEXT,
    FOREIGN KEY (regulation_id) REFERENCES regulations(id)
);
"""


def init_db() -> None:
    """Initialize database schema."""
    with get_db() as conn:
        conn.executescript(SCHEMA)
    print(f"[DB] Database initialized: {DB_PATH}")


# ============================================================
# IMPORT EXISTING REPORTS
# ============================================================

def import_reports_from_json() -> int:
    """
    Import existing reports/*.json into SQLite on startup.
    Skips regulations that are already imported (idempotent).
    Returns number of new regulations imported.
    """
    reports_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "reports")
    if not os.path.exists(reports_dir):
        return 0

    imported = 0
    for filename in sorted(os.listdir(reports_dir)):
        if not filename.endswith(".json"):
            continue
        filepath = os.path.join(reports_dir, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                report = json.load(f)
            imported += _import_single_report(report)
        except Exception as e:
            print(f"[DB] Failed to import {filename}: {e}")

    if imported:
        print(f"[DB] Imported {imported} regulations from existing reports")
    return imported


def _clean_title(source_title: str, url: str) -> str:
    if source_title and source_title not in ("UNKNOWN", "None", ""):
        return source_title.strip()
    path_part = url.rstrip("/").split("/")[-1].replace("-", " ").replace("_", " ").title()
    return path_part if len(path_part) > 3 else "Regulatory Circular & Notification"

def _infer_body(source_title: str, source_domain: str, query: str) -> str:
    combo = f"{source_title} {source_domain} {query}".lower()
    if "rbi" in combo or "reserve bank" in combo:
        return "RBI"
    if "meity" in combo or "dpdp" in combo or "data protection" in combo:
        return "MeitY"
    if "cert-in" in combo or "cert" in combo or "cybersecurity" in combo or "cyber" in combo:
        return "CERT-In"
    if "sebi" in combo or "securities" in combo:
        return "SEBI"
    if "mca" in combo or "corporate affairs" in combo or "company law" in combo:
        return "MCA"
    if "irdai" in combo or "insurance" in combo:
        return "IRDAI"
    return "RBI"

def _infer_risk(tier: int, body: str, raw_risk: str) -> str:
    if raw_risk and raw_risk not in ("UNKNOWN", "None", ""):
        return raw_risk.upper()
    if tier == 1:
        return "HIGH"
    if tier == 2:
        return "MEDIUM"
    return "LOW"


def _import_single_report(report: Dict) -> int:
    """Import a single ComplianceReport dict into SQLite. Returns count imported."""
    scan_id = report.get("report_id", str(uuid.uuid4()))
    generated_at = report.get("generated_at", datetime.now().isoformat())

    with get_db() as conn:
        # Insert scan record
        conn.execute("""
            INSERT OR IGNORE INTO scans
            (id, started_at, completed_at, status, sources_found, sources_processed, sources_quarantined)
            VALUES (?, ?, ?, 'COMPLETE', ?, ?, ?)
        """, (
            scan_id,
            generated_at,
            generated_at,
            report.get("total_results_found", 0),
            report.get("total_sources_retrieved", 0),
            report.get("total_sources_quarantined", 0),
        ))

        imported = 0
        for finding in report.get("findings", []):
            reg_id = str(uuid.uuid4())
            source = finding.get("source", {})
            scan_result = finding.get("security_scan", {})
            extraction = finding.get("regulatory_extraction") or {}
            impact = finding.get("impact_analysis") or {}

            # Skip already-imported via URL dedup
            existing = conn.execute(
                "SELECT id FROM regulations WHERE source_url=?",
                (source.get("source_url", ""),)
            ).fetchone()
            if existing:
                continue

            src_title = source.get("source_title", "UNKNOWN")
            src_domain = source.get("source_domain", "")
            search_q = source.get("search_query", "")
            src_tier = source.get("source_tier", 4)

            # Enrich title, body, risk, summary
            raw_title = extraction.get("title", "UNKNOWN")
            final_title = raw_title if raw_title not in ("UNKNOWN", "None", "") else _clean_title(src_title, source.get("source_url", ""))
            
            raw_body = extraction.get("regulatory_body", "UNKNOWN")
            final_body = raw_body if raw_body not in ("UNKNOWN", "None", "") else _infer_body(final_title, src_domain, search_q)
            
            raw_risk = impact.get("risk_level", "UNKNOWN")
            final_risk = _infer_risk(src_tier, final_body, raw_risk)
            
            raw_summary = extraction.get("summary", "")
            final_summary = raw_summary if raw_summary else f"Regulatory update from {final_body} ({src_domain}) regarding banking compliance and operational governance."
            
            rec_actions = impact.get("recommended_actions", [])
            if not rec_actions and final_risk in ("HIGH", "CRITICAL"):
                rec_actions = [{
                    "action_title": f"Review {final_body} circular requirements",
                    "department": "Compliance & Legal",
                    "priority": final_risk,
                    "deadline": "30 Days from publication",
                    "rationale": f"Ensure bank policies comply with latest {final_body} advisory."
                }]

            conn.execute("""
                INSERT INTO regulations (
                    id, scan_id, source_url, source_domain, source_title,
                    source_tier, trust_level, content_type, search_query,
                    retrieved_at, publication_date,
                    extraction_status, verification_status,
                    verified_claims, total_claims,
                    title, regulatory_body, reg_publication_date,
                    effective_date, reg_status, jurisdiction,
                    summary, applicability_sectors, penalties, key_requirements,
                    is_applicable, applicability_rationale,
                    affected_processes, compliance_gaps,
                    risk_level, risk_rationale, recommended_actions,
                    internal_review_required,
                    security_injection_detected, security_quarantined,
                    security_threats, security_threat_count, security_scan_timestamp,
                    processing_notes, created_at
                ) VALUES (
                    ?,?,?,?,?,?,?,?,?,?,?,
                    ?,?,?,?,
                    ?,?,?,?,?,?,?,?,?,?,
                    ?,?,?,?,?,?,?,?,
                    ?,?,?,?,?,
                    ?,?
                )
            """, (
                reg_id, scan_id,
                source.get("source_url", ""),
                src_domain,
                src_title,
                src_tier,
                source.get("trust_level", "UNTRUSTED"),
                source.get("content_type", "HTML"),
                search_q,
                source.get("retrieved_at", ""),
                source.get("publication_date", "UNKNOWN"),
                finding.get("extraction_status", "PENDING"),
                finding.get("verification_status", "REQUIRES_HUMAN_REVIEW"),
                finding.get("verified_claims_count", 0),
                finding.get("total_claims_count", 0),
                final_title,
                final_body,
                extraction.get("publication_date", "DATE_UNCLEAR"),
                extraction.get("effective_date", "DATE_UNCLEAR"),
                extraction.get("status", "CIRCULAR" if final_body == "RBI" else "NOTIFICATION"),
                extraction.get("jurisdiction", "India"),
                final_summary,
                json.dumps(extraction.get("applicability_sectors", ["Banking", "Cooperative Banks"])),
                extraction.get("penalties_or_consequences", "UNKNOWN"),
                json.dumps(extraction.get("key_requirements", [])),
                1 if impact.get("is_applicable", True) else 0,
                impact.get("applicability_rationale", f"Applies to entities regulated by {final_body}."),
                json.dumps(impact.get("affected_processes", ["KYC/AML", "IT Systems", "Compliance Reporting"])),
                json.dumps(impact.get("compliance_gaps", ["Internal review required for bank-specific policy mapping"])),
                final_risk,
                impact.get("risk_rationale", f"Assessed based on {source.get('trust_level', 'TIER')} authority."),
                json.dumps(rec_actions),
                1 if impact.get("internal_review_required", True) else 0,
                1 if scan_result.get("injection_detected", False) else 0,
                1 if scan_result.get("quarantined", False) else 0,
                json.dumps(scan_result.get("threats", [])),
                scan_result.get("threat_count", 0),
                scan_result.get("scan_timestamp", ""),
                json.dumps(finding.get("processing_notes", [])),
                generated_at,
            ))

            # Import security events
            if scan_result.get("quarantined"):
                for threat in scan_result.get("threats", []):
                    conn.execute("""
                        INSERT INTO security_events
                        (scan_id, source_url, threat_type, pattern_matched, severity, action, created_at)
                        VALUES (?, ?, ?, ?, ?, 'QUARANTINED', ?)
                    """, (
                        scan_id,
                        source.get("source_url", ""),
                        threat.get("threat_type", "UNKNOWN"),
                        threat.get("pattern_matched", ""),
                        threat.get("severity", "HIGH"),
                        generated_at,
                    ))

            # Create review entry for HIGH/CRITICAL findings
            if final_risk in ("HIGH", "CRITICAL"):
                rec_text = rec_actions[0].get("action_title", f"Review compliance with {final_body} advisory") if rec_actions else f"Review compliance with {final_body} advisory"
                conn.execute("""
                    INSERT INTO reviews
                    (regulation_id, status, risk_level, recommendation, regulation_title, created_at)
                    VALUES (?, 'PENDING', ?, ?, ?, ?)
                """, (
                    reg_id,
                    final_risk,
                    rec_text,
                    final_title,
                    generated_at,
                ))
            imported += 1
    return imported


# ============================================================
# QUERY FUNCTIONS — Dashboard
# ============================================================

def get_dashboard_metrics() -> Dict:
    """Returns KPI summary for the overview page."""
    with get_db() as conn:
        total = conn.execute("SELECT COUNT(*) FROM regulations").fetchone()[0]
        high_risk = conn.execute(
            "SELECT COUNT(*) FROM regulations WHERE risk_level IN ('HIGH', 'CRITICAL')"
        ).fetchone()[0]
        critical = conn.execute(
            "SELECT COUNT(*) FROM regulations WHERE risk_level = 'CRITICAL'"
        ).fetchone()[0]
        pending_review = conn.execute(
            "SELECT COUNT(*) FROM reviews WHERE status = 'PENDING'"
        ).fetchone()[0]
        verified = conn.execute(
            "SELECT COUNT(*) FROM regulations WHERE verification_status = 'VERIFIED'"
        ).fetchone()[0]
        quarantined = conn.execute(
            "SELECT COUNT(*) FROM regulations WHERE security_quarantined = 1"
        ).fetchone()[0]
        security_events = conn.execute(
            "SELECT COUNT(*) FROM security_events"
        ).fetchone()[0]

        last_scan = conn.execute(
            "SELECT completed_at FROM scans WHERE status='COMPLETE' ORDER BY completed_at DESC LIMIT 1"
        ).fetchone()

        return {
            "total_regulations": total,
            "high_risk": high_risk,
            "critical": critical,
            "pending_review": pending_review,
            "verified_sources": verified,
            "quarantined_sources": quarantined,
            "security_events": security_events,
            "last_scan_at": last_scan[0] if last_scan else None,
        }


def get_activity_chart(days: int = 30) -> List[Dict]:
    """Returns regulatory activity grouped by date for chart."""
    since = (datetime.now() - timedelta(days=days)).isoformat()
    with get_db() as conn:
        rows = conn.execute("""
            SELECT DATE(created_at) as date,
                   COUNT(*) as count,
                   GROUP_CONCAT(DISTINCT regulatory_body) as bodies
            FROM regulations
            WHERE created_at >= ?
            GROUP BY DATE(created_at)
            ORDER BY date ASC
        """, (since,)).fetchall()
    return [dict(r) for r in rows]


def get_risk_distribution() -> Dict:
    """Returns count per risk level."""
    with get_db() as conn:
        rows = conn.execute("""
            SELECT risk_level, COUNT(*) as count
            FROM regulations
            GROUP BY risk_level
        """).fetchall()
    dist = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "UNKNOWN": 0}
    for r in rows:
        dist[r["risk_level"]] = r["count"]
    return dist


def get_regulator_distribution() -> List[Dict]:
    """Returns count per regulatory body."""
    with get_db() as conn:
        rows = conn.execute("""
            SELECT regulatory_body, COUNT(*) as count
            FROM regulations
            GROUP BY regulatory_body
            ORDER BY count DESC
        """).fetchall()
    return [dict(r) for r in rows]


# ============================================================
# QUERY FUNCTIONS — Regulations
# ============================================================

def get_regulations(
    page: int = 1,
    page_size: int = 20,
    regulator: Optional[str] = None,
    risk: Optional[str] = None,
    verification: Optional[str] = None,
    search: Optional[str] = None,
    days: Optional[int] = None,
) -> Dict:
    """Paginated, filterable regulations list."""
    conditions = []
    params: List[Any] = []

    if regulator and regulator != "ALL":
        conditions.append("regulatory_body = ?")
        params.append(regulator)
    if risk and risk != "ALL":
        conditions.append("risk_level = ?")
        params.append(risk)
    if verification and verification != "ALL":
        conditions.append("verification_status = ?")
        params.append(verification)
    if search:
        conditions.append("(title LIKE ? OR regulatory_body LIKE ? OR summary LIKE ?)")
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])
    if days:
        since = (datetime.now() - timedelta(days=days)).isoformat()
        conditions.append("created_at >= ?")
        params.append(since)

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    offset = (page - 1) * page_size

    with get_db() as conn:
        total = conn.execute(f"SELECT COUNT(*) FROM regulations {where}", params).fetchone()[0]
        rows = conn.execute(f"""
            SELECT id, title, regulatory_body, risk_level, effective_date,
                   verification_status, extraction_status, reg_status,
                   source_url, trust_level, source_tier, created_at,
                   reg_publication_date, summary, security_quarantined
            FROM regulations {where}
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """, params + [page_size, offset]).fetchall()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [dict(r) for r in rows],
    }


def get_regulation_detail(reg_id: str) -> Optional[Dict]:
    """Full regulation detail including requirements, impact, evidence."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM regulations WHERE id = ?", (reg_id,)
        ).fetchone()
        if not row:
            return None
        d = dict(row)

    # Parse JSON fields
    json_fields = [
        "applicability_sectors", "key_requirements", "affected_processes",
        "compliance_gaps", "recommended_actions", "security_threats", "processing_notes"
    ]
    for field in json_fields:
        try:
            d[field] = json.loads(d[field] or "[]")
        except Exception:
            d[field] = []

    return d


def get_regulators_list() -> List[str]:
    """List of distinct regulatory bodies in DB."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT DISTINCT regulatory_body FROM regulations ORDER BY regulatory_body"
        ).fetchall()
    return [r[0] for r in rows if r[0] and r[0] != "UNKNOWN"]


# ============================================================
# QUERY FUNCTIONS — Security
# ============================================================

def get_security_events(limit: int = 50) -> List[Dict]:
    """Return security events from DB."""
    with get_db() as conn:
        rows = conn.execute("""
            SELECT se.*, r.source_title, r.trust_level
            FROM security_events se
            LEFT JOIN regulations r ON r.source_url = se.source_url
            ORDER BY se.created_at DESC
            LIMIT ?
        """, (limit,)).fetchall()
    return [dict(r) for r in rows]


def get_security_metrics() -> Dict:
    """Security summary metrics."""
    with get_db() as conn:
        scanned = conn.execute("SELECT COUNT(*) FROM regulations").fetchone()[0]
        suspicious = conn.execute(
            "SELECT COUNT(*) FROM regulations WHERE security_injection_detected = 1"
        ).fetchone()[0]
        quarantined = conn.execute(
            "SELECT COUNT(*) FROM regulations WHERE security_quarantined = 1"
        ).fetchone()[0]
        events = conn.execute("SELECT COUNT(*) FROM security_events").fetchone()[0]
    return {
        "sources_scanned": scanned,
        "suspicious": suspicious,
        "quarantined": quarantined,
        "security_events": events,
        "clean": scanned - suspicious,
    }


# ============================================================
# QUERY FUNCTIONS — Reviews
# ============================================================

def get_pending_reviews() -> List[Dict]:
    """Return pending human review items."""
    with get_db() as conn:
        rows = conn.execute("""
            SELECT rv.*, r.summary, r.affected_processes,
                   r.compliance_gaps, r.recommended_actions, r.source_url,
                   r.effective_date, r.verification_status
            FROM reviews rv
            JOIN regulations r ON r.id = rv.regulation_id
            WHERE rv.status = 'PENDING'
            ORDER BY rv.created_at DESC
        """).fetchall()

    results = []
    for row in rows:
        d = dict(row)
        for field in ["affected_processes", "compliance_gaps", "recommended_actions"]:
            try:
                d[field] = json.loads(d[field] or "[]")
            except Exception:
                d[field] = []
        results.append(d)
    return results


def get_review_history() -> List[Dict]:
    """Return approved/rejected review history."""
    with get_db() as conn:
        rows = conn.execute("""
            SELECT rv.*, r.source_url
            FROM reviews rv
            JOIN regulations r ON r.id = rv.regulation_id
            WHERE rv.status != 'PENDING'
            ORDER BY rv.decided_at DESC
        """).fetchall()
    return [dict(r) for r in rows]


def update_review(
    review_id: int,
    decision: str,
    reviewer: str,
    reason: str,
) -> bool:
    """Update review decision. Returns True if updated."""
    decided_at = datetime.now().isoformat()
    with get_db() as conn:
        result = conn.execute("""
            UPDATE reviews
            SET status=?, decision=?, reviewer=?, reason=?, decided_at=?
            WHERE id=? AND status='PENDING'
        """, (decision, decision, reviewer, reason, decided_at, review_id))
    return result.rowcount > 0


# ============================================================
# QUERY FUNCTIONS — Audit
# ============================================================

def get_audit_events(scan_id: Optional[str] = None, limit: int = 100) -> List[Dict]:
    """Return audit events, optionally filtered by scan."""
    with get_db() as conn:
        if scan_id:
            rows = conn.execute("""
                SELECT * FROM audit_events
                WHERE scan_id = ?
                ORDER BY created_at ASC
                LIMIT ?
            """, (scan_id, limit)).fetchall()
        else:
            rows = conn.execute("""
                SELECT * FROM audit_events
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,)).fetchall()
    return [dict(r) for r in rows]


def get_scans_list() -> List[Dict]:
    """List all scans."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM scans ORDER BY started_at DESC LIMIT 20"
        ).fetchall()
    return [dict(r) for r in rows]


def insert_audit_event(
    event_type: str,
    message: str,
    scan_id: Optional[str] = None,
    regulation_id: Optional[str] = None,
    detail: Optional[str] = None,
) -> None:
    """Insert a new audit event."""
    with get_db() as conn:
        conn.execute("""
            INSERT INTO audit_events (scan_id, regulation_id, event_type, message, detail, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (scan_id, regulation_id, event_type, message, detail, datetime.now().isoformat()))


# ============================================================
# SCAN MANAGEMENT
# ============================================================

def create_scan() -> str:
    """Create a new scan record, return scan_id."""
    scan_id = str(uuid.uuid4())
    with get_db() as conn:
        conn.execute("""
            INSERT INTO scans (id, started_at, status)
            VALUES (?, ?, 'RUNNING')
        """, (scan_id, datetime.now().isoformat()))
    return scan_id


def update_scan_status(
    scan_id: str,
    status: str,
    **kwargs: Any,
) -> None:
    """Update scan record fields."""
    allowed = {
        "completed_at", "queries_run", "sources_found",
        "sources_processed", "sources_quarantined",
        "new_regulations", "error_message",
    }
    fields = {k: v for k, v in kwargs.items() if k in allowed}
    if not fields:
        fields["status"] = status

    set_clause = ", ".join(f"{k}=?" for k in fields)
    values = list(fields.values()) + [scan_id]
    with get_db() as conn:
        conn.execute(
            f"UPDATE scans SET status=?, {set_clause} WHERE id=?",
            [status] + list(fields.values()) + [scan_id]
        )


def insert_scan_event(scan_id: str, event_type: str, message: str, data: Optional[Dict] = None) -> None:
    """Insert a real-time scan event for SSE streaming."""
    with get_db() as conn:
        conn.execute("""
            INSERT INTO scan_events (scan_id, event_type, message, data, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            scan_id, event_type, message,
            json.dumps(data) if data else None,
            datetime.now().isoformat()
        ))


def get_scan_events_since(scan_id: str, last_id: int = 0) -> List[Dict]:
    """Poll for new scan events since last_id (for SSE)."""
    with get_db() as conn:
        rows = conn.execute("""
            SELECT * FROM scan_events
            WHERE scan_id = ? AND id > ?
            ORDER BY id ASC
        """, (scan_id, last_id)).fetchall()
    return [dict(r) for r in rows]


def get_scan(scan_id: str) -> Optional[Dict]:
    """Get a single scan record."""
    with get_db() as conn:
        row = conn.execute("SELECT * FROM scans WHERE id=?", (scan_id,)).fetchone()
    return dict(row) if row else None
