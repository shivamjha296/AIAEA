"""
Module 2: Live Web Search using DuckDuckGo (DDGS).

Generates targeted regulatory search queries from the organization profile
and executes them against DDGS. Returns LIVE search results only — no
static result lists, no cached data, no demo mode.

Architecture reference: Section 6.1 — Web Search and Discovery
"""

import abc
import logging
from datetime import datetime
from typing import Any, Dict, List
import urllib.parse
import httpx

from ddgs import DDGS

from config import (
    DDGS_MAX_RESULTS,
    DDGS_REGION,
    DDGS_TIMELIMIT,
    REGULATORY_SEARCH_QUERIES,
    OrganizationProfile,
    SEARXNG_BASE_URL,
    SEARXNG_ENGINES,
    SEARXNG_MAX_RESULTS,
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


class SearchProvider(abc.ABC):
    """Abstract base class for search providers."""
    
    @abc.abstractmethod
    def search(self, query: str) -> List[Dict[str, Any]]:
        """Execute a search query and return a list of result dictionaries."""
        pass


class DDGSSearchProvider(SearchProvider):
    """DuckDuckGo Search implementation."""
    
    def search(self, query: str) -> List[Dict[str, Any]]:
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

            results_list = list(results)
            logger.info(f"DDGS returned {len(results_list)} results for: '{query}'")
            
            # Normalize results
            normalized = []
            for r in results_list:
                normalized.append({
                    "title": r.get("title", "N/A"),
                    "href": r.get("href", "N/A"),
                    "body": r.get("body", "N/A"),
                    "provider": "DDGS",
                })
            return normalized

        except Exception as e:
            error_msg = f"DDGS search failed for query '{query}': {e}"
            logger.error(error_msg)
            # Graceful failure
            return []


class SearXNGSearchProvider(SearchProvider):
    """SearXNG Search implementation."""
    
    def search(self, query: str) -> List[Dict[str, Any]]:
        logger.info(f"Executing SearXNG search: '{query}'")
        
        try:
            url = urllib.parse.urljoin(SEARXNG_BASE_URL, "/search")
            params = {
                "q": query,
                "format": "json",
                "engines": SEARXNG_ENGINES,
                "time_range": "month",
            }
            
            # Timeout is somewhat short to not hang the whole pipeline
            response = httpx.get(url, params=params, timeout=10.0)
            response.raise_for_status()
            
            data = response.json()
            results = data.get("results", [])
            
            if not results:
                logger.warning(f"No results returned from SearXNG for query: '{query}'")
                return []
                
            results_list = results[:SEARXNG_MAX_RESULTS]
            logger.info(f"SearXNG returned {len(results_list)} results for: '{query}'")
            
            # Normalize results
            normalized = []
            for r in results_list:
                engine = r.get("engine", "searxng")
                normalized.append({
                    "title": r.get("title", "N/A"),
                    "href": r.get("url", "N/A"),
                    "body": r.get("content", "N/A"),
                    "provider": f"SearXNG ({engine})",
                })
            return normalized
            
        except httpx.RequestError as e:
            logger.error(f"SearXNG connection error: {e}")
            return []
        except httpx.HTTPStatusError as e:
            logger.error(f"SearXNG HTTP error: {e}")
            return []
        except Exception as e:
            logger.error(f"SearXNG unexpected error: {e}")
            return []


class SearchOrchestrator:
    """Orchestrates multiple search providers."""
    
    def __init__(self):
        self.providers = [
            DDGSSearchProvider(),
            SearXNGSearchProvider()
        ]
        
    def _normalize_url(self, url: str) -> str:
        """Strip trailing slashes and fragments for deduplication."""
        if not url or url == "N/A":
            return ""
        parsed = urllib.parse.urlparse(url)
        # Strip fragment, keep path
        path = parsed.path.rstrip('/') if parsed.path != '/' else '/'
        normalized = f"{parsed.scheme}://{parsed.netloc}{path}"
        if parsed.query:
            normalized += f"?{parsed.query}"
        return normalized

    def execute_search(self, query: str) -> List[Dict[str, Any]]:
        """
        Execute search across all providers, aggregate, and deduplicate.
        """
        aggregated_results = []
        for provider in self.providers:
            provider_results = provider.search(query)
            aggregated_results.extend(provider_results)
            
        if not aggregated_results:
            logger.error(f"All search providers failed or returned empty for query '{query}'")
            raise RuntimeError(f"All search providers failed for query '{query}'")
            
        # Deduplicate
        seen_urls = set()
        deduped = []
        for r in aggregated_results:
            raw_url = r.get("href", "")
            norm_url = self._normalize_url(raw_url)
            
            if not norm_url or norm_url in seen_urls:
                continue
                
            seen_urls.add(norm_url)
            deduped.append(r)
            
        logger.info(f"Aggregated {len(aggregated_results)} results, deduplicated to {len(deduped)} unique results.")
        return deduped


def execute_search(query: str, provider: SearchProvider = None) -> List[Dict[str, Any]]:
    """
    Backwards compatible execute_search function.
    Now defaults to using the SearchOrchestrator if no provider specified.
    """
    if provider is not None:
        return provider.search(query)
        
    orchestrator = SearchOrchestrator()
    return orchestrator.execute_search(query)


def search_all_queries(profile: OrganizationProfile) -> List[Dict[str, Any]]:
    """
    Generate queries from the profile and execute all searches.

    Returns a deduplicated list of search results with the originating query attached.
    """
    queries = generate_queries(profile)
    all_results = []
    seen_urls = set()
    orchestrator = SearchOrchestrator()

    for query in queries:
        try:
            # We use the orchestrator to get deduped results for this specific query
            results = orchestrator.execute_search(query)
            for result in results:
                url = result.get("href", "")
                norm_url = orchestrator._normalize_url(url)
                if norm_url and norm_url not in seen_urls:
                    seen_urls.add(norm_url)
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
