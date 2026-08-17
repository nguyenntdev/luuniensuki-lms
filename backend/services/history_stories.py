# -*- coding: utf-8 -*-
"""History Story Engine — block-based stories service (Phase 10).

Business logic for docs/specs/HISTORY_FIRST_MASTER_SPEC.md section 30. A story
is an ordered list of typed blocks (30.1), never one giant HTML field. Every
block that references a knowledge-graph entity/source is validated so the
renderer can always deep-link into the atlas/urns/map/timeline/sources
surfaces (30.2).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models import (
    HistoricalEntity,
    HistoricalSource,
    HistoryStory,
    QuizQuestion,
)
from .history_governance import audit_action

# Ordered block-type vocabulary (Spec 30.1).
STORY_BLOCK_TYPES: frozenset[str] = frozenset(
    {
        "text",
        "image",
        "quote",
        "relief_focus",
        "urn_3d_focus",
        "map_focus",
        "timeline_focus",
        "source_excerpt",
        "compare",
        "reflection_question",
        "quiz",
        "callout",
    }
)

# Blocks whose only hard requirement is a single scalar field.
_BLOCK_SCALAR_FIELDS: dict[str, str] = {
    "text": "body",
    "image": "image_url",
    "quote": "quote",
    "source_excerpt": "source_id",
    "reflection_question": "question",
    "quiz": "quiz_id",
    "callout": "body",
}

# Blocks that reference a non-empty list of entity ids (30.2 entity_ids).
_BLOCK_LIST_FIELDS: dict[str, str] = {
    "map_focus": "entity_ids",
    "timeline_focus": "entity_ids",
    "compare": "entity_ids",
}

_RELIEF_FOCUS_FIELDS = ("entity_id", "entity_slug")
_URN_FOCUS_FIELDS = ("urn_slug", "entity_id")


# --------------------------------------------------------------------------- #
# Block validation
# --------------------------------------------------------------------------- #
def _first_present(block: dict, fields: tuple[str, ...]):
    for field in fields:
        if block.get(field) not in (None, ""):
            return field, block[field]
    return None, None


def _resolve_entity(db: Session, ref: str, value: Any):
    """Resolve an entity reference by id (UUID) or slug."""
    if ref == "entity_id":
        try:
            return db.get(HistoricalEntity, UUID(str(value)))
        except (ValueError, TypeError):
            return None
    return db.scalar(
        select(HistoricalEntity).where(
            func.lower(HistoricalEntity.slug) == str(value).lower()
        )
    )


def _entity_exists(db: Session, value: Any) -> bool:
    """True when ``value`` references an existing entity (by UUID or slug)."""
    try:
        return db.get(HistoricalEntity, UUID(str(value))) is not None
    except (ValueError, TypeError):
        count = db.scalar(
            select(func.count())
            .select_from(HistoricalEntity)
            .where(HistoricalEntity.slug == str(value))
        )
        return bool(count and count > 0)


def _source_exists(db: Session, value: Any) -> bool:
    try:
        return db.get(HistoricalSource, UUID(str(value))) is not None
    except (ValueError, TypeError):
        return False


def _quiz_exists(db: Session, value: Any) -> bool:
    try:
        return db.get(QuizQuestion, UUID(str(value))) is not None
    except (ValueError, TypeError):
        return False


def validate_story_blocks(blocks: Any, db: Optional[Session] = None) -> list[str]:
    """Validate a story's block list.

    Returns a list of human-readable errors (empty when valid). Structural
    checks (type membership, required fields) always run; existence checks for
    referenced entity/source/quiz ids run only when ``db`` is provided.
    """
    errors: list[str] = []
    if not isinstance(blocks, list):
        return ["blocks must be a JSON array"]
    if not blocks:
        return []
    for idx, block in enumerate(blocks):
        if not isinstance(block, dict):
            errors.append(f"block {idx}: must be an object")
            continue
        btype = block.get("type")
        if btype not in STORY_BLOCK_TYPES:
            errors.append(f"block {idx}: unknown block type {btype!r}")
            continue
        label = f"block {idx} ({btype})"

        if btype in _BLOCK_SCALAR_FIELDS:
            field = _BLOCK_SCALAR_FIELDS[btype]
            value = block.get(field)
            if value is None or (isinstance(value, str) and not value.strip()):
                errors.append(f"{label}: missing required field '{field}'")
        elif btype in _BLOCK_LIST_FIELDS:
            field = _BLOCK_LIST_FIELDS[btype]
            value = block.get(field)
            if not isinstance(value, list) or not value:
                errors.append(f"{label}: '{field}' must be a non-empty list")
        elif btype == "relief_focus":
            ref, value = _first_present(block, _RELIEF_FOCUS_FIELDS)
            if ref is None:
                errors.append(f"{label}: requires one of entity_id / entity_slug")
        elif btype == "urn_3d_focus":
            ref, value = _first_present(block, _URN_FOCUS_FIELDS)
            if ref is None:
                errors.append(f"{label}: requires one of urn_slug / entity_id")

        if db is None:
            continue

        if btype in _BLOCK_LIST_FIELDS:
            for ref in block[_BLOCK_LIST_FIELDS[btype]]:
                if not _entity_exists(db, ref):
                    errors.append(
                        f"{label}: referenced entity {ref!r} does not exist"
                    )
        elif btype == "relief_focus":
            ref, value = _first_present(block, _RELIEF_FOCUS_FIELDS)
            entity = _resolve_entity(db, ref, value) if ref else None
            if entity is None:
                errors.append(f"{label}: referenced entity {value!r} does not exist")
            elif entity.entity_type != "relief":
                errors.append(f"{label}: entity {value!r} is not a relief")
        elif btype == "urn_3d_focus":
            ref, value = _first_present(block, _URN_FOCUS_FIELDS)
            entity = _resolve_entity(db, ref, value) if ref else None
            if entity is None:
                errors.append(f"{label}: referenced entity {value!r} does not exist")
            elif entity.entity_type != "urn":
                errors.append(f"{label}: entity {value!r} is not an urn")
        elif btype == "source_excerpt":
            if not _source_exists(db, block.get("source_id")):
                errors.append(
                    f"{label}: referenced source {block.get('source_id')!r} does not exist"
                )
        elif btype == "quiz":
            if not _quiz_exists(db, block.get("quiz_id")):
                errors.append(
                    f"{label}: referenced quiz {block.get('quiz_id')!r} does not exist"
                )
    return errors


# --------------------------------------------------------------------------- #
# CRUD
# --------------------------------------------------------------------------- #
def list_stories(
    db: Session,
    *,
    status: Optional[str] = None,
    featured_only: bool = False,
) -> list[HistoryStory]:
    q = select(HistoryStory)
    if status:
        q = q.where(HistoryStory.status == status)
    if featured_only:
        q = q.where(HistoryStory.featured.is_(True))
    q = q.order_by(
        HistoryStory.featured.desc(),
        HistoryStory.published_at.desc().nullslast(),
        HistoryStory.created_at.desc(),
    )
    return list(db.scalars(q))


def get_story(db: Session, slug_or_id: Any) -> Optional[HistoryStory]:
    """Resolve a story by UUID id or unique slug."""
    key = str(slug_or_id)
    try:
        parsed = UUID(key)
    except (ValueError, TypeError):
        parsed = None
    if parsed is not None:
        story = db.get(HistoryStory, parsed)
        if story is not None:
            return story
    return db.scalar(
        select(HistoryStory).where(func.lower(HistoryStory.slug) == key.lower())
    )


def create_story(
    db: Session,
    *,
    data: dict[str, Any],
    actor_id: Optional[UUID] = None,
) -> HistoryStory:
    errors = validate_story_blocks(data.get("blocks", []), db)
    if errors:
        raise ValueError("; ".join(errors))
    story = HistoryStory(**data)
    if actor_id:
        story.created_by = actor_id
    db.add(story)
    db.flush()
    audit_action(
        db,
        actor_id=actor_id,
        action="create",
        resource_type="story",
        resource_id=story.id,
        after_json={"slug": story.slug, "title_vi": story.title_vi},
    )
    return story


def update_story(
    db: Session,
    *,
    story: HistoryStory,
    data: dict[str, Any],
    actor_id: Optional[UUID] = None,
) -> HistoryStory:
    if data.get("blocks") is not None:
        errors = validate_story_blocks(data["blocks"], db)
        if errors:
            raise ValueError("; ".join(errors))
    before = {
        "slug": story.slug,
        "title_vi": story.title_vi,
        "status": story.status,
        "featured": story.featured,
    }
    for key, value in data.items():
        setattr(story, key, value)
    db.flush()
    audit_action(
        db,
        actor_id=actor_id,
        action="update",
        resource_type="story",
        resource_id=story.id,
        before_json=before,
        after_json={
            "slug": story.slug,
            "title_vi": story.title_vi,
            "status": story.status,
            "featured": story.featured,
        },
    )
    return story


def publish_story(
    db: Session,
    *,
    story: HistoryStory,
    actor_id: Optional[UUID] = None,
) -> HistoryStory:
    before = {"status": story.status}
    story.status = "published"
    if story.published_at is None:
        story.published_at = datetime.now(timezone.utc)
    db.flush()
    audit_action(
        db,
        actor_id=actor_id,
        action="publish",
        resource_type="story",
        resource_id=story.id,
        before_json=before,
        after_json={"status": story.status},
    )
    return story