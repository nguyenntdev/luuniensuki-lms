#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Idempotent database seeder for STTT Imperial City dataset (Lưu Niên — Đại Nội Huế).

Populates:
1. 4 Spatial Zones from data/imperial/zones_and_sites.json
2. 16 Architectural Sites / Monuments with pedagogical metadata
3. Active Aerial Map Asset from data/imperial/aerial_map_manifest.json
4. Initial 16 normalized UV annotations linked to monuments
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4, uuid5, NAMESPACE_DNS

from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session, sessionmaker

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.imperial_models import (
    CONTENT_SCOPE_IMPERIAL,
    ImperialMapAnnotation,
    ImperialMapAsset,
    ImperialSite,
    ImperialZone,
)
from backend.models import User, UserRole

DEFAULT_DB_URL = "postgresql+psycopg://postgres:postgres@localhost:5432/luuniensuki"


def get_or_create_admin_user(session: Session) -> User:
    """Find an administrative user or create a deterministic system user for authoring."""
    admin = session.execute(
        select(User).where(User.role.in_([UserRole.admin, UserRole.super_admin]))
    ).scalars().first()
    if admin:
        return admin

    admin = session.execute(select(User)).scalars().first()
    if admin:
        return admin

    system_admin = User(
        id=UUID("00000000-0000-0000-0000-000000000001"),
        username="system_curator",
        display_name="Giám tuyển Hệ thống",
        email="curator@luuniensuki.vn",
        password_hash="$2b$12$eX.SampleHashForSystemAdminUserOnly123456789012345678",
        role=UserRole.admin,
    )
    session.add(system_admin)
    session.commit()
    return system_admin


def seed_imperial_data(db_url: str | None = None) -> dict[str, int]:
    """Execute idempotent seeding of spatial zones, sites, aerial map asset, and annotations."""
    url = db_url or os.environ.get("DATABASE_URL") or DEFAULT_DB_URL
    engine = create_engine(url, pool_pre_ping=True)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    zones_path = REPO_ROOT / "data" / "imperial" / "zones_and_sites.json"
    manifest_path = REPO_ROOT / "data" / "imperial" / "aerial_map_manifest.json"

    if not zones_path.exists():
        raise FileNotFoundError(f"Missing {zones_path}")
    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing {manifest_path}")

    zones_data = json.loads(zones_path.read_text(encoding="utf-8"))
    manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))

    stats = {
        "zones_seeded": 0,
        "sites_seeded": 0,
        "maps_seeded": 0,
        "annotations_seeded": 0,
    }

    with SessionLocal() as session:
        curator = get_or_create_admin_user(session)

        # ------------------------------------------------------------------- #
        # 1. Spatial Zones
        # ------------------------------------------------------------------- #
        zone_map: dict[str, UUID] = {}
        for z in zones_data.get("zones", []):
            slug = z["slug"]
            zone_id = uuid5(NAMESPACE_DNS, f"imperial_zone:{slug}")
            zone = session.get(ImperialZone, zone_id)
            if not zone:
                zone = session.execute(
                    select(ImperialZone).where(
                        ImperialZone.content_scope == CONTENT_SCOPE_IMPERIAL,
                        ImperialZone.slug == slug,
                    )
                ).scalar_one_or_none()

            if zone:
                zone.title_vi = z["title_vi"]
                zone.title_en = z.get("title_en")
                zone.description = z.get("description_vi") or z.get("description")
                zone.display_order = z.get("display_order", 0)
                zone_map[slug] = zone.id
            else:
                zone = ImperialZone(
                    id=zone_id,
                    content_scope=CONTENT_SCOPE_IMPERIAL,
                    slug=slug,
                    title_vi=z["title_vi"],
                    title_en=z.get("title_en"),
                    description=z.get("description_vi") or z.get("description"),
                    display_order=z.get("display_order", 0),
                    row_version=1,
                )
                session.add(zone)
                session.flush()
                zone_map[slug] = zone.id
            stats["zones_seeded"] += 1

        # ------------------------------------------------------------------- #
        # 2. Architectural Sites / Monuments
        # ------------------------------------------------------------------- #
        site_map: dict[str, UUID] = {}
        for idx, s in enumerate(zones_data.get("sites", [])):
            slug = s["slug"]
            z_slug = s.get("zone_slug")
            z_id = zone_map.get(z_slug)
            if not z_id:
                raise ValueError(f"Site '{slug}' references unknown zone '{z_slug}'")

            site_id = uuid5(NAMESPACE_DNS, f"imperial_site:{slug}")
            site = session.get(ImperialSite, site_id)
            if not site:
                site = session.execute(
                    select(ImperialSite).where(
                        ImperialSite.content_scope == CONTENT_SCOPE_IMPERIAL,
                        ImperialSite.slug == slug,
                    )
                ).scalar_one_or_none()

            alt_names = s.get("alternative_names", [])
            summary = s.get("historical_summary") or s.get("summary_vi")

            if site:
                site.zone_id = z_id
                site.name_vi = s["name_vi"]
                site.name_en = s.get("name_en")
                site.alternative_names = alt_names
                site.learning_level = s.get("learning_level", "L1_DOCUMENTED")
                site.condition = s.get("condition", "extant")
                site.summary_vi = summary
                site.historical_context = summary
                site.construction_year = s.get("construction_year")
                site.is_published = s.get("published", True)
                site.display_order = idx + 1
                site_map[slug] = site.id
            else:
                site = ImperialSite(
                    id=site_id,
                    content_scope=CONTENT_SCOPE_IMPERIAL,
                    zone_id=z_id,
                    slug=slug,
                    name_vi=s["name_vi"],
                    name_en=s.get("name_en"),
                    alternative_names=alt_names,
                    learning_level=s.get("learning_level", "L1_DOCUMENTED"),
                    condition=s.get("condition", "extant"),
                    summary_vi=summary,
                    historical_context=summary,
                    construction_year=s.get("construction_year"),
                    is_published=s.get("published", True),
                    display_order=idx + 1,
                    created_by=curator.id,
                    updated_by=curator.id,
                    row_version=1,
                )
                session.add(site)
                session.flush()
                site_map[slug] = site.id
            stats["sites_seeded"] += 1

        # ------------------------------------------------------------------- #
        # 3. Aerial Map Asset
        # ------------------------------------------------------------------- #
        map_slug = manifest_data["slug"]
        map_version = manifest_data.get("version", 1)
        map_id = uuid5(NAMESPACE_DNS, f"imperial_map:{map_slug}:{map_version}")

        # Reset active flag on any existing active maps if manifest is active
        if manifest_data.get("is_active", True):
            session.execute(
                text(
                    "UPDATE imperial_map_assets SET is_active = FALSE "
                    "WHERE content_scope = 'STTT_IMPERIAL_CITY' AND is_active = TRUE"
                )
            )

        map_asset = session.get(ImperialMapAsset, map_id)
        if not map_asset:
            map_asset = session.execute(
                select(ImperialMapAsset).where(
                    ImperialMapAsset.content_scope == CONTENT_SCOPE_IMPERIAL,
                    ImperialMapAsset.slug == map_slug,
                    ImperialMapAsset.version == map_version,
                )
            ).scalar_one_or_none()

        now = datetime.now(timezone.utc)
        if map_asset:
            map_asset.title_vi = manifest_data["title_vi"]
            map_asset.title_en = manifest_data.get("title_en")
            map_asset.width_px = manifest_data["width_px"]
            map_asset.height_px = manifest_data["height_px"]
            map_asset.mime_type = manifest_data["mime_type"]
            map_asset.image_storage_key = manifest_data["image_storage_key"]
            map_asset.image_sha256 = manifest_data["image_sha256"]
            map_asset.source_title = manifest_data["source_title"]
            map_asset.credit_text = manifest_data["credit_text"]
            map_asset.license_kind = manifest_data["license_kind"]
            map_asset.license_status = manifest_data.get("license_status", "approved")
            map_asset.review_status = manifest_data.get("review_status", "published")
            map_asset.is_active = manifest_data.get("is_active", True)
            map_asset.published_at = now
            map_asset.approved_by = curator.id
        else:
            map_asset = ImperialMapAsset(
                id=map_id,
                content_scope=CONTENT_SCOPE_IMPERIAL,
                title_vi=manifest_data["title_vi"],
                title_en=manifest_data.get("title_en"),
                slug=map_slug,
                version=map_version,
                width_px=manifest_data["width_px"],
                height_px=manifest_data["height_px"],
                mime_type=manifest_data["mime_type"],
                image_storage_key=manifest_data["image_storage_key"],
                image_sha256=manifest_data["image_sha256"],
                source_title=manifest_data["source_title"],
                credit_text=manifest_data["credit_text"],
                license_kind=manifest_data["license_kind"],
                license_status=manifest_data.get("license_status", "approved"),
                review_status=manifest_data.get("review_status", "published"),
                is_active=manifest_data.get("is_active", True),
                created_by=curator.id,
                approved_by=curator.id,
                published_at=now,
                row_version=1,
            )
            session.add(map_asset)
            session.flush()
        stats["maps_seeded"] += 1

        # ------------------------------------------------------------------- #
        # 4. Initial 16 Annotations
        # ------------------------------------------------------------------- #
        for anno_data in manifest_data.get("initial_annotations", []):
            s_slug = anno_data["site_slug"]
            s_id = site_map.get(s_slug)
            if not s_id:
                continue

            anno_id = uuid5(NAMESPACE_DNS, f"imperial_anno:{map_asset.id}:{s_id}")
            anno = session.get(ImperialMapAnnotation, anno_id)
            if not anno:
                anno = session.execute(
                    select(ImperialMapAnnotation).where(
                        ImperialMapAnnotation.map_asset_id == map_asset.id,
                        ImperialMapAnnotation.site_id == s_id,
                    )
                ).scalar_one_or_none()

            u_coord = anno_data["u"]
            v_coord = anno_data["v"]
            confidence = anno_data.get("confidence") or "approximate"
            marker_style = anno_data.get("marker_style") or "monument"

            if anno:
                anno.u = u_coord
                anno.v = v_coord
                anno.shape_type = anno_data.get("shape_type", "point")
                anno.label = anno_data.get("name_vi")
                anno.marker_style = marker_style
                anno.position_confidence = confidence
                anno.is_visible = anno_data.get("is_visible", True)
                anno.review_status = "published"
                anno.published_at = now
            else:
                anno = ImperialMapAnnotation(
                    id=anno_id,
                    content_scope=CONTENT_SCOPE_IMPERIAL,
                    map_asset_id=map_asset.id,
                    site_id=s_id,
                    shape_type=anno_data.get("shape_type", "point"),
                    u=u_coord,
                    v=v_coord,
                    label=anno_data.get("name_vi"),
                    marker_style=marker_style,
                    position_confidence=confidence,
                    review_status="published",
                    is_visible=anno_data.get("is_visible", True),
                    created_by=curator.id,
                    updated_by=curator.id,
                    approved_by=curator.id,
                    published_at=now,
                    row_version=1,
                )
                session.add(anno)
            stats["annotations_seeded"] += 1

        # ------------------------------------------------------------------- #
        # 5. Learning Paths, Steps & Pedagogical Activities
        # ------------------------------------------------------------------- #
        from backend.services.imperial_learning import _ensure_default_learning_paths
        _ensure_default_learning_paths(session)

        session.commit()

    print(
        f"Seeding completed successfully: "
        f"{stats['zones_seeded']} zones, {stats['sites_seeded']} sites, "
        f"{stats['maps_seeded']} maps, {stats['annotations_seeded']} annotations."
    )
    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed STTT Imperial City dataset into database.")
    parser.add_argument("--db-url", type=str, default=None, help="Database connection URL")
    args = parser.parse_args()
    seed_imperial_data(args.db_url)


if __name__ == "__main__":
    main()
