"""LN-08 study-specific metrics (secondary observables + error axes).

The shared evaluator (``research_v2.evaluation.metrics``) computes the paired
decision accuracy with exact numerators/denominators and CIs. This module adds
the LN-08 secondary metrics required by the spec (17/18_PRIMARY_METRIC):

- false-acceptance-of-negation rate (contradiction gold -> feedback_supported)
- false-acceptance-of-source-error rate (source-error gold -> feedback_supported)
- false-rejection rate of synonym-equivalent answers (preserve_semantics gold
  -> feedback_incomplete) - false acceptance must never be reported in
  isolation from false rejection (spec 17.C.4)
- abstain rate with the abstention-coverage view

All functions operate on prediction + gold rows (oracle material
evaluator-side only) and report exact numerators/denominators. Gold decisions
here are CONTRACT labels (the runner maps native ``abstain`` ->
``abstain_insufficient_data`` upstream of the evaluator).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

STUDY_ID = "LN-08"

SUPPORT_LABEL = "feedback_supported"
CONTRADICTION_LABEL = "classify_contradiction"
SOURCE_ERROR_LABEL = "classify_source_error"
INCOMPLETE_LABEL = "feedback_incomplete"
SEMANTICS_LABEL = "preserve_semantics"
ABSTAIN_LABEL = "abstain_insufficient_data"


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with Path(path).open(encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _rate(preds: list[Mapping[str, Any]], golds: Mapping[str, str], gold_label: str,
          pred_label: str) -> dict[str, Any]:
    """Exact numerator/denominator rate of gold_label predicted as pred_label."""
    denom = sum(1 for g in golds.values() if g == gold_label)
    numer = sum(
        1
        for row in preds
        if golds.get(row["case_id"]) == gold_label and row.get("decision") == pred_label
    )
    return {"numerator": numer, "denominator": denom, "rate": (numer / denom) if denom else None}


def false_negation_acceptance_rate(
    preds: list[Mapping[str, Any]], golds: Mapping[str, str]
) -> dict[str, Any]:
    """Rate of contradiction gold answers accepted as supported."""
    return _rate(preds, golds, CONTRADICTION_LABEL, SUPPORT_LABEL)


def false_source_error_acceptance_rate(
    preds: list[Mapping[str, Any]], golds: Mapping[str, str]
) -> dict[str, Any]:
    """Rate of source-error gold answers accepted as supported."""
    return _rate(preds, golds, SOURCE_ERROR_LABEL, SUPPORT_LABEL)


def synonym_false_rejection_rate(
    preds: list[Mapping[str, Any]], golds: Mapping[str, str]
) -> dict[str, Any]:
    """Rate of supported gold answers (canonical + synonym-equivalent strata,
    folded under the contract label ``feedback_supported``) wrongly scored
    ``feedback_incomplete``. This is the false-rejection axis: keyword-only
    comparators reject every synonym paraphrase for missing the exact keyword.
    """
    return _rate(preds, golds, SUPPORT_LABEL, INCOMPLETE_LABEL)


def abstain_rate(preds: list[Mapping[str, Any]], golds: Mapping[str, str]) -> dict[str, Any]:
    """Fraction of all gold cases answered with calibrated abstention."""
    denom = len(golds)
    numer = sum(1 for row in preds if row.get("decision") == ABSTAIN_LABEL)
    return {"numerator": numer, "denominator": denom, "rate": (numer / denom) if denom else None}


def error_axis_summary(
    preds: list[Mapping[str, Any]], golds: Mapping[str, str]
) -> dict[str, Any]:
    """Both error axes together: false acceptance AND false rejection."""
    return {
        "false_negation_acceptance": false_negation_acceptance_rate(preds, golds),
        "false_source_error_acceptance": false_source_error_acceptance_rate(preds, golds),
        "synonym_false_rejection": synonym_false_rejection_rate(preds, golds),
        "abstain": abstain_rate(preds, golds),
    }
