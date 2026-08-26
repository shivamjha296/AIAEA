"""
Autonomous Regulatory & Compliance Radar — Main Pipeline Orchestrator.

This is the entry point that runs the full LIVE pipeline:

  1. Load organization profile
  2. Generate search queries
  3. Execute DDGS live search
  4. For each result:
     a. Validate source tier
     b. Retrieve content (HTTP GET)
     c. Extract text (HTML or PDF)
     d. Security scan (prompt injection detection)
     e. Quarantined LLM extraction (if clean)
     f. Pydantic validation
     g. Evidence verification
     h. Privileged LLM impact analysis
  5. Generate final JSON report
  6. Print summary

THERE IS NO DEMO MODE.
If the internet is unavailable → explicit error, no fallback.
If Ollama is unavailable → explicit error, no fallback.

Usage:
    python main.py
    python main.py --queries 3        # Limit number of queries
    python main.py --max-sources 5    # Limit sources per query
"""

import argparse
import logging
import sys
from datetime import datetime
from typing import List

# Ensure UTF-8 output encoding across Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from config import DEFAULT_ORG_PROFILE
from models import (
    ComplianceReportEntry,
    ContentType,
    SecurityScanResult,
    SourceMetadata,
    VerificationStatus,
)
from pipeline.search import execute_search, generate_queries
from pipeline.source_validator import classify_source, get_tier_description, is_processable
from pipeline.retriever import retrieve_source, save_pdf_temporarily
from pipeline.extractor import extract_content
from pipeline.security import scan_content, get_sanitized_content
from pipeline.quarantined_llm import quarantined_extraction
from pipeline.evidence_verifier import verify_evidence
from pipeline.privileged_llm import privileged_impact_analysis
from pipeline.report_generator import (
    generate_report,
    print_report_summary,
    save_report,
)


# ============================================================
# LOGGING CONFIGURATION
# ============================================================

def setup_logging(verbose: bool = False) -> None:
    """Configure logging for the pipeline."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(name)-25s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("pipeline.log", encoding="utf-8"),
        ],
    )


# ============================================================
# PIPELINE ORCHESTRATOR
# ============================================================

def process_single_source(
    url: str,
    title: str,
    search_query: str,
    org_profile,
) -> ComplianceReportEntry:
    """
    Process a single search result through the full pipeline.

    Returns a ComplianceReportEntry regardless of outcome — failures
    are recorded with appropriate status codes, never silently ignored.
    """
    logger = logging.getLogger("pipeline.orchestrator")
    processing_notes: List[str] = []

    # ── Step 1: Source Validation ──
    tier, trust_level, action = classify_source(url)
    tier_desc = get_tier_description(tier)
    logger.info(f"Source tier: {tier} ({tier_desc}) — {url}")

    source_meta = SourceMetadata(
        source_url=url,
        source_domain=url.split("/")[2] if len(url.split("/")) > 2 else "unknown",
        source_title=title or "UNKNOWN",
        source_tier=tier,
        trust_level=trust_level,
        search_query=search_query,
        retrieved_at=datetime.now().isoformat(),
    )

    # Check if source should be auto-processed
    if not is_processable(tier):
        processing_notes.append(
            f"Source is Tier {tier} ({tier_desc}). "
            f"Flagged for manual verification only."
        )
        return ComplianceReportEntry(
            source=source_meta,
            security_scan=SecurityScanResult(),
            extraction_status="SKIPPED_LOW_TRUST",
            verification_status=VerificationStatus.REQUIRES_HUMAN_REVIEW,
            processing_notes=processing_notes,
        )

    # ── Step 2: Content Retrieval (HTTP GET) ──
    raw_content, content_type, retrieved_at = retrieve_source(url)
    source_meta.retrieved_at = retrieved_at
    source_meta.content_type = content_type

    if raw_content is None:
        processing_notes.append("Source retrieval failed — URL unreachable or returned error.")
        return ComplianceReportEntry(
            source=source_meta,
            security_scan=SecurityScanResult(),
            extraction_status="SOURCE_UNAVAILABLE",
            verification_status=VerificationStatus.SOURCE_UNAVAILABLE,
            processing_notes=processing_notes,
        )

    # ── Step 3: Content Extraction ──
    pdf_filepath = None
    if content_type == ContentType.PDF:
        pdf_filepath = save_pdf_temporarily(raw_content, url)

    extracted = extract_content(
        raw_content, content_type, url=url, pdf_filepath=pdf_filepath
    )

    if not extracted.extraction_success:
        processing_notes.append(f"Content extraction failed: {extracted.error}")
        return ComplianceReportEntry(
            source=source_meta,
            security_scan=SecurityScanResult(),
            extraction_status="EXTRACTION_FAILED",
            verification_status=VerificationStatus.SOURCE_UNAVAILABLE,
            processing_notes=processing_notes,
        )

    source_meta.source_title = extracted.title if extracted.title != "UNKNOWN" else title
    source_meta.publication_date = extracted.publication_date
    source_meta.content_length = len(extracted.text)

    logger.info(
        f"Content extracted: {len(extracted.text)} chars, "
        f"type={content_type.value}, title='{extracted.title[:60]}'"
    )

    # ── Step 4: Security Scan ──
    security_result = scan_content(extracted.text, source_url=url)

    if security_result.quarantined:
        processing_notes.append(
            f"SOURCE QUARANTINED: {security_result.threat_count} threats detected. "
            f"Content will NOT be sent to LLM."
        )
        return ComplianceReportEntry(
            source=source_meta,
            security_scan=security_result,
            extraction_status="SECURITY_QUARANTINED",
            verification_status=VerificationStatus.SECURITY_QUARANTINED,
            processing_notes=processing_notes,
        )

    if security_result.injection_detected:
        processing_notes.append(
            f"Minor injection patterns detected ({security_result.threat_count}). "
            f"Proceeding with warnings."
        )

    # Get sanitized content for LLM
    sanitized_content = get_sanitized_content(extracted.text, security_result)

    # ── Step 5: Quarantined LLM Extraction ──
    logger.info("Sending content to Quarantined LLM for extraction...")
    extraction = quarantined_extraction(sanitized_content, source_url=url)

    if extraction is None:
        processing_notes.append(
            "Quarantined LLM extraction failed. "
            "Check Ollama availability and model configuration."
        )
        return ComplianceReportEntry(
            source=source_meta,
            security_scan=security_result,
            extraction_status="FAILED",
            verification_status=VerificationStatus.REQUIRES_HUMAN_REVIEW,
            processing_notes=processing_notes,
        )

    # ── Step 6: Evidence Verification ──
    logger.info("Verifying evidence claims against source text...")
    verified_extraction, verification_status, verified_count, total_count = verify_evidence(
        extraction,
        extracted.text,
        source_pages=extracted.pages if extracted.pages else None,
    )

    # ── Step 7: Privileged LLM Impact Analysis ──
    logger.info("Sending sterile data to Privileged LLM for impact analysis...")
    impact = privileged_impact_analysis(verified_extraction, org_profile)

    if impact is None:
        processing_notes.append(
            "Privileged LLM impact analysis failed. "
            "Regulatory extraction is available but impact is not assessed."
        )

    # ── Assemble Finding ──
    return ComplianceReportEntry(
        source=source_meta,
        security_scan=security_result,
        regulatory_extraction=verified_extraction,
        extraction_status="SUCCESS",
        verification_status=verification_status,
        verified_claims_count=verified_count,
        total_claims_count=total_count,
        impact_analysis=impact,
        processing_notes=processing_notes,
    )


def run_pipeline(
    max_queries: int = 3,
    max_sources_per_query: int = 5,
    verbose: bool = False,
) -> None:
    """
    Run the full LIVE compliance radar pipeline.

    This is the primary execution path. There is NO demo mode.
    """
    setup_logging(verbose)
    logger = logging.getLogger("pipeline.main")

    print("\n" + "=" * 80)
    print("  AUTONOMOUS REGULATORY & COMPLIANCE RADAR")
    print("  Pipeline Mode: LIVE — All data from real-time web sources")
    print("=" * 80)

    org_profile = DEFAULT_ORG_PROFILE
    print(f"\n  Organization: {org_profile.name}")
    print(f"  Jurisdiction: {org_profile.jurisdiction}")
    print(f"  Bank Type:    {org_profile.bank_type}")
    print(f"  Started:      {datetime.now().isoformat()}")
    print("-" * 80)

    # ── Step 1: Generate Search Queries ──
    all_queries = generate_queries(org_profile)
    queries_to_run = all_queries[:max_queries]
    logger.info(f"Running {len(queries_to_run)} of {len(all_queries)} generated queries")

    # ── Step 2-7: Search & Process ──
    all_findings: List[ComplianceReportEntry] = []
    total_results = 0
    total_quarantined = 0
    seen_urls = set()

    for qi, query in enumerate(queries_to_run, 1):
        print(f"\n  [{qi}/{len(queries_to_run)}] Searching: {query}")
        logger.info(f"Query {qi}/{len(queries_to_run)}: {query}")

        try:
            results = execute_search(query)
        except RuntimeError as e:
            logger.error(f"Search failed: {e}")
            print(f"    [WARNING] Search failed: {e}")
            continue

        total_results += len(results)
        sources_processed = 0

        for result in results:
            url = result.get("href", "")
            title = result.get("title", "UNKNOWN")

            if not url or url in seen_urls:
                continue
            seen_urls.add(url)

            if sources_processed >= max_sources_per_query:
                logger.info(f"Reached max sources ({max_sources_per_query}) for this query")
                break

            print(f"    -> Processing: {url[:70]}...")

            try:
                finding = process_single_source(url, title, query, org_profile)
                all_findings.append(finding)
                sources_processed += 1

                if finding.security_scan.quarantined:
                    total_quarantined += 1
                    print(f"      [QUARANTINED] {finding.security_scan.threat_count} threats detected")
                elif finding.extraction_status == "SUCCESS":
                    ext = finding.regulatory_extraction
                    risk = finding.impact_analysis.risk_level if finding.impact_analysis else "N/A"
                    print(f"      [SUCCESS] Extracted: {ext.title[:50] if ext else 'N/A'} | Risk: {risk}")
                else:
                    print(f"      [INFO] Status: {finding.extraction_status}")

            except Exception as e:
                logger.error(f"Unexpected error processing {url}: {e}", exc_info=True)
                print(f"      [ERROR] {e}")

    # ── Step 8: Generate Report ──
    print("\n" + "-" * 80)
    print("  Generating compliance report...")

    report = generate_report(
        findings=all_findings,
        queries_executed=queries_to_run,
        org_name=org_profile.name,
        org_type=org_profile.bank_type,
        jurisdiction=org_profile.jurisdiction,
        total_results_found=total_results,
        total_quarantined=total_quarantined,
    )

    # Save report
    report_path = save_report(report)
    print(f"  Report saved: {report_path}")

    # Print summary
    print_report_summary(report)

    return report


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Autonomous Regulatory & Compliance Radar — LIVE Pipeline",
        epilog=(
            "This pipeline uses LIVE web data. No demo mode. "
            "Requires: Internet connection + Ollama running locally."
        ),
    )
    parser.add_argument(
        "--queries", type=int, default=3,
        help="Maximum number of search queries to execute (default: 3)"
    )
    parser.add_argument(
        "--max-sources", type=int, default=5,
        help="Maximum sources to process per query (default: 5)"
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="Enable verbose/debug logging"
    )

    args = parser.parse_args()

    try:
        run_pipeline(
            max_queries=args.queries,
            max_sources_per_query=args.max_sources,
            verbose=args.verbose,
        )
    except KeyboardInterrupt:
        print("\n\nPipeline interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nPipeline failed: {e}")
        logging.getLogger("pipeline.main").error(f"Pipeline failed: {e}", exc_info=True)
        sys.exit(1)
