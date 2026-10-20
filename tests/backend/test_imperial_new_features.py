# -*- coding: utf-8 -*-
"""Integration test suite for STTT Imperial City V5.2 new features.
Specs:
- STTT-SPEC-AUDIO-PASSPORT-002: Heritage Audio Guide API & Digital Passport System
- STTT-SPEC-PWA-PRINT-001: PWA Offline Batch Synchronization

Verifies:
1. GET /api/v1/imperial/audio-guides returns valid catalog (16 monuments, total duration, transcripts).
2. GET /api/v1/imperial/sites/{slug}/audio returns script text, duration, and timed transcripts.
3. POST /api/v1/imperial/submissions/batch-sync processes batch items and returns proper sync statistics.
4. Strict zero forbidden legacy terms across all new JSON, Python, and TypeScript files.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Generator
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.sql.elements import TextClause

import backend.models as models
from backend.apischemas.imperial_audio import ImperialAudioCatalogOut, ImperialAudioGuideOut
from backend.apischemas.imperial_sync import (
    ImperialBatchSyncRequest,
    ImperialBatchSyncResponse,
)
from backend.deps import get_current_user, get_db
from backend.imperial_models import (
    CONTENT_SCOPE_IMPERIAL,
    Base,
    ImperialActivity,
    ImperialSite,
    ImperialSubmission,
    ImperialZone,
)
from backend.main import app
from backend.models import User, UserRole
from scripts.imperial.audit_no_legacy_content import FORBIDDEN_TERMS, scan_file_for_violations

REPO_ROOT = Path(__file__).resolve().parents[2]


# --------------------------------------------------------------------------- #
# Database Fixture for Isolated Testing
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="module")
def new_features_db_engine():
    """Create isolated in-memory SQLite engine with imperial tables."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    tables = [
        models.User.__table__,
        ImperialZone.__table__,
        ImperialSite.__table__,
        ImperialActivity.__table__,
        ImperialSubmission.__table__,
    ]
    # Strip PostgreSQL specific defaults for SQLite compatibility
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
def clean_database(new_features_db_engine):
    """Clean tables between each test run to ensure strict isolation."""
    TestingSession = sessionmaker(bind=new_features_db_engine, autoflush=False, autocommit=False)
    with TestingSession() as sess:
        sess.query(ImperialSubmission).delete()
        sess.query(ImperialActivity).delete()
        sess.query(ImperialSite).delete()
        sess.query(ImperialZone).delete()
        sess.query(models.User).delete()
        sess.commit()
    yield


@pytest.fixture
def db_session(new_features_db_engine) -> Generator[Session, None, None]:
    """Yield a database session and clean up after each test."""
    TestingSession = sessionmaker(bind=new_features_db_engine, autoflush=False, autocommit=False)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def test_users(db_session: Session) -> dict[str, models.User]:
    """Create test users: authenticated learner and unauthenticated/guest user."""
    learner_id = uuid4()
    learner_user = models.User(
        id=learner_id,
        username=f"learner_{learner_id.hex[:6]}",
        email=f"learner_{learner_id.hex[:6]}@example.com",
        display_name=f"Learner {learner_id.hex[:6]}",
        password_hash="mock_hash",
        role=models.UserRole.learner,
    )
    guest_id = uuid4()
    guest_user = models.User(
        id=guest_id,
        username=f"guest_{guest_id.hex[:6]}",
        email=f"guest_{guest_id.hex[:6]}@example.com",
        display_name=f"Guest {guest_id.hex[:6]}",
        password_hash="mock_hash",
        role=models.UserRole.guest,
    )
    db_session.add_all([learner_user, guest_user])
    db_session.commit()
    return {"learner": learner_user, "guest": guest_user}


@pytest.fixture
def seeded_activities(db_session: Session, test_users: dict[str, models.User]) -> list[ImperialActivity]:
    """Seed test zone, site, and activities under CONTENT_SCOPE_IMPERIAL."""
    user = test_users["learner"]
    zone = ImperialZone(
        id=uuid4(),
        content_scope=CONTENT_SCOPE_IMPERIAL,
        slug="central-axis",
        title_vi="Trục trung tâm",
        title_en="Central Axis",
        description="Trục nghi lễ chính đạo",
        display_order=1,
    )
    db_session.add(zone)
    db_session.flush()

    site = ImperialSite(
        id=uuid4(),
        content_scope=CONTENT_SCOPE_IMPERIAL,
        zone_id=zone.id,
        slug="ngo-mon",
        name_vi="Ngọ Môn",
        name_en="Meridian Gate",
        name_han_nom="午門",
        learning_level="L2_LEARNING_READY",
        condition="extant",
        construction_year=1833,
        summary_vi="Cổng chính phía nam Hoàng Thành Huế",
        is_published=True,
        created_by=user.id,
        updated_by=user.id,
    )
    db_session.add(site)
    db_session.flush()

    act1 = ImperialActivity(
        id=uuid4(),
        content_scope=CONTENT_SCOPE_IMPERIAL,
        site_id=site.id,
        activity_type="mee_inquiry",
        title="Khảo sát cấu trúc Ngũ Môn",
        instructions="Vì sao Ngọ Môn có năm cửa ngõ?",
        max_points=100,
        is_active=True,
    )
    act2 = ImperialActivity(
        id=uuid4(),
        content_scope=CONTENT_SCOPE_IMPERIAL,
        site_id=site.id,
        activity_type="mee_inquiry",
        title="Khảo sát Lầu Ngũ Phụng",
        instructions="Phân tích kết cấu 100 cột và chức năng lễ nghi của Lầu Ngũ Phụng.",
        max_points=100,
        is_active=True,
    )
    db_session.add_all([act1, act2])
    db_session.commit()
    return [act1, act2]


@pytest.fixture
def api_client(db_session: Session, test_users: dict[str, models.User]) -> Generator[TestClient, None, None]:
    """Provide TestClient with dependency overrides defaulting to learner user."""
    def _override_db():
        yield db_session

    def _override_user():
        return test_users["learner"]

    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_current_user] = _override_user

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


# =========================================================================== #
# 1. GET /api/v1/imperial/audio-guides (Catalog Endpoint)
# =========================================================================== #
def test_get_audio_guides_catalog(api_client: TestClient):
    """Verify GET /api/v1/imperial/audio-guides returns a valid catalog."""
    response = api_client.get("/api/v1/imperial/audio-guides")
    assert response.status_code == 200, response.text

    data = response.json()
    assert data["content_scope"] == "STTT_IMPERIAL_CITY_AUDIO_GUIDES"
    assert data["version"] == "1.0.0"
    assert data["total_guides"] == 16, f"Expected 16 guides, got {data['total_guides']}"
    assert data["total_duration_seconds"] > 0
    assert len(data["tracks"]) == 16

    # Verify each track conforms to the ImperialAudioGuideOut schema
    seen_slugs = set()
    for track in data["tracks"]:
        slug = track["monument_slug"]
        assert slug, "Missing monument_slug"
        assert slug not in seen_slugs, f"Duplicate monument_slug: {slug}"
        seen_slugs.add(slug)

        assert track["title_vi"], f"Missing title_vi for {slug}"
        assert 60 <= track["duration_seconds"] <= 300, (
            f"Duration {track['duration_seconds']}s outside target range (60-300s) for {slug}"
        )
        assert track["audio_url"].startswith("/assets/imperial/audio/")
        assert track["audio_url"].endswith(".mp3")
        assert len(track["script_text"]) >= 20, f"Script text too short for {slug}"
        assert len(track["timed_transcript"]) >= 1, f"Missing timed transcript cues for {slug}"

        # Verify time-coding structure of cues
        for cue in track["timed_transcript"]:
            assert cue["time_sec"] >= 0.0
            assert cue["text"], f"Empty cue text in track {slug}"


# =========================================================================== #
# 2. GET /api/v1/imperial/sites/{slug}/audio (Individual Track Endpoint)
# =========================================================================== #
@pytest.mark.parametrize(
    "site_slug,expected_title",
    [
        ("ngo-mon", "Ngọ Môn"),
        ("dien-thai-hoa", "Điện Thái Hòa"),
        ("the-to-mieu", "Thế Tổ Miếu"),
        ("thai-binh-lau", "Thái Bình Lâu"),
        ("cung-dien-tho", "Cung Diên Thọ"),
    ],
)
def test_get_site_audio_guide_by_slug(api_client: TestClient, site_slug: str, expected_title: str):
    """Verify GET /api/v1/imperial/sites/{slug}/audio returns script, duration, and timed transcripts."""
    response = api_client.get(f"/api/v1/imperial/sites/{site_slug}/audio")
    assert response.status_code == 200, response.text

    track = response.json()
    assert track["monument_slug"] == site_slug
    assert track["title_vi"] == expected_title
    assert 60 <= track["duration_seconds"] <= 300
    assert track["audio_url"] == f"/assets/imperial/audio/{site_slug}.mp3"
    assert len(track["script_text"]) >= 50
    assert len(track["timed_transcript"]) >= 3

    # Check cue continuity
    for cue in track["timed_transcript"]:
        assert cue["time_sec"] >= 0.0
        assert len(cue["text"].strip()) > 0


def test_get_site_audio_guide_not_found(api_client: TestClient):
    """Verify GET /api/v1/imperial/sites/{slug}/audio returns 404 for non-existent monument."""
    response = api_client.get("/api/v1/imperial/sites/unknown-monument-xyz/audio")
    assert response.status_code == 404
    payload = response.json()
    # Support both custom error envelope and standard HTTPException
    if "error" in payload:
        assert payload["error"]["code"] == "AUDIO_GUIDE_NOT_FOUND"
    else:
        assert "not found" in payload.get("detail", "").lower()


# =========================================================================== #
# 3. POST /api/v1/imperial/submissions/batch-sync (PWA Offline Sync)
# =========================================================================== #
def test_batch_sync_submissions_success(
    api_client: TestClient,
    db_session: Session,
    seeded_activities: list[ImperialActivity],
    test_users: dict[str, models.User],
):
    """Verify POST /api/v1/imperial/submissions/batch-sync processes batch items and returns sync stats."""
    act1, act2 = seeded_activities
    client_ts1 = "2026-10-16T09:00:00Z"
    client_ts2 = "2026-10-16T09:15:00Z"

    payload = {
        "items": [
            {
                "id": "queued-item-01",
                "activity_id": str(act1.id),
                "answer_text": "Cấu trúc 5 cửa ngõ thể hiện tư tưởng trung quân thời Minh Mạng.",
                "evidence_refs": [{"source": "Đại Nam Thực Lục", "detail": "Quyển 14"}],
                "client_timestamp": client_ts1,
            },
            {
                "id": "queued-item-02",
                "activity_id": str(act2.id),
                "answer_text": "Lầu Ngũ Phụng có 100 cột gỗ lim chia làm 5 mái lợp ngói lưu ly.",
                "evidence_refs": [{"source": "Khảo sát thực địa", "detail": "Đếm cột thực tế"}],
                "client_timestamp": client_ts2,
            },
        ]
    }

    response = api_client.post("/api/v1/imperial/submissions/batch-sync", json=payload)
    assert response.status_code == 200, response.text

    result = response.json()
    assert result["synced_count"] == 2
    assert result["failed_count"] == 0
    assert len(result["results"]) == 2

    r1 = result["results"][0]
    assert r1["client_id"] == "queued-item-01"
    assert r1["status"] == "synced"
    assert r1["server_id"] is not None
    assert r1["error"] is None

    r2 = result["results"][1]
    assert r2["client_id"] == "queued-item-02"
    assert r2["status"] == "synced"
    assert r2["server_id"] is not None
    assert r2["error"] is None

    # Verify persistence in database
    subs = db_session.query(ImperialSubmission).filter(
        ImperialSubmission.student_id == test_users["learner"].id
    ).all()
    assert len(subs) == 2


def test_batch_sync_idempotency_acknowledgment(
    api_client: TestClient,
    db_session: Session,
    seeded_activities: list[ImperialActivity],
    test_users: dict[str, models.User],
):
    """Verify that re-syncing duplicate items returns status='acknowledged' without duplicating rows."""
    act1 = seeded_activities[0]
    client_ts = "2026-10-16T09:00:00Z"
    payload = {
        "items": [
            {
                "id": "duplicate-queued-item",
                "activity_id": str(act1.id),
                "answer_text": "Cửa Ngọ Môn chính giữa chỉ dành riêng cho thiên tử.",
                "evidence_refs": [],
                "client_timestamp": client_ts,
            }
        ]
    }

    # First sync
    res1 = api_client.post("/api/v1/imperial/submissions/batch-sync", json=payload)
    assert res1.status_code == 200
    assert res1.json()["results"][0]["status"] == "synced"

    # Second sync of the same content
    res2 = api_client.post("/api/v1/imperial/submissions/batch-sync", json=payload)
    assert res2.status_code == 200
    r2 = res2.json()
    assert r2["synced_count"] == 1
    assert r2["failed_count"] == 0
    assert r2["results"][0]["status"] == "acknowledged"

    # Total rows in DB remains 1
    total = db_session.query(ImperialSubmission).filter(
        ImperialSubmission.activity_id == act1.id,
        ImperialSubmission.student_id == test_users["learner"].id,
    ).count()
    assert total == 1


def test_batch_sync_graceful_handling_of_invalid_items(
    api_client: TestClient,
    seeded_activities: list[ImperialActivity],
):
    """Verify invalid activity UUID reports status='failed' while valid item succeeds."""
    act1 = seeded_activities[0]
    payload = {
        "items": [
            {
                "id": "valid-item",
                "activity_id": str(act1.id),
                "answer_text": "Bài làm hợp lệ tại Ngọ Môn.",
                "evidence_refs": [],
                "client_timestamp": "2026-10-16T10:00:00Z",
            },
            {
                "id": "invalid-item",
                "activity_id": str(uuid4()),  # Non-existent activity
                "answer_text": "Bài làm cho hoạt động không tồn tại.",
                "evidence_refs": [],
                "client_timestamp": "2026-10-16T10:05:00Z",
            },
        ]
    }

    response = api_client.post("/api/v1/imperial/submissions/batch-sync", json=payload)
    assert response.status_code == 200

    result = response.json()
    assert result["synced_count"] == 1
    assert result["failed_count"] == 1

    valid_res = [r for r in result["results"] if r["client_id"] == "valid-item"][0]
    assert valid_res["status"] == "synced"

    invalid_res = [r for r in result["results"] if r["client_id"] == "invalid-item"][0]
    assert invalid_res["status"] == "failed"
    assert "not found" in invalid_res["error"].lower()


def test_batch_sync_guest_role_forbidden(
    db_session: Session,
    seeded_activities: list[ImperialActivity],
    test_users: dict[str, models.User],
):
    """Verify guest role is rejected with 403 Forbidden."""
    def _override_db():
        yield db_session

    def _override_guest():
        return test_users["guest"]

    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_current_user] = _override_guest

    with TestClient(app) as client:
        payload = {
            "items": [
                {
                    "id": "guest-item",
                    "activity_id": str(seeded_activities[0].id),
                    "answer_text": "Guest submission",
                    "client_timestamp": "2026-10-16T10:00:00Z",
                }
            ]
        }
        res = client.post("/api/v1/imperial/submissions/batch-sync", json=payload)
        assert res.status_code == 403
        assert "learner role or higher required" in res.text.lower()

    app.dependency_overrides.clear()


# =========================================================================== #
# 4. DATA ISOLATION: ZERO FORBIDDEN LEGACY TERMS
# =========================================================================== #
def test_zero_forbidden_legacy_terms_across_new_features():
    """Verify zero forbidden legacy terms exist across all new JSON, Python, and TypeScript files."""
    new_files_to_check = [
        REPO_ROOT / "data" / "imperial" / "audio_guides.json",
        REPO_ROOT / "backend" / "services" / "imperial_audio.py",
        REPO_ROOT / "backend" / "services" / "imperial_sync.py",
        REPO_ROOT / "backend" / "apischemas" / "imperial_audio.py",
        REPO_ROOT / "backend" / "apischemas" / "imperial_sync.py",
        REPO_ROOT / "tests" / "backend" / "test_imperial_new_features.py",
        REPO_ROOT / "frontend" / "src" / "lib" / "imperial" / "passport-logic.ts",
        REPO_ROOT / "frontend" / "src" / "lib" / "imperial" / "passport-logic.test.ts",
    ]

    violations = []
    for f in new_files_to_check:
        assert f.exists(), f"File {f} not found"
        file_violations = scan_file_for_violations(f)
        violations.extend(file_violations)

    assert violations == [], (
        f"Found {len(violations)} forbidden legacy term violation(s) in new features:\n"
        + "\n".join(f"  {v.file_path}:{v.line_number} -> {v.matched_term}" for v in violations)
    )


def test_forbidden_terms_crawler_catches_violations(tmp_path: Path):
    """Positive control ensuring the crawler reliably detects any forbidden terms."""
    clean_sample = tmp_path / "clean_sample.json"
    clean_sample.write_text(json.dumps({"site": "Ngọ Môn", "reign": "Minh Mạng"}), encoding="utf-8")
    assert scan_file_for_violations(clean_sample) == []

    for term in FORBIDDEN_TERMS[:5]:
        safe_name = term.replace(" ", "_")
        dirty_sample = tmp_path / f"dirty_{safe_name}.txt"
        dirty_sample.write_text(f"Line 1: clean\nLine 2: Leaked {term} here\nLine 3: clean", encoding="utf-8")
        found = scan_file_for_violations(dirty_sample)
        assert len(found) >= 1, f"Failed to catch: {term}"
        assert found[0].matched_term == term
        assert found[0].line_number == 2


def test_imperial_heritage_images_service():
    """Verify service functions in backend.services.imperial_heritage_images."""
    from backend.services import imperial_heritage_images

    # 1. List all images
    all_images = imperial_heritage_images.list_heritage_images()
    assert isinstance(all_images, list)
    if all_images:
        first_img = all_images[0]
        assert "id" in first_img
        assert "src" in first_img

        # 2. Get image by ID
        img_id = first_img["id"]
        retrieved = imperial_heritage_images.get_image_by_id(img_id)
        assert retrieved is not None
        assert retrieved["id"] == img_id

        # 3. Filter by site_slug
        site_slug = first_img.get("site_slug")
        if site_slug:
            filtered = imperial_heritage_images.list_heritage_images(site_slug=site_slug)
            assert all(img.get("site_slug") == site_slug for img in filtered)

            # 4. Get primary image for site
            primary = imperial_heritage_images.get_primary_image_for_site(site_slug)
            assert primary is not None
            assert primary.get("site_slug") == site_slug

    # 5. Non-existent image ID
    assert imperial_heritage_images.get_image_by_id("non-existent-image-xyz") is None
    # 6. Non-existent site primary image
    assert imperial_heritage_images.get_primary_image_for_site("non-existent-site-xyz") is None

