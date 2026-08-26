"""
Background pipeline scanner for the API layer.

Runs the existing Python pipeline in a background thread,
emitting real-time SSE events via the scan_events table.
"""

import json
import logging
import os
import sys
import threading
import uuid
from datetime import datetime
from typing import Optional

# Add parent directory to path so we can import pipeline modules
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from api.database import (
    create_scan,
    get_scan,
    import_reports_from_json,
    insert_audit_event,
    insert_scan_event,
    update_scan_status,
)

logger = logging.getLogger(__name__)


def _emit(scan_id: str, event_type: str, message: str, data: Optional[dict] = None) -> None:
    """Helper: persist an SSE event to the database."""
    insert_scan_event(scan_id, event_type, message, data)
    insert_audit_event(event_type, message, scan_id=scan_id, detail=json.dumps(data) if data else None)
    logger.info(f"[SCAN {scan_id[:8]}] {event_type}: {message}")


def run_live_scan_background(scan_id: str, max_queries: int = 2, max_sources: int = 3) -> None:
    """
    Execute the full compliance pipeline in a background thread.
    Emits SSE events to scan_events table at each stage.

    This function runs the ACTUAL existing pipeline — not a simulation.
    """
    try:
        _emit(scan_id, "STARTED", "Live regulatory scan initiated")

        # ── Stage 1: Import modules ──
        _emit(scan_id, "INITIALIZING", "Loading pipeline modules...")
        from config import DEFAULT_ORG_PROFILE
        from models import ContentType, SecurityScanResult, VerificationStatus
        from pipeline.search import execute_search, generate_queries
        from pipeline.source_validator import classify_source, get_tier_description, is_processable
        from pipeline.retriever import retrieve_source, save_pdf_temporarily
        from pipeline.extractor import extract_content
        from pipeline.security import scan_content, get_sanitized_content
        from pipeline.quarantined_llm import quarantined_extraction
        from pipeline.evidence_verifier import verify_evidence
        from pipeline.privileged_llm import privileged_impact_analysis
        from pipeline.report_generator import generate_report, save_report

        org_profile = DEFAULT_ORG_PROFILE

        # ── Stage 2: Generate queries ──
        _emit(scan_id, "QUERY_GENERATION", "Generating regulatory search queries...")
        all_queries = generate_queries(org_profile)
        queries_to_run = all_queries[:max_queries]
        _emit(scan_id, "QUERIES_READY", f"Generated {len(queries_to_run)} queries",
              {"queries": queries_to_run})

        update_scan_status(scan_id, "RUNNING", queries_run=len(queries_to_run))

        # ── Stage 3: DDGS search ──
        all_results = []
        for qi, query in enumerate(queries_to_run, 1):
            _emit(scan_id, "SEARCHING", f"Query {qi}/{len(queries_to_run)}: {query}")
            try:
                results = execute_search(query)
                all_results.extend(results)
                _emit(scan_id, "SEARCH_RESULTS",
                      f"Found {len(results)} sources for query {qi}",
                      {"count": len(results), "query": query})
            except RuntimeError as e:
                _emit(scan_id, "SEARCH_ERROR", f"Search failed for query: {str(e)}")

        total_found = len(all_results)
        update_scan_status(scan_id, "RUNNING", sources_found=total_found)
        _emit(scan_id, "SEARCH_COMPLETE",
              f"Search complete — {total_found} sources discovered",
              {"total": total_found})

        # ── Stage 4-11: Process each source ──
        from main import process_single_source
        from pipeline.report_generator import generate_report, save_report

        findings = []
        seen_urls = set()
        sources_processed = 0
        sources_quarantined = 0

        for result in all_results:
            if sources_processed >= max_sources * max_queries:
                break
            url = result.get("href", "")
            title = result.get("title", "UNKNOWN")
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)

            _emit(scan_id, "FETCHING", f"Retrieving source: {url[:60]}...",
                  {"url": url, "title": title})

            try:
                finding = process_single_source(url, title, queries_to_run[0] if queries_to_run else "", org_profile)
                findings.append(finding)
                sources_processed += 1

                if finding.security_scan.quarantined:
                    sources_quarantined += 1
                    _emit(scan_id, "SECURITY_QUARANTINE",
                          f"Source quarantined: {url[:60]}",
                          {"url": url, "threats": finding.security_scan.threat_count})
                elif finding.extraction_status == "SUCCESS":
                    ext = finding.regulatory_extraction
                    risk = finding.impact_analysis.risk_level if finding.impact_analysis else "UNKNOWN"
                    _emit(scan_id, "EXTRACTION_SUCCESS",
                          f"Extracted: {ext.title[:50] if ext else 'N/A'} | Risk: {risk}",
                          {"risk": risk, "url": url})
                else:
                    _emit(scan_id, "EXTRACTION_STATUS",
                          f"Status: {finding.extraction_status}",
                          {"status": finding.extraction_status, "url": url})

            except Exception as e:
                _emit(scan_id, "PROCESSING_ERROR",
                      f"Error processing {url[:60]}: {str(e)}")

        update_scan_status(scan_id, "RUNNING",
                           sources_processed=sources_processed,
                           sources_quarantined=sources_quarantined)

        # ── Stage 12: Generate report ──
        _emit(scan_id, "GENERATING_REPORT", "Assembling compliance report...")
        report = generate_report(
            findings=findings,
            queries_executed=queries_to_run,
            org_name=org_profile.name,
            org_type=org_profile.bank_type,
            jurisdiction=org_profile.jurisdiction,
            total_results_found=total_found,
            total_quarantined=sources_quarantined,
        )
        report_path = save_report(report)
        _emit(scan_id, "REPORT_SAVED", f"Report saved: {os.path.basename(report_path)}")

        # ── Stage 13: Import into SQLite ──
        _emit(scan_id, "IMPORTING", "Importing results into database...")
        report_dict = json.loads(report.model_dump_json())
        from api.database import _import_single_report
        new_regs = _import_single_report(report_dict)

        completed_at = datetime.now().isoformat()
        update_scan_status(
            scan_id, "COMPLETE",
            completed_at=completed_at,
            new_regulations=new_regs,
        )
        _emit(scan_id, "COMPLETE",
              f"Scan complete — {new_regs} new regulations imported",
              {
                  "sources_discovered": total_found,
                  "sources_processed": sources_processed,
                  "new_regulations": new_regs,
                  "quarantined": sources_quarantined,
              })

    except Exception as e:
        logger.error(f"Scan {scan_id} failed: {e}", exc_info=True)
        _emit(scan_id, "FAILED", f"Scan failed: {str(e)}")
        update_scan_status(scan_id, "FAILED", error_message=str(e))


def start_scan(max_queries: int = 2, max_sources: int = 3) -> str:
    """
    Create a scan record and launch the pipeline in a background thread.
    Returns the scan_id immediately.
    """
    scan_id = create_scan()
    thread = threading.Thread(
        target=run_live_scan_background,
        args=(scan_id, max_queries, max_sources),
        daemon=True,
        name=f"scan-{scan_id[:8]}",
    )
    thread.start()
    logger.info(f"Scan {scan_id} started in background thread")
    return scan_id
