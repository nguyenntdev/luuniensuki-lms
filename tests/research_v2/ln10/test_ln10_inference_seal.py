"""Inference seal: predictions depend only on legitimate features, never gold."""
from __future__ import annotations

import json

import pytest

from research_v2.contracts.types import ContractError, StudyInput
from research_v2.methods.ln10.proposed import predict_batch
from tests.research_v2.ln10.ln10_helpers import (
    make_features,
    make_input,
)


def _inputs(rows):
    return [
        StudyInput("LN-10", r["case_id"], "test", r["group_id"], r["input"])
        for r in rows
    ]


def test_oracle_keys_are_forbidden_in_study_input():
    features = make_features(expected_decision="allow_authorized_transition")
    with pytest.raises(ContractError, match="forbidden"):
        make_input(features, case_id="leak-1")


def test_nested_oracle_keys_are_forbidden():
    features = make_features()
    features["input"] = {"expected_decision": "deny_transition"}
    with pytest.raises(ContractError, match="forbidden"):
        make_input(features, case_id="leak-2")


def test_changing_only_gold_material_cannot_change_predictions(t3_inputs):
    rows = t3_inputs[:20]
    base = [p.to_dict() for p in predict_batch(_inputs(rows), {"seed": 11})]
    mutated = [
        dict(
            r,
            expected_decision="deny_transition",
            fault_id="x",
            cohort="ATTACK",
            oracle={"expected_decision": "resolve_revision_conflict"},
        )
        for r in rows
    ]
    after = [p.to_dict() for p in predict_batch(_inputs(mutated), {"seed": 11})]
    assert after == base


def test_predictions_never_carry_gold_fields(t3_inputs):
    from research_v2.evaluation.metrics import FORBIDDEN_GOLD_IN_PREDICTION

    rows = t3_inputs[:10]
    preds = predict_batch(_inputs(rows), {"seed": 11})
    for pred in preds:
        row = pred.to_dict()
        assert not (set(row) & FORBIDDEN_GOLD_IN_PREDICTION)
        assert json.dumps(row).count("expected_decision") == 0


def test_non_schema_feature_keys_do_not_affect_decisions():
    feats_a = make_features(learner={"profile_id": "SYN-NOVICE"}, seed=1)
    feats_b = make_features(learner={"profile_id": "SYN-ADVANCED"}, seed=2)
    assert (
        predict_batch([make_input(feats_a, case_id="x")], {"seed": 11})[0].to_dict()
        == predict_batch([make_input(feats_b, case_id="x")], {"seed": 11})[0].to_dict()
    )
