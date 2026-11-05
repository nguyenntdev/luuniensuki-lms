# -*- coding: utf-8 -*-
"""Peer / Group Historical Inquiry Router (V5-T038 / Wave W03, Slot A08).

Exposes endpoints for collaborative primary source evidence synthesis,
inquiry group workspaces, privacy isolation, and teacher moderation.
"""
from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from ..apischemas.history_inquiry import (
    AddGroupMemberIn,
    BoardRequestRevisionIn,
    BoardResubmitIn,
    ComparativeLinkCreate,
    ComparativeLinkOut,
    HistoricalInquiryActivityCreate,
    HistoricalInquiryActivityOut,
    HistoricalInquiryGroupCreate,
    HistoricalInquiryGroupMemberOut,
    HistoricalInquiryGroupOut,
    HistoricalInquirySubmissionOut,
    HistoricalInquirySubmissionUpdate,
    HistoricalInquiryTeacherModerationIn,
    HistoricalInquiryTeacherModerationOut,
    InquiryBoardCardCreate,
    InquiryBoardCardOut,
    InquiryBoardCardUpdate,
    InquiryBoardOut,
    InquiryEvidenceItemIn,
    InquiryEvidenceItemOut,
    RevisionCycleOut,
    TeacherInlineFeedbackCreate,
    TeacherInlineFeedbackOut,
)
from ..db import get_db
from ..deps import get_current_user
from ..models import User
from ..services import history_inquiry as svc

router = APIRouter(prefix="/api/v1/history/inquiry", tags=["history-inquiry"])


def _group_to_out(group) -> HistoricalInquiryGroupOut:
    members_out = [
        HistoricalInquiryGroupMemberOut(
            id=m.id,
            user_id=m.user_id,
            display_name=m.user.display_name if m.user else None,
            username=m.user.username if m.user else None,
            role=m.role,
            joined_at=m.joined_at,
        )
        for m in (group.members or [])
    ]
    sub = group.submission
    return HistoricalInquiryGroupOut(
        id=group.id,
        activity_id=group.activity_id,
        classroom_id=group.classroom_id,
        name=group.name,
        created_by_id=group.created_by_id,
        members=members_out,
        submission_status=sub.status if sub else None,
        score=sub.score if sub else None,
        created_at=group.created_at,
    )


def _submission_to_out(submission) -> HistoricalInquirySubmissionOut:
    evidence_out = [
        InquiryEvidenceItemOut(
            id=str(item.get("id", "")),
            source_id=str(item.get("source_id", "")),
            source_title=str(item.get("source_title", "")),
            author=item.get("author"),
            locator=str(item.get("locator", "")),
            excerpt=str(item.get("excerpt", "")),
            claim_id=str(item["claim_id"]) if item.get("claim_id") else None,
            claim_title=item.get("claim_title"),
            support_type=str(item.get("support_type", "supports")),
            interpretation_note=str(item.get("interpretation_note", "")),
            contributed_by_user_id=str(item.get("contributed_by_user_id", "")),
            contributed_by_name=str(item.get("contributed_by_name", "Anonymous")),
            contributed_at=str(item.get("contributed_at", "")),
        )
        for item in (submission.evidence_items or [])
    ]
    comp_links = [
        ComparativeLinkOut(
            id=str(l.get("id", "")),
            source_id_a=str(l.get("source_id_a", "")),
            source_title_a=str(l.get("source_title_a", "")),
            source_id_b=str(l["source_id_b"]) if l.get("source_id_b") else None,
            source_title_b=l.get("source_title_b"),
            claim_id=str(l["claim_id"]) if l.get("claim_id") else None,
            claim_title=l.get("claim_title"),
            relation_type=str(l.get("relation_type", "supports")),
            rationale=str(l.get("rationale", "")),
            created_by_user_id=str(l.get("created_by_user_id", "")),
            created_by_name=str(l.get("created_by_name", "")),
            created_at=str(l.get("created_at", "")),
        )
        for l in (getattr(submission, "comparative_links", None) or [])
    ]
    inline_fb = [
        TeacherInlineFeedbackOut(
            id=str(f.get("id", "")),
            target_type=str(f.get("target_type", "card")),
            target_id=str(f["target_id"]) if f.get("target_id") else None,
            teacher_id=str(f.get("teacher_id", "")),
            teacher_name=str(f.get("teacher_name", "")),
            comment=str(f.get("comment", "")),
            created_at=str(f.get("created_at", "")),
            resolved=bool(f.get("resolved", False)),
        )
        for f in (getattr(submission, "inline_feedback", None) or [])
    ]
    return HistoricalInquirySubmissionOut(
        id=submission.id,
        group_id=submission.group_id,
        activity_id=submission.activity_id,
        hypothesis=submission.hypothesis or "",
        synthesis_argument=submission.synthesis_argument or "",
        epistemic_rating=submission.epistemic_rating or "dang_khao_cuu",
        evidence_items=evidence_out,
        comparative_links=comp_links,
        inline_feedback=inline_fb,
        revision_cycle=getattr(submission, "revision_cycle", 1) or 1,
        revision_history=list(getattr(submission, "revision_history", None) or []),
        status=submission.status,
        privacy_mode=submission.privacy_mode,
        submitted_at=submission.submitted_at,
        submitted_by_id=submission.submitted_by_id,
        moderated_by_id=submission.moderated_by_id,
        moderated_at=submission.moderated_at,
        teacher_feedback=submission.teacher_feedback,
        score=submission.score,
        rubric_evaluation=submission.rubric_evaluation,
        version=submission.version,
        created_at=submission.created_at,
        updated_at=submission.updated_at,
    )


# --------------------------------------------------------------------------- #
# Activities
# --------------------------------------------------------------------------- #
@router.post(
    "/activities",
    response_model=HistoricalInquiryActivityOut,
    status_code=status.HTTP_201_CREATED,
)
def create_activity(
    payload: HistoricalInquiryActivityCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    activity = svc.create_inquiry_activity(db, current_user, payload)
    return HistoricalInquiryActivityOut.model_validate(activity)


@router.get("/activities", response_model=list[HistoricalInquiryActivityOut])
def list_activities(
    classroom_id: Optional[UUID] = Query(None, description="Filter activities by classroom ID"),
    db: Session = Depends(get_db),
):
    activities = svc.list_inquiry_activities(db, classroom_id)
    return [HistoricalInquiryActivityOut.model_validate(a) for a in activities]


@router.get("/activities/{activity_id}", response_model=HistoricalInquiryActivityOut)
def get_activity(
    activity_id: UUID,
    db: Session = Depends(get_db),
):
    activity = svc.get_inquiry_activity(db, activity_id)
    return HistoricalInquiryActivityOut.model_validate(activity)


# --------------------------------------------------------------------------- #
# Groups & Membership
# --------------------------------------------------------------------------- #
@router.post(
    "/activities/{activity_id}/groups",
    response_model=HistoricalInquiryGroupOut,
    status_code=status.HTTP_201_CREATED,
)
def create_group(
    activity_id: UUID,
    payload: HistoricalInquiryGroupCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    group = svc.create_inquiry_group(db, current_user, activity_id, payload)
    return _group_to_out(group)


@router.get(
    "/activities/{activity_id}/groups",
    response_model=list[HistoricalInquiryGroupOut],
)
def list_groups(
    activity_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    groups = svc.list_inquiry_groups(db, activity_id)
    return [_group_to_out(g) for g in groups]


@router.post(
    "/groups/{group_id}/members",
    response_model=HistoricalInquiryGroupMemberOut,
    status_code=status.HTTP_201_CREATED,
)
def add_member(
    group_id: UUID,
    payload: AddGroupMemberIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    member = svc.add_group_member(db, current_user, group_id, payload)
    return HistoricalInquiryGroupMemberOut(
        id=member.id,
        user_id=member.user_id,
        display_name=member.user.display_name if member.user else None,
        username=member.user.username if member.user else None,
        role=member.role,
        joined_at=member.joined_at,
    )


# --------------------------------------------------------------------------- #
# Submissions & Evidence Synthesis
# --------------------------------------------------------------------------- #
@router.get(
    "/groups/{group_id}/submission",
    response_model=HistoricalInquirySubmissionOut,
)
def get_submission(
    group_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    submission = svc.get_group_submission(db, current_user, group_id)
    return _submission_to_out(submission)


@router.put(
    "/groups/{group_id}/submission",
    response_model=HistoricalInquirySubmissionOut,
)
def update_submission(
    group_id: UUID,
    payload: HistoricalInquirySubmissionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    submission = svc.update_group_submission(db, current_user, group_id, payload)
    return _submission_to_out(submission)


@router.post(
    "/groups/{group_id}/evidence",
    response_model=InquiryEvidenceItemOut,
    status_code=status.HTTP_201_CREATED,
)
def add_evidence(
    group_id: UUID,
    payload: InquiryEvidenceItemIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = svc.add_evidence_item(db, current_user, group_id, payload)
    return InquiryEvidenceItemOut(**item)


@router.delete(
    "/groups/{group_id}/evidence/{evidence_id}",
    response_model=HistoricalInquirySubmissionOut,
)
def remove_evidence(
    group_id: UUID,
    evidence_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    submission = svc.remove_evidence_item(db, current_user, group_id, evidence_id)
    return _submission_to_out(submission)


@router.post(
    "/groups/{group_id}/submit",
    response_model=HistoricalInquirySubmissionOut,
)
def submit_inquiry(
    group_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    submission = svc.submit_group_inquiry(db, current_user, group_id)
    return _submission_to_out(submission)


# --------------------------------------------------------------------------- #
# Teacher Moderation
# --------------------------------------------------------------------------- #
@router.post(
    "/submissions/{submission_id}/moderate",
    response_model=HistoricalInquiryTeacherModerationOut,
)
def moderate_submission(
    submission_id: UUID,
    payload: HistoricalInquiryTeacherModerationIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    submission = svc.moderate_inquiry_submission(db, current_user, submission_id, payload)
    return HistoricalInquiryTeacherModerationOut(
        submission_id=submission.id,
        status=submission.status,
        score=submission.score,
        teacher_feedback=submission.teacher_feedback or "",
        rubric_evaluation=submission.rubric_evaluation,
        moderated_at=submission.moderated_at or submission.updated_at,
        moderated_by_id=submission.moderated_by_id or current_user.id,
    )


# --------------------------------------------------------------------------- #
# Evidence Board for Groups (V5-T093 / Wave W09, Slot A03)
# --------------------------------------------------------------------------- #
@router.get(
    "/groups/{group_id}/board",
    response_model=InquiryBoardOut,
)
def get_group_board(
    group_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve full collaborative evidence board for group."""
    board_data = svc.get_inquiry_board(db, current_user, group_id)
    return InquiryBoardOut(**board_data)


@router.post(
    "/groups/{group_id}/board/cards",
    response_model=InquiryBoardCardOut,
    status_code=status.HTTP_201_CREATED,
)
def add_board_card(
    group_id: UUID,
    payload: InquiryBoardCardCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add an evidence card to the inquiry board."""
    card = svc.add_board_card(db, current_user, group_id, payload)
    return InquiryBoardCardOut(**card)


@router.put(
    "/groups/{group_id}/board/cards/{card_id}",
    response_model=InquiryBoardCardOut,
)
def update_board_card(
    group_id: UUID,
    card_id: str,
    payload: InquiryBoardCardUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update evidence card positioning, column, or comparative notes on board."""
    card = svc.update_board_card(db, current_user, group_id, card_id, payload)
    return InquiryBoardCardOut(**card)


@router.delete(
    "/groups/{group_id}/board/cards/{card_id}",
)
def remove_board_card(
    group_id: UUID,
    card_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove evidence card from board."""
    svc.remove_board_card(db, current_user, group_id, card_id)
    return {"success": True, "removed_card_id": card_id}


@router.post(
    "/groups/{group_id}/board/comparisons",
    response_model=ComparativeLinkOut,
    status_code=status.HTTP_201_CREATED,
)
def add_comparative_link(
    group_id: UUID,
    payload: ComparativeLinkCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add a comparative source evidence link to the board."""
    link = svc.add_comparative_link(db, current_user, group_id, payload)
    return ComparativeLinkOut(**link)


@router.delete(
    "/groups/{group_id}/board/comparisons/{comparison_id}",
)
def remove_comparative_link(
    group_id: UUID,
    comparison_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove a comparative source evidence link from the board."""
    svc.remove_comparative_link(db, current_user, group_id, comparison_id)
    return {"success": True, "removed_comparison_id": comparison_id}


@router.post(
    "/groups/{group_id}/board/feedback",
    response_model=TeacherInlineFeedbackOut,
    status_code=status.HTTP_201_CREATED,
)
def add_teacher_inline_feedback(
    group_id: UUID,
    payload: TeacherInlineFeedbackCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Teacher provides inline feedback annotation on board card or section."""
    fb = svc.add_teacher_inline_feedback(db, current_user, group_id, payload)
    return TeacherInlineFeedbackOut(**fb)


@router.post(
    "/groups/{group_id}/board/request-revision",
    response_model=InquiryBoardOut,
)
def request_board_revision(
    group_id: UUID,
    payload: BoardRequestRevisionIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Teacher requests revision on the evidence board, unlocking it for student revision."""
    board_data = svc.request_board_revision(db, current_user, group_id, payload)
    return InquiryBoardOut(**board_data)


@router.post(
    "/groups/{group_id}/board/resubmit",
    response_model=InquiryBoardOut,
)
def resubmit_board(
    group_id: UUID,
    payload: BoardResubmitIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Group resubmits revised evidence board for teacher review."""
    board_data = svc.resubmit_board(db, current_user, group_id, payload)
    return InquiryBoardOut(**board_data)


@router.get(
    "/groups/{group_id}/board/revisions",
    response_model=RevisionCycleOut,
)
def get_board_revisions(
    group_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve audit trail of revision cycles for this inquiry group."""
    rev_data = svc.get_board_revisions(db, current_user, group_id)
    return RevisionCycleOut(**rev_data)
