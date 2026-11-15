"""P07 experiment runner: methods x datasets x metrics, deterministic.

Every method (proposed + baselines) runs over the same case rows; predictions
are written to JSONL; metrics carry exact numerators/denominators. Gold is
loaded separately and never enters any method's input.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from research_v3.methods.p07.baselines import METHOD_VERSION as BASELINE_VERSION
from research_v3.methods.p07.baselines import predict_case as baseline_predict
from research_v3.methods.p07.metrics import all_metrics
from research_v3.methods.p07.selector import METHOD_VERSION as PROPOSED_VERSION
from research_v3.methods.p07.selector import predict_case as proposed_predict

METHODS: tuple[str, ...] = (
    "proposed",
    "c0_url_present",
    "c1_static_image_fallback",
    "b05_random_eligible",
)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with Path(path).open(encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def gold_from_cases(cases: list[dict[str, Any]]) -> dict[str, str]:
    """Oracle verdicts derived from the derivational-fact rule (not from any
    model output). A case is 'select'-satisfiable iff at least one candidate
    verifiably affords ALL required affordances and passes rights."""
    from research_v3.methods.p07.affordances import LICENSES_PERMITTING_USE

    golds: dict[str, str] = {}
    for case in cases:
        if not case["objects"]:
            golds[case["case_id"]] = "abstain"
            continue
        task = case["task"]
        required = task["required_affordances"]
        device = case["device"]
        verdict = "reject_missing_affordance"
        rights_only_blocked = True
        for o in case["objects"]:
            if o.get("license_status") not in LICENSES_PERMITTING_USE:
                continue
            rights_only_blocked = False
            if o["modality"] == "3d" and not device.get("webgl", True):
                continue
            if device.get("max_payload_kb") is not None and o["kb"] > device["max_payload_kb"]:
                continue
            if o["kb"] > 0 and device.get("network_kbps", 0) < (
                500 if o["modality"] == "3d" else 100 if o["modality"] != "text" else 10
            ):
                continue
            if device.get("keyboard_only") and o["affordances"].get("keyboard_accessible") is not True:
                continue
            if device.get("screen_reader") and o["affordances"].get("screen_reader_ready") is not True:
                continue
            if all(o["affordances"].get(r) is True for r in required):
                verdict = "select"
                break
        if rights_only_blocked and case["objects"] and all(
            o.get("license_status") not in LICENSES_PERMITTING_USE for o in case["objects"]
        ):
            verdict = "reject_rights_violation"
        golds[case["case_id"]] = verdict
    return golds


def run_method(method: str, cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    preds: list[dict[str, Any]] = []
    for row in cases:
        if method == "proposed":
            preds.append(proposed_predict(row))
        else:
            preds.append(baseline_predict(method, row))
    return preds


def evaluate(
    cases: list[dict[str, Any]], golds: dict[str, str]
) -> dict[str, dict[str, Any]]:
    """All methods, all metrics. golds never enter method inputs."""
    case_index = {str(c["case_id"]): c for c in cases}
    results: dict[str, dict[str, Any]] = {}
    for method in METHODS:
        preds = run_method(method, cases)
        results[method] = all_metrics(preds, golds, case_index)
        results[method]["method_version"] = (
            PROPOSED_VERSION if method == "proposed" else BASELINE_VERSION
        )
    return results
