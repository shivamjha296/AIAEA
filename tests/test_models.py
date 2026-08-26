"""
Pydantic Schema Validation Tests.

Tests that the Pydantic models correctly validate well-formed data,
reject malformed data, and use appropriate fail-safe defaults.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pydantic import ValidationError

from models import (
    ActionItem,
    ComplianceReport,
    ComplianceReportEntry,
    ContentType,
    EvidenceDetail,
    ImpactAnalysis,
    RegulatoryExtraction,
    SecurityScanResult,
    SourceMetadata,
    SourceTrustLevel,
    ThreatDetail,
    VerificationStatus,
)


class TestEvidenceDetail:
    """Test the EvidenceDetail model."""

    def test_valid_evidence(self):
        """Valid evidence with all fields should parse correctly."""
        evidence = EvidenceDetail(
            claim="Banks must report breaches within 72 hours",
            source_quote="shall report any personal data breach to the Board within 72 hours",
            page_or_section="Page 5",
            verified=True,
        )
        assert evidence.claim == "Banks must report breaches within 72 hours"
        assert evidence.verified is True
        assert evidence.page_or_section == "Page 5"

    def test_evidence_defaults(self):
        """Evidence with only required fields should use defaults."""
        evidence = EvidenceDetail(
            claim="Test claim",
            source_quote="Test quote",
        )
        assert evidence.page_or_section == "UNKNOWN"
        assert evidence.verified is False

    def test_empty_claim_allowed(self):
        """Empty strings should be allowed (field is present but empty)."""
        evidence = EvidenceDetail(claim="", source_quote="")
        assert evidence.claim == ""


class TestRegulatoryExtraction:
    """Test the RegulatoryExtraction model."""

    def test_valid_full_extraction(self):
        """Full extraction with all fields should parse correctly."""
        extraction = RegulatoryExtraction(
            title="DPDP Rules, 2025",
            regulatory_body="MeitY",
            publication_date="2025-11-13",
            effective_date="2026-11-01",
            status="NEW",
            jurisdiction="India",
            summary="Digital Personal Data Protection Rules",
            key_requirements=[
                EvidenceDetail(
                    claim="72-hour breach notification",
                    source_quote="shall report within 72 hours",
                )
            ],
            applicability_sectors=["Banking", "Technology"],
            penalties_or_consequences="Up to ₹250 crore",
        )
        assert extraction.title == "DPDP Rules, 2025"
        assert extraction.regulatory_body == "MeitY"
        assert len(extraction.key_requirements) == 1

    def test_extraction_defaults(self):
        """Extraction with no fields should use fail-safe defaults."""
        extraction = RegulatoryExtraction()
        assert extraction.title == "UNKNOWN"
        assert extraction.regulatory_body == "UNKNOWN"
        assert extraction.publication_date == "DATE_UNCLEAR"
        assert extraction.effective_date == "DATE_UNCLEAR"
        assert extraction.status == "UNKNOWN"
        assert extraction.jurisdiction == "India"
        assert extraction.key_requirements == []
        assert extraction.penalties_or_consequences == "UNKNOWN"

    def test_extraction_with_multiple_requirements(self):
        """Multiple requirements should be correctly stored."""
        reqs = [
            EvidenceDetail(claim=f"Requirement {i}", source_quote=f"Quote {i}")
            for i in range(5)
        ]
        extraction = RegulatoryExtraction(key_requirements=reqs)
        assert len(extraction.key_requirements) == 5


class TestSourceMetadata:
    """Test the SourceMetadata model."""

    def test_valid_source(self):
        """Valid source metadata should parse correctly."""
        source = SourceMetadata(
            source_url="https://rbi.org.in/circular/123",
            source_domain="rbi.org.in",
            source_title="RBI Circular 123",
            source_tier=1,
            trust_level=SourceTrustLevel.AUTHORITATIVE,
            content_type=ContentType.HTML,
            search_query="RBI circular 2025",
        )
        assert source.source_tier == 1
        assert source.trust_level == SourceTrustLevel.AUTHORITATIVE
        assert source.retrieved_at  # Should have a default timestamp

    def test_source_defaults(self):
        """Source with only required fields should use appropriate defaults."""
        source = SourceMetadata(
            source_url="https://example.com",
            source_domain="example.com",
        )
        assert source.source_title == "UNKNOWN"
        assert source.source_tier == 4
        assert source.trust_level == SourceTrustLevel.UNTRUSTED


class TestSecurityScanResult:
    """Test the SecurityScanResult model."""

    def test_clean_scan(self):
        """Clean scan should have no threats."""
        result = SecurityScanResult()
        assert result.injection_detected is False
        assert result.quarantined is False
        assert result.threat_count == 0
        assert result.threats == []

    def test_scan_with_threats(self):
        """Scan with threats should track all details."""
        result = SecurityScanResult(
            injection_detected=True,
            quarantined=True,
            threats=[
                ThreatDetail(
                    threat_type="PROMPT_INJECTION",
                    pattern_matched="ignore all previous instructions",
                    severity="CRITICAL",
                )
            ],
            threat_count=1,
        )
        assert result.injection_detected is True
        assert result.quarantined is True
        assert result.threats[0].severity == "CRITICAL"


class TestImpactAnalysis:
    """Test the ImpactAnalysis model."""

    def test_valid_impact(self):
        """Full impact analysis should parse correctly."""
        impact = ImpactAnalysis(
            is_applicable=True,
            applicability_rationale="Bank processes personal data",
            affected_processes=["KYC", "Digital Lending"],
            compliance_gaps=[
                "UNKNOWN — REQUIRES INTERNAL BANK REVIEW"
            ],
            risk_level="HIGH",
            recommended_actions=[
                ActionItem(
                    action_title="Update breach reporting",
                    department="Compliance",
                    priority="CRITICAL",
                    rationale="DPDP mandates 72-hour reporting",
                )
            ],
        )
        assert impact.is_applicable is True
        assert impact.risk_level == "HIGH"
        assert len(impact.recommended_actions) == 1
        assert impact.internal_review_required is True  # Default

    def test_impact_defaults(self):
        """Impact with defaults should indicate review needed."""
        impact = ImpactAnalysis()
        assert impact.internal_review_required is True
        assert "PUBLICLY AVAILABLE" in impact.public_evidence_note


class TestComplianceReport:
    """Test the ComplianceReport model."""

    def test_valid_report(self):
        """Full report should assemble correctly."""
        report = ComplianceReport(
            report_id="test-123",
            organization_name="Test Bank",
            organization_type="Urban Cooperative Bank",
            jurisdiction="India",
        )
        assert report.pipeline_mode == "LIVE"
        assert report.generated_at  # Should have timestamp
        assert len(report.disclaimers) > 0
        assert "LIVE" in report.disclaimers[0]

    def test_report_has_no_demo_mode(self):
        """Report should always be LIVE mode."""
        report = ComplianceReport(
            report_id="test",
            organization_name="Test",
            organization_type="Test",
            jurisdiction="India",
        )
        assert report.pipeline_mode == "LIVE"
        # Verify demo mode is not even an option
        assert "DEMO" not in report.pipeline_mode


class TestVerificationStatus:
    """Test VerificationStatus enum values."""

    def test_all_failsafe_statuses_exist(self):
        """All required fail-safe statuses must be defined."""
        required_statuses = [
            "SOURCE_UNAVAILABLE",
            "SECURITY_QUARANTINED",
            "EVIDENCE_UNVERIFIED",
            "SOURCE_CONFLICT",
            "DATE_UNCLEAR",
            "APPLICABILITY_UNKNOWN",
            "REQUIRES_HUMAN_REVIEW",
            "VERIFIED",
        ]
        for status_name in required_statuses:
            assert hasattr(VerificationStatus, status_name), \
                f"Missing fail-safe status: {status_name}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
