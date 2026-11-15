"""Invalid inputs must raise typed failures, never silent guessed fallbacks."""
from __future__ import annotations

import pytest

from research_v2.contracts.types import ContractError, StudyInput
from research_v2.methods.ln01.proposed import predict_batch as proposed_batch
from research_v2.methods.ln01.baselines import predict_batch_b0, predict_batch_c1
from research_v2.methods.ln01 import ablations

from ln01_helpers import make_features, make_input


def test_oracle_leakage_rejected_by_contract():
    with pytest.raises(ContractError, match="forbidden"):
        StudyInput("LN-01", "leak", "test", "g", {"oracle": {"expected_decision": "accept"}})


def test_expected_decision_nested_in_input_rejected():
    with pytest.raises(ContractError, match="forbidden|nested"):
        StudyInput("LN-01", "leak2", "test", "g", {"input": {"expected_decision": "accept"}})


@pytest.mark.parametrize("fn", [proposed_batch, predict_batch_b0, predict_batch_c1, ablations.predict_batch])
def test_missing_nodes_raises_typed_error(fn):
    features = {"prerequisites": [[0, 1]], "curriculum_anchor": {}}
    with pytest.raises(ContractError, match="nodes"):
        fn([StudyInput("LN-01", "bad-nodes", "test", "g", features)], {})


@pytest.mark.parametrize("fn", [proposed_batch, predict_batch_c1])
def test_edge_references_unknown_node_raises(fn):
    features = make_features(prerequisites=[[0, 9]])
    with pytest.raises(ContractError, match="unknown node index"):
        fn([StudyInput("LN-01", "bad-edge", "test", "g", features)], {})


@pytest.mark.parametrize("fn", [proposed_batch, predict_batch_b0])
def test_malformed_node_raises(fn):
    features = make_features()
    features["nodes"][2] = {"grade": "eleven"}
    with pytest.raises(ContractError, match="node 2"):
        fn([StudyInput("LN-01", "bad-node", "test", "g", features)], {})


def test_non_integer_edge_raises():
    features = make_features(prerequisites=[[0, "one"]])
    with pytest.raises(ContractError, match="non-integer"):
        proposed_batch([StudyInput("LN-01", "bad-edge2", "test", "g", features)], {})


def test_b0_empty_node_set_raises_not_silent_accept():
    features = make_features(nodes=[], prerequisites=[])
    with pytest.raises(ValueError, match="empty node set"):
        predict_batch_b0([StudyInput("LN-01", "empty", "test", "g", features)], {})
