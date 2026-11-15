"""LN-02 study-local metric helpers (pure functions over predictions).

The canonical evaluation path is ``research_v2.evaluation.metrics.compute_metrics``
(accuracy + confusion + CIs, sealed gold). This module adds the study-specific
diagnostics required by spec sections 14.M/17:

- **conditional recommendation utility**: among cases the policy does *not*
  refuse (not reject/abstain), the fraction of eligible recommendations that
  are true eligibilities - the "utility subject to prerequisite safety"
  endpoint;
- **prerequisite safety (false-eligible rate)**: among prerequisite-violating
  cases, the fraction the policy wrongly recommends - the mandatory safety
  denominator for the conditional utility endpoint;
- **abstention coverage**: fraction of unobserved-evidence cases answered
  with the calibrated abstain label rather than a forced guess.

All functions operate on plain (prediction, gold) label pairs; they never
touch oracle material and contain no hardcoded expected decisions.
"""
from __future__ import annotations

from collections import Counter
from typing import Sequence

REFUSE_LABELS = frozenset({"reject_cycle", "reject_invalid_score", "abstain_insufficient_data"})
VIOLATION_GOLD_LABELS = frozenset({"remediate_first", "reject_cycle", "reject_invalid_score"})
UNOBSERVED_EVIDENCE_LABEL = "abstain_insufficient_data"


def conditional_recommendation_utility(
    pred_labels: Sequence[str], gold_labels: Sequence[str]
) -> dict[str, float | int | None]:
    """Eligibility precision among non-refused cases + safety denominator."""
    if len(pred_labels) != len(gold_labels):
        raise ValueError("pred/gold label sequences must have equal length")
    non_refused = 0
    true_eligible = 0
    for pred, gold in zip(pred_labels, gold_labels):
        if pred in REFUSE_LABELS:
            continue
        non_refused += 1
        if pred == "recommend_eligible" and gold == "recommend_eligible":
            true_eligible += 1
    return {
        "n_non_refused": non_refused,
        "n_true_eligible": true_eligible,
        "conditional_utility": (true_eligible / non_refused) if non_refused else None,
    }


def prerequisite_safety(
    pred_labels: Sequence[str], gold_labels: Sequence[str]
) -> dict[str, float | int | None]:
    """False-eligible rate among prerequisite-violating cases (must be 0)."""
    if len(pred_labels) != len(gold_labels):
        raise ValueError("pred/gold label sequences must have equal length")
    violating = 0
    false_eligible = 0
    for pred, gold in zip(pred_labels, gold_labels):
        if gold in VIOLATION_GOLD_LABELS:
            violating += 1
            if pred == "recommend_eligible":
                false_eligible += 1
    return {
        "n_violating": violating,
        "n_false_eligible": false_eligible,
        "false_eligible_rate": (false_eligible / violating) if violating else None,
        "safe": false_eligible == 0,
    }


def abstention_coverage(
    pred_labels: Sequence[str], gold_labels: Sequence[str]
) -> dict[str, float | int | None]:
    """Fraction of unobserved-evidence gold cases answered with abstain."""
    if len(pred_labels) != len(gold_labels):
        raise ValueError("pred/gold label sequences must have equal length")
    unobserved = sum(1 for gold in gold_labels if gold == UNOBSERVED_EVIDENCE_LABEL)
    abstained = sum(
        1
        for pred, gold in zip(pred_labels, gold_labels)
        if gold == UNOBSERVED_EVIDENCE_LABEL and pred == UNOBSERVED_EVIDENCE_LABEL
    )
    return {
        "n_unobserved": unobserved,
        "n_abstained": abstained,
        "coverage": (abstained / unobserved) if unobserved else None,
    }


def label_histogram(labels: Sequence[str]) -> dict[str, int]:
    return dict(sorted(Counter(labels).items()))


def summarize(
    pred_labels: Sequence[str], gold_labels: Sequence[str]
) -> dict[str, object]:
    """Bundle of all LN-02 study diagnostics for one method run."""
    n = len(pred_labels)
    if n != len(gold_labels):
        raise ValueError("pred/gold label sequences must have equal length")
    correct = sum(1 for p, g in zip(pred_labels, gold_labels) if p == g)
    summary: dict[str, object] = {
        "n_cases": n,
        "n_correct": correct,
        "accuracy": (correct / n) if n else None,
        "pred_histogram": label_histogram(pred_labels),
        "gold_histogram": label_histogram(gold_labels),
        "conditional_recommendation_utility": conditional_recommendation_utility(
            pred_labels, gold_labels
        ),
        "prerequisite_safety": prerequisite_safety(pred_labels, gold_labels),
        "abstention_coverage": abstention_coverage(pred_labels, gold_labels),
    }
    return summary


__all__ = [
    "REFUSE_LABELS",
    "VIOLATION_GOLD_LABELS",
    "UNOBSERVED_EVIDENCE_LABEL",
    "abstention_coverage",
    "conditional_recommendation_utility",
    "label_histogram",
    "prerequisite_safety",
    "summarize",
]
