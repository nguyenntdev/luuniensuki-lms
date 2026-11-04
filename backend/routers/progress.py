# -*- coding: utf-8 -*-
"""Progress API router for student learning progression.

Exposes:
- GET /api/v1/progress/summary
- GET /api/v1/progress/motifs/{motif_id}
- POST /api/v1/progress/action (unified with rate-limiting, anti-replay, and anti-abuse)
- POST /api/v1/progress/discover
- POST /api/v1/progress/complete-lesson
- POST /api/v1/progress/submit-quiz
"""
from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from ..apischemas.progress import (
    MotifProgressionItem,
    ProgressionActionRequest,
    ProgressionActionResponse,
    StudentProgressionSummaryOut,
)
from ..db import get_db
from ..deps import get_current_user
from ..models import User
from ..services import progress_service

router = APIRouter(prefix="/api/v1/progress", tags=["progress"])


@router.get("/summary", response_model=StudentProgressionSummaryOut)
def get_progression_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StudentProgressionSummaryOut:
    """Retrieve full student learning progression summary."""
    return progress_service.get_student_progression_summary(db, current_user)


@router.get("/motifs/{motif_id}", response_model=MotifProgressionItem)
def get_motif_progress(
    motif_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MotifProgressionItem:
    """Retrieve individual motif progression."""
    return progress_service.get_motif_progression_detail(db, current_user, motif_id)


@router.post("/action", response_model=ProgressionActionResponse)
def handle_progression_action(
    payload: ProgressionActionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProgressionActionResponse:
    """Process a server-verified progression action (discover, complete_lesson, submit_quiz)."""
    return progress_service.process_progression_action(
        db=db,
        user=current_user,
        action=payload.action,
        motif_id=payload.motif_id,
        time_spent_seconds=payload.time_spent_seconds or 0,
        answers=payload.answers,
        idempotency_key=payload.idempotency_key,
        client_claimed_status=payload.client_claimed_status,
    )


@router.post("/discover", response_model=ProgressionActionResponse)
def discover_motif(
    payload: ProgressionActionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProgressionActionResponse:
    """Record genuine discovery (hotspot / 3D exploration)."""
    return progress_service.process_progression_action(
        db=db,
        user=current_user,
        action="discover",
        motif_id=payload.motif_id,
        time_spent_seconds=payload.time_spent_seconds or 0,
        idempotency_key=payload.idempotency_key,
        client_claimed_status=payload.client_claimed_status,
    )


@router.post("/complete-lesson", response_model=ProgressionActionResponse)
def complete_lesson_action(
    payload: ProgressionActionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProgressionActionResponse:
    """Record verified lesson completion."""
    return progress_service.process_progression_action(
        db=db,
        user=current_user,
        action="complete_lesson",
        motif_id=payload.motif_id,
        time_spent_seconds=payload.time_spent_seconds or 0,
        idempotency_key=payload.idempotency_key,
        client_claimed_status=payload.client_claimed_status,
    )


@router.post("/submit-quiz", response_model=ProgressionActionResponse)
def submit_quiz_action(
    payload: ProgressionActionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProgressionActionResponse:
    """Record quiz submission and evaluate mastery."""
    return progress_service.process_progression_action(
        db=db,
        user=current_user,
        action="submit_quiz",
        motif_id=payload.motif_id,
        time_spent_seconds=payload.time_spent_seconds or 0,
        answers=payload.answers,
        idempotency_key=payload.idempotency_key,
        client_claimed_status=payload.client_claimed_status,
    )
