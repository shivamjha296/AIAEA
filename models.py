"""
Pydantic data models for the Autonomous Regulatory & Compliance Radar.

Every schema enforces strict validation. Fields that cannot be determined from
public sources use explicit fail-safe defaults (UNKNOWN, DATE_UNCLEAR, etc.)
rather than guessing or hallucinating.

Architecture reference: Section 7.1 — Pydantic Data Models
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


# ============================================================
# ENUMS — Controlled vocabularies
# ============================================================

class RegulatoryStatus(str, Enum):
    """Classification of the regulatory document type."""
    NEW = "NEW"
    AMENDMENT = "AMENDMENT"
    REPEAL = "REPEAL"
    CIRCULAR = "CIRCULAR"
    NOTIFICATION = "NOTIFICATION"
    GUIDELINE = "GUIDELINE"
    GOVERNMENT_ORDER = "GOVERNMENT_ORDER"
    COURT_DECISION = "COURT_DECISION"
    COMMENTARY = "COMMENTARY"
    IRRELEVANT = "IRRELEVANT"
    UNKNOWN = "UNKNOWN"


class SourceTrustLevel(str, Enum):
    """4-tier trust hierarchy for sources."""
    AUTHORITATIVE = "AUTHORITATIVE"     # Tier 1: .gov.in, RBI, MeitY
    HIGH = "HIGH"                       # Tier 2: Legal publications
    MEDIUM = "MEDIUM"                   # Tier 3: News outlets
    UNTRUSTED = "UNTRUSTED"             # Tier 4: Blogs, social media


class VerificationStatus(str, Enum):
    """Status of evidence verification against source text."""
    VERIFIED = "VERIFIED"
    EVIDENCE_UNVERIFIED = "EVIDENCE_UNVERIFIED"
    SOURCE_UNAVAILABLE = "SOURCE_UNAVAILABLE"
    SECURITY_QUARANTINED = "SECURITY_QUARANTINED"
    SOURCE_CONFLICT = "SOURCE_CONFLICT"
    DATE_UNCLEAR = "DATE_UNCLEAR"
    APPLICABILITY_UNKNOWN = "APPLICABILITY_UNKNOWN"
    REQUIRES_HUMAN_REVIEW = "REQUIRES_HUMAN_REVIEW"


class Priority(str, Enum):
    """Priority levels for action items."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ContentType(str, Enum):
    """Type of retrieved content."""
    HTML = "HTML"
    PDF = "PDF"
    UNKNOWN = "UNKNOWN"


# ============================================================
# SOURCE & RETRIEVAL MODELS
# ============================================================

class SourceMetadata(BaseModel):
    """Metadata about a retrieved source — full traceability."""
    source_url: str = Field(description="The URL from which content was retrieved.")
    source_domain: str = Field(description="Domain of the source (e.g., rbi.org.in).")
    source_title: str = Field(default="UNKNOWN", description="Title of the page/document.")
    source_tier: int = Field(default=4, description="Trust tier (1=Authoritative, 4=Untrusted).")
    trust_level: SourceTrustLevel = Field(
        default=SourceTrustLevel.UNTRUSTED,
        description="Trust classification."
    )
    content_type: ContentType = Field(
        default=ContentType.UNKNOWN,
        description="Whether the source is HTML or PDF."
    )
    search_query: str = Field(default="", description="The search query that discovered this source.")
    retrieved_at: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="ISO timestamp when the source was retrieved."
    )
    publication_date: str = Field(
        default="UNKNOWN",
        description="Publication/update date of the source, if discoverable."
    )
    content_length: int = Field(default=0, description="Length of extracted text in characters.")


# ============================================================
# SECURITY MODELS
# ============================================================

class ThreatDetail(BaseModel):
    """Details of a detected security threat in source content."""
    threat_type: str = Field(description="Type of threat (e.g., PROMPT_INJECTION, HIDDEN_INSTRUCTION).")
    pattern_matched: str = Field(description="The pattern or text that triggered the detection.")
    location: str = Field(default="UNKNOWN", description="Approximate location in the content.")
    severity: str = Field(default="HIGH", description="Severity: LOW, MEDIUM, HIGH, CRITICAL.")


class SecurityScanResult(BaseModel):
    """Result of security scanning on retrieved content."""
    injection_detected: bool = Field(
        default=False,
        description="Whether prompt injection was detected."
    )
    quarantined: bool = Field(
        default=False,
        description="Whether the source was quarantined due to security threats."
    )
    threats: List[ThreatDetail] = Field(
        default_factory=list,
        description="List of detected threats."
    )
    threat_count: int = Field(default=0, description="Number of threats detected.")
    scan_timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="When the security scan was performed."
    )


# ============================================================
# REGULATORY EXTRACTION MODELS (Quarantined LLM output)
# ============================================================

class EvidenceDetail(BaseModel):
    """
    A single regulatory claim with its supporting evidence.

    The source_quote MUST be a verbatim quote from the retrieved text.
    If no exact quote can be found, verified should be False.
    """
    claim: str = Field(description="The summarized regulatory requirement or obligation.")
    source_quote: str = Field(
        description="Exact verbatim quote from the source text supporting the claim. "
                    "Must exist in the original retrieved content."
    )
    page_or_section: str = Field(
        default="UNKNOWN",
        description="Page number (for PDFs) or section heading where the quote appears."
    )
    verified: bool = Field(
        default=False,
        description="Whether the source_quote was verified to exist in the retrieved text."
    )


class RegulatoryExtraction(BaseModel):
    """
    Structured extraction from a regulatory source.

    This is the output schema for the Quarantined LLM.
    Every field must be extracted from the actual source content.
    If a field cannot be determined, use the explicit default.
    """
    title: str = Field(
        default="UNKNOWN",
        description="Official title of the regulation, circular, or notification."
    )
    regulatory_body: str = Field(
        default="UNKNOWN",
        description="The authority issuing the regulation (e.g., RBI, MeitY, CERT-In)."
    )
    publication_date: str = Field(
        default="DATE_UNCLEAR",
        description="Date the regulation was published (YYYY-MM-DD if available)."
    )
    effective_date: str = Field(
        default="DATE_UNCLEAR",
        description="Date the regulation becomes legally enforceable (YYYY-MM-DD if available)."
    )
    status: str = Field(
        default="UNKNOWN",
        description="Classification: NEW, AMENDMENT, REPEAL, CIRCULAR, NOTIFICATION, "
                    "GUIDELINE, GOVERNMENT_ORDER, COURT_DECISION, COMMENTARY, IRRELEVANT."
    )
    jurisdiction: str = Field(
        default="India",
        description="Jurisdiction where the regulation applies."
    )
    summary: str = Field(
        default="",
        description="Brief summary of the regulation's purpose and scope."
    )
    key_requirements: List[EvidenceDetail] = Field(
        default_factory=list,
        description="List of specific obligations/requirements with supporting evidence."
    )
    applicability_sectors: List[str] = Field(
        default_factory=list,
        description="Sectors or entity types to which the regulation applies."
    )
    penalties_or_consequences: str = Field(
        default="UNKNOWN",
        description="Penalties for non-compliance, if stated in the source."
    )


# ============================================================
# IMPACT ANALYSIS MODELS (Privileged LLM output)
# ============================================================

class ActionItem(BaseModel):
    """A specific compliance action that should be taken."""
    action_title: str = Field(description="Clear title of the required action.")
    department: str = Field(description="Department responsible (e.g., Compliance, IT, Legal).")
    priority: str = Field(
        default="MEDIUM",
        description="Priority: LOW, MEDIUM, HIGH, CRITICAL."
    )
    deadline: str = Field(
        default="UNKNOWN — REQUIRES INTERNAL BANK REVIEW",
        description="Recommended deadline. Use 'UNKNOWN' if not determinable from public info."
    )
    rationale: str = Field(
        description="Why this action is needed, linked to the regulatory requirement."
    )


class ImpactAnalysis(BaseModel):
    """
    Impact analysis of a regulation on the organization.

    This is the output of the Privileged LLM.
    Uses ONLY publicly available information + the sanitized regulatory extraction.
    Fields that require internal data are marked UNKNOWN.
    """
    is_applicable: bool = Field(
        default=True,
        description="Whether the regulation applies to this organization type."
    )
    applicability_rationale: str = Field(
        default="",
        description="Explanation of why the regulation is or is not applicable."
    )
    affected_processes: List[str] = Field(
        default_factory=list,
        description="Business processes potentially affected."
    )
    compliance_gaps: List[str] = Field(
        default_factory=list,
        description="Identified or potential compliance gaps. "
                    "Use 'UNKNOWN — REQUIRES INTERNAL BANK REVIEW' for gaps "
                    "that cannot be assessed without internal information."
    )
    risk_level: str = Field(
        default="UNKNOWN",
        description="Overall risk: LOW, MEDIUM, HIGH, CRITICAL, or UNKNOWN."
    )
    risk_rationale: str = Field(
        default="",
        description="Explanation of the risk assessment."
    )
    recommended_actions: List[ActionItem] = Field(
        default_factory=list,
        description="Specific actions recommended for compliance."
    )
    internal_review_required: bool = Field(
        default=True,
        description="Whether internal bank review is required for complete assessment."
    )
    public_evidence_note: str = Field(
        default="This analysis is based on PUBLICLY AVAILABLE information only. "
                "Internal bank policies and systems were NOT accessed.",
        description="Disclaimer about the evidence basis."
    )


# ============================================================
# COMPLETE COMPLIANCE REPORT
# ============================================================

class ComplianceReportEntry(BaseModel):
    """A single regulatory finding with full traceability."""
    # Source traceability
    source: SourceMetadata
    security_scan: SecurityScanResult

    # Regulatory extraction (from Quarantined LLM)
    regulatory_extraction: Optional[RegulatoryExtraction] = None
    extraction_status: str = Field(
        default="PENDING",
        description="Status of extraction: SUCCESS, FAILED, QUARANTINED, SOURCE_UNAVAILABLE."
    )

    # Evidence verification
    verification_status: str = Field(
        default=VerificationStatus.REQUIRES_HUMAN_REVIEW,
        description="Overall verification status of the evidence."
    )
    verified_claims_count: int = Field(default=0)
    total_claims_count: int = Field(default=0)

    # Impact analysis (from Privileged LLM)
    impact_analysis: Optional[ImpactAnalysis] = None

    # Processing metadata
    processing_notes: List[str] = Field(
        default_factory=list,
        description="Notes about processing issues, warnings, or limitations."
    )


class ComplianceReport(BaseModel):
    """
    The final compliance report — generated entirely from the current pipeline execution.

    Every value originates from live data. No hardcoded regulatory answers.
    """
    # Report metadata
    report_id: str = Field(description="Unique identifier for this report.")
    generated_at: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="When this report was generated."
    )
    pipeline_mode: str = Field(
        default="LIVE",
        description="Always LIVE. No demo mode."
    )

    # Organization context
    organization_name: str = Field(description="Name of the organization being assessed.")
    organization_type: str = Field(description="Type of organization (e.g., Urban Cooperative Bank).")
    jurisdiction: str = Field(description="Primary jurisdiction.")

    # Search context
    queries_executed: List[str] = Field(
        default_factory=list,
        description="Search queries that were executed."
    )
    total_results_found: int = Field(default=0)
    total_sources_retrieved: int = Field(default=0)
    total_sources_quarantined: int = Field(default=0)

    # Findings
    findings: List[ComplianceReportEntry] = Field(
        default_factory=list,
        description="Individual regulatory findings."
    )

    # Summary statistics
    critical_findings: int = Field(default=0)
    high_findings: int = Field(default=0)
    medium_findings: int = Field(default=0)
    low_findings: int = Field(default=0)
    unknown_findings: int = Field(default=0)

    # Disclaimers
    disclaimers: List[str] = Field(
        default_factory=lambda: [
            "This report is generated from LIVE web sources retrieved at the time of execution.",
            "All analysis is based on PUBLICLY AVAILABLE information only.",
            "Internal bank policies and systems were NOT accessed or assumed.",
            "Fields marked 'UNKNOWN' or 'REQUIRES INTERNAL BANK REVIEW' need internal verification.",
            "This report does NOT constitute legal advice.",
        ]
    )
