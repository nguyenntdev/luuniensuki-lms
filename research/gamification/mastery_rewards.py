"""Research Gamification - Mastery Rewards (Study LN-05 alias module).

Re-exports core policy definitions and functions.
"""

from research.gamification.mastery_reward_policy import (
    BASELINE_POLICY_VERSION,
    POLICY_VERSION,
    PolicyEvaluationResult,
    evaluate_mastery_reward_ablation,
    evaluate_mastery_reward_baseline,
    evaluate_mastery_reward_intervention,
)

__all__ = [
    "POLICY_VERSION",
    "BASELINE_POLICY_VERSION",
    "PolicyEvaluationResult",
    "evaluate_mastery_reward_baseline",
    "evaluate_mastery_reward_intervention",
    "evaluate_mastery_reward_ablation",
]
