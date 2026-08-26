"""
Module 2: Live Web Search using DuckDuckGo (DDGS).

Generates targeted regulatory search queries from the organization profile
and executes them against DDGS. Returns LIVE search results only — no
static result lists, no cached data, no demo mode.

Architecture reference: Section 6.1 — Web Search and Discovery
"""

import logging
from datetime import datetime
from typing import Any, Dict, List

from ddgs import DDGS

from config import (
    DDGS_MAX_RESULTS,
    DDGS_REGION,
    DDGS_TIMELIMIT,
    REGULATORY_SEARCH_QUERIES,
    OrganizationProfile,
)

logger = logging.getLogger(__name__)


def generate_queries(profile: OrganizationProfile) -> List[str]:
    """
    Dynamically generate search queries based on the organization profile.

    The queries are templates filled with the current year.
    The actual search results come from LIVE DDGS execution.
    """
    current_year = datetime.now().year
    queries = []

    for template in REGULATORY_SEARCH_QUERIES:
        query = template.format(year=current_year)
        queries.append(query)

    logger.info(f"Generated {len(queries)} search queries for {profile.name}")
    return queries


def execute_search(query: str) -> List[Dict[str, Any]]:
    """
    Execute a LIVE search using DDGS.

    Args:
        query: The search query string.

    Returns:
        List of search result dicts with keys: title, href, body.

    Raises:
        RuntimeError: If the search fails (network error, etc.)
    """
    logger.info(f"Executing DDGS search: '{query}'")

    try:
        results = DDGS().text(
            query,
            region=DDGS_REGION,
            timelimit=DDGS_TIMELIMIT,
            max_results=DDGS_MAX_RESULTS,
        )

        if not results:
            logger.warning(f"No results returned for query: '{query}'")
            return []

        # Ensure results is a list (DDGS may return a generator)
        results_list = list(results)

        logger.info(f"DDGS returned {len(results_list)} results for: '{query}'")
        for i, r in enumerate(results_list):
            logger.debug(f"  [{i+1}] {r.get('title', 'N/A')} — {r.get('href', 'N/A')}")

        return results_list

    except Exception as e:
        error_msg = f"DDGS search failed for query '{query}': {e}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e


def search_all_queries(profile: OrganizationProfile) -> List[Dict[str, Any]]:
    """
    Generate queries from the profile and execute all searches.

    Returns a deduplicated list of search results with the originating query attached.
    """
    queries = generate_queries(profile)
    all_results = []
    seen_urls = set()

    for query in queries:
        try:
            results = execute_search(query)
            for result in results:
                url = result.get("href", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    result["_search_query"] = query
                    result["_retrieved_at"] = datetime.now().isoformat()
                    all_results.append(result)
        except RuntimeError as e:
            logger.warning(f"Skipping failed query: {e}")
            continue

    logger.info(
        f"Total unique results across all queries: {len(all_results)} "
        f"(from {len(queries)} queries)"
    )
    return all_results
