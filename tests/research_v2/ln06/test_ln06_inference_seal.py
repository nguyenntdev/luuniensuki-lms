"""Inference seal: predictions depend only on legitimate features, never gold material."""
from __future__ import annotations

import json

import pytest

from research_v2.contracts.types import ContractError, StudyInput
from research_v2.methods.ln06.dataset import load_jsonl, DATASET_PATH, TrailCase
from research_v2.methods.ln06.proposed import predict_batch, solve_case


def _inputs(rows):
    return [
        StudyInput("LN-06", r["case_id"], "test", r["group_id"],
                   {k: v for k, v in r["input"].items()})
        for r in rows
    ]


def test_oracle_keys_are_forbidden_in_study_input():
    features = {
        "stops": [{"id": "a", "cost": 1, "provides": ["o1"], "requires": []}],
        "available_stops": ["a"], "target_outcomes": ["o1"],
        "time_budget_minutes": 10, "checkpoint_claim_verified": True,
        "expected_decision": "find_valid_route",
    }
    with pytest.raises(ContractError, match="forbidden"):
        StudyInput("LN-06", "c1", "test", "g1", features)


def test_changing_only_gold_material_cannot_change_predictions(t3_dataset_paths):
    inputs_path, _ = t3_dataset_paths
    rows = load_jsonl(inputs_path)[:20]
    base = predict_batch(_inputs(rows), {})
    # Mutate every conceivable oracle-ish top-level field on the fixture rows;
    # the masked input is untouched, so predictions must be identical.
    mutated = [dict(r, expected_decision="cost_exceeded", fault_id="x",
                    cohort="ATTACK", oracle={"expected_decision": "reject_cycle"})
               for r in rows]
    after = predict_batch(_inputs(mutated), {})
    assert [p.to_dict() for p in base] == [p.to_dict() for p in after]


def test_solve_case_ignores_non_schema_feature_keys():
    features = {
        "stops": [{"id": "a", "cost": 1, "provides": ["o1"], "requires": []}],
        "available_stops": ["a"], "target_outcomes": ["o1"],
        "time_budget_minutes": 10, "checkpoint_claim_verified": True,
        "learner": {"profile_id": "x"}, "seed": 1,
    }
    case_a = TrailCase.from_features(features, case_id="x")
    features["learner"] = {"profile_id": "totally-different"}
    case_b = TrailCase.from_features(features, case_id="x")
    assert solve_case(case_a)["decision"] == solve_case(case_b)["decision"]


def test_predictions_never_carry_gold_fields(t3_dataset_paths):
    from research_v2.evaluation.metrics import FORBIDDEN_GOLD_IN_PREDICTION

    inputs_path, _ = t3_dataset_paths
    rows = load_jsonl(inputs_path)[:10]
    preds = predict_batch(_inputs(rows), {})
    for pred in preds:
        row = pred.to_dict()
        assert not (set(row) & FORBIDDEN_GOLD_IN_PREDICTION)
        assert json.dumps(row).count("expected_decision") == 0
