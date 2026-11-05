# -*- coding: utf-8 -*-
"""Automated tests for Study LN-07 (Universal Design for Learning & Multimodal Equivalence).

Verifies invariants:
- INV-LN-07-01: Asset existence in metadata does not guarantee HTTP/runtime availability on device.
- INV-LN-07-02: Fallback is only pedagogically equivalent when it preserves necessary affordances and operations.
- INV-LN-07-03: Cropped 2D image is not a replacement for 3D/map with spatial relations if localization is required.
- INV-LN-07-04: Keyboard accessibility and audio transcript must be evaluated independently.
- INV-LN-07-05: If no valid modality exists, report unmet conditions rather than lowering learning standards.
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from research.udl.modality_equivalence import (
    BASELINE_POLICY_VERSION,
    POLICY_VERSION,
    evaluate_modality_ablation,
    evaluate_modality_baseline,
    evaluate_modality_intervention,
)
from research.integrations.ln07 import run_policy


FIXTURE_PATH = (
    Path(__file__).resolve().parents[2]
    / "LUU_NIEN_SPEC_10_STUDIES_MODULAR_FULL_2026"
    / "LUU_NIEN_SPEC_MODULAR_10_STUDIES_2026"
    / "04_FIXTURES"
    / "CONCRETE"
    / "LN-07_concrete.jsonl"
)


def _sample_scenario(
    *,
    webgl: bool = True,
    network_kbps: int = 3000,
    keyboard_only: bool = False,
    requested_modality: str | None = None,
    validate_requested_only: bool = False,
    transcript_required: bool = False,
    audio_transcript: bool = True,
    option_3d_keyboard: bool = True,
) -> dict:
    return {
        "content": {"id": "ngo-mon", "label": "Ngọ Môn", "type": "imperial-site"},
        "device": {
            "keyboard_only": keyboard_only,
            "network_kbps": network_kbps,
            "webgl": webgl,
        },
        "options": [
            {
                "affordances": ["visual_detail", "spatial_relation"],
                "kb": 1600,
                "keyboard": option_3d_keyboard,
                "modality": "3d",
                "requires_webgl": True,
            },
            {
                "affordances": ["visual_detail", "spatial_relation"],
                "kb": 90,
                "keyboard": True,
                "modality": "2d",
                "requires_webgl": False,
            },
            {
                "affordances": ["description"],
                "kb": 500,
                "keyboard": True,
                "modality": "audio",
                "transcript": audio_transcript,
            },
            {
                "affordances": ["visual_detail", "spatial_relation"],
                "kb": 5,
                "keyboard": True,
                "modality": "text",
            },
        ],
        "requested_modality": requested_modality,
        "validate_requested_only": validate_requested_only,
        "task": {
            "required_affordances": (
                ["description"] if requested_modality == "audio" else ["visual_detail", "spatial_relation"]
            ),
            "transcript_required": transcript_required,
            "type": "identify_relief_relation",
        },
    }


def test_nominal_intervention():
    scenario = _sample_scenario()
    res = evaluate_modality_intervention(scenario)
    assert res.decision == "choose_feasible_modality"
    assert res.task_feasible is True
    assert res.fallback_failure is False
    assert res.missing_affordance_count == 0
    assert "affordances_satisfied" in res.reason_codes
    assert res.policy_version == POLICY_VERSION


def test_no_webgl_accessible_fallback_intervention():
    scenario = _sample_scenario(webgl=False)
    res = evaluate_modality_intervention(scenario)
    assert res.decision == "choose_accessible_fallback"
    assert res.task_feasible is True
    assert res.fallback_failure is False
    assert res.missing_affordance_count == 0
    assert "webgl_unavailable" in res.reason_codes
    assert "accessible_2d_fallback_selected" in res.reason_codes


def test_missing_transcript_rejected_intervention():
    scenario = _sample_scenario(
        requested_modality="audio",
        transcript_required=True,
        audio_transcript=False,
    )
    res = evaluate_modality_intervention(scenario)
    assert res.decision == "reject_audio_equivalence"
    assert res.task_feasible is False
    assert res.fallback_failure is True
    assert "missing_transcript" in res.reason_codes
    assert "accessibility_violation" in res.reason_codes


def test_low_bandwidth_fallback_intervention():
    scenario = _sample_scenario(network_kbps=80)
    res = evaluate_modality_intervention(scenario)
    assert res.decision == "choose_low_data_fallback"
    assert res.task_feasible is True
    assert res.fallback_failure is False
    assert res.missing_affordance_count == 0
    assert "bandwidth_constrained_3d" in res.reason_codes
    assert "low_data_fallback_selected" in res.reason_codes


def test_keyboard_inaccessible_rejected_intervention():
    scenario = _sample_scenario(
        keyboard_only=True,
        requested_modality="3d",
        validate_requested_only=True,
        option_3d_keyboard=False,
    )
    res = evaluate_modality_intervention(scenario)
    assert res.decision == "reject_inaccessible_option"
    assert res.task_feasible is False
    assert res.fallback_failure is True
    assert "keyboard_inaccessible" in res.reason_codes


def test_baseline_naive_behavior():
    # Nominal
    nom = _sample_scenario()
    res_nom = evaluate_modality_baseline(nom)
    assert res_nom.decision == "choose_feasible_modality"
    assert res_nom.task_feasible is True
    assert res_nom.policy_version == BASELINE_POLICY_VERSION

    # No WebGL: Baseline blindly attempts 3D -> task fails
    no_webgl = _sample_scenario(webgl=False)
    res_nowebgl = evaluate_modality_baseline(no_webgl)
    assert res_nowebgl.decision == "choose_feasible_modality"
    assert res_nowebgl.task_feasible is False
    assert res_nowebgl.fallback_failure is True

    # Low bandwidth: Baseline blindly attempts 3D -> download times out
    low_bw = _sample_scenario(network_kbps=80)
    res_lowbw = evaluate_modality_baseline(low_bw)
    assert res_lowbw.decision == "choose_feasible_modality"
    assert res_lowbw.task_feasible is False
    assert res_lowbw.fallback_failure is True


def test_ablation_modes():
    scenario_no_webgl = _sample_scenario(webgl=False)

    # url_existence_only
    abl_url = evaluate_modality_ablation(
        scenario_no_webgl, config={"ablation_type": "url_existence_only"}
    )
    assert abl_url.decision == "choose_feasible_modality"

    # disable_accessibility
    scenario_kb = _sample_scenario(
        keyboard_only=True,
        requested_modality="3d",
        validate_requested_only=True,
        option_3d_keyboard=False,
    )
    abl_acc = evaluate_modality_ablation(
        scenario_kb, config={"ablation_type": "disable_accessibility"}
    )
    # With accessibility disabled, it chooses 3D instead of rejecting
    assert abl_acc.decision == "choose_feasible_modality"


def test_run_policy_adapter_contract():
    scenario = _sample_scenario()
    out = run_policy(scenario, mode="intervention", config={})
    assert isinstance(out, dict)
    assert out["decision"] == "choose_feasible_modality"
    assert isinstance(out["reason_codes"], list)
    assert out["policy_version"] == POLICY_VERSION
    assert isinstance(out["task_feasible"], bool)
    assert out["task_feasible"] is True
    assert "fallback_failure" in out
    assert "missing_affordance_count" in out


def test_concrete_fixture_conformance():
    """Verify that intervention matches 100% of all 720 scenarios in LN-07 concrete fixtures."""
    if not FIXTURE_PATH.exists():
        pytest.skip(f"Concrete fixtures not found at {FIXTURE_PATH}")

    total = 0
    matched = 0
    with open(FIXTURE_PATH, encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            total += 1
            res = run_policy(row["input"], mode="intervention", config={})
            expected = row["oracle"]["expected_decision"]
            assert (
                res["decision"] == expected
            ), f"Mismatch on {row['case_id']} ({row['fault_id']}): got {res['decision']}, expected {expected}"
            assert isinstance(res["task_feasible"], bool)
            matched += 1

    assert total == 720
    assert matched == 720
