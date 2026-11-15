"""Shared inference-time feature extraction and typed validation for LN-03.

Only legitimate inference-time fields are read (review history, recall state,
claim evidence state, task mode, budget). Gold/oracle/fault material is
rejected by the frozen contracts; this module additionally fails closed on
malformed scenario structure instead of guessing fallbacks.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Mapping

from .errors import ScenarioError
from .labels import STUDY_ID


@dataclass(frozen=True)
class SchedulingCase:
    """Validated inference-time view of one LN-03 scheduling scenario."""

    case_id: str
    task_type: str
    fact_prerequisite_mastered: bool
    source_verified: bool
    scheduler_weight_raw: Any
    due_utc: str | None
    now_utc: str | None
    repetitions: float | None
    stability_days: float | None
    difficulty: float | None
    card_state: str | None
    due_dt: datetime | None = None
    now_dt: datetime | None = None

    @property
    def is_generative(self) -> bool:
        return self.task_type == "historical_explanation"


GENERATIVE_TASK_TYPES = frozenset({"historical_explanation"})
RETRIEVAL_TASK_TYPES = frozenset({"fact_retrieval", "fact_recall", "retrieval", "quiz"})


def _require_mapping(value: Any, where: str, case_id: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ScenarioError(f"{STUDY_ID} case {case_id!r}: {where} must be a mapping")
    return value


def _finite_or_none(value: Any, where: str, case_id: str) -> float | None:
    """Return a finite float, or None when the field is legitimately absent.

    String sentinels ("NaN", "Inf", "undefined") and non-numeric scalars are
    rejected; absent (None/missing) is distinct from invalid.
    """
    if value is None:
        return None
    if isinstance(value, bool):
        raise ScenarioError(f"{STUDY_ID} case {case_id!r}: {where} must be numeric, got bool")
    if isinstance(value, str):
        if value.strip() == "":
            return None
        raise ScenarioError(f"{STUDY_ID} case {case_id!r}: {where} non-numeric string {value!r}")
    if not isinstance(value, (int, float)):
        raise ScenarioError(f"{STUDY_ID} case {case_id!r}: {where} must be numeric, got {type(value).__name__}")
    f = float(value)
    if not math.isfinite(f):
        raise ScenarioError(f"{STUDY_ID} case {case_id!r}: {where} is non-finite ({value!r})")
    return f


def is_valid_finite_number(value: Any) -> bool:
    """Legacy-compatible finiteness probe (numeric strings like 'NaN' -> False)."""
    if value is None:
        return False
    if isinstance(value, str):
        try:
            return math.isfinite(float(value))
        except (ValueError, TypeError):
            return False
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return math.isfinite(float(value))
    return False


def _parse_utc(stamp: str | None, where: str, case_id: str) -> datetime | None:
    if stamp is None or stamp == "":
        return None
    if not isinstance(stamp, str):
        raise ScenarioError(f"{STUDY_ID} case {case_id!r}: {where} must be an ISO-8601 string")
    try:
        return datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ScenarioError(f"{STUDY_ID} case {case_id!r}: {where} unparseable timestamp {stamp!r}") from exc


def parse_case(case_id: str, features: Mapping[str, Any]) -> SchedulingCase:
    """Extract and validate the inference-time scenario from masked features."""
    feats = _require_mapping(features, "features", case_id)
    card_raw = feats.get("review_card")
    card = _require_mapping(card_raw, "review_card", case_id) if card_raw is not None else {}

    task_type = feats.get("task_type")
    if not isinstance(task_type, str) or not task_type:
        raise ScenarioError(f"{STUDY_ID} case {case_id!r}: task_type must be a non-empty string")

    fact_prereq = feats.get("fact_prerequisite_mastered")
    if not isinstance(fact_prereq, bool):
        raise ScenarioError(
            f"{STUDY_ID} case {case_id!r}: fact_prerequisite_mastered must be boolean, got {fact_prereq!r}"
        )

    source_verified = card.get("source_verified")
    if not isinstance(source_verified, bool):
        raise ScenarioError(
            f"{STUDY_ID} case {case_id!r}: review_card.source_verified must be boolean, got {source_verified!r}"
        )

    if "scheduler_weight" not in feats:
        raise ScenarioError(f"{STUDY_ID} case {case_id!r}: scheduler_weight is required")

    due_raw = card.get("due_utc")
    now_raw = feats.get("now_utc")
    due_str = due_raw if isinstance(due_raw, str) else None
    now_str = now_raw if isinstance(now_raw, str) else None
    due_dt = _parse_utc(due_str, "review_card.due_utc", case_id)
    now_dt = _parse_utc(now_str, "now_utc", case_id)

    state = card.get("state")
    if state is not None and not isinstance(state, str):
        raise ScenarioError(f"{STUDY_ID} case {case_id!r}: review_card.state must be a string")

    repetitions = _finite_or_none(card.get("repetitions"), "review_card.repetitions", case_id)
    stability = _finite_or_none(card.get("stability_days"), "review_card.stability_days", case_id)
    difficulty = _finite_or_none(card.get("difficulty"), "review_card.difficulty", case_id)
    if repetitions is not None and repetitions < 0:
        raise ScenarioError(f"{STUDY_ID} case {case_id!r}: review_card.repetitions must be >= 0")
    if stability is not None and stability < 0:
        raise ScenarioError(f"{STUDY_ID} case {case_id!r}: review_card.stability_days must be >= 0")

    return SchedulingCase(
        case_id=case_id,
        task_type=task_type,
        fact_prerequisite_mastered=fact_prereq,
        source_verified=source_verified,
        scheduler_weight_raw=feats["scheduler_weight"],
        due_utc=due_str,
        now_utc=now_str,
        repetitions=repetitions,
        stability_days=stability,
        difficulty=difficulty,
        card_state=state,
        due_dt=due_dt,
        now_dt=now_dt,
    )
