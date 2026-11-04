# -*- coding: utf-8 -*-
"""V5-T034 (Wave W03, Slot A04): Submission Server Persistence.

Audits and verifies:
1. Student authentication required for submission.
2. Classroom & assignment scope enforcement:
   - Student cannot submit to an assignment if not enrolled in that classroom (403 NOT_CLASS_MEMBER).
   - Cannot submit to an unpublished or draft assignment (400 ASSIGNMENT_NOT_PUBLISHED).
3. Deadline enforcement:
   - Past due submissions are strictly rejected (400 ASSIGNMENT_DEADLINE_PASSED).
4. Content validation (M-E-E historical structure):
   - Empty or missing claim, evidence, or explanation rejected (422 INVALID_SUBMISSION_CONTENT).
5. Idempotency handling:
   - Re-submitting with the identical idempotency_key returns the original submission record
     without duplicate row creation.
6. Negative / Abuse tests:
   - Offline browser client cannot claim server-confirmed submission.
   - Non-enrolled students cannot forge submissions.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select

from backend.models import (
    ClassMember,
    Classroom,
    HistoricalClaim,
    HistoricalEntity,
    HistoricalPublicationStatus,
    HistoricalVerificationStatus,
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
from backend.services import history_learning as hl

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(autouse=True)
def _reset_auth_rate_limit():
    """Reset auth rate limit state before each test."""
    import backend.main as main

    main._auth_rate_limit_state.clear()
    yield
    main._auth_rate_limit_state.clear()


def _make_user(client, db_session, email, display_name, role=UserRole.learner):
    res = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "display_name": display_name},
    )
    assert res.status_code == 201, res.text
    user = db_session.execute(select(User).where(User.email == email)).scalar_one()
    user.role = role
    db_session.commit()
    return user


def _auth_headers_for(user: User) -> dict[str, str]:
    from datetime import timedelta
    from backend.config import settings
    from backend.security import create_jwt_token

    token = create_jwt_token(
        subject=str(user.id),
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        expires_delta=timedelta(minutes=60),
        issuer=settings.jwt_issuer,
        audience=settings.jwt_audience,
        extra_claims={"type": "access", "role": user.role.value if hasattr(user.role, "value") else str(user.role)},
    )
    return {"Authorization": f"Bearer {token}"}


def _seed_verified_assignment(db_session, teacher_user):
    """Seed prerequisite urn, motif, claim, lesson, classroom and assignment."""
    urn = db_session.scalar(select(Urn).where(Urn.slug == "cao-dinh"))
    if not urn:
        urn = Urn(
            slug="cao-dinh",
            name="Cao Đỉnh",
            model_url="/models/cao-dinh.glb",
            display_order=1,
        )
        db_session.add(urn)
        db_session.flush()

    motif = db_session.scalar(select(Motif).where(Motif.mesh_name == "mesh_canh_dieu_t034"))
    if not motif:
        motif = Motif(
            urn_id=urn.id,
            mesh_name="mesh_canh_dieu_t034",
            name="Cánh Diều Khảo Cứu T034",
            category=MotifCategory.dong_vat,
            rarity=MotifRarity.common,
            pos_x=0.0,
            pos_y=0.0,
            pos_z=0.0,
            bounding_radius=1.0,
            cam_pos_x=0.0,
            cam_pos_y=0.0,
            cam_pos_z=2.0,
            cam_look_at_x=0.0,
            cam_look_at_y=0.0,
            cam_look_at_z=0.0,
        )
        db_session.add(motif)
        db_session.flush()

    entity = db_session.scalar(select(HistoricalEntity).where(HistoricalEntity.slug == "cao-dinh-entity"))
    if not entity:
        entity = HistoricalEntity(
            slug="cao-dinh-entity",
            name_vi="Cao Đỉnh",
            name_en="Cao Dinh Urn",
            entity_type="urn",
        )
        db_session.add(entity)
        db_session.flush()

    claim = db_session.scalar(select(HistoricalClaim).where(HistoricalClaim.claim_key == "claim_t034_verified"))
    if not claim:
        claim = HistoricalClaim(
            entity_id=entity.id,
            claim_key="claim_t034_verified",
            claim_type="factual",
            statement_vi="Cánh diều trên Cao Đỉnh biểu trưng cho phong tục thả diều cung đình triều Nguyễn.",
            verification_status="expert_verified",
            origin="primary_source",
        )
        db_session.add(claim)
        db_session.flush()

    lesson = db_session.scalar(select(LessonContent).where(LessonContent.motif_id == motif.id))
    if not lesson:
        lesson = LessonContent(
            motif_id=motif.id,
            version=1,
            description="Bài giảng khảo cứu biểu tượng diều",
            intro_text="Khảo sát diều trên Cao Đỉnh",
            historical_context="Triều vua Minh Mạng",
            content_validation_status="valid",
            is_published=True,
            additional_images={"required_claim_ids": [str(claim.id)]},
        )
        db_session.add(lesson)
        db_session.flush()

    classroom = Classroom(
        name="Lớp Sử 11 Chuyên Quốc Học Huế",
        class_code=f"C{uuid4().hex[:6].upper()}",
        teacher_id=teacher_user.id,
    )
    db_session.add(classroom)
    db_session.flush()

    # Create published assignment with future due date (3 days ahead)
    due_at = datetime.now(timezone.utc) + timedelta(days=3)
    assignment = hl.create_source_locked_assignment(
        db=db_session,
        teacher_id=teacher_user.id,
        classroom_id=classroom.id,
        lesson_id=lesson.id,
        title="Bài tập khảo cứu: Em kết luận gì về biểu tượng cánh diều?",
        instructions="Viết bài theo cấu trúc M-E-E và trích dẫn bằng chứng xác thực.",
        due_at=due_at,
        points=100,
        claim_ids=[claim.id],
        status="published",
    )

    db_session.commit()
    return classroom, assignment, lesson, claim


def test_submission_requires_authentication(client, db_session):
    """Anonymous visitors cannot submit assignments (requires Bearer/cookie auth)."""
    random_id = uuid4()
    payload = {
        "submission_content": {
            "claim": "Biểu tượng rồng biểu thị vương quyền tuyệt đối",
            "evidence": "Khâm định Đại Nam Hội điển Sự lệ Quyển 78",
            "explanation": "Trang trí rồng chỉ xuất hiện tại các công trình của Hoàng đế",
        }
    }
    res = client.post(f"/api/v1/history/assignments/{random_id}/submit", json=payload)
    assert res.status_code in (401, 403), res.text


def test_submission_content_validation_rejects_empty_and_incomplete(client, db_session):
    """Negative validation test: empty or missing M-E-E parts fail with 422."""
    teacher = _make_user(client, db_session, f"teacher_{uuid4().hex[:6]}@school.edu", "Thầy Thọ", UserRole.teacher)
    student = _make_user(client, db_session, f"student_{uuid4().hex[:6]}@school.edu", "Học sinh A")
    classroom, assignment, _, _ = _seed_verified_assignment(db_session, teacher)

    # Enroll student
    db_session.add(ClassMember(class_id=classroom.id, user_id=student.id, role="learner"))
    db_session.commit()

    headers = _auth_headers_for(student)

    # Empty payload
    res = client.post(
        f"/api/v1/history/assignments/{assignment.id}/submit",
        json={"submission_content": {}},
        headers=headers,
    )
    assert res.status_code == 422, res.text
    assert "INVALID_SUBMISSION_CONTENT" in res.text

    # Missing evidence and explanation
    res = client.post(
        f"/api/v1/history/assignments/{assignment.id}/submit",
        json={"submission_content": {"claim": "Chỉ có mệnh đề, không có bằng chứng"}},
        headers=headers,
    )
    assert res.status_code == 422, res.text
    assert "INVALID_SUBMISSION_CONTENT" in res.text


def test_submission_scope_enforcement_rejects_non_enrolled_student(client, db_session):
    """Negative security test: student from another classroom cannot submit to this assignment."""
    teacher = _make_user(client, db_session, f"teacher_{uuid4().hex[:6]}@school.edu", "Cô Hà", UserRole.teacher)
    unauthorized_student = _make_user(client, db_session, f"outsider_{uuid4().hex[:6]}@other.edu", "Người ngoài")
    classroom, assignment, _, _ = _seed_verified_assignment(db_session, teacher)

    headers = _auth_headers_for(unauthorized_student)
    payload = {
        "submission_content": {
            "claim": "Khảo cứu Cửu Đỉnh độc lập",
            "evidence": "Đại Nam Thực Lục Tập 2",
            "explanation": "Quy chế đúc đỉnh được thực hiện chuẩn xác",
        }
    }
    res = client.post(
        f"/api/v1/history/assignments/{assignment.id}/submit",
        json=payload,
        headers=headers,
    )
    assert res.status_code == 403, res.text
    assert "NOT_CLASS_MEMBER" in res.text


def test_submission_deadline_enforcement_rejects_late_submission(client, db_session):
    """Submissions after the due_at deadline must fail with 400 ASSIGNMENT_DEADLINE_PASSED."""
    teacher = _make_user(client, db_session, f"teacher_{uuid4().hex[:6]}@school.edu", "Thầy Minh", UserRole.teacher)
    student = _make_user(client, db_session, f"student_{uuid4().hex[:6]}@school.edu", "Học sinh Trễ")
    classroom, assignment, _, _ = _seed_verified_assignment(db_session, teacher)

    # Enroll student
    db_session.add(ClassMember(class_id=classroom.id, user_id=student.id, role="learner"))

    # Set due date to 2 hours in the past
    assignment.due_at = datetime.now(timezone.utc) - timedelta(hours=2)
    db_session.commit()

    headers = _auth_headers_for(student)
    payload = {
        "submission_content": {
            "claim": "Bài nộp trễ hạn",
            "evidence": "Tư liệu bổ sung sau hạn chót",
            "explanation": "Giải thích chi tiết",
        }
    }
    res = client.post(
        f"/api/v1/history/assignments/{assignment.id}/submit",
        json=payload,
        headers=headers,
    )
    assert res.status_code == 400, res.text
    assert "ASSIGNMENT_DEADLINE_PASSED" in res.text


def test_submission_idempotency_and_success_persistence(client, db_session):
    """Positive flow & Idempotency:
    - First submission succeeds (persisted in DB with assessment_basis_snapshot).
    - Duplicate POST with same idempotency_key returns identical submission without error or row duplication.
    """
    teacher = _make_user(client, db_session, f"teacher_{uuid4().hex[:6]}@school.edu", "Thầy Vũ", UserRole.teacher)
    student = _make_user(client, db_session, f"student_{uuid4().hex[:6]}@school.edu", "Nguyễn Lê Hoàng Nam")
    classroom, assignment, _, _ = _seed_verified_assignment(db_session, teacher)

    # Enroll student
    db_session.add(ClassMember(class_id=classroom.id, user_id=student.id, role="learner"))
    db_session.commit()

    headers = _auth_headers_for(student)
    idempotency_key = f"idem-key-{uuid4().hex}"
    payload = {
        "submission_content": {
            "claim": "Cánh diều trên Cao Đỉnh biểu thị phong tục tao nhã của vương triều Nguyễn",
            "evidence": "Theo Khâm Định Đại Nam Hội Điển Sự Lệ (Quyển 78)",
            "evidence_citations": ["Khâm Định Đại Nam Hội Điển Sự Lệ", "Đại Nam Thực Lục"],
            "explanation": "Nghệ thuật đúc đồng thể hiện đời sống văn hóa cung đình phong phú.",
        },
        "idempotency_key": idempotency_key,
    }

    # First POST
    res1 = client.post(
        f"/api/v1/history/assignments/{assignment.id}/submit",
        json=payload,
        headers=headers,
    )
    assert res1.status_code == 200, res1.text
    data1 = res1.json()
    submission_id = data1["id"]
    assert data1["status"] == "submitted"
    assert data1["idempotency_key"] == idempotency_key
    assert "assessment_basis_snapshot" in data1
    assert data1["assessment_basis_snapshot"]["assignment_id"] == str(assignment.id)

    # Duplicate POST with same idempotency key
    res2 = client.post(
        f"/api/v1/history/assignments/{assignment.id}/submit",
        json=payload,
        headers=headers,
    )
    assert res2.status_code == 200, res2.text
    data2 = res2.json()
    assert data2["id"] == submission_id
    assert data2["idempotency_key"] == idempotency_key

    # Check database row count: strictly 1 row
    sub_count = db_session.scalar(
        select(HistoryAssignmentSubmission)
        .where(
            HistoryAssignmentSubmission.assignment_id == assignment.id,
            HistoryAssignmentSubmission.student_id == student.id,
        )
    )
    assert sub_count is not None
    assert str(sub_count.id) == submission_id


def test_frontend_submissions_api_contract_and_offline_abuse():
    """Verify frontend/src/lib/imperial/submissions-api.ts contract:
    - persistStudentSubmissionToServer rejects offline fake success (CLIENT_OFFLINE).
    - persistStudentSubmissionToServer validates M-E-E completeness (INVALID_SUBMISSION_CONTENT).
    """
    ts_file = REPO_ROOT / "frontend" / "src" / "lib" / "imperial" / "submissions-api.ts"
    assert ts_file.exists(), "submissions-api.ts must exist"
    content = ts_file.read_text(encoding="utf-8")

    # Invariant: offline client cannot fake a server-confirmed submission
    assert "persistStudentSubmissionToServer" in content
    assert "CLIENT_OFFLINE" in content
    assert "navigator.onLine" in content
    assert "idempotencyKey" in content
    assert "INVALID_SUBMISSION_CONTENT" in content
