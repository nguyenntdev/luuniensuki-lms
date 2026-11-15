"""Typed scalar guards on LN-02 decision paths (reviewer findings 1-5).

Covers the typed-failure contract at the boundaries the previous code left
to raw ``TypeError``:

- C1 with an unobserved ``score_observed`` (None) must abstain, not crash.
- proposed / ablations with an explicitly None prerequisite threshold must
  reach a typed outcome (missing prerequisite data), never a raw TypeError.
- Bools are never silently coerced to 0/1: a bool score or bool threshold is
  a typed failure.
- Valid-input outcomes are byte-identical to the pre-guard reference
  decisions/scores captured from the audited engine.
"""
from __future__ import annotations

import copy
import pytest

from research_v2.contracts.types import StudyInput
from research_v2.methods.ln02 import ablations, proposed
from research_v2.methods.ln02.baselines import (
    predict_one_b0,
    predict_one_c1,
)
from research_v2.methods.ln02.core import (
    MethodContractError,
    coerce_finite_float,
)

from ln02_helpers import (
    HEALTHY_MASTERY,
    high_aggregate_missing_prerequisite_features,
    make_input,
    nominal_features,
    unobserved_dimension_features,
)


def _with_features(features: dict) -> StudyInput:
    return make_input(case_id="typed-guard", features=features)


def _mutated(base: dict, **changes) -> dict:
    features = copy.deepcopy(base)
    features.update(changes)
    return features


def _task_with_prerequisites(base: dict, prerequisites: dict) -> dict:
    features = copy.deepcopy(base)
    task = dict(features.get("target_task") or {})
    task["prerequisites"] = prerequisites
    features["target_task"] = task
    return features


# --------------------------------------------------------------------------- #
# 1. C1 with score_observed=None -> typed abstention, never raw TypeError
# --------------------------------------------------------------------------- #
def test_c1_none_score_observed_abstains_typed():
    features = _mutated(nominal_features(), score_observed=None)
    pred = predict_one_c1(_with_features(features), {})
    assert pred.decision == "abstain_insufficient_data"
    assert "INSUFFICIENT_COMPETENCY_DATA" in pred.reason_codes
    assert "UNOBSERVED_SCORE:score_observed" in pred.reason_codes


def test_c1_missing_score_observed_abstains_typed():
    features = nominal_features()
    del features["score_observed"]
    pred = predict_one_c1(_with_features(features), {})
    assert pred.decision == "abstain_insufficient_data"
    assert "UNOBSERVED_SCORE:score_observed" in pred.reason_codes


def test_c1_none_score_with_unmet_gate_still_remediates():
    """Stage-1 gate ordering is preserved: when the task's target competency
    is below its threshold, C1 remediates before the scalar stage ever needs
    the aggregate score."""
    features = high_aggregate_missing_prerequisite_features()
    features["score_observed"] = None
    features["target_task"]["target_competency"] = "S1"  # mastery 0.22 < 0.6
    pred = predict_one_c1(_with_features(features), {})
    assert pred.decision == "remediate_first"
    assert "UNMET_PREREQUISITE:S1" in pred.reason_codes


# --------------------------------------------------------------------------- #
# 2. proposed with a None prerequisite threshold -> typed, never TypeError
# --------------------------------------------------------------------------- #
def test_proposed_none_threshold_typed_outcome_not_typeerror():
    features = _task_with_prerequisites(
        nominal_features(), {"S1": None, "S2": 0.45}
    )
    pred = proposed.predict_one(_with_features(features), {})
    # The None-threshold dimension carries no enforceable gate; S2 still
    # clears its own threshold, so the honest outcome is eligible with no
    # fabricated remediation for the unmeasurable requirement.
    assert pred.decision == "recommend_eligible"
    assert "PREREQUISITE_NOT_MET" not in pred.reason_codes


def test_proposed_none_threshold_with_observed_gap_typed_outcome():
    """A None threshold must not mask a real gap on a different dimension:
    the gap dim keeps a real threshold and still remediates."""
    features = _task_with_prerequisites(
        high_aggregate_missing_prerequisite_features(), {"S1": 0.6, "S2": None}
    )
    pred = proposed.predict_one(_with_features(features), {})
    assert pred.decision == "remediate_first"
    assert "UNMET_PREREQUISITE:S1" in pred.reason_codes


# --------------------------------------------------------------------------- #
# 3. ablations a1/a2/a3 with a None threshold -> typed, never TypeError
# --------------------------------------------------------------------------- #
NONE_THRESHOLD_PREREQS = {"S1": None, "S2": 0.45}


def test_a1_none_threshold_typed_outcome_not_typeerror():
    features = _task_with_prerequisites(
        nominal_features(), NONE_THRESHOLD_PREREQS
    )
    pred = ablations.predict_one_a1(_with_features(features), {})
    assert pred.decision == "recommend_eligible"
    assert "UNMET_PREREQUISITE" not in "|".join(pred.reason_codes)


def test_a2_none_threshold_typed_outcome_not_typeerror():
    features = _task_with_prerequisites(
        nominal_features(), NONE_THRESHOLD_PREREQS
    )
    pred = ablations.predict_one_a2(_with_features(features), {})
    # a2 only forces remediation via imputation when a required dim is
    # unobserved; healthy mastery plus a None threshold stays eligible.
    assert pred.decision == "recommend_eligible"


def test_a2_none_threshold_with_unobserved_dim_still_imputes():
    """a2's mechanism (impute-missing-as-zero) still fires on unobserved dims
    with a real threshold even when another threshold is None."""
    features = unobserved_dimension_features()  # S2 unobserved
    task = dict(features["target_task"])
    task["prerequisites"] = {"S2": 0.5, "S3": None}
    features["target_task"] = task
    pred = ablations.predict_one_a2(_with_features(features), {})
    assert pred.decision == "remediate_first"
    assert "ABLATION_NO_ABSTENTION" in pred.reason_codes
    assert "UNOBSERVED_DIMENSION:S2" in pred.reason_codes


def test_a3_none_threshold_typed_outcome_not_typeerror():
    features = _task_with_prerequisites(
        nominal_features(), NONE_THRESHOLD_PREREQS
    )
    pred = ablations.predict_one_a3(_with_features(features), {})
    assert pred.decision in ("recommend_eligible", "remediate_first")
    assert "ABLATION_COLLAPSED_LATENT" in pred.reason_codes


# --------------------------------------------------------------------------- #
# 4. Bools are typed failures, never silently coerced to 0/1
# --------------------------------------------------------------------------- #
def test_coerce_finite_float_rejects_bool():
    with pytest.raises(MethodContractError):
        coerce_finite_float(True, field="score_observed")
    with pytest.raises(MethodContractError):
        coerce_finite_float(False, field="target_task.prerequisites[S1]")


def test_coerce_finite_float_none_and_valid_numbers():
    assert coerce_finite_float(None, field="score_observed") is None
    assert coerce_finite_float(0.72, field="score_observed") == 0.72
    assert coerce_finite_float(1, field="score_observed") == 1.0


def test_bool_score_observed_rejected_by_validity_gate():
    """A bool aggregate score is observed-but-invalid, not 0/1."""
    for bad in (True, False):
        features = _mutated(nominal_features(), score_observed=bad)
        pred = predict_one_b0(_with_features(features), {})
        assert pred.decision == "reject_invalid_score"
        features_c1 = _mutated(nominal_features(), score_observed=bad)
        pred_c1 = predict_one_c1(_with_features(features_c1), {})
        assert pred_c1.decision == "reject_invalid_score"


def test_bool_mastery_value_rejected_by_validity_gate():
    features = copy.deepcopy(nominal_features())
    features["mastery"] = {**HEALTHY_MASTERY, "S2": True}
    pred = proposed.predict_one(_with_features(features), {})
    assert pred.decision == "reject_invalid_score"


def test_bool_threshold_rejected_by_validity_gate():
    features = _task_with_prerequisites(
        nominal_features(), {"S1": True, "S2": 0.45}
    )
    for predict in (
        proposed.predict_one,
        predict_one_b0,
        predict_one_c1,
        ablations.predict_one_a1,
        ablations.predict_one_a2,
        ablations.predict_one_a3,
    ):
        pred = predict(_with_features(copy.deepcopy(features)), {})
        assert pred.decision == "reject_invalid_score"


def test_unobserved_required_dimensions_treats_bool_as_unobserved():
    """Validity-gate-adjacent helper: a bool mastery observation is not a
    measurement, so the dimension counts as unobserved (consistent with
    ``_as_float``), keeping the helper coherent even though the validity gate
    rejects bools before this is reached on live paths."""
    from research_v2.methods.ln02.core import unobserved_required_dimensions

    mastery = {"S1": 0.8, "S2": True, "S3": None}
    missing = unobserved_required_dimensions(
        mastery, {"S1": 0.5, "S2": 0.5, "S3": 0.5}
    )
    assert missing == ["S2", "S3"]


# --------------------------------------------------------------------------- #
# 5. Valid inputs unchanged (reference outcomes from the audited engine)
# --------------------------------------------------------------------------- #
def _ref(case: str) -> StudyInput:
    base = {
        "nominal": nominal_features,
        "gap": high_aggregate_missing_prerequisite_features,
        "unobs": unobserved_dimension_features,
    }[case]()
    return make_input(case_id=f"ref-guard-{case}", features=base)


REFERENCE_OUTCOMES = {
    ("nominal", "proposed"): ("recommend_eligible", 1.0),
    ("nominal", "b0"): ("recommend_eligible", 0.72),
    ("nominal", "c1"): ("recommend_eligible", 1.044797),
    ("nominal", "a1"): ("recommend_eligible", 0.72),
    ("nominal", "a2"): ("recommend_eligible", 1.0),
    ("nominal", "a3"): ("recommend_eligible", 0.775),
    ("gap", "proposed"): ("remediate_first", 1.0),
    ("gap", "b0"): ("recommend_eligible", 0.74),
    ("gap", "c1"): ("recommend_eligible", 1.045969),
    ("gap", "a1"): ("recommend_eligible", 0.74),
    ("gap", "a2"): ("remediate_first", 1.0),
    ("gap", "a3"): ("recommend_eligible", 0.66),
    ("unobs", "proposed"): ("abstain_insufficient_data", 0.75),
    ("unobs", "b0"): ("recommend_eligible", 0.78),
    ("unobs", "c1"): ("recommend_eligible", 1.265666),
    ("unobs", "a1"): ("recommend_eligible", 0.78),
    ("unobs", "a2"): ("remediate_first", 0.75),
    ("unobs", "a3"): ("abstain_insufficient_data", 0.75),
}

METHODS = {
    "proposed": proposed.predict_one,
    "b0": predict_one_b0,
    "c1": predict_one_c1,
    "a1": ablations.predict_one_a1,
    "a2": ablations.predict_one_a2,
    "a3": ablations.predict_one_a3,
}


@pytest.mark.parametrize("case", ["nominal", "gap", "unobs"])
@pytest.mark.parametrize("method", sorted(METHODS))
def test_valid_inputs_match_reference_outcomes(case, method):
    pred = METHODS[method](_ref(case), {})
    expected_decision, expected_score = REFERENCE_OUTCOMES[(case, method)]
    assert pred.decision == expected_decision
    assert pred.score == expected_score
