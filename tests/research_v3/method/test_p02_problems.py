"""P02 problem contract tests: typed instances, gates, canonical hashing."""
from __future__ import annotations

import pytest

from research_v3.methods.p02.problems import (
    ABSTAIN,
    NOT_APPLICABLE,
    Activity,
    PlanningProblem,
    ProblemError,
    SolverResult,
    parse_problem,
    travel_minutes,
)


def _problem(**over) -> PlanningProblem:
    base = dict(
        problem_id="p1",
        family_id="fam|d0.5",
        activities=(
            Activity(id="A", cost=40, provides=("T",), requires=()),
            Activity(id="B", cost=40, provides=("T",), requires=()),
        ),
        targets=frozenset({"T"}),
        budget=50,
        travel={},
    )
    base.update(over)
    return PlanningProblem(**base)


def test_alternative_providers_both_usable():
    p = _problem()
    assert len(p.usable_activities()) == 2
    assert travel_minutes(p, "A", "B") == 0


def test_activity_validation():
    with pytest.raises(ProblemError):
        Activity(id="", cost=1, provides=("T",), requires=())
    with pytest.raises(ProblemError):
        Activity(id="A", cost=-1, provides=("T",), requires=())
    with pytest.raises(ProblemError):
        Activity(id="A", cost=1, provides=("T",), requires=(), source_tier="bogus")


def test_problem_validation_duplicate_ids_and_bad_travel():
    with pytest.raises(ProblemError):
        _problem(
            activities=(
                Activity(id="A", cost=1, provides=("T",), requires=()),
                Activity(id="A", cost=2, provides=("T2",), requires=()),
            )
        )
    with pytest.raises(ProblemError):
        _problem(travel={("A", "ZZ"): 5})
    with pytest.raises(ProblemError):
        _problem(budget=-5)


def test_frozen_travel_matrix():
    p = _problem(travel={("A", "B"): 5})
    with pytest.raises(TypeError):
        p.travel[("A", "B")] = 9  # type: ignore[index]


def test_sha256_deterministic_and_payload_sensitive():
    p1 = _problem()
    p2 = _problem()
    assert p1.sha256() == p2.sha256()
    p3 = _problem(budget=51)
    assert p1.sha256() != p3.sha256()


def test_gates_accessible_and_source_floor():
    p = _problem(
        activities=(
            Activity(id="A", cost=10, provides=("T",), requires=(), accessible=False),
            Activity(id="B", cost=20, provides=("T",), requires=(), source_tier="unverified"),
        )
    )
    assert [a.id for a in p.usable_activities()] == []
    p2 = _problem(
        activities=(
            Activity(id="A", cost=10, provides=("T",), requires=(), accessible=False),
            Activity(id="B", cost=20, provides=("T",), requires=(), source_tier="review_pending"),
        ),
        min_source_tier="review_pending",
    )
    assert [a.id for a in p2.usable_activities()] == ["B"]


def test_parse_problem_round_trip():
    raw = {
        "problem_id": "rt",
        "family_id": "fam",
        "activities": [
            {"id": "A", "cost": 40, "provides": ["T"], "requires": []},
            {"id": "B", "cost": 40, "provides": ["T"], "requires": []},
        ],
        "targets": ["T"],
        "budget": 50,
        "travel": {"A->B": 3},
    }
    p = parse_problem(raw)
    assert travel_minutes(p, "A", "B") == 3
    again = parse_problem(p.to_dict())
    assert again.sha256() == p.sha256()


def test_sentinels_distinct():
    assert ABSTAIN != NOT_APPLICABLE
    assert ABSTAIN == "ABSTAIN"
    assert NOT_APPLICABLE == "NOT_APPLICABLE"


def test_solver_result_rejects_route_on_infeasible():
    with pytest.raises(ProblemError):
        SolverResult(
            problem_id="p1", solver_id="x", decision="no_feasible_route",
            status="optimal", route=("A",), total_cost=40, dwell_cost=40,
            travel_cost=0,
        )
    with pytest.raises(ProblemError):
        SolverResult(
            problem_id="p1", solver_id="x", decision="find_valid_route",
            status="abstain", route=("A",), total_cost=40, dwell_cost=40,
            travel_cost=0,
        )
    with pytest.raises(ProblemError):
        SolverResult(
            problem_id="p1", solver_id="x", decision="weird", status="optimal",
            route=(), total_cost=0, dwell_cost=0, travel_cost=0,
        )
