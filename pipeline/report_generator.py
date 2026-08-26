"""
Module 13-14: Report Generator — Final JSON Report Assembly.

Assembles the complete ComplianceReport from the current pipeline execution.
Every value originates from live data. No hardcoded regulatory answers.

The report includes:
- Full source traceability (URLs, timestamps, tiers)
- Security scan results
- Regulatory extractions with evidence
- Impact analysis with recommended actions
- Risk statistics
- Disclaimers about public-only evidence basis

Architecture reference: Section 6.5 — Alert & Report Generation
"""

import json
import logging
import os
import uuid
from datetime import datetime
from typing import List

from config import REPORTS_DIR
from models import ComplianceReport, ComplianceReportEntry

logger = logging.getLogger(__name__)


def _ensure_reports_dir() -> str:
    """Create the reports directory if it doesn't exist."""
    os.makedirs(REPORTS_DIR, exist_ok=True)
    return REPORTS_DIR


def calculate_risk_statistics(findings: List[ComplianceReportEntry]) -> dict:
    """
    Calculate risk level statistics from all findings.

    Returns counts by risk level.
    """
    stats = {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
        "unknown": 0,
    }

    for finding in findings:
        if finding.impact_analysis:
            risk = finding.impact_analysis.risk_level.upper()
            if risk == "CRITICAL":
                stats["critical"] += 1
            elif risk == "HIGH":
                stats["high"] += 1
            elif risk == "MEDIUM":
                stats["medium"] += 1
            elif risk == "LOW":
                stats["low"] += 1
            else:
                stats["unknown"] += 1
        else:
            stats["unknown"] += 1

    return stats


def generate_report(
    findings: List[ComplianceReportEntry],
    queries_executed: List[str],
    org_name: str,
    org_type: str,
    jurisdiction: str,
    total_results_found: int = 0,
    total_quarantined: int = 0,
) -> ComplianceReport:
    """
    Assemble the final compliance report from the current pipeline execution.

    All data comes from the live pipeline — nothing is hardcoded.
    """
    risk_stats = calculate_risk_statistics(findings)

    report = ComplianceReport(
        report_id=str(uuid.uuid4()),
        generated_at=datetime.now().isoformat(),
        pipeline_mode="LIVE",
        organization_name=org_name,
        organization_type=org_type,
        jurisdiction=jurisdiction,
        queries_executed=queries_executed,
        total_results_found=total_results_found,
        total_sources_retrieved=len(findings),
        total_sources_quarantined=total_quarantined,
        findings=findings,
        critical_findings=risk_stats["critical"],
        high_findings=risk_stats["high"],
        medium_findings=risk_stats["medium"],
        low_findings=risk_stats["low"],
        unknown_findings=risk_stats["unknown"],
    )

    logger.info(
        f"Report generated: {report.report_id}\n"
        f"  Findings: {len(findings)}\n"
        f"  Critical: {risk_stats['critical']}, High: {risk_stats['high']}, "
        f"Medium: {risk_stats['medium']}, Low: {risk_stats['low']}, "
        f"Unknown: {risk_stats['unknown']}"
    )

    return report


def save_report(report: ComplianceReport) -> str:
    """
    Save the compliance report as a timestamped JSON file.

    Returns the path to the saved report.
    """
    reports_dir = _ensure_reports_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"compliance_report_{timestamp}.json"
    filepath = os.path.join(reports_dir, filename)

    try:
        report_dict = report.model_dump()

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report_dict, f, indent=2, ensure_ascii=False, default=str)

        logger.info(f"Report saved: {filepath}")
        return filepath

    except Exception as e:
        logger.error(f"Failed to save report: {e}")
        raise


def print_report_summary(report: ComplianceReport) -> None:
    """Print a human-readable summary of the report to console."""
    print("\n" + "=" * 80)
    print("  AUTONOMOUS REGULATORY & COMPLIANCE RADAR — REPORT SUMMARY")
    print("=" * 80)
    print(f"  Report ID:        {report.report_id}")
    print(f"  Generated At:     {report.generated_at}")
    print(f"  Pipeline Mode:    {report.pipeline_mode}")
    print(f"  Organization:     {report.organization_name}")
    print(f"  Type:             {report.organization_type}")
    print(f"  Jurisdiction:     {report.jurisdiction}")
    print("-" * 80)
    print(f"  Queries Executed: {len(report.queries_executed)}")
    print(f"  Results Found:    {report.total_results_found}")
    print(f"  Sources Retrieved:{report.total_sources_retrieved}")
    print(f"  Sources Quarantined: {report.total_sources_quarantined}")
    print("-" * 80)
    print("  RISK DISTRIBUTION:")
    print(f"    CRITICAL:  {report.critical_findings}")
    print(f"    HIGH:      {report.high_findings}")
    print(f"    MEDIUM:    {report.medium_findings}")
    print(f"    LOW:       {report.low_findings}")
    print(f"    UNKNOWN:   {report.unknown_findings}")
    print("-" * 80)

    if report.findings:
        print("\n  FINDINGS:\n")
        for i, finding in enumerate(report.findings, 1):
            status_icon = {
                "SUCCESS": "[OK]",
                "QUARANTINED": "[QUARANTINED]",
                "FAILED": "[FAILED]",
                "SOURCE_UNAVAILABLE": "[UNAVAILABLE]",
            }.get(finding.extraction_status, "[?]")

            print(f"  {status_icon} Finding {i}:")
            print(f"      Source:    {finding.source.source_url[:80]}")
            print(f"      Tier:      {finding.source.source_tier} ({finding.source.trust_level})")
            print(f"      Retrieved: {finding.source.retrieved_at}")
            print(f"      Status:    {finding.extraction_status}")
            print(f"      Security:  {'CLEAN' if not finding.security_scan.injection_detected else 'THREATS DETECTED'}")

            if finding.regulatory_extraction:
                ext = finding.regulatory_extraction
                print(f"      Title:     {ext.title[:70]}")
                print(f"      Authority: {ext.regulatory_body}")
                print(f"      Effective: {ext.effective_date}")
                print(f"      Evidence:  {finding.verified_claims_count}/{finding.total_claims_count} verified")

            if finding.impact_analysis:
                imp = finding.impact_analysis
                print(f"      Risk:      {imp.risk_level}")
                print(f"      Applicable:{imp.is_applicable}")
                if imp.recommended_actions:
                    print(f"      Actions:   {len(imp.recommended_actions)} recommended")

            print()

    print("-" * 80)
    print("  DISCLAIMERS:")
    for disclaimer in report.disclaimers:
        print(f"    * {disclaimer}")
    print("=" * 80 + "\n")
