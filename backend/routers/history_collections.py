# -*- coding: utf-8 -*-
"""History Collection API router (Phase 11, Spec section 47).

Public read surface serves published+public collections without auth. Owners
can manage their own collections; staff can manage any. Mutations audited.
"""
from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..apischemas.history_collections import (
    HistoryCollectionCreate,
    HistoryCollectionListOut,
    HistoryCollectionOut,
    HistoryCollectionUpdate,
)
from ..db import get_db
from ..deps import get_current_user, get_current_user_optional
from ..errors import AppError
from ..models import User
from ..services import history_collections as svc

router = APIRouter(tags=["history-collections"])


def _out(c) -> HistoryCollectionOut:
    return HistoryCollectionOut.model_validate(c)


@router.get("/api/v1/history/collections", response_model=HistoryCollectionListOut)
def list_history_collections(
    visibility: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    # Public listing: only published + public (or the caller's own).
    items = svc.list_collections(db, visibility=visibility)
    visible = [c for c in items if svc._can_view(db, c, current_user)]
    return HistoryCollectionListOut(
        items=[_out(c) for c in visible], total=len(visible), offset=0, limit=len(visible)
    )


@router.get(
    "/api/v1/history/collections/{slug}", response_model=HistoryCollectionOut
)
def get_history_collection(
    slug: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    item = svc.get_collection(db, slug)
    if not item or not svc._can_view(db, item, current_user):
        raise AppError("HISTORY_COLLECTION_NOT_FOUND", "History collection not found", 404)
    return _out(item)


@router.post(
    "/api/v1/history/collections",
    response_model=HistoryCollectionOut,
)
def create_history_collection(
    payload: HistoryCollectionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from ..rbac import STAFF_ROLES

    if current_user.role not in STAFF_ROLES:
        raise AppError("HISTORY_COLLECTION_FORBIDDEN", "Not authorized", 403)
    if svc.get_collection(db, payload.slug):
        raise AppError("HISTORY_COLLECTION_SLUG_EXISTS", "Collection slug already in use", 409)
    try:
        item = svc.create_collection(db, data=payload.model_dump(), owner=current_user)
    except ValueError as exc:
        raise AppError("HISTORY_COLLECTION_INVALID_REF", str(exc), 422) from exc
    db.commit()
    return _out(item)


@router.patch(
    "/api/v1/history/collections/{collection_id}",
    response_model=HistoryCollectionOut,
)
def update_history_collection(
    collection_id: UUID,
    payload: HistoryCollectionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = svc.get_collection(db, collection_id)
    if not item:
        raise AppError("HISTORY_COLLECTION_NOT_FOUND", "History collection not found", 404)
    from ..rbac import ADMIN_ROLES

    if item.owner_id != current_user.id and current_user.role not in ADMIN_ROLES:
        raise AppError("HISTORY_COLLECTION_FORBIDDEN", "Not authorized", 403)
    data = payload.model_dump(exclude_unset=True)
    if data.get("slug"):
        existing = svc.get_collection(db, data["slug"])
        if existing and existing.id != item.id:
            raise AppError("HISTORY_COLLECTION_SLUG_EXISTS", "Collection slug already in use", 409)
    try:
        item = svc.update_collection(db, collection=item, data=data, actor=current_user)
    except ValueError as exc:
        raise AppError("HISTORY_COLLECTION_INVALID_REF", str(exc), 422) from exc
    db.commit()
    return _out(item)


@router.post(
    "/api/v1/history/collections/{collection_id}/publish",
    response_model=HistoryCollectionOut,
)
def publish_history_collection(
    collection_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = svc.get_collection(db, collection_id)
    if not item:
        raise AppError("HISTORY_COLLECTION_NOT_FOUND", "History collection not found", 404)
    from ..rbac import ADMIN_ROLES

    if item.owner_id != current_user.id and current_user.role not in ADMIN_ROLES:
        raise AppError("HISTORY_COLLECTION_FORBIDDEN", "Not authorized", 403)
    item = svc.publish_collection(db, collection=item, actor=current_user)
    db.commit()
    return _out(item)
