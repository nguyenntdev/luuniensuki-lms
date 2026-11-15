"""P07 affordance ontology: typed affordances, constraints and licenses.

Spec contract (P07 spec section 3, requirement 1): exact input/output
dataclasses with type/constraint invariants and a ``NOT_APPLICABLE`` value
distinct from negative predictions and from ``ABSTAIN``.

Affordance axes (multilabel, closed vocabulary):
  - image                 : visual raster/rubbing is served
  - visual_detail         : task-relevant fine visual detail is preserved
  - spatial_relation      : spatial composition/relations preserved
  - relief_depth          : depth/relief information preserved (3D or rubbing)
  - inscription_text      : the inscription/glyph text the task requires is
                            readable as text (transcript, transcription or
                            text layer). Image presence alone NEVER implies
                            this — the V2 LN-07 lesson.
  - audio                 : narration/audio guide
  - audio_transcript      : text transcript of the audio (WCAG 1.2.1 axis)
  - description           : structured description / alt text
  - keyboard_accessible   : operable without a pointer (WCAG 2.1.1 axis)
  - screen_reader_ready   : semantics exposed to assistive tech (WCAG 4.1.2)
  - spatial_interaction   : manipulable 3D interaction

Tri-state values: True (affordance present), False (absent), None
(NOT_APPLICABLE — the axis does not apply to this object type, e.g.
``relief_depth`` on a text transcript). ``None`` is distinct from ``False``:
a selector must treat NOT_APPLICABLE as "cannot verify, axis does not apply"
and only *require* axes the task actually demands.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

#: Closed affordance vocabulary (multilabel ontology).
AFFORDANCE_VOCAB: frozenset[str] = frozenset(
    {
        "image",
        "visual_detail",
        "spatial_relation",
        "relief_depth",
        "inscription_text",
        "audio",
        "audio_transcript",
        "description",
        "keyboard_accessible",
        "screen_reader_ready",
        "spatial_interaction",
    }
)

#: Affordances that count as inscription/text-content affordances. A raster
#: that HAS an image but OMITS these is NOT cognitively equivalent for a task
#: that requires them (V2 LN-07 mandatory counterexample).
INSCRIPTION_AFFORDANCES: frozenset[str] = frozenset({"inscription_text"})

#: License values that permit academic analysis + derived artifacts for this
#: study. Anything else (or missing/ambiguous) fails rights screening.
LICENSES_PERMITTING_USE: frozenset[str] = frozenset(
    {"CC0", "CC-BY-4.0", "CC-BY-SA-4.0", "public_domain"}
)

_LICENSE_FORBIDDEN_EXPLICIT: frozenset[str] = frozenset(
    {"CC-BY-NC-4.0", "rights_reserved", "restricted", "unknown"}
)


class SchemaError(ValueError):
    """Raised when an object/task row violates the P07 input schema."""


def _opt_bool(v: Any, ctx: str) -> bool | None:
    if v is None:
        return None
    if isinstance(v, bool):
        return v
    raise SchemaError(f"{ctx}: expected bool|None, got {v!r}")


def _opt_num(v: Any, ctx: str) -> int | None:
    if v is None:
        return None
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise SchemaError(f"{ctx}: expected numeric|None, got {v!r}")
    if v < 0:
        raise SchemaError(f"{ctx}: negative value {v!r}")
    return int(v)


@dataclass(frozen=True)
class LearningObject:
    """One candidate multimodal learning object (a media variant).

    ``license_status`` is a rights *observation* recorded from the provider
    record (e.g. Smithsonian ``objectRights: CC0`` + per-media ``usage.access``).
    It is data, never an inference: adapters may only copy provider-stated
    values or ``unknown``. ``affordance_facts`` records WHICH derivational
    facts back each ``True`` affordance (auditability of affordance claims).
    """

    object_id: str
    modality: str  # "3d" | "2d_image" | "2d_rubbing" | "text" | "audio"
    kb: int
    affordances: Mapping[str, bool | None]
    license_status: str  # CC0 | CC-BY-4.0 | ... | unknown
    source_record_id: str | None = None
    source_url: str | None = None
    provider: str | None = None
    affordance_facts: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.object_id:
            raise SchemaError("object_id required")
        if self.modality not in {"3d", "2d_image", "2d_rubbing", "text", "audio"}:
            raise SchemaError(f"{self.object_id}: unknown modality {self.modality!r}")
        kb = _opt_num(self.kb, f"{self.object_id}.kb")
        object.__setattr__(self, "kb", kb if kb is not None else 0)
        unknown = set(self.affordances) - AFFORDANCE_VOCAB
        if unknown:
            raise SchemaError(f"{self.object_id}: affordances outside vocabulary: {sorted(unknown)}")
        for name, value in self.affordances.items():
            if value is not None and not isinstance(value, bool):
                raise SchemaError(f"{self.object_id}.{name}: affordance must be bool|None")
        if not self.license_status:
            raise SchemaError(f"{self.object_id}: license_status required (use 'unknown')")
        if self.affordance_facts:
            extra = set(self.affordance_facts) - set(self.affordances)
            if extra:
                raise SchemaError(f"{self.object_id}: facts without affordance axes {sorted(extra)}")

    def affords(self, axis: str) -> bool | None:
        """Tri-state affordance query. KeyError on unknown axis name."""
        if axis not in AFFORDANCE_VOCAB:
            raise SchemaError(f"unknown affordance axis {axis!r}")
        return self.affordances.get(axis)


@dataclass(frozen=True)
class TaskRequirements:
    """What ONE learning task demands of a learning object.

    ``required_affordances``: every listed axis must be True (not None) on a
    feasible object. ``NOT_APPLICABLE`` axes are never required.
    """

    task_id: str
    task_type: str
    required_affordances: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.task_id:
            raise SchemaError("task_id required")
        bad = set(self.required_affordances) - AFFORDANCE_VOCAB
        if bad:
            raise SchemaError(f"{self.task_id}: required affordances outside vocabulary: {sorted(bad)}")


@dataclass(frozen=True)
class DeviceConstraints:
    """Device / bandwidth / accessibility constraints of the learner session."""

    network_kbps: int
    keyboard_only: bool = False
    screen_reader: bool = False
    webgl: bool = True
    max_payload_kb: int | None = None

    def __post_init__(self) -> None:
        if isinstance(self.network_kbps, bool) or not isinstance(self.network_kbps, (int, float)):
            raise SchemaError(f"network_kbps must be numeric, got {self.network_kbps!r}")
        if self.network_kbps < 0:
            raise SchemaError("network_kbps must be >= 0")
        object.__setattr__(self, "network_kbps", int(self.network_kbps))


@dataclass(frozen=True)
class SelectionDecision:
    """Typed selector output with an explicit failure reason axis."""

    decision: str  # "select" | "reject_missing_affordance" | "reject_rights_violation" | "reject_infeasible" | "abstain"
    selected_object_id: str | None
    missing_affordances: tuple[str, ...] = ()
    reason_codes: tuple[str, ...] = ()
    kb_used: int | None = None

    def __post_init__(self) -> None:
        allowed = {
            "select",
            "reject_missing_affordance",
            "reject_rights_violation",
            "reject_infeasible",
            "abstain",
        }
        if self.decision not in allowed:
            raise SchemaError(f"invalid decision {self.decision!r}")
        if self.decision == "select" and not self.selected_object_id:
            raise SchemaError("select requires selected_object_id")
        if self.decision != "select" and self.selected_object_id is not None:
            raise SchemaError(f"{self.decision} must not carry a selected object")
        if self.decision == "reject_missing_affordance" and not self.missing_affordances:
            raise SchemaError("reject_missing_affordance must name the missing affordances")


def parse_task(row: Mapping[str, Any]) -> TaskRequirements:
    return TaskRequirements(
        task_id=str(row["task_id"]),
        task_type=str(row.get("task_type", "unspecified")),
        required_affordances=tuple(row.get("required_affordances", ())),
    )


def parse_device(row: Mapping[str, Any]) -> DeviceConstraints:
    return DeviceConstraints(
        network_kbps=row.get("network_kbps", 0),
        keyboard_only=bool(row.get("keyboard_only", False)),
        screen_reader=bool(row.get("screen_reader", False)),
        webgl=bool(row.get("webgl", True)),
        max_payload_kb=_opt_num(row.get("max_payload_kb"), "max_payload_kb"),
    )
