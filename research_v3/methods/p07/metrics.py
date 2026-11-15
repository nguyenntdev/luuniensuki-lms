"""P07 metrics: task feasibility, missing-affordance recall, false completion,
rights compliance — all with exact numerators/denominators.

Decision semantics:
  - gold label per case: the ORACLE verdict for that case
    ("select" with object id, or one of the typed rejects/abstain).
  - task_feasibility_rate : fraction of cases where the prediction is a
    SELECT whose object covers all required affordances and passes
    rights+constraints, matched against the gold feasibility verdict.
  - false_completion_rate : predicted select where gold says the case is
    NOT satisfiable (the sensitive error axis: accepting a modality that
    omits a required affordance).
  - missing_affordance_recall : fraction of gold missing-affordance cases
    whose prediction carries the matching reason code.
  - rights_compliance_violations : count of selects whose chosen object has
    a non-permissive license (must be 0 for any publishable method).

Every metric carries exact numerators/denominators; no fabricated confidence.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Mapping

COMPLETION_DECISIONS = frozenset({"select"})
REJECT_DECISIONS = frozenset(
    {"reject_missing_affordance", "reject_rights_violation", "reject_infeasible", "abstain"}
)


def _rate(numer: int, denom: int) -> dict[str, Any]:
    return {
        "numerator": numer,
        "denominator": denom,
        "rate": (numer / denom) if denom else None,
    }


def task_feasibility(preds: list[Mapping[str, Any]], golds: Mapping[str, str]) -> dict[str, Any]:
    """Exact-match decision accuracy: predicted decision == gold decision."""
    numer = sum(1 for p in preds if p.get("decision") == golds.get(str(p.get("case_id"))))
    return _rate(numer, len(golds))


def false_completion(preds: list[Mapping[str, Any]], golds: Mapping[str, str]) -> dict[str, Any]:
    """Predicted select where gold requires a reject/abstain."""
    numer = sum(
        1
        for p in preds
        if p.get("decision") in COMPLETION_DECISIONS
        and golds.get(str(p.get("case_id"))) in REJECT_DECISIONS
    )
    denom = sum(1 for p in preds if str(p.get("case_id")) in golds)
    return _rate(numer, denom)


def false_rejection(preds: list[Mapping[str, Any]], golds: Mapping[str, str]) -> dict[str, Any]:
    """Predicted reject/abstain where gold says a feasible object existed."""
    numer = sum(
        1
        for p in preds
        if p.get("decision") in REJECT_DECISIONS
        and golds.get(str(p.get("case_id"))) == "select"
    )
    denom = sum(1 for p in preds if str(p.get("case_id")) in golds)
    return _rate(numer, denom)


def missing_affordance_recall(preds: list[Mapping[str, Any]], golds: Mapping[str, str]) -> dict[str, Any]:
    """Gold missing-affordance cases whose prediction names the right axis."""
    gold_cases = {c for c, d in golds.items() if d == "reject_missing_affordance"}
    numer = sum(
        1
        for p in preds
        if str(p.get("case_id")) in gold_cases
        and p.get("decision") == "reject_missing_affordance"
        and p.get("missing_affordances")
    )
    return _rate(numer, len(gold_cases))


def rights_compliance(preds: list[Mapping[str, Any]], case_index: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    """Selects must never pick an object whose license forbids use."""
    violations: list[dict[str, Any]] = []
    for p in preds:
        if p.get("decision") != "select":
            continue
        case = case_index.get(str(p.get("case_id")))
        if not case:
            continue
        chosen = p.get("selected_object_id")
        obj = next((o for o in case["objects"] if o["object_id"] == chosen), None)
        if obj and obj.get("license_status") not in (
            "CC0",
            "CC-BY-4.0",
            "CC-BY-SA-4.0",
            "public_domain",
            "synthetic, no third-party rights",
        ):
            violations.append(
                {
                    "case_id": p.get("case_id"),
                    "selected_object_id": chosen,
                    "license_status": obj.get("license_status"),
                }
            )
    return {
        "violations": violations,
        "violation_count": len(violations),
        "denominator": len(preds),
        "violation_rate": (len(violations) / len(preds)) if preds else None,
    }


def confusion_by_stratum(preds: list[Mapping[str, Any]], golds: Mapping[str, str]) -> dict[str, Any]:
    """Per-stratum confusion: gold decision x predicted decision counts."""
    table: dict[str, Counter] = {}
    for p in preds:
        cid = str(p.get("case_id"))
        if cid not in golds:
            continue
        stratum = cid.split("-", 1)[0]
        table.setdefault(stratum, Counter())[(golds[cid], p.get("decision"))] += 1
    return {
        stratum: {f"gold_{g}__pred_{p}": n for (g, p), n in counter.items()}
        for stratum, counter in sorted(table.items())
    }


def all_metrics(
    preds: list[Mapping[str, Any]],
    golds: Mapping[str, str],
    case_index: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    return {
        "task_feasibility_rate": task_feasibility(preds, golds),
        "false_completion_rate": false_completion(preds, golds),
        "false_rejection_rate": false_rejection(preds, golds),
        "missing_affordance_recall": missing_affordance_recall(preds, golds),
        "rights_compliance": rights_compliance(preds, case_index),
        "confusion_by_stratum": confusion_by_stratum(preds, golds),
    }
