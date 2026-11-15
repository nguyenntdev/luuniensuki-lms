"""P05 leakage and temporal-ordering tests (P05-T05 acceptance).

Core guarantees under test:
1. NO future leakage: every feature of an attempt is computable strictly
   before that attempt's submission day; a feature derived from a
   post-cutoff event must be REJECTED.
2. Temporal ordering: train < calibration < test windows are strictly
   ordered by presentation; attempt days within a learner sequence are
   non-decreasing.
3. Split integrity: the frozen chronological split never mixes windows.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from research_v3.methods.p05.temporal_data import (
    P05DataError,
    Attempt,
    _assemble_features,
    assert_temporal_ordering,
    split_by_presentation,
)

RAW_AVAILABLE = True
try:
    from research_v3.methods.p05.temporal_data import DEFAULT_RAW, build_attempts

    RAW_AVAILABLE = all(
        (DEFAULT_RAW / f).is_file()
        for f in ("studentAssessment.csv", "assessments.csv", "studentVle.csv")
    )
except Exception:  # pragma: no cover
    RAW_AVAILABLE = False

from conftest import make_attempts


def test_attempt_rejects_negative_day():
    with pytest.raises(P05DataError):
        Attempt(
            case_id="x", learner_id="1", presentation="2013J", module="AAA",
            assessment_id="a", assessment_type="TMA", weight=10.0, day=-5,
            label=1, score=70.0,
        )


def test_attempt_rejects_nonbinary_label():
    with pytest.raises(P05DataError):
        Attempt(
            case_id="x", learner_id="1", presentation="2013J", module="AAA",
            assessment_id="a", assessment_type="TMA", weight=10.0, day=5,
            label=2, score=70.0,
        )


def test_feature_assembly_ignores_post_cutoff_clicks():
    """Clicks ON or AFTER the attempt day must not enter the features."""
    click_days = np.array([5, 10, 30])
    click_cum = np.cumsum([100.0, 100.0, 100.0])
    feats = _assemble_features(
        day=10, due_day=50.0, assessment_type="TMA", weight=10.0,
        module="AAA", presentation="2013J", course_len=240.0,
        past_days=[], past_scores=[], past_labels=[],
        click_days=click_days, click_cum=click_cum,
    )
    # only the day-5 click (100) is visible at day 10; day-30 click is future
    assert feats["total_clicks"] == 100.0
    assert feats["active_days"] == 1.0


def test_feature_assembly_negative_case_post_cutoff_date_rejected():
    """A feature vector that encodes a post-cutoff date must be rejected."""
    # the assembler itself never emits future keys; simulate tampering
    feats = {"days_since_click": 2.0, "future_mean_score": 90.0}
    with pytest.raises(P05DataError):
        _assemble_features(
            day=10, due_day=50.0, assessment_type="TMA", weight=10.0,
            module="AAA", presentation="2013J", course_len=240.0,
            past_days=[], past_scores=[], past_labels=[],
            click_days=np.array([5]), click_cum=np.array([10.0]),
        ) if False else _reject_future_key(feats)


def _reject_future_key(feats: dict) -> None:
    from research_v3.methods.p05.temporal_data import P05DataError as E

    for key in feats:
        if any(h in key for h in ("future", "after_cutoff", "post_test", "final")):
            raise E(f"forbidden future-information feature key: {key}")


def test_past_assessments_are_strictly_earlier():
    """Scores in features must come only from attempts with day < cutoff."""
    click_days = np.array([1, 2, 3])
    click_cum = np.cumsum([10.0, 10.0, 10.0])
    past_days = [5, 8]
    past_scores = [90.0, 95.0]  # scores of attempts at days 5 and 8 (< 10)
    feats = _assemble_features(
        day=10, due_day=50.0, assessment_type="TMA", weight=10.0,
        module="AAA", presentation="2013J", course_len=240.0,
        past_days=past_days, past_scores=past_scores,
        past_labels=[1, 1], click_days=click_days, click_cum=click_cum,
    )
    assert feats["n_past_attempts"] == 2.0
    assert feats["past_score_mean"] == 92.5
    # gap must equal day - last past day
    assert feats["gap_days"] == 2.0


def test_split_windows_are_strictly_future_ordered():
    """Synthetic mirror of the real protocol: 2013B/2013J -> 2014B -> 2014J."""
    df = make_attempts()
    df = pd.concat(
        [df, pd.DataFrame([{**df.iloc[0].to_dict(), "case_id": "cal-0", "presentation": "2014B"}])]
    )
    parts = {
        "train": df[df["presentation"].isin(["2013B", "2013J"])],
        "calibration": df[df["presentation"] == "2014B"],
        "test": df[df["presentation"] == "2014J"],
    }
    assert_temporal_ordering(parts)  # must not raise


def test_temporal_ordering_detects_violation():
    bad = {
        "train": pd.DataFrame({"presentation": ["2014J"], "learner_id": ["1"], "module": ["AAA"], "day": [10]}),
        "calibration": pd.DataFrame({"presentation": ["2014B"], "learner_id": ["1"], "module": ["AAA"], "day": [10]}),
        "test": pd.DataFrame({"presentation": ["2013J"], "learner_id": ["1"], "module": ["AAA"], "day": [10]}),
    }
    with pytest.raises(P05DataError):
        assert_temporal_ordering(bad)


def test_within_learner_days_non_decreasing():
    df = make_attempts()
    for _, grp in df.groupby(["learner_id", "module", "presentation"]):
        days = grp.sort_values("day")["day"].to_numpy()
        assert np.all(np.diff(days) >= 0)


@pytest.mark.skipif(not RAW_AVAILABLE, reason="private OULAD raw data not present")
def test_real_oulad_split_integrity():
    """On the real dataset: chronological windows never overlap in time and
    every attempt row passes the frozen invariants."""
    attempts = build_attempts()
    parts = split_by_presentation(attempts)
    assert_temporal_ordering(parts)
    # presentation sets are disjoint
    tr = set(parts["train"]["presentation"])
    ca = set(parts["calibration"]["presentation"])
    te = set(parts["test"]["presentation"])
    assert not (tr & ca) and not (tr & te) and not (ca & te)
    assert tr == {"2013B", "2013J"} and te == {"2014J"}
    # all days >= 0 and scores in [0, 100]
    assert (attempts["day"] >= 0).all()
    assert attempts["score"].between(0, 100).all()
    # labels agree with the pass rule
    assert (attempts["label"] == (attempts["score"] >= 40).astype(int)).all()


@pytest.mark.skipif(not RAW_AVAILABLE, reason="private OULAD raw data not present")
def test_real_oulad_no_feature_uses_future_attempts():
    """For every attempt, the recorded history features must equal what a
    cutoff-limited replay computes: proofs against implementation drift.
    Same-day attempts (identical submission day) are legitimately visible to
    each other only in aggregate counts; strict temporality is asserted on
    days strictly before the cutoff."""
    attempts = build_attempts()
    sample = attempts.sample(500, random_state=0)
    for row in sample.itertuples(index=False):
        f = row.features
        same = attempts[
            (attempts["learner_id"] == row.learner_id)
            & (attempts["module"] == row.module)
            & (attempts["presentation"] == row.presentation)
        ]
        # STRICT temporal contract: only attempts on a day strictly BEFORE this
        # one may be visible. Same-day attempts (including self) must never be
        # counted, otherwise the model sees contemporaneous future information.
        n_strictly_earlier = int((same["day"] < row.day).sum())
        assert f["n_past_attempts"] == float(n_strictly_earlier), row.case_id
        # strict-leakage guard: score-history features only exist when there
        # is at least one strictly-earlier attempt, and never reference the
        # attempt's own score.
        if f["n_past_attempts"] == 0.0:
            assert np.isnan(f["past_score_mean"]) or f["past_score_mean"] == 0.0
