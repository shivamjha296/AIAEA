"""
Source Trust Tier Classification Tests.

Tests the 4-tier source trust hierarchy to ensure:
- Official .gov.in domains → Tier 1 (Authoritative)
- Legal publications → Tier 2 (High)
- News outlets → Tier 3 (Medium)
- Unknown/blog sources → Tier 4 (Untrusted)
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pipeline.source_validator import (
    classify_source,
    extract_domain,
    is_processable,
    get_tier_description,
)


class TestDomainExtraction:
    """Test URL to domain extraction."""

    def test_simple_url(self):
        assert extract_domain("https://rbi.org.in/") == "rbi.org.in"

    def test_www_prefix_removed(self):
        assert extract_domain("https://www.rbi.org.in/scripts/page.aspx") == "rbi.org.in"

    def test_subdomain_preserved(self):
        assert extract_domain("https://m.rbi.org.in/page") == "m.rbi.org.in"

    def test_complex_url(self):
        domain = extract_domain(
            "https://www.meity.gov.in/content/digital-personal-data-protection"
        )
        assert domain == "meity.gov.in"

    def test_empty_url(self):
        assert extract_domain("") == ""

    def test_invalid_url(self):
        assert extract_domain("not-a-url") == ""


class TestSourceClassification:
    """Test 4-tier source trust classification."""

    # ── Tier 1: Authoritative (Government / Regulators) ──

    def test_rbi_tier1(self):
        tier, trust, _ = classify_source("https://www.rbi.org.in/Scripts/circular.aspx")
        assert tier == 1
        assert trust == "AUTHORITATIVE"

    def test_meity_tier1(self):
        tier, trust, _ = classify_source("https://meity.gov.in/dpdp-rules")
        assert tier == 1
        assert trust == "AUTHORITATIVE"

    def test_cert_in_tier1(self):
        tier, trust, _ = classify_source("https://www.cert-in.org.in/directives")
        assert tier == 1
        assert trust == "AUTHORITATIVE"

    def test_mca_tier1(self):
        tier, trust, _ = classify_source("https://www.mca.gov.in/notification")
        assert tier == 1
        assert trust == "AUTHORITATIVE"

    def test_egazette_tier1(self):
        tier, trust, _ = classify_source("https://egazette.gov.in/gazette/2025")
        assert tier == 1
        assert trust == "AUTHORITATIVE"

    def test_generic_gov_in_tier1(self):
        """Any .gov.in domain should be Tier 1."""
        tier, trust, _ = classify_source("https://some-ministry.gov.in/page")
        assert tier == 1
        assert trust == "AUTHORITATIVE"

    def test_nic_in_tier1(self):
        """NIC domains (.nic.in) should also be Tier 1."""
        tier, trust, _ = classify_source("https://something.nic.in/page")
        assert tier == 1
        assert trust == "AUTHORITATIVE"

    # ── Tier 2: High Trust (Legal Publications) ──

    def test_livelaw_tier2(self):
        tier, trust, _ = classify_source("https://www.livelaw.in/regulatory-update")
        assert tier == 2
        assert trust == "HIGH"

    def test_barandbench_tier2(self):
        tier, trust, _ = classify_source("https://www.barandbench.com/news")
        assert tier == 2
        assert trust == "HIGH"

    def test_mondaq_tier2(self):
        tier, trust, _ = classify_source("https://www.mondaq.com/india/banking")
        assert tier == 2
        assert trust == "HIGH"

    # ── Tier 3: Medium Trust (News Outlets) ──

    def test_economic_times_tier3(self):
        tier, trust, _ = classify_source(
            "https://economictimes.indiatimes.com/industry/banking"
        )
        assert tier == 3
        assert trust == "MEDIUM"

    def test_livemint_tier3(self):
        tier, trust, _ = classify_source("https://www.livemint.com/economy/policy")
        assert tier == 3
        assert trust == "MEDIUM"

    def test_thehindu_tier3(self):
        tier, trust, _ = classify_source("https://www.thehindu.com/business/regulation")
        assert tier == 3
        assert trust == "MEDIUM"

    # ── Tier 4: Untrusted (Blogs / Social / Unknown) ──

    def test_unknown_blog_tier4(self):
        tier, trust, _ = classify_source("https://random-blog.wordpress.com/post")
        assert tier == 4
        assert trust == "UNTRUSTED"

    def test_social_media_tier4(self):
        tier, trust, _ = classify_source("https://twitter.com/rbi/status/123")
        assert tier == 4
        assert trust == "UNTRUSTED"

    def test_unknown_domain_tier4(self):
        tier, trust, _ = classify_source("https://totally-unknown-site.xyz/page")
        assert tier == 4
        assert trust == "UNTRUSTED"


class TestProcessability:
    """Test which tiers are auto-processable."""

    def test_tier1_processable(self):
        assert is_processable(1) is True

    def test_tier2_processable(self):
        assert is_processable(2) is True

    def test_tier3_processable(self):
        assert is_processable(3) is True

    def test_tier4_not_processable(self):
        assert is_processable(4) is False


class TestTierDescription:
    """Test tier description retrieval."""

    def test_tier1_description(self):
        desc = get_tier_description(1)
        assert "Authoritative" in desc

    def test_tier4_description(self):
        desc = get_tier_description(4)
        assert "Untrusted" in desc

    def test_invalid_tier(self):
        desc = get_tier_description(99)
        assert "Unknown" in desc


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
