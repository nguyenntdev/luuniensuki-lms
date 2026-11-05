# -*- coding: utf-8 -*-
"""Peer / Group Historical Inquiry Service (V5-T038 / Wave W03, Slot A08).

Implements collaborative source evidence synthesis, teacher moderation, and
privacy isolation for historical inquiry activities.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..apischemas.history_inquiry import (
    AddGroupMemberIn,
    BoardRequestRevisionIn,
    BoardResubmitIn,
    ComparativeLinkCreate,
    HistoricalInquiryActivityCreate,
    HistoricalInquiryGroupCreate,
    HistoricalInquirySubmissionUpdate,
    HistoricalInquiryTeacherModerationIn,
    InquiryBoardCardCreate,
    InquiryBoardCardUpdate,
    InquiryEvidenceItemIn,
    TeacherInlineFeedbackCreate,
)
from ..errors import AppError
from ..history_inquiry_models import (
    HistoricalInquiryActivity,
    HistoricalInquiryGroup,
    HistoricalInquiryGroupMember,
    HistoricalInquirySubmission,
    InquiryMemberRole,
    InquiryPrivacyMode,
    InquirySubmissionStatus,
)
from ..history_models import HistoricalClaim, HistoricalSource
from ..models import ClassMember, Classroom, User, UserRole
from ..rbac import ADMIN_ROLES, STAFF_ROLES


def is_teacher_or_staff(user: User, classroom: Optional[Classroom] = None) -> bool:
    """Check if user has teacher/curator authority over classroom or globally."""
    if user.role in ADMIN_ROLES:
        return True
    if classroom:
        return bool(user.role == UserRole.teacher and classroom.teacher_id == user.id)
    return bool(user.role in STAFF_ROLES)


def is_classroom_enrolled(db: Session, user: User, classroom_id: UUID) -> bool:
    """Check if student is enrolled in classroom or is the classroom teacher/admin."""
    if user.role in ADMIN_ROLES:
        return True
    classroom = db.get(Classroom, classroom_id)
    if classroom and user.role == UserRole.teacher and classroom.teacher_id == user.id:
        return True
    member = db.execute(
        select(ClassMember).where(
            ClassMember.class_id == classroom_id,
            ClassMember.user_id == user.id,
        )
    ).scalar_one_or_none()
    return member is not None


def is_group_member(db: Session, user_id: UUID, group_id: UUID) -> bool:
    """Check if user is a registered member of the inquiry group."""
    member = db.execute(
        select(HistoricalInquiryGroupMember).where(
            HistoricalInquiryGroupMember.group_id == group_id,
            HistoricalInquiryGroupMember.user_id == user_id,
        )
    ).scalar_one_or_none()
    return member is not None


# --------------------------------------------------------------------------- #
# Activities
# --------------------------------------------------------------------------- #
def create_inquiry_activity(
    db: Session,
    user: User,
    payload: HistoricalInquiryActivityCreate,
) -> HistoricalInquiryActivity:
    """Create a new historical inquiry activity scoped to a classroom or global."""
    classroom = None
    if payload.classroom_id:
        classroom = db.get(Classroom, payload.classroom_id)
        if not classroom:
            raise AppError("CLASSROOM_NOT_FOUND", "Classroom not found", 404)
        if not is_teacher_or_staff(user, classroom):
            raise AppError(
                "FORBIDDEN_SCOPE",
                "Only classroom teacher or staff can create inquiry activities for this class",
                403,
            )

    # Validate suggested sources exist
    if payload.suggested_source_ids:
        for sid in payload.suggested_source_ids:
            source = db.get(HistoricalSource, sid)
            if not source:
                raise AppError("SOURCE_NOT_FOUND", f"Suggested historical source '{sid}' not found", 404)

    # Validate suggested claims exist
    if payload.suggested_claim_ids:
        for cid in payload.suggested_claim_ids:
            claim = db.get(HistoricalClaim, cid)
            if not claim:
                raise AppError("CLAIM_NOT_FOUND", f"Suggested historical claim '{cid}' not found", 404)

    activity = HistoricalInquiryActivity(
        classroom_id=payload.classroom_id,
        title=payload.title,
        description=payload.description,
        guiding_questions=payload.guiding_questions or [],
        suggested_source_ids=[str(s) for s in (payload.suggested_source_ids or [])],
        suggested_claim_ids=[str(c) for c in (payload.suggested_claim_ids or [])],
        rubric_criteria=payload.rubric_criteria or {},
        created_by_id=user.id,
        due_at=payload.due_at,
        is_active=payload.is_active,
    )
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return activity


def list_inquiry_activities(
    db: Session,
    classroom_id: Optional[UUID] = None,
) -> list[HistoricalInquiryActivity]:
    """List inquiry activities optionally filtered by classroom."""
    stmt = select(HistoricalInquiryActivity).where(HistoricalInquiryActivity.is_active.is_(True))
    if classroom_id:
        stmt = stmt.where(HistoricalInquiryActivity.classroom_id == classroom_id)
    stmt = stmt.order_by(HistoricalInquiryActivity.created_at.desc())
    return list(db.execute(stmt).scalars().all())


def get_inquiry_activity(db: Session, activity_id: UUID) -> HistoricalInquiryActivity:
    """Retrieve inquiry activity details."""
    activity = db.get(HistoricalInquiryActivity, activity_id)
    if not activity:
        raise AppError("ACTIVITY_NOT_FOUND", "Historical inquiry activity not found", 404)
    return activity


# --------------------------------------------------------------------------- #
# Groups & Membership
# --------------------------------------------------------------------------- #
def create_inquiry_group(
    db: Session,
    user: User,
    activity_id: UUID,
    payload: HistoricalInquiryGroupCreate,
) -> HistoricalInquiryGroup:
    """Create a collaborative group for an inquiry activity and initialize draft submission."""
    activity = get_inquiry_activity(db, activity_id)

    # If classroom-scoped, ensure creator has access
    if activity.classroom_id and not is_classroom_enrolled(db, user, activity.classroom_id):
        raise AppError("FORBIDDEN_SCOPE", "User is not enrolled in the classroom for this inquiry", 403)

    group = HistoricalInquiryGroup(
        activity_id=activity.id,
        classroom_id=activity.classroom_id,
        name=payload.name,
        created_by_id=user.id,
    )
    db.add(group)
    db.flush()

    # Add creator as leader
    leader_member = HistoricalInquiryGroupMember(
        group_id=group.id,
        user_id=user.id,
        role=InquiryMemberRole.leader.value,
    )
    db.add(leader_member)

    # Add other invited members
    if payload.member_ids:
        for mid in payload.member_ids:
            if mid == user.id:
                continue
            if activity.classroom_id and not is_classroom_enrolled(db, db.get(User, mid), activity.classroom_id):
                raise AppError("USER_NOT_ENROLLED", f"User {mid} is not enrolled in this classroom", 400)
            member = HistoricalInquiryGroupMember(
                group_id=group.id,
                user_id=mid,
                role=InquiryMemberRole.contributor.value,
            )
            db.add(member)

    # Initialize blank collaborative submission
    submission = HistoricalInquirySubmission(
        group_id=group.id,
        activity_id=activity.id,
        hypothesis="",
        synthesis_argument="",
        epistemic_rating="dang_khao_cuu",
        evidence_items=[],
        status=InquirySubmissionStatus.draft.value,
        privacy_mode=InquiryPrivacyMode.private_group.value,
    )
    db.add(submission)
    db.commit()
    db.refresh(group)
    return group


def list_inquiry_groups(
    db: Session,
    activity_id: UUID,
) -> list[HistoricalInquiryGroup]:
    """List groups participating in an inquiry activity."""
    stmt = (
        select(HistoricalInquiryGroup)
        .options(
            selectinload(HistoricalInquiryGroup.members).selectinload(HistoricalInquiryGroupMember.user),
            selectinload(HistoricalInquiryGroup.submission),
        )
        .where(HistoricalInquiryGroup.activity_id == activity_id)
        .order_by(HistoricalInquiryGroup.created_at.asc())
    )
    return list(db.execute(stmt).scalars().all())


def add_group_member(
    db: Session,
    user: User,
    group_id: UUID,
    payload: AddGroupMemberIn,
) -> HistoricalInquiryGroupMember:
    """Add a member to an inquiry group (must be group member, teacher, or staff)."""
    group = db.get(HistoricalInquiryGroup, group_id)
    if not group:
        raise AppError("GROUP_NOT_FOUND", "Inquiry group not found", 404)

    classroom = db.get(Classroom, group.classroom_id) if group.classroom_id else None
    if not (is_group_member(db, user.id, group.id) or is_teacher_or_staff(user, classroom)):
        raise AppError("FORBIDDEN_SCOPE", "Not authorized to manage members of this group", 403)

    target_user = db.get(User, payload.user_id)
    if not target_user:
        raise AppError("USER_NOT_FOUND", "User not found", 404)

    if group.classroom_id and not is_classroom_enrolled(db, target_user, group.classroom_id):
        raise AppError("USER_NOT_ENROLLED", "Target user is not enrolled in this classroom", 400)

    existing = db.execute(
        select(HistoricalInquiryGroupMember).where(
            HistoricalInquiryGroupMember.group_id == group_id,
            HistoricalInquiryGroupMember.user_id == payload.user_id,
        )
    ).scalar_one_or_none()
    if existing:
        return existing

    member = HistoricalInquiryGroupMember(
        group_id=group_id,
        user_id=payload.user_id,
        role=payload.role,
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    return member


# --------------------------------------------------------------------------- #
# Submissions & Collaborative Synthesis
# --------------------------------------------------------------------------- #
def get_group_submission(
    db: Session,
    user: User,
    group_id: UUID,
) -> HistoricalInquirySubmission:
    """Retrieve group inquiry submission enforcing privacy isolation."""
    group = db.get(HistoricalInquiryGroup, group_id)
    if not group:
        raise AppError("GROUP_NOT_FOUND", "Inquiry group not found", 404)

    stmt = select(HistoricalInquirySubmission).where(HistoricalInquirySubmission.group_id == group_id)
    submission = db.execute(stmt).scalar_one_or_none()
    if not submission:
        # Create draft if missing
        submission = HistoricalInquirySubmission(
            group_id=group.id,
            activity_id=group.activity_id,
            hypothesis="",
            synthesis_argument="",
            epistemic_rating="dang_khao_cuu",
            evidence_items=[],
            status=InquirySubmissionStatus.draft.value,
            privacy_mode=InquiryPrivacyMode.private_group.value,
        )
        db.add(submission)
        db.commit()
        db.refresh(submission)

    # Privacy Isolation check
    classroom = db.get(Classroom, group.classroom_id) if group.classroom_id else None
    user_is_member = is_group_member(db, user.id, group.id)
    user_is_teacher = is_teacher_or_staff(user, classroom)

    if not (user_is_member or user_is_teacher):
        # User is an outside student
        if submission.privacy_mode == InquiryPrivacyMode.private_group.value or submission.status == InquirySubmissionStatus.draft.value:
            raise AppError(
                "FORBIDDEN_SCOPE",
                "This inquiry draft is private to group members and the teacher",
                403,
            )
        # If class_visible and submitted/approved, verify caller belongs to same class
        if group.classroom_id and not is_classroom_enrolled(db, user, group.classroom_id):
            raise AppError("FORBIDDEN_SCOPE", "Access restricted to classroom peers", 403)

    return submission


def update_group_submission(
    db: Session,
    user: User,
    group_id: UUID,
    payload: HistoricalInquirySubmissionUpdate,
) -> HistoricalInquirySubmission:
    """Update collaborative inquiry draft.

    Strict Negative Abuse: ONLY group members can alter their group's collaborative submission!
    """
    group = db.get(HistoricalInquiryGroup, group_id)
    if not group:
        raise AppError("GROUP_NOT_FOUND", "Inquiry group not found", 404)

    # STRICT NEGATIVE ABUSE CHECK
    if not is_group_member(db, user.id, group.id):
        raise AppError(
            "FORBIDDEN_SCOPE",
            "Negative abuse violation: Group member cannot alter another group's collaborative inquiry submission",
            403,
        )

    submission = db.execute(
        select(HistoricalInquirySubmission).where(HistoricalInquirySubmission.group_id == group_id)
    ).scalar_one_or_none()
    if not submission:
        raise AppError("SUBMISSION_NOT_FOUND", "Inquiry submission not found", 404)

    # Status lock check
    if submission.status in (InquirySubmissionStatus.submitted.value, InquirySubmissionStatus.approved.value):
        raise AppError(
            "SUBMISSION_LOCKED",
            f"Cannot alter submission while in '{submission.status}' status. Await teacher review or revision request.",
            400,
        )

    # Epistemic rigor validation: Cannot claim verified status without evidence
    new_rating = payload.epistemic_rating or submission.epistemic_rating
    if new_rating == "su_lieu_xac_thuc" and len(submission.evidence_items or []) == 0:
        raise AppError(
            "INSUFFICIENT_EVIDENCE",
            "Cannot set epistemic rating to 'su_lieu_xac_thuc' (Sử liệu xác thực) without backing primary source citations",
            422,
        )

    if payload.hypothesis is not None:
        submission.hypothesis = payload.hypothesis
    if payload.synthesis_argument is not None:
        submission.synthesis_argument = payload.synthesis_argument
    if payload.epistemic_rating is not None:
        submission.epistemic_rating = payload.epistemic_rating
    if payload.privacy_mode is not None:
        submission.privacy_mode = payload.privacy_mode

    submission.version += 1
    submission.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(submission)
    return submission


def add_evidence_item(
    db: Session,
    user: User,
    group_id: UUID,
    payload: InquiryEvidenceItemIn,
) -> dict[str, Any]:
    """Add a verified source evidence citation to the group's collaborative synthesis.

    Strict Negative Abuse: ONLY group members can add evidence to their inquiry submission.
    """
    group = db.get(HistoricalInquiryGroup, group_id)
    if not group:
        raise AppError("GROUP_NOT_FOUND", "Inquiry group not found", 404)

    # STRICT NEGATIVE ABUSE CHECK
    if not is_group_member(db, user.id, group.id):
        raise AppError(
            "FORBIDDEN_SCOPE",
            "Negative abuse violation: Group member cannot alter another group's collaborative inquiry submission",
            403,
        )

    submission = db.execute(
        select(HistoricalInquirySubmission).where(HistoricalInquirySubmission.group_id == group_id)
    ).scalar_one_or_none()
    if not submission:
        raise AppError("SUBMISSION_NOT_FOUND", "Inquiry submission not found", 404)

    if submission.status in (InquirySubmissionStatus.submitted.value, InquirySubmissionStatus.approved.value):
        raise AppError("SUBMISSION_LOCKED", "Cannot alter evidence while submission is locked", 400)

    # Authoritative source verification
    source = db.get(HistoricalSource, payload.source_id)
    if not source:
        raise AppError("SOURCE_NOT_FOUND", f"Authoritative historical source '{payload.source_id}' not found", 404)

    # Authoritative claim verification (if provided)
    claim = None
    if payload.claim_id:
        claim = db.get(HistoricalClaim, payload.claim_id)
        if not claim:
            raise AppError("CLAIM_NOT_FOUND", f"Authoritative historical claim '{payload.claim_id}' not found", 404)

    evidence_item = {
        "id": str(uuid.uuid4()),
        "source_id": str(source.id),
        "source_title": source.title,
        "author": source.author_text,
        "locator": payload.locator,
        "excerpt": payload.excerpt,
        "claim_id": str(claim.id) if claim else None,
        "claim_title": claim.statement_vi if claim else None,
        "support_type": payload.support_type,
        "interpretation_note": payload.interpretation_note,
        "contributed_by_user_id": str(user.id),
        "contributed_by_name": user.display_name or user.username or "Anonymous Peer",
        "contributed_at": datetime.now(timezone.utc).isoformat(),
    }

    current_items = list(submission.evidence_items or [])
    current_items.append(evidence_item)
    submission.evidence_items = current_items
    submission.version += 1
    submission.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(submission)
    return evidence_item


def remove_evidence_item(
    db: Session,
    user: User,
    group_id: UUID,
    evidence_id: str,
) -> HistoricalInquirySubmission:
    """Remove an evidence citation from group submission. Only group members allowed."""
    group = db.get(HistoricalInquiryGroup, group_id)
    if not group:
        raise AppError("GROUP_NOT_FOUND", "Inquiry group not found", 404)

    if not is_group_member(db, user.id, group.id):
        raise AppError(
            "FORBIDDEN_SCOPE",
            "Negative abuse violation: Group member cannot alter another group's collaborative inquiry submission",
            403,
        )

    submission = db.execute(
        select(HistoricalInquirySubmission).where(HistoricalInquirySubmission.group_id == group_id)
    ).scalar_one_or_none()
    if not submission:
        raise AppError("SUBMISSION_NOT_FOUND", "Inquiry submission not found", 404)

    if submission.status in (InquirySubmissionStatus.submitted.value, InquirySubmissionStatus.approved.value):
        raise AppError("SUBMISSION_LOCKED", "Cannot alter evidence while submission is locked", 400)

    current_items = list(submission.evidence_items or [])
    filtered_items = [item for item in current_items if item.get("id") != evidence_id]
    if len(filtered_items) == len(current_items):
        raise AppError("EVIDENCE_NOT_FOUND", f"Evidence item '{evidence_id}' not found", 404)

    submission.evidence_items = filtered_items
    submission.version += 1
    submission.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(submission)
    return submission


def submit_group_inquiry(
    db: Session,
    user: User,
    group_id: UUID,
) -> HistoricalInquirySubmission:
    """Submit the group's collaborative synthesis for teacher review and grading."""
    group = db.get(HistoricalInquiryGroup, group_id)
    if not group:
        raise AppError("GROUP_NOT_FOUND", "Inquiry group not found", 404)

    if not is_group_member(db, user.id, group.id):
        raise AppError(
            "FORBIDDEN_SCOPE",
            "Negative abuse violation: Group member cannot submit another group's inquiry",
            403,
        )

    submission = db.execute(
        select(HistoricalInquirySubmission).where(HistoricalInquirySubmission.group_id == group_id)
    ).scalar_one_or_none()
    if not submission:
        raise AppError("SUBMISSION_NOT_FOUND", "Inquiry submission not found", 404)

    # Minimum scientific inquiry completeness check
    if not submission.hypothesis.strip():
        raise AppError("INCOMPLETE_SUBMISSION", "Research hypothesis cannot be blank", 422)
    if not submission.synthesis_argument.strip():
        raise AppError("INCOMPLETE_SUBMISSION", "Historical synthesis argument cannot be blank", 422)
    if len(submission.evidence_items or []) == 0:
        raise AppError("INSUFFICIENT_EVIDENCE", "Must synthesize at least one verified primary source evidence citation", 422)

    submission.status = InquirySubmissionStatus.submitted.value
    submission.submitted_at = datetime.now(timezone.utc)
    submission.submitted_by_id = user.id
    hist = list(submission.revision_history or [])
    hist.append({
        "cycle": submission.revision_cycle,
        "action": "submitted",
        "actor_id": str(user.id),
        "actor_name": user.display_name or user.username or "Student",
        "notes": "Collaborative inquiry submission",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    submission.revision_history = hist
    submission.version += 1
    submission.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(submission)
    return submission


def moderate_inquiry_submission(
    db: Session,
    user: User,
    submission_id: UUID,
    payload: HistoricalInquiryTeacherModerationIn,
) -> HistoricalInquirySubmission:
    """Teacher moderation & feedback for group inquiry submission.

    Strict Role Check: Caller must be the classroom teacher or staff/admin.
    """
    submission = db.get(HistoricalInquirySubmission, submission_id)
    if not submission:
        raise AppError("SUBMISSION_NOT_FOUND", "Inquiry submission not found", 404)

    group = db.get(HistoricalInquiryGroup, submission.group_id)
    classroom = db.get(Classroom, group.classroom_id) if group and group.classroom_id else None

    # TEACHER/STAFF ROLE CHECK
    if not is_teacher_or_staff(user, classroom):
        raise AppError(
            "FORBIDDEN_SCOPE",
            "Only classroom teacher or staff can moderate and grade inquiry submissions",
            403,
        )

    submission.status = payload.status
    submission.teacher_feedback = payload.teacher_feedback
    submission.score = payload.score
    if payload.rubric_evaluation:
        submission.rubric_evaluation = payload.rubric_evaluation

    submission.moderated_by_id = user.id
    submission.moderated_at = datetime.now(timezone.utc)
    hist = list(submission.revision_history or [])
    hist.append({
        "cycle": submission.revision_cycle,
        "action": payload.status,
        "actor_id": str(user.id),
        "actor_name": user.display_name or user.username or "Teacher",
        "notes": payload.teacher_feedback,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    submission.revision_history = hist
    submission.version += 1
    submission.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(submission)
    return submission


# --------------------------------------------------------------------------- #
# Evidence Board for Groups (V5-T093 / Wave W09, Slot A03)
# --------------------------------------------------------------------------- #
def get_inquiry_board(
    db: Session,
    user: User,
    group_id: UUID,
) -> dict[str, Any]:
    """Retrieve full collaborative evidence board with support/refute cards, comparative links, and teacher feedback."""
    group = db.get(HistoricalInquiryGroup, group_id)
    if not group:
        raise AppError("GROUP_NOT_FOUND", "Inquiry group not found", 404)

    activity = db.get(HistoricalInquiryActivity, group.activity_id)
    if not activity:
        raise AppError("ACTIVITY_NOT_FOUND", "Inquiry activity not found", 404)

    submission = get_group_submission(db, user, group_id)

    # Collect and format cards with inline feedback
    raw_cards = list(submission.evidence_items or [])
    raw_feedback = list(submission.inline_feedback or [])

    formatted_cards = []
    for idx, card in enumerate(raw_cards):
        cid = str(card.get("id", ""))
        card_feedback = [
            fb for fb in raw_feedback
            if fb.get("target_type") == "card" and str(fb.get("target_id")) == cid
        ]
        support_type = str(card.get("support_type", "supports"))
        default_col = "supporting" if support_type == "supports" else "refuting" if support_type == "refutes" else "unresolved"
        formatted_cards.append({
            "id": cid,
            "source_id": str(card.get("source_id", "")),
            "source_title": str(card.get("source_title", "")),
            "author": card.get("author"),
            "locator": str(card.get("locator", "")),
            "excerpt": str(card.get("excerpt", "")),
            "claim_id": str(card["claim_id"]) if card.get("claim_id") else None,
            "claim_title": card.get("claim_title"),
            "support_type": support_type,
            "board_column": str(card.get("board_column", default_col)),
            "position": int(card.get("position", idx)),
            "linked_evidence_id": str(card["linked_evidence_id"]) if card.get("linked_evidence_id") else None,
            "comparison_notes": card.get("comparison_notes"),
            "inline_feedback": card_feedback,
            "interpretation_note": str(card.get("interpretation_note", "")),
            "contributed_by_user_id": str(card.get("contributed_by_user_id", "")),
            "contributed_by_name": str(card.get("contributed_by_name", "Anonymous")),
            "contributed_at": str(card.get("contributed_at", "")),
        })

    return {
        "group_id": group.id,
        "group_name": group.name,
        "activity_id": activity.id,
        "activity_title": activity.title,
        "hypothesis": submission.hypothesis or "",
        "synthesis_argument": submission.synthesis_argument or "",
        "epistemic_rating": submission.epistemic_rating or "dang_khao_cuu",
        "status": submission.status,
        "privacy_mode": submission.privacy_mode,
        "revision_cycle": getattr(submission, "revision_cycle", 1) or 1,
        "version": submission.version,
        "columns": ["supporting", "refuting", "synthesis", "unresolved"],
        "cards": formatted_cards,
        "comparative_links": list(submission.comparative_links or []),
        "inline_feedback": raw_feedback,
        "revision_history": list(submission.revision_history or []),
        "teacher_feedback": submission.teacher_feedback,
        "score": submission.score,
        "rubric_evaluation": submission.rubric_evaluation or {},
        "updated_at": submission.updated_at,
    }


def add_board_card(
    db: Session,
    user: User,
    group_id: UUID,
    payload: InquiryBoardCardCreate,
) -> dict[str, Any]:
    """Add an evidence card to the collaborative inquiry board.

    Strict Negative Abuse: Students outside the group cannot edit or inject evidence into the board (403 Forbidden).
    """
    group = db.get(HistoricalInquiryGroup, group_id)
    if not group:
        raise AppError("GROUP_NOT_FOUND", "Inquiry group not found", 404)

    # STRICT NEGATIVE ABUSE CHECK
    if not is_group_member(db, user.id, group.id):
        raise AppError(
            "FORBIDDEN_SCOPE",
            "Negative abuse violation: Group member cannot alter another group's collaborative inquiry submission",
            403,
        )

    submission = db.execute(
        select(HistoricalInquirySubmission).where(HistoricalInquirySubmission.group_id == group_id)
    ).scalar_one_or_none()
    if not submission:
        raise AppError("SUBMISSION_NOT_FOUND", "Inquiry submission not found", 404)

    if submission.status in (InquirySubmissionStatus.submitted.value, InquirySubmissionStatus.approved.value):
        raise AppError("SUBMISSION_LOCKED", "Cannot alter evidence while submission is locked", 400)

    # Validate source exists
    source = db.get(HistoricalSource, payload.source_id)
    if not source:
        raise AppError("SOURCE_NOT_FOUND", f"Authoritative historical source '{payload.source_id}' not found", 404)

    # Validate claim exists (if provided)
    claim = None
    if payload.claim_id:
        claim = db.get(HistoricalClaim, payload.claim_id)
        if not claim:
            raise AppError("CLAIM_NOT_FOUND", f"Authoritative historical claim '{payload.claim_id}' not found", 404)

    # Auto-assign column if omitted
    col = payload.board_column
    if not col:
        if payload.support_type == "supports":
            col = "supporting"
        elif payload.support_type == "refutes":
            col = "refuting"
        elif payload.support_type == "disputed":
            col = "unresolved"
        else:
            col = "synthesis"

    card_id = str(uuid.uuid4())
    current_items = list(submission.evidence_items or [])
    pos = payload.position if payload.position is not None else len(current_items)

    card = {
        "id": card_id,
        "source_id": str(source.id),
        "source_title": source.title,
        "author": source.author_text,
        "locator": payload.locator,
        "excerpt": payload.excerpt,
        "claim_id": str(claim.id) if claim else None,
        "claim_title": claim.statement_vi if claim else None,
        "support_type": payload.support_type,
        "board_column": col,
        "position": pos,
        "linked_evidence_id": payload.linked_evidence_id,
        "comparison_notes": payload.comparison_notes,
        "interpretation_note": payload.interpretation_note,
        "contributed_by_user_id": str(user.id),
        "contributed_by_name": user.display_name or user.username or "Anonymous Peer",
        "contributed_at": datetime.now(timezone.utc).isoformat(),
    }

    current_items.append(card)
    submission.evidence_items = current_items
    submission.version += 1
    submission.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(submission)

    card["inline_feedback"] = []
    return card


def update_board_card(
    db: Session,
    user: User,
    group_id: UUID,
    card_id: str,
    payload: InquiryBoardCardUpdate,
) -> dict[str, Any]:
    """Update evidence card positioning, column, comparative notes, or interpretation on the board.

    Strict Negative Abuse: Only group members can alter board cards (403 Forbidden).
    """
    group = db.get(HistoricalInquiryGroup, group_id)
    if not group:
        raise AppError("GROUP_NOT_FOUND", "Inquiry group not found", 404)

    if not is_group_member(db, user.id, group.id):
        raise AppError(
            "FORBIDDEN_SCOPE",
            "Negative abuse violation: Group member cannot alter another group's collaborative inquiry submission",
            403,
        )

    submission = db.execute(
        select(HistoricalInquirySubmission).where(HistoricalInquirySubmission.group_id == group_id)
    ).scalar_one_or_none()
    if not submission:
        raise AppError("SUBMISSION_NOT_FOUND", "Inquiry submission not found", 404)

    if submission.status in (InquirySubmissionStatus.submitted.value, InquirySubmissionStatus.approved.value):
        raise AppError("SUBMISSION_LOCKED", "Cannot alter evidence while submission is locked", 400)

    current_items = list(submission.evidence_items or [])
    card_index = -1
    for idx, c in enumerate(current_items):
        if c.get("id") == card_id:
            card_index = idx
            break

    if card_index < 0:
        raise AppError("EVIDENCE_NOT_FOUND", f"Evidence card '{card_id}' not found", 404)

    target_card = dict(current_items[card_index])
    if payload.support_type is not None:
        target_card["support_type"] = payload.support_type
    if payload.board_column is not None:
        target_card["board_column"] = payload.board_column
    if payload.position is not None:
        target_card["position"] = payload.position
    if payload.linked_evidence_id is not None:
        target_card["linked_evidence_id"] = payload.linked_evidence_id
    if payload.comparison_notes is not None:
        target_card["comparison_notes"] = payload.comparison_notes
    if payload.interpretation_note is not None:
        target_card["interpretation_note"] = payload.interpretation_note
    if payload.locator is not None:
        target_card["locator"] = payload.locator
    if payload.excerpt is not None:
        target_card["excerpt"] = payload.excerpt

    current_items[card_index] = target_card
    submission.evidence_items = current_items
    submission.version += 1
    submission.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(submission)

    raw_feedback = list(submission.inline_feedback or [])
    target_card["inline_feedback"] = [
        fb for fb in raw_feedback
        if fb.get("target_type") == "card" and str(fb.get("target_id")) == card_id
    ]
    return target_card


def remove_board_card(
    db: Session,
    user: User,
    group_id: UUID,
    card_id: str,
) -> bool:
    """Delete an evidence card from the board. Only group members allowed."""
    group = db.get(HistoricalInquiryGroup, group_id)
    if not group:
        raise AppError("GROUP_NOT_FOUND", "Inquiry group not found", 404)

    if not is_group_member(db, user.id, group.id):
        raise AppError(
            "FORBIDDEN_SCOPE",
            "Negative abuse violation: Group member cannot alter another group's collaborative inquiry submission",
            403,
        )

    submission = db.execute(
        select(HistoricalInquirySubmission).where(HistoricalInquirySubmission.group_id == group_id)
    ).scalar_one_or_none()
    if not submission:
        raise AppError("SUBMISSION_NOT_FOUND", "Inquiry submission not found", 404)

    if submission.status in (InquirySubmissionStatus.submitted.value, InquirySubmissionStatus.approved.value):
        raise AppError("SUBMISSION_LOCKED", "Cannot alter evidence while submission is locked", 400)

    current_items = list(submission.evidence_items or [])
    filtered_items = [c for c in current_items if c.get("id") != card_id]
    if len(filtered_items) == len(current_items):
        raise AppError("EVIDENCE_NOT_FOUND", f"Evidence card '{card_id}' not found", 404)

    submission.evidence_items = filtered_items
    submission.version += 1
    submission.updated_at = datetime.now(timezone.utc)
    db.commit()
    return True


def add_comparative_link(
    db: Session,
    user: User,
    group_id: UUID,
    payload: ComparativeLinkCreate,
) -> dict[str, Any]:
    """Create a comparative source evidence link between two sources or source and claim.

    Strict Negative Abuse: Students outside the group cannot create comparative links (403 Forbidden).
    """
    group = db.get(HistoricalInquiryGroup, group_id)
    if not group:
        raise AppError("GROUP_NOT_FOUND", "Inquiry group not found", 404)

    if not is_group_member(db, user.id, group.id):
        raise AppError(
            "FORBIDDEN_SCOPE",
            "Negative abuse violation: Group member cannot alter another group's collaborative inquiry submission",
            403,
        )

    submission = db.execute(
        select(HistoricalInquirySubmission).where(HistoricalInquirySubmission.group_id == group_id)
    ).scalar_one_or_none()
    if not submission:
        raise AppError("SUBMISSION_NOT_FOUND", "Inquiry submission not found", 404)

    if submission.status in (InquirySubmissionStatus.submitted.value, InquirySubmissionStatus.approved.value):
        raise AppError("SUBMISSION_LOCKED", "Cannot alter evidence while submission is locked", 400)

    source_a = db.get(HistoricalSource, payload.source_id_a)
    if not source_a:
        raise AppError("SOURCE_NOT_FOUND", f"Source A '{payload.source_id_a}' not found", 404)

    source_b = None
    if payload.source_id_b:
        source_b = db.get(HistoricalSource, payload.source_id_b)
        if not source_b:
            raise AppError("SOURCE_NOT_FOUND", f"Source B '{payload.source_id_b}' not found", 404)

    claim = None
    if payload.claim_id:
        claim = db.get(HistoricalClaim, payload.claim_id)
        if not claim:
            raise AppError("CLAIM_NOT_FOUND", f"Claim '{payload.claim_id}' not found", 404)

    link_id = str(uuid.uuid4())
    link = {
        "id": link_id,
        "source_id_a": str(source_a.id),
        "source_title_a": source_a.title,
        "source_id_b": str(source_b.id) if source_b else None,
        "source_title_b": source_b.title if source_b else None,
        "claim_id": str(claim.id) if claim else None,
        "claim_title": claim.statement_vi if claim else None,
        "relation_type": payload.relation_type,
        "rationale": payload.rationale,
        "created_by_user_id": str(user.id),
        "created_by_name": user.display_name or user.username or "Anonymous Peer",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    current_links = list(submission.comparative_links or [])
    current_links.append(link)
    submission.comparative_links = current_links
    submission.version += 1
    submission.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(submission)
    return link


def remove_comparative_link(
    db: Session,
    user: User,
    group_id: UUID,
    link_id: str,
) -> bool:
    """Remove a comparative link from the evidence board."""
    group = db.get(HistoricalInquiryGroup, group_id)
    if not group:
        raise AppError("GROUP_NOT_FOUND", "Inquiry group not found", 404)

    if not is_group_member(db, user.id, group.id):
        raise AppError(
            "FORBIDDEN_SCOPE",
            "Negative abuse violation: Group member cannot alter another group's collaborative inquiry submission",
            403,
        )

    submission = db.execute(
        select(HistoricalInquirySubmission).where(HistoricalInquirySubmission.group_id == group_id)
    ).scalar_one_or_none()
    if not submission:
        raise AppError("SUBMISSION_NOT_FOUND", "Inquiry submission not found", 404)

    if submission.status in (InquirySubmissionStatus.submitted.value, InquirySubmissionStatus.approved.value):
        raise AppError("SUBMISSION_LOCKED", "Cannot alter evidence while submission is locked", 400)

    current_links = list(submission.comparative_links or [])
    filtered_links = [l for l in current_links if l.get("id") != link_id]
    if len(filtered_links) == len(current_links):
        raise AppError("LINK_NOT_FOUND", f"Comparative link '{link_id}' not found", 404)

    submission.comparative_links = filtered_links
    submission.version += 1
    submission.updated_at = datetime.now(timezone.utc)
    db.commit()
    return True


def add_teacher_inline_feedback(
    db: Session,
    user: User,
    group_id: UUID,
    payload: TeacherInlineFeedbackCreate,
) -> dict[str, Any]:
    """Classroom teacher adds inline feedback annotation to an evidence card or board section.

    Strict Role Check: Students cannot post teacher feedback (403 Forbidden).
    """
    group = db.get(HistoricalInquiryGroup, group_id)
    if not group:
        raise AppError("GROUP_NOT_FOUND", "Inquiry group not found", 404)

    classroom = db.get(Classroom, group.classroom_id) if group.classroom_id else None
    if not is_teacher_or_staff(user, classroom):
        raise AppError(
            "FORBIDDEN_SCOPE",
            "Only classroom teacher or staff can provide inline feedback on inquiry board",
            403,
        )

    submission = db.execute(
        select(HistoricalInquirySubmission).where(HistoricalInquirySubmission.group_id == group_id)
    ).scalar_one_or_none()
    if not submission:
        raise AppError("SUBMISSION_NOT_FOUND", "Inquiry submission not found", 404)

    feedback_id = str(uuid.uuid4())
    fb = {
        "id": feedback_id,
        "target_type": payload.target_type,
        "target_id": payload.target_id,
        "teacher_id": str(user.id),
        "teacher_name": user.display_name or user.username or "Teacher",
        "comment": payload.comment,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "resolved": False,
    }

    current_fb = list(submission.inline_feedback or [])
    current_fb.append(fb)
    submission.inline_feedback = current_fb
    submission.version += 1
    submission.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(submission)
    return fb


def request_board_revision(
    db: Session,
    user: User,
    group_id: UUID,
    payload: BoardRequestRevisionIn,
) -> dict[str, Any]:
    """Classroom teacher requests revision on the evidence board, unlocking it for student revision.

    Strict Role Check: Only classroom teacher or staff (403 Forbidden for students).
    """
    group = db.get(HistoricalInquiryGroup, group_id)
    if not group:
        raise AppError("GROUP_NOT_FOUND", "Inquiry group not found", 404)

    classroom = db.get(Classroom, group.classroom_id) if group.classroom_id else None
    if not is_teacher_or_staff(user, classroom):
        raise AppError(
            "FORBIDDEN_SCOPE",
            "Only classroom teacher or staff can request revisions on inquiry board",
            403,
        )

    submission = db.execute(
        select(HistoricalInquirySubmission).where(HistoricalInquirySubmission.group_id == group_id)
    ).scalar_one_or_none()
    if not submission:
        raise AppError("SUBMISSION_NOT_FOUND", "Inquiry submission not found", 404)

    submission.status = InquirySubmissionStatus.revision_requested.value
    submission.teacher_feedback = payload.teacher_feedback
    if payload.score is not None:
        submission.score = payload.score
    if payload.rubric_evaluation:
        submission.rubric_evaluation = payload.rubric_evaluation

    submission.moderated_by_id = user.id
    submission.moderated_at = datetime.now(timezone.utc)

    hist = list(submission.revision_history or [])
    hist.append({
        "cycle": getattr(submission, "revision_cycle", 1) or 1,
        "action": "revision_requested",
        "actor_id": str(user.id),
        "actor_name": user.display_name or user.username or "Teacher",
        "notes": payload.revision_notes or payload.teacher_feedback,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    submission.revision_history = hist
    submission.version += 1
    submission.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(submission)
    return get_inquiry_board(db, user, group_id)


def resubmit_board(
    db: Session,
    user: User,
    group_id: UUID,
    payload: BoardResubmitIn,
) -> dict[str, Any]:
    """Group members resubmit evidence board after addressing teacher revisions.

    Strict Negative Abuse: Only group members can resubmit (403 Forbidden).
    """
    group = db.get(HistoricalInquiryGroup, group_id)
    if not group:
        raise AppError("GROUP_NOT_FOUND", "Inquiry group not found", 404)

    if not is_group_member(db, user.id, group.id):
        raise AppError(
            "FORBIDDEN_SCOPE",
            "Negative abuse violation: Group member cannot submit another group's inquiry",
            403,
        )

    submission = db.execute(
        select(HistoricalInquirySubmission).where(HistoricalInquirySubmission.group_id == group_id)
    ).scalar_one_or_none()
    if not submission:
        raise AppError("SUBMISSION_NOT_FOUND", "Inquiry submission not found", 404)

    if submission.status in (InquirySubmissionStatus.submitted.value, InquirySubmissionStatus.approved.value):
        raise AppError("SUBMISSION_LOCKED", f"Board already in '{submission.status}' status", 400)

    # Completeness check
    if not (submission.hypothesis or "").strip():
        raise AppError("INCOMPLETE_SUBMISSION", "Research hypothesis cannot be blank", 422)
    if not (submission.synthesis_argument or "").strip():
        raise AppError("INCOMPLETE_SUBMISSION", "Historical synthesis argument cannot be blank", 422)
    if len(submission.evidence_items or []) == 0:
        raise AppError("INSUFFICIENT_EVIDENCE", "Must synthesize at least one verified primary source evidence citation", 422)

    current_cycle = getattr(submission, "revision_cycle", 1) or 1
    new_cycle = current_cycle + 1
    submission.revision_cycle = new_cycle
    submission.status = InquirySubmissionStatus.submitted.value
    submission.submitted_at = datetime.now(timezone.utc)
    submission.submitted_by_id = user.id

    hist = list(submission.revision_history or [])
    hist.append({
        "cycle": new_cycle,
        "action": "resubmitted",
        "actor_id": str(user.id),
        "actor_name": user.display_name or user.username or "Student",
        "notes": payload.revision_notes or "Board resubmitted after addressing revision feedback",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    submission.revision_history = hist
    submission.version += 1
    submission.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(submission)
    return get_inquiry_board(db, user, group_id)


def get_board_revisions(
    db: Session,
    user: User,
    group_id: UUID,
) -> dict[str, Any]:
    """Retrieve audit trail of revision cycles for this inquiry group."""
    group = db.get(HistoricalInquiryGroup, group_id)
    if not group:
        raise AppError("GROUP_NOT_FOUND", "Inquiry group not found", 404)

    classroom = db.get(Classroom, group.classroom_id) if group.classroom_id else None
    user_is_member = is_group_member(db, user.id, group.id)
    user_is_teacher = is_teacher_or_staff(user, classroom)

    if not (user_is_member or user_is_teacher):
        raise AppError(
            "FORBIDDEN_SCOPE",
            "Negative abuse violation: Access to revision audit trail restricted to group members and teachers",
            403,
        )

    submission = db.execute(
        select(HistoricalInquirySubmission).where(HistoricalInquirySubmission.group_id == group_id)
    ).scalar_one_or_none()
    if not submission:
        raise AppError("SUBMISSION_NOT_FOUND", "Inquiry submission not found", 404)

    return {
        "group_id": group.id,
        "revision_cycle": getattr(submission, "revision_cycle", 1) or 1,
        "status": submission.status,
        "history": list(submission.revision_history or []),
    }
