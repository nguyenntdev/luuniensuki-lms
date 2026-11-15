"""LN-10 proposed policy — process-verifiable SRL state machine (I1).

Zimmerman cyclical self-regulated-learning authorization over learner-owned
projects, enforcing INV-LN-10-01..05 from the observed engine
(``research/srl/project_state_machine.py`` -> ``backend.domain.reflection_cycle``):

Decision procedure (single pass, severity-ordered; the first triggered gate
determines the label so families never collapse):

1. Structural schema validation (typed :class:`DatasetError`, not a decision).
2. Ownership / actor authorization gate: the actor must be the project owner
   (or an authorized staff role) -> ``deny_transition`` with
   ``unauthorized_actor``. INV-LN-10-02: every material revision needs an
   authorized actor.
3. Offline concurrency gate (the mandatory mechanism). Two independent
   detectors, both decisive:
   a. **Explicit concurrent-edit set**: when the case carries
      ``concurrent_edits``, two or more edits targeting the SAME
      ``expected_version`` with DIVERGENT payloads (action, new_goal or
      rationale) are two conflicting offline edits to the same version ->
      ``resolve_revision_conflict`` with ``concurrent_offline_edits``. The
      transition is rejected/postponed into a visible conflict-resolution
      state; NOTHING is silently applied (INV-LN-10-04). Identical
      redeliveries (same payload, same editor intent) are idempotent, not
      conflicts.
   b. **Compare-and-swap check**: ``transition.expected_version`` must equal
      ``project.version``; a stale expectation proves a concurrent offline
      edit already advanced the project -> ``resolve_revision_conflict`` with
      ``offline_conflict``.
4. Reflection gate: project completion (``submit``) or stage advancement
   requires the learner's completed self-reflection ->
   ``reject_premature_submit`` with ``skipped_reflection``. INV-LN-10-03:
   checklist progress never substitutes for reflection.
5. Rationale gate (forethought): material revisions (``revise_plan``,
   ``update_goal``) require a non-empty pedagogical rationale ->
   ``request_reflection`` with ``missing_rationale`` (the learner must
   reflect and justify before re-submitting).
6. FSM edge legality: the (state, action) pair must be a legal edge of the
   Zimmerman cycle table -> ``deny_transition`` with ``illegal_state_transition``.
7. Event-log replay sanity: duplicate event ids in the log ->
   ``postpone`` with ``reordered_event_log`` (deferred, never guessed).
8. Unknown state/action are NOT guessed: they yield ``postpone`` with the
   typed reason (``unknown_project_state`` / ``unknown_transition_action``) —
   abstain/defer is a distinct family, never merged into a generic reject.
9. Nominal -> ``allow_authorized_transition`` (apply the transition).

False-rejection protection: identical to the legacy engine, a legitimate
re-observation of the same stage by the same owner (Case 3 in the spec) is
legal; only genuinely conflicting content or stale versions block.

Determinism: identical (features, config, seed) produce byte-identical
predictions; no randomness is consumed (the ``seed`` config is accepted for
interface compatibility only). No oracle, fault_id, cohort or gold label is
ever read.
"""
from __future__ import annotations

from typing import Any, Mapping

from research_v2.contracts.types import StudyInput, StudyPrediction

from .dataset import (
    ACTIONABLE_ACTIONS,
    KNOWN_ACTIONS,
    KNOWN_PROJECT_STATES,
    DatasetError,
    OfflineEdit,
    SRLCase,
    parse_case,
)
from .labels import (
    REASON_CONCURRENT_EDITS,
    REASON_ILLEGAL_TRANSITION,
    REASON_MISSING_RATIONALE,
    REASON_MISSING_VERSION,
    REASON_NOMINAL,
    REASON_OFFLINE_CONFLICT,
    REASON_REORDERED_LOG,
    REASON_SKIPPED_REFLECTION,
    REASON_UNKNOWN_ACTION,
    REASON_UNKNOWN_STATE,
    STUDY_ID,
    build_prediction,
)

METHOD_ID = "proposed"
METHOD_VERSION = "ln10-proposed-v2.0"

#: Staff roles allowed to move a project they do not own (mentoring/review),
#: mirroring ``verify_project_ownership`` in the observed engine.
AUTHORIZED_STAFF_ROLES = frozenset({"teacher", "admin", "staff"})

#: Legal Zimmerman-cycle (state, action) edges for actionable transitions.
LEGAL_EDGES: frozenset[tuple[str, str]] = frozenset(
    {
        ("planning", "revise_plan"),
        ("planning", "update_goal"),
        ("planning", "advance_stage"),
        ("monitoring", "revise_plan"),
        ("monitoring", "update_goal"),
        ("monitoring", "advance_stage"),
        ("monitoring", "submit"),
        ("reflecting", "record_reflection"),
        ("reflecting", "revise_plan"),
        ("revising", "revise_plan"),
        ("revising", "update_goal"),
        ("revising", "advance_stage"),
    }
)


class PolicyInputError(DatasetError):
    """Typed failure for structurally invalid inputs (no silent default)."""


def _ownership_ok(case: SRLCase) -> bool:
    if case.actor.role in AUTHORIZED_STAFF_ROLES:
        return True
    return case.actor.owns_project


def _edits_conflict(edits: tuple[OfflineEdit, ...]) -> tuple[bool, tuple[str, ...]]:
    """Detect two conflicting offline edits to the same project version.

    Returns ``(conflict, evidence_ids)``. Two edits conflict when they share
    an ``expected_version`` and their payloads diverge in action, new_goal or
    non-empty rationale. Identical redeliveries are idempotent, not conflicts.
    """
    by_version: dict[int | None, list[OfflineEdit]] = {}
    for edit in edits:
        by_version.setdefault(edit.expected_version, []).append(edit)
    for version, group in sorted(
        by_version.items(), key=lambda kv: (kv[0] is None, kv[0] or 0)
    ):
        if len(group) < 2:
            continue
        first = group[0]
        for other in group[1:]:
            if (
                other.action != first.action
                or other.new_goal != first.new_goal
                or (other.rationale or "") != (first.rationale or "")
            ):
                evidence = (
                    f"edit:{first.editor}:v{version}",
                    f"edit:{other.editor}:v{version}",
                )
                return True, evidence
    return False, ()


def _event_log_ok(case: SRLCase) -> bool:
    ids = [str(ev.get("event_id")) for ev in case.event_log]
    return len(ids) == len(set(ids))


def decide_case(
    case: SRLCase,
    *,
    enforce_ownership: bool = True,
    enforce_concurrency: bool = True,
    enforce_reflection_gate: bool = True,
    enforce_rationale: bool = True,
) -> dict[str, Any]:
    """Core decision function; keyword flags exist only for ablations.

    Returns ``{"decision": str, "reason_codes": tuple, "evidence_ids": tuple,
    "transition_applied": bool, "conflict_detected": bool,
    "reflection_required": bool}``.
    """
    project = case.project
    transition = case.transition
    evidence: list[str] = [f"project:v{project.version}", f"actor:{case.actor.role}"]

    # 1. Unknown-state / unknown-action abstention (checked first: an unknown
    #    state makes every downstream gate meaningless -> defer, never guess).
    if project.state not in KNOWN_PROJECT_STATES:
        return {
            "decision": "postpone",
            "reason_codes": (REASON_UNKNOWN_STATE, f"state:{project.state}"),
            "evidence_ids": tuple(evidence),
            "transition_applied": False,
            "conflict_detected": False,
            "reflection_required": True,
        }
    if transition.action not in KNOWN_ACTIONS:
        return {
            "decision": "postpone",
            "reason_codes": (REASON_UNKNOWN_ACTION, f"action:{transition.action}"),
            "evidence_ids": tuple(evidence),
            "transition_applied": False,
            "conflict_detected": False,
            "reflection_required": True,
        }

    # 2. Missing version context: cannot compare-and-swap responsibly.
    if enforce_concurrency and (
        project.version is None or transition.expected_version is None
    ):
        return {
            "decision": "postpone",
            "reason_codes": (REASON_MISSING_VERSION,),
            "evidence_ids": tuple(evidence),
            "transition_applied": False,
            "conflict_detected": False,
            "reflection_required": True,
        }

    # 3. Ownership / authorization gate.
    if enforce_ownership and not _ownership_ok(case):
        evidence.append(f"owns_project:{case.actor.owns_project}")
        return {
            "decision": "deny_transition",
            "reason_codes": ("unauthorized_actor",),
            "evidence_ids": tuple(evidence),
            "transition_applied": False,
            "conflict_detected": False,
            "reflection_required": False,
        }

    # 4a. Explicit two-conflicting-offline-edits detector (mandatory case).
    if enforce_concurrency and case.concurrent_edits:
        conflict, edit_evidence = _edits_conflict(case.concurrent_edits)
        if conflict:
            return {
                "decision": "resolve_revision_conflict",
                "reason_codes": (REASON_CONCURRENT_EDITS,),
                "evidence_ids": tuple(evidence) + edit_evidence,
                "transition_applied": False,
                "conflict_detected": True,
                "reflection_required": False,
            }

    # 4b. Compare-and-swap concurrency gate (stale offline edit).
    if (
        enforce_concurrency
        and transition.expected_version is not None
        and transition.expected_version != project.version
    ):
        evidence.append(f"expected_version:{transition.expected_version}")
        return {
            "decision": "resolve_revision_conflict",
            "reason_codes": (REASON_OFFLINE_CONFLICT,),
            "evidence_ids": tuple(evidence),
            "transition_applied": False,
            "conflict_detected": True,
            "reflection_required": False,
        }

    # 5. Reflection gate for project completion / stage advancement.
    needs_reflection = (
        enforce_reflection_gate
        and transition.action in ("submit", "advance_stage")
        and not project.reflection_completed
    )
    if needs_reflection:
        return {
            "decision": "reject_premature_submit",
            "reason_codes": (REASON_SKIPPED_REFLECTION, f"action:{transition.action}"),
            "evidence_ids": tuple(evidence),
            "transition_applied": False,
            "conflict_detected": False,
            "reflection_required": True,
        }

    # 6. Rationale gate for material revisions (forethought evidence).
    needs_rationale = (
        enforce_rationale
        and transition.action in ("revise_plan", "update_goal")
        and not (transition.rationale or "").strip()
    )
    if needs_rationale:
        return {
            "decision": "request_reflection",
            "reason_codes": (REASON_MISSING_RATIONALE, f"action:{transition.action}"),
            "evidence_ids": tuple(evidence),
            "transition_applied": False,
            "conflict_detected": False,
            "reflection_required": True,
        }

    # 7. FSM edge legality (actionable transitions only; record_reflection is
    #    always legal from any known state).
    if transition.action in ACTIONABLE_ACTIONS:
        edge = (project.state, transition.action)
        if edge not in LEGAL_EDGES:
            return {
                "decision": "deny_transition",
                "reason_codes": (REASON_ILLEGAL_TRANSITION, f"edge:{edge[0]}->{edge[1]}"),
                "evidence_ids": tuple(evidence),
                "transition_applied": False,
                "conflict_detected": False,
                "reflection_required": False,
            }

    # 8. Event-log replay sanity.
    if not _event_log_ok(case):
        return {
            "decision": "postpone",
            "reason_codes": (REASON_REORDERED_LOG,),
            "evidence_ids": tuple(evidence),
            "transition_applied": False,
            "conflict_detected": False,
            "reflection_required": True,
        }

    # 9. Nominal authorized transition.
    return {
        "decision": "allow_authorized_transition",
        "reason_codes": (REASON_NOMINAL,),
        "evidence_ids": tuple(evidence),
        "transition_applied": True,
        "conflict_detected": False,
        "reflection_required": False,
    }


def solve_case(case: SRLCase, **gate_flags: bool) -> dict[str, Any]:
    """Public entry point (named for ablation dispatch symmetry with LN-06)."""
    return decide_case(case, **gate_flags)


def predict_one(inp: StudyInput, config: Mapping[str, Any] | None = None) -> StudyPrediction:
    if not isinstance(inp, StudyInput):
        raise PolicyInputError(f"predict_one expects StudyInput, got {type(inp).__name__}")
    case = parse_case(inp.case_id, inp.features)
    result = solve_case(case)
    del config  # deterministic policy; config accepted for ABI compatibility
    return build_prediction(
        case_id=inp.case_id,
        decision=result["decision"],
        reason_codes=tuple(result["reason_codes"]),
        evidence_ids=tuple(result["evidence_ids"]),
        score=1.0 if result["transition_applied"] else 0.0,
    )


def predict_batch(inputs: list[StudyInput], config: dict | None = None) -> list[StudyPrediction]:
    """Contract ABI: deterministic LN-10 decisions for a batch of inputs.

    Any invalid row rejects the whole batch with its location (no guessed
    fallback), per the study specification.
    """
    out: list[StudyPrediction] = []
    for i, inp in enumerate(inputs):
        try:
            out.append(predict_one(inp, config))
        except DatasetError:
            raise
        except Exception as exc:  # surface typed failure with batch location
            raise PolicyInputError(
                f"input[{i}] case {getattr(inp, 'case_id', '?')!r}: {exc}"
            ) from exc
    return out
