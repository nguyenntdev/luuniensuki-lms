"""LN-07 proposed policy — UDL affordance-preservation modality engine.

Core mechanism (spec 14_PROPOSED_MODEL, mechanism M "formal coverage of
instructional affordances across representations"):

1. **Hard accessibility checks** (INV-LN-07-04, independent axes):
   - keyboard-only learners need keyboard-operable variants;
   - screen-reader learners need screen-reader-ready semantics with
     transcript/text equivalence.
   A modality that fails the learner's hard accessibility axis is
   ``reject_inaccessible_option`` unless another available variant passes.

2. **Device/resource feasibility**: WebGL requirement vs device support and
   bandwidth budget (heavy 3D assets are infeasible below
   ``BANDWIDTH_3D_MIN_KBPS`` kbps / large payloads).

3. **Affordance coverage with inscription fidelity** (the study's mandatory
   mechanism): a candidate is pedagogically equivalent only if it affords
   EVERY required affordance. A 2D raster/rubbing fallback that has an image
   but OMITS the inscription the task requires is NOT equivalent — the engine
   flags the missing affordance and, when a sufficient modality exists (e.g.
   structured text with the inscription transcription), routes to it;
   otherwise it rejects with ``reject_missing_affordance``. Image existence
   (``available`` + ``alt_text``) never substitutes for the inscription
   affordance.

4. **Transcript fidelity for audio**: an audio selection under a
   ``transcript_required`` task must carry a transcript (WCAG 1.2.1), else
   ``reject_audio_equivalence`` unless a text-equivalent variant exists.

5. **Deterministic routing**: among feasible candidates the engine picks the
   stratum-appropriate decision label with lexicographic option-id
   tie-breaking. No randomness is consumed; identical inputs produce
   identical predictions for any seed (the ``seed`` config is accepted for
   interface compatibility only).

All outputs are deterministic and oracle-free: no gold material
(``expected_decision``, ``fault_id``, ``oracle``) is read at inference time.
"""
from __future__ import annotations

from typing import Any, Mapping

from .dataset import DatasetError, ModalityCase, ModalityOption, from_input
from .labels import (
    INSCRIPTION_AFFORDANCES,
    REASON_AFFORDANCE_PRESERVED,
    REASON_ASSET_UNAVAILABLE,
    REASON_BANDWIDTH_CONSTRAINED,
    REASON_KEYBOARD_INACCESSIBLE,
    REASON_MISSING_AFFORDANCE,
    REASON_MISSING_INSCRIPTION,
    REASON_MISSING_TRANSCRIPT,
    REASON_NOMINAL,
    REASON_NO_SUFFICIENT_MODALITY,
    REASON_ROUTE_TO_SUFFICIENT,
    REASON_SCREEN_READER_INACCESSIBLE,
    REASON_WEBGL_UNAVAILABLE,
    build_prediction,
)
from .rubric import audio_requirement_met, rubric_score

STUDY_ID = "LN-07"
METHOD_ID = "proposed"
METHOD_VERSION = "ln07-proposed-v2.0"

__all__ = [
    "STUDY_ID",
    "METHOD_ID",
    "METHOD_VERSION",
    "solve_case",
    "predict_one",
    "predict_batch",
]


def _has_transcript(o: ModalityOption) -> bool:
    return o.transcript is True


def _screen_reader_ok(o: ModalityOption, case: ModalityCase | None = None) -> bool:
    """Semantic availability to a screen-reader learner.

    Text is natively readable; explicit screen-reader-ready flags and
    transcript-bearing audio are accessible. Narrated audio without a
    transcript is accessible only when no transcript fidelity requirement
    applies (the transcript axis is scored separately).
    """
    if o.screen_reader_ready is True:
        return True
    if o.modality == "text":
        return True
    if o.transcript is True and o.screen_reader_ready is not False:
        return True
    if (
        o.modality == "audio"
        and (case is None or not case.task.transcript_required)
    ):
        return True
    return False


def _covers_required(o: ModalityOption, case: ModalityCase) -> bool:
    """Strict affordance coverage including inscription fidelity.

    Inscription-type required affordances must be declared by the variant
    itself (or via a text-equivalence transcript on the variant); image
    presence never substitutes.
    """
    required = case.task.required_affordances
    if o.modality == "audio" and not audio_requirement_met(o, required):
        return False
    score = rubric_score(case, o)
    return bool(score["complete"])


def _route_for(
    decision: str,
    case: ModalityCase,
    chosen: ModalityOption | None,
    *,
    reasons: tuple[str, ...],
    missing: tuple[str, ...] = (),
) -> dict[str, Any]:
    return {
        "decision": decision,
        "reason_codes": reasons,
        "selected_option_id": chosen.id if chosen else "",
        "selected_modality": chosen.modality if chosen else "",
        "fallback_type": _fallback_type(decision),
        "missing_affordances": tuple(sorted(set(missing))),
        "task_feasible": chosen is not None,
    }


def _fallback_type(decision: str) -> str:
    return {
        "choose_feasible_modality": "none",
        "choose_accessible_fallback": "rubbing_2d",
        "choose_low_data_fallback": "low_data_rubbing_2d",
        "choose_accessible_audio_text": "accessible_transcript",
        "choose_curated_archive_fallback": "curated_rubbing_archive",
    }.get(decision, "none")


def _inscription_needed(case: ModalityCase) -> bool:
    return any(a in INSCRIPTION_AFFORDANCES for a in case.task.required_affordances)


def solve_case(case: ModalityCase) -> dict[str, Any]:
    """Deterministic decision procedure for one validated case.

    Strict precedence (mirrors the observed engine's rule order so the gold
    strata remain identifiable, with the affordance-fidelity gate applied to
    every branch):
      1. screen-reader / keyboard accessibility (independent axes)
      2. transcript fidelity for audio requests under transcript_required
      3. 3D availability (missing/unavailable asset -> archive fallback)
      4. WebGL support (unavailable/lost -> accessible 2D rubbing fallback)
      5. bandwidth budget (below threshold -> low-data fallback)
      6. nominal: primary 3D modality if affordance-complete
    """
    device = case.device
    task = case.task
    required = task.required_affordances

    # ---- 3a. Screen reader active: need accessible audio/text path --------
    if device.screen_reader:
        cands = [
            o
            for o in case.options
            if o.available and _screen_reader_ok(o, case) and _covers_required(o, case)
        ]
        cands.sort(key=lambda o: o.id)
        if cands:
            chosen = cands[0]
            return _route_for(
                "choose_accessible_audio_text",
                case,
                chosen,
                reasons=(
                    "screen_reader_active",
                    "accessible_audio_text_selected",
                    REASON_AFFORDANCE_PRESERVED,
                ),
            )
        # No sufficient modality: distinguish missing affordance vs access axis
        any_accessible = [
            o
            for o in case.options
            if o.available
            and _screen_reader_ok(o, case)
            and (
                o.affordance_set & set(required)
                or "description" in o.affordance_set
            )
        ]
        missing = tuple(required)
        if any_accessible:
            # Screen-reader-capable candidates exist but none affords the
            # required affordance set -> cognitive gap, not a pure access
            # barrier.
            return _route_for(
                "reject_missing_affordance",
                case,
                None,
                reasons=(
                    REASON_MISSING_AFFORDANCE,
                    REASON_NO_SUFFICIENT_MODALITY,
                    "missing:" + ",".join(sorted(set(missing))),
                ),
                missing=missing,
            )
        return _route_for(
            "reject_inaccessible_option",
            case,
            None,
            reasons=(
                REASON_SCREEN_READER_INACCESSIBLE,
                "no_accessible_alternative",
            ),
            missing=missing,
        )

    # ---- 3b. Keyboard-only learner: variant must be keyboard operable -----
    if device.keyboard_only:
        cands = [o for o in case.options if o.available and o.keyboard and _covers_required(o, case)]
        cands.sort(key=lambda o: o.id)
        if cands:
            chosen = cands[0]
            # Stratum label: audio/text accessible path when visual modalities
            # are keyboard-blocked, else the nominal label.
            return _route_for(
                "choose_accessible_audio_text",
                case,
                chosen,
                reasons=(
                    "keyboard_only_learner",
                    "keyboard_accessible_path_selected",
                    REASON_AFFORDANCE_PRESERVED,
                ),
            )
        blocked = [o for o in case.options if o.available and not o.keyboard]
        if blocked:
            return _route_for(
                "reject_inaccessible_option",
                case,
                None,
                reasons=(
                    REASON_KEYBOARD_INACCESSIBLE,
                    "requires_mouse_navigation",
                    "missing_accessible_alternative",
                ),
            )

    # ---- 2. Transcript fidelity gate (applies to every audio selection) ---
    audio_opts = [o for o in case.options if o.modality == "audio" and o.available]
    if task.transcript_required and audio_opts and all(not _has_transcript(o) for o in audio_opts):
        text_opt = case.first_available("text")
        if text_opt is None or not _covers_required(text_opt, case):
            return _route_for(
                "reject_audio_equivalence",
                case,
                None,
                reasons=(
                    REASON_MISSING_TRANSCRIPT,
                    "audio_transcript_required",
                    "accessibility_violation",
                ),
            )
        return _route_for(
            "choose_accessible_audio_text",
            case,
            text_opt,
            reasons=(
                REASON_MISSING_TRANSCRIPT,
                REASON_ROUTE_TO_SUFFICIENT,
                REASON_AFFORDANCE_PRESERVED,
            ),
        )

    # ---- 3. 3D availability ----------------------------------------------
    opt_3d = case.first_available("3d")
    if opt_3d is None:
        return _archive_or_reject(case)

    # ---- 4. WebGL support --------------------------------------------------
    if not device.webgl_usable or opt_3d.requires_webgl and not device.webgl_usable:
        return _rubbing_or_reject(
            case, "choose_accessible_fallback", (REASON_WEBGL_UNAVAILABLE,)
        )

    # ---- 5. Bandwidth budget ----------------------------------------------
    if device.low_bandwidth or opt_3d.kb * 8 > device.network_kbps * 1024:
        return _rubbing_or_reject(
            case, "choose_low_data_fallback", (REASON_BANDWIDTH_CONSTRAINED,)
        )

    # ---- 6. Nominal: primary modality must still afford everything --------
    if _covers_required(opt_3d, case):
        return _route_for(
            "choose_feasible_modality",
            case,
            opt_3d,
            reasons=(REASON_NOMINAL, REASON_AFFORDANCE_PRESERVED),
        )
    missing = tuple(
        a
        for a in required
        if a not in opt_3d.affordance_set
    )
    return _route_to_sufficient(case, opt_3d, missing)


def _archive_or_reject(case: ModalityCase) -> dict[str, Any]:
    """3D asset unavailable -> archival rubbing fallback (RULE-LN-07-07)."""
    rubbing = next((o for o in case.options if o.is_rubbing and o.available), None)
    if rubbing is not None and _covers_required(rubbing, case):
        return _route_for(
            "choose_curated_archive_fallback",
            case,
            rubbing,
            reasons=(
                REASON_ASSET_UNAVAILABLE,
                "archival_rubbing_fallback_selected",
                REASON_AFFORDANCE_PRESERVED,
            ),
        )
    chosen = rubbing
    missing: tuple[str, ...] = ()
    if chosen is None:
        chosen = next((o for o in case.options if o.modality == "2d" and o.available), None)
    if chosen is None:
        return _route_for(
            "reject_missing_affordance",
            case,
            None,
            reasons=(
                REASON_ASSET_UNAVAILABLE,
                REASON_NO_SUFFICIENT_MODALITY,
            ),
            missing=tuple(case.task.required_affordances),
        )
    missing = tuple(
        a for a in case.task.required_affordances if a not in chosen.affordance_set
    )
    return _route_to_sufficient(case, chosen, missing)


def _rubbing_or_reject(
    case: ModalityCase, decision: str, prior_reasons: tuple[str, ...]
) -> dict[str, Any]:
    """2D rubbing fallback for WebGL/bandwidth strata, with fidelity gate.

    The fallback must carry the required affordances INCLUDING inscription
    equivalence. A raster that has an image but omits the inscription the
    task requires is not complete: the engine routes to a sufficient
    modality (text with transcript) when one exists, else rejects with the
    missing-affordance label.
    """
    rubbing = next((o for o in case.options if o.is_rubbing and o.available), None)
    if rubbing is None:
        rubbing = next(
            (o for o in case.options if o.modality == "2d" and o.available), None
        )
    if rubbing is not None and _covers_required(rubbing, case):
        return _route_for(
            decision,
            case,
            rubbing,
            reasons=prior_reasons
            + ("accessible_2d_fallback_selected", REASON_AFFORDANCE_PRESERVED),
        )
    if rubbing is None:
        return _route_for(
            "reject_missing_affordance",
            case,
            None,
            reasons=prior_reasons + (REASON_NO_SUFFICIENT_MODALITY,),
            missing=tuple(case.task.required_affordances),
        )
    missing = tuple(
        a for a in case.task.required_affordances if a not in rubbing.affordance_set
    )
    routed = _route_to_sufficient(case, rubbing, missing)
    # ensure the stratum decision label is preserved when routing succeeds
    if routed["decision"].startswith("choose_"):
        routed = dict(routed)
        routed["decision"] = decision
        routed["reason_codes"] = tuple(routed["reason_codes"]) + (REASON_ROUTE_TO_SUFFICIENT,)
    return routed


def _route_to_sufficient(
    case: ModalityCase, failed: ModalityOption, missing: tuple[str, ...]
) -> dict[str, Any]:
    """Flag the missing affordance; route to a sufficient modality or reject.

    This is the mandatory counterexample path (spec LN-07-03 Case 1): the
    raster fallback HAS an image but OMITS the inscription the task requires.
    The engine never treats it as pedagogically complete.
    """
    inscription_gap = any(a in INSCRIPTION_AFFORDANCES for a in missing)
    reasons = [REASON_MISSING_AFFORDANCE]
    if inscription_gap:
        reasons.append(REASON_MISSING_INSCRIPTION)
    reasons.append("missing:" + ",".join(sorted(set(missing))))

    # Sufficient modality search: available variants that afford everything.
    sufficient = [o for o in case.options if o.available and _covers_required(o, case)]
    sufficient.sort(key=lambda o: o.id)
    if sufficient:
        chosen = sufficient[0]
        decision = "choose_accessible_audio_text"
        if chosen.modality == "text":
            decision = "choose_accessible_audio_text"
        return _route_for(
            decision,
            case,
            chosen,
            reasons=tuple(reasons) + (REASON_ROUTE_TO_SUFFICIENT, REASON_AFFORDANCE_PRESERVED),
            missing=missing,
        )
    return _route_for(
        "reject_missing_affordance",
        case,
        None,
        reasons=tuple(reasons) + (REASON_NO_SUFFICIENT_MODALITY,),
        missing=missing,
    )


# ---------------------------------------------------------------------------
# Contract ABI
# ---------------------------------------------------------------------------

def predict_one(inp: Any, config: Mapping[str, Any] | None = None) -> Any:
    from research_v2.contracts.types import StudyInput

    if not isinstance(inp, StudyInput):
        raise DatasetError(f"predict_one expects StudyInput, got {type(inp).__name__}")
    case = from_input(inp)
    result = solve_case(case)
    return build_prediction(
        case_id=inp.case_id,
        decision=result["decision"],
        reason_codes=result["reason_codes"],
        evidence_ids=(result["selected_option_id"],) if result["selected_option_id"] else (),
        score=1.0 if result["task_feasible"] else 0.0,
    )


def predict_batch(inputs: list, config: dict | None = None) -> list:
    """Contract ABI: deterministic LN-07 decisions for a batch of inputs.

    Any invalid row rejects the whole batch with its location (no guessed
    fallback), per the study specification.
    """
    del config  # deterministic policy; seed accepted for interface parity only
    out = []
    for i, inp in enumerate(inputs):
        try:
            out.append(predict_one(inp))
        except DatasetError:
            raise
        except Exception as exc:  # surface typed failure with batch location
            raise DatasetError(f"input[{i}] case {getattr(inp, 'case_id', '?')!r}: {exc}") from exc
    return out
