"""LN-03 study-local metrics (evaluator-side diagnostics).

The sealed evaluation path (``research_v2.evaluation.metrics.compute_metrics``)
remains the authoritative metric source for matrix runs. This module provides
study-specific diagnostics over saved prediction rows:

- ``invalid_generative_assignment_rate`` (primary-metric counterpart): the
  fraction of *at-risk* rows where a generative explanation was scheduled
  without a stable fact base or a verified source.
- mode/decision distribution and gate-level audit counts.

Unit of analysis for ``invalid_generative_assignment_rate``:

- **Denominator**: rows AT RISK — every row whose ``decision`` is
  ``schedule_eligible`` AND whose ``task_type`` is ``historical_explanation``
  (i.e. a generative task was actually assigned at inference time). Rows that
  are not at risk (other decisions or other task types) are excluded from both
  numerator and denominator.
- **Numerator**: at-risk rows that violate the fact-stability gate OR the
  source gate. Each row is counted **at most once** (a row failing both gates
  contributes 1 to the numerator, not 2). Gate-level ``per_gate`` counts keep
  the per-gate attribution and may sum to more than the numerator.

Missing feature fields count as invalid assignments (fail-closed audit; the
proposed method rejects such inputs). The rate is guaranteed to lie in
``[0.0, 1.0]``; a zero denominator yields ``rate=None`` (nothing was at risk).
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Iterable, Mapping

from research_v2.evaluation.statistical_tests import wilson_ci

from .labels import STUDY_ID


def _as_bool(value: Any) -> bool:
    return value is True


def _case_features(row: Mapping[str, Any]) -> Mapping[str, Any]:
    return row.get("input") or {}


def invalid_generative_assignment_rate(rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Rate at which generative tasks were scheduled without prerequisites.

    Denominator: at-risk rows — rows with decision ``schedule_eligible`` on
    generative tasks (``task_type == "historical_explanation"``), i.e. rows
    where a generative task was assigned. Missing feature fields count as
    invalid assignments (fail-closed audit; the proposed method rejects such
    inputs).

    Numerator: at-risk rows violating the fact-stability gate or the source
    gate. Each row is counted at most once; a row failing BOTH gates adds 1,
    and its double failure is still visible in ``per_gate``.
    """
    total = 0
    invalid = 0
    per_gate = Counter[str]()
    for row in rows:
        decision = row.get("decision")
        features = _case_features(row)
        card = features.get("review_card") or {}
        is_generative = features.get("task_type") == "historical_explanation"
        if decision != "schedule_eligible" or not is_generative:
            continue
        total += 1
        fact_ok = _as_bool(features.get("fact_prerequisite_mastered"))
        src_ok = _as_bool(card.get("source_verified"))
        row_invalid = False
        if not fact_ok:
            per_gate["missing_fact_base"] += 1
            row_invalid = True
        if not src_ok:
            per_gate["absent_source"] += 1
            row_invalid = True
        if row_invalid:
            invalid += 1
    if invalid > total:  # defensive: cannot happen with the per-row boolean
        raise AssertionError(
            f"invalid_generative_assignment_rate: numerator {invalid} "
            f"exceeds denominator {total}"
        )
    rate = (invalid / total) if total else None
    if rate is not None:
        assert 0.0 <= rate <= 1.0, f"rate {rate} outside [0, 1]"
    ci_lo, ci_hi = wilson_ci(invalid, total) if total else (None, None)
    return {
        "study_id": STUDY_ID,
        "metric": "invalid_generative_assignment_rate",
        "numerator": invalid,
        "denominator": total,
        "rate": rate,
        "ci95": [ci_lo, ci_hi],
        "per_gate": dict(per_gate),
        "unit": "rate_per_eligible_generative_schedule",
    }


def decision_distribution(rows: Iterable[Mapping[str, Any]]) -> dict[str, int]:
    return dict(Counter(str(r.get("decision")) for r in rows))


def summarize(rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    rows = list(rows)
    return {
        "study_id": STUDY_ID,
        "n_cases": len(rows),
        "decisions": decision_distribution(rows),
        "invalid_generative_assignment": invalid_generative_assignment_rate(rows),
    }
