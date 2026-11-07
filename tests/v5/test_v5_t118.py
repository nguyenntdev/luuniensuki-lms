# -*- coding: utf-8 -*-
"""V5-T118: Market claims evidence register Test Suite.

Ticket: V5-T118 (Wave W11, Slot A08).
Goal:
- Market claims evidence register in docs/rbpc/BUSINESS_PLAN_DRAFT.md, docs/rbpc/MARKET_CLAIMS_EVIDENCE_REGISTER.md,
  and backend/services/rbpc_market_claims.py.
- Categorize every market claim with dates, method, sample size, and truth tier (OBSERVED / HYPOTHESIS / FORECAST).
- Export utilities for pitch reviews (JSON and Markdown).
- Negative abuse invariant:
  Unverified external benchmark or TAM projection cannot be displayed as actual LƯU NIÊN operational KPI.
"""
from __future__ import annotations

import json
from pathlib import Path
import pytest

from backend.services.rbpc_market_claims import (
    CANONICAL_MARKET_CLAIMS,
    MarketClaimCategory,
    MarketClaimEvidence,
    MarketClaimsEvidenceRegister,
    TruthTier,
    default_market_claims_register,
)


def test_v5_t118_register_integrity_and_truth_tier_coverage():
    """Verify that every canonical market claim contains mandatory fields, valid truth tier, date, method, and sample size."""
    register = default_market_claims_register
    claims = register.get_all_claims()
    assert len(claims) >= 14, f"Expected at least 14 market claims, found {len(claims)}"

    tiers_found = {c.truth_tier for c in claims}
    assert TruthTier.OBSERVED in tiers_found
    assert TruthTier.HYPOTHESIS in tiers_found
    assert TruthTier.FORECAST in tiers_found

    for c in claims:
        assert c.claim_id.startswith("MC-")
        assert c.statement
        assert c.metric_value
        assert c.date_recorded
        assert c.methodology
        assert c.sample_size
        assert c.source_reference
        assert c.validation_status == "VERIFIED"


def test_v5_t118_truth_tier_filtering_and_counts():
    """Verify queries by truth tier and category."""
    register = default_market_claims_register
    observed = register.get_by_truth_tier(TruthTier.OBSERVED)
    hypotheses = register.get_by_truth_tier(TruthTier.HYPOTHESIS)
    forecasts = register.get_by_truth_tier(TruthTier.FORECAST)

    assert len(observed) >= 5
    assert len(hypotheses) >= 4
    assert len(forecasts) >= 3

    # Check specific critical claims
    mc010 = next(c for c in observed if c.claim_id == "MC-010")
    assert "202,360,638 VND" in mc010.statement
    assert mc010.truth_tier == TruthTier.OBSERVED

    mc012 = next(c for c in forecasts if c.claim_id == "MC-012")
    assert mc012.category == MarketClaimCategory.MARKET_SIZING
    assert mc012.truth_tier == TruthTier.FORECAST
    assert not mc012.is_operational_kpi


def test_v5_t118_negative_abuse_tam_or_forecast_cannot_be_operational_kpi():
    """Negative abuse invariant:
    Unverified external benchmark or TAM projection cannot be displayed as actual LƯU NIÊN operational KPI.
    Only OBSERVED actuals can be operational KPIs.
    """
    register = default_market_claims_register

    # Attempting to mark a FORECAST or HYPOTHESIS as operational KPI must raise ValueError
    invalid_forecast = MarketClaimEvidence(
        claim_id="MC-BAD-01",
        category=MarketClaimCategory.MARKET_SIZING,
        truth_tier=TruthTier.FORECAST,
        statement="Fabricated operational claim claiming TAM as current KPI",
        metric_value="28.5B VND current platform GMV",
        date_recorded="2026-11-05",
        methodology="Unfounded projection",
        sample_size="N/A",
        source_reference="None",
        is_operational_kpi=True,  # VIOLATION!
    )
    with pytest.raises(ValueError, match="Negative abuse"):
        register.validate_claim_against_operational_kpi(invalid_forecast)

    invalid_hypothesis = MarketClaimEvidence(
        claim_id="MC-BAD-02",
        category=MarketClaimCategory.USER_BEHAVIOR,
        truth_tier=TruthTier.HYPOTHESIS,
        statement="Unproven conversion rate claimed as active KPI",
        metric_value="15% active booking conversion",
        date_recorded="2026-11-05",
        methodology="Survey test",
        sample_size="N=5",
        source_reference="None",
        is_operational_kpi=True,  # VIOLATION!
    )
    with pytest.raises(ValueError, match="Negative abuse"):
        register.validate_claim_against_operational_kpi(invalid_hypothesis)


def test_v5_t118_negative_abuse_all_registered_operational_kpis_are_observed():
    """Verify that every claim in the default register marked is_operational_kpi is strictly OBSERVED."""
    register = default_market_claims_register
    kpis = register.get_operational_kpis()
    assert len(kpis) > 0
    for kpi in kpis:
        assert kpi.truth_tier == TruthTier.OBSERVED, (
            f"Claim {kpi.claim_id} is marked as operational KPI but has tier {kpi.truth_tier}"
        )
        assert kpi.category != MarketClaimCategory.MARKET_SIZING, (
            f"TAM/SAM/SOM market sizing claim {kpi.claim_id} cannot be an operational KPI."
        )


def test_v5_t118_export_utilities_json_and_markdown():
    """Verify JSON and Markdown export formats for investor/RBPC pitch reviews."""
    register = default_market_claims_register

    # 1. JSON Export
    json_out = register.export_json()
    assert isinstance(json_out, str)
    parsed = json.loads(json_out)
    assert parsed["title"] == "LƯU NIÊN RBPC 2026 Market Claims Evidence Register"
    assert "OBSERVED" in parsed["truth_tiers_defined"]
    assert "HYPOTHESIS" in parsed["truth_tiers_defined"]
    assert "FORECAST" in parsed["truth_tiers_defined"]
    assert parsed["summary"]["total_claims"] == len(register.get_all_claims())
    assert len(parsed["claims"]) == len(register.get_all_claims())

    # 2. Markdown Export
    md_out = register.export_markdown_table()
    assert isinstance(md_out, str)
    assert "# LƯU NIÊN — Market Claims Evidence Register" in md_out
    assert "| Claim ID | Truth Tier | Category |" in md_out
    assert "`OBSERVED`" in md_out
    assert "`HYPOTHESIS`" in md_out
    assert "`FORECAST`" in md_out
    assert "Negative Abuse Guardrail Invariant" in md_out


def test_v5_t118_documentation_files_parity():
    """Verify that docs/rbpc/BUSINESS_PLAN_DRAFT.md and docs/rbpc/MARKET_CLAIMS_EVIDENCE_REGISTER.md exist and contain truth tier citations."""
    repo_root = Path(__file__).resolve().parents[2]
    bp_path = repo_root / "docs" / "rbpc" / "BUSINESS_PLAN_DRAFT.md"
    reg_path = repo_root / "docs" / "rbpc" / "MARKET_CLAIMS_EVIDENCE_REGISTER.md"

    assert bp_path.exists(), "docs/rbpc/BUSINESS_PLAN_DRAFT.md must exist"
    assert reg_path.exists(), "docs/rbpc/MARKET_CLAIMS_EVIDENCE_REGISTER.md must exist"

    bp_content = bp_path.read_text(encoding="utf-8")
    reg_content = reg_path.read_text(encoding="utf-8")

    # Business plan must reference the claim IDs and truth tiers
    assert "MC-001" in bp_content
    assert "OBSERVED" in bp_content
    assert "HYPOTHESIS" in bp_content
    assert "FORECAST" in bp_content
    assert "MC-010" in bp_content
    assert "202,360,638 VND" in bp_content

    # Market claims register must detail the methodology and sample sizes
    assert "DOC-RBPC-EVID-001" in reg_content
    assert "MC-001" in reg_content
    assert "MC-015" in reg_content
    assert "Negative Abuse Invariant & Anti-Deception Guardrail" in reg_content
