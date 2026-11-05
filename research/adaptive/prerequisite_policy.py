# -*- coding: utf-8 -*-
"""Prerequisite-Aware Adaptive Learning Policy Engine (Study LN-02).

Design Blueprint Implementation:
- Evaluates four-dimensional historical competencies (S1: Spatial, S2: Temporal, S3: Evidence, S4: Argumentation).
- Strict verification of hard prerequisite thresholds before proposing tasks.
- Acyclicity validation on dependency graphs (reject_cycle).
- Domain range validation [0, 1] on observed scores and mastery vectors (reject_invalid_score).
- Abstention mechanism for missing competency dimensions (abstain_insufficient_data, INV-LN-02-01).
- Provides deterministic pure policy evaluation for baseline, intervention, and ablation modes.
"""
from __future__ import annotations

from typing import Any, Optional

from backend.domain.competency_prerequisites import (
    CompetencyDimension,
    RecommendationDecision,
    ReasonCode,
    POLICY_VERSION,
    detect_dependency_cycle,
    validate_score_value,
    validate_all_scenario_scores,
    calculate_competency_coverage,
    evaluate_intervention,
    evaluate_baseline,
    evaluate_ablation,
)


class PrerequisitePolicy:
    """Adaptive learning policy evaluator supporting research benchmark modes."""

    version: str = POLICY_VERSION

    @classmethod
    def evaluate(
        cls,
        scenario_input: dict[str, Any],
        *,
        mode: str = "intervention",
        config: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Evaluate a pedagogical scenario under the specified policy mode.

        Args:
            scenario_input: Structured pedagogical scenario input.
            mode: Policy evaluation mode ('intervention', 'baseline', 'ablation').
            config: Optional configuration overrides.

        Returns:
            Dictionary containing decision, reason_codes, policy_version,
            and research observables (prerequisite_violated, competency_coverage, etc.).
        """
        cfg = config or {}
        if mode == "intervention":
            return evaluate_intervention(scenario_input, config=cfg)
        elif mode == "baseline":
            return evaluate_baseline(scenario_input, config=cfg)
        elif mode == "ablation":
            return evaluate_ablation(scenario_input, config=cfg)
        else:
            raise ValueError(f"Unknown policy evaluation mode: '{mode}'. Must be one of: 'intervention', 'baseline', 'ablation'.")


def evaluate_policy(
    scenario_input: dict[str, Any],
    *,
    mode: str = "intervention",
    config: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Pure functional entrypoint for evaluating prerequisite policies."""
    return PrerequisitePolicy.evaluate(scenario_input, mode=mode, config=config)
