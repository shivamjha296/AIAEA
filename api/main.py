"""
FastAPI application — Regulatory Compliance Radar REST API.

Bridges the existing Python pipeline to the Next.js frontend.
All data originates from SQLite (populated by the live pipeline).

Endpoints:
  GET  /api/health
  GET  /api/dashboard/metrics
  GET  /api/regulations
  GET  /api/regulations/{id}
  GET  /api/risk
  GET  /api/security/events
  GET  /api/security/metrics
  GET  /api/reviews/pending
  GET  /api/reviews/history
  POST /api/reviews/{id}/approve
  POST /api/reviews/{id}/reject
  POST /api/scans
  GET  /api/scans/{scan_id}/events  (SSE)
  GET  /api/scans
  GET  /api/audit
  GET  /api/regulations/{id}/export
"""

import asyncio
import json
import logging
import os
import sys
import time
from typing import Any, AsyncGenerator, Dict, List, Optional

import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

# Add parent directory so pipeline imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from api.database import (
    get_activity_chart,
    get_audit_events,
    get_dashboard_metrics,
    get_pending_reviews,
    get_regulation_detail,
    get_regulations,
    get_regulators_list,
    get_review_history,
    get_risk_distribution,
    get_regulator_distribution,
    get_scan,
    get_scan_events_since,
    get_scans_list,
    get_security_events,
    get_security_metrics,
    import_reports_from_json,
    init_db,
    update_review,
)
from api.scanner import start_scan

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================
# APP SETUP
# ============================================================

app = FastAPI(
    title="Regulatory Compliance Radar API",
    description="REST API bridging the Python compliance pipeline to the Next.js frontend",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event() -> None:
    """Initialize DB and import existing reports on startup."""
    init_db()
    imported = import_reports_from_json()
    logger.info(f"Startup complete. Imported {imported} regulations from existing reports.")


# ============================================================
# REQUEST/RESPONSE MODELS
# ============================================================

class ReviewDecisionRequest(BaseModel):
    reviewer: str
    reason: str


class ScanRequest(BaseModel):
    max_queries: int = 2
    max_sources: int = 3


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/api/health")
async def health_check() -> Dict:
    """Check availability of all system components."""
    status: Dict[str, Any] = {
        "api": "operational",
        "database": "unknown",
        "llm": "unknown",
        "search": "unknown",
    }

    # Database
    try:
        from api.database import get_dashboard_metrics
        get_dashboard_metrics()
        status["database"] = "operational"
    except Exception as e:
        status["database"] = f"error: {e}"

    # Ollama LLM
    try:
        async with httpx.AsyncClient(timeout=3) as client:
            r = await client.get("http://localhost:11434/api/tags")
            status["llm"] = "operational" if r.status_code == 200 else "unavailable"
    except Exception:
        status["llm"] = "unavailable"

    # Search (quick DDGS ping)
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get("https://duckduckgo.com", headers={"User-Agent": "Mozilla/5.0"})
            status["search"] = "operational" if r.status_code == 200 else "degraded"
    except Exception:
        status["search"] = "unavailable"

    overall = "operational" if all(
        v == "operational" for k, v in status.items() if k != "llm"
    ) else "degraded"
    status["overall"] = overall
    return status


# ============================================================
# DASHBOARD
# ============================================================

@app.get("/api/dashboard/metrics")
async def dashboard_metrics() -> Dict:
    return get_dashboard_metrics()


@app.get("/api/dashboard/activity")
async def dashboard_activity(days: int = Query(default=30, ge=7, le=90)) -> List[Dict]:
    return get_activity_chart(days)


@app.get("/api/dashboard/regulators")
async def regulator_distribution() -> List[Dict]:
    return get_regulator_distribution()


# ============================================================
# REGULATIONS
# ============================================================

@app.get("/api/regulations")
async def list_regulations(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    regulator: Optional[str] = None,
    risk: Optional[str] = None,
    verification: Optional[str] = None,
    search: Optional[str] = None,
    days: Optional[int] = None,
) -> Dict:
    return get_regulations(
        page=page,
        page_size=page_size,
        regulator=regulator,
        risk=risk,
        verification=verification,
        search=search,
        days=days,
    )


@app.get("/api/regulations/regulators")
async def list_regulators() -> List[str]:
    return get_regulators_list()


@app.get("/api/regulations/{reg_id}")
async def get_regulation(reg_id: str) -> Dict:
    reg = get_regulation_detail(reg_id)
    if not reg:
        raise HTTPException(status_code=404, detail="Regulation not found")
    return reg


@app.get("/api/regulations/{reg_id}/export")
async def export_regulation(reg_id: str) -> JSONResponse:
    """Export full regulation detail as downloadable JSON."""
    reg = get_regulation_detail(reg_id)
    if not reg:
        raise HTTPException(status_code=404, detail="Regulation not found")
    filename = f"regulation_{reg_id[:8]}.json"
    return JSONResponse(
        content=reg,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ============================================================
# RISK
# ============================================================

@app.get("/api/risk")
async def risk_register(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    risk: Optional[str] = None,
    regulator: Optional[str] = None,
    verification: Optional[str] = None,
) -> Dict:
    data = get_regulations(
        page=page,
        page_size=page_size,
        risk=risk,
        regulator=regulator,
        verification=verification,
    )
    data["distribution"] = get_risk_distribution()
    return data


@app.get("/api/risk/distribution")
async def risk_distribution() -> Dict:
    return get_risk_distribution()


# ============================================================
# SECURITY
# ============================================================

@app.get("/api/security/events")
async def security_events(limit: int = Query(default=50, ge=1, le=200)) -> List[Dict]:
    return get_security_events(limit=limit)


@app.get("/api/security/metrics")
async def security_metrics() -> Dict:
    return get_security_metrics()


# ============================================================
# HUMAN REVIEW
# ============================================================

@app.get("/api/reviews/pending")
async def pending_reviews() -> List[Dict]:
    return get_pending_reviews()


@app.get("/api/reviews/history")
async def review_history() -> List[Dict]:
    return get_review_history()


@app.post("/api/reviews/{review_id}/approve")
async def approve_review(review_id: int, body: ReviewDecisionRequest) -> Dict:
    success = update_review(review_id, "APPROVED", body.reviewer, body.reason)
    if not success:
        raise HTTPException(status_code=404, detail="Review not found or already decided")
    return {"status": "APPROVED", "review_id": review_id, "reviewer": body.reviewer}


@app.post("/api/reviews/{review_id}/reject")
async def reject_review(review_id: int, body: ReviewDecisionRequest) -> Dict:
    success = update_review(review_id, "REJECTED", body.reviewer, body.reason)
    if not success:
        raise HTTPException(status_code=404, detail="Review not found or already decided")
    return {"status": "REJECTED", "review_id": review_id, "reviewer": body.reviewer}


# ============================================================
# SCANS + SSE
# ============================================================

@app.post("/api/scans")
async def create_scan(body: ScanRequest) -> Dict:
    """Start a live pipeline scan. Returns scan_id immediately."""
    scan_id = start_scan(
        max_queries=body.max_queries,
        max_sources=body.max_sources,
    )
    return {"scan_id": scan_id, "status": "RUNNING"}


@app.get("/api/scans")
async def list_scans() -> List[Dict]:
    return get_scans_list()


@app.get("/api/scans/{scan_id}")
async def get_scan_status(scan_id: str) -> Dict:
    scan = get_scan(scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return scan


@app.get("/api/scans/{scan_id}/events")
async def scan_events_sse(scan_id: str) -> StreamingResponse:
    """
    Server-Sent Events stream for real-time scan progress.
    Polls scan_events table and streams new events as SSE.
    """
    async def event_generator() -> AsyncGenerator[str, None]:
        last_id = 0
        consecutive_empty = 0
        max_wait = 300  # 5 minutes max

        yield f"data: {json.dumps({'event': 'CONNECTED', 'message': 'Stream connected'})}\n\n"

        start_time = time.time()
        while time.time() - start_time < max_wait:
            events = get_scan_events_since(scan_id, last_id)

            for event in events:
                last_id = event["id"]
                payload = json.dumps({
                    "event": event["event_type"],
                    "message": event["message"],
                    "data": json.loads(event["data"]) if event.get("data") else None,
                    "timestamp": event["created_at"],
                })
                yield f"data: {payload}\n\n"
                consecutive_empty = 0

                if event["event_type"] in ("COMPLETE", "FAILED"):
                    return

            if not events:
                consecutive_empty += 1
                # Check if scan is done
                scan = get_scan(scan_id)
                if scan and scan["status"] in ("COMPLETE", "FAILED"):
                    yield f"data: {json.dumps({'event': scan['status'], 'message': 'Scan finished'})}\n\n"
                    return

            await asyncio.sleep(1)

        yield f"data: {json.dumps({'event': 'TIMEOUT', 'message': 'Stream timed out'})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ============================================================
# AUDIT TRAIL
# ============================================================

@app.get("/api/audit")
async def audit_trail(
    scan_id: Optional[str] = None,
    limit: int = Query(default=100, ge=1, le=500),
) -> List[Dict]:
    return get_audit_events(scan_id=scan_id, limit=limit)


# ============================================================
# ROOT
# ============================================================

@app.get("/")
async def root() -> Dict:
    return {
        "name": "Regulatory Compliance Radar API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "operational",
    }
