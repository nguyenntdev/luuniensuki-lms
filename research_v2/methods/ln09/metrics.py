"""LN-09 study-specific metrics.

Primary metric (spec 17): actionable recommendation precision at fixed teacher
review capacity on independently reviewed cases — realized on the frozen T3
holdout as exact-match decision validity (the fraction of cases where the
method's decision equals the sealed gold decision), with false-accept and
false-reject rates reported separately so neither can be hidden by the
aggregate. The gold vocabulary is the legacy engine's DecisionCode space;
predictions are emitted in the same vocabulary so the evaluator scores them
verbatim (documented divergence from ``label_space.LN09_DECISIONS``).

Label-space bridge (evaluator-side only, never in model input):
    legacy gold label                      -> V2 contract label
    propose_explained_action               -> recommend_action
    abstain_missing_evidence               -> abstain_insufficient_data
    abstain_conflict                       -> require_teacher_override
    abstain_unverified_source              -> require_teacher_override
    request_refresh                        -> abstain_insufficient_data
    descriptive_summary_only               -> descriptive_only

Confidence intervals reuse ``research_v2.evaluation.statistical_tests``
(Wilson and Clopper-Pearson) — no local reimplementation.
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Mapping, Sequence

from research_v2.evaluation.statistical_tests import clopper_pearson_ci, wilson_ci

# False-accept / false-reject classification against the 6-label gold space.
# Accept = the method proposed an actionable intervention.
# Reject = every explicit abstention / refresh / descriptive outcome.
ACCEPT_DECISIONS = frozenset({"propose_explained_action"})
REJECT_DECISIONS = frozenset(
    {
        "abstain_missing_evidence",
        "abstain_conflict",
        "abstain_unverified_source",
        "request_refresh",
        "descriptive_summary_only",
    }
)

# Deterministic gold->V2 vocabulary bridge (documented divergence bridge).
GOLD_TO_V2_LABEL: Mapping[str, str] = {
    "propose_explained_action": "recommend_action",
    "abstain_missing_evidence": "abstain_insufficient_data",
    "abstain_conflict": "require_teacher_override",
    "abstain_unverified_source": "require_teacher_override",
    "request_refresh": "abstain_insufficient_data",
    "descriptive_summary_only": "descriptive_only",
}

V2_DECISIONS: tuple[str, ...] = (
    "recommend_action",
    "descriptive_only",
    "abstain_insufficient_data",
    "require_teacher_override",
)


def to_v2_label(gold_or_pred: str) -> str:
    """Map a legacy-vocabulary label into the V2 contract label space.

    Unknown labels raise ``ValueError`` (never a silent guessed fallback).
    """
    try:
        return GOLD_TO_V2_LABEL[gold_or_pred]
    except KeyError as exc:
        raise ValueError(f"unknown LN-09 decision label: {gold_or_pred!r}") from exc


def _rate(successes: int, n: int) -> float | None:
    return (successes / n) if n else None


def actionable_recommendation_precision(
    decisions: Sequence[str], gold: Sequence[str]
) -> dict[str, Any]:
    """Primary metric: exact numerator/denominator + Wilson/CP CIs.

    Also reports directional error rates:
      - false_accept_rate: proposed actions on cases whose gold decision is an
        abstention/refresh/descriptive outcome (includes the mandatory
        high-risk-no-evidence deficit-inference violation)
      - false_reject_rate: abstained on cases whose gold decision is an
        actionable proposal
    """
    if len(decisions) != len(gold):
        raise ValueError("decisions and gold must align pairwise")
    n = len(gold)
    if n == 0:
        return {
            "metric": "actionable_recommendation_precision",
            "n_total": 0,
            "n_valid": 0,
            "value": None,
            "wilson_ci_95": [None, None],
            "clopper_pearson_ci_95": [None, None],
            "false_accept_rate": None,
            "false_reject_rate": None,
            "evidence_sufficient": False,
        }
    for label in (*decisions, *gold):
        if label not in GOLD_TO_V2_LABEL:
            raise ValueError(f"unknown LN-09 decision label: {label!r}")
    valid = sum(1 for d, g in zip(decisions, gold) if d == g)
    false_accepts = sum(
        1 for d, g in zip(decisions, gold) if d in ACCEPT_DECISIONS and g in REJECT_DECISIONS
    )
    false_rejects = sum(
        1 for d, g in zip(decisions, gold) if d in REJECT_DECISIONS and g in ACCEPT_DECISIONS
    )
    n_gold_accept = sum(1 for g in gold if g in ACCEPT_DECISIONS)
    n_gold_reject = n - n_gold_accept
    return {
        "metric": "actionable_recommendation_precision",
        "n_total": n,
        "n_valid": valid,
        "value": _rate(valid, n),
        "wilson_ci_95": wilson_ci(valid, n),
        "clopper_pearson_ci_95": clopper_pearson_ci(valid, n),
        "false_accept_rate": _rate(false_accepts, n_gold_reject),
        "false_reject_rate": _rate(false_rejects, n_gold_accept),
        "n_gold_accept": n_gold_accept,
        "n_gold_reject": n_gold_reject,
        # Evidence gate: with fewer than 5 paired cases, mark insufficient
        # rather than publishing a CI that overstates precision.
        "evidence_sufficient": n >= 5,
    }


def direction_aware_error_rate(
    decisions: Sequence[str], gold: Sequence[str]
) -> dict[str, Any]:
    """Separate false-accept vs false-reject confusion (never merged into one reject bin)."""
    if len(decisions) != len(gold):
        raise ValueError("decisions and gold must align pairwise")
    confusion: dict[str, int] = {}
    for d, g in zip(decisions, gold):
        key = f"{g}->{d}"
        confusion[key] = confusion.get(key, 0) + 1
    return {"confusion_counts": confusion}


def k_anonymity_suppression_rate(decisions: Sequence[str]) -> dict[str, Any]:
    """Share of decisions suppressed to descriptive-only (privacy gate active)."""
    n = len(decisions)
    suppressed = sum(1 for d in decisions if d == "descriptive_summary_only")
    return {
        "metric": "k_anonymity_suppression_rate",
        "n_total": n,
        "n_suppressed": suppressed,
        "value": _rate(suppressed, n),
    }


def evaluate_predictions_file(
    predictions_path: Path | str, gold_path: Path | str
) -> dict[str, Any]:
    """Compute LN-09 metrics from a predictions.jsonl + gold jsonl pair.

    Purely evaluator-side: reads gold, never writes it back into predictions.
    """
    import json

    preds = [
        json.loads(line)
        for line in Path(predictions_path).open(encoding="utf-8")
        if line.strip()
    ]
    golds = [
        json.loads(line) for line in Path(gold_path).open(encoding="utf-8") if line.strip()
    ]
    gold_by_case = {row["case_id"]: row.get("expected_decision") for row in golds}
    paired_pred: list[str] = []
    paired_gold: list[str] = []
    missing = []
    for row in preds:
        cid = row["case_id"]
        if cid not in gold_by_case:
            missing.append(cid)
            continue
        paired_pred.append(str(row.get("decision")))
        paired_gold.append(str(gold_by_case[cid]))
    if missing:
        raise ValueError(f"predictions reference unknown gold cases: {sorted(missing)[:5]}")
    if len(paired_pred) != len(gold_by_case):
        raise ValueError(
            f"paired denominator mismatch: {len(paired_pred)} predictions vs {len(gold_by_case)} gold rows"
        )
    result = actionable_recommendation_precision(paired_pred, paired_gold)
    result["direction_aware"] = direction_aware_error_rate(paired_pred, paired_gold)
    result["k_anonymity_suppression"] = k_anonymity_suppression_rate(paired_pred)
    return result


def finite_json_safe(result: Mapping[str, Any]) -> bool:
    """Assert every float in a metrics result is finite (strict-JSON rule)."""

    def walk(obj: Any) -> bool:
        if isinstance(obj, float):
            return math.isfinite(obj)
        if isinstance(obj, dict):
            return all(walk(v) for v in obj.values())
        if isinstance(obj, (list, tuple)):
            return all(walk(v) for v in obj)
        return True

    return walk(dict(result))
