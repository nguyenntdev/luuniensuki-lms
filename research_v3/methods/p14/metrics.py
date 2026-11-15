"""P14 metric statistics: CIs and baseline comparisons on audit outcomes.

Reuses the portfolio-standard statistics from research_v3.eval.statistics so
P14 shares one statistical standard with the rest of V3. Per the spec, the
statistical unit is the learning object; CIs are Wilson / Clopper-Pearson on
conformance proportions, and paired baseline-vs-proposed object verdicts use
McNemar where applicable. No claim of learning benefit is derivable from these
numbers (see claims_guard).
"""
from __future__ import annotations

from typing import Any, Sequence

from research_v3.eval.statistics import (
    mcnemar_exact,
    null_result,
    proportion_ci,
)


def conformance_with_ci(passed: int, total: int) -> dict[str, Any]:
    """Conformance rate with both standard binomial CIs (never [0,0] at 0)."""
    if total <= 0:
        return {"rate": None, "n": 0, "passed": passed, **{k: None for k in ("wilson_ci_95", "clopper_pearson_ci_95")}}
    return {
        "rate": round(passed / total, 4),
        "n": total,
        "passed": passed,
        **proportion_ci(passed, total),
    }


def paired_baseline_comparison(
    proposed_pass: Sequence[bool],
    baseline_pass: Sequence[bool],
) -> dict[str, Any]:
    """Exact McNemar on paired object verdicts (proposed vs one baseline).

    This is a comparison of audit verdicts, NOT of learning outcomes; the
    returned note is fixed so the wording cannot drift into benefit language.
    """
    if len(proposed_pass) != len(baseline_pass):
        raise ValueError("paired comparison requires equal-length verdict vectors")
    exact = mcnemar_exact(proposed_pass, baseline_pass)
    return {
        "test": "mcnemar_exact",
        "n_objects": len(proposed_pass),
        "proposed_pass": sum(proposed_pass),
        "baseline_pass": sum(baseline_pass),
        "statistic": exact,
        "note": (
            "Compares audit verdicts only; NOT a learning-outcome comparison and "
            "must not be reported as one."
        ),
    }


def null_or_negative_record(
    *, observed: float | None, baseline: float | None, p_value: float | None
) -> dict[str, Any]:
    """Wrap the portfolio null-result helper for P14's preregistered H0."""
    return null_result(observed=observed, baseline=baseline, p_value=p_value)
