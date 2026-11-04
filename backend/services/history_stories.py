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
    HistoricalClaim,
    HistoricalClaimSource,
    HistoricalEntity,
    HistoricalSource,
    HistoryStory,
    QuizQuestion,
)
from ..apischemas.history_stories import HistoryStoryOut
from ..domain.story_citations import FootnoteMapper
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


def _claim_exists(db: Session, value: Any) -> bool:
    try:
        return db.get(HistoricalClaim, UUID(str(value))) is not None
    except (ValueError, TypeError):
        return False


def _quiz_exists(db: Session, value: Any) -> bool:
    try:
        return db.get(QuizQuestion, UUID(str(value))) is not None
    except (ValueError, TypeError):
        return False


def validate_story_citations(citations: Any, db: Optional[Session] = None) -> list[str]:
    """Validate structured story citations, link integrity, and epistemic consistency."""
    errors: list[str] = []
    if not isinstance(citations, list):
        return ["citations must be a list"]
    for idx, cite in enumerate(citations):
        if not isinstance(cite, dict):
            errors.append(f"citation {idx}: must be an object")
            continue
        src_id = cite.get("source_id")
        claim_id = cite.get("claim_id")
        raw_cert = str(cite.get("epistemic_certainty") or "").lower()
        is_verified_claimed = (
            raw_cert in ("su_lieu_xac_thuc", "verified", "sử liệu xác thực", "expert_verified", "editor_reviewed")
            or cite.get("is_verified") is True
        )

        if db is not None:
            if src_id:
                if not _source_exists(db, src_id):
                    errors.append(f"citation {idx}: referenced source {src_id!r} does not exist")
            if claim_id:
                claim = None
                try:
                    claim = db.get(HistoricalClaim, UUID(str(claim_id)))
                except (ValueError, TypeError):
                    pass
                if not claim:
                    errors.append(f"citation {idx}: referenced claim {claim_id!r} does not exist")
                elif is_verified_claimed:
                    if (
                        claim.verification_status in ("disputed", "rejected", "needs_source", "unreviewed")
                        or claim.confidence == "disputed"
                    ):
                        errors.append(
                            f"citation {idx}: cannot present disputed or unverified claim {claim_id!r} as verified historical fact ('Sử liệu xác thực')"
                        )
                    elif not claim.source_bindings and not src_id:
                        errors.append(
                            f"citation {idx}: claim {claim_id!r} has no attached source and cannot be presented as verified historical fact ('Sử liệu xác thực')"
                        )

        if is_verified_claimed and not src_id and not cite.get("has_source") and not claim_id:
            errors.append(
                f"citation {idx}: claim has no attached source and cannot be presented as verified historical fact ('Sử liệu xác thực')"
            )
    return errors


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

        # Check source_claim_ids if present
        if "source_claim_ids" in block:
            cids = block["source_claim_ids"]
            if not isinstance(cids, list):
                errors.append(f"{label}: 'source_claim_ids' must be a list")
            elif db is not None:
                for cid in cids:
                    claim = None
                    try:
                        claim = db.get(HistoricalClaim, UUID(str(cid)))
                    except (ValueError, TypeError):
                        pass
                    if not claim:
                        errors.append(f"{label}: referenced claim {cid!r} does not exist")
                    else:
                        block_cert = str(block.get("epistemic_certainty") or "").lower()
                        if block_cert in ("su_lieu_xac_thuc", "verified", "sử liệu xác thực"):
                            if (
                                claim.verification_status in ("disputed", "rejected", "needs_source", "unreviewed")
                                or claim.confidence == "disputed"
                            ):
                                errors.append(
                                    f"{label}: cannot present disputed or unverified claim {cid!r} as verified historical fact ('Sử liệu xác thực')"
                                )
                            elif not claim.source_bindings:
                                errors.append(
                                    f"{label}: claim {cid!r} has no attached source and cannot be presented as verified historical fact ('Sử liệu xác thực')"
                                )

        # Check source_id on any block
        if "source_id" in block and block.get("source_id"):
            src_val = block.get("source_id")
            if db is not None and not _source_exists(db, src_val):
                errors.append(f"{label}: referenced source {src_val!r} does not exist")

        # Check citations within block
        if "citations" in block:
            cite_errs = validate_story_citations(block["citations"], db)
            for cerr in cite_errs:
                errors.append(f"{label}: {cerr}")

        # Block-level epistemic integrity check
        block_cert = str(block.get("epistemic_certainty") or "").lower()
        if block_cert in ("su_lieu_xac_thuc", "verified", "sử liệu xác thực"):
            has_src = bool(block.get("source_id"))
            if not has_src and block.get("citations") and isinstance(block["citations"], list):
                has_src = any(bool(c.get("source_id")) for c in block["citations"] if isinstance(c, dict))
            if not has_src and block.get("source_claim_ids") and isinstance(block["source_claim_ids"], list) and db is not None:
                for cid in block["source_claim_ids"]:
                    try:
                        clm = db.get(HistoricalClaim, UUID(str(cid)))
                        if clm and clm.source_bindings:
                            has_src = True
                            break
                    except Exception:
                        pass
            if not has_src:
                errors.append(
                    f"{label}: passage has no attached source and cannot be presented as verified historical fact ('Sử liệu xác thực')"
                )

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
    if db is not None:
        errors.extend(FootnoteMapper.validate_strict_citations(blocks=blocks, db=db))
    return errors


def resolve_story_citations(
    db: Session,
    blocks: list,
    story_citations: Optional[list] = None,
) -> list[dict[str, Any]]:
    """Build structured bibliographic citations with source references and evidence footnotes."""
    return FootnoteMapper.resolve_story_citations_and_footnotes(
        blocks=blocks, citations=story_citations, db=db
    ).citations


def build_story_out(db: Session, story: HistoryStory) -> HistoryStoryOut:
    """Build HistoryStoryOut with resolved structured citations and evidence links."""
    story_cites = getattr(story, "_cached_citations", None)
    citations = resolve_story_citations(db, story.blocks or [], story_cites)
    out = HistoryStoryOut.model_validate(story)
    out.citations = citations
    return out


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
    citations = data.pop("citations", None)
    if citations:
        if data.get("blocks"):
            has_block_citations = any("citations" in b for b in data["blocks"] if isinstance(b, dict))
            if not has_block_citations and isinstance(data["blocks"][0], dict):
                data["blocks"][0]["citations"] = citations
        else:
            data["blocks"] = [{"type": "text", "body": "", "citations": citations}]

    errors = validate_story_blocks(data.get("blocks", []), db)
    if citations:
        errors.extend(validate_story_citations(citations, db))
    if db is not None:
        errors.extend(FootnoteMapper.validate_strict_citations(blocks=data.get("blocks", []), citations=citations, db=db))
    elif citations:
        errors.extend(FootnoteMapper.validate_strict_citations(blocks=data.get("blocks", []), citations=citations))
    if errors:
        raise ValueError("; ".join(errors))
    story = HistoryStory(**data)
    if actor_id:
        story.created_by = actor_id
    if citations:
        story._cached_citations = citations
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
    citations = data.pop("citations", None)
    if citations is not None:
        target_blocks = data.get("blocks") if data.get("blocks") is not None else list(story.blocks or [])
        if target_blocks and isinstance(target_blocks[0], dict):
            target_blocks[0]["citations"] = citations
            data["blocks"] = target_blocks

    errors = []
    blocks_to_check = data.get("blocks") if data.get("blocks") is not None else story.blocks
    if data.get("blocks") is not None:
        errors.extend(validate_story_blocks(data["blocks"], db))
    if citations is not None:
        errors.extend(validate_story_citations(citations, db))
    if db is not None:
        errors.extend(FootnoteMapper.validate_strict_citations(blocks=blocks_to_check, citations=citations, db=db))
    elif citations is not None:
        errors.extend(FootnoteMapper.validate_strict_citations(blocks=blocks_to_check, citations=citations))
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
    if citations is not None:
        story._cached_citations = citations
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