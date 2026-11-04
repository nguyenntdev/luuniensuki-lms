# -*- coding: utf-8 -*-
"""Museum Operator Media CMS Service (V5-T050 / W04-A10).

Enforces:
1. Strict File & Format Validation:
   - Whitelist: GLB (3D mesh), PNG, JPEG, WEBP.
   - Magic bytes sniffing and anti-abuse validation.
   - Rejection of executable, script, and disguised files (.exe, .sh, .php, .html, etc.).
   - Strict file size constraints (50MB for 3D meshes, 10MB for images).
2. Licensing & Rights Metadata Verification:
   - Required rights owner, valid approved license type, creator attribution.
   - Rejection of unlicensed or unauthorized rights declarations.
3. Staged Publication Approval Workflow:
   - State lifecycle: draft -> in_review -> approved -> published.
   - Prevents illegal skips (draft -> published is strictly blocked).
   - Version revisioning: new file upload resets publication state to require re-approval.
   - Rejection flow requires non-empty reason.
4. Historical Asset Integration & Audit:
   - Publication synchronizes to persistent HistoricalAsset table.
   - Comprehensive audit logging via historical_content_audit_log.
"""
from __future__ import annotations

import hashlib
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import desc, func, or_, select
from sqlalchemy.orm import Session

from ..errors import AppError
from ..models import (
    HistoricalAsset,
    MediaCmsItem,
    MediaCmsStatus,
    User,
    UserRole,
)
from ..services import history_governance as gov

REPO_ROOT = Path(__file__).resolve().parents[2]
MEDIA_UPLOAD_DIR = REPO_ROOT / "public" / "uploads" / "media-cms"

# Magic byte signatures
GLB_MAGIC = b"glTF"
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
JPEG_MAGIC = b"\xff\xd8\xff"
RIFF_MAGIC = b"RIFF"
WEBP_SUB_MAGIC = b"WEBP"

ALLOWED_FORMATS = {
    ".glb": ("glb", "model/gltf-binary"),
    ".png": ("png", "image/png"),
    ".jpg": ("jpeg", "image/jpeg"),
    ".jpeg": ("jpeg", "image/jpeg"),
    ".webp": ("webp", "image/webp"),
}

FORBIDDEN_EXTENSIONS = {
    ".exe", ".sh", ".php", ".html", ".htm", ".js", ".py", ".bat",
    ".cmd", ".msi", ".dll", ".so", ".cgi", ".pl", ".jar", ".jsp",
    ".bin", ".elf", ".vbs", ".ps1", ".com", ".scr", ".phtml", ".phar",
}

APPROVED_LICENSES = {
    "CC BY 4.0",
    "CC BY 4.0 / Educational Fair Use",
    "CC-BY-4.0",
    "CC BY",
    "CC BY-SA 4.0",
    "CC BY-NC 4.0",
    "CC BY-NC-ND 4.0",
    "CC0 1.0",
    "CC0",
    "Public Domain",
    "Educational Fair Use",
    "Museum Partner License",
    "Custom Grant",
}

UNAUTHORIZED_OR_RESTRICTED_LICENSES = {
    "unlicensed",
    "none",
    "copyrighted_unauthorized",
    "revoked",
    "pirated",
    "restricted_no_display",
}

MAX_MESH_BYTES = 50 * 1024 * 1024   # 50 MB
MAX_IMAGE_BYTES = 10 * 1024 * 1024  # 10 MB


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal and shell injection."""
    cleaned = Path(filename).name
    cleaned = re.sub(r"[^\w\.\-]", "_", cleaned)
    return cleaned or "unnamed_media"


def validate_file_content(
    file_bytes: bytes,
    original_filename: str,
    declared_content_type: Optional[str] = None,
) -> tuple[str, str, str, int]:
    """Validate upload content, size, magic bytes, and compute SHA-256.

    Returns:
        tuple[file_format, mime_type, sha256_hex, file_size]
    """
    if not file_bytes:
        raise AppError(
            code="EMPTY_FILE",
            message="Uploaded file is empty",
            status_code=400,
        )

    # 1. Filename & Extension inspection
    ext = Path(original_filename).suffix.lower()
    if ext in FORBIDDEN_EXTENSIONS:
        raise AppError(
            code="FORBIDDEN_FILE_TYPE",
            message=f"Executable and script files are strictly prohibited ({ext})",
            status_code=400,
            details={"extension": ext},
        )

    if ext not in ALLOWED_FORMATS:
        raise AppError(
            code="INVALID_FILE_TYPE",
            message=f"Unsupported file format '{ext}'. Allowed formats: .glb, .png, .jpg, .jpeg, .webp",
            status_code=400,
            details={"allowed": list(ALLOWED_FORMATS.keys())},
        )

    file_format, canonical_mime = ALLOWED_FORMATS[ext]
    file_size = len(file_bytes)

    # 2. Size constraints
    max_size = MAX_MESH_BYTES if file_format == "glb" else MAX_IMAGE_BYTES
    if file_size > max_size:
        raise AppError(
            code="FILE_TOO_LARGE",
            message=f"File exceeds maximum allowed size ({max_size // (1024 * 1024)}MB)",
            status_code=400,
            details={"size_bytes": file_size, "max_bytes": max_size},
        )

    # 3. Executable header and script injection check
    header = file_bytes[:16]
    if header.startswith(b"MZ") or header.startswith(b"\x7fELF") or header.startswith(b"#!"):
        raise AppError(
            code="MALICIOUS_CONTENT_DETECTED",
            message="Executable binary signature detected in upload",
            status_code=400,
        )

    first_chunk = file_bytes[:2048].lower()
    if b"<?php" in first_chunk or b"<html" in first_chunk or b"<script" in first_chunk:
        raise AppError(
            code="MALICIOUS_CONTENT_DETECTED",
            message="Embedded script or HTML detected in media upload",
            status_code=400,
        )

    # 4. Strict Magic Byte Verification
    if file_format == "glb":
        if not file_bytes.startswith(GLB_MAGIC):
            raise AppError(
                code="INVALID_GLB_FORMAT",
                message="File content does not match binary glTF (GLB) magic bytes",
                status_code=400,
            )
    elif file_format == "png":
        if not file_bytes.startswith(PNG_MAGIC):
            raise AppError(
                code="INVALID_PNG_FORMAT",
                message="File content does not match PNG magic bytes",
                status_code=400,
            )
    elif file_format == "jpeg":
        if not file_bytes.startswith(JPEG_MAGIC):
            raise AppError(
                code="INVALID_JPEG_FORMAT",
                message="File content does not match JPEG magic bytes",
                status_code=400,
            )
    elif file_format == "webp":
        if not (file_bytes.startswith(RIFF_MAGIC) and file_bytes[8:12] == WEBP_SUB_MAGIC):
            raise AppError(
                code="INVALID_WEBP_FORMAT",
                message="File content does not match WEBP magic bytes",
                status_code=400,
            )

    sha256 = hashlib.sha256(file_bytes).hexdigest()
    return file_format, canonical_mime, sha256, file_size


def validate_licensing_metadata(
    rights_owner: str,
    license_type: str,
    attribution: str,
) -> None:
    """Validate licensing metadata completeness and authorization."""
    if not rights_owner or not rights_owner.strip():
        raise AppError(
            code="MISSING_RIGHTS_OWNER",
            message="Rights owner is mandatory for museum media records",
            status_code=422,
        )

    if not license_type or not license_type.strip():
        raise AppError(
            code="MISSING_LICENSE",
            message="License type is mandatory",
            status_code=422,
        )

    norm_license = license_type.strip().lower()
    if norm_license in UNAUTHORIZED_OR_RESTRICTED_LICENSES:
        raise AppError(
            code="INVALID_LICENSE",
            message=f"License '{license_type}' is restricted or unauthorized for museum educational distribution",
            status_code=422,
            details={"license_type": license_type},
        )

    valid_match = False
    for app_lic in APPROVED_LICENSES:
        if app_lic.lower() == norm_license:
            valid_match = True
            break

    if not valid_match:
        raise AppError(
            code="UNAPPROVED_LICENSE",
            message=f"License '{license_type}' is not recognized in museum approved licenses registry",
            status_code=422,
            details={"approved_licenses": sorted(list(APPROVED_LICENSES))},
        )

    if not attribution or not attribution.strip():
        raise AppError(
            code="MISSING_ATTRIBUTION",
            message="Creator attribution is mandatory",
            status_code=422,
        )


def persist_file_to_storage(file_bytes: bytes, filename: str, sha256: str) -> str:
    """Save upload to media storage directory and return public URL."""
    MEDIA_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = sanitize_filename(filename)
    stored_name = f"{sha256[:12]}_{safe_name}"
    target_path = MEDIA_UPLOAD_DIR / stored_name
    with target_path.open("wb") as f:
        f.write(file_bytes)
    return f"/public/uploads/media-cms/{stored_name}"


def create_media_cms_item(
    db: Session,
    *,
    file_bytes: bytes,
    original_filename: str,
    title: str,
    description: Optional[str],
    asset_type: str,
    rights_owner: str,
    license_type: str,
    attribution: str,
    public_display_allowed: bool = True,
    derivative_allowed: bool = True,
    historical_entity_id: Optional[UUID] = None,
    relic_slug: Optional[str] = None,
    current_user: User,
) -> MediaCmsItem:
    """Create a new media CMS item in draft status."""
    if not title or not title.strip():
        raise AppError(
            code="MISSING_TITLE",
            message="Media item title is mandatory",
            status_code=422,
        )

    validate_licensing_metadata(rights_owner, license_type, attribution)
    file_format, mime_type, sha256, file_size = validate_file_content(
        file_bytes, original_filename
    )

    storage_url = persist_file_to_storage(file_bytes, original_filename, sha256)
    thumbnail_url = storage_url if file_format != "glb" else None

    item = MediaCmsItem(
        title=title.strip(),
        description=description.strip() if description else None,
        asset_type=asset_type or ("model3d" if file_format == "glb" else "image"),
        file_format=file_format,
        mime_type=mime_type,
        storage_url=storage_url,
        thumbnail_url=thumbnail_url,
        file_size_bytes=file_size,
        sha256=sha256,
        rights_owner=rights_owner.strip(),
        license_type=license_type.strip(),
        attribution=attribution.strip(),
        public_display_allowed=public_display_allowed,
        derivative_allowed=derivative_allowed,
        historical_entity_id=historical_entity_id,
        relic_slug=relic_slug.strip().lower() if relic_slug else None,
        publication_status=MediaCmsStatus.draft.value,
        version=1,
        uploaded_by_id=current_user.id,
    )
    db.add(item)
    db.flush()

    gov.audit_action(
        db,
        actor_id=current_user.id,
        action="media_cms_upload",
        resource_type="media_cms_item",
        resource_id=item.id,
        after_json={
            "title": item.title,
            "file_format": item.file_format,
            "sha256": item.sha256,
            "rights_owner": item.rights_owner,
            "license_type": item.license_type,
            "publication_status": item.publication_status,
            "version": item.version,
        },
    )
    db.commit()
    db.refresh(item)
    return item


def list_media_cms_items(
    db: Session,
    *,
    status_filter: Optional[str] = None,
    asset_type: Optional[str] = None,
    relic_slug: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[MediaCmsItem], int]:
    """List media items with filters and pagination."""
    q = select(MediaCmsItem)
    if status_filter:
        q = q.where(MediaCmsItem.publication_status == status_filter)
    if asset_type:
        q = q.where(MediaCmsItem.asset_type == asset_type)
    if relic_slug:
        q = q.where(MediaCmsItem.relic_slug == relic_slug.lower())
    if search:
        s = f"%{search.strip()}%"
        q = q.where(
            or_(
                MediaCmsItem.title.ilike(s),
                MediaCmsItem.rights_owner.ilike(s),
                MediaCmsItem.attribution.ilike(s),
            )
        )

    count_q = select(func.count()).select_from(q.subquery())
    total = db.scalar(count_q) or 0

    items_q = q.order_by(desc(MediaCmsItem.created_at)).offset(offset).limit(limit)
    items = list(db.scalars(items_q).all())
    return items, total


def get_media_cms_item(db: Session, item_id: UUID) -> MediaCmsItem:
    """Retrieve media item by ID or raise 404."""
    item = db.get(MediaCmsItem, item_id)
    if not item:
        raise AppError(
            code="MEDIA_ITEM_NOT_FOUND",
            message=f"Media CMS item '{item_id}' not found",
            status_code=404,
        )
    return item


def update_media_cms_item(
    db: Session,
    item_id: UUID,
    payload_data: dict[str, Any],
    current_user: User,
) -> MediaCmsItem:
    """Update metadata of a media CMS item."""
    item = get_media_cms_item(db, item_id)
    before_json = {
        "title": item.title,
        "rights_owner": item.rights_owner,
        "license_type": item.license_type,
        "attribution": item.attribution,
        "public_display_allowed": item.public_display_allowed,
        "publication_status": item.publication_status,
    }

    # If updating rights fields, validate them
    new_owner = payload_data.get("rights_owner", item.rights_owner)
    new_license = payload_data.get("license_type", item.license_type)
    new_attribution = payload_data.get("attribution", item.attribution)
    validate_licensing_metadata(new_owner, new_license, new_attribution)

    for field, val in payload_data.items():
        if val is not None and hasattr(item, field):
            setattr(item, field, val)

    # Staged governance: If item was published and metadata is modified,
    # reset to in_review so changes undergo editorial review
    if item.publication_status == MediaCmsStatus.published.value:
        item.publication_status = MediaCmsStatus.in_review.value
        item.review_notes = "Metadata modified after publication; pending re-approval."

    item.updated_at = datetime.now(timezone.utc)
    db.flush()

    gov.audit_action(
        db,
        actor_id=current_user.id,
        action="media_cms_update",
        resource_type="media_cms_item",
        resource_id=item.id,
        before_json=before_json,
        after_json={
            "title": item.title,
            "rights_owner": item.rights_owner,
            "license_type": item.license_type,
            "attribution": item.attribution,
            "public_display_allowed": item.public_display_allowed,
            "publication_status": item.publication_status,
        },
    )
    db.commit()
    db.refresh(item)
    return item


def upload_new_version(
    db: Session,
    item_id: UUID,
    file_bytes: bytes,
    original_filename: str,
    current_user: User,
) -> MediaCmsItem:
    """Upload a replacement version for an existing media item."""
    item = get_media_cms_item(db, item_id)
    file_format, mime_type, sha256, file_size = validate_file_content(
        file_bytes, original_filename
    )

    before_version = item.version
    before_status = item.publication_status

    storage_url = persist_file_to_storage(file_bytes, original_filename, sha256)
    item.storage_url = storage_url
    item.file_format = file_format
    item.mime_type = mime_type
    item.file_size_bytes = file_size
    item.sha256 = sha256
    if file_format != "glb":
        item.thumbnail_url = storage_url
    item.version += 1

    # New binary payload resets publication status to draft for staged review
    item.publication_status = MediaCmsStatus.draft.value
    item.review_notes = f"Version {item.version} uploaded; awaiting operator review."
    item.updated_at = datetime.now(timezone.utc)
    db.flush()

    gov.audit_action(
        db,
        actor_id=current_user.id,
        action="media_cms_version_bump",
        resource_type="media_cms_item",
        resource_id=item.id,
        before_json={"version": before_version, "status": before_status},
        after_json={"version": item.version, "status": item.publication_status, "sha256": item.sha256},
    )
    db.commit()
    db.refresh(item)
    return item


def submit_for_review(db: Session, item_id: UUID, current_user: User) -> MediaCmsItem:
    """Transition media item from draft/rejected to in_review."""
    item = get_media_cms_item(db, item_id)
    if item.publication_status not in (MediaCmsStatus.draft.value, MediaCmsStatus.rejected.value):
        raise AppError(
            code="INVALID_STATE_TRANSITION",
            message=f"Cannot submit item in status '{item.publication_status}' for review. Expected draft or rejected.",
            status_code=400,
        )

    validate_licensing_metadata(item.rights_owner, item.license_type, item.attribution)

    before_status = item.publication_status
    item.publication_status = MediaCmsStatus.in_review.value
    item.review_notes = None
    item.updated_at = datetime.now(timezone.utc)
    db.flush()

    gov.audit_action(
        db,
        actor_id=current_user.id,
        action="media_cms_submit_review",
        resource_type="media_cms_item",
        resource_id=item.id,
        before_json={"status": before_status},
        after_json={"status": item.publication_status},
    )
    db.commit()
    db.refresh(item)
    return item


def approve_media_item(
    db: Session,
    item_id: UUID,
    current_user: User,
    notes: Optional[str] = None,
) -> MediaCmsItem:
    """Transition media item from in_review to approved."""
    item = get_media_cms_item(db, item_id)
    if item.publication_status != MediaCmsStatus.in_review.value:
        raise AppError(
            code="INVALID_STATE_TRANSITION",
            message=f"Item must be in 'in_review' status before approval (current: '{item.publication_status}').",
            status_code=400,
        )

    before_status = item.publication_status
    item.publication_status = MediaCmsStatus.approved.value
    item.reviewed_by_id = current_user.id
    item.reviewed_at = datetime.now(timezone.utc)
    item.review_notes = notes.strip() if notes else "Approved by museum curator."
    item.updated_at = datetime.now(timezone.utc)
    db.flush()

    gov.audit_action(
        db,
        actor_id=current_user.id,
        action="media_cms_approve",
        resource_type="media_cms_item",
        resource_id=item.id,
        before_json={"status": before_status},
        after_json={"status": item.publication_status, "notes": item.review_notes},
    )
    db.commit()
    db.refresh(item)
    return item


def reject_media_item(
    db: Session,
    item_id: UUID,
    reason: str,
    current_user: User,
) -> MediaCmsItem:
    """Transition media item from in_review to rejected with mandatory reason."""
    if not reason or not reason.strip():
        raise AppError(
            code="REJECTION_REASON_REQUIRED",
            message="Rejection reason is mandatory when rejecting a media CMS asset",
            status_code=422,
        )

    item = get_media_cms_item(db, item_id)
    if item.publication_status != MediaCmsStatus.in_review.value:
        raise AppError(
            code="INVALID_STATE_TRANSITION",
            message=f"Cannot reject item in status '{item.publication_status}'. Expected 'in_review'.",
            status_code=400,
        )

    before_status = item.publication_status
    item.publication_status = MediaCmsStatus.rejected.value
    item.reviewed_by_id = current_user.id
    item.reviewed_at = datetime.now(timezone.utc)
    item.review_notes = reason.strip()
    item.updated_at = datetime.now(timezone.utc)
    db.flush()

    gov.audit_action(
        db,
        actor_id=current_user.id,
        action="media_cms_reject",
        resource_type="media_cms_item",
        resource_id=item.id,
        before_json={"status": before_status},
        after_json={"status": item.publication_status, "reason": item.review_notes},
        reason=item.review_notes,
    )
    db.commit()
    db.refresh(item)
    return item


def publish_media_item(
    db: Session,
    item_id: UUID,
    current_user: User,
) -> MediaCmsItem:
    """Stage publication approval: transition from approved to published.

    Invariants:
    1. Direct publication from draft or in_review is strictly blocked.
    2. public_display_allowed must be True.
    3. Synchronizes record to HistoricalAsset table.
    """
    item = get_media_cms_item(db, item_id)

    # 1. Staged approval invariant
    if item.publication_status != MediaCmsStatus.approved.value:
        raise AppError(
            code="STAGED_APPROVAL_REQUIRED",
            message=f"Direct publication of unapproved media is forbidden. Item is '{item.publication_status}' and must be 'approved' first.",
            status_code=400,
            details={"current_status": item.publication_status, "required_status": "approved"},
        )

    # 2. Public display rights invariant
    if not item.public_display_allowed:
        raise AppError(
            code="PUBLIC_DISPLAY_NOT_ALLOWED",
            message="Cannot publish media asset when public display is disallowed by licensing terms",
            status_code=400,
        )

    before_status = item.publication_status
    item.publication_status = MediaCmsStatus.published.value
    item.updated_at = datetime.now(timezone.utc)
    db.flush()

    # 3. Synchronize to HistoricalAsset table
    h_asset = db.query(HistoricalAsset).filter(HistoricalAsset.storage_url == item.storage_url).first()
    if not h_asset:
        h_asset = HistoricalAsset(
            asset_type="3d_model" if item.file_format == "glb" else "image",
            storage_url=item.storage_url,
            thumbnail_url=item.thumbnail_url,
            mime_type=item.mime_type,
            byte_size=item.file_size_bytes,
            sha256=item.sha256,
            rights_status="cleared",
            license=item.license_type,
            attribution=item.attribution,
            source_origin=item.rights_owner,
            public_display_allowed=item.public_display_allowed,
            derivative_allowed=item.derivative_allowed,
            entity_id=item.historical_entity_id,
        )
        db.add(h_asset)
        db.flush()
    else:
        h_asset.rights_status = "cleared"
        h_asset.license = item.license_type
        h_asset.attribution = item.attribution
        h_asset.source_origin = item.rights_owner
        h_asset.public_display_allowed = item.public_display_allowed
        h_asset.derivative_allowed = item.derivative_allowed
        db.flush()

    # 4. Audit
    gov.audit_action(
        db,
        actor_id=current_user.id,
        action="media_cms_publish",
        resource_type="media_cms_item",
        resource_id=item.id,
        before_json={"status": before_status},
        after_json={
            "status": item.publication_status,
            "historical_asset_id": str(h_asset.id) if h_asset else None,
        },
    )
    db.commit()
    db.refresh(item)
    return item


def archive_media_item(
    db: Session,
    item_id: UUID,
    current_user: User,
) -> MediaCmsItem:
    """Archive a media item."""
    item = get_media_cms_item(db, item_id)
    before_status = item.publication_status
    item.publication_status = MediaCmsStatus.archived.value
    item.updated_at = datetime.now(timezone.utc)
    db.flush()

    # Update corresponding HistoricalAsset if any
    h_asset = db.query(HistoricalAsset).filter(HistoricalAsset.storage_url == item.storage_url).first()
    if h_asset:
        h_asset.rights_status = "restricted"
        h_asset.public_display_allowed = False
        db.flush()

    gov.audit_action(
        db,
        actor_id=current_user.id,
        action="media_cms_archive",
        resource_type="media_cms_item",
        resource_id=item.id,
        before_json={"status": before_status},
        after_json={"status": item.publication_status},
    )
    db.commit()
    db.refresh(item)
    return item


def delete_media_item(
    db: Session,
    item_id: UUID,
    current_user: User,
) -> None:
    """Delete a draft or rejected media item."""
    item = get_media_cms_item(db, item_id)
    if item.publication_status not in (MediaCmsStatus.draft.value, MediaCmsStatus.rejected.value):
        raise AppError(
            code="CANNOT_DELETE_ACTIVE_MEDIA",
            message=f"Cannot delete media item in status '{item.publication_status}'. Only draft or rejected items may be deleted.",
            status_code=400,
        )

    gov.audit_action(
        db,
        actor_id=current_user.id,
        action="media_cms_delete",
        resource_type="media_cms_item",
        resource_id=item.id,
        before_json={"title": item.title, "storage_url": item.storage_url},
    )
    db.delete(item)
    db.commit()


def build_media_preview(db: Session, item_id: UUID) -> dict[str, Any]:
    """Generate preview data for museum operator viewer."""
    item = get_media_cms_item(db, item_id)

    viewer_type = "mesh_3d" if item.file_format == "glb" else "image_2d"
    viewer_config = {
        "url": item.storage_url,
        "format": item.file_format,
        "mime_type": item.mime_type,
        "sha256": item.sha256,
        "size_bytes": item.file_size_bytes,
        "thumbnail_url": item.thumbnail_url or item.storage_url,
        "fallback_2d": (
            item.thumbnail_url or "/assets/ban-duc-noi/CAO%20DINH/CAO%20%C4%90%E1%BB%88NH.jpg"
            if item.file_format == "glb" else None
        ),
    }

    rights_summary = {
        "rights_owner": item.rights_owner,
        "license_type": item.license_type,
        "attribution": item.attribution,
        "public_display_allowed": item.public_display_allowed,
        "derivative_allowed": item.derivative_allowed,
        "is_cleared": bool(item.publication_status == MediaCmsStatus.published.value and item.public_display_allowed),
    }

    staged_review_summary = {
        "current_stage": item.publication_status,
        "version": item.version,
        "can_publish": bool(item.publication_status == MediaCmsStatus.approved.value and item.public_display_allowed),
        "review_notes": item.review_notes,
        "reviewed_at": item.reviewed_at.isoformat() if item.reviewed_at else None,
    }

    return {
        "item": item,
        "viewer_type": viewer_type,
        "viewer_config": viewer_config,
        "rights_summary": rights_summary,
        "staged_review_summary": staged_review_summary,
    }
