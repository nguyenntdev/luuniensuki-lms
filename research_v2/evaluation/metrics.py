"""Metric computation from saved predictions plus access-controlled gold.

Gold labels are read only by the evaluator, after predictions are persisted.
Predictions never contain gold material, so any leakage must fail here.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

from ..contracts.canonical_hash import canonical_json, sha256_bytes
from .statistical_tests import clopper_pearson_ci, wilson_ci

FORBIDDEN_GOLD_IN_PREDICTION = frozenset(
    {
        "oracle",
        "expected_decision",
        "expected_category",
        "fault_id",
        "gold_label",
        "gold",
        "label",
        "labels",
        "cohort",
        "expected_outcome",
        "expected_conclusion",
        "oracle_basis",
        "annotation_provenance",
        "synthetic_annotation_template",
        "external_expert_annotation",
        "correct",
        "is_correct",
    }
)


class EvaluationError(ValueError):
    pass


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for lineno, line in enumerate(Path(path).open(encoding="utf-8"), 1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise EvaluationError(f"{path}:{lineno}: invalid JSON: {exc}") from exc
    return rows


def _gold_label(gold_row: Mapping[str, Any]) -> str:
    oracle = gold_row.get("oracle") or {}
    label = gold_row.get("expected_decision") or oracle.get("expected_decision")
    if not label:
        raise EvaluationError(f"gold row {gold_row.get('case_id')!r} has no expected decision")
    return str(label)


def _pred_label(pred_row: Mapping[str, Any]) -> str:
    label = pred_row.get("decision")
    if not label:
        raise EvaluationError(f"prediction {pred_row.get('case_id')!r} has no decision")
    return str(label)


def _iter_keys(value: Any) -> Any:
    """Yield every dict key found anywhere inside a JSON-like structure."""
    if isinstance(value, Mapping):
        for key, child in value.items():
            yield key
            yield from _iter_keys(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            yield from _iter_keys(child)


def _assert_no_gold_material(row: Mapping[str, Any]) -> None:
    """Reject any row that carries gold material at any nesting depth."""
    leaked = sorted({str(k) for k in _iter_keys(row) if str(k) in FORBIDDEN_GOLD_IN_PREDICTION})
    if leaked:
        raise EvaluationError(
            f"prediction row {row.get('case_id')!r} contains gold material {leaked}; "
            "predictions must be oracle-free"
        )


def _unique_case_ids(rows: list[dict[str, Any]], source: str) -> set[str]:
    """Return case_id set, failing closed on missing or duplicated identifiers."""
    ids: set[str] = set()
    duplicates: Counter[str] = Counter()
    for row in rows:
        case_id = row.get("case_id")
        if case_id is None:
            raise EvaluationError(f"{source} row is missing 'case_id'")
        key = str(case_id)
        duplicates[key] += 1
        ids.add(key)
    repeated = sorted(k for k, n in duplicates.items() if n > 1)
    if repeated:
        raise EvaluationError(
            f"duplicate case_id in {source}: {len(repeated)} duplicated, e.g. {repeated[:5]}"
        )
    return ids


def compute_metrics(
    predictions: Path,
    eval_gold: Path,
    metrics_plan: Path | None = None,
    label_map: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Compute classification metrics with exact numerator/denominator and CIs.

    ``label_map`` applies an evaluator-side equivalence mapping from a
    prediction's vocabulary to the sealed gold vocabulary (e.g. a study's
    native contract label -> legacy gold label). ``None`` means exact match.

    Also detects any gold material smuggled into the prediction file (a
    scientific-integrity violation, not merely a bug), duplicate case
    identifiers on either side, and one-to-one coverage between predictions
    and gold (missing predictions AND extra predictions both fail).
    """
    preds = _load_jsonl(Path(predictions))
    golds = _load_jsonl(Path(eval_gold))
    label_map = dict(label_map or {})

    for row in preds:
        _assert_no_gold_material(row)

    pred_ids = _unique_case_ids(preds, "predictions")
    gold_ids = _unique_case_ids(golds, "gold")

    missing = sorted(gold_ids - pred_ids)
    if missing:
        raise EvaluationError(f"missing predictions for {len(missing)} gold cases, e.g. {missing[:5]}")
    extra = sorted(pred_ids - gold_ids)
    if extra:
        raise EvaluationError(
            f"extra predictions for {len(extra)} cases absent from gold, e.g. {extra[:5]}"
        )

    correct = 0
    total = 0
    errors = 0
    per_class_total: Counter[str] = Counter()
    per_class_correct: Counter[str] = Counter()
    confusion: Counter[tuple[str, str]] = Counter()
    case_results: list[dict[str, Any]] = []

    pred_by_case = {str(row["case_id"]): row for row in preds}
    gold_by_case = {str(row["case_id"]): row for row in golds}

    for case_id, gold_row in gold_by_case.items():
        pred_row = pred_by_case[case_id]
        gold_label = _gold_label(gold_row)
        pred_label = _pred_label(pred_row)
        pred_label_mapped = label_map.get(pred_label, pred_label)
        total += 1
        per_class_total[gold_label] += 1
        confusion[(gold_label, pred_label_mapped)] += 1
        ok = gold_label == pred_label_mapped
        if ok:
            correct += 1
            per_class_correct[gold_label] += 1
        else:
            errors += 1
        case_results.append(
            {
                "case_id": case_id,
                "group_id": pred_row.get("group_id", gold_row.get("group_id", "unknown")),
                "gold": gold_label,
                "pred": pred_label,
                "pred_mapped": pred_label_mapped,
                "correct": ok,
            }
        )

    accuracy = correct / total if total else None
    error_rate = errors / total if total else None
    result: dict[str, Any] = {
        "n_total": total,
        "n_correct": correct,
        "n_errors": errors,
        "accuracy": accuracy,
        "error_rate": error_rate,
        "accuracy_wilson_ci_95": wilson_ci(correct, total),
        "accuracy_clopper_pearson_ci_95": clopper_pearson_ci(correct, total),
        "error_rate_wilson_ci_95": wilson_ci(errors, total),
        "error_rate_clopper_pearson_ci_95": clopper_pearson_ci(errors, total),
        "per_class": {
            label: {
                "n": per_class_total[label],
                "correct": per_class_correct[label],
                "accuracy": (per_class_correct[label] / per_class_total[label]) if per_class_total[label] else None,
            }
            for label in sorted(per_class_total)
        },
        "confusion": {
            f"{gold}->{pred}": count
            for (gold, pred), count in sorted(confusion.items())
        },
        "predictions_sha256": sha256_bytes(canonical_json(preds)),
        "gold_sha256": sha256_bytes(canonical_json(golds)),
        "label_map": label_map,
        "cases": case_results,
    }
    if metrics_plan is not None and Path(metrics_plan).is_file():
        result["metrics_plan_sha256"] = sha256_bytes(Path(metrics_plan).read_bytes())
    return result
