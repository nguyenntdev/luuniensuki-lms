"""Typed failures on malformed inputs - never silent defaults."""
from __future__ import annotations

import pytest

from research_v2.contracts.types import ContractError, StudyInput
from research_v2.methods.ln02 import proposed
from research_v2.methods.ln02.baselines_b0 import predict_batch as b0
from research_v2.methods.ln02.baselines_c1 import predict_batch as c1
from research_v2.methods.ln02.ablations_a1 import predict_batch as a1
from research_v2.methods.ln02.ablations_a2 import predict_batch as a2
from research_v2.methods.ln02.ablations_a3 import predict_batch as a3
from research_v2.methods.ln02.core import MethodContractError
from ln02_helpers import make_input

DAG_AWARE_METHODS = [proposed.predict_batch, a1, a2, a3]
ALL_METHODS = [proposed.predict_batch, b0, c1, a1, a2, a3]


def test_non_mapping_features_rejected():
    """The frozen contract crashes on list-features (AttributeError from
    ``StudyInput.__post_init__``); the method layer must reject them with a
    typed MethodContractError before any decision is made."""
    with pytest.raises((ContractError, AttributeError)):
        StudyInput(
            study_id="LN-02",
            case_id="bad",
            split_id="test",
            group_id="g",
            features=["not", "a", "mapping"],  # type: ignore[arg-type]
        )
    shim = StudyInput(
        study_id="LN-02",
        case_id="bad-shim",
        split_id="test",
        group_id="g",
        features={"stub": True},  # constructible placeholder
    )
    bad = StudyInput(
        study_id=shim.study_id,
        case_id="bad",
        split_id="test",
        group_id="g",
        features=shim.features,
    )
    object.__setattr__(bad, "features", ["not", "a", "mapping"])
    with pytest.raises(MethodContractError):
        proposed.predict_batch([bad], {})
    with pytest.raises(MethodContractError):
        b0([bad], {})


@pytest.mark.parametrize("predict_batch", ALL_METHODS)
def test_non_list_batch_rejected(predict_batch):
    with pytest.raises(MethodContractError):
        predict_batch({"case_id": "x"}, {})  # type: ignore[arg-type]


@pytest.mark.parametrize("predict_batch", DAG_AWARE_METHODS)
def test_malformed_graph_edges_rejected(predict_batch):
    inp = make_input()
    features = dict(inp.features)
    features["graph_edges"] = [["only-one-element"]]
    broken = StudyInput(
        study_id=inp.study_id,
        case_id=inp.case_id,
        split_id=inp.split_id,
        group_id=inp.group_id,
        features=features,
    )
    with pytest.raises(MethodContractError):
        predict_batch([broken], {})


@pytest.mark.parametrize("predict_batch", ALL_METHODS)
def test_malformed_target_task_rejected(predict_batch):
    inp = make_input()
    features = dict(inp.features)
    features["target_task"] = "not-a-mapping"
    broken = StudyInput(
        study_id=inp.study_id,
        case_id=inp.case_id,
        split_id=inp.split_id,
        group_id=inp.group_id,
        features=features,
    )
    with pytest.raises(MethodContractError):
        predict_batch([broken], {})


@pytest.mark.parametrize("predict_batch", ALL_METHODS)
def test_malformed_mastery_rejected(predict_batch):
    inp = make_input()
    features = dict(inp.features)
    features["mastery"] = [0.5, 0.6]
    broken = StudyInput(
        study_id=inp.study_id,
        case_id=inp.case_id,
        split_id=inp.split_id,
        group_id=inp.group_id,
        features=features,
    )
    with pytest.raises(MethodContractError):
        predict_batch([broken], {})


@pytest.mark.parametrize("predict_batch", ALL_METHODS)
def test_malformed_prerequisites_rejected(predict_batch):
    inp = make_input()
    features = dict(inp.features)
    features["target_task"] = {"id": "t", "prerequisites": ["S1"]}
    broken = StudyInput(
        study_id=inp.study_id,
        case_id=inp.case_id,
        split_id=inp.split_id,
        group_id=inp.group_id,
        features=features,
    )
    with pytest.raises(MethodContractError):
        predict_batch([broken], {})


def test_invalid_config_values_rejected():
    inp = make_input()
    with pytest.raises(MethodContractError):
        proposed.predict_batch([inp], {"mastery_uncertainty_eps": "high"})
    with pytest.raises(MethodContractError):
        proposed.predict_batch([inp], {"mastery_uncertainty_eps": 1.5})
    with pytest.raises(MethodContractError):
        b0([inp], {"aggregate_score_threshold": "zero-point-five"})
    with pytest.raises(MethodContractError):
        b0([inp], {"aggregate_score_threshold": 42.0})


def test_baselines_ignore_malformed_graph_edges_by_scope():
    """B0/C1 are DAG-blind by classical scope; malformed edges are inert
    (never read) rather than a silent validity check - documented behaviour."""
    inp = make_input()
    features = dict(inp.features)
    features["graph_edges"] = [["only-one-element"]]
    broken = StudyInput(
        study_id=inp.study_id,
        case_id=inp.case_id,
        split_id=inp.split_id,
        group_id=inp.group_id,
        features=features,
    )
    for predict_batch in (b0, c1):
        pred = predict_batch([broken], {})[0]
        assert pred.decision in ("recommend_eligible", "remediate_first")


def test_proposed_rejects_unknown_score_field_config():
    inp = make_input()
    with pytest.raises(MethodContractError):
        proposed.predict_batch([inp], {"score_field": "score_observed_v2"})


def test_ablation_variant_dispatch_validated():
    inp = make_input()
    from research_v2.methods.ln02 import ablations

    with pytest.raises(MethodContractError):
        ablations.predict_batch([inp], {"variant": "not-a-variant"})
