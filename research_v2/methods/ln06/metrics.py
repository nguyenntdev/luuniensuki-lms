"""LN-06 study-specific metrics (secondary observables + primary endpoint).

The shared evaluator (``research_v2.evaluation.metrics``) computes the paired
decision accuracy with exact numerators/denominators and CIs. This module adds
the LN-06 secondary metrics required by the spec (17/18_SECONDARY_METRICS):

- feasible solution rate and false infeasibility rate (primary endpoint pair)
- prerequisite violations on returned routes
- coverage at budget (fraction of targets covered by returned routes)
- travel minutes and dwell minutes decomposition
- cost-regret versus the brute-force certified optimum on solvable cases

All functions operate on prediction + gold rows (oracle material evaluator-side
only) and report exact numerators/denominators.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

from .dataset import TrailCase
from .proposed import solve_case


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with Path(path).open(encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def false_infeasibility_rate(preds: list[Mapping[str, Any]], golds: Mapping[str, str]) -> dict[str, Any]:
    """Rate of `find_valid_route` gold cases predicted infeasible (any reject)."""
    reject_labels = {"no_feasible_route", "cost_exceeded", "reject_cycle", "reject_checkpoint_source"}
    denom = sum(1 for cid, g in golds.items() if g == "find_valid_route")
    numer = sum(
        1
        for row in preds
        if golds.get(row["case_id"]) == "find_valid_route" and row.get("decision") in reject_labels
    )
    return {"numerator": numer, "denominator": denom, "rate": (numer / denom) if denom else None}


def route_quality_metrics(
    preds: list[Mapping[str, Any]],
    cases: Mapping[str, TrailCase],
    *,
    compute_optimum: bool = False,
) -> dict[str, Any]:
    """Dwell/travel decomposition, coverage and (optional) exact regret.

    ``compute_optimum`` runs the brute-force oracle per case - expensive; only
    for small audit samples.
    """
    violations_total = 0
    n_with_route = 0
    travel_total = 0
    dwell_total = 0
    coverage_numer = 0
    coverage_denom = 0
    regrets: list[int] = []
    for row in preds:
        case = cases.get(row["case_id"])
        if case is None:
            continue
        route = tuple(row.get("evidence_ids") or ())
        by_id = {s.id: s for s in case.stops}
        if route and all(sid in by_id for sid in route):
            n_with_route += 1
            acquired: set[str] = set()
            for sid in route:
                violations_total += sum(1 for req in by_id[sid].requires if req not in acquired)
                acquired |= set(by_id[sid].provides)
            dwell_total += sum(by_id[sid].cost for sid in route)
            edges = {(e.source, e.target): e.minutes for e in case.travel_edges}
            travel_total += sum(edges.get((a, b), 0) for a, b in zip(route, route[1:]))
            covered = case.target_outcomes & acquired
            coverage_numer += len(covered)
            coverage_denom += len(case.target_outcomes)
            if compute_optimum and case.target_outcomes <= acquired:
                ref = solve_case(case)
                if ref["decision"] == "find_valid_route":
                    regrets.append(max(0, int(row.get("score") or 0) - int(ref["total_cost"])))
    return {
        "n_routes": n_with_route,
        "prerequisite_violation_total": violations_total,
        "dwell_minutes_total": dwell_total,
        "travel_minutes_total": travel_total,
        "coverage_at_budget": (coverage_numer / coverage_denom) if coverage_denom else None,
        "n_regret_pairs": len(regrets),
        "regret_total": sum(regrets),
        "regret_max": max(regrets) if regrets else None,
    }


def per_class_confusion(preds: list[Mapping[str, Any]], golds: Mapping[str, str]) -> dict[str, Any]:
    confusion: Counter[tuple[str, str]] = Counter()
    for row in preds:
        g = golds.get(row["case_id"])
        if g is not None:
            confusion[(g, str(row.get("decision")))] += 1
    return {f"{g}->{p}": n for (g, p), n in sorted(confusion.items())}


def compute_study_metrics(
    predictions_path: Path,
    gold_path: Path,
    cases: Mapping[str, TrailCase] | None = None,
    *,
    compute_optimum: bool = False,
) -> dict[str, Any]:
    """Full LN-06 secondary metric block for one method/seed cell."""
    preds = load_jsonl(Path(predictions_path))
    golds = {
        row["case_id"]: row["expected_decision"] for row in load_jsonl(Path(gold_path))
    }
    result: dict[str, Any] = {
        "false_infeasibility": false_infeasibility_rate(preds, golds),
        "per_class_confusion": per_class_confusion(preds, golds),
    }
    if cases:
        result["route_quality"] = route_quality_metrics(preds, cases, compute_optimum=compute_optimum)
    return result
