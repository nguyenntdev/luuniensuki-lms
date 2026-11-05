# -*- coding: utf-8 -*-
"""FSRS Spaced Repetition and Adaptive Evidence Practice Router.

Wave W09 / Slot A07 / Ticket V5-T097.

Provides:
- Adaptive evidence practice endpoints for primary historical sources.
- Server-authoritative anti-abuse guards (minimum dwell time, rapid clicking / brute-force protection).
- Clean separation between gamification XP and memory stability.
- Algorithmic transparency and user opt-out controls.
"""
from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..deps import get_current_user, get_db
from ..models import User
from ..apischemas.fsrs import (
    DueEvidenceTaskOut,
    DueEvidenceTaskListOut,
    EvidenceEvaluationIn,
    EvidenceEvaluationOut,
    FsrsModelTransparencyOut,
    FsrsSettingsOut,
    FsrsSettingsUpdateIn,
)
from ..services import fsrs as fsrs_service

router = APIRouter(tags=["fsrs"])


@router.get(
    "/api/v1/fsrs/evidence/due",
    response_model=DueEvidenceTaskListOut,
)
@router.get(
    "/api/v1/reviews/evidence/due",
    response_model=DueEvidenceTaskListOut,
)
def get_due_evidence_tasks(
    limit: int = Query(default=10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DueEvidenceTaskListOut:
    """Retrieve due primary source evidence evaluation tasks for the learner."""
    cards = fsrs_service.get_due_evidence_tasks(db, current_user, limit=limit)
    out_tasks = []
    for c in cards:
        src = c.source
        retrievability_val = fsrs_service.retrievability(0.0, c.fsrs_stability or 1.0)
        out_tasks.append(
            DueEvidenceTaskOut(
                card_id=c.id,
                source_id=c.source_id,
                source_title=src.title if src else "Tư liệu lịch sử triều Nguyễn",
                author_text=src.author_text if src else None,
                citation_text=src.citation_text if src else None,
                excerpt=src.excerpt if src else None,
                prompt=c.prompt,
                task_type=c.task_type or "source_evaluation",
                fsrs_state=c.fsrs_state,
                fsrs_difficulty=c.fsrs_difficulty,
                fsrs_stability=c.fsrs_stability,
                fsrs_due_date=c.fsrs_due_date,
                retrievability=retrievability_val,
                is_mastered=c.is_mastered,
                mastery_badge_awarded=c.mastery_badge_awarded,
            )
        )

    return DueEvidenceTaskListOut(tasks=out_tasks, total_due=len(out_tasks))


@router.post(
    "/api/v1/fsrs/evidence/evaluate",
    response_model=EvidenceEvaluationOut,
)
@router.post(
    "/api/v1/reviews/evidence/evaluate",
    response_model=EvidenceEvaluationOut,
)
def evaluate_evidence_task(
    payload: EvidenceEvaluationIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> EvidenceEvaluationOut:
    """Evaluate a primary source evidence task with anti-abuse and transparency."""
    try:
        res = fsrs_service.evaluate_evidence_task(
            db=db,
            user=current_user,
            card_id=payload.card_id,
            score=payload.score,
            dwell_time_seconds=payload.dwell_time_seconds,
            rating=payload.rating,
            client_claimed_badge=payload.client_claimed_badge,
            client_claimed_xp=payload.client_claimed_xp,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404,
            detail=str(e),
        )

    return EvidenceEvaluationOut(**res)


@router.get(
    "/api/v1/fsrs/transparency",
    response_model=FsrsModelTransparencyOut,
)
def get_fsrs_transparency() -> FsrsModelTransparencyOut:
    """Inspect full FSRS-5 algorithmic transparency formulas and anti-abuse safeguards."""
    return FsrsModelTransparencyOut(**fsrs_service.get_model_transparency())


@router.get(
    "/api/v1/fsrs/settings",
    response_model=FsrsSettingsOut,
)
@router.get(
    "/api/v1/users/me/fsrs-settings",
    response_model=FsrsSettingsOut,
)
def get_user_fsrs_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FsrsSettingsOut:
    """Fetch user FSRS settings including opt-out status and optimal retention."""
    settings = fsrs_service.get_or_create_user_settings(db, current_user.id)
    return FsrsSettingsOut(
        fsrs_enabled=settings.fsrs_enabled,
        optimal_retention=settings.optimal_retention,
        recommended_range=[0.70, 0.97],
        review_count=settings.review_count_at_last_optimize,
        using_personal_params=bool(settings.parameters and settings.parameters != fsrs_service.DEFAULT_W),
        cohort="fsrs_v1_treatment",
    )


@router.put(
    "/api/v1/fsrs/settings",
    response_model=FsrsSettingsOut,
)
@router.put(
    "/api/v1/users/me/fsrs-settings",
    response_model=FsrsSettingsOut,
)
def update_user_fsrs_settings(
    payload: FsrsSettingsUpdateIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FsrsSettingsOut:
    """Update user FSRS retention target and opt-out preferences."""
    settings = fsrs_service.update_user_settings(
        db,
        current_user.id,
        fsrs_enabled=payload.fsrs_enabled,
        optimal_retention=payload.optimal_retention,
    )
    return FsrsSettingsOut(
        fsrs_enabled=settings.fsrs_enabled,
        optimal_retention=settings.optimal_retention,
        recommended_range=[0.70, 0.97],
        review_count=settings.review_count_at_last_optimize,
        using_personal_params=bool(settings.parameters and settings.parameters != fsrs_service.DEFAULT_W),
        cohort="fsrs_v1_treatment",
    )
