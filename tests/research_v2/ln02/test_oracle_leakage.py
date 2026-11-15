"""Oracle-leakage seal: gold material must never enter or affect inference."""
from __future__ import annotations

import pytest

from research_v2.contracts.types import ContractError, StudyInput
from research_v2.methods.ln02 import proposed
from ln02_helpers import (
    make_input,
    nominal_features,
)

FORBIDDEN_KEYS = [
    "oracle",
    "expected_decision",
    "expected_category",
    "gold",
    "gold_label",
    "fault_id",
    "canonical_fault",
    "cohort",
]


@pytest.mark.parametrize("key", FORBIDDEN_KEYS)
def test_top_level_oracle_key_rejected_by_contract(key):
    features = nominal_features()
    features[key] = {"expected_decision": "recommend_eligible"}
    with pytest.raises(ContractError):
        StudyInput(
            study_id="LN-02",
            case_id="leak",
            split_id="test",
            group_id="g",
            features=features,
        )


@pytest.mark.parametrize("key", FORBIDDEN_KEYS)
def test_nested_input_oracle_key_rejected_by_contract(key):
    features = nominal_features()
    features["input"] = {key: "recommend_eligible"}
    with pytest.raises(ContractError):
        StudyInput(
            study_id="LN-02",
            case_id="leak-nested",
            split_id="test",
            group_id="g",
            features=features,
        )


def test_changing_oracle_payload_only_never_alters_prediction():
    """If a forbidden key could be smuggled in, mutating it must not matter -
    here the contract rejects the input outright (fail-closed seal)."""
    base = nominal_features()
    inp_clean = make_input(features=base)
    pred_clean = proposed.predict_batch([inp_clean], {})[0]
    for key in FORBIDDEN_KEYS:
        features = nominal_features()
        features[key] = "recommend_eligible" if key != "cohort" else "A"
        with pytest.raises(ContractError):
            proposed.predict_batch(
                [make_input(case_id=f"leak-{key}", features=features)], {}
            )
    assert pred_clean.decision == "recommend_eligible"


def test_predictions_carry_no_gold_fields():
    inp = make_input()
    pred = proposed.predict_batch([inp], {})[0]
    payload = pred.to_dict()
    for key in FORBIDDEN_KEYS:
        assert key not in payload
