"""Calibration and subgroup-robustness reporting.

Accuracy alone is not enough for a risk/ranking study: report calibration and
worst-group performance so a headline number cannot hide a broken subgroup.
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence

from research_v2.evaluation.statistical_tests import wilson_ci


def reliability_bins(
    probs: Sequence[float],
    outcomes: Sequence[int],
    *,
    n_bins: int = 10,
) -> list[dict[str, Any]]:
    """Equal-width reliability bins with per-bin observed frequency and count."""
    if len(probs) != len(outcomes):
        raise ValueError("probs and outcomes must align")
    if not probs:
        return []
    bins: list[list[tuple[float, int]]] = [[] for _ in range(n_bins)]
    for p, y in zip(probs, outcomes):
        idx = min(n_bins - 1, max(0, int(p * n_bins)))
        bins[idx].append((p, y))
    out: list[dict[str, Any]] = []
    for i, bucket in enumerate(bins):
        lo, hi = i / n_bins, (i + 1) / n_bins
        if not bucket:
            out.append({"bin": [lo, hi], "n": 0, "mean_prob": None, "observed": None})
            continue
        mean_p = sum(p for p, _ in bucket) / len(bucket)
        observed = sum(y for _, y in bucket) / len(bucket)
        out.append(
            {
                "bin": [lo, hi],
                "n": len(bucket),
                "mean_prob": mean_p,
                "observed": observed,
                "observed_ci_95": wilson_ci(sum(y for _, y in bucket), len(bucket)),
            }
        )
    return out


def expected_calibration_error(bins: Sequence[Mapping[str, Any]]) -> float | None:
    """Weighted gap between predicted probability and observed frequency."""
    total = sum(int(b["n"]) for b in bins)
    if total == 0:
        return None
    err = 0.0
    for b in bins:
        if not b["n"]:
            continue
        err += (int(b["n"]) / total) * abs(float(b["mean_prob"]) - float(b["observed"]))
    return err


def worst_group(
    subgroup_correct: Mapping[str, Sequence[bool]],
    *,
    min_n: int = 20,
) -> dict[str, Any] | None:
    """Return the lowest-accuracy subgroup meeting a minimum size, with a CI."""
    evaluated = []
    for name, flags in subgroup_correct.items():
        n = len(flags)
        if n < min_n:
            continue
        correct = sum(1 for f in flags if f)
        evaluated.append(
            {
                "group": name,
                "n": n,
                "accuracy": correct / n,
                "ci_95": wilson_ci(correct, n),
            }
        )
    if not evaluated:
        return None
    return min(evaluated, key=lambda g: g["accuracy"])


def robustness_report(
    per_group: Mapping[str, Sequence[bool]],
    *,
    min_n: int = 20,
) -> dict[str, Any]:
    """Macro-average across groups plus the worst group, so shifts cannot hide."""
    groups = [g for g, flags in per_group.items() if len(flags) >= min_n]
    macro = None
    if groups:
        macro = sum(
            sum(1 for f in per_group[g] if f) / len(per_group[g]) for g in groups
        ) / len(groups)
    return {
        "n_groups_evaluated": len(groups),
        "macro_accuracy": macro,
        "worst_group": worst_group(per_group, min_n=min_n),
        "groups_below_min_n_skipped": sorted(
            g for g, flags in per_group.items() if len(flags) < min_n
        ),
    }
