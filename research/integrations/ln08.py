# -*- coding: utf-8 -*-
"""Research integration adapter for Study LN-08 (Diagnostic Feedback).

Connects the pedagogical scenario corpus to the domain diagnostic engine.
Never routes by case_id/fault_id and never reads the oracle file.
"""
from __future__ import annotations

from typing import Any

from research.feedback.diagnostic_feedback import (
    evaluate_ablation,
    evaluate_baseline,
    evaluate_intervention,
)


def run_policy(
    scenario_input: dict[str, Any],
    *,
    mode: str,
    config: dict[str, Any],
) -> dict[str, Any]:
    """Execute historical diagnostic policy for a scenario input.

    Modes:
    - 'baseline': Naive keyword matcher blind to negation and source attribution.
    - 'intervention': Full historical misconception taxonomy diagnostic pipeline.
    - 'ablation': Component-isolated variants (keyword_only, disable_negation, disable_source_link).
    """
    if not isinstance(scenario_input, dict):
        raise TypeError("scenario_input must be a dict")

    cfg = config or {}

    if mode == "baseline":
        return evaluate_baseline(scenario_input, cfg)
    elif mode == "intervention":
        return evaluate_intervention(scenario_input, cfg)
    elif mode == "ablation":
        return evaluate_ablation(scenario_input, cfg)
    else:
        raise ValueError(f"Unsupported mode: {mode}")
