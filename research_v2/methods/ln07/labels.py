"""LN-07 decision labels and typed validation.

Native decision labels follow the observed legacy UDL policy engine
(``research/udl/modality_equivalence.py`` / ``research/integrations/ln07.py``),
from which the T3 gold oracle (``DESIGN_SPEC_EMPIRICAL_HOLDOUT`` basis) was
generated:

- ``choose_feasible_modality``        : nominal device; primary modality covers
  the required affordances.
- ``choose_accessible_fallback``      : WebGL unavailable/lost; accessible 2D
  rubbing fallback preserves the required affordances.
- ``choose_low_data_fallback``        : bandwidth below the 3D threshold; the
  low-data 2D path preserves the required affordances.
- ``choose_accessible_audio_text``    : screen reader / keyboard-only learner;
  accessible audio/text path with transcript equivalence.
- ``choose_curated_archive_fallback`` : 3D asset unavailable; archival rubbing
  fallback preserves the required affordances.

Rejection labels come from the same legacy guard surface plus the frozen
contract space; they stay distinct by design (LN-07-04 forbids collapsing
rejection families into one generic reject):

- ``reject_inaccessible_option``  : legacy guard - keyboard / screen-reader
  barrier with no accessible alternative (WCAG 2.1.1 / 1.1.1 axis).
- ``reject_audio_equivalence``    : legacy guard - transcript fidelity failure
  on an audio path (WCAG 1.2.1 axis).
- ``reject_missing_affordance``   : cognitive-affordance failure - the chosen
  modality omits a pedagogically required affordance (e.g. a raster fallback
  that has an image but omits the inscription the task requires).

The frozen contract space (``research_v2.contracts.label_space.LN07_DECISIONS``)
declares ``complete_multimodal`` / ``fallback_acceptable`` /
``reject_inaccessible`` / ``reject_missing_affordance``. Native labels are
validated strictly against the native space (unknown labels raise typed
errors); the contract mapping is diagnostic and never silently rewrites a
decision, mirroring the LN-03/LN-04 convention.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from research_v2.contracts.label_space import (
    LN07_DECISIONS as CONTRACT_DECISIONS,
    LabelSpaceError,
)

STUDY_ID = "LN-07"


class Decision(str, Enum):
    CHOOSE_FEASIBLE_MODALITY = "choose_feasible_modality"
    CHOOSE_ACCESSIBLE_FALLBACK = "choose_accessible_fallback"
    CHOOSE_LOW_DATA_FALLBACK = "choose_low_data_fallback"
    CHOOSE_ACCESSIBLE_AUDIO_TEXT = "choose_accessible_audio_text"
    CHOOSE_CURATED_ARCHIVE_FALLBACK = "choose_curated_archive_fallback"
    REJECT_INACCESSIBLE_OPTION = "reject_inaccessible_option"
    REJECT_AUDIO_EQUIVALENCE = "reject_audio_equivalence"
    REJECT_MISSING_AFFORDANCE = "reject_missing_affordance"


NATIVE_DECISIONS: frozenset[str] = frozenset(d.value for d in Decision)

#: Public alias (matrix/runbook tooling refers to the legal label vocabulary).
DECISION_LABELS: frozenset[str] = NATIVE_DECISIONS

#: Contract label space frozen in research_v2.contracts.label_space.
CONTRACT_ONLY_DECISIONS: frozenset[str] = CONTRACT_DECISIONS

#: Diagnostic mapping native -> contract space (NOT applied automatically).
NATIVE_TO_CONTRACT: dict[str, str] = {
    "choose_feasible_modality": "complete_multimodal",
    "choose_accessible_fallback": "fallback_acceptable",
    "choose_low_data_fallback": "fallback_acceptable",
    "choose_accessible_audio_text": "fallback_acceptable",
    "choose_curated_archive_fallback": "fallback_acceptable",
    "reject_inaccessible_option": "reject_inaccessible",
    "reject_audio_equivalence": "reject_missing_affordance",
    "reject_missing_affordance": "reject_missing_affordance",
}


class LabelError(ValueError):
    """Raised when a native policy output cannot be mapped to a legal label."""


@dataclass(frozen=True)
class DecisionInfo:
    decision: str
    selected_modality: str
    fallback_type: str


INFO_BY_DECISION: dict[str, DecisionInfo] = {
    "choose_feasible_modality": DecisionInfo("choose_feasible_modality", "3d", "none"),
    "choose_accessible_fallback": DecisionInfo("choose_accessible_fallback", "2d", "rubbing_2d"),
    "choose_low_data_fallback": DecisionInfo(
        "choose_low_data_fallback", "2d", "low_data_rubbing_2d"
    ),
    "choose_accessible_audio_text": DecisionInfo(
        "choose_accessible_audio_text", "audio_text", "accessible_transcript"
    ),
    "choose_curated_archive_fallback": DecisionInfo(
        "choose_curated_archive_fallback", "2d", "curated_rubbing_archive"
    ),
}

# Reason codes emitted by policies, grouped for the error analysis ledger.
REASON_NOMINAL = "nominal"
REASON_AFFORDANCE_PRESERVED = "pedagogical_affordance_preserved"
REASON_MISSING_AFFORDANCE = "missing_required_affordance"
REASON_MISSING_INSCRIPTION = "missing_inscription_affordance"
REASON_MISSING_TRANSCRIPT = "missing_transcript"
REASON_KEYBOARD_INACCESSIBLE = "keyboard_inaccessible"
REASON_SCREEN_READER_INACCESSIBLE = "screen_reader_inaccessible"
REASON_WEBGL_UNAVAILABLE = "webgl_unavailable"
REASON_BANDWIDTH_CONSTRAINED = "bandwidth_constrained"
REASON_ASSET_UNAVAILABLE = "asset_unavailable"
REASON_NO_SUFFICIENT_MODALITY = "no_sufficient_modality"
REASON_ROUTE_TO_SUFFICIENT = "routed_to_sufficient_modality"
REASON_BASELINE_URL_ONLY = "baseline_url_presence_only"
REASON_BASELINE_NAIVE = "naive_selection"
REASON_BASELINE_STATIC_FALLBACK = "baseline_static_image_fallback"
REASON_ABLATION = "ablation"

#: Bandwidth threshold (kbps) below which heavy 3D assets are infeasible
#: (mirrors the observed engine constant).
BANDWIDTH_3D_MIN_KBPS = 500

#: Maximum asset size (KB) served on a low-bandwidth connection.
LOW_DATA_MAX_KB = 100

#: Affordance tokens that count as inscription/text-content affordances.
#: A raster fallback that merely shows the image does NOT carry these; it must
#: either afford the inscription explicitly or provide a transcript/text
#: equivalence (spec LN-07-14 mechanism 1, mandatory counterexample Case 1).
INSCRIPTION_AFFORDANCES: frozenset[str] = frozenset(
    {"inscription", "inscription_text", "text_content", "han_nom_text", "glyph_reading"}
)

#: Affordances an audio-only modality cannot convey without a description
#: track (spec LN-07-03 counterexample Case 2).
AUDIO_ONLY_INCOMPATIBLE: frozenset[str] = frozenset(
    {"spatial_relation", "relief_depth", "spatial_shape", "spatial_orientation"}
)


def validate_native_decision(decision: str) -> str:
    """Validate against the native engine space; typed failure on unknown."""
    if decision not in NATIVE_DECISIONS:
        raise LabelError(
            f"{STUDY_ID}: decision {decision!r} not in native label space "
            f"{sorted(NATIVE_DECISIONS)}"
        )
    return decision


def validate_contract_decision(decision: str) -> str:
    """Validate against the frozen V2 contract space (diagnostic use)."""
    if decision not in CONTRACT_DECISIONS:
        raise LabelSpaceError(
            f"{STUDY_ID}: decision {decision!r} not in contract label space "
            f"{sorted(CONTRACT_DECISIONS)}"
        )
    return decision


def to_contract_decision(native: str) -> str:
    """Deterministic native -> contract mapping (diagnostic; total mapping)."""
    try:
        return NATIVE_TO_CONTRACT[native]
    except KeyError as exc:
        raise LabelError(
            f"{STUDY_ID}: no contract mapping for native decision {native!r}"
        ) from exc


def map_decision(native: str) -> str:
    """Strict native mapping used by every policy (unknown => typed error)."""
    return validate_native_decision(native)


def build_prediction(
    *,
    case_id: str,
    decision: str,
    reason_codes: tuple[str, ...] = (),
    evidence_ids: tuple[str, ...] = (),
    score: float | None = None,
):
    """Construct a contract-valid StudyPrediction with a validated label."""
    from research_v2.contracts.types import StudyPrediction

    label = map_decision(decision)
    return StudyPrediction(
        study_id=STUDY_ID,
        case_id=case_id,
        decision=label,
        score=score,
        reason_codes=tuple(reason_codes),
        evidence_ids=tuple(evidence_ids),
    )
