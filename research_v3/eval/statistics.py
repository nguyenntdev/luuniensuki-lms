"""Statistics for Research V3: exact tests, robust CIs, multiple-comparison control.

Reuses the vetted V2 implementations so the whole portfolio shares one standard
and one set of assumptions.
"""
from __future__ import annotations

from typing import Any, Sequence

from research_v2.evaluation.statistical_tests import (  # noqa: F401  (single source of truth)
    benjamini_hochberg,
    cliffs_delta,
    clopper_pearson_ci,
    cluster_bootstrap_paired,
    holm_adjust,
    mcnemar_exact,
    wilson_ci,
)


def paired_report(
    a_correct: Sequence[bool],
    b_correct: Sequence[bool],
    group_ids: Sequence[str],
    *,
    label_a: str = "proposed",
    label_b: str = "baseline",
    seed: int = 42,
    n_boot: int = 2000,
) -> dict[str, Any]:
    """One paired comparison with exact test + cluster bootstrap CI + effect size."""
    diffs = [int(x) - int(y) for x, y in zip(a_correct, b_correct)]
    return {
        "a": label_a,
        "b": label_b,
        "n": len(diffs),
        "mean_diff": (sum(diffs) / len(diffs)) if diffs else None,
        "mcnemar": mcnemar_exact(a_correct, b_correct),
        "cluster_bootstrap": cluster_bootstrap_paired(diffs, group_ids, seed=seed, n=n_boot),
        "cliffs_delta": cliffs_delta(
            [1.0 if x else 0.0 for x in a_correct],
            [1.0 if x else 0.0 for x in b_correct],
        ),
    }


def family_control(p_values: Sequence[float], *, method: str = "holm") -> list[float]:
    """Multiple-comparison correction across a paper's confirmatory family."""
    if method == "holm":
        return holm_adjust(p_values)
    if method == "bh":
        return benjamini_hochberg(p_values)
    raise ValueError(f"unknown correction method {method!r}")


def proportion_ci(successes: int, n: int) -> dict[str, list[float | None]]:
    """Both Wilson and Clopper-Pearson, so zero-error rates never report [0, 0]."""
    return {
        "wilson_ci_95": wilson_ci(successes, n),
        "clopper_pearson_ci_95": clopper_pearson_ci(successes, n),
    }


def null_result(*, observed: float | None, baseline: float | None, p_value: float | None) -> dict[str, Any]:
    """Explicit null/negative result record; never silently dropped."""
    is_null = (
        observed is None
        or baseline is None
        or p_value is None
        or p_value >= 0.05
        or observed <= baseline
    )
    return {
        "observed": observed,
        "baseline": baseline,
        "p_value": p_value,
        "is_null_or_negative": bool(is_null),
        "note": "Reported as a null/negative result; not tuned toward a positive claim.",
    }
