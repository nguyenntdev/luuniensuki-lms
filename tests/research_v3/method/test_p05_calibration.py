"""P05 metric and calibration sanity tests (P05-T14 acceptance)."""
from __future__ import annotations

import numpy as np
import pytest

from research_v3.methods.p05.metrics_p05 import (
    P05MetricError,
    auc_ci_cluster_bootstrap,
    evaluate_probabilistic,
)
from research_v3.eval.calibration import expected_calibration_error, reliability_bins


def test_perfect_predictions_have_zero_brier_and_low_ece():
    y = [0, 0, 1, 1] * 25
    p = [0.01, 0.02, 0.98, 0.99] * 25
    m = evaluate_probabilistic(y, p)
    assert m["brier"] < 0.001
    assert m["auc"] == 1.0
    assert m["ece_10bin"] < 0.05


def test_brier_degrades_with_noise():
    y = [0, 0, 1, 1] * 50
    p_good = [0.05, 0.1, 0.9, 0.95] * 50
    p_bad = [0.45, 0.55, 0.5, 0.5] * 50
    assert evaluate_probabilistic(y, p_bad)["brier"] > evaluate_probabilistic(y, p_good)["brier"]


def test_calibration_sanity_overconfident_model_has_high_ece():
    """A model predicting 0.99 for events that happen 50% of the time must
    show large ECE — this is the guard against fake confidence."""
    y = [1, 0] * 100
    p = [0.99, 0.99] * 100
    m = evaluate_probabilistic(y, p)
    assert m["ece_10bin"] > 0.4
    assert m["brier"] > 0.24


def test_calibration_sanity_well_calibrated_model_has_low_ece():
    y = [1] * 50 + [0] * 50
    p = [0.5] * 100
    m = evaluate_probabilistic(y, p)
    assert m["ece_10bin"] < 0.01


def test_abstained_rows_excluded_from_denominator_and_reported():
    y = [0, 1, 0, 1, 1, 0]
    p = [0.2, 0.8, 0.3, 0.9, 0.7, 0.1]
    abstain = [False, False, False, False, True, True]
    m = evaluate_probabilistic(y, p, abstain_mask=abstain)
    assert m["n"] == 4
    assert m["n_abstained"] == 2


def test_single_class_window_refused_no_fabricated_auc():
    with pytest.raises(P05MetricError):
        evaluate_probabilistic([1, 1, 1], [0.9, 0.8, 0.7])


def test_invalid_probabilities_refused():
    with pytest.raises(P05MetricError):
        evaluate_probabilistic([0, 1], [0.2, 1.4])
    with pytest.raises(P05MetricError):
        evaluate_probabilistic([0, 1], [0.2, float("nan")])


def test_misaligned_inputs_refused():
    with pytest.raises(P05MetricError):
        evaluate_probabilistic([0, 1, 1], [0.2, 0.8])


def test_reliability_bins_partition_and_bounds():
    rng = np.random.default_rng(0)
    p = rng.uniform(0, 1, size=1000)
    y = (rng.uniform(0, 1, size=1000) < p).astype(int)
    bins = reliability_bins(p.tolist(), y.tolist(), n_bins=10)
    assert sum(b["n"] for b in bins) == 1000
    for b in bins:
        if b["n"]:
            assert 0.0 <= b["mean_prob"] <= 1.0
            assert 0.0 <= b["observed"] <= 1.0
    ece = expected_calibration_error(bins)
    assert 0.0 <= ece <= 1.0


def test_auc_cluster_bootstrap_brackets_point_estimate():
    rng = np.random.default_rng(1)
    n_learners = 60
    per = 10
    clusters = np.repeat([f"L{i}" for i in range(n_learners)], per)
    y = rng.choice([0, 1], size=n_learners * per, p=[0.5, 0.5])
    p = np.clip(y * 0.6 + rng.uniform(0, 0.4, size=len(y)), 0.01, 0.99)
    res = auc_ci_cluster_bootstrap(y, p, clusters, n_boot=300, seed=42)
    lo, hi = res["ci_95"]
    assert lo <= res["auc_point"] <= hi
    assert 0.0 <= lo and hi <= 1.0
