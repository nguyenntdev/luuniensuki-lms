"""LN-06 scoring rubric and audit-oracle helpers.

The rubric encodes the auditable oracle basis (``PEDAGOGICAL_DAG_CONSTRAINTS``)
as an INDEPENDENT feasibility checker: it re-derives the expected decision for
a case from first principles (brute force over subsets for small instances),
without importing the proposed solver. It is evaluator-side material and must
never be imported by an inference-time policy.

Independence guarantee: cycle certification is re-implemented inside this
module (worklist dead-end cascade + least-fixpoint reachability probe) and
shares no code with the proposed policy's ``cyclic_outcomes`` — if the
policy's certification were wrong, this oracle remains able to disagree
with it.
"""
from __future__ import annotations

import itertools
from collections import deque
from typing import Any

from .dataset import Stop, TrailCase


class RubricError(ValueError):
    """Raised when the rubric cannot certify a case."""


# ---------------------------------------------------------------------------
# Independent cycle certification (no shared code with the proposed policy)
# ---------------------------------------------------------------------------

def _oracle_blocked_outcomes(stops: tuple[Stop, ...]) -> frozenset[str]:
    """Independently certify which outcomes are blocked by circular prerequisites.

    Re-implemented from first principles for oracle independence (the proposed
    policy's ``cyclic_outcomes`` is deliberately NOT imported here, so a bug in
    the policy cannot make oracle and policy agree wrongly).

    Worklist cascade (Kahn-style reverse elimination): repeatedly retire any
    stop that requires an outcome provided by no remaining stop — a missing
    prerequisite, not a cycle — since it can never be visited; retiring removes
    its outcomes from the provider index and repeats to a fixpoint.
    Every outcome still provided by a surviving stop is then probed with a
    least-fixpoint reachability search over prerequisite "generations": an
    outcome becomes reachable when some surviving stop that provides it needs
    only reachable prerequisites. An outcome that is provided yet unreachable
    can only be explained by a circular dependency, because any acyclic
    dependency chain bottoms out at requires-free stops, which are always
    reachable. The least fixpoint exists and is unique (monotone operator on
    a finite lattice), so the certification is deterministic.
    """
    if not stops:
        return frozenset()
    by_id = {s.id: s for s in stops}
    providers: dict[str, set[str]] = {}
    for s in stops:
        for o in s.provides:
            providers.setdefault(o, set()).add(s.id)
    provided: set[str] = set(providers)

    # Worklist cascade: retire stops whose prerequisites can never be met by
    # any surviving stop. A stop is a dead end when some required outcome has
    # no remaining provider at all (missing prerequisite). Retiring removes
    # the stop's outcomes from the provider index, which may cascade. A stop
    # that is the SOLE provider of one of its own required outcomes is NOT
    # retired here: its outcome keeps a provider but can never be acquired,
    # and the reachability probe below certifies it as cyclic (a deadlock).
    dead: set[str] = set()
    queue = deque(by_id)
    while queue:
        sid = queue.popleft()
        if sid in dead:
            continue
        if not any(r not in provided for r in by_id[sid].requires):
            continue
        dead.add(sid)
        for o in by_id[sid].provides:
            if o in providers:
                providers[o].discard(sid)
                if not providers[o]:
                    provided.discard(o)
        queue.extend(by_id)

    # Reachability probe over the surviving structure: an outcome is
    # reachable when some surviving provider of it needs only already-
    # reachable prerequisites (least fixpoint over prerequisite generations).
    # Acyclic chains always bottom out at requires-free survivors, so a
    # provided-but-unreachable outcome certifies a circular dependency.
    reachable: set[str] = set()
    changed = True
    while changed:
        newly = {
            o
            for o in provided
            if o not in reachable
            and any(all(r in reachable for r in by_id[p].requires) for p in providers[o])
        }
        changed = bool(newly)
        reachable |= newly
    return frozenset(provided - reachable)


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
    if _oracle_blocked_outcomes(case.stops):
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
