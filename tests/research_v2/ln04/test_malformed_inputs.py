"""Malformed-input handling: typed failures, never silent defaults (LN-04)."""
from __future__ import annotations

import pytest

from methods_helpers import verified_nominal_features
from research_v2.contracts.types import ContractError, StudyInput
from research_v2.methods.ln04 import proposed


def _case(features: dict, case_id: str = "LN-04-TEST-INV") -> StudyInput:
    return StudyInput(
        study_id="LN-04", case_id=case_id, split_id="test", group_id="grp-inv", features=features
    )


def test_missing_study_id_rejected_by_contract():
    with pytest.raises(ContractError):
        StudyInput(
            study_id="",
            case_id="c",
            split_id="test",
            group_id="g",
            features=verified_nominal_features(),
        )


def test_wrong_study_prefix_rejected():
    with pytest.raises(ContractError):
        StudyInput(
            study_id="XX-99",
            case_id="c",
            split_id="test",
            group_id="g",
            features=verified_nominal_features(),
        )


def test_empty_features_degrade_fail_closed_not_crash():
    pred = proposed.predict_one(_case({}))
    # No question, no retrieval -> fail-closed abstention, not a fabricated hint.
    assert pred.decision == "abstain_insufficient_source"


def test_malformed_hint_level_falls_back_deterministically():
    features = verified_nominal_features(task={"hint_level": "not-a-number"})
    pred = proposed.predict_one(_case(features))
    assert pred.decision == "socratic_question"
    assert "hint_level_1" in pred.reason_codes


def test_forbidden_gold_key_nested_deep_is_rejected():
    with pytest.raises(ContractError):
        StudyInput(
            study_id="LN-04",
            case_id="c-deep",
            split_id="test",
            group_id="g",
            features={**verified_nominal_features(), "input": {"label": "hint"}},
        )


def test_batch_length_contract():
    rows = [_case(verified_nominal_features(), f"c-{i}") for i in range(4)]
    preds = proposed.predict_batch(rows)
    assert len(preds) == len(rows)
