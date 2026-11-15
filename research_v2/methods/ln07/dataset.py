"""LN-07 dataset loading, schema validation and oracle-free case view.

Inference-time feature schema for one case (the ``input`` subtree of the T3
holdout fixtures; see spec 03/04):

    content            : {id, motif, motif_name, type} heritage asset identity
    device             : {webgl, network_kbps, keyboard_only, screen_reader,
                         webgl_context_lost?}
    learner            : profile metadata (never used by policies)
    task               : {type, description, required_affordances,
                         transcript_required}
    options            : list of modality variants {id, modality, kb,
                         affordances, keyboard, requires_webgl, available,
                         alt_text?, transcript?, screen_reader_ready?,
                         sub_type?}
    seed               : scenario generation seed (tie-breaking only)

Any invalid row rejects the whole batch with its location - never a guessed
fallback value. Gold material (``expected_decision``, ``oracle``, ``fault_id``)
never enters this module: the runner masks fixture rows via
``research_v2.contracts.input_masking.mask_case_input`` before dispatch.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .labels import BANDWIDTH_3D_MIN_KBPS


class DatasetError(ValueError):
    """Raised when a dataset row violates the LN-07 input schema."""


REPO_ROOT = Path(__file__).resolve().parents[3]
DATASET_PATH = REPO_ROOT / "research_v2" / "data" / "ln07" / "t3_inputs.jsonl"
GOLD_PATH = REPO_ROOT / "research_v2" / "data" / "ln07" / "t3_gold.jsonl"
STUDY_ID = "LN-07"


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with Path(path).open(encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                rows.append(json.loads(line))
    return rows


@dataclass(frozen=True)
class ModalityOption:
    id: str
    modality: str
    kb: int
    affordances: tuple[str, ...]
    keyboard: bool
    requires_webgl: bool
    available: bool
    alt_text: str = ""
    transcript: bool | None = None
    screen_reader_ready: bool | None = None
    sub_type: str = ""

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any], *, location: str) -> "ModalityOption":
        if not isinstance(raw, Mapping):
            raise DatasetError(f"{location}: option must be a mapping, got {type(raw).__name__}")
        oid = raw.get("id")
        if not isinstance(oid, str) or not oid:
            raise DatasetError(f"{location}: option.id must be a non-empty string")
        modality = raw.get("modality")
        if not isinstance(modality, str) or not modality:
            raise DatasetError(f"{location}: option {oid!r} modality must be a non-empty string")
        kb = raw.get("kb", 0)
        if not isinstance(kb, (int, float)) or isinstance(kb, bool) or kb < 0:
            raise DatasetError(f"{location}: option {oid!r} kb must be a non-negative number")
        affordances = raw.get("affordances", [])
        if not isinstance(affordances, list) or not all(isinstance(a, str) for a in affordances):
            raise DatasetError(
                f"{location}: option {oid!r} affordances must be a list of strings"
            )
        keyboard = raw.get("keyboard", True)
        if not isinstance(keyboard, bool):
            raise DatasetError(f"{location}: option {oid!r} keyboard must be a boolean")
        requires_webgl = raw.get("requires_webgl", False)
        if not isinstance(requires_webgl, bool):
            raise DatasetError(f"{location}: option {oid!r} requires_webgl must be a boolean")
        available = raw.get("available", True)
        if not isinstance(available, bool):
            raise DatasetError(f"{location}: option {oid!r} available must be a boolean")
        alt_text = raw.get("alt_text", "")
        if not isinstance(alt_text, str):
            raise DatasetError(f"{location}: option {oid!r} alt_text must be a string")
        transcript = raw.get("transcript")
        if transcript is not None and not isinstance(transcript, bool):
            raise DatasetError(f"{location}: option {oid!r} transcript must be a boolean or null")
        srr = raw.get("screen_reader_ready")
        if srr is not None and not isinstance(srr, bool):
            raise DatasetError(
                f"{location}: option {oid!r} screen_reader_ready must be a boolean or null"
            )
        sub_type = raw.get("sub_type", "")
        if not isinstance(sub_type, str):
            raise DatasetError(f"{location}: option {oid!r} sub_type must be a string")
        return cls(
            id=oid,
            modality=modality,
            kb=int(kb),
            affordances=tuple(dict.fromkeys(affordances)),
            keyboard=keyboard,
            requires_webgl=requires_webgl,
            available=available,
            alt_text=alt_text,
            transcript=transcript,
            screen_reader_ready=srr,
            sub_type=sub_type,
        )

    @property
    def affordance_set(self) -> frozenset[str]:
        return frozenset(self.affordances)

    @property
    def is_rubbing(self) -> bool:
        return self.modality == "2d" and self.sub_type == "rubbing"


@dataclass(frozen=True)
class DeviceProfile:
    webgl: bool
    network_kbps: int
    keyboard_only: bool
    screen_reader: bool
    webgl_context_lost: bool = False

    @property
    def webgl_usable(self) -> bool:
        return self.webgl and not self.webgl_context_lost

    @property
    def low_bandwidth(self) -> bool:
        return self.network_kbps < BANDWIDTH_3D_MIN_KBPS


@dataclass(frozen=True)
class TaskSpec:
    type: str
    description: str
    required_affordances: tuple[str, ...]
    transcript_required: bool

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any], *, location: str) -> "TaskSpec":
        if not isinstance(raw, Mapping):
            raise DatasetError(f"{location}: task must be a mapping")
        ttype = raw.get("type")
        if not isinstance(ttype, str) or not ttype:
            raise DatasetError(f"{location}: task.type must be a non-empty string")
        required = raw.get("required_affordances")
        if not isinstance(required, list) or not all(isinstance(a, str) and a for a in required):
            raise DatasetError(
                f"{location}: task.required_affordances must be a list of non-empty strings"
            )
        transcript_required = raw.get("transcript_required", False)
        if not isinstance(transcript_required, bool):
            raise DatasetError(f"{location}: task.transcript_required must be a boolean")
        return cls(
            type=ttype,
            description=str(raw.get("description", "")),
            required_affordances=tuple(dict.fromkeys(required)),
            transcript_required=transcript_required,
        )


@dataclass(frozen=True)
class ModalityCase:
    """Validated, oracle-free view of one LN-07 case."""

    case_id: str
    content_id: str
    content_type: str
    device: DeviceProfile
    task: TaskSpec
    options: tuple[ModalityOption, ...]
    seed: int = 0

    @classmethod
    def from_features(cls, features: Mapping[str, Any], *, case_id: str) -> "ModalityCase":
        location = f"case {case_id!r}"
        if not isinstance(features, Mapping):
            raise DatasetError(f"{location}: features must be a mapping")

        content = features.get("content")
        if not isinstance(content, Mapping):
            raise DatasetError(f"{location}: content must be a mapping")
        content_id = content.get("id")
        if not isinstance(content_id, str) or not content_id:
            raise DatasetError(f"{location}: content.id must be a non-empty string")

        raw_device = features.get("device")
        if not isinstance(raw_device, Mapping):
            raise DatasetError(f"{location}: device must be a mapping")
        webgl = raw_device.get("webgl", True)
        kbps = raw_device.get("network_kbps", BANDWIDTH_3D_MIN_KBPS)
        keyboard_only = raw_device.get("keyboard_only", False)
        screen_reader = raw_device.get("screen_reader", False)
        webgl_context_lost = raw_device.get("webgl_context_lost", False)
        for name, val in (
            ("webgl", webgl),
            ("keyboard_only", keyboard_only),
            ("screen_reader", screen_reader),
            ("webgl_context_lost", webgl_context_lost),
        ):
            if not isinstance(val, bool):
                raise DatasetError(f"{location}: device.{name} must be a boolean")
        if not isinstance(kbps, (int, float)) or isinstance(kbps, bool) or kbps < 0:
            raise DatasetError(f"{location}: device.network_kbps must be a non-negative number")

        raw_task = features.get("task")
        if not isinstance(raw_task, Mapping):
            raise DatasetError(f"{location}: task must be a mapping")
        task = TaskSpec.from_dict(raw_task, location=location)

        raw_options = features.get("options")
        if not isinstance(raw_options, list) or not raw_options:
            raise DatasetError(f"{location}: options must be a non-empty list")
        options = tuple(
            ModalityOption.from_dict(o, location=f"{location} options[{i}]")
            for i, o in enumerate(raw_options)
        )
        ids = [o.id for o in options]
        if len(set(ids)) != len(ids):
            raise DatasetError(f"{location}: duplicate option ids in {ids}")

        seed = features.get("seed", 0)
        if not isinstance(seed, int) or isinstance(seed, bool):
            raise DatasetError(f"{location}: seed must be an integer")

        return cls(
            case_id=case_id,
            content_id=content_id,
            content_type=str(content.get("type", "")),
            device=DeviceProfile(
                webgl=bool(webgl),
                network_kbps=int(kbps),
                keyboard_only=bool(keyboard_only),
                screen_reader=bool(screen_reader),
                webgl_context_lost=bool(webgl_context_lost),
            ),
            task=task,
            options=options,
            seed=seed,
        )

    # -- convenience accessors ------------------------------------------------
    def options_with_modality(self, modality: str) -> tuple[ModalityOption, ...]:
        return tuple(o for o in self.options if o.modality == modality)

    def first_available(self, modality: str) -> ModalityOption | None:
        for o in self.options:
            if o.modality == modality and o.available:
                return o
        return None


@dataclass(frozen=True)
class DecisionTrace:
    """Structured result of one policy evaluation on one validated case."""

    decision: str
    reason_codes: tuple[str, ...]
    selected_option_id: str
    selected_modality: str
    fallback_type: str
    missing_affordances: tuple[str, ...]
    task_feasible: bool


def from_input(inp: Any) -> ModalityCase:
    """Build the validated case view from a contract StudyInput."""
    from research_v2.contracts.types import StudyInput

    if not isinstance(inp, StudyInput):
        raise DatasetError(f"expects StudyInput, got {type(inp).__name__}")
    return ModalityCase.from_features(inp.features, case_id=inp.case_id)
