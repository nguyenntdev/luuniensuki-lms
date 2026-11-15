"""P13 analysis engine: descriptives, effect sizes, classification, calibration.

Observational/descriptive + predictive-secondary ONLY:
  - group contrasts: Cliff's delta with cluster bootstrap CIs on id_student
    (research_v3.eval.statistics), Holm-corrected within the preregistered
    family;
  - classification: logistic regression on frozen features; ROC-AUC/PR-AUC/
    Brier/ECE via sklearn + research_v3.eval.calibration; paired AUC
    comparison via cluster bootstrap of per-learner score differences;
  - no causal inference anywhere; every artifact passes the construct guard.
"""
from __future__ import annotations

import zlib
from typing import Any, Sequence

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from research_v3.eval.calibration import expected_calibration_error, reliability_bins
from research_v3.eval.statistics import cliffs_delta, family_control
from research_v3.methods.p13.construct_validity import enforce_proxy_guard
from research_v3.methods.p13.srl_features import (
    C0_FEATURES,
    C1_FEATURES,
    SRL_PROXIES,
)

SEED = 20261115
BOOTSTRAP_RESAMPLES = 2000


def _delta_pairwise(xa: np.ndarray, xb: np.ndarray) -> float:
    """Cliff's delta via broadcasting; chunked to bound memory."""
    na, nb = xa.size, xb.size
    if na == 0 or nb == 0:
        return float("nan")
    gt = 0.0
    lt = 0.0
    chunk = max(1, int(5_000_000 // max(1, nb)))
    for s in range(0, na, chunk):
        block = xa[s : s + chunk]
        gt += float(np.count_nonzero(block[:, None] > xb[None, :]))
        lt += float(np.count_nonzero(block[:, None] < xb[None, :]))
    return (gt - lt) / (na * nb)


def _delta_rank(xa: np.ndarray, xb: np.ndarray) -> float:
    """Cliff's delta from midranks of the pooled sample (ties-aware).

    Equivalent to the pairwise definition: with midranks R over the pooled
    sample, sum(R_a) - sum(R_b) = gt - lt + (n_a*n_b + ties)/2, so
    delta = 2*(sum(R_a)-sum(R_b))/(n_a*n_b) - 1 reproduces the pairwise value
    including ties (verified against research_v2 cliffs_delta in tests).
    """
    na, nb = xa.size, xb.size
    if na == 0 or nb == 0:
        return float("nan")
    pooled = np.concatenate([xa, xb])
    order = np.argsort(pooled, kind="mergesort")
    ranks = np.empty(pooled.size, dtype=float)
    sorted_vals = pooled[order]
    # midranks
    ranks_sorted = np.arange(1, pooled.size + 1, dtype=float)
    # average ranks within tie groups
    i = 0
    while i < pooled.size:
        j = i
        while j + 1 < pooled.size and sorted_vals[j + 1] == sorted_vals[i]:
            j += 1
        if j > i:
            ranks_sorted[i : j + 1] = (i + j + 2) / 2.0
        i = j + 1
    ranks[order] = ranks_sorted
    # scipy-convention U for sample a: U = R_a - na*(na+1)/2 counts
    # (a > b) + 0.5 * ties.
    sum_a = float(ranks[:na].sum())
    u_a = sum_a - na * (na + 1) / 2.0
    # Recover gt/lt exactly: cross ties via sorted searchsorted.
    xb_sorted = np.sort(xb)
    cross_ties = 0.0
    chunk = max(1, int(5_000_000 // max(1, nb)))
    for s in range(0, na, chunk):
        block = xa[s : s + chunk]
        left = np.searchsorted(xb_sorted, block, side="left")
        right = np.searchsorted(xb_sorted, block, side="right")
        cross_ties += float(np.sum(right - left))
    gt = u_a - cross_ties / 2.0
    lt = na * nb - gt - cross_ties
    return (gt - lt) / (na * nb)

#: Preregistered contrast family (confirmatory; Holm-corrected).
CONTRAST_FAMILY = (
    ("Pass", "Fail"),
    ("Pass", "Withdrawn"),
    ("Fail", "Withdrawn"),
)


def _matrix(rows: Sequence[dict[str, Any]], names: Sequence[str]) -> np.ndarray:
    return np.asarray(
        [[float(r["features"][n]) for n in names] for r in rows], dtype=float
    )


def _labels(rows: Sequence[dict[str, Any]]) -> np.ndarray:
    return np.asarray([1 if r["label"] == "Pass" else 0 for r in rows], dtype=int)


FEATURE_SETS: dict[str, list[str]] = {
    "C0": list(C0_FEATURES),
    "C1": list(C1_FEATURES),
    "C2": list(SRL_PROXIES),
    # Ablations (spec A1..A4) — true removals from C2.
    "A1_no_forethought": [p for p in SRL_PROXIES if not p.startswith(("plan_", "reflect_"))],
    "A2_no_temporal_order": list(SRL_PROXIES),  # used with shuffled-date features
    "A3_no_help_seeking": [p for p in SRL_PROXIES if not p.startswith("help_seeking_")],
    "A4_no_effort": [p for p in SRL_PROXIES if not p.startswith("effort_")],
}


def _make_model(seed: int = SEED) -> Pipeline:
    # Fixed preregistered budget: no hyperparameter search; L2 logistic
    # regression with standardised inputs, liblinear for determinism.
    return Pipeline(
        [
            ("scaler", StandardScaler()),
            (
                "clf",
                LogisticRegression(
                    l1_ratio=0.0, C=1.0, solver="liblinear", max_iter=1000, random_state=seed
                ),
            ),
        ]
    )


def fit_calibrate_scores(
    train_rows: Sequence[dict[str, Any]],
    cal_rows: Sequence[dict[str, Any]],
    test_rows: Sequence[dict[str, Any]],
    feature_names: Sequence[str],
    feature_source: dict[str, Sequence[dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    """Fit on train, evaluate on test; A = pass-vs-rest.

    ``feature_source`` optionally overrides which physical rows provide each
    partition's features (used by the A2 shuffled-date ablation while keeping
    case alignment frozen).
    """
    src = feature_source or {
        "train": train_rows,
        "calibration": cal_rows,
        "test": test_rows,
    }
    X_train, y_train = _matrix(src["train"], feature_names), _labels(src["train"])
    if len(set(y_train.tolist())) < 2:
        return {"status": "DEGENERATE", "reason": "single-class train partition"}

    model = _make_model()
    model.fit(X_train, y_train)

    X_test, y_test = _matrix(src["test"], feature_names), _labels(src["test"])
    proba = model.predict_proba(X_test)[:, 1]

    # Isotonic-free calibration report (the model itself is the pre-registered
    # calibration: fixed C, no test tuning). Report ECE on raw scores.
    bins = reliability_bins(proba.tolist(), y_test.tolist(), n_bins=10)
    ece = expected_calibration_error(bins)

    metrics: dict[str, Any] = {
        "n_train": int(len(src["train"])),
        "n_test": int(len(src["test"])),
        "prevalence_pass": float(y_test.mean()),
        "roc_auc": float(roc_auc_score(y_test, proba)),
        "pr_auc": float(average_precision_score(y_test, proba)),
        "brier": float(brier_score_loss(y_test, proba)),
        "ece": float(ece) if ece is not None else None,
        "reliability_bins": bins,
        "feature_names": list(feature_names),
        "coefficients": {
            n: float(c)
            for n, c in zip(feature_names, model.named_steps["clf"].coef_[0].tolist())
        },
    }
    # per-learner scores for paired AUC comparison + subgroup cuts
    metrics["_proba"] = proba.tolist()
    metrics["_y"] = y_test.tolist()
    metrics["_case_ids"] = [str(r["case_id"]) for r in src["test"]]
    metrics["_group_ids"] = [str(r["group_id"]) for r in src["test"]]
    return metrics


def paired_auc_comparison(
    proba_a: Sequence[float],
    proba_b: Sequence[float],
    y: Sequence[int],
    group_ids: Sequence[str],
    *,
    n_boot: int = BOOTSTRAP_RESAMPLES,
    seed: int = SEED,
) -> dict[str, Any]:
    """Paired AUC difference (A - B) with learner-cluster bootstrap CI."""
    pa = np.asarray(proba_a, dtype=float)
    pb = np.asarray(proba_b, dtype=float)
    yy = np.asarray(y, dtype=int)
    if not (len(pa) == len(pb) == len(yy) == len(group_ids)):
        raise ValueError("aligned inputs required")

    auc_a = float(roc_auc_score(yy, pa))
    auc_b = float(roc_auc_score(yy, pb))

    uniq = sorted(set(group_ids))
    idx_by_group: dict[str, list[int]] = {g: [] for g in uniq}
    for i, g in enumerate(group_ids):
        idx_by_group[g].append(i)
    rng = np.random.default_rng(seed)
    deltas = np.empty(n_boot, dtype=float)
    for b in range(n_boot):
        pick = rng.choice(uniq, size=len(uniq), replace=True)
        idx: list[int] = []
        for g in pick:
            idx.extend(idx_by_group[g])
        yy_b = yy[idx]
        if len(set(yy_b.tolist())) < 2:
            deltas[b] = np.nan
            continue
        deltas[b] = roc_auc_score(yy_b, pa[idx]) - roc_auc_score(yy_b, pb[idx])
    finite = deltas[np.isfinite(deltas)]
    lo, hi = np.percentile(finite, [2.5, 97.5])
    return {
        "auc_a": auc_a,
        "auc_b": auc_b,
        "delta_auc": auc_a - auc_b,
        "ci_95": [float(lo), float(hi)],
        "n_clusters": len(uniq),
        "n_test_rows": int(len(yy)),
        "resamples": n_boot,
        "method": "cluster_bootstrap_on_id_student",
    }


def group_contrast(
    rows: Sequence[dict[str, Any]],
    feature_name: str,
    group_a: str,
    group_b: str,
    *,
    n_boot: int = BOOTSTRAP_RESAMPLES,
    seed: int = SEED,
) -> dict[str, Any]:
    """Cliff's delta between two outcome groups with learner bootstrap CI."""
    a = np.asarray(
        [float(r["features"][feature_name]) for r in rows if r["label"] == group_a], dtype=float
    )
    b = np.asarray(
        [float(r["features"][feature_name]) for r in rows if r["label"] == group_b], dtype=float
    )
    if a.size == 0 or b.size == 0:
        return {"feature": feature_name, "contrast": f"{group_a}_vs_{group_b}", "status": "EMPTY"}
    delta = cliffs_delta(a.tolist(), b.tolist())

    # bootstrap CI resampling learners (cluster-aware)
    groups_a = [str(r["group_id"]) for r in rows if r["label"] == group_a]
    groups_b = [str(r["group_id"]) for r in rows if r["label"] == group_b]
    uniq = sorted(set(groups_a) | set(groups_b))
    vals_by_group: dict[str, list[float]] = {}
    for r in rows:
        if r["label"] in (group_a, group_b):
            vals_by_group.setdefault(str(r["group_id"]), []).append(
                float(r["features"][feature_name])
            )
    group_label = {g: (1 if g in set(groups_a) else 0) for g in vals_by_group}
    rng = np.random.default_rng(seed + (zlib.crc32(feature_name.encode("utf-8")) % 1000))

    # Bootstrap resamples LEARNERS (cluster-aware), then computes Cliff's delta
    # on rank space: concatenate resampled values, rank once per replicate, and
    # derive gt/lt counts from the ranks (equivalent to pairwise comparison,
    # much faster). Exact equality of ranks is handled via midranks so ties
    # contribute (n_a*n_b - gt - lt) symmetrically, matching cliffs_delta().
    packed: dict[str, np.ndarray] = {
        g: np.asarray(v, dtype=float) for g, v in vals_by_group.items()
    }
    uniq_arr = np.asarray(uniq)
    labels_arr = np.asarray([group_label[g] for g in uniq], dtype=int)

    boot = np.empty(n_boot, dtype=float)
    for i in range(n_boot):
        pick = rng.integers(0, len(uniq), size=len(uniq))
        xa_parts = [packed[uniq_arr[j]] for j in pick if labels_arr[j] == 1]
        xb_parts = [packed[uniq_arr[j]] for j in pick if labels_arr[j] == 0]
        if not xa_parts or not xb_parts:
            boot[i] = np.nan
            continue
        xa = np.concatenate(xa_parts)
        xb = np.concatenate(xb_parts)
        boot[i] = _delta_rank(xa, xb)
    finite = boot[np.isfinite(boot)]
    lo, hi = np.percentile(finite, [2.5, 97.5])
    from scipy import stats as _st

    try:
        u = _st.mannwhitneyu(a, b, alternative="two-sided")
        p_value = float(u.pvalue)
    except Exception:  # pragma: no cover
        p_value = None
    return {
        "feature": feature_name,
        "contrast": f"{group_a}_vs_{group_b}",
        "n_a": int(a.size),
        "n_b": int(b.size),
        "mean_a": float(a.mean()),
        "mean_b": float(b.mean()),
        "cliffs_delta": float(delta),
        "ci_95": [float(lo), float(hi)],
        "p_value_mwu": p_value,
        "method": "cliffs_delta_cluster_bootstrap_on_id_student",
    }


def confirmatory_family(
    rows: Sequence[dict[str, Any]], feature_names: Sequence[str]
) -> dict[str, Any]:
    """All preregistered contrasts x proxies with Holm correction per contrast."""
    results: dict[str, Any] = {}
    for ga, gb in CONTRAST_FAMILY:
        per_feature = [
            group_contrast(rows, f, ga, gb)
            for f in feature_names
            if f in SRL_PROXIES
        ]
        pvals = [r.get("p_value_mwu") for r in per_feature]
        ok = [p is not None for p in pvals]
        if any(ok):
            ps = [p if p is not None else 1.0 for p in pvals]
            adjusted = family_control(ps, method="holm")
            for r, p_raw, p_adj, was_ok in zip(per_feature, ps, adjusted, ok):
                r["p_value_mwu"] = p_raw if was_ok else None
                r["p_value_holm"] = p_adj if was_ok else None
        results[f"{ga}_vs_{gb}"] = per_feature
    return results


def subgroup_auc(
    proba: Sequence[float], y: Sequence[int], subgroup: Sequence[str], *, min_n: int = 20
) -> dict[str, Any]:
    """AUC per subgroup value; groups under min_n reported but flagged."""
    out: dict[str, Any] = {}
    for val in sorted(set(subgroup)):
        idx = [i for i, s in enumerate(subgroup) if s == val]
        yy = [y[i] for i in idx]
        if len(set(yy)) < 2 or len(idx) < min_n:
            out[val] = {"n": len(idx), "auc": None, "below_min_n": len(idx) < min_n}
            continue
        out[val] = {
            "n": len(idx),
            "auc": float(roc_auc_score(yy, [proba[i] for i in idx])),
            "below_min_n": False,
        }
    return out


def guarded_text(name: str, text: str) -> str:
    """Public wrapper so the runner routes ALL narrative text through the guard."""
    return enforce_proxy_guard(name, text)
