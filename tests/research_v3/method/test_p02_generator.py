"""P02 generator + oracle tests: certified optima, family structure, split.

The generator's ground truth is NEVER fabricated: every instance stores the
verdict of the independent brute-force oracle. These tests verify that the
certification is (a) present, (b) reproducible, (c) agrees with direct
enumeration on tiny cases, and (d) that family-level group splits never leak.
"""
from __future__ import annotations

import itertools

import pytest

from research_v3.eval.leakage import audit_rows
from research_v3.eval.splitters import assert_no_leakage, freeze_hash, group_split
from research_v3.methods.p02.generator import (
    BUDGET_REGIMES,
    TOPOLOGY_FAMILIES,
    generate_case,
    generate_matrix,
)
from research_v3.methods.p02.oracle import OracleError, brute_force_verdict
from research_v3.methods.p02.problems import travel_minutes


def test_families_and_regimes_registered():
    assert TOPOLOGY_FAMILIES == (
        "chain",
        "alternative_pair",
        "dense_cover",
        "unreachable_bridge",
        "mixed_lattice",
        "blocked_access",
    )
    assert BUDGET_REGIMES == ("tight", "mid", "loose")
    with pytest.raises(ValueError):
        generate_case(family="nope", regime="mid", seed=1, index=0)
    with pytest.raises(ValueError):
        generate_case(family="chain", regime="nope", seed=1, index=0)


def test_deterministic_generation_byte_identical():
    a = generate_case(family="alternative_pair", regime="mid", seed=42, index=3, alt_density=0.5)
    b = generate_case(family="alternative_pair", regime="mid", seed=42, index=3, alt_density=0.5)
    assert a.problem.sha256() == b.problem.sha256()
    assert a.oracle.decision == b.oracle.decision
    assert a.oracle.optimum_cost == b.oracle.optimum_cost
    c = generate_case(family="alternative_pair", regime="mid", seed=42, index=4, alt_density=0.5)
    assert c.problem.sha256() != a.problem.sha256()


def test_every_generated_instance_carries_oracle_certification():
    cases = generate_matrix(seed=7, instances_per_cell=1)
    assert len(cases) == len(TOPOLOGY_FAMILIES) * len(BUDGET_REGIMES) * 3
    for c in cases:
        assert c.oracle.decision in {"find_valid_route", "no_feasible_route", "cost_exceeded"}
        if c.oracle.decision == "find_valid_route":
            assert c.oracle.optimum_cost is not None
            assert c.oracle.optimum_cost <= c.problem.budget
            assert c.oracle.optimal_route


def test_oracle_agrees_with_direct_enumeration_tiny_case():
    """Independent check: enumerate subsets x permutations in the test itself."""
    case = generate_case(family="chain", regime="mid", seed=5, index=2, alt_density=1.0)
    p = case.problem
    usable = p.usable_activities()
    ids = [a.id for a in usable]
    by_id = p.by_id()
    best = None
    for r in range(len(ids) + 1):
        for subset in itertools.combinations(ids, r):
            for perm in itertools.permutations(subset):
                acquired: set[str] = set()
                ok = True
                for sid in perm:
                    if any(req not in acquired for req in by_id[sid].requires):
                        ok = False
                        break
                    acquired |= set(by_id[sid].provides)
                if not ok or not (p.targets <= acquired):
                    continue
                cost = sum(by_id[sid].cost for sid in perm) + sum(
                    travel_minutes(p, x, y) for x, y in zip(perm, perm[1:])
                )
                if best is None or cost < best:
                    best = cost
    v = brute_force_verdict(p)
    if best is None:
        assert v.decision == "no_feasible_route"
    elif best > p.budget:
        assert v.decision == "cost_exceeded" and v.optimum_cost == best
    else:
        assert v.decision == "find_valid_route" and v.optimum_cost == best


def test_blocked_access_family_needs_gate():
    for i in range(6):
        case = generate_case(family="blocked_access", regime="mid", seed=11, index=i, alt_density=0.0)
        assert case.oracle.decision == "no_feasible_route"


def test_alternative_pair_family_has_two_providers_of_final_target():
    case = generate_case(family="alternative_pair", regime="mid", seed=3, index=0, alt_density=0.0)
    p = case.problem
    final = sorted(p.targets)[-1]
    providers = [a.id for a in p.activities if final in a.provides]
    assert len(providers) >= 2
    # A/B semantics: the instance is feasible with ONE provider.
    assert case.oracle.decision in {"find_valid_route", "cost_exceeded"}


def test_unreachable_bridge_family_is_infeasible():
    for i in range(4):
        case = generate_case(family="unreachable_bridge", regime="loose", seed=13, index=i, alt_density=1.0)
        assert case.oracle.decision == "no_feasible_route"


def test_regime_budget_shape():
    """tight regimes can be below-optimum; loose budgets exceed the optimum."""
    tight_ok = mid_ok = False
    for i in range(20):
        t = generate_case(family="chain", regime="tight", seed=21, index=i, alt_density=0.5)
        m = generate_case(family="chain", regime="loose", seed=21, index=i, alt_density=0.5)
        if t.oracle.decision == "cost_exceeded":
            tight_ok = True
        if m.oracle.decision == "find_valid_route":
            assert m.problem.budget >= (m.oracle.optimum_cost or 0)
            mid_ok = True
    assert tight_ok, "tight regime must produce cost_exceeded gold cases"
    assert mid_ok


def test_oracle_refuses_oversized_instances():
    acts = [{"id": f"a{i}", "cost": 1, "provides": [f"O{i}"], "requires": []} for i in range(15)]
    from research_v3.methods.p02.problems import parse_problem

    p = parse_problem(
        {
            "problem_id": "big",
            "family_id": "f",
            "activities": acts,
            "targets": [f"O{i}" for i in range(15)],
            "budget": 100,
            "travel": {},
        }
    )
    with pytest.raises(OracleError):
        brute_force_verdict(p)


def test_family_group_split_no_leakage():
    cases = generate_matrix(seed=20261115, instances_per_cell=3)
    rows = [
        {"case_id": c.problem.problem_id, "family_id": c.problem.family_id} for c in cases
    ]
    split = group_split(rows, group_key="family_id", paper_id="P02", protocol="group")
    assert_no_leakage(split)
    # Determinism + hash stability.
    split2 = group_split(rows, group_key="family_id", paper_id="P02", protocol="group")
    assert freeze_hash(split) == freeze_hash(split2)
    # All four partitions non-empty at this family count.
    assert all(len(ids) > 0 for ids in split.split_ids.values())
    # Inputs carry no gold keys (leakage audit of the instance payloads).
    payloads = [{"case_id": c.problem.problem_id, "input": c.problem.to_dict()} for c in cases]
    report = audit_rows(payloads, strict=True)
    assert report["status"] == "PASS"
