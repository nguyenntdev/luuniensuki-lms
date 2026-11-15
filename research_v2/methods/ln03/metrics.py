"""LN-03 study-local metrics (evaluator-side diagnostics).

The sealed evaluation path (``research_v2.evaluation.metrics.compute_metrics``)
remains the authoritative metric source for matrix runs. This module provides
study-specific diagnostics over saved prediction rows:

- ``invalid_generative_assignment_rate`` (primary-metric counterpart): fraction
  of cases where a generative explanation was scheduled without a stable fact
  base or a verified source.
- mode/decision distribution and gate-level audit counts.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Iterable, Mapping

from .labels import STUDY_ID


def _as_bool(value: Any) -> bool:
    return value is True


def _case_features(row: Mapping[str, Any]) -> Mapping[str, Any]:
    return row.get("input") or {}


def invalid_generative_assignment_rate(rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Rate at which generative tasks were scheduled without prerequisites.

    Numerator: decisions of ``schedule_eligible`` on generative tasks where the
    fact base was unstable/absent or the source unverified at inference time.
    Denominator: all evaluated rows. Missing feature fields count as invalid
    assignments (fail-closed audit; the proposed method rejects such inputs).
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
        if not fact_ok:
            invalid += 1
            per_gate["missing_fact_base"] += 1
        if not src_ok:
            invalid += 1
            per_gate["absent_source"] += 1
    denominator = max(total, 1)
    return {
        "study_id": STUDY_ID,
        "metric": "invalid_generative_assignment_rate",
        "numerator": invalid,
        "denominator": total,
        "rate": invalid / denominator if total else None,
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
