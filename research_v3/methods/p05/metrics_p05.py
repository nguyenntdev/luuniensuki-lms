"""P05 metrics: AUC, Brier, NLL, calibration (reusing research_v3/eval)."""
from __future__ import annotations

from typing import Any, Sequence

import numpy as np
from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score

from research_v3.eval.calibration import expected_calibration_error, reliability_bins


class P05MetricError(ValueError):
    pass


def evaluate_probabilistic(
    y_true: Sequence[int],
    probs: Sequence[float],
    *,
    abstain_mask: Sequence[bool] | None = None,
) -> dict[str, Any]:
    """AUC / Brier / NLL / ECE with an explicit abstention contract.

    Abstained rows are excluded from the denominator and the exclusion is
    reported; they are never counted as failures or successes.
    """
    y = np.asarray(list(y_true), dtype=int)
    p = np.asarray(list(probs), dtype=float)
    if len(y) != len(p):
        raise P05MetricError("y_true and probs must align")
    if abstain_mask is not None:
        keep = ~np.asarray(list(abstain_mask), dtype=bool)
        y, p = y[keep], p[keep]
    if len(y) == 0:
        raise P05MetricError("no scorable rows after abstention filter")
    if not np.all(np.isfinite(p)) or np.any((p < 0) | (p > 1)):
        raise P05MetricError("probabilities must be finite in [0, 1]")
    if len(np.unique(y)) < 2:
        raise P05MetricError("single-class outcome window: AUC undefined; refusing to fabricate")

    bins = reliability_bins(p.tolist(), y.tolist(), n_bins=10)
    return {
        "n": int(len(y)),
        "n_abstained": int(np.asarray(abstain_mask, dtype=bool).sum()) if abstain_mask is not None else 0,
        "prevalence": float(y.mean()),
        "auc": float(roc_auc_score(y, p)),
        "brier": float(brier_score_loss(y, p)),
        "nll": float(log_loss(y, p, labels=[0, 1])),
        "ece_10bin": float(expected_calibration_error(bins)),
        "reliability_bins": bins,
    }


def auc_ci_cluster_bootstrap(
    y_true: Sequence[int],
    probs: Sequence[float],
    cluster_ids: Sequence[str],
    *,
    n_boot: int = 2000,
    seed: int = 42,
) -> dict[str, Any]:
    """Learner-clustered bootstrap CI for AUC on FIXED predictions."""
    y = np.asarray(list(y_true), dtype=int)
    p = np.asarray(list(probs), dtype=float)
    g = np.asarray(list(cluster_ids))
    if len(y) != len(p) or len(y) != len(g):
        raise P05MetricError("misaligned inputs for AUC bootstrap")
    point = float(roc_auc_score(y, p))
    uniq = sorted(set(g.tolist()))
    idx_by_group: dict[str, np.ndarray] = {
        u: np.where(g == u)[0] for u in uniq
    }
    rng = np.random.default_rng(seed)
    aucs = np.empty(n_boot, dtype=float)
    for b in range(n_boot):
        pick = rng.choice(uniq, size=len(uniq), replace=True)
        idx = np.concatenate([idx_by_group[u] for u in pick])
        yb, pb = y[idx], p[idx]
        if len(np.unique(yb)) < 2:
            aucs[b] = np.nan
        else:
            aucs[b] = roc_auc_score(yb, pb)
    aucs = aucs[np.isfinite(aucs)]
    lo, hi = np.percentile(aucs, [2.5, 97.5])
    return {
        "auc_point": point,
        "ci_95": [float(lo), float(hi)],
        "resamples": n_boot,
        "valid_resamples": int(len(aucs)),
        "cluster": "learner",
        "method": "cluster_bootstrap_fixed_predictions",
    }
