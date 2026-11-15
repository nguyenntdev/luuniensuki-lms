"""P02 solvers: C0 sanity, C1 exact branch-and-bound, C2 Dijkstra-with-state,
proposed constraint-aware A* planner, and the A3 alternative-blind ablation.

Shared contract (typed, fail-closed):

- every solver returns :class:`~problems.SolverResult` with an HONEST status
  (``optimal`` only when the solver itself proved global optimality over the
  FULL dwell+travel objective; ``heuristic`` for plans without proof;
  ``timeout``/``abstain`` never silently downgrade to infeasible);
- FALSE INFEASIBILITY is the cardinal sin: an exact solver must answer
  ``no_feasible_route`` only when it has PROVEN no feasible plan exists;
- decisions are find_valid_route | no_feasible_route | cost_exceeded | abstain;
- all solvers are deterministic for identical inputs (no global RNG).

Problem being solved (see METHOD.md): choose an ordered subset S of activities
minimising dwell(S) + travel(order) subject to (i) every target outcome is
provided by some a in S (ALTERNATIVE semantics: one provider suffices),
(ii) the order is a topological order of S's internal prerequisite DAG,
(iii) total <= budget, (iv) accessibility and source-authenticity gates.
With zero travel edges this already contains minimum-cost set cover (NP-hard),
so no polynomial exactness is claimed anywhere.
"""
from __future__ import annotations

import heapq
import time
from typing import Any, Iterable, Mapping

from .problems import (
    ABSTAIN,
    Activity,
    PlanningProblem,
    ProblemError,
    SolverResult,
    travel_minutes,
)

# Fail-closed search budgets: exceeding them yields timeout/abstain statuses,
# never an unproven "optimal" label and never a fake infeasible verdict.
DEFAULT_NODE_BUDGET = 200_000
DEFAULT_TIME_BUDGET_S = 10.0

_FEASIBLE = "find_valid_route"
_INFEASIBLE = "no_feasible_route"
_OVER_BUDGET = "cost_exceeded"


class _BudgetExceeded(Exception):
    """Internal: search budget exhausted; converted to timeout at the boundary."""


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def route_total_cost(problem: PlanningProblem, route: Iterable[str]) -> int:
    """Dwell + directed-travel cost of an explicit ordered route."""
    ids = list(route)
    by_id = problem.by_id()
    dwell = sum(by_id[sid].cost for sid in ids)
    tv = sum(travel_minutes(problem, a, b) for a, b in zip(ids, ids[1:]))
    return dwell + tv


def validate_route(problem: PlanningProblem, route: Iterable[str]) -> list[str]:
    """Contract violations of an ordered route ([] = genuinely valid)."""
    violations: list[str] = []
    by_id = problem.by_id()
    acquired: set[str] = set()
    for sid in route:
        a = by_id.get(sid)
        if a is None:
            violations.append(f"unknown_activity:{sid}")
            continue
        for req in a.requires:
            if req not in acquired:
                violations.append(f"unmet_prerequisite:{sid}:{req}")
        acquired |= set(a.provides)
    missing = sorted(problem.targets - (acquired & problem.targets))
    if missing:
        violations.append("missing_targets:" + ",".join(missing))
    total = route_total_cost(problem, route)
    if total > problem.budget:
        violations.append(f"over_budget:{total}>{problem.budget}")
    if problem.require_accessible:
        for sid in route:
            if not by_id[sid].accessible:
                violations.append(f"inaccessible_activity:{sid}")
    tier_rank = {"verified": 2, "review_pending": 1, "unverified": 0}
    floor = tier_rank[problem.min_source_tier]
    for sid in route:
        if tier_rank[by_id[sid].source_tier] < floor:
            violations.append(f"below_source_floor:{sid}")
    return violations


def _gates_ok(problem: PlanningProblem, a: Activity) -> bool:
    if problem.require_accessible and not a.accessible:
        return False
    tier_rank = {"verified": 2, "review_pending": 1, "unverified": 0}
    return tier_rank[a.source_tier] >= tier_rank[problem.min_source_tier]


def _dwell(problem: PlanningProblem, subset: Iterable[str]) -> int:
    by_id = problem.by_id()
    return sum(by_id[sid].cost for sid in subset)


def _usable_or_missing(problem: PlanningProblem) -> tuple[list[Activity], list[str]]:
    """Gate-filtered activities + provably-missing target outcomes."""
    usable = [a for a in problem.usable_activities() if _gates_ok(problem, a)]
    covered: set[str] = set()
    for a in usable:
        covered |= set(a.provides)
    return usable, sorted(problem.targets - covered)


# ---------------------------------------------------------------------------
# C0 — greedy first-feasible (SANITY_ONLY comparator)
# ---------------------------------------------------------------------------

def solve_greedy(problem: PlanningProblem, **_: Any) -> SolverResult:
    """C0 sanity: repeatedly add the cheapest activity covering a pending
    target, then order lexicographically topologically. Ignores travel in
    selection. Never claims optimality (status always ``heuristic``)."""
    started = time.perf_counter()

    def res(decision: str, route: tuple[str, ...] = (), reasons: tuple[str, ...] = ()) -> SolverResult:
        return SolverResult(
            problem.problem_id, "c0_greedy", decision, "heuristic", route,
            route_total_cost(problem, route) if route else 0,
            _dwell(problem, route), 
            (route_total_cost(problem, route) - _dwell(problem, route)) if route else 0,
            reason_codes=reasons,
            wall_ms=(time.perf_counter() - started) * 1000.0,
        )

    usable, missing = _usable_or_missing(problem)
    if missing:
        return res(_INFEASIBLE, reasons=("missing_targets:" + ",".join(missing),))
    chosen: list[str] = []
    acquired: set[str] = set()
    pending = set(problem.targets)
    while pending:
        candidates = [a for a in usable if a.id not in chosen and (set(a.provides) & pending)]
        if not candidates:
            return res(_INFEASIBLE, reasons=("greedy_dead_end",))
        pick = min(candidates, key=lambda a: (a.cost, a.id))
        chosen.append(pick.id)
        acquired |= set(pick.provides)
        pending = set(problem.targets) - acquired
    order, travel_cost, _exact = _order_min_travel(problem, tuple(sorted(chosen)), 0)
    if order is None:
        return res(_INFEASIBLE, reasons=("ordering_deadlock",))
    total = _dwell(problem, order) + travel_cost
    decision = _FEASIBLE if total <= problem.budget else _OVER_BUDGET
    return res(
        decision,
        tuple(order) if decision == _FEASIBLE else (),
        ("greedy_selection",),
    )


# ---------------------------------------------------------------------------
# Shared ordering stage: exact min-travel topological order (small subsets) or
# deterministic lexicographic Kahn (fallback; no travel optimality claim).
# ---------------------------------------------------------------------------

def _chosen_dependencies(chosen: tuple[str, ...], by_id: Mapping[str, Activity]) -> dict[str, set[str]]:
    providers_of: dict[str, set[str]] = {}
    for sid in chosen:
        for o in by_id[sid].provides:
            providers_of.setdefault(o, set()).add(sid)
    deps: dict[str, set[str]] = {sid: set() for sid in chosen}
    for sid in chosen:
        for req in by_id[sid].requires:
            ps = providers_of.get(req)
            if not ps:
                deps[sid].add(sid)  # self-deadlock marker: unmet prerequisite
            else:
                deps[sid] |= {p for p in ps if p != sid}
    return deps


class _OrderBudgetExceeded(Exception):
    pass


def _order_min_travel_dp(
    problem: PlanningProblem,
    chosen: tuple[str, ...],
    deps: dict[str, set[str]],
) -> tuple[tuple[str, ...], int]:
    """Held-Karp-style DP over (visited_mask, last) minimising travel.
    Raises ``_OrderBudgetExceeded`` when the DP would exceed 2^18 states."""
    k = len(chosen)
    if k > 18:
        raise _OrderBudgetExceeded()
    index = {sid: i for i, sid in enumerate(chosen)}
    full = (1 << k) - 1
    best_state: dict[tuple[int, int], tuple[int, tuple[str, ...]]] = {}
    for sid in chosen:
        if not deps[sid]:
            key = (1 << index[sid], index[sid])
            cand = (0, (sid,))
            cur = best_state.get(key)
            if cur is None or cand < cur:
                best_state[key] = cand
    for mask in range(1 << k):
        for last_i, sid in enumerate(chosen):
            if not (mask >> last_i) & 1:
                continue
            st = best_state.get((mask, last_i))
            if st is None:
                continue
            cost_so_far, p = st
            for nxt_i, nxt in enumerate(chosen):
                if (mask >> nxt_i) & 1:
                    continue
                acquired = {chosen[i] for i in range(k) if (mask >> i) & 1}
                if not deps[nxt] <= acquired:
                    continue
                cand = (cost_so_far + travel_minutes(problem, sid, nxt), p + (nxt,))
                key = (mask | (1 << nxt_i), nxt_i)
                cur = best_state.get(key)
                if cur is None or cand < cur:
                    best_state[key] = cand
    finalists = [best_state[(full, i)] for i in range(k) if (full, i) in best_state]
    if not finalists:
        raise ProblemError("internal: acyclic subset admits no topological order")
    travel_cost, p = min(finalists, key=lambda t: (t[0], t[1]))
    return p, travel_cost


def _order_min_travel(
    problem: PlanningProblem,
    chosen: tuple[str, ...],
    exact_order_limit: int = 8,
) -> tuple[tuple[str, ...] | None, int, bool]:
    """Minimum-travel topological order of ``chosen``.

    Returns (order | None, travel_cost, used_exact_dp). ``None`` = genuine
    deadlock (cycle or unmet prerequisite inside the subset). Exact DP when
    len(chosen) <= exact_order_limit and travel edges exist; otherwise a
    deterministic lexicographic Kahn order (travel-agnostic, marked exact=False).
    """
    by_id = problem.by_id()
    if not chosen:
        return (), 0, True
    deps = _chosen_dependencies(chosen, by_id)
    if any(sid in d for sid, d in deps.items()):
        return None, 0, False
    has_travel = bool(problem.travel)
    if has_travel and len(chosen) <= exact_order_limit:
        order, travel_cost = _order_min_travel_dp(problem, chosen, deps)
        return order, travel_cost, True
    # Lexicographic Kahn (deterministic). Without travel edges every valid
    # order costs 0, so the order stage is still exact (travel-optimal).
    remaining = {sid: set(d) for sid, d in deps.items()}
    heap = [sid for sid, d in remaining.items() if not d]
    heapq.heapify(heap)
    order: list[str] = []
    placed: set[str] = set()
    while heap:
        sid = heapq.heappop(heap)
        if sid in placed:
            continue
        order.append(sid)
        placed.add(sid)
        for other, d in remaining.items():
            if other not in placed and sid in d:
                d.discard(sid)
                if not d:
                    heapq.heappush(heap, other)
    if len(order) != len(chosen):
        return None, 0, False
    travel_cost = sum(travel_minutes(problem, a, b) for a, b in zip(order, order[1:]))
    return tuple(order), travel_cost, not has_travel


# ---------------------------------------------------------------------------
# C1 — exact branch-and-bound over the JOINT objective (subset selection +
# exact per-subset ordering), written fresh for P02 (conceptually informed by
# the tested V2 LN-06 `_min_cost_subset`, but joint-objective aware).
# ---------------------------------------------------------------------------

def solve_branch_and_bound(
    problem: PlanningProblem,
    *,
    node_budget: int = DEFAULT_NODE_BUDGET,
    exact_order_limit: int = 8,
    close_prerequisites: bool = True,
    **_: Any,
) -> SolverResult:
    """C1 serious classical comparator.

    DFS over provider choices for pending target outcomes (with prerequisite
    closure). Pruning is exact: any completion costs >= current dwell (travel
    >= 0), so branches with dwell > best_total are cut. Each covering subset
    is evaluated with the EXACT min-travel order (small subsets), giving a
    proven global optimum when the search completes within its node budget.
    Node-budget exhaustion returns the best plan found with status
    ``timeout`` (or ``abstain`` when nothing was found) — never infeasible.
    """
    started = time.perf_counter()
    by_id = problem.by_id()
    usable, missing = _usable_or_missing(problem)
    if missing:
        return SolverResult(
            problem.problem_id, "c1_branch_and_bound", _INFEASIBLE, "optimal", (),
            0, 0, 0,
            reason_codes=("missing_targets:" + ",".join(missing),),
            wall_ms=(time.perf_counter() - started) * 1000.0,
        )
    providers: dict[str, list[Activity]] = {}
    for a in usable:
        for o in a.provides:
            providers.setdefault(o, []).append(a)
    for lst in providers.values():
        lst.sort(key=lambda a: (a.cost, a.id))

    best: tuple[int, tuple[str, ...]] | None = None  # (joint_cost, ordered_route)
    best_order_exact = True
    visited: set[tuple[frozenset[str], frozenset[str]]] = set()
    expansions = 0

    def search(selected: frozenset[str], needed: frozenset[str], covered: frozenset[str]) -> None:
        nonlocal best, best_order_exact, expansions
        expansions += 1
        if expansions > node_budget:
            raise _BudgetExceeded()
        state = (selected, needed)
        if state in visited:
            return
        visited.add(state)
        dwell = _dwell(problem, selected)
        if best is not None and dwell > best[0]:
            return  # exact prune: travel >= 0 can never recover the gap
        pending = needed - covered
        if not pending:
            chosen = tuple(sorted(selected))
            order, travel_cost, exact = _order_min_travel(problem, chosen, exact_order_limit)
            if order is None:
                return
            total = dwell + travel_cost
            if best is None or total < best[0] or (total == best[0] and tuple(order) < best[1]):
                best = (total, tuple(order))
                best_order_exact = exact
            return
        outcome = min(pending, key=lambda o: (len(providers.get(o, ())), o))
        for stop in providers.get(outcome, ()):
            if stop.id in selected:
                continue
            extra = set(stop.requires) if close_prerequisites else set()
            search(selected | {stop.id}, needed | extra, covered | set(stop.provides))

    try:
        search(frozenset(), frozenset(problem.targets), frozenset())
    except _BudgetExceeded:
        if best is not None:
            return SolverResult(
                problem.problem_id, "c1_branch_and_bound", _FEASIBLE, "timeout", best[1],
                best[0], _dwell(problem, best[1]), best[0] - _dwell(problem, best[1]),
                reason_codes=("node_budget_exhausted", "best_found_not_proven"),
                wall_ms=(time.perf_counter() - started) * 1000.0,
            )
        return SolverResult(
            problem.problem_id, "c1_branch_and_bound", ABSTAIN, "timeout", (),
            0, 0, 0, reason_codes=("node_budget_exhausted",),
            wall_ms=(time.perf_counter() - started) * 1000.0,
        )

    if best is None:
        # Search completed exhaustively: no covering, orderable subset exists.
        return SolverResult(
            problem.problem_id, "c1_branch_and_bound", _INFEASIBLE, "optimal", (),
            0, 0, 0, reason_codes=("proven_no_feasible_subset",),
            wall_ms=(time.perf_counter() - started) * 1000.0,
        )
    total, route = best
    dwell = _dwell(problem, route)
    status = "optimal" if best_order_exact else "bound_proven"
    decision = _FEASIBLE if total <= problem.budget else _OVER_BUDGET
    return SolverResult(
        problem.problem_id, "c1_branch_and_bound", decision, status,
        route if decision == _FEASIBLE else (),
        total, dwell, total - dwell,
        reason_codes=("exhaustive_search_complete",),
        wall_ms=(time.perf_counter() - started) * 1000.0,
        nodes_expanded=expansions,
    )


# ---------------------------------------------------------------------------
# C2 — independent exact search: Dijkstra-with-state over acquired outcomes.
# A fresh reimplementation for P02 (no library, no shared code with C1);
# labelled honestly as "independent exact search (reimplementation)".
# ---------------------------------------------------------------------------

def solve_dijkstra_state(
    problem: PlanningProblem,
    *,
    state_node_budget: int = 400_000,
    exact_order_limit: int = 8,
    **_: Any,
) -> SolverResult:
    """Dijkstra over states (acquired_outcomes, chosen_subset, last_activity).

    Edge weights (dwell + directed travel) are non-negative, so the first
    settled state that covers all targets is the global optimum — the
    standard Dijkstra argument, not a heuristic. Budget exhaustion returns
    the best found with status ``timeout`` (or ``abstain``) — never infeasible.
    """
    started = time.perf_counter()
    usable, missing = _usable_or_missing(problem)
    if missing:
        return SolverResult(
            problem.problem_id, "c2_dijkstra_state", _INFEASIBLE, "optimal", (),
            0, 0, 0,
            reason_codes=("missing_targets:" + ",".join(missing),),
            wall_ms=(time.perf_counter() - started) * 1000.0,
        )

    start = (frozenset(), frozenset(), None)  # (acquired, chosen, last)
    dist: dict[tuple[Any, ...], int] = {start: 0}
    best_path: dict[tuple[Any, ...], tuple[str, ...]] = {start: ()}
    heap: list[tuple[int, int, tuple[Any, ...]]] = [(0, 0, start)]
    tie = 0
    settled = 0
    goal_cost: int | None = None
    goal_state: tuple[Any, ...] | None = None
    timed_out = False

    while heap:
        d, _, state = heapq.heappop(heap)
        if d > dist.get(state, 10**9):
            continue
        settled += 1
        if settled > state_node_budget:
            timed_out = True
            break
        acquired, chosen, last = state
        if problem.targets <= acquired:
            goal_cost, goal_state = d, state
            break  # non-negative weights: first settled goal state is optimal
        for a in usable:
            if a.id in chosen:
                continue
            if any(r not in acquired for r in a.requires):
                continue
            step = a.cost + (travel_minutes(problem, last, a.id) if last is not None else 0)
            n_state = (acquired | set(a.provides), chosen | {a.id}, a.id)
            nd = d + step
            if nd < dist.get(n_state, 10**9):
                dist[n_state] = nd
                best_path[n_state] = best_path[state] + (a.id,)
                tie += 1
                heapq.heappush(heap, (nd, tie, n_state))

    if goal_cost is None:
        if timed_out:
            return SolverResult(
                problem.problem_id, "c2_dijkstra_state", ABSTAIN, "timeout", (),
                0, 0, 0, reason_codes=("state_budget_exhausted",),
                wall_ms=(time.perf_counter() - started) * 1000.0,
            )
        # Heap exhausted without a goal: PROVEN unreachable over usable acts.
        return SolverResult(
            problem.problem_id, "c2_dijkstra_state", _INFEASIBLE, "optimal", (),
            0, 0, 0, reason_codes=("proven_unreachable_targets",),
            wall_ms=(time.perf_counter() - started) * 1000.0,
        )

    # The settled path cost already includes travel of the FOUND order; a
    # different order of the same subset may be cheaper. Re-solve travel for
    # the settled subset exactly (small subsets) and take the min. The
    # status stays "optimal" iff the search cost was achieved by an exact
    # order AND the DP confirms it (otherwise honest downgrade).
    path = best_path[goal_state]
    ordered, travel_cost, exact = _order_min_travel(problem, tuple(sorted(path)), exact_order_limit)
    if ordered is None:  # pragma: no cover - Dijkstra paths are order-valid
        ordered, travel_cost, exact = path, sum(
            travel_minutes(problem, a, b) for a, b in zip(path, path[1:])
        ), True
    dwell_cost = _dwell(problem, ordered)
    total = min(goal_cost, dwell_cost + travel_cost)
    if total < goal_cost:
        status = "bound_proven"
        reason = "dijkstra_goal_then_exact_reorder"
    else:
        status = "optimal" if exact else "bound_proven"
        reason = "dijkstra_first_settled_goal"
    decision = _FEASIBLE if total <= problem.budget else _OVER_BUDGET
    return SolverResult(
        problem.problem_id, "c2_dijkstra_state", decision, status,
        tuple(ordered) if decision == _FEASIBLE else (),
        total, dwell_cost, travel_cost,
        reason_codes=(reason,),
        wall_ms=(time.perf_counter() - started) * 1000.0,
        nodes_expanded=settled,
    )


# ---------------------------------------------------------------------------
# Proposed — constraint-aware planner: A* with admissible dwell lower bound,
# accessibility + source-authenticity constraints, honest status ladder.
# ---------------------------------------------------------------------------

def _dwell_lower_bound(
    targets_pending: frozenset[str],
    providers: Mapping[str, list[Activity]],
) -> int:
    """Admissible h: max over pending outcomes of the cheapest provider dwell.

    Why not the SUM of per-outcome cheapest providers? When one activity
    provides several pending outcomes, the sum double-counts it and can
    EXCEED the true remaining cost (inadmissible; verified by a documented
    counterexample during development). The max over pending outcomes is
    dominated by any feasible completion (each pending outcome needs at
    least one activity costing >= its cheapest provider, and one activity's
    cost is paid once), so h <= h* holds and A* stays admissible. It is
    weaker than a set-cover LP bound but always safe.
    """
    if not targets_pending:
        return 0
    return max(
        min((a.cost for a in providers.get(o, ())), default=0) for o in targets_pending
    )


def solve_proposed(
    problem: PlanningProblem,
    *,
    node_budget: int = DEFAULT_NODE_BUDGET,
    time_budget_s: float = DEFAULT_TIME_BUDGET_S,
    exact_order_limit: int = 8,
    **_: Any,
) -> SolverResult:
    """Proposed constraint-aware planner (A* + gates + exact reordering).

    Status ladder (honest by construction):
    - ``optimal``    : A* completed and the final order is exact;
    - ``heuristic``  : plan returned, final order fell back to Kahn;
    - ``timeout``    : node/time budget exhausted (plan or ABSTAIN);
    - proven ``no_feasible_route`` only after full state-space exhaustion.
    """
    started = time.perf_counter()
    usable, missing = _usable_or_missing(problem)
    if missing:
        return SolverResult(
            problem.problem_id, "p02_proposed", _INFEASIBLE, "optimal", (),
            0, 0, 0,
            reason_codes=("missing_targets:" + ",".join(missing),),
            wall_ms=(time.perf_counter() - started) * 1000.0,
        )
    providers: dict[str, list[Activity]] = {}
    for a in usable:
        for o in a.provides:
            providers.setdefault(o, []).append(a)

    def h(acquired: frozenset[str]) -> int:
        return _dwell_lower_bound(problem.targets - acquired, providers)

    start = (frozenset(), frozenset(), None)
    g_best: dict[tuple[Any, ...], int] = {start: 0}
    path: dict[tuple[Any, ...], tuple[str, ...]] = {start: ()}
    heap: list[tuple[int, int, int, tuple[Any, ...]]] = [(h(frozenset()), 0, 0, start)]
    tie = 0
    settled = 0
    goal: tuple[int, tuple[str, ...]] | None = None
    timed_out = False

    while heap:
        f, _, _, state = heapq.heappop(heap)
        d = g_best.get(state, 10**9)
        if f - h(state[0]) > d:
            continue  # stale heap entry
        settled += 1
        if settled > node_budget or (time.perf_counter() - started) > time_budget_s:
            timed_out = True
            break
        acquired, chosen, last = state
        if problem.targets <= acquired:
            goal = (d, path[state])
            break
        for a in usable:
            if a.id in chosen:
                continue
            if any(r not in acquired for r in a.requires):
                continue
            step = a.cost + (travel_minutes(problem, last, a.id) if last is not None else 0)
            n_state = (acquired | set(a.provides), chosen | {a.id}, a.id)
            nd = d + step
            if nd < g_best.get(n_state, 10**9):
                g_best[n_state] = nd
                path[n_state] = path[state] + (a.id,)
                tie += 1
                heapq.heappush(heap, (nd + h(n_state[0]), tie, nd, n_state))

    if goal is None:
        if timed_out:
            return SolverResult(
                problem.problem_id, "p02_proposed", ABSTAIN, "timeout", (),
                0, 0, 0, reason_codes=("search_budget_exhausted",),
                wall_ms=(time.perf_counter() - started) * 1000.0,
            )
        # Full reachable state explored with no goal: PROVEN infeasible.
        return SolverResult(
            problem.problem_id, "p02_proposed", _INFEASIBLE, "optimal", (),
            0, 0, 0, reason_codes=("proven_unreachable_targets",),
            wall_ms=(time.perf_counter() - started) * 1000.0,
        )

    # The A* path cost already includes travel of the FOUND order, but a
    # different order of the same subset may be cheaper. Re-solve travel for
    # the settled subset exactly (small subsets) and take the min.
    _cost, subset = goal
    ordered, travel_cost, exact = _order_min_travel(
        problem, tuple(sorted(subset)), exact_order_limit
    )
    if ordered is None:  # pragma: no cover - A* paths are prerequisite-ordered
        raise ProblemError("internal: A* produced a subset with no topological order")
    dwell_cost = _dwell(problem, ordered)
    total = min(_cost, dwell_cost + travel_cost)
    if total < _cost:
        # A cheaper order exists for the same subset; A*'s g-value was order-
        # path-dependent. This keeps the RESULT optimal for the subset, but it
        # can no longer certify global optimality (the search ranked states by
        # one particular order). Honest status downgrade:
        status = "heuristic"
        reason = "astar_goal_then_exact_reorder"
    else:
        status = "optimal" if exact else "heuristic"
        reason = "astar_first_settled_goal"
    decision = _FEASIBLE if total <= problem.budget else _OVER_BUDGET
    return SolverResult(
        problem.problem_id, "p02_proposed", decision, status,
        tuple(ordered) if decision == _FEASIBLE else (),
        total, dwell_cost, travel_cost,
        reason_codes=(reason, "exact_order" if exact else "kahn_order_fallback"),
        wall_ms=(time.perf_counter() - started) * 1000.0,
        nodes_expanded=settled,
    )


# ---------------------------------------------------------------------------
# A3 — ablation: alternative-blind selection (reproduces the LN-06 legacy
# all-providers false-infeasibility bug on purpose, as a mutation probe).
# ---------------------------------------------------------------------------

def solve_ablation_alternative_blind(
    problem: PlanningProblem,
    *,
    exact_order_limit: int = 8,
    **_: Any,
) -> SolverResult:
    """A3 mutation: require the UNION of every provider of each target
    outcome (legacy semantics) instead of choosing one. Expected failure
    family: false infeasibility on the A/B alternative-provider shape."""
    started = time.perf_counter()

    def res(decision: str, reasons: tuple[str, ...], route: tuple[str, ...] = ()) -> SolverResult:
        total = route_total_cost(problem, route) if route else 0
        return SolverResult(
            problem.problem_id, "a3_alternative_blind", decision, "heuristic", route,
            total, _dwell(problem, route), total - _dwell(problem, route),
            reason_codes=reasons,
            wall_ms=(time.perf_counter() - started) * 1000.0,
        )

    usable, missing = _usable_or_missing(problem)
    if missing:
        return res(_INFEASIBLE, ("missing_targets:" + ",".join(missing),))
    providers: dict[str, list[Activity]] = {}
    for a in usable:
        for o in a.provides:
            providers.setdefault(o, []).append(a)
    all_providers: list[str] = []
    seen: set[str] = set()
    for o in sorted(problem.targets):
        for a in sorted(providers[o], key=lambda x: x.id):
            if a.id not in seen:
                seen.add(a.id)
                all_providers.append(a.id)
    ordered, travel_cost, _exact = _order_min_travel(
        problem, tuple(sorted(all_providers)), exact_order_limit
    )
    if ordered is None:
        # The all-providers union admits no valid order — the legacy false
        # infeasibility signature when a feasible single-provider plan exists.
        return res(_INFEASIBLE, ("legacy_false_infeasibility",))
    total = _dwell(problem, ordered) + travel_cost
    decision = _FEASIBLE if total <= problem.budget else _OVER_BUDGET
    route = tuple(ordered) if decision == _FEASIBLE else ()
    return res(decision, ("all_providers_summed",), route)


# ---------------------------------------------------------------------------
# Registry / dispatch
# ---------------------------------------------------------------------------

SOLVER_REGISTRY: dict[str, Any] = {
    "c0_greedy": solve_greedy,
    "c1_branch_and_bound": solve_branch_and_bound,
    "c2_dijkstra_state": solve_dijkstra_state,
    "p02_proposed": solve_proposed,
    "a3_alternative_blind": solve_ablation_alternative_blind,
}

EXACT_SOLVERS = frozenset({"c1_branch_and_bound", "c2_dijkstra_state", "p02_proposed"})

SOLVER_DESCRIPTIONS: dict[str, str] = {
    "c0_greedy": "C0 sanity: greedy first-feasible (cheapest covering pick).",
    "c1_branch_and_bound": (
        "C1 serious classical: exact branch-and-bound over the joint "
        "dwell+travel objective (our reimplementation, no external library)."
    ),
    "c2_dijkstra_state": (
        "C2 independent exact search (reimplementation): Dijkstra-with-state "
        "over (acquired, chosen, last); NOT a published library."
    ),
    "p02_proposed": (
        "Proposed: constraint-aware A* planner with accessibility and "
        "source-authenticity gates and honest status reporting."
    ),
    "a3_alternative_blind": (
        "A3 ablation: alternative-blind all-providers selection (legacy "
        "false-infeasibility mutation)."
    ),
}


def run_solver(solver_id: str, problem: PlanningProblem, **kwargs: Any) -> SolverResult:
    """Dispatch one solver by registry id (unknown ids fail closed)."""
    fn = SOLVER_REGISTRY.get(solver_id)
    if fn is None:
        raise ProblemError(f"unknown solver id {solver_id!r}; known: {sorted(SOLVER_REGISTRY)}")
    return fn(problem, **kwargs)
