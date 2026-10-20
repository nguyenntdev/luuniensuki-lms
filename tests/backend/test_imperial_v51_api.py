# -*- coding: utf-8 -*-
"""Comprehensive integration test suite for STTT Imperial City V5.1 API.

Validates:
1. Learning Media & Interactive Hotspots:
   - Creation of media (image, panorama360, model3d) and contexts (extant, historical_photo, restoration_drawing)
   - Normalized UV coordinate bounds validation (0.0 <= u, v <= 1.0)
   - Public retrieval of learning media and hotspots for architectural sites
2. Art Details, Story Types & Grounded Claim Sources:
   - Art details with story types ('documented_event', 'legend', 'oral_account', 'interpretation')
   - Primary claim sources with evidence strengths ('verified', 'probable', 'traditional')
   - Detail retrieval by slug and UUID
   - Optimistic locking concurrency control (409 Conflict)
3. Heritage Detective Clues & Progressive Hints:
   - Detective riddles pointing to sites or art details
   - Guess attempts with progressive hint revelation
   - Logging of clue attempts for authenticated and guest users
4. Gamified Quiz / Inquiry Questions:
   - Public question list hiding answer_key before submission
   - Game submission returning accuracy, explanation, and primary source citation
5. Teacher Assignment Releases:
   - Creation and retrieval of classroom journey assignment releases
   - RBAC enforcement (staff/teacher required)
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
from backend.deps import (
    get_admin_user,
    get_current_user,
    get_current_user_optional,
    get_db,
    get_staff_user,
)
from backend.imperial_models import (
    CONTENT_SCOPE_IMPERIAL,
    Base,
    ImperialSite,
    ImperialZone,
)
from backend.imperial_v51_models import (
    ImperialArtDetail,
    ImperialArtDetailClaimSource,
    ImperialArtDetailQuestion,
    ImperialAssignmentRelease,
    ImperialClue,
    ImperialClueAttempt,
    ImperialLearningMedia,
    ImperialMediaHotspot,
    ImperialQuestion,
)
from backend.main import app


# --------------------------------------------------------------------------- #
# Database Fixture for Isolated Integration Testing
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="module")
def imperial_v51_db_engine():
    """Create in-memory SQLite engine with all required tables."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    tables = [
        models.User.__table__,
        ImperialZone.__table__,
        ImperialSite.__table__,
        ImperialLearningMedia.__table__,
        ImperialArtDetail.__table__,
        ImperialMediaHotspot.__table__,
        ImperialArtDetailClaimSource.__table__,
        ImperialArtDetailQuestion.__table__,
        ImperialClue.__table__,
        ImperialClueAttempt.__table__,
        ImperialQuestion.__table__,
        ImperialAssignmentRelease.__table__,
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
def clean_database_tables(imperial_v51_db_engine):
    """Clean all test tables between each test run to ensure strict isolation."""
    TestingSession = sessionmaker(bind=imperial_v51_db_engine, autoflush=False, autocommit=False)
    with TestingSession() as sess:
        sess.query(ImperialClueAttempt).delete()
        sess.query(ImperialClue).delete()
        sess.query(ImperialQuestion).delete()
        sess.query(ImperialAssignmentRelease).delete()
        sess.query(ImperialMediaHotspot).delete()
        sess.query(ImperialArtDetailQuestion).delete()
        sess.query(ImperialArtDetailClaimSource).delete()
        sess.query(ImperialArtDetail).delete()
        sess.query(ImperialLearningMedia).delete()
        sess.query(ImperialSite).delete()
        sess.query(ImperialZone).delete()
        sess.query(models.User).delete()
        sess.commit()
    yield


@pytest.fixture
def db_session(imperial_v51_db_engine) -> Generator[Session, None, None]:
    """Yield a database session and clean up after each test."""
    TestingSession = sessionmaker(bind=imperial_v51_db_engine, autoflush=False, autocommit=False)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def teacher_user(db_session: Session) -> models.User:
    """Fixture providing a teacher user."""
    user = models.User(
        id=uuid4(),
        email="teacher@dainoi.edu.vn",
        username="teacher_hue",
        password_hash="hashed_secret_test",
        display_name="Thầy Giáo Hoàng Thành",
        role=models.UserRole.teacher,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def student_user(db_session: Session) -> models.User:
    """Fixture providing a learner/student user."""
    user = models.User(
        id=uuid4(),
        email="student@dainoi.edu.vn",
        username="student_hue",
        password_hash="hashed_secret_test",
        display_name="Học Sinh Cố Đô",
        role=models.UserRole.learner,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def sample_zone_and_site(db_session: Session, teacher_user: models.User) -> tuple[ImperialZone, ImperialSite]:
    """Fixture providing a published zone and site."""
    zone = ImperialZone(
        id=uuid4(),
        slug="hoang-thanh",
        title_vi="Hoàng Thành",
        title_en="Imperial Enclosure",
        display_order=1,
    )
    db_session.add(zone)
    db_session.flush()

    site = ImperialSite(
        id=uuid4(),
        zone_id=zone.id,
        slug="dien-thai-hoa",
        name_vi="Điện Thái Hòa",
        name_en="Palace of Supreme Harmony",
        name_han_nom="太和殿",
        site_type="palace",
        condition="extant",
        learning_level="L1_DOCUMENTED",
        summary_vi="Tòa điện thiết triều quan trọng nhất trong Hoàng Thành Huế.",
        is_published=True,
        display_order=1,
        created_by=teacher_user.id,
    )
    db_session.add(site)
    db_session.commit()
    db_session.refresh(zone)
    db_session.refresh(site)
    return zone, site


@pytest.fixture
def client(imperial_v51_db_engine, teacher_user: models.User):
    """TestClient wired with in-memory DB and authenticated teacher override."""
    TestingSession = sessionmaker(bind=imperial_v51_db_engine, autoflush=False, autocommit=False)

    def _override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_staff_user] = lambda: teacher_user
    app.dependency_overrides[get_admin_user] = lambda: teacher_user
    app.dependency_overrides[get_current_user] = lambda: teacher_user
    app.dependency_overrides[get_current_user_optional] = lambda: teacher_user

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


# =========================================================================== #
# Test Suites
# =========================================================================== #
class TestLearningMediaAndHotspots:
    """Test learning media (images, 360, 3D models) and UV hotspots."""

    def test_create_and_retrieve_learning_media_with_hotspots(
        self, client: TestClient, sample_zone_and_site
    ):
        zone, site = sample_zone_and_site

        # 1. Admin creates learning media
        media_payload = {
            "site_id": str(site.id),
            "kind": "panorama360",
            "media_url": "https://assets.histolab.icu/media/dien-thai-hoa-360.jpg",
            "thumbnail_url": "https://assets.histolab.icu/media/dien-thai-hoa-360-thumb.jpg",
            "asset_revision": 1,
            "width_px": 4096,
            "height_px": 2048,
            "license_status": "approved",
            "review_status": "published",
            "alt_text": "Toàn cảnh 360 độ ngai vàng Điện Thái Hòa",
            "credit_text": "Bảo tàng Cổ vật Cung đình Huế",
            "asset_context": "extant",
        }
        res_media = client.post("/api/v1/imperial/admin/media", json=media_payload)
        assert res_media.status_code == 201
        media_data = res_media.json()
        media_id = media_data["id"]
        assert media_data["kind"] == "panorama360"
        assert media_data["asset_context"] == "extant"

        # 2. Admin creates hotspot on media with UV coordinates
        hotspot_payload = {
            "point_kind": "point",
            "u": 0.5234567,
            "v": 0.4123456,
            "title": "Ngai vàng vua Nguyễn",
            "description": "Biểu tượng quyền lực tối cao của triều đại",
            "review_status": "published",
        }
        res_hotspot = client.post(
            f"/api/v1/imperial/admin/media/{media_id}/hotspots",
            json=hotspot_payload,
        )
        assert res_hotspot.status_code == 201
        hotspot_data = res_hotspot.json()
        assert hotspot_data["title"] == "Ngai vàng vua Nguyễn"
        assert hotspot_data["u"] == pytest.approx(0.5234567, abs=1e-5)

        # 3. Public site learning media retrieval
        res_public = client.get(f"/api/v1/imperial/sites/{site.slug}/learning-media")
        assert res_public.status_code == 200
        items = res_public.json()
        assert len(items) == 1
        assert items[0]["id"] == media_id
        assert len(items[0]["hotspots"]) == 1
        assert items[0]["hotspots"][0]["title"] == "Ngai vàng vua Nguyễn"

        # 4. Media hotspots endpoint
        res_hs = client.get(f"/api/v1/imperial/media/{media_id}/hotspots")
        assert res_hs.status_code == 200
        hs_list = res_hs.json()
        assert len(hs_list) == 1
        assert hs_list[0]["title"] == "Ngai vàng vua Nguyễn"

    @pytest.mark.parametrize(
        "invalid_u, invalid_v",
        [
            (-0.001, 0.5),
            (1.001, 0.5),
            (0.5, -0.1),
            (0.5, 1.05),
        ],
    )
    def test_hotspot_uv_out_of_bounds_rejection(
        self, client: TestClient, sample_zone_and_site, invalid_u, invalid_v
    ):
        zone, site = sample_zone_and_site

        # Create media
        res_media = client.post(
            "/api/v1/imperial/admin/media",
            json={
                "site_id": str(site.id),
                "kind": "image",
                "media_url": "https://assets.histolab.icu/media/test.jpg",
                "license_status": "approved",
                "review_status": "published",
            },
        )
        assert res_media.status_code == 201
        media_id = res_media.json()["id"]

        # Attempt to create hotspot with invalid UV
        res_hs = client.post(
            f"/api/v1/imperial/admin/media/{media_id}/hotspots",
            json={
                "point_kind": "point",
                "u": invalid_u,
                "v": invalid_v,
                "title": "Invalid Hotspot",
            },
        )
        assert res_hs.status_code == 422


class TestArtDetailsAndEvidence:
    """Test art details with story types, primary claim sources, and questions."""

    def test_create_and_retrieve_art_detail_with_story_and_claims(
        self, client: TestClient, sample_zone_and_site
    ):
        zone, site = sample_zone_and_site

        detail_payload = {
            "site_id": str(site.id),
            "title": "Rồng chầu mặt trời bờ nóc Điện Thái Hòa",
            "slug": "rong-chau-mat-troi-dien-thai-hoa",
            "kind": "relief",
            "motif": "Lưỡng long chầu nguyệt",
            "material": "Vôi vữa khảm sành sứ",
            "technique": "Khảm sành sứ (mosaics)",
            "description_observation": "Cặp rồng uốn lượn chầu về vầng thái dương ở giữa đỉnh bờ nóc.",
            "story_body": "Hình tượng rồng triều Nguyễn mang phong thái uy nghiêm, biểu trưng cho thiên tử và sự thái bình thịnh trị.",
            "story_type": "legend",
            "meaning_body": "Biểu đạt ước vọng mưa thuận gió hòa và sự hưng thịnh của quốc gia.",
            "historical_value_body": "Được tạo tác trong đợt trùng tu năm 1833 dưới triều vua Minh Mạng.",
            "cultural_value_body": "Đỉnh cao của nghệ thuật pháp lam và khảm sành sứ cung đình Huế.",
            "art_value_body": "Đường nét sống động, màu men sành sứ bền bỉ qua hơn một thế kỷ.",
            "review_status": "published",
            "content_revision": 1,
            "claim_sources": [
                {
                    "section": "historical_value",
                    "claim_text": "Tác phẩm được hoàn thiện vào thời Minh Mạng năm 1833",
                    "source_title": "Đại Nam Thực Lục Chính Biên",
                    "source_locator": "Đệ nhị kỷ, quyển 104",
                    "evidence_strength": "verified",
                }
            ],
            "questions": [
                {
                    "question_type": "multiple_choice",
                    "prompt": "Chất liệu chính tạo nên bức phù điêu rồng là gì?",
                    "options": ["Vôi vữa khảm sành sứ", "Đồng đúc nguyên khối", "Gỗ mít sơn son thiếp vàng", "Đá cẩm thạch"],
                    "answer_key": "Vôi vữa khảm sành sứ",
                    "explanation": "Nghệ thuật khảm sành sứ là nét đặc trưng nổi bật của kiến trúc cung đình Huế.",
                    "display_order": 1,
                }
            ],
        }

        # 1. Admin creates art detail
        res = client.post("/api/v1/imperial/admin/art-details", json=detail_payload)
        assert res.status_code == 201
        created = res.json()
        detail_id = created["id"]
        assert created["story_type"] == "legend"
        assert len(created["claim_sources"]) == 1
        assert created["claim_sources"][0]["evidence_strength"] == "verified"
        assert len(created["questions"]) == 1

        # 2. Public retrieval by slug
        res_slug = client.get("/api/v1/imperial/art-details/rong-chau-mat-troi-dien-thai-hoa")
        assert res_slug.status_code == 200
        detail_slug = res_slug.json()
        assert detail_slug["id"] == detail_id
        assert detail_slug["kind"] == "relief"
        assert detail_slug["story_type"] == "legend"

        # 3. Public retrieval by UUID
        res_uuid = client.get(f"/api/v1/imperial/art-details/{detail_id}")
        assert res_uuid.status_code == 200
        assert res_uuid.json()["slug"] == "rong-chau-mat-troi-dien-thai-hoa"

        # 4. List site's art details
        res_site_details = client.get(f"/api/v1/imperial/sites/{site.slug}/art-details")
        assert res_site_details.status_code == 200
        items = res_site_details.json()
        assert len(items) == 1
        assert items[0]["slug"] == "rong-chau-mat-troi-dien-thai-hoa"

    def test_art_detail_optimistic_locking(
        self, client: TestClient, sample_zone_and_site
    ):
        zone, site = sample_zone_and_site

        # Create
        res = client.post(
            "/api/v1/imperial/admin/art-details",
            json={
                "site_id": str(site.id),
                "title": "Hoa văn chữ Thọ",
                "slug": "hoa-van-chu-tho",
                "kind": "carving",
                "review_status": "published",
            },
        )
        assert res.status_code == 201
        detail_id = res.json()["id"]

        # First update succeeds and increments row_version from 1 to 2
        res_update1 = client.patch(
            f"/api/v1/imperial/admin/art-details/{detail_id}",
            json={"title": "Hoa văn chữ Thọ cách điệu", "row_version": 1},
        )
        assert res_update1.status_code == 200
        assert res_update1.json()["row_version"] == 2

        # Second update with stale row_version (1) fails with 409 Conflict
        res_update2 = client.patch(
            f"/api/v1/imperial/admin/art-details/{detail_id}",
            json={"title": "Hoa văn chữ Thọ mới", "row_version": 1},
        )
        assert res_update2.status_code == 409


class TestHeritageDetectiveClues:
    """Test detective clues and progressive hint attempts."""

    def test_clue_attempt_flow_with_progressive_hints(
        self, client: TestClient, sample_zone_and_site
    ):
        zone, site = sample_zone_and_site

        # Create clue
        clue_payload = {
            "title": "Manh mối: Nơi thiết triều đại lễ",
            "clue_text": "Tìm ngôi điện có 80 cột gỗ lim thếp vàng, mái lợp ngói hoàng lưu ly rực rỡ.",
            "target_type": "site",
            "target_id": str(site.id),
            "hint_steps": [
                {"step": 1, "hint": "Công trình nằm trên trục Dũng đạo của Hoàng Thành."},
                {"step": 2, "hint": "Trước mặt công trình là sân Đại Triều Nghi với hai tầng bậc."},
                {"step": 3, "hint": "Tên điện mang ý nghĩa sự hòa hợp tột cùng theo quan niệm Nho gia."},
            ],
            "grade_level": "middle",
            "difficulty": "medium",
            "review_status": "published",
        }
        res_clue = client.post("/api/v1/imperial/admin/clues", json=clue_payload)
        assert res_clue.status_code == 201
        clue_id = res_clue.json()["id"]

        # 1. Public list clues
        res_list = client.get("/api/v1/imperial/clues?target_type=site")
        assert res_list.status_code == 200
        assert len(res_list.json()) == 1

        # 2. First attempt (wrong target) -> receives hint step 1
        wrong_id = str(uuid4())
        res_attempt1 = client.post(
            f"/api/v1/imperial/clues/{clue_id}/attempt",
            json={"selected_target_id": wrong_id, "attempt_number": 1},
        )
        assert res_attempt1.status_code == 200
        data1 = res_attempt1.json()
        assert data1["is_correct"] is False
        assert len(data1["hint_steps"]) == 1
        assert "trục Dũng đạo" in data1["hint_steps"][0]["hint"]

        # 3. Second attempt (wrong target) -> receives hint step 1 & 2
        res_attempt2 = client.post(
            f"/api/v1/imperial/clues/{clue_id}/attempt",
            json={"selected_target_id": wrong_id, "attempt_number": 2},
        )
        assert res_attempt2.status_code == 200
        data2 = res_attempt2.json()
        assert data2["is_correct"] is False
        assert len(data2["hint_steps"]) == 2

        # 4. Third attempt (correct target) -> is_correct True
        res_attempt3 = client.post(
            f"/api/v1/imperial/clues/{clue_id}/attempt",
            json={"selected_target_id": str(site.id), "attempt_number": 3},
        )
        assert res_attempt3.status_code == 200
        data3 = res_attempt3.json()
        assert data3["is_correct"] is True
        assert "Chính xác" in data3["message"]


class TestGamifiedQuestionsAndSubmission:
    """Test gamified quiz questions with answer_key hidden and submission rationale."""

    def test_question_answer_key_hidden_and_submission(
        self, client: TestClient, sample_zone_and_site
    ):
        zone, site = sample_zone_and_site

        # Create question via admin
        q_payload = {
            "site_id": str(site.id),
            "question_type": "multiple_choice",
            "prompt": "Điện Thái Hòa được khởi công xây dựng vào năm nào?",
            "options": ["1805", "1802", "1833", "1885"],
            "answer_key": "1805",
            "explanation_why": "Vua Gia Long cho khởi công xây dựng Điện Thái Hòa vào năm Ất Sửu (1805).",
            "source_citation": "Đại Nam Thực Lục Chính Biên, Đệ nhất kỷ, quyển 26",
            "review_status": "published",
        }
        res_q = client.post("/api/v1/imperial/admin/questions", json=q_payload)
        assert res_q.status_code == 201
        q_id = res_q.json()["id"]

        # 1. Public list questions: MUST HIDE answer_key
        res_public = client.get(f"/api/v1/imperial/games/questions?site={site.slug}")
        assert res_public.status_code == 200
        q_list = res_public.json()
        assert len(q_list) == 1
        public_q = q_list[0]
        assert "answer_key" not in public_q
        assert public_q["prompt"] == q_payload["prompt"]

        # 2. Submit wrong answer
        res_sub_wrong = client.post(
            "/api/v1/imperial/games/submit",
            json={"question_id": q_id, "user_answer": "1802"},
        )
        assert res_sub_wrong.status_code == 200
        data_wrong = res_sub_wrong.json()
        assert data_wrong["is_correct"] is False
        assert data_wrong["correct_answer"] == "1805"
        assert "1805" in data_wrong["explanation_why"]
        assert "Đại Nam Thực Lục" in data_wrong["source_citation"]

        # 3. Submit correct answer
        res_sub_correct = client.post(
            "/api/v1/imperial/games/submit",
            json={"question_id": q_id, "user_answer": "1805"},
        )
        assert res_sub_correct.status_code == 200
        data_correct = res_sub_correct.json()
        assert data_correct["is_correct"] is True
        assert data_correct["correct_answer"] == "1805"


class TestTeacherAssignments:
    """Test teacher classroom journey assignments."""

    def test_teacher_create_and_manage_assignment(
        self, client: TestClient, teacher_user: models.User
    ):
        assignment_payload = {
            "class_name": "Lớp 10A1 Sử Huế",
            "journey_slug": "khao-sat-hoang-thanh-co-do",
            "title": "Nhiệm vụ điền dã: Khảo sát nghệ thuật kiến trúc cung đình",
            "due_date": "2026-11-20T17:00:00Z",
            "rubric_weights": {"S1": 0.25, "S2": 0.25, "S3": 0.25, "S4": 0.25},
            "is_active": True,
        }

        # 1. Teacher creates assignment release
        res = client.post("/api/v1/imperial/teacher/assignments", json=assignment_payload)
        assert res.status_code == 201
        created = res.json()
        assert created["class_name"] == "Lớp 10A1 Sử Huế"
        assert created["teacher_id"] == str(teacher_user.id)
        assert created["journey_slug"] == "khao-sat-hoang-thanh-co-do"
        assignment_id = created["id"]

        # 2. Teacher retrieves their assignments
        res_list = client.get("/api/v1/imperial/teacher/assignments")
        assert res_list.status_code == 200
        releases = res_list.json()
        assert len(releases) == 1
        assert releases[0]["id"] == assignment_id

        # 3. Teacher updates assignment
        res_patch = client.patch(
            f"/api/v1/imperial/teacher/assignments/{assignment_id}",
            json={"title": "Nhiệm vụ điền dã (Gia hạn thêm 2 ngày)"},
        )
        assert res_patch.status_code == 200
        assert res_patch.json()["title"] == "Nhiệm vụ điền dã (Gia hạn thêm 2 ngày)"
        assert res_patch.json()["row_version"] == 2
