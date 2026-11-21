"""Measure minimum same-group substitutions in the archived CatBoost order."""
import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from fractions import Fraction
from math import ceil
from pathlib import Path

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp

HERE = Path(__file__).resolve().parent
JOINT = HERE.parent / "joint"
BOOSTED = JOINT / "boosted" / "run"
sys.path.insert(0, str(JOINT))

from frontier import optimal
from screen import cohort_data
from policies import fair_rank, prefix_table

BANDS = (0, 1, 5, 10, None)


@dataclass
class Course:
    name: str
    table: np.ndarray
    keys: tuple
    male: np.ndarray
    female: np.ndarray

    @property
    def seats(self):
        return len(self.table)


def read_json(path):
    return json.loads(path.read_text())


def captured(method):
    return method["captures_f"] + method["captures_m"]


def freeze(name, raw):
    """Prepare rankings, archive controls and targets before requesting outcomes."""
    _, test, _, _, _, outcomes, source = cohort_data(name, raw)
    archive = BOOSTED / f"{name}_forecasts.npz"
    hashes = dict(line.split()[::-1] for line in (BOOSTED / "forecasts.sha256").read_text().splitlines())
    assert hashlib.sha256(archive.read_bytes()).hexdigest() == hashes[archive.name]
    with np.load(archive) as data:
        scores = data["scores"]
        assert scores.shape == (41, len(test))
        assert np.all((scores > 0) & (scores < 1))
        assert data["ordered_keys"].item() == hashlib.sha256("\n".join(test.key).encode()).hexdigest()

    courses = []
    for pool, ordered in test.assign(p=scores[0]).groupby("pool"):
        ordered = ordered.sort_values(["p", "sid"], ascending=[False, True])
        female = ordered.female.to_numpy()
        table = prefix_table(len(ordered) // 10, female.mean())
        courses.append(Course(str(pool), table, tuple(ordered.key),
                              np.flatnonzero(~female), np.flatnonzero(female)))

    archives = {
        scorer: read_json(directory / "results.json")[name]
        for scorer, directory in [("logistic", JOINT / "run"), ("boosted", BOOSTED)]
    }
    cases = archives["boosted"]["female_cases"], archives["boosted"]["male_cases"]
    seats = sum(course.seats for course in courses)
    floors = {}
    for scorer, result in archives.items():
        assert (result["female_cases"], result["male_cases"]) == cases
        assert result["learners"] == len(test) and result["pools"] == len(courses)
        for method in result["methods"].values():
            assert method["seats"] == seats
        floors[scorer] = captured(result["methods"]["unrestricted"]) - seats // 100

    controls = {}
    constrained_recalls = {}
    for scorer, result in archives.items():
        for policy, method in result["methods"].items():
            recall = min(Fraction(method[key], total) for key, total in
                         zip(("captures_f", "captures_m"), cases))
            controls[f"{scorer}/{policy}"] = {
                "female_captured": method["captures_f"], "male_captured": method["captures_m"],
                "worst_group_recall": float(recall), "precision": captured(method) / seats,
                "meets_original_floor": captured(method) >= floors["logistic"],
                "meets_boosted_floor": captured(method) >= floors["boosted"],
            }
            if policy != "unrestricted":
                constrained_recalls[f"{scorer}/{policy}"] = recall
    recall = max(constrained_recalls.values())
    best_policies = [policy for policy, rate in constrained_recalls.items() if rate == recall]
    recall_goal = recall + Fraction(1, 50)
    goals = tuple(ceil(recall_goal * total) for total in cases)
    return courses, outcomes, {
        **source, "learners": len(test), "pools": len(courses), "seats": seats,
        "female_cases": cases[0], "male_cases": cases[1], "capture_floors": floors,
        "point_archive_sha256": hashes[archive.name],
        "best_constrained_archived_policies": best_policies,
        "best_constrained_archived_recall": float(recall),
        "recall_target": str(recall_goal), "target_captures": dict(zip(("female", "male"), goals)),
        "archived_controls": controls,
    }


def group_options(labels, counts, band):
    sums = np.r_[0, np.cumsum(labels)]
    low = 0 if band is None else np.maximum(0, counts - band)
    high = len(labels) if band is None else np.minimum(len(labels), counts + band)
    negatives = counts - low - (sums[counts] - sums[low])
    positives = sums[high] - sums[counts]
    return sums[counts], np.minimum(negatives, positives)


def course_options(course, labels, band):
    female = np.arange(max(course.table[-1], course.seats - len(course.male)),
                       min(course.seats, len(course.female)) + 1)
    f, f_cap = group_options(labels[course.female], female, band)
    m, m_cap = group_options(labels[course.male], course.seats - female, band)
    return np.column_stack((female, f, m, f_cap, m_cap)).tolist()


def minimum_plan(tables, floor, group_goals):
    """Choose one feasible split per course and integer improvements per group."""
    n = len(tables)
    starts = np.r_[0, np.cumsum([len(table) for table in tables])]
    options = starts[-1]
    constraints = np.zeros((3 * n + 3, options + 2 * n))
    for i, table in enumerate(tables):
        values = np.asarray(table)
        section = slice(starts[i], starts[i + 1])
        constraints[i, section] = 1
        for group in range(2):
            gain = options + 2 * i + group
            row = n + 2 * i + group
            constraints[row, section] = -values[:, 3 + group]
            constraints[row, gain] = 1
            constraints[-3 + group, section] = values[:, 1 + group]
            constraints[-3 + group, gain] = 1
    constraints[-1] = constraints[-3] + constraints[-2]
    lower = np.r_[np.ones(n), np.full(2 * n, -np.inf), group_goals, floor]
    upper = np.r_[np.ones(n), np.zeros(2 * n), np.full(3, np.inf)]
    objective = np.r_[np.zeros(options), np.ones(2 * n)]
    result = milp(objective, integrality=np.ones(len(objective)),
                  bounds=Bounds(0, np.r_[np.ones(options), np.full(2 * n, np.inf)]),
                  constraints=LinearConstraint(constraints, lower, upper),
                  options={"mip_rel_gap": 0.0})
    if not result.success:
        raise RuntimeError(result.message)
    solution = np.rint(result.x).astype(int)
    assert np.allclose(solution, result.x, atol=1e-6, rtol=0)
    assert np.all(constraints @ solution >= lower) and np.all(constraints @ solution <= upper)
    assert int(sum(solution[options:])) == round(result.fun)
    return [
        (int(np.flatnonzero(solution[starts[i]:starts[i + 1]]).item()),
         int(solution[options + 2 * i]), int(solution[options + 2 * i + 1]))
        for i in range(n)
    ]


def verify_plan(courses, labels, tables, band, plan, floor, group_goals):
    captures = np.zeros(2, dtype=int)
    for course, y, options, (pick, f_gain, m_gain) in zip(courses, labels, tables, plan, strict=True):
        n, f, m, f_cap, m_cap = options[pick]
        retained = []
        for group, (positions, seats, base, gain, capacity) in enumerate(
            ((course.female, n, f, f_gain, f_cap),
             (course.male, course.seats - n, m, m_gain, m_cap))
        ):
            assert 0 <= gain <= capacity
            ranks = np.arange(len(positions))
            chosen = ranks < seats
            in_band = np.ones_like(chosen) if band is None else (
                (ranks >= seats - band) & (ranks < seats + band)
            )
            removed = np.flatnonzero(chosen & ~y[positions] & in_band)[:gain]
            admitted = np.flatnonzero(~chosen & y[positions] & in_band)[:gain]
            assert len(removed) == len(admitted) == gain
            chosen[removed] = False
            chosen[admitted] = True
            retained.append(positions[chosen])
            assert len(retained[-1]) == seats
            hits = int(y[retained[-1]].sum())
            assert hits == base + gain
            captures[group] += hits
        ranking = fair_rank(*retained, course.table)
        assert len(set(ranking)) == course.seats
        assert (np.isin(ranking, course.female).cumsum() >= course.table).all()
    assert sum(captures) >= floor and np.all(captures >= group_goals)
    return int(sum(f + m for _, f, m in plan))


def budget_frontier(tables, budget):
    """In each cell (at most edits, exact female captures), maximize male captures."""
    unreachable = -10_000
    states = np.zeros((budget + 1, 1), dtype=np.int32)
    for table in tables:
        local = {}
        for _, female, male, f_cap, m_cap in table:
            for f_gain in range(min(f_cap, budget) + 1):
                opportunities = local.setdefault(female + f_gain, {})
                for m_gain in range(min(m_cap, budget - f_gain) + 1):
                    edits = f_gain + m_gain
                    opportunities[edits] = max(opportunities.get(edits, -1), male + m_gain)
        after = np.full((budget + 1, states.shape[1] + max(local)), unreachable, dtype=np.int32)
        for female, options in local.items():
            best = -1
            for edits, male in sorted(options.items()):
                if male > best:
                    shifted = after[edits:, female:female + states.shape[1]]
                    before = states[:budget + 1 - edits]
                    np.maximum(shifted, before + male, out=shifted, where=before != unreachable)
                    best = male
        states = after
    return states


def feasible(male_counts, floor, group_goals):
    female_counts = np.arange(len(male_counts))
    return np.any((female_counts >= group_goals[0]) & (male_counts >= group_goals[1])
                  & (female_counts + male_counts >= floor))


def band_report(courses, labels, band, summary):
    tables = [course_options(course, y, band) for course, y in zip(courses, labels, strict=True)]
    # Taking all useful replacements at a split dominates using fewer when
    # there is no edit limit. The full-capacity DP also proves infeasibility.
    saturated = [[(n, f + f_cap, m + m_cap) for n, f, m, f_cap, m_cap in table]
                 for table in tables]
    max_capture = sum(max(f + m for _, f, m in table) for table in saturated)
    unlimited = budget_frontier(
        [[(n, f, m, 0, 0) for n, f, m in table] for table in saturated], 0
    )[0]
    cases = summary["female_cases"], summary["male_cases"]
    goals = tuple(summary["target_captures"][group] for group in ("female", "male"))
    rows = {}
    for scorer, floor in summary["capture_floors"].items():
        upper = optimal([{"course": course.name} for course in courses], saturated, *cases, floor)
        row = {"worst_group_recall_ceiling": upper.get("worst_recall")}
        for goal_name, group_goals in [("precision_only", (0, 0)), ("precision_and_recall", goals)]:
            count = None
            if feasible(unlimited, floor, group_goals):
                plan = minimum_plan(tables, floor, group_goals)
                count = verify_plan(courses, labels, tables, band, plan, floor, group_goals)
                check = budget_frontier(tables, count)
                assert feasible(check[count], floor, group_goals)
                assert count == 0 or not feasible(check[count - 1], floor, group_goals)
            row[goal_name] = {"feasible": count is not None, "minimum_replacements": count}
        rows[scorer] = row
    return {"maximum_captures": max_capture, "floors": rows}, saturated


def check_archive(name, band, report, saturated, courses, summary):
    title = "fixed_score_order" if band == 0 else "free_within_group_order"
    for scorer, filename in [("logistic", "logistic_floor.json"), ("boosted", "frontier.json")]:
        archived = read_json(BOOSTED / filename)[name]
        assert archived["required_captures"] == summary["capture_floors"][scorer]
        assert archived["seats"] == summary["seats"]
        bound = archived[title]
        actual_tables = {c.name: [list(row) for row in table]
                         for c, table in zip(courses, saturated, strict=True)}
        assert actual_tables == bound["course_tables"]
        assert report["floors"][scorer]["worst_group_recall_ceiling"] == bound.get("worst_recall")


def evaluate(name, courses, outcomes, summary):
    target = outcomes({key for course in courses for key in course.keys})
    labels = [np.array([target[key] for key in course.keys], dtype=bool) for course in courses]
    for group in ("female", "male"):
        assert summary[f"{group}_cases"] == sum(
            y[getattr(course, group)].sum() for course, y in zip(courses, labels, strict=True)
        )
    assert sum(int(y[:course.seats].sum()) for course, y in zip(courses, labels, strict=True)) == (
        summary["archived_controls"]["boosted/unrestricted"]["female_captured"]
        + summary["archived_controls"]["boosted/unrestricted"]["male_captured"]
    )
    summary["bands"] = {}
    for band in BANDS:
        report, saturated = band_report(courses, labels, band, summary)
        summary["bands"]["unrestricted" if band is None else str(band)] = report
        if band in (0, None):
            check_archive(name, band, report, saturated, courses, summary)
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("raw", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    frozen = {name: freeze(name, args.raw) for name in ("oulad", "uci697")}
    results = {name: evaluate(name, *payload) for name, payload in frozen.items()}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(results, indent=2, allow_nan=False) + "\n")
