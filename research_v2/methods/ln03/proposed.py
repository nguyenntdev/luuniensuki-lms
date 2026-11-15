"""LN-03 proposed method: evidence-grounded dual-mode spaced scheduling.

Implements the dual-mode policy with the full prerequisite chain
(legacy rule order preserved, per ``dual_mode_policy.schedule_dual_mode_intervention``):

1. ``RULE-LN-03-04`` non-finite scheduler weight -> ``reject_invalid_scheduler``
2. ``RULE-LN-03-03`` review not due -> ``postpone``
3. ``RULE-LN-03-02`` generative task with unstable/absent fact base
   -> ``assign_fact_retrieval`` (remediate/postpone; never assign generative)
4. ``RULE-LN-03-05`` generative task without verified source -> ``block_explanation``
5. ``RULE-LN-03-01`` otherwise -> ``schedule_eligible``

Fact-base stability uses observed repetitions against the configured
threshold (from features/config), rejecting a missing fact base outright.
Deterministic: identical input + config + seed produce identical decisions.
"""
from __future__ import annotations

import math
from typing import Any, Iterable, Mapping

from research_v2.contracts.types import StudyInput, StudyPrediction

from .errors import PolicyConfigError, ScenarioError
from .labels import (
    REASON_ABSENT_SOURCE,
    REASON_MISSING_FACT_BASE,
    REASON_NONFINITE_WEIGHT,
    REASON_NOT_DUE,
    RULE_DUE,
    RULE_FACT,
    RULE_SCHEDULE,
    RULE_SOURCE,
    RULE_WEIGHT,
    STUDY_ID,
    native_decision,
)
from .scenario import SchedulingCase, is_valid_finite_number, parse_case

METHOD_ID = "proposed"
METHOD_VERSION = "ln03-proposed-v1"

DEFAULT_CONFIG: Mapping[str, Any] = {
    "fact_stability_min_repetitions": 2,
    "stability_days_floor": 1.0,
    "postpone_if_not_due": True,
    "fact_stability_enabled": True,
    "source_gate_enabled": True,
    "due_scheduling_enabled": True,
}


def _validate_config(config: Mapping[str, Any]) -> dict[str, Any]:
    cfg = dict(DEFAULT_CONFIG)
    for key, value in (config or {}).items():
        if key in cfg:
            cfg[key] = value
    threshold = cfg["fact_stability_min_repetitions"]
    if isinstance(threshold, bool) or not isinstance(threshold, (int, float)) or not math.isfinite(float(threshold)):
        raise PolicyConfigError(f"{STUDY_ID}: fact_stability_min_repetitions must be a finite number, got {threshold!r}")
    if threshold < 0:
        raise PolicyConfigError(f"{STUDY_ID}: fact_stability_min_repetitions must be >= 0")
    floor = cfg["stability_days_floor"]
    if isinstance(floor, bool) or not isinstance(floor, (int, float)) or not math.isfinite(float(floor)):
        raise PolicyConfigError(f"{STUDY_ID}: stability_days_floor must be a finite number, got {floor!r}")
    if floor < 0:
        raise PolicyConfigError(f"{STUDY_ID}: stability_days_floor must be >= 0")
    for flag in ("postpone_if_not_due", "fact_stability_enabled", "source_gate_enabled", "due_scheduling_enabled"):
        if not isinstance(cfg[flag], bool):
            raise PolicyConfigError(f"{STUDY_ID}: config flag {flag!r} must be boolean")
    return cfg


def _fact_base_stable(case: SchedulingCase, cfg: Mapping[str, Any]) -> tuple[bool, tuple[str, ...]]:
    """Determine whether the fact base is stable for a generative task.

    Stability requires (a) the fact prerequisite flag observed on the card and
    (b) observed repetitions meeting the configured threshold when repetition
    history exists. Missing/invalid fact-base signals are rejected, not guessed.
    """
    if not case.fact_prerequisite_mastered:
        return False, (REASON_MISSING_FACT_BASE, RULE_FACT)
    threshold = float(cfg["fact_stability_min_repetitions"])
    if case.repetitions is None:
        # No observed repetition history: the prerequisite flag alone is the
        # stability signal recorded by the engine (matches legacy behaviour).
        return True, ()
    floor = float(cfg["stability_days_floor"])
    stable = case.repetitions >= threshold and (
        case.stability_days is None or case.stability_days >= floor
    )
    if stable:
        return True, ()
    return False, (REASON_MISSING_FACT_BASE, RULE_FACT, "unstable_repetition_history")


def decide(case: SchedulingCase, cfg: Mapping[str, Any]) -> tuple[str, tuple[str, ...], float | None]:
    """Pure decision function. Returns (decision, reason_codes, score)."""
    # 1. Non-finite scheduler parameters -> reject (RULE-LN-03-04)
    if not is_valid_finite_number(case.scheduler_weight_raw):
        return "reject_invalid_scheduler", (REASON_NONFINITE_WEIGHT, RULE_WEIGHT), None

    # 2. Due-date scheduling (RULE-LN-03-03): postpone when not due.
    if cfg["due_scheduling_enabled"] and cfg["postpone_if_not_due"]:
        if case.due_dt is not None and case.now_dt is not None and case.due_dt > case.now_dt:
            return "postpone", (REASON_NOT_DUE, RULE_DUE), None

    # 3. Fact-stability prerequisite for generative tasks (RULE-LN-03-02).
    if cfg["fact_stability_enabled"] and case.is_generative:
        stable, reasons = _fact_base_stable(case, cfg)
        if not stable:
            return "assign_fact_retrieval", reasons, None

    # 4. Verified-source gate for generative tasks (RULE-LN-03-05).
    if cfg["source_gate_enabled"] and case.is_generative and not case.source_verified:
        return "block_explanation", (REASON_ABSENT_SOURCE, RULE_SOURCE), None

    # 5. Nominal: due, stable fact base, verified source -> schedule.
    return "schedule_eligible", ("schedule_eligible", RULE_SCHEDULE), 1.0


def predict_one(inp: StudyInput, cfg: Mapping[str, Any]) -> StudyPrediction:
    case = parse_case(inp.case_id, inp.features)
    decision, reasons, score = decide(case, cfg)
    decision = native_decision(decision)
    return StudyPrediction(
        study_id=STUDY_ID,
        case_id=inp.case_id,
        decision=decision,
        score=score,
        reason_codes=tuple(reasons),
        evidence_ids=(f"review_card:{inp.features.get('review_card', {}).get('id', inp.case_id)}",)
        if isinstance(inp.features, Mapping) and isinstance(inp.features.get("review_card"), Mapping)
        else (),
    )


def predict_batch(inputs: Iterable[StudyInput], config: Mapping[str, Any] | None = None) -> list[StudyPrediction]:
    """Batch predict. Malformed rows raise typed errors with case location."""
    cfg = _validate_config(config or {})
    return [predict_one(inp, cfg) for inp in inputs]
