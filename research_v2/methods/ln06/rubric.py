"""LN-06 scoring rubric and audit-oracle helpers.

The rubric encodes the auditable oracle basis (``PEDAGOGICAL_DAG_CONSTRAINTS``)
as an INDEPENDENT feasibility checker: it re-derives the expected decision for
a case from first principles (brute force over subsets for small instances),
without importing the proposed solver. It is evaluator-side material and must
never be imported by an inference-time policy.
"""
from __future__ import annotations

import itertools
from typing import Any

from .dataset import Stop, TrailCase
from .proposed import cyclic_outcomes


class RubricError(ValueError):
    """Raised when the rubric cannot certify a case."""


def _covers(targets: frozenset[str], chosen: tuple[str, ...], by_id: dict[str, Stop]) -> bool:
    covered: set[str] = set()
    for sid in chosen:
        covered |= set(by_id[sid].provides)
    return targets <= covered


def _order_ok(chosen: tuple[str, ...], by_id: dict[str, Stop]) -> bool:
    acquired: set[str] = set()
    for sid in chosen:
        if any(req not in acquired for req in by_id[sid].requires):
            return False
        acquired |= set(by_id[sid].provides)
    return True


def _topological_order_exists(chosen: tuple[str, ...], by_id: dict[str, Stop]) -> bool:
    """Kahn's algorithm over the chosen subset's internal dependencies."""
    providers_of: dict[str, list[str]] = {}
    for sid in chosen:
        for o in by_id[sid].provides:
            providers_of.setdefault(o, []).append(sid)
    deps: dict[str, set[str]] = {sid: set() for sid in chosen}
    for sid in chosen:
        for req in by_id[sid].requires:
            providers = providers_of.get(req, ())
            if not providers:
                # No provider exists among the chosen stops: the requirement
                # can never be satisfied, so no valid order exists.
                return False
            for provider in providers:
                if provider != sid:
                    deps[sid].add(provider)
    indegree = {sid: len(d) for sid, d in deps.items()}
    queue = [sid for sid, d in indegree.items() if d == 0]
    seen = 0
    while queue:
        current = queue.pop()
        seen += 1
        for sid, d in deps.items():
            if current in d:
                d.discard(current)
                indegree[sid] -= 1
                if indegree[sid] == 0:
                    queue.append(sid)
    return seen == len(chosen)


def brute_force_expected_decision(case: TrailCase, *, max_stops: int = 12) -> str:
    """Independent oracle: brute-force certified expected decision.

    Enumeration over subsets of available stops (exact for len(stops) <=
    ``max_stops``). Raises :class:`RubricError` on oversized instances rather
    than guessing.
    """
    by_id = {s.id: s for s in case.stops}
    if len(case.stops) > max_stops:
        raise RubricError(
            f"brute-force oracle limited to {max_stops} stops; case {case.case_id!r} has {len(case.stops)}"
        )
    if not case.checkpoint_claim_verified:
        return "reject_checkpoint_source"
    if cyclic_outcomes(case.stops):
        return "reject_cycle"

    available = tuple(sorted(case.available_stops & set(by_id)))
    covered_by_available = {o for sid in available for o in by_id[sid].provides}
    if not case.target_outcomes <= covered_by_available:
        return "no_feasible_route"

    best_cost: int | None = None
    for r in range(len(available) + 1):
        for subset in itertools.combinations(available, r):
            if not _covers(case.target_outcomes, subset, by_id):
                continue
            if not case.travel_edges:
                # Without travel edges any topological order works iff one
                # exists; dwell cost is order-independent.
                if not _topological_order_exists(subset, by_id):
                    continue
                cost = sum(by_id[sid].cost for sid in subset)
            else:
                # With travel edges, order matters; try every permutation.
                valid_costs = [
                    sum(by_id[sid].cost for sid in subset)
                    + sum(
                        next(
                            (
                                e.minutes
                                for e in case.travel_edges
                                if e.source == a and e.target == b
                            ),
                            0,
                        )
                        for a, b in zip(perm, perm[1:])
                    )
                    for perm in itertools.permutations(subset)
                    if _order_ok(perm, by_id)
                ]
                if not valid_costs:
                    continue
                cost = min(valid_costs) if subset else 0
            if best_cost is None or cost < best_cost:
                best_cost = cost
    if best_cost is None:
        return "no_feasible_route"
    return "cost_exceeded" if best_cost > case.time_budget_minutes else "find_valid_route"


def score_prediction(pred_decision: str, expected: str) -> dict[str, Any]:
    """Paired rubric row for one case: exact-match plus error taxonomy."""
    is_match = pred_decision == expected
    error_class: str | None = None
    if not is_match:
        if expected == "find_valid_route":
            error_class = "false_infeasibility"
        elif pred_decision == "find_valid_route":
            error_class = "false_acceptance"
        else:
            error_class = "wrong_rejection_reason"
    return {
        "pred": pred_decision,
        "expected": expected,
        "correct": is_match,
        "error_class": error_class,
    }
