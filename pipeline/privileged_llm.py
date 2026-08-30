"""
Pipeline Module: Privileged LLM Impact Analysis (Pure Ollama LLM)
================================================================
The validated, sanitized extraction JSON is sent to the Privileged LLM
to assess regulatory impact on the organization.

The Privileged LLM NEVER sees untrusted raw content.
"""

import json
import logging
import time
from typing import Optional
import httpx
from pydantic import ValidationError

from config import (
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    OLLAMA_TEMPERATURE_ANALYSIS,
    OLLAMA_REQUEST_TIMEOUT,
    OrganizationProfile,
)
from models import RegulatoryExtraction, ImpactAnalysis

logger = logging.getLogger("pipeline.privileged_llm")

PRIVILEGED_SYSTEM_PROMPT = """You are a senior banking regulatory compliance officer and risk analyst.
Your job is to analyze validated regulatory updates and assess their impact on a specific financial institution.

CRITICAL INSTRUCTIONS:
- You receive ONLY verified, structured regulatory data.
- Assess applicability, operational impact, compliance gaps, and risk level.
- Base your analysis ONLY on the regulatory text provided and the organization profile.
- Do NOT fabricate internal bank policies or systems.
- If an impact cannot be determined from public information, state: "UNKNOWN — REQUIRES INTERNAL BANK REVIEW".
- For risk level, use ONLY: CRITICAL, HIGH, MEDIUM, LOW, UNKNOWN.
- For recommended actions, assign clear departments, priorities, deadlines, and rationales.
- Output ONLY valid JSON matching the exact schema specified below. No markdown, no prose.

JSON SCHEMA:
{
    "is_applicable": true,
    "applicability_rationale": "Clear explanation of why this regulation applies or does not apply",
    "affected_processes": ["List of banking processes affected, e.g., KYC/AML, Loan Underwriting, IT Security, etc."],
    "compliance_gaps": ["List of potential gaps between standard practices and new requirements"],
    "risk_level": "One of: CRITICAL, HIGH, MEDIUM, LOW, UNKNOWN",
    "risk_rationale": "Detailed explanation for the assigned risk level",
    "recommended_actions": [
        {
            "action_title": "Specific action the bank must take",
            "department": "Responsible department, e.g., Compliance, IT, Legal, Risk Management",
            "priority": "One of: CRITICAL, HIGH, MEDIUM, LOW",
            "deadline": "Target timeframe, e.g., Within 30 days, Immediate, By [date]",
            "rationale": "Why this action is needed"
        }
    ],
    "internal_review_required": true,
    "public_evidence_note": "This analysis is based on PUBLICLY AVAILABLE regulatory information only."
}"""


def privileged_impact_analysis(
    extraction: RegulatoryExtraction,
    org_profile: OrganizationProfile,
) -> Optional[ImpactAnalysis]:
    """
    MODULE 10-12: Pure Privileged LLM impact analysis via Ollama.
    """
    requirements_summary = []
    for req in extraction.key_requirements:
        verification = "VERIFIED" if req.verified else "UNVERIFIED"
        requirements_summary.append(f"- {req.claim} [{verification}]")

    analysis_prompt = f"""Analyze the following VERIFIED regulatory update for impact on our organization.

ORGANIZATION PROFILE (publicly available information only):
{org_profile.to_context_string()}

REGULATORY UPDATE (extracted and validated):
Title: {extraction.title}
Authority: {extraction.regulatory_body}
Publication Date: {extraction.publication_date}
Effective Date: {extraction.effective_date}
Status: {extraction.status}
Jurisdiction: {extraction.jurisdiction}
Summary: {extraction.summary}
Applicable Sectors: {', '.join(extraction.applicability_sectors) or 'Not specified'}
Penalties: {extraction.penalties_or_consequences}

KEY REQUIREMENTS:
{chr(10).join(requirements_summary) if requirements_summary else 'None extracted'}
"""

    url = f"{OLLAMA_BASE_URL}/api/chat"
    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": PRIVILEGED_SYSTEM_PROMPT},
            {"role": "user", "content": analysis_prompt},
        ],
        "stream": False,
        "format": "json",
        "options": {
            "temperature": OLLAMA_TEMPERATURE_ANALYSIS,
        },
    }

    max_retries = 3
    base_wait = 2

    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Calling Privileged LLM ({OLLAMA_MODEL}) for impact analysis... (Attempt {attempt}/{max_retries})")
            response = httpx.post(
                url,
                json=payload,
                timeout=OLLAMA_REQUEST_TIMEOUT,
            )
            response.raise_for_status()

            result = response.json()
            content = result.get("message", {}).get("content", "")
            if not content:
                logger.error(f"Privileged LLM returned empty content (Attempt {attempt}/{max_retries})")
                if attempt < max_retries:
                    time.sleep(base_wait ** attempt)
                    continue
                return None

            parsed_json = json.loads(content)

            # Normalize string lists if LLM formats entries as dict objects
            if "compliance_gaps" in parsed_json and isinstance(parsed_json["compliance_gaps"], list):
                parsed_json["compliance_gaps"] = [
                    g if isinstance(g, str) else (g.get("gap_title") or g.get("description") or str(g))
                    for g in parsed_json["compliance_gaps"]
                ]
            if "affected_processes" in parsed_json and isinstance(parsed_json["affected_processes"], list):
                parsed_json["affected_processes"] = [
                    p if isinstance(p, str) else (p.get("process_name") or p.get("process") or str(p))
                    for p in parsed_json["affected_processes"]
                ]

            impact = ImpactAnalysis(**parsed_json)
            logger.info(f"Privileged LLM analysis complete: risk={impact.risk_level}")
            return impact

        except httpx.RequestError as e:
            logger.warning(f"Ollama network error (Attempt {attempt}/{max_retries}): {e}")
        except httpx.HTTPStatusError as e:
            logger.warning(f"Ollama HTTP error (Attempt {attempt}/{max_retries}): {e}")
        except json.JSONDecodeError as e:
            logger.warning(f"Ollama JSON parse error (Attempt {attempt}/{max_retries}): {e}")
        except ValidationError as e:
            logger.warning(f"Ollama Pydantic validation error (Attempt {attempt}/{max_retries}): {e}")
        except Exception as e:
            logger.error(f"Unexpected error in Privileged LLM impact analysis: {e}")
            return None

        if attempt < max_retries:
            sleep_time = base_wait ** attempt
            logger.info(f"Retrying in {sleep_time}s...")
            time.sleep(sleep_time)
            
    logger.error(f"Privileged LLM impact analysis failed after {max_retries} attempts.")
    return None
