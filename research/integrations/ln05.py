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
    if mode == "baseline":
        result = evaluate_mastery_reward_baseline(scenario_input, config)
    elif mode == "intervention":
        result = evaluate_mastery_reward_intervention(scenario_input, config)
    elif mode == "ablation":
        result = evaluate_mastery_reward_ablation(scenario_input, config)
    else:
        raise ValueError(f"Unknown mode: {mode}")

    return result.to_dict()
