# -*- coding: utf-8 -*-
"""Adapter for Study LN-06: Cognitively Constrained Heritage Trails.

Callable contract:
    def run_policy(scenario_input: dict, *, mode: str, config: dict) -> dict
"""
from __future__ import annotations

from typing import Any

from backend.domain.heritage_checkpoints import HeritageStop
from research.heritage_trails.cognitive_route import (
    evaluate_route_baseline,
    evaluate_route_intervention,
)


def run_policy(
    scenario_input: dict[str, Any],
    *,
    mode: str,
    config: dict[str, Any],
) -> dict[str, Any]:
    """Execute LN-06 trail policy.

    Args:
        scenario_input: Pedagogical scenario containing stops, available_stops,
            target_outcomes, time_budget_minutes, checkpoint_claim_verified.
        mode: 'baseline', 'intervention', or 'ablation'.
        config: Optional configuration dictionary.

    Returns:
        dict with decision, reason_codes, policy_version, and observables:
            prerequisite_violation_count (int, REQUIRED by derive_study_metrics)
            outcome_coverage (float)
            route_cost (int)
            unreachable_checkpoint_rate (float)
    """
    raw_stops = scenario_input.get("stops", [])
    stops = [HeritageStop.from_dict(s) for s in raw_stops]
    available_stops = scenario_input.get("available_stops", [])
    target_outcomes = scenario_input.get("target_outcomes", [])
    time_budget_minutes = scenario_input.get("time_budget_minutes", 60)
    checkpoint_claim_verified = scenario_input.get("checkpoint_claim_verified", True)

    if mode == "baseline":
        plan = evaluate_route_baseline(
            stops=stops,
            available_stops=available_stops,
            target_outcomes=target_outcomes,
            time_budget_minutes=time_budget_minutes,
            checkpoint_claim_verified=checkpoint_claim_verified,
        )
    elif mode == "intervention":
        plan = evaluate_route_intervention(
            stops=stops,
            available_stops=available_stops,
            target_outcomes=target_outcomes,
            time_budget_minutes=time_budget_minutes,
            checkpoint_claim_verified=checkpoint_claim_verified,
            enforce_prerequisites=True,
            enforce_budget=True,
            enforce_reachability=True,
            enforce_sources=True,
        )
    elif mode == "ablation":
        # Ablation mode can disable specific constraints via config
        enforce_prereq = config.get("enforce_prerequisites", True)
        enforce_budget = config.get("enforce_budget", True)
        enforce_reach = config.get("enforce_reachability", True)
        enforce_src = config.get("enforce_sources", True)

        plan = evaluate_route_intervention(
            stops=stops,
            available_stops=available_stops,
            target_outcomes=target_outcomes,
            time_budget_minutes=time_budget_minutes,
            checkpoint_claim_verified=checkpoint_claim_verified,
            enforce_prerequisites=enforce_prereq,
            enforce_budget=enforce_budget,
            enforce_reachability=enforce_reach,
            enforce_sources=enforce_src,
        )
    else:
        raise ValueError(f"Unknown mode: {mode}")

    return {
        "decision": plan.decision,
        "reason_codes": plan.reason_codes,
        "policy_version": plan.policy_version,
        "prerequisite_violation_count": int(plan.prerequisite_violation_count),
        "outcome_coverage": float(plan.outcome_coverage),
        "route_cost": int(plan.route_cost),
        "unreachable_checkpoint_rate": float(plan.unreachable_checkpoint_rate),
        "stop_sequence": plan.stop_sequence,
        "research_only": True,
    }
