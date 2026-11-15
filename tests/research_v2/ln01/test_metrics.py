"""Metrics sanity: primary metric math, CIs finite, direction-aware errors."""
from __future__ import annotations

import pytest

from research_v2.methods.ln01.metrics import (
    direction_aware_error_rate,
    spiral_validity_rate,
)

GOLD_FAMILIES = ["accept", "reject_cycle", "reject_grade_order", "reject_missing_anchor", "reject_no_progression"]


def test_perfect_predictions_score_one_with_valid_ci():
    res = spiral_validity_rate(GOLD_FAMILIES, GOLD_FAMILIES)
    assert res["n_total"] == 5
    assert res["n_valid"] == 5
    assert res["value"] == 1.0
    lo, hi = res["wilson_ci_95"]
    assert 0.0 <= lo <= hi <= 1.0
    lo_cp, hi_cp = res["clopper_pearson_ci_95"]
    assert 0.0 <= lo_cp <= hi_cp <= 1.0
    assert res["evidence_sufficient"] is True


def test_false_accept_and_false_reject_are_reported_separately():
    decisions = ["accept", "accept", "reject_cycle", "reject_cycle", "accept"]
    gold = ["accept", "reject_cycle", "reject_cycle", "accept", "accept"]
    res = spiral_validity_rate(decisions, gold)
    # false accept: case 2 (gold reject_cycle, pred accept)
    assert res["false_accept_rate"] == 0.5  # 1 of 2 gold-reject cases
    # false reject: case 4 (gold accept, pred reject_cycle)
    assert res["false_reject_rate"] == 1 / 3  # 1 of 3 gold-accept cases
    confusion = direction_aware_error_rate(decisions, gold)["confusion_counts"]
    assert confusion["reject_cycle->accept"] == 1
    assert confusion["accept->reject_cycle"] == 1
    assert confusion["accept->accept"] == 2


def test_insufficient_evidence_flag_for_tiny_n():
    res = spiral_validity_rate(["accept"], ["accept"])
    assert res["evidence_sufficient"] is False


def test_misaligned_lengths_raise():
    with pytest.raises(ValueError, match="align"):
        spiral_validity_rate(["accept"], ["accept", "accept"])


def test_evaluate_predictions_file_end_to_end(tmp_path):
    import json

    preds = tmp_path / "preds.jsonl"
    gold = tmp_path / "gold.jsonl"
    with preds.open("w", encoding="utf-8") as fh:
        for i, d in enumerate(["accept", "reject_cycle"]):
            fh.write(json.dumps({"case_id": f"c{i}", "decision": d}) + "\n")
    with gold.open("w", encoding="utf-8") as fh:
        for i, g in enumerate(["accept", "reject_cycle"]):
            fh.write(json.dumps({"case_id": f"c{i}", "expected_decision": g}) + "\n")
    from research_v2.methods.ln01.metrics import evaluate_predictions_file

    res = evaluate_predictions_file(preds, gold)
    assert res["value"] == 1.0
