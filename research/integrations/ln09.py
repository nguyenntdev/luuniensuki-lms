# -*- coding: utf-8 -*-
"""Callable adapter for Study LN-09 (Learning Analytics & Teacher Intervention).

Runner contract:
    def run_policy(scenario_input: dict, *, mode: str, config: dict) -> dict:
        return {
            'decision': str,
            'reason_codes': list[str],
            'policy_version': str,
            'action_proposed': bool,
            ...observables...
        }
"""
from __future__ import annotations

from typing import Any, Dict

from research.teacher_analytics.intervention_rules import (
    evaluate_ablation_rules,
    evaluate_baseline_rules,
    evaluate_intervention_rules,
)


def run_policy(
    scenario_input: Dict[str, Any],
    *,
    mode: str,
    config: Dict[str, Any],
) -> Dict[str, Any]:
    """Execute the policy adapter for Study LN-09."""
    if mode == "baseline":
        result = evaluate_baseline_rules(scenario_input, config)
    elif mode == "intervention":
        result = evaluate_intervention_rules(scenario_input, config)
    elif mode == "ablation":
        result = evaluate_ablation_rules(scenario_input, config)
    else:
        raise ValueError(f"Unknown mode: {mode}")

    return result.to_dict()
