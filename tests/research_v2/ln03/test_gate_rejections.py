"""Gate rejection tests: missing fact base, absent source, non-finite weight."""
from __future__ import annotations

import math

import pytest

from research_v2.contracts.types import StudyInput
from research_v2.methods.ln03 import proposed
from research_v2.methods.ln03.errors import ScenarioError

from ln03_helpers import make_features


def _inp(case_id: str, features: dict) -> StudyInput:
    return StudyInput("LN-03", case_id, "test", "grp-gates", features)


def test_missing_fact_base_rejected():
    features = make_features()
    del features["fact_prerequisite_mastered"]
    with pytest.raises(ScenarioError, match="fact_prerequisite_mastered"):
        proposed.predict_batch([_inp("LN-03-G1", features)])


def test_absent_source_rejected_when_field_missing():
    features = make_features()
    del features["review_card"]["source_verified"]
    with pytest.raises(ScenarioError, match="source_verified"):
        proposed.predict_batch([_inp("LN-03-G2", features)])


def test_unverified_source_blocks_explanation():
    pred = proposed.predict_batch([_inp("LN-03-G3", make_features(source_verified=False))])[0]
    assert pred.decision == "block_explanation"
    assert "absent_source" in pred.reason_codes
    assert "RULE-LN-03-05" in pred.reason_codes


@pytest.mark.parametrize("weight", [float("nan"), float("inf"), float("-inf")])
def test_non_finite_weight_rejected(weight):
    pred = proposed.predict_batch([_inp("LN-03-G4", make_features(scheduler_weight=weight))])[0]
    assert pred.decision == "reject_invalid_scheduler"
    assert "nonfinite_weight" in pred.reason_codes
    assert "RULE-LN-03-04" in pred.reason_codes
    assert pred.score is None


def test_non_numeric_weight_string_rejected():
    pred = proposed.predict_batch([_inp("LN-03-G5", make_features(scheduler_weight="undefined"))])[0]
    assert pred.decision == "reject_invalid_scheduler"


def test_weight_none_rejected_not_guessed():
    pred = proposed.predict_batch([_inp("LN-03-G6", make_features(scheduler_weight=None))])[0]
    assert pred.decision == "reject_invalid_scheduler"


def test_nonfinite_feature_values_rejected():
    features = make_features()
    features["review_card"]["stability_days"] = float("nan")
    with pytest.raises(ScenarioError, match="non-finite"):
        proposed.predict_batch([_inp("LN-03-G7", features)])


def test_negative_repetitions_rejected():
    features = make_features()
    features["review_card"]["repetitions"] = -1
    with pytest.raises(ScenarioError, match="repetitions"):
        proposed.predict_batch([_inp("LN-03-G8", features)])


def test_bad_timestamp_rejected():
    features = make_features()
    features["review_card"]["due_utc"] = "not-a-timestamp"
    with pytest.raises(ScenarioError, match="unparseable"):
        proposed.predict_batch([_inp("LN-03-G9", features)])


def test_invalid_config_threshold_fails_closed():
    with pytest.raises(Exception, match="fact_stability_min_repetitions"):
        proposed.predict_batch(
            [_inp("LN-03-G10", make_features())], {"fact_stability_min_repetitions": float("inf")}
        )


def test_finite_weight_accepted():
    pred = proposed.predict_batch([_inp("LN-03-G11", make_features(scheduler_weight=1.2))])[0]
    assert pred.decision == "schedule_eligible"
    assert pred.score is not None and math.isfinite(pred.score)
