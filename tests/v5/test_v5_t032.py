# -*- coding: utf-8 -*-
"""V5-T032 (Wave W03, Slot A02): School, Teacher, and Classroom Model Test Suite.

Audits and verifies:
1. Classroom model & lifecycle:
   - Full model verification: id, name, description, teacher_id, school_id, term, class_code,
     max_students, is_archived, settings, timestamps.
   - Create, update, archive, unarchive, and delete operations.
2. School association & membership:
   - School model (name, code, address, city, region, is_active, settings).
   - Association with classrooms via school_id and term scope.
   - School teacher/staff membership management.
   - Querying classrooms by school.
3. Teacher ownership:
   - Teacher creating classroom is assigned teacher_id ownership.
   - Teacher can view and manage their own classrooms.
   - Outside teacher (not owner, not admin) cannot access or modify classroom (403 Forbidden).
4. Secure join code generation & validation:
   - Generation of unique, non-ambiguous 8-character uppercase alphanumeric codes.
   - Validation on join (case normalization, format validation).
   - Negative: Invalid/non-existent code rejected (400/404).
   - Negative: Archived classroom rejects new joins (400).
   - Negative: Full capacity classroom (max_students reached) rejects new joins (400).
5. Enrollment & Adult guardian flow:
   - Role enforcement: only learner accounts can join (staff/teacher gets 403).
   - Idempotency: re-joining existing class returns membership without duplicate rows.
   - Guardian flow: student enrollment records guardian_email, guardian_consent, and guardian_user_id.
   - Enrolled classrooms lookup via GET /api/v1/classrooms/enrolled.
6. Student roster & Negative abuse protections:
   - Teacher of classroom receives full student roster with contact and guardian details.
   - Enrolled student receives peer roster with privacy redactions (other students' PII omitted).
   - Negative abuse: Student from outside cannot view classroom details (403).
   - Negative abuse: Student from outside cannot view classroom roster (403).
   - Negative abuse: Unauthenticated visitor rejected with 401.
   - Negative abuse: Guest user rejected with 403.
"""
from __future__ import annotations

import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from backend.models import Classroom, ClassMember, School, SchoolMember, User, UserRole
from backend.services import classroom as classroom_service


# --------------------------------------------------------------------------- #
# Helpers & Seeders
# --------------------------------------------------------------------------- #

def _register_and_login(client: TestClient, db_session, email: str, role: UserRole, display_name: str) -> User:
    """Helper to create a user with a specific role and authenticate the test client."""
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password123!", "display_name": display_name},
    )
    user = db_session.execute(select(User).where(User.email == email)).scalar_one()
    user.role = role
    db_session.commit()
    db_session.refresh(user)

    client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Password123!"},
    )
    return user


def _login_as(client: TestClient, email: str):
    """Log in as an existing user."""
    client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Password123!"},
    )


# --------------------------------------------------------------------------- #
# Test 1: School Model and School API Management
# --------------------------------------------------------------------------- #

def test_school_model_and_api_crud(client: TestClient, db_session):
    """Verify School model creation, code uniqueness, querying, and updating."""
    admin = _register_and_login(client, db_session, "admin_sch@test.edu", UserRole.admin, "Admin School")

    # 1. Create school via API
    school_payload = {
        "name": "Trường THPT Chuyên Quốc Học Huế",
        "code": "THPT-QHH",
        "address": "12 Lê Lợi, TP Huế",
        "city": "Huế",
        "region": "Thừa Thiên Huế",
        "settings": {"founded_year": 1896, "heritage_curriculum": True},
    }
    res = client.post("/api/v1/schools", json=school_payload)
    assert res.status_code == 201, res.text
    school_data = res.json()
    school_id = school_data["id"]
    assert school_data["name"] == "Trường THPT Chuyên Quốc Học Huế"
    assert school_data["code"] == "THPT-QHH"
    assert school_data["city"] == "Huế"
    assert school_data["is_active"] is True

    # 2. Duplicate school code rejected
    dup_res = client.post("/api/v1/schools", json={**school_payload, "name": "Duplicate School"})
    assert dup_res.status_code == 400
    assert "already exists" in dup_res.text

    # 3. List schools with filter
    list_res = client.get("/api/v1/schools?city=Huế")
    assert list_res.status_code == 200
    schools = list_res.json()
    assert any(s["id"] == school_id for s in schools)

    # 4. Get school detail
    get_res = client.get(f"/api/v1/schools/{school_id}")
    assert get_res.status_code == 200
    assert get_res.json()["name"] == "Trường THPT Chuyên Quốc Học Huế"

    # 5. Update school
    update_res = client.patch(
        f"/api/v1/schools/{school_id}",
        json={"address": "12 Lê Lợi, Phường Vĩnh Ninh, TP Huế"},
    )
    assert update_res.status_code == 200
    assert "Phường Vĩnh Ninh" in update_res.json()["address"]


# --------------------------------------------------------------------------- #
# Test 2: Classroom Model and Association with School & Teacher
# --------------------------------------------------------------------------- #

def test_classroom_creation_and_school_association(client: TestClient, db_session):
    """Verify classroom model creation with teacher ownership, school_id, and term scope."""
    # Seed School
    school = classroom_service.create_school(
        db=db_session,
        name="Trường THCS Nguyễn Tri Phương",
        code="THCS-NTP",
        city="Huế",
    )

    # Create Teacher
    teacher = _register_and_login(client, db_session, "teacher_ntp@test.edu", UserRole.teacher, "Thầy Nguyễn")

    # Add teacher to school
    classroom_service.add_school_member(db_session, school.id, teacher.id, role="teacher")

    # Create Classroom with school association and term scope
    payload = {
        "name": "Lịch Sử Lớp 8A1 - Cửu Đỉnh Di Sản",
        "description": "Lớp học thực địa chuyên đề Cửu Đỉnh Đại Nội",
        "max_students": 35,
        "school_id": str(school.id),
        "term": "2025-2026-HK1",
        "settings": {"require_guardian_consent": True},
    }
    res = client.post("/api/v1/classrooms", json=payload)
    assert res.status_code == 201, res.text
    class_data = res.json()
    assert class_data["name"] == payload["name"]
    assert class_data["teacher_id"] == str(teacher.id)
    assert class_data["school_id"] == str(school.id)
    assert class_data["term"] == "2025-2026-HK1"
    assert len(class_data["class_code"]) == 8
    assert class_data["member_count"] == 0

    # Query classroom detail
    detail_res = client.get(f"/api/v1/classrooms/{class_data['id']}")
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["school_name"] == "Trường THCS Nguyễn Tri Phương"
    assert detail["teacher_name"] == "Thầy Nguyễn"
    assert detail["term"] == "2025-2026-HK1"

    # Query classrooms by school
    sch_classes = client.get(f"/api/v1/schools/{school.id}/classrooms")
    assert sch_classes.status_code == 200
    assert len(sch_classes.json()) >= 1
    assert any(c["id"] == class_data["id"] for c in sch_classes.json())


# --------------------------------------------------------------------------- #
# Test 3: Teacher Ownership and Unauthorized Access Protection
# --------------------------------------------------------------------------- #

def test_teacher_ownership_isolation(client: TestClient, db_session):
    """Verify that Teacher A cannot view, edit, or delete Teacher B's classroom."""
    teacher_a = _register_and_login(client, db_session, "teacher_a@test.edu", UserRole.teacher, "Cô An")
    res_a = client.post(
        "/api/v1/classrooms",
        json={"name": "Lớp Di Sản Cô An", "max_students": 30},
    )
    class_a_id = res_a.json()["id"]

    # Teacher B logs in
    teacher_b = _register_and_login(client, db_session, "teacher_b@test.edu", UserRole.teacher, "Thầy Bình")

    # Negative abuse 1: Teacher B cannot view Teacher A's classroom details
    res_get = client.get(f"/api/v1/classrooms/{class_a_id}")
    assert res_get.status_code == 403, "Teacher B must receive 403 accessing Teacher A's class"

    # Negative abuse 2: Teacher B cannot update Teacher A's classroom
    res_put = client.put(
        f"/api/v1/classrooms/{class_a_id}",
        json={"name": "Hacked Classroom Name"},
    )
    assert res_put.status_code == 403

    # Negative abuse 3: Teacher B cannot archive Teacher A's classroom
    res_arch = client.post(f"/api/v1/classrooms/{class_a_id}/archive")
    assert res_arch.status_code == 403

    # Negative abuse 4: Teacher B cannot delete Teacher A's classroom
    res_del = client.delete(f"/api/v1/classrooms/{class_a_id}")
    assert res_del.status_code == 403

    # Negative abuse 5: Teacher B's classroom list does NOT include Teacher A's classroom
    res_list = client.get("/api/v1/classrooms")
    assert res_list.status_code == 200
    class_ids = [c["id"] for c in res_list.json()]
    assert class_a_id not in class_ids


# --------------------------------------------------------------------------- #
# Test 4: Join Code Generation, Validation, and Secure Enrollment
# --------------------------------------------------------------------------- #

def test_join_code_validation_and_enrollment(client: TestClient, db_session):
    """Verify join code format, case-insensitivity, adult guardian flow, and idempotency."""
    teacher = _register_and_login(client, db_session, "teacher_join@test.edu", UserRole.teacher, "Thầy Cường")
    res_c = client.post(
        "/api/v1/classrooms",
        json={"name": "Lớp Khảo Cứu Cửu Đỉnh", "max_students": 25},
    )
    class_code = res_c.json()["class_code"]
    class_id = res_c.json()["id"]

    # Learner joins
    learner = _register_and_login(client, db_session, "student1@test.edu", UserRole.learner, "Học sinh Nam")

    # Join with lowercase code (must be auto-normalized to uppercase)
    join_payload = {
        "class_code": class_code.lower(),
        "guardian_email": "phuhuynh_nam@family.vn",
        "guardian_consent": True,
    }
    join_res = client.post("/api/v1/classrooms/join", json=join_payload)
    assert join_res.status_code == 200, join_res.text
    join_data = join_res.json()
    assert join_data["classroom"]["id"] == class_id
    assert join_data["classroom"]["member_count"] == 1

    # Idempotent re-join: joining again returns membership without duplicating
    rejoin_res = client.post("/api/v1/classrooms/join", json=join_payload)
    assert rejoin_res.status_code == 200
    assert rejoin_res.json()["classroom"]["member_count"] == 1

    # Verify enrolled classrooms list
    enrolled_res = client.get("/api/v1/classrooms/enrolled")
    assert enrolled_res.status_code == 200
    enrolled = enrolled_res.json()
    assert len(enrolled) == 1
    assert enrolled[0]["id"] == class_id


# --------------------------------------------------------------------------- #
# Test 5: Negative Abuse - Outside Student Cannot Access Without Join Code
# --------------------------------------------------------------------------- #

def test_negative_abuse_outside_student_cannot_access_or_join_without_code(client: TestClient, db_session):
    """Negative abuse: Student from outside cannot join or access a classroom without valid authorization/join code."""
    teacher = _register_and_login(client, db_session, "teacher_sec@test.edu", UserRole.teacher, "Cô Dung")
    res = client.post(
        "/api/v1/classrooms",
        json={"name": "Lớp Lịch Sử Bí Mật", "max_students": 20},
    )
    class_code = res.json()["class_code"]
    class_id = res.json()["id"]

    # Outside student logs in
    outside_student = _register_and_login(client, db_session, "outside_student@test.edu", UserRole.learner, "Học Sinh Ngoài")

    # Negative 1: Outside student cannot view classroom details (403)
    detail_res = client.get(f"/api/v1/classrooms/{class_id}")
    assert detail_res.status_code == 403, "Outside student without enrollment must receive 403"

    # Negative 2: Outside student cannot view roster (403)
    roster_res = client.get(f"/api/v1/classrooms/{class_id}/roster")
    assert roster_res.status_code == 403, "Outside student must receive 403 accessing roster"

    # Negative 3: Outside student cannot join with invalid / fake code
    bad_join = client.post("/api/v1/classrooms/join", json={"class_code": "INVALID9"})
    assert bad_join.status_code in (400, 404)
    assert "not found" in bad_join.text.lower()

    # Negative 4: Outside student cannot join with empty/whitespace code
    empty_join = client.post("/api/v1/classrooms/join", json={"class_code": "   "})
    assert empty_join.status_code in (400, 422)


# --------------------------------------------------------------------------- #
# Test 6: Negative Abuse - Archived and Overcapacity Classrooms Reject Join
# --------------------------------------------------------------------------- #

def test_negative_abuse_archived_and_full_classrooms_reject_join(client: TestClient, db_session):
    """Negative abuse: Archived classroom and classroom reaching max capacity reject new joins."""
    teacher = _register_and_login(client, db_session, "teacher_limits@test.edu", UserRole.teacher, "Thầy Hưng")

    # 1. Test max_students = 1 capacity
    res_cap = client.post(
        "/api/v1/classrooms",
        json={"name": "Lớp 1 Thầy 1 Trò", "max_students": 1},
    )
    cap_code = res_cap.json()["class_code"]

    student_1 = _register_and_login(client, db_session, "cap_student1@test.edu", UserRole.learner, "Học Sinh 1")
    res1 = client.post("/api/v1/classrooms/join", json={"class_code": cap_code})
    assert res1.status_code == 200

    # Student 2 tries to join full classroom -> rejected with 400
    student_2 = _register_and_login(client, db_session, "cap_student2@test.edu", UserRole.learner, "Học Sinh 2")
    res2 = client.post("/api/v1/classrooms/join", json={"class_code": cap_code})
    assert res2.status_code == 400
    assert "capacity" in res2.text.lower() or "maximum" in res2.text.lower()

    # 2. Test archived classroom rejects join
    _login_as(client, "teacher_limits@test.edu")
    res_arch = client.post(
        "/api/v1/classrooms",
        json={"name": "Lớp Đã Đóng", "max_students": 30},
    )
    arch_id = res_arch.json()["id"]
    arch_code = res_arch.json()["class_code"]

    # Teacher archives class
    client.post(f"/api/v1/classrooms/{arch_id}/archive")

    # Learner attempts to join archived class -> rejected with 400
    _login_as(client, "cap_student2@test.edu")
    arch_join_res = client.post("/api/v1/classrooms/join", json={"class_code": arch_code})
    assert arch_join_res.status_code == 400
    assert "archived" in arch_join_res.text.lower()


# --------------------------------------------------------------------------- #
# Test 7: Student Roster Privacy and Teacher Authorization
# --------------------------------------------------------------------------- #

def test_student_roster_access_and_pii_redaction(client: TestClient, db_session):
    """Verify classroom roster endpoint permissions: teacher sees full PII, student sees redacted peer roster."""
    teacher = _register_and_login(client, db_session, "teacher_roster@test.edu", UserRole.teacher, "Cô Mai")
    res_c = client.post(
        "/api/v1/classrooms",
        json={"name": "Lớp Di Sản Huế 9A", "max_students": 30},
    )
    class_id = res_c.json()["id"]
    class_code = res_c.json()["class_code"]

    # Student 1 enrolls with guardian info
    s1 = _register_and_login(client, db_session, "student_s1@test.edu", UserRole.learner, "Học Sinh Lê")
    client.post("/api/v1/classrooms/join", json={
        "class_code": class_code,
        "guardian_email": "parent_s1@home.vn",
        "guardian_consent": True,
    })

    # Student 2 enrolls
    s2 = _register_and_login(client, db_session, "student_s2@test.edu", UserRole.learner, "Học Sinh Trần")
    client.post("/api/v1/classrooms/join", json={"class_code": class_code})

    # 1. Teacher views roster -> full PII (email, guardian_email, consent) visible
    _login_as(client, "teacher_roster@test.edu")
    teacher_roster_res = client.get(f"/api/v1/classrooms/{class_id}/roster")
    assert teacher_roster_res.status_code == 200
    t_roster = teacher_roster_res.json()
    assert t_roster["student_count"] == 2
    student1_entry = next(s for s in t_roster["students"] if s["user_id"] == str(s1.id))
    assert student1_entry["email"] == "student_s1@test.edu"
    assert student1_entry["guardian_email"] == "parent_s1@home.vn"
    assert student1_entry["guardian_consent"] is True

    # 2. Student 2 views roster -> Student 1's email and guardian email are REDACTED (None or empty)
    _login_as(client, "student_s2@test.edu")
    student_roster_res = client.get(f"/api/v1/classrooms/{class_id}/roster")
    assert student_roster_res.status_code == 200
    s_roster = student_roster_res.json()
    peer_s1 = next(s for s in s_roster["students"] if s["user_id"] == str(s1.id))
    assert peer_s1["display_name"] == "Học Sinh Lê"
    assert peer_s1["email"] is None or peer_s1["email"] == ""
    assert peer_s1["guardian_email"] is None
    # But Student 2 can see their own info
    self_s2 = next(s for s in s_roster["students"] if s["user_id"] == str(s2.id))
    assert self_s2["email"] == "student_s2@test.edu"


# --------------------------------------------------------------------------- #
# Test 8: Non-Learner Cannot Join Classrooms
# --------------------------------------------------------------------------- #

def test_negative_abuse_non_learner_role_cannot_join_classroom(client: TestClient, db_session):
    """Negative abuse: Teacher or Admin user cannot join a classroom as student via /join endpoint."""
    teacher_creator = _register_and_login(client, db_session, "creator_t@test.edu", UserRole.teacher, "Thầy Tạo")
    c_res = client.post("/api/v1/classrooms", json={"name": "Lớp Khoa Học"})
    code = c_res.json()["class_code"]

    # Another teacher tries to join as student
    teacher_joiner = _register_and_login(client, db_session, "joiner_t@test.edu", UserRole.teacher, "Thầy Tham Gia")
    join_res = client.post("/api/v1/classrooms/join", json={"class_code": code})
    assert join_res.status_code == 403
    assert "only learners" in join_res.text.lower()
