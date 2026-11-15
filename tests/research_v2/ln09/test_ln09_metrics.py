"""Metrics: primary metric math, vocabulary bridge, CIs finite, direction-aware
errors, k-anonymity suppression rate, evaluator file pairing."""
from __future__ import annotations

import json

import pytest

from research_v2.methods.ln09.metrics import (
    GOLD_TO_V2_LABEL,
    actionable_recommendation_precision,
    direction_aware_error_rate,
    evaluate_predictions_file,
    finite_json_safe,
    k_anonymity_suppression_rate,
    to_v2_label,
)

GOLD_FAMILIES = [
    "propose_explained_action",
    "abstain_missing_evidence",
    "abstain_conflict",
    "abstain_unverified_source",
    "request_refresh",
    "descriptive_summary_only",
]


def test_perfect_predictions_score_one_with_valid_ci():
    res = actionable_recommendation_precision(GOLD_FAMILIES, GOLD_FAMILIES)
    assert res["n_total"] == 6
    assert res["n_valid"] == 6
    assert res["value"] == 1.0
    lo, hi = res["wilson_ci_95"]
    assert 0.0 <= lo <= hi <= 1.0
    assert res["evidence_sufficient"] is True


def test_false_accept_captures_deficit_inference_violation():
    """Proposing an action where gold abstains (the mandatory counterexample)
    counts as a false accept on the gold-reject denominator."""
    decisions = ["propose_explained_action", "propose_explained_action", "abstain_conflict", "request_refresh", "descriptive_summary_only", "descriptive_summary_only"]
    gold = ["propose_explained_action", "abstain_missing_evidence", "abstain_conflict", "request_refresh", "abstain_unverified_source", "descriptive_summary_only"]
    res = actionable_recommendation_precision(decisions, gold)
    assert res["n_valid"] == 4
    assert res["n_gold_reject"] == 5
    # One deficit inference from missing logs.
    assert res["false_accept_rate"] == pytest.approx(1 / 5)
    assert res["false_reject_rate"] == 0.0


def test_false_reject_reported_separately():
    decisions = ["abstain_missing_evidence", "abstain_missing_evidence", "abstain_conflict"]
    gold = ["propose_explained_action", "abstain_missing_evidence", "abstain_conflict"]
    res = actionable_recommendation_precision(decisions, gold)
    assert res["n_gold_accept"] == 1
    assert res["false_reject_rate"] == 1.0
    assert res["false_accept_rate"] == 0.0


def test_unknown_label_raises_never_silent():
    with pytest.raises(ValueError, match="unknown LN-09 decision label"):
        actionable_recommendation_precision(["accept"], ["accept"])
    with pytest.raises(ValueError, match="unknown LN-09 decision label"):
        to_v2_label("sort_of_abstain")


def test_gold_to_v2_bridge_is_total_and_deterministic():
    for legacy in GOLD_FAMILIES:
        mapped = to_v2_label(legacy)
        assert mapped in {"recommend_action", "descriptive_only", "abstain_insufficient_data", "require_teacher_override"}
    assert to_v2_label("propose_explained_action") == "recommend_action"
    assert to_v2_label("abstain_missing_evidence") == "abstain_insufficient_data"


def test_misaligned_lengths_raise():
    with pytest.raises(ValueError, match="align"):
        actionable_recommendation_precision(["propose_explained_action"], ["propose_explained_action"] * 2)


def test_insufficient_evidence_flag_for_tiny_n():
    res = actionable_recommendation_precision(["propose_explained_action"], ["propose_explained_action"])
    assert res["evidence_sufficient"] is False


def test_k_anonymity_suppression_rate():
    res = k_anonymity_suppression_rate(["descriptive_summary_only", "propose_explained_action", "descriptive_summary_only"])
    assert res["n_total"] == 3
    assert res["n_suppressed"] == 2
    assert res["value"] == pytest.approx(2 / 3)


def test_confusion_distinguishes_all_families():
    decisions = ["propose_explained_action", "abstain_missing_evidence", "descriptive_summary_only"]
    gold = ["abstain_missing_evidence", "abstain_missing_evidence", "propose_explained_action"]
    confusion = direction_aware_error_rate(decisions, gold)["confusion_counts"]
    assert confusion["abstain_missing_evidence->propose_explained_action"] == 1
    assert confusion["abstain_missing_evidence->abstain_missing_evidence"] == 1
    assert confusion["propose_explained_action->descriptive_summary_only"] == 1


def test_evaluate_predictions_file_end_to_end(tmp_path):
    preds = tmp_path / "preds.jsonl"
    gold = tmp_path / "gold.jsonl"
    with preds.open("w", encoding="utf-8") as fh:
        for i, d in enumerate(["propose_explained_action", "abstain_missing_evidence"]):
            fh.write(json.dumps({"case_id": f"c{i}", "decision": d}) + "\n")
    with gold.open("w", encoding="utf-8") as fh:
        for i, g in enumerate(["propose_explained_action", "abstain_missing_evidence"]):
            fh.write(json.dumps({"case_id": f"c{i}", "expected_decision": g}) + "\n")
    res = evaluate_predictions_file(preds, gold)
    assert res["value"] == 1.0
    assert finite_json_safe(res)


def test_metrics_result_finite_json_safe():
    res = actionable_recommendation_precision(GOLD_FAMILIES, GOLD_FAMILIES)
    assert finite_json_safe(res)
