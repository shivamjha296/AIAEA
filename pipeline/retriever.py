"""
Module 4a: Live Source Retrieval — HTTP GET for HTML and PDF.

After DDGS returns a result, this module:
1. Issues an HTTP GET to the actual URL.
2. Detects content type (HTML vs PDF).
3. Downloads PDFs to temporary storage.
4. Records retrieval timestamp.
5. Returns raw content + metadata.

Architecture reference: Section 6.2 — Web Scraping and Content Extraction
"""

import logging
import os
import time
from datetime import datetime
from typing import Optional, Tuple

import requests

from config import HTTP_MAX_RETRIES, HTTP_TIMEOUT, HTTP_USER_AGENT, TEMP_DIR
from models import ContentType

logger = logging.getLogger(__name__)


def _ensure_temp_dir() -> str:
    """Create the temporary download directory if it doesn't exist."""
    os.makedirs(TEMP_DIR, exist_ok=True)
    return TEMP_DIR


def detect_content_type(response: requests.Response) -> ContentType:
    """
    Detect whether the response contains HTML or PDF content.

    Checks Content-Type header and URL extension as fallback.
    """
    content_type_header = response.headers.get("Content-Type", "").lower()

    if "application/pdf" in content_type_header:
        return ContentType.PDF
    if "text/html" in content_type_header:
        return ContentType.HTML
    if "application/xhtml" in content_type_header:
        return ContentType.HTML

    # Fallback: check URL extension
    url_lower = response.url.lower()
    if url_lower.endswith(".pdf"):
        return ContentType.PDF
    if any(url_lower.endswith(ext) for ext in [".html", ".htm", ".asp", ".aspx", ".php"]):
        return ContentType.HTML

    # Default to HTML for web pages
    return ContentType.HTML


def retrieve_source(url: str) -> Tuple[Optional[bytes], ContentType, str]:
    """
    Retrieve content from a URL via HTTP GET.

    Args:
        url: The source URL to retrieve.

    Returns:
        Tuple of (raw_content_bytes, content_type, retrieved_at_timestamp)
        Returns (None, UNKNOWN, timestamp) if retrieval fails.
    """
    retrieved_at = datetime.now().isoformat()
    headers = {
        "User-Agent": HTTP_USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/pdf,*/*",
        "Accept-Language": "en-IN,en;q=0.9",
    }

    for attempt in range(1, HTTP_MAX_RETRIES + 1):
        try:
            logger.info(f"Retrieving source (attempt {attempt}): {url}")

            response = requests.get(
                url,
                headers=headers,
                timeout=HTTP_TIMEOUT,
                allow_redirects=True,
                verify=True,
            )
            response.raise_for_status()

            content_type = detect_content_type(response)
            raw_content = response.content

            logger.info(
                f"Successfully retrieved {len(raw_content)} bytes "
                f"({content_type.value}) from: {url}"
            )

            return raw_content, content_type, retrieved_at

        except requests.exceptions.Timeout:
            logger.warning(f"Timeout retrieving {url} (attempt {attempt})")
            if attempt < HTTP_MAX_RETRIES:
                time.sleep(2 * attempt)  # Exponential backoff
            continue

        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error retrieving {url}: {e}")
            return None, ContentType.UNKNOWN, retrieved_at

        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error retrieving {url}: {e}")
            if attempt < HTTP_MAX_RETRIES:
                time.sleep(2 * attempt)
            continue

        except requests.exceptions.RequestException as e:
            logger.error(f"Request error retrieving {url}: {e}")
            return None, ContentType.UNKNOWN, retrieved_at

    logger.error(f"All {HTTP_MAX_RETRIES} retrieval attempts failed for: {url}")
    return None, ContentType.UNKNOWN, retrieved_at


def save_pdf_temporarily(pdf_bytes: bytes, url: str) -> Optional[str]:
    """
    Save a downloaded PDF to temporary storage for extraction.

    Args:
        pdf_bytes: The raw PDF content.
        url: The source URL (used for naming).

    Returns:
        Path to the saved PDF, or None if saving failed.
    """
    try:
        temp_dir = _ensure_temp_dir()
        # Create a safe filename from the URL
        safe_name = url.split("/")[-1][:80] or "document"
        if not safe_name.lower().endswith(".pdf"):
            safe_name += ".pdf"
        # Remove unsafe characters
        safe_name = "".join(c if c.isalnum() or c in "._-" else "_" for c in safe_name)
        filepath = os.path.join(temp_dir, safe_name)

        with open(filepath, "wb") as f:
            f.write(pdf_bytes)

        logger.info(f"PDF saved temporarily: {filepath}")
        return filepath

    except Exception as e:
        logger.error(f"Failed to save PDF temporarily: {e}")
        return None
