# -*- coding: utf-8 -*-
"""History Collection service (Phase 11, Spec section 47).

Teachers/editors curate structured collections referencing canonical
entities/sources/stories/questions ids. Visibility: private (owner+staff),
classroom (teacher's classroom), public (published).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from ..models import (
    HistoricalEntity,
    HistoricalSource,
    HistoryCollection,
    HistoryStory,
    QuizQuestion,
    User,
)
from .history_governance import audit_action


def _exists_any(db: Session, model, ids: list) -> list[str]:
    """Return the ids from ``ids`` that do NOT resolve to a row of ``model``."""
    missing: list[str] = []
    for raw in ids or []:
        try:
            target = UUID(str(raw))
        except (ValueError, TypeError):
            missing.append(str(raw))
            continue
        if db.get(model, target) is None:
            missing.append(str(raw))
    return missing


def validate_references(
    db: Session,
    *,
    entity_ids: Optional[list] = None,
    source_ids: Optional[list] = None,
    story_ids: Optional[list] = None,
    question_ids: Optional[list] = None,
) -> list[str]:
    errors: list[str] = []
    if entity_ids:
        for raw in _exists_any(db, HistoricalEntity, entity_ids):
            errors.append(f"entity {raw!r} does not exist")
    if source_ids:
        for raw in _exists_any(db, HistoricalSource, source_ids):
            errors.append(f"source {raw!r} does not exist")
    if story_ids:
        for raw in _exists_any(db, HistoryStory, story_ids):
            errors.append(f"story {raw!r} does not exist")
    if question_ids:
        for raw in _exists_any(db, QuizQuestion, question_ids):
            errors.append(f"question {raw!r} does not exist")
    return errors


def list_collections(
    db: Session,
    *,
    visibility: Optional[str] = None,
    owner_id: Optional[UUID] = None,
) -> list[HistoryCollection]:
    q = select(HistoryCollection)
    if visibility:
        q = q.where(HistoryCollection.visibility == visibility)
    if owner_id:
        q = q.where(HistoryCollection.owner_id == owner_id)
    q = q.order_by(
        HistoryCollection.updated_at.desc(),
        HistoryCollection.created_at.desc(),
    )
    return list(db.scalars(q))


def get_collection(db: Session, slug_or_id: Any) -> Optional[HistoryCollection]:
    key = str(slug_or_id)
    try:
        parsed = UUID(key)
    except (ValueError, TypeError):
        parsed = None
    if parsed is not None:
        item = db.get(HistoryCollection, parsed)
        if item is not None:
            return item
    return db.scalar(
        select(HistoryCollection).where(
            func.lower(HistoryCollection.slug) == key.lower()
        )
    )


def _can_view(db: Session, collection: HistoryCollection, user: Optional[User]) -> bool:
    if collection.status == "published" and collection.visibility == "public":
        return True
    if user is None:
        return False
    if user.id == collection.owner_id:
        return True
    from ..rbac import STAFF_ROLES

    if user.role in STAFF_ROLES:
        return True
    return False


def create_collection(
    db: Session,
    *,
    data: dict[str, Any],
    owner: User,
) -> HistoryCollection:
    errors = validate_references(
        db,
        entity_ids=data.get("entity_ids"),
        source_ids=data.get("source_ids"),
        story_ids=data.get("story_ids"),
        question_ids=data.get("question_ids"),
    )
    if errors:
        raise ValueError("; ".join(errors))
    item = HistoryCollection(owner_id=owner.id, **data)
    db.add(item)
    db.flush()
    audit_action(
        db,
        actor_id=owner.id,
        action="create",
        resource_type="collection",
        resource_id=item.id,
        after_json={"slug": item.slug, "title_vi": item.title_vi},
    )
    return item


def update_collection(
    db: Session,
    *,
    collection: HistoryCollection,
    data: dict[str, Any],
    actor: User,
) -> HistoryCollection:
    if any(data.get(k) is not None for k in ("entity_ids", "source_ids", "story_ids", "question_ids")):
        errors = validate_references(
            db,
            entity_ids=data.get("entity_ids"),
            source_ids=data.get("source_ids"),
            story_ids=data.get("story_ids"),
            question_ids=data.get("question_ids"),
        )
        if errors:
            raise ValueError("; ".join(errors))
    before = {"slug": collection.slug, "title_vi": collection.title_vi, "visibility": collection.visibility}
    for key, value in data.items():
        setattr(collection, key, value)
    db.flush()
    audit_action(
        db,
        actor_id=actor.id,
        action="update",
        resource_type="collection",
        resource_id=collection.id,
        before_json=before,
        after_json={"slug": collection.slug, "title_vi": collection.title_vi, "visibility": collection.visibility},
    )
    return collection


def publish_collection(
    db: Session,
    *,
    collection: HistoryCollection,
    actor: User,
) -> HistoryCollection:
    before = {"status": collection.status, "visibility": collection.visibility}
    collection.status = "published"
    if collection.visibility == "private":
        collection.visibility = "public"
    if collection.published_at is None:
        collection.published_at = datetime.now(timezone.utc)
    db.flush()
    audit_action(
        db,
        actor_id=actor.id,
        action="publish",
        resource_type="collection",
        resource_id=collection.id,
        before_json=before,
        after_json={"status": collection.status, "visibility": collection.visibility},
    )
    return collection
