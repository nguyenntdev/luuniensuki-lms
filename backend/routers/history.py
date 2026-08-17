# -*- coding: utf-8 -*-
"""History-First public + admin API router (Phase 1).

Public read endpoints under ``/api/v1/history/*`` (no auth for published
content) and admin mutation endpoints under ``/api/v1/admin/history/*``
(RBAC + audit logging).

Per docs/specs/HISTORY_FIRST_MASTER_SPEC.md Part XVII, the public surface
must not require login, and every state-changing admin endpoint audits the
actor/action to ``historical_content_audit_log``.
"""
from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, or_, select, text
from sqlalchemy.orm import Session

from ..apischemas.history import (
    HistoricalAssetCreate,
    HistoricalAssetOut,
    HistoricalClaimCreate,
    HistoricalClaimListOut,
    HistoricalClaimOut,
    HistoricalClaimSourceCreate,
    HistoricalClaimSourceOut,
    HistoricalClaimUpdate,
    HistoricalEntityCreate,
    HistoricalEntityListOut,
    HistoricalEntityOut,
    HistoricalEntityUpdate,
    HistoricalGeographyOut,
    HistoricalGeographyUpsert,
    HistoricalRelationCreate,
    HistoricalRelationOut,
    HistoricalSearchItem,
    HistoricalSearchOut,
    HistoricalSourceCreate,
    HistoricalSourceListOut,
    HistoricalSourceOut,
    HistoricalSourceUpdate,
)
from ..db import get_db
from ..deps import get_admin_user, get_current_user, get_staff_user
from ..errors import AppError
from ..models import HistoricalEntity, HistoricalEntityRelation, User
from ..services import history_governance as gov

router = APIRouter(tags=["history"])


def _entity_to_out(entity) -> HistoricalEntityOut:
    return HistoricalEntityOut.model_validate(entity)


# --------------------------------------------------------------------------- #
# Public read endpoints — no auth required for published/verified content
# --------------------------------------------------------------------------- #
@router.get("/api/v1/history/entities", response_model=HistoricalEntityListOut)
def list_history_entities(
    entity_type: Optional[str] = Query(default=None),
    publication_status: Optional[str] = Query(default=None),
    search: Optional[str] = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    items, total = gov.list_entities(
        db,
        entity_type=entity_type,
        publication_status=publication_status,
        search=search,
        offset=offset,
        limit=limit,
    )
    return HistoricalEntityListOut(
        items=[_entity_to_out(e) for e in items], total=total, offset=offset, limit=limit
    )


@router.get("/api/v1/history/entities/by-slug/{slug}", response_model=HistoricalEntityOut)
def get_history_entity_by_slug(slug: str, db: Session = Depends(get_db)):
    entity = gov.get_entity_by_slug(db, slug)
    if not entity:
        raise AppError("HISTORY_ENTITY_NOT_FOUND", "Historical entity not found", 404)
    return _entity_to_out(entity)


@router.get("/api/v1/history/entities/{entity_id}", response_model=HistoricalEntityOut)
def get_history_entity(entity_id: UUID, db: Session = Depends(get_db)):
    entity = gov.get_entity(db, entity_id)
    if not entity:
        raise AppError("HISTORY_ENTITY_NOT_FOUND", "Historical entity not found", 404)
    return _entity_to_out(entity)


@router.get(
    "/api/v1/history/entities/{entity_id}/claims",
    response_model=HistoricalClaimListOut,
)
def list_entity_claims(
    entity_id: UUID,
    verification_status: Optional[str] = Query(default=None),
    claim_type: Optional[str] = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    items, total = gov.list_claims(
        db,
        entity_id=entity_id,
        verification_status=verification_status,
        claim_type=claim_type,
        offset=offset,
        limit=limit,
    )
    return HistoricalClaimListOut(
        items=[HistoricalClaimOut.model_validate(c) for c in items],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get("/api/v1/history/claims/{claim_id}", response_model=HistoricalClaimOut)
def get_history_claim(claim_id: UUID, db: Session = Depends(get_db)):
    claim = gov.get_claim(db, claim_id)
    if not claim:
        raise AppError("HISTORY_CLAIM_NOT_FOUND", "Historical claim not found", 404)
    return HistoricalClaimOut.model_validate(claim)


@router.get(
    "/api/v1/history/claims/{claim_id}/sources",
    response_model=list[HistoricalClaimSourceOut],
)
def list_claim_sources(claim_id: UUID, db: Session = Depends(get_db)):
    if not gov.get_claim(db, claim_id):
        raise AppError("HISTORY_CLAIM_NOT_FOUND", "Historical claim not found", 404)
    bindings = gov.list_claim_sources(db, claim_id=claim_id)
    return [HistoricalClaimSourceOut.model_validate(b) for b in bindings]


@router.get("/api/v1/history/sources", response_model=HistoricalSourceListOut)
def list_history_sources(
    source_type: Optional[str] = Query(default=None),
    search: Optional[str] = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    items, total = gov.list_sources(
        db, source_type=source_type, search=search, offset=offset, limit=limit
    )
    return HistoricalSourceListOut(
        items=[HistoricalSourceOut.model_validate(s) for s in items],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get("/api/v1/history/sources/{source_id}", response_model=HistoricalSourceOut)
def get_history_source(source_id: UUID, db: Session = Depends(get_db)):
    source = gov.get_source(db, source_id)
    if not source:
        raise AppError("HISTORY_SOURCE_NOT_FOUND", "Historical source not found", 404)
    return HistoricalSourceOut.model_validate(source)


@router.get(
    "/api/v1/history/entities/{entity_id}/relations",
    response_model=list[HistoricalRelationOut],
)
def list_entity_relations(
    entity_id: UUID,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=200),
    db: Session = Depends(get_db),
):
    if not gov.get_entity(db, entity_id):
        raise AppError("HISTORY_ENTITY_NOT_FOUND", "Historical entity not found", 404)
    items, _ = gov.list_relations(db, entity_id=entity_id, offset=offset, limit=limit)
    return [HistoricalRelationOut.model_validate(r) for r in items]


@router.get("/api/v1/history/entities/{entity_id}/graph")
def entity_knowledge_graph(
    entity_id: UUID,
    depth: int = Query(default=1, ge=1, le=2),
    db: Session = Depends(get_db),
):
    """Contextual knowledge graph (Spec section 26): the requested entity and
    its 1-hop (optionally 2-hop) neighbors from historical_entity_relations.

    Nodes carry type/slug/name so the explorer can render links; edges carry
    the predicate, direction and optional source. Unverified relations are
    included but flagged so the UI can show epistemic state honestly.
    """
    from ..models import HistoricalEntityRelation

    root = gov.get_entity(db, entity_id)
    if not root:
        raise AppError("HISTORY_ENTITY_NOT_FOUND", "Historical entity not found", 404)

    nodes = {str(root.id): _entity_node(root)}
    edges = []

    def _scan(entity_id_uuid: UUID, current_depth: int) -> None:
        rels = list(
            db.scalars(
                select(HistoricalEntityRelation).where(
                    or_(
                        HistoricalEntityRelation.subject_entity_id == entity_id_uuid,
                        HistoricalEntityRelation.object_entity_id == entity_id_uuid,
                    )
                )
            )
        )
        for rel in rels:
            other_id = (
                rel.object_entity_id
                if rel.subject_entity_id == entity_id_uuid
                else rel.subject_entity_id
            )
            other = db.get(HistoricalEntity, other_id)
            if not other:
                continue
            if str(other.id) not in nodes:
                nodes[str(other.id)] = _entity_node(other)
            edges.append(
                {
                    "source": str(rel.subject_entity_id),
                    "target": str(rel.object_entity_id),
                    "predicate": rel.predicate,
                    "verification_status": rel.verification_status,
                    "source_id": str(rel.source_id) if rel.source_id else None,
                }
            )
            if current_depth < depth and other.entity_type not in ("urn",):
                _scan(other_id, current_depth + 1)

    _scan(entity_id, 1)

    return {
        "root_id": str(root.id),
        "nodes": list(nodes.values()),
        "edges": edges,
    }


def _entity_node(entity) -> dict:
    return {
        "id": str(entity.id),
        "entity_type": entity.entity_type,
        "slug": entity.slug,
        "name_vi": entity.name_vi,
        "name_en": entity.name_en,
        "publication_status": entity.publication_status,
        "summary_vi": entity.summary_vi,
    }


@router.get("/api/v1/history/events")
def list_history_events(db: Session = Depends(get_db)):
    """Expose heritage timeline events as graph-joinable history data.

    Reads the Rust-owned ``historical_events`` table (migration 0043) so the
    timeline and the knowledge graph share one source of truth. No fabricated
    fields; returns what the timeline already records.
    """
    from sqlalchemy import text as sa_text

    table_exists = db.scalar(
        sa_text(
            "SELECT to_regclass('public.historical_events') IS NOT NULL"
        )
    )
    if not table_exists:
        return {"items": [], "meta": {"count": 0}}

    result = []
    for (event_id, slug, name_vi, occurred_on, description_vi, era_id) in db.execute(
        text(
            "SELECT id, slug, name_vi, occurred_on, description_vi, era_id "
            "FROM historical_events ORDER BY occurred_on"
        )
    ).all():
        result.append(
            {
                "id": str(event_id),
                "slug": slug,
                "name_vi": name_vi,
                "occurred_on": str(occurred_on),
                "description_vi": description_vi,
                "era_id": str(era_id) if era_id else None,
            }
        )
    return {"items": result, "meta": {"count": len(result)}}


@router.get(
    "/api/v1/history/entities/{entity_id}/geography",
    response_model=HistoricalGeographyOut,
)
def get_entity_geography(entity_id: UUID, db: Session = Depends(get_db)):
    geo = gov.get_geography(db, entity_id)
    if not geo:
        raise AppError("HISTORY_GEO_NOT_FOUND", "Historical geography not found", 404)
    return HistoricalGeographyOut.model_validate(geo)


@router.get("/api/v1/history/map")
def history_map(
    entity_type: Optional[str] = Query(default=None),
    mapping_status: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    """Heritage map data contract (Spec section 24.3).

    Returns only entities that have a geographic signal (lat/lng or a
    historical_geographies row), with precision/mapping-status metadata so the
    UI can render uncertainty honestly (24.4). Never fabricates coordinates.
    """
    q = select(HistoricalEntity).where(
        HistoricalEntity.deleted_at.is_(None),
        HistoricalEntity.latitude.isnot(None),
        HistoricalEntity.longitude.isnot(None),
    )
    if entity_type:
        q = q.where(HistoricalEntity.entity_type == entity_type)
    if mapping_status:
        q = q.join(
            HistoricalGeography,
            HistoricalGeography.entity_id == HistoricalEntity.id,
        ).where(HistoricalGeography.mapping_status == mapping_status)

    items = []
    for entity in db.scalars(q):
        geo = db.get(HistoricalGeography, entity.id)
        related = gov.list_relations(db, entity_id=entity.id, offset=0, limit=50)[0]
        items.append(
            {
                "entity_id": str(entity.id),
                "entity_type": entity.entity_type,
                "slug": entity.slug,
                "name": entity.name_vi,
                "lat": entity.latitude,
                "lng": entity.longitude,
                "geo_precision": (geo.geo_precision if geo else entity.geo_precision),
                "mapping_status": (geo.mapping_status if geo else None),
                "related_reliefs": [
                    str(r.object_entity_id)
                    for r in related
                    if r.predicate == "depicts" and r.object_entity_id
                ],
                "urns": [
                    str(r.object_entity_id)
                    for r in related
                    if r.predicate in ("located_on", "part_of") and r.object_entity_id
                ],
            }
        )
    return {"items": items, "meta": {"count": len(items)}}


@router.get("/api/v1/history/urns")
def history_urns(db: Session = Depends(get_db)):
    """Convenience: all urn entities with their relief counts (for the public
    Cửu Đỉnh overview and Atlas urn filter)."""
    urns, _ = gov.list_entities(db, entity_type="urn", offset=0, limit=50)
    result = []
    for urn in urns:
        count = db.scalar(
            select(func.count())
            .select_from(HistoricalEntityRelation)
            .where(
                HistoricalEntityRelation.predicate == "located_on",
                HistoricalEntityRelation.object_entity_id == urn.id,
            )
        )
        result.append(
            {
                "id": str(urn.id),
                "slug": urn.slug,
                "name_vi": urn.name_vi,
                "name_en": urn.name_en,
                "summary_vi": urn.summary_vi,
                "publication_status": urn.publication_status,
                "relief_count": int(count or 0),
            }
        )
    result.sort(key=lambda u: u["slug"])
    return {"items": result, "total": len(result)}


@router.get("/api/v1/history/search", response_model=HistoricalSearchOut)
def search_history(
    q: str = Query(..., min_length=1, max_length=200),
    limit: int = Query(default=20, ge=1, le=50),
    db: Session = Depends(get_db),
):
    items, _ = gov.list_entities(db, search=q, offset=0, limit=limit)
    return HistoricalSearchOut(
        query=q,
        items=[
            HistoricalSearchItem(
                id=e.id,
                entity_type=e.entity_type,
                slug=e.slug,
                name_vi=e.name_vi,
                name_en=e.name_en,
                summary_vi=e.summary_vi,
                publication_status=e.publication_status,
            )
            for e in items
        ],
        total=len(items),
    )


# --------------------------------------------------------------------------- #
# Admin mutation endpoints — require admin, audit everything
# --------------------------------------------------------------------------- #
@router.post(
    "/api/v1/admin/history/entities",
    response_model=HistoricalEntityOut,
    dependencies=[Depends(get_staff_user)],
)
def create_history_entity(
    payload: HistoricalEntityCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if gov.get_entity_by_slug(db, payload.slug):
        raise AppError("HISTORY_SLUG_EXISTS", "Slug already in use", 409)
    entity = gov.create_entity(
        db, data=payload.model_dump(), actor_id=current_user.id
    )
    db.commit()
    return _entity_to_out(entity)


@router.patch(
    "/api/v1/admin/history/entities/{entity_id}",
    response_model=HistoricalEntityOut,
    dependencies=[Depends(get_staff_user)],
)
def update_history_entity(
    entity_id: UUID,
    payload: HistoricalEntityUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    entity = gov.get_entity(db, entity_id)
    if not entity:
        raise AppError("HISTORY_ENTITY_NOT_FOUND", "Historical entity not found", 404)
    data = payload.model_dump(exclude_unset=True)
    if "slug" in data and data["slug"] and data["slug"] != entity.slug:
        existing = gov.get_entity_by_slug(db, data["slug"])
        if existing and existing.id != entity.id:
            raise AppError("HISTORY_SLUG_EXISTS", "Slug already in use", 409)
    entity = gov.update_entity(db, entity=entity, data=data, actor_id=current_user.id)
    db.commit()
    return _entity_to_out(entity)


@router.post(
    "/api/v1/admin/history/sources",
    response_model=HistoricalSourceOut,
    dependencies=[Depends(get_staff_user)],
)
def create_history_source(
    payload: HistoricalSourceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    source = gov.create_source(db, data=payload.model_dump(), actor_id=current_user.id)
    db.commit()
    return HistoricalSourceOut.model_validate(source)


@router.patch(
    "/api/v1/admin/history/sources/{source_id}",
    response_model=HistoricalSourceOut,
    dependencies=[Depends(get_staff_user)],
)
def update_history_source(
    source_id: UUID,
    payload: HistoricalSourceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    source = gov.get_source(db, source_id)
    if not source:
        raise AppError("HISTORY_SOURCE_NOT_FOUND", "Historical source not found", 404)
    source = gov.update_source(
        db, source=source, data=payload.model_dump(exclude_unset=True), actor_id=current_user.id
    )
    db.commit()
    return HistoricalSourceOut.model_validate(source)


@router.post(
    "/api/v1/admin/history/claims",
    response_model=HistoricalClaimOut,
    dependencies=[Depends(get_staff_user)],
)
def create_history_claim(
    payload: HistoricalClaimCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not gov.get_entity(db, payload.entity_id):
        raise AppError("HISTORY_ENTITY_NOT_FOUND", "Historical entity not found", 404)
    claim = gov.create_claim(db, data=payload.model_dump(), actor_id=current_user.id)
    db.commit()
    return HistoricalClaimOut.model_validate(claim)


@router.patch(
    "/api/v1/admin/history/claims/{claim_id}",
    response_model=HistoricalClaimOut,
    dependencies=[Depends(get_staff_user)],
)
def update_history_claim(
    claim_id: UUID,
    payload: HistoricalClaimUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    claim = gov.get_claim(db, claim_id)
    if not claim:
        raise AppError("HISTORY_CLAIM_NOT_FOUND", "Historical claim not found", 404)
    claim = gov.update_claim(
        db, claim=claim, data=payload.model_dump(exclude_unset=True), actor_id=current_user.id
    )
    db.commit()
    return HistoricalClaimOut.model_validate(claim)


@router.post(
    "/api/v1/admin/history/claims/{claim_id}/sources",
    response_model=HistoricalClaimSourceOut,
    dependencies=[Depends(get_staff_user)],
)
def attach_claim_source(
    claim_id: UUID,
    payload: HistoricalClaimSourceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    claim = gov.get_claim(db, claim_id)
    if not claim:
        raise AppError("HISTORY_CLAIM_NOT_FOUND", "Historical claim not found", 404)
    source = gov.get_source(db, payload.source_id)
    if not source:
        raise AppError("HISTORY_SOURCE_NOT_FOUND", "Historical source not found", 404)
    binding = gov.attach_source_to_claim(
        db, claim=claim, source=source, data=payload.model_dump(), actor_id=current_user.id
    )
    db.commit()
    return HistoricalClaimSourceOut.model_validate(binding)


@router.post(
    "/api/v1/admin/history/claims/{claim_id}/transition",
    response_model=HistoricalClaimOut,
    dependencies=[Depends(get_staff_user)],
)
def transition_claim_status(
    claim_id: UUID,
    target: str = Query(...),
    reason: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    claim = gov.get_claim(db, claim_id)
    if not claim:
        raise AppError("HISTORY_CLAIM_NOT_FOUND", "Historical claim not found", 404)
    action_map = {
        "editor_reviewed": "editor_approve",
        "expert_verified": "expert_verify",
        "rejected": "reject",
        "disputed": "dispute",
        "needs_source": "request_source",
        "superseded": "supersede",
    }
    try:
        claim = gov.transition_claim_status(
            db,
            claim=claim,
            target=target,
            actor_id=current_user.id,
            reason=reason,
            action=action_map.get(target, "update"),
        )
    except ValueError as exc:
        raise AppError("HISTORY_CLAIM_INVALID_TRANSITION", str(exc), 422) from exc
    db.commit()
    return HistoricalClaimOut.model_validate(claim)


@router.post(
    "/api/v1/admin/history/relations",
    response_model=HistoricalRelationOut,
    dependencies=[Depends(get_staff_user)],
)
def create_history_relation(
    payload: HistoricalRelationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if payload.subject_entity_id == payload.object_entity_id:
        raise AppError(
            "HISTORY_SELF_RELATION",
            "Self-relations are not allowed",
            422,
        )
    if not gov.get_entity(db, payload.subject_entity_id):
        raise AppError("HISTORY_ENTITY_NOT_FOUND", "Subject entity not found", 404)
    if not gov.get_entity(db, payload.object_entity_id):
        raise AppError("HISTORY_ENTITY_NOT_FOUND", "Object entity not found", 404)
    try:
        relation = gov.create_relation(
            db, data=payload.model_dump(), actor_id=current_user.id
        )
    except Exception as exc:  # unique constraint on (subject, predicate, object)
        db.rollback()
        raise AppError("HISTORY_RELATION_EXISTS", "Relation already exists", 409) from exc
    db.commit()
    return HistoricalRelationOut.model_validate(relation)


@router.delete(
    "/api/v1/admin/history/relations/{relation_id}",
    dependencies=[Depends(get_staff_user)],
)
def delete_history_relation(relation_id: UUID, db: Session = Depends(get_db)):
    if not gov.delete_relation(db, relation_id=relation_id):
        raise AppError("HISTORY_RELATION_NOT_FOUND", "Relation not found", 404)
    db.commit()
    return {"ok": True}


@router.put(
    "/api/v1/admin/history/entities/{entity_id}/geography",
    response_model=HistoricalGeographyOut,
    dependencies=[Depends(get_staff_user)],
)
def upsert_history_geography(
    entity_id: UUID,
    payload: HistoricalGeographyUpsert,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not gov.get_entity(db, entity_id):
        raise AppError("HISTORY_ENTITY_NOT_FOUND", "Historical entity not found", 404)
    geo = gov.upsert_geography(db, entity_id=entity_id, data=payload.model_dump())
    gov.audit_action(
        db,
        actor_id=current_user.id,
        action="update",
        resource_type="geography",
        resource_id=entity_id,
        after_json={"geo_precision": geo.geo_precision, "mapping_status": geo.mapping_status},
    )
    db.commit()
    return HistoricalGeographyOut.model_validate(geo)


@router.post(
    "/api/v1/admin/history/assets",
    response_model=HistoricalAssetOut,
    dependencies=[Depends(get_staff_user)],
)
def create_history_asset(
    payload: HistoricalAssetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from ..models import HistoricalAsset

    asset = HistoricalAsset(**payload.model_dump())
    db.add(asset)
    db.flush()
    gov.audit_action(
        db,
        actor_id=current_user.id,
        action="create",
        resource_type="asset",
        resource_id=asset.id,
        after_json={"asset_type": asset.asset_type, "storage_url": asset.storage_url},
    )
    db.commit()
    return HistoricalAssetOut.model_validate(asset)


@router.get(
    "/api/v1/admin/history/audit",
    dependencies=[Depends(get_admin_user)],
)
def list_history_audit(
    resource_type: Optional[str] = Query(default=None),
    resource_id: Optional[UUID] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    from sqlalchemy import select

    from ..models import HistoricalContentAuditLog

    q = select(HistoricalContentAuditLog).order_by(
        HistoricalContentAuditLog.created_at.desc()
    )
    if resource_type:
        q = q.where(HistoricalContentAuditLog.resource_type == resource_type)
    if resource_id:
        q = q.where(HistoricalContentAuditLog.resource_id == resource_id)
    rows = list(db.scalars(q.offset(offset).limit(limit)))
    return {
        "items": [
            {
                "id": r.id,
                "actor_id": str(r.actor_id) if r.actor_id else None,
                "action": r.action,
                "resource_type": r.resource_type,
                "resource_id": str(r.resource_id) if r.resource_id else None,
                "before": r.before_json,
                "after": r.after_json,
                "reason": r.reason,
                "request_id": r.request_id,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ],
        "total": len(rows),
    }
