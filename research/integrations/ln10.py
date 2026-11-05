# -*- coding: utf-8 -*-
"""Research adapter for Study LN-10 (Self-Regulated Project-Based Learning).

Callable entrypoint for benchmark runners and experiment suites:
    run_policy(scenario_input: dict, *, mode: str, config: dict) -> dict
"""
from __future__ import annotations

from typing import Any

from research.srl.project_state_machine import SRLProjectStateMachine

_state_machine = SRLProjectStateMachine()


def run_policy(
    scenario_input: dict[str, Any],
    *,
    mode: str,
    config: dict[str, Any],
) -> dict[str, Any]:
    """Execute LN-10 policy decision for given scenario input and mode.
    
    Args:
        scenario_input: Pure scenario input (actor, content, learner, project, transition)
        mode: Policy mode ('baseline', 'intervention', 'ablation')
        config: Extra policy configuration flags
        
    Returns:
        Dictionary containing decision, reason_codes, policy_version,
        and domain observables (transition_applied, conflict_detected, etc.)
    """
    return _state_machine.evaluate_transition(scenario_input, mode=mode, config=config)
