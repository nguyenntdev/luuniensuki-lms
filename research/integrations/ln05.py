"""Callable adapter for Study LN-05.

Runner contract:
    def run_policy(scenario_input: dict, *, mode: str, config: dict) -> dict:
        return {
            'decision': str,
            'reason_codes': list[str],
            'policy_version': str,
            'badge_awarded': bool,
            ...observables...
        }
"""

from typing import Any, Dict

from research.baselines.strong_baselines import run_ln05_b1
from research.gamification.mastery_reward_policy import (
    evaluate_mastery_reward_ablation,
    evaluate_mastery_reward_baseline,
    evaluate_mastery_reward_intervention,
)


def run_policy(
    scenario_input: Dict[str, Any],
    *,
    mode: str,
    config: Dict[str, Any],
) -> Dict[str, Any]:
    """Execute the policy adapter for Study LN-05."""
    cfg = config or {}
    if mode in ("b1", "baseline_b1", "streak"):
        return run_ln05_b1(scenario_input, cfg)
    if mode in ("baseline", "b0"):
        if str(cfg.get("baseline_type", "")).lower() in ("b1", "streak", "strong"):
            return run_ln05_b1(scenario_input, cfg)
        result = evaluate_mastery_reward_baseline(scenario_input, cfg)
    elif mode == "intervention":
        result = evaluate_mastery_reward_intervention(scenario_input, cfg)
    elif mode == "ablation":
        result = evaluate_mastery_reward_ablation(scenario_input, cfg)
    else:
        raise ValueError(f"Unknown mode: {mode}")

    return result.to_dict()
