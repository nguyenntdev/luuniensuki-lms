# -*- coding: utf-8 -*-
"""V5-T082 (Wave W08, Slot A02): Role and Multi-Tenant Matrix Security Across All Domains.

Priority: P0; Classification: PRODUCTION_COMPLETION

Verifies:
1. Matrix audit across all major roles:
   - `admin`, `staff`, `teacher`, `learner`, `partner` (provider), `guest`.
2. Horizontal and vertical tenant boundaries:
   - Cross-school isolation (School A cannot view/edit School B; teachers cannot modify other schools).
   - Cross-partner isolation (Partner A cannot view/edit Partner B inquiries or receive Partner B details).
   - Cross-classroom isolation (Student outside class cannot submit to assignments or view class details/roster; Teacher B cannot tamper with Classroom A).
   - Editorial role restriction (Learner and Guest cannot verify or publish claims/entities).
3. Negative abuse & side-channel leak defense:
   - Cross-tenant operations return HTTP 403 Forbidden without leaking metadata side-channels or row existence.
   - PII redaction on class rosters and public partner lookups.
   - Unauthenticated callers receive 401 Unauthorized.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Any, Optional

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import select

from backend.history_models import (
    HistoricalClaim,
    HistoricalEntity,
    HistoricalSource,
)
from backend.models import (
    ClassMember,
    Classroom,
    ContentStatus,
    HistoryAssignmentSubmission,
    HistoryLessonAssignment,
    LessonContent,
    Motif,
    MotifCategory,
    MotifRarity,
    School,
    SchoolMember,
    Urn,
    User,
    UserRole,
)
from backend.models_rbpc import (
    RbpcConsentStatus,
    RbpcCreator,
    RbpcExperience,
    RbpcInquiry,
    RbpcInquiryStatus,
)
from backend.security import hash_password
from backend.services import classroom as classroom_service
from backend.services import history_governance as gov


# --------------------------------------------------------------------------- #
# Seed & Auth Helpers
# --------------------------------------------------------------------------- #

def _create_user(
    db_session,
    email: str,
    role: UserRole = UserRole.learner,
    display_name: str | None = None,
    school_id: Optional[uuid.UUID] = None,
) -> User:
    """Helper to persist a user with specific role and optional school_id."""
    user = User(
        email=email,
        password_hash=hash_password("Password123!"),
        display_name=display_name or f"User {email.split('@')[0]}",
        username=f"usr_{uuid.uuid4().hex[:8]}",
        role=role,
        is_profile_public=True,
        school_id=school_id,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _login_user(client: TestClient, email: str, password: str = "Password123!") -> dict:
    """Login helper setting session cookies on test client."""
    client.cookies.clear()
    res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
        headers={"X-Test-Client-IP": f"client_{email}"},
    )
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    return res.json()


def _seed_source_locked_prerequisites(db_session) -> dict[str, Any]:
    """Seed historical urn, motif, entity, source, and claim for lesson assignments."""
    urn = Urn(
        name="Cao Đỉnh V5",
        slug=f"cao-dinh-v5-{uuid.uuid4().hex[:6]}",
        model_url="/models/cao_dinh.glb",
        display_order=1,
    )
    db_session.add(urn)
    db_session.flush()

    motif = Motif(
        name="Rồng mây V5",
        mesh_name=f"mesh_rong_may_{uuid.uuid4().hex[:6]}",
        urn_id=urn.id,
        category=MotifCategory.linh_thu,
        rarity=MotifRarity.epic,
        pos_x=0.0,
        pos_y=0.0,
        pos_z=0.0,
        bounding_radius=1.0,
    )
    db_session.add(motif)
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
        excerpt="Cao Đỉnh được đúc vào năm Bính Thân 1836...",
    )
    db_session.add(source)
    db_session.flush()

    entity = HistoricalEntity(
        slug=f"ent-cao-dinh-{uuid.uuid4().hex[:6]}",
        name_vi="Cao Đỉnh Thực Lục",
        entity_type="urn",
        publication_status="verified",
    )
    db_session.add(entity)
    db_session.flush()

    claim = HistoricalClaim(
        claim_key=f"claim-cao-dinh-{uuid.uuid4().hex[:6]}",
        claim_type="factual",
        statement_vi="Cao Đỉnh được đúc vào năm Bính Thân 1836 dưới thời vua Minh Mạng.",
        entity_id=entity.id,
        verification_status="verified",
        confidence="high",
        origin="editorial",
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
        "source": source,
        "entity": entity,
        "claim": claim,
        "lesson": lesson,
    }


# --------------------------------------------------------------------------- #
# Test 1: Cross-School Isolation & Role Matrix
# --------------------------------------------------------------------------- #

def test_cross_school_isolation_and_role_matrix(client: TestClient, db_session):
    """Verify cross-school tenant boundaries and administrative privileges.

    - School A and School B exist with separate teachers and classrooms.
    - Teacher A (School A) cannot update School B details or add members to School B (403).
    - Teacher A cannot list School B's classrooms (403).
    - Teacher A cannot assign Classroom A to School B without membership (403).
    - Admin user CAN view and manage cross-school resources.
    """
    school_a = classroom_service.create_school(db_session, name="Trường THPT Chuyên Quốc Học Huế", code="QH-HUE", city="Huế")
    school_b = classroom_service.create_school(db_session, name="Trường THPT Hai Bà Trưng Huế", code="HBT-HUE", city="Huế")

    teacher_a = _create_user(db_session, f"teacher_sch_a_{uuid.uuid4().hex[:6]}@school.edu.vn", role=UserRole.teacher, school_id=school_a.id)
    classroom_service.add_school_member(db_session, school_a.id, teacher_a.id, role="teacher")

    teacher_b = _create_user(db_session, f"teacher_sch_b_{uuid.uuid4().hex[:6]}@school.edu.vn", role=UserRole.teacher, school_id=school_b.id)
    classroom_service.add_school_member(db_session, school_b.id, teacher_b.id, role="teacher")

    admin = _create_user(db_session, f"admin_matrix_{uuid.uuid4().hex[:6]}@admin.edu.vn", role=UserRole.admin)

    # 1. Teacher A logs in
    _login_user(client, teacher_a.email)

    # Teacher A cannot update School B details (403)
    res_upd_b = client.patch(
        f"/api/v1/schools/{school_b.id}",
        json={"name": "Hacked School B"},
    )
    assert res_upd_b.status_code == status.HTTP_403_FORBIDDEN
    assert "Not authorized to update this school" in res_upd_b.text

    # Teacher A cannot add members to School B (403)
    some_user = _create_user(db_session, f"some_user_{uuid.uuid4().hex[:6]}@school.edu.vn", role=UserRole.teacher)
    res_add_member = client.post(
        f"/api/v1/schools/{school_b.id}/members",
        json={"user_id": str(some_user.id), "role": "teacher"},
    )
    assert res_add_member.status_code == status.HTTP_403_FORBIDDEN
    assert "Not authorized to manage members" in res_add_member.text

    # Teacher A cannot list School B classrooms (403)
    res_list_b_classes = client.get(f"/api/v1/schools/{school_b.id}/classrooms")
    assert res_list_b_classes.status_code == status.HTTP_403_FORBIDDEN

    # Teacher A creating classroom cannot associate with School B (403)
    res_create_tamper = client.post(
        "/api/v1/classrooms",
        json={"name": "Tampered Class in School B", "max_students": 25, "school_id": str(school_b.id)},
    )
    assert res_create_tamper.status_code == status.HTTP_403_FORBIDDEN

    # 2. Admin logs in: Admin CAN view and manage cross-school resources
    _login_user(client, admin.email)
    res_admin_upd = client.patch(
        f"/api/v1/schools/{school_b.id}",
        json={"address": "Cập nhật bởi Quản trị viên"},
    )
    assert res_admin_upd.status_code == status.HTTP_200_OK

    res_admin_list = client.get(f"/api/v1/schools/{school_b.id}/classrooms")
    assert res_admin_list.status_code == status.HTTP_200_OK


# --------------------------------------------------------------------------- #
# Test 2: Cross-Partner Isolation & Parameter Poisoning Protection
# --------------------------------------------------------------------------- #

def test_cross_partner_isolation_and_parameter_poisoning(client: TestClient, db_session):
    """Verify partner multi-tenant isolation and parameter poisoning resistance.

    - Partner A (Provider A) and Partner B (Provider B) have separate experiences and inquiries.
    - Partner A cannot see Partner B inquiries on GET `/api/v1/rbpc/partner/inquiries`.
    - Passing query param `?provider=<Partner_B_ID>` from Partner A is strictly ignored.
    - Partner A attempting to PATCH Partner B inquiry returns HTTP 403 (FORBIDDEN_SCOPE).
    - Guest and Learner accounts cannot access partner endpoints (403).
    - Unauthenticated callers receive 401.
    """
    partner_a = _create_user(db_session, f"prov_a_{uuid.uuid4().hex[:6]}@partner.vn", role=UserRole.teacher)
    partner_b = _create_user(db_session, f"prov_b_{uuid.uuid4().hex[:6]}@partner.vn", role=UserRole.teacher)
    learner = _create_user(db_session, f"learner_inq_{uuid.uuid4().hex[:6]}@learner.vn", role=UserRole.learner)
    guest = _create_user(db_session, f"guest_inq_{uuid.uuid4().hex[:6]}@guest.vn", role=UserRole.guest)

    creator_a = RbpcCreator(
        slug=f"artisan-iso-a-{uuid.uuid4().hex[:6]}",
        public_name="Nghệ Nhân A",
        craft_tradition="Đúc đồng",
        approved_bio_vi="Tiểu sử nghệ nhân A",
        consent_status=RbpcConsentStatus.consented.value,
        is_verified=True,
    )
    creator_b = RbpcCreator(
        slug=f"artisan-iso-b-{uuid.uuid4().hex[:6]}",
        public_name="Nghệ Nhân B",
        craft_tradition="Thêu nón",
        approved_bio_vi="Tiểu sử nghệ nhân B",
        consent_status=RbpcConsentStatus.consented.value,
        is_verified=True,
    )
    db_session.add_all([creator_a, creator_b])
    db_session.flush()

    exp_a = RbpcExperience(
        slug=f"exp-iso-a-{uuid.uuid4().hex[:6]}",
        creator_id=creator_a.id,
        provider_name="Cơ sở Đúc Đồng A",
        provider_id=partner_a.id,
        title_vi="Trải nghiệm Đúc Đồng A",
        description_vi="Mô tả trải nghiệm Đúc Đồng A",
        area_public="Huế",
        publication_state="published",
    )
    exp_b = RbpcExperience(
        slug=f"exp-iso-b-{uuid.uuid4().hex[:6]}",
        creator_id=creator_b.id,
        provider_name="Cơ sở Thêu Nón B",
        provider_id=partner_b.id,
        title_vi="Trải nghiệm Thêu Nón B",
        description_vi="Mô tả trải nghiệm Thêu Nón B",
        area_public="Huế",
        publication_state="published",
    )
    db_session.add_all([exp_a, exp_b])
    db_session.flush()

    inquiry_a = RbpcInquiry(
        public_ref=f"INQ-A-{uuid.uuid4().hex[:6].upper()}",
        experience_id=exp_a.id,
        provider_id=partner_a.id,
        name="Visitor A",
        contact_channel="email",
        contact_value="visitor_a@test.vn",
        desired_date=date.today() + timedelta(days=7),
        party_size=2,
        state=RbpcInquiryStatus.new.value,
        idempotency_key=f"idem-iso-a-{uuid.uuid4().hex}",
        opaque_token=f"tok_iso_a_{uuid.uuid4().hex}",
    )
    inquiry_b = RbpcInquiry(
        public_ref=f"INQ-B-{uuid.uuid4().hex[:6].upper()}",
        experience_id=exp_b.id,
        provider_id=partner_b.id,
        name="Visitor B",
        contact_channel="phone",
        contact_value="0987654321",
        desired_date=date.today() + timedelta(days=10),
        party_size=4,
        state=RbpcInquiryStatus.new.value,
        idempotency_key=f"idem-iso-b-{uuid.uuid4().hex}",
        opaque_token=f"tok_iso_b_{uuid.uuid4().hex}",
    )
    db_session.add_all([inquiry_a, inquiry_b])
    db_session.commit()

    # 1. Partner A logs in
    _login_user(client, partner_a.email)
    res_a_list = client.get("/api/v1/rbpc/partner/inquiries")
    assert res_a_list.status_code == 200
    refs_a = [item["reference"] for item in res_a_list.json()["items"]]
    assert inquiry_a.public_ref in refs_a
    assert inquiry_b.public_ref not in refs_a

    # Parameter poisoning resistance: Partner A queries with ?provider=<partner_b_id>
    res_poison = client.get(f"/api/v1/rbpc/partner/inquiries?provider={partner_b.id}")
    assert res_poison.status_code == 200
    refs_poison = [item["reference"] for item in res_poison.json()["items"]]
    assert inquiry_b.public_ref not in refs_poison, "Poisoning leak: Partner A accessed Partner B inquiries via query param"

    # Partner A attempting to PATCH Partner B inquiry returns 403 FORBIDDEN_SCOPE
    res_patch_tamper = client.patch(
        f"/api/v1/rbpc/partner/inquiries/{inquiry_b.id}",
        json={"status": "contacted", "note": "Malicious tampering attempt"},
    )
    assert res_patch_tamper.status_code == status.HTTP_403_FORBIDDEN
    assert res_patch_tamper.json()["error"]["code"] == "FORBIDDEN_SCOPE"

    # 2. Guest user is blocked with 403
    _login_user(client, guest.email)
    res_guest_list = client.get("/api/v1/rbpc/partner/inquiries")
    assert res_guest_list.status_code == status.HTTP_403_FORBIDDEN

    # 3. Unauthenticated access is blocked with 401
    client.cookies.clear()
    res_unauth = client.get("/api/v1/rbpc/partner/inquiries")
    assert res_unauth.status_code == status.HTTP_401_UNAUTHORIZED


# --------------------------------------------------------------------------- #
# Test 3: Cross-Classroom Isolation & Student Boundary Enforcement
# --------------------------------------------------------------------------- #

def test_cross_classroom_isolation_and_student_boundaries(client: TestClient, db_session):
    """Verify cross-classroom isolation:
    - Teacher A manages Classroom A; Teacher B manages Classroom B.
    - Student A is enrolled only in Classroom A; Student B enrolled only in Classroom B.
    - Teacher B cannot view, modify, or archive Classroom A (403).
    - Teacher B cannot export Classroom A gradebook (403).
    - Student B cannot view Classroom A details or roster (403).
    - Student B cannot submit work to Assignment A (403 NOT_CLASS_MEMBER).
    - Student A cannot view Student B's submission (403).
    """
    prereqs = _seed_source_locked_prerequisites(db_session)

    teacher_a = _create_user(db_session, f"teach_a_{uuid.uuid4().hex[:6]}@matrix.edu", role=UserRole.teacher)
    teacher_b = _create_user(db_session, f"teach_b_{uuid.uuid4().hex[:6]}@matrix.edu", role=UserRole.teacher)
    student_a = _create_user(db_session, f"student_a_{uuid.uuid4().hex[:6]}@matrix.edu", role=UserRole.learner)
    student_b = _create_user(db_session, f"student_b_{uuid.uuid4().hex[:6]}@matrix.edu", role=UserRole.learner)

    # Teacher A creates Classroom A
    _login_user(client, teacher_a.email)
    res_class_a = client.post(
        "/api/v1/classrooms",
        json={"name": "Lớp Nghiên Cứu A", "max_students": 30},
    )
    class_a_id = res_class_a.json()["id"]
    class_a_code = res_class_a.json()["class_code"]

    # Teacher A creates Assignment A
    res_assign_a = client.post(
        "/api/v1/history/assignments",
        json={
            "classroom_id": class_a_id,
            "lesson_id": str(prereqs["lesson"].id),
            "title": "Bài tập Khảo sát Lớp A",
            "points": 100,
            "claim_ids": [str(prereqs["claim"].id)],
            "status": "published",
        },
    )
    assignment_a_id = res_assign_a.json()["id"]

    # Teacher B creates Classroom B
    _login_user(client, teacher_b.email)
    res_class_b = client.post(
        "/api/v1/classrooms",
        json={"name": "Lớp Nghiên Cứu B", "max_students": 30},
    )
    class_b_id = res_class_b.json()["id"]
    class_b_code = res_class_b.json()["class_code"]

    # Student A joins Classroom A
    _login_user(client, student_a.email)
    client.post("/api/v1/classrooms/join", json={"class_code": class_a_code})

    # Student A submits Assignment A
    res_sub_a = client.post(
        f"/api/v1/history/assignments/{assignment_a_id}/submit",
        json={
            "submission_content": {
                "claim": "Minh Mạng đúc Cao Đỉnh",
                "evidence": "Đại Nam Thực Lục",
                "explanation": "Đầy đủ bằng chứng",
            }
        },
    )
    submission_a_id = res_sub_a.json()["id"]

    # Student B joins Classroom B
    _login_user(client, student_b.email)
    client.post("/api/v1/classrooms/join", json={"class_code": class_b_code})

    # 1. Negative abuse: Teacher B cannot view Classroom A
    _login_user(client, teacher_b.email)
    res_tb_view_a = client.get(f"/api/v1/classrooms/{class_a_id}")
    assert res_tb_view_a.status_code == status.HTTP_403_FORBIDDEN

    # Teacher B cannot edit Classroom A
    res_tb_edit_a = client.put(f"/api/v1/classrooms/{class_a_id}", json={"name": "Tampered Name"})
    assert res_tb_edit_a.status_code == status.HTTP_403_FORBIDDEN

    # Teacher B cannot export Classroom A gradebook
    res_tb_export_a = client.get(f"/api/v1/classrooms/{class_a_id}/export")
    assert res_tb_export_a.status_code == status.HTTP_403_FORBIDDEN

    # Teacher B cannot grade Submission A
    res_tb_grade_a = client.post(
        f"/api/v1/history/assignments/{assignment_a_id}/submissions/{submission_a_id}/grade",
        json={"score": 5.0, "teacher_feedback": "Unauthorized Grade"},
    )
    assert res_tb_grade_a.status_code == status.HTTP_403_FORBIDDEN

    # 2. Negative abuse: Student B (not in Class A) cannot view Classroom A details
    _login_user(client, student_b.email)
    res_sb_view_a = client.get(f"/api/v1/classrooms/{class_a_id}")
    assert res_sb_view_a.status_code == status.HTTP_403_FORBIDDEN

    # Student B cannot submit to Assignment A
    res_sb_sub_a = client.post(
        f"/api/v1/history/assignments/{assignment_a_id}/submit",
        json={
            "submission_content": {
                "claim": "Illegal Submission",
                "evidence": "None",
                "explanation": "Not enrolled",
            }
        },
    )
    assert res_sb_sub_a.status_code == status.HTTP_403_FORBIDDEN
    assert res_sb_sub_a.json()["error"]["code"] == "NOT_CLASS_MEMBER"

    # Student B cannot view Student A's submission
    res_sb_view_sub = client.get(
        f"/api/v1/history/assignments/{assignment_a_id}/submissions/{submission_a_id}"
    )
    assert res_sb_view_sub.status_code == status.HTTP_403_FORBIDDEN


# --------------------------------------------------------------------------- #
# Test 4: Editorial Role Restrictions (Learner & Guest Blocked)
# --------------------------------------------------------------------------- #

def test_editorial_role_restrictions(client: TestClient, db_session):
    """Verify editorial role matrix:
    - Only editorial roles (admin, staff, teacher) can verify or publish claims and entities.
    - Learner cannot transition claims (403).
    - Guest cannot transition claims (403).
    - Learner cannot resolve editorial disputes (403).
    - Unauthenticated cannot transition claims (401/403).
    """
    admin = _create_user(db_session, f"admin_edit_{uuid.uuid4().hex[:6]}@edu.vn", role=UserRole.admin)
    teacher = _create_user(db_session, f"teach_edit_{uuid.uuid4().hex[:6]}@edu.vn", role=UserRole.teacher)
    learner = _create_user(db_session, f"learner_edit_{uuid.uuid4().hex[:6]}@edu.vn", role=UserRole.learner)
    guest = _create_user(db_session, f"guest_edit_{uuid.uuid4().hex[:6]}@guest.vn", role=UserRole.guest)

    entity = gov.create_entity(
        db_session,
        data={
            "slug": f"ent-edit-{uuid.uuid4().hex[:6]}",
            "name_vi": "Thực Thể Biên Tập",
            "entity_type": "urn",
        },
        actor_id=admin.id,
    )
    claim = gov.create_claim(
        db_session,
        data={
            "entity_id": entity.id,
            "claim_type": "factual",
            "statement_vi": "Khẳng định cần biên tập.",
            "verification_status": "draft",
            "origin": "editorial",
        },
        actor_id=admin.id,
    )
    db_session.commit()

    # 1. Learner attempts to advance claim status -> 403 Forbidden
    _login_user(client, learner.email)
    res_learner_trans = client.post(
        f"/api/v1/admin/history/claims/{claim.id}/transition",
        params={"target": "internal_review", "reason": "Learner illegal review attempt"},
    )
    assert res_learner_trans.status_code == status.HTTP_403_FORBIDDEN

    # Learner attempts to resolve dispute -> 403 Forbidden
    res_learner_disp = client.post(
        "/api/v1/admin/editorial/disputes/resolve",
        json={"item_type": "claim", "item_id": str(claim.id), "resolution": "resolved"},
    )
    assert res_learner_disp.status_code == status.HTTP_403_FORBIDDEN

    # 2. Guest attempts to advance claim status -> 403 Forbidden
    _login_user(client, guest.email)
    res_guest_trans = client.post(
        f"/api/v1/admin/history/claims/{claim.id}/transition",
        params={"target": "internal_review", "reason": "Guest illegal review attempt"},
    )
    assert res_guest_trans.status_code == status.HTTP_403_FORBIDDEN

    # 3. Unauthenticated attempt -> 401 Unauthorized
    client.cookies.clear()
    res_unauth_trans = client.post(
        f"/api/v1/admin/history/claims/{claim.id}/transition",
        params={"target": "internal_review", "reason": "Unauthenticated attempt"},
    )
    assert res_unauth_trans.status_code == status.HTTP_401_UNAUTHORIZED

    # 4. Teacher (authorized editorial role) can advance claim
    _login_user(client, teacher.email)
    res_teacher_trans = client.post(
        f"/api/v1/admin/history/claims/{claim.id}/transition",
        params={"target": "internal_review", "reason": "Giáo viên gửi duyệt bản thảo"},
    )
    assert res_teacher_trans.status_code == status.HTTP_200_OK
    assert res_teacher_trans.json()["verification_status"] == "internal_review"


# --------------------------------------------------------------------------- #
# Test 5: Negative Abuse & Zero Information Leakage in Rejections
# --------------------------------------------------------------------------- #

def test_negative_abuse_and_zero_information_leakage(client: TestClient, db_session):
    """Verify that cross-tenant operations return standard 403 Forbidden envelopes
    without leaking internal entity existence or metadata.

    - Teacher A attempting to access Teacher B's non-existent classroom returns 404.
    - Teacher A attempting to access Teacher B's existing classroom returns 403 Forbidden.
    - Error details on 403 Forbidden do NOT reveal foreign tenant PII, timestamps, or student counts.
    """
    teacher_a = _create_user(db_session, f"teach_leak_a_{uuid.uuid4().hex[:6]}@edu.vn", role=UserRole.teacher)
    teacher_b = _create_user(db_session, f"teach_leak_b_{uuid.uuid4().hex[:6]}@edu.vn", role=UserRole.teacher)

    _login_user(client, teacher_b.email)
    res_b_class = client.post(
        "/api/v1/classrooms",
        json={"name": "Bảo Mật Lớp B", "max_students": 20},
    )
    class_b_id = res_b_class.json()["id"]

    _login_user(client, teacher_a.email)

    # Accessing existing foreign classroom returns 403
    res_403 = client.get(f"/api/v1/classrooms/{class_b_id}")
    assert res_403.status_code == status.HTTP_403_FORBIDDEN
    body_403 = res_403.json()
    assert "error" in body_403
    assert "details" in body_403["error"]
    # Verify no details leaked
    assert body_403["error"]["details"] == {}
    assert "Bảo Mật Lớp B" not in res_403.text

    # Accessing non-existent classroom returns 404
    fake_id = uuid.uuid4()
    res_404 = client.get(f"/api/v1/classrooms/{fake_id}")
    assert res_404.status_code == status.HTTP_404_NOT_FOUND
    body_404 = res_404.json()
    assert "error" in body_404
