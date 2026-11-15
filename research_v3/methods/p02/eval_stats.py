"""P02 statistics wrappers: reuse the vetted V2/V3 shared implementations.

The confirmatory comparison family for P02 is paired by instance family;
cost-difference distributions are tested with Wilcoxon signed-rank (paired,
non-normal-safe) with cluster bootstrap CIs by family_id, plus exact
proportion CIs for feasibility rates.
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
from research_v3.eval.statistics import proportion_ci  # noqa: F401


def paired_report(
    diffs: Sequence[float],
    group_ids: Sequence[str],
    *,
    label_a: str,
    label_b: str,
    seed: int = 42,
    n_boot: int = 2000,
) -> dict[str, Any]:
    """Paired cost-difference report: Wilcoxon + cluster bootstrap CI + effect size."""
    if len(diffs) != len(group_ids):
        raise ValueError("diffs and group_ids must align")
    report: dict[str, Any] = {
        "a": label_a,
        "b": label_b,
        "n": len(diffs),
        "mean_diff": (sum(diffs) / len(diffs)) if diffs else None,
        "note": "cost(a) - cost(b) on commonly feasible instances; positive means a is more expensive",
    }
    if diffs and _scipy_available():
        from research_v2.evaluation.statistical_tests import _as_array  # type: ignore

        try:
            from scipy import stats as _stats

            arr = _as_array(diffs)
            if float(arr.max()) == float(arr.min()):
                report["wilcoxon"] = {
                    "statistic": None,
                    "p_value": 1.0,
                    "note": "all paired differences identical; no evidence of a difference",
                }
            else:
                stat, p = _stats.wilcoxon(arr)
                report["wilcoxon"] = {"statistic": float(stat), "p_value": float(p)}
        except Exception as exc:  # pragma: no cover - degrade, never fabricate
            report["wilcoxon"] = {"statistic": None, "p_value": None, "error": str(exc)}
    else:
        report["wilcoxon"] = {"statistic": None, "p_value": None, "note": "scipy unavailable or no pairs"}
    if diffs:
        report["cluster_bootstrap"] = cluster_bootstrap_paired(
            list(diffs), list(group_ids), seed=seed, n=n_boot
        )
        nonzeros = [d for d in diffs if d != 0]
        report["cliffs_delta"] = cliffs_delta(nonzeros, [0.0] * len(nonzeros)) if nonzeros else 0.0
    else:
        report["cluster_bootstrap"] = None
        report["cliffs_delta"] = None
    return report


def _scipy_available() -> bool:
    try:
        import scipy  # noqa: F401
        return True
    except Exception:
        return False
