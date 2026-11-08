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

from research.baselines.strong_baselines import run_ln09_b1
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
    cfg = config or {}
    if mode in ("b1", "baseline_b1", "ema"):
        return run_ln09_b1(scenario_input, cfg)
    if mode in ("baseline", "b0"):
        if str(cfg.get("baseline_type", "")).lower() in ("b1", "ema", "strong"):
            return run_ln09_b1(scenario_input, cfg)
        result = evaluate_baseline_rules(scenario_input, cfg)
    elif mode == "intervention":
        result = evaluate_intervention_rules(scenario_input, cfg)
    elif mode == "ablation":
        result = evaluate_ablation_rules(scenario_input, cfg)
    else:
        raise ValueError(f"Unknown mode: {mode}")

    return result.to_dict()
