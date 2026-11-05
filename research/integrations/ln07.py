# -*- coding: utf-8 -*-
"""Callable adapter for Study LN-07 (UDL and Multimodal Equivalence).

Runner contract:
    def run_policy(scenario_input: dict, *, mode: str, config: dict) -> dict:
        return {
            'decision': str,
            'reason_codes': list[str],
            'policy_version': str,
            'task_feasible': bool,
            'fallback_failure': bool,
            'missing_affordance_count': int,
            ...observables...
        }
"""
from __future__ import annotations

from typing import Any, Dict

from research.udl.modality_equivalence import (
    evaluate_modality_ablation,
    evaluate_modality_baseline,
    evaluate_modality_intervention,
)


def run_policy(
    scenario_input: Dict[str, Any],
    *,
    mode: str,
    config: Dict[str, Any],
) -> Dict[str, Any]:
    """Execute the policy adapter for Study LN-07."""
    if mode == "baseline":
        result = evaluate_modality_baseline(scenario_input, config)
    elif mode == "intervention":
        result = evaluate_modality_intervention(scenario_input, config)
    elif mode == "ablation":
        result = evaluate_modality_ablation(scenario_input, config)
    else:
        raise ValueError(f"Unknown mode: {mode}")

    return result.to_dict()
