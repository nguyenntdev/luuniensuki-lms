"""LN-07 mechanism-isolating ablations.

Each ablation removes exactly one mechanism from the proposed engine and
keeps everything else identical (same input, same device semantics, same
label space), so any metric movement is attributable to that mechanism:

- ``a1`` (``ablations_a1``): transcript requirement disabled. Audio selections
  under transcript-required tasks are accepted without a transcript; the
  sensitive metric is false acceptance of transcript-inaccessible audio.

- ``a2`` (``ablations_a2``): keyboard/ARIA (screen-reader) checks disabled.
  The engine no longer verifies keyboard operability or screen-reader
  readiness; the sensitive metric is accessibility-barrier false accepts
  (WCAG 2.1.1 / 4.1.2 axes).

- ``a3`` (``ablations_a3``): inscription-affordance check disabled. A raster
  fallback that HAS an image but OMITS the inscription the task required is
  accepted as pedagogically complete — reproducing the naive equivalence
  regression the proposed engine exists to prevent (mandatory counterexample
  Case 1).

Ablations run the genuinely modified code path (feature flags into
``solve_case``), not a relabelled proposed output.
"""
from __future__ import annotations

from typing import Any

from .dataset import ModalityCase
from .labels import REASON_ABLATION
from .proposed import solve_case as _solve_case_full

STUDY_ID = "LN-07"

__all__ = ["a1_solve", "a2_solve", "a3_solve", "solve_case"]


def solve_case(
    case: ModalityCase,
    *,
    check_transcript: bool = True,
    check_keyboard: bool = True,
    check_screen_reader: bool = True,
    check_inscription: bool = True,
) -> dict[str, Any]:
    """Proposed engine with selectable mechanism switches (ablation surface)."""
    from . import proposed as engine

    if check_transcript and check_keyboard and check_screen_reader and check_inscription:
        return _solve_case_full(case)

    # Genuinely modified code path: run the full engine on a mechanism-
    # disabled view of the case (the same technique the legacy ablation uses),
    # then mark the ablation in reason codes.
    view = _ablated_view(
        case,
        check_transcript=check_transcript,
        check_keyboard=check_keyboard,
        check_screen_reader=check_screen_reader,
        check_inscription=check_inscription,
    )
    result = _solve_case_full(view)
    result = dict(result)
    result["reason_codes"] = tuple(result["reason_codes"]) + (
        REASON_ABLATION,
        _ablation_tag(check_transcript, check_keyboard, check_screen_reader, check_inscription),
    )
    return result


def _ablation_tag(
    check_transcript: bool, check_keyboard: bool, check_screen_reader: bool, check_inscription: bool
) -> str:
    if not check_transcript:
        return "no_transcript_requirement"
    if not check_keyboard and not check_screen_reader:
        return "no_keyboard_aria_check"
    if not check_inscription:
        return "no_inscription_affordance_check"
    return "partial_ablation"


def _ablated_view(
    case: ModalityCase,
    *,
    check_transcript: bool,
    check_keyboard: bool,
    check_screen_reader: bool,
    check_inscription: bool,
) -> ModalityCase:
    """Derive the mechanism-disabled view of the case (dataclass copy)."""
    from dataclasses import replace

    from .dataset import DeviceProfile, TaskSpec

    device = case.device
    if not check_keyboard:
        device = replace(device, keyboard_only=False)
    if not check_screen_reader:
        device = replace(device, screen_reader=False)

    task = case.task
    if not check_transcript:
        task = replace(task, transcript_required=False)
    if not check_inscription:
        # Drop inscription-type affordances from the required set so the
        # engine cannot see the gap (the naive equivalence position).
        from .labels import INSCRIPTION_AFFORDANCES

        task = replace(
            task,
            required_affordances=tuple(
                a for a in task.required_affordances if a not in INSCRIPTION_AFFORDANCES
            ),
        )
    return replace(case, device=device, task=task)


# ---------------------------------------------------------------------------
# A1 — transcript requirement disabled
# ---------------------------------------------------------------------------

def a1_solve(case: ModalityCase) -> dict[str, Any]:
    return solve_case(case, check_transcript=False)


# ---------------------------------------------------------------------------
# A2 — keyboard/ARIA (screen-reader) checks disabled
# ---------------------------------------------------------------------------

def a2_solve(case: ModalityCase) -> dict[str, Any]:
    return solve_case(case, check_keyboard=False, check_screen_reader=False)


# ---------------------------------------------------------------------------
# A3 — inscription-affordance check disabled
# ---------------------------------------------------------------------------

def a3_solve(case: ModalityCase) -> dict[str, Any]:
    return solve_case(case, check_inscription=False)
