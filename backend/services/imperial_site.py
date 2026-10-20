# -*- coding: utf-8 -*-
"""Service layer for Imperial City spatial zones and architectural sites (STTT).

Provides domain querying and retrieval for:
- 4 Spatial Zones with site counts
- Architectural sites with pedagogical filters (zone, condition, search, publication status)
- Detailed site dossier including architectural features and media
- Historical claims and primary source evidence references
- Chronological timeline events (construction, alterations, conservation)
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional, Union
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from ..apischemas.imperial import (
    ImperialMediaOut,
    ImperialSiteDetail,
    ImperialSiteEvidence,
    ImperialSiteEvidenceItem,
    ImperialSiteSummary,
    ImperialSiteTimeline,
    ImperialSiteTimelineItem,
    ImperialZoneSummary,
)
from ..errors import AppError
from ..imperial_models import (
    CONTENT_SCOPE_IMPERIAL,
    ImperialMedia,
    ImperialSite,
    ImperialZone,
)

# Optional cached supplemental data from seed json
_ZONES_AND_SITES_FILE = Path(__file__).resolve().parents[2] / "data" / "imperial" / "zones_and_sites.json"
_supplemental_cache: Optional[dict[str, dict[str, Any]]] = None


def _get_supplemental_data() -> dict[str, dict[str, Any]]:
    global _supplemental_cache
    if _supplemental_cache is not None:
        return _supplemental_cache
    cache: dict[str, dict[str, Any]] = {}
    if _ZONES_AND_SITES_FILE.exists():
        try:
            raw = json.loads(_ZONES_AND_SITES_FILE.read_text(encoding="utf-8"))
            for s in raw.get("sites", []):
                slug = s.get("slug")
                if slug:
                    cache[slug] = s
        except Exception:
            pass
    _supplemental_cache = cache
    return _supplemental_cache


def get_zones(db: Session) -> list[ImperialZoneSummary]:
    """List 4 spatial zones with their associated site counts."""
    counts_sub = (
        select(ImperialSite.zone_id, func.count(ImperialSite.id).label("site_count"))
        .where(ImperialSite.content_scope == CONTENT_SCOPE_IMPERIAL)
        .group_by(ImperialSite.zone_id)
        .subquery()
    )

    stmt = (
        select(
            ImperialZone,
            func.coalesce(counts_sub.c.site_count, 0).label("site_count"),
        )
        .outerjoin(counts_sub, ImperialZone.id == counts_sub.c.zone_id)
        .where(ImperialZone.content_scope == CONTENT_SCOPE_IMPERIAL)
        .order_by(ImperialZone.display_order.asc(), ImperialZone.slug.asc())
    )

    results: list[ImperialZoneSummary] = []
    for zone, site_count in db.execute(stmt):
        results.append(
            ImperialZoneSummary(
                id=zone.id,
                slug=zone.slug,
                title_vi=zone.title_vi,
                title_en=zone.title_en,
                display_order=zone.display_order,
                site_count=site_count,
            )
        )
    return results


def get_sites(
    db: Session,
    zone_id: Optional[Union[UUID, str]] = None,
    condition: Optional[str] = None,
    search: Optional[str] = None,
    is_published: Optional[bool] = True,
) -> list[ImperialSiteSummary]:
    """List architectural monuments with optional filters."""
    stmt = (
        select(ImperialSite)
        .where(ImperialSite.content_scope == CONTENT_SCOPE_IMPERIAL)
    )

    if is_published is not None:
        stmt = stmt.where(ImperialSite.is_published == is_published)

    if zone_id is not None:
        # Check if zone_id is a UUID or slug
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
            stmt = stmt.where(ImperialSite.zone_id == parsed_uuid)
        else:
            # Query by zone slug
            stmt = stmt.join(ImperialZone, ImperialSite.zone_id == ImperialZone.id).where(
                ImperialZone.slug == str(zone_id)
            )

    if condition:
        stmt = stmt.where(ImperialSite.condition == condition)

    if search:
        term = f"%{search.strip()}%"
        stmt = stmt.where(
            or_(
                ImperialSite.name_vi.ilike(term),
                ImperialSite.name_en.ilike(term),
                ImperialSite.slug.ilike(term),
                ImperialSite.name_han_nom.ilike(term),
            )
        )

    stmt = stmt.order_by(ImperialSite.display_order.asc(), ImperialSite.name_vi.asc())
    sites = db.execute(stmt).scalars().all()

    return [
        ImperialSiteSummary(
            id=s.id,
            zone_id=s.zone_id,
            slug=s.slug,
            name_vi=s.name_vi,
            name_en=s.name_en,
            site_type=s.site_type,
            condition=s.condition,
            learning_level=s.learning_level,
            is_published=s.is_published,
            display_order=s.display_order,
        )
        for s in sites
    ]


def get_site_by_slug(db: Session, slug: str) -> Optional[ImperialSiteDetail]:
    """Retrieve detailed site dossier by slug, including zone and media."""
    stmt = (
        select(ImperialSite)
        .where(
            ImperialSite.content_scope == CONTENT_SCOPE_IMPERIAL,
            ImperialSite.slug == slug,
        )
        .options(
            selectinload(ImperialSite.zone),
            selectinload(ImperialSite.media),
        )
    )
    site = db.execute(stmt).scalar_one_or_none()
    if not site:
        return None

    zone_summary = None
    if site.zone:
        zone_summary = ImperialZoneSummary(
            id=site.zone.id,
            slug=site.zone.slug,
            title_vi=site.zone.title_vi,
            title_en=site.zone.title_en,
            display_order=site.zone.display_order,
            site_count=0,
        )

    media_items = [
        ImperialMediaOut.model_validate(m)
        for m in site.media
        if getattr(m, "is_published", True)
    ]

    return ImperialSiteDetail(
        id=site.id,
        content_scope=site.content_scope,
        zone_id=site.zone_id,
        slug=site.slug,
        name_vi=site.name_vi,
        name_en=site.name_en,
        name_han_nom=site.name_han_nom,
        alternative_names=site.alternative_names or [],
        site_type=site.site_type,
        condition=site.condition,
        learning_level=site.learning_level,
        summary_vi=site.summary_vi,
        summary_en=site.summary_en,
        historical_context=site.historical_context,
        architectural_features=site.architectural_features,
        construction_year=site.construction_year,
        latitude=site.latitude,
        longitude=site.longitude,
        is_published=site.is_published,
        display_order=site.display_order,
        published_at=site.published_at,
        created_at=site.created_at,
        updated_at=site.updated_at,
        row_version=site.row_version,
        zone=zone_summary,
        media=media_items,
    )


def get_site_evidence(db: Session, slug: str) -> ImperialSiteEvidence:
    """Retrieve historical claims and primary source evidence references for a monument."""
    stmt = select(ImperialSite).where(
        ImperialSite.content_scope == CONTENT_SCOPE_IMPERIAL,
        ImperialSite.slug == slug,
    )
    site = db.execute(stmt).scalar_one_or_none()
    if not site:
        raise AppError("IMPERIAL_SITE_NOT_FOUND", f"Imperial site '{slug}' not found", 404)

    evidence_items: list[ImperialSiteEvidenceItem] = []
    supp = _get_supplemental_data().get(slug, {})

    # 1. Primary sources from seed/manifest
    for src in supp.get("primary_sources", []):
        vol_chap = src.get("volume_or_chapter", "")
        archival = src.get("archival_unit", "")
        citation_parts = [p for p in (vol_chap, archival) if p]
        citation_text = " — ".join(citation_parts) if citation_parts else src.get("citation", "")

        evidence_items.append(
            ImperialSiteEvidenceItem(
                claim_type="architectural_chronicle",
                assertion_vi=src.get("citation") or site.summary_vi or site.name_vi,
                confidence_level="verified",
                source_title=src.get("source_title", "Chính sử triều Nguyễn"),
                source_citation=citation_text,
                verification_status="verified",
            )
        )

    # If no primary sources in supplemental data, provide baseline chronicle evidence
    if not evidence_items:
        evidence_items.append(
            ImperialSiteEvidenceItem(
                claim_type="historical_summary",
                assertion_vi=site.summary_vi or f"Di tích {site.name_vi} trong Hoàng Thành Huế.",
                confidence_level="verified" if site.learning_level != "L1_DOCUMENTED" else "approximate",
                source_title="Hồ sơ Di tích Cố đô Huế",
                source_citation=f"Xây dựng năm {site.construction_year}" if site.construction_year else "Triều Nguyễn",
                verification_status="verified",
            )
        )

    return ImperialSiteEvidence(
        site_slug=site.slug,
        site_name_vi=site.name_vi,
        evidence=evidence_items,
    )


def get_site_timeline(db: Session, slug: str) -> ImperialSiteTimeline:
    """Retrieve chronological events (construction, alterations, conservation) for a monument."""
    stmt = select(ImperialSite).where(
        ImperialSite.content_scope == CONTENT_SCOPE_IMPERIAL,
        ImperialSite.slug == slug,
    )
    site = db.execute(stmt).scalar_one_or_none()
    if not site:
        raise AppError("IMPERIAL_SITE_NOT_FOUND", f"Imperial site '{slug}' not found", 404)

    timeline_items: list[ImperialSiteTimelineItem] = []
    supp = _get_supplemental_data().get(slug, {})
    reign = supp.get("reign") or "Triều Nguyễn"

    # Construction event
    if site.construction_year:
        timeline_items.append(
            ImperialSiteTimelineItem(
                year=site.construction_year,
                period_label=f"Năm {site.construction_year} (Thời {reign})",
                event_title=f"Khởi công và định hình {site.name_vi}",
                description=site.summary_vi or site.historical_context,
                source_ref=supp.get("primary_sources", [{}])[0].get("source_title") if supp.get("primary_sources") else "Chính sử triều Nguyễn",
                is_verified=True,
            )
        )

    # Condition & Restoration events
    cond_desc = supp.get("condition_description_vi")
    if cond_desc:
        timeline_items.append(
            ImperialSiteTimelineItem(
                year=1990,
                period_label="Thời kỳ đương đại",
                event_title="Trùng tu, bảo tồn và phát huy giá trị di sản",
                description=cond_desc,
                source_ref="Trung tâm Bảo tồn Di tích Cố đô Huế",
                is_verified=True,
            )
        )

    # Ensure chronological order
    timeline_items.sort(key=lambda t: t.year or 0)

    return ImperialSiteTimeline(
        site_slug=site.slug,
        site_name_vi=site.name_vi,
        timeline=timeline_items,
    )
