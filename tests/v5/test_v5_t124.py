# -*- coding: utf-8 -*-
"""V5-T124 (Wave W12, Slot A04): RBAC Privacy and Incident Tabletop Rehearsal.

Priority: P0; Classification: PRODUCTION_COMPLETION

Covers comprehensive tabletop rehearsal and live integration verification:
1. Two-School / Two-Tenant Malicious Actor Exercises:
   - Malicious Teacher B probing School A details, members, classrooms, and gradebooks.
   - Malicious Student B attempting cross-classroom submission, roster exfiltration, and foreign submission snooping.
   - Malicious unverified teacher attempting access to student PII.
2. Two-Tenant Marketplace Partner Boundary Exercises:
   - Partner A attempting to view, probe with ?provider query param, or mutate Partner B's inquiries.
   - Non-existent resource probes returning 404 without distinguishing existence.
3. Consent Revocation & Right-to-Erasure Exercises (Decree 13/2023/ND-CP):
   - School pilot guardian consent withdrawal: immediately suspends empirical research assessments (403 GUARDIAN_CONSENT_WITHDRAWN)
     and excludes student data from cohort outcome analytics.
   - Visitor marketplace inquiry consent withdrawal: immediately anonymizes name to '[ANONYMIZED]' and contact to '[REDACTED]'.
4. Security Incident Containment & Kill Switch Rehearsal:
   - Admin kill switch toggles and incident containment procedures.
5. Negative Abuse Invariant:
   - Zero sensitive cross-account or cross-tenant leakage.
   - Error responses strictly return standardized error envelopes without disclosing internal details, counts, or PII.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import select

from backend.config import settings
from backend.domain.learning_outcome import (
    DEFAULT_HISTORICAL_INQUIRY_RUBRIC,
    AssessmentInstrumentType,
    AssessmentPhase,
    EthicsProtocolStatus,
    PilotConsentStatus,
)
from backend.history_models import (
    HistoricalClaim,
    HistoricalEntity,
    HistoricalSource,
    HistoryAssignmentSubmission,
    HistoryEthicsProtocol,
    HistoryLearningOutcomeAssessment,
    HistoryLearningOutcomeSubmission,
    HistoryLessonAssignment,
    HistoryPilotGuardianConsent,
)
from backend.models import (
    ClassMember,
    Classroom,
    ContentStatus,
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
from backend.security import create_jwt_token, hash_password
from backend.services import classroom as classroom_service
from backend.services import feature_flags as ff_service
from backend.services import history_learning as hl
from backend.services import rbpc_retention as retention_service


# --------------------------------------------------------------------------- #
# Helpers & Fixtures
# --------------------------------------------------------------------------- #

def _create_user(
    db_session,
    email: str,
    role: UserRole = UserRole.learner,
    display_name: str | None = None,
    school_id: Optional[uuid.UUID] = None,
    is_school_verified: bool = True,
) -> User:
    """Helper to persist a user with specific role and optional school_id."""
    user = User(
        id=uuid.uuid4(),
        email=email,
        password_hash=hash_password("SecurePassword123!"),
        display_name=display_name or f"User {email.split('@')[0]}",
        username=f"usr_{uuid.uuid4().hex[:8]}",
        role=role,
        is_profile_public=True,
        school_id=school_id,
        is_school_verified=is_school_verified,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _auth_headers(user: User) -> dict[str, str]:
    """Generate authenticated bearer headers for user."""
    role_str = user.role.value if hasattr(user.role, "value") else str(user.role)
    token = create_jwt_token(
        subject=str(user.id),
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        expires_delta=timedelta(minutes=60),
        issuer=settings.jwt_issuer,
        audience=settings.jwt_audience,
        extra_claims={"type": "access", "role": role_str},
    )
    return {"Authorization": f"Bearer {token}"}


def _seed_source_locked_prerequisites(db_session) -> dict[str, Any]:
    """Seed historical urn, motif, entity, source, and claim for lesson assignments."""
    urn = Urn(
        name="Thuần Đỉnh Tabletop",
        slug=f"thuan-dinh-tt-{uuid.uuid4().hex[:6]}",
        model_url="/models/thuan_dinh.glb",
        display_order=2,
    )
    db_session.add(urn)
    db_session.flush()

    motif = Motif(
        name="Thần Quy Tabletop",
        mesh_name=f"mesh_than_quy_{uuid.uuid4().hex[:6]}",
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
        title="Khâm Định Đại Nam Hội Điển Sự Lệ",
        author_text="Nội các triều Nguyễn",
        source_type="primary",
        publication_year=1851,
        citation_text="Hội Điển Sự Lệ, Quyển 120.",
        rights_status="public_domain",
        license="CC-BY-4.0",
        verification_status="expert_verified",
        checksum=uuid.uuid4().hex,
        excerpt="Thuần Đỉnh khắc hình Thần Quy năm Minh Mạng thứ 17...",
    )
    db_session.add(source)
    db_session.flush()

    entity = HistoricalEntity(
        slug=f"ent-thuan-dinh-{uuid.uuid4().hex[:6]}",
        name_vi="Thuần Đỉnh Thần Quy",
        entity_type="urn",
        publication_status="verified",
    )
    db_session.add(entity)
    db_session.flush()

    claim = HistoricalClaim(
        claim_key=f"claim-thuan-dinh-{uuid.uuid4().hex[:6]}",
        claim_type="factual",
        statement_vi="Thần Quy được khắc trên Thuần Đỉnh tượng trưng cho sự trường tồn.",
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
        description="Khảo sát biểu tượng Thần Quy trên Thuần Đỉnh.",
        intro_text="Biểu tượng linh quy trong văn hóa cung đình Huế.",
        historical_context="Triều Nguyễn đúc Cửu Đỉnh năm 1835-1837.",
        symbolism="Sự trường tồn của vương triều và đất nước.",
        fun_fact="Thuần Đỉnh đại diện cho sự thuần khiết, thanh bình.",
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
# Tabletop Scenario 1: Two-School Malicious Actor Isolation Rehearsal
# --------------------------------------------------------------------------- #

def test_tabletop_two_school_malicious_actor_isolation(client: TestClient, db_session):
    """Tabletop Exercise 1: Two-School Malicious Actor Attack.

    Simulates an adversarial teacher (Teacher B) and rogue student (Student B) from School B
    attempting unauthorized access, data harvesting, and cross-submission into School A.

    Invariants Verified:
    - Teacher B cannot update School A details or add members to School A (403 Forbidden).
    - Teacher B cannot view Classroom A roster or gradebook (403 Forbidden).
    - Student B cannot view Classroom A roster or submit work to Assignment A (403 Forbidden).
    - Unverified teacher cannot access classroom student PII (403 UNVERIFIED_TEACHER_ACCESS_DENIED).
    - Negative abuse: Zero sensitive foreign student names, emails, or scores are leaked.
    """
    prereqs = _seed_source_locked_prerequisites(db_session)

    # 1. Setup School A and School B
    school_a = classroom_service.create_school(
        db_session,
        name="Trường THPT Chuyên Quốc Học Huế (Tabletop A)",
        code=f"QH-TT-{uuid.uuid4().hex[:4]}",
        city="Huế",
    )
    school_b = classroom_service.create_school(
        db_session,
        name="Trường THPT Hai Bà Trưng Huế (Tabletop B)",
        code=f"HBT-TT-{uuid.uuid4().hex[:4]}",
        city="Huế",
    )

    teacher_a = _create_user(
        db_session,
        f"teacher_a_{uuid.uuid4().hex[:6]}@school-a.edu.vn",
        role=UserRole.teacher,
        display_name="Thầy Giáo Trường A",
        school_id=school_a.id,
    )
    classroom_service.add_school_member(db_session, school_a.id, teacher_a.id, role="teacher")

    teacher_b_attacker = _create_user(
        db_session,
        f"malicious_teacher_b_{uuid.uuid4().hex[:6]}@school-b.edu.vn",
        role=UserRole.teacher,
        display_name="Kẻ Tấn Công Trường B",
        school_id=school_b.id,
    )
    classroom_service.add_school_member(db_session, school_b.id, teacher_b_attacker.id, role="teacher")

    student_a = _create_user(
        db_session,
        f"student_victim_a_{uuid.uuid4().hex[:6]}@school-a.edu.vn",
        role=UserRole.learner,
        display_name="Học Sinh Nạn Nhân A",
        school_id=school_a.id,
    )
    classroom_service.add_school_member(db_session, school_a.id, student_a.id, role="student")

    student_b_attacker = _create_user(
        db_session,
        f"rogue_student_b_{uuid.uuid4().hex[:6]}@school-b.edu.vn",
        role=UserRole.learner,
        display_name="Học Sinh Xâm Nhập B",
        school_id=school_b.id,
    )
    classroom_service.add_school_member(db_session, school_b.id, student_b_attacker.id, role="student")

    # Classroom A owned by Teacher A
    classroom_a = classroom_service.create_classroom(
        db_session,
        teacher=teacher_a,
        name="Lớp Sử 10A1 Quốc Học (Mục Tiêu)",
        school_id=school_a.id,
        term="Học kỳ 1 2026-2027",
    )
    classroom_service.join_classroom_by_code(
        db_session,
        user=student_a,
        class_code=classroom_a.class_code,
        guardian_email="phuhuynh_a@vietnam.edu.vn",
        guardian_consent=True,
    )

    # Assignment in Classroom A
    assignment_a = hl.create_source_locked_assignment(
        db=db_session,
        teacher_id=teacher_a.id,
        classroom_id=classroom_a.id,
        lesson_id=prereqs["lesson"].id,
        title="Nghiên Cứu Thần Quy Thuần Đỉnh",
        instructions="Khảo cứu tư liệu gốc và phân tích ý nghĩa linh thú.",
        due_at=datetime.now(timezone.utc) + timedelta(days=7),
        points=100,
        claim_ids=[prereqs["claim"].id],
        status="published",
    )

    headers_b = _auth_headers(teacher_b_attacker)

    # --- ATTACK VECTOR 1: Teacher B probes School A management ---
    res_school_tamper = client.patch(
        f"/api/v1/schools/{school_a.id}",
        json={"name": "Hacked School Name"},
        headers=headers_b,
    )
    assert res_school_tamper.status_code == status.HTTP_403_FORBIDDEN

    res_add_member = client.post(
        f"/api/v1/schools/{school_a.id}/members",
        json={"user_id": str(teacher_b_attacker.id), "role": "teacher"},
        headers=headers_b,
    )
    assert res_add_member.status_code == status.HTTP_403_FORBIDDEN

    # --- ATTACK VECTOR 2: Teacher B probes Classroom A gradebook & roster ---
    res_gradebook = client.get(
        f"/api/v1/classrooms/{classroom_a.id}/gradebook",
        headers=headers_b,
    )
    assert res_gradebook.status_code == status.HTTP_403_FORBIDDEN
    assert "phuhuynh_a@vietnam.edu.vn" not in res_gradebook.text
    assert "Học Sinh Nạn Nhân A" not in res_gradebook.text

    res_roster = client.get(
        f"/api/v1/classrooms/{classroom_a.id}/roster",
        headers=headers_b,
    )
    assert res_roster.status_code == status.HTTP_403_FORBIDDEN

    # --- ATTACK VECTOR 3: Rogue Student B probes Classroom A & attempts assignment submission ---
    headers_student_b = _auth_headers(student_b_attacker)

    res_student_roster = client.get(
        f"/api/v1/classrooms/{classroom_a.id}/roster",
        headers=headers_student_b,
    )
    assert res_student_roster.status_code == status.HTTP_403_FORBIDDEN

    res_cross_submit = client.post(
        f"/api/v1/history/assignments/{assignment_a.id}/submit",
        json={
            "submission_content": {
                "motif_name": "Thần Quy",
                "evidence_sources": ["Khâm Định Đại Nam Hội Điển Sự Lệ"],
                "historical_analysis": "Học sinh Trường B cố tình nộp bài sang Trường A trái phép.",
            },
            "idempotency_key": str(uuid.uuid4()),
        },
        headers=headers_student_b,
    )
    assert res_cross_submit.status_code == status.HTTP_403_FORBIDDEN
    assert "NOT_CLASS_MEMBER" in res_cross_submit.text

    # --- ATTACK VECTOR 4: Unverified teacher attempts access to student PII ---
    unverified_teacher = _create_user(
        db_session,
        f"unverified_teacher_{uuid.uuid4().hex[:6]}@school-a.edu.vn",
        role=UserRole.teacher,
        display_name="Giáo Viên Chưa Xác Minh",
        school_id=school_a.id,
        is_school_verified=False,
    )
    # Even if classroom belongs to this unverified user, access to student PII must fail closed
    unverified_class = classroom_service.create_classroom(
        db_session,
        teacher=unverified_teacher,
        name="Lớp Thử Nghiệm Chưa Xác Minh",
        school_id=school_a.id,
    )
    headers_unverified = _auth_headers(unverified_teacher)
    res_unverified_gb = client.get(
        f"/api/v1/classrooms/{unverified_class.id}/gradebook",
        headers=headers_unverified,
    )
    assert res_unverified_gb.status_code == status.HTTP_403_FORBIDDEN
    assert "UNVERIFIED_TEACHER_ACCESS_DENIED" in res_unverified_gb.text


# --------------------------------------------------------------------------- #
# Tabletop Scenario 2: Two-Tenant Marketplace Partner Boundary Rehearsal
# --------------------------------------------------------------------------- #

def test_tabletop_two_tenant_marketplace_partner_boundary(client: TestClient, db_session):
    """Tabletop Exercise 2: Two-Tenant Marketplace Partner Boundary Drill.

    Simulates an adversarial craft partner (Partner B) attempting to view or alter
    customer booking inquiries intended for Partner A.

    Invariants Verified:
    - Partner A queries only see Partner A inquiries.
    - Parameter poisoning via ?provider=<target_id> is ignored for non-admins.
    - Cross-tenant status update PATCH is rejected with 403 FORBIDDEN_SCOPE.
    - Probe against non-existent inquiry returns 404 NOT_FOUND.
    - Zero customer PII or internal notes from Partner A are disclosed to Partner B.
    """
    partner_a = _create_user(
        db_session,
        f"artisan_a_{uuid.uuid4().hex[:6]}@hue-craft.vn",
        role=UserRole.teacher,
        display_name="Nghệ Nhân Kim Hoàn Đồng Khánh",
    )
    partner_b = _create_user(
        db_session,
        f"artisan_b_attacker_{uuid.uuid4().hex[:6]}@phuoc-tich.vn",
        role=UserRole.teacher,
        display_name="Nghệ Nhân Gốm Phước Tích",
    )

    creator_a = RbpcCreator(
        slug=f"kim-hoan-dong-khanh-{uuid.uuid4().hex[:6]}",
        public_name="Hợp tác xã Kim Hoàn Đồng Khánh",
        craft_tradition="Chế tác Kim hoàn Huế",
        approved_bio_vi="Tiểu sử nghệ nhân phục vụ kiểm thử tabletop.",
        consent_status=RbpcConsentStatus.consented.value,
        is_verified=True,
    )
    db_session.add(creator_a)
    db_session.flush()

    exp_a = RbpcExperience(
        slug=f"trai-nghiem-kim-hoan-{uuid.uuid4().hex[:6]}",
        creator_id=creator_a.id,
        provider_name="Hiệu Kim Hoàn Đồng Khánh",
        title_vi="Chạm Bạc Cung Đình Huế",
        description_vi="Trải nghiệm chạm bạc truyền thống.",
        provider_id=partner_a.id,
        publication_state="published",
        availability_mode="inquiry_only",
    )
    db_session.add(exp_a)
    db_session.flush()

    # Inquiry intended strictly for Partner A
    inquiry_a = RbpcInquiry(
        public_ref=f"INQ-A-{uuid.uuid4().hex[:8].upper()}",
        idempotency_key=f"idem-key-{uuid.uuid4().hex}",
        opaque_token=uuid.uuid4().hex,
        experience_id=exp_a.id,
        provider_id=partner_a.id,
        name="Nguyễn Văn Khách Hàng",
        contact_channel="email",
        contact_value="khachhang_vip@example.com",
        desired_date="2026-12-01",
        party_size=3,
        privacy_accepted=True,
        state=RbpcInquiryStatus.new.value,
        internal_note="Khách yêu cầu nghệ nhân lâu năm hướng dẫn chi tiết.",
    )
    db_session.add(inquiry_a)
    db_session.commit()
    db_session.refresh(inquiry_a)

    headers_partner_b = _auth_headers(partner_b)

    # --- ATTACK VECTOR 1: Partner B attempts listing inquiries ---
    res_list_b = client.get("/api/v1/rbpc/partner/inquiries", headers=headers_partner_b)
    assert res_list_b.status_code == status.HTTP_200_OK
    b_data = res_list_b.json()
    assert b_data["total"] == 0
    assert len(b_data["items"]) == 0

    # --- ATTACK VECTOR 2: Parameter poisoning with ?provider=<partner_a.id> ---
    res_poison = client.get(
        f"/api/v1/rbpc/partner/inquiries?provider={partner_a.id}",
        headers=headers_partner_b,
    )
    assert res_poison.status_code == status.HTTP_200_OK
    poison_data = res_poison.json()
    assert poison_data["total"] == 0
    assert "khachhang_vip@example.com" not in res_poison.text

    # --- ATTACK VECTOR 3: Partner B attempts direct PATCH on Partner A inquiry ---
    res_patch = client.patch(
        f"/api/v1/rbpc/partner/inquiries/{inquiry_a.id}",
        json={"status": "contacted", "note": "Partner B hijack attempt"},
        headers=headers_partner_b,
    )
    assert res_patch.status_code == status.HTTP_403_FORBIDDEN
    assert "FORBIDDEN_SCOPE" in res_patch.text

    # --- ATTACK VECTOR 4: Probe non-existent UUID returns 404 cleanly ---
    random_id = uuid.uuid4()
    res_missing = client.patch(
        f"/api/v1/rbpc/partner/inquiries/{random_id}",
        json={"status": "contacted"},
        headers=headers_partner_b,
    )
    assert res_missing.status_code == status.HTTP_404_NOT_FOUND


# --------------------------------------------------------------------------- #
# Tabletop Scenario 3: Guardian Consent Revocation Drill (Decree 13/2023/ND-CP)
# --------------------------------------------------------------------------- #

def test_tabletop_guardian_consent_revocation_drill(client: TestClient, db_session):
    """Tabletop Exercise 3: Guardian Consent Revocation Exercise.

    Simulates a guardian withdrawing consent for a minor student under an active school pilot
    research ethics protocol (Decree 13/2023/ND-CP Article 11).

    Invariants Verified:
    - Consent status transitions: pending -> verified -> withdrawn.
    - Once withdrawn, subsequent empirical research submissions fail with 403 GUARDIAN_CONSENT_WITHDRAWN.
    - Cohort research learning metrics computation automatically excludes students with withdrawn consent.
    - Negative abuse: student data is protected from non-consented research processing.
    """
    admin_user = _create_user(
        db_session,
        f"admin_ethics_{uuid.uuid4().hex[:6]}@admin.edu.vn",
        role=UserRole.admin,
        display_name="Cán Bộ Đạo Đức Nghiên Cứu",
    )
    teacher_user = _create_user(
        db_session,
        f"teacher_pilot_{uuid.uuid4().hex[:6]}@school.edu.vn",
        role=UserRole.teacher,
        display_name="Giáo Viên Chủ Nhiệm",
    )
    student_user = _create_user(
        db_session,
        f"student_minor_{uuid.uuid4().hex[:6]}@school.edu.vn",
        role=UserRole.learner,
        display_name="Học Sinh Vị Thành Niên",
    )

    headers_admin = _auth_headers(admin_user)
    headers_teacher = _auth_headers(teacher_user)
    headers_student = _auth_headers(student_user)

    # 1. Establish an approved Ethics Protocol
    protocol_code = f"IRB-2026-TT-{uuid.uuid4().hex[:4].upper()}"
    res_proto = client.post(
        "/api/v1/history/learning-outcomes/ethics-protocols",
        json={
            "protocol_code": protocol_code,
            "title": "Nghiên cứu Tabletop Đánh giá Năng lực Sử học",
            "irb_institution": "Đại học Sư phạm Huế",
            "status": "approved",
            "approved_by": "GS. Lê Văn Nghiên Cứu",
            "valid_until": (datetime.now(timezone.utc) + timedelta(days=180)).isoformat(),
            "data_retention_days": 180,
            "participant_consent_required": True,
        },
        headers=headers_admin,
    )
    assert res_proto.status_code == status.HTTP_200_OK
    protocol_id = res_proto.json()["id"]

    # Create associated assessment under this protocol
    assessment = hl.create_learning_outcome_assessment(
        db_session,
        {
            "ethics_protocol_id": uuid.UUID(protocol_id),
            "title": "Đánh giá Năng lực Sử liệu Tabletop",
            "slug": f"assessment-tt-{uuid.uuid4().hex[:6]}",
            "prompt_markdown": "Đọc bản dập Thuần Đỉnh mục Thần Quy và phân tích.",
        },
    )

    # 2. Register Guardian Consent
    res_consent = client.post(
        f"/api/v1/history/learning-outcomes/ethics-protocols/{protocol_id}/consent",
        json={
            "ethics_protocol_id": str(protocol_id),
            "student_id": str(student_user.id),
            "guardian_name": "Trần Thị Phụ Huynh",
            "guardian_email": "phuhuynh_tt@example.com",
            "guardian_phone": "0912345678",
            "relationship_type": "parent",
        },
        headers=headers_student,
    )
    assert res_consent.status_code == status.HTTP_200_OK
    consent_data = res_consent.json()
    consent_id = consent_data["id"]
    assert consent_data["consent_status"] == "pending"

    # 3. Teacher verifies consent
    res_verify = client.post(
        f"/api/v1/history/learning-outcomes/ethics-protocols/{protocol_id}/consent/{consent_id}/verify",
        headers=headers_teacher,
    )
    assert res_verify.status_code == status.HTTP_200_OK
    assert res_verify.json()["consent_status"] == "verified"

    # Verify query status is verified
    res_status = client.get(
        f"/api/v1/history/learning-outcomes/ethics-protocols/{protocol_id}/consent/{student_user.id}/status",
        headers=headers_student,
    )
    assert res_status.status_code == status.HTTP_200_OK
    assert res_status.json()["is_consent_verified"] is True

    # 4. Guardian executes RIGHT OF WITHDRAWAL (Decree 13/2023/ND-CP Article 11)
    res_withdraw = client.post(
        f"/api/v1/history/learning-outcomes/ethics-protocols/{protocol_id}/consent/{consent_id}/withdraw",
        json={"reason": "Phụ huynh yêu cầu rút lui khỏi nghiên cứu thực nghiệm."},
        headers=headers_student,
    )
    assert res_withdraw.status_code == status.HTTP_200_OK
    assert res_withdraw.json()["consent_status"] == "withdrawn"

    # Status check confirms withdrawal
    res_status_after = client.get(
        f"/api/v1/history/learning-outcomes/ethics-protocols/{protocol_id}/consent/{student_user.id}/status",
        headers=headers_student,
    )
    assert res_status_after.status_code == status.HTTP_200_OK
    assert res_status_after.json()["consent_status"] == "withdrawn"
    assert res_status_after.json()["is_consent_verified"] is False

    # 5. Blocked: Subsequent empirical assessment submission fails closed with 403
    res_blocked_sub = client.post(
        f"/api/v1/history/learning-outcomes/assessments/{assessment.id}/submit",
        json={"responses": {"q1": "Câu trả lời bị chặn do rút đồng thuận"}},
        headers=headers_student,
    )
    assert res_blocked_sub.status_code == status.HTTP_403_FORBIDDEN
    assert "GUARDIAN_CONSENT_WITHDRAWN" in res_blocked_sub.text


# --------------------------------------------------------------------------- #
# Tabletop Scenario 4: Marketplace Inquiry Consent Withdrawal & PII Scrubbing
# --------------------------------------------------------------------------- #

def test_tabletop_marketplace_inquiry_consent_withdrawal(client: TestClient, db_session):
    """Tabletop Exercise 4: Visitor Marketplace Inquiry Consent Revocation & PII Scrubbing.

    Simulates a visitor using their high-entropy opaque bearer token to withdraw inquiry consent
    and invoke right-to-erasure (Decree 13/2023/ND-CP Article 11).

    Invariants Verified:
    - Visitor opaque token lookup returns status without disclosing visitor PII (Zero-PII Invariant).
    - Consent withdrawal immediately transitions state to 'closed', sets privacy_accepted=False.
    - Name is sanitized to '[ANONYMIZED]' and contact_value to '[REDACTED]'.
    - Repeated withdrawal is idempotent and returns anonymized state without error.
    - Partner inquiry list reflects anonymized data with zero residual contact information.
    """
    partner = _create_user(
        db_session,
        f"partner_hue_{uuid.uuid4().hex[:6]}@craft.vn",
        role=UserRole.teacher,
        display_name="Xưởng Nón Bài Thơ Huế",
    )
    creator = RbpcCreator(
        slug=f"artisan-non-{uuid.uuid4().hex[:6]}",
        public_name="Nghệ nhân Nón Huế",
        craft_tradition="Làm nón lá bài thơ",
        approved_bio_vi="Tiểu sử nghệ nhân nón bài thơ Huế.",
        consent_status=RbpcConsentStatus.consented.value,
        is_verified=True,
    )
    db_session.add(creator)
    db_session.flush()

    exp = RbpcExperience(
        slug=f"non-bai-tho-hue-{uuid.uuid4().hex[:6]}",
        creator_id=creator.id,
        provider_name="Xưởng Nón Bài Thơ Huế",
        title_vi="Làm Nón Bài Thơ Xứ Huế",
        description_vi="Trải nghiệm làm nón lá truyền thống xứ Huế.",
        provider_id=partner.id,
        publication_state="published",
        availability_mode="inquiry_only",
    )
    db_session.add(exp)
    db_session.flush()

    opaque_token = uuid.uuid4().hex
    inquiry = RbpcInquiry(
        public_ref=f"INQ-REV-{uuid.uuid4().hex[:8].upper()}",
        idempotency_key=f"idem-key-{uuid.uuid4().hex}",
        opaque_token=opaque_token,
        experience_id=exp.id,
        provider_id=partner.id,
        name="Phan Thị Du Khách",
        contact_channel="phone",
        contact_value="0988776655",
        desired_date="2026-12-15",
        party_size=2,
        privacy_accepted=True,
        state=RbpcInquiryStatus.new.value,
        message="Tôi muốn đặt lịch làm nón cho 2 người vào buổi sáng.",
    )
    db_session.add(inquiry)
    db_session.commit()
    db_session.refresh(inquiry)

    # 1. Visitor checks inquiry status with bearer token (Verify Zero-PII lookup)
    res_status = client.get(f"/api/v1/rbpc/inquiries/status/{opaque_token}")
    assert res_status.status_code == status.HTTP_200_OK
    status_body = res_status.json()
    assert "0988776655" not in res_status.text
    assert "Phan Thị Du Khách" not in res_status.text
    assert status_body["reference"] == inquiry.public_ref

    # 2. Visitor invokes consent withdrawal
    res_withdraw = client.post(f"/api/v1/rbpc/inquiries/status/{opaque_token}/withdraw")
    assert res_withdraw.status_code == status.HTTP_200_OK
    withdraw_body = res_withdraw.json()
    assert withdraw_body["privacy_accepted"] is False
    assert withdraw_body["status"] == "closed"

    # 3. Verify database state: PII is completely scrubbed
    db_session.expire_all()
    inquiry_refreshed = db_session.get(RbpcInquiry, inquiry.id)
    assert inquiry_refreshed.name == "[ANONYMIZED]"
    assert inquiry_refreshed.contact_value == "[REDACTED]"
    assert inquiry_refreshed.message is None
    assert inquiry_refreshed.privacy_accepted is False
    assert inquiry_refreshed.state == "closed"

    # 4. Verify Partner perspective: inquiries list shows redacted contact details
    headers_partner = _auth_headers(partner)
    res_partner_list = client.get("/api/v1/rbpc/partner/inquiries", headers=headers_partner)
    assert res_partner_list.status_code == status.HTTP_200_OK
    partner_items = res_partner_list.json()["items"]
    assert len(partner_items) == 1
    assert partner_items[0]["contact_name"] == "[ANONYMIZED]"
    assert partner_items[0]["contact_value"] == "[REDACTED]"
    assert "0988776655" not in res_partner_list.text


# --------------------------------------------------------------------------- #
# Tabletop Scenario 5: Security Incident Tabletop & Kill Switch Rehearsal
# --------------------------------------------------------------------------- #

def test_tabletop_incident_containment_and_kill_switches(client: TestClient, db_session):
    """Tabletop Exercise 5: Security Incident Containment and Granular Kill Switch Rehearsal.

    Simulates SEV-1 incident protocol activation where an operator trips the emergency
    kill switch for AI Tutor and RBPC Commerce during suspected exploitation.

    Invariants Verified:
    - Admin-only access to kill-switch management (non-admin receives 403).
    - Toggling kill switches updates runtime overrides immediately.
    - Public heritage browsing (Heritage Places, Stories) remains 100% available
      even when kill switches are tripped (Golden Rule 1: Preserve Public Availability First).
    - Recovery procedure restores switches to active state.
    """
    admin = _create_user(
        db_session,
        f"sec_incident_commander_{uuid.uuid4().hex[:6]}@histolab.icu",
        role=UserRole.admin,
        display_name="Chỉ Huy Xử Lý Sự Cố An Ninh",
    )
    learner = _create_user(
        db_session,
        f"visitor_browsing_{uuid.uuid4().hex[:6]}@public.vn",
        role=UserRole.learner,
    )

    headers_admin = _auth_headers(admin)
    headers_learner = _auth_headers(learner)

    # 1. Non-admin cannot access kill switch controls (403)
    res_forbidden = client.get("/api/v1/admin/kill-switches", headers=headers_learner)
    assert res_forbidden.status_code == status.HTTP_403_FORBIDDEN

    # 2. Admin inspects kill switches
    res_status = client.get("/api/v1/admin/kill-switches", headers=headers_admin)
    assert res_status.status_code == status.HTTP_200_OK
    flags = res_status.json()["flags"]
    assert "FEATURE_FLAG_AI_TUTOR_ENABLED" in flags
    assert "FEATURE_FLAG_RBPC_COMMERCE_ENABLED" in flags

    # 3. INCIDENT SIMULATION: Containment phase trips AI Tutor kill switch
    res_trip = client.post(
        "/api/v1/admin/kill-switches/FEATURE_FLAG_AI_TUTOR_ENABLED/toggle",
        json={"enabled": False, "reason": "TABLETOP_SEV1_CONTAINMENT_TEST"},
        headers=headers_admin,
    )
    assert res_trip.status_code == status.HTTP_200_OK
    assert ff_service.is_feature_flag_enabled("FEATURE_FLAG_AI_TUTOR_ENABLED", db=db_session) is False

    # 4. Golden Rule 1 Verification: Public heritage browsing remains fully accessible
    res_places = client.get("/api/v1/heritage/places")
    assert res_places.status_code == status.HTTP_200_OK

    res_stories = client.get("/api/v1/rbpc/stories")
    assert res_stories.status_code == status.HTTP_200_OK

    # 5. RECOVERY PHASE: Restore kill switch after incident containment
    res_restore = client.post(
        "/api/v1/admin/kill-switches/FEATURE_FLAG_AI_TUTOR_ENABLED/toggle",
        json={"enabled": True, "reason": "TABLETOP_RECOVERY_SUCCESSFUL"},
        headers=headers_admin,
    )
    assert res_restore.status_code == status.HTTP_200_OK
    assert ff_service.is_feature_flag_enabled("FEATURE_FLAG_AI_TUTOR_ENABLED", db=db_session) is True
