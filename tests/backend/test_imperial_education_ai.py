# -*- coding: utf-8 -*-
"""Integration tests for STTT Imperial City Learning Paths, Activities, Submissions, and Scope-Locked AI Tutor.

Validates:
1. Learning paths and step sequences retrieval (curated trails with site metadata).
2. Site pedagogical inquiry activity retrieval.
3. Student activity submission with evidence references and validation.
4. Role-based access control:
   - Learners can submit activities (guests receive 403 Forbidden).
   - Staff/teachers can view submissions and submit rubric grades (learners receive 403 Forbidden).
5. Teacher grading with S1-S4 rubric scores (0-3 scale each), total score computation, and feedback.
6. Scope-locked AI tutor:
   - Queries about Ngọ Môn / Điện Thái Hòa return evidence-grounded answers citing primary sources
     (Đại Nam Thực Lục, Hội Điển Sự Lệ) and structured into 3 epistemic sections.
   - Queries with forbidden legacy terms (Cửu Đỉnh, 162 motif, bản đúc nổi) or out-of-scope topics
     are strictly refused with insufficient_evidence = True and exact refusal message.
"""
from __future__ import annotations

import json
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
from backend.deps import get_admin_user, get_current_user, get_db, get_staff_user
from backend.imperial_models import (
    CONTENT_SCOPE_IMPERIAL,
    Base,
    ImperialActivity,
    ImperialLearningPath,
    ImperialMapAnnotation,
    ImperialMapAsset,
    ImperialMedia,
    ImperialPathStep,
    ImperialSite,
    ImperialSubmission,
    ImperialZone,
)
from backend.main import app
from backend.routers.imperial import get_learner_user


# --------------------------------------------------------------------------- #
# Database Fixture for Isolated Integration Testing
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="module")
def imperial_db_engine():
    """Create in-memory SQLite engine with all imperial, learning, and user tables."""
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
        ImperialLearningPath.__table__,
        ImperialPathStep.__table__,
        ImperialActivity.__table__,
        ImperialSubmission.__table__,
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
        sess.query(ImperialSubmission).delete()
        sess.query(ImperialActivity).delete()
        sess.query(ImperialPathStep).delete()
        sess.query(ImperialLearningPath).delete()
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
    """Create test users with learner, teacher, guest, and admin roles."""
    student_id = uuid4()
    student_user = models.User(
        id=student_id,
        username=f"student_{student_id.hex[:6]}",
        email=f"student_{student_id.hex[:6]}@example.com",
        display_name="Nguyen Van Hoc Sinh",
        password_hash="mock_hash",
        role=models.UserRole.learner,
    )

    teacher_id = uuid4()
    teacher_user = models.User(
        id=teacher_id,
        username=f"teacher_{teacher_id.hex[:6]}",
        email=f"teacher_{teacher_id.hex[:6]}@example.com",
        display_name="Thay Giao Su",
        password_hash="mock_hash",
        role=models.UserRole.teacher,
    )

    guest_id = uuid4()
    guest_user = models.User(
        id=guest_id,
        username=f"guest_{guest_id.hex[:6]}",
        email=f"guest_{guest_id.hex[:6]}@example.com",
        display_name="Khach Vang Lai",
        password_hash="mock_hash",
        role=models.UserRole.guest,
    )

    admin_id = uuid4()
    admin_user = models.User(
        id=admin_id,
        username=f"admin_{admin_id.hex[:6]}",
        email=f"admin_{admin_id.hex[:6]}@example.com",
        display_name="Quan Tri Vien",
        password_hash="mock_hash",
        role=models.UserRole.admin,
    )

    db_session.add_all([student_user, teacher_user, guest_user, admin_user])
    db_session.commit()
    return {
        "student": student_user,
        "teacher": teacher_user,
        "guest": guest_user,
        "admin": admin_user,
    }


@pytest.fixture
def seeded_monuments(db_session: Session, test_users: dict[str, models.User]):
    """Seed baseline spatial zones and sites for testing learning paths and AI tutor."""
    admin = test_users["admin"]

    # 1. Zone
    zone = ImperialZone(
        id=uuid4(),
        content_scope=CONTENT_SCOPE_IMPERIAL,
        slug="central-ceremonial-axis",
        title_vi="Trục trung tâm",
        title_en="Central Ceremonial Axis",
        description="Trục chính đạo thiết lập trật tự không gian quyền lực và nghi lễ.",
        display_order=1,
    )
    db_session.add(zone)
    db_session.flush()

    # 2. Sites (Ngọ Môn, Cầu Trung Đạo, Sân Đại Triều Nghi, Điện Thái Hòa)
    ngo_mon = ImperialSite(
        id=uuid4(),
        content_scope=CONTENT_SCOPE_IMPERIAL,
        zone_id=zone.id,
        slug="ngo-mon",
        name_vi="Ngọ Môn",
        name_en="Meridian Gate",
        site_type="gate",
        condition="extant",
        learning_level="L2_VERIFIED",
        summary_vi="Cổng chính phía nam của Hoàng Thành Huế, xây dựng năm 1833 thời Minh Mạng.",
        historical_context="Cửa chính của Hoàng Thành, nơi diễn ra lễ ban Sóc và thoái vị năm 1945.",
        architectural_features="Cấu trúc đài đá 5 cửa và lầu Ngũ Phụng mái chồng diềm.",
        construction_year=1833,
        is_published=True,
        display_order=1,
        created_by=admin.id,
    )
    cau_trung_dao = ImperialSite(
        id=uuid4(),
        content_scope=CONTENT_SCOPE_IMPERIAL,
        zone_id=zone.id,
        slug="cau-trung-dao",
        name_vi="Cầu Trung Đạo",
        name_en="Trung Dao Bridge",
        site_type="bridge",
        condition="extant",
        learning_level="L1_DOCUMENTED",
        summary_vi="Chiếc cầu bắc qua hồ Thái Dịch trên trục thần đạo.",
        historical_context="Nối liền Ngọ Môn và sân Đại Triều Nghi.",
        architectural_features="Mặt cầu lát đá thanh, hai đầu cầu có cổng đồng quán.",
        construction_year=1833,
        is_published=True,
        display_order=2,
        created_by=admin.id,
    )
    san_dai_trieu = ImperialSite(
        id=uuid4(),
        content_scope=CONTENT_SCOPE_IMPERIAL,
        zone_id=zone.id,
        slug="san-dai-trieu-nghi",
        name_vi="Sân Đại Triều Nghi",
        name_en="Grand Ceremony Court",
        site_type="courtyard",
        condition="extant",
        learning_level="L2_VERIFIED",
        summary_vi="Khoảng sân rộng hai tầng trước điện Thái Hòa dành cho bách quan bái mạng.",
        historical_context="Nơi tổ chức lễ đại triều mùng 1 và ngày rằm hàng tháng.",
        architectural_features="Hai tầng sân lát gạch và hai hàng bia phẩm tán bằng đá.",
        construction_year=1805,
        is_published=True,
        display_order=3,
        created_by=admin.id,
    )
    dien_thai_hoa = ImperialSite(
        id=uuid4(),
        content_scope=CONTENT_SCOPE_IMPERIAL,
        zone_id=zone.id,
        slug="dien-thai-hoa",
        name_vi="Điện Thái Hòa",
        name_en="Supreme Harmony Palace",
        site_type="palace",
        condition="extant",
        learning_level="L2_VERIFIED",
        summary_vi="Tòa điện quan trọng bậc nhất biểu trưng cho quyền lực tối cao của hoàng triều.",
        historical_context="Nơi đặt ngai vàng thiên tử, thiết đại lễ đăng quang và tiếp sứ thần.",
        architectural_features="Kiến trúc trùng thiềm điệp ốc với 80 cột gỗ lim sơn son thếp vàng.",
        construction_year=1805,
        is_published=True,
        display_order=4,
        created_by=admin.id,
    )

    db_session.add_all([ngo_mon, cau_trung_dao, san_dai_trieu, dien_thai_hoa])
    db_session.commit()

    return {
        "zone": zone,
        "ngo_mon": ngo_mon,
        "cau_trung_dao": cau_trung_dao,
        "san_dai_trieu": san_dai_trieu,
        "dien_thai_hoa": dien_thai_hoa,
    }


# =========================================================================== #
# Test Class 1: Learning Paths & Steps Retrieval
# =========================================================================== #
class TestImperialLearningPaths:
    """Validates learning paths listing, step sequences, and site metadata attachment."""

    def test_get_learning_paths_list(self, db_session: Session, seeded_monuments: dict):
        def _override_db():
            yield db_session

        app.dependency_overrides[get_db] = _override_db
        try:
            with TestClient(app) as client:
                res = client.get("/api/v1/imperial/paths")
                assert res.status_code == 200
                data = res.json()
                assert isinstance(data, list)
                assert len(data) >= 1

                # Check path structure
                main_path = next(p for p in data if p["slug"] == "truc-chinh-dao-hoang-thanh")
                assert main_path["title"] == "Trục Chính Đạo Hoàng Thành"
                assert main_path["duration_min"] == 45
                assert len(main_path["learning_objectives"]) >= 2
                assert len(main_path["steps"]) == 4

                # Check step ordering and site metadata
                steps = sorted(main_path["steps"], key=lambda s: s["step_order"])
                assert steps[0]["site"]["slug"] == "ngo-mon"
                assert steps[1]["site"]["slug"] == "cau-trung-dao"
                assert steps[2]["site"]["slug"] == "san-dai-trieu-nghi"
                assert steps[3]["site"]["slug"] == "dien-thai-hoa"

                # Verify /learning-paths alias
                res_alias = client.get("/api/v1/imperial/learning-paths")
                assert res_alias.status_code == 200
                assert len(res_alias.json()) == len(data)
        finally:
            app.dependency_overrides.clear()

    def test_get_learning_path_by_slug(self, db_session: Session, seeded_monuments: dict):
        def _override_db():
            yield db_session

        app.dependency_overrides[get_db] = _override_db
        try:
            with TestClient(app) as client:
                res = client.get("/api/v1/imperial/paths/truc-chinh-dao-hoang-thanh")
                assert res.status_code == 200
                data = res.json()
                assert data["slug"] == "truc-chinh-dao-hoang-thanh"
                assert data["content_scope"] == "STTT_IMPERIAL_CITY"
                assert len(data["steps"]) == 4
                for s in data["steps"]:
                    assert s["prompt"]
                    assert s["estimated_minutes"] > 0
                    assert s["site"] is not None

                # Verify /learning-paths/{slug} alias
                res_alias = client.get("/api/v1/imperial/learning-paths/truc-chinh-dao-hoang-thanh")
                assert res_alias.status_code == 200
                assert res_alias.json()["slug"] == "truc-chinh-dao-hoang-thanh"
        finally:
            app.dependency_overrides.clear()

    def test_get_learning_path_not_found(self, db_session: Session, seeded_monuments: dict):
        def _override_db():
            yield db_session

        app.dependency_overrides[get_db] = _override_db
        try:
            with TestClient(app) as client:
                res = client.get("/api/v1/imperial/paths/duong-di-khong-ton-tai")
                assert res.status_code == 404
                data = res.json()
                assert "IMPERIAL_PATH_NOT_FOUND" in str(data)
        finally:
            app.dependency_overrides.clear()


# =========================================================================== #
# Test Class 2: Activities, Submissions & Teacher Rubric Evaluation
# =========================================================================== #
class TestImperialActivitiesAndSubmissions:
    """Validates activity retrieval, student submission, and teacher rubric grading."""

    def test_get_site_activities(self, db_session: Session, seeded_monuments: dict):
        def _override_db():
            yield db_session

        app.dependency_overrides[get_db] = _override_db
        try:
            with TestClient(app) as client:
                res = client.get("/api/v1/imperial/sites/ngo-mon/activities")
                assert res.status_code == 200
                data = res.json()
                assert isinstance(data, list)
                assert len(data) >= 1
                activity = data[0]
                assert activity["content_scope"] == "STTT_IMPERIAL_CITY"
                assert activity["title"]
                assert activity["instructions"]
                assert activity["max_points"] == 100
        finally:
            app.dependency_overrides.clear()

    def test_student_submit_activity_and_teacher_grade(
        self, db_session: Session, seeded_monuments: dict, test_users: dict[str, models.User]
    ):
        student = test_users["student"]
        teacher = test_users["teacher"]

        def _override_db():
            yield db_session

        def _override_student():
            return student

        def _override_teacher():
            return teacher

        app.dependency_overrides[get_db] = _override_db
        try:
            with TestClient(app) as client:
                # 1. Fetch activity ID for Ngọ Môn
                act_res = client.get("/api/v1/imperial/sites/ngo-mon/activities")
                assert act_res.status_code == 200
                activities = act_res.json()
                activity_id = activities[0]["id"]

                # 2. Student submits answer
                app.dependency_overrides[get_current_user] = _override_student
                app.dependency_overrides[get_learner_user] = _override_student

                submission_payload = {
                    "answer_text": "Ngọ Môn có 5 cửa: cửa giữa dành cho Thiên tử, 2 cửa tả hữu giáp môn cho bá quan, 2 cửa ngoài cùng cho binh mã.",
                    "evidence_refs": [
                        {
                            "source_title": "Đại Nam Thực Lục Chính Biên",
                            "chapter": "Đệ nhị kỷ, Quyển 98",
                            "quote": "Tháng 3 năm Quý Tỵ (1833), dựng cổng Ngọ Môn trổ 5 cửa...",
                        }
                    ],
                }
                sub_res = client.post(
                    f"/api/v1/imperial/activities/{activity_id}/submissions",
                    json=submission_payload,
                )
                assert sub_res.status_code == 201
                sub_data = sub_res.json()
                submission_id = sub_data["id"]
                assert sub_data["status"] == "submitted"
                assert sub_data["score"] is None
                assert len(sub_data["evidence_refs"]) == 1

                # 3. Teacher views submissions
                app.dependency_overrides[get_staff_user] = _override_teacher
                list_res = client.get(
                    f"/api/v1/imperial/teacher/submissions?activity_id={activity_id}"
                )
                assert list_res.status_code == 200
                submissions_list = list_res.json()
                assert any(s["id"] == submission_id for s in submissions_list)

                # 4. Teacher grades submission with S1-S4 rubric scores
                grade_payload = {
                    "rubric_scores": {
                        "S1_spatial": 3,
                        "S2_temporal": 2,
                        "S3_evidence": 3,
                        "S4_argument": 2,
                    },
                    "feedback": "Phân tích trật tự phân tầng không gian chính xác, trích dẫn chuẩn Đại Nam Thực Lục.",
                    "status": "graded",
                }
                grade_res = client.post(
                    f"/api/v1/imperial/teacher/submissions/{submission_id}/grade",
                    json=grade_payload,
                )
                assert grade_res.status_code == 200
                graded_data = grade_res.json()
                assert graded_data["status"] == "graded"
                assert graded_data["score"] == 10.0  # 3 + 2 + 3 + 2
                assert graded_data["rubric_scores"] == {
                    "S1_spatial": 3,
                    "S2_temporal": 2,
                    "S3_evidence": 3,
                    "S4_argument": 2,
                }
                assert "trích dẫn chuẩn" in graded_data["feedback"]
                assert graded_data["graded_by"] == str(teacher.id)
                assert graded_data["row_version"] == 2
        finally:
            app.dependency_overrides.clear()

    def test_rubric_validation_rejects_out_of_scale_score(
        self, db_session: Session, seeded_monuments: dict, test_users: dict[str, models.User]
    ):
        student = test_users["student"]
        teacher = test_users["teacher"]

        def _override_db():
            yield db_session

        def _override_student():
            return student

        def _override_teacher():
            return teacher

        app.dependency_overrides[get_db] = _override_db
        try:
            with TestClient(app) as client:
                act_res = client.get("/api/v1/imperial/sites/ngo-mon/activities")
                activity_id = act_res.json()[0]["id"]

                app.dependency_overrides[get_learner_user] = _override_student
                sub_res = client.post(
                    f"/api/v1/imperial/activities/{activity_id}/submissions",
                    json={"answer_text": "Báo cáo khảo sát di tích."},
                )
                submission_id = sub_res.json()["id"]

                # Try to grade with score > 3 (e.g. 5)
                app.dependency_overrides[get_staff_user] = _override_teacher
                bad_grade = {
                    "rubric_scores": {
                        "S1_spatial": 5,  # Out of range! Max is 3
                    },
                    "feedback": "Điểm vượt khung",
                }
                err_res = client.post(
                    f"/api/v1/imperial/teacher/submissions/{submission_id}/grade",
                    json=bad_grade,
                )
                assert err_res.status_code == 400
                assert "INVALID_RUBRIC_SCORE" in err_res.text
        finally:
            app.dependency_overrides.clear()

    def test_guest_user_cannot_submit_activity(
        self, db_session: Session, seeded_monuments: dict, test_users: dict[str, models.User]
    ):
        guest = test_users["guest"]

        def _override_db():
            yield db_session

        def _override_guest():
            return guest

        app.dependency_overrides[get_db] = _override_db
        app.dependency_overrides[get_current_user] = _override_guest
        try:
            with TestClient(app) as client:
                act_res = client.get("/api/v1/imperial/sites/ngo-mon/activities")
                activity_id = act_res.json()[0]["id"]

                sub_res = client.post(
                    f"/api/v1/imperial/activities/{activity_id}/submissions",
                    json={"answer_text": "Khách thử nộp bài."},
                )
                assert sub_res.status_code == 403
        finally:
            app.dependency_overrides.clear()


# =========================================================================== #
# Test Class 3: Scope-Locked AI Tutor Service
# =========================================================================== #
class TestImperialAITutorScopeLocked:
    """Validates epistemic grounding in primary sources and strict deny-list interception."""

    def test_ai_tutor_answers_ngo_mon_with_grounded_primary_sources(
        self, db_session: Session, seeded_monuments: dict
    ):
        def _override_db():
            yield db_session

        app.dependency_overrides[get_db] = _override_db
        try:
            with TestClient(app) as client:
                ask_payload = {
                    "query": "Kiến trúc Ngọ Môn có ý nghĩa lịch sử như thế nào?",
                    "site_slug": "ngo-mon",
                }
                res = client.post("/api/v1/imperial/ai/ask", json=ask_payload)
                assert res.status_code == 200
                data = res.json()

                # Epistemic checks
                assert data["content_scope"] == "STTT_IMPERIAL_CITY"
                assert data["insufficient_evidence"] is False
                assert data["site_slug"] == "ngo-mon"

                # 1. Inquiry answer
                assert "Minh Mạng" in data["inquiry_answer"]
                assert "Ngũ Phụng" in data["inquiry_answer"]
                assert "5 cửa" in data["inquiry_answer"]

                # 2. Primary sources cited
                assert len(data["sources_cited"]) >= 1
                sources_titles = [s["source_title"] for s in data["sources_cited"]]
                assert any("Đại Nam Thực Lục" in t for t in sources_titles)
                # Ensure primary sources contain citations
                for src in data["sources_cited"]:
                    assert src["citation"]

                # 3. Certainty vs Uncertainty
                cert_uncert = data["certainty_vs_uncertainty"]
                assert cert_uncert["certainty"]
                assert "1833" in cert_uncert["certainty"]
                assert cert_uncert["uncertainty"]

                # Verify /ai/chat alias
                res_chat = client.post("/api/v1/imperial/ai/chat", json=ask_payload)
                assert res_chat.status_code == 200
                data_chat = res_chat.json()
                assert data_chat["site_slug"] == "ngo-mon"
                assert "Ngũ Phụng" in data_chat["inquiry_answer"]
        finally:
            app.dependency_overrides.clear()

    def test_ai_tutor_answers_dien_thai_hoa_via_keyword_resolution(
        self, db_session: Session, seeded_monuments: dict
    ):
        def _override_db():
            yield db_session

        app.dependency_overrides[get_db] = _override_db
        try:
            with TestClient(app) as client:
                ask_payload = {
                    "query": "Hãy giải thích kết cấu trùng thiềm điệp ốc tại điện Thái Hòa",
                }
                res = client.post("/api/v1/imperial/ai/ask", json=ask_payload)
                assert res.status_code == 200
                data = res.json()

                assert data["insufficient_evidence"] is False
                assert data["site_slug"] == "dien-thai-hoa"
                assert "trùng thiềm điệp ốc" in data["inquiry_answer"]
                assert "80 cột gỗ lim" in data["inquiry_answer"]
                assert any("Hội Điển" in s["source_title"] or "Thực Lục" in s["source_title"] for s in data["sources_cited"])
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.parametrize(
        "forbidden_query",
        [
            "Ý nghĩa của Cửu Đỉnh triều Nguyễn là gì?",
            "Cho tôi biết thông tin về 9 đỉnh đồng",
            "Các bản đúc nổi trên chín đỉnh miêu tả điều gì?",
            "Có phải có 162 relief motifs trên đỉnh không?",
            "Tìm hiểu về 162 phù điêu hoa văn",
            "Cao Đỉnh được đúc vào năm nào?",
            "Huyền Đỉnh biểu trưng cho điều gì?",
            "ban duc noi cuu dinh",
        ],
    )
    def test_ai_tutor_strictly_refuses_legacy_cuu_dinh_and_motifs(
        self, db_session: Session, seeded_monuments: dict, forbidden_query: str
    ):
        def _override_db():
            yield db_session

        app.dependency_overrides[get_db] = _override_db
        try:
            with TestClient(app) as client:
                ask_payload = {"query": forbidden_query}
                res = client.post("/api/v1/imperial/ai/ask", json=ask_payload)
                assert res.status_code == 200
                data = res.json()

                # Must flag insufficient evidence and return exact refusal
                assert data["insufficient_evidence"] is True
                assert data["message"] == "Nội dung này nằm ngoài phạm vi học liệu lịch sử Đại Nội Huế của dự án."
                assert data["inquiry_answer"] == "Nội dung này nằm ngoài phạm vi học liệu lịch sử Đại Nội Huế của dự án."
                assert data["sources_cited"] == []
                assert data["certainty_vs_uncertainty"]["certainty"] == ""
        finally:
            app.dependency_overrides.clear()

    def test_ai_tutor_refuses_completely_outside_topics(
        self, db_session: Session, seeded_monuments: dict
    ):
        def _override_db():
            yield db_session

        app.dependency_overrides[get_db] = _override_db
        try:
            with TestClient(app) as client:
                ask_payload = {"query": "Hôm nay thời tiết ở Tokyo như thế nào?"}
                res = client.post("/api/v1/imperial/ai/ask", json=ask_payload)
                assert res.status_code == 200
                data = res.json()

                assert data["insufficient_evidence"] is True
                assert data["message"] == "Nội dung này nằm ngoài phạm vi học liệu lịch sử Đại Nội Huế của dự án."
                assert data["sources_cited"] == []
        finally:
            app.dependency_overrides.clear()
