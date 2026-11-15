"""Contract tests for Research V2 frozen types, hashing, masking and labels."""
from __future__ import annotations

import json

import pytest

from research_v2.contracts.canonical_hash import (
    STANDARD_NAME,
    canonical_json,
    sha256_input,
    verify_input_hash,
)
from research_v2.contracts.input_masking import mask_case_input
from research_v2.contracts.label_space import (
    LabelSpaceError,
    validate_decision,
    validate_oracle_basis,
)
from research_v2.contracts.types import ContractError, StudyInput, StudyPrediction


def test_canonical_hash_is_stable_and_standard_named():
    obj = {"b": 1, "a": [1, 2, {"z": "ế"}]}
    assert sha256_input(obj) == sha256_input({"a": [1, 2, {"z": "ế"}], "b": 1})
    assert STANDARD_NAME == "sha256(sort_keys,compact,utf8)"
    assert canonical_json(obj).startswith(b"{")


def test_verify_input_hash_detects_tampering():
    rec = {"input": {"x": 1}, "input_hash": sha256_input({"x": 1})}
    verify_input_hash(rec)
    rec["input"]["x"] = 2
    with pytest.raises(ValueError, match="stale input_hash"):
        verify_input_hash(rec)


def test_canonical_json_rejects_nan_and_infinity():
    with pytest.raises(ValueError):
        canonical_json({"x": float("inf")})


def test_study_input_rejects_oracle_leakage():
    with pytest.raises(ContractError, match="forbidden"):
        StudyInput("LN-06", "c1", "test", "g1", {"oracle": {"expected_decision": "x"}})
    with pytest.raises(ContractError, match="forbidden"):
        StudyInput("LN-06", "c1", "test", "g1", {"input": {"expected_decision": "x"}})


def test_study_input_accepts_clean_features():
    si = StudyInput("LN-06", "c1", "test", "g1", {"budget": 50, "stops": ["a", "b"]})
    assert si.to_dict()["case_id"] == "c1"
    pred = StudyPrediction("LN-06", "c1", "find_valid_route", 1.0, ("nominal",), ())
    assert pred.to_dict()["decision"] == "find_valid_route"


def test_mask_case_input_strips_gold_material():
    row = {
        "input": {"budget": 50, "oracle": {"x": 1}, "fault_id": "f"},
        "oracle": {"expected_decision": "find_valid_route"},
        "expected_decision": "find_valid_route",
        "annotation_provenance": "PROGRAMMATIC_TEMPLATE_NO_HUMAN_ADJUDICATION",
    }
    masked = mask_case_input(row)
    assert masked == {"budget": 50}


def test_label_space_validation():
    validate_decision("LN-06", "find_valid_route")
    with pytest.raises(LabelSpaceError):
        validate_decision("LN-06", "totally_made_up")
    validate_oracle_basis("PEDAGOGICAL_DAG_CONSTRAINTS")
    with pytest.raises(LabelSpaceError):
        validate_oracle_basis("HUMAN_EXPERT_CONSENSUS")
