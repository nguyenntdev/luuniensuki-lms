# -*- coding: utf-8 -*-
"""Research benchmark adapter for LN-02 (Prerequisite-Aware Adaptive Learning).

Callable adapter contract:
    def run_policy(scenario_input: dict, *, mode: str, config: dict) -> dict

Adheres strictly to research guidelines:
- Never routes by case_id / fault_id.
- Never inspects oracle or expected decisions.
- Evaluates real pedagogical logic based on competency graph, mastery vectors,
  and score validity constraints.
"""
from __future__ import annotations

from typing import Any

from research.adaptive.prerequisite_policy import PrerequisitePolicy
from research.baselines.strong_baselines import run_ln02_b1


def run_policy(
    scenario_input: dict[str, Any],
    *,
    mode: str,
    config: dict[str, Any],
) -> dict[str, Any]:
    """Execute the LN-02 prerequisite policy on scenario input.

    Args:
        scenario_input: Pedagogical scenario dictionary containing graph_edges,
                        mastery, score_observed, learner, and target_task.
        mode: Policy mode ('baseline', 'b1', 'intervention', 'ablation').
        config: Configuration dictionary for policy options or ablation variants.

    Returns:
        Result dictionary containing:
            - decision (str)
            - reason_codes (list[str])
            - policy_version (str)
            - prerequisite_violated (bool)
            - competency_coverage (float)
            - unjustified_recommendation (bool)
            - research_only (bool)
    """
    cfg = config or {}
    if mode in ("b1", "baseline_b1", "irt"):
        return run_ln02_b1(scenario_input, cfg)
    if mode in ("baseline", "b0") and str(cfg.get("baseline_type", "")).lower() in ("b1", "irt", "strong"):
        return run_ln02_b1(scenario_input, cfg)
    return PrerequisitePolicy.evaluate(scenario_input, mode=mode, config=cfg)
