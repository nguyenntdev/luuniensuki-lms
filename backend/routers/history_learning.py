# -*- coding: utf-8 -*-
"""Historical Learning Engine V2 API router (Phase 8).

Server-authoritative grading (Spec 33.1-33.7), public question listing, staff
question authoring with the content-validity invariant (Spec 32.2), and the V2
mastery dimension surface (Spec 34).

The grading endpoint NEVER trusts client correctness — the client submits only
``{answer: {...}}`` and the server derives ``correct``/``score`` from the
question's answer contract and authoritative knowledge-graph relations.
"""
from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..apischemas.history_learning import (
    HistoryQuestionCreate,
    HistoryQuestionGradeIn,
    HistoryQuestionGradeOut,
    HistoryQuestionListOut,
    HistoryQuestionOut,
    HistorySkillsOut,
    MasteryDimensionOut,
)
from ..db import get_db
from ..deps import get_current_user, get_staff_user
from ..errors import AppError
from ..models import (
    HistoricalClaim,
    HistoricalEntity,
    HistoryQuestionType,
    QuizQuestion,
    User,
)
from ..rbac import ADMIN_ROLES, STAFF_ROLES
from ..services import history_learning as hl

router = APIRouter(tags=["history-learning"])

# V2 question types (registry keys seeded by migration 0050). Authoring may also
# reference legacy types that already exist on the enum.
V2_QUESTION_TYPES = {
    "chronology_order",
    "image_identification",
    "map_location",
    "urn_hotspot",
    "evidence_match",
    "entity_match",
    "compare_two",
    "source_interpretation",
    "short_response",
    "multi_select",
    "relationship_chain",
}


def _question_to_out(question) -> HistoryQuestionOut:
    out = HistoryQuestionOut.model_validate(question)
    out.status = question.content_validation_status
    return out


# --------------------------------------------------------------------------- #
# Grading — auth required, server-authoritative
# --------------------------------------------------------------------------- #
@router.post(
    "/api/v1/history/questions/{question_id}/grade",
    response_model=HistoryQuestionGradeOut,
)
def grade_history_question(
    question_id: UUID,
    payload: HistoryQuestionGradeIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    question = db.get(QuizQuestion, question_id)
    if not question:
        raise AppError("HISTORY_QUESTION_NOT_FOUND", "History question not found", 404)

    result = hl.grade_question(db, question, payload.answer)
    dimensions = question.skill_dimensions or []
    hl.update_mastery_from_result(db, current_user.id, question, result)
    db.commit()

    return HistoryQuestionGradeOut(
        correct=result["correct"],
        score=result["score"],
        feedback_vi=result["feedback_vi"],
        skill_dimensions=list(dimensions),
    )


# --------------------------------------------------------------------------- #
# Public read endpoints — no auth
# --------------------------------------------------------------------------- #
@router.get(
    "/api/v1/history/questions",
    response_model=HistoryQuestionListOut,
)
def list_history_questions(
    question_type: Optional[str] = Query(default=None),
    entity_id: Optional[UUID] = Query(default=None),
    content_validation_status: Optional[str] = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    q = select(QuizQuestion)
    if question_type:
        q = q.where(QuizQuestion.question_type == question_type)
    if entity_id:
        q = q.where(QuizQuestion.entity_id == entity_id)
    if content_validation_status:
        q = q.where(QuizQuestion.content_validation_status == content_validation_status)
    total = db.scalar(select(func.count()).select_from(q.subquery())) or 0
    items = list(
        db.scalars(
            q.order_by(QuizQuestion.created_at.desc()).offset(offset).limit(limit)
        )
    )
    return HistoryQuestionListOut(
        items=[_question_to_out(i) for i in items],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/api/v1/history/questions/{question_id}",
    response_model=HistoryQuestionOut,
)
def get_history_question(question_id: UUID, db: Session = Depends(get_db)):
    question = db.get(QuizQuestion, question_id)
    if not question:
        raise AppError("HISTORY_QUESTION_NOT_FOUND", "History question not found", 404)
    return _question_to_out(question)


# --------------------------------------------------------------------------- #
# Authoring — staff only
# --------------------------------------------------------------------------- #
@router.post(
    "/api/v1/history/questions",
    response_model=HistoryQuestionOut,
    dependencies=[Depends(get_staff_user)],
)
def create_history_question(
    payload: HistoryQuestionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if payload.question_type not in V2_QUESTION_TYPES and not (
        payload.question_type
        in {"multiple_choice", "true_false", "image_select", "mesh_location"}
    ):
        raise AppError(
            "HISTORY_QUESTION_INVALID_TYPE",
            f"Unsupported question_type '{payload.question_type}'",
            422,
        )
    if payload.entity_id and not db.get(HistoricalEntity, payload.entity_id):
        raise AppError("HISTORY_ENTITY_NOT_FOUND", "Historical entity not found", 404)
    if payload.claim_ids:
        for claim_id in payload.claim_ids:
            if not db.get(HistoricalClaim, claim_id):
                raise AppError(
                    "HISTORY_CLAIM_NOT_FOUND", "Historical claim not found", 404
                )

    data = payload.model_dump()
    data["correct_answer"] = data.get("correct_answer") or ""
    # JSONB columns serialize via stdlib json — store IDs as strings, never UUID
    # objects, so the response/insert round-trips cleanly.
    data["claim_ids"] = [str(c) for c in (data.get("claim_ids") or [])]
    data["source_ids"] = [str(s) for s in (data.get("source_ids") or [])]
    data["created_by_id"] = current_user.id

    question = QuizQuestion(**data)
    # Content-validity invariant (Spec 32.2): a question whose backing claims
    # are not verified/editor-reviewed is blocked for authoritative learning.
    question.content_validation_status = (
        "valid"
        if hl.content_validity_check(db, question)
        else "blocked_for_authoritative_learning"
    )
    db.add(question)
    db.flush()
    _ensure_registry_row(db, payload.question_type)
    db.commit()
    return _question_to_out(question)


def _ensure_registry_row(db: Session, key: str) -> None:
    """Idempotently record a V2 question type key in the registry table."""
    if key not in V2_QUESTION_TYPES:
        return
    existing = db.scalar(
        select(HistoryQuestionType).where(HistoryQuestionType.key == key)
    )
    if existing is None:
        db.add(HistoryQuestionType(key=key, label_vi=key, label_en=key, sort_order=0))
        db.flush()


# --------------------------------------------------------------------------- #
# Mastery V2 — auth required
# --------------------------------------------------------------------------- #
@router.get(
    "/api/v1/history/skills/{user_id}",
    response_model=HistorySkillsOut,
)
def get_history_skills(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.id != user_id and current_user.role not in (ADMIN_ROLES | STAFF_ROLES):
        raise HTTPException(status_code=403, detail="Not authorized")
    dimensions = hl.get_mastery_dimensions(db, user_id)
    values = [d["value"] for d in dimensions if d["value"] is not None]
    overall = round(sum(values) / len(values), 4) if values else None
    return HistorySkillsOut(
        user_id=user_id,
        dimensions=[MasteryDimensionOut(**d) for d in dimensions],
        overall=overall,
    )