"""P06 selection-quality metrics (NON-CAUSAL).

All metrics measure ranking/selection quality against realized outcomes.
Nothing here may be reinterpreted as an intervention effect (METHOD.md §1).
Reuses vetted CIs from ``research_v3/eval/statistics.py``.
"""
from __future__ import annotations

import math
from typing import Any, Mapping, Sequence

from research_v3.eval.statistics import proportion_ci
from research_v3.methods.p06.selection import (
    K_ANONYMITY_MIN_N,
    Candidate,
    SelectionResult,
    suppress_small_cells,
)


def precision_at_k(selected: Sequence[str], candidates: Mapping[str, Candidate]) -> float | None:
    if not selected:
        return None
    hits = sum(1 for cid in selected if candidates[cid].is_fail)
    return hits / len(selected)


def recall_at_k(
    selected: Sequence[str],
    candidates: Mapping[str, Candidate],
    *,
    total_fails: int,
) -> float | None:
    """Primary metric: failure capture among all Fail cases in the cohort."""
    if total_fails <= 0:
        return None
    hits = sum(1 for cid in selected if candidates[cid].is_fail)
    return hits / total_fails


def ndcg_at_k(
    selected: Sequence[str],
    candidates: Mapping[str, Candidate],
    *,
    k: int,
) -> float | None:
    """Binary-relevance NDCG over the eligible ranked list (log discount).

    Ideal ranking = all fails first; gain vector uses the cohort's eligible
    learners. Returns None when there are no eligible learners or no fails.
    """
    pool = [c for c in candidates.values() if c.risk >= 0.0 and c.case_id]
    eligible = [c for c in pool if c.case_id in {s for s in selected} or c.has_actionable_evidence]
    if not eligible or not any(c.is_fail for c in eligible):
        return None
    dcg = 0.0
    for rank, cid in enumerate(selected[:k], start=1):
        rel = 1.0 if candidates[cid].is_fail else 0.0
        dcg += rel / math.log2(rank + 1)
    n_fails_eligible = sum(1 for c in eligible if c.is_fail)
    ideal_hits = min(n_fails_eligible, k)
    idcg = sum(1.0 / math.log2(r + 1) for r in range(1, ideal_hits + 1))
    if idcg <= 0:
        return None
    return dcg / idcg


def subgroup_coverage(
    selected: Sequence[str],
    candidates: Mapping[str, Candidate],
    *,
    pools: Mapping[str, int],
    minima: Mapping[str, int],
) -> dict[str, dict[str, Any]]:
    """Per-group coverage of the equity floor, with k-anonymity suppression.

    Uniform semantics (preregistered, METHOD.md §7):
    coverage_g = |S ∩ g| / min(m_g, |E_g|) when the denominator is defined
    (m_g > 0 and pool_g > 0), else ``value=None, reason="no_required_seats"``.
    Cells with |S ∩ g| < min_n are suppressed (value None, reason recorded).
    """
    sel_counts: dict[str, int] = {}
    for cid in selected:
        g = candidates[cid].subgroup
        sel_counts[g] = sel_counts.get(g, 0) + 1
    raw: dict[str, dict[str, Any]] = {}
    for g, m in minima.items():
        if m <= 0 or pools.get(g, 0) <= 0:
            raw[g] = {"n": int(sel_counts.get(g, 0)), "value": None, "reason": "no_required_seats"}
            continue
        denom = min(m, pools.get(g, 0))
        raw[g] = {"n": int(sel_counts.get(g, 0)), "value": sel_counts.get(g, 0) / denom, "reason": None}
    # suppress small selected cells (k-anonymity on reported stats)
    for g, rec in raw.items():
        if rec["n"] < K_ANONYMITY_MIN_N and rec["reason"] is None:
            suppressed = suppress_small_cells({g: rec["n"]})[g]
            rec.update(suppressed)
    return raw


def fairness_gap(coverage: Mapping[str, Mapping[str, Any]], *, disadvantaged: str = "Y", advantaged: str = "N") -> float | None:
    """coverage_disadvantaged - coverage_advantaged; None if either suppressed.

    Preregistered direction: gap <= 0 desired (disability group not
    under-covered). Suppressed cells propagate as None, never as 0.
    """
    cy = coverage.get(disadvantaged, {}).get("value")
    cn = coverage.get(advantaged, {}).get("value")
    if cy is None or cn is None:
        return None
    return float(cy) - float(cn)


def metrics_for_round(
    result: SelectionResult,
    candidates: Mapping[str, Candidate],
    *,
    k: int,
    minima: Mapping[str, int],
    pools: Mapping[str, int],
    total_fails: int,
) -> dict[str, Any]:
    """One selection round -> full metric record (all provisional CIs attached)."""
    selected = list(result.selected)
    p = precision_at_k(selected, candidates)
    r = recall_at_k(selected, candidates, total_fails=total_fails)
    n = len(selected)
    record: dict[str, Any] = {
        "k": int(k),
        "n_selected": n,
        "capacity_violation": bool(n > k),
        "precision_at_k": p,
        "recall_at_k": r,
        "ndcg_at_k": ndcg_at_k(selected, candidates, k=k),
        "n_fails_in_cohort": int(total_fails),
    }
    if p is not None and n > 0:
        record["precision_ci_95"] = proportion_ci(int(round(p * n)), n)
    else:
        record["precision_ci_95"] = {"wilson_ci_95": [None, None], "clopper_pearson_ci_95": [None, None]}
    cov = subgroup_coverage(selected, candidates, pools=pools, minima=minima)
    record["subgroup_coverage"] = cov
    record["fairness_gap"] = fairness_gap(cov)
    return record
