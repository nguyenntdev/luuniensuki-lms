"""Statistical rigorous evaluation module for Research V4.2.

Provides cluster-aware bootstrap confidence intervals, paired delta estimation,
multiplicity corrections (Holm-Bonferroni), permutation tests, and power feasibility analysis.
"""

from __future__ import annotations

import math
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple
import numpy as np


def cluster_bootstrap_ci(
    data_rows: Sequence[Dict[str, Any]],
    cluster_key: str,
    metric_fn: Callable[[Sequence[Dict[str, Any]]], float],
    n_bootstraps: int = 1000,
    alpha: float = 0.05,
    seed: int = 42,
) -> Tuple[float, float, float]:
    """Compute (mean, lower_ci, upper_ci) using cluster-resampled bootstrap.
    
    Resamples whole clusters with replacement to respect intra-cluster correlation.
    """
    rng = np.random.RandomState(seed)
    # Group rows by cluster
    clusters: Dict[Any, List[Dict[str, Any]]] = {}
    for row in data_rows:
        cid = row.get(cluster_key, "default_cluster")
        clusters.setdefault(cid, []).append(row)

    cluster_ids = list(clusters.keys())
    n_clusters = len(cluster_ids)
    if n_clusters == 0:
        return 0.0, 0.0, 0.0

    # If only 1 cluster, fall back to instance bootstrap
    if n_clusters == 1:
        single_cluster_rows = clusters[cluster_ids[0]]
        n_rows = len(single_cluster_rows)
        boot_estimates = []
        for _ in range(n_bootstraps):
            sample_indices = rng.choice(n_rows, size=n_rows, replace=True)
            sampled_rows = [single_cluster_rows[i] for i in sample_indices]
            boot_estimates.append(metric_fn(sampled_rows))
    else:
        boot_estimates = []
        for _ in range(n_bootstraps):
            sampled_cids = rng.choice(cluster_ids, size=n_clusters, replace=True)
            sampled_rows = []
            for cid in sampled_cids:
                sampled_rows.extend(clusters[cid])
            boot_estimates.append(metric_fn(sampled_rows))

    boot_estimates_arr = np.asarray(boot_estimates, dtype=float)
    point_est = float(np.mean(boot_estimates_arr))
    lower = float(np.percentile(boot_estimates_arr, 100.0 * (alpha / 2.0)))
    upper = float(np.percentile(boot_estimates_arr, 100.0 * (1.0 - alpha / 2.0)))
    return point_est, lower, upper


def paired_cluster_bootstrap_delta(
    records: Sequence[Dict[str, Any]],
    cluster_key: str,
    cand_metric_fn: Callable[[Sequence[Dict[str, Any]]], float],
    base_metric_fn: Callable[[Sequence[Dict[str, Any]]], float],
    n_bootstraps: int = 1000,
    alpha: float = 0.05,
    seed: int = 42,
) -> Tuple[float, float, float]:
    """Compute point estimate and 95% CI for paired difference Delta = M(cand) - M(base) via cluster bootstrap."""
    rng = np.random.RandomState(seed)
    clusters: Dict[Any, List[Dict[str, Any]]] = {}
    for row in records:
        cid = row.get(cluster_key, "default_cluster")
        clusters.setdefault(cid, []).append(row)

    cluster_ids = list(clusters.keys())
    n_clusters = len(cluster_ids)
    if n_clusters == 0:
        return 0.0, 0.0, 0.0

    point_delta = cand_metric_fn(records) - base_metric_fn(records)

    deltas = []
    for _ in range(n_bootstraps):
        if n_clusters == 1:
            rows = clusters[cluster_ids[0]]
            n_rows = len(rows)
            idxs = rng.choice(n_rows, size=n_rows, replace=True)
            sampled_rows = [rows[i] for i in idxs]
        else:
            sampled_cids = rng.choice(cluster_ids, size=n_clusters, replace=True)
            sampled_rows = []
            for cid in sampled_cids:
                sampled_rows.extend(clusters[cid])
        d = cand_metric_fn(sampled_rows) - base_metric_fn(sampled_rows)
        deltas.append(d)

    deltas_arr = np.asarray(deltas, dtype=float)
    lower = float(np.percentile(deltas_arr, 100.0 * (alpha / 2.0)))
    upper = float(np.percentile(deltas_arr, 100.0 * (1.0 - alpha / 2.0)))
    return float(point_delta), lower, upper


def paired_permutation_test(
    diffs: Sequence[float],
    n_permutations: int = 2000,
    alternative: str = "greater",
    seed: int = 42,
) -> float:
    """Exact/Monte-Carlo paired permutation (sign randomization) test on difference values."""
    arr = np.asarray(diffs, dtype=float)
    n = len(arr)
    if n == 0:
        return 1.0

    observed_stat = float(np.mean(arr))
    rng = np.random.RandomState(seed)

    signs = rng.choice([-1.0, 1.0], size=(n_permutations, n))
    perm_stats = np.mean(signs * arr, axis=1)

    if alternative == "greater":
        p_val = float(np.mean(perm_stats >= observed_stat))
    elif alternative == "less":
        p_val = float(np.mean(perm_stats <= observed_stat))
    else:  # two-sided
        p_val = float(np.mean(np.abs(perm_stats) >= np.abs(observed_stat)))

    return max(1.0 / n_permutations, p_val)


def holm_bonferroni(p_values: Sequence[float]) -> List[float]:
    """Perform step-down Holm-Bonferroni Family-Wise Error Rate (FWER) multiplicity adjustment.
    
    Given m p-values, sorted p(1) <= p(2) <= ... <= p(m):
    adj_p(k) = min(1.0, max( (m - i + 1) * p(i) for i <= k ))
    """
    m = len(p_values)
    if m == 0:
        return []

    indexed_p = sorted(enumerate(p_values), key=lambda x: x[1])
    adjusted = [0.0] * m

    cum_max = 0.0
    for rank, (orig_idx, p_val) in enumerate(indexed_p):
        multiplier = m - rank
        raw_adj = multiplier * p_val
        cum_max = max(cum_max, raw_adj)
        adjusted[orig_idx] = min(1.0, cum_max)

    return adjusted


def power_feasibility_check(
    n_samples: int,
    n_clusters: int,
    delta_min: float,
    min_instances: int = 30,
    min_clusters: int = 5,
) -> Dict[str, Any]:
    """Check whether a dataset has sufficient sample size and cluster degrees of freedom.
    
    Underpowered datasets (e.g. n < 30 or n_clusters < 5) cannot support generalizable claims.
    """
    issues = []
    if n_samples < min_instances:
        issues.append(f"Insufficient sample size: n={n_samples} < minimum {min_instances}")
    if n_clusters < min_clusters:
        issues.append(f"Insufficient independent clusters: n_clusters={n_clusters} < minimum {min_clusters}")

    adequate = len(issues) == 0
    return {
        "adequate": adequate,
        "n_samples": n_samples,
        "n_clusters": n_clusters,
        "delta_min": delta_min,
        "issues": issues,
    }
