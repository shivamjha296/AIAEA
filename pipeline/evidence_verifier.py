"""
Module 9: Evidence Verification — Binding Claims to Source Text.

For every claim in the RegulatoryExtraction, this module verifies that
the source_quote ACTUALLY EXISTS in the original retrieved content.

Rules:
- If the quote is found → verified = True, with location info
- If the quote is NOT found → verified = False, status = EVIDENCE_UNVERIFIED
- NEVER generates a quote that doesn't exist in the retrieved source

Architecture reference: Section 6.5 — Verification & Change Detection
"""

import logging
from difflib import SequenceMatcher
from typing import List, Tuple

from models import EvidenceDetail, RegulatoryExtraction, VerificationStatus

logger = logging.getLogger(__name__)

# Minimum similarity ratio for fuzzy matching
# (accounts for minor whitespace/formatting differences)
FUZZY_MATCH_THRESHOLD = 0.75


def _normalize_text(text: str) -> str:
    """Normalize text for comparison: lowercase, collapse whitespace."""
    import re
    text = text.lower().strip()
    text = re.sub(r"\s+", " ", text)
    return text


def _find_quote_in_source(
    quote: str, source_text: str, pages: List[dict] = None
) -> Tuple[bool, str, float]:
    """
    Search for a quote in the source text.

    Returns:
        (found, location, similarity_score)
    """
    normalized_quote = _normalize_text(quote)
    normalized_source = _normalize_text(source_text)

    # Exact substring match (after normalization)
    if normalized_quote in normalized_source:
        # Try to find the page for PDF content
        location = _find_page_location(quote, pages) if pages else "UNKNOWN"
        return True, location, 1.0

    # Fuzzy matching: slide a window across the source
    quote_len = len(normalized_quote)
    if quote_len < 10:
        # Too short for reliable fuzzy matching
        return False, "UNKNOWN", 0.0

    best_ratio = 0.0
    best_location = "UNKNOWN"

    # Check chunks of similar length throughout the source
    step = max(1, quote_len // 4)
    for i in range(0, len(normalized_source) - quote_len + 1, step):
        chunk = normalized_source[i:i + quote_len + 20]  # slight overlap for partial matches
        ratio = SequenceMatcher(None, normalized_quote, chunk).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            if pages:
                # Estimate which page this position corresponds to
                best_location = _estimate_page_from_position(
                    i, source_text, pages
                )

    if best_ratio >= FUZZY_MATCH_THRESHOLD:
        return True, best_location, best_ratio

    return False, "UNKNOWN", best_ratio


def _find_page_location(quote: str, pages: List[dict]) -> str:
    """Find which page a quote appears on (for PDF content)."""
    if not pages:
        return "UNKNOWN"

    normalized_quote = _normalize_text(quote)
    for page_entry in pages:
        page_text = _normalize_text(page_entry.get("text", ""))
        if normalized_quote in page_text:
            return f"Page {page_entry['page']}"

    return "UNKNOWN"


def _estimate_page_from_position(
    char_position: int, full_text: str, pages: List[dict]
) -> str:
    """Estimate the page number from a character position in the full text."""
    cumulative_length = 0
    for page_entry in pages:
        page_text = page_entry.get("text", "")
        cumulative_length += len(page_text) + 50  # Account for page markers
        if char_position < cumulative_length:
            return f"Page {page_entry['page']}"
    return "UNKNOWN"


def verify_evidence(
    extraction: RegulatoryExtraction,
    source_text: str,
    source_pages: List[dict] = None,
) -> Tuple[RegulatoryExtraction, str, int, int]:
    """
    Verify all evidence claims against the original source text.

    For each key_requirement in the extraction:
    - If the source_quote is found in the source text → verified = True
    - If not found → verified = False
    - Location (page/section) is updated if found

    Args:
        extraction: The RegulatoryExtraction from the Quarantined LLM.
        source_text: The original extracted content from the web source.
        source_pages: Page-by-page text for PDFs (for page number attribution).

    Returns:
        (updated_extraction, overall_status, verified_count, total_count)
    """
    verified_count = 0
    total_count = len(extraction.key_requirements)
    updated_requirements: List[EvidenceDetail] = []

    logger.info(f"Verifying {total_count} evidence claims against source text...")

    for i, requirement in enumerate(extraction.key_requirements):
        quote = requirement.source_quote

        if not quote or quote.strip() == "":
            # No quote provided — cannot verify
            updated_req = requirement.model_copy(update={
                "verified": False,
                "page_or_section": "UNKNOWN — No quote provided by extraction LLM",
            })
            updated_requirements.append(updated_req)
            logger.warning(f"  Claim {i+1}: No source quote provided — UNVERIFIED")
            continue

        found, location, similarity = _find_quote_in_source(
            quote, source_text, source_pages
        )

        if found:
            verified_count += 1
            updated_req = requirement.model_copy(update={
                "verified": True,
                "page_or_section": location if location != "UNKNOWN" else requirement.page_or_section,
            })
            updated_requirements.append(updated_req)
            logger.info(
                f"  Claim {i+1}: VERIFIED (similarity={similarity:.2f}, "
                f"location={location})"
            )
        else:
            updated_req = requirement.model_copy(update={
                "verified": False,
            })
            updated_requirements.append(updated_req)
            logger.warning(
                f"  Claim {i+1}: UNVERIFIED — quote not found in source "
                f"(best similarity={similarity:.2f})"
            )

    # Update the extraction with verified requirements
    updated_extraction = extraction.model_copy(update={
        "key_requirements": updated_requirements,
    })

    # Determine overall verification status
    if total_count == 0:
        overall_status = VerificationStatus.REQUIRES_HUMAN_REVIEW
    elif verified_count == total_count:
        overall_status = VerificationStatus.VERIFIED
    elif verified_count > 0:
        overall_status = VerificationStatus.REQUIRES_HUMAN_REVIEW
    else:
        overall_status = VerificationStatus.EVIDENCE_UNVERIFIED

    logger.info(
        f"Evidence verification complete: {verified_count}/{total_count} claims verified. "
        f"Overall status: {overall_status}"
    )

    return updated_extraction, overall_status, verified_count, total_count
