import pytest
import sys
import os
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import run_pipeline
from config import OrganizationProfile

class TestIntegration:
    @patch("pipeline.search.DDGS")
    @patch("pipeline.retriever.requests.get")
    @patch("pipeline.quarantined_llm.httpx.post")
    @patch("pipeline.privileged_llm.httpx.post")
    def test_full_pipeline_flow(self, mock_priv_post, mock_quar_post, mock_get, mock_ddgs):
        # 1. Mock Search
        mock_ddgs_instance = MagicMock()
        mock_ddgs_instance.text.return_value = [{"title": "RBI Mock Circular", "href": "https://rbi.org.in/mock"}]
        mock_ddgs.return_value = mock_ddgs_instance
        
        # 2. Mock Retrieval
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "text/html"}
        mock_response.content = b"<html><body>RBI Mock Circular regarding cooperative banks. The bank must do X immediately.</body></html>"
        mock_get.return_value = mock_response
        
        # 3. Mock Quarantined LLM
        mock_quar_response = MagicMock()
        mock_quar_response.json.return_value = {
            "message": {
                "content": '{"title": "RBI Mock Circular", "regulatory_body": "RBI", "status": "NEW", "jurisdiction": "India", "summary": "Sum", "key_requirements": [{"claim": "You must do X.", "source_quote": "The bank must do X immediately.", "page_or_section": "1"}], "applicability_sectors": [], "penalties_or_consequences": "UNKNOWN"}'
            }
        }
        mock_quar_post.return_value = mock_quar_response
        
        # 4. Mock Privileged LLM
        mock_priv_response = MagicMock()
        mock_priv_response.json.return_value = {
            "message": {
                "content": '{"is_applicable": true, "applicability_rationale": "Yes", "affected_processes": [], "compliance_gaps": [], "risk_level": "HIGH", "risk_rationale": "Risk", "recommended_actions": [], "internal_review_required": true, "public_evidence_note": ""}'
            }
        }
        mock_priv_post.return_value = mock_priv_response
        
        profile = OrganizationProfile(name="Test Bank", bank_type="Coop", jurisdiction="India")
        
        run_pipeline(max_queries=1, max_sources_per_query=1)
