# -*- coding: utf-8 -*-
"""Comprehensive integration test suite for STTT Imperial City API (Lưu Niên — Đại Nội Huế).

Validates:
1. Public endpoints:
   - Zones retrieval with site counts
   - Sites listing with filters (zone, condition, search)
   - Site dossier detail by slug (including zone and media)
   - Site evidence claims and primary sources
   - Site chronological timeline events
   - Active published aerial map retrieval
   - Public map image asset streaming with cache headers
2. Annotation creation with UV bounds checking ([0.0, 1.0]) and audit logging
3. Optimistic locking concurrency control (409 Conflict on row_version mismatch)
4. Atomic aerial map publication transactions
5. JSON export and import with dry-run diffing and all-or-nothing transactional execution
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Generator
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.sql.elements import TextClause

import backend.models as models
from backend.apischemas.imperial import (
    ImperialAnnotationCreate,
    ImperialAnnotationUpdate,
    ImperialMapAssetUpload,
)
from backend.deps import get_admin_user, get_db, get_staff_user
from backend.imperial_models import (
    CONTENT_SCOPE_IMPERIAL,
    Base,
    ImperialAnnotationAudit,
    ImperialAnnotationLink,
    ImperialMapAnnotation,
    ImperialMapAsset,
    ImperialMedia,
    ImperialSite,
    ImperialZone,
)
from backend.main import app


# --------------------------------------------------------------------------- #
# Database Fixture for Isolated Integration Testing
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="module")
def imperial_db_engine():
    """Create in-memory SQLite engine with all imperial and user tables."""
    for idx in list(ImperialMapAsset.__table__.indexes):
        if idx.name == "idx_imperial_active_map":
            idx.unique = False

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    tables = [
        models.User.__table__,
        ImperialZone.__table__,
        ImperialSite.__table__,
        ImperialMedia.__table__,
        ImperialMapAsset.__table__,
        ImperialMapAnnotation.__table__,
        ImperialAnnotationLink.__table__,
        ImperialAnnotationAudit.__table__,
    ]
    # Clean PostgreSQL specific defaults for SQLite compatibility
    for t in tables:
        for col in t.columns:
            if (
                col.server_default is not None
                and hasattr(col.server_default, "arg")
                and isinstance(col.server_default.arg, TextClause)
            ):
                col.server_default.arg.text = col.server_default.arg.text.replace(
                    "::jsonb", ""
                )
    Base.metadata.create_all(engine, tables=tables)
    return engine


@pytest.fixture(autouse=True)
def clean_database_tables(imperial_db_engine):
    """Clean all test tables between each test run to ensure strict isolation."""
    TestingSession = sessionmaker(bind=imperial_db_engine, autoflush=False, autocommit=False)
    with TestingSession() as sess:
        sess.query(ImperialAnnotationAudit).delete()
        sess.query(ImperialAnnotationLink).delete()
        sess.query(ImperialMapAnnotation).delete()
        sess.query(ImperialMapAsset).delete()
        sess.query(ImperialMedia).delete()
        sess.query(ImperialSite).delete()
        sess.query(ImperialZone).delete()
        sess.query(models.User).delete()
        sess.commit()
    yield


@pytest.fixture
def db_session(imperial_db_engine) -> Generator[Session, None, None]:
    """Yield a database session and clean up after each test."""
    TestingSession = sessionmaker(bind=imperial_db_engine, autoflush=False, autocommit=False)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def test_users(db_session: Session) -> dict[str, models.User]:
    """Create test users with admin and staff roles."""
    admin_id = uuid4()
    admin_user = models.User(
        id=admin_id,
        username=f"admin_{admin_id.hex[:6]}",
        email=f"admin_{admin_id.hex[:6]}@example.com",
        display_name=f"Admin {admin_id.hex[:6]}",
        password_hash="mock_hash",
        role=models.UserRole.admin,
    )
    staff_id = uuid4()
    staff_user = models.User(
        id=staff_id,
        username=f"staff_{staff_id.hex[:6]}",
        email=f"staff_{staff_id.hex[:6]}@example.com",
        display_name=f"Staff {staff_id.hex[:6]}",
        password_hash="mock_hash",
        role=models.UserRole.teacher,
    )
    db_session.add_all([admin_user, staff_user])
    db_session.commit()
    return {"admin": admin_user, "staff": staff_user}


@pytest.fixture
def api_client(db_session: Session, test_users: dict[str, models.User]) -> Generator[TestClient, None, None]:
    """Provide a TestClient with overridden dependencies for DB and authentication."""
    def _override_db():
        yield db_session

    def _override_staff():
        return test_users["staff"]

    def _override_admin():
        return test_users["admin"]

    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_staff_user] = _override_staff
    app.dependency_overrides[get_admin_user] = _override_admin

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
def seeded_dataset(db_session: Session, test_users: dict[str, models.User]):
    """Seed baseline spatial zones, sites, map asset, and annotations."""
    admin = test_users["admin"]

    # 1. Spatial Zones
    zone1 = ImperialZone(
        id=uuid4(),
        content_scope=CONTENT_SCOPE_IMPERIAL,
        slug="central-ceremonial-axis",
        title_vi="Trục trung tâm",
        title_en="Central Ceremonial Axis",
        description="Trục chính đạo thiết lập trật tự không gian quyền lực",
        display_order=1,
    )
    zone2 = ImperialZone(
        id=uuid4(),
        content_scope=CONTENT_SCOPE_IMPERIAL,
        slug="ancestral-worship-space",
        title_vi="Không gian thờ tự",
        title_en="Ancestral Worship Space",
        description="Khu vực các miếu điện linh thiêng",
        display_order=2,
    )
    db_session.add_all([zone1, zone2])
    db_session.flush()

    # 2. Monuments / Sites
    site_ngo_mon = ImperialSite(
        id=uuid4(),
        content_scope=CONTENT_SCOPE_IMPERIAL,
        zone_id=zone1.id,
        slug="ngo-mon",
        name_vi="Ngọ Môn",
        name_en="Meridian Gate",
        alternative_names=["Cửa Ngọ Môn", "Lầu Ngũ Phụng"],
        site_type="gate",
        condition="extant",
        learning_level="L2_LEARNING_READY",
        summary_vi="Cổng chính phía nam của Hoàng Thành Huế.",
        historical_context="Xây dựng năm Minh Mạng thứ 14 (1833).",
        architectural_features="Cấu trúc đài đá chữ U trổ 5 cửa, trên là lầu Ngũ Phụng.",
        construction_year=1833,
        is_published=True,
        display_order=1,
        created_by=admin.id,
        updated_by=admin.id,
    )
    site_thai_hoa = ImperialSite(
        id=uuid4(),
        content_scope=CONTENT_SCOPE_IMPERIAL,
        zone_id=zone1.id,
        slug="dien-thai-hoa",
        name_vi="Điện Thái Hòa",
        name_en="Throne Palace",
        site_type="palace",
        condition="extant",
        learning_level="L2_LEARNING_READY",
        summary_vi="Cung điện thiết đại triều uy nghiêm.",
        historical_context="Xây dựng thời vua Gia Long năm 1805.",
        construction_year=1805,
        is_published=True,
        display_order=2,
        created_by=admin.id,
        updated_by=admin.id,
    )
    site_the_to_mieu = ImperialSite(
        id=uuid4(),
        content_scope=CONTENT_SCOPE_IMPERIAL,
        zone_id=zone2.id,
        slug="the-to-mieu",
        name_vi="Thế Tổ Miếu",
        name_en="Ancestral Temple",
        site_type="temple",
        condition="extant",
        learning_level="L2_LEARNING_READY",
        summary_vi="Nơi thờ phụng các vị vua triều Nguyễn.",
        construction_year=1821,
        is_published=True,
        display_order=3,
        created_by=admin.id,
        updated_by=admin.id,
    )
    db_session.add_all([site_ngo_mon, site_thai_hoa, site_the_to_mieu])
    db_session.flush()

    # 3. Aerial Map Asset
    map_asset = ImperialMapAsset(
        id=uuid4(),
        content_scope=CONTENT_SCOPE_IMPERIAL,
        slug="dai-noi-aerial-v1",
        version=1,
        title_vi="Bản đồ không ảnh Đại Nội Huế",
        title_en="Aerial Orthomosaic Map",
        width_px=4096,
        height_px=3072,
        mime_type="image/webp",
        image_storage_key="imperial/maps/dai-noi-aerial-v1.webp",
        image_sha256="4b6c31046889c25651c6b1a7d6565fcf46200676b50e4a7a8d003f56d98f79d2",
        source_title="Nguồn viễn thám di sản Huế",
        credit_text="Bản đồ học tập số Đại Nội Huế",
        license_kind="educational_fair_use",
        license_status="approved",
        review_status="published",
        is_active=True,
        created_by=admin.id,
        approved_by=admin.id,
        row_version=1,
    )
    db_session.add(map_asset)
    db_session.flush()

    # 4. Published Annotation
    anno_ngo_mon = ImperialMapAnnotation(
        id=uuid4(),
        content_scope=CONTENT_SCOPE_IMPERIAL,
        map_asset_id=map_asset.id,
        site_id=site_ngo_mon.id,
        shape_type="point",
        u=0.5002,
        v=0.8524,
        label="Ngọ Môn",
        marker_style="monument_primary",
        review_status="published",
        is_visible=True,
        position_confidence="verified",
        created_by=admin.id,
        updated_by=admin.id,
        approved_by=admin.id,
        row_version=1,
    )
    db_session.add(anno_ngo_mon)
    db_session.commit()

    return {
        "zone1": zone1,
        "zone2": zone2,
        "site_ngo_mon": site_ngo_mon,
        "site_thai_hoa": site_thai_hoa,
        "site_the_to_mieu": site_the_to_mieu,
        "map_asset": map_asset,
        "anno_ngo_mon": anno_ngo_mon,
    }


# =========================================================================== #
# 1. Public API Endpoint Tests
# =========================================================================== #
class TestPublicImperialAPI:
    """Test public endpoints without requiring authentication."""

    def test_get_zones_with_site_counts(self, api_client: TestClient, seeded_dataset):
        res = api_client.get("/api/v1/imperial/zones")
        assert res.status_code == 200, res.text
        data = res.json()
        assert len(data) >= 2
        # Zone 1 has 2 sites, Zone 2 has 1 site
        z1 = next(z for z in data if z["slug"] == "central-ceremonial-axis")
        assert z1["site_count"] == 2
        z2 = next(z for z in data if z["slug"] == "ancestral-worship-space")
        assert z2["site_count"] == 1

    def test_get_sites_filters(self, api_client: TestClient, seeded_dataset):
        # All published sites
        res = api_client.get("/api/v1/imperial/sites")
        assert res.status_code == 200
        assert len(res.json()) >= 3

        # Filter by zone slug
        res_zone = api_client.get("/api/v1/imperial/sites", params={"zone": "central-ceremonial-axis"})
        assert res_zone.status_code == 200
        assert len(res_zone.json()) == 2
        assert all(s["slug"] in ("ngo-mon", "dien-thai-hoa") for s in res_zone.json())

        # Search by term
        res_search = api_client.get("/api/v1/imperial/sites", params={"search": "Thái Hòa"})
        assert res_search.status_code == 200
        assert len(res_search.json()) == 1
        assert res_search.json()[0]["slug"] == "dien-thai-hoa"

    def test_get_site_by_slug_success_and_not_found(self, api_client: TestClient, seeded_dataset):
        res = api_client.get("/api/v1/imperial/sites/ngo-mon")
        assert res.status_code == 200
        data = res.json()
        assert data["slug"] == "ngo-mon"
        assert data["name_vi"] == "Ngọ Môn"
        assert data["zone"]["slug"] == "central-ceremonial-axis"
        assert data["construction_year"] == 1833

        # Nonexistent site
        res_404 = api_client.get("/api/v1/imperial/sites/nonexistent-monument")
        assert res_404.status_code == 404
        assert res_404.json()["error"]["code"] == "IMPERIAL_SITE_NOT_FOUND"

    def test_get_site_evidence(self, api_client: TestClient, seeded_dataset):
        res = api_client.get("/api/v1/imperial/sites/ngo-mon/evidence")
        assert res.status_code == 200
        data = res.json()
        assert data["site_slug"] == "ngo-mon"
        assert len(data["evidence"]) >= 1
        assert any(e["source_title"] for e in data["evidence"])

    def test_get_site_timeline(self, api_client: TestClient, seeded_dataset):
        res = api_client.get("/api/v1/imperial/sites/ngo-mon/timeline")
        assert res.status_code == 200
        data = res.json()
        assert data["site_slug"] == "ngo-mon"
        assert len(data["timeline"]) >= 1
        # Year 1833 construction event present
        assert any(t["year"] == 1833 for t in data["timeline"])

    def test_get_active_map_and_annotations(self, api_client: TestClient, seeded_dataset):
        res = api_client.get("/api/v1/imperial/maps/active")
        assert res.status_code == 200
        data = res.json()
        assert data["scope"] == "STTT_IMPERIAL_CITY"
        assert data["map"]["slug"] == "dai-noi-aerial-v1"
        assert len(data["annotations"]) >= 1
        anno = data["annotations"][0]
        assert anno["site"]["slug"] == "ngo-mon"
        assert 0.0 <= anno["u"] <= 1.0
        assert 0.0 <= anno["v"] <= 1.0

    def test_get_map_asset_image_caching_headers(self, api_client: TestClient, seeded_dataset):
        map_id = seeded_dataset["map_asset"].id
        res = api_client.get(f"/api/v1/imperial/assets/{map_id}/image")
        assert res.status_code == 200
        assert "Cache-Control" in res.headers
        assert "public" in res.headers["Cache-Control"]
        assert "ETag" in res.headers


# =========================================================================== #
# 2. Annotation Creation & UV Bounds Validation Tests
# =========================================================================== #
class TestAnnotationCreationAndUVBounds:
    """Test annotation marker creation, bounds validation, and audit entry."""

    def test_create_annotation_valid_uv(self, api_client: TestClient, seeded_dataset):
        map_id = seeded_dataset["map_asset"].id
        site_id = seeded_dataset["site_thai_hoa"].id

        payload = {
            "site_id": str(site_id),
            "shape_type": "point",
            "u": 0.5002,
            "v": 0.6384,
            "label": "Điện Thái Hòa",
            "marker_style": "palace",
            "position_confidence": "verified",
        }
        res = api_client.post(f"/api/v1/imperial/admin/maps/{map_id}/annotations", json=payload)
        assert res.status_code == 201, res.text
        data = res.json()
        assert data["u"] == 0.5002
        assert data["v"] == 0.6384
        assert data["review_status"] == "draft"
        assert data["row_version"] == 1

        # Check audit entry created
        audit_res = api_client.get(f"/api/v1/imperial/admin/annotations/{data['id']}/audit")
        assert audit_res.status_code == 200
        audits = audit_res.json()
        assert len(audits) >= 1
        assert audits[0]["action"] == "create"

    @pytest.mark.parametrize(
        "invalid_u, invalid_v",
        [
            (-0.0001, 0.5),
            (1.0001, 0.5),
            (0.5, -0.1),
            (0.5, 1.2),
            (-1.0, -1.0),
            (2.0, 2.0),
        ],
    )
    def test_reject_out_of_bounds_uv(
        self, api_client: TestClient, seeded_dataset, invalid_u, invalid_v
    ):
        map_id = seeded_dataset["map_asset"].id
        site_id = seeded_dataset["site_the_to_mieu"].id

        payload = {
            "site_id": str(site_id),
            "u": invalid_u,
            "v": invalid_v,
        }
        res = api_client.post(f"/api/v1/imperial/admin/maps/{map_id}/annotations", json=payload)
        assert res.status_code == 422, f"Should reject u={invalid_u}, v={invalid_v}"


# =========================================================================== #
# 3. Optimistic Locking Concurrency Tests
# =========================================================================== #
class TestOptimisticLockingConcurrency:
    """Validate 409 Conflict rejection when row_version does not match current DB version."""

    def test_optimistic_locking_flow(self, api_client: TestClient, seeded_dataset):
        anno = seeded_dataset["anno_ngo_mon"]
        anno_id = anno.id
        initial_version = anno.row_version

        # 1. Successful update matching row_version
        update_payload = {
            "u": 0.5010,
            "v": 0.8530,
            "row_version": initial_version,
        }
        res1 = api_client.patch(f"/api/v1/imperial/admin/annotations/{anno_id}", json=update_payload)
        assert res1.status_code == 200
        updated = res1.json()
        assert updated["row_version"] == initial_version + 1
        assert updated["u"] == 0.5010

        # 2. Stale update with old row_version must return 409 Conflict
        stale_payload = {
            "u": 0.5020,
            "v": 0.8540,
            "row_version": initial_version,  # Stale!
        }
        res2 = api_client.patch(f"/api/v1/imperial/admin/annotations/{anno_id}", json=stale_payload)
        assert res2.status_code == 409
        err = res2.json()["error"]
        assert err["code"] == "IMPERIAL_CONCURRENCY_CONFLICT"
        assert err["details"]["current_row_version"] == initial_version + 1


# =========================================================================== #
# 4. Atomic Map Publication Tests
# =========================================================================== #
class TestMapPublication:
    """Test map publication lifecycle, license checks, and atomic state transition."""

    def test_publish_map_requires_approved_license(self, api_client: TestClient, db_session: Session, test_users):
        admin = test_users["admin"]
        # Create map with pending license
        draft_map = ImperialMapAsset(
            id=uuid4(),
            content_scope=CONTENT_SCOPE_IMPERIAL,
            slug="dai-noi-aerial-v2-draft",
            version=2,
            title_vi="Bản đồ thử nghiệm v2",
            width_px=4096,
            height_px=3072,
            mime_type="image/webp",
            image_storage_key="imperial/maps/test-v2.webp",
            image_sha256="0" * 64,
            source_title="Ảnh thử nghiệm",
            credit_text="Credit",
            license_kind="permission_required",
            license_status="pending",  # Unapproved!
            review_status="draft",
            is_active=False,
            created_by=admin.id,
            row_version=1,
        )
        db_session.add(draft_map)
        db_session.commit()

        # Attempt to publish unapproved map
        res = api_client.post(f"/api/v1/imperial/admin/maps/{draft_map.id}/publish")
        assert res.status_code == 400
        assert res.json()["error"]["code"] == "IMPERIAL_LICENSE_NOT_APPROVED"

    def test_publish_approved_map_sets_active_and_publishes_annotations(
        self, api_client: TestClient, db_session: Session, seeded_dataset, test_users
    ):
        admin = test_users["admin"]
        old_active_map = seeded_dataset["map_asset"]

        # Create new approved map
        new_map = ImperialMapAsset(
            id=uuid4(),
            content_scope=CONTENT_SCOPE_IMPERIAL,
            slug="dai-noi-aerial-v2",
            version=2,
            title_vi="Bản đồ không ảnh Đại Nội Huế v2",
            width_px=4096,
            height_px=3072,
            mime_type="image/webp",
            image_storage_key="imperial/maps/v2.webp",
            image_sha256="1" * 64,
            source_title="Nguồn viễn thám",
            credit_text="Lưu Niên",
            license_kind="educational_fair_use",
            license_status="approved",
            review_status="approved",
            is_active=False,
            created_by=admin.id,
            row_version=1,
        )
        # Add draft annotation on new map
        new_anno = ImperialMapAnnotation(
            id=uuid4(),
            content_scope=CONTENT_SCOPE_IMPERIAL,
            map_asset_id=new_map.id,
            site_id=seeded_dataset["site_thai_hoa"].id,
            shape_type="point",
            u=0.5,
            v=0.6,
            label="Thái Hòa v2",
            review_status="draft",
            created_by=admin.id,
            updated_by=admin.id,
            row_version=1,
        )
        db_session.add_all([new_map, new_anno])
        db_session.commit()

        # Publish new map
        pub_res = api_client.post(f"/api/v1/imperial/admin/maps/{new_map.id}/publish")
        assert pub_res.status_code == 200
        data = pub_res.json()
        assert data["is_active"] is True
        assert data["review_status"] == "published"
        assert data["row_version"] == 2

        # Verify old map is deactivated
        db_session.refresh(old_active_map)
        assert old_active_map.is_active is False

        # Verify draft annotation was published atomically
        db_session.refresh(new_anno)
        assert new_anno.review_status == "published"


# =========================================================================== #
# 5. Export and Import Dry-Run Diff & All-or-Nothing Transaction Tests
# =========================================================================== #
class TestAnnotationExportImport:
    """Test full JSON export, dry-run diffing, and all-or-nothing transactional import."""

    def test_export_annotations(self, api_client: TestClient, seeded_dataset):
        map_id = seeded_dataset["map_asset"].id
        res = api_client.get(f"/api/v1/imperial/admin/maps/{map_id}/export")
        assert res.status_code == 200
        data = res.json()
        assert data["schema_version"] == "imperial-annotations/1.0"
        assert data["content_scope"] == "STTT_IMPERIAL_CITY"
        assert "export_sha256" in data
        assert len(data["annotations"]) >= 1

    def test_import_dry_run_diff(self, api_client: TestClient, seeded_dataset):
        map_id = seeded_dataset["map_asset"].id
        site_the_to_mieu = seeded_dataset["site_the_to_mieu"]

        import_payload = {
            "schema_version": "imperial-annotations/1.0",
            "content_scope": "STTT_IMPERIAL_CITY",
            "annotations": [
                # 1. Existing site -> should be classified as updated
                {
                    "site_slug": "ngo-mon",
                    "u": 0.5005,
                    "v": 0.8525,
                    "label": "Ngọ Môn (Updated)",
                },
                # 2. New site -> should be classified as new
                {
                    "site_slug": site_the_to_mieu.slug,
                    "u": 0.3621,
                    "v": 0.7022,
                    "label": "Thế Tổ Miếu",
                },
                # 3. Invalid out-of-bounds site -> should be classified as invalid
                {
                    "site_slug": "dien-thai-hoa",
                    "u": 1.5,  # Out of bounds
                    "v": 0.5,
                },
            ],
        }

        # Dry run must not alter database
        res = api_client.post(
            f"/api/v1/imperial/admin/maps/{map_id}/import",
            params={"dry_run": "true"},
            json=import_payload,
        )
        assert res.status_code == 200
        data = res.json()
        assert data["dry_run"] is True
        assert data["valid"] is False  # item 3 was invalid
        assert data["summary"]["new_count"] == 1
        assert data["summary"]["updated_count"] == 1
        assert data["summary"]["invalid_count"] == 1

    def test_import_all_or_nothing_fails_on_invalid_items(self, api_client: TestClient, seeded_dataset):
        map_id = seeded_dataset["map_asset"].id

        payload_with_error = {
            "schema_version": "imperial-annotations/1.0",
            "content_scope": "STTT_IMPERIAL_CITY",
            "annotations": [
                {
                    "site_slug": "ngo-mon",
                    "u": 0.50,
                    "v": 0.85,
                },
                {
                    "site_slug": "invalid-site-not-existing",
                    "u": 0.3,
                    "v": 0.3,
                },
            ],
        }

        # dry_run=false with invalid items must reject with 422 and rollback
        res = api_client.post(
            f"/api/v1/imperial/admin/maps/{map_id}/import",
            params={"dry_run": "false"},
            json=payload_with_error,
        )
        assert res.status_code == 422
        assert res.json()["error"]["code"] == "IMPERIAL_IMPORT_ERROR"

    def test_import_all_or_nothing_success_commits(self, api_client: TestClient, seeded_dataset):
        map_id = seeded_dataset["map_asset"].id
        site_the_to_mieu = seeded_dataset["site_the_to_mieu"]

        clean_payload = {
            "schema_version": "imperial-annotations/1.0",
            "content_scope": "STTT_IMPERIAL_CITY",
            "annotations": [
                {
                    "site_slug": site_the_to_mieu.slug,
                    "u": 0.3621,
                    "v": 0.7022,
                    "label": "Thế Tổ Miếu",
                }
            ],
        }

        res = api_client.post(
            f"/api/v1/imperial/admin/maps/{map_id}/import",
            params={"dry_run": "false"},
            json=clean_payload,
        )
        assert res.status_code == 200
        assert res.json()["status"] == "success"
        assert res.json()["created_count"] == 1

        # Verify new annotation is now in database
        check_res = api_client.get(f"/api/v1/imperial/admin/maps/{map_id}/annotations")
        assert check_res.status_code == 200
        annos = check_res.json()
        assert any(a["site"]["slug"] == "the-to-mieu" for a in annos)
