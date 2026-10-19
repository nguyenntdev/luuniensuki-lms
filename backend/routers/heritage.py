# -*- coding: utf-8 -*-
"""Heritage Knowledge Catalogue API Router (LƯU NIÊN — RBPC 2026).

Public and protected endpoints under ``/api/v1/heritage/*``:
- Browse and filter heritage places with deterministic keyset cursor pagination.
- Retrieve detailed place dossier with relationships, bibliographic sources, and media assets.
- Rights-cleared media and 3D Sketchfab embeds (sorted by confidence, blocking SF-020).
- Diacritic-tolerant, accent-insensitive unified catalogue search.

Namespace: /api/v1/heritage/*
Content Scope: RBPC_HUE (isolated from legacy CUU_DINH)
"""
from __future__ import annotations

import base64
import json
import logging
import re
import unicodedata
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session, selectinload

from ..apischemas.heritage import (
    HeritageEngagementOut,
    HeritageEntityType,
    HeritageMediaAssetOut,
    HeritagePlaceDetailOut,
    HeritagePlaceListOut,
    HeritagePlaceOut,
    HeritageRecordStatus,
    HeritageRelationOut,
    HeritageSearchItemOut,
    HeritageSearchOut,
    HeritageSourceEvidenceOut,
)
from ..db import get_db
from ..deps import get_current_user_optional
from ..errors import AppError
from ..models import User
from ..models_rbpc import (
    HeritageAccuracyGrade,
    HeritageHeritageRelation,
    HeritageMediaAsset,
    HeritagePlace,
    HeritageSourceEvidence,
    RbpcStory,
)
from ..rbac import STAFF_ROLES

logger = logging.getLogger("luuniensuki.heritage")

router = APIRouter(tags=["heritage"])

# Accuracy order for 3D model ranking
_ACCURACY_PRIORITY = {
    HeritageAccuracyGrade.survey_grade.value: 1,
    HeritageAccuracyGrade.measured_photogrammetry.value: 2,
    HeritageAccuracyGrade.historian_reviewed.value: 3,
    HeritageAccuracyGrade.illustrative_only.value: 4,
    HeritageAccuracyGrade.unreviewed.value: 5,
}

SLUG_PATTERN = re.compile(r"^[a-zA-Z0-9_\-]{1,120}$")


def _validate_slug(slug: str) -> str:
    """Validate slug format ensuring safe alphanumeric and hyphen/underscore path parameters."""
    cleaned = (slug or "").strip().lower()
    if not cleaned or not SLUG_PATTERN.match(cleaned):
        raise AppError("INVALID_INPUT", f"Malformed slug identifier: '{slug}'.", status.HTTP_400_BAD_REQUEST)
    return cleaned


def _strip_diacritics(s: str) -> str:
    """Normalize and strip combining diacritics for accent-insensitive search."""
    if not s:
        return ""
    normalized = unicodedata.normalize("NFD", s)
    stripped = "".join(c for c in normalized if unicodedata.category(c) != "Mn")
    return stripped.lower().strip()


def _is_staff_user(user: Optional[User]) -> bool:
    """Check if the requesting user has editorial/staff privileges."""
    return user is not None and user.role in STAFF_ROLES


def _has_cleared_3d_asset(place: HeritagePlace) -> bool:
    """Return True if place has at least one rights-cleared, non-rejected 3D model."""
    assets = getattr(place, "media_assets", None) or []
    for m in assets:
        if m.content_scope != "RBPC_HUE":
            continue
        if m.media_type in ("sketchfab_embed", "glb"):
            if m.accuracy_grade != "rejected_accuracy" and m.content_status != "rejected_accuracy":
                if m.embed_permission_status != "blocked" and m.commercial_use_status != "blocked_nc":
                    return True
    return False


def _place_to_out(place: HeritagePlace, has_3d: Optional[bool] = None) -> HeritagePlaceOut:
    """Transform ORM HeritagePlace into Pydantic HeritagePlaceOut summary."""
    if has_3d is None:
        has_3d = _has_cleared_3d_asset(place)

    lat = float(place.location_lat) if place.location_lat is not None else None
    lon = float(place.location_lon) if place.location_lon is not None else None

    return HeritagePlaceOut(
        id=place.id,
        slug=place.slug,
        name_vi=place.name_vi,
        name_en=place.name_en,
        entity_type=place.entity_type,
        heritage_category=place.heritage_category,
        parent_id=place.parent_id,
        official_designation=place.official_designation,
        official_reference_id=place.official_reference_id,
        period_label=place.period_label,
        historical_state=place.historical_state,
        location_lat=lat,
        location_lon=lon,
        geo_precision=place.geo_precision,
        current_access_status=place.current_access_status or "unknown",
        visitor_summary_vi=place.visitor_summary_vi,
        visitor_summary_en=place.visitor_summary_en,
        editorial_status=place.editorial_status,
        content_scope=place.content_scope,
        has_3d=has_3d,
        thumbnail_url=place.thumbnail_url,
        published_at=place.published_at,
        created_at=place.created_at,
        updated_at=place.updated_at,
    )


def _place_to_detail_out(place: HeritagePlace) -> HeritagePlaceDetailOut:
    """Transform ORM HeritagePlace into composite HeritagePlaceDetailOut."""
    base_out = _place_to_out(place)

    # Child places (only published for public, strictly RBPC_HUE)
    children = [
        _place_to_out(c)
        for c in (place.children or [])
        if c.editorial_status == HeritageRecordStatus.published.value
        and c.content_scope == "RBPC_HUE"
    ]

    # Parent place (strictly RBPC_HUE)
    parent = (
        _place_to_out(place.parent)
        if place.parent
        and place.parent.editorial_status == HeritageRecordStatus.published.value
        and place.parent.content_scope == "RBPC_HUE"
        else None
    )

    # Relationships (both outgoing and incoming, strictly RBPC_HUE)
    relations: list[HeritageRelationOut] = []
    for rel in (place.outgoing_relations or []):
        if rel.to_place and rel.to_place.content_scope != "RBPC_HUE":
            continue
        to_slug = rel.to_place.slug if rel.to_place else None
        to_name = rel.to_place.name_vi if rel.to_place else None
        relations.append(
            HeritageRelationOut(
                id=rel.id,
                from_place_id=rel.from_place_id,
                to_place_id=rel.to_place_id,
                from_place_slug=place.slug,
                from_place_name=place.name_vi,
                to_place_slug=to_slug,
                to_place_name=to_name,
                relationship_type=rel.relationship_type,
                claim_id=rel.claim_id,
                review_state=rel.review_state,
                created_at=rel.created_at,
            )
        )
    for rel in (place.incoming_relations or []):
        if rel.from_place and rel.from_place.content_scope != "RBPC_HUE":
            continue
        from_slug = rel.from_place.slug if rel.from_place else None
        from_name = rel.from_place.name_vi if rel.from_place else None
        relations.append(
            HeritageRelationOut(
                id=rel.id,
                from_place_id=rel.from_place_id,
                to_place_id=rel.to_place_id,
                from_place_slug=from_slug,
                from_place_name=from_name,
                to_place_slug=place.slug,
                to_place_name=place.name_vi,
                relationship_type=rel.relationship_type,
                claim_id=rel.claim_id,
                review_state=rel.review_state,
                created_at=rel.created_at,
            )
        )

    # Bibliographic Sources (strictly RBPC_HUE)
    sources = [
        HeritageSourceEvidenceOut.model_validate(src)
        for src in (place.sources or [])
        if src.evidence_status in ("verified", "needs_review")
        and src.content_scope == "RBPC_HUE"
    ]

    # Media assets (filtered: strictly RBPC_HUE, non-rejected accuracy, non-blocked, and rights-cleared)
    media = [
        HeritageMediaAssetOut.model_validate(m)
        for m in (place.media_assets or [])
        if m.content_scope == "RBPC_HUE"
        and m.accuracy_grade != "rejected_accuracy"
        and m.content_status not in ("rejected_accuracy", "blocked", "withdrawn")
        and m.embed_permission_status != "blocked"
        and m.commercial_use_status != "blocked_nc"
    ]

    # Commercial Engagement CTA (strictly RBPC_HUE)
    engagement: Optional[HeritageEngagementOut] = None
    if place.stories:
        published_story = next((s for s in place.stories if s.status == "published" and s.content_scope == "RBPC_HUE"), None)
        if published_story:
            engagement = HeritageEngagementOut(
                cta_kind="story_journey",
                target_slug=published_story.slug,
                title_vi=f"Khám phá câu chuyện: {published_story.title_vi}",
                title_en=f"Discover Story: {published_story.title_en}" if published_story.title_en else None,
                notice="Hành trình trải nghiệm văn hóa kết nối di sản kiến trúc với làng nghề chế tác truyền thống.",
            )
    if engagement is None:
        engagement = HeritageEngagementOut(cta_kind="none")

    return HeritagePlaceDetailOut(
        **base_out.model_dump(),
        access_notes=place.access_notes,
        historical_summary_vi=place.historical_summary_vi,
        historical_summary_en=place.historical_summary_en,
        parent_place=parent,
        child_places=children,
        relations=relations,
        sources=sources,
        media=media,
        engagement=engagement,
    )


# --------------------------------------------------------------------------- #
# Endpoints
# --------------------------------------------------------------------------- #
@router.get("/api/v1/heritage/places", response_model=HeritagePlaceListOut)
def list_heritage_places(
    category: Optional[str] = Query(default=None, description="Filter by heritage category."),
    entity_type: Optional[HeritageEntityType] = Query(default=None, description="Filter by structural entity type."),
    editorial_status: Optional[HeritageRecordStatus] = Query(default=None, description="Filter by editorial status (staff only)."),
    content_scope: str = Query(default="RBPC_HUE", description="Content scope isolation."),
    has_3d: Optional[bool] = Query(default=None, description="Filter by availability of rights-cleared 3D models."),
    cursor: Optional[str] = Query(default=None, description="Keyset pagination cursor."),
    limit: int = Query(default=20, ge=1, le=100, description="Items per page."),
    q: Optional[str] = Query(default=None, description="Search keyword filter."),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Browse and filter heritage places with cursor pagination.

    Public visitors receive only ``published`` records. Staff may filter by any
    editorial status or inspect all statuses.
    """
    is_staff = _is_staff_user(current_user)

    # Content scope guardrail: strictly locked to RBPC_HUE
    if content_scope != "RBPC_HUE":
        raise AppError(
            "FORBIDDEN_SCOPE",
            "Content scope is strictly locked to 'RBPC_HUE' for heritage catalogue.",
            status.HTTP_400_BAD_REQUEST,
        )

    # Parameter bounds validation
    if category and len(category.strip()) > 100:
        raise AppError("INVALID_INPUT", "Category parameter exceeds maximum length of 100 characters.", status.HTTP_400_BAD_REQUEST)
    if q and len(q.strip()) > 200:
        raise AppError("INVALID_INPUT", "Search filter exceeds maximum length of 200 characters.", status.HTTP_400_BAD_REQUEST)

    # Base query
    stmt = (
        select(HeritagePlace)
        .options(
            selectinload(HeritagePlace.media_assets),
        )
        .where(HeritagePlace.content_scope == "RBPC_HUE")
    )

    # Editorial status guardrail
    if not is_staff:
        stmt = stmt.where(HeritagePlace.editorial_status == HeritageRecordStatus.published.value)
    elif editorial_status is not None:
        stmt = stmt.where(HeritagePlace.editorial_status == editorial_status.value)

    # Category and entity type filters
    if category:
        stmt = stmt.where(HeritagePlace.heritage_category == category.strip())
    if entity_type:
        stmt = stmt.where(HeritagePlace.entity_type == entity_type.value)

    # 3D availability subquery filter (strictly scoped to RBPC_HUE and rights-cleared)
    if has_3d is not None:
        subq_3d = (
            select(HeritageMediaAsset.place_id)
            .where(
                HeritageMediaAsset.place_id.is_not(None),
                HeritageMediaAsset.content_scope == "RBPC_HUE",
                HeritageMediaAsset.media_type.in_(["sketchfab_embed", "glb"]),
                HeritageMediaAsset.accuracy_grade != "rejected_accuracy",
                HeritageMediaAsset.content_status != "rejected_accuracy",
                HeritageMediaAsset.embed_permission_status != "blocked",
                HeritageMediaAsset.commercial_use_status != "blocked_nc",
            )
            .distinct()
        )
        if has_3d:
            stmt = stmt.where(HeritagePlace.id.in_(subq_3d))
        else:
            stmt = stmt.where(~HeritagePlace.id.in_(subq_3d))

    # Keyword search filter if provided
    if q and q.strip():
        term = q.strip().lower()
        stmt = stmt.where(
            or_(
                func.lower(HeritagePlace.name_vi).ilike(f"%{term}%"),
                func.lower(HeritagePlace.name_en).ilike(f"%{term}%"),
                func.lower(HeritagePlace.official_reference_id).ilike(f"%{term}%"),
                func.lower(HeritagePlace.visitor_summary_vi).ilike(f"%{term}%"),
            )
        )

    # Total count calculation before pagination
    count_stmt = select(func.count()).select_from(stmt.order_by(None).subquery())
    total_count = db.scalar(count_stmt) or 0

    # Keyset cursor pagination (ordered by created_at DESC, id DESC)
    if cursor:
        if len(cursor) > 1024:
            raise AppError("INVALID_INPUT", "Cursor token exceeds maximum length of 1024 characters.", status.HTTP_400_BAD_REQUEST)
        try:
            raw_bytes = base64.urlsafe_b64decode(cursor.encode("ascii"))
            cursor_data = json.loads(raw_bytes.decode("utf-8"))
            if not isinstance(cursor_data, dict) or "created_at" not in cursor_data or "id" not in cursor_data:
                raise ValueError("Cursor must contain 'created_at' and 'id' fields.")
            cur_created_at = datetime.fromisoformat(cursor_data["created_at"])
            cur_id = UUID(cursor_data["id"])
            stmt = stmt.where(
                or_(
                    HeritagePlace.created_at < cur_created_at,
                    and_(
                        HeritagePlace.created_at == cur_created_at,
                        HeritagePlace.id < cur_id,
                    ),
                )
            )
        except Exception as exc:
            logger.warning("Invalid pagination cursor provided: %s (%s)", cursor, exc)
            raise AppError("INVALID_INPUT", "Malformed or invalid pagination cursor.", status.HTTP_400_BAD_REQUEST)

    # Order and fetch limit + 1 to determine has_more
    stmt = stmt.order_by(HeritagePlace.created_at.desc(), HeritagePlace.id.desc()).limit(limit + 1)
    places = list(db.scalars(stmt))

    has_more = len(places) > limit
    page_items = places[:limit]

    next_cursor: Optional[str] = None
    if has_more and page_items:
        last_item = page_items[-1]
        token_payload = {
            "created_at": last_item.created_at.isoformat(),
            "id": str(last_item.id),
        }
        next_cursor = base64.urlsafe_b64encode(json.dumps(token_payload).encode("utf-8")).decode("ascii")

    items_out = [_place_to_out(p) for p in page_items]

    return HeritagePlaceListOut(
        items=items_out,
        next_cursor=next_cursor,
        has_more=has_more,
        total_count=total_count,
    )


@router.get("/api/v1/heritage/search", response_model=HeritageSearchOut)
def search_heritage_places(
    q: str = Query(..., min_length=2, description="Search keyword."),
    scope: str = Query(default="RBPC_HUE", description="Content scope."),
    limit: int = Query(default=20, ge=1, le=100, description="Max search results."),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Accent-tolerant, diacritic-insensitive search across heritage places.

    Matches query against Vietnamese names, English names, UNESCO reference IDs,
    and summaries with relevance scoring. Public visitors only search published entries.
    """
    is_staff = _is_staff_user(current_user)

    # Scope isolation guardrail
    if scope != "RBPC_HUE":
        raise AppError(
            "FORBIDDEN_SCOPE",
            "Content scope is strictly locked to 'RBPC_HUE' for heritage search.",
            status.HTTP_400_BAD_REQUEST,
        )

    raw_query = q.strip()
    if len(raw_query) > 200:
        raise AppError("INVALID_INPUT", "Search query exceeds maximum length of 200 characters.", status.HTTP_400_BAD_REQUEST)
    norm_query = _strip_diacritics(raw_query)

    stmt = (
        select(HeritagePlace)
        .options(selectinload(HeritagePlace.media_assets))
        .where(HeritagePlace.content_scope == "RBPC_HUE")
    )
    if not is_staff:
        stmt = stmt.where(HeritagePlace.editorial_status == HeritageRecordStatus.published.value)

    candidates = list(db.scalars(stmt))

    results: list[HeritageSearchItemOut] = []
    for p in candidates:
        name_vi_norm = _strip_diacritics(p.name_vi)
        name_en_norm = _strip_diacritics(p.name_en or "")
        ref_norm = _strip_diacritics(p.official_reference_id or "")
        vis_vi_norm = _strip_diacritics(p.visitor_summary_vi or "")
        hist_vi_norm = _strip_diacritics(p.historical_summary_vi or "")

        matched_field: Optional[str] = None
        score: float = 0.0

        if norm_query in name_vi_norm:
            score = 10.0 + (5.0 if name_vi_norm.startswith(norm_query) else 0.0)
            matched_field = "name_vi"
        elif norm_query in name_en_norm:
            score = 8.5
            matched_field = "name_en"
        elif norm_query in ref_norm:
            score = 8.0
            matched_field = "official_reference_id"
        elif norm_query in vis_vi_norm:
            score = 6.0
            matched_field = "visitor_summary"
        elif norm_query in hist_vi_norm:
            score = 4.5
            matched_field = "historical_summary"

        if matched_field:
            results.append(
                HeritageSearchItemOut(
                    id=p.id,
                    slug=p.slug,
                    name_vi=p.name_vi,
                    name_en=p.name_en,
                    entity_type=p.entity_type,
                    heritage_category=p.heritage_category,
                    summary=p.visitor_summary_vi or p.visitor_summary_en,
                    matched_on=matched_field,
                    score=score,
                    has_3d=_has_cleared_3d_asset(p),
                    thumbnail_url=p.thumbnail_url,
                )
            )

    # Sort results by score DESC, name_vi ASC
    results.sort(key=lambda x: (-(x.score or 0.0), x.name_vi))
    paged_results = results[:limit]

    return HeritageSearchOut(
        items=paged_results,
        total=len(results),
        query=raw_query,
        scope=scope,
    )


@router.get("/api/v1/heritage/places/{slug}", response_model=HeritagePlaceDetailOut)
@router.get("/api/v1/heritage/places/{slug}/detail", response_model=HeritagePlaceDetailOut)
def get_heritage_place_detail(
    slug: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Retrieve comprehensive heritage place dossier by unique slug.

    Returns the deep composite representation with parent/child hierarchies,
    relational knowledge graph links, verified source citations, rights-cleared
    media, and commercial story engagement CTAs.
    """
    valid_slug = _validate_slug(slug)
    is_staff = _is_staff_user(current_user)

    stmt = (
        select(HeritagePlace)
        .options(
            selectinload(HeritagePlace.parent),
            selectinload(HeritagePlace.children),
            selectinload(HeritagePlace.outgoing_relations).selectinload(HeritageHeritageRelation.to_place),
            selectinload(HeritagePlace.incoming_relations).selectinload(HeritageHeritageRelation.from_place),
            selectinload(HeritagePlace.sources),
            selectinload(HeritagePlace.media_assets),
            selectinload(HeritagePlace.stories),
        )
        .where(
            HeritagePlace.slug == valid_slug,
            HeritagePlace.content_scope == "RBPC_HUE",
        )
    )

    place = db.scalar(stmt)
    if not place:
        raise AppError("HERITAGE_PLACE_NOT_FOUND", f"Heritage place '{slug}' not found.", status.HTTP_404_NOT_FOUND)

    # Access control: unpublished places require staff privilege
    if not is_staff and place.editorial_status != HeritageRecordStatus.published.value:
        raise AppError("HERITAGE_PLACE_NOT_FOUND", f"Heritage place '{slug}' not found.", status.HTTP_404_NOT_FOUND)

    return _place_to_detail_out(place)


@router.get("/api/v1/heritage/places/{slug}/media", response_model=list[HeritageMediaAssetOut])
def get_heritage_place_media(
    slug: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Retrieve rights-cleared media assets for a heritage place.

    Strictly omits inaccurate, rejected, or rights-restricted assets.
    """
    valid_slug = _validate_slug(slug)
    is_staff = _is_staff_user(current_user)

    place = db.scalar(
        select(HeritagePlace).where(
            HeritagePlace.slug == valid_slug,
            HeritagePlace.content_scope == "RBPC_HUE",
        )
    )
    if not place:
        raise AppError("HERITAGE_PLACE_NOT_FOUND", f"Heritage place '{slug}' not found.", status.HTTP_404_NOT_FOUND)

    if not is_staff and place.editorial_status != HeritageRecordStatus.published.value:
        raise AppError("HERITAGE_PLACE_NOT_FOUND", f"Heritage place '{slug}' not found.", status.HTTP_404_NOT_FOUND)

    media_stmt = (
        select(HeritageMediaAsset)
        .where(
            HeritageMediaAsset.place_id == place.id,
            HeritageMediaAsset.content_scope == "RBPC_HUE",
            HeritageMediaAsset.accuracy_grade != "rejected_accuracy",
            HeritageMediaAsset.content_status.not_in(["rejected_accuracy", "blocked", "withdrawn"]),
            HeritageMediaAsset.embed_permission_status != "blocked",
            HeritageMediaAsset.commercial_use_status != "blocked_nc",
        )
        .order_by(HeritageMediaAsset.created_at.desc())
    )
    assets = list(db.scalars(media_stmt))
    return [HeritageMediaAssetOut.model_validate(m) for m in assets]


@router.get("/api/v1/heritage/places/{slug}/3d", response_model=list[HeritageMediaAssetOut])
def get_heritage_place_3d_models(
    slug: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Retrieve approved 3D Sketchfab viewer embeds for a heritage place.

    Enforces strict 3D quality and rights guardrails:
    - SF-020 (nguyenduc0) and any models with accuracy_grade='rejected_accuracy' are BLOCKED.
    - CC BY-NC-SA models (blocked_nc) are excluded from commercial presentation.
    - Results are sorted by confidence and photogrammetric measurement fidelity.
    - If no rights-cleared 3D model exists, returns empty array [] enabling graceful 2D fallback.
    """
    valid_slug = _validate_slug(slug)
    is_staff = _is_staff_user(current_user)

    place = db.scalar(
        select(HeritagePlace).where(
            HeritagePlace.slug == valid_slug,
            HeritagePlace.content_scope == "RBPC_HUE",
        )
    )
    if not place:
        raise AppError("HERITAGE_PLACE_NOT_FOUND", f"Heritage place '{slug}' not found.", status.HTTP_404_NOT_FOUND)

    if not is_staff and place.editorial_status != HeritageRecordStatus.published.value:
        raise AppError("HERITAGE_PLACE_NOT_FOUND", f"Heritage place '{slug}' not found.", status.HTTP_404_NOT_FOUND)

    models_stmt = (
        select(HeritageMediaAsset)
        .where(
            HeritageMediaAsset.place_id == place.id,
            HeritageMediaAsset.content_scope == "RBPC_HUE",
            HeritageMediaAsset.media_type.in_(["sketchfab_embed", "glb"]),
            HeritageMediaAsset.accuracy_grade != "rejected_accuracy",
            HeritageMediaAsset.content_status != "rejected_accuracy",
            HeritageMediaAsset.embed_permission_status != "blocked",
            HeritageMediaAsset.commercial_use_status != "blocked_nc",
        )
    )

    models = list(db.scalars(models_stmt))

    # Sort models by accuracy priority: survey_grade -> measured_photogrammetry -> historian_reviewed ...
    models.sort(key=lambda m: _ACCURACY_PRIORITY.get(m.accuracy_grade, 99))

    return [HeritageMediaAssetOut.model_validate(m) for m in models]
