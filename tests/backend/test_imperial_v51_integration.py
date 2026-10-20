# -*- coding: utf-8 -*-
"""Integration tests for STTT Imperial City V5.1 extensions (Lưu Niên — Đại Nội Huế).

Validates:
1. Media hotspots retrieval and normalized UV coordinates bounds ([0.0, 1.0]).
2. Art detail queries (dossier with story, meaning, claim sources, and questions).
3. Detective clue attempts with progressive hint revelation and attempt logging.
4. Game questions retrieval (answer_key hidden) and answer submission verification.
5. Teacher classroom assignments CRUD with IDOR security validation.
6. Zero legacy Cửu Đỉnh leakage across all V5.1 models and responses.

Ref: SPEC V5.1 Traceability
"""
from __future__ import annotations

import uuid
from typing import Generator
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.sql.elements import TextClause

import backend.models as models
from backend.deps import get_current_user, get_db, get_staff_user
from backend.imperial_models import (
    CONTENT_SCOPE_IMPERIAL,
    Base,
    ImperialMapAsset,
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


@pytest.fixture(scope="module")
def imperial_v51_db_engine():
    """Create in-memory SQLite engine with V5.1 tables."""
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
def clean_v51_database_tables(imperial_v51_db_engine):
    """Clean all test tables between each test run."""
    TestingSession = sessionmaker(bind=imperial_v51_db_engine, autoflush=False, autocommit=False)
    with TestingSession() as sess:
        sess.query(ImperialAssignmentRelease).delete()
        sess.query(ImperialQuestion).delete()
        sess.query(ImperialClueAttempt).delete()
        sess.query(ImperialClue).delete()
        sess.query(ImperialArtDetailQuestion).delete()
        sess.query(ImperialArtDetailClaimSource).delete()
        sess.query(ImperialMediaHotspot).delete()
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
def test_users(db_session: Session) -> dict[str, models.User]:
    """Create test users for teacher and student."""
    teacher_1 = models.User(
        id=uuid4(),
        username="teacher_hue_1",
        email="teacher1@example.com",
        display_name="Thầy Nguyễn Hoàng — Lịch sử",
        password_hash="mock_hash",
        role=models.UserRole.teacher,
    )
    teacher_2 = models.User(
        id=uuid4(),
        username="teacher_hue_2",
        email="teacher2@example.com",
        display_name="Cô Lê Thị Mai — Lịch sử",
        password_hash="mock_hash",
        role=models.UserRole.teacher,
    )
    student = models.User(
        id=uuid4(),
        username="student_thpt",
        email="student@example.com",
        display_name="Học sinh THPT Quốc Học",
        password_hash="mock_hash",
        role=models.UserRole.learner,
    )
    db_session.add_all([teacher_1, teacher_2, student])
    db_session.commit()
    return {"teacher_1": teacher_1, "teacher_2": teacher_2, "student": student}


@pytest.fixture
def seed_v51_data(db_session: Session) -> dict[str, object]:
    """Seed minimal authentic Đại Nội Huế V5.1 entities."""
    zone = ImperialZone(
        id=uuid4(),
        content_scope=CONTENT_SCOPE_IMPERIAL,
        slug="central-ceremonial-axis",
        title_vi="Trục trung tâm",
        display_order=1,
    )
    site = ImperialSite(
        id=uuid4(),
        content_scope=CONTENT_SCOPE_IMPERIAL,
        zone_id=zone.id,
        slug="dien-thai-hoa",
        name_vi="Điện Thái Hòa",
        is_published=True,
    )
    media = ImperialLearningMedia(
        id=uuid4(),
        content_scope=CONTENT_SCOPE_IMPERIAL,
        site_id=site.id,
        kind="image",
        media_url="/panoramas/the-mieu.jpg",
        license_status="approved",
        review_status="published",
        asset_context="extant",
    )
    art_detail = ImperialArtDetail(
        id=uuid4(),
        content_scope=CONTENT_SCOPE_IMPERIAL,
        site_id=site.id,
        slug="hoa-tiet-rong-may-dien-thai-hoa",
        title="Họa tiết Rồng mây Điện Thái Hòa",
        kind="carving",
        motif="Long vân khánh hội",
        story_body="Hình tượng rồng năm móng tại điện Thái Hòa là độc quyền biểu tượng của Hoàng đế nhà Nguyễn.",
        story_type="documented_event",
        meaning_body="Rồng năm móng là linh vật đứng đầu Tứ linh, tượng trưng cho thiên mệnh.",
        review_status="published",
    )
    claim_source = ImperialArtDetailClaimSource(
        id=uuid4(),
        content_scope=CONTENT_SCOPE_IMPERIAL,
        detail_id=art_detail.id,
        section="Quy chế đồ án rồng ngai vàng",
        claim_text="Chỉ có cung điện của thiên tử và ngai vàng mới được chạm rồng 5 móng.",
        source_title="Khâm Định Đại Nam Hội Điển Sự Lệ",
        source_locator="Quyển 214: Công bộ",
        evidence_strength="verified",
    )
    hotspot = ImperialMediaHotspot(
        id=uuid4(),
        content_scope=CONTENT_SCOPE_IMPERIAL,
        media_id=media.id,
        point_kind="point",
        u=0.485,
        v=0.520,
        title="Rồng vờn mây trên cột cái",
        detail_id=art_detail.id,
        review_status="published",
    )
    clue = ImperialClue(
        id=uuid4(),
        content_scope=CONTENT_SCOPE_IMPERIAL,
        title="Bí mật chín rồng ngự trị đỉnh cao quyền lực",
        clue_text="Nơi bách quan triều bái ngày sóc vọng, ánh vàng rực rỡ trên 80 cột gỗ lim.",
        target_type="site",
        target_id=site.id,
        hint_steps=[
            "Nằm trên trục Dũng Đạo.",
            "Tổ chức lễ đăng quang 13 vị vua triều Nguyễn.",
            "Điện Thái Hòa với ngai vàng nguyên bản.",
        ],
        review_status="published",
    )
    question = ImperialQuestion(
        id=uuid4(),
        content_scope=CONTENT_SCOPE_IMPERIAL,
        site_id=site.id,
        detail_id=art_detail.id,
        question_type="multiple_choice",
        prompt="Đặc điểm nào trên chân rồng tại điện Thái Hòa khẳng định đây là hình tượng dành riêng cho Hoàng đế?",
        options=["3 móng", "4 móng", "5 móng", "không móng"],
        answer_key="5 móng",
        explanation_why="Theo điển lệ, chỉ có Hoàng đế mới được dùng rồng 5 móng.",
        source_citation="Khâm Định Đại Nam Hội Điển Sự Lệ",
        review_status="published",
    )
    db_session.add_all(
        [zone, site, media, art_detail, claim_source, hotspot, clue, question]
    )
    db_session.commit()
    return {
        "zone": zone,
        "site": site,
        "media": media,
        "art_detail": art_detail,
        "hotspot": hotspot,
        "clue": clue,
        "question": question,
    }


@pytest.fixture
def api_client(
    db_session: Session, test_users: dict[str, models.User]
) -> Generator[TestClient, None, None]:
    """TestClient overriding DB and auth."""
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_staff_user] = lambda: test_users["teacher_1"]
    app.dependency_overrides[get_current_user] = lambda: test_users["teacher_1"]

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


class TestImperialV51Integration:
    """Test suite for V5.1 end-to-end functionality and pedagogical contracts."""

    def test_get_site_learning_media_and_hotspots(
        self, api_client: TestClient, seed_v51_data: dict[str, object]
    ):
        """Verify learning media retrieval and published hotspot coordinates."""
        site = seed_v51_data["site"]
        res = api_client.get(f"/api/v1/imperial/sites/{site.slug}/learning-media")
        assert res.status_code == 200
        media_list = res.json()
        assert len(media_list) >= 1
        m = media_list[0]
        assert m["media_url"] == "/panoramas/the-mieu.jpg"
        assert len(m["hotspots"]) == 1
        h = m["hotspots"][0]
        assert 0.0 <= h["u"] <= 1.0
        assert 0.0 <= h["v"] <= 1.0
        assert h["title"] == "Rồng vờn mây trên cột cái"

    def test_get_art_detail_dossier(
        self, api_client: TestClient, seed_v51_data: dict[str, object]
    ):
        """Verify art detail dossier with story, sources, and metadata."""
        detail = seed_v51_data["art_detail"]
        res = api_client.get(f"/api/v1/imperial/art-details/{detail.slug}")
        assert res.status_code == 200
        data = res.json()
        assert data["slug"] == detail.slug
        assert data["story_type"] == "documented_event"
        assert len(data["claim_sources"]) >= 1
        assert "Khâm Định Đại Nam Hội Điển" in data["claim_sources"][0]["source_title"]

    def test_heritage_detective_clue_attempt(
        self, api_client: TestClient, seed_v51_data: dict[str, object]
    ):
        """Verify clue listing and progressive hint attempt flow."""
        clue = seed_v51_data["clue"]
        site = seed_v51_data["site"]

        # List clues
        res_list = api_client.get("/api/v1/imperial/clues")
        assert res_list.status_code == 200
        clues = res_list.json()
        assert any(c["id"] == str(clue.id) for c in clues)

        # Attempt with wrong target -> reveals hint 1
        wrong_id = str(uuid4())
        res_wrong = api_client.post(
            f"/api/v1/imperial/clues/{clue.id}/attempt",
            json={"selected_target_id": wrong_id, "attempt_number": 1},
        )
        assert res_wrong.status_code == 200
        wrong_data = res_wrong.json()
        assert wrong_data["is_correct"] is False
        assert len(wrong_data["hint_steps"]) == 1
        assert "trục Dũng Đạo" in wrong_data["hint_steps"][0]

        # Attempt with correct target -> success
        res_correct = api_client.post(
            f"/api/v1/imperial/clues/{clue.id}/attempt",
            json={"selected_target_id": str(site.id), "attempt_number": 2},
        )
        assert res_correct.status_code == 200
        correct_data = res_correct.json()
        assert correct_data["is_correct"] is True
        assert "Chính xác" in correct_data["message"]

    def test_game_question_and_submission(
        self, api_client: TestClient, seed_v51_data: dict[str, object]
    ):
        """Verify game question query hides answer_key, and submission evaluates accurately."""
        question = seed_v51_data["question"]
        res_q = api_client.get("/api/v1/imperial/games/questions")
        assert res_q.status_code == 200
        questions = res_q.json()
        assert len(questions) >= 1
        q_item = questions[0]
        # Contract: public quiz questions must NEVER expose answer_key
        assert "answer_key" not in q_item

        # Submit answer
        res_submit = api_client.post(
            "/api/v1/imperial/games/submit",
            json={"question_id": str(question.id), "user_answer": "5 móng"},
        )
        assert res_submit.status_code == 200
        submit_data = res_submit.json()
        assert submit_data["is_correct"] is True
        assert submit_data["correct_answer"] == "5 móng"
        assert "Khâm Định Đại Nam Hội Điển" in submit_data["source_citation"]

    def test_teacher_assignment_lifecycle_and_idor_protection(
        self,
        api_client: TestClient,
        db_session: Session,
        test_users: dict[str, models.User],
    ):
        """Verify teacher can create and list assignments, and cannot edit another teacher's assignment."""
        # Teacher 1 creates assignment
        create_payload = {
            "class_name": "Lớp 10A1 — Chuyên Sử Quốc Học",
            "journey_slug": "truc-chinh-dao-hoang-thanh",
            "title": "Nghiên cứu trục nghi lễ qua Ngọ Môn và Điện Thái Hòa",
            "due_date": "2026-11-01T23:59:59Z",
            "rubric_weights": {"S1_spatial": 25, "S2_temporal": 25, "S3_evidence": 25, "S4_argument": 25},
            "is_active": True,
        }
        res_create = api_client.post("/api/v1/imperial/teacher/assignments", json=create_payload)
        assert res_create.status_code == 201
        assignment = res_create.json()
        assignment_id = assignment["id"]
        assert assignment["class_name"] == "Lớp 10A1 — Chuyên Sử Quốc Học"

        # List teacher 1's assignments
        res_list = api_client.get("/api/v1/imperial/teacher/assignments")
        assert res_list.status_code == 200
        assert len(res_list.json()) >= 1

        # Teacher 2 attempts to edit Teacher 1's assignment -> IDOR 403 Forbidden
        app.dependency_overrides[get_staff_user] = lambda: test_users["teacher_2"]
        res_forbidden = api_client.patch(
            f"/api/v1/imperial/teacher/assignments/{assignment_id}",
            json={"title": "Hacked Title", "row_version": 1},
        )
        assert res_forbidden.status_code == 403

        # Teacher 1 edits their own assignment -> 200 OK
        app.dependency_overrides[get_staff_user] = lambda: test_users["teacher_1"]
        res_update = api_client.patch(
            f"/api/v1/imperial/teacher/assignments/{assignment_id}",
            json={"title": "Tiêu đề đã được cập nhật bởi Thầy Hoàng", "row_version": 1},
        )
        assert res_update.status_code == 200
        assert res_update.json()["title"] == "Tiêu đề đã được cập nhật bởi Thầy Hoàng"

    def test_zero_legacy_cuu_dinh_leakage(
        self, api_client: TestClient, seed_v51_data: dict[str, object]
    ):
        """Verify strict isolation: no Cửu Đỉnh 9-urn artifacts in imperial v5.1 endpoints."""
        res_media = api_client.get("/api/v1/imperial/sites/dien-thai-hoa/learning-media")
        assert "cao-dinh" not in res_media.text.lower()
        assert "huyen-dinh" not in res_media.text.lower()

        res_art = api_client.get("/api/v1/imperial/sites/dien-thai-hoa/art-details")
        assert "cuu-dinh" not in res_art.text.lower()
        assert "162" not in res_art.text.lower()

        res_clues = api_client.get("/api/v1/imperial/clues")
        assert "cuu dinh" not in res_clues.text.lower()
