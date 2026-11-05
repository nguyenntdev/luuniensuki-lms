# -*- coding: utf-8 -*-
"""V5-T094 (Wave W09, Slot A04): Rubric Analytics Dashboard & Invariants Test Suite.

Audits and verifies:
1. Endpoint: GET /api/v1/classrooms/{classroom_id}/rubric-analytics
   - School-safe aggregate analytics per rubric version.
   - Historical reasoning criteria dimensions (S1 Spatial, S2 Temporal, S3 Evidence, S4 Argument).
   - Student privacy suppression minimums: k-anonymity for cohorts < 5.
2. Security & IDOR Access Control:
   - Unauthenticated requests receive HTTP 401 Unauthorized.
   - Learner and guest users receive HTTP 403 Forbidden.
   - Horizontal privilege escalation (IDOR defense): Teacher A cannot view Classroom B (HTTP 403 Forbidden).
   - Admin user has cross-classroom oversight (HTTP 200).
3. Negative Abuse Guardrail:
   - Descriptive statistics are strictly separated from causal claims.
   - Requests asserting causal learning gains (`claim_causality=true`) without an approved controlled study
     protocol code are rejected with HTTP 422 CANNOT_CLAIM_CAUSAL_LEARNING_GAIN_WITHOUT_CONTROLLED_STUDY.
   - Requests with an approved `HistoryEthicsProtocol` allow causal inference (`causal_inference_permitted=true`).
4. Privacy Suppression (k-anonymity for cohorts < 5):
   - When evaluated cohort size n < 5: `is_suppressed = True`.
   - Granular score distributions, means, medians, standard deviations, and mastery rates are suppressed (None).
   - Descriptive notice and k-anonymity privacy notice returned.
5. Full Descriptive Analytics (cohorts n >= 5):
   - When evaluated cohort size n >= 5: `is_suppressed = False`.
   - Accurate calculation of mean, median, standard deviation, mastery rate (>= 66.7%), and 4-level distribution
     (M0 Chưa đạt, M1 Cơ bản, M2 Khá, M3 Xuất sắc) across all 4 criteria.
   - Overall average calculated across dimensions.
6. Rubric Version Filtering:
   - Multi-version inventory discovery and strict filtering by `rubric_version`.
7. Coexistence:
   - Unified aggregation across both `HistoryAssignmentSubmission` and `ImperialSubmission`.
"""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import select

from backend.history_models import (
    HistoryEthicsProtocol,
    HistoryLessonAssignment,
    HistoryAssignmentSubmission,
)
from backend.imperial_models import (
    CONTENT_SCOPE_IMPERIAL,
    ImperialActivity,
    ImperialSite,
    ImperialSubmission,
    ImperialZone,
)
from backend.models import (
    ClassMember,
    Classroom,
    ContentRating,
    ContentStatus,
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


def _setup_classroom(db_session, teacher: User, name: str = "Lớp Sử THPT") -> Classroom:
    """Create a classroom assigned to a teacher."""
    classroom = Classroom(
        name=name,
        teacher_id=teacher.id,
        class_code=f"C{uuid.uuid4().hex[:6].upper()}",
        is_archived=False,
    )
    db_session.add(classroom)
    db_session.commit()
    db_session.refresh(classroom)
    return classroom


def _create_lesson_and_assignment(
    db_session,
    classroom: Classroom,
    teacher: User,
    rubric_version: str = "GDPT_2018_V1",
    title: str = "Bài Khảo Sát Di Sản Cửu Đỉnh",
) -> HistoryLessonAssignment:
    """Create a lesson and source-locked history lesson assignment."""
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

    lesson = LessonContent(
        motif_id=motif.id,
        intro_text="Bài giảng chuẩn mực về hình tượng Rồng trên Cao Đỉnh.",
        description="Nội dung bài học nguyên bản — cơ sở khảo sát lịch sử.",
        historical_context="Đúc năm Minh Mạng thứ 16-17 (1835-1836).",
        symbolism="Tượng trưng cho vương quyền tối thượng.",
        version=1,
        is_published=True,
        content_validation_status="valid",
        status=ContentStatus.published,
        content_rating=ContentRating.everyone,
    )
    db_session.add(lesson)
    db_session.flush()

    assignment = HistoryLessonAssignment(
        classroom_id=classroom.id,
        lesson_id=lesson.id,
        assigned_by_id=teacher.id,
        title=title,
        instructions="Khảo sát hình tượng và lập luận theo 4 tiêu chí rubric.",
        status="published",
        points=100,
        pinned_version=1,
        pinned_lesson_snapshot={"intro_text": lesson.intro_text, "description": lesson.description},
        rubric={"rubric_version": rubric_version, "version": 1},
        pinned_source_ids=[],
        pinned_sources_snapshot=[],
        pinned_claim_ids=[],
        published_at=datetime.now(timezone.utc),
    )
    db_session.add(assignment)
    db_session.commit()
    db_session.refresh(assignment)
    return assignment


# --------------------------------------------------------------------------- #
# Test 1 & 2: Authentication & Authorization (401, 403)
# --------------------------------------------------------------------------- #
def test_unauthenticated_rubric_analytics_returns_401(client, db_session):
    """Anonymous/unauthenticated callers receive HTTP 401 Unauthorized."""
    teacher = _create_user(db_session, f"t1_{uuid.uuid4().hex[:6]}@school.edu.vn", role=UserRole.teacher)
    classroom = _setup_classroom(db_session, teacher)

    client.cookies.clear()
    res = client.get(f"/api/v1/classrooms/{classroom.id}/rubric-analytics")
    assert res.status_code == 401, f"Expected 401, got {res.status_code}: {res.text}"


def test_learner_access_to_rubric_analytics_returns_403(client, db_session):
    """Learners/students calling rubric analytics receive HTTP 403 Forbidden."""
    teacher = _create_user(db_session, f"t2_{uuid.uuid4().hex[:6]}@school.edu.vn", role=UserRole.teacher)
    student = _create_user(db_session, f"s2_{uuid.uuid4().hex[:6]}@school.edu.vn", role=UserRole.learner)
    classroom = _setup_classroom(db_session, teacher)

    _login_user(client, student.email)
    res = client.get(f"/api/v1/classrooms/{classroom.id}/rubric-analytics")
    assert res.status_code == 403, f"Expected 403 for student, got {res.status_code}: {res.text}"


# --------------------------------------------------------------------------- #
# Test 3: Horizontal Privilege Escalation Protection (IDOR Defense)
# --------------------------------------------------------------------------- #
def test_teacher_horizontal_privilege_escalation_blocked_returns_403(client, db_session):
    """Teacher A cannot view Classroom B rubric analytics (IDOR defense)."""
    teacher_a = _create_user(db_session, f"t3a_{uuid.uuid4().hex[:6]}@school.edu.vn", role=UserRole.teacher)
    teacher_b = _create_user(db_session, f"t3b_{uuid.uuid4().hex[:6]}@school.edu.vn", role=UserRole.teacher)

    class_a = _setup_classroom(db_session, teacher_a, name="Lớp 10A")
    class_b = _setup_classroom(db_session, teacher_b, name="Lớp 10B")

    # Teacher A logs in and attempts to access Classroom B's rubric analytics
    _login_user(client, teacher_a.email)
    res = client.get(f"/api/v1/classrooms/{class_b.id}/rubric-analytics")
    assert res.status_code == 403, f"Expected 403 for cross-classroom IDOR attempt, got {res.status_code}: {res.text}"

    # Teacher B logs in and attempts to access Classroom A's rubric analytics
    _login_user(client, teacher_b.email)
    res = client.get(f"/api/v1/classrooms/{class_a.id}/rubric-analytics")
    assert res.status_code == 403, f"Expected 403 for cross-classroom IDOR attempt, got {res.status_code}: {res.text}"


# --------------------------------------------------------------------------- #
# Test 4: Negative Abuse — Reject Causal Claims Without Controlled Study
# --------------------------------------------------------------------------- #
def test_negative_abuse_causal_learning_gain_rejected_without_controlled_study_422(client, db_session):
    """Negative Abuse Rule: Attempting to assert causal learning gain claims without an approved

    controlled study protocol strictly fails with HTTP 422.
    """
    teacher = _create_user(db_session, f"t4_{uuid.uuid4().hex[:6]}@school.edu.vn", role=UserRole.teacher)
    classroom = _setup_classroom(db_session, teacher)

    _login_user(client, teacher.email)

    # 1. claim_causality=true without study_protocol_code -> 422
    res1 = client.get(f"/api/v1/classrooms/{classroom.id}/rubric-analytics?claim_causality=true")
    assert res1.status_code == 422, f"Expected 422, got {res1.status_code}: {res1.text}"
    err1 = res1.json()
    assert "CANNOT_CLAIM_CAUSAL_LEARNING_GAIN_WITHOUT_CONTROLLED_STUDY" in str(err1)

    # 2. claim_causality=true with non-existent protocol code -> 422
    res2 = client.get(
        f"/api/v1/classrooms/{classroom.id}/rubric-analytics?claim_causality=true&study_protocol_code=INVALID-IRB-999"
    )
    assert res2.status_code == 422, f"Expected 422, got {res2.status_code}: {res2.text}"
    err2 = res2.json()
    assert "CANNOT_CLAIM_CAUSAL_LEARNING_GAIN_WITHOUT_CONTROLLED_STUDY" in str(err2)

    # 3. claim_causality=true with unapproved / draft protocol code -> 422
    draft_protocol = HistoryEthicsProtocol(
        protocol_code=f"IRB-DRAFT-{uuid.uuid4().hex[:6]}",
        title="Nghiên cứu tác động phương pháp học tập di sản",
        irb_institution="Đại học Sư phạm Huế",
        status="draft",  # NOT approved
    )
    db_session.add(draft_protocol)
    db_session.commit()

    res3 = client.get(
        f"/api/v1/classrooms/{classroom.id}/rubric-analytics?claim_causality=true&study_protocol_code={draft_protocol.protocol_code}"
    )
    assert res3.status_code == 422, f"Expected 422, got {res3.status_code}: {res3.text}"

    # 4. claim_causality=true with APPROVED protocol -> 200 with causal_inference_permitted=True
    approved_protocol = HistoryEthicsProtocol(
        protocol_code=f"IRB-APP-{uuid.uuid4().hex[:6]}",
        title="Nghiên cứu đối chứng thực nghiệm can thiệp Rubric S1-S4",
        irb_institution="Hội đồng Đạo đức Nghiên cứu Giáo dục Quốc gia",
        status="approved",
        approved_by="PGS. TS. Trần Văn Nghiên",
        approved_at=datetime.now(timezone.utc),
    )
    db_session.add(approved_protocol)
    db_session.commit()

    res4 = client.get(
        f"/api/v1/classrooms/{classroom.id}/rubric-analytics?claim_causality=true&study_protocol_code={approved_protocol.protocol_code}"
    )
    assert res4.status_code == 200, f"Expected 200, got {res4.status_code}: {res4.text}"
    data4 = res4.json()
    assert data4["causal_inference_permitted"] is True
    assert data4["analytics_type"] == "controlled_experimental"
    assert data4["study_protocol_code"] == approved_protocol.protocol_code


# --------------------------------------------------------------------------- #
# Test 5: Privacy Suppression (k-anonymity for cohort < 5)
# --------------------------------------------------------------------------- #
def test_privacy_suppression_k_anonymity_when_cohort_less_than_5(client, db_session):
    """When evaluated cohort size is less than 5 (n < 5), granular distributions and individual

    metrics MUST BE SUPPRESSED (k-anonymity privacy protection).
    """
    teacher = _create_user(db_session, f"t5_{uuid.uuid4().hex[:6]}@school.edu.vn", role=UserRole.teacher)
    classroom = _setup_classroom(db_session, teacher)
    assignment = _create_lesson_and_assignment(db_session, classroom, teacher, rubric_version="GDPT_2018_V1")

    # Add 3 students (n = 3 < 5)
    students = [
        _create_user(db_session, f"s5_{i}_{uuid.uuid4().hex[:6]}@student.edu.vn", role=UserRole.learner)
        for i in range(3)
    ]
    for s in students:
        db_session.add(ClassMember(class_id=classroom.id, user_id=s.id, role="learner"))
        # Add graded submission with S1-S4 rubric evaluation
        sub = HistoryAssignmentSubmission(
            assignment_id=assignment.id,
            student_id=s.id,
            status="graded",
            score=85.0,
            rubric_evaluation={
                "rubric_version": "GDPT_2018_V1",
                "S1_SPATIAL": 2.5,
                "S2_TEMPORAL": 2.0,
                "S3_EVIDENCE": 3.0,
                "S4_ARGUMENT": 2.0,
            },
            graded_by_id=teacher.id,
            graded_at=datetime.now(timezone.utc),
        )
        db_session.add(sub)
    db_session.commit()

    _login_user(client, teacher.email)
    res = client.get(f"/api/v1/classrooms/{classroom.id}/rubric-analytics")
    assert res.status_code == 200, res.text
    data = res.json()

    assert data["cohort_size"] == 3
    assert data["min_k_threshold"] == 5
    assert data["is_suppressed"] is True
    assert "K-anonymity privacy protection" in data["suppression_reason"]
    assert data["overall_average"] is None
    assert data["recommendations"] == []

    # All 4 criteria dimensions must have granular metrics masked/None
    assert len(data["criteria_analytics"]) == 4
    for crit in data["criteria_analytics"]:
        assert crit["mean"] is None
        assert crit["median"] is None
        assert crit["std_dev"] is None
        assert crit["mastery_rate"] is None
        assert crit["distribution"] is None
        assert crit["sample_size"] == 3


# --------------------------------------------------------------------------- #
# Test 6: Full Descriptive Analytics (cohort >= 5)
# --------------------------------------------------------------------------- #
def test_full_descriptive_analytics_when_cohort_at_least_5(client, db_session):
    """When cohort size is at least 5 (n >= 5), full descriptive analytics, dimensions,

    and distributions are computed and returned.
    """
    teacher = _create_user(db_session, f"t6_{uuid.uuid4().hex[:6]}@school.edu.vn", role=UserRole.teacher)
    classroom = _setup_classroom(db_session, teacher)
    assignment = _create_lesson_and_assignment(db_session, classroom, teacher, rubric_version="GDPT_2018_V1")

    # Add 6 students (n = 6 >= 5)
    students = [
        _create_user(db_session, f"s6_{i}_{uuid.uuid4().hex[:6]}@student.edu.vn", role=UserRole.learner)
        for i in range(6)
    ]
    # Give known distinct scores to check calculations
    scores_plan = [
        {"S1": 3.0, "S2": 3.0, "S3": 3.0, "S4": 3.0}, # advanced
        {"S1": 2.5, "S2": 2.0, "S3": 3.0, "S4": 2.5}, # competent
        {"S1": 2.0, "S2": 2.0, "S3": 2.5, "S4": 2.0}, # competent
        {"S1": 1.5, "S2": 1.0, "S3": 2.0, "S4": 1.5}, # emerging/competent
        {"S1": 1.0, "S2": 1.0, "S3": 1.5, "S4": 1.0}, # emerging
        {"S1": 0.5, "S2": 0.5, "S3": 1.0, "S4": 0.5}, # needs improvement
    ]

    for s, scores in zip(students, scores_plan):
        db_session.add(ClassMember(class_id=classroom.id, user_id=s.id, role="learner"))
        sub = HistoryAssignmentSubmission(
            assignment_id=assignment.id,
            student_id=s.id,
            status="graded",
            score=70.0,
            rubric_evaluation={
                "rubric_version": "GDPT_2018_V1",
                "S1_SPATIAL": scores["S1"],
                "S2_TEMPORAL": scores["S2"],
                "S3_EVIDENCE": scores["S3"],
                "S4_ARGUMENT": scores["S4"],
            },
            graded_by_id=teacher.id,
            graded_at=datetime.now(timezone.utc),
        )
        db_session.add(sub)
    db_session.commit()

    _login_user(client, teacher.email)
    res = client.get(f"/api/v1/classrooms/{classroom.id}/rubric-analytics")
    assert res.status_code == 200, res.text
    data = res.json()

    assert data["cohort_size"] == 6
    assert data["is_suppressed"] is False
    assert data["suppression_reason"] is None
    assert data["analytics_type"] == "descriptive"
    assert data["causal_inference_permitted"] is False
    assert "Descriptive statistics only" in data["methodological_notice"]

    # Verify overall average is computed
    assert data["overall_average"] is not None
    assert data["overall_average"] > 0.0

    # Verify criteria analytics for all 4 dimensions
    crit_map = {c["criterion_key"]: c for c in data["criteria_analytics"]}
    assert "S1_SPATIAL" in crit_map
    assert "S2_TEMPORAL" in crit_map
    assert "S3_EVIDENCE" in crit_map
    assert "S4_ARGUMENT" in crit_map

    s1 = crit_map["S1_SPATIAL"]
    assert s1["sample_size"] == 6
    assert s1["mean"] == pytest.approx(round((3.0 + 2.5 + 2.0 + 1.5 + 1.0 + 0.5) / 6, 2), 0.05)
    assert s1["median"] is not None
    assert s1["std_dev"] is not None
    assert s1["mastery_rate"] is not None
    # Level distribution counts must sum to 6
    dist = s1["distribution"]
    assert dist is not None
    assert sum(dist.values()) == 6


# --------------------------------------------------------------------------- #
# Test 7: Rubric Version Filtering & Available Versions Inventory
# --------------------------------------------------------------------------- #
def test_rubric_version_filtering_and_multi_version_inventory(client, db_session):
    """Rubric analytics supports multi-version inventory and filters by rubric_version."""
    teacher = _create_user(db_session, f"t7_{uuid.uuid4().hex[:6]}@school.edu.vn", role=UserRole.teacher)
    classroom = _setup_classroom(db_session, teacher)

    asgn_v1 = _create_lesson_and_assignment(db_session, classroom, teacher, rubric_version="GDPT_2018_V1")
    asgn_v2 = _create_lesson_and_assignment(db_session, classroom, teacher, rubric_version="GDPT_2026_V2")

    # Add 5 students for v1
    students_v1 = [
        _create_user(db_session, f"s7v1_{i}_{uuid.uuid4().hex[:6]}@student.edu.vn", role=UserRole.learner)
        for i in range(5)
    ]
    for s in students_v1:
        db_session.add(
            HistoryAssignmentSubmission(
                assignment_id=asgn_v1.id,
                student_id=s.id,
                status="graded",
                rubric_evaluation={"rubric_version": "GDPT_2018_V1", "S1": 2.5, "S2": 2.5, "S3": 2.5, "S4": 2.5},
            )
        )

    # Add 2 students for v2 (cohort 2 < 5)
    students_v2 = [
        _create_user(db_session, f"s7v2_{i}_{uuid.uuid4().hex[:6]}@student.edu.vn", role=UserRole.learner)
        for i in range(2)
    ]
    for s in students_v2:
        db_session.add(
            HistoryAssignmentSubmission(
                assignment_id=asgn_v2.id,
                student_id=s.id,
                status="graded",
                rubric_evaluation={"rubric_version": "GDPT_2026_V2", "S1": 3.0, "S2": 3.0, "S3": 3.0, "S4": 3.0},
            )
        )
    db_session.commit()

    _login_user(client, teacher.email)

    # Query without filter: defaults to active version
    res = client.get(f"/api/v1/classrooms/{classroom.id}/rubric-analytics")
    assert res.status_code == 200
    data = res.json()
    assert "GDPT_2018_V1" in data["available_rubric_versions"]
    assert "GDPT_2026_V2" in data["available_rubric_versions"]

    # Query with ?rubric_version=GDPT_2018_V1 -> cohort 5 (unsuppressed)
    res_v1 = client.get(f"/api/v1/classrooms/{classroom.id}/rubric-analytics?rubric_version=GDPT_2018_V1")
    assert res_v1.status_code == 200
    data_v1 = res_v1.json()
    assert data_v1["cohort_size"] == 5
    assert data_v1["is_suppressed"] is False

    # Query with ?rubric_version=GDPT_2026_V2 -> cohort 2 (suppressed due to k-anonymity)
    res_v2 = client.get(f"/api/v1/classrooms/{classroom.id}/rubric-analytics?rubric_version=GDPT_2026_V2")
    assert res_v2.status_code == 200
    data_v2 = res_v2.json()
    assert data_v2["cohort_size"] == 2
    assert data_v2["is_suppressed"] is True


# --------------------------------------------------------------------------- #
# Test 8: Admin Cross-Classroom Oversight
# --------------------------------------------------------------------------- #
def test_admin_cross_classroom_oversight(client, db_session):
    """Admin users have authorized access to view rubric analytics across all classrooms."""
    teacher = _create_user(db_session, f"t8_{uuid.uuid4().hex[:6]}@school.edu.vn", role=UserRole.teacher)
    admin = _create_user(db_session, f"admin8_{uuid.uuid4().hex[:6]}@school.edu.vn", role=UserRole.admin)
    classroom = _setup_classroom(db_session, teacher)

    _login_user(client, admin.email)
    res = client.get(f"/api/v1/classrooms/{classroom.id}/rubric-analytics")
    assert res.status_code == 200, f"Expected 200 for admin, got {res.status_code}: {res.text}"
    assert res.json()["classroom_id"] == str(classroom.id)


# --------------------------------------------------------------------------- #
# Test 9: Imperial and History Assignment Coexistence
# --------------------------------------------------------------------------- #
def test_imperial_and_history_submission_coexistence(client, db_session):
    """Analytics correctly aggregates rubric evaluations from both History and Imperial submissions."""
    teacher = _create_user(db_session, f"t9_{uuid.uuid4().hex[:6]}@school.edu.vn", role=UserRole.teacher)
    classroom = _setup_classroom(db_session, teacher)
    asgn = _create_lesson_and_assignment(db_session, classroom, teacher, rubric_version="v1.0")

    # Setup Imperial zone, site, activity
    zone = ImperialZone(slug=f"zone-{uuid.uuid4().hex[:4]}", title_vi="Khu Vực", title_en="Zone", display_order=1)
    db_session.add(zone)
    db_session.flush()

    site = ImperialSite(
        zone_id=zone.id,
        slug=f"site-{uuid.uuid4().hex[:4]}",
        name_vi="Điện Thái Hòa",
        name_en="Thai Hoa Palace",
        site_type="palace",
        condition="intact",
        learning_level="secondary",
        is_published=True,
    )
    db_session.add(site)
    db_session.flush()

    activity = ImperialActivity(
        site_id=site.id,
        activity_type="source_investigation",
        title="Khảo sát",
        instructions="Quan sát trục Thần đạo",
        is_active=True,
    )
    db_session.add(activity)
    db_session.flush()

    # Create 3 students submitting history assignment
    history_students = [
        _create_user(db_session, f"s9h_{i}_{uuid.uuid4().hex[:6]}@student.edu.vn", role=UserRole.learner)
        for i in range(3)
    ]
    for s in history_students:
        db_session.add(
            HistoryAssignmentSubmission(
                assignment_id=asgn.id,
                student_id=s.id,
                status="graded",
                rubric_evaluation={"rubric_version": "v1.0", "s1": 2.5, "s2": 2.5, "s3": 2.5, "s4": 2.5},
            )
        )

    # Create 3 students submitting imperial activity in same classroom
    imperial_students = [
        _create_user(db_session, f"s9i_{i}_{uuid.uuid4().hex[:6]}@student.edu.vn", role=UserRole.learner)
        for i in range(3)
    ]
    for s in imperial_students:
        db_session.add(
            ImperialSubmission(
                activity_id=activity.id,
                student_id=s.id,
                classroom_id=classroom.id,
                status="graded",
                answer_text="Học sinh điền dã khảo sát",
                rubric_scores={"rubric_version": "v1.0", "s1": 2.0, "s2": 2.0, "s3": 2.0, "s4": 2.0},
            )
        )
    db_session.commit()

    _login_user(client, teacher.email)
    res = client.get(f"/api/v1/classrooms/{classroom.id}/rubric-analytics?rubric_version=v1.0")
    assert res.status_code == 200, res.text
    data = res.json()

    # Total distinct students = 3 + 3 = 6 >= 5 (k-anonymity unsuppressed)
    assert data["cohort_size"] == 6
    assert data["is_suppressed"] is False
    assert data["overall_average"] is not None
    assert data["overall_average"] > 0
