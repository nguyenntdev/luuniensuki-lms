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
    raw_stops = scenario_input.get("stops", []) or []
    stops = [HeritageStop.from_dict(s) for s in raw_stops]
    available_stops = scenario_input.get("available_stops", []) or []
    target_outcomes = scenario_input.get("target_outcomes", []) or []
    time_budget_raw = scenario_input.get("time_budget_minutes")
    time_budget_minutes = 60 if time_budget_raw is None else int(time_budget_raw)
    checkpoint_claim_raw = scenario_input.get("checkpoint_claim_verified")
    checkpoint_claim_verified = True if checkpoint_claim_raw is None else bool(checkpoint_claim_raw)

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
        ablation_type = str(
            config.get("ablation_type")
            or config.get("label")
            or config.get("variant")
            or ""
        )

        enforce_prereq = config.get("enforce_prerequisites", True)
        if (
            config.get("ignore_prerequisites") is True
            or config.get("disable_prerequisites") is True
            or config.get("shortest_distance_only") is True
            or ablation_type in ("ignore_prerequisites", "disable_prerequisites", "shortest_distance_only")
        ):
            enforce_prereq = False

        enforce_budget = config.get("enforce_budget", True)
        if (
            config.get("disable_budget") is True
            or config.get("ignore_budget") is True
            or ablation_type in ("disable_budget", "ignore_budget")
        ):
            enforce_budget = False

        enforce_reach = config.get("enforce_reachability", True)
        if (
            config.get("disable_reachability") is True
            or config.get("ignore_reachability") is True
            or ablation_type in ("disable_reachability", "ignore_reachability")
        ):
            enforce_reach = False

        enforce_src = config.get("enforce_sources", True)
        if (
            config.get("disable_sources") is True
            or config.get("ignore_sources") is True
            or config.get("no_theme_filter") is True
            or ablation_type in ("disable_sources", "ignore_sources", "no_theme_filter")
        ):
            enforce_src = False

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
