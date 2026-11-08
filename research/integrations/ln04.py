# -*- coding: utf-8 -*-
"""Research Policy Adapter for Study LN-04 (Source-Grounded AI Scaffolding).

Callable contract:
  def run_policy(scenario_input: dict, *, mode: str, config: dict) -> dict
"""
from __future__ import annotations

from typing import Any

from backend.domain.scaffolding_policy import evaluate_scaffolding_policy
from research.baselines.strong_baselines import run_ln04_b1


def run_policy(scenario_input: dict[str, Any], *, mode: str, config: dict[str, Any]) -> dict[str, Any]:
    """Execute the scaffolding policy for study LN-04 on a synthetic scenario input.

    Modes:
      - 'baseline' / 'b0': Direct answer bot revealing historical solutions immediately,
                           with unconstrained source extrapolation.
      - 'b1': Prompted generic LLM tutor without progressive Socratic fading or injection sanitizer.
      - 'intervention': Hint budget management, progressive Socratic scaffolding
                        (observation -> evidence -> reasoning), strict source
                        verification gate, and answer leakage defense.
      - 'ablation': Direct answers without hint budget, disable refusal on unverified
                    source, or disable out-of-scope check.
    """
    cfg = config or {}
    if mode in ("b1", "baseline_b1", "prompted_llm"):
        return run_ln04_b1(scenario_input, cfg)
    if mode in ("baseline", "b0") and str(cfg.get("baseline_type", "")).lower() in ("b1", "prompted_llm", "strong"):
        return run_ln04_b1(scenario_input, cfg)
    result = evaluate_scaffolding_policy(scenario_input, mode=mode, config=cfg)
    return result.to_dict()
