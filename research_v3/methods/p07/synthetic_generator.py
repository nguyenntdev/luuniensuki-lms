"""P07 deterministic synthetic stress-stratum generator.

Generates the scored stress suites the spec REQUIRES (section 5) and G16
demands: a scored matrix whose ONLY difference between paired positive and
negative cases is the missing transcript/inscription affordance, so the
ablation is identifiable (the ablation removes exactly that check and flips
exactly the paired negatives).

Strata (all deterministic from ``seed``):
  S1 image_exists_missing_inscription : raster with an image but no
      inscription text; task requires inscription_text  [MANDATORY]
  S2 audio_missing_transcript         : audio guide without transcript;
      task requires audio_transcript (screen-reader learner)
  S3 keyboard_inaccessible_3d         : 3D object not keyboard operable;
      keyboard-only learner
  S4 low_bandwidth_with_transcript    : 80 kbps link; text/rubbing fallback
      WITH transcript is feasible  (positive control — must be acceptable)
  S5 license_ambiguous                : provider field "unknown" vs "CC0"
  S6 transcript_identifiability_pair  : PAIRED cases identical except one
      affordance axis (transcript/inscription) — the G16 scored stress suite

No real-provider metadata is invented: provider-backed objects carry only
fields copied from real records (see external.py); everything else is
synthetic and labeled ``synthetic: true`` with LICENSE "synthetic, no
third-party rights".
"""
from __future__ import annotations

import json
from typing import Any

SYNTHETIC_LICENSE = "synthetic, no third-party rights"

_BASE_OBJECTS: list[dict[str, Any]] = [
    {
        "object_id": "syn_3d",
        "modality": "3d",
        "kb": 1850,
        "affordances": {
            "image": True,
            "visual_detail": True,
            "spatial_relation": True,
            "relief_depth": True,
            "spatial_interaction": True,
            "keyboard_accessible": True,
            "screen_reader_ready": False,
            "inscription_text": None,
        },
    },
    {
        "object_id": "syn_raster",
        "modality": "2d_image",
        "kb": 320,
        "affordances": {
            "image": True,
            "visual_detail": True,
            "spatial_relation": False,
            "relief_depth": False,
            "keyboard_accessible": True,
            "screen_reader_ready": False,
            "inscription_text": None,
        },
    },
    {
        "object_id": "syn_rubbing",
        "modality": "2d_rubbing",
        "kb": 95,
        "affordances": {
            "image": True,
            "visual_detail": True,
            "spatial_relation": True,
            "relief_depth": True,
            "keyboard_accessible": True,
            "screen_reader_ready": False,
            "inscription_text": None,
        },
    },
    {
        "object_id": "syn_audio",
        "modality": "audio",
        "kb": 480,
        "affordances": {
            "audio": True,
            "description": True,
            "visual_detail": True,
            "relief_depth": True,
            "keyboard_accessible": True,
            "screen_reader_ready": True,
            "audio_transcript": None,
            "inscription_text": None,
        },
    },
    {
        "object_id": "syn_text",
        "modality": "text",
        "kb": 10,
        "affordances": {
            "description": True,
            "visual_detail": True,
            "relief_depth": True,
            "keyboard_accessible": True,
            "screen_reader_ready": True,
            "audio_transcript": None,
            "inscription_text": None,
        },
    },
]

_TASKS: dict[str, dict[str, Any]] = {
    "epigraphy_reading": {
        "task_type": "analyze_epigraphy",
        "required_affordances": ["visual_detail", "inscription_text"],
    },
    "audio_narration_comprehension": {
        "task_type": "audio_comprehension",
        "required_affordances": ["audio", "audio_transcript"],
    },
    "relief_relation_identification": {
        "task_type": "identify_relief_relation",
        "required_affordances": ["visual_detail", "spatial_relation"],
    },
}

_DEVICE_NOMINAL: dict[str, Any] = {
    "network_kbps": 3000,
    "keyboard_only": False,
    "screen_reader": False,
    "webgl": True,
}
_DEVICE_LOW_BANDWIDTH: dict[str, Any] = {
    "network_kbps": 120,
    "keyboard_only": False,
    "screen_reader": False,
    "webgl": True,
    "max_payload_kb": 100,
}
_DEVICE_KEYBOARD_ONLY: dict[str, Any] = {
    "network_kbps": 3000,
    "keyboard_only": True,
    "screen_reader": False,
    "webgl": True,
}
_DEVICE_SCREEN_READER: dict[str, Any] = {
    "network_kbps": 3000,
    "keyboard_only": True,
    "screen_reader": True,
    "webgl": False,
}


def _clone_objects() -> list[dict[str, Any]]:
    return json.loads(json.dumps(_BASE_OBJECTS))


def _case(case_id: str, group_id: str, task_key: str, device: dict[str, Any],
          mutate: Any, seed: int) -> dict[str, Any]:
    objects = _clone_objects()
    for o in objects:
        o["license_status"] = "CC0"
        o["provider"] = "synthetic"
    mutate(objects)  # mutators may override any field, including license
    return {
        "case_id": case_id,
        "group_id": group_id,
        "seed": seed,
        "synthetic": True,
        "license": SYNTHETIC_LICENSE,
        "task": {"task_id": task_key, **_TASKS[task_key]},
        "device": dict(device),
        "objects": objects,
    }


def _set(objs: list[dict[str, Any]], oid: str, axis: str, value: bool | None) -> None:
    for o in objs:
        if o["object_id"] == oid:
            o["affordances"][axis] = value
            return
    raise ValueError(f"object {oid} not found")


def generate_stress_cases(seed: int = 20261115) -> list[dict[str, Any]]:
    """Deterministic stress suite; identical inputs always identical outputs."""
    cases: list[dict[str, Any]] = []

    def add(case_id: str, group: str, task: str, device: dict[str, Any], mutate: Any) -> None:
        cases.append(_case(case_id, group, task, device, mutate, seed))

    # S1 MANDATORY: raster HAS an image but OMITS the inscription.
    add("S1-POS-feasible-text", "G-S1", "epigraphy_reading", _DEVICE_NOMINAL,
        lambda o: _set(o, "syn_text", "inscription_text", True))
    add("S1-NEG-raster-missing-inscription", "G-S1", "epigraphy_reading", _DEVICE_NOMINAL,
        lambda o: [_set(o, "syn_text", "inscription_text", False), _set(o, "syn_raster", "inscription_text", False)])
    add("S1-NEG-rubbing-missing-inscription", "G-S1", "epigraphy_reading", _DEVICE_NOMINAL,
        lambda o: [_set(o, "syn_text", "inscription_text", False), _set(o, "syn_rubbing", "inscription_text", False)])

    # S2: audio WITHOUT transcript on a transcript-required task (screen reader).
    add("S2-POS-audio-with-transcript", "G-S2", "audio_narration_comprehension", _DEVICE_SCREEN_READER,
        lambda o: _set(o, "syn_audio", "audio_transcript", True))
    add("S2-NEG-audio-missing-transcript", "G-S2", "audio_narration_comprehension", _DEVICE_SCREEN_READER,
        lambda o: [_set(o, "syn_audio", "audio_transcript", False), _set(o, "syn_text", "audio_transcript", False)])

    # S3: keyboard-inaccessible 3D, keyboard-only learner.
    add("S3-POS-3d-keyboard-ok", "G-S3", "relief_relation_identification", _DEVICE_KEYBOARD_ONLY,
        lambda o: _set(o, "syn_3d", "keyboard_accessible", True))
    add("S3-NEG-3d-keyboard-inaccessible", "G-S3", "relief_relation_identification", _DEVICE_KEYBOARD_ONLY,
        lambda o: _set(o, "syn_3d", "keyboard_accessible", False))

    # S4: low-bandwidth WITH transcript must be ACCEPTED (positive control).
    # The 10KB text object carrying inscription_text + audio_transcript passes
    # the 120 kbps / 100 KB budget; the audio object (480 KB) does not.
    add("S4-POS-lowbw-text-transcript", "G-S4", "epigraphy_reading", _DEVICE_LOW_BANDWIDTH,
        lambda o: _set(o, "syn_text", "inscription_text", True))
    add("S4-NEG-lowbw-text-no-transcript", "G-S4", "epigraphy_reading", _DEVICE_LOW_BANDWIDTH,
        lambda o: _set(o, "syn_text", "inscription_text", False))
    add("S4-POS-lowbw-rubbing", "G-S4", "relief_relation_identification", _DEVICE_LOW_BANDWIDTH,
        lambda o: o)

    # S5: license ambiguity vs CC0.
    def lic_unknown(objs: list[dict[str, Any]]) -> None:
        for o in objs:
            o["license_status"] = "unknown"
    add("S5-NEG-all-license-unknown", "G-S5", "relief_relation_identification", _DEVICE_NOMINAL, lic_unknown)
    add("S5-POS-license-cc0", "G-S5", "relief_relation_identification", _DEVICE_NOMINAL, lambda o: o)

    # S6 G16 IDENTIFIABILITY PAIR: cases differ ONLY in the transcript/inscription axis.
    add("S6-PAIR-A-inscription-present", "G-S6-PAIR", "epigraphy_reading", _DEVICE_NOMINAL,
        lambda o: _set(o, "syn_text", "inscription_text", True))
    add("S6-PAIR-B-inscription-removed", "G-S6-PAIR", "epigraphy_reading", _DEVICE_NOMINAL,
        lambda o: _set(o, "syn_text", "inscription_text", False))
    add("S6-PAIR-C-transcript-present", "G-S6-PAIR", "audio_narration_comprehension", _DEVICE_SCREEN_READER,
        lambda o: _set(o, "syn_audio", "audio_transcript", True))
    add("S6-PAIR-D-transcript-removed", "G-S6-PAIR", "audio_narration_comprehension", _DEVICE_SCREEN_READER,
        lambda o: [_set(o, "syn_audio", "audio_transcript", False), _set(o, "syn_text", "audio_transcript", False)])

    # S7: nothing at all is feasible -> explicit abstain, no fake success.
    add("S7-NEG-empty-pool", "G-S7", "relief_relation_identification", _DEVICE_NOMINAL,
        lambda o: o.clear() or None)

    return cases


def stratum_of(case_id: str) -> str:
    return case_id.split("-", 1)[0]
