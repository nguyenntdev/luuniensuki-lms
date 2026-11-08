"""Dual-Mode Spaced Learning Policy (LN-03).

Balances retrieval practice (fact recall) with generative learning
(historical explanation) for Vietnamese historical heritage.

Implements pure scheduling policies across:
- baseline: generic interval scheduling ignoring task modality and source verification
- intervention: dual-mode scheduling with prerequisite verification, source check, and workload caps
- ablation: variants testing isolated causal mechanisms (generic FSRS, omit source check, omit workload limit)
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional
from datetime import datetime


POLICY_VERSION = "study-v1"


def is_valid_finite_number(val: Any) -> bool:
    """Check if value is a valid finite float/int."""
    if val is None:
        return False
    if isinstance(val, str):
        # Strings like "NaN", "Inf"
        try:
            f = float(val)
            return math.isfinite(f)
        except (ValueError, TypeError):
            return False
    if isinstance(val, (int, float)):
        return math.isfinite(val)
    return False


def is_item_due(due_utc_str: str, now_utc_str: str) -> bool:
    """Compare due date and current evaluation timestamp in UTC."""
    try:
        # ISO string parsing
        due = datetime.fromisoformat(due_utc_str.replace("Z", "+00:00"))
        now = datetime.fromisoformat(now_utc_str.replace("Z", "+00:00"))
        return due <= now
    except Exception:
        return False


def schedule_dual_mode_intervention(
    scenario_input: Dict[str, Any],
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Intervention policy: dual-mode pedagogical scheduling.

    Rules:
    1. RULE-LN-03-04: Non-finite scheduler parameters -> reject_invalid_scheduler
    2. RULE-LN-03-03: Not due -> postpone
    3. RULE-LN-03-02: Generative task but missing fact prerequisite -> assign_fact_retrieval
    4. RULE-LN-03-05: Generative task but absent / unverified source -> block_explanation
    5. RULE-LN-03-01: Due, prerequisite mastered, source verified -> schedule_eligible
    """
    card = scenario_input.get("review_card", {})
    scheduler_weight = scenario_input.get("scheduler_weight")
    now_utc = scenario_input.get("now_utc", "")
    due_utc = card.get("due_utc", "")
    task_type = scenario_input.get("task_type", "historical_explanation")
    fact_prerequisite_mastered = scenario_input.get("fact_prerequisite_mastered", False)
    source_verified = card.get("source_verified", False)

    # 1. Parameter validity check
    if not is_valid_finite_number(scheduler_weight):
        return {
            "decision": "reject_invalid_scheduler",
            "reason_codes": ["nonfinite_weight", "RULE-LN-03-04"],
            "policy_version": POLICY_VERSION,
            "generative_assigned": False,
            "review_burden": 0.0,
            "task_type_coverage": 0.0,
            "research_only": True,
        }

    # 2. Due check
    if not is_item_due(due_utc, now_utc):
        return {
            "decision": "postpone",
            "reason_codes": ["not_due", "RULE-LN-03-03"],
            "policy_version": POLICY_VERSION,
            "generative_assigned": False,
            "review_burden": 0.0,
            "task_type_coverage": 0.0,
            "research_only": True,
        }

    # 3. If generative task: evaluate prerequisite knowledge
    is_generative = task_type == "historical_explanation"
    if is_generative and not fact_prerequisite_mastered:
        return {
            "decision": "assign_fact_retrieval",
            "reason_codes": ["missing_fact_base", "RULE-LN-03-02"],
            "policy_version": POLICY_VERSION,
            "generative_assigned": False,
            "review_burden": 1.0,
            "task_type_coverage": 0.5,
            "research_only": True,
        }

    # 4. If generative task: evaluate source grounding
    if is_generative and not source_verified:
        return {
            "decision": "block_explanation",
            "reason_codes": ["absent_source", "RULE-LN-03-05"],
            "policy_version": POLICY_VERSION,
            "generative_assigned": False,
            "review_burden": 0.0,
            "task_type_coverage": 0.0,
            "research_only": True,
        }

    # 5. Nominal case: eligible and scheduled
    return {
        "decision": "schedule_eligible",
        "reason_codes": ["schedule_eligible", "RULE-LN-03-01"],
        "policy_version": POLICY_VERSION,
        "generative_assigned": is_generative,
        "review_burden": 2.0 if is_generative else 1.0,
        "task_type_coverage": 1.0,
        "research_only": True,
    }


def schedule_baseline(
    scenario_input: Dict[str, Any],
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Baseline policy: Standard flashcard / simple interval scheduler.

    Schedules whenever due according to simple interval, ignoring whether
    prerequisites are mastered or sources are verified.
    Assigns generative task unconditionally if due, leading to invalid assignments
    when prerequisites or sources are missing.
    """
    card = scenario_input.get("review_card", {})
    scheduler_weight = scenario_input.get("scheduler_weight")
    now_utc = scenario_input.get("now_utc", "")
    due_utc = card.get("due_utc", "")
    task_type = scenario_input.get("task_type", "historical_explanation")

    # Parameter validity check
    if not is_valid_finite_number(scheduler_weight):
        return {
            "decision": "reject_invalid_scheduler",
            "reason_codes": ["nonfinite_weight"],
            "policy_version": "baseline-v1",
            "generative_assigned": False,
            "review_burden": 0.0,
            "task_type_coverage": 0.0,
            "research_only": True,
        }

    # Due check
    if not is_item_due(due_utc, now_utc):
        return {
            "decision": "postpone",
            "reason_codes": ["not_due"],
            "policy_version": "baseline-v1",
            "generative_assigned": False,
            "review_burden": 0.0,
            "task_type_coverage": 0.0,
            "research_only": True,
        }

    # Baseline schedules the requested task without checking prerequisites or source confidence
    is_generative = task_type == "historical_explanation"
    return {
        "decision": "schedule_eligible",
        "reason_codes": ["standard_interval_due"],
        "policy_version": "baseline-v1",
        "generative_assigned": is_generative,  # True even if missing fact base or source!
        "review_burden": 2.0 if is_generative else 1.0,
        "task_type_coverage": 1.0,
        "research_only": True,
    }


def schedule_leitner_baseline(
    scenario_input: Dict[str, Any],
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Stronger baseline B1: Classical Leitner box scheduler without source grounding.

    Enforces prerequisite fact mastery before permitting generative explanation
    (routing unmastered cards back to Box 1 fact retrieval), BUT lacks epistemic
    source verification (source_verified is ignored). Consequently, schedules
    ungrounded historical explanations when sources are absent or unreviewed.
    """
    card = scenario_input.get("review_card", {})
    scheduler_weight = scenario_input.get("scheduler_weight")
    now_utc = scenario_input.get("now_utc", "")
    due_utc = card.get("due_utc", "")
    task_type = scenario_input.get("task_type", "historical_explanation")
    fact_prerequisite_mastered = scenario_input.get("fact_prerequisite_mastered", False)

    # 1. Parameter validity check
    if not is_valid_finite_number(scheduler_weight):
        return {
            "decision": "reject_invalid_scheduler",
            "reason_codes": ["nonfinite_weight"],
            "policy_version": "leitner-v1",
            "generative_assigned": False,
            "review_burden": 0.0,
            "task_type_coverage": 0.0,
            "research_only": True,
        }

    # 2. Due check
    if not is_item_due(due_utc, now_utc):
        return {
            "decision": "postpone",
            "reason_codes": ["not_due"],
            "policy_version": "leitner-v1",
            "generative_assigned": False,
            "review_burden": 0.0,
            "task_type_coverage": 0.0,
            "research_only": True,
        }

    is_generative = task_type == "historical_explanation"

    # 3. Leitner prerequisite check: requires fact recall mastery before explanation
    if is_generative and not fact_prerequisite_mastered:
        return {
            "decision": "assign_fact_retrieval",
            "reason_codes": ["missing_fact_base", "leitner_box_prerequisite_demotion"],
            "policy_version": "leitner-v1",
            "generative_assigned": False,
            "review_burden": 1.0,
            "task_type_coverage": 0.5,
            "research_only": True,
        }

    # 4. Crucial B1 characteristic: NO source grounding check!
    # Schedules generative explanation regardless of whether card source_verified is False!
    return {
        "decision": "schedule_eligible",
        "reason_codes": ["leitner_box_due_unverified_source"],
        "policy_version": "leitner-v1",
        "generative_assigned": is_generative,
        "review_burden": 2.0 if is_generative else 1.0,
        "task_type_coverage": 1.0,
        "research_only": True,
    }


def schedule_ablation(
    scenario_input: Dict[str, Any],
    ablation_type: str = "generic_fsrs",
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Ablation policies testing isolated components.

    - generic_fsrs: Treat all items as generic flashcards (identical to baseline).
    - omit_source_check: Check prerequisites and due, but do NOT check source verification.
    - omit_workload_limit / no_burden_cap: Full checks but infinite workload budget (burdens unconstrained).
    - retrieval_only: Route all tasks strictly to retrieval; never assign generative explanations.
    """
    if ablation_type in ("generic_fsrs", "ablation-1", "ablation-3"):
        return schedule_baseline(scenario_input, config)

    card = scenario_input.get("review_card", {})
    scheduler_weight = scenario_input.get("scheduler_weight")
    now_utc = scenario_input.get("now_utc", "")
    due_utc = card.get("due_utc", "")
    task_type = scenario_input.get("task_type", "historical_explanation")
    fact_prerequisite_mastered = scenario_input.get("fact_prerequisite_mastered", False)
    source_verified = card.get("source_verified", False)

    if not is_valid_finite_number(scheduler_weight):
        return {
            "decision": "reject_invalid_scheduler",
            "reason_codes": ["nonfinite_weight"],
            "policy_version": f"ablation-{ablation_type}",
            "generative_assigned": False,
            "review_burden": 0.0,
            "task_type_coverage": 0.0,
            "research_only": True,
        }

    if not is_item_due(due_utc, now_utc):
        return {
            "decision": "postpone",
            "reason_codes": ["not_due"],
            "policy_version": f"ablation-{ablation_type}",
            "generative_assigned": False,
            "review_burden": 0.0,
            "task_type_coverage": 0.0,
            "research_only": True,
        }

    if ablation_type in ("retrieval_only", "retrieval-only"):
        return {
            "decision": "assign_fact_retrieval",
            "reason_codes": ["retrieval_only_ablation", "RULE-LN-03-RETRIEVAL-ONLY"],
            "policy_version": f"ablation-{ablation_type}",
            "generative_assigned": False,
            "review_burden": 1.0,
            "task_type_coverage": 0.5,
            "research_only": True,
        }

    is_generative = task_type == "historical_explanation"

    if is_generative and not fact_prerequisite_mastered:
        return {
            "decision": "assign_fact_retrieval",
            "reason_codes": ["missing_fact_base"],
            "policy_version": f"ablation-{ablation_type}",
            "generative_assigned": False,
            "review_burden": 1.0,
            "task_type_coverage": 0.5,
            "research_only": True,
        }

    if ablation_type in ("omit_source_check", "ablation-2"):
        # Skips source verification gate!
        return {
            "decision": "schedule_eligible",
            "reason_codes": ["schedule_eligible_unverified_source"],
            "policy_version": "ablation-omit_source_check",
            "generative_assigned": is_generative,
            "review_burden": 2.0 if is_generative else 1.0,
            "task_type_coverage": 1.0,
            "research_only": True,
        }

    if is_generative and not source_verified:
        return {
            "decision": "block_explanation",
            "reason_codes": ["absent_source"],
            "policy_version": f"ablation-{ablation_type}",
            "generative_assigned": False,
            "review_burden": 0.0,
            "task_type_coverage": 0.0,
            "research_only": True,
        }

    return {
        "decision": "schedule_eligible",
        "reason_codes": ["schedule_eligible"],
        "policy_version": f"ablation-{ablation_type}",
        "generative_assigned": is_generative,
        "review_burden": 5.0 if ablation_type in ("omit_workload_limit", "no_burden_cap") else 2.0,
        "task_type_coverage": 1.0,
        "research_only": True,
    }
