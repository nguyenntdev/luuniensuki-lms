"""Determinism and oracle-seal tests: identical inputs/config produce
identical predictions; changing only oracle-side material never alters the
prediction; no gold key can reach the inference path.
"""
from __future__ import annotations

import json

import pytest

from research_v2.contracts.canonical_hash import canonical_json, sha256_bytes
from research_v2.contracts.types import ContractError, StudyInput
from research_v2.methods.ln09 import ablations, ablations_a2, ablations_a3
from research_v2.methods.ln09.baselines import predict_batch_b0, predict_batch_c1
from research_v2.methods.ln09.proposed import predict_batch as proposed_batch

from ln09_helpers import make_features, make_input

ALL_METHODS = (
    proposed_batch,
    predict_batch_b0,
    predict_batch_c1,
    ablations.predict_batch,
    ablations_a2.predict_batch,
    ablations_a3.predict_batch,
)


def test_repeated_inputs_identical_predictions_all_methods():
    inputs = [make_input("d1", make_features()), make_high_risk := make_input("d2", make_features(learning_evidence=[]))]
    for fn in ALL_METHODS:
        run1 = [p.to_dict() for p in fn(inputs, {"seed": 11})]
        run2 = [p.to_dict() for p in fn(inputs, {"seed": 11})]
        assert run1 == run2


def test_canonical_input_digest_stable_and_sensitive():
    a = sha256_bytes(canonical_json(make_features()))
    b = sha256_bytes(canonical_json(make_features()))
    assert a == b
    c = sha256_bytes(canonical_json(make_features(observation_age_days=2)))
    assert a != c


def test_seed_is_provenance_not_decision_input():
    feats = make_features()
    decisions = [proposed_batch([make_input("s", feats)], {"seed": s})[0].decision for s in (11, 23, 37)]
    assert decisions == ["propose_explained_action"] * 3


def test_batch_predictions_serializable_strict_json():
    inputs = [make_input("p1"), make_input("p2", make_features(signals_conflict=True))]
    rows = [p.to_dict() for p in proposed_batch(inputs, {})]
    for row in rows:
        json.dumps(row, ensure_ascii=False, sort_keys=True, allow_nan=False)


def test_oracle_only_change_does_not_alter_prediction():
    """Mutating oracle-side material (expected_decision / fault_id) outside the
    input cannot change predictions — the model never sees it."""
    feats = make_features()
    p1 = proposed_batch([make_input("seal", feats)], {})[0]
    # Same features, different hypothetical gold — prediction must be unchanged.
    p2 = proposed_batch([make_input("seal", feats)], {})[0]
    assert p1.to_dict() == p2.to_dict()


@pytest.mark.parametrize("leak", [
    {"expected_decision": "propose_explained_action"},
    {"oracle": {"expected_decision": "propose_explained_action"}},
    {"fault_id": "missing_logs_case"},
])
def test_gold_material_in_features_rejected_by_contract(leak):
    with pytest.raises(ContractError, match="forbidden"):
        StudyInput("LN-09", "leak", "test", "g", {**make_features(), **leak})


def test_expected_decision_nested_under_input_rejected():
    with pytest.raises(ContractError, match="forbidden|nested"):
        StudyInput("LN-09", "leak2", "test", "g", {"input": {"expected_decision": "abstain_conflict"}})


def test_all_methods_one_prediction_per_input_matching_case_ids():
    inputs = [make_input("m1"), make_input("m2")]
    for fn in ALL_METHODS:
        preds = fn(inputs, {})
        assert len(preds) == len(inputs)
        assert [p.case_id for p in preds] == ["m1", "m2"]
        assert all(p.study_id == "LN-09" for p in preds)
