# -*- coding: utf-8 -*-
"""V5-T040: Classroom Comprehensive End-to-End Integration Acceptance Suite.

Wave W03, Slot A10 (Priority: P0, Classification: PRODUCTION_COMPLETION).
Verifies complete multi-school / multi-classroom lifecycle:
1. School A & School B setup with distinct teachers and classes.
2. Teacher A assigns source-locked lesson with rubric and verified claims.
3. Student A enrolls via join code and submits work.
4. Teacher A reviews and grades submission via rubric with feedback.
5. Student A inspects grade, rubric evaluation, and feedback.
6. Teacher A exports gradebook CSV.
7. Multi-tenant isolation:
   - Teacher B / Student B cannot view or modify School A data.
   - Cross-school / cross-classroom mutation attempts return 403 Forbidden.
   - Enrolled lists, gradebooks, and exports strictly maintain school boundaries.
8. Negative & abuse guardrails:
   - Submissions to unpublished assignments are rejected (400).
   - Non-members cannot submit to assignments (403).
   - Non-teachers cannot grade submissions (403).
   - Random/fake join codes are rejected (400).
"""
from __future__ import annotations

import csv
import io
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
import pytest
from sqlalchemy import select

from backend.models import (
    ClassMember,
    Classroom,
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


# --------------------------------------------------------------------------- #
# Helper Fixtures & Setup Functions
# --------------------------------------------------------------------------- #

def _create_user(
    db_session,
    email: str,
    role: UserRole = UserRole.learner,
    display_name: str | None = None,
) -> User:
    """Create a verified test user with given role and unique username."""
    user = User(
        email=email,
        password_hash=hash_password("Password123!"),
        display_name=display_name or f"User {email.split('@')[0]}",
        username=f"usr_{uuid.uuid4().hex[:8]}",
        role=role,
        is_profile_public=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _login_user(client, email: str, password: str = "Password123!") -> dict:
    """Authenticate user via login endpoint and set session cookie."""
    res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    return res.json()


def _seed_source_locked_prerequisites(db_session):
    """Seed historical entity, verified claim, source, urn, and lesson for assignments."""
    urn = Urn(
        slug=f"urn-e2e-{uuid.uuid4().hex[:6]}",
        name="Cao Đỉnh",
        model_url="/models/cao_dinh.glb",
        display_order=1,
    )
    db_session.add(urn)
    db_session.flush()

    motif = Motif(
        urn_id=urn.id,
        mesh_name=f"mesh_rong_may_{uuid.uuid4().hex[:6]}",
        name=f"Họa tiết Rồng Mây {uuid.uuid4().hex[:4]}",
        category=MotifCategory.linh_thu,
        rarity=MotifRarity.legendary,
        pos_x=0.0,
        pos_y=0.0,
        pos_z=0.0,
        bounding_radius=1.0,
    )
    db_session.add(motif)
    db_session.flush()

    entity = HistoricalEntity(
        slug=f"ent-cao-dinh-{uuid.uuid4().hex[:6]}",
        entity_type="monument",
        name_vi="Cao Đỉnh",
        summary_vi="Đỉnh đồng đúc thời Minh Mạng.",
    )
    db_session.add(entity)
    db_session.flush()

    source = HistoricalSource(
        title="Đại Nam Thực Lục Chính Biên",
        author_text="Quốc sử quán triều Nguyễn",
        source_type="primary",
        publication_year=1844,
        citation_text="Đại Nam Thực Lục Chính Biên, Đệ nhị kỷ, Quyển 98.",
        rights_status="public_domain",
        license="CC-BY-4.0",
        verification_status="expert_verified",
        checksum=uuid.uuid4().hex,
        excerpt="Tháng 3 năm Quý Tỵ (1833), dựng cổng Ngọ Môn trổ 5 cửa...",
    )
    db_session.add(source)
    db_session.flush()

    claim = HistoricalClaim(
        claim_key=f"claim-rong-may-{uuid.uuid4().hex[:6]}",
        claim_type="symbolism",
        statement_vi="Rồng năm móng trên Cao Đỉnh biểu thị vương quyền tối cao của Thiên tử.",
        entity_id=entity.id,
        verification_status="expert_verified",
        confidence="high",
        origin="authoritative_import",
    )
    db_session.add(claim)
    db_session.flush()

    lesson = LessonContent(
        motif_id=motif.id,
        version=1,
        description="Khảo sát biểu tượng Rồng trên Cửu Đỉnh.",
        intro_text="Giới thiệu ý nghĩa rồng mây trong mỹ thuật cung đình.",
        historical_context="Triều Nguyễn đúc Cửu Đỉnh năm 1835-1837.",
        symbolism="Quyền lực và thái bình thịnh trị.",
        fun_fact="Cao Đỉnh nặng nhất trong 9 đỉnh đồng.",
        status=ContentStatus.published,
        content_validation_status="verified",
        is_published=True,
    )
    db_session.add(lesson)
    db_session.commit()
    db_session.refresh(lesson)
    db_session.refresh(source)
    db_session.refresh(claim)

    return {
        "urn": urn,
        "motif": motif,
        "entity": entity,
        "source": source,
        "claim": claim,
        "lesson": lesson,
    }


# --------------------------------------------------------------------------- #
# Test 1: Full Lifecycle E2E Test
# --------------------------------------------------------------------------- #

def test_full_classroom_lifecycle_e2e(client, db_session):
    """E2E Test: Setup -> Assign -> Enroll -> Submit -> Grade -> Inspect -> Export."""
    # 1. Setup School A & School B Teachers & Students
    teacher_a = _create_user(db_session, "teacher_a_e2e@school-a.edu.vn", role=UserRole.teacher, display_name="Thầy Nguyễn Văn A")
    teacher_b = _create_user(db_session, "teacher_b_e2e@school-b.edu.vn", role=UserRole.teacher, display_name="Cô Lê Thị B")
    student_a = _create_user(db_session, "student_a_e2e@school-a.edu.vn", role=UserRole.learner, display_name="Học sinh Trần Văn Nam")
    student_b = _create_user(db_session, "student_b_e2e@school-b.edu.vn", role=UserRole.learner, display_name="Học sinh Hoàng Thị Mai")

    # Seed lesson prerequisites
    prereqs = _seed_source_locked_prerequisites(db_session)
    lesson = prereqs["lesson"]
    source = prereqs["source"]
    claim = prereqs["claim"]

    # 1. Teacher A creates Classroom A
    _login_user(client, teacher_a.email)
    res_create_a = client.post(
        "/api/v1/classrooms",
        json={
            "name": "Lớp 11 Sử — THPT Chuyên Quốc Học Huế",
            "description": "Chuyên đề khảo sát di sản Cửu Đỉnh và Hoàng Thành Huế",
            "max_students": 35,
            "settings": {"school_name": "THPT Chuyên Quốc Học Huế", "academic_year": "2026-2027"},
        },
    )
    assert res_create_a.status_code == 201, res_create_a.text
    class_a_data = res_create_a.json()
    class_a_id = class_a_data["id"]
    class_a_code = class_a_data["class_code"]
    assert class_a_code and len(class_a_code) == 8

    # Teacher B creates Classroom B
    _login_user(client, teacher_b.email)
    res_create_b = client.post(
        "/api/v1/classrooms",
        json={
            "name": "Lớp 10 Văn — THPT Hai Bà Trưng Huế",
            "description": "Lớp văn học và di sản văn hóa Huế",
            "max_students": 30,
            "settings": {"school_name": "THPT Hai Bà Trưng Huế", "academic_year": "2026-2027"},
        },
    )
    assert res_create_b.status_code == 201
    class_b_id = res_create_b.json()["id"]

    # 2. Student A joins Classroom A using join code
    _login_user(client, student_a.email)
    res_join = client.post(
        "/api/v1/classrooms/join",
        json={"class_code": class_a_code},
    )
    assert res_join.status_code == 200, res_join.text
    join_data = res_join.json()
    assert join_data["classroom"]["id"] == class_a_id
    assert any(m["user_id"] == str(student_a.id) for m in join_data["classroom"]["members"])

    # Verify student is in enrolled classrooms
    res_enrolled = client.get("/api/v1/classrooms/enrolled")
    assert res_enrolled.status_code == 200
    enrolled_ids = [c["id"] for c in res_enrolled.json()]
    assert class_a_id in enrolled_ids
    assert class_b_id not in enrolled_ids

    # 3. Teacher A assigns source-locked lesson to Classroom A
    _login_user(client, teacher_a.email)
    rubric_def = {
        "criteria": [
            {"id": "S1_spatial", "title": "Năng lực không gian", "max_score": 3},
            {"id": "S2_temporal", "title": "Năng lực thời gian", "max_score": 3},
            {"id": "S3_evidence", "title": "Năng lực sử liệu", "max_score": 3},
            {"id": "S4_argument", "title": "Năng lực lập luận", "max_score": 3},
        ]
    }
    due_date = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    res_assign = client.post(
        "/api/v1/history/assignments",
        json={
            "classroom_id": class_a_id,
            "lesson_id": str(lesson.id),
            "title": "Khảo sát biểu tượng quyền lực trên Cao Đỉnh",
            "instructions": "Phân tích trật tự phân tầng không gian và trích dẫn bằng chứng từ Đại Nam Thực Lục.",
            "due_at": due_date,
            "points": 100,
            "rubric": rubric_def,
            "source_ids": [str(source.id)],
            "claim_ids": [str(claim.id)],
            "status": "draft",
        },
    )
    assert res_assign.status_code == 201, res_assign.text
    assignment_id = res_assign.json()["id"]
    assert res_assign.json()["status"] == "draft"

    # Teacher A publishes the assignment (enforcing claim verification gate)
    res_publish = client.post(f"/api/v1/history/assignments/{assignment_id}/publish")
    assert res_publish.status_code == 200, res_publish.text
    assert res_publish.json()["status"] == "published"
    assert res_publish.json()["verified_claim_ids"] == [str(claim.id)]

    # Verify immutable assessment basis snapshot exists
    res_basis = client.get(f"/api/v1/history/assignments/{assignment_id}/assessment-basis")
    assert res_basis.status_code == 200
    basis_data = res_basis.json()
    assert basis_data["pinned_version"] == 1
    assert basis_data["pinned_claim_ids"] == [str(claim.id)]
    assert len(basis_data["pinned_sources"]) == 1

    # 4. Student A inspects published assignments and submits work
    _login_user(client, student_a.email)
    res_student_assigns = client.get(f"/api/v1/history/assignments?classroom_id={class_a_id}")
    assert res_student_assigns.status_code == 200
    assert any(a["id"] == assignment_id for a in res_student_assigns.json()["items"])

    submission_payload = {
        "submission_content": {
            "claim": "Cao Đỉnh ngự ở vị trí trung tâm thể hiện vị thế độc tôn của vua Minh Mạng.",
            "evidence": "Trích Đại Nam Thực Lục: Tháng 3 năm Quý Tỵ dựng cổng Ngọ Môn và đúc Cửu Đỉnh.",
            "explanation": "Vị trí chính giữa ứng với quẻ Càn trong Kinh Dịch biểu thị uy quyền tối thượng.",
            "answer_text": "Bài làm hoàn chỉnh khảo sát biểu tượng quyền lực trên Cao Đỉnh.",
        }
    }
    res_submit = client.post(
        f"/api/v1/history/assignments/{assignment_id}/submit",
        json=submission_payload,
    )
    assert res_submit.status_code == 200, res_submit.text
    submission_data = res_submit.json()
    submission_id = submission_data["id"]
    assert submission_data["status"] == "submitted"
    assert submission_data["student_id"] == str(student_a.id)
    assert submission_data["assessment_basis_snapshot"]["pinned_claim_ids"] == [str(claim.id)]

    # 5. Teacher A reviews submission and grades via rubric
    _login_user(client, teacher_a.email)
    res_submissions_list = client.get(f"/api/v1/history/assignments/{assignment_id}/submissions")
    assert res_submissions_list.status_code == 200
    assert res_submissions_list.json()["total"] == 1
    assert res_submissions_list.json()["items"][0]["id"] == submission_id

    grade_payload = {
        "score": 9.5,
        "rubric_evaluation": {
            "S1_spatial": 3,
            "S2_temporal": 2,
            "S3_evidence": 3,
            "S4_argument": 3,
            "total_raw": 11,
            "normalized_10": 9.5,
        },
        "teacher_feedback": "Phân tích trật tự không gian rất sâu sắc, trích dẫn chuẩn xác Đại Nam Thực Lục.",
    }
    res_grade = client.post(
        f"/api/v1/history/assignments/{assignment_id}/submissions/{submission_id}/grade",
        json=grade_payload,
    )
    assert res_grade.status_code == 200, res_grade.text
    graded_data = res_grade.json()
    assert graded_data["status"] == "graded"
    assert graded_data["score"] == 9.5
    assert graded_data["rubric_evaluation"]["S1_spatial"] == 3
    assert graded_data["teacher_feedback"] == "Phân tích trật tự không gian rất sâu sắc, trích dẫn chuẩn xác Đại Nam Thực Lục."
    assert graded_data["graded_by_id"] == str(teacher_a.id)

    # 6. Student A inspects graded submission & feedback
    _login_user(client, student_a.email)
    res_student_view = client.get(
        f"/api/v1/history/assignments/{assignment_id}/submissions/{submission_id}"
    )
    assert res_student_view.status_code == 200
    st_sub = res_student_view.json()
    assert st_sub["status"] == "graded"
    assert st_sub["score"] == 9.5
    assert "trích dẫn chuẩn xác" in st_sub["teacher_feedback"]

    # 7. Teacher A exports gradebook CSV for Classroom A
    _login_user(client, teacher_a.email)
    res_export = client.get(f"/api/v1/classrooms/{class_a_id}/export")
    assert res_export.status_code == 200, res_export.text
    assert "text/csv" in res_export.headers.get("content-type", "")
    assert f"classroom_{class_a_id}_progress.csv" in res_export.headers.get("content-disposition", "")

    csv_text = res_export.text.lstrip("\ufeff")
    csv_reader = csv.reader(io.StringIO(csv_text))
    rows = list(csv_reader)
    assert len(rows) >= 2, "Expected header and at least one student row"
    header = rows[0]
    assert "Student ID" in header
    assert "Display Name" in header
    assert "Total XP" in header

    # Student A's row exists in export
    student_row = next((r for r in rows[1:] if r[0] == str(student_a.id)), None)
    assert student_row is not None
    assert student_row[1] == "Học sinh Trần Văn Nam"


# --------------------------------------------------------------------------- #
# Test 2: Strict Multi-Tenant Isolation
# --------------------------------------------------------------------------- #

def test_multi_school_multi_classroom_isolation(client, db_session):
    """Verify strict tenant isolation: School/Teacher B cannot view or tamper with School A data."""
    # Setup School A and School B users
    teacher_a = _create_user(db_session, "tenant_teacher_a@school-a.edu.vn", role=UserRole.teacher)
    teacher_b = _create_user(db_session, "tenant_teacher_b@school-b.edu.vn", role=UserRole.teacher)
    student_a = _create_user(db_session, "tenant_student_a@school-a.edu.vn", role=UserRole.learner)
    student_b = _create_user(db_session, "tenant_student_b@school-b.edu.vn", role=UserRole.learner)

    prereqs = _seed_source_locked_prerequisites(db_session)

    # Teacher A creates class A
    _login_user(client, teacher_a.email)
    res_a = client.post(
        "/api/v1/classrooms",
        json={"name": "School A History Honors", "description": "School A", "max_students": 25},
    )
    class_a_id = res_a.json()["id"]
    class_a_code = res_a.json()["class_code"]

    # Student A joins class A
    _login_user(client, student_a.email)
    client.post("/api/v1/classrooms/join", json={"class_code": class_a_code})

    # Teacher A creates assignment in class A
    _login_user(client, teacher_a.email)
    res_assign_a = client.post(
        "/api/v1/history/assignments",
        json={
            "classroom_id": class_a_id,
            "lesson_id": str(prereqs["lesson"].id),
            "title": "School A Assignment",
            "points": 100,
            "claim_ids": [str(prereqs["claim"].id)],
            "status": "published",
        },
    )
    assignment_a_id = res_assign_a.json()["id"]

    # Student A submits to assignment A
    _login_user(client, student_a.email)
    res_sub_a = client.post(
        f"/api/v1/history/assignments/{assignment_a_id}/submit",
        json={
            "submission_content": {
                "claim": "Claim A",
                "evidence": "Evidence A",
                "explanation": "Explanation A",
            }
        },
    )
    submission_a_id = res_sub_a.json()["id"]

    # ---------------------------------------------------------
    # Multi-tenant Isolation Assertions for Teacher B (School B)
    # ---------------------------------------------------------
    _login_user(client, teacher_b.email)

    # 1. Teacher B cannot view Classroom A details
    res_b_view_class_a = client.get(f"/api/v1/classrooms/{class_a_id}")
    assert res_b_view_class_a.status_code == 403, f"Expected 403, got {res_b_view_class_a.status_code}"

    # 2. Teacher B cannot list Classroom A in their classroom list
    res_b_list = client.get("/api/v1/classrooms")
    assert res_b_list.status_code == 200
    assert not any(c["id"] == class_a_id for c in res_b_list.json())

    # 3. Teacher B cannot export Classroom A gradebook CSV
    res_b_export = client.get(f"/api/v1/classrooms/{class_a_id}/export")
    assert res_b_export.status_code == 403

    # 4. Teacher B cannot view submissions for Assignment A
    res_b_subs = client.get(f"/api/v1/history/assignments/{assignment_a_id}/submissions")
    assert res_b_subs.status_code == 403

    # 5. Teacher B cannot grade Submission A
    res_b_grade = client.post(
        f"/api/v1/history/assignments/{assignment_a_id}/submissions/{submission_a_id}/grade",
        json={"score": 10.0, "teacher_feedback": "Unauthorized Grade Attempt"},
    )
    assert res_b_grade.status_code == 403

    # 6. Teacher B cannot create an assignment inside Classroom A
    res_b_tamper_assign = client.post(
        "/api/v1/history/assignments",
        json={
            "classroom_id": class_a_id,
            "lesson_id": str(prereqs["lesson"].id),
            "title": "Tampered Assignment",
            "points": 100,
        },
    )
    assert res_b_tamper_assign.status_code == 403

    # ---------------------------------------------------------
    # Multi-tenant Isolation Assertions for Student B (School B)
    # ---------------------------------------------------------
    _login_user(client, student_b.email)

    # 7. Student B (not in Class A) cannot view Student A's submission
    res_st_b_view_sub = client.get(
        f"/api/v1/history/assignments/{assignment_a_id}/submissions/{submission_a_id}"
    )
    assert res_st_b_view_sub.status_code == 403

    # 8. Student B cannot submit to Assignment A without enrollment
    res_st_b_submit = client.post(
        f"/api/v1/history/assignments/{assignment_a_id}/submit",
        json={
            "submission_content": {
                "claim": "Unauthorized Claim",
                "evidence": "Unauthorized Evidence",
                "explanation": "Unauthorized Explanation",
            }
        },
    )
    assert res_st_b_submit.status_code == 403
    assert res_st_b_submit.json()["error"]["code"] == "NOT_CLASS_MEMBER"


# --------------------------------------------------------------------------- #
# Test 3: Negative and Abuse Guardrails
# --------------------------------------------------------------------------- #

def test_negative_and_abuse_guardrails(client, db_session):
    """Negative abuse testing: unpublished submissions, non-members, fake codes, and invalid data."""
    teacher = _create_user(db_session, "guardrail_teacher@school.edu.vn", role=UserRole.teacher)
    student = _create_user(db_session, "guardrail_student@school.edu.vn", role=UserRole.learner)
    prereqs = _seed_source_locked_prerequisites(db_session)

    # Teacher creates classroom
    _login_user(client, teacher.email)
    res_c = client.post(
        "/api/v1/classrooms",
        json={"name": "Guardrail Classroom", "max_students": 10},
    )
    class_id = res_c.json()["id"]

    # Negative 1: Join with invalid/non-existent code returns 400
    _login_user(client, student.email)
    res_fake_code = client.post("/api/v1/classrooms/join", json={"class_code": "NONEXIST"})
    assert res_fake_code.status_code == 400

    # Negative 2: Student submits to draft/unpublished assignment returns 400
    _login_user(client, teacher.email)
    res_draft_assign = client.post(
        "/api/v1/history/assignments",
        json={
            "classroom_id": class_id,
            "lesson_id": str(prereqs["lesson"].id),
            "title": "Draft Assignment",
            "status": "draft",
        },
    )
    draft_id = res_draft_assign.json()["id"]

    # Student joins class legitimately
    class_code = res_c.json()["class_code"]
    _login_user(client, student.email)
    client.post("/api/v1/classrooms/join", json={"class_code": class_code})

    # Student attempts submitting to draft
    res_sub_draft = client.post(
        f"/api/v1/history/assignments/{draft_id}/submit",
        json={
            "submission_content": {
                "claim": "Claim Draft",
                "evidence": "Evidence Draft",
                "explanation": "Explanation Draft",
            }
        },
    )
    assert res_sub_draft.status_code == 400
    assert res_sub_draft.json()["error"]["code"] == "ASSIGNMENT_NOT_PUBLISHED"

    # Negative 3: Student attempts submitting empty / invalid M-E-E content returns 422
    _login_user(client, teacher.email)
    client.post(f"/api/v1/history/assignments/{draft_id}/publish")

    _login_user(client, student.email)
    res_empty_submit = client.post(
        f"/api/v1/history/assignments/{draft_id}/submit",
        json={"submission_content": {}},
    )
    assert res_empty_submit.status_code == 422
    assert res_empty_submit.json()["error"]["code"] == "INVALID_SUBMISSION_CONTENT"

    # Negative 4: Learner attempts to grade a submission returns 403
    res_valid_submit = client.post(
        f"/api/v1/history/assignments/{draft_id}/submit",
        json={
            "submission_content": {
                "claim": "Valid Claim",
                "evidence": "Valid Evidence",
                "explanation": "Valid Explanation",
            }
        },
    )
    sub_id = res_valid_submit.json()["id"]

    res_learner_grade = client.post(
        f"/api/v1/history/assignments/{draft_id}/submissions/{sub_id}/grade",
        json={"score": 10.0, "teacher_feedback": "Self Grade Attempt"},
    )
    assert res_learner_grade.status_code == 403
    assert res_learner_grade.json()["error"]["code"] == "FORBIDDEN"
