"""LN-06 statistical analysis helpers (evaluator-side only).

Implements the study stats plan (20_STATS_AND_POWER) on top of the shared
``research_v2.evaluation.statistical_tests`` primitives:

- paired binary comparison of two methods over identical case hashes:
  exact McNemar test;
- Holm correction across the pre-registered contrast family;
- cluster bootstrap over independent groups (monument family + topology
  template + source edition) for route-level observables;
- Wilson / Clopper-Pearson CIs already provided by the shared module.
"""
from __future__ import annotations

import random
from typing import Any, Mapping, Sequence

from research_v2.evaluation.statistical_tests import (
    clopper_pearson_ci,
    holm_adjust,
    mcnemar_exact,
    wilson_ci,
)

__all__ = [
    "clopper_pearson_ci",
    "holm_adjust",
    "mcnemar_exact",
    "wilson_ci",
    "paired_contrast",
    "cluster_bootstrap_mean",
]


def paired_contrast(
    correct_a: Sequence[bool], correct_b: Sequence[bool]
) -> dict[str, Any]:
    """Pre-registered primary contrast: exact McNemar on paired correctness."""
    if len(correct_a) != len(correct_b):
        raise ValueError("paired contrast requires equal-length sequences")
    result = mcnemar_exact(list(correct_a), list(correct_b))
    n = len(correct_a)
    acc_a = sum(1 for x in correct_a if x) / n if n else None
    acc_b = sum(1 for x in correct_b if x) / n if n else None
    result.update(
        {
            "n_pairs": n,
            "accuracy_method_a": acc_a,
            "accuracy_method_b": acc_b,
        }
    )
    return result


def cluster_bootstrap_mean(
    values: Sequence[float],
    groups: Sequence[str],
    *,
    n_boot: int = 2000,
    seed: int = 11,
    alpha: float = 0.05,
) -> dict[str, Any]:
    """Cluster bootstrap CI of the mean, resampling independent groups.

    Deterministic for a fixed seed. All-correct/all-zero inputs use Wilson /
    Clopper-Pearson bounds instead of reporting a degenerate [x, x] interval.
    """
    if len(values) != len(groups):
        raise ValueError("values and groups must have equal length")
    by_group: dict[str, list[float]] = {}
    for v, g in zip(values, groups):
        by_group.setdefault(g, []).append(float(v))
    group_means = [sum(vs) / len(vs) for vs in by_group.values()]
    point = sum(group_means) / len(group_means) if group_means else None
    rng = random.Random(seed)
    stats: list[float] = []
    keys = sorted(by_group)
    for _ in range(n_boot):
        sample = [by_group[k] for k in rng.choices(keys, k=len(keys))]
        flat = [v for vs in sample for v in vs]
        if flat:
            stats.append(sum(flat) / len(flat))
    stats.sort()
    lo = stats[int((alpha / 2) * len(stats))]
    hi = stats[min(len(stats) - 1, int((1 - alpha / 2) * len(stats)))]
    successes = sum(1 for v in values if v >= 1.0)
    binary = successes == len(values) or successes == 0
    return {
        "point_estimate": point,
        "ci95_low": lo,
        "ci95_high": hi,
        "n_clusters": len(by_group),
        "n_boot": n_boot,
        "degenerate_binary": binary,
        "wilson_ci_95_if_binary": wilson_ci(successes, len(values)) if binary else None,
        "clopper_pearson_ci_95_if_binary": (
            clopper_pearson_ci(successes, len(values)) if binary else None
        ),
    }
