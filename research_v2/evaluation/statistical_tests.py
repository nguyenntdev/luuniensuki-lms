"""Statistical tests with correct small-sample and paired behavior.

All functions return strict-JSON-safe dicts (finite numbers or None).
"""
from __future__ import annotations

import math
from typing import Iterable, Sequence

import numpy as np

try:  # scipy is optional; degrade gracefully but never fabricate results
    from scipy import stats as _stats
except Exception:  # pragma: no cover - scipy present in CI
    _stats = None


def _as_array(values: Iterable[float]) -> np.ndarray:
    arr = np.asarray(list(values), dtype=float)
    if arr.size and not np.all(np.isfinite(arr)):  # pragma: no cover - guarded upstream
        raise ValueError("non-finite value supplied to statistical test")
    return arr


def mcnemar_exact(paired_correct_a: Sequence[bool], paired_correct_b: Sequence[bool]) -> dict:
    """Exact McNemar test on two paired binary correctness vectors."""
    a = np.asarray(list(paired_correct_a), dtype=bool)
    b = np.asarray(list(paired_correct_b), dtype=bool)
    if a.shape != b.shape:
        raise ValueError("paired vectors must have equal length")
    n01 = int(np.sum(~a & b))
    n10 = int(np.sum(a & ~b))
    discordant = n01 + n10
    if discordant == 0:
        return {
            "statistic": 0.0,
            "p_value": 1.0,
            "n_discordant": 0,
            "b_intervention_only": n10,
            "c_comparator_only": n01,
            "method": "mcnemar_zero_discordant",
        }
    if _stats is None:  # pragma: no cover
        # Exact two-sided binomial without scipy, using log-space summation.
        k = min(n01, n10)
        p = 0.0
        log_half = math.log(0.5)
        for i in range(0, k + 1):
            log_comb = (
                math.lgamma(discordant + 1)
                - math.lgamma(i + 1)
                - math.lgamma(discordant - i + 1)
            )
            p += math.exp(log_comb + discordant * log_half)
        p = min(1.0, 2.0 * p)
        return {
            "statistic": float(min(n01, n10)),
            "p_value": float(p),
            "n_discordant": discordant,
            "b_intervention_only": n10,
            "c_comparator_only": n01,
            "method": "mcnemar_exact_binomial",
        }
    res = _stats.binomtest(min(n01, n10), discordant, 0.5, alternative="two-sided")
    return {
        "statistic": float(min(n01, n10)),
        "p_value": float(res.pvalue),
        "n_discordant": discordant,
        "b_intervention_only": n10,
        "c_comparator_only": n01,
        "method": "mcnemar_exact_binomial",
    }


def holm_adjust(p_values: Sequence[float]) -> list[float]:
    """Holm-Bonferroni step-down adjustment. Monotone non-decreasing vs raw."""
    p = list(float(x) for x in p_values)
    m = len(p)
    if m == 0:
        return []
    order = sorted(range(m), key=lambda i: p[i])
    adjusted = [0.0] * m
    running = 0.0
    for rank, idx in enumerate(order):
        val = (m - rank) * p[idx]
        running = max(running, val)
        adjusted[idx] = min(1.0, running)
    return adjusted


def benjamini_hochberg(p_values: Sequence[float]) -> list[float]:
    """Benjamini-Hochberg FDR adjustment."""
    p = list(float(x) for x in p_values)
    m = len(p)
    if m == 0:
        return []
    order = sorted(range(m), key=lambda i: p[i])
    adjusted = [0.0] * m
    running = 1.0
    for rank in range(m - 1, -1, -1):
        idx = order[rank]
        val = p[idx] * m / (rank + 1)
        running = min(running, val)
        adjusted[idx] = min(1.0, running)
    return adjusted


def wilson_ci(successes: int, n: int, z: float = 1.959963984540054) -> list[float]:
    """Wilson score interval for a binomial proportion."""
    if n <= 0:
        return [None, None]
    phat = successes / n
    denom = 1 + z * z / n
    center = (phat + z * z / (2 * n)) / denom
    half = z * math.sqrt(phat * (1 - phat) / n + z * z / (4 * n * n)) / denom
    return [max(0.0, center - half), min(1.0, center + half)]


def clopper_pearson_ci(successes: int, n: int, alpha: float = 0.05) -> list[float]:
    """Exact Clopper-Pearson interval for a binomial proportion."""
    if n <= 0:
        return [None, None]
    if _stats is None:  # pragma: no cover
        return wilson_ci(successes, n)
    lo = 0.0 if successes == 0 else float(_stats.beta.ppf(alpha / 2, successes, n - successes + 1))
    hi = 1.0 if successes == n else float(_stats.beta.ppf(1 - alpha / 2, successes + 1, n - successes))
    return [lo, hi]


def cluster_bootstrap_paired(
    diff_by_unit: Sequence[float],
    group_ids: Sequence[str],
    seed: int = 42,
    n: int = 5000,
) -> dict:
    """Cluster bootstrap CI for a paired difference, resampling by group.

    Units sharing a group id are resampled together, which respects the
    correlated-template structure and avoids fake independent-evidence CIs.
    """
    diffs = np.asarray(list(diff_by_unit), dtype=float)
    groups = list(group_ids)
    if diffs.size != len(groups):
        raise ValueError("diff_by_unit and group_ids must align")
    if diffs.size == 0:
        return {"mean": None, "ci_95": [None, None], "n_groups": 0, "n_units": 0, "method": "cluster_bootstrap_paired"}
    uniq = sorted(set(groups))
    index_by_group = {g: [] for g in uniq}
    for i, g in enumerate(groups):
        index_by_group[g].append(i)
    rng = np.random.default_rng(seed)
    means = np.empty(n, dtype=float)
    for b in range(n):
        pick = rng.choice(uniq, size=len(uniq), replace=True)
        idx: list[int] = []
        for g in pick:
            idx.extend(index_by_group[g])
        means[b] = float(diffs[idx].mean())
    lo, hi = np.percentile(means, [2.5, 97.5])
    return {
        "mean": float(diffs.mean()),
        "ci_95": [float(lo), float(hi)],
        "n_groups": len(uniq),
        "n_units": int(diffs.size),
        "resamples": n,
        "method": "cluster_bootstrap_paired",
    }


def cliffs_delta(a: Sequence[float], b: Sequence[float]) -> float:
    """Cliff's delta effect size in [-1, 1]."""
    x = _as_array(a)
    y = _as_array(b)
    if x.size == 0 or y.size == 0:
        return 0.0
    diff = x[:, None] - y[None, :]
    gt = float(np.sum(diff > 0))
    lt = float(np.sum(diff < 0))
    return (gt - lt) / (x.size * y.size)
