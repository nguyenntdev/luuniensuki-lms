"""Hard-gate semantics: unobserved dimensions abstain, cycles are rejected,
invalid scores are rejected - for every runner method."""
from __future__ import annotations

import pytest

from research_v2.methods.ln02 import ablations, proposed
from research_v2.methods.ln02.baselines_b0 import predict_batch as b0
from research_v2.methods.ln02.baselines_c1 import predict_batch as c1
from ln02_helpers import (
    cyclic_graph_features,
    invalid_score_features,
    make_input,
    unobserved_dimension_features,
)


def test_proposed_abstains_on_unobserved_required_dimension():
    inp = make_input(features=unobserved_dimension_features())
    pred = proposed.predict_batch([inp], {})[0]
    assert pred.decision == "abstain_insufficient_data"
    assert any("UNOBSERVED_DIMENSION:S2" in rc for rc in pred.reason_codes)
    # never guess: an unobserved skill is not zero and not one
    assert pred.decision != "recommend_eligible"
    assert pred.decision != "remediate_first"


def test_proposed_rejects_cycle():
    inp = make_input(features=cyclic_graph_features())
    pred = proposed.predict_batch([inp], {})[0]
    assert pred.decision == "reject_cycle"
    assert pred.reason_codes[0] == "CYCLE_DETECTED"


def test_proposed_rejects_invalid_score():
    inp = make_input(features=invalid_score_features())
    pred = proposed.predict_batch([inp], {})[0]
    assert pred.decision == "reject_invalid_score"
    assert pred.reason_codes[0] == "INVALID_SCORE_RANGE"


def test_cycle_priority_over_invalid_score():
    features = invalid_score_features()
    features["graph_edges"] = [["a", "b"], ["b", "a"]]
    inp = make_input(features=features)
    pred = proposed.predict_batch([inp], {})[0]
    assert pred.decision == "reject_cycle"


def test_invalid_mastery_value_rejected():
    features = unobserved_dimension_features()
    features["mastery"]["S1"] = 12.5
    features["learner"]["competencies"]["S1"] = 12.5
    inp = make_input(features=features)
    pred = proposed.predict_batch([inp], {})[0]
    assert pred.decision == "reject_invalid_score"


@pytest.mark.parametrize(
    "predict_batch",
    [proposed.predict_batch, ablations.predict_a1_batch, ablations.predict_a2_batch, ablations.predict_a3_batch],
)
def test_all_vector_methods_reject_cycle(predict_batch):
    inp = make_input(features=cyclic_graph_features())
    assert predict_batch([inp], {})[0].decision == "reject_cycle"


@pytest.mark.parametrize(
    "predict_batch",
    [proposed.predict_batch, ablations.predict_a1_batch, ablations.predict_a2_batch, ablations.predict_a3_batch],
)
def test_all_vector_methods_reject_invalid_score(predict_batch):
    inp = make_input(features=invalid_score_features())
    assert predict_batch([inp], {})[0].decision == "reject_invalid_score"


def test_classical_baselines_are_deliberately_dag_blind():
    """C1/B0 scope note (spec 12): unidimensional models never read the DAG;
    they still reject the measurement-invalid score (MLE undefined)."""
    cyc_inp = make_input(features=cyclic_graph_features())
    assert c1([cyc_inp], {})[0].decision == "recommend_eligible"
    assert b0([cyc_inp], {})[0].decision == "recommend_eligible"
    inv_inp = make_input(features=invalid_score_features())
    assert c1([inv_inp], {})[0].decision == "reject_invalid_score"
    assert b0([inv_inp], {})[0].decision == "reject_invalid_score"


def test_c1_gate_abstains_on_unobserved_target_dimension():
    features = unobserved_dimension_features()
    features["target_task"]["target_competency"] = "S2"  # required and unobserved
    inp = make_input(features=features)
    pred = c1([inp], {})[0]
    assert pred.decision == "abstain_insufficient_data"
