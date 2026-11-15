"""MANDATORY counterexample: high aggregate score but one necessary skill absent.

The non-compensatory gate must remediate, never recommend (spec 14.C.4).
The always-accept naive baseline must fail this case - the scientific gap.
"""
from __future__ import annotations

import pytest

from research_v2.methods.ln02 import ablations, proposed
from research_v2.methods.ln02.baselines_b0 import predict_batch as b0_batch
from research_v2.methods.ln02.baselines_c1 import predict_batch as c1_batch
from ln02_helpers import (
    high_aggregate_missing_prerequisite_features,
    make_input,
    nominal_features,
)


def _case(features, case_id):
    return make_input(case_id=case_id, features=features)


def test_proposed_remediates_when_required_skill_absent_despite_high_score():
    inp = _case(high_aggregate_missing_prerequisite_features(), "counter-high-S1")
    pred = proposed.predict_batch([inp], {})[0]
    assert pred.decision == "remediate_first"
    assert any("PREREQUISITE_NOT_MET" in rc or rc == "PREREQUISITE_NOT_MET" for rc in pred.reason_codes)
    assert any("UNMET_PREREQUISITE:S1" in rc for rc in pred.reason_codes)


def test_proposed_still_recommends_when_all_required_dims_clear():
    inp = _case(nominal_features(), "counter-healthy")
    pred = proposed.predict_batch([inp], {})[0]
    assert pred.decision == "recommend_eligible"


@pytest.mark.parametrize(
    "predict_batch",
    [b0_batch, c1_batch, ablations.predict_a1_batch, ablations.predict_a3_batch],
)
def test_baselines_fail_the_mandatory_case(predict_batch):
    """Scalar/aggregate comparators wrongly accept the counterexample -
    evidence that the non-compensatory mechanism is the discriminating one."""
    inp = _case(high_aggregate_missing_prerequisite_features(), "counter-high-S1")
    pred = predict_batch([inp], {})[0]
    assert pred.decision == "recommend_eligible"


def test_a2_no_abstention_forces_remediation_on_unobserved():
    """a2 imputes the missing dimension as 0 -> remediation instead of a
    guess; distinct from the proposed calibrated abstention."""
    from ln02_helpers import unobserved_dimension_features

    inp = _case(unobserved_dimension_features(), "counter-unobserved")
    proposed_pred = proposed.predict_batch([inp], {})[0]
    a2_pred = ablations.predict_a2_batch([inp], {})[0]
    assert proposed_pred.decision == "abstain_insufficient_data"
    assert a2_pred.decision == "remediate_first"


def test_two_near_identical_tasks_with_different_prerequisites():
    """Spec 03.F Case 4: identical learner, tasks differ only in which
    dimension is required; the gate must track the requirement, not the
    aggregate score."""
    learner = {
        "mastery": {"S1": 0.9, "S2": 0.3, "S3": 0.85, "S4": 0.8},
        "learner": {"competencies": {"S1": 0.9, "S2": 0.3, "S3": 0.85, "S4": 0.8}},
        "score_observed": 0.75,
        "graph_edges": [["S1", "S3"]],
        "content": {"id": "motif-pair", "type": "imperial-urn-motif"},
    }
    task_a = {
        "id": "task-a",
        "prerequisites": {"S1": 0.6},
        "target_competency": "S3",
    }
    task_b = {
        "id": "task-b",
        "prerequisites": {"S2": 0.6},
        "target_competency": "S3",
    }
    features_a = {**learner, "target_task": task_a}
    features_b = {**learner, "target_task": task_b}
    preds = proposed.predict_batch(
        [
            _case(features_a, "pair-task-a"),
            _case(features_b, "pair-task-b"),
        ],
        {},
    )
    assert preds[0].decision == "recommend_eligible"
    assert preds[1].decision == "remediate_first"
