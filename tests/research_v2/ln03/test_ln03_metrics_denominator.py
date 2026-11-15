"""Denominator/numerator integrity tests for LN-03 diagnostic metrics.

Regression coverage for the evaluator-side metric module
``research_v2.methods.ln03.metrics``:

- a row failing BOTH gates must be counted once (rate <= 1.0),
- numerator/denominator are reported explicitly and consistently,
- a zero-denominator run yields ``rate=None`` (no crash, no fake 1.0),
- the Wilson CI is present and bounded within [0, 1].
"""
from __future__ import annotations

import math

from research_v2.methods.ln03.metrics import (
    invalid_generative_assignment_rate,
    summarize,
)


def _row(
    decision: str,
    fact_ok: bool,
    src_ok: bool,
    *,
    task_type: str = "historical_explanation",
    omit_fact: bool = False,
    omit_card: bool = False,
):
    features: dict = {"task_type": task_type}
    if not omit_fact:
        features["fact_prerequisite_mastered"] = fact_ok
    if not omit_card:
        features["review_card"] = {"source_verified": src_ok}
    return {"decision": decision, "input": features}


def test_row_failing_both_gates_counted_once_rate_within_bounds():
    rows = [
        # at-risk row failing BOTH gates -> numerator += 1 (not 2)
        _row("schedule_eligible", fact_ok=False, src_ok=False),
        # healthy at-risk row
        _row("schedule_eligible", fact_ok=True, src_ok=True),
        # not at risk: wrong decision
        _row("assign_fact_retrieval", fact_ok=False, src_ok=False),
    ]
    result = invalid_generative_assignment_rate(rows)
    assert result["numerator"] == 1
    assert result["denominator"] == 2
    assert result["rate"] == 0.5
    assert 0.0 <= result["rate"] <= 1.0
    # both gate failures still attributed per-gate
    assert result["per_gate"]["missing_fact_base"] == 1
    assert result["per_gate"]["absent_source"] == 1


def test_all_invalid_rows_rate_is_exactly_one_not_greater():
    rows = [_row("schedule_eligible", fact_ok=False, src_ok=False) for _ in range(5)]
    result = invalid_generative_assignment_rate(rows)
    assert result["denominator"] == 5
    assert result["numerator"] == 5
    assert result["rate"] == 1.0


def test_numerator_denominator_reported_and_consistent():
    rows = [
        _row("schedule_eligible", fact_ok=True, src_ok=False),
        _row("schedule_eligible", fact_ok=False, src_ok=True),
        _row("schedule_eligible", fact_ok=True, src_ok=True),
        _row("hold", fact_ok=False, src_ok=False, task_type="fact_retrieval"),
    ]
    result = invalid_generative_assignment_rate(rows)
    assert result["denominator"] == 3
    assert result["numerator"] == 2
    assert math.isclose(result["rate"], 2 / 3)
    assert result["numerator"] <= result["denominator"]
    nested = summarize(rows)["invalid_generative_assignment"]
    assert nested == result


def test_missing_feature_fields_are_fail_closed_but_counted_once():
    rows = [_row("schedule_eligible", fact_ok=False, src_ok=False, omit_fact=True, omit_card=True)]
    result = invalid_generative_assignment_rate(rows)
    assert result["denominator"] == 1
    assert result["numerator"] == 1
    assert result["rate"] == 1.0
    assert result["per_gate"]["missing_fact_base"] == 1
    assert result["per_gate"]["absent_source"] == 1


def test_zero_denominator_returns_rate_none_with_none_ci():
    rows = [
        _row("assign_fact_retrieval", fact_ok=False, src_ok=False),
        _row("schedule_eligible", fact_ok=False, src_ok=False, task_type="fact_retrieval"),
    ]
    result = invalid_generative_assignment_rate(rows)
    assert result["denominator"] == 0
    assert result["numerator"] == 0
    assert result["rate"] is None
    assert result["ci95"] == [None, None]


def test_zero_denominator_via_empty_input():
    result = invalid_generative_assignment_rate([])
    assert result["denominator"] == 0
    assert result["numerator"] == 0
    assert result["rate"] is None
    assert result["ci95"] == [None, None]


def test_wilson_ci_present_and_within_unit_interval():
    rows = (
        [_row("schedule_eligible", fact_ok=True, src_ok=True) for _ in range(8)]
        + [_row("schedule_eligible", fact_ok=False, src_ok=True)]
        + [_row("schedule_eligible", fact_ok=True, src_ok=False)]
    )
    result = invalid_generative_assignment_rate(rows)
    lo, hi = result["ci95"]
    assert lo is not None and hi is not None
    assert 0.0 <= lo <= hi <= 1.0
    assert lo <= result["rate"] <= hi
