# -*- coding: utf-8 -*-
"""Self-Regulated Learning (SRL) Project State Machine (Study LN-10).

Provides the state machine engine governing project lifecycle transitions for
the Hue Heritage Urban Project (Chuyên đề Đô thị di sản Huế).
"""
from __future__ import annotations

from typing import Any, Optional

from backend.domain.reflection_cycle import (
    DecisionCode,
    ProjectStage,
    ReasonCode,
    SRLPhase,
    TransitionAction,
    evaluate_srl_cycle,
)


class SRLProjectStateMachine:
    """State machine executing self-regulated project transitions.
    
    Supports:
    - baseline: Naive linear checklist advancing stages unconditionally.
    - intervention: Cyclical SRL state machine enforcing reflection,
      optimistic concurrency, and student ownership.
    - ablation: Selectively disabled components (reflection loop, concurrency, ownership).
    """

    def __init__(self, default_policy_version: str = "study-ln10-v1") -> None:
        self.default_policy_version = default_policy_version

    def evaluate_transition(
        self,
        scenario_input: dict[str, Any],
        *,
        mode: str = "intervention",
        config: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Evaluate a project transition request under specified mode."""
        cfg = config or {}

        if mode in ("baseline", "b0"):
            # Naive linear checklist: advances regardless of reflection, ownership, or concurrency
            project = scenario_input.get("project", {}) if isinstance(scenario_input, dict) else {}
            return {
                "decision": DecisionCode.ALLOW_AUTHORIZED_TRANSITION.value,
                "reason_codes": [ReasonCode.BASELINE_AUTO_ADVANCE.value],
                "policy_version": "ln10-baseline-v1",
                "transition_applied": True,
                "conflict_detected": False,
                "reflection_completed": bool(project.get("reflection_completed", False)),
                "ownership_verified": False,
                "research_only": True,
            }

        elif mode in ("baseline_progress_tracker", "b1", "baseline_b1"):
            # B1: Timestamp-based progress tracker without reflection verification
            # Enforces ownership and concurrency, but skips reflection gate and revision rationale
            res = evaluate_srl_cycle(
                scenario_input,
                enforce_ownership=True,
                enforce_concurrency=True,
                enforce_reflection_gate=False,
                enforce_rationale=False,
                policy_version="ln10-baseline-b1-v1",
            )
            return {
                "decision": res.decision.value,
                "reason_codes": res.reason_codes,
                "policy_version": res.policy_version,
                "transition_applied": res.transition_applied,
                "conflict_detected": res.conflict_detected,
                "reflection_completed": res.reflection_completed,
                "ownership_verified": res.ownership_verified,
                "explanation": res.explanation,
                "research_only": True,
            }

        elif mode == "intervention":
            res = evaluate_srl_cycle(
                scenario_input,
                enforce_ownership=True,
                enforce_concurrency=True,
                enforce_reflection_gate=True,
                enforce_rationale=True,
                policy_version="ln10-intervention-srl-v1",
            )
            return {
                "decision": res.decision.value,
                "reason_codes": res.reason_codes,
                "policy_version": res.policy_version,
                "transition_applied": res.transition_applied,
                "conflict_detected": res.conflict_detected,
                "reflection_completed": res.reflection_completed,
                "ownership_verified": res.ownership_verified,
                "explanation": res.explanation,
                "research_only": True,
            }

        elif mode == "ablation":
            # Configurable ablations:
            # 1. disable_reflection (aliases: no_reflection_gate, free_navigation): drops reflection gate and revision rationale
            # 2. disable_concurrency (alias: no_concurrency): drops optimistic concurrency checking
            # 3. disable_ownership (alias: skip_forethought): drops learner ownership verification
            ablation_type = str(cfg.get("ablation_type") or cfg.get("variant") or cfg.get("label") or "")

            disable_concurrency = bool(
                cfg.get("disable_concurrency", False)
                or cfg.get("no_concurrency", False)
                or ablation_type in ("disable_concurrency", "no_concurrency")
            )
            disable_ownership = bool(
                cfg.get("disable_ownership", False)
                or ablation_type == "disable_ownership"
            )
            # Forethought rationale skipping
            skip_forethought = bool(
                cfg.get("skip_forethought", False)
                or ablation_type == "skip_forethought"
            )
            # Reflection gate skipping
            no_reflection_gate = bool(
                cfg.get("no_reflection_gate", False)
                or ablation_type == "no_reflection_gate"
            )
            # Free navigation skips both reflection and stage gates
            free_navigation = bool(
                cfg.get("free_navigation", False)
                or ablation_type == "free_navigation"
            )

            # Master reflection disable flag
            disable_reflection = bool(
                cfg.get("disable_reflection", False)
                or ablation_type == "disable_reflection"
                or free_navigation
                or (not (disable_concurrency or disable_ownership or skip_forethought or no_reflection_gate))
            )

            res = evaluate_srl_cycle(
                scenario_input,
                enforce_ownership=not disable_ownership,
                enforce_concurrency=not disable_concurrency,
                enforce_reflection_gate=not (disable_reflection or no_reflection_gate or free_navigation),
                enforce_rationale=not (disable_reflection or skip_forethought or free_navigation),
                policy_version="ln10-ablation-v1",
            )
            return {
                "decision": res.decision.value,
                "reason_codes": res.reason_codes,
                "policy_version": res.policy_version,
                "transition_applied": res.transition_applied,
                "conflict_detected": res.conflict_detected,
                "reflection_completed": res.reflection_completed,
                "ownership_verified": res.ownership_verified,
                "explanation": res.explanation,
                "research_only": True,
            }

        else:
            raise ValueError(f"Unknown mode: {mode}")
