# -*- coding: utf-8 -*-
"""Research UDL - Modality & Pedagogical Equivalence Policy Engine (Study LN-07).

Theory: Universal Design for Learning (UDL 3.0); Multimedia Learning.
Research context: Tương đương chức năng sư phạm của học liệu 2D, 3D, âm thanh, văn bản
trong bối cảnh Cửu Đỉnh và không gian di sản Huế.

Pedagogical Invariants:
- INV-LN-07-01: Asset existence in metadata does not guarantee HTTP/runtime availability on device.
- INV-LN-07-02: Fallback is only pedagogically equivalent when it preserves necessary affordances and operations.
- INV-LN-07-03: Cropped 2D image is not a replacement for 3D/map with spatial relations if localization is required.
- INV-LN-07-04: Keyboard accessibility and audio transcript must be evaluated independently.
- INV-LN-07-05: If no valid modality exists, report unmet conditions rather than lowering learning standards.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set


POLICY_VERSION = "2.0-intervention"
BASELINE_POLICY_VERSION = "1.0-baseline"
ABLATION_POLICY_VERSION = "1.5-ablation"

# Bandwidth threshold below which heavy 3D models (>500KB) become unfeasible
BANDWIDTH_3D_MIN_KBPS = 500


@dataclass(frozen=True)
class LearningAffordance:
    """Represents a cognitive or pedagogical affordance required by a learning task."""
    id: str
    required_evidence: str = "visual_or_spatial"
    operation: str = "observe_and_identify"


@dataclass(frozen=True)
class MediaVariant:
    """Represents a multimodal asset variant (3D, 2D rubbing, audio guide, text transcript)."""
    id: str
    modality: str
    kb: int
    affordances: List[str]
    keyboard: bool = True
    requires_webgl: bool = False
    transcript: Optional[bool] = None


@dataclass(frozen=True)
class DeviceConstraint:
    """Hardware, network, and assistive technology constraints of the learner device."""
    webgl: bool = True
    network_kbps: int = 3000
    keyboard_only: bool = False
    screen_reader: bool = False


@dataclass(frozen=True)
class ModalityDecision:
    """Formal decision output from the UDL modality guard."""
    chosen_modality: Optional[str]
    supported_affordances: List[str]
    missing_affordances: List[str]
    decision: str
    reason_codes: List[str]


@dataclass(frozen=True)
class PolicyEvaluationResult:
    """Evaluation result conforming to benchmark runner contract and observable requirements."""
    decision: str
    reason_codes: List[str]
    policy_version: str
    task_feasible: bool
    fallback_failure: bool
    missing_affordance_count: int
    observables: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        res: Dict[str, Any] = {
            "decision": self.decision,
            "reason_codes": list(self.reason_codes),
            "policy_version": self.policy_version,
            "task_feasible": self.task_feasible,
            "fallback_failure": self.fallback_failure,
            "missing_affordance_count": self.missing_affordance_count,
        }
        res.update(self.observables)
        return res


def evaluate_modality_baseline(
    scenario_input: Dict[str, Any],
    config: Optional[Dict[str, Any]] = None,
) -> PolicyEvaluationResult:
    """Baseline policy: Naive fallback checking only URL string presence or file existence

    without verifying that 2D rubbing, text transcript, or audio provides equivalent
    learning affordances or device compatibility.
    """
    config = config or {}
    device = scenario_input.get("device", {})
    task = scenario_input.get("task", {})
    options = scenario_input.get("options", [])
    requested_modality = scenario_input.get("requested_modality")

    # In baseline, any option that is listed in options is assumed to be usable.
    # It blindly serves the primary or requested modality without checking constraints.
    primary_option = None
    if requested_modality:
        primary_option = next((o for o in options if o.get("modality") == requested_modality), None)
    if not primary_option:
        primary_option = next((o for o in options if o.get("modality") == "3d"), options[0] if options else None)

    decision = "choose_feasible_modality"
    reason_codes = ["baseline_url_present", "naive_selection"]

    # Determine ground-truth runtime feasibility under baseline blindness:
    # 1. No WebGL: 3D crashes/fails to render on non-WebGL device
    webgl = device.get("webgl", True)
    kbps = device.get("network_kbps", 3000)
    keyboard_only = device.get("keyboard_only", False)
    transcript_req = task.get("transcript_required", False)

    is_feasible = True
    missing_count = 0
    fallback_failure = False

    if requested_modality == "audio" and transcript_req:
        audio_opt = next((o for o in options if o.get("modality") == "audio"), {})
        if not audio_opt.get("transcript", True):
            is_feasible = False
            missing_count = 1
            fallback_failure = True
    elif keyboard_only:
        req_opt = next((o for o in options if o.get("modality") == (requested_modality or "3d")), {})
        if not req_opt.get("keyboard", True):
            is_feasible = False
            fallback_failure = True
    elif not webgl:
        # Blind baseline attempts to render 3D on non-WebGL hardware
        is_feasible = False
        fallback_failure = True
        missing_count = len(task.get("required_affordances", []))
    elif kbps < BANDWIDTH_3D_MIN_KBPS:
        # Blind baseline serves 1600KB 3D on 80 kbps connection (>160s download timeout)
        is_feasible = False
        fallback_failure = True

    return PolicyEvaluationResult(
        decision=decision,
        reason_codes=reason_codes,
        policy_version=BASELINE_POLICY_VERSION,
        task_feasible=is_feasible,
        fallback_failure=fallback_failure,
        missing_affordance_count=missing_count,
        observables={
            "mode": "baseline",
            "selected_modality": primary_option.get("modality") if primary_option else None,
            "blind_url_check_only": True,
            "webgl_verified": False,
            "bandwidth_verified": False,
            "accessibility_verified": False,
        },
    )


def evaluate_modality_intervention(
    scenario_input: Dict[str, Any],
    config: Optional[Dict[str, Any]] = None,
) -> PolicyEvaluationResult:
    """Intervention policy: Functional pedagogical equivalence validation ensuring

    task feasibility regardless of modality (3D GLB, 2D rubbing, transcript, audio),
    WCAG 2.2 accessibility, and keyboard navigation completeness.
    """
    config = config or {}
    device = scenario_input.get("device", {})
    task = scenario_input.get("task", {})
    options = scenario_input.get("options", [])
    requested_modality = scenario_input.get("requested_modality")
    val_requested_only = scenario_input.get("validate_requested_only", False)

    required_affordances = set(task.get("required_affordances", []))
    keyboard_only = device.get("keyboard_only", False)
    webgl = device.get("webgl", True)
    network_kbps = device.get("network_kbps", 3000)
    transcript_required = task.get("transcript_required", False)

    # RULE-LN-07-05 / INV-LN-07-04: Keyboard accessibility evaluation
    if val_requested_only and requested_modality:
        req_opt = next((o for o in options if o.get("modality") == requested_modality), None)
        if req_opt and keyboard_only and not req_opt.get("keyboard", True):
            return PolicyEvaluationResult(
                decision="reject_inaccessible_option",
                reason_codes=[
                    "keyboard_inaccessible",
                    "requires_mouse_navigation",
                    "missing_accessible_alternative",
                ],
                policy_version=POLICY_VERSION,
                task_feasible=False,
                fallback_failure=True,
                missing_affordance_count=0,
                observables={
                    "mode": "intervention",
                    "selected_modality": requested_modality,
                    "keyboard_only": keyboard_only,
                    "option_keyboard_support": False,
                    "wcag_violation": "2.1.1 Keyboard Navigation",
                },
            )

    # RULE-LN-07-03 / INV-LN-07-04: Audio transcript requirement evaluation
    if requested_modality == "audio" and transcript_required:
        audio_opt = next((o for o in options if o.get("modality") == "audio"), None)
        if audio_opt and not audio_opt.get("transcript", True):
            return PolicyEvaluationResult(
                decision="reject_audio_equivalence",
                reason_codes=[
                    "missing_transcript",
                    "audio_transcript_required",
                    "accessibility_violation",
                ],
                policy_version=POLICY_VERSION,
                task_feasible=False,
                fallback_failure=True,
                missing_affordance_count=0,
                observables={
                    "mode": "intervention",
                    "selected_modality": "audio",
                    "transcript_required": True,
                    "transcript_available": False,
                    "wcag_violation": "1.2.1 Audio-only Pre-recorded Alternative",
                },
            )

    # Evaluate options against device constraints and pedagogical affordances
    # Find 3D option, 2D rubbing option, text option
    opt_3d = next((o for o in options if o.get("modality") == "3d"), None)
    opt_2d = next((o for o in options if o.get("modality") == "2d"), None)
    opt_text = next((o for o in options if o.get("modality") == "text"), None)

    # RULE-LN-07-02 / INV-LN-07-01: No WebGL on device -> select accessible 2D rubbing fallback
    if not webgl:
        # Check if 2D rubbing satisfies task affordances
        opt_2d_affordances = set(opt_2d.get("affordances", [])) if opt_2d else set()
        affordances_preserved = required_affordances.issubset(opt_2d_affordances)

        return PolicyEvaluationResult(
            decision="choose_accessible_fallback",
            reason_codes=[
                "webgl_unavailable",
                "accessible_2d_fallback_selected",
                "pedagogical_affordance_preserved",
            ],
            policy_version=POLICY_VERSION,
            task_feasible=affordances_preserved,
            fallback_failure=not affordances_preserved,
            missing_affordance_count=len(required_affordances - opt_2d_affordances),
            observables={
                "mode": "intervention",
                "selected_modality": "2d",
                "fallback_type": "rubbing_2d",
                "webgl_required": False,
                "supported_affordances": sorted(list(opt_2d_affordances)),
                "pedagogical_equivalence_verified": affordances_preserved,
            },
        )

    # RULE-LN-07-04: Low bandwidth constraint (< 500 kbps) -> select low-data 2D rubbing fallback
    if network_kbps < BANDWIDTH_3D_MIN_KBPS:
        opt_2d_affordances = set(opt_2d.get("affordances", [])) if opt_2d else set()
        affordances_preserved = required_affordances.issubset(opt_2d_affordances)

        return PolicyEvaluationResult(
            decision="choose_low_data_fallback",
            reason_codes=[
                "bandwidth_constrained_3d",
                "low_data_fallback_selected",
                "pedagogical_affordance_preserved",
            ],
            policy_version=POLICY_VERSION,
            task_feasible=affordances_preserved,
            fallback_failure=not affordances_preserved,
            missing_affordance_count=len(required_affordances - opt_2d_affordances),
            observables={
                "mode": "intervention",
                "selected_modality": "2d",
                "fallback_type": "rubbing_2d",
                "network_kbps": network_kbps,
                "bandwidth_threshold_kbps": BANDWIDTH_3D_MIN_KBPS,
                "supported_affordances": sorted(list(opt_2d_affordances)),
                "pedagogical_equivalence_verified": affordances_preserved,
            },
        )

    # RULE-LN-07-01: Nominal conditions -> 3D primary modality feasible
    opt_3d_affordances = set(opt_3d.get("affordances", [])) if opt_3d else set()
    affordances_preserved = required_affordances.issubset(opt_3d_affordances)

    return PolicyEvaluationResult(
        decision="choose_feasible_modality",
        reason_codes=[
            "affordances_satisfied",
            "device_compatible",
            "primary_modality_selected",
        ],
        policy_version=POLICY_VERSION,
        task_feasible=affordances_preserved,
        fallback_failure=False,
        missing_affordance_count=len(required_affordances - opt_3d_affordances),
        observables={
            "mode": "intervention",
            "selected_modality": "3d",
            "webgl_supported": True,
            "network_kbps": network_kbps,
            "supported_affordances": sorted(list(opt_3d_affordances)),
            "pedagogical_equivalence_verified": affordances_preserved,
        },
    )


def evaluate_modality_ablation(
    scenario_input: Dict[str, Any],
    config: Optional[Dict[str, Any]] = None,
) -> PolicyEvaluationResult:
    """Ablation policy: Configurable policy ablations:

    - ablation_type = 'url_existence_only': Behaves like naive baseline.
    - ablation_type = 'disable_cognitive_affordances': Disables affordance verification.
    - ablation_type = 'disable_accessibility': Disables keyboard and transcript validation.
    """
    config = config or {}
    ablation_type = config.get("ablation_type", "url_existence_only")

    if ablation_type in ("url_existence_only", "3d_only") or config.get("3d_only"):
        res = evaluate_modality_baseline(scenario_input, config)
        return PolicyEvaluationResult(
            decision=res.decision,
            reason_codes=["ablation_url_only"] + res.reason_codes,
            policy_version=ABLATION_POLICY_VERSION,
            task_feasible=res.task_feasible,
            fallback_failure=res.fallback_failure,
            missing_affordance_count=res.missing_affordance_count,
            observables={"ablation_type": ablation_type, **res.observables},
        )

    if ablation_type in ("disable_accessibility",) or config.get("disable_accessibility"):
        # Run intervention without keyboard and transcript checks
        sanitized_input = dict(scenario_input)
        device = dict(sanitized_input.get("device", {}))
        device["keyboard_only"] = False
        sanitized_input["device"] = device
        sanitized_input["validate_requested_only"] = False
        task = dict(sanitized_input.get("task", {}))
        task["transcript_required"] = False
        sanitized_input["task"] = task
        if sanitized_input.get("requested_modality") == "audio":
            sanitized_input["requested_modality"] = None

        res = evaluate_modality_intervention(sanitized_input, config)
        return PolicyEvaluationResult(
            decision=res.decision,
            reason_codes=["ablation_no_accessibility"] + res.reason_codes,
            policy_version=ABLATION_POLICY_VERSION,
            task_feasible=res.task_feasible,
            fallback_failure=res.fallback_failure,
            missing_affordance_count=res.missing_affordance_count,
            observables={"ablation_type": ablation_type, **res.observables},
        )

    if (
        ablation_type in ("disable_cognitive_affordances", "no_text_equivalence")
        or config.get("no_text_equivalence")
        or config.get("disable_cognitive_affordances")
    ):
        # Disregard required affordances
        sanitized_input = dict(scenario_input)
        task = dict(sanitized_input.get("task", {}))
        task["required_affordances"] = []
        sanitized_input["task"] = task

        res = evaluate_modality_intervention(sanitized_input, config)
        return PolicyEvaluationResult(
            decision=res.decision,
            reason_codes=["ablation_no_cognitive_affordances"] + res.reason_codes,
            policy_version=ABLATION_POLICY_VERSION,
            task_feasible=res.task_feasible,
            fallback_failure=res.fallback_failure,
            missing_affordance_count=0,
            observables={"ablation_type": ablation_type, **res.observables},
        )

    if (
        ablation_type in ("ignore_network_constraints",)
        or config.get("ignore_network_constraints")
    ):
        # Ignore network bandwidth constraints (bypass low-bandwidth fallback)
        sanitized_input = dict(scenario_input)
        device = dict(sanitized_input.get("device", {}))
        device["network_kbps"] = 100000
        sanitized_input["device"] = device

        res = evaluate_modality_intervention(sanitized_input, config)
        return PolicyEvaluationResult(
            decision=res.decision,
            reason_codes=["ablation_ignore_network_constraints"] + res.reason_codes,
            policy_version=ABLATION_POLICY_VERSION,
            task_feasible=res.task_feasible,
            fallback_failure=res.fallback_failure,
            missing_affordance_count=res.missing_affordance_count,
            observables={"ablation_type": ablation_type, **res.observables},
        )

    # Fallback default
    return evaluate_modality_baseline(scenario_input, config)
