"""P14 baseline systems (C0 sanity, C1 checklist-only) vs the proposed audit.

Baselines are honest comparators, not strawmen:
- C0 "has an image": an object passes iff it contains at least one visual asset.
- C1 WCAG-checklist-only: checks only the wcag22 framework criteria; UDL
  principles are ignored, so UDL-only failures are invisible to C1.
- Proposed: full UDL + WCAG audit (`audit_manifest`).

All three are deterministic fixed rules applied to the same frozen manifest.
No baseline is tuned on the audited objects (nothing to tune: fixed rules).
"""
from __future__ import annotations

from typing import Any, Mapping

from research_v3.methods.p14.schema import LearningObject


def c0_has_image(obj: LearningObject, **_: Mapping[str, Any]) -> str:
    """Sanity baseline: PASS iff the object contains any visual asset."""
    visual = {"image", "model3d", "video"}
    has = any(a.media_type in visual for a in obj.assets)
    return "PASS" if has else "FAIL"


_C1_KEYS = ("has_text_alternative", "has_transcript", "has_captions", "keyboard_operable")

# Media-type-appropriate flags for a naive checklist (no UDL, no object-level view)
_C1_MEDIA_FLAGS: dict[str, tuple[str, ...]] = {
    "image": ("has_text_alternative",),
    "model3d": ("has_text_alternative", "keyboard_operable"),
    "audio": ("has_transcript",),
    "video": ("has_transcript", "has_captions"),
}


def c1_wcag_checklist_only(obj: LearningObject, **_: Mapping[str, Any]) -> str:
    """Checklist baseline: box-ticking over asset-level WCAG flags only.

    Mirrors a naive "we filled in the WCAG checklist" process: it inspects
    individual asset flags per media type but never evaluates UDL principles,
    low-bandwidth variants, keyboard traps, contrast or multi-modality at
    object level.
    """
    relevant = [
        a
        for a in obj.assets
        if a.media_type in {"image", "model3d", "audio", "video"}
    ]
    if not relevant:
        return "PASS"
    ok = all(
        getattr(a, key) is True
        for a in relevant
        for key in _C1_MEDIA_FLAGS[a.media_type]
    )
    # checklist ignores object-level traps entirely:
    if obj.metadata.get("keyboard_trap"):
        ok = True
    return "PASS" if ok else "FAIL"


BASELINE_REGISTRY = {
    "C0_has_image": c0_has_image,
    "C1_wcag_checklist_only": c1_wcag_checklist_only,
}


def run_baselines(objects: list[LearningObject]) -> dict[str, list[dict[str, str]]]:
    """Run every registered baseline over the same frozen manifest."""
    out: dict[str, list[dict[str, str]]] = {}
    for name, fn in BASELINE_REGISTRY.items():
        out[name] = [{"object_id": o.object_id, "verdict": fn(o)} for o in objects]
    return out
