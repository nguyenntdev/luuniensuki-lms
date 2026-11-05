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

        if mode == "baseline":
            # Naive linear checklist: advances regardless of reflection, ownership, or concurrency
            project = scenario_input.get("project", {})
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
            # 1. disable_reflection: drops reflection gate and revision rationale
            # 2. disable_concurrency: drops optimistic concurrency checking
            # 3. disable_ownership: drops learner ownership verification
            disable_concurrency = bool(cfg.get("disable_concurrency", False))
            disable_ownership = bool(cfg.get("disable_ownership", False))
            # If neither concurrency nor ownership is disabled, default ablation is disable_reflection
            disable_reflection = bool(
                cfg.get("disable_reflection", not (disable_concurrency or disable_ownership))
            )

            res = evaluate_srl_cycle(
                scenario_input,
                enforce_ownership=not disable_ownership,
                enforce_concurrency=not disable_concurrency,
                enforce_reflection_gate=not disable_reflection,
                enforce_rationale=not disable_reflection,
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
