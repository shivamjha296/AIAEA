import pytest
import sys
import os
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pipeline.search import generate_queries, execute_search, DDGSSearchProvider, SearXNGSearchProvider, SearchOrchestrator
from pipeline.retriever import retrieve_source
from pipeline.extractor import extract_content
from pipeline.evidence_verifier import verify_evidence
from pipeline.quarantined_llm import quarantined_extraction
from pipeline.privileged_llm import privileged_impact_analysis
from models import RegulatoryExtraction, EvidenceDetail, ContentType
from config import OrganizationProfile

class TestSearch:
    def test_generate_queries(self):
        profile = OrganizationProfile(name="Test Bank", bank_type="Coop", jurisdiction="India")
        queries = generate_queries(profile)
        assert len(queries) > 0
        assert "Test Bank" not in queries[0] # Just checking it's using templates

    @patch("pipeline.search.DDGS")
    def test_execute_search_ddgs(self, mock_ddgs):
        mock_instance = MagicMock()
        mock_instance.text.return_value = [{"title": "RBI", "href": "http://rbi.org", "body": "test"}]
        mock_ddgs.return_value = mock_instance
        
        provider = DDGSSearchProvider()
        results = provider.search("RBI circular")
        assert len(results) == 1
        assert results[0]["title"] == "RBI"
        assert results[0]["provider"] == "DDGS"

    @patch("pipeline.search.httpx.get")
    def test_execute_search_searxng(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [
                {"title": "RBI SearXNG", "url": "http://rbi.org/searxng", "content": "test", "engine": "duckduckgo"}
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        provider = SearXNGSearchProvider()
        results = provider.search("RBI circular")
        assert len(results) == 1
        assert results[0]["title"] == "RBI SearXNG"
        assert "SearXNG" in results[0]["provider"]

    def test_search_orchestrator_deduplication(self):
        orchestrator = SearchOrchestrator()
        
        # Test exact match
        url1 = "https://rbi.org.in/Scripts/NotificationUser.aspx"
        url2 = "https://rbi.org.in/Scripts/NotificationUser.aspx?id=1"
        url3 = "https://rbi.org.in/Scripts/NotificationUser.aspx#section"
        
        # Normalization strips fragments
        assert orchestrator._normalize_url(url1) == "https://rbi.org.in/Scripts/NotificationUser.aspx"
        assert orchestrator._normalize_url(url3) == "https://rbi.org.in/Scripts/NotificationUser.aspx"
        
        # Query params are kept
        assert orchestrator._normalize_url(url2) == "https://rbi.org.in/Scripts/NotificationUser.aspx?id=1"

    @patch.object(DDGSSearchProvider, "search")
    @patch.object(SearXNGSearchProvider, "search")
    def test_search_orchestrator_aggregation(self, mock_searxng, mock_ddgs):
        mock_ddgs.return_value = [
            {"title": "Result 1", "href": "https://example.com/1", "body": "...", "provider": "DDGS"}
        ]
        mock_searxng.return_value = [
            {"title": "Result 1 from SearXNG", "href": "https://example.com/1#test", "body": "...", "provider": "SearXNG (duckduckgo)"},
            {"title": "Result 2", "href": "https://example.com/2", "body": "...", "provider": "SearXNG (bing)"}
        ]
        
        orchestrator = SearchOrchestrator()
        results = orchestrator.execute_search("Test query")
        
        # Should deduplicate example.com/1 and example.com/1#test
        assert len(results) == 2
        assert results[0]["href"] == "https://example.com/1"
        assert results[1]["href"] == "https://example.com/2"

class TestRetriever:
    @patch("pipeline.retriever.requests.get")
    def test_retrieve_source_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "text/html"}
        mock_response.content = b"<html><body>test</body></html>"
        mock_get.return_value = mock_response

        content, mime_type, retrieved_at = retrieve_source("http://example.com")
        assert mime_type == ContentType.HTML
        assert b"test" in content

    @patch("pipeline.retriever.requests.get")
    def test_retrieve_source_failure(self, mock_get):
        import requests
        mock_get.side_effect = requests.RequestException("Timeout")
        content, mime_type, retrieved_at = retrieve_source("http://example.com")
        assert content is None
        assert mime_type == ContentType.UNKNOWN

class TestExtractor:
    def test_html_extraction(self):
        html_bytes = b"<html><head><title>Test</title></head><body><p>Hello <b>World</b></p></body></html>"
        result = extract_content(html_bytes, "text/html")
        assert "Hello" in result.text
        assert not result.pages

    def test_empty_html_extraction(self):
        result = extract_content(b"", "text/html")
        assert result.text == ""

class TestQuarantinedLLM:
    @patch("pipeline.quarantined_llm.httpx.post")
    def test_quarantined_extraction_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "message": {
                "content": '{"title": "Test Reg", "regulatory_body": "RBI", "status": "NEW", "jurisdiction": "India", "summary": "Sum", "key_requirements": [], "applicability_sectors": [], "penalties_or_consequences": "UNKNOWN"}'
            }
        }
        mock_post.return_value = mock_response
        
        ext = quarantined_extraction("Test content", "http://test.com")
        assert ext is not None
        assert ext.title == "Test Reg"

    @patch("pipeline.quarantined_llm.httpx.post")
    def test_quarantined_extraction_malformed_retry(self, mock_post):
        # First 2 fail, 3rd succeeds
        bad_response = MagicMock()
        bad_response.json.return_value = {"message": {"content": '{"bad": json}'}}
        
        good_response = MagicMock()
        good_response.json.return_value = {
            "message": {
                "content": '{"title": "Test Reg", "regulatory_body": "RBI", "status": "NEW", "jurisdiction": "India", "summary": "Sum", "key_requirements": [], "applicability_sectors": [], "penalties_or_consequences": "UNKNOWN"}'
            }
        }
        
        mock_post.side_effect = [bad_response, bad_response, good_response]
        
        # Override base_wait in the test if possible, or just let it wait a couple seconds
        with patch('pipeline.quarantined_llm.time.sleep', return_value=None):
            ext = quarantined_extraction("Test content", "http://test.com")
            assert ext is not None
            assert ext.title == "Test Reg"

class TestEvidenceVerifier:
    def test_verify_evidence_found(self):
        ext = RegulatoryExtraction(
            title="Test", regulatory_body="RBI", status="NEW", jurisdiction="India", summary="Sum",
            applicability_sectors=[], penalties_or_consequences="",
            key_requirements=[
                EvidenceDetail(claim="You must do X.", source_quote="The bank must do X immediately.", page_or_section="1")
            ]
        )
        source_text = "Here is the rule: The bank must do X immediately. End of rule."
        
        updated_ext, status, verified, total = verify_evidence(ext, source_text)
        assert verified == 1
        assert updated_ext.key_requirements[0].verified is True

    def test_verify_evidence_missing(self):
        ext = RegulatoryExtraction(
            title="Test", regulatory_body="RBI", status="NEW", jurisdiction="India", summary="Sum",
            applicability_sectors=[], penalties_or_consequences="",
            key_requirements=[
                EvidenceDetail(claim="You must do Y.", source_quote="The bank must do Y.", page_or_section="1")
            ]
        )
        source_text = "Here is the rule: The bank must do X immediately. End of rule."
        
        updated_ext, status, verified, total = verify_evidence(ext, source_text)
        assert verified == 0
        assert updated_ext.key_requirements[0].verified is False

class TestPrivilegedLLM:
    @patch("pipeline.privileged_llm.httpx.post")
    def test_privileged_analysis_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "message": {
                "content": '{"is_applicable": true, "applicability_rationale": "Yes", "affected_processes": [], "compliance_gaps": [], "risk_level": "HIGH", "risk_rationale": "Risk", "recommended_actions": [], "internal_review_required": true, "public_evidence_note": ""}'
            }
        }
        mock_post.return_value = mock_response
        
        ext = RegulatoryExtraction(
            title="Test", regulatory_body="RBI", status="NEW", jurisdiction="India", summary="Sum",
            applicability_sectors=[], penalties_or_consequences="", key_requirements=[]
        )
        profile = OrganizationProfile(name="Bank", bank_type="Coop", jurisdiction="India")
        
        analysis = privileged_impact_analysis(ext, profile)
        assert analysis is not None
        assert analysis.risk_level == "HIGH"
