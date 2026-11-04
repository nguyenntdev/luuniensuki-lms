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
    HistoricalInquiryActivityCreate,
    HistoricalInquiryGroupCreate,
    HistoricalInquirySubmissionUpdate,
    HistoricalInquiryTeacherModerationIn,
    InquiryEvidenceItemIn,
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
    submission.version += 1
    submission.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(submission)
    return submission
