# -*- coding: utf-8 -*-
"""Museum Operator Media CMS Router (Wave W04 / Slot A10 / V5-T050).

Provides admin endpoints for museum operators and curators:
- Secure asset uploads with format & magic byte verification (GLB, PNG, JPEG, WEBP)
- Licensing & rights metadata governance (HMCC, CC BY 4.0, educational fair use)
- Staged publication lifecycle: draft -> in_review -> approved -> published
- Abuse prevention: rejection of executables/scripts (.exe, .sh, .php, .html)
- Strict role-based permissions (editor/staff for uploads & edits, admin for approval & publish)
- Integration with HistoricalAsset catalog and immutable audit logging
"""
from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import (
    APIRouter,
    Body,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from ..apischemas.media_cms import (
    MediaCmsItemListOut,
    MediaCmsItemOut,
    MediaCmsItemUpdate,
    MediaCmsPreviewOut,
    MediaCmsReviewAction,
)
from ..db import get_db
from ..deps import get_admin_user, get_current_user, get_staff_user
from ..models import User
from ..services import media_cms as cms_service

router = APIRouter(prefix="/api/v1/admin/media-cms", tags=["admin-media-cms"])


@router.post(
    "/upload",
    response_model=MediaCmsItemOut,
    status_code=status.HTTP_201_CREATED,
)
async def upload_media_asset(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    asset_type: str = Form("image"),
    rights_owner: str = Form(...),
    license_type: str = Form(...),
    attribution: str = Form(...),
    public_display_allowed: bool = Form(True),
    derivative_allowed: bool = Form(True),
    relic_slug: Optional[str] = Form(None),
    historical_entity_id: Optional[UUID] = Form(None),
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db),
) -> MediaCmsItemOut:
    """Securely upload a museum media asset in draft status."""
    file_bytes = await file.read()
    item = cms_service.create_media_cms_item(
        db,
        file_bytes=file_bytes,
        original_filename=file.filename or "media_upload",
        title=title,
        description=description,
        asset_type=asset_type,
        rights_owner=rights_owner,
        license_type=license_type,
        attribution=attribution,
        public_display_allowed=public_display_allowed,
        derivative_allowed=derivative_allowed,
        historical_entity_id=historical_entity_id,
        relic_slug=relic_slug,
        current_user=current_user,
    )
    return MediaCmsItemOut.model_validate(item)


@router.get(
    "/items",
    response_model=MediaCmsItemListOut,
)
def list_media_items(
    status_filter: Optional[str] = Query(None, alias="status"),
    asset_type: Optional[str] = Query(None),
    relic_slug: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db),
) -> MediaCmsItemListOut:
    """List museum media assets with filter and search criteria."""
    items, total = cms_service.list_media_cms_items(
        db,
        status_filter=status_filter,
        asset_type=asset_type,
        relic_slug=relic_slug,
        search=search,
        limit=limit,
        offset=offset,
    )
    return MediaCmsItemListOut(
        items=[MediaCmsItemOut.model_validate(i) for i in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/items/{item_id}",
    response_model=MediaCmsItemOut,
)
def get_media_item(
    item_id: UUID,
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db),
) -> MediaCmsItemOut:
    """Retrieve details of a single media item."""
    item = cms_service.get_media_cms_item(db, item_id)
    return MediaCmsItemOut.model_validate(item)


@router.patch(
    "/items/{item_id}",
    response_model=MediaCmsItemOut,
)
def update_media_item(
    item_id: UUID,
    payload: MediaCmsItemUpdate,
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db),
) -> MediaCmsItemOut:
    """Update metadata and licensing properties of a media asset."""
    item = cms_service.update_media_cms_item(
        db,
        item_id=item_id,
        payload_data=payload.model_dump(exclude_unset=True),
        current_user=current_user,
    )
    return MediaCmsItemOut.model_validate(item)


@router.post(
    "/items/{item_id}/version",
    response_model=MediaCmsItemOut,
)
async def upload_media_version(
    item_id: UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db),
) -> MediaCmsItemOut:
    """Upload a new binary version for an existing media asset."""
    file_bytes = await file.read()
    item = cms_service.upload_new_version(
        db,
        item_id=item_id,
        file_bytes=file_bytes,
        original_filename=file.filename or "media_version",
        current_user=current_user,
    )
    return MediaCmsItemOut.model_validate(item)


@router.post(
    "/items/{item_id}/submit-review",
    response_model=MediaCmsItemOut,
)
def submit_media_review(
    item_id: UUID,
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db),
) -> MediaCmsItemOut:
    """Submit a draft or rejected media asset for editorial review."""
    item = cms_service.submit_for_review(db, item_id=item_id, current_user=current_user)
    return MediaCmsItemOut.model_validate(item)


@router.post(
    "/items/{item_id}/approve",
    response_model=MediaCmsItemOut,
)
def approve_media(
    item_id: UUID,
    payload: MediaCmsReviewAction = Body(default_factory=MediaCmsReviewAction),
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> MediaCmsItemOut:
    """Approve a media asset in review status (admin/curator only)."""
    item = cms_service.approve_media_item(
        db, item_id=item_id, current_user=current_user, notes=payload.notes
    )
    return MediaCmsItemOut.model_validate(item)


@router.post(
    "/items/{item_id}/reject",
    response_model=MediaCmsItemOut,
)
def reject_media(
    item_id: UUID,
    payload: MediaCmsReviewAction,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> MediaCmsItemOut:
    """Reject a media asset with mandatory review explanation."""
    reason = payload.reason or payload.notes or ""
    item = cms_service.reject_media_item(
        db, item_id=item_id, reason=reason, current_user=current_user
    )
    return MediaCmsItemOut.model_validate(item)


@router.post(
    "/items/{item_id}/publish",
    response_model=MediaCmsItemOut,
)
def publish_media(
    item_id: UUID,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> MediaCmsItemOut:
    """Publish an approved media asset and sync to historical assets catalog."""
    item = cms_service.publish_media_item(
        db, item_id=item_id, current_user=current_user
    )
    return MediaCmsItemOut.model_validate(item)


@router.post(
    "/items/{item_id}/archive",
    response_model=MediaCmsItemOut,
)
def archive_media(
    item_id: UUID,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> MediaCmsItemOut:
    """Archive a media asset (admin only)."""
    item = cms_service.archive_media_item(
        db, item_id=item_id, current_user=current_user
    )
    return MediaCmsItemOut.model_validate(item)


@router.get(
    "/preview/{item_id}",
    response_model=MediaCmsPreviewOut,
)
def preview_media(
    item_id: UUID,
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db),
) -> MediaCmsPreviewOut:
    """Get staged preview configuration and rights summary for operator preview."""
    preview_data = cms_service.build_media_preview(db, item_id=item_id)
    return MediaCmsPreviewOut(
        item=MediaCmsItemOut.model_validate(preview_data["item"]),
        viewer_type=preview_data["viewer_type"],
        viewer_config=preview_data["viewer_config"],
        rights_summary=preview_data["rights_summary"],
        staged_review_summary=preview_data["staged_review_summary"],
    )


@router.delete(
    "/items/{item_id}",
    status_code=status.HTTP_200_OK,
)
def delete_media(
    item_id: UUID,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> dict:
    """Delete a draft or rejected media asset."""
    cms_service.delete_media_item(db, item_id=item_id, current_user=current_user)
    return {"deleted": True, "id": str(item_id)}
