"""P07 proposed selector — affordance-complete, constraint- and rights-aware.

Mechanism (fixed constraints; no learned weights — see METHOD.md equation E1):

For task T with required affordances R(T), device constraints D, candidate
objects O = {o1..on}:

  1. RIGHTS SCREEN (hard): o is dropped unless license_status(o) in
     LICENSES_PERMITTING_USE. If ALL candidates fail only this screen the
     decision is ``reject_rights_violation`` (never a silent substitution).
  2. DEVICE/BANDWIDTH FEASIBILITY (hard): o requires bandwidth kb(o) <=
     min(payload_budget(D), bandwidth-feasible ceiling for its modality);
     3D additionally requires webgl(D); audio additionally requires the
     player to be non-WebGL (always true here). Keyboard-only or
     screen-reader learners require keyboard_accessible /
     screen_reader_ready respectively.
  3. AFFORDANCE COVERAGE (the named mechanism): covers(o, R(T)) iff for every
     r in R(T): o.affords(r) is True (NOT_APPLICABLE/None never counts as
     coverage). An image-bearing raster missing inscription_text is therefore
     NOT equivalent for an inscription task.
  4. SELECTION: among feasible+covering candidates pick minimal kb, tie-break
     lexicographic object_id. If none covers, the object with the FEWEST
     missing required affordances is named in the failure reason and the
     decision is ``reject_missing_affordance`` (fail-closed, no false
     completion). If the candidate pool is empty the decision is ``abstain``.

Determinism: pure function of inputs; no RNG, no clock, no gold access.
Complexity: O(n * |R(T)|) per case, n = candidate count.
"""
from __future__ import annotations

from typing import Mapping, Sequence

from .affordances import (
    LICENSES_PERMITTING_USE,
    DeviceConstraints,
    LearningObject,
    SelectionDecision,
    TaskRequirements,
)

#: Modality bandwidth ceilings (kbps) below which the modality cannot stream
#: in study-configured time budgets. 3D assets are heavy; 2D/audio/text are
#: progressively lighter. Configured constants, not learned parameters.
BANDWIDTH_CEILING_KBPS: dict[str, int] = {
    "3d": 500,
    "2d_image": 100,
    "2d_rubbing": 100,
    "audio": 100,
    "text": 10,
}

REASON_RIGHTS_FORBIDDEN = "license_forbids_use"
REASON_BANDWIDTH = "bandwidth_budget_exceeded"
REASON_WEBGL = "webgl_unavailable"
REASON_KEYBOARD = "keyboard_inaccessible"
REASON_SCREEN_READER = "screen_reader_inaccessible"
REASON_MISSING_AFFORDANCE = "missing_required_affordance"
REASON_NO_CANDIDATES = "no_candidate_objects"
REASON_ABSTAIN = "abstain_no_feasible_candidate"
REASON_SELECTED = "affordance_complete_under_constraints"

METHOD_ID = "proposed"
METHOD_VERSION = "p07-proposed-v1.0"


def missing_required(o: LearningObject, task: TaskRequirements) -> tuple[str, ...]:
    """Axes in R(T) that o does NOT verifiably afford (None/False both fail)."""
    return tuple(r for r in task.required_affordances if o.affords(r) is not True)


def _violations(
    o: LearningObject, task: TaskRequirements, device: DeviceConstraints
) -> dict[str, tuple[str, ...]]:
    """All hard-check violations for one candidate, grouped by axis."""
    v: dict[str, tuple[str, ...]] = {}
    if o.license_status not in LICENSES_PERMITTING_USE:
        v["rights"] = (REASON_RIGHTS_FORBIDDEN,)
    budget = device.max_payload_kb
    if o.kb > (budget if budget is not None else o.kb):
        v["bandwidth"] = (REASON_BANDWIDTH,)
    if o.kb > 0 and device.network_kbps < BANDWIDTH_CEILING_KBPS.get(o.modality, 0):
        v["bandwidth"] = (REASON_BANDWIDTH,)
    if o.modality == "3d" and not device.webgl:
        v["webgl"] = (REASON_WEBGL,)
    if device.keyboard_only and o.affords("keyboard_accessible") is not True:
        v["keyboard"] = (REASON_KEYBOARD,)
    if device.screen_reader and o.affords("screen_reader_ready") is not True:
        v["screen_reader"] = (REASON_SCREEN_READER,)
    miss = missing_required(o, task)
    if miss:
        v["affordance"] = (REASON_MISSING_AFFORDANCE,)
    return v


def select(
    task: TaskRequirements,
    device: DeviceConstraints,
    objects: Sequence[LearningObject],
) -> SelectionDecision:
    """Affordance-complete selection. Pure; deterministic; oracle-free."""
    if not objects:
        return SelectionDecision(
            "abstain", None, (), (REASON_NO_CANDIDATES, REASON_ABSTAIN)
        )
    audited = sorted(objects, key=lambda o: o.object_id)
    rights_blocked = [o for o in audited if "rights" in _violations(o, task, device)]
    if rights_blocked and len(rights_blocked) == len(audited):
        return SelectionDecision(
            "reject_rights_violation",
            None,
            (),
            (REASON_RIGHTS_FORBIDDEN, REASON_ABSTAIN),
        )
    feasible: list[LearningObject] = []
    best_failure: tuple[int, tuple[str, ...], LearningObject] | None = None
    device_only_codes: tuple[str, ...] = ()
    for o in audited:
        v = _violations(o, task, device)
        if not v:
            feasible.append(o)
            continue
        miss = v.get("affordance", ())
        device_codes = tuple(
            code for axis in ("bandwidth", "webgl", "keyboard", "screen_reader") for code in v.get(axis, ())
        )
        if device_codes and not device_only_codes:
            device_only_codes = device_codes
        if miss:
            n_miss = len(missing_required(o, task))
            if best_failure is None or n_miss < best_failure[0]:
                best_failure = (n_miss, device_codes + (REASON_MISSING_AFFORDANCE,), o)
    if not feasible:
        if best_failure is not None:
            return SelectionDecision(
                "reject_missing_affordance",
                None,
                missing_required(best_failure[2], task),
                best_failure[1] + (REASON_ABSTAIN,),
            )
        return SelectionDecision(
            "reject_infeasible", None, (), device_only_codes + (REASON_ABSTAIN,)
        )
    chosen = min(feasible, key=lambda o: (o.kb, o.object_id))
    return SelectionDecision(
        "select",
        chosen.object_id,
        (),
        (REASON_SELECTED,),
        kb_used=chosen.kb,
    )


def predict_case(row: Mapping[str, object]) -> dict[str, object]:
    """Adapter from a case row (objects + task + device) to a decision row."""
    from .affordances import parse_device, parse_task

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
    decision = select(task, device, objects)
    return {
        "case_id": str(row["case_id"]),
        "group_id": str(row.get("group_id", row["case_id"])),
        "decision": decision.decision,
        "selected_object_id": decision.selected_object_id,
        "missing_affordances": list(decision.missing_affordances),
        "reason_codes": list(decision.reason_codes),
        "kb_used": decision.kb_used,
    }
