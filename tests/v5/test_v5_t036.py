# -*- coding: utf-8 -*-
"""V5-T036: Teacher gradebook and authenticated CSV export with horizontal privilege protection.

Audits and verifies:
1. In backend/routers/classrooms.py:
   - `get_classroom_gradebook`: Real student roster, scores, missing/pending filters.
   - `export_classroom_gradebook_csv`: Authenticated CSV export with UTF-8 BOM encoding for Excel.
   - `export_class_progress`: Classroom progress CSV export.
2. Horizontal Privilege Escalation Protection (IDOR safety):
   - Teacher A from Class A cannot access or export Class B gradebook (blocked with 403 Forbidden).
   - Teacher B from Class B cannot access or export Class A gradebook (blocked with 403 Forbidden).
   - Learner / student cannot access or export gradebook (blocked with 403 Forbidden).
   - Unauthenticated caller receives 401 Unauthorized.
   - Admin user CAN view and export cross-classroom gradebooks.
3. Roster filtering and metrics:
   - Filter by status `missing`, `pending`, `completed`, `all`.
   - Search by student display name or email.
   - Anonymized export replaces real names with `HS-ANON-xxx` codes.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest

from backend.models import (
    AssignmentProgress,
    ClassMember,
    Classroom,
    Quest,
    QuestAssignment,
    User,
    UserRole,
)
from backend.security import hash_password


def _create_user(
    db_session,
    email: str,
    role: UserRole = UserRole.teacher,
    display_name: str | None = None,
) -> User:
    """Helper to persist a user with specific role."""
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


def _login_user(client, email: str, password: str = "Password123!") -> dict:
    """Login helper setting session cookies on test client."""
    client.cookies.clear()
    res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    return res.json()


def _create_test_environment(db_session):
    """Seed Teacher A (Class A) and Teacher B (Class B) with students and assignments."""
    teacher_a = _create_user(
        db_session, f"teacher_a_{uuid.uuid4().hex[:6]}@school.edu.vn", role=UserRole.teacher, display_name="Thầy Nguyễn Văn A"
    )
    teacher_b = _create_user(
        db_session, f"teacher_b_{uuid.uuid4().hex[:6]}@school.edu.vn", role=UserRole.teacher, display_name="Cô Lê Thị B"
    )
    admin_user = _create_user(
        db_session, f"admin_{uuid.uuid4().hex[:6]}@school.edu.vn", role=UserRole.admin, display_name="Quản Trị Viên"
    )

    # Classrooms
    class_a = Classroom(
        name="Lớp 10A1 — THPT Quốc Học Huế",
        teacher_id=teacher_a.id,
        class_code=f"C{uuid.uuid4().hex[:6].upper()}",
        is_archived=False,
    )
    class_b = Classroom(
        name="Lớp 10B2 — THPT Hai Bà Trưng",
        teacher_id=teacher_b.id,
        class_code=f"C{uuid.uuid4().hex[:6].upper()}",
        is_archived=False,
    )
    db_session.add_all([class_a, class_b])
    db_session.flush()

    # Students for Class A
    stu_a1 = _create_user(
        db_session, f"stu_a1_{uuid.uuid4().hex[:6]}@student.edu.vn", role=UserRole.learner, display_name="Nguyễn Hoàng Nam"
    )
    stu_a2 = _create_user(
        db_session, f"stu_a2_{uuid.uuid4().hex[:6]}@student.edu.vn", role=UserRole.learner, display_name="Trần Phương Thảo"
    )
    stu_a3 = _create_user(
        db_session, f"stu_a3_{uuid.uuid4().hex[:6]}@student.edu.vn", role=UserRole.learner, display_name="Lê Quốc Bảo"
    )

    # Student for Class B
    stu_b1 = _create_user(
        db_session, f"stu_b1_{uuid.uuid4().hex[:6]}@student.edu.vn", role=UserRole.learner, display_name="Võ Quỳnh Anh"
    )

    mem_a1 = ClassMember(class_id=class_a.id, user_id=stu_a1.id, role="learner")
    mem_a2 = ClassMember(class_id=class_a.id, user_id=stu_a2.id, role="learner")
    mem_a3 = ClassMember(class_id=class_a.id, user_id=stu_a3.id, role="learner")
    mem_b1 = ClassMember(class_id=class_b.id, user_id=stu_b1.id, role="learner")
    db_session.add_all([mem_a1, mem_a2, mem_a3, mem_b1])
    db_session.flush()

    # Quests & Assignments for Class A
    quest1 = Quest(
        slug=f"quest-1-{uuid.uuid4().hex[:6]}",
        name="Khảo sát Ngọ Môn",
        description="Nghiên cứu kiến trúc Ngọ Môn",
        category="heritage",
        display_order=1,
        is_active=True,
    )
    quest2 = Quest(
        slug=f"quest-2-{uuid.uuid4().hex[:6]}",
        name="Khảo sát Điện Thái Hòa",
        description="Nghiên cứu nhất thi nhất họa",
        category="heritage",
        display_order=2,
        is_active=True,
    )
    db_session.add_all([quest1, quest2])
    db_session.flush()

    now = datetime.now(timezone.utc)
    # Assignment 1: Due in 7 days (Future -> pending if not completed)
    assign_active = QuestAssignment(
        class_id=class_a.id,
        quest_id=quest1.id,
        assigned_by_id=teacher_a.id,
        due_at=now + timedelta(days=7),
        points_override=10,
        notes="Nhiệm vụ tuần 1",
    )
    # Assignment 2: Due 2 days ago (Past -> missing if not completed)
    assign_overdue = QuestAssignment(
        class_id=class_a.id,
        quest_id=quest2.id,
        assigned_by_id=teacher_a.id,
        due_at=now - timedelta(days=2),
        points_override=10,
        notes="Nhiệm vụ tuần 2 (đã quá hạn)",
    )
    db_session.add_all([assign_active, assign_overdue])
    db_session.flush()

    # Student 1: Completed both assignments -> status: completed
    prog_a1_1 = AssignmentProgress(
        assignment_id=assign_active.id,
        user_id=stu_a1.id,
        status="completed",
        completed_at=now - timedelta(days=1),
    )
    prog_a1_2 = AssignmentProgress(
        assignment_id=assign_overdue.id,
        user_id=stu_a1.id,
        status="completed",
        completed_at=now - timedelta(days=3),
    )

    # Student 2: In progress on assign_active, NOT submitted assign_overdue -> status: missing (due to overdue assignment)
    prog_a2_1 = AssignmentProgress(
        assignment_id=assign_active.id,
        user_id=stu_a2.id,
        status="in_progress",
    )

    # Student 3: Completed assign_overdue, in progress on assign_active -> status: pending (active assignment pending)
    prog_a3_1 = AssignmentProgress(
        assignment_id=assign_active.id,
        user_id=stu_a3.id,
        status="in_progress",
    )
    prog_a3_2 = AssignmentProgress(
        assignment_id=assign_overdue.id,
        user_id=stu_a3.id,
        status="completed",
        completed_at=now - timedelta(days=3),
    )

    db_session.add_all([prog_a1_1, prog_a1_2, prog_a2_1, prog_a3_1, prog_a3_2])
    db_session.commit()

    return {
        "teacher_a": teacher_a,
        "teacher_b": teacher_b,
        "admin": admin_user,
        "class_a": class_a,
        "class_b": class_b,
        "students_a": [stu_a1, stu_a2, stu_a3],
        "student_b": stu_b1,
    }


def test_unauthenticated_gradebook_and_export_returns_401(client):
    """Unauthenticated requests to gradebook and CSV exports must return 401."""
    client.cookies.clear()
    dummy_id = uuid.uuid4()
    r1 = client.get(f"/api/v1/classrooms/{dummy_id}/gradebook")
    assert r1.status_code == 401

    r2 = client.get(f"/api/v1/classrooms/{dummy_id}/gradebook/export")
    assert r2.status_code == 401

    r3 = client.get(f"/api/v1/classrooms/{dummy_id}/export")
    assert r3.status_code == 401


def test_learner_access_to_gradebook_returns_403(client, db_session):
    """Learners/students must receive 403 Forbidden when attempting to access gradebook."""
    env = _create_test_environment(db_session)
    student = env["students_a"][0]
    _login_user(client, student.email)

    r1 = client.get(f"/api/v1/classrooms/{env['class_a'].id}/gradebook")
    assert r1.status_code == 403

    r2 = client.get(f"/api/v1/classrooms/{env['class_a'].id}/gradebook/export")
    assert r2.status_code == 403

    r3 = client.get(f"/api/v1/classrooms/{env['class_a'].id}/export")
    assert r3.status_code == 403


def test_teacher_horizontal_privilege_escalation_blocked_returns_403(client, db_session):
    """Teacher A cannot view or export Teacher B's classroom gradebook (horizontal IDOR blocked)."""
    env = _create_test_environment(db_session)
    teacher_a = env["teacher_a"]
    teacher_b = env["teacher_b"]
    class_a = env["class_a"]
    class_b = env["class_b"]

    _login_user(client, teacher_a.email)

    # Teacher A attempts to access Classroom B gradebook
    r_gradebook = client.get(f"/api/v1/classrooms/{class_b.id}/gradebook")
    assert r_gradebook.status_code == 403, f"Expected 403 for Teacher A on Class B, got {r_gradebook.status_code}"

    # Teacher A attempts to export Classroom B gradebook CSV
    r_export_gradebook = client.get(f"/api/v1/classrooms/{class_b.id}/gradebook/export")
    assert r_export_gradebook.status_code == 403, f"Expected 403 on gradebook export, got {r_export_gradebook.status_code}"

    # Teacher A attempts to export Classroom B progress CSV
    r_export = client.get(f"/api/v1/classrooms/{class_b.id}/export")
    assert r_export.status_code == 403, f"Expected 403 on progress export, got {r_export.status_code}"

    # Reverse: Teacher B attempts to access Classroom A gradebook
    _login_user(client, teacher_b.email)
    r_b_on_a = client.get(f"/api/v1/classrooms/{class_a.id}/gradebook")
    assert r_b_on_a.status_code == 403

    r_b_export = client.get(f"/api/v1/classrooms/{class_a.id}/gradebook/export")
    assert r_b_export.status_code == 403


def test_teacher_can_view_own_gradebook_and_roster(client, db_session):
    """Teacher can view their own classroom gradebook with roster, scores, and metrics."""
    env = _create_test_environment(db_session)
    teacher_a = env["teacher_a"]
    class_a = env["class_a"]
    _login_user(client, teacher_a.email)

    res = client.get(f"/api/v1/classrooms/{class_a.id}/gradebook")
    assert res.status_code == 200
    data = res.json()

    assert data["classroom_id"] == str(class_a.id)
    assert data["classroom_name"] == class_a.name
    assert data["teacher_id"] == str(teacher_a.id)
    assert data["total_students"] == 3

    # Check metrics
    metrics = data["metrics"]
    assert metrics["total_students"] == 3
    assert metrics["completed_count"] == 1  # Student 1
    assert metrics["missing_count"] == 1    # Student 2
    assert metrics["pending_count"] == 1    # Student 3

    # Check roster items
    roster = data["roster"]
    assert len(roster) == 3

    student_statuses = {s["display_name"]: s["status"] for s in roster}
    assert student_statuses["Nguyễn Hoàng Nam"] == "completed"
    assert student_statuses["Trần Phương Thảo"] == "missing"
    assert student_statuses["Lê Quốc Bảo"] == "pending"

    # Verify assignment structure for each student
    nam = next(s for s in roster if s["display_name"] == "Nguyễn Hoàng Nam")
    assert nam["completed_count"] == 2
    assert nam["missing_count"] == 0
    assert len(nam["assignments"]) == 2


def test_teacher_gradebook_filter_by_status_and_search(client, db_session):
    """Teacher can filter gradebook by missing/pending/completed status and search query."""
    env = _create_test_environment(db_session)
    teacher_a = env["teacher_a"]
    class_a = env["class_a"]
    _login_user(client, teacher_a.email)

    # 1. Filter by status: missing
    res_missing = client.get(
        f"/api/v1/classrooms/{class_a.id}/gradebook?status_filter=missing"
    )
    assert res_missing.status_code == 200
    roster_missing = res_missing.json()["roster"]
    assert len(roster_missing) == 1
    assert roster_missing[0]["display_name"] == "Trần Phương Thảo"
    assert roster_missing[0]["status"] == "missing"

    # 2. Filter by status: pending
    res_pending = client.get(
        f"/api/v1/classrooms/{class_a.id}/gradebook?status_filter=pending"
    )
    assert res_pending.status_code == 200
    roster_pending = res_pending.json()["roster"]
    assert len(roster_pending) == 1
    assert roster_pending[0]["display_name"] == "Lê Quốc Bảo"
    assert roster_pending[0]["status"] == "pending"

    # 3. Filter by status: completed
    res_completed = client.get(
        f"/api/v1/classrooms/{class_a.id}/gradebook?status_filter=completed"
    )
    assert res_completed.status_code == 200
    roster_completed = res_completed.json()["roster"]
    assert len(roster_completed) == 1
    assert roster_completed[0]["display_name"] == "Nguyễn Hoàng Nam"
    assert roster_completed[0]["status"] == "completed"

    # 4. Search by display name
    res_search = client.get(
        f"/api/v1/classrooms/{class_a.id}/gradebook?search=Hoàng+Nam"
    )
    assert res_search.status_code == 200
    assert len(res_search.json()["roster"]) == 1
    assert res_search.json()["roster"][0]["display_name"] == "Nguyễn Hoàng Nam"

    # 5. Search by email
    res_email = client.get(
        f"/api/v1/classrooms/{class_a.id}/gradebook?search=student.edu.vn"
    )
    assert res_email.status_code == 200
    assert len(res_email.json()["roster"]) == 3


def test_teacher_can_export_gradebook_csv_and_anonymized(client, db_session):
    """Teacher can export gradebook as CSV with UTF-8 BOM, including anonymized export."""
    env = _create_test_environment(db_session)
    teacher_a = env["teacher_a"]
    class_a = env["class_a"]
    _login_user(client, teacher_a.email)

    # 1. Standard Gradebook CSV Export
    res_csv = client.get(
        f"/api/v1/classrooms/{class_a.id}/gradebook/export"
    )
    assert res_csv.status_code == 200
    assert "text/csv" in res_csv.headers["content-type"]
    assert f'filename="classroom_{class_a.id}_gradebook.csv"' in res_csv.headers["content-disposition"]

    csv_text = res_csv.text
    # UTF-8 BOM check
    assert csv_text.startswith("\ufeff")
    assert "Mã học sinh" in csv_text
    assert "Họ và tên" in csv_text
    assert "Tiến độ hoàn thành (%)" in csv_text
    assert "Nguyễn Hoàng Nam" in csv_text
    assert "Trần Phương Thảo" in csv_text
    assert "Lê Quốc Bảo" in csv_text

    # 2. Filtered Gradebook CSV Export
    res_filtered = client.get(
        f"/api/v1/classrooms/{class_a.id}/gradebook/export?status_filter=missing"
    )
    assert res_filtered.status_code == 200
    assert "Trần Phương Thảo" in res_filtered.text
    assert "Nguyễn Hoàng Nam" not in res_filtered.text

    # 3. Anonymized Gradebook CSV Export
    res_anon = client.get(
        f"/api/v1/classrooms/{class_a.id}/gradebook/export?anonymize=true"
    )
    assert res_anon.status_code == 200
    anon_text = res_anon.text
    assert "HS-ANON-001" in anon_text
    assert "Học sinh 001" in anon_text
    assert "Nguyễn Hoàng Nam" not in anon_text
    assert "Trần Phương Thảo" not in anon_text

    # 4. Progress CSV Export endpoint
    res_progress = client.get(
        f"/api/v1/classrooms/{class_a.id}/export"
    )
    assert res_progress.status_code == 200
    assert "text/csv" in res_progress.headers["content-type"]
    assert "Student ID" in res_progress.text


def test_admin_cross_classroom_access(client, db_session):
    """Admin user can view and export gradebook for any classroom across schools."""
    env = _create_test_environment(db_session)
    admin_user = env["admin"]
    class_a = env["class_a"]
    class_b = env["class_b"]

    _login_user(client, admin_user.email)

    # Admin access Class A
    res_a = client.get(f"/api/v1/classrooms/{class_a.id}/gradebook")
    assert res_a.status_code == 200
    assert res_a.json()["total_students"] == 3

    # Admin access Class B
    res_b = client.get(f"/api/v1/classrooms/{class_b.id}/gradebook")
    assert res_b.status_code == 200
    assert res_b.json()["total_students"] == 1

    # Admin export Class A
    res_export = client.get(f"/api/v1/classrooms/{class_a.id}/gradebook/export")
    assert res_export.status_code == 200
    assert "Nguyễn Hoàng Nam" in res_export.text
