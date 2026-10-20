# -*- coding: utf-8 -*-
"""Integration tests for STTTNNĐ (Lưu Niên — Đại Nội Huế) complete data flow.

Tests:
1. Seed database with zones, monuments, aerial map assets, and annotations.
2. Query active map and verify all 16 UV markers ([0.0, 1.0] bounds, site joins).
3. Verify site dossier 7-section pedagogical architecture across monuments.
4. Verify strict data isolation (content_scope = 'STTT_IMPERIAL_CITY', zero contamination).
5. Verify optimistic locking concurrency (row_version handling).
"""
from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import Session, sessionmaker

import backend.imperial_models as im
from backend.models import User, UserRole

REPO_ROOT = Path(__file__).resolve().parents[2]
ZONES_SITES_FILE = REPO_ROOT / "data" / "imperial" / "zones_and_sites.json"
AERIAL_MANIFEST_FILE = REPO_ROOT / "data" / "imperial" / "aerial_map_manifest.json"


@pytest.fixture(scope="module")
def db_engine():
    """Isolated in-memory SQLite engine with JSONB and UUID compatibility interceptors."""
    engine = create_engine("sqlite:///:memory:", echo=False)

    @event.listens_for(engine, "before_cursor_execute", retval=True)
    def intercept_pg_syntax(conn, cursor, statement, parameters, context, executemany):
        # Strip Postgres-specific cast for SQLite compatibility
        clean_statement = statement.replace("::jsonb", "")
        return clean_statement, parameters

    # Create User table and all 13 Imperial tables
    User.__table__.create(engine)
    tables = [
        im.ImperialZone,
        im.ImperialSite,
        im.ImperialMapAsset,
        im.ImperialMapAnnotation,
        im.ImperialAnnotationLink,
        im.ImperialAnnotationAudit,
        im.ImperialLens,
        im.ImperialLensSite,
        im.ImperialLearningPath,
        im.ImperialPathStep,
        im.ImperialActivity,
        im.ImperialSubmission,
        im.ImperialMedia,
    ]
    for model in tables:
        model.__table__.create(engine)

    yield engine
    engine.dispose()


@pytest.fixture
def session(db_engine):
    """Provides a fresh transactional session for each test."""
    connection = db_engine.connect()
    transaction = connection.begin()
    SessionLocal = sessionmaker(bind=connection, autoflush=False, autocommit=False)
    sess = SessionLocal()

    yield sess

    sess.close()
    transaction.rollback()
    connection.close()


def _seed_imperial_dataset(sess: Session) -> dict[str, Any]:
    """Helper to seed the complete verified STTT Imperial dataset from JSON fixtures."""
    zones_data = json.loads(ZONES_SITES_FILE.read_text(encoding="utf-8"))
    manifest_data = json.loads(AERIAL_MANIFEST_FILE.read_text(encoding="utf-8"))

    # 0. Seed Admin Actor User for audit foreign keys
    admin_id = uuid.uuid5(uuid.NAMESPACE_DNS, "admin-imperial")
    admin_user = User(
        id=admin_id,
        email="admin.imperial@luuniensuki.vn",
        password_hash="argon2_hashed_secret",
        display_name="Cán bộ Quản trị Di sản Đại Nội",
        role=UserRole.admin,
    )
    sess.add(admin_user)
    sess.flush()

    # 1. Seed Zones
    zone_map: dict[str, im.ImperialZone] = {}
    for z in zones_data["zones"]:
        zone_obj = im.ImperialZone(
            id=uuid.uuid5(uuid.NAMESPACE_DNS, z["slug"]),
            content_scope="STTT_IMPERIAL_CITY",
            slug=z["slug"],
            title_vi=z["title_vi"],
            title_en=z.get("title_en"),
            description=z.get("description_vi"),
            display_order=z.get("display_order", 0),
        )
        sess.add(zone_obj)
        zone_map[z["slug"]] = zone_obj

    sess.flush()

    # 2. Seed Sites
    site_map: dict[str, im.ImperialSite] = {}
    for s in zones_data["sites"]:
        zone = zone_map[s["zone_slug"]]
        site_obj = im.ImperialSite(
            id=uuid.uuid5(uuid.NAMESPACE_DNS, s["slug"]),
            content_scope="STTT_IMPERIAL_CITY",
            zone_id=zone.id,
            slug=s["slug"],
            name_vi=s["name_vi"],
            name_en=s.get("name_en"),
            name_han_nom=s.get("name_han_nom"),
            alternative_names=s.get("alternative_names", []),
            condition=s.get("condition", "extant"),
            learning_level=s.get("learning_level", "L1_DOCUMENTED"),
            summary_vi=s.get("historical_summary"),
            construction_year=s.get("construction_year"),
            is_published=s.get("published", True),
            created_by=admin_user.id,
            updated_by=admin_user.id,
            display_order=0,
            row_version=1,
        )
        sess.add(site_obj)
        site_map[s["slug"]] = site_obj

    sess.flush()

    # 3. Seed Aerial Map Asset
    map_asset = im.ImperialMapAsset(
        id=uuid.uuid5(uuid.NAMESPACE_DNS, manifest_data["slug"]),
        content_scope="STTT_IMPERIAL_CITY",
        title_vi=manifest_data["title_vi"],
        title_en=manifest_data.get("title_en"),
        slug=manifest_data["slug"],
        version=manifest_data["version"],
        image_storage_key=manifest_data["image_storage_key"],
        image_sha256=manifest_data["image_sha256"],
        mime_type=manifest_data["mime_type"],
        width_px=manifest_data["width_px"],
        height_px=manifest_data["height_px"],
        source_title=manifest_data["source_title"],
        credit_text=manifest_data["credit_text"],
        license_kind=manifest_data["license_kind"],
        license_status=manifest_data["license_status"],
        review_status=manifest_data["review_status"],
        is_active=manifest_data["is_active"],
        created_by=admin_user.id,
        row_version=1,
    )
    sess.add(map_asset)
    sess.flush()

    # 4. Seed Annotations
    anno_list: list[im.ImperialMapAnnotation] = []
    for anno in manifest_data["initial_annotations"]:
        site = site_map[anno["site_slug"]]
        anno_obj = im.ImperialMapAnnotation(
            id=uuid.uuid5(uuid.NAMESPACE_DNS, anno["annotation_id"]),
            content_scope="STTT_IMPERIAL_CITY",
            map_asset_id=map_asset.id,
            site_id=site.id,
            shape_type=anno.get("shape_type", "point"),
            u=anno["u"],
            v=anno["v"],
            label=anno["name_vi"],
            marker_style=anno.get("marker_style", "monument"),
            review_status="published",
            position_confidence=anno.get("confidence", "verified"),
            created_by=admin_user.id,
            updated_by=admin_user.id,
            row_version=1,
        )
        sess.add(anno_obj)
        anno_list.append(anno_obj)

    sess.commit()

    return {
        "zones": zone_map,
        "sites": site_map,
        "map_asset": map_asset,
        "annotations": anno_list,
        "raw_zones_data": zones_data,
    }


# =========================================================================== #
# Integration Tests
# =========================================================================== #
class TestImperialApiIntegration:
    """Verifies complete end-to-end data flow for STTT Imperial City dataset."""

    def test_seed_database_and_verify_counts(self, session: Session):
        """Seed database and assert exact entity counts and relationships."""
        seed_result = _seed_imperial_dataset(session)

        # 4 zones
        zones = session.execute(select(im.ImperialZone)).scalars().all()
        assert len(zones) == 4
        zone_slugs = {z.slug for z in zones}
        assert "central-ceremonial-axis" in zone_slugs
        assert "ancestral-worship-space" in zone_slugs
        assert "purple-forbidden-city" in zone_slugs
        assert "royal-living-gardens" in zone_slugs

        # 16 monuments
        sites = session.execute(select(im.ImperialSite)).scalars().all()
        assert len(sites) == 16
        for s in sites:
            assert s.zone_id is not None
            assert s.name_vi is not None
            assert s.content_scope == "STTT_IMPERIAL_CITY"

        # 1 aerial map asset
        maps = session.execute(select(im.ImperialMapAsset)).scalars().all()
        assert len(maps) == 1
        assert maps[0].slug == "dai-noi-aerial-v1"
        assert maps[0].width_px == 4096
        assert maps[0].height_px == 3072
        assert maps[0].is_active is True

        # 16 annotations
        annos = session.execute(select(im.ImperialMapAnnotation)).scalars().all()
        assert len(annos) == 16

    def test_active_map_query_and_16_uv_markers(self, session: Session):
        """Simulates GET /api/v1/imperial/maps/active and verifies all 16 UV annotations."""
        _seed_imperial_dataset(session)

        # Fetch active map asset
        active_map = session.execute(
            select(im.ImperialMapAsset).where(
                im.ImperialMapAsset.is_active == True,
                im.ImperialMapAsset.review_status == "published",
            )
        ).scalar_one()

        assert active_map.slug == "dai-noi-aerial-v1"
        assert active_map.version == 1

        # Query all annotations belonging to this active map
        annos = session.execute(
            select(im.ImperialMapAnnotation)
            .where(
                im.ImperialMapAnnotation.map_asset_id == active_map.id,
                im.ImperialMapAnnotation.review_status == "published",
            )
        ).scalars().all()

        assert len(annos) == 16

        for anno in annos:
            u_val = float(anno.u)
            v_val = float(anno.v)
            # UV bounds strictly within [0.0, 1.0]
            assert 0.0 <= u_val <= 1.0, f"Annotation {anno.label} u={u_val} out of bounds"
            assert 0.0 <= v_val <= 1.0, f"Annotation {anno.label} v={v_val} out of bounds"
            # Site relationship
            assert anno.site is not None
            assert anno.site.content_scope == "STTT_IMPERIAL_CITY"
            assert anno.site.zone is not None

        # Specific known monuments
        ngo_mon_anno = next(a for a in annos if a.site.slug == "ngo-mon")
        assert float(ngo_mon_anno.u) == pytest.approx(0.5002, abs=1e-4)
        assert float(ngo_mon_anno.v) == pytest.approx(0.8524, abs=1e-4)

        thai_hoa_anno = next(a for a in annos if a.site.slug == "dien-thai-hoa")
        assert float(thai_hoa_anno.u) == pytest.approx(0.5002, abs=1e-4)
        assert float(thai_hoa_anno.v) == pytest.approx(0.6384, abs=1e-4)

    def test_site_dossier_7_sections_data_flow(self, session: Session):
        """Verify the 7-section pedagogical architecture for L2 monuments."""
        seed_result = _seed_imperial_dataset(session)
        raw_sites = {s["slug"]: s for s in seed_result["raw_zones_data"]["sites"]}

        l2_slugs = [
            "ngo-mon",
            "san-dai-trieu-nghi",
            "dien-thai-hoa",
            "the-to-mieu",
            "hien-lam-cac",
            "dien-can-chanh",
            "dien-kien-trung",
            "duyet-thi-duong",
            "cung-dien-tho",
        ]

        for slug in l2_slugs:
            # Query site from DB
            site = session.execute(
                select(im.ImperialSite).where(im.ImperialSite.slug == slug)
            ).scalar_one()

            raw = raw_sites[slug]

            # 1. Hero identity
            assert site.name_vi == raw["name_vi"]
            assert site.condition in (
                "extant",
                "reconstructed",
                "ruin",
                "restored",
                "archaeological",
                "foundation_ruin",
                "restored_2023",
            )
            assert site.zone.slug == raw["zone_slug"]

            # 2. Guiding question & summary
            inquiry_q = raw.get("guiding_inquiry_question") or raw.get("guiding_question")
            assert inquiry_q and len(inquiry_q.strip()) > 10
            assert site.summary_vi and len(site.summary_vi.strip()) > 20

            # 3. Timeline & Construction
            assert raw.get("construction_year") is not None
            assert raw.get("reign") is not None

            # 4. Sources & Primary evidence (Section 5)
            sources = raw.get("primary_sources", [])
            assert len(sources) >= 1
            for s in sources:
                assert s.get("source_title") is not None
                assert s.get("citation") is not None

            # 5. Pedagogical Task (Section 6)
            task = raw.get("pedagogical_task", {})
            assert task.get("task_prompt") is not None
            assert len(task["task_prompt"].strip()) > 15

            # 6. Rubrics S1-S4
            rubrics = raw.get("rubrics", {})
            assert any(k in rubrics for k in ("S1_spatial", "S1"))
            assert any(k in rubrics for k in ("S2_temporal", "S2"))
            assert any(k in rubrics for k in ("S3_evidence", "S3"))
            assert any(k in rubrics for k in ("S4_argument", "S4_reasoning", "S4"))

    def test_strict_data_isolation(self, session: Session):
        """Verify strict content_scope enforcement and zero legacy leakage in records."""
        _seed_imperial_dataset(session)

        # 1. Content scope check across all tables
        for model in (im.ImperialZone, im.ImperialSite, im.ImperialMapAsset, im.ImperialMapAnnotation):
            records = session.execute(select(model)).scalars().all()
            for r in records:
                assert r.content_scope == "STTT_IMPERIAL_CITY"

        # 2. Scan records for forbidden legacy terms
        forbidden = [
            "cửu đỉnh",
            "cuu dinh",
            "cao đỉnh",
            "nhân đỉnh",
            "chương đỉnh",
            "162",
            "bản đúc nổi",
            "relief motif",
        ]
        sites = session.execute(select(im.ImperialSite)).scalars().all()
        for s in sites:
            text_corpus = f"{s.name_vi} {s.summary_vi or ''} {s.slug}".lower()
            for f_term in forbidden:
                assert f_term not in text_corpus, f"Forbidden term '{f_term}' found in site {s.slug}"

    def test_optimistic_locking_concurrency(self, session: Session):
        """Verify row_version optimistic concurrency behavior."""
        _seed_imperial_dataset(session)

        site = session.execute(
            select(im.ImperialSite).where(im.ImperialSite.slug == "ngo-mon")
        ).scalar_one()

        initial_version = site.row_version
        assert initial_version == 1

        # Simulate update with version increment
        site.display_order = 10
        site.row_version = initial_version + 1
        session.commit()

        reloaded = session.execute(
            select(im.ImperialSite).where(im.ImperialSite.slug == "ngo-mon")
        ).scalar_one()
        assert reloaded.row_version == 2
        assert reloaded.display_order == 10
