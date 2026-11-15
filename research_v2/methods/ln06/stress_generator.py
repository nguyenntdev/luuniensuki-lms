"""LN-06 T3 stress-scenario generator (deterministic, family/seed controlled).

Extends beyond the legacy five balanced fault strata with the T3 stress axes
required by the spec (08_T3_STRESS_GENERATOR):

- alternative providers for the same objective (the mandatory A/B case)
- unreachable bridges (missing provider in the prerequisite chain)
- asymmetric travel times
- multiple valid routes
- budgets near the feasibility boundary

Every generated scenario is paired with an expected decision derived from the
independent brute-force rubric oracle - never from the proposed policy itself.
Generation is fully deterministic per (family, seed): no global RNG state.
"""
from __future__ import annotations

import random
from typing import Any

from .dataset import TrailCase
from .labels import DECISION_VALUES
from .rubric import RubricError, brute_force_expected_decision

STRESS_FAMILIES = (
    "alternative_providers",
    "unreachable_bridge",
    "asymmetric_travel",
    "multiple_valid_routes",
    "boundary_budget",
)


def _learner(profile_seq: int, seed: int) -> dict[str, Any]:
    rng = random.Random(hash(("learner", profile_seq, seed)) & 0xFFFFFFFF)
    return {
        "competencies": {
            "S1": round(0.3 + 0.4 * rng.random(), 3),
            "S2": round(0.3 + 0.3 * rng.random(), 3),
        },
        "profile_id": f"STRESS-LEARNER-{profile_seq:04d}",
        "synthetic": True,
        "evaluation_mode": "programmatic_synthetic_scenario",
    }


def generate_stress_case(family: str, seed: int, case_index: int) -> dict[str, Any]:
    """Build one deterministic stress scenario ``input`` mapping."""
    if family not in STRESS_FAMILIES:
        raise ValueError(f"unknown stress family {family!r}; known: {STRESS_FAMILIES}")
    rng = random.Random(hash((family, seed, case_index)) & 0xFFFFFFFF)
    stops: list[dict[str, Any]] = []
    targets: list[str] = []
    verified = True

    if family == "alternative_providers":
        # Mandatory shape: A and B both provide T at 40 each; one extra cheap
        # stop; budget 50 forces choosing exactly one of A/B.
        a_on = rng.random() < 0.5
        stops = [
            {"id": "A", "cost": 40, "provides": ["T"], "requires": [], "type": "alt"},
            {"id": "B", "cost": 40, "provides": ["T"], "requires": [], "type": "alt"},
            {"id": "C", "cost": 10, "provides": ["U"], "requires": ["T"], "type": "alt"},
        ]
        targets = ["T", "U"] if a_on else ["T"]

    elif family == "unreachable_bridge":
        stops = [
            {"id": "s1", "cost": 10, "provides": ["o1"], "requires": [], "type": "chain"},
            {"id": "s2", "cost": 10, "provides": ["o2"], "requires": ["o1"], "type": "chain"},
            {"id": "s4", "cost": 10, "provides": ["o4"], "requires": ["o3"], "type": "chain"},
        ]
        targets = ["o1", "o2", "o4"]  # o3 has no provider anywhere

    elif family == "asymmetric_travel":
        stops = [
            {"id": "s1", "cost": 10, "provides": ["o1"], "requires": [], "type": "travel"},
            {"id": "s2", "cost": 10, "provides": ["o2"], "requires": [], "type": "travel"},
        ]
        targets = ["o1", "o2"]

    elif family == "multiple_valid_routes":
        stops = [
            {"id": "p1", "cost": 15, "provides": ["o1"], "requires": [], "type": "route"},
            {"id": "p2", "cost": 15, "provides": ["o2"], "requires": [], "type": "route"},
            {"id": "q1", "cost": 12, "provides": ["o1", "o2"], "requires": [], "type": "route"},
        ]
        targets = ["o1", "o2"]

    else:  # boundary_budget
        chain_cost = 30
        stops = [
            {"id": "c1", "cost": 10, "provides": ["o1"], "requires": [], "type": "chain"},
            {"id": "c2", "cost": 20, "provides": ["o2"], "requires": ["o1"], "type": "chain"},
        ]
        targets = ["o1", "o2"]
        # Budget sits exactly on the minimal feasible cost (boundary).
        budget = chain_cost if rng.random() < 0.5 else chain_cost - 1
        scenario = {
            "case_id": f"LN-06-STRESS-{family}-{case_index:05d}",
            "stops": stops,
            "available_stops": [s["id"] for s in stops],
            "target_outcomes": targets,
            "time_budget_minutes": budget,
            "checkpoint_claim_verified": verified,
            "learner": _learner(case_index, seed),
            "seed": seed,
        }
        return scenario

    scenario = {
        "case_id": f"LN-06-STRESS-{family}-{case_index:05d}",
        "stops": stops,
        "available_stops": [s["id"] for s in stops],
        "target_outcomes": targets,
        "time_budget_minutes": 50,
        "checkpoint_claim_verified": verified,
        "learner": _learner(case_index, seed),
        "seed": seed,
    }
    if family == "asymmetric_travel":
        go = 5 + int(rng.random() * 10)
        back = go + 5 + int(rng.random() * 10)
        scenario["travel_edges"] = [
            {"from": "s1", "to": "s2", "minutes": go},
            {"from": "s2", "to": "s1", "minutes": back},
        ]
        scenario["time_budget_minutes"] = 25 + back  # boundary varies with travel
    if family == "multiple_valid_routes":
        scenario["time_budget_minutes"] = 12 if rng.random() < 0.5 else 15
    return scenario


def generate_stress_batch(
    seed: int, *, n_per_family: int = 3, max_stops: int = 12
) -> list[dict[str, Any]]:
    """Generate a labelled stress batch: input + oracle-side expected decision."""
    rows: list[dict[str, Any]] = []
    for family in STRESS_FAMILIES:
        for i in range(n_per_family):
            scenario = generate_stress_case(family, seed, i + 1)
            case = TrailCase.from_features(scenario, case_id=str(scenario["case_id"]))
            try:
                expected = brute_force_expected_decision(case, max_stops=max_stops)
            except RubricError as exc:
                raise ValueError(f"stress case {case.case_id!r}: {exc}") from exc
            if expected not in DECISION_VALUES:
                raise ValueError(f"stress case {case.case_id!r}: oracle produced illegal label {expected!r}")
            rows.append(
                {
                    "case_id": scenario["case_id"],
                    "input": scenario,
                    "oracle_expected_decision_evaluator_only": expected,
                }
            )
    return rows
