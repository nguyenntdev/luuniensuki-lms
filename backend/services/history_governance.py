# -*- coding: utf-8 -*-
"""History-First governance services (Phase 1).

Business logic for the historical domain: entity/claim/source/relation CRUD,
the verification-state machine, the claim-source verification invariant, and
the append-only governance audit log.

Rules enforced here (docs/specs/HISTORY_FIRST_MASTER_SPEC.md Part III):

- Engineering completion never implies historical verification.
- A factual/chronology/geographic/identification claim MUST NOT reach
  ``expert_verified`` unless it has at least one eligible source binding
  (``supports`` / ``primary_evidence_for``) and has passed editor review.
- State transitions are audited to ``historical_content_audit_log``.
"""
from __future__ import annotations

import uuid
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from ..models import (
    HistoricalClaim,
    HistoricalClaimSource,
    HistoricalContentAuditLog,
    HistoricalEntity,
    HistoricalEntityRelation,
    HistoricalGeography,
    HistoricalSource,
)


# --------------------------------------------------------------------------- #
# Audit
# --------------------------------------------------------------------------- #
def audit_action(
    db: Session,
    *,
    actor_id: Optional[UUID],
    action: str,
    resource_type: str,
    resource_id: Optional[UUID] = None,
    before_json: Optional[dict[str, Any]] = None,
    after_json: Optional[dict[str, Any]] = None,
    reason: Optional[str] = None,
    request_id: Optional[str] = None,
) -> None:
    """Append an immutable governance audit entry."""
    db.add(
        HistoricalContentAuditLog(
            actor_id=actor_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            before_json=before_json,
            after_json=after_json,
            reason=reason,
            request_id=request_id,
        )
    )


# --------------------------------------------------------------------------- #
# Entities
# --------------------------------------------------------------------------- #
def list_entities(
    db: Session,
    *,
    entity_type: Optional[str] = None,
    publication_status: Optional[str] = None,
    search: Optional[str] = None,
    offset: int = 0,
    limit: int = 50,
) -> tuple[list[HistoricalEntity], int]:
    q = select(HistoricalEntity)
    if entity_type:
        q = q.where(HistoricalEntity.entity_type == entity_type)
    if publication_status:
        q = q.where(HistoricalEntity.publication_status == publication_status)
    if search:
        like = f"%{search}%"
        q = q.where(
            or_(
                HistoricalEntity.name_vi.ilike(like),
                HistoricalEntity.name_en.ilike(like),
                HistoricalEntity.slug.ilike(like),
            )
        )
    total = db.scalar(select(func.count()).select_from(q.subquery())) or 0
    items = list(
        db.scalars(
            q.order_by(HistoricalEntity.name_vi).offset(offset).limit(limit)
        )
    )
    return items, total


def get_entity(db: Session, entity_id: UUID) -> Optional[HistoricalEntity]:
    return db.get(HistoricalEntity, entity_id)


def get_entity_by_slug(db: Session, slug: str) -> Optional[HistoricalEntity]:
    return db.scalar(
        select(HistoricalEntity).where(
            func.lower(HistoricalEntity.slug) == slug.lower()
        )
    )


def create_entity(
    db: Session,
    *,
    data: dict[str, Any],
    actor_id: Optional[UUID] = None,
) -> HistoricalEntity:
    entity = HistoricalEntity(**data)
    if actor_id:
        entity.created_by = actor_id
        entity.updated_by = actor_id
    db.add(entity)
    db.flush()
    audit_action(
        db,
        actor_id=actor_id,
        action="create",
        resource_type="entity",
        resource_id=entity.id,
        after_json={"slug": entity.slug, "entity_type": entity.entity_type},
    )
    return entity


def update_entity(
    db: Session,
    *,
    entity: HistoricalEntity,
    data: dict[str, Any],
    actor_id: Optional[UUID] = None,
) -> HistoricalEntity:
    before = {
        "slug": entity.slug,
        "name_vi": entity.name_vi,
        "publication_status": entity.publication_status,
    }
    for key, value in data.items():
        setattr(entity, key, value)
    entity.content_version += 1
    if actor_id:
        entity.updated_by = actor_id
    db.flush()
    audit_action(
        db,
        actor_id=actor_id,
        action="update",
        resource_type="entity",
        resource_id=entity.id,
        before_json=before,
        after_json={
            "slug": entity.slug,
            "name_vi": entity.name_vi,
            "publication_status": entity.publication_status,
            "content_version": entity.content_version,
        },
    )
    return entity


# --------------------------------------------------------------------------- #
# Sources
# --------------------------------------------------------------------------- #
def list_sources(
    db: Session,
    *,
    source_type: Optional[str] = None,
    search: Optional[str] = None,
    offset: int = 0,
    limit: int = 50,
) -> tuple[list[HistoricalSource], int]:
    q = select(HistoricalSource)
    if source_type:
        q = q.where(HistoricalSource.source_type == source_type)
    if search:
        like = f"%{search}%"
        q = q.where(
            or_(
                HistoricalSource.title.ilike(like),
                HistoricalSource.author_text.ilike(like),
            )
        )
    total = db.scalar(select(func.count()).select_from(q.subquery())) or 0
    items = list(
        db.scalars(
            q.order_by(HistoricalSource.title).offset(offset).limit(limit)
        )
    )
    return items, total


def get_source(db: Session, source_id: UUID) -> Optional[HistoricalSource]:
    return db.get(HistoricalSource, source_id)


def create_source(
    db: Session,
    *,
    data: dict[str, Any],
    actor_id: Optional[UUID] = None,
) -> HistoricalSource:
    source = HistoricalSource(**data)
    if actor_id:
        source.created_by = actor_id
    db.add(source)
    db.flush()
    audit_action(
        db,
        actor_id=actor_id,
        action="create",
        resource_type="source",
        resource_id=source.id,
        after_json={"title": source.title, "source_type": source.source_type},
    )
    return source


def update_source(
    db: Session,
    *,
    source: HistoricalSource,
    data: dict[str, Any],
    actor_id: Optional[UUID] = None,
) -> HistoricalSource:
    before = {"title": source.title, "verification_status": source.verification_status}
    for key, value in data.items():
        setattr(source, key, value)
    db.flush()
    audit_action(
        db,
        actor_id=actor_id,
        action="update",
        resource_type="source",
        resource_id=source.id,
        before_json=before,
        after_json={"title": source.title, "verification_status": source.verification_status},
    )
    return source


# --------------------------------------------------------------------------- #
# Claims
# --------------------------------------------------------------------------- #
ELIGIBLE_SUPPORT_TYPES = {"supports", "primary_evidence_for"}
REVIEWABLE_CLAIM_TYPES = {
    "factual",
    "chronology",
    "geographic",
    "identification",
}


def claim_has_eligible_source(db: Session, claim: HistoricalClaim) -> bool:
    """True if the claim has at least one binding whose support type is eligible
    for verification (``supports`` or ``primary_evidence_for``)."""
    if not claim.id:
        return False
    count = db.scalar(
        select(func.count())
        .select_from(HistoricalClaimSource)
        .where(
            HistoricalClaimSource.claim_id == claim.id,
            HistoricalClaimSource.support_type.in_(ELIGIBLE_SUPPORT_TYPES),
        )
    )
    return bool(count and count > 0)


def _can_be_editor_reviewed(db: Session, claim: HistoricalClaim) -> bool:
    """A reviewable factual claim requires an eligible source binding before it
    may pass editorial review (Spec 9.2: source-attached is a precondition of
    the review workflow)."""
    if claim.claim_type in REVIEWABLE_CLAIM_TYPES:
        return claim_has_eligible_source(db, claim)
    return True


def _can_be_expert_verified(db: Session, claim: HistoricalClaim) -> bool:
    """A reviewable factual claim requires an eligible source binding AND prior
    editor review before it may be expert-verified (Spec section 9.2)."""
    if claim.claim_type in REVIEWABLE_CLAIM_TYPES:
        return (
            claim.verification_status == "editor_reviewed"
            and claim_has_eligible_source(db, claim)
        )
    return claim.verification_status == "editor_reviewed"


def list_claims(
    db: Session,
    *,
    entity_id: Optional[UUID] = None,
    verification_status: Optional[str] = None,
    claim_type: Optional[str] = None,
    offset: int = 0,
    limit: int = 50,
) -> tuple[list[HistoricalClaim], int]:
    q = select(HistoricalClaim)
    if entity_id:
        q = q.where(HistoricalClaim.entity_id == entity_id)
    if verification_status:
        q = q.where(HistoricalClaim.verification_status == verification_status)
    if claim_type:
        q = q.where(HistoricalClaim.claim_type == claim_type)
    total = db.scalar(select(func.count()).select_from(q.subquery())) or 0
    items = list(
        db.scalars(
            q.order_by(HistoricalClaim.created_at).offset(offset).limit(limit)
        )
    )
    return items, total


def get_claim(db: Session, claim_id: UUID) -> Optional[HistoricalClaim]:
    return db.get(HistoricalClaim, claim_id)


def create_claim(
    db: Session,
    *,
    data: dict[str, Any],
    actor_id: Optional[UUID] = None,
) -> HistoricalClaim:
    claim = HistoricalClaim(**data)
    if actor_id:
        claim.created_by = actor_id
    db.add(claim)
    db.flush()
    audit_action(
        db,
        actor_id=actor_id,
        action="create",
        resource_type="claim",
        resource_id=claim.id,
        after_json={
            "statement_vi": claim.statement_vi,
            "claim_type": claim.claim_type,
            "verification_status": claim.verification_status,
            "origin": claim.origin,
        },
    )
    return claim


def update_claim(
    db: Session,
    *,
    claim: HistoricalClaim,
    data: dict[str, Any],
    actor_id: Optional[UUID] = None,
) -> HistoricalClaim:
    before = {
        "statement_vi": claim.statement_vi,
        "verification_status": claim.verification_status,
        "confidence": claim.confidence,
    }
    for key, value in data.items():
        setattr(claim, key, value)
    if actor_id:
        claim.updated_by = actor_id  # type: ignore[attr-defined]
    db.flush()
    audit_action(
        db,
        actor_id=actor_id,
        action="update",
        resource_type="claim",
        resource_id=claim.id,
        before_json=before,
        after_json={
            "statement_vi": claim.statement_vi,
            "verification_status": claim.verification_status,
            "confidence": claim.confidence,
        },
    )
    return claim


def transition_claim_status(
    db: Session,
    *,
    claim: HistoricalClaim,
    target: str,
    actor_id: Optional[UUID],
    reason: Optional[str] = None,
    action: str = "update",
) -> HistoricalClaim:
    """Move a claim through the verification state machine, enforcing the
    source-binding invariant. Raises ValueError on invalid transitions."""
    before = claim.verification_status
    if target == before:
        return claim

    if target == "editor_reviewed" and not _can_be_editor_reviewed(db, claim):
        raise ValueError(
            "Editor review of a factual claim requires an eligible source."
        )
    if target == "expert_verified" and not _can_be_expert_verified(db, claim):
        raise ValueError(
            "Verified factual claims require an eligible source and prior "
            "editor review."
        )
    if target == "needs_source" and claim_has_eligible_source(db, claim):
        raise ValueError(
            "Cannot mark a claim as needs_source while an eligible source is bound."
        )

    claim.verification_status = target
    claim.review_notes = reason or claim.review_notes
    if target == "editor_reviewed":
        claim.reviewed_by = actor_id
        claim.reviewed_at = func.now()
    if target == "expert_verified":
        claim.verified_by = actor_id
        claim.verified_at = func.now()
    db.flush()
    audit_action(
        db,
        actor_id=actor_id,
        action=action,
        resource_type="claim",
        resource_id=claim.id,
        before_json={"verification_status": before},
        after_json={"verification_status": target},
        reason=reason,
    )
    return claim


def attach_source_to_claim(
    db: Session,
    *,
    claim: HistoricalClaim,
    source: HistoricalSource,
    data: dict[str, Any],
    actor_id: Optional[UUID] = None,
) -> HistoricalClaimSource:
    binding = HistoricalClaimSource(
        claim_id=claim.id,
        source_id=source.id,
        support_type=data.get("support_type", "supports"),
        locator_type=data.get("locator_type"),
        page_start=data.get("page_start"),
        page_end=data.get("page_end"),
        chapter=data.get("chapter"),
        section=data.get("section"),
        figure=data.get("figure"),
        folio=data.get("folio"),
        inscription_location=data.get("inscription_location"),
        quotation_excerpt=data.get("quotation_excerpt"),
        quotation_language=data.get("quotation_language"),
        editor_note=data.get("editor_note"),
        created_by=actor_id,
    )
    db.add(binding)
    db.flush()
    # A claim with an eligible source may now move toward review, but is not
    # automatically verified.
    if claim.verification_status == "unreviewed" and binding.support_type in ELIGIBLE_SUPPORT_TYPES:
        claim.verification_status = "source_attached"
        db.flush()
    audit_action(
        db,
        actor_id=actor_id,
        action="attach_source",
        resource_type="claim",
        resource_id=claim.id,
        after_json={"source_id": str(source.id), "support_type": binding.support_type},
    )
    return binding


def list_claim_sources(
    db: Session, *, claim_id: UUID
) -> list[HistoricalClaimSource]:
    return list(
        db.scalars(
            select(HistoricalClaimSource)
            .where(HistoricalClaimSource.claim_id == claim_id)
            .options(selectinload(HistoricalClaimSource.source))
        )
    )


# --------------------------------------------------------------------------- #
# Relations
# --------------------------------------------------------------------------- #
def list_relations(
    db: Session,
    *,
    entity_id: Optional[UUID] = None,
    offset: int = 0,
    limit: int = 100,
) -> tuple[list[HistoricalEntityRelation], int]:
    q = select(HistoricalEntityRelation)
    if entity_id:
        q = q.where(
            or_(
                HistoricalEntityRelation.subject_entity_id == entity_id,
                HistoricalEntityRelation.object_entity_id == entity_id,
            )
        )
    total = db.scalar(select(func.count()).select_from(q.subquery())) or 0
    items = list(db.scalars(q.offset(offset).limit(limit)))
    return items, total


def create_relation(
    db: Session,
    *,
    data: dict[str, Any],
    actor_id: Optional[UUID] = None,
) -> HistoricalEntityRelation:
    relation = HistoricalEntityRelation(**data)
    if actor_id:
        relation.created_by = actor_id
    db.add(relation)
    db.flush()
    audit_action(
        db,
        actor_id=actor_id,
        action="create",
        resource_type="relation",
        resource_id=relation.id,
        after_json={
            "subject_entity_id": str(relation.subject_entity_id),
            "predicate": relation.predicate,
            "object_entity_id": str(relation.object_entity_id),
        },
    )
    return relation


def delete_relation(db: Session, *, relation_id: UUID) -> bool:
    relation = db.get(HistoricalEntityRelation, relation_id)
    if not relation:
        return False
    db.delete(relation)
    db.flush()
    audit_action(
        db,
        actor_id=None,
        action="delete",
        resource_type="relation",
        resource_id=relation_id,
        before_json={"subject_entity_id": str(relation.subject_entity_id)},
    )
    return True


# --------------------------------------------------------------------------- #
# Geography
# --------------------------------------------------------------------------- #
def get_geography(db: Session, entity_id: UUID) -> Optional[HistoricalGeography]:
    return db.get(HistoricalGeography, entity_id)


def upsert_geography(
    db: Session,
    *,
    entity_id: UUID,
    data: dict[str, Any],
) -> HistoricalGeography:
    geo = db.get(HistoricalGeography, entity_id)
    if geo is None:
        geo = HistoricalGeography(entity_id=entity_id, **data)
        db.add(geo)
    else:
        for key, value in data.items():
            setattr(geo, key, value)
    db.flush()
    return geo
