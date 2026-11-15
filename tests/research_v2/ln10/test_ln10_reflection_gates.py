"""Reflection-gate tests: skip-reflection -> require/reject, never apply.

Mandatory case 2 (project completion with no reflection) and case 4 (empty
reflection text with flag claims) plus the rationale gate (missing
forethought rationale blocks the transition).
"""
from __future__ import annotations

from tests.research_v2.ln10.ln10_helpers import (
    make_features,
    make_input,
    missing_rationale_features,
    premature_submit_features,
)
from research_v2.methods.ln10.ablations import a1_solve
from research_v2.methods.ln10.baselines import c1_decide
from research_v2.methods.ln10.dataset import parse_case
from research_v2.methods.ln10.proposed import decide_case, predict_batch


def test_submit_without_reflection_is_rejected_premature():
    inp = make_input(premature_submit_features(), case_id="premature-submit")
    pred = predict_batch([inp], {"seed": 11})[0]
    assert pred.decision == "reject_premature_submit"
    assert "skipped_reflection" in pred.reason_codes
    assert pred.score == 0.0


def test_empty_reflection_text_with_flag_claims_still_gated():
    """reflection_completed=True but rationale text empty -> revision still gated."""
    features = make_features(
        transition={
            "action": "revise_plan",
            "expected_version": 3,
            "new_goal": "heritage_learning_campaign",
            "rationale": "   ",
        },
    )
    case = parse_case("empty-text-flags", features)
    result = decide_case(case)
    assert result["decision"] == "request_reflection"
    assert "missing_rationale" in result["reason_codes"]


def test_missing_rationale_blocks_transition():
    inp = make_input(missing_rationale_features(), case_id="missing-rationale")
    pred = predict_batch([inp], {"seed": 11})[0]
    assert pred.decision == "request_reflection"
    assert "missing_rationale" in pred.reason_codes


def test_reflection_gate_respects_legitimate_stage_repeat():
    """False-rejection protection: same owner re-observing the stage is legal."""
    case = parse_case("stage-repeat", make_features())
    result = decide_case(case)
    assert result["decision"] == "allow_authorized_transition"


def test_a1_ablation_applies_premature_submit():
    """Removing the reflection gate makes the ablation apply the submission."""
    case = parse_case("premature-a1", premature_submit_features())
    result = a1_solve(case)
    assert result["decision"] == "allow_authorized_transition"
    assert "reflection_gate_disabled" in result["reason_codes"]


def test_c1_baseline_has_no_reflection_gate():
    case = parse_case("premature-c1", premature_submit_features())
    result = c1_decide(case)
    assert result["decision"] == "allow_authorized_transition"
