"""Ablation divergence: every ablation must genuinely change a code path.

15_ABLATIONS.C: an ablation that scores identically to I1 on its sensitive
stratum is NOT an ablation. Each test proves divergence on the ablation's
sensitive gold stratum, and the metrics module is checked for the paired
sensitivity axes.
"""
from __future__ import annotations

import pytest

from research_v2.contracts.types import StudyInput
from research_v2.methods.ln10.ablations import (
    a1_solve,
    a2_solve,
    a3_solve,
    predict_batch_a1,
    predict_batch_a2,
    predict_batch_a3,
)
from research_v2.methods.ln10.baselines import (
    b0_decide,
    c1_decide,
    predict_batch_b0,
    predict_batch_c1,
)
from research_v2.methods.ln10.dataset import parse_case
from research_v2.methods.ln10.proposed import decide_case, predict_batch
from tests.research_v2.ln10.ln10_helpers import (
    conflicting_edits_features,
    make_features,
    make_input,
    premature_submit_features,
    unauthorized_actor_features,
)


def _study_input(features, case_id):
    return StudyInput("LN-10", case_id, "test", f"LN-10-grp-{case_id}", features)


def test_a1_diverges_on_premature_submit_stratum(t3_inputs, t3_gold):
    premature = [r for r in t3_inputs if t3_gold[r["case_id"]] == "reject_premature_submit"]
    inputs = [_study_input(r["input"], r["case_id"]) for r in premature]
    proposed_ok = sum(
        1 for p in predict_batch(inputs, {"seed": 11}) if p.decision == "reject_premature_submit"
    )
    a1_ok = sum(
        1 for p in predict_batch_a1(inputs, {"seed": 11}) if p.decision == "reject_premature_submit"
    )
    assert proposed_ok == len(inputs)
    assert a1_ok == 0  # gate removed -> stratum silently accepted


def test_a2_diverges_on_conflict_stratum(t3_inputs, t3_gold):
    conflicts = [r for r in t3_inputs if t3_gold[r["case_id"]] == "resolve_revision_conflict"]
    inputs = [_study_input(r["input"], r["case_id"]) for r in conflicts]
    proposed_ok = sum(
        1
        for p in predict_batch(inputs, {"seed": 11})
        if p.decision == "resolve_revision_conflict"
    )
    a2_ok = sum(
        1
        for p in predict_batch_a2(inputs, {"seed": 11})
        if p.decision == "resolve_revision_conflict"
    )
    assert proposed_ok == len(inputs)
    assert a2_ok == 0


def test_a3_diverges_on_unauthorized_stratum(t3_inputs, t3_gold):
    unauthorized = [r for r in t3_inputs if t3_gold[r["case_id"]] == "deny_transition"]
    inputs = [_study_input(r["input"], r["case_id"]) for r in unauthorized]
    proposed_ok = sum(
        1 for p in predict_batch(inputs, {"seed": 11}) if p.decision == "deny_transition"
    )
    a3_ok = sum(
        1 for p in predict_batch_a3(inputs, {"seed": 11}) if p.decision == "deny_transition"
    )
    assert proposed_ok == len(inputs)
    assert a3_ok == 0


def test_c1_diverges_on_reflection_and_rationale_strata(t3_inputs, t3_gold):
    reflection = [r for r in t3_inputs if t3_gold[r["case_id"]] == "request_reflection"]
    premature = [r for r in t3_inputs if t3_gold[r["case_id"]] == "reject_premature_submit"]
    r_inputs = [_study_input(r["input"], r["case_id"]) for r in reflection]
    p_inputs = [_study_input(r["input"], r["case_id"]) for r in premature]
    assert all(
        p.decision == "request_reflection"
        for p in predict_batch(r_inputs, {"seed": 11})
    )
    assert all(
        p.decision == "allow_authorized_transition"
        for p in predict_batch_c1(r_inputs, {"seed": 11})
    )
    assert all(
        p.decision == "allow_authorized_transition"
        for p in predict_batch_c1(p_inputs, {"seed": 11})
    )


def test_b0_loses_every_gate_stratum(t3_inputs, t3_gold):
    gate_rows = [
        r
        for r in t3_inputs
        if t3_gold[r["case_id"]] != "allow_authorized_transition"
    ]
    inputs = [_study_input(r["input"], r["case_id"]) for r in gate_rows]
    preds = predict_batch_b0(inputs, {"seed": 11})
    assert all(p.decision == "allow_authorized_transition" for p in preds)


def test_ablations_keep_nominal_acceptance():
    """Ablations must not break the nominal path (divergence is gate-specific)."""
    case = parse_case("nominal-ablation", make_features())
    for solve in (a1_solve, a2_solve, a3_solve):
        assert solve(case)["decision"] == "allow_authorized_transition"


def test_conflict_stratum_not_masked_as_reflection_family():
    """Conflict detection must stay a distinct family (no label collapsing)."""
    case = parse_case("conflict-family", conflicting_edits_features())
    result = decide_case(case)
    assert result["decision"] == "resolve_revision_conflict"
    assert result["decision"] not in ("request_reflection", "deny_transition")


def test_metrics_axes_are_sensitive(t3_inputs, t3_gold):
    from research_v2.methods.ln10.metrics import summarize

    rows = [
        {"case_id": r["case_id"], "decision": p.decision}
        for r, p in zip(
            t3_inputs,
            predict_batch(
                [_study_input(r["input"], r["case_id"]) for r in t3_inputs],
                {"seed": 11},
            ),
        )
    ]
    summary = summarize(rows, t3_gold)
    assert summary["false_acceptance"]["rate"] == 0.0
    assert summary["false_rejection"]["rate"] == 0.0
    assert summary["conflict_detection"]["rate"] == 1.0
    assert summary["reflection_gate_enforcement"]["rate"] == 1.0


def test_baselines_share_label_space_with_proposed():
    """Comparability: all methods emit native labels, never foreign vocab."""
    from research_v2.methods.ln10.labels import NATIVE_DECISIONS

    scenarios = [
        make_features(),
        conflicting_edits_features(),
        premature_submit_features(),
        unauthorized_actor_features(),
    ]
    for feats in scenarios:
        case = parse_case("labels-check", feats)
        for decide in (b0_decide, c1_decide):
            assert decide(case)["decision"] in NATIVE_DECISIONS
        for solve in (a1_solve, a2_solve, a3_solve):
            assert solve(case)["decision"] in NATIVE_DECISIONS
