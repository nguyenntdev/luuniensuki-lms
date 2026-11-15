"""Accessibility-axis tests: screen-reader missing transcript and keyboard-
inaccessible modalities (INV-LN-07-04 — the two axes are independent).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from tests.research_v2.ln07.ln07_helpers import (  # noqa: E402
    make_case,
    policy_predict,
    policy_solve,
)


def screen_reader_no_transcript_case(case_id: str = "sr-no-transcript"):
    """Screen-reader learner; audio lacks a transcript but carries a
    description track affording the spatial requirement.

    The ONLY screen-reader-opaque failure axis is the missing transcript:
    when the transcript requirement is disabled (ablation A1) the audio path
    becomes acceptable; with the requirement active it must be rejected or
    routed to a text-equivalent variant (none exists that affords the spatial
    requirement here, so the audio transcript gate decides).
    """
    options = [
        {
            "id": "a_3d",
            "modality": "3d",
            "kb": 1850,
            "keyboard": True,
            "requires_webgl": True,
            "available": True,
            "affordances": ["visual_detail", "spatial_relation", "relief_depth"],
        },
        {
            "id": "a_audio",
            "modality": "audio",
            "kb": 480,
            "keyboard": True,
            "requires_webgl": False,
            "available": True,
            "transcript": False,  # transcript MISSING (only failure axis)
            "screen_reader_ready": False,
            "affordances": ["visual_detail", "spatial_relation", "description"],
        },
        {
            "id": "a_text",
            "modality": "text",
            "kb": 10,
            "keyboard": True,
            "requires_webgl": False,
            "available": True,
            "screen_reader_ready": True,
            "affordances": ["visual_detail"],  # cannot afford spatial relation
        },
    ]
    return make_case(
        required=["visual_detail", "spatial_relation"],
        screen_reader=True,
        transcript_required=True,
        options=options,
        case_id=case_id,
    )


def keyboard_only_non_keyboard_case(case_id: str = "kbd-inaccessible"):
    """Keyboard-only learner; every available option needs mouse interaction."""
    options = [
        {
            "id": "k_3d",
            "modality": "3d",
            "kb": 1850,
            "keyboard": False,  # mouse-only navigation
            "requires_webgl": True,
            "available": True,
            "affordances": ["visual_detail", "spatial_relation", "relief_depth"],
        },
        {
            "id": "k_static",
            "modality": "static_image",
            "kb": 320,
            "keyboard": False,  # hotspot interaction needs a mouse
            "requires_webgl": False,
            "available": True,
            "alt_text": "Ảnh tĩnh",
            "affordances": ["visual_detail", "spatial_relation"],
        },
    ]
    return make_case(
        required=["visual_detail", "spatial_relation"],
        keyboard_only=True,
        options=options,
        case_id=case_id,
    )


class TestScreenReaderTranscriptFidelity:
    def test_screen_reader_missing_transcript_not_accepted(self):
        result = policy_solve("proposed", screen_reader_no_transcript_case())
        # The transcript-bearing accessible path is required; audio without a
        # transcript must not be silently accepted.
        assert result["decision"] != "choose_accessible_audio_text" or (
            result["selected_option_id"] != "a_audio"
        )
        # With no sufficient accessible variant the engine rejects with a
        # typed reason (access axis or transcript fidelity, never a guess).
        assert result["decision"] in (
            "reject_inaccessible_option",
            "reject_audio_equivalence",
            "reject_missing_affordance",
        )
        assert result["task_feasible"] is False

    def test_audio_without_transcript_routed_to_sufficient_text(self):
        case = screen_reader_no_transcript_case()
        # Give the text variant the full requirement set: the transcript gap
        # on audio must route to the sufficient text path.
        from dataclasses import replace

        text_opt = next(o for o in case.options if o.modality == "text")
        text_ok = replace(text_opt, affordances=("visual_detail", "spatial_relation"))
        case2 = replace(
            case,
            options=tuple(
                text_ok if o.modality == "text" else o for o in case.options
            ),
        )
        result = policy_solve("proposed", case2)
        assert result["decision"] == "choose_accessible_audio_text"
        assert result["selected_option_id"] == "a_text"

    def test_a1_ablation_accepts_missing_transcript(self):
        result = policy_solve("ablations_a1", screen_reader_no_transcript_case())
        # Transcript requirement disabled -> audio accepted without transcript.
        assert result["decision"] != "reject_missing_affordance"
        assert "ablation" in result["reason_codes"]
        assert "no_transcript_requirement" in result["reason_codes"]

    def test_ablation_diverges_from_proposed_on_transcript_axis(self):
        case = screen_reader_no_transcript_case()
        proposed = policy_solve("proposed", case)
        a1 = policy_solve("ablations_a1", case)
        assert proposed["decision"] != a1["decision"] or (
            "no_transcript_requirement" in a1["reason_codes"]
            and "no_transcript_requirement" not in proposed["reason_codes"]
        )


class TestKeyboardInaccessibility:
    def test_keyboard_only_with_mouse_only_options_rejected(self):
        result = policy_solve("proposed", keyboard_only_non_keyboard_case())
        assert result["decision"] == "reject_inaccessible_option"
        assert result["task_feasible"] is False
        assert "keyboard_inaccessible" in result["reason_codes"]
        assert "missing_accessible_alternative" in result["reason_codes"]

    def test_a2_ablation_ignores_keyboard_barrier(self):
        result = policy_solve("ablations_a2", keyboard_only_non_keyboard_case())
        # Keyboard/ARIA checks disabled -> the 3D option is served.
        assert result["decision"] == "choose_feasible_modality"
        assert "no_keyboard_aria_check" in result["reason_codes"]

    def test_screen_reader_and_keyboard_are_independent_axes(self):
        # Keyboard failure must be reported as keyboard_inaccessible, NOT as a
        # screen-reader problem, when the screen reader is off.
        case = keyboard_only_non_keyboard_case()
        assert case.device.screen_reader is False
        result = policy_solve("proposed", case)
        assert "screen_reader_inaccessible" not in result["reason_codes"]
        assert "keyboard_inaccessible" in result["reason_codes"]


class TestContractAbiAccessibility:
    def test_ablation_aliases_run_through_contract_abi(self):
        from research_v2.contracts.types import StudyPrediction

        from tests.research_v2.ln07.ln07_helpers import make_input

        preds = policy_predict("ablations_a2", [make_input(keyboard_only_non_keyboard_case())])
        assert len(preds) == 1
        assert isinstance(preds[0], StudyPrediction)
        # a2 disabled the keyboard axis, so the native label surfaces; the
        # label must still be inside the validated native space.
        assert preds[0].decision == "choose_feasible_modality"
