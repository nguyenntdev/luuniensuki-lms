"""LN-03 Research Policy Integration Adapter.

Provides the standardized `run_policy` entrypoint for benchmark runners
and evaluation suites:
  run_policy(scenario_input: dict, *, mode: str, config: dict) -> dict
"""

from __future__ import annotations

from typing import Any, Dict

from research.spaced_learning.dual_mode_policy import (
    schedule_baseline,
    schedule_dual_mode_intervention,
    schedule_ablation,
)


def run_policy(
    scenario_input: Dict[str, Any],
    *,
    mode: str,
    config: Dict[str, Any],
) -> Dict[str, Any]:
    """Execute dual-mode spaced learning policy.

    Args:
        scenario_input: Structured pedagogical scenario dictionary (case_id, learner, review_card, etc.)
        mode: Policy mode ('baseline', 'intervention', 'ablation')
        config: Extra hyperparameters or ablation specifications

    Returns:
        Result dictionary containing decision, reason_codes, policy_version,
        and domain observables (generative_assigned, review_burden, task_type_coverage).
    """
    if mode == "baseline":
        return schedule_baseline(scenario_input, config)
    elif mode == "intervention":
        return schedule_dual_mode_intervention(scenario_input, config)
    elif mode == "ablation":
        ablation_type = (
            config.get("ablation_type")
            or config.get("variant")
            or config.get("ablation")
            or ("retrieval_only" if config.get("retrieval_only") else None)
            or ("no_burden_cap" if config.get("no_burden_cap") else None)
            or "generic_fsrs"
        )
        return schedule_ablation(scenario_input, ablation_type=ablation_type, config=config)
    else:
        raise ValueError(f"Unknown mode '{mode}'. Expected 'baseline', 'intervention', or 'ablation'.")
