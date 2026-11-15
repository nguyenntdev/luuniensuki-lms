"""P07 ablation variants: TRUE removals of the named mechanisms.

A1_no_affordance_coverage : drop the required-affordance coverage check.
A2_no_device_constraints  : drop bandwidth/WebGL/keyboard/screen-reader checks.
A5_no_rights_filtering    : drop the license screen.

Each ablation is an independent decision procedure over the same case rows;
nothing is renamed or re-labeled — the mechanism is genuinely absent, so any
metric divergence is attributable to the removed mechanism.
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence

from research_v3.methods.p07.affordances import (
    DeviceConstraints,
    LearningObject,
    SelectionDecision,
    TaskRequirements,
)

REASON_ABLATION = "ablation"
REASON_MISSING_AFFORDANCE = "missing_required_affordance"
REASON_NO_CANDIDATES = "no_candidate_objects"


def _base_violations(
    o: LearningObject,
    task: TaskRequirements,
    device: DeviceConstraints,
    *,
    check_device: bool,
    check_affordance: bool,
    check_rights: bool,
) -> tuple[str, ...]:
    codes: list[str] = []
    if check_rights and o.license_status not in {"CC0", "CC-BY-4.0", "CC-BY-SA-4.0", "public_domain"}:
        codes.append("license_forbids_use")
    if check_device:
        if o.kb > 0 and device.network_kbps < (500 if o.modality == "3d" else 100 if o.modality != "text" else 10):
            codes.append("bandwidth_budget_exceeded")
        if o.modality == "3d" and not device.webgl:
            codes.append("webgl_unavailable")
        if device.keyboard_only and o.affords("keyboard_accessible") is not True:
            codes.append("keyboard_inaccessible")
        if device.screen_reader and o.affords("screen_reader_ready") is not True:
            codes.append("screen_reader_inaccessible")
    if check_affordance and any(o.affords(r) is not True for r in task.required_affordances):
        codes.append(REASON_MISSING_AFFORDANCE)
    return tuple(codes)


def _run_ablation(
    task: TaskRequirements,
    device: DeviceConstraints,
    objects: Sequence[LearningObject],
    *,
    check_device: bool,
    check_affordance: bool,
    check_rights: bool,
) -> SelectionDecision:
    if not objects:
        return SelectionDecision("abstain", None, (), (REASON_NO_CANDIDATES,))
    audited = sorted(objects, key=lambda o: o.object_id)
    feasible = [
        o
        for o in audited
        if not _base_violations(
            o,
            task,
            device,
            check_device=check_device,
            check_affordance=check_affordance,
            check_rights=check_rights,
        )
    ]
    if not feasible:
        return SelectionDecision("reject_infeasible", None, (), (REASON_ABLATION,))
    chosen = min(feasible, key=lambda o: (o.kb, o.object_id))
    return SelectionDecision("select", chosen.object_id, (), (REASON_ABLATION,), kb_used=chosen.kb)


def _parse(row: Mapping[str, Any]) -> tuple[TaskRequirements, DeviceConstraints, list[LearningObject]]:
    from research_v3.methods.p07.affordances import parse_device, parse_task

    task = parse_task(row["task"])  # type: ignore[arg-type]
    device = parse_device(row["device"])  # type: ignore[arg-type]
    objects = [
        LearningObject(
            object_id=str(o["object_id"]),
            modality=str(o["modality"]),
            kb=int(o["kb"]),  # type: ignore[call-overload]
            affordances=dict(o["affordances"]),  # type: ignore[arg-type]
            license_status=str(o["license_status"]),
            source_record_id=o.get("source_record_id"),
            source_url=o.get("source_url"),
            provider=o.get("provider"),
            affordance_facts=dict(o.get("affordance_facts", {})),  # type: ignore[arg-type]
        )
        for o in row["objects"]  # type: ignore[union-attr]
    ]
    return task, device, objects


def _predict(method: str, row: Mapping[str, Any]) -> dict[str, Any]:
    task, device, objects = _parse(row)
    kw: dict[str, bool]
    if method == "A1_no_affordance_coverage":
        kw = dict(check_device=True, check_affordance=False, check_rights=True)
    elif method == "A2_no_device_constraints":
        kw = dict(check_device=False, check_affordance=True, check_rights=True)
    elif method == "A5_no_rights_filtering":
        kw = dict(check_device=True, check_affordance=True, check_rights=False)
    else:
        raise ValueError(f"unknown ablation {method!r}")
    d = _run_ablation(task, device, objects, **kw)
    return {
        "case_id": str(row["case_id"]),
        "group_id": str(row.get("group_id", row["case_id"])),
        "decision": d.decision,
        "selected_object_id": d.selected_object_id,
        "missing_affordances": list(d.missing_affordances),
        "reason_codes": list(d.reason_codes),
        "kb_used": d.kb_used,
    }


def predict_case(method: str, row: Mapping[str, Any]) -> dict[str, Any]:
    return _predict(method, row)
