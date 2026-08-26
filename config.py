"""
Configuration for the Autonomous Regulatory & Compliance Radar.

This module defines:
- Organization profile (configurable, publicly available information only)
- Ollama LLM settings
- Regulatory search query templates
- Source trust tier definitions

NO hardcoded regulatory data. Only search parameters and organizational context.
"""

from dataclasses import dataclass, field
from typing import Dict, List


# ============================================================
# OLLAMA LLM CONFIGURATION
# ============================================================

OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "llama3.2:1b"  # Active downloaded model
OLLAMA_TEMPERATURE_EXTRACTION = 0.0   # Deterministic for Quarantined LLM
OLLAMA_TEMPERATURE_ANALYSIS = 0.2     # Slightly creative for Privileged LLM
OLLAMA_REQUEST_TIMEOUT = 120          # Seconds — regulatory texts can be long


# ============================================================
# HTTP RETRIEVAL CONFIGURATION
# ============================================================

HTTP_TIMEOUT = 30        # Seconds for source retrieval
HTTP_MAX_RETRIES = 2
HTTP_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
MAX_CONTENT_LENGTH = 500_000  # Maximum characters to send to LLM


# ============================================================
# SEARCH CONFIGURATION
# ============================================================

DDGS_REGION = "in-en"        # India — English
DDGS_TIMELIMIT = "m"         # Last month
DDGS_MAX_RESULTS = 10        # Results per query


# ============================================================
# ORGANIZATION PROFILE — PUBLICLY AVAILABLE INFORMATION ONLY
# ============================================================

@dataclass
class OrganizationProfile:
    """
    Configurable organization profile using ONLY publicly available information.

    This profile establishes the context for regulatory search and impact analysis.
    It does NOT claim access to confidential bank systems or internal policies.
    """
    name: str = "Representative Indian Cooperative Bank"
    industry: str = "Banking"
    bank_type: str = "Urban Cooperative Bank"
    jurisdiction: str = "India"
    state: str = "Maharashtra"

    business_activities: List[str] = field(default_factory=lambda: [
        "Retail Banking",
        "Digital Banking",
        "Digital Lending",
        "KYC Processing",
        "Payment Services",
        "Customer Data Processing",
        "NEFT/RTGS/IMPS Transactions",
        "Fixed Deposits & Savings Accounts",
    ])

    departments: List[str] = field(default_factory=lambda: [
        "Compliance",
        "Legal",
        "IT",
        "Cyber Security",
        "Operations",
        "Risk Management",
    ])

    regulatory_bodies: List[str] = field(default_factory=lambda: [
        "RBI",       # Reserve Bank of India
        "MeitY",     # Ministry of Electronics and Information Technology
        "CERT-In",   # Indian Computer Emergency Response Team
        "MCA",       # Ministry of Corporate Affairs
        "SEBI",      # Securities and Exchange Board of India
        "IRDAI",     # Insurance Regulatory and Development Authority
    ])

    key_regulatory_domains: List[str] = field(default_factory=lambda: [
        "Data Protection (DPDP Act)",
        "Cybersecurity",
        "KYC/AML Compliance",
        "Digital Lending Guidelines",
        "Cooperative Banking Regulations",
        "Payment Systems",
        "IT Governance",
        "Outsourcing Guidelines",
    ])

    def to_context_string(self) -> str:
        """Serialize profile to a text block for LLM context."""
        return (
            f"Organization: {self.name}\n"
            f"Industry: {self.industry}\n"
            f"Type: {self.bank_type}\n"
            f"Jurisdiction: {self.jurisdiction}, {self.state}\n"
            f"Business Activities: {', '.join(self.business_activities)}\n"
            f"Departments: {', '.join(self.departments)}\n"
            f"Regulatory Bodies: {', '.join(self.regulatory_bodies)}\n"
            f"Key Regulatory Domains: {', '.join(self.key_regulatory_domains)}\n"
            f"\nNOTE: This profile contains ONLY publicly available information. "
            f"No internal policies or confidential data are included. "
            f"If internal information is required for a compliance assessment, "
            f"state: 'UNKNOWN — REQUIRES INTERNAL BANK REVIEW'."
        )


# Default profile instance
DEFAULT_ORG_PROFILE = OrganizationProfile()


# ============================================================
# SEARCH QUERY TEMPLATES
# Queries are dynamically generated — only templates are configured.
# The actual search results come from LIVE DDGS.
# ============================================================

REGULATORY_SEARCH_QUERIES = [
    "RBI circular cooperative bank compliance {year}",
    "MeitY DPDP Act rules notification {year}",
    "CERT-In cybersecurity directive banking {year}",
    "RBI digital lending guidelines update {year}",
    "India data protection regulation banking {year}",
    "RBI KYC AML compliance update cooperative bank {year}",
    "MCA corporate governance banking notification {year}",
    "RBI IT governance cybersecurity framework bank {year}",
]


# ============================================================
# SOURCE TRUST TIER HIERARCHY
# Per architecture: 4-tier trust system
# ============================================================

SOURCE_TIER_DEFINITIONS: Dict[int, dict] = {
    1: {
        "name": "Authoritative (Official Regulator / Government)",
        "trust_level": "AUTHORITATIVE",
        "action": "Direct extraction; automatically initiates compliance mapping.",
        "domains": [
            "rbi.org.in",
            "meity.gov.in",
            "cert-in.org.in",
            "mca.gov.in",
            "egazette.gov.in",
            "sebi.gov.in",
            "irdai.gov.in",
            "pib.gov.in",
            "india.gov.in",
            "legislative.gov.in",
            "drishtiias.com",  # Government exam/policy reference
        ],
    },
    2: {
        "name": "High Trust (Major Legal Publications)",
        "trust_level": "HIGH",
        "action": "Utilized for discovery; triggers search for corresponding Tier 1 source.",
        "domains": [
            "scconline.com",
            "barandbench.com",
            "livelaw.in",
            "indiakanoon.org",
            "lawctopus.com",
            "mondaq.com",
            "vinodkothari.com",
        ],
    },
    3: {
        "name": "Medium Trust (Major News Outlets)",
        "trust_level": "MEDIUM",
        "action": "Alert generated for human review; no automated action taken.",
        "domains": [
            "thehindu.com",
            "economictimes.indiatimes.com",
            "livemint.com",
            "ndtv.com",
            "business-standard.com",
            "financialexpress.com",
            "thehindubusinessline.com",
            "reuters.com",
            "bloomberg.com",
        ],
    },
    4: {
        "name": "Untrusted (Blogs / Social Media / Unknown)",
        "trust_level": "UNTRUSTED",
        "action": "Ignored or flagged exclusively for manual verification.",
        "domains": [],  # Catch-all for anything not in Tier 1-3
    },
}


# ============================================================
# REPORT CONFIGURATION
# ============================================================

REPORTS_DIR = "reports"
TEMP_DIR = "temp_downloads"
