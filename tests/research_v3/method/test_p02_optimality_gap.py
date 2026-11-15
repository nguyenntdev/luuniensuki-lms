"""P02 optimality-gap tests vs the independent brute-force oracle.

The generator certifies each instance with the oracle; these tests then
require every exact solver to reproduce the certified optimum exactly on
randomised small instances (this is the 'optimality gap vs brute force'
mandate) and on hand-built adversarial cases where greedy heuristics fail.
"""
from __future__ import annotations

import pytest

from research_v3.methods.p02.generator import generate_case, generate_matrix
from research_v3.methods.p02.metrics import evaluate_cell
from research_v3.methods.p02.problems import parse_problem
from research_v3.methods.p02.solvers import run_solver

EXACT_IDS = ("c1_branch_and_bound", "c2_dijkstra_state", "p02_proposed")


@pytest.mark.parametrize("family", ["chain", "alternative_pair", "dense_cover", "mixed_lattice"])
@pytest.mark.parametrize("regime", ["tight", "mid", "loose"])
def test_exact_solvers_match_oracle_random_small(family, regime):
    """Certified-oracle agreement over randomised small instances (20 per cell)."""
    cases = [
        generate_case(family=family, regime=regime, seed=99, index=i, alt_density=d)
        for i in range(7)
        for d in (0.0, 0.5, 1.0)
    ]
    for sid in EXACT_IDS:
        results = [run_solver(sid, c.problem) for c in cases]
        cell = evaluate_cell(sid, cases, results)
        assert cell.false_infeasibility == 0, (sid, family, regime)
        assert cell.false_feasible == 0, (sid, family, regime)
        assert cell.mean_relative_gap in (None, 0.0), (sid, family, regime)


def test_adversarial_cover_greedy_trap():
    """Cheapest-single-pick greedy is lured; the exact optimum uses the joint set."""
    p = parse_problem(
        {
            "problem_id": "greedy-trap",
            "family_id": "dense_cover",
            "activities": [
                {"id": "cheap1", "cost": 3, "provides": ["O1"], "requires": []},
                {"id": "cheap2", "cost": 3, "provides": ["O2"], "requires": []},
                {"id": "cheap3", "cost": 3, "provides": ["O3"], "requires": []},
                {"id": "joint", "cost": 7, "provides": ["O1", "O2", "O3"], "requires": []},
            ],
            "targets": ["O1", "O2", "O3"],
            "budget": 7,
            "travel": {},
        }
    )
    from research_v3.methods.p02.oracle import brute_force_verdict

    v = brute_force_verdict(p)
    assert v.decision == "find_valid_route" and v.optimum_cost == 7
    r = run_solver("p02_proposed", p)
    assert r.decision == "find_valid_route" and r.total_cost == 7
    assert r.status == "optimal"
    # The sanity greedy must fall into the trap (over budget or worse cost).
    c0 = run_solver("c0_greedy", p)
    assert c0.decision != "find_valid_route" or c0.total_cost > 7


def test_asymmetric_travel_order_matters():
    """Order-aware optimality: the cheap subset ordered badly exceeds budget."""
    p = parse_problem(
        {
            "problem_id": "asym",
            "family_id": "mixed_lattice",
            "activities": [
                {"id": "A", "cost": 10, "provides": ["T1"], "requires": []},
                {"id": "B", "cost": 10, "provides": ["T2"], "requires": []},
            ],
            "targets": ["T1", "T2"],
            "budget": 22,
            "travel": {"A->B": 20, "B->A": 1},
        }
    )
    r = run_solver("p02_proposed", p)
    assert r.decision == "find_valid_route"
    assert r.route[0] == "B" and r.total_cost == 21


def test_prerequisite_closure_increases_cost():
    """The cheap provider pulls in a prerequisite making it dearer than the
    standalone provider; exact solvers must price the closure and pick base."""
    p = parse_problem(
        {
            "problem_id": "closure",
            "family_id": "chain",
            "activities": [
                {"id": "base", "cost": 12, "provides": ["T"], "requires": []},
                {"id": "cheap", "cost": 5, "provides": ["T"], "requires": ["PRE"]},
                {"id": "prep", "cost": 10, "provides": ["PRE"], "requires": []},
            ],
            "targets": ["T"],
            "budget": 30,
            "travel": {},
        }
    )
    for sid in EXACT_IDS:
        r = run_solver(sid, p)
        assert r.decision == "find_valid_route", (sid, r)
        assert r.total_cost == 12 and "base" in r.route, (sid, r)
    # And when base is over budget, the closure path is correctly priced too:
    p_tight = parse_problem(
        {
            "problem_id": "closure-tight",
            "family_id": "chain",
            "activities": [
                {"id": "base", "cost": 12, "provides": ["T"], "requires": []},
                {"id": "cheap", "cost": 5, "provides": ["T"], "requires": ["PRE"]},
                {"id": "prep", "cost": 10, "provides": ["PRE"], "requires": []},
            ],
            "targets": ["T"],
            "budget": 12,
            "travel": {},
        }
    )
    r2 = run_solver("p02_proposed", p_tight)
    assert r2.decision == "find_valid_route" and r2.total_cost == 12


def test_larger_random_matrix_zero_gap_zero_false_infeasibility():
    """Full matrix slice (54 instances): exact solvers are gap-free."""
    cases = generate_matrix(seed=555, instances_per_cell=1)
    for sid in EXACT_IDS:
        results = [run_solver(sid, c.problem) for c in cases]
        cell = evaluate_cell(sid, cases, results).to_dict()
        assert cell["false_infeasibility"] == 0, (sid, cell)
        assert cell["false_feasible"] == 0
        assert cell["mean_relative_gap"] in (None, 0.0)


def test_c0_greedy_is_not_exact_somewhere():
    """C0 sanity must NOT be exact on the full matrix (generator sanity check):
    a C0 'win' would indicate the benchmark is trivial."""
    cases = generate_matrix(seed=555, instances_per_cell=2)
    results = [run_solver("c0_greedy", c.problem) for c in cases]
    cell = evaluate_cell("c0_greedy", cases, results).to_dict()
    assert cell["exact_match_rate"] < 1.0
    assert cell["false_infeasibility"] > 0 or (cell["mean_relative_gap"] or 0) > 0


def test_a3_mutation_reproduces_false_infeasibility_on_alternatives():
    """The A3 ablation must reproduce the legacy false-infeasibility family."""
    cases = [
        generate_case(family="alternative_pair", regime="mid", seed=31, index=i, alt_density=0.0)
        for i in range(6)
    ]
    results = [run_solver("a3_alternative_blind", c.problem) for c in cases]
    cell = evaluate_cell("a3_alternative_blind", cases, results)
    assert cell.false_infeasibility > 0, "A3 mutation failed to reproduce the legacy bug"
