"""LN-07 rubric: affordance-coverage scoring used by the blinded task rubric.

The rubric evaluates a *chosen* modality variant against the task's required
affordances (primary endpoint: objective-completion feasibility weighted by
accessibility group, spec 17_PRIMARY_METRIC). It is policy-independent: both
the proposed engine and external auditors call the same pure functions, so a
pass/fail verdict is reproducible from the case features alone.

Key mechanisms (spec 14_PROPOSED_MODEL M.1/M.3):

1. Every required affordance must be covered by the variant's affordance set.
2. A 2D raster/rubbing fallback carries the inscription affordance only if the
   variant declares it OR provides a text-equivalence transcript; an image
   that merely exists is not inscription-equivalent.
3. An audio variant covers spatial affordances only via an explicit
   description track; otherwise the spatial affordance is missing.
4. Keyboard inaccessibility and missing screen-reader semantics are
   independent hard checks (INV-LN-07-04), never inferred from each other.
"""
from __future__ import annotations

from typing import Mapping

from .dataset import ModalityCase, ModalityOption
from .labels import (
    AUDIO_ONLY_INCOMPATIBLE,
    INSCRIPTION_AFFORDANCES,
    REASON_MISSING_TRANSCRIPT,
)


def missing_affordances_for(option: ModalityOption, required: tuple[str, ...]) -> tuple[str, ...]:
    """Affordances required by the task but not afforded by ``option``."""
    have = option.affordance_set
    return tuple(a for a in required if a not in have)


def inscription_requirement_met(
    option: ModalityOption, required: tuple[str, ...], *, has_text_equivalence: bool
) -> bool:
    """True when every inscription-type requirement is genuinely afford-able.

    A required inscription affordance is satisfied when:
    - the variant itself declares the affordance, OR
    - the variant carries a text-equivalence transcript (``has_text_equivalence``).
    Image presence alone (``available`` + non-empty ``alt_text``) never counts:
    a raster fallback HAS an image yet still OMITS the inscription the task
    requires, which is precisely the mandatory counterexample (Case 1).
    """
    needed = [a for a in required if a in INSCRIPTION_AFFORDANCES]
    if not needed:
        return True
    if has_text_equivalence:
        return True
    return all(a in option.affordance_set for a in needed)


def audio_requirement_met(option: ModalityOption, required: tuple[str, ...]) -> bool:
    """True when a non-visual variant can convey every required spatial affordance.

    Audio covers spatial affordances only with an explicit description track
    (``description`` affordance) — spec LN-07-03 counterexample Case 2. A text
    variant carries spatial semantics only by declaring the affordance
    explicitly (text cannot "show" spatial relations either).
    """
    spatial_needed = [a for a in required if a in AUDIO_ONLY_INCOMPATIBLE]
    if not spatial_needed:
        return True
    if option.modality == "text":
        return all(a in option.affordance_set for a in spatial_needed)
    if "description" in option.affordance_set:
        return True
    return all(a in option.affordance_set for a in spatial_needed)


def has_text_equivalence(option: ModalityOption, case: ModalityCase) -> bool:
    """Text-equivalence availability for ``option`` in the case context.

    True when the option itself carries a transcript, or the case provides an
    available text/audio variant with a transcript that covers the same
    inscription requirements (the "route to a sufficient modality" path).
    """
    if option.transcript is True:
        return True
    if option.modality == "text":
        return True
    for other in case.options:
        if not other.available:
            continue
        if other.modality == "text" and other.available:
            return True
    return False


def rubric_score(
    case: ModalityCase, option: ModalityOption, *, transcript_required: bool | None = None
) -> Mapping[str, object]:
    """Score one (case, option) pair against the blinded task rubric.

    Returns a dict with:
        missing_affordances : required-but-unafforded affordances
        covered_affordances : required affordances the variant genuinely covers
        transcript_ok       : transcript requirement satisfied (if any)
        inscription_ok      : inscription/text-equivalence requirement satisfied
        keyboard_ok         : keyboard operability for keyboard-only learners
        screen_reader_ok    : screen-reader semantics for AT learners
        complete            : True iff every required affordance is preserved
    """
    required = case.task.required_affordances
    missing = list(missing_affordances_for(option, required))
    need_transcript = case.task.transcript_required if transcript_required is None else transcript_required

    transcript_ok = True
    if need_transcript and option.modality == "audio":
        transcript_ok = option.transcript is True

    text_equiv = has_text_equivalence(option, case)
    inscription_ok = inscription_requirement_met(
        option, required, has_text_equivalence=text_equiv
    )

    keyboard_ok = option.keyboard or not case.device.keyboard_only
    screen_reader_ok = (
        option.screen_reader_ready is True
        or option.modality == "text"
        or (option.transcript is True and option.screen_reader_ready is not False)
        # Audio with narration is semantically available to a screen-reader
        # learner when no transcript fidelity requirement applies; the
        # transcript axis is scored independently above.
        or (option.modality == "audio" and not need_transcript)
        or not case.device.screen_reader
    )

    # An inscription-required affordance that only a text-equivalence path can
    # carry is still "missing" on this variant when the variant is not itself
    # text-equivalent: flag it so the caller must route to a sufficient
    # modality instead of claiming completeness.
    for a in required:
        if a in INSCRIPTION_AFFORDANCES and a not in option.affordance_set and not text_equiv:
            if a not in missing:
                missing.append(a)

    # Description-borne affordances (e.g. narration-carried spatial semantics):
    # a *description* affordance itself is carried by prose media (audio with
    # narration, text with prose) even when the token is not declared — an
    # image cannot narrate itself. Other undeclared affordances stay missing.
    for a in required:
        if a in option.affordance_set:
            continue
        if a == "description" and option.modality in ("audio", "text"):
            continue
        if a not in missing:
            missing.append(a)

    complete = (
        not missing
        and transcript_ok
        and inscription_ok
        and keyboard_ok
        and screen_reader_ok
    )
    return {
        "missing_affordances": tuple(sorted(set(missing))),
        "covered_affordances": tuple(sorted(set(required) - set(missing))),
        "transcript_ok": transcript_ok,
        "inscription_ok": inscription_ok,
        "keyboard_ok": keyboard_ok,
        "screen_reader_ok": screen_reader_ok,
        "complete": complete,
    }


def case_feasible_with_option(case: ModalityCase, option: ModalityOption) -> bool:
    """Independent feasibility checker: can this option complete the task?"""
    if not option.available:
        return False
    if option.requires_webgl and not case.device.webgl_usable:
        return False
    if case.device.low_bandwidth and option.kb > LOW_DATA_MAX_KB:
        return False
    if case.device.keyboard_only and not option.keyboard:
        return False
    score = rubric_score(case, option)
    return bool(score["complete"])
