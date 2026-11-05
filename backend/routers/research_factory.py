# -*- coding: utf-8 -*-
"""Research Factory Admin & Release API Router (Phase P11 / V5-T079 / W07-A09).

Exposes production control plane endpoints for:
- Preflight release verification against publication gates.
- Atomic snapshot creation, HMAC signed revisions, and pointer swaps.
- Immediate CDN & application cache purge tracking.
- Retraction / invalidation of disputed claims, expired sources, or stories.
- Revert / rollback of active releases with audit logging.
"""
from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..apischemas.research_factory import (
    InvalidationResultOut,
    ReleaseAuditOut,
    ReleaseCreateIn,
    ReleaseDetailOut,
    ReleaseInvalidateIn,
    ReleaseOut,
    ReleasePreflightIn,
    ReleasePreflightReportOut,
    ReleaseRollbackIn,
    RollbackResultOut,
)
from ..db import get_db
from ..deps import get_current_user, get_staff_user
from ..errors import AppError
from ..models import User
from ..research_factory_models import (
    ResearchCachePurgeEvent,
    ResearchCorrectionEvent,
    ResearchPublicationRelease,
)
from ..services.research_factory import releases as svc

router = APIRouter(prefix="/api/v1/admin/research-factory", tags=["research-factory-admin"])


def _release_to_detail(release: ResearchPublicationRelease) -> ReleaseDetailOut:
    stories_in_snapshot = release.snapshot_payload.get("stories", [])
    return ReleaseDetailOut(
        id=release.id,
        release_code=release.release_code,
        scope=release.scope,
        status=release.status,
        manifest_sha256=release.manifest_sha256,
        signed_revision=release.signed_revision,
        signer_identity=release.signer_identity,
        signer_role=release.signer_role,
        snapshot_payload=release.snapshot_payload,
        previous_release_id=release.previous_release_id,
        published_at=release.published_at,
        invalidated_at=release.invalidated_at,
        rolled_back_at=release.rolled_back_at,
        cache_purge_status=release.cache_purge_status,
        purged_at=release.purged_at,
        stories_count=len(stories_in_snapshot),
        created_at=release.created_at,
    )


# --------------------------------------------------------------------------- #
# Preflight Verification
# --------------------------------------------------------------------------- #
@router.post(
    "/releases/preflight",
    response_model=ReleasePreflightReportOut,
    dependencies=[Depends(get_staff_user)],
)
def check_release_preflight(
    payload: ReleasePreflightIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Run two-phase preflight validation against editorial, rights, and asset gates."""
    report = svc.run_release_preflight(
        db,
        story_ids=payload.story_ids,
        claim_ids=payload.claim_ids,
        scope=payload.scope,
        allow_unreviewed=payload.allow_unreviewed,
    )
    return ReleasePreflightReportOut.model_validate(report)


# --------------------------------------------------------------------------- #
# Atomic Publication & Pointer Swap
# --------------------------------------------------------------------------- #
@router.post(
    "/releases",
    response_model=ReleaseDetailOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(get_staff_user)],
)
def create_publication_release(
    payload: ReleaseCreateIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Atomically publish a collection of approved stories with signed revision and cache purge."""
    release = svc.publish_release(
        db,
        story_ids=payload.story_ids,
        release_code=payload.release_code,
        signer=current_user,
        previous_release_id=payload.previous_release_id,
        scope=payload.scope,
        allow_unreviewed=payload.allow_unreviewed,
        simulate_failure_at_story_idx=payload.simulate_failure_at_story_idx,
    )
    return _release_to_detail(release)


# --------------------------------------------------------------------------- #
# Release Lookup
# --------------------------------------------------------------------------- #
@router.get(
    "/releases/active",
    response_model=ReleaseDetailOut,
    dependencies=[Depends(get_staff_user)],
)
def get_active_release(
    scope: str = Query(default="cuu_dinh_162_motifs"),
    db: Session = Depends(get_db),
):
    """Retrieve the currently active published release manifest."""
    release = svc.get_active_publication_release(db, scope=scope)
    if not release:
        raise AppError("ACTIVE_RELEASE_NOT_FOUND", f"No active release found for scope '{scope}'.", 404)
    return _release_to_detail(release)


@router.get(
    "/releases/{release_id}",
    response_model=ReleaseDetailOut,
    dependencies=[Depends(get_staff_user)],
)
def get_release_by_id(
    release_id: UUID,
    db: Session = Depends(get_db),
):
    """Retrieve detailed snapshot and signed manifest for a specific release."""
    release = svc.get_publication_release(db, release_id=release_id)
    if not release:
        raise AppError("RELEASE_NOT_FOUND", f"Publication release '{release_id}' not found.", 404)
    return _release_to_detail(release)


# --------------------------------------------------------------------------- #
# Invalidation & Retraction (P11 Watchers)
# --------------------------------------------------------------------------- #
@router.post(
    "/releases/{release_id}/invalidate",
    response_model=InvalidationResultOut,
    dependencies=[Depends(get_staff_user)],
)
def invalidate_release(
    release_id: UUID,
    payload: ReleaseInvalidateIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Invalidate a specific story, claim, or entire release and immediately purge caches."""
    result = svc.invalidate_release_item(
        db,
        release_id=release_id,
        trigger_type=payload.trigger_type,
        rationale=payload.rationale,
        actor=current_user,
        story_id=payload.story_id,
        claim_id=payload.claim_id,
        source_id=payload.source_id,
        entity_slug=payload.entity_slug,
    )
    return InvalidationResultOut.model_validate(result)


# --------------------------------------------------------------------------- #
# Revert & Rollback (P11-A10)
# --------------------------------------------------------------------------- #
@router.post(
    "/releases/{release_id}/rollback",
    response_model=RollbackResultOut,
    dependencies=[Depends(get_staff_user)],
)
def rollback_release(
    release_id: UUID,
    payload: ReleaseRollbackIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Atomically roll back a published release to a prior state and purge caches."""
    result = svc.rollback_publication_release(
        db,
        release_id=release_id,
        rollback_reason=payload.rollback_reason,
        actor=current_user,
        restore_release_id=payload.restore_release_id,
    )
    return RollbackResultOut.model_validate(result)


# --------------------------------------------------------------------------- #
# Audit & Provenance History
# --------------------------------------------------------------------------- #
@router.get(
    "/releases/{release_id}/audit",
    response_model=ReleaseAuditOut,
    dependencies=[Depends(get_staff_user)],
)
def get_release_audit_trail(
    release_id: UUID,
    db: Session = Depends(get_db),
):
    """Retrieve correction events and cache purge records for a release."""
    release = svc.get_publication_release(db, release_id=release_id)
    if not release:
        raise AppError("RELEASE_NOT_FOUND", f"Publication release '{release_id}' not found.", 404)

    corrections = db.scalars(
        select(ResearchCorrectionEvent)
        .where(ResearchCorrectionEvent.release_id == release.id)
        .order_by(ResearchCorrectionEvent.created_at.desc())
    ).all()

    purges = db.scalars(
        select(ResearchCachePurgeEvent)
        .where(ResearchCachePurgeEvent.release_id == release.id)
        .order_by(ResearchCachePurgeEvent.purged_at.desc())
    ).all()

    return ReleaseAuditOut(
        release_id=release.id,
        release_code=release.release_code,
        corrections=[
            {
                "id": str(c.id),
                "trigger_type": c.trigger_type,
                "story_id": str(c.story_id) if c.story_id else None,
                "claim_id": str(c.claim_id) if c.claim_id else None,
                "source_id": str(c.source_id) if c.source_id else None,
                "rationale": c.rationale,
                "actor": c.actor_identity,
                "cache_purged": c.cache_purged,
                "created_at": c.created_at.isoformat(),
            }
            for c in corrections
        ],
        cache_purges=[
            {
                "id": str(p.id),
                "cache_key": p.cache_key,
                "resource_type": p.resource_type,
                "resource_id": p.resource_id,
                "status": p.purge_status,
                "purged_at": p.purged_at.isoformat(),
            }
            for p in purges
        ],
    )
