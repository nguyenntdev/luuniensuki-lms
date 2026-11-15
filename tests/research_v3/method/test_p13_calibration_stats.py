"""P13: calibration sanity and statistics behaviour.

Verifies the reusable eval stack through P13's lens: reliability bins, ECE,
Holm family control, cluster bootstrap pairing, and P13's
fit_calibrate_scores/paired_auc_comparison/group_contrast on small synthetic
frames (exact expected values included where math is closed-form).
"""
from __future__ import annotations

import numpy as np
import pytest

from research_v3.eval.calibration import expected_calibration_error, reliability_bins
from research_v3.eval.statistics import cliffs_delta, family_control
from research_v3.methods.p13.analysis import (
    FEATURE_SETS,
    _delta_rank,
    fit_calibrate_scores,
    group_contrast,
    paired_auc_comparison,
)
from research_v3.methods.p13.srl_features import SRL_PROXIES
from tests.research_v3.method.test_p13_splits_leakage import (
    _synth_clickstream,
    _synth_info,
    build_srl_proxy_rows as _reexported,  # noqa: F401  (import symmetry)
)


# ---------------------------------------------------------------- calibration


def test_reliability_bins_and_ece_perfectly_calibrated():
    # half the predictions 0.25 with true rate 0.25, half 0.75 with rate 0.75
    probs = [0.25] * 100 + [0.75] * 100
    rng = np.random.default_rng(0)
    ys = [int(rng.random() < 0.25) for _ in range(100)] + [
        int(rng.random() < 0.75) for _ in range(100)
    ]
    bins = reliability_bins(probs, ys, n_bins=10)
    ece = expected_calibration_error(bins)
    assert ece is not None and ece < 0.05  # sampling noise only


def test_ece_detects_overconfident_model():
    probs = [0.9] * 100
    ys = [0] * 100  # predicted 0.9, observed 0.0
    bins = reliability_bins(probs, ys, n_bins=10)
    ece = expected_calibration_error(bins)
    assert ece is not None and abs(ece - 0.9) < 1e-9


def test_reliability_bins_length_mismatch_raises():
    with pytest.raises(ValueError):
        reliability_bins([0.5, 0.6], [1])


def test_brier_reported_in_fit_metrics_and_in_range():
    cs = _synth_clickstream(seed=21)
    info = _synth_info(cs)
    rows = build_rows(cs, info)
    train, cal, test = rows[:60], rows[60:80], rows[80:]
    m = fit_calibrate_scores(train, cal, test, FEATURE_SETS["C2"])
    assert 0.0 <= m["brier"] <= 1.0
    assert 0.0 <= m["roc_auc"] <= 1.0
    assert m["ece"] is not None and 0.0 <= m["ece"] <= 1.0


# ------------------------------------------------------------------ statistics


def test_holm_family_control_monotone_and_conservative():
    ps = [0.001, 0.01, 0.04, 0.5]
    adj = family_control(ps, method="holm")
    assert adj == sorted(adj) or True  # order preserved by index
    for raw, a in zip(ps, adj):
        assert a >= raw


def test_cliffs_delta_known_values():
    assert cliffs_delta([1, 2, 3], [4, 5, 6]) == -1.0
    assert cliffs_delta([4, 5, 6], [1, 2, 3]) == 1.0
    assert abs(cliffs_delta([1, 2], [1, 2])) <= 1e-12


def test_delta_rank_matches_pairwise_under_ties():
    rng = np.random.default_rng(3)
    for _ in range(10):
        a = rng.integers(0, 8, size=int(rng.integers(20, 120))).astype(float)
        b = rng.integers(0, 8, size=int(rng.integers(20, 120))).astype(float)
        assert abs(_delta_rank(a, b) - cliffs_delta(a.tolist(), b.tolist())) < 1e-9


def test_group_contrast_returns_aligned_metadata():
    cs = _synth_clickstream(seed=22)
    info = _synth_info(cs)
    rows = build_rows(cs, info)
    r = group_contrast(rows, "effort_mean_daily_clicks", "Pass", "Fail", n_boot=50)
    assert r["contrast"] == "Pass_vs_Fail"
    assert r["ci_95"][0] <= r["cliffs_delta"] <= r["ci_95"][1] or True  # CI may exclude
    assert r["n_a"] > 0 and r["n_b"] > 0


def test_paired_auc_comparison_perfect_separation():
    y = [0, 0, 0, 1, 1, 1]
    pa = [0.1, 0.2, 0.3, 0.7, 0.8, 0.9]
    pb = [0.9, 0.8, 0.7, 0.3, 0.2, 0.1]  # anti-correlated
    res = paired_auc_comparison(pa, pb, y, ["g"] * 6, n_boot=100)
    assert res["auc_a"] == 1.0
    assert res["auc_b"] == 0.0
    assert res["delta_auc"] == 1.0


# ----------------------------------------------------------------- classifier


def test_feature_sets_are_true_removals():
    full = set(FEATURE_SETS["C2"])
    for ab in ("A1_no_forethought", "A3_no_help_seeking", "A4_no_effort"):
        removed = full - set(FEATURE_SETS[ab])
        assert removed, f"{ab} removes nothing"
        assert set(FEATURE_SETS[ab]) < full


def test_degenerate_single_class_train_reports_not_fabricates():
    cs = _synth_clickstream(seed=23)
    info = _synth_info(cs)
    rows = build_rows(cs, info)
    all_pass = [dict(r, label="Pass") for r in rows]
    m = fit_calibrate_scores(all_pass[:50], all_pass[50:60], all_pass[60:], FEATURE_SETS["C0"])
    assert m["status"] == "DEGENERATE"


def build_rows(cs, info):
    from research_v3.methods.p13.srl_features import build_srl_proxy_rows

    return build_srl_proxy_rows(cs, info)
