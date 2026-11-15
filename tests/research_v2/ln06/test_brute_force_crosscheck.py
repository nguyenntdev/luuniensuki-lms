"""Brute-force cross-check of the proposed policy against the independent rubric oracle."""
from __future__ import annotations

import pytest

from research_v2.methods.ln06.dataset import load_jsonl, DATASET_PATH
from research_v2.methods.ln06.proposed import solve_case
from research_v2.methods.ln06.rubric import brute_force_expected_decision, score_prediction
from research_v2.methods.ln06.stress_generator import STRESS_FAMILIES, generate_stress_case


def test_all_t3_cases_match_brute_force_oracle():
    rows = load_jsonl(DATASET_PATH)
    mismatches = []
    for row in rows:
        case = __import__(
            "research_v2.methods.ln06.dataset", fromlist=["TrailCase"]
        ).TrailCase.from_features(row["input"], case_id=str(row["case_id"]))
        expected = brute_force_expected_decision(case)
        actual = solve_case(case)["decision"]
        if expected != actual:
            mismatches.append((case.case_id, actual, expected))
    assert not mismatches, f"proposed vs oracle mismatches: {mismatches[:5]}"


def test_sealed_gold_agrees_with_brute_force_oracle(t3_dataset_paths):
    _, gold_path = t3_dataset_paths
    rows = load_jsonl(DATASET_PATH)
    gold = {
        row["case_id"]: row["expected_decision"] for row in load_jsonl(gold_path)
    }
    assert len(gold) == 120
    for row in rows:
        case = __import__(
            "research_v2.methods.ln06.dataset", fromlist=["TrailCase"]
        ).TrailCase.from_features(row["input"], case_id=str(row["case_id"]))
        assert brute_force_expected_decision(case) == gold[case.case_id], case.case_id


@pytest.mark.parametrize("family", STRESS_FAMILIES)
def test_stress_families_match_brute_force_oracle(family):
    for i in range(1, 4):
        scenario = generate_stress_case(family, seed=11, case_index=i)
        case = __import__(
            "research_v2.methods.ln06.dataset", fromlist=["TrailCase"]
        ).TrailCase.from_features(scenario, case_id=str(scenario["case_id"]))
        expected = brute_force_expected_decision(case)
        actual = solve_case(case)["decision"]
        assert actual == expected, f"{case.case_id}: proposed={actual} oracle={expected}"


def test_score_prediction_error_taxonomy():
    row = score_prediction("no_feasible_route", "find_valid_route")
    assert row["error_class"] == "false_infeasibility"
    assert row["correct"] is False
    row = score_prediction("find_valid_route", "cost_exceeded")
    assert row["error_class"] == "false_acceptance"
    row = score_prediction("reject_cycle", "cost_exceeded")
    assert row["error_class"] == "wrong_rejection_reason"
    row = score_prediction("find_valid_route", "find_valid_route")
    assert row["correct"] is True and row["error_class"] is None
