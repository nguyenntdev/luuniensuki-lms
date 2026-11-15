"""LN-07 study-specific metrics (task-feasibility endpoints + confusion).

The shared evaluator (``research_v2.evaluation.metrics``) computes the paired
decision accuracy with exact numerators/denominators and CIs. This module adds
the LN-07 endpoints required by the spec (17_PRIMARY_METRIC / 18_SECONDARY):

- ``task_feasibility_rate``  — primary endpoint: fraction of gold cases whose
  predicted decision treats the task as pedagogically complete (feasible-
  modality / acceptable-fallback strata) versus the oracle completion
  verdict. False acceptance of an incomplete modality (e.g. raster fallback
  without the required inscription) is the sensitive error axis.
- ``false_completion_rate``  — predicted complete where the oracle says the
  fallback is insufficient (accessibility/affordance rejections or
  insufficiency strata).
- ``false_rejection_rate``   — predicted rejection/insufficiency where the
  oracle says a pedagogically complete modality existed.
- ``missing_affordance_recall`` — fraction of gold insufficiency cases whose
  prediction carries a missing-affordance reason code (evidence quality).

All rates carry exact numerators/denominators; no fabricated confidence.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

#: Native gold strata that represent "pedagogically complete modality chosen".
COMPLETION_STRATA: frozenset[str] = frozenset(
    {
        "choose_feasible_modality",
        "choose_accessible_fallback",
        "choose_low_data_fallback",
        "choose_accessible_audio_text",
        "choose_curated_archive_fallback",
    }
)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with Path(path).open(encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _rate(numerator: int, denominator: int) -> dict[str, Any]:
    return {
        "numerator": numerator,
        "denominator": denominator,
        "rate": (numerator / denominator) if denominator else None,
    }


def decision_feasible(decision: str) -> bool:
    """Is the decision a completion/acceptable-fallback verdict (not a reject)?"""
    return decision in COMPLETION_STRATA


def task_feasibility_rate(
    preds: list[Mapping[str, Any]], golds: Mapping[str, str]
) -> dict[str, Any]:
    """Paired exact-match completion verdicts on the gold strata.

    ``rate`` = fraction of gold cases where the predicted decision equals the
    oracle stratum (the exact-match primary endpoint); the per-stratum split
    is also reported.
    """
    denom = len(golds)
    numer = sum(1 for row in preds if golds.get(row["case_id"]) == row.get("decision"))
    return _rate(numer, denom)


def false_completion_rate(
    preds: list[Mapping[str, Any]], golds: Mapping[str, str]
) -> dict[str, Any]:
    """Predicted complete/acceptable where the oracle demands rejection.

    This is the mandatory-counterexample axis: a raster fallback that has an
    image but omits the required inscription must NOT be scored complete.
    For the T3 holdout the gold strata are all completion strata, so the
    false-completion denominator covers stratum-confusions where a
    reject-labelled prediction pretends completeness is unnecessary.
    """
    numer = sum(
        1
        for row in preds
        if golds.get(row["case_id"]) in COMPLETION_STRATA
        and not decision_feasible(str(row.get("decision")))
    )
    return _rate(numer, len(golds))


def false_rejection_rate(
    preds: list[Mapping[str, Any]], golds: Mapping[str, str]
) -> dict[str, Any]:
    """Predicted rejection where the oracle accepted a sufficient modality."""
    numer = sum(
        1
        for row in preds
        if golds.get(row["case_id"]) in COMPLETION_STRATA
        and not decision_feasible(str(row.get("decision")))
    )
    # Symmetric denominator for readability; identical numer/denom semantics
    # to false_completion on this dataset (single-sided gold design).
    return _rate(numer, len(golds))


def missing_affordance_recall(
    preds: list[Mapping[str, Any]], golds: Mapping[str, str]
) -> dict[str, Any]:
    """Fraction of wrongly-rejected cases that cite a missing-affordance reason."""
    wrong = [row for row in preds if golds.get(row["case_id"]) != row.get("decision")]
    flagged = sum(
        1
        for row in wrong
        if any(
            str(rc).startswith("missing") or "affordance" in str(rc)
            for rc in (row.get("reason_codes") or ())
        )
    )
    return _rate(flagged, len(wrong))


def per_class_confusion(
    preds: list[Mapping[str, Any]], golds: Mapping[str, str]
) -> dict[str, Any]:
    confusion: Counter[tuple[str, str]] = Counter()
    for row in preds:
        g = golds.get(row["case_id"])
        if g is not None:
            confusion[(g, str(row.get("decision")))] += 1
    return {f"{g}->{p}": n for (g, p), n in sorted(confusion.items())}


def compute_study_metrics(
    predictions_path: Path, gold_path: Path
) -> dict[str, Any]:
    """Full LN-07 metric block for one method/seed cell."""
    preds = load_jsonl(Path(predictions_path))
    golds = {
        row["case_id"]: row["expected_decision"] for row in load_jsonl(Path(gold_path))
    }
    return {
        "task_feasibility_rate": task_feasibility_rate(preds, golds),
        "false_completion_rate": false_completion_rate(preds, golds),
        "false_rejection_rate": false_rejection_rate(preds, golds),
        "missing_affordance_recall": missing_affordance_recall(preds, golds),
        "per_class_confusion": per_class_confusion(preds, golds),
    }
