"""
Module 3: Source Validation — 4-Tier Trust Hierarchy.

Evaluates source URLs against a tiered trust system. Official government
domains (Tier 1) receive automatic processing; blogs and social media
(Tier 4) are flagged for manual review only.

Architecture reference: Section 6.2 — Source Validation
"""

import logging
from urllib.parse import urlparse
from typing import Tuple

from config import SOURCE_TIER_DEFINITIONS
from models import SourceTrustLevel

logger = logging.getLogger(__name__)


def extract_domain(url: str) -> str:
    """
    Extract the base domain from a URL.

    Examples:
        https://www.rbi.org.in/Scripts/... → rbi.org.in
        https://meity.gov.in/content/...  → meity.gov.in
    """
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname or ""
        # Remove 'www.' prefix for consistent matching
        if hostname.startswith("www."):
            hostname = hostname[4:]
        return hostname.lower()
    except Exception:
        return ""


def classify_source(url: str) -> Tuple[int, str, str]:
    """
    Classify a source URL into a trust tier.

    Args:
        url: The source URL to classify.

    Returns:
        Tuple of (tier_number, trust_level, pipeline_action)
    """
    domain = extract_domain(url)

    if not domain:
        logger.warning(f"Could not extract domain from URL: {url}")
        return 4, SourceTrustLevel.UNTRUSTED, SOURCE_TIER_DEFINITIONS[4]["action"]

    # Check each tier's domain list
    for tier_num in [1, 2, 3]:
        tier_def = SOURCE_TIER_DEFINITIONS[tier_num]
        for tier_domain in tier_def["domains"]:
            # Check if the domain matches or is a subdomain
            if domain == tier_domain or domain.endswith("." + tier_domain):
                logger.info(
                    f"Source classified as Tier {tier_num} ({tier_def['trust_level']}): "
                    f"{domain}"
                )
                return tier_num, tier_def["trust_level"], tier_def["action"]

    # Check for generic .gov.in domains (all government domains are Tier 1)
    if domain.endswith(".gov.in") or domain.endswith(".nic.in"):
        tier_def = SOURCE_TIER_DEFINITIONS[1]
        logger.info(f"Source classified as Tier 1 (government domain): {domain}")
        return 1, tier_def["trust_level"], tier_def["action"]

    # Default: Tier 4 (Untrusted)
    tier_def = SOURCE_TIER_DEFINITIONS[4]
    logger.info(f"Source classified as Tier 4 (Untrusted): {domain}")
    return 4, tier_def["trust_level"], tier_def["action"]


def is_processable(tier: int) -> bool:
    """
    Determine if a source should be automatically processed.

    Tier 1 and 2 sources are auto-processed.
    Tier 3 sources generate alerts but are still processed for information.
    Tier 4 sources are logged but skipped for auto-processing.
    """
    return tier <= 3


def get_tier_description(tier: int) -> str:
    """Get a human-readable description of a trust tier."""
    if tier in SOURCE_TIER_DEFINITIONS:
        return SOURCE_TIER_DEFINITIONS[tier]["name"]
    return "Unknown Tier"
