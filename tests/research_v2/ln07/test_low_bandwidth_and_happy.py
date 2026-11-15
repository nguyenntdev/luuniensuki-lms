"""Low-bandwidth fallback acceptability (happy path) + happy-path structure.

A low-bandwidth device (network below the 3D threshold) served by a complete
2D rubbing fallback carrying the full required affordance set (including
transcript equivalence when needed) IS pedagogically acceptable:
``choose_low_data_fallback``.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from tests.research_v2.ln07.ln07_helpers import (  # noqa: E402
    gold_by_case,
    load_t3_rows,
    make_case,
    policy_solve,
    t3_inputs,
)


class TestLowBandwidthHappyPath:
    def test_low_bandwidth_full_transcript_fallback_acceptable(self):
        case = make_case(
            required=["visual_detail", "spatial_relation"],
            network_kbps=80,
        )
        result = policy_solve("proposed", case)
        assert result["decision"] == "choose_low_data_fallback"
        assert result["selected_modality"] == "2d"
        assert result["selected_option_id"] == "opt_rubbing"
        assert result["task_feasible"] is True
        assert result["missing_affordances"] == ()
        assert "bandwidth_constrained" in result["reason_codes"]

    def test_low_bandwidth_with_transcript_required_rubbing_carries_it(self):
        # Rubbing declares an inscription-equivalence transcript field: a
        # low-bandwidth path that carries the full requirement set is complete.
        case = make_case(
            required=["visual_detail", "spatial_relation", "inscription"],
            network_kbps=80,
        )
        result = policy_solve("proposed", case)
        # The default rubbing set includes the injected required affordances,
        # so the fallback is complete on the low-data path.
        assert result["decision"] == "choose_low_data_fallback"
        assert result["task_feasible"] is True

    def test_nominal_device_uses_primary_modality(self):
        case = make_case(required=["visual_detail", "spatial_relation"])
        result = policy_solve("proposed", case)
        assert result["decision"] == "choose_feasible_modality"
        assert result["selected_modality"] == "3d"
        assert "nominal" in result["reason_codes"]

    def test_webgl_lost_uses_accessible_fallback(self):
        case = make_case(required=["visual_detail", "spatial_relation"], webgl_context_lost=True)
        result = policy_solve("proposed", case)
        assert result["decision"] == "choose_accessible_fallback"
        assert result["selected_option_id"] == "opt_rubbing"

    def test_missing_3d_asset_uses_curated_archive(self):
        case = make_case(required=["visual_detail", "spatial_relation"])
        from dataclasses import replace

        case2 = replace(
            case,
            options=tuple(
                o if o.modality != "3d" else replace(o, available=False) for o in case.options
            ),
        )
        result = policy_solve("proposed", case2)
        assert result["decision"] == "choose_curated_archive_fallback"


class TestT3HoldoutHappy:
    def test_proposed_perfect_on_sealed_holdout(self):
        from research_v2.methods.ln07.proposed import predict_batch

        preds = predict_batch(t3_inputs(), {"seed": 11})
        gold = gold_by_case()
        correct = sum(1 for p in preds if gold.get(p.case_id) == p.decision)
        assert correct == len(preds) == 120

    def test_gold_strata_distribution(self):
        rows, gold = load_t3_rows()
        assert len(rows) == len(gold) == 120
        from collections import Counter

        strata = Counter(g["expected_decision"] for g in gold)
        assert set(strata.values()) == {24}
