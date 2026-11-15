"""LN-10 study-specific metrics (evaluator-side diagnostics).

The sealed evaluation path (``research_v2.evaluation.metrics.compute_metrics``)
remains the authoritative metric source for matrix runs. This module adds the
LN-10 secondary metrics required by the spec (17_PRIMARY_METRIC /
18_SECONDARY_METRICS):

- primary endpoint: valid-state transition acceptance at bounded
  invalid-transition risk — operationalised as paired exact-match decision
  accuracy with the false-acceptance / false-rejection split.
- false_acceptance_rate: gold rejections/conflicts/postponements predicted
  ``allow_authorized_transition`` (the dangerous direction; bounded risk).
- false_rejection_rate: gold ``allow_authorized_transition`` predicted as any
  gate family (learner-burden direction; a dummy refusal cannot win because
  this axis is reported alongside).
- conflict_detection_rate: gold ``resolve_revision_conflict`` cases where the
  method emitted ``resolve_revision_conflict`` (the mandatory mechanism).
- reflection_gate_enforcement_rate: gold ``reject_premature_submit`` cases
  where the method emitted ``reject_premature_submit``.

All functions operate on prediction + gold rows (oracle material evaluator-side
only) and report exact numerators/denominators. If the primary metric cannot
be computed for lack of observations the caller must mark the release gate
``EVIDENCE_INSUFFICIENT`` (denominator zero is reported, never guessed).
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Iterable, Mapping

from .labels import STUDY_ID

ACCEPT_LABEL = "allow_authorized_transition"
CONFLICT_LABEL = "resolve_revision_conflict"
PREMATURE_SUBMIT_LABEL = "reject_premature_submit"


def _rate(numer: int, denom: int) -> float | None:
    return (numer / denom) if denom else None


def false_acceptance_rate(
    preds: Iterable[Mapping[str, Any]], golds: Mapping[str, str]
) -> dict[str, Any]:
    """Rate of gold gate labels predicted as a silent/unsafe accept."""
    preds = list(preds)
    pred_by_case = {row["case_id"]: row for row in preds}
    numer = 0
    denom = 0
    per_gold: Counter[str] = Counter()
    for case_id, gold in golds.items():
        pred = pred_by_case.get(case_id)
        if pred is None:
            continue
        if gold == ACCEPT_LABEL:
            continue
        denom += 1
        if pred.get("decision") == ACCEPT_LABEL:
            numer += 1
            per_gold[gold] += 1
    return {
        "study_id": STUDY_ID,
        "metric": "false_acceptance_rate",
        "numerator": numer,
        "denominator": denom,
        "rate": _rate(numer, denom),
        "per_gold_label": dict(per_gold),
        "unit": "rate_per_gold_gate_case",
    }


def false_rejection_rate(
    preds: Iterable[Mapping[str, Any]], golds: Mapping[str, str]
) -> dict[str, Any]:
    """Rate of gold nominal transitions blocked by any gate (learner burden)."""
    preds = list(preds)
    pred_by_case = {row["case_id"]: row for row in preds}
    numer = 0
    denom = 0
    per_pred: Counter[str] = Counter()
    for case_id, gold in golds.items():
        pred = pred_by_case.get(case_id)
        if pred is None:
            continue
        if gold != ACCEPT_LABEL:
            continue
        denom += 1
        decision = pred.get("decision")
        if decision != ACCEPT_LABEL:
            numer += 1
            per_pred[str(decision)] += 1
    return {
        "study_id": STUDY_ID,
        "metric": "false_rejection_rate",
        "numerator": numer,
        "denominator": denom,
        "rate": _rate(numer, denom),
        "per_predicted_label": dict(per_pred),
        "unit": "rate_per_gold_nominal_case",
    }


def conflict_detection_rate(
    preds: Iterable[Mapping[str, Any]], golds: Mapping[str, str]
) -> dict[str, Any]:
    """Rate of gold conflict cases detected as ``resolve_revision_conflict``.

    This is the sensitivity metric for the mandatory mechanism: two
    conflicting offline edits to the same version must be detected, never
    silently applied.
    """
    preds = list(preds)
    pred_by_case = {row["case_id"]: row for row in preds}
    numer = 0
    denom = sum(1 for g in golds.values() if g == CONFLICT_LABEL)
    for case_id, gold in golds.items():
        pred = pred_by_case.get(case_id)
        if pred is None or gold != CONFLICT_LABEL:
            continue
        if pred.get("decision") == CONFLICT_LABEL:
            numer += 1
    return {
        "study_id": STUDY_ID,
        "metric": "conflict_detection_rate",
        "numerator": numer,
        "denominator": denom,
        "rate": _rate(numer, denom),
        "unit": "rate_per_gold_conflict_case",
    }


def reflection_gate_enforcement_rate(
    preds: Iterable[Mapping[str, Any]], golds: Mapping[str, str]
) -> dict[str, Any]:
    """Rate of gold premature-submit cases gated by ``reject_premature_submit``."""
    preds = list(preds)
    pred_by_case = {row["case_id"]: row for row in preds}
    numer = 0
    denom = sum(1 for g in golds.values() if g == PREMATURE_SUBMIT_LABEL)
    for case_id, gold in golds.items():
        pred = pred_by_case.get(case_id)
        if pred is None or gold != PREMATURE_SUBMIT_LABEL:
            continue
        if pred.get("decision") == PREMATURE_SUBMIT_LABEL:
            numer += 1
    return {
        "study_id": STUDY_ID,
        "metric": "reflection_gate_enforcement_rate",
        "numerator": numer,
        "denominator": denom,
        "rate": _rate(numer, denom),
        "unit": "rate_per_gold_premature_submit_case",
    }


def decision_distribution(rows: Iterable[Mapping[str, Any]]) -> dict[str, int]:
    return dict(Counter(str(r.get("decision")) for r in rows))


def summarize(
    preds: Iterable[Mapping[str, Any]], golds: Mapping[str, str]
) -> dict[str, Any]:
    preds = list(preds)
    return {
        "study_id": STUDY_ID,
        "n_cases": len(preds),
        "decisions": decision_distribution(preds),
        "false_acceptance": false_acceptance_rate(preds, golds),
        "false_rejection": false_rejection_rate(preds, golds),
        "conflict_detection": conflict_detection_rate(preds, golds),
        "reflection_gate_enforcement": reflection_gate_enforcement_rate(preds, golds),
    }
