# -*- coding: utf-8 -*-
"""V5-T033 (Wave W03, Slot A03): Assignment and source-locked lessons.

Requirements & Invariants:
1. Teachers assign lessons with pinned version, rubric, and source set to a classroom.
2. Pinned assessment basis: Editing the master lesson later must not alter the
   submitted assessment basis for an existing assignment.
3. Negative abuse: Assignment cannot be published if lesson has unverified historical claims
   (returns HTTP 422 ASSIGNMENT_UNVERIFIED_CLAIMS).
4. Positive verification: Assignment publishes cleanly when all linked claims reach verified status.
5. Student submission & rubric-based grading against the immutable pinned assessment basis.
6. Access control: Enforces classroom scoping and role permissions.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest
from sqlalchemy import select

from backend.models import (
    ClassMember,
    Classroom,
    ContentRating,
    ContentStatus,
    HistoricalClaim,
    HistoricalEntity,
    HistoricalSource,
    HistoryAssignmentSubmission,
    HistoryLessonAssignment,
    LessonContent,
    Motif,
    MotifCategory,
    MotifRarity,
    Urn,
    User,
    UserRole,
)
from backend.security import hash_password
from backend.services import history_learning as hl

REPO_ROOT = Path(__file__).resolve().parents[2]


# --------------------------------------------------------------------------- #
# Helpers & Fixtures
# --------------------------------------------------------------------------- #

@pytest.fixture(autouse=True)
def _reset_auth_rate_limit():
    """Reset auth rate limit before each test."""
    import backend.main as main

    main._auth_rate_limit_state.clear()
    yield
    main._auth_rate_limit_state.clear()


def _create_user(
    db_session,
    email: str,
    role: UserRole = UserRole.learner,
    display_name: str | None = None,
) -> User:
    user = User(
        email=email,
        password_hash=hash_password("Password123!"),
        display_name=display_name or f"User {email.split('@')[0]}",
        username=f"user_{uuid.uuid4().hex[:8]}",
        role=role,
        is_profile_public=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _login_user(client, email: str, password: str = "Password123!"):
    res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"


def _setup_test_context(db_session):
    """Seed classroom, teacher, students, urn, motif, lesson, sources, and claims."""
    teacher = _create_user(
        db_session,
        f"teacher_{uuid.uuid4().hex[:6]}@school.edu.vn",
        role=UserRole.teacher,
        display_name="Thầy Giáo Sử Triều Nguyễn",
    )
    other_teacher = _create_user(
        db_session,
        f"other_teacher_{uuid.uuid4().hex[:6]}@school.edu.vn",
        role=UserRole.teacher,
        display_name="Cô Giáo Sử Khác",
    )
    student = _create_user(
        db_session,
        f"student_{uuid.uuid4().hex[:6]}@school.edu.vn",
        role=UserRole.learner,
        display_name="Học Sinh Chuyên Sử",
    )
    outsider = _create_user(
        db_session,
        f"outsider_{uuid.uuid4().hex[:6]}@school.edu.vn",
        role=UserRole.learner,
        display_name="Học Sinh Ngoài Lớp",
    )

    classroom = Classroom(
        name="Lớp Sử 10A1 — Cửu Đỉnh Di Sản",
        teacher_id=teacher.id,
        class_code=f"CD{uuid.uuid4().hex[:4].upper()}",
        is_archived=False,
    )
    other_classroom = Classroom(
        name="Lớp Sử 10B2 — Khác",
        teacher_id=other_teacher.id,
        class_code=f"CD{uuid.uuid4().hex[:4].upper()}",
        is_archived=False,
    )
    db_session.add_all([classroom, other_classroom])
    db_session.commit()
    db_session.refresh(classroom)
    db_session.refresh(other_classroom)

    # Enroll student in classroom
    cm = ClassMember(class_id=classroom.id, user_id=student.id, role="learner")
    db_session.add(cm)
    db_session.commit()

    # Urn and Motif
    urn_slug = f"urn-{uuid.uuid4().hex[:8]}"
    urn = Urn(
        slug=urn_slug,
        name="Cao Đỉnh",
        model_url=f"/models/{urn_slug}.glb",
        display_order=1,
    )
    db_session.add(urn)
    db_session.flush()

    motif = Motif(
        urn_id=urn.id,
        mesh_name=f"mesh_cao_dinh_{uuid.uuid4().hex[:8]}",
        name="Long (Rồng)",
        name_en="Dragon",
        category=MotifCategory.dong_vat,
        rarity=MotifRarity.legendary,
        pos_x=0.0,
        pos_y=0.0,
        pos_z=0.0,
        bounding_radius=1.0,
    )
    db_session.add(motif)
    db_session.flush()

    # Sources
    source1 = HistoricalSource(
        source_type="royal_chronicle",
        title="Đại Nam Thực Lục Chính Biên",
        author_text="Quốc sử quán triều Nguyễn",
        publication_year=1848,
        pages="Đệ nhị kỷ, quyển 154, tờ 12a",
        verification_status="expert_verified",
        license="Public Domain",
        rights_status="public_domain",
        url="https://archives.org.vn/dntl-154",
    )
    source2 = HistoricalSource(
        source_type="court_gazette",
        title="Khâm Định Đại Nam Hội Điển Sự Lệ",
        author_text="Nội các triều Nguyễn",
        publication_year=1851,
        pages="Quyển 214, Công bộ - Đúc tượng vạc",
        verification_status="expert_verified",
        license="Public Domain",
        rights_status="public_domain",
        url="https://archives.org.vn/hoidien-214",
    )
    db_session.add_all([source1, source2])
    db_session.flush()

    # Entity & Verified Claim
    entity = HistoricalEntity(
        entity_type="urn",
        slug=f"cao-dinh-{uuid.uuid4().hex[:6]}",
        name_vi="Cao Đỉnh",
        publication_status="published",
    )
    db_session.add(entity)
    db_session.flush()

    verified_claim = HistoricalClaim(
        entity_id=entity.id,
        claim_key=f"claim_verified_{uuid.uuid4().hex[:8]}",
        claim_type="historical_fact",
        statement_vi="Cao Đỉnh là chiếc đỉnh đầu tiên và quan trọng nhất trong Cửu Đỉnh nhà Nguyễn.",
        origin="editorial",
        verification_status="expert_verified",
        confidence="high",
    )
    unreviewed_claim = HistoricalClaim(
        entity_id=entity.id,
        claim_key=f"claim_unreviewed_{uuid.uuid4().hex[:8]}",
        claim_type="traditional_account",
        statement_vi="Truyền thuyết chưa kiểm chứng về nghệ nhân đúc đỉnh.",
        origin="community_submission",
        verification_status="unreviewed",
        confidence="low",
    )
    disputed_claim = HistoricalClaim(
        entity_id=entity.id,
        claim_key=f"claim_disputed_{uuid.uuid4().hex[:8]}",
        claim_type="interpretation",
        statement_vi="Khẳng định tranh cãi về niên đại hoàn thành phần quai đỉnh.",
        origin="web_crawl",
        verification_status="disputed",
        confidence="low",
    )
    db_session.add_all([verified_claim, unreviewed_claim, disputed_claim])
    db_session.flush()

    # Master Lesson Content (version 1)
    lesson = LessonContent(
        motif_id=motif.id,
        intro_text="Bài giảng chuẩn mực về hình tượng Rồng trên Cao Đỉnh.",
        description="Nội dung bài học nguyên bản phiên bản 1 — cơ sở khảo sát lịch sử.",
        historical_context="Đúc năm Minh Mạng thứ 16-17 (1835-1836).",
        symbolism="Tượng trưng cho vương quyền tối thượng và sự thống nhất của đất nước.",
        fun_fact="Rồng trên Cao Đỉnh có 5 móng chỉ dành riêng cho Hoàng đế.",
        version=1,
        is_published=True,
        content_validation_status="valid",
        status=ContentStatus.published,
        content_rating=ContentRating.everyone,
    )
    db_session.add(lesson)
    db_session.commit()
    db_session.refresh(lesson)

    return {
        "teacher": teacher,
        "other_teacher": other_teacher,
        "student": student,
        "outsider": outsider,
        "classroom": classroom,
        "other_classroom": other_classroom,
        "lesson": lesson,
        "sources": [source1, source2],
        "verified_claim": verified_claim,
        "unreviewed_claim": unreviewed_claim,
        "disputed_claim": disputed_claim,
    }


# =========================================================================== #
# Tests
# =========================================================================== #

def test_teacher_assigns_lesson_with_pinned_version_rubric_and_source_set(client, db_session):
    """Test 1: Teacher assigns a lesson with pinned version, rubric, and source set to a classroom."""
    ctx = _setup_test_context(db_session)
    teacher = ctx["teacher"]
    classroom = ctx["classroom"]
    lesson = ctx["lesson"]
    sources = ctx["sources"]
    verified_claim = ctx["verified_claim"]

    _login_user(client, teacher.email)

    custom_rubric = {
        "criteria": {
            "S1_SPATIAL": {"name": "Không gian", "max_points": 25, "weight": 0.25},
            "S2_TEMPORAL": {"name": "Thời gian", "max_points": 25, "weight": 0.25},
            "S3_EVIDENCE": {"name": "Chứng cứ nguồn sử", "max_points": 25, "weight": 0.25},
            "S4_ARGUMENT": {"name": "Lập luận", "max_points": 25, "weight": 0.25},
        },
        "max_score": 100,
    }

    payload = {
        "classroom_id": str(classroom.id),
        "lesson_id": str(lesson.id),
        "title": "Nhiệm vụ 1: Khảo sát hình tượng Rồng trên Cao Đỉnh",
        "instructions": "Học sinh đối chiếu hình tượng trên đỉnh với chép sử trong Đại Nam Thực Lục.",
        "due_at": "2026-11-20T23:59:59Z",
        "points": 100,
        "rubric": custom_rubric,
        "source_ids": [str(s.id) for s in sources],
        "claim_ids": [str(verified_claim.id)],
        "status": "draft",
    }

    res = client.post("/api/v1/history/assignments", json=payload)
    assert res.status_code == 201, res.text
    data = res.json()

    assert data["classroom_id"] == str(classroom.id)
    assert data["lesson_id"] == str(lesson.id)
    assert data["pinned_version"] == 1
    assert data["status"] == "draft"
    assert data["title"] == payload["title"]

    # Verify pinned lesson snapshot
    snapshot = data["pinned_lesson_snapshot"]
    assert snapshot["version"] == 1
    assert snapshot["description"] == lesson.description
    assert snapshot["symbolism"] == lesson.symbolism

    # Verify pinned rubric
    assert data["rubric"]["criteria"]["S1_SPATIAL"]["max_points"] == 25

    # Verify pinned source set
    assert set(data["pinned_source_ids"]) == {str(s.id) for s in sources}
    assert len(data["pinned_sources_snapshot"]) == 2
    source_titles = {s["title"] for s in data["pinned_sources_snapshot"]}
    assert "Đại Nam Thực Lục Chính Biên" in source_titles

    # Verify pinned claims
    assert data["pinned_claim_ids"] == [str(verified_claim.id)]


def test_negative_abuse_assignment_cannot_be_published_if_lesson_has_unverified_claims(
    client, db_session
):
    """Test 2: Negative abuse — Assignment cannot be published if lesson has unverified historical claims."""
    ctx = _setup_test_context(db_session)
    teacher = ctx["teacher"]
    classroom = ctx["classroom"]
    lesson = ctx["lesson"]
    unreviewed_claim = ctx["unreviewed_claim"]
    disputed_claim = ctx["disputed_claim"]

    _login_user(client, teacher.email)

    # Case A: Assignment draft with unreviewed claim fails publication gate
    res = client.post(
        "/api/v1/history/assignments",
        json={
            "classroom_id": str(classroom.id),
            "lesson_id": str(lesson.id),
            "title": "Assignment with unreviewed claim",
            "claim_ids": [str(unreviewed_claim.id)],
            "status": "draft",
        },
    )
    assert res.status_code == 201, res.text
    assignment_id = res.json()["id"]

    # Attempt to publish -> MUST be rejected with HTTP 422 ASSIGNMENT_UNVERIFIED_CLAIMS
    pub_res = client.post(f"/api/v1/history/assignments/{assignment_id}/publish")
    assert pub_res.status_code == 422, pub_res.text
    err = pub_res.json()["error"]
    assert err["code"] == "ASSIGNMENT_UNVERIFIED_CLAIMS"
    assert "unreviewed" in str(err["details"]).lower() or "ineligible" in str(err["details"]).lower()

    # Verify assignment status is STILL draft
    get_res = client.get(f"/api/v1/history/assignments/{assignment_id}")
    assert get_res.json()["status"] == "draft"

    # Case B: Assignment draft with disputed claim fails publication gate
    res_b = client.post(
        "/api/v1/history/assignments",
        json={
            "classroom_id": str(classroom.id),
            "lesson_id": str(lesson.id),
            "title": "Assignment with disputed claim",
            "claim_ids": [str(disputed_claim.id)],
            "status": "draft",
        },
    )
    assert res_b.status_code == 201
    assign_b_id = res_b.json()["id"]

    pub_res_b = client.post(f"/api/v1/history/assignments/{assign_b_id}/publish")
    assert pub_res_b.status_code == 422
    assert pub_res_b.json()["error"]["code"] == "ASSIGNMENT_UNVERIFIED_CLAIMS"

    # Case C: Creating an assignment directly with status='published' with unverified claims fails immediately
    create_pub_res = client.post(
        "/api/v1/history/assignments",
        json={
            "classroom_id": str(classroom.id),
            "lesson_id": str(lesson.id),
            "title": "Directly published with unverified claim",
            "claim_ids": [str(unreviewed_claim.id)],
            "status": "published",
        },
    )
    assert create_pub_res.status_code == 422
    assert create_pub_res.json()["error"]["code"] == "ASSIGNMENT_UNVERIFIED_CLAIMS"

    # Case D: Lesson blocked for authoritative learning prevents publication
    lesson.content_validation_status = "blocked_for_authoritative_learning"
    db_session.commit()

    res_d = client.post(
        "/api/v1/history/assignments",
        json={
            "classroom_id": str(classroom.id),
            "lesson_id": str(lesson.id),
            "title": "Assignment on blocked lesson",
            "claim_ids": [str(ctx["verified_claim"].id)],
            "status": "draft",
        },
    )
    assert res_d.status_code == 201
    assign_d_id = res_d.json()["id"]

    pub_res_d = client.post(f"/api/v1/history/assignments/{assign_d_id}/publish")
    assert pub_res_d.status_code == 422
    assert pub_res_d.json()["error"]["code"] == "ASSIGNMENT_UNVERIFIED_CLAIMS"


def test_assignment_publication_succeeds_when_all_claims_are_verified(client, db_session):
    """Test 3: Positive verification — Assignment publishes cleanly when all linked claims are verified."""
    ctx = _setup_test_context(db_session)
    teacher = ctx["teacher"]
    classroom = ctx["classroom"]
    lesson = ctx["lesson"]
    sources = ctx["sources"]
    verified_claim = ctx["verified_claim"]

    _login_user(client, teacher.email)

    res = client.post(
        "/api/v1/history/assignments",
        json={
            "classroom_id": str(classroom.id),
            "lesson_id": str(lesson.id),
            "title": "Khảo sát chứng cứ Cao Đỉnh chuẩn mực",
            "source_ids": [str(s.id) for s in sources],
            "claim_ids": [str(verified_claim.id)],
            "status": "draft",
        },
    )
    assert res.status_code == 201, res.text
    assignment_id = res.json()["id"]

    # Publish assignment
    pub_res = client.post(f"/api/v1/history/assignments/{assignment_id}/publish")
    assert pub_res.status_code == 200, pub_res.text
    pub_data = pub_res.json()

    assert pub_data["status"] == "published"
    assert pub_data["pinned_version"] == 1
    assert pub_data["published_at"] is not None
    assert pub_data["verified_claim_ids"] == [str(verified_claim.id)]
    assert set(pub_data["pinned_source_ids"]) == {str(s.id) for s in sources}

    # Verify via GET
    get_res = client.get(f"/api/v1/history/assignments/{assignment_id}")
    assert get_res.status_code == 200
    assert get_res.json()["status"] == "published"


def test_pinned_assessment_basis_immutable_when_master_lesson_edited_later(client, db_session):
    """Test 4: Pinned assessment basis invariant:
    Editing the master lesson later must not alter the submitted assessment basis for an existing assignment.
    """
    ctx = _setup_test_context(db_session)
    teacher = ctx["teacher"]
    student = ctx["student"]
    classroom = ctx["classroom"]
    lesson = ctx["lesson"]
    sources = ctx["sources"]
    verified_claim = ctx["verified_claim"]

    _login_user(client, teacher.email)

    # 1. Create and publish assignment under master lesson version 1
    create_res = client.post(
        "/api/v1/history/assignments",
        json={
            "classroom_id": str(classroom.id),
            "lesson_id": str(lesson.id),
            "title": "Chuyên đề khảo sát Rồng Cao Đỉnh V1",
            "source_ids": [str(sources[0].id)],
            "claim_ids": [str(verified_claim.id)],
            "status": "published",
        },
    )
    assert create_res.status_code == 201, create_res.text
    assignment_id = create_res.json()["id"]

    # 2. Student submits assignment response
    _login_user(client, student.email)
    submission_payload = {
        "submission_content": {
            "answer_text": "Hình tượng Rồng thời Minh Mạng được khắc họa uy nghiêm theo phong cách nhà Nguyễn.",
            "citations": [
                {"source_id": str(sources[0].id), "quote": "Đại Nam Thực Lục Chính Biên ghi nhận lễ đúc đỉnh"}
            ],
            "evidence_keys": [str(verified_claim.id)],
        }
    }
    sub_res = client.post(
        f"/api/v1/history/assignments/{assignment_id}/submit",
        json=submission_payload,
    )
    assert sub_res.status_code == 200, sub_res.text
    sub_data = sub_res.json()
    submission_id = sub_data["id"]

    # Verify initial submission captures assessment basis for version 1
    basis_at_submission = sub_data["assessment_basis_snapshot"]
    assert basis_at_submission["pinned_version"] == 1
    assert basis_at_submission["lesson_snapshot"]["description"] == (
        "Nội dung bài học nguyên bản phiên bản 1 — cơ sở khảo sát lịch sử."
    )

    # 3. Simulate another teacher or admin modifying the master lesson in the database
    lesson.version = 2
    lesson.description = "BẢN SỬA ĐỔI TOÀN DIỆN V2 — NỘI DUNG ĐÃ THAY ĐỔI HOÀN TOÀN!"
    lesson.historical_context = "Ngữ cảnh mới được cập nhật trong năm học sau."
    lesson.symbolism = "Ý nghĩa biểu tượng đã được tái phân tích."
    db_session.commit()
    db_session.refresh(lesson)

    assert lesson.version == 2
    assert lesson.description == "BẢN SỬA ĐỔI TOÀN DIỆN V2 — NỘI DUNG ĐÃ THAY ĐỔI HOÀN TOÀN!"

    # 4. Verify assignment's assessment basis remains 100% pinned to Version 1
    _login_user(client, teacher.email)
    basis_res = client.get(f"/api/v1/history/assignments/{assignment_id}/assessment-basis")
    assert basis_res.status_code == 200, basis_res.text
    basis_data = basis_res.json()

    assert basis_data["pinned_version"] == 1
    assert basis_data["lesson_snapshot"]["version"] == 1
    assert basis_data["lesson_snapshot"]["description"] == (
        "Nội dung bài học nguyên bản phiên bản 1 — cơ sở khảo sát lịch sử."
    )
    assert basis_data["lesson_snapshot"]["description"] != lesson.description

    # 5. Verify student submission's captured assessment basis is also unaltered
    get_sub_res = client.get(
        f"/api/v1/history/assignments/{assignment_id}/submissions/{submission_id}"
    )
    assert get_sub_res.status_code == 200, get_sub_res.text
    stored_sub = get_sub_res.json()

    assert stored_sub["assessment_basis_snapshot"]["pinned_version"] == 1
    assert stored_sub["assessment_basis_snapshot"]["lesson_snapshot"]["version"] == 1
    assert stored_sub["assessment_basis_snapshot"]["lesson_snapshot"]["description"] == (
        "Nội dung bài học nguyên bản phiên bản 1 — cơ sở khảo sát lịch sử."
    )


def test_submission_and_rubric_grading_workflow(client, db_session):
    """Test 5: Student submission, listing, and teacher grading using rubric criteria."""
    ctx = _setup_test_context(db_session)
    teacher = ctx["teacher"]
    student = ctx["student"]
    classroom = ctx["classroom"]
    lesson = ctx["lesson"]
    verified_claim = ctx["verified_claim"]

    _login_user(client, teacher.email)

    res = client.post(
        "/api/v1/history/assignments",
        json={
            "classroom_id": str(classroom.id),
            "lesson_id": str(lesson.id),
            "title": "Bài tập phân tích nguồn sử",
            "claim_ids": [str(verified_claim.id)],
            "status": "published",
        },
    )
    assert res.status_code == 201
    assignment_id = res.json()["id"]

    # Student submits
    _login_user(client, student.email)
    sub_res = client.post(
        f"/api/v1/history/assignments/{assignment_id}/submit",
        json={
            "submission_content": {
                "text": "Phân tích đối chiếu chỉ dụ của vua Minh Mạng...",
                "sources_used": ["Đại Nam Thực Lục"],
            }
        },
    )
    assert sub_res.status_code == 200, sub_res.text
    submission_id = sub_res.json()["id"]
    assert sub_res.json()["status"] == "submitted"

    # Teacher lists submissions
    _login_user(client, teacher.email)
    list_subs_res = client.get(f"/api/v1/history/assignments/{assignment_id}/submissions")
    assert list_subs_res.status_code == 200
    subs_list = list_subs_res.json()
    assert subs_list["total"] == 1
    assert subs_list["items"][0]["id"] == submission_id

    # Teacher grades submission using rubric evaluation
    grade_res = client.post(
        f"/api/v1/history/assignments/{assignment_id}/submissions/{submission_id}/grade",
        json={
            "score": 94.5,
            "rubric_evaluation": {
                "S1_SPATIAL": 24,
                "S2_TEMPORAL": 24,
                "S3_EVIDENCE": 23,
                "S4_ARGUMENT": 23.5,
            },
            "teacher_feedback": "Bài làm xuất sắc, phân tích sâu sắc các tài liệu mộc bản và châu bản.",
        },
    )
    assert grade_res.status_code == 200, grade_res.text
    graded_data = grade_res.json()

    assert graded_data["status"] == "graded"
    assert graded_data["score"] == 94.5
    assert graded_data["rubric_evaluation"]["S1_SPATIAL"] == 24
    assert "châu bản" in graded_data["teacher_feedback"]
    assert graded_data["graded_by_id"] == str(teacher.id)
    assert graded_data["graded_at"] is not None


def test_assignment_access_control_and_permissions(client, db_session):
    """Test 6: Access control — learners cannot create/publish assignments, cross-class isolation."""
    ctx = _setup_test_context(db_session)
    teacher = ctx["teacher"]
    other_teacher = ctx["other_teacher"]
    student = ctx["student"]
    outsider = ctx["outsider"]
    classroom = ctx["classroom"]
    lesson = ctx["lesson"]
    verified_claim = ctx["verified_claim"]

    # 1. Learner cannot create assignment
    _login_user(client, student.email)
    create_res = client.post(
        "/api/v1/history/assignments",
        json={
            "classroom_id": str(classroom.id),
            "lesson_id": str(lesson.id),
            "title": "Học sinh tự tạo bài tập",
            "status": "draft",
        },
    )
    assert create_res.status_code == 403
    assert create_res.json()["error"]["code"] == "FORBIDDEN"

    # 2. Teacher cannot create assignment for a classroom taught by another teacher
    _login_user(client, other_teacher.email)
    other_create_res = client.post(
        "/api/v1/history/assignments",
        json={
            "classroom_id": str(classroom.id),
            "lesson_id": str(lesson.id),
            "title": "Giáo viên khác tạo bài tập lớp 10A1",
            "status": "draft",
        },
    )
    assert other_create_res.status_code == 403
    assert other_create_res.json()["error"]["code"] == "FORBIDDEN"

    # 3. Create published assignment for classroom
    _login_user(client, teacher.email)
    assign_res = client.post(
        "/api/v1/history/assignments",
        json={
            "classroom_id": str(classroom.id),
            "lesson_id": str(lesson.id),
            "title": "Bài tập lớp 10A1",
            "claim_ids": [str(verified_claim.id)],
            "status": "published",
        },
    )
    assert assign_res.status_code == 201
    assignment_id = assign_res.json()["id"]

    # 4. Outsider student cannot submit to this classroom assignment
    _login_user(client, outsider.email)
    submit_res = client.post(
        f"/api/v1/history/assignments/{assignment_id}/submit",
        json={"submission_content": {"text": "Học sinh ngoài lớp nộp trộm"}},
    )
    assert submit_res.status_code == 403
    assert submit_res.json()["error"]["code"] == "NOT_CLASS_MEMBER"
