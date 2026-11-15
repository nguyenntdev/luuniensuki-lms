"""P02 INDEPENDENT oracle: brute-force certification of the true optimum.

Evaluator-side material ONLY. Solvers must never import this module — the
oracle shares no code with any solver in ``solvers.py`` (independence by
design, mirroring the LN-06 rubric pattern). If a solver's exactness claim
were wrong, this oracle must be able to disagree with it.

The oracle enumerates over subsets x permutations directly from first
principles: for every subset of usable activities that covers all targets,
try every permutation, keep those where every prerequisite is already
acquired in prefix order, and take the minimum dwell+travel cost. Costs are
computed from the raw problem fields, never via solver helpers.

Raises ``OracleError`` on oversized instances rather than guessing (fail-
closed): no fabricated optima, ever.
"""
from __future__ import annotations

import itertools
from dataclasses import dataclass
from typing import Any

from .problems import PlanningProblem

MAX_ORACLE_ACTIVITIES = 12
MAX_ORACLE_ROUTE = 12  # Held-Karp DP ceiling: 2^12 * 144 states, exact


class OracleError(ValueError):
    """Raised when the oracle cannot certify an instance (too large)."""


@dataclass(frozen=True)
class OracleVerdict:
    problem_id: str
    decision: str  # find_valid_route | no_feasible_route | cost_exceeded
    optimum_cost: int | None  # None when infeasible
    optimal_route: tuple[str, ...] | None
    best_over_budget_cost: int | None  # min cost among feasible-order subsets over budget


def _covers(targets: frozenset[str], subset: tuple[str, ...], provides: dict[str, frozenset[str]]) -> bool:
    covered: set[str] = set()
    for sid in subset:
        covered |= provides[sid]
    return targets <= covered


def _min_ordered_cost(
    subset: tuple[str, ...],
    requires: dict[str, frozenset[str]],
    provides: dict[str, frozenset[str]],
    costs: dict[str, int],
    travel: Any,
) -> int | None:
    """Min dwell+travel over valid orderings; None when none exists.

    Independent re-implementation, exact for both cases:
    - No travel edges: Kahn's algorithm decides whether any topological order
      exists (dwell is order-independent).
    - With travel: Held-Karp bitmask DP over (visited_mask, last) with a
      prefix-prerequisite feasibility check — 2^k * k^2, exact, and much
      faster than enumerating k! permutations.
    """
    dwell = sum(costs[sid] for sid in subset)
    if not travel:
        deps: dict[str, set[str]] = {sid: set() for sid in subset}
        providers_of: dict[str, list[str]] = {}
        for sid in subset:
            for o in provides[sid]:
                providers_of.setdefault(o, []).append(sid)
        for sid in subset:
            for req in requires[sid]:
                ps = providers_of.get(req)
                if not ps:
                    return None  # unmet prerequisite inside this subset
                deps[sid] |= {p for p in ps if p != sid}
        indeg = {sid: len(d) for sid, d in deps.items()}
        queue = [sid for sid, d in indeg.items() if d == 0]
        seen = 0
        while queue:
            cur = queue.pop()
            seen += 1
            for sid in subset:
                if cur in deps[sid]:
                    deps[sid].discard(cur)
                    indeg[sid] -= 1
                    if indeg[sid] == 0:
                        queue.append(sid)
        return dwell if seen == len(subset) else None

    k = len(subset)
    if k == 0:
        return 0
    if k > MAX_ORACLE_ROUTE:
        raise OracleError(f"ordered subset too large for the DP: {k}")
    index = {sid: i for i, sid in enumerate(subset)}
    full = (1 << k) - 1
    # acquired outcomes per mask
    acq: list[frozenset[str]] = [frozenset()] * (1 << k)
    for mask in range(1, 1 << k):
        low = mask & -mask
        i = low.bit_length() - 1
        acq[mask] = acq[mask ^ low] | provides[subset[i]]
    INF = 10**15
    best: dict[tuple[int, int], int] = {}
    for i, sid in enumerate(subset):
        if not requires[sid]:
            best[(1 << i, i)] = costs[sid]
    for mask in range(1 << k):
        acquired = acq[mask]
        for i in range(k):
            if not (mask >> i) & 1:
                continue
            base = best.get((mask, i))
            if base is None:
                continue
            for j in range(k):
                if (mask >> j) & 1:
                    continue
                if any(r not in acquired for r in requires[subset[j]]):
                    continue
                step = costs[subset[j]] + travel.get((subset[i], subset[j]), 0)
                key = (mask | (1 << j), j)
                val = base + step
                if val < best.get(key, INF):
                    best[key] = val
    finals = [v for (mask, _i), v in best.items() if mask == full]
    return min(finals) if finals else None


def brute_force_verdict(problem: PlanningProblem) -> OracleVerdict:
    """Exact decision + optimum by exhaustive enumeration (small instances)."""
    n = len(problem.activities)
    if n > MAX_ORACLE_ACTIVITIES:
        raise OracleError(
            f"oracle limited to {MAX_ORACLE_ACTIVITIES} activities; "
            f"{problem.problem_id!r} has {n}"
        )
    usable = problem.usable_activities()
    if len(usable) > MAX_ORACLE_ROUTE + 3:  # keep subset dimension bounded
        raise OracleError(
            f"oracle limited to {MAX_ORACLE_ROUTE + 3} usable activities; "
            f"{problem.problem_id!r} has {len(usable)}"
        )

    provides = {a.id: frozenset(a.provides) for a in usable}
    requires = {a.id: frozenset(a.requires) for a in usable}
    costs = {a.id: a.cost for a in usable}
    ids = tuple(a.id for a in usable)

    covered_by_usable: set[str] = set()
    for sid in ids:
        covered_by_usable |= provides[sid]
    if not problem.targets <= covered_by_usable:
        return OracleVerdict(problem.problem_id, "no_feasible_route", None, None, None)

    best_cost: int | None = None
    best_route: tuple[str, ...] | None = None
    best_over_budget: int | None = None

    for r in range(len(ids) + 1):
        for subset in itertools.combinations(ids, r):
            if not _covers(problem.targets, subset, provides):
                continue
            cost = _min_ordered_cost(subset, requires, provides, costs, problem.travel)
            if cost is None:
                continue
            if best_over_budget is None or cost < best_over_budget:
                best_over_budget = cost
            if best_cost is None or cost < best_cost:
                best_cost = cost
                best_route = subset

    if best_cost is None:
        return OracleVerdict(problem.problem_id, "no_feasible_route", None, None, None)
    if best_cost > problem.budget:
        return OracleVerdict(
            problem.problem_id, "cost_exceeded", best_cost, best_route, best_over_budget
        )
    return OracleVerdict(
        problem.problem_id, "find_valid_route", best_cost, best_route, best_over_budget
    )
