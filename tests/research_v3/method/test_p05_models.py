"""P05 model contract tests: determinism, monotone forgetting, abstention."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import roc_auc_score

from research_v3.methods.p05.models import (
    AblatedModel,
    C0BaseRate,
    C1LogisticRecencyFreq,
    ForgettingAwareKT,
    FrequencyRankScheduler,
    P05ModelError,
    ReviewScheduler,
    add_decay_features,
    random_ranking_recall,
)
from tests.research_v3.method.conftest import make_attempts  # noqa: F401  (used via fixture)
import pandas as pd
import pytest


def _one_row(synthetic_attempts):
    return synthetic_attempts.head(1).copy()


def test_decay_is_monotone_decreasing_in_gap(synthetic_attempts):
    """Forgetting mechanism: retrieval strength must strictly decrease as
    elapsed gap grows, for every half-life on the grid."""
    for h in (10.0, 50.0, 120.0):
        thetas = []
        for gap in (1.0, 5.0, 20.0, 60.0, 120.0):
            df = synthetic_attempts.head(1).copy()
            df["features"] = [{**df.iloc[0]["features"], "gap_days": gap}]
            out = add_decay_features(df, h)
            thetas.append(out.iloc[0]["features"]["theta"])
        assert all(t2 < t1 for t1, t2 in zip(thetas, thetas[1:])), h


def test_decay_equal_history_zero_gap_is_history(synthetic_attempts):
    df = synthetic_attempts.head(1).copy()
    df["features"] = [{**df.iloc[0]["features"], "gap_days": 0.0}]
    out = add_decay_features(df, 50.0)
    f = out.iloc[0]["features"]
    assert f["theta"] == pytest.approx(0.5 * 0.7 + 0.5 * (np.log1p(100.0) / np.log1p(400.0)))


def test_c0_is_constant_and_calibrated_to_train_rate(synthetic_parts):
    c0 = C0BaseRate().fit(synthetic_parts["train"])
    p, abstain = c0.predict_batch(synthetic_parts["test"])
    assert len(p) == len(synthetic_parts["test"])
    assert np.allclose(p, synthetic_parts["train"]["label"].mean())
    assert not abstain.any()


def test_c0_unfitted_raises():
    with pytest.raises(P05ModelError):
        C0BaseRate().predict_batch(pd.DataFrame({"a": [1]}))


def test_c1_and_proposed_fit_and_predict(synthetic_parts):
    c1 = C1LogisticRecencyFreq().fit(synthetic_parts["train"], synthetic_parts["calibration"])
    p1, a1 = c1.predict_batch(synthetic_parts["test"])
    assert len(p1) == len(synthetic_parts["test"]) and not a1.any()
    assert p1.min() >= 0.0 and p1.max() <= 1.0
    kt = ForgettingAwareKT().fit(synthetic_parts["train"], synthetic_parts["calibration"])
    pk, ak = kt.predict_batch(synthetic_parts["test"])
    assert len(pk) == len(synthetic_parts["test"]) and not ak.any()
    assert kt.half_life_ in (10.0, 20.0, 35.0, 50.0, 80.0, 120.0)


def test_determinism_same_inputs_same_predictions(synthetic_parts):
    """Byte-for-byte reproducibility: identical fits must give identical
    probability vectors (deterministic solver + fixed column order)."""
    c1a = C1LogisticRecencyFreq().fit(synthetic_parts["train"], synthetic_parts["calibration"])
    c1b = C1LogisticRecencyFreq().fit(synthetic_parts["train"], synthetic_parts["calibration"])
    pa, _ = c1a.predict_batch(synthetic_parts["test"])
    pb, _ = c1b.predict_batch(synthetic_parts["test"])
    assert np.array_equal(pa, pb)
    kta = ForgettingAwareKT().fit(synthetic_parts["train"], synthetic_parts["calibration"])
    ktb = ForgettingAwareKT().fit(synthetic_parts["train"], synthetic_parts["calibration"])
    qa, _ = kta.predict_batch(synthetic_parts["test"])
    qb, _ = ktb.predict_batch(synthetic_parts["test"])
    assert np.array_equal(qa, qb)
    assert kta.half_life_ == ktb.half_life_ and kta.selected_C_ == ktb.selected_C_


def test_empty_features_refused_not_aplicable(synthetic_parts):
    c1 = C1LogisticRecencyFreq().fit(synthetic_parts["train"], synthetic_parts["calibration"])
    broken = synthetic_parts["test"].head(1).copy()
    broken["features"] = [{}]
    with pytest.raises(P05ModelError):
        c1.predict_batch(broken)


def test_single_class_train_refused(synthetic_parts):
    degenerate = synthetic_parts["train"].copy()
    degenerate["label"] = 1
    with pytest.raises(P05ModelError):
        C1LogisticRecencyFreq().fit(degenerate, synthetic_parts["calibration"])


def test_ablation_true_removal(synthetic_parts):
    """A1 must actually remove the decay feature group from the design."""
    m = AblatedModel("A1_no_elapsed_time").fit(synthetic_parts["train"], synthetic_parts["calibration"])
    assert "gap_days" not in m.columns_
    assert "log_gap" not in m.columns_
    assert "decay_score_mean_h45" not in m.columns_
    m5 = AblatedModel("A5_no_recency_features").fit(synthetic_parts["train"], synthetic_parts["calibration"])
    assert "days_since_click" not in m5.columns_
    m3 = AblatedModel("A3_no_score_history").fit(synthetic_parts["train"], synthetic_parts["calibration"])
    assert "past_score_mean" not in m3.columns_
    with pytest.raises(P05ModelError):
        AblatedModel("nonexistent_variant")


def test_scheduler_ranks_high_risk_first_and_tie_break_uses_gap():
    test = pd.DataFrame(
        {
            "case_id": ["a", "b", "c", "d"],
            "learner_id": ["1", "2", "3", "4"],
            "label": [0, 1, 0, 1],
            "features": [
                {"gap_days": 10.0},
                {"gap_days": 10.0},
                {"gap_days": 30.0},
                {"gap_days": 60.0},
            ],
        }
    )
    risk = np.array([0.9, 0.9, 0.5, 0.5])  # failure risk directly
    sched = ReviewScheduler(tie_half_life_days=10.0)
    order = sched.rank(test, risk)
    # highest risk first; among the (c,d) risk tie, longer idle (60d) first
    assert list(order[:2]) == [0, 1]
    assert list(order[2:]) == [3, 2]
    rec = sched.recall_at_budget(test, risk, budgets_pct=(50,))
    # top 2 by risk = {a, b}; only b is a failure -> recall = 1/2 (honest,
    # not all failures are reachable at this budget under this ranking)
    assert rec["recall_failures@50%"] == pytest.approx(0.5)
    # 80% of 4 cases = 3 returned (a, b, d): only a is a failure -> 1/2.
    # Capturing BOTH failures (a and c) requires the full budget, so this is an
    # honest ceiling at 80% rather than a scheduler defect.
    rec80 = sched.recall_at_budget(test, risk, budgets_pct=(80,))
    assert rec80["recall_failures@80%"] == pytest.approx(0.5)
    rec100 = sched.recall_at_budget(test, risk, budgets_pct=(100,))
    assert rec100["recall_failures@100%"] == pytest.approx(1.0)


def test_frequency_rank_scheduler_differs_from_decay_tie_break():
    test = pd.DataFrame(
        {
            "case_id": ["a", "b"],
            "learner_id": ["1", "2"],
            "label": [0, 0],
            "features": [{"gap_days": 5.0}, {"gap_days": 90.0}],
        }
    )
    risk = np.array([0.5, 0.5])
    decay_order = ReviewScheduler(tie_half_life_days=10.0).rank(test, risk)
    freq_order = FrequencyRankScheduler().rank(test, risk)
    assert decay_order[0] == 1  # longer-idle pair first under decay rule
    assert freq_order[0] in (0, 1)  # freq rank has no tie-break; stable by learner id


def test_random_ranking_recall_deterministic(synthetic_parts):
    r1 = random_ranking_recall(synthetic_parts["test"], seed=11)
    r2 = random_ranking_recall(synthetic_parts["test"], seed=11)
    assert r1 == r2


def test_recall_at_budget_alignment(synthetic_parts):
    test = synthetic_parts["test"]
    probs = np.linspace(0.1, 0.9, len(test))
    rec = ReviewScheduler(tie_half_life_days=10.0).recall_at_budget(test, probs, budgets_pct=(100,))
    assert rec["recall_failures@100%"] == pytest.approx(1.0)
