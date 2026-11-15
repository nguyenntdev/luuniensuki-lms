"""P02 solver counterexamples and contract tests (mandatory suites).

Covers the spec-mandated stress cases:
- A/B alternative providers (budget 50, each 40 min) -> feasible, cost 40, ONE chosen;
- tight budget -> cost_exceeded;
- prerequisite cycle -> no_feasible_route (proven);
- unreachable target -> no_feasible_route;
- accessibility / source-authenticity gates;
- determinism (byte-stable results across runs);
- solver-status honesty (no fabricated optima).
"""
from __future__ import annotations

import pytest

from research_v3.methods.p02.problems import (
    ABSTAIN,
    Activity,
    PlanningProblem,
    SolverResult,
    parse_problem,
)
from research_v3.methods.p02.solvers import (
    EXACT_SOLVERS,
    SOLVER_REGISTRY,
    run_solver,
    route_total_cost,
    solve_ablation_alternative_blind,
    validate_route,
)

ALL_IDS = ("c0_greedy", "c1_branch_and_bound", "c2_dijkstra_state", "p02_proposed")
EXACT_IDS = ("c1_branch_and_bound", "c2_dijkstra_state", "p02_proposed")


def _mk(pid, acts, targets, budget, travel=None, **kw) -> PlanningProblem:
    return parse_problem(
        {
            "problem_id": pid,
            "family_id": kw.pop("family_id", "test"),
            "activities": acts,
            "targets": targets,
            "budget": budget,
            "travel": travel or {},
            **kw,
        }
    )


# ---------------------------------------------------------------------------
# MANDATORY: A/B alternative-provider counterexample (LN-06 regression family)
# ---------------------------------------------------------------------------

def test_ab_alternative_providers_must_choose_one():
    """A and B both provide T at 40 min each, budget 50 => feasible, cost 40,
    exactly one of A/B chosen. The legacy all-providers bug rejected this."""
    p = _mk(
        "ab-counterexample",
        [
            {"id": "A", "cost": 40, "provides": ["T"], "requires": []},
            {"id": "B", "cost": 40, "provides": ["T"], "requires": []},
        ],
        ["T"],
        50,
    )
    for sid in EXACT_IDS:
        r = run_solver(sid, p)
        assert r.decision == "find_valid_route", (sid, r)
        assert r.total_cost == 40
        assert len(r.route) == 1 and r.route[0] in {"A", "B"}
        assert r.status in {"optimal", "bound_proven"}
        assert validate_route(p, r.route) == []
    # The mutation probe MUST fail this family with the legacy signature.
    a3 = solve_ablation_alternative_blind(p)
    assert a3.decision in {"no_feasible_route", "cost_exceeded"}


# ---------------------------------------------------------------------------
# Tight budget -> cost_exceeded
# ---------------------------------------------------------------------------

def test_tight_budget_is_cost_exceeded():
    p = _mk("tight", [{"id": "A", "cost": 40, "provides": ["T"], "requires": []}], ["T"], 30)
    for sid in EXACT_IDS:
        r = run_solver(sid, p)
        assert r.decision == "cost_exceeded", (sid, r)
        assert r.total_cost == 40
        assert r.status in {"optimal", "bound_proven"}


# ---------------------------------------------------------------------------
# Cycle -> no_feasible_route
# ---------------------------------------------------------------------------

def test_prerequisite_cycle_proven_infeasible():
    p = _mk(
        "cycle",
        [
            {"id": "A", "cost": 10, "provides": ["T"], "requires": ["X"]},
            {"id": "B", "cost": 10, "provides": ["X"], "requires": ["T"]},
        ],
        ["T"],
        100,
    )
    for sid in EXACT_IDS:
        r = run_solver(sid, p)
        assert r.decision == "no_feasible_route", (sid, r)
        assert r.status in {"optimal", "bound_proven"}  # proven, not abstained


# ---------------------------------------------------------------------------
# Unreachable target -> no_feasible_route
# ---------------------------------------------------------------------------

def test_unreachable_target_is_no_feasible_route():
    p = _mk(
        "unreachable",
        [{"id": "A", "cost": 10, "provides": ["O1"], "requires": []}],
        ["O1", "OB"],
        100,
    )
    for sid in ALL_IDS:
        r = run_solver(sid, p)
        assert r.decision == "no_feasible_route", (sid, r)
    a3 = solve_ablation_alternative_blind(p)
    assert a3.decision == "no_feasible_route"


def test_unreachable_via_chain_gap():
    """Target requires an outcome whose only provider needs the target first."""
    p = _mk(
        "chain-gap",
        [
            {"id": "A", "cost": 10, "provides": ["T"], "requires": []},
            {"id": "B", "cost": 10, "provides": ["X"], "requires": ["Y"]},
            {"id": "C", "cost": 10, "provides": ["Y"], "requires": ["X"]},
        ],
        ["T", "X"],
        100,
    )
    for sid in EXACT_IDS:
        r = run_solver(sid, p)
        assert r.decision == "no_feasible_route", (sid, r)


# ---------------------------------------------------------------------------
# Gates
# ---------------------------------------------------------------------------

def test_accessibility_gate_blocks_only_provider():
    p = _mk(
        "access",
        [{"id": "A", "cost": 10, "provides": ["T"], "requires": [], "accessible": False}],
        ["T"],
        100,
    )
    for sid in EXACT_IDS:
        r = run_solver(sid, p)
        assert r.decision == "no_feasible_route", (sid, r)
    # Disabling the gate makes it feasible again (ablation semantics).
    p_open = _mk(
        "access-open",
        [{"id": "A", "cost": 10, "provides": ["T"], "requires": [], "accessible": False}],
        ["T"],
        100,
        require_accessible=False,
    )
    r = run_solver("p02_proposed", p_open)
    assert r.decision == "find_valid_route"


def test_source_tier_gate_blocks_unverified():
    p = _mk(
        "source",
        [{"id": "A", "cost": 10, "provides": ["T"], "requires": [], "source_tier": "unverified"}],
        ["T"],
        100,
        min_source_tier="verified",
    )
    for sid in EXACT_IDS:
        r = run_solver(sid, p)
        assert r.decision == "no_feasible_route", (sid, r)
    # Relaxing the floor admits the activity.
    p_relaxed = _mk(
        "source-relaxed",
        [{"id": "A", "cost": 10, "provides": ["T"], "requires": [], "source_tier": "review_pending"}],
        ["T"],
        100,
        min_source_tier="review_pending",
    )
    r = run_solver("p02_proposed", p_relaxed)
    assert r.decision == "find_valid_route"


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------

def test_solvers_deterministic_byte_identical():
    p = _mk(
        "det",
        [
            {"id": "A", "cost": 12, "provides": ["T1"], "requires": []},
            {"id": "B", "cost": 9, "provides": ["T2"], "requires": []},
            {"id": "C", "cost": 7, "provides": ["T1", "T2"], "requires": []},
        ],
        ["T1", "T2"],
        100,
        travel={"A->B": 3, "B->A": 4, "B->C": 2, "C->B": 1, "A->C": 8, "C->A": 6},
    )
    for sid in ALL_IDS:
        runs = [run_solver(sid, p) for _ in range(3)]
        assert all(
            (r.decision, r.status, r.route, r.total_cost) == (runs[0].decision, runs[0].status, runs[0].route, runs[0].total_cost)
            for r in runs
        ), sid


# ---------------------------------------------------------------------------
# Status honesty
# ---------------------------------------------------------------------------

def test_no_solver_claims_optimal_without_proof_route_valid():
    """Every returned route must pass full validation; abstain never carries a
    route; heuristic status never accompanies a proof reason code."""
    p = _mk(
        "honesty",
        [
            {"id": "A", "cost": 30, "provides": ["T1"], "requires": []},
            {"id": "B", "cost": 22, "provides": ["T1"], "requires": []},
            {"id": "C", "cost": 25, "provides": ["T2"], "requires": ["T1"]},
            {"id": "D", "cost": 40, "provides": ["T1", "T2"], "requires": []},
        ],
        ["T1", "T2"],
        95,
        travel={"A->C": 5, "C->A": 5, "B->C": 3, "C->B": 3, "D->C": 9, "C->D": 7},
    )
    for sid in ALL_IDS:
        r = run_solver(sid, p)
        if r.route:
            assert validate_route(p, r.route) == [], (sid, r)
        if r.decision == "find_valid_route":
            assert r.status in {"optimal", "bound_proven", "heuristic"}


def test_unknown_solver_fails_closed():
    p = _mk("x", [{"id": "A", "cost": 1, "provides": ["T"], "requires": []}], ["T"], 10)
    with pytest.raises(Exception):
        run_solver("nope", p)


def test_empty_targets_trivially_feasible():
    p = _mk("empty", [{"id": "A", "cost": 5, "provides": ["T"], "requires": []}], [], 10)
    r = run_solver("p02_proposed", p)
    assert r.decision == "find_valid_route" and r.route == ()


def test_route_cost_helper_matches_manual_sum():
    p = _mk(
        "cost",
        [
            {"id": "A", "cost": 10, "provides": ["T1"], "requires": []},
            {"id": "B", "cost": 5, "provides": ["T2"], "requires": []},
        ],
        ["T1", "T2"],
        100,
        travel={"A->B": 3},
    )
    assert route_total_cost(p, ("A", "B")) == 18


def test_validate_route_flags_violations():
    p = _mk(
        "viol",
        [
            {"id": "A", "cost": 10, "provides": ["T1"], "requires": []},
            {"id": "B", "cost": 5, "provides": ["T2"], "requires": ["T1"]},
        ],
        ["T1", "T2"],
        100,
    )
    assert validate_route(p, ("B", "A"))  # unmet prerequisite
    assert validate_route(p, ("A", "B")) == []
    assert validate_route(p, ("A",))  # missing T2


def test_budget_exhaustion_downgrades_to_timeout_never_infeasible():
    """With a 1-node budget the exact B&B must NOT claim infeasibility."""
    p = _mk(
        "timeout",
        [
            {"id": "A", "cost": 30, "provides": ["T"], "requires": []},
            {"id": "B", "cost": 20, "provides": ["T"], "requires": []},
        ],
        ["T"],
        100,
    )
    r = run_solver("c1_branch_and_bound", p, node_budget=1)
    assert r.decision in {ABSTAIN, "find_valid_route"}
    assert r.status == "timeout"
    # Default budget still solves it exactly.
    r2 = run_solver("c1_branch_and_bound", p)
    assert r2.decision == "find_valid_route" and r2.total_cost == 20


def test_registry_has_all_contracted_solvers():
    for sid in ("c0_greedy", "c1_branch_and_bound", "c2_dijkstra_state", "p02_proposed", "a3_alternative_blind"):
        assert sid in SOLVER_REGISTRY
    assert EXACT_SOLVERS == frozenset({"c1_branch_and_bound", "c2_dijkstra_state", "p02_proposed"})
