"""Cross-check the two optimization formulations against enumerated learner sets."""
from itertools import combinations, product

import numpy as np
import pytest

from run import Course, budget_frontier, course_options, feasible, minimum_plan, verify_plan


def enumerate_group(labels, seats, band):
    baseline = set(range(seats))
    permitted = set(range(len(labels))) if band is None else {
        rank for rank in range(len(labels)) if seats - band <= rank < seats + band
    }
    for chosen in combinations(range(len(labels)), seats):
        changed = baseline.symmetric_difference(chosen)
        if changed <= permitted:
            yield len(changed) // 2, sum(int(labels[i]) for i in chosen)


def enumerate_course(course, labels, band):
    for seats in range(course.seats + 1):
        if seats < course.table[-1]:
            continue
        f = enumerate_group(labels[course.female], seats, band)
        m = enumerate_group(labels[course.male], course.seats - seats, band)
        for (f_edits, f_hits), (m_edits, m_hits) in product(f, m):
            yield f_edits + m_edits, f_hits, m_hits


@pytest.mark.parametrize("band", [0, 1, 2, None])
def test_budget_frontier_matches_exhaustive_subsets(band):
    courses = [
        Course("a", np.array([0, 1]), (), np.array([1, 2, 4]), np.array([0, 3, 5])),
        Course("b", np.array([0, 0]), (), np.array([0, 2, 3]), np.array([1, 4])),
    ]
    labels = [np.array(row, dtype=bool) for row in ([0, 0, 1, 1, 1, 0], [0, 1, 0, 1, 1])]
    tables = [course_options(c, y, band) for c, y in zip(courses, labels, strict=True)]
    exact = [
        (edits + other_edits, f + other_f, m + other_m)
        for (edits, f, m), (other_edits, other_f, other_m)
        in product(*(enumerate_course(c, y, band) for c, y in zip(courses, labels, strict=True)))
    ]
    maximum_budget = sum(c.seats for c in courses)
    frontier = budget_frontier(tables, maximum_budget)
    for floor, f_goal, m_goal in product(range(6), range(5), range(5)):
        goal = (f_goal, m_goal)
        minimum = min((edits for edits, f, m in exact
                       if f >= f_goal and m >= m_goal and f + m >= floor), default=None)
        assert [bool(feasible(row, floor, goal)) for row in frontier] == [
            minimum is not None and budget >= minimum for budget in range(maximum_budget + 1)
        ]
    # Check exact integer optima including a precision-only target, both group
    # constraints, and a zero-edit feasible target, depending on the band.
    for floor, goal in [(0, (0, 0)), (3, (0, 0)), (3, (2, 1)), (4, (1, 2))]:
        if feasible(frontier[-1], floor, goal):
            plan = minimum_plan(tables, floor, goal)
            edits = verify_plan(courses, labels, tables, band, plan, floor, goal)
            assert edits == next(b for b, row in enumerate(frontier) if feasible(row, floor, goal))
