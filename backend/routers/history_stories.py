# -*- coding: utf-8 -*-
"""History Story Engine API router (Phase 10).

Block-based history stories (Spec section 30). Public read surface serves only
``published`` stories without auth; mutations are staff-only and every change
is audited to ``historical_content_audit_log``.
"""
from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..apischemas.history_stories import (
    HistoryStoryCreate,
    HistoryStoryListOut,
    HistoryStoryOut,
    HistoryStoryUpdate,
)
from ..db import get_db
from ..deps import get_current_user, get_staff_user
from ..errors import AppError
from ..models import User
from ..services import history_stories as svc

router = APIRouter(tags=["history-stories"])


def _story_to_out(story) -> HistoryStoryOut:
    return HistoryStoryOut.model_validate(story)


# --------------------------------------------------------------------------- #
# Public read endpoints — published only, no auth required
# --------------------------------------------------------------------------- #
@router.get("/api/v1/history/stories", response_model=HistoryStoryListOut)
def list_history_stories(
    featured_only: bool = Query(default=False),
    db: Session = Depends(get_db),
):
    stories = svc.list_stories(
        db, status="published", featured_only=featured_only
    )
    return HistoryStoryListOut(
        items=[_story_to_out(s) for s in stories],
        total=len(stories),
        offset=0,
        limit=len(stories),
    )


@router.get("/api/v1/history/stories/{slug}", response_model=HistoryStoryOut)
def get_history_story(slug: str, db: Session = Depends(get_db)):
    story = svc.get_story(db, slug)
    if not story or story.status != "published":
        raise AppError("HISTORY_STORY_NOT_FOUND", "History story not found", 404)
    return _story_to_out(story)


# --------------------------------------------------------------------------- #
# Staff mutation endpoints — require staff, audit everything
# --------------------------------------------------------------------------- #
@router.post(
    "/api/v1/history/stories",
    response_model=HistoryStoryOut,
    dependencies=[Depends(get_staff_user)],
)
def create_history_story(
    payload: HistoryStoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if svc.get_story(db, payload.slug):
        raise AppError("HISTORY_STORY_SLUG_EXISTS", "Story slug already in use", 409)
    try:
        story = svc.create_story(
            db, data=payload.model_dump(), actor_id=current_user.id
        )
    except ValueError as exc:
        raise AppError("HISTORY_STORY_INVALID_BLOCKS", str(exc), 422) from exc
    db.commit()
    return _story_to_out(story)


@router.patch(
    "/api/v1/history/stories/{story_id}",
    response_model=HistoryStoryOut,
    dependencies=[Depends(get_staff_user)],
)
def update_history_story(
    story_id: UUID,
    payload: HistoryStoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    story = svc.get_story(db, story_id)
    if not story:
        raise AppError("HISTORY_STORY_NOT_FOUND", "History story not found", 404)
    data = payload.model_dump(exclude_unset=True)
    if data.get("slug"):
        existing = svc.get_story(db, data["slug"])
        if existing and existing.id != story.id:
            raise AppError("HISTORY_STORY_SLUG_EXISTS", "Story slug already in use", 409)
    try:
        story = svc.update_story(
            db, story=story, data=data, actor_id=current_user.id
        )
    except ValueError as exc:
        raise AppError("HISTORY_STORY_INVALID_BLOCKS", str(exc), 422) from exc
    db.commit()
    return _story_to_out(story)


@router.post(
    "/api/v1/history/stories/{story_id}/publish",
    response_model=HistoryStoryOut,
    dependencies=[Depends(get_staff_user)],
)
def publish_history_story(
    story_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    story = svc.get_story(db, story_id)
    if not story:
        raise AppError("HISTORY_STORY_NOT_FOUND", "History story not found", 404)
    story = svc.publish_story(db, story=story, actor_id=current_user.id)
    db.commit()
    return _story_to_out(story)