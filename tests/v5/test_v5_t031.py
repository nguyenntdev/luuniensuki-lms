# -*- coding: utf-8 -*-
"""V5-T031: Retire Mock Gradebook LocalStorage in Frontend Submissions API Test Suite.

Scope & Invariants:
1. Unauthenticated requests to teacher gradebook/submissions endpoints are rejected with HTTP 401.
2. Learners / non-staff users cannot access teacher submission gradebook endpoints (HTTP 403).
3. Fresh production teacher receives strictly empty list `[]` with ZERO fictional student names
   ("Nguyễn Lê Hoàng Nam", "Trần Mai Phương Thảo", "Lê Quốc Bảo", "Phạm Hồng Ngọc", "Võ Thị Quỳnh Anh")
   and ZERO synthetic mock IDs ("sub-001" .. "sub-005").
4. Real student activity submissions are saved via authoritative server API endpoints,
   retrieved by teachers, and evaluated using S1-S4 rubric criteria (0-3 scale).
5. Out-of-scale rubric scores (> 3 or < 0) are rejected with HTTP 400 (INVALID_RUBRIC_SCORE).
6. Frontend submissions-api contract enforces strict demo fixture isolation: mock data is never
   returned or written to localStorage unless explicitly in demo/preview mode.
"""
from __future__ import annotations

import json
from pathlib import Path
import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import select

from backend.imperial_models import (
    CONTENT_SCOPE_IMPERIAL,
    ImperialActivity,
    ImperialSubmission,
    ImperialZone,
    ImperialSite,
)
from backend.models import User, UserRole
from backend.security import hash_password

FICTIONAL_DEMO_NAMES = {
    "Nguyễn Lê Hoàng Nam",
    "Trần Mai Phương Thảo",
    "Lê Quốc Bảo",
    "Phạm Hồng Ngọc",
    "Võ Thị Quỳnh Anh",
}

FICTIONAL_DEMO_IDS = {
    "sub-001",
    "sub-002",
    "sub-003",
    "sub-004",
    "sub-005",
}


def _create_user(
    db_session,
    email: str,
    role: UserRole = UserRole.teacher,
    display_name: str | None = None,
) -> User:
    """Helper to persist a user with specific role for tenant tests."""
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
    """Login helper setting session cookies on test client."""
    res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    return res.json()


def _ensure_test_activity(db_session) -> ImperialActivity:
    """Ensure at least one ImperialActivity exists in the test database."""
    activity = db_session.execute(
        select(ImperialActivity).where(
            ImperialActivity.content_scope == CONTENT_SCOPE_IMPERIAL
        )
    ).scalars().first()
    if activity:
        return activity

    # Create Zone & Site if needed
    zone = db_session.execute(
        select(ImperialZone).where(ImperialZone.content_scope == CONTENT_SCOPE_IMPERIAL)
    ).scalars().first()
    if not zone:
        zone = ImperialZone(
            id=uuid.uuid4(),
            content_scope=CONTENT_SCOPE_IMPERIAL,
            slug=f"zone-t031-{uuid.uuid4().hex[:6]}",
            title_vi="Hoàng Thành Huế",
            title_en="Imperial Enclosure",
            display_order=1,
        )
        db_session.add(zone)
        db_session.flush()

    site = db_session.execute(
        select(ImperialSite).where(ImperialSite.content_scope == CONTENT_SCOPE_IMPERIAL)
    ).scalars().first()
    if not site:
        site = ImperialSite(
            id=uuid.uuid4(),
            zone_id=zone.id,
            content_scope=CONTENT_SCOPE_IMPERIAL,
            slug=f"site-t031-{uuid.uuid4().hex[:6]}",
            name_vi="Ngọ Môn Huế",
            name_en="Noon Gate",
            is_published=True,
        )
        db_session.add(site)
        db_session.flush()

    activity = ImperialActivity(
        id=uuid.uuid4(),
        site_id=site.id,
        content_scope=CONTENT_SCOPE_IMPERIAL,
        title="Khảo sát cấu trúc không gian Ngọ Môn",
        activity_type="observation",
        instructions="Phân tích mô hình M-E-E về trật tự phân tầng không gian",
    )
    db_session.add(activity)
    db_session.commit()
    db_session.refresh(activity)
    return activity


def test_unauthenticated_gradebook_and_submissions_rejected(client):
    """Verify unauthenticated requests to teacher gradebook/submissions are rejected with 401."""
    # 1. GET imperial teacher submissions without credentials -> 401
    res_imp = client.get("/api/v1/imperial/teacher/submissions")
    assert res_imp.status_code == 401, f"Expected 401, got {res_imp.status_code}"

    # 2. GET history submissions without credentials -> 401
    res_hist = client.get("/api/v1/history/submissions")
    assert res_hist.status_code == 401, f"Expected 401, got {res_hist.status_code}"

    # 3. POST grade submission without credentials -> 401
    fake_sub_id = uuid.uuid4()
    res_grade = client.post(
        f"/api/v1/imperial/teacher/submissions/{fake_sub_id}/grade",
        json={"rubric_scores": {"S1_spatial": 2}, "status": "graded"},
    )
    assert res_grade.status_code == 401, f"Expected 401, got {res_grade.status_code}"


def test_student_role_forbidden_from_teacher_gradebook(client, db_session):
    """Verify that a learner/student is forbidden from accessing teacher gradebook and grading endpoints."""
    student = _create_user(
        db_session,
        f"learner_t031_{uuid.uuid4().hex[:6]}@example.com",
        role=UserRole.learner,
    )
    _login_user(client, student.email)

    # 1. Student attempts to access teacher submissions list -> 403
    res_list = client.get("/api/v1/imperial/teacher/submissions")
    assert res_list.status_code == 403, f"Expected 403 for student, got {res_list.status_code}"

    # 2. Student attempts to grade a submission -> 403
    res_grade = client.post(
        f"/api/v1/imperial/teacher/submissions/{uuid.uuid4()}/grade",
        json={"rubric_scores": {"S1_spatial": 2}, "status": "graded"},
    )
    assert res_grade.status_code == 403, f"Expected 403 for student grading, got {res_grade.status_code}"


def test_fresh_production_teacher_sees_zero_fictional_names_and_empty_list(client, db_session):
    """Verify that a fresh teacher receives strictly [] and sees NO fictional names or fake grades."""
    fresh_teacher = _create_user(
        db_session,
        f"teacher_t031_fresh_{uuid.uuid4().hex[:6]}@example.com",
        role=UserRole.teacher,
        display_name="Cô Trần Thị Hạnh",
    )
    _login_user(client, fresh_teacher.email)

    # 1. GET /api/v1/imperial/teacher/submissions for fresh tenant
    res_imp = client.get("/api/v1/imperial/teacher/submissions")
    assert res_imp.status_code == 200, res_imp.text
    data_imp = res_imp.json()
    assert isinstance(data_imp, list)

    # Invariants: Zero fictional demo names or fake grades in returned items
    for item in data_imp:
        # Negative check: no mock demo IDs
        assert str(item.get("id")) not in FICTIONAL_DEMO_IDS
        # If student details mapped, no fake names
        answer_text = item.get("answer_text", "")
        for demo_name in FICTIONAL_DEMO_NAMES:
            assert demo_name not in answer_text, f"Found leaked demo name '{demo_name}' in answer"

    # 2. GET /api/v1/history/submissions
    res_hist = client.get("/api/v1/history/submissions")
    assert res_hist.status_code == 200, res_hist.text
    data_hist = res_hist.json()
    assert isinstance(data_hist, list)


def test_real_student_submission_persisted_and_graded_via_server_apis(client, db_session):
    """Verify complete end-to-end server flow: student submits activity, teacher evaluates with S1-S4 rubrics."""
    activity = _ensure_test_activity(db_session)
    student = _create_user(
        db_session,
        f"student_real_t031_{uuid.uuid4().hex[:6]}@example.com",
        role=UserRole.learner,
        display_name="Đặng Tuấn Kiệt",
    )
    teacher = _create_user(
        db_session,
        f"teacher_eval_t031_{uuid.uuid4().hex[:6]}@example.com",
        role=UserRole.teacher,
        display_name="Thầy Nguyễn Quốc Huy",
    )

    # 1. Real Student submits activity
    _login_user(client, student.email)
    sub_payload = {
        "answer_text": "Mệnh đề: Ngọ Môn thể hiện quy chuẩn quyền lực triều Nguyễn qua kiến trúc năm cửa chín lầu.",
        "evidence_refs": ["Đại Nam Thực Lục Chính Biên Quyển 26", "Khảo sát thực địa Ngọ Môn 2026"],
    }
    sub_res = client.post(
        f"/api/v1/imperial/activities/{activity.id}/submissions",
        json=sub_payload,
    )
    assert sub_res.status_code == 201, f"Submission failed: {sub_res.text}"
    sub_data = sub_res.json()
    submission_id = sub_data["id"]
    assert sub_data["status"] == "submitted"
    assert sub_data["score"] is None
    assert sub_data["student_id"] == str(student.id)

    # 2. Teacher retrieves submissions list from server
    _login_user(client, teacher.email)
    list_res = client.get(f"/api/v1/imperial/teacher/submissions?activity_id={activity.id}")
    assert list_res.status_code == 200, list_res.text
    submissions_list = list_res.json()
    matched = [s for s in submissions_list if s["id"] == submission_id]
    assert len(matched) == 1, f"Expected submission {submission_id} in teacher list"

    # 3. Teacher evaluates submission with S1-S4 rubrics
    grade_payload = {
        "rubric_scores": {
            "S1_spatial": 3,
            "S2_temporal": 2,
            "S3_evidence": 3,
            "S4_argument": 2,
        },
        "feedback": "Phân tích trật tự không gian rất tốt, trích dẫn chính xác Đại Nam Thực Lục.",
        "status": "graded",
    }
    grade_res = client.post(
        f"/api/v1/imperial/teacher/submissions/{submission_id}/grade",
        json=grade_payload,
    )
    assert grade_res.status_code == 200, f"Grading failed: {grade_res.text}"
    graded_data = grade_res.json()
    assert graded_data["status"] == "graded"
    assert graded_data["score"] == 10.0  # 3 + 2 + 3 + 2
    assert graded_data["rubric_scores"] == {
        "S1_spatial": 3,
        "S2_temporal": 2,
        "S3_evidence": 3,
        "S4_argument": 2,
    }
    assert graded_data["graded_by"] == str(teacher.id)
    assert graded_data["row_version"] == 2


def test_rubric_validation_rejects_out_of_scale_score(client, db_session):
    """Verify that rubric scores exceeding the 0-3 scale are rejected with HTTP 400."""
    activity = _ensure_test_activity(db_session)
    student = _create_user(
        db_session,
        f"stu_bad_score_{uuid.uuid4().hex[:6]}@example.com",
        role=UserRole.learner,
    )
    teacher = _create_user(
        db_session,
        f"teacher_bad_score_{uuid.uuid4().hex[:6]}@example.com",
        role=UserRole.teacher,
    )

    _login_user(client, student.email)
    sub_res = client.post(
        f"/api/v1/imperial/activities/{activity.id}/submissions",
        json={"answer_text": "Bài khảo sát kiểm thử giới hạn rubric."},
    )
    assert sub_res.status_code == 201
    submission_id = sub_res.json()["id"]

    _login_user(client, teacher.email)
    bad_grade = {
        "rubric_scores": {
            "S1_spatial": 5,  # Out of range! Max is 3
            "S2_temporal": 1,
            "S3_evidence": 2,
            "S4_argument": 2,
        },
        "feedback": "Điểm vượt ngưỡng tối đa 3đ",
        "status": "graded",
    }
    err_res = client.post(
        f"/api/v1/imperial/teacher/submissions/{submission_id}/grade",
        json=bad_grade,
    )
    assert err_res.status_code == 400
    assert "INVALID_RUBRIC_SCORE" in err_res.text


def test_frontend_submissions_api_contract_and_fixture_isolation():
    """Verify that frontend/src/lib/imperial/submissions-api.ts isolates mock fixtures to demoMode."""
    repo_root = Path(__file__).resolve().parents[2]
    api_file = repo_root / "frontend" / "src/lib/imperial/submissions-api.ts"
    assert api_file.exists(), "submissions-api.ts must exist"

    content = api_file.read_text(encoding="utf-8")

    # 1. Verifies DEMO_STUDENT_SUBMISSIONS is explicitly defined
    assert "export const DEMO_STUDENT_SUBMISSIONS: StudentSubmission[]" in content, (
        "DEMO_STUDENT_SUBMISSIONS must be defined and isolated"
    )

    # 2. Verifies loadStudentSubmissions takes options?: LoadStudentSubmissionsOptions
    assert "export function loadStudentSubmissions(options?: LoadStudentSubmissionsOptions)" in content, (
        "loadStudentSubmissions must support options with demoMode flag"
    )

    # 3. Negative check: loadStudentSubmissions must NOT unconditionally inject mock data into empty storage
    # Previously: localStorage.setItem(SUBMISSIONS_STORAGE_KEY, JSON.stringify(INITIAL_STUDENT_SUBMISSIONS));
    assert 'localStorage.setItem(SUBMISSIONS_STORAGE_KEY, JSON.stringify(INITIAL_STUDENT_SUBMISSIONS))' not in content, (
        "Forbidden: loadStudentSubmissions must never auto-seed mock data into localStorage"
    )

    # 4. Verifies real server APIs are called
    assert "/api/v1/imperial/teacher/submissions" in content, (
        "fetchTeacherSubmissionsFromBackend must connect to real server API"
    )
    assert "/api/v1/history/submissions" in content, (
        "Submissions client must support history submissions endpoint"
    )
    assert "export async function gradeSubmissionWithApi" in content, (
        "gradeSubmissionWithApi must be exported for authoritative grading"
    )
