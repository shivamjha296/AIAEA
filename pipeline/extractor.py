"""
Module 4b: Content Extraction — HTML (BeautifulSoup4) and PDF (PyMuPDF).

HTML path:
  1. Parse with BeautifulSoup4
  2. Strip navigation, headers, footers, ads
  3. Preserve meaningful text, title, publication date
  4. Return clean text

PDF path:
  1. Open with PyMuPDF (fitz)
  2. Extract text page-by-page with page numbers
  3. Preserve section structure
  4. Return clean text with page references

Architecture reference: Section 6.2 — Web Scraping and Content Extraction
"""

import logging
import re
from dataclasses import dataclass, field
from typing import List, Optional

from bs4 import BeautifulSoup

from config import MAX_CONTENT_LENGTH
from models import ContentType

logger = logging.getLogger(__name__)


@dataclass
class ExtractedContent:
    """Result of content extraction from a source."""
    text: str = ""
    title: str = "UNKNOWN"
    publication_date: str = "UNKNOWN"
    content_type: ContentType = ContentType.UNKNOWN
    page_count: int = 0
    pages: List[dict] = field(default_factory=list)  # For PDFs: [{page: 1, text: "..."}]
    extraction_success: bool = False
    error: str = ""


# ============================================================
# HTML EXTRACTION
# ============================================================

# Elements to remove (navigation, boilerplate)
HTML_REMOVE_TAGS = [
    "nav", "header", "footer", "aside", "script", "style", "noscript",
    "iframe", "form", "button", "input", "select", "textarea",
    "advertisement", "ad", "sidebar",
]

# Class/ID patterns suggesting boilerplate
BOILERPLATE_PATTERNS = re.compile(
    r"(nav|menu|sidebar|footer|header|breadcrumb|cookie|popup|modal|"
    r"advertisement|social|share|comment|related|recommend)",
    re.IGNORECASE,
)


def extract_html(raw_html: bytes, url: str = "") -> ExtractedContent:
    """
    Extract meaningful content from an HTML page.

    Removes navigation, ads, boilerplate. Preserves meaningful text,
    title, and publication date when available.
    """
    result = ExtractedContent(content_type=ContentType.HTML)

    try:
        html_text = raw_html.decode("utf-8", errors="replace")
        soup = BeautifulSoup(html_text, "lxml")

        # Extract title
        title_tag = soup.find("title")
        if title_tag and title_tag.string:
            result.title = title_tag.string.strip()

        # Try to find publication date from meta tags
        date_meta_names = [
            "article:published_time", "datePublished", "date",
            "DC.date", "publication_date", "pubdate",
            "article:modified_time", "dateModified",
        ]
        for meta_name in date_meta_names:
            meta = soup.find("meta", attrs={"property": meta_name}) or \
                   soup.find("meta", attrs={"name": meta_name})
            if meta and meta.get("content"):
                result.publication_date = meta["content"].strip()
                break

        # Remove only script, style, nav, footer, header, aside, noscript
        for tag_name in ["script", "style", "nav", "footer", "header", "aside", "noscript", "iframe"]:
            for element in soup.find_all(tag_name):
                element.decompose()

        # Extract text from main content area if present, or entire body
        main_content = (
            soup.find("main") or
            soup.find("article") or
            soup.find(attrs={"role": "main"}) or
            soup.find("div", id=re.compile(r"main|content|body", re.I)) or
            soup.find("body") or
            soup
        )

        text = main_content.get_text(separator="\n", strip=True)

        # Clean up excessive whitespace
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        text = "\n".join(lines)

        # Truncate if too long
        if len(text) > MAX_CONTENT_LENGTH:
            text = text[:MAX_CONTENT_LENGTH] + "\n\n[CONTENT TRUNCATED]"
            logger.warning(f"Content truncated to {MAX_CONTENT_LENGTH} chars for: {url}")

        result.text = text
        result.extraction_success = bool(text.strip())

        logger.info(
            f"HTML extraction: {len(text)} chars, title='{result.title[:60]}', "
            f"date='{result.publication_date}'"
        )

    except Exception as e:
        result.error = f"HTML extraction failed: {e}"
        logger.error(result.error)

    return result


# ============================================================
# PDF EXTRACTION
# ============================================================

def extract_pdf(raw_pdf: bytes, filepath: Optional[str] = None) -> ExtractedContent:
    """
    Extract text from a PDF using PyMuPDF (fitz).

    Preserves page numbers for evidence traceability.
    Each page's text is stored separately with its page number.
    """
    result = ExtractedContent(content_type=ContentType.PDF)

    try:
        import fitz  # PyMuPDF

        # Open from bytes or file
        if filepath:
            doc = fitz.open(filepath)
        else:
            doc = fitz.open(stream=raw_pdf, filetype="pdf")

        result.page_count = len(doc)
        all_text_parts = []

        for page_num in range(len(doc)):
            page = doc[page_num]
            page_text = page.get_text("text")

            if page_text.strip():
                page_entry = {
                    "page": page_num + 1,
                    "text": page_text.strip(),
                }
                result.pages.append(page_entry)
                all_text_parts.append(
                    f"[PAGE {page_num + 1}]\n{page_text.strip()}"
                )

        # Try to extract title from metadata
        metadata = doc.metadata
        if metadata and metadata.get("title"):
            result.title = metadata["title"]

        # Try to extract date from metadata
        if metadata:
            for date_key in ["creationDate", "modDate"]:
                date_val = metadata.get(date_key, "")
                if date_val:
                    # PDF dates are often in format D:YYYYMMDDHHmmSS
                    result.publication_date = date_val
                    break

        doc.close()

        full_text = "\n\n".join(all_text_parts)

        # Truncate if too long
        if len(full_text) > MAX_CONTENT_LENGTH:
            full_text = full_text[:MAX_CONTENT_LENGTH] + "\n\n[CONTENT TRUNCATED]"

        result.text = full_text
        result.extraction_success = bool(full_text.strip())

        logger.info(
            f"PDF extraction: {result.page_count} pages, "
            f"{len(full_text)} chars, title='{result.title[:60]}'"
        )

    except Exception as e:
        result.error = f"PDF extraction failed: {e}"
        logger.error(result.error)

    return result


# ============================================================
# UNIFIED EXTRACTION ENTRY POINT
# ============================================================

def extract_content(
    raw_content: bytes,
    content_type: ContentType,
    url: str = "",
    pdf_filepath: Optional[str] = None,
) -> ExtractedContent:
    """
    Extract content from raw bytes based on content type.

    Routes to HTML or PDF extraction as appropriate.
    """
    if content_type == ContentType.PDF:
        return extract_pdf(raw_content, filepath=pdf_filepath)
    elif content_type == ContentType.HTML:
        return extract_html(raw_content, url=url)
    else:
        # Try HTML first, then PDF
        logger.warning(f"Unknown content type for {url}, attempting HTML extraction")
        result = extract_html(raw_content, url=url)
        if not result.extraction_success:
            logger.warning("HTML extraction failed, attempting PDF extraction")
            result = extract_pdf(raw_content)
        return result
