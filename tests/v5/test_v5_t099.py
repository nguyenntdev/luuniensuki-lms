# -*- coding: utf-8 -*-
"""V5-T099 (Wave W09, Slot A09): Teacher Onboarding, Support Center, and Student PII Safety Test Suite.

Audits and verifies:
1. Teacher Interactive Onboarding Tour API:
   - GET /api/v1/teacher/onboarding/profile: returns profile, school verification status, demo vs verified mode.
   - POST /api/v1/teacher/onboarding/step: records step progression.
   - POST /api/v1/teacher/onboarding/complete: marks tour completed.
   - POST /api/v1/teacher/onboarding/dismiss: dismisses tour banner.
2. Verified Sample Lesson Templates:
   - GET /api/v1/teacher/sample-templates: returns curated lesson templates.
   - Prominently labeled with is_sample_template=True, template_badge="SAMPLE TEMPLATE", and explicit disclaimer.
   - POST /api/v1/teacher/sample-templates/{id}/clone: clones template into a draft lesson plan.
3. Teacher Training Resources:
   - GET /api/v1/teacher/training/resources: returns curated professional development guides.
   - Filterable by category (curriculum_standards, rubric_scoring, student_privacy, technical_guidance).
4. Teacher Support Center:
   - POST /api/v1/teacher/support/tickets: submits a support ticket with unique ticket_code (TKT-YYYYMM-XXX).
   - GET /api/v1/teacher/support/tickets: lists tickets with role isolation.
   - POST /api/v1/teacher/support/tickets/{id}/reply: adds threaded replies.
5. Negative Abuse Defense (Critical Invariant V5-T099):
   - Unverified school users / guest teachers CANNOT access real student PII or live class records.
   - Guest teacher calling roster or gradebook receives HTTP 403.
   - Unverified teacher calling roster receives HTTP 403 (UNVERIFIED_TEACHER_ACCESS_DENIED).
   - Unverified teacher calling gradebook receives HTTP 403 (UNVERIFIED_TEACHER_ACCESS_DENIED).
   - Unverified teacher calling gradebook export receives HTTP 403 (UNVERIFIED_TEACHER_ACCESS_DENIED).
   - Verified school teacher can access their own classroom roster and gradebook with student PII.
"""
from __future__ import annotations

import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from backend.domain.teacher_onboarding import (
    SAMPLE_LESSON_TEMPLATES,
    TEACHER_TRAINING_RESOURCES,
    UnverifiedTeacherAccessDeniedError,
    verify_teacher_school_access,
)
from backend.models import (
    ClassMember,
    Classroom,
    School,
    SchoolMember,
    User,
    UserRole,
)
from backend.services import classroom as classroom_service
from backend.teacher_models import TeacherOnboardingProfile, TeacherSupportTicket


# --------------------------------------------------------------------------- #
# Helpers & Seeders
# --------------------------------------------------------------------------- #

def _create_user(
    db_session,
    email: str,
    role: UserRole,
    display_name: str,
    is_school_verified: bool = True,
    school_id: uuid.UUID | None = None,
) -> User:
    user = db_session.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if not user:
        from backend.security import hash_password
        user = User(
            id=uuid.uuid4(),
            email=email,
            password_hash=hash_password("Password123!"),
            display_name=display_name,
            username=f"u_{uuid.uuid4().hex[:8]}",
            role=role,
            is_school_verified=is_school_verified,
            school_id=school_id,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
    else:
        user.role = role
        user.is_school_verified = is_school_verified
        user.school_id = school_id
        db_session.commit()
        db_session.refresh(user)
    return user


def _login(client: TestClient, email: str, password: str = "Password123!") -> dict[str, str]:
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Login failed: {res.text}"
    token = client.cookies.get("luuniensuki_access") or res.cookies.get("luuniensuki_access") or ""
    return {"Authorization": f"Bearer {token}"}


# --------------------------------------------------------------------------- #
# Test 1: Onboarding Tour Lifecycle API
# --------------------------------------------------------------------------- #

def test_teacher_onboarding_tour_lifecycle(client: TestClient, db_session):
    """Verify teacher onboarding profile initialization, step tracking, and completion."""
    teacher = _create_user(
        db_session, "t_tour@quochoc.edu.vn", UserRole.teacher, "Cô Thảo Sử", is_school_verified=True
    )
    headers = _login(client, teacher.email)

    # 1. Fetch onboarding profile
    res_prof = client.get("/api/v1/teacher/onboarding/profile", headers=headers)
    assert res_prof.status_code == 200, res_prof.text
    prof = res_prof.json()
    assert prof["teacher_id"] == str(teacher.id)
    assert prof["is_school_verified"] is True
    assert prof["mode"] == "verified"
    assert prof["is_completed"] is False
    assert prof["current_step"] == "welcome"

    # 2. Record onboarding steps
    res_step1 = client.post(
        "/api/v1/teacher/onboarding/step",
        json={"step": "curriculum_standards", "completed": True},
        headers=headers,
    )
    assert res_step1.status_code == 200
    assert "curriculum_standards" in res_step1.json()["completed_steps"]

    res_step2 = client.post(
        "/api/v1/teacher/onboarding/step",
        json={"step": "sample_templates", "completed": True},
        headers=headers,
    )
    assert res_step2.status_code == 200
    assert "sample_templates" in res_step2.json()["completed_steps"]

    # 3. Dismiss tour banner
    res_dismiss = client.post(
        "/api/v1/teacher/onboarding/dismiss",
        json={"dismiss": True},
        headers=headers,
    )
    assert res_dismiss.status_code == 200
    assert res_dismiss.json()["tour_dismissed"] is True

    # 4. Complete tour
    res_complete = client.post("/api/v1/teacher/onboarding/complete", headers=headers)
    assert res_complete.status_code == 200
    assert res_complete.json()["is_completed"] is True
    assert res_complete.json()["completed_at"] is not None

    # 5. Reset tour for retraining
    res_reset = client.post("/api/v1/teacher/onboarding/reset", headers=headers)
    assert res_reset.status_code == 200
    assert res_reset.json()["is_completed"] is False
    assert res_reset.json()["completed_steps"] == []


# --------------------------------------------------------------------------- #
# Test 2: Sample Templates Clearly Marked as "SAMPLE TEMPLATE" & Cloneable
# --------------------------------------------------------------------------- #

def test_sample_lesson_templates_contract_and_cloning(client: TestClient, db_session):
    """Verify sample templates carry explicit 'SAMPLE TEMPLATE' badges, disclaimers, and can be cloned."""
    teacher = _create_user(
        db_session, "t_samples@quochoc.edu.vn", UserRole.teacher, "Thầy Hoàng Sử", is_school_verified=True
    )
    headers = _login(client, teacher.email)

    # 1. List sample templates
    res_list = client.get("/api/v1/teacher/sample-templates", headers=headers)
    assert res_list.status_code == 200, res_list.text
    templates = res_list.json()
    assert len(templates) >= 3

    for tmpl in templates:
        assert tmpl["is_sample_template"] is True
        assert tmpl["template_badge"] == "SAMPLE TEMPLATE"
        assert "SAMPLE TEMPLATE" in tmpl["disclaimer"]
        assert "CV 5512/BGDĐT" in tmpl["curriculum_framework"]
        assert tmpl["duration_minutes"] == 45
        assert len(tmpl["inquiry_activities"]) == 4

    # 2. Get specific template detail
    sample_id = "sample-cao-dinh-dragon-45min"
    res_detail = client.get(f"/api/v1/teacher/sample-templates/{sample_id}", headers=headers)
    assert res_detail.status_code == 200
    detail = res_detail.json()
    assert detail["id"] == sample_id
    assert "Rồng trên Cao Đỉnh" in detail["title"]

    # 3. Clone sample template to personal draft
    res_clone = client.post(f"/api/v1/teacher/sample-templates/{sample_id}/clone", headers=headers)
    assert res_clone.status_code == 201, res_clone.text
    cloned = res_clone.json()
    assert "cloned_plan_id" in cloned
    assert "[Bản sao mẫu]" in cloned["title"]
    assert cloned["status"] == "draft"


# --------------------------------------------------------------------------- #
# Test 3: Teacher Training Resources and Categorization
# --------------------------------------------------------------------------- #

def test_teacher_training_resources(client: TestClient, db_session):
    """Verify training resources covering CV 5512, Rubric scoring, and Decree 13/2023/ND-CP privacy."""
    learner = _create_user(db_session, "learner_tr@test.edu", UserRole.learner, "Học sinh xem tập huấn")
    headers = _login(client, learner.email)

    # 1. List all training resources (publicly accessible to all authenticated users)
    res_all = client.get("/api/v1/teacher/training/resources", headers=headers)
    assert res_all.status_code == 200, res_all.text
    resources = res_all.json()
    assert len(resources) >= 4

    # Verify key modules exist
    titles = [r["title"] for r in resources]
    assert any("5512" in t for t in titles)
    assert any("Rubric" in t for t in titles)
    assert any("13/2023/NĐ-CP" in t for t in titles)

    # 2. Filter by category
    res_privacy = client.get("/api/v1/teacher/training/resources?category=student_privacy", headers=headers)
    assert res_privacy.status_code == 200
    assert len(res_privacy.json()) >= 1
    assert res_privacy.json()[0]["category"] == "student_privacy"

    # 3. Get single resource by ID
    res_one = client.get("/api/v1/teacher/training/resources/tr-mod-01-cv5512", headers=headers)
    assert res_one.status_code == 200
    assert res_one.json()["id"] == "tr-mod-01-cv5512"
    assert res_one.json()["is_mandatory_for_verification"] is True


# --------------------------------------------------------------------------- #
# Test 4: Support Ticket Submission, Threaded Replies, and Role Scope
# --------------------------------------------------------------------------- #

def test_support_ticket_submission_and_threaded_replies(client: TestClient, db_session):
    """Verify support ticket submission, unique code generation, replies, and teacher isolation."""
    teacher_a = _create_user(
        db_session, "teacher_ticket_a@quochoc.edu.vn", UserRole.teacher, "Thầy Anh", is_school_verified=True
    )
    teacher_b = _create_user(
        db_session, "teacher_ticket_b@haibatrung.edu.vn", UserRole.teacher, "Cô Bích", is_school_verified=True
    )
    admin = _create_user(
        db_session, "admin_support@luunien.edu.vn", UserRole.admin, "BQT Luu Nien", is_school_verified=True
    )

    headers_a = _login(client, teacher_a.email)
    headers_b = _login(client, teacher_b.email)
    headers_admin = _login(client, admin.email)

    # 1. Teacher A submits support ticket
    ticket_payload = {
        "subject": "Cần hướng dẫn tích hợp Rubric S1-S4 cho bài kiểm tra 1 tiết",
        "category": "rubric_scoring",
        "priority": "high",
        "message": "Kính gửi ban chuyên môn, tôi muốn cấu hình thang điểm 0-3 cho tiêu chí S3 sử liệu.",
    }
    res_create = client.post("/api/v1/teacher/support/tickets", json=ticket_payload, headers=headers_a)
    assert res_create.status_code == 201, res_create.text
    ticket_data = res_create.json()
    ticket_id = ticket_data["id"]
    assert ticket_data["ticket_code"].startswith("TKT-")
    assert ticket_data["status"] == "open"
    assert ticket_data["teacher_name"] == "Thầy Anh"

    # 2. Teacher A lists tickets -> sees own ticket
    res_list_a = client.get("/api/v1/teacher/support/tickets", headers=headers_a)
    assert res_list_a.status_code == 200
    assert any(t["id"] == ticket_id for t in res_list_a.json())

    # 3. Teacher B lists tickets -> cannot see Teacher A's ticket (isolated)
    res_list_b = client.get("/api/v1/teacher/support/tickets", headers=headers_b)
    assert res_list_b.status_code == 200
    assert not any(t["id"] == ticket_id for t in res_list_b.json())

    # 4. Teacher B cannot view Teacher A's ticket detail (403 Forbidden)
    res_get_b = client.get(f"/api/v1/teacher/support/tickets/{ticket_id}", headers=headers_b)
    assert res_get_b.status_code == 403

    # 5. Admin replies to ticket
    res_admin_reply = client.post(
        f"/api/v1/teacher/support/tickets/{ticket_id}/reply",
        json={"message": "Ban Quản Trị đã gửi tài liệu hướng dẫn hiệu chuẩn qua email."},
        headers=headers_admin,
    )
    assert res_admin_reply.status_code == 200
    updated_ticket = res_admin_reply.json()
    assert updated_ticket["status"] == "in_progress"
    assert len(updated_ticket["responses"]) == 1
    assert updated_ticket["admin_response"] == "Ban Quản Trị đã gửi tài liệu hướng dẫn hiệu chuẩn qua email."

    # 6. Teacher A replies back
    res_teacher_reply = client.post(
        f"/api/v1/teacher/support/tickets/{ticket_id}/reply",
        json={"message": "Cảm ơn BQT, tôi đã nhận được tài liệu."},
        headers=headers_a,
    )
    assert res_teacher_reply.status_code == 200
    assert len(res_teacher_reply.json()["responses"]) == 2


# --------------------------------------------------------------------------- #
# Test 5: Negative Abuse - Unverified School User & Guest Blocked from Student PII
# --------------------------------------------------------------------------- #

def test_negative_abuse_unverified_school_users_and_guests_blocked_from_real_pii(
    client: TestClient, db_session
):
    """Critical Invariant (V5-T099):

    Unverified school users and guest teachers CANNOT access real student PII
    (emails, guardian details) or live classroom records/gradebook.
    """
    # 1. Create a school and verified classroom with student PII
    school = classroom_service.create_school(
        db=db_session,
        name="Trường THPT Quốc Học",
        code=f"QHH-{uuid.uuid4().hex[:4]}",
        city="Huế",
    )
    verified_teacher = _create_user(
        db_session, "verified_teacher@quochoc.edu.vn", UserRole.teacher, "Thầy Chính Thức", is_school_verified=True, school_id=school.id
    )
    classroom_service.add_school_member(db_session, school.id, verified_teacher.id, role="teacher")

    headers_v = _login(client, verified_teacher.email)
    res_class = client.post(
        "/api/v1/classrooms",
        json={"name": "Lớp Sử 10A1", "school_id": str(school.id), "max_students": 30},
        headers=headers_v,
    )
    assert res_class.status_code == 201
    class_id = res_class.json()["id"]
    class_code = res_class.json()["class_code"]

    # 2. Enroll a student with private guardian details
    student = _create_user(db_session, "student_pii@home.vn", UserRole.learner, "Học Sinh Thật")
    headers_s = _login(client, student.email)
    client.post(
        "/api/v1/classrooms/join",
        json={
            "class_code": class_code,
            "guardian_email": "phuhuynh_mat@family.vn",
            "guardian_consent": True,
        },
        headers=headers_s,
    )

    # 3. Create UNVERIFIED teacher account
    unverified_teacher = _create_user(
        db_session,
        "unverified_teacher@test.edu",
        UserRole.teacher,
        "Giáo Viên Chưa Xác Thực",
        is_school_verified=False,
    )
    headers_unverified = _login(client, unverified_teacher.email)

    # 4. Create GUEST teacher account
    guest_teacher = _create_user(
        db_session,
        "guest_teacher@test.edu",
        UserRole.guest,
        "Khách Thử Nghiệm",
        is_school_verified=False,
    )
    headers_guest = _login(client, guest_teacher.email)

    # ----------------------------------------------------------------------- #
    # Negative Abuse Verification:
    # ----------------------------------------------------------------------- #

    # Abuse 1: Unverified teacher attempts to access student roster -> HTTP 403
    res_unverified_roster = client.get(
        f"/api/v1/classrooms/{class_id}/roster", headers=headers_unverified
    )
    assert res_unverified_roster.status_code == 403
    assert "UNVERIFIED_TEACHER_ACCESS_DENIED" in res_unverified_roster.text or "Not authorized" in res_unverified_roster.text

    # Abuse 2: Unverified teacher attempts to access gradebook -> HTTP 403
    res_unverified_gradebook = client.get(
        f"/api/v1/classrooms/{class_id}/gradebook", headers=headers_unverified
    )
    assert res_unverified_gradebook.status_code == 403
    assert "UNVERIFIED_TEACHER_ACCESS_DENIED" in res_unverified_gradebook.text or "Not authorized" in res_unverified_gradebook.text

    # Abuse 3: Unverified teacher attempts to export gradebook CSV -> HTTP 403
    res_unverified_export = client.get(
        f"/api/v1/classrooms/{class_id}/gradebook/export", headers=headers_unverified
    )
    assert res_unverified_export.status_code == 403
    assert "UNVERIFIED_TEACHER_ACCESS_DENIED" in res_unverified_export.text or "Not authorized" in res_unverified_export.text

    # Abuse 4: Guest teacher attempts to access student roster -> HTTP 403
    res_guest_roster = client.get(
        f"/api/v1/classrooms/{class_id}/roster", headers=headers_guest
    )
    assert res_guest_roster.status_code == 403

    # Abuse 5: Guest teacher attempts to access gradebook -> HTTP 403
    res_guest_gradebook = client.get(
        f"/api/v1/classrooms/{class_id}/gradebook", headers=headers_guest
    )
    assert res_guest_gradebook.status_code == 403

    # 5. Positive verification: Verified teacher can view student roster and guardian PII
    res_v_roster = client.get(f"/api/v1/classrooms/{class_id}/roster", headers=headers_v)
    assert res_v_roster.status_code == 200
    roster = res_v_roster.json()
    assert roster["student_count"] == 1
    student_entry = roster["students"][0]
    assert student_entry["email"] == "student_pii@home.vn"
    assert student_entry["guardian_email"] == "phuhuynh_mat@family.vn"
    assert student_entry["guardian_consent"] is True

    # 6. Domain function direct verification
    with pytest.raises(UnverifiedTeacherAccessDeniedError):
        verify_teacher_school_access(unverified_teacher)

    with pytest.raises(UnverifiedTeacherAccessDeniedError):
        verify_teacher_school_access(guest_teacher)

    assert verify_teacher_school_access(verified_teacher) is True
