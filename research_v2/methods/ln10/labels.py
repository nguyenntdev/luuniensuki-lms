"""LN-10 decision labels, typed mapping and reason codes.

Native decision vocabulary (emitted by every LN-10 V2 policy and used verbatim
by the frozen T3 gold oracle, basis ``ZIMMERMAN_SRL_CYCLICAL_INVARIANT``):

- ``allow_authorized_transition``  : ownership, version CAS, reflection and
  rationale all verified -> apply the transition.
- ``request_reflection``           : material revision without an articulated
  pedagogical rationale; the learner must reflect and justify first.
- ``reject_premature_submit``      : submission (project completion) attempted
  with the reflection gate unsatisfied; the learner must reflect first.
- ``deny_transition``              : actor is not authorized to move this
  project (missing ownership, forged identity, illegal FSM edge).
- ``resolve_revision_conflict``    : two conflicting offline edits target the
  same version (explicit concurrent-edit set or stale compare-and-swap);
  nothing is applied silently - the conflict must be resolved first.
- ``postpone``                     : the evaluator cannot responsibly decide
  now (missing version context, reordered event log, unknown state/action);
  the transition is deferred, never guessed.

Frozen V2 contract space (``research_v2.contracts.label_space.LN10_DECISIONS``):
``apply_transition``, ``require_reflection``, ``reject_unauthorized``,
``reject_conflict``, ``postpone``. The contract space is the documented
many-to-one projection of the native space (``NATIVE_TO_CONTRACT``); it is
diagnostic and never silently rewrites a decision, mirroring the LN-01/LN-03/
LN-05 pattern where the frozen gold vocabulary is the scoreable space.

Abstain/defer/reject families stay distinct by design: a conflict resolution
(``resolve_revision_conflict``) must never collapse into an authorization
denial (``deny_transition``) or a reflection request, otherwise the confusion
matrix cannot separate false accepts from false rejects. Unknown labels raise
:class:`LabelError` - no guessed fallback.
"""
from __future__ import annotations

from enum import Enum
from typing import Mapping

from research_v2.contracts.label_space import LN10_DECISIONS, LabelSpaceError
from research_v2.contracts.types import ContractError

STUDY_ID = "LN-10"


class LabelError(ValueError):
    """Raised when a policy would emit a decision outside the native space."""


class Decision(str, Enum):
    """Native LN-10 decision labels (= frozen T3 gold vocabulary)."""

    ALLOW_AUTHORIZED_TRANSITION = "allow_authorized_transition"
    REQUEST_REFLECTION = "request_reflection"
    DENY_TRANSITION = "deny_transition"
    RESOLVE_REVISION_CONFLICT = "resolve_revision_conflict"
    REJECT_PREMATURE_SUBMIT = "reject_premature_submit"
    POSTPONE = "postpone"


NATIVE_DECISIONS: frozenset[str] = frozenset(d.value for d in Decision)

CONTRACT_DECISIONS: frozenset[str] = LN10_DECISIONS

#: Documented many-to-one projection native -> frozen contract space.
NATIVE_TO_CONTRACT: Mapping[str, str] = {
    "allow_authorized_transition": "apply_transition",
    "request_reflection": "require_reflection",
    "reject_premature_submit": "require_reflection",
    "deny_transition": "reject_unauthorized",
    "resolve_revision_conflict": "reject_conflict",
    "postpone": "postpone",
}

# Reason codes emitted by the LN-10 policies (stable, machine-checkable).
REASON_NOMINAL = "nominal_authorized"
REASON_UNAUTHORIZED_ACTOR = "unauthorized_actor"
REASON_OFFLINE_CONFLICT = "offline_conflict"
REASON_CONCURRENT_EDITS = "concurrent_offline_edits"
REASON_SKIPPED_REFLECTION = "skipped_reflection"
REASON_EMPTY_REFLECTION_TEXT = "empty_reflection_text"
REASON_MISSING_RATIONALE = "missing_rationale"
REASON_MISSING_VERSION = "missing_version_info"
REASON_REORDERED_LOG = "reordered_event_log"
REASON_UNKNOWN_STATE = "unknown_project_state"
REASON_UNKNOWN_ACTION = "unknown_transition_action"
REASON_ILLEGAL_TRANSITION = "illegal_state_transition"
REASON_BASELINE_AUTO_ADVANCE = "baseline_checklist_auto_advance"
REASON_ABLATION = "ablation"
REASON_NO_OWNERSHIP_CHECK = "ownership_check_disabled"
REASON_NO_CONCURRENCY_CHECK = "concurrency_check_disabled"
REASON_NO_REFLECTION_GATE = "reflection_gate_disabled"


def map_native_decision(decision: str) -> str:
    """Validate a native decision label; typed failure on unknown labels."""
    if not isinstance(decision, str) or decision not in NATIVE_DECISIONS:
        raise LabelError(
            f"{STUDY_ID}: decision {decision!r} not in native label space "
            f"{sorted(NATIVE_DECISIONS)}"
        )
    return decision


def to_contract_decision(native: str) -> str:
    """Project a native decision onto the frozen V2 contract space.

    Raises :class:`LabelError` for labels outside the native space (never
    guesses a fallback projection).
    """
    map_native_decision(native)
    projected = NATIVE_TO_CONTRACT[native]
    if projected not in CONTRACT_DECISIONS:
        raise LabelSpaceError(
            f"{STUDY_ID}: projected decision {projected!r} not in contract "
            f"label space {sorted(CONTRACT_DECISIONS)}"
        )
    return projected


def validate_contract_decision(decision: str) -> str:
    """Validate against the frozen contract space (diagnostic use)."""
    if decision not in CONTRACT_DECISIONS:
        raise LabelSpaceError(
            f"{STUDY_ID}: decision {decision!r} not in contract label space "
            f"{sorted(CONTRACT_DECISIONS)}"
        )
    return decision


def build_prediction(
    *,
    case_id: str,
    decision: str,
    reason_codes: tuple[str, ...] = (),
    evidence_ids: tuple[str, ...] = (),
    score: float | None = None,
):
    """Construct a contract-valid, native-labelled StudyPrediction."""
    from research_v2.contracts.types import StudyPrediction

    map_native_decision(decision)
    try:
        return StudyPrediction(
            study_id=STUDY_ID,
            case_id=case_id,
            decision=decision,
            score=score,
            reason_codes=tuple(reason_codes),
            evidence_ids=tuple(evidence_ids),
        )
    except ContractError as exc:
        raise LabelError(f"case {case_id!r}: contract violation: {exc}") from exc
