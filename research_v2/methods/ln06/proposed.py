"""LN-06 proposed policy — minimum-cost feasible heritage trail planning.

Decision procedure (strict precedence):

1. Source-provenance gate: unverified checkpoint claims are rejected before
   any routing work (``reject_checkpoint_source``).
2. Structural cycle certification over the full prerequisite structure
   (``reject_cycle``). V2 uses an outcome-level acquirability fixpoint that
   respects alternative providers, fixing the legacy single-provider (OR-as-
   AND) cycle read; a stop requiring an outcome it is the sole provider of is
   correctly identified as a deadlock.
3. Minimum-cost feasible stop-subset selection covering the target outcomes
   plus the transitive prerequisite closure. Alternative providers of the same
   outcome are mutually exclusive alternatives: the search picks ONE provider
   per outcome (never sums them). Subset selection is a set-cover variant
   (NP-hard); small instances are solved exactly with a branch-and-bound with
   memoisation and a deterministic node budget, large instances fall back to a
   deterministic greedy set-cover heuristic. Optimality is only ever claimed
   for the exact path; heuristic runs are honestly marked via the
   ``heuristic_fallback`` reason code (no polynomial-exactness claim).
4. Visit ordering: Kahn topological order with lexicographic stop-id tie-break
   (no travel edges), or - when travel edges are present and the chosen subset
   is small - an exact Held-Karp-style DP over topologically feasible states
   minimising travel; larger subsets use deterministic nearest-ready greedy.
5. Budget check on the CHOSEN minimal subset: dwell + travel > budget is
   ``cost_exceeded``; otherwise ``find_valid_route`` with the ordered
   sequence.

All outputs are deterministic for identical inputs: no randomness is consumed
(the ``seed`` config is accepted for interface compatibility only).
"""
from __future__ import annotations

import heapq
from typing import Any, Mapping

from .dataset import DatasetError, Stop, TrailCase, TravelEdge
from .labels import (
    REASON_ABLATION,
    REASON_NOMINAL,
    REASON_OVER_BUDGET,
    REASON_PREREQ_CYCLE,
    REASON_SOURCE_GAP,
    REASON_UNREACHABLE_OUTCOME,
    build_prediction,
)

STUDY_ID = "LN-06"
METHOD_ID = "proposed"
METHOD_VERSION = "ln06-proposed-v2.0"

DEFAULT_EXACT_NODE_BUDGET = 200_000
DEFAULT_EXACT_ORDER_LIMIT = 10


class SearchBudgetExceeded(RuntimeError):
    """Internal signal: branch-and-bound node budget exhausted."""


# ---------------------------------------------------------------------------
# Cycle certification (outcome-level, alternative-provider aware)
# ---------------------------------------------------------------------------

def cyclic_outcomes(stops: tuple[Stop, ...]) -> frozenset[str]:
    """Return outcomes whose acquisition is blocked by circular prerequisites.

    Two-phase, deterministic:

    Phase 1 prunes "dead" stops: a stop requiring an outcome that no remaining
    stop provides can never be visited (missing prerequisite, not a cycle);
    removing it may orphan further outcomes/prerequisites, so pruning repeats
    to a fixpoint.

    Phase 2 runs an acquirability fixpoint over the surviving stops (starts
    from the empty set; an outcome becomes acquirable when some surviving stop
    provides it and all of its requires are already acquirable). Any outcome
    that is provided by a surviving stop yet never becomes acquirable is
    blocked by a circular dependency.
    """
    provided_by: dict[str, set[str]] = {}
    for s in stops:
        for o in s.provides:
            provided_by.setdefault(o, set()).add(s.id)

    live = {s.id for s in stops}
    by_id = {s.id: s for s in stops}
    changed = True
    while changed:
        changed = False
        for sid in list(live):
            s = by_id[sid]
            if any(r not in provided_by or not (provided_by[r] & live) for r in s.requires):
                live.discard(sid)
                changed = True

    acquirable: set[str] = set()
    changed = True
    while changed:
        changed = False
        for sid in live:
            s = by_id[sid]
            if all(r in acquirable for r in s.requires):
                newly = set(s.provides) - acquirable
                if newly:
                    acquirable |= newly
                    changed = True

    provided_live = {o for sid in live for o in by_id[sid].provides}
    return frozenset(provided_live - acquirable)


# ---------------------------------------------------------------------------
# Minimum-cost subset selection (exact branch-and-bound, greedy fallback)
# ---------------------------------------------------------------------------

def _min_cost_subset_exact(
    by_id: Mapping[str, Stop],
    available_ids: tuple[str, ...],
    targets: frozenset[str],
    node_budget: int,
    *,
    close_prerequisites: bool = True,
) -> tuple[tuple[str, ...], int] | None:
    """Exact minimum-dwell subset covering targets (+ prerequisite closure).

    Returns ``(sorted_stop_ids, dwell_cost)`` or ``None`` when no feasible
    subset exists. Deterministic: branches explore providers ordered by
    (cost, id) and ties between equal-cost solutions prefer the
    lexicographically smallest id tuple.
    """
    providers: dict[str, list[Stop]] = {}
    for sid in available_ids:
        s = by_id[sid]
        for o in s.provides:
            providers.setdefault(o, []).append(s)
    for o in providers:
        providers[o].sort(key=lambda s: (s.cost, s.id))

    best: tuple[int, tuple[str, ...]] | None = None
    visited: set[tuple[frozenset[str], frozenset[str]]] = set()
    expansions = 0

    def search(
        selected: frozenset[str],
        needed: frozenset[str],
        covered: frozenset[str],
    ) -> None:
        nonlocal best, expansions
        expansions += 1
        if expansions > node_budget:
            raise SearchBudgetExceeded()
        state = (selected, needed)
        if state in visited:
            return
        visited.add(state)

        total = sum(by_id[sid].cost for sid in selected)
        if best is not None and total > best[0]:
            return

        pending = needed - covered
        if not pending:
            candidate = (total, tuple(sorted(selected)))
            if best is None or candidate < best:
                best = candidate
            return

        outcome = min(pending, key=lambda o: (len(providers.get(o, ())), o))
        for stop in providers.get(outcome, []):
            if stop.id in selected:
                continue
            extra_needed = set(stop.requires) if close_prerequisites else set()
            search(
                selected | {stop.id},
                needed | extra_needed,
                covered | set(stop.provides),
            )

    search(frozenset(), frozenset(targets), frozenset())
    if best is None:
        return None
    return best[1], best[0]


def _min_cost_subset_greedy(
    by_id: Mapping[str, Stop],
    available_ids: tuple[str, ...],
    targets: frozenset[str],
    *,
    close_prerequisites: bool = True,
) -> tuple[tuple[str, ...], int] | None:
    """Deterministic greedy set-cover heuristic (used only for large instances).

    May rarely miss a feasible solution that the exact search would find; any
    run that used it is marked with the ``heuristic_fallback`` reason code so
    downstream analysis never mistakes it for a certified result.
    """
    selected: list[str] = []
    needed: set[str] = set(targets)
    covered: set[str] = set()
    available = [by_id[sid] for sid in available_ids]
    while True:
        pending = needed - covered
        if not pending:
            return tuple(sorted(selected)), sum(by_id[sid].cost for sid in selected)
        candidates = [
            s
            for s in available
            if s.id not in selected and set(s.provides) & pending
        ]
        if not candidates:
            return None
        best_stop = min(
            candidates,
            key=lambda s: (
                s.cost / max(1, len(set(s.provides) & pending)),
                s.cost,
                s.id,
            ),
        )
        selected.append(best_stop.id)
        if close_prerequisites:
            needed |= set(best_stop.requires)
        covered |= set(best_stop.provides)


def select_min_cost_subset(
    stops: tuple[Stop, ...],
    available_stops: frozenset[str],
    targets: frozenset[str],
    *,
    node_budget: int = DEFAULT_EXACT_NODE_BUDGET,
    close_prerequisites: bool = True,
) -> tuple[tuple[str, ...], int, bool] | None:
    """Public subset-selection entry point.

    Returns ``(stop_ids, dwell_cost, used_heuristic)`` or ``None``.
    """
    by_id = {s.id: s for s in stops}
    available_ids = tuple(sorted(available_stops & set(by_id)))
    if not targets:
        return (), 0, False
    try:
        exact = _min_cost_subset_exact(
            by_id, available_ids, targets, node_budget,
            close_prerequisites=close_prerequisites,
        )
        if exact is None:
            return None
        return exact[0], exact[1], False
    except SearchBudgetExceeded:
        greedy = _min_cost_subset_greedy(
            by_id, available_ids, targets, close_prerequisites=close_prerequisites
        )
        if greedy is None:
            return None
        return greedy[0], greedy[1], True


# ---------------------------------------------------------------------------
# Visit ordering (topological; travel-aware when edges exist)
# ---------------------------------------------------------------------------

def _chosen_dependencies(chosen: tuple[str, ...], by_id: Mapping[str, Stop]) -> dict[str, set[str]]:
    """Map each chosen stop to the chosen stops that must precede it."""
    providers_of: dict[str, list[str]] = {}
    for sid in chosen:
        for o in by_id[sid].provides:
            providers_of.setdefault(o, []).append(sid)
    deps: dict[str, set[str]] = {sid: set() for sid in chosen}
    for sid in chosen:
        for req in by_id[sid].requires:
            for provider in providers_of.get(req, ()):
                if provider != sid:
                    deps[sid].add(provider)
    return deps


def _travel_lookup(edges: tuple[TravelEdge, ...]) -> dict[tuple[str, str], int]:
    return {(e.source, e.target): e.minutes for e in edges}


def _order_exact_travel(
    chosen: tuple[str, ...],
    by_id: Mapping[str, Stop],
    travel: Mapping[tuple[str, str], int],
) -> tuple[tuple[str, ...], int]:
    """Exact minimum-travel topological order (Held-Karp over feasible states)."""
    deps = _chosen_dependencies(chosen, by_id)
    index = {sid: i for i, sid in enumerate(chosen)}
    full = (1 << len(chosen)) - 1
    # state: (visited_mask, last_index) -> (travel_cost, path_tuple)
    best_state: dict[tuple[int, int], tuple[int, tuple[str, ...]]] = {}
    for sid in chosen:
        if not deps[sid]:
            mask = 1 << index[sid]
            cand = (0, (sid,))
            cur = best_state.get((mask, index[sid]))
            if cur is None or cand < cur:
                best_state[(mask, index[sid])] = cand
    for mask in range(1 << len(chosen)):
        for last, sid in enumerate(chosen):
            if not (mask >> last) & 1:
                continue
            state = best_state.get((mask, last))
            if state is None:
                continue
            cost_so_far, path = state
            for nxt_i, nxt in enumerate(chosen):
                if (mask >> nxt_i) & 1:
                    continue
                if not deps[nxt] <= {chosen[i] for i in range(len(chosen)) if (mask >> i) & 1}:
                    continue
                step = travel.get((sid, nxt), 0)
                cand = (cost_so_far + step, path + (nxt,))
                key = (mask | (1 << nxt_i), nxt_i)
                cur = best_state.get(key)
                if cur is None or cand < cur:
                    best_state[key] = cand
    finalists = [
        best_state[(full, i)] for i in range(len(chosen)) if (full, i) in best_state
    ]
    if not finalists:
        raise DatasetError("internal: chosen subset admits no topological order")
    travel_cost, path = min(finalists, key=lambda t: (t[0], t[1]))
    return path, travel_cost


def _order_greedy_travel(
    chosen: tuple[str, ...],
    by_id: Mapping[str, Stop],
    travel: Mapping[tuple[str, str], int],
) -> tuple[tuple[str, ...], int]:
    """Deterministic nearest-ready topological greedy (large subsets)."""
    deps = _chosen_dependencies(chosen, by_id)
    remaining = dict(deps)
    placed: set[str] = set()
    order: list[str] = []
    total_travel = 0
    current: str | None = None
    ready_heap = [(sid, sid) for sid, d in remaining.items() if not d]
    heapq.heapify(ready_heap)
    while ready_heap:
        _, sid = heapq.heappop(ready_heap)
        if sid in placed:
            continue
        order.append(sid)
        placed.add(sid)
        if current is not None:
            total_travel += travel.get((current, sid), 0)
        current = sid
        for other, d in remaining.items():
            if other not in placed and sid in d:
                d.discard(sid)
                if not d:
                    heapq.heappush(ready_heap, (other, other))
    if len(order) != len(chosen):
        raise DatasetError("internal: topological ordering failed on an acyclic subset")
    return tuple(order), total_travel


def order_route(
    chosen: tuple[str, ...],
    by_id: Mapping[str, Stop],
    edges: tuple[TravelEdge, ...],
    *,
    exact_order_limit: int = DEFAULT_EXACT_ORDER_LIMIT,
) -> tuple[tuple[str, ...], int]:
    """Return (ordered stop ids, total travel minutes) for the chosen subset."""
    travel = _travel_lookup(edges)
    if len(chosen) <= exact_order_limit and travel:
        return _order_exact_travel(chosen, by_id, travel)
    if travel:
        return _order_greedy_travel(chosen, by_id, travel)
    deps = _chosen_dependencies(chosen, by_id)
    heap = [(sid, sid) for sid, d in deps.items() if not d]
    heapq.heapify(heap)
    remaining = {sid: set(d) for sid, d in deps.items()}
    order: list[str] = []
    while heap:
        _, sid = heapq.heappop(heap)
        order.append(sid)
        for other, d in remaining.items():
            if other not in order and sid in d:
                d.discard(sid)
                if not d:
                    heapq.heappush(heap, (other, other))
    if len(order) != len(chosen):
        raise DatasetError("internal: topological ordering failed on an acyclic subset")
    return tuple(order), 0


# ---------------------------------------------------------------------------
# Core decision
# ---------------------------------------------------------------------------

def _order_or_cycle(
    chosen: tuple[str, ...],
    by_id: Mapping[str, Stop],
    case: TrailCase,
    enforce_prerequisites: bool,
    *,
    exact_order_limit: int,
):
    """Order the chosen subset; return (None, 0) on an internal deadlock."""
    try:
        return order_route(chosen, by_id, case.travel_edges, exact_order_limit=exact_order_limit)
    except DatasetError:
        if enforce_prerequisites:
            raise  # unreachable: cyclic outcomes were certified earlier
        return None, 0


def solve_case(
    case: TrailCase,
    *,
    enforce_budget: bool = True,
    enforce_prerequisites: bool = True,
    enforce_sources: bool = True,
    node_budget: int = DEFAULT_EXACT_NODE_BUDGET,
    exact_order_limit: int = DEFAULT_EXACT_ORDER_LIMIT,
) -> dict[str, Any]:
    """Solve one validated case; returns decision, reason_codes, cost and route.

    The keyword flags exist so ablations can disable one mechanism at a time;
    the proposed policy itself enables everything.
    """
    by_id = {s.id: s for s in case.stops}

    if enforce_sources and not case.checkpoint_claim_verified:
        return {
            "decision": "reject_checkpoint_source",
            "reason_codes": (REASON_SOURCE_GAP,),
            "route": (),
            "total_cost": 0,
            "dwell_cost": 0,
            "travel_cost": 0,
            "used_heuristic": False,
        }

    if enforce_prerequisites:
        cyclic = cyclic_outcomes(case.stops)
        if cyclic:
            return {
                "decision": "reject_cycle",
                "reason_codes": (REASON_PREREQ_CYCLE, "cyclic_outcomes:" + ",".join(sorted(cyclic))),
                "route": (),
                "total_cost": 0,
                "dwell_cost": 0,
                "travel_cost": 0,
                "used_heuristic": False,
            }

    selection = select_min_cost_subset(
        case.stops,
        case.available_stops,
        case.target_outcomes,
        node_budget=node_budget,
        close_prerequisites=enforce_prerequisites,
    )
    if selection is None:
        covered_by_available = {
            o
            for sid in case.available_stops
            if sid in by_id
            for o in by_id[sid].provides
        }
        missing = sorted(case.target_outcomes - covered_by_available)
        reason = REASON_UNREACHABLE_OUTCOME if missing else "no_feasible_subset"
        return {
            "decision": "no_feasible_route",
            "reason_codes": (reason, "missing_outcomes:" + ",".join(missing)),
            "route": (),
            "total_cost": 0,
            "dwell_cost": 0,
            "travel_cost": 0,
            "used_heuristic": False,
        }

    chosen, dwell, used_heuristic = selection
    providers_of: dict[str, set[str]] = {}
    for sid in chosen:
        for o in by_id[sid].provides:
            providers_of.setdefault(o, set()).add(sid)
    # A chosen stop whose prerequisite is provided by no chosen stop means the
    # prerequisite-closure search was bypassed (a2) or its provider is
    # unavailable: the outcome chain cannot be satisfied in order.
    if enforce_prerequisites:
        unmet = sorted(
            sid
            for sid in chosen
            for req in by_id[sid].requires
            if not (providers_of.get(req) or set()) & set(chosen)
        )
        if unmet:
            return {
                "decision": "no_feasible_route",
                "reason_codes": (REASON_UNREACHABLE_OUTCOME, "unmet_prerequisite:" + ",".join(unmet)),
                "route": (),
                "total_cost": 0,
                "dwell_cost": 0,
                "travel_cost": 0,
                "used_heuristic": used_heuristic,
            }
    ordered, travel_cost = _order_or_cycle(chosen, by_id, case, enforce_prerequisites,
                                           exact_order_limit=exact_order_limit)
    if ordered is None:
        # The chosen subset's internal dependencies admit no topological order
        # (reached only when cycle certification was disabled).
        return {
            "decision": "reject_cycle",
            "reason_codes": (REASON_PREREQ_CYCLE, "ordering_deadlock"),
            "route": (),
            "total_cost": 0,
            "dwell_cost": 0,
            "travel_cost": 0,
            "used_heuristic": used_heuristic,
        }
    total = dwell + travel_cost

    if enforce_budget and total > case.time_budget_minutes:
        return {
            "decision": "cost_exceeded",
            "reason_codes": (REASON_OVER_BUDGET,),
            "route": ordered,
            "total_cost": total,
            "dwell_cost": dwell,
            "travel_cost": travel_cost,
            "used_heuristic": used_heuristic,
        }

    reasons = [REASON_NOMINAL]
    if used_heuristic:
        reasons.append("heuristic_fallback")
    if not enforce_budget:
        reasons.append("budget_check_disabled")
    if not enforce_prerequisites:
        reasons.append("prerequisite_closure_disabled")
    return {
        "decision": "find_valid_route",
        "reason_codes": tuple(reasons),
        "route": ordered,
        "total_cost": total,
        "dwell_cost": dwell,
        "travel_cost": travel_cost,
        "used_heuristic": used_heuristic,
    }


# ---------------------------------------------------------------------------
# Contract ABI
# ---------------------------------------------------------------------------

def predict_one(inp: Any, config: Mapping[str, Any] | None = None) -> Any:
    from research_v2.contracts.types import StudyInput

    if not isinstance(inp, StudyInput):
        raise DatasetError(f"predict_one expects StudyInput, got {type(inp).__name__}")
    cfg = dict(config or {})
    case = TrailCase.from_features(inp.features, case_id=inp.case_id)
    result = solve_case(
        case,
        node_budget=int(cfg.get("exact_node_budget", DEFAULT_EXACT_NODE_BUDGET)),
        exact_order_limit=int(cfg.get("exact_order_limit", DEFAULT_EXACT_ORDER_LIMIT)),
    )
    return build_prediction(
        case_id=inp.case_id,
        decision=result["decision"],
        reason_codes=result["reason_codes"],
        evidence_ids=tuple(result["route"]),
        score=float(result["total_cost"]),
    )


def predict_batch(inputs: list, config: dict | None = None) -> list:
    """Contract ABI: deterministic LN-06 decisions for a batch of inputs.

    Any invalid row rejects the whole batch with its location (no guessed
    fallback), per the study specification.
    """
    cfg = dict(config or {})
    out = []
    for i, inp in enumerate(inputs):
        try:
            out.append(predict_one(inp, cfg))
        except DatasetError:
            raise
        except Exception as exc:  # surface typed failure with batch location
            raise DatasetError(f"input[{i}] case {getattr(inp, 'case_id', '?')!r}: {exc}") from exc
    return out
