# -*- coding: utf-8 -*-
"""Service layer for Imperial City aerial map assets, annotations, and studio curation (STTT).

Provides domain operations for:
- Active published map asset and annotations
- Querying map annotations with zone and lens filters
- Optimistic locking coordinate updates with audit trail
- Soft-delete / archiving of annotations
- Atomic map publication transactions
- Full dataset annotation export and dry-run import verification
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Optional, Union
from uuid import UUID

from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import Session, selectinload

from ..apischemas.imperial import (
    ImperialAnnotationAuditOut,
    ImperialAnnotationCreate,
    ImperialAnnotationOut,
    ImperialAnnotationUpdate,
    ImperialMapAssetDetail,
    ImperialMapAssetPublish,
    ImperialMapAssetSummary,
    ImperialMapAssetUpload,
    ImperialSiteSummary,
)
from ..errors import AppError
from ..imperial_models import (
    CONTENT_SCOPE_IMPERIAL,
    ImperialAnnotationAudit,
    ImperialAnnotationLink,
    ImperialLensSite,
    ImperialMapAnnotation,
    ImperialMapAsset,
    ImperialSite,
    ImperialZone,
)


def get_active_map(db: Session) -> dict[str, Any]:
    """Retrieve the active published aerial map asset with all published annotations."""
    stmt = (
        select(ImperialMapAsset)
        .where(
            ImperialMapAsset.content_scope == CONTENT_SCOPE_IMPERIAL,
            ImperialMapAsset.is_active == True,
            ImperialMapAsset.review_status == "published",
        )
    )
    active_map = db.execute(stmt).scalar_one_or_none()
    if not active_map:
        raise AppError("IMPERIAL_ACTIVE_MAP_NOT_FOUND", "No active published aerial map found", 404)

    # Fetch published visible annotations for active map
    anno_stmt = (
        select(ImperialMapAnnotation)
        .where(
            ImperialMapAnnotation.map_asset_id == active_map.id,
            ImperialMapAnnotation.review_status == "published",
            ImperialMapAnnotation.is_visible == True,
        )
        .options(
            selectinload(ImperialMapAnnotation.site).selectinload(ImperialSite.zone),
            selectinload(ImperialMapAnnotation.links),
        )
        .order_by(ImperialMapAnnotation.z_index.asc(), ImperialMapAnnotation.created_at.asc())
    )
    annotations = db.execute(anno_stmt).scalars().all()

    image_url = active_map.image_storage_key
    if not image_url.startswith("/") and not image_url.startswith("http"):
        image_url = f"/api/v1/imperial/assets/{active_map.id}/image"

    return {
        "scope": CONTENT_SCOPE_IMPERIAL,
        "map": {
            "id": active_map.id,
            "slug": active_map.slug,
            "version": active_map.version,
            "title_vi": active_map.title_vi,
            "title_en": active_map.title_en,
            "image": {
                "url": image_url,
                "width": active_map.width_px,
                "height": active_map.height_px,
            },
            "credit": active_map.credit_text,
            "license_kind": active_map.license_kind,
            "license_status": active_map.license_status,
            "review_status": active_map.review_status,
            "revision": active_map.row_version,
            "row_version": active_map.row_version,
        },
        "annotations": [
            {
                "id": a.id,
                "site": {
                    "id": a.site.id,
                    "slug": a.site.slug,
                    "name_vi": a.site.name_vi,
                    "zone_slug": a.site.zone.slug if (a.site and a.site.zone) else None,
                    "learning_level": a.site.learning_level if a.site else None,
                    "condition": a.site.condition if a.site else None,
                }
                if a.site
                else None,
                "shape_type": a.shape_type,
                "u": float(a.u),
                "v": float(a.v),
                "polygon_uv": a.polygon_uv,
                "label": a.label or (a.site.name_vi if a.site else None),
                "marker_style": a.marker_style,
                "position_confidence": a.position_confidence,
                "review_status": a.review_status,
                "is_visible": a.is_visible,
                "row_version": a.row_version,
            }
            for a in annotations
        ],
    }


def get_map_annotations(
    db: Session,
    map_id: UUID,
    zone_id: Optional[Union[UUID, str]] = None,
    lens_id: Optional[UUID] = None,
    include_drafts: bool = False,
) -> list[ImperialAnnotationOut]:
    """List map annotations with optional zone/lens filters and draft visibility."""
    map_asset = db.get(ImperialMapAsset, map_id)
    if not map_asset:
        raise AppError("IMPERIAL_MAP_NOT_FOUND", f"Map asset '{map_id}' not found", 404)

    # Public requests can only query published maps
    if not include_drafts and map_asset.review_status != "published":
        raise AppError("IMPERIAL_MAP_NOT_PUBLISHED", "Map asset is not published", 404)

    stmt = (
        select(ImperialMapAnnotation)
        .where(
            ImperialMapAnnotation.map_asset_id == map_id,
            ImperialMapAnnotation.content_scope == CONTENT_SCOPE_IMPERIAL,
        )
        .options(
            selectinload(ImperialMapAnnotation.site),
            selectinload(ImperialMapAnnotation.links),
        )
    )

    if not include_drafts:
        stmt = stmt.where(
            ImperialMapAnnotation.review_status == "published",
            ImperialMapAnnotation.is_visible == True,
        )
    else:
        # Exclude permanently archived unless specifically needed
        stmt = stmt.where(ImperialMapAnnotation.review_status != "archived")

    if zone_id is not None:
        is_uuid = False
        parsed_uuid = None
        if isinstance(zone_id, UUID):
            is_uuid = True
            parsed_uuid = zone_id
        else:
            try:
                parsed_uuid = UUID(str(zone_id))
                is_uuid = True
            except ValueError:
                is_uuid = False

        if is_uuid:
            stmt = stmt.join(ImperialSite, ImperialMapAnnotation.site_id == ImperialSite.id).where(
                ImperialSite.zone_id == parsed_uuid
            )
        else:
            stmt = (
                stmt.join(ImperialSite, ImperialMapAnnotation.site_id == ImperialSite.id)
                .join(ImperialZone, ImperialSite.zone_id == ImperialZone.id)
                .where(ImperialZone.slug == str(zone_id))
            )

    if lens_id is not None:
        stmt = stmt.join(
            ImperialLensSite,
            ImperialMapAnnotation.site_id == ImperialLensSite.site_id,
        ).where(ImperialLensSite.lens_id == lens_id)

    stmt = stmt.order_by(ImperialMapAnnotation.z_index.asc(), ImperialMapAnnotation.created_at.asc())
    annotations = db.execute(stmt).scalars().all()

    return [ImperialAnnotationOut.model_validate(a) for a in annotations]


def create_annotation(
    db: Session,
    map_id: UUID,
    payload: ImperialAnnotationCreate,
    actor_id: UUID,
) -> ImperialAnnotationOut:
    """Create a draft annotation marker with UV bounds validation and audit log."""
    map_asset = db.get(ImperialMapAsset, map_id)
    if not map_asset:
        raise AppError("IMPERIAL_MAP_NOT_FOUND", f"Map asset '{map_id}' not found", 404)

    if map_asset.review_status == "archived":
        raise AppError("IMPERIAL_MAP_ARCHIVED", "Cannot annotate an archived map", 400)

    # Validate normalized UV bounds [0.0, 1.0]
    if not (0.0 <= payload.u <= 1.0 and 0.0 <= payload.v <= 1.0):
        raise AppError("IMPERIAL_UV_OUT_OF_BOUNDS", "UV coordinates must be between 0.0 and 1.0", 422)

    # Check site exists and matches STTT scope
    site = db.get(ImperialSite, payload.site_id)
    if not site or site.content_scope != CONTENT_SCOPE_IMPERIAL:
        raise AppError("IMPERIAL_SITE_NOT_FOUND", "Referenced site not found in STTT scope", 404)

    # Check for existing annotation for this site on this map
    existing_stmt = select(ImperialMapAnnotation).where(
        ImperialMapAnnotation.map_asset_id == map_id,
        ImperialMapAnnotation.site_id == payload.site_id,
        ImperialMapAnnotation.review_status != "archived",
    )
    existing = db.execute(existing_stmt).scalar_one_or_none()
    if existing:
        raise AppError(
            "IMPERIAL_ANNOTATION_EXISTS",
            f"Annotation for site '{site.slug}' already exists on this map",
            409,
        )

    anno = ImperialMapAnnotation(
        content_scope=CONTENT_SCOPE_IMPERIAL,
        map_asset_id=map_id,
        site_id=payload.site_id,
        shape_type=payload.shape_type,
        u=payload.u,
        v=payload.v,
        polygon_uv=payload.polygon_uv,
        label=payload.label or site.name_vi,
        marker_style=payload.marker_style or "monument",
        z_index=payload.z_index,
        is_visible=payload.is_visible,
        review_status="draft",
        position_confidence=payload.position_confidence or "approximate",
        position_source_ref=payload.position_source_ref,
        editorial_notes=payload.editorial_notes,
        created_by=actor_id,
        updated_by=actor_id,
        row_version=1,
    )
    db.add(anno)
    db.flush()

    audit = ImperialAnnotationAudit(
        content_scope=CONTENT_SCOPE_IMPERIAL,
        annotation_id=anno.id,
        actor_id=actor_id,
        action="create",
        before_json=None,
        after_json={
            "id": str(anno.id),
            "map_asset_id": str(map_id),
            "site_id": str(anno.site_id),
            "u": float(anno.u),
            "v": float(anno.v),
            "label": anno.label,
            "marker_style": anno.marker_style,
            "position_confidence": anno.position_confidence,
            "review_status": anno.review_status,
        },
    )
    db.add(audit)
    db.commit()
    db.refresh(anno)

    return ImperialAnnotationOut.model_validate(anno)


def update_annotation(
    db: Session,
    annotation_id: UUID,
    payload: ImperialAnnotationUpdate,
    actor_id: UUID,
) -> ImperialAnnotationOut:
    """Update annotation with optimistic concurrency control and audit history."""
    anno = db.get(ImperialMapAnnotation, annotation_id)
    if not anno or anno.content_scope != CONTENT_SCOPE_IMPERIAL:
        raise AppError("IMPERIAL_ANNOTATION_NOT_FOUND", f"Annotation '{annotation_id}' not found", 404)

    # Optimistic locking concurrency check
    if payload.row_version != anno.row_version:
        raise AppError(
            "IMPERIAL_CONCURRENCY_CONFLICT",
            "Annotation has been modified by another editor. Please reload and compare.",
            409,
            {"current_row_version": anno.row_version, "submitted_row_version": payload.row_version},
        )

    # Validate UV coordinates if modified
    new_u = payload.u if payload.u is not None else float(anno.u)
    new_v = payload.v if payload.v is not None else float(anno.v)
    if not (0.0 <= new_u <= 1.0 and 0.0 <= new_v <= 1.0):
        raise AppError("IMPERIAL_UV_OUT_OF_BOUNDS", "UV coordinates must be between 0.0 and 1.0", 422)

    before_dict = {
        "u": float(anno.u),
        "v": float(anno.v),
        "label": anno.label,
        "marker_style": anno.marker_style,
        "position_confidence": anno.position_confidence,
        "review_status": anno.review_status,
        "is_visible": anno.is_visible,
        "row_version": anno.row_version,
    }

    if payload.u is not None:
        anno.u = payload.u
    if payload.v is not None:
        anno.v = payload.v
    if payload.shape_type is not None:
        anno.shape_type = payload.shape_type
    if payload.polygon_uv is not None:
        anno.polygon_uv = payload.polygon_uv
    if payload.label is not None:
        anno.label = payload.label
    if payload.marker_style is not None:
        anno.marker_style = payload.marker_style
    if payload.z_index is not None:
        anno.z_index = payload.z_index
    if payload.is_visible is not None:
        anno.is_visible = payload.is_visible
    if payload.review_status is not None:
        anno.review_status = payload.review_status
    if payload.position_confidence is not None:
        anno.position_confidence = payload.position_confidence
    if payload.position_source_ref is not None:
        anno.position_source_ref = payload.position_source_ref
    if payload.editorial_notes is not None:
        anno.editorial_notes = payload.editorial_notes

    anno.updated_by = actor_id
    anno.updated_at = datetime.now(timezone.utc)
    anno.row_version += 1

    after_dict = {
        "u": float(anno.u),
        "v": float(anno.v),
        "label": anno.label,
        "marker_style": anno.marker_style,
        "position_confidence": anno.position_confidence,
        "review_status": anno.review_status,
        "is_visible": anno.is_visible,
        "row_version": anno.row_version,
    }

    audit = ImperialAnnotationAudit(
        content_scope=CONTENT_SCOPE_IMPERIAL,
        annotation_id=anno.id,
        actor_id=actor_id,
        action="update",
        before_json=before_dict,
        after_json=after_dict,
    )
    db.add(audit)
    db.commit()
    db.refresh(anno)

    return ImperialAnnotationOut.model_validate(anno)


def delete_annotation(
    db: Session,
    annotation_id: UUID,
    actor_id: UUID,
) -> bool:
    """Soft-delete / archive an annotation with audit trail."""
    anno = db.get(ImperialMapAnnotation, annotation_id)
    if not anno or anno.content_scope != CONTENT_SCOPE_IMPERIAL:
        raise AppError("IMPERIAL_ANNOTATION_NOT_FOUND", f"Annotation '{annotation_id}' not found", 404)

    before_dict = {
        "review_status": anno.review_status,
        "is_visible": anno.is_visible,
        "row_version": anno.row_version,
    }

    anno.review_status = "archived"
    anno.is_visible = False
    anno.updated_by = actor_id
    anno.updated_at = datetime.now(timezone.utc)
    anno.row_version += 1

    after_dict = {
        "review_status": anno.review_status,
        "is_visible": anno.is_visible,
        "row_version": anno.row_version,
    }

    audit = ImperialAnnotationAudit(
        content_scope=CONTENT_SCOPE_IMPERIAL,
        annotation_id=anno.id,
        actor_id=actor_id,
        action="archive",
        before_json=before_dict,
        after_json=after_dict,
    )
    db.add(audit)
    db.commit()
    return True


def publish_map(
    db: Session,
    map_id: UUID,
    actor_id: UUID,
) -> ImperialMapAssetDetail:
    """Publish a map snapshot atomically: validates license, updates active map, publishes annotations."""
    map_asset = db.get(ImperialMapAsset, map_id)
    if not map_asset or map_asset.content_scope != CONTENT_SCOPE_IMPERIAL:
        raise AppError("IMPERIAL_MAP_NOT_FOUND", f"Map asset '{map_id}' not found", 404)

    if map_asset.license_status != "approved":
        raise AppError(
            "IMPERIAL_LICENSE_NOT_APPROVED",
            f"Map asset license is '{map_asset.license_status}'. Must be 'approved' before publication.",
            400,
        )

    now = datetime.now(timezone.utc)

    # 1. Reset existing active maps in STTT scope
    db.execute(
        update(ImperialMapAsset)
        .where(
            ImperialMapAsset.content_scope == CONTENT_SCOPE_IMPERIAL,
            ImperialMapAsset.is_active == True,
            ImperialMapAsset.id != map_id,
        )
        .values(is_active=False)
    )

    # 2. Update map asset
    map_asset.is_active = True
    map_asset.review_status = "published"
    map_asset.published_at = now
    map_asset.approved_by = actor_id
    map_asset.updated_at = now
    map_asset.row_version += 1

    # 3. Publish draft/approved annotations on this map
    db.execute(
        update(ImperialMapAnnotation)
        .where(
            ImperialMapAnnotation.map_asset_id == map_id,
            ImperialMapAnnotation.review_status.in_(["draft", "in_review", "approved"]),
        )
        .values(
            review_status="published",
            published_at=now,
            approved_by=actor_id,
            updated_at=now,
            row_version=ImperialMapAnnotation.row_version + 1,
        )
    )

    db.commit()
    db.refresh(map_asset)
    return ImperialMapAssetDetail.model_validate(map_asset)


def export_annotations(db: Session, map_id: UUID) -> dict[str, Any]:
    """Generate export JSON with schema_version 'imperial-annotations/1.0', content hash, and site mappings."""
    map_asset = db.get(ImperialMapAsset, map_id)
    if not map_asset or map_asset.content_scope != CONTENT_SCOPE_IMPERIAL:
        raise AppError("IMPERIAL_MAP_NOT_FOUND", f"Map asset '{map_id}' not found", 404)

    stmt = (
        select(ImperialMapAnnotation)
        .where(
            ImperialMapAnnotation.map_asset_id == map_id,
            ImperialMapAnnotation.review_status != "archived",
        )
        .options(selectinload(ImperialMapAnnotation.site))
        .order_by(ImperialMapAnnotation.z_index.asc(), ImperialMapAnnotation.created_at.asc())
    )
    annotations = db.execute(stmt).scalars().all()

    export_dict: dict[str, Any] = {
        "schema_version": "imperial-annotations/1.0",
        "content_scope": CONTENT_SCOPE_IMPERIAL,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "map": {
            "id": str(map_asset.id),
            "slug": map_asset.slug,
            "version": map_asset.version,
            "image_sha256": map_asset.image_sha256,
        },
        "annotations": [
            {
                "id": str(a.id),
                "site_slug": a.site.slug if a.site else None,
                "site_name_vi": a.site.name_vi if a.site else None,
                "shape_type": a.shape_type,
                "u": float(a.u),
                "v": float(a.v),
                "polygon_uv": a.polygon_uv,
                "label": a.label,
                "marker_style": a.marker_style,
                "position_confidence": a.position_confidence,
                "position_source_ref": a.position_source_ref,
                "is_visible": a.is_visible,
                "review_status": a.review_status,
            }
            for a in annotations
        ],
    }

    canonical = json.dumps(
        {k: v for k, v in export_dict.items() if k != "export_sha256"},
        sort_keys=True,
        default=str,
    )
    export_dict["export_sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return export_dict


def import_annotations(
    db: Session,
    map_id: UUID,
    payload: dict[str, Any],
    actor_id: UUID,
    dry_run: bool = True,
) -> dict[str, Any]:
    """Validate schema, verify site mappings and UV bounds, compute diff, and atomically import annotations."""
    map_asset = db.get(ImperialMapAsset, map_id)
    if not map_asset or map_asset.content_scope != CONTENT_SCOPE_IMPERIAL:
        raise AppError("IMPERIAL_MAP_NOT_FOUND", f"Map asset '{map_id}' not found", 404)

    # 1. Validate scope and schema version
    scope = payload.get("content_scope") or payload.get("scope")
    if scope != CONTENT_SCOPE_IMPERIAL:
        raise AppError(
            "IMPERIAL_INVALID_SCOPE",
            f"Expected content_scope '{CONTENT_SCOPE_IMPERIAL}', got '{scope}'",
            422,
        )

    schema_version = str(payload.get("schema_version", ""))
    if not (schema_version == "imperial-annotations/1.0" or schema_version.startswith("1.")):
        raise AppError(
            "IMPERIAL_INVALID_SCHEMA_VERSION",
            f"Unsupported schema_version '{schema_version}'. Expected 'imperial-annotations/1.0' or '1.0.0'.",
            422,
        )

    # 2. Pre-fetch sites in STTT scope
    all_sites = db.execute(
        select(ImperialSite).where(ImperialSite.content_scope == CONTENT_SCOPE_IMPERIAL)
    ).scalars().all()
    sites_by_slug = {s.slug: s for s in all_sites}
    sites_by_id = {str(s.id): s for s in all_sites}

    # 3. Pre-fetch existing annotations for this map
    existing_annos = {
        a.site_id: a
        for a in db.execute(
            select(ImperialMapAnnotation).where(
                ImperialMapAnnotation.map_asset_id == map_id,
                ImperialMapAnnotation.review_status != "archived",
            )
        ).scalars().all()
    }

    raw_items = payload.get("annotations", [])
    new_items: list[dict[str, Any]] = []
    updated_items: list[dict[str, Any]] = []
    invalid_items: list[dict[str, Any]] = []

    for i, item in enumerate(raw_items):
        site_slug = item.get("site_slug")
        site_id_raw = item.get("site_id")

        site = None
        if site_slug and site_slug in sites_by_slug:
            site = sites_by_slug[site_slug]
        elif site_id_raw and str(site_id_raw) in sites_by_id:
            site = sites_by_id[str(site_id_raw)]

        if not site:
            invalid_items.append({
                "index": i,
                "data": item,
                "reason": f"Site with slug '{site_slug}' / id '{site_id_raw}' not found in STTT scope",
            })
            continue

        u, v = item.get("u"), item.get("v")
        if u is None or v is None:
            invalid_items.append({"index": i, "data": item, "reason": "Missing u or v coordinate"})
            continue

        try:
            u_float = float(u)
            v_float = float(v)
        except (ValueError, TypeError):
            invalid_items.append({"index": i, "data": item, "reason": "Invalid non-numeric UV coordinate"})
            continue

        if not (0.0 <= u_float <= 1.0 and 0.0 <= v_float <= 1.0):
            invalid_items.append({
                "index": i,
                "data": item,
                "reason": f"Coordinates ({u_float}, {v_float}) outside normalized range [0.0, 1.0]",
            })
            continue

        existing = existing_annos.get(site.id)
        if existing:
            updated_items.append({
                "annotation_id": str(existing.id),
                "site_id": str(site.id),
                "site_slug": site.slug,
                "u": u_float,
                "v": v_float,
                "label": item.get("label") or site.name_vi,
                "marker_style": item.get("marker_style", existing.marker_style),
                "position_confidence": item.get("position_confidence", existing.position_confidence),
            })
        else:
            new_items.append({
                "site_id": str(site.id),
                "site_slug": site.slug,
                "u": u_float,
                "v": v_float,
                "shape_type": item.get("shape_type", "point"),
                "label": item.get("label") or site.name_vi,
                "marker_style": item.get("marker_style", "monument"),
                "position_confidence": item.get("position_confidence", "approximate"),
            })

    if dry_run:
        return {
            "dry_run": True,
            "valid": len(invalid_items) == 0,
            "summary": {
                "total": len(raw_items),
                "new_count": len(new_items),
                "updated_count": len(updated_items),
                "invalid_count": len(invalid_items),
            },
            "diff": {
                "new": new_items,
                "updated": updated_items,
                "invalid": invalid_items,
            },
        }

    # Execute all-or-nothing transaction
    if invalid_items:
        raise AppError(
            "IMPERIAL_IMPORT_ERROR",
            f"Cannot import: {len(invalid_items)} item(s) failed validation.",
            422,
            {"invalid": invalid_items},
        )

    now = datetime.now(timezone.utc)

    # 1. Insert new items
    for item in new_items:
        s_id = UUID(item["site_id"])
        anno = ImperialMapAnnotation(
            content_scope=CONTENT_SCOPE_IMPERIAL,
            map_asset_id=map_id,
            site_id=s_id,
            shape_type=item["shape_type"],
            u=item["u"],
            v=item["v"],
            label=item["label"],
            marker_style=item["marker_style"],
            position_confidence=item["position_confidence"],
            review_status="draft",
            is_visible=True,
            created_by=actor_id,
            updated_by=actor_id,
            row_version=1,
        )
        db.add(anno)
        db.flush()

        db.add(
            ImperialAnnotationAudit(
                content_scope=CONTENT_SCOPE_IMPERIAL,
                annotation_id=anno.id,
                actor_id=actor_id,
                action="import_create",
                before_json=None,
                after_json={
                    "u": item["u"],
                    "v": item["v"],
                    "label": item["label"],
                    "site_slug": item["site_slug"],
                },
            )
        )

    # 2. Update existing items
    for item in updated_items:
        a_id = UUID(item["annotation_id"])
        existing = db.get(ImperialMapAnnotation, a_id)
        if existing:
            before_dict = {
                "u": float(existing.u),
                "v": float(existing.v),
                "label": existing.label,
                "row_version": existing.row_version,
            }
            existing.u = item["u"]
            existing.v = item["v"]
            existing.label = item["label"]
            existing.marker_style = item["marker_style"]
            existing.position_confidence = item["position_confidence"]
            existing.updated_by = actor_id
            existing.updated_at = now
            existing.row_version += 1

            db.add(
                ImperialAnnotationAudit(
                    content_scope=CONTENT_SCOPE_IMPERIAL,
                    annotation_id=existing.id,
                    actor_id=actor_id,
                    action="import_update",
                    before_json=before_dict,
                    after_json={
                        "u": item["u"],
                        "v": item["v"],
                        "label": item["label"],
                        "row_version": existing.row_version,
                    },
                )
            )

    db.commit()
    return {
        "dry_run": False,
        "status": "success",
        "created_count": len(new_items),
        "updated_count": len(updated_items),
    }


def get_annotation_audit(db: Session, annotation_id: UUID) -> list[ImperialAnnotationAuditOut]:
    """Retrieve full append-only audit trail for an annotation."""
    anno = db.get(ImperialMapAnnotation, annotation_id)
    if not anno or anno.content_scope != CONTENT_SCOPE_IMPERIAL:
        raise AppError("IMPERIAL_ANNOTATION_NOT_FOUND", f"Annotation '{annotation_id}' not found", 404)

    stmt = (
        select(ImperialAnnotationAudit)
        .where(
            ImperialAnnotationAudit.annotation_id == annotation_id,
            ImperialAnnotationAudit.content_scope == CONTENT_SCOPE_IMPERIAL,
        )
        .order_by(ImperialAnnotationAudit.created_at.desc())
    )
    audits = db.execute(stmt).scalars().all()
    return [ImperialAnnotationAuditOut.model_validate(a) for a in audits]


def list_maps(db: Session) -> list[ImperialMapAssetSummary]:
    """List all aerial map asset versions for admin curation."""
    stmt = (
        select(ImperialMapAsset)
        .where(ImperialMapAsset.content_scope == CONTENT_SCOPE_IMPERIAL)
        .order_by(ImperialMapAsset.version.desc(), ImperialMapAsset.created_at.desc())
    )
    maps = db.execute(stmt).scalars().all()
    return [ImperialMapAssetSummary.model_validate(m) for m in maps]


def create_map_asset(
    db: Session,
    payload: ImperialMapAssetUpload,
    actor_id: UUID,
) -> ImperialMapAssetDetail:
    """Create metadata record for a newly uploaded aerial map asset."""
    # Check uniqueness of (content_scope, slug, version)
    stmt = select(ImperialMapAsset).where(
        ImperialMapAsset.content_scope == CONTENT_SCOPE_IMPERIAL,
        ImperialMapAsset.slug == payload.slug,
        ImperialMapAsset.version == payload.version,
    )
    existing = db.execute(stmt).scalar_one_or_none()
    if existing:
        raise AppError(
            "IMPERIAL_MAP_VERSION_EXISTS",
            f"Map asset '{payload.slug}' version {payload.version} already exists",
            409,
        )

    map_asset = ImperialMapAsset(
        content_scope=CONTENT_SCOPE_IMPERIAL,
        title_vi=payload.title_vi,
        title_en=payload.title_en,
        slug=payload.slug,
        version=payload.version,
        image_storage_key=payload.image_storage_key,
        preview_storage_key=payload.preview_storage_key,
        image_sha256=payload.image_sha256,
        mime_type=payload.mime_type,
        width_px=payload.width_px,
        height_px=payload.height_px,
        source_title=payload.source_title,
        source_locator=payload.source_locator,
        copyright_holder=payload.copyright_holder,
        credit_text=payload.credit_text,
        license_kind=payload.license_kind,
        license_evidence_key=payload.license_evidence_key,
        license_status="pending",
        review_status="draft",
        is_active=False,
        created_by=actor_id,
        row_version=1,
    )
    db.add(map_asset)
    db.commit()
    db.refresh(map_asset)
    return ImperialMapAssetDetail.model_validate(map_asset)
