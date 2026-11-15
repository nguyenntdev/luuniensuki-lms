"""P01 evaluation metrics computed from Predictions + sealed gold.

All metrics are recomputable from saved prediction rows + gold rows (tested).
CIs reuse research_v3.eval.statistics (Wilson + Clopper-Pearson), paired tests
reuse research_v2.evaluation.statistical_tests via the same import path.
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence

from research_v3.eval.statistics import proportion_ci
from research_v2.evaluation.statistical_tests import mcnemar_exact

from .types import ABSTAIN, FAIL_LABEL, LABELS, P01ContractError


def _per_class_recall(pred: Sequence[str], gold: Sequence[str]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for lab in LABELS:
        idx = [i for i, g in enumerate(gold) if g == lab]
        correct = sum(1 for i in idx if pred[i] == lab)
        n = len(idx)
        entry: dict[str, Any] = {"n": n, "correct": correct}
        if n:
            entry["recall"] = correct / n
            entry.update(proportion_ci(correct, n))
        else:
            entry["recall"] = None
        out[lab] = entry
    return out


def macro_f1(pred: Sequence[str], gold: Sequence[str]) -> float | None:
    f1s: list[float] = []
    for lab in LABELS:
        tp = sum(1 for p, g in zip(pred, gold) if p == lab and g == lab)
        fp = sum(1 for p, g in zip(pred, gold) if p == lab and g != lab)
        fn = sum(1 for p, g in zip(pred, gold) if p != lab and g == lab)
        denom = 2 * tp + fp + fn
        if denom == 0:
            continue
        f1s.append(2 * tp / denom)
    return sum(f1s) / len(f1s) if f1s else None


def compute_classification_metrics(
    pred_rows: Sequence[Mapping[str, Any]],
    gold_rows: Sequence[Mapping[str, Any]],
    *,
    model_id: str,
) -> dict[str, Any]:
    """Accuracy + macro-F1 + per-class recall + coverage, fail-closed on coverage."""
    gold_by_case = {str(r["case_id"]): str(r["label"]) for r in gold_rows}
    pred_by_case = {str(r["case_id"]): r for r in pred_rows}
    if len(pred_by_case) != len(pred_rows):
        raise P01ContractError(f"{model_id}: duplicate case_id in predictions")
    missing = sorted(set(gold_by_case) - set(pred_by_case))
    extra = sorted(set(pred_by_case) - set(gold_by_case))
    if missing or extra:
        raise P01ContractError(
            f"{model_id}: prediction/gold mismatch: missing={missing[:5]} extra={extra[:5]}"
        )
    cases = sorted(gold_by_case)
    pred = [str(pred_by_case[c]["decision"]) for c in cases]
    gold = [gold_by_case[c] for c in cases]
    n = len(cases)
    correct = sum(1 for p, g in zip(pred, gold) if p == g)
    abstained = sum(1 for p in pred if p == ABSTAIN)
    metrics: dict[str, Any] = {
        "model_id": model_id,
        "n": n,
        "n_correct": correct,
        "accuracy": correct / n,
        **proportion_ci(correct, n),
        "macro_f1": macro_f1(pred, gold),
        "per_class_recall": _per_class_recall(pred, gold),
        "coverage": (n - abstained) / n,
        "n_abstained": abstained,
        "confusion": {
            f"{g}->{p}": sum(1 for pp, gg in zip(pred, gold) if gg == g and pp == p)
            for g in LABELS
            for p in LABELS + (ABSTAIN,)
            if sum(1 for pp, gg in zip(pred, gold) if gg == g and pp == p) > 0
        },
    }
    return metrics


def paired_mcnemar(
    pred_a: Sequence[Mapping[str, Any]],
    pred_b: Sequence[Mapping[str, Any]],
    gold_rows: Sequence[Mapping[str, Any]],
    *,
    label_a: str,
    label_b: str,
) -> dict[str, Any]:
    """Exact McNemar between two models over identical, fully covered case sets."""
    gold_by_case = {str(r["case_id"]): str(r["label"]) for r in gold_rows}
    a_by_case = {str(r["case_id"]): str(r["decision"]) for r in pred_a}
    b_by_case = {str(r["case_id"]): str(r["decision"]) for r in pred_b}
    if set(a_by_case) != set(b_by_case) or set(a_by_case) != set(gold_by_case):
        raise P01ContractError(
            f"{label_a} vs {label_b}: paired test requires identical case coverage"
        )
    cases = sorted(gold_by_case)
    a_correct = [a_by_case[c] == gold_by_case[c] for c in cases]
    b_correct = [b_by_case[c] == gold_by_case[c] for c in cases]
    result = mcnemar_exact(a_correct, b_correct)
    return {
        "a": label_a,
        "b": label_b,
        "n": len(cases),
        "a_accuracy": sum(a_correct) / len(cases),
        "b_accuracy": sum(b_correct) / len(cases),
        **result,
    }


def fail_false_alarm_rate(
    pred_rows: Sequence[Mapping[str, Any]],
    gold_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Empirical false-alarm rate of the Fail re-route among non-Fail gold rows."""
    gold_by_case = {str(r["case_id"]): str(r["label"]) for r in gold_rows}
    nonfail = [r for r in pred_rows if gold_by_case[str(r["case_id"])] != FAIL_LABEL]
    alarms = sum(1 for r in nonfail if str(r["decision"]) == FAIL_LABEL)
    n = len(nonfail)
    out: dict[str, Any] = {"n_nonfail": n, "n_fail_alarms": alarms}
    if n:
        out["rate"] = alarms / n
        out.update(proportion_ci(alarms, n))
    return out
