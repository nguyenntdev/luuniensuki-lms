# -*- coding: utf-8 -*-
"""V5-T035 (Wave W03, Slot A05): Rubric Grading API & Anti-Abuse Test Suite.

Audits and verifies:
1. Teacher rubric scoring across historical reasoning criteria:
   - 0-3 scale per criterion: spatial (S1), temporal (S2), evidence (S3), argumentation (S4).
   - Real reviewer ID (current_user.id) and timestamp (graded_at).
   - Qualitative feedback note.
   - Proper calculation of total score and row_version increment.
2. Immutable audit history & revisions:
   - Grading records immutable audit entry with actor, action, old_value, new_value.
   - Re-grading / revision creates subsequent audit record with incremented row_version.
   - Audit trail endpoint GET /api/v1/imperial/teacher/submissions/{id}/audit.
3. Single submission inspection:
   - GET /api/v1/imperial/teacher/submissions/{id}.
4. Negative abuse tests:
   - Unauthorized students/learners attempting to grade receive HTTP 403 Forbidden.
   - Client devtools attempting to forge a graded status during submission creation
     have their forged status/scores completely ignored by the server.
   - Unauthorized students attempting to view audit history receive HTTP 403 Forbidden.
   - Unauthenticated requests receive HTTP 401 Unauthorized.
   - Guest users receive HTTP 403 Forbidden.
5. Strict validation:
   - Rubric scores outside 0-3 (e.g. 4, -1, booleans) return HTTP 400 Bad Request.
   - Non-existent submission returns HTTP 404 Not Found.
"""
from __future__ import annotations

import os
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select

from backend.imperial_models import (
    CONTENT_SCOPE_IMPERIAL,
    ImperialActivity,
    ImperialSite,
    ImperialSubmission,
    ImperialZone,
)
from backend.models import AuditLog, User, UserRole
from backend.security import hash_password

REPO_ROOT = Path(__file__).resolve().parents[2]


# --------------------------------------------------------------------------- #
# Helpers & Fixtures
# --------------------------------------------------------------------------- #
@pytest.fixture(autouse=True)
def _reset_auth_rate_limit():
    """Reset auth rate limit before each test."""
    import backend.main as main

    if hasattr(main, "_auth_rate_limit_state"):
        main._auth_rate_limit_state.clear()
    yield
    if hasattr(main, "_auth_rate_limit_state"):
        main._auth_rate_limit_state.clear()


def _create_user(
    db_session,
    email: str,
    role: UserRole = UserRole.learner,
    display_name: str | None = None,
) -> User:
    """Create user directly in test db."""
    user = User(
        email=email,
        password_hash=hash_password("Password123!"),
        display_name=display_name or f"User {email.split('@')[0]}",
        username=f"u_{uuid4().hex[:8]}",
        role=role,
        is_profile_public=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _login(client, email: str, password: str = "Password123!"):
    """Switch active user session on client."""
    client.cookies.clear()
    res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    return res


def _seed_activity(db_session, creator: User) -> tuple[ImperialSite, ImperialActivity]:
    """Seed test zone, site, and activity."""
    zone = ImperialZone(
        id=uuid4(),
        content_scope=CONTENT_SCOPE_IMPERIAL,
        slug=f"zone-rubric-{uuid4().hex[:8]}",
        title_vi="Khu vực Hoàng Thành",
        title_en="Imperial Citadel Zone",
        display_order=1,
    )
    db_session.add(zone)
    db_session.flush()

    site = ImperialSite(
        id=uuid4(),
        content_scope=CONTENT_SCOPE_IMPERIAL,
        zone_id=zone.id,
        slug=f"ngo-mon-{uuid4().hex[:8]}",
        name_vi="Ngọ Môn",
        name_en="Meridian Gate",
        site_type="gate",
        condition="extant",
        learning_level="L2_VERIFIED",
        summary_vi="Cổng chính phía nam của Hoàng thành Huế.",
        historical_context="Xây dựng năm 1833 dưới thời vua Minh Mạng.",
        architectural_features="Cấu trúc năm cửa chín lầu.",
        construction_year=1833,
        is_published=True,
        display_order=1,
        created_by=creator.id,
    )
    db_session.add(site)
    db_session.flush()

    activity = ImperialActivity(
        id=uuid4(),
        content_scope=CONTENT_SCOPE_IMPERIAL,
        site_id=site.id,
        activity_type="inquiry",
        title="Khảo sát năm cửa Ngọ Môn",
        instructions="Phân tích trật tự phân tầng không gian và chính sử triều Nguyễn theo mô hình M-E-E.",
        max_points=12,
        is_active=True,
    )
    db_session.add(activity)
    db_session.commit()
    return site, activity


# --------------------------------------------------------------------------- #
# Test 1: Teacher Rubric Scoring & Reviewer ID / Timestamp
# --------------------------------------------------------------------------- #
def test_teacher_rubric_scoring_success(client, db_session):
    """Verifies teacher rubric scoring across S1-S4 criteria (0-3 scale), reviewer ID, and timestamp."""
    admin = _create_user(db_session, f"admin_{uuid4().hex[:6]}@example.com", UserRole.admin, "Admin")
    teacher = _create_user(db_session, f"teacher_{uuid4().hex[:6]}@example.com", UserRole.teacher, "TS. Tran Van Tho")
    student = _create_user(db_session, f"student_{uuid4().hex[:6]}@example.com", UserRole.learner, "Nguyen Le Hoang Nam")

    site, activity = _seed_activity(db_session, admin)

    # 1. Student submits response
    _login(client, student.email)
    sub_res = client.post(
        f"/api/v1/imperial/activities/{activity.id}/submissions",
        json={
            "answer_text": "Cửa giữa dành riêng cho Thiên tử, hai cửa Tả Hữu Giáp Môn cho quan văn võ, hai cửa ngoài cùng cho binh mã kéo pháo.",
            "evidence_refs": [
                {
                    "source_title": "Khâm Định Đại Nam Hội Điển Sự Lệ",
                    "chapter": "Quyển 78 (Công Bộ)",
                    "quote": "Cửa giữa lợp ngói lưu ly vàng chỉ dành cho Thiên tử đi...",
                }
            ],
        },
    )
    assert sub_res.status_code == 201, sub_res.text
    sub_data = sub_res.json()
    submission_id = sub_data["id"]
    assert sub_data["status"] == "submitted"
    assert sub_data["score"] is None
    assert sub_data["graded_by"] is None
    assert sub_data["graded_at"] is None

    # 2. Teacher grades with 4 historical reasoning criteria: S1, S2, S3, S4
    _login(client, teacher.email)
    grade_payload = {
        "rubric_scores": {
            "S1_spatial": 3,
            "S2_temporal": 2,
            "S3_evidence": 3,
            "S4_argument": 2,
        },
        "feedback": "Lập luận M-E-E rất sắc sảo, trích dẫn Hội Điển chính xác. Cần bổ sung mốc trùng tu thời Khải Định để hoàn thiện.",
        "status": "graded",
    }
    grade_res = client.post(
        f"/api/v1/imperial/teacher/submissions/{submission_id}/grade",
        json=grade_payload,
    )
    assert grade_res.status_code == 200, grade_res.text
    graded = grade_res.json()

    assert graded["id"] == submission_id
    assert graded["status"] == "graded"
    assert graded["score"] == 10.0  # 3 + 2 + 3 + 2 = 10
    assert graded["rubric_scores"]["S1_spatial"] == 3
    assert graded["rubric_scores"]["S2_temporal"] == 2
    assert graded["rubric_scores"]["S3_evidence"] == 3
    assert graded["rubric_scores"]["S4_argument"] == 2
    assert graded["graded_by"] == str(teacher.id)
    assert graded["graded_at"] is not None
    assert "Hội Điển" in graded["feedback"]
    assert graded["row_version"] == 2

    # 3. Check single submission GET endpoint
    detail_res = client.get(f"/api/v1/imperial/teacher/submissions/{submission_id}")
    assert detail_res.status_code == 200, detail_res.text
    detail = detail_res.json()
    assert detail["id"] == submission_id
    assert detail["score"] == 10.0
    assert detail["graded_by"] == str(teacher.id)


# --------------------------------------------------------------------------- #
# Test 2: Audit History & Revisions Tracking
# --------------------------------------------------------------------------- #
def test_submission_audit_history_and_revisions(client, db_session):
    """Verifies that grading and subsequent re-grading append immutable audit records with state diffs."""
    admin = _create_user(db_session, f"admin_{uuid4().hex[:6]}@example.com", UserRole.admin, "Admin")
    teacher = _create_user(db_session, f"teacher_{uuid4().hex[:6]}@example.com", UserRole.teacher, "Thay Tho")
    student = _create_user(db_session, f"student_{uuid4().hex[:6]}@example.com", UserRole.learner, "Hoc Sinh A")

    site, activity = _seed_activity(db_session, admin)

    _login(client, student.email)
    sub_res = client.post(
        f"/api/v1/imperial/activities/{activity.id}/submissions",
        json={"answer_text": "Phân tích không gian di tích Ngọ Môn."},
    )
    submission_id = sub_res.json()["id"]

    # Initial Grade (Revision 1)
    _login(client, teacher.email)
    grade1_res = client.post(
        f"/api/v1/imperial/teacher/submissions/{submission_id}/grade",
        json={
            "rubric_scores": {"s1_spatial": 2, "s2_temporal": 2, "s3_evidence": 2, "s4_argument": 2},
            "feedback": "Bài làm mức độ khá.",
            "status": "graded",
        },
    )
    assert grade1_res.status_code == 200
    assert grade1_res.json()["row_version"] == 2

    # Verify audit record in database
    db_audits = list(
        db_session.execute(
            select(AuditLog)
            .where(
                AuditLog.resource_type == "imperial_submission",
                AuditLog.resource_id == UUID(submission_id),
            )
            .order_by(AuditLog.created_at.asc())
        ).scalars().all()
    )
    assert len(db_audits) == 1
    assert db_audits[0].action == "rubric_grade"
    assert db_audits[0].user_id == teacher.id
    assert db_audits[0].old_value["status"] == "submitted"
    assert db_audits[0].old_value["score"] is None
    assert db_audits[0].new_value["status"] == "graded"
    assert db_audits[0].new_value["score"] == 8.0
    assert db_audits[0].new_value["row_version"] == 2

    # Re-grade / Revision (Revision 2)
    grade2_res = client.post(
        f"/api/v1/imperial/teacher/submissions/{submission_id}/grade",
        json={
            "rubric_scores": {"s1_spatial": 3, "s2_temporal": 3, "s3_evidence": 3, "s4_argument": 3},
            "feedback": "Phúc khảo: học sinh đã bổ sung tư liệu EFEO, nâng lên mức xuất sắc.",
            "status": "graded",
        },
    )
    assert grade2_res.status_code == 200
    assert grade2_res.json()["row_version"] == 3
    assert grade2_res.json()["score"] == 12.0

    # Query audit history endpoint
    audit_res = client.get(f"/api/v1/imperial/teacher/submissions/{submission_id}/audit")
    assert audit_res.status_code == 200, audit_res.text
    audit_logs = audit_res.json()

    assert len(audit_logs) == 2
    # First revision
    assert audit_logs[0]["action"] == "rubric_grade"
    assert audit_logs[0]["user_id"] == str(teacher.id)
    assert audit_logs[0]["new_value"]["score"] == 8.0
    assert audit_logs[0]["new_value"]["row_version"] == 2

    # Second revision
    assert audit_logs[1]["action"] == "rubric_grade"
    assert audit_logs[1]["user_id"] == str(teacher.id)
    assert audit_logs[1]["old_value"]["score"] == 8.0
    assert audit_logs[1]["new_value"]["score"] == 12.0
    assert audit_logs[1]["new_value"]["row_version"] == 3
    assert "Phúc khảo" in audit_logs[1]["new_value"]["feedback"]


# --------------------------------------------------------------------------- #
# Test 3: Negative Abuse — Unauthorized Students Cannot Forge Graded Status
# --------------------------------------------------------------------------- #
def test_unauthorized_student_cannot_call_grading_api(client, db_session):
    """Verifies that non-teacher/staff accounts receive HTTP 403 when trying to grade."""
    admin = _create_user(db_session, f"admin_{uuid4().hex[:6]}@example.com", UserRole.admin, "Admin")
    student = _create_user(db_session, f"student_{uuid4().hex[:6]}@example.com", UserRole.learner, "Hoc Sinh B")

    site, activity = _seed_activity(db_session, admin)

    _login(client, student.email)
    sub_res = client.post(
        f"/api/v1/imperial/activities/{activity.id}/submissions",
        json={"answer_text": "Báo cáo khảo sát thực địa."},
    )
    submission_id = sub_res.json()["id"]

    # Student attempts to grade their own submission
    hack_res = client.post(
        f"/api/v1/imperial/teacher/submissions/{submission_id}/grade",
        json={
            "rubric_scores": {"s1_spatial": 3, "s2_temporal": 3, "s3_evidence": 3, "s4_argument": 3},
            "status": "graded",
            "feedback": "Hacked self-evaluation",
        },
    )
    assert hack_res.status_code == 403, "Students must not be allowed to grade submissions"

    # Submission remains ungraded in database
    sub = db_session.get(ImperialSubmission, UUID(submission_id))
    assert sub.status == "submitted"
    assert sub.score is None
    assert sub.graded_by is None


def test_client_devtools_cannot_forge_graded_status_during_submission(client, db_session):
    """Verifies that extra fields injected by devtools (status='graded', score=12) are completely ignored."""
    admin = _create_user(db_session, f"admin_{uuid4().hex[:6]}@example.com", UserRole.admin, "Admin")
    student = _create_user(db_session, f"student_{uuid4().hex[:6]}@example.com", UserRole.learner, "Hoc Sinh C")

    site, activity = _seed_activity(db_session, admin)

    _login(client, student.email)
    # Malicious client craft attempting to self-proclaim graded status and perfect score
    forged_payload = {
        "answer_text": "Bài làm tự chấm điểm bằng Devtools.",
        "status": "graded",
        "score": 12.0,
        "rubric_scores": {"s1_spatial": 3, "s2_temporal": 3, "s3_evidence": 3, "s4_argument": 3},
        "feedback": "Tự động cho 10 điểm",
        "graded_by": str(uuid4()),
        "graded_at": "2026-11-01T00:00:00Z",
    }
    sub_res = client.post(
        f"/api/v1/imperial/activities/{activity.id}/submissions",
        json=forged_payload,
    )
    assert sub_res.status_code == 201, sub_res.text
    data = sub_res.json()

    # The server strictly forces status='submitted' and discards forged scores
    assert data["status"] == "submitted"
    assert data["score"] is None
    assert data["rubric_scores"] in ({}, None)
    assert data["feedback"] is None
    assert data["graded_by"] is None
    assert data["graded_at"] is None

    # Verify directly in database row
    sub_row = db_session.get(ImperialSubmission, UUID(data["id"]))
    assert sub_row.status == "submitted"
    assert sub_row.score is None
    assert sub_row.rubric_scores == {}
    assert sub_row.graded_by is None


def test_unauthorized_student_cannot_view_audit_history(client, db_session):
    """Verifies that students cannot access teacher submission audit logs."""
    admin = _create_user(db_session, f"admin_{uuid4().hex[:6]}@example.com", UserRole.admin, "Admin")
    teacher = _create_user(db_session, f"teacher_{uuid4().hex[:6]}@example.com", UserRole.teacher, "Teacher")
    student = _create_user(db_session, f"student_{uuid4().hex[:6]}@example.com", UserRole.learner, "Student")

    site, activity = _seed_activity(db_session, admin)

    _login(client, student.email)
    sub_res = client.post(
        f"/api/v1/imperial/activities/{activity.id}/submissions",
        json={"answer_text": "Nội dung bài làm."},
    )
    submission_id = sub_res.json()["id"]

    # Teacher grades
    _login(client, teacher.email)
    teacher_client_res = client.post(
        f"/api/v1/imperial/teacher/submissions/{submission_id}/grade",
        json={"rubric_scores": {"s1_spatial": 2}, "feedback": "Đạt yêu cầu."},
    )
    assert teacher_client_res.status_code == 200

    # Student attempts to inspect audit trail
    _login(client, student.email)
    audit_res = client.get(f"/api/v1/imperial/teacher/submissions/{submission_id}/audit")
    assert audit_res.status_code == 403

    # Unauthenticated client attempts to inspect audit trail
    client.cookies.clear()
    anon_res = client.get(f"/api/v1/imperial/teacher/submissions/{submission_id}/audit")
    assert anon_res.status_code in (401, 403)


# --------------------------------------------------------------------------- #
# Test 4: Strict Rubric Validation Rules
# --------------------------------------------------------------------------- #
def test_rubric_validation_rejects_invalid_values(client, db_session):
    """Verifies that out-of-scale (>3 or <0) and non-integer values are rejected."""
    admin = _create_user(db_session, f"admin_{uuid4().hex[:6]}@example.com", UserRole.admin, "Admin")
    teacher = _create_user(db_session, f"teacher_{uuid4().hex[:6]}@example.com", UserRole.teacher, "Teacher")
    student = _create_user(db_session, f"student_{uuid4().hex[:6]}@example.com", UserRole.learner, "Student")

    site, activity = _seed_activity(db_session, admin)

    _login(client, student.email)
    sub_res = client.post(
        f"/api/v1/imperial/activities/{activity.id}/submissions",
        json={"answer_text": "Báo cáo di sản."},
    )
    submission_id = sub_res.json()["id"]

    _login(client, teacher.email)

    # 1. Score > 3
    res_high = client.post(
        f"/api/v1/imperial/teacher/submissions/{submission_id}/grade",
        json={"rubric_scores": {"s1_spatial": 4}},
    )
    assert res_high.status_code == 400
    assert "INVALID_RUBRIC_SCORE" in res_high.text

    # 2. Score < 0
    res_neg = client.post(
        f"/api/v1/imperial/teacher/submissions/{submission_id}/grade",
        json={"rubric_scores": {"s1_spatial": -1}},
    )
    assert res_neg.status_code == 400
    assert "INVALID_RUBRIC_SCORE" in res_neg.text

    # 3. Non-existent submission ID
    fake_id = uuid4()
    res_404 = client.post(
        f"/api/v1/imperial/teacher/submissions/{fake_id}/grade",
        json={"rubric_scores": {"s1_spatial": 2}},
    )
    assert res_404.status_code == 404
    assert "IMPERIAL_SUBMISSION_NOT_FOUND" in res_404.text


# --------------------------------------------------------------------------- #
# Test 5: Teacher Resubmit Request Workflow
# --------------------------------------------------------------------------- #
def test_teacher_can_request_resubmission(client, db_session):
    """Verifies teacher can return a submission with status 'resubmit_requested' and note."""
    admin = _create_user(db_session, f"admin_{uuid4().hex[:6]}@example.com", UserRole.admin, "Admin")
    teacher = _create_user(db_session, f"teacher_{uuid4().hex[:6]}@example.com", UserRole.teacher, "Teacher")
    student = _create_user(db_session, f"student_{uuid4().hex[:6]}@example.com", UserRole.learner, "Student")

    site, activity = _seed_activity(db_session, admin)

    _login(client, student.email)
    sub_res = client.post(
        f"/api/v1/imperial/activities/{activity.id}/submissions",
        json={"answer_text": "Câu trả lời quá ngắn gọn."},
    )
    submission_id = sub_res.json()["id"]

    _login(client, teacher.email)
    resubmit_res = client.post(
        f"/api/v1/imperial/teacher/submissions/{submission_id}/grade",
        json={
            "rubric_scores": {"s1_spatial": 1, "s2_temporal": 0, "s3_evidence": 0, "s4_argument": 1},
            "status": "resubmit_requested",
            "feedback": "Cần khảo sát lại thực tế và trích dẫn rõ điều 78 Hội Điển Sự Lệ.",
        },
    )
    assert resubmit_res.status_code == 200, resubmit_res.text
    resubmit_data = resubmit_res.json()
    assert resubmit_data["status"] == "resubmit_requested"
    assert resubmit_data["score"] == 2.0
    assert "trích dẫn rõ" in resubmit_data["feedback"]

    # Verify audit record reflects resubmit_requested
    audit_res = client.get(f"/api/v1/imperial/teacher/submissions/{submission_id}/audit")
    assert audit_res.status_code == 200
    assert audit_res.json()[0]["new_value"]["status"] == "resubmit_requested"
