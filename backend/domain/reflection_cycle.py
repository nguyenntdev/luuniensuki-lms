# -*- coding: utf-8 -*-
"""Self-Regulated Learning (SRL) Reflection Cycle Domain (Study LN-10).

Pedagogical Foundation:
Implements Zimmerman's cyclical model of self-regulated learning (Forethought ->
Performance -> Self-Reflection) within the Hue Heritage Urban Project (Dự án Đô thị di sản Huế).

Core Invariants:
- INV-LN-10-01: A learner-set goal cannot be modified silently by algorithms.
- INV-LN-10-02: Every material revision must have an authorized actor, pedagogical rationale,
  and revision parent / version.
- INV-LN-10-03: Never equate simple checklist completion with true self-regulated learning competence.
- INV-LN-10-04: Offline concurrent modifications must trigger conflict resolution rather than
  overwriting concurrent progress.
- INV-LN-10-05: Students are never forced to reveal private personal data in reflection journals.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class SRLPhase(str, Enum):
    """Zimmerman's tripartite SRL phases."""
    FORETHOUGHT = "forethought"
    PERFORMANCE = "performance"
    SELF_REFLECTION = "self_reflection"


class ProjectStage(str, Enum):
    """Pedagogical project stages in the Hue Heritage project."""
    PLANNING = "planning"
    MONITORING = "monitoring"
    REFLECTING = "reflecting"
    REVISING = "revising"
    COMPLETED = "completed"
    SUBMITTED = "submitted"


class TransitionAction(str, Enum):
    """Actions triggering state transitions or plan updates."""
    REVISE_PLAN = "revise_plan"
    SUBMIT = "submit"
    ADVANCE_STAGE = "advance_stage"
    UPDATE_GOAL = "update_goal"
    RECORD_REFLECTION = "record_reflection"


class DecisionCode(str, Enum):
    """Authorized decision outcomes for study LN-10."""
    ALLOW_AUTHORIZED_TRANSITION = "allow_authorized_transition"
    REQUEST_REFLECTION = "request_reflection"
    DENY_TRANSITION = "deny_transition"
    RESOLVE_REVISION_CONFLICT = "resolve_revision_conflict"
    REJECT_PREMATURE_SUBMIT = "reject_premature_submit"
    ABSTAIN = "abstain"


class ReasonCode(str, Enum):
    """Standardized explanation and reason codes."""
    NOMINAL_AUTHORIZED = "nominal_authorized"
    MISSING_RATIONALE = "missing_rationale"
    UNAUTHORIZED_ACTOR = "unauthorized_actor"
    OFFLINE_CONFLICT = "offline_conflict"
    SKIPPED_REFLECTION = "skipped_reflection"
    BASELINE_AUTO_ADVANCE = "baseline_checklist_auto_advance"
    INSUFFICIENT_DATA = "insufficient_data"


@dataclass(frozen=True)
class ProjectGoal:
    """DATA-LN-10-01: Learner/teacher agreed objective."""
    id: str
    goal_statement: str
    content_scope: str
    created_at: str
    version: int = 1
    schema_version: str = "1.0"
    policy_version: str = "study-v1"
    source_commit: str = "54da2beb71f3df70e1f00b215ae0fb1a850eb263"


@dataclass(frozen=True)
class ProjectPlan:
    """DATA-LN-10-02: Milestones, sources, and time budget."""
    tasks: tuple[str, ...] = field(default_factory=tuple)
    milestones: tuple[str, ...] = field(default_factory=tuple)
    source_needs: tuple[str, ...] = field(default_factory=tuple)
    due_dates: tuple[str, ...] = field(default_factory=tuple)
    schema_version: str = "1.0"


@dataclass(frozen=True)
class ReflectionRecord:
    """DATA-LN-10-03: What worked, difficulties, planned change, evidence."""
    what_worked: str = ""
    difficulties: str = ""
    planned_change: str = ""
    timestamp: Optional[str] = None
    rationale: Optional[str] = None
    is_complete: bool = False
    evidence_locator: Optional[str] = None
    schema_version: str = "1.0"


@dataclass(frozen=True)
class LearnerProject:
    """Learner project entity representation."""
    id: str
    goal: str
    version: int
    owner: str
    stage: str
    reflection_completed: bool = False
    type: str = "heritage_city"


@dataclass(frozen=True)
class ProjectTransition:
    """Project transition request payload."""
    from_stage: str
    to_stage: Optional[str]
    action: str
    rationale: str
    actor: dict[str, Any]
    expected_version: int
    new_goal: Optional[str] = None


@dataclass(frozen=True)
class TeacherSignoff:
    """DATA-LN-10-05: Teacher signoff for project submission."""
    id: str
    teacher_id: str
    project_id: str
    approved: bool
    comments: str
    created_at: str
    schema_version: str = "1.0"


@dataclass(frozen=True)
class TransitionEvaluationResult:
    """Outcome of an SRL transition evaluation."""
    decision: DecisionCode
    reason_codes: list[str]
    policy_version: str
    transition_applied: bool
    conflict_detected: bool
    reflection_completed: bool
    ownership_verified: bool
    explanation: str
    observables: dict[str, Any] = field(default_factory=dict)


def verify_project_ownership(actor: dict[str, Any] | None) -> tuple[bool, str]:
    """Verify actor has authority to modify the project."""
    if not actor or not isinstance(actor, dict):
        return False, "Actor profile missing"
    
    role = actor.get("role", "")
    owns_project = actor.get("owns_project", False)

    # Teachers and staff can mentor/review
    if role in ("teacher", "admin", "staff"):
        return True, "Authorized staff role"

    # Students must own their project to exercise learner agency
    if owns_project:
        return True, "Learner owns project"

    return False, "Vai trò không được chỉnh sửa"


def check_optimistic_concurrency(
    expected_version: int | None,
    current_version: int | None,
) -> tuple[bool, str]:
    """Verify no concurrent/stale edits have caused revision conflict."""
    if expected_version is None or current_version is None:
        return False, "Version information missing"
    
    if expected_version == current_version:
        return True, "Version aligned"
    
    return False, "Hai phiên chỉnh sửa xung đột"


def validate_reflection_completion(
    project: dict[str, Any] | None,
    transition: dict[str, Any] | None,
) -> tuple[bool, str]:
    """Verify self-reflection is completed before advancing to final stages."""
    if not project or not isinstance(project, dict):
        return False, "Project state missing"
    if not transition or not isinstance(transition, dict):
        return False, "Transition details missing"

    action = transition.get("action", "")
    reflection_completed = project.get("reflection_completed", False)

    if action == "submit" and not reflection_completed:
        return False, "Nộp trước khi có phản tư cần thiết"

    return True, "Reflection requirement satisfied"


def validate_revision_rationale(
    transition: dict[str, Any] | None,
) -> tuple[bool, str]:
    """Verify material revisions have an articulate pedagogical rationale."""
    if not transition or not isinstance(transition, dict):
        return False, "Transition details missing"

    action = transition.get("action", "")
    rationale = transition.get("rationale")

    # Revisions require non-empty rationale
    if action == "revise_plan":
        if rationale is None or not str(rationale).strip():
            return False, "Thiếu lí do điều chỉnh"

    return True, "Rationale provided"


def evaluate_srl_cycle(
    scenario_input: dict[str, Any],
    *,
    enforce_ownership: bool = True,
    enforce_concurrency: bool = True,
    enforce_reflection_gate: bool = True,
    enforce_rationale: bool = True,
    policy_version: str = "study-ln10-v1",
) -> TransitionEvaluationResult:
    """Pure domain evaluation of an SRL transition request."""
    if not isinstance(scenario_input, dict):
        scenario_input = {}
    actor = scenario_input.get("actor", {})
    project = scenario_input.get("project", {})
    transition = scenario_input.get("transition", {})

    current_version = project.get("version")
    expected_version = transition.get("expected_version")
    refl_completed = project.get("reflection_completed", False)

    # 1. Project Ownership / Actor Authorization
    if enforce_ownership:
        owner_ok, owner_msg = verify_project_ownership(actor)
        if not owner_ok:
            return TransitionEvaluationResult(
                decision=DecisionCode.DENY_TRANSITION,
                reason_codes=[ReasonCode.UNAUTHORIZED_ACTOR.value, owner_msg],
                policy_version=policy_version,
                transition_applied=False,
                conflict_detected=False,
                reflection_completed=refl_completed,
                ownership_verified=False,
                explanation=owner_msg,
            )

    # 2. Optimistic Concurrency Control
    if enforce_concurrency:
        ver_ok, ver_msg = check_optimistic_concurrency(expected_version, current_version)
        if not ver_ok:
            return TransitionEvaluationResult(
                decision=DecisionCode.RESOLVE_REVISION_CONFLICT,
                reason_codes=[ReasonCode.OFFLINE_CONFLICT.value, ver_msg],
                policy_version=policy_version,
                transition_applied=False,
                conflict_detected=True,
                reflection_completed=refl_completed,
                ownership_verified=True,
                explanation=ver_msg,
            )

    # 3. Reflection Requirement for Submissions / Advances
    if enforce_reflection_gate:
        refl_ok, refl_msg = validate_reflection_completion(project, transition)
        if not refl_ok:
            return TransitionEvaluationResult(
                decision=DecisionCode.REJECT_PREMATURE_SUBMIT,
                reason_codes=[ReasonCode.SKIPPED_REFLECTION.value, refl_msg],
                policy_version=policy_version,
                transition_applied=False,
                conflict_detected=False,
                reflection_completed=False,
                ownership_verified=True,
                explanation=refl_msg,
            )

    # 4. Rationale Requirement for Material Revisions
    if enforce_rationale:
        rat_ok, rat_msg = validate_revision_rationale(transition)
        if not rat_ok:
            return TransitionEvaluationResult(
                decision=DecisionCode.REQUEST_REFLECTION,
                reason_codes=[ReasonCode.MISSING_RATIONALE.value, rat_msg],
                policy_version=policy_version,
                transition_applied=False,
                conflict_detected=False,
                reflection_completed=False,
                ownership_verified=True,
                explanation=rat_msg,
            )

    # 5. Nominal Authorized Transition
    return TransitionEvaluationResult(
        decision=DecisionCode.ALLOW_AUTHORIZED_TRANSITION,
        reason_codes=[ReasonCode.NOMINAL_AUTHORIZED.value, "Có mục tiêu, xác nhận và lí do"],
        policy_version=policy_version,
        transition_applied=True,
        conflict_detected=False,
        reflection_completed=True,
        ownership_verified=True,
        explanation="Có mục tiêu, xác nhận và lí do",
    )
