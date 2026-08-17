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
from ..models import User
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


@router.get(
    "/api/v1/history/entities/{entity_id}/geography",
    response_model=HistoricalGeographyOut,
)
def get_entity_geography(entity_id: UUID, db: Session = Depends(get_db)):
    geo = gov.get_geography(db, entity_id)
    if not geo:
        raise AppError("HISTORY_GEO_NOT_FOUND", "Historical geography not found", 404)
    return HistoricalGeographyOut.model_validate(geo)


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
