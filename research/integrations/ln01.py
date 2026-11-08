"""Callable adapter for Study LN-01 (Spiral Curriculum Progression: Liên thông học liệu xoắn ốc GDĐP khối 10–11–12).

Theory: Spiral curriculum; constructive alignment; historical reasoning.
Runner contract:
    def run_policy(scenario_input: dict, *, mode: str, config: dict) -> dict:
        return {
            'decision': str,
            'reason_codes': list[str],
            'policy_version': str,
            'progression_valid': bool,
            ...observables...
        }

Modes:
    - 'baseline': Simple flat/content-only progression (ignores cognitive jumps, cycles, anchors).
    - 'intervention': Strict spiral progression verifying DAG cycle avoidance, grade monotonicity,
      regulatory curriculum anchor linkage, and cognitive complexity sequence.
    - 'ablation': Configurable ablation allowing specific checks to be bypassed.
"""

from __future__ import annotations

from typing import Any, Dict

from research.spiral.progression_graph import (
    evaluate_spiral_progression_ablation,
    evaluate_spiral_progression_baseline,
    evaluate_spiral_progression_intervention,
    evaluate_spiral_progression_topological_baseline,
)


def run_policy(
    scenario_input: Dict[str, Any],
    *,
    mode: str,
    config: Dict[str, Any],
) -> Dict[str, Any]:
    """Execute the policy adapter for Study LN-01."""
    if mode in ("baseline", "b0"):
        baseline_type = str(config.get("baseline_type", "")).lower()
        if baseline_type in ("topological", "b1", "topological_sort"):
            result = evaluate_spiral_progression_topological_baseline(scenario_input, config)
        else:
            result = evaluate_spiral_progression_baseline(scenario_input, config)
    elif mode in ("topological_baseline", "b1"):
        result = evaluate_spiral_progression_topological_baseline(scenario_input, config)
    elif mode == "intervention":
        result = evaluate_spiral_progression_intervention(scenario_input, config)
    elif mode == "ablation":
        result = evaluate_spiral_progression_ablation(scenario_input, config)
    else:
        raise ValueError(f"Unknown mode for LN-01 policy adapter: {mode}")

    return result.to_dict()
