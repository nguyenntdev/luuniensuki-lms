"""LN-06 baseline policies (C0 sanity + C1 strong classical).

- ``b0`` (``baselines_b0`` alias): naive reverse input-order tourist walk.
  Ignores the prerequisite DAG entirely; prerequisite violations are visible
  in reason codes. SANITY_ONLY comparator - never a strong baseline.
- ``c1`` (``baselines_c1`` alias): A*/Dijkstra shortest-travel-path baseline
  on the travel-only objective - the classical serious comparator. It picks
  the cheapest path of stops that reaches every target outcome (stop choice =
  shortest route on the weighted travel/dwell graph), then orders by that
  path. Prerequisite order is deliberately IGNORED, which is exactly the
  matched-subtask weakness under study: it minimises travel while violating
  pedagogical ordering.

Both baselines share the legitimate input features, the budget semantics and
the LN-06 label space with I1. Neither shares implementation code with the
proposed solver (independent decision procedures by design).
"""
from __future__ import annotations

import heapq
from typing import Any, Mapping

from .dataset import DatasetError, TrailCase
from .labels import (
    REASON_ASTAR_TRAVEL_ONLY,
    REASON_BASELINE_NAIVE,
    REASON_OVER_BUDGET,
    REASON_SOURCE_GAP,
    build_prediction,
)

STUDY_ID = "LN-06"


# ---------------------------------------------------------------------------
# B0 - naive reverse-order tourist walk (C0, SANITY_ONLY)
# ---------------------------------------------------------------------------

def b0_solve(case: TrailCase) -> dict[str, Any]:
    stops_by_id = {s.id: s for s in case.stops}
    if not case.checkpoint_claim_verified:
        # b0 is sloppy, but a hard provenance wall is study policy for every
        # method sharing the label space; refusing here keeps comparability.
        return {
            "decision": "reject_checkpoint_source",
            "reason_codes": (REASON_SOURCE_GAP, "b0_naive"),
            "route": (),
            "total_cost": 0,
        }
    naive = tuple(
        s.id for s in reversed(case.stops) if s.id in case.available_stops
    )
    dwell = sum(stops_by_id[sid].cost for sid in naive)
    acquired: set[str] = set()
    violations = 0
    for sid in naive:
        for req in stops_by_id[sid].requires:
            if req not in acquired:
                violations += 1
        acquired |= set(stops_by_id[sid].provides)
    covered = case.target_outcomes & acquired
    total = dwell
    reasons = [REASON_BASELINE_NAIVE, f"prerequisite_violations:{violations}"]
    if total > case.time_budget_minutes:
        return {
            "decision": "cost_exceeded",
            "reason_codes": tuple(reasons + [REASON_OVER_BUDGET]),
            "route": naive,
            "total_cost": total,
        }
    if covered < case.target_outcomes:
        return {
            "decision": "no_feasible_route",
            "reason_codes": tuple(reasons + ["unreachable_outcome"]),
            "route": naive,
            "total_cost": total,
        }
    return {
        "decision": "find_valid_route",
        "reason_codes": tuple(reasons),
        "route": naive,
        "total_cost": total,
    }


# ---------------------------------------------------------------------------
# C1 - A* shortest travel path ignoring prerequisite order (C1, strong)
# ---------------------------------------------------------------------------

def _adjacency(case: TrailCase) -> dict[str, list[tuple[str, int]]]:
    """Weighted directed adjacency: dwell cost + travel minutes per move."""
    by_id = {s.id: s for s in case.stops}
    travel: dict[tuple[str, str], int] = {}
    for e in case.travel_edges:
        travel[(e.source, e.target)] = e.minutes
    adj: dict[str, list[tuple[str, int]]] = {}
    ids = [s.id for s in case.stops if s.id in case.available_stops]
    for a in ids:
        adj.setdefault(a, [])
        for b in ids:
            if a == b:
                continue
            # Uniform fallback weight when no explicit edge exists: symmetric
            # placeholder so the travel-only graph stays connected.
            adj[a].append((b, travel.get((a, b), 1)))
    return adj


def c1_solve(case: TrailCase) -> dict[str, Any]:
    """A* over states (current stop, acquired outcomes) minimising travel+dwell.

    Prerequisite ordering is NOT enforced as a search constraint - the state
    merely tracks which outcomes have been picked up along the walked path.
    Goal: all target outcomes acquired. If no available stop provides a target
    outcome, the goal is unreachable -> ``no_feasible_route`` (honest, cheap,
    and the one place C1 legitimately agrees with certification).
    """
    by_id = {s.id: s for s in case.stops}
    if not case.checkpoint_claim_verified:
        return {
            "decision": "reject_checkpoint_source",
            "reason_codes": (REASON_SOURCE_GAP, "c1_astar"),
            "route": (),
            "total_cost": 0,
        }

    start_providers: dict[str, list[str]] = {}
    for sid in sorted(case.available_stops & set(by_id)):
        for o in by_id[sid].provides:
            start_providers.setdefault(o, []).append(sid)
    unreachable = sorted(case.target_outcomes - set(start_providers))
    if unreachable:
        return {
            "decision": "no_feasible_route",
            "reason_codes": (REASON_ASTAR_TRAVEL_ONLY, "unreachable_outcome:" + ",".join(unreachable)),
            "route": (),
            "total_cost": 0,
        }

    adj = _adjacency(case)
    if not adj:
        return {
            "decision": "no_feasible_route",
            "reason_codes": (REASON_ASTAR_TRAVEL_ONLY, "empty_network"),
            "route": (),
            "total_cost": 0,
        }

    def h(acquired: frozenset[str]) -> int:
        return 0 if case.target_outcomes <= acquired else 1

    # A* with g = dwell+travel spent, tie-break lexicographically for determinism
    start_state = None
    heap: list[tuple[int, int, tuple[str, ...], frozenset[str], str | None]] = []
    counter = 0
    for sid in sorted(adj):
        acquired = frozenset(by_id[sid].provides)
        g = by_id[sid].cost
        counter += 1
        heapq.heappush(heap, (g + h(acquired), counter, (sid,), acquired, sid))
    settled: set[tuple[frozenset[str], str]] = set()

    while heap:
        f, _, path, acquired, current = heapq.heappop(heap)
        g = f - h(acquired)
        state = (acquired, current)
        if state in settled:
            continue
        settled.add(state)
        if case.target_outcomes <= acquired:
            total = sum(by_id[sid].cost for sid in path)
            for a, b in zip(path, path[1:]):
                total += next((m for nxt, m in adj[a] if nxt == b), 0)
            return {
                "decision": "find_valid_route",
                "reason_codes": (REASON_ASTAR_TRAVEL_ONLY, "prerequisite_order_ignored"),
                "route": path,
                "total_cost": total,
            }
        for nxt, minutes in adj[current]:
            if nxt in path:
                continue
            new_acquired = acquired | frozenset(by_id[nxt].provides)
            ng = g + minutes + by_id[nxt].cost
            counter += 1
            heapq.heappush(heap, (ng + h(new_acquired), counter, path + (nxt,), new_acquired, nxt))
    return {
        "decision": "no_feasible_route",
        "reason_codes": (REASON_ASTAR_TRAVEL_ONLY, "goal_unreachable"),
        "route": (),
        "total_cost": 0,
    }


# ---------------------------------------------------------------------------
# Contract ABI
# ---------------------------------------------------------------------------

def _predict(inputs: list, config: dict | None, solver) -> list:
    from research_v2.contracts.types import StudyInput

    cfg = dict(config or {})
    out = []
    for i, inp in enumerate(inputs):
        if not isinstance(inp, StudyInput):
            raise DatasetError(f"input[{i}] expects StudyInput, got {type(inp).__name__}")
        case = TrailCase.from_features(inp.features, case_id=inp.case_id)
        try:
            result = solver(case)
        except Exception as exc:
            raise DatasetError(f"input[{i}] case {inp.case_id!r}: {exc}") from exc
        out.append(
            build_prediction(
                case_id=inp.case_id,
                decision=result["decision"],
                reason_codes=result["reason_codes"],
                evidence_ids=tuple(result["route"]),
                score=float(result["total_cost"]),
            )
        )
    return out


def b0_predict_one(inp: Any, config: Mapping[str, Any] | None = None) -> Any:
    return _predict([inp], config, b0_solve)[0]


def predict_batch_b0(inputs: list, config: dict | None = None) -> list:
    return _predict(inputs, config, b0_solve)


def c1_predict_one(inp: Any, config: Mapping[str, Any] | None = None) -> Any:
    return _predict([inp], config, c1_solve)[0]


def predict_batch_c1(inputs: list, config: dict | None = None) -> list:
    return _predict(inputs, config, c1_solve)
