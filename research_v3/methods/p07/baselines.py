"""P07 baseline comparators.

- ``c0_url_present`` (C0 sanity): "URL present = usable". Any non-empty,
  rights-passing candidate is accepted; the first listed object wins. Sanity
  comparator only — never called a strong baseline (spec E02).
- ``c1_static_image_fallback`` (C1 classical): if the preferred 3D path is
  infeasible, serve the first static image and check ONLY the non-inscription
  affordance subset. The inscription/transcript gap is exactly the matched
  weakness under study (V2 LN-07 lesson).
- ``b05_random_eligible``: rights-passing pseudo-random choice from a seeded
  shuffle (seeded, deterministic per seed).

Both baselines consume the same case rows as the proposed engine and emit the
same decision schema. Neither imports the selector (independent procedures).
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence

from .affordances import (
    LICENSES_PERMITTING_USE,
    DeviceConstraints,
    LearningObject,
    SelectionDecision,
    TaskRequirements,
)

REASON_URL_ONLY = "url_present_only"
REASON_STATIC_FALLBACK = "static_image_fallback_ignores_inscription"
REASON_RIGHTS_FORBIDDEN = "license_forbids_use"
REASON_NO_CANDIDATES = "no_candidate_objects"

METHOD_VERSION = "p07-baselines-v1.0"


def _rights_ok(o: LearningObject) -> bool:
    return o.license_status in LICENSES_PERMITTING_USE


def c0_url_present(
    task: TaskRequirements, device: DeviceConstraints, objects: Sequence[LearningObject]
) -> SelectionDecision:
    """C0 sanity: first rights-passing object with a non-empty record wins."""
    for o in objects:
        if o.object_id and _rights_ok(o):
            return SelectionDecision(
                "select", o.object_id, (), (REASON_URL_ONLY,), kb_used=o.kb
            )
    if objects:
        return SelectionDecision(
            "reject_rights_violation", None, (), (REASON_RIGHTS_FORBIDDEN,)
        )
    return SelectionDecision("abstain", None, (), (REASON_NO_CANDIDATES,))


def _non_inscription_subset(task: TaskRequirements) -> tuple[str, ...]:
    return tuple(r for r in task.required_affordances if r != "inscription_text")


def c1_static_image_fallback(
    task: TaskRequirements, device: DeviceConstraints, objects: Sequence[LearningObject]
) -> SelectionDecision:
    """C1 classical: prefer 3D; fall back to first static image; the
    inscription requirement is silently dropped from the check."""
    needed = _non_inscription_subset(task)
    for o in objects:
        if not _rights_ok(o):
            continue
        if o.modality == "3d" and (not device.webgl or device.max_payload_kb is not None and o.kb > device.max_payload_kb):
            continue
        if o.modality == "3d" and device.network_kbps < 500:
            continue
        if all(o.affords(r) is True for r in needed):
            return SelectionDecision(
                "select", o.object_id, (), (REASON_STATIC_FALLBACK,), kb_used=o.kb
            )
    # fall through to the first static image that exists at all
    for o in objects:
        if o.modality in {"2d_image", "2d_rubbing"} and _rights_ok(o):
            return SelectionDecision(
                "select", o.object_id, (), (REASON_STATIC_FALLBACK,), kb_used=o.kb
            )
    return SelectionDecision("reject_infeasible", None, (), (REASON_NO_CANDIDATES,))


def b05_random_eligible(
    task: TaskRequirements, device: DeviceConstraints, objects: Sequence[LearningObject], seed: int = 2026
) -> SelectionDecision:
    """Seeded pseudo-random choice among rights-passing objects."""
    import hashlib

    eligible = [o for o in objects if _rights_ok(o)]
    if not eligible:
        if objects:
            return SelectionDecision(
                "reject_rights_violation", None, (), (REASON_RIGHTS_FORBIDDEN,)
            )
        return SelectionDecision("abstain", None, (), (REASON_NO_CANDIDATES,))
    digest = hashlib.sha256(f"{seed}:{task.task_id}".encode()).digest()
    pick = eligible[int.from_bytes(digest[:4], "big") % len(eligible)]
    return SelectionDecision(
        "select", pick.object_id, (), ("random_eligible",), kb_used=pick.kb
    )


def predict_case(method: str, row: Mapping[str, Any]) -> dict[str, Any]:
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
    if method == "c0_url_present":
        d = c0_url_present(task, device, objects)
    elif method == "c1_static_image_fallback":
        d = c1_static_image_fallback(task, device, objects)
    elif method == "b05_random_eligible":
        d = b05_random_eligible(task, device, objects, seed=int(row.get("seed", 2026)))
    else:
        raise ValueError(f"unknown baseline method {method!r}")
    return {
        "case_id": str(row["case_id"]),
        "group_id": str(row.get("group_id", row["case_id"])),
        "decision": d.decision,
        "selected_object_id": d.selected_object_id,
        "missing_affordances": list(d.missing_affordances),
        "reason_codes": list(d.reason_codes),
        "kb_used": d.kb_used,
    }
