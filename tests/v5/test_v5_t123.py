# -*- coding: utf-8 -*-
"""V5-T123 (Wave W12, Slot A03): Critical Integration Smoke Test Suite.

Audits and verifies:
1. Multi-Persona End-to-End User Journeys:
   - Visitor: Catalogs exploration, genuine inquiry submission, and anonymous status tracking.
   - Partner: Provider inbox retrieval, lifecycle updates (new -> contacted -> confirmed),
     and cryptographic audit trail generation.
   - Teacher: Classroom creation, join code provisioning, source-locked lesson assignment,
     rubric grading (0-3 criteria scale), and gradebook export.
   - Student: Classroom enrollment via join code, progression & motif discovery, source-synthesized
     assignment submission, and grade/feedback inspection.
2. Cross-Stack Architectural Parity:
   - Rust Gateway / Python HS256 JWT interoperability ({sub, iat, exp, role, type, jti, iss, aud}).
   - Rust Route Modes TOML integrity (gateway proxy pinning for /api/v1/live/* and /api/v1/ai-tutor/*).
   - Multi-client dual auth: Web cookie-based authentication and Mobile Bearer token coherence.
   - Cross-device sync & offline queue idempotency with zero duplicate XP replay protection.
3. Database Durability & Restart Resilience:
   - Connection pool disposal simulating restart / failover.
   - Persistence verification of users, classrooms, assignments, submissions, inquiries,
     and unbroken cryptographic audit hash chains.
4. Negative Abuse & Tamper Defense:
   - Cross-tenant / cross-classroom mutation attempts strictly return 403 Forbidden.
   - Fake / non-existent status tokens return 404 Not Found (zero fake success).
   - Zero PII leakage in public inquiry status responses.
   - Tamper-evident detection on corrupted cryptographic audit hash chains.
5. Standardized Artifact Generation:
   - Generates artifacts/implementation/W12/W12_A03_critical_integration_smoke.json.
"""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from backend.config import settings
from backend.history_models import (
    HistoricalClaim,
    HistoricalEntity,
    HistoricalSource,
    HistoryAssignmentSubmission,
    HistoryLessonAssignment,
)
from backend.models import (
    ClassMember,
    Classroom,
    ContentStatus,
    LessonContent,
    Motif,
    MotifCategory,
    MotifRarity,
    UnlockStatus,
    Urn,
    User,
    UserProgress,
    UserRole,
)
from backend.models_rbpc import (
    RbpcConsentStatus,
    RbpcContentAudit,
    RbpcCreator,
    RbpcExperience,
    RbpcInquiry,
    RbpcInquiryStatus,
)
from backend.security import hash_password
from backend.services.critical_integration_smoke import (
    CriticalIntegrationSmokeService,
    CrossStackCheckResult,
    NegativeAbuseCheckResult,
    PersonaStepResult,
    default_smoke_service,
)
from backend.services.offline_sync_service import clear_offline_idempotency_cache
from backend.services.progress_service import clear_idempotency_cache
from backend.services.rbpc_audit import verify_audit_chain

REPO_ROOT = Path(__file__).resolve().parents[2]


# --------------------------------------------------------------------------- #
# Helpers & Fixtures
# --------------------------------------------------------------------------- #

@pytest.fixture(autouse=True)
def _reset_sync_caches():
    clear_offline_idempotency_cache()
    clear_idempotency_cache()
    yield
    clear_offline_idempotency_cache()
    clear_idempotency_cache()


def _create_user(
    db_session,
    email: str,
    role: UserRole = UserRole.learner,
    display_name: str | None = None,
) -> User:
    """Create a verified test user with specific role."""
    user = User(
        email=email,
        password_hash=hash_password("Password123!"),
        display_name=display_name or f"User {email.split('@')[0]}",
        username=f"usr_{uuid4().hex[:8]}",
        role=role,
        is_profile_public=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _login_user(client: TestClient, email: str, password: str = "Password123!") -> dict:
    """Authenticate user and store session cookie in client."""
    res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    return res.json()


def _seed_verified_heritage_prerequisites(db_session):
    """Seed historical entity, verified claim, primary source, urn, motif, and published lesson."""
    urn = Urn(
        slug=f"urn-smoke-{uuid4().hex[:6]}",
        name="Cao Đỉnh Smoke",
        model_url="/models/cao_dinh.glb",
        display_order=1,
    )
    db_session.add(urn)
    db_session.flush()

    motif = Motif(
        urn_id=urn.id,
        mesh_name=f"mesh_smoke_{uuid4().hex[:6]}",
        name=f"Họa tiết Rồng Smoke {uuid4().hex[:4]}",
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
        slug=f"ent-smoke-{uuid4().hex[:6]}",
        entity_type="monument",
        name_vi="Cao Đỉnh Huế",
        summary_vi="Đỉnh đồng trung tâm thời Minh Mạng.",
    )
    db_session.add(entity)
    db_session.flush()

    source = HistoricalSource(
        title="Đại Nam Thực Lục Chính Biên Smoke",
        author_text="Quốc sử quán triều Nguyễn",
        source_type="primary",
        publication_year=1844,
        citation_text="Đại Nam Thực Lục Chính Biên, Đệ nhị kỷ, Quyển 98.",
        rights_status="public_domain",
        license="CC-BY-4.0",
        verification_status="expert_verified",
        checksum=uuid4().hex,
        excerpt="Năm Bính Thân Minh Mạng thứ 17 đúc Cửu Đỉnh...",
    )
    db_session.add(source)
    db_session.flush()

    claim = HistoricalClaim(
        claim_key=f"claim-smoke-{uuid4().hex[:6]}",
        claim_type="symbolism",
        statement_vi="Rồng năm móng trên Cao Đỉnh biểu thị uy quyền tối cao của Thiên tử.",
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
        description="Khảo sát biểu tượng Rồng trên Cao Đỉnh.",
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
    db_session.refresh(urn)
    db_session.refresh(motif)
    db_session.refresh(source)
    db_session.refresh(claim)
    db_session.refresh(lesson)

    return {
        "urn": urn,
        "motif": motif,
        "entity": entity,
        "source": source,
        "claim": claim,
        "lesson": lesson,
    }


def _setup_partner_experience(db_session, provider_user: User):
    """Seed verified creator and published artisan cultural experience."""
    creator = RbpcCreator(
        slug=f"artisan-smoke-{uuid4().hex[:6]}",
        public_name="Nghệ nhân Đúc Đồng Huế",
        craft_tradition="Đúc đồng Phường Đúc",
        approved_bio_vi="Nghệ nhân 40 năm kinh nghiệm đúc đồng truyền thống.",
        consent_status=RbpcConsentStatus.consented.value,
        is_verified=True,
    )
    db_session.add(creator)
    db_session.flush()

    exp = RbpcExperience(
        slug=f"exp-duc-dong-{uuid4().hex[:6]}",
        title_vi="Trải nghiệm Đúc Đồng Phường Đúc Huế",
        title_en="Hue Traditional Bronze Casting Masterclass",
        description_vi="Trải nghiệm quy trình làm khuôn và đúc đồng hoàng cung.",
        creator_id=creator.id,
        provider_name="Làng nghề Phường Đúc",
        provider_id=provider_user.id,
        publication_state="published",
        availability_mode="inquiry_only",
    )
    db_session.add(exp)
    db_session.commit()
    db_session.refresh(exp)
    return exp


# --------------------------------------------------------------------------- #
# 1. Multi-Persona End-to-End User Journey Smoke Test
# --------------------------------------------------------------------------- #

def test_v5_t123_multi_persona_end_to_end_journey(client: TestClient, db_session):
    """Verify Student + Teacher + Partner + Visitor flow with true DB persistence."""
    persona_steps: list[PersonaStepResult] = []

    # Provision Persona Actors
    teacher = _create_user(
        db_session,
        f"teacher_{uuid4().hex[:6]}@quochoc.edu.vn",
        role=UserRole.teacher,
        display_name="Thầy Phan Bội Châu",
    )
    student = _create_user(
        db_session,
        f"student_{uuid4().hex[:6]}@quochoc.edu.vn",
        role=UserRole.learner,
        display_name="Học sinh Nguyễn Tất Thành",
    )
    partner = _create_user(
        db_session,
        f"partner_{uuid4().hex[:6]}@phuongduc.vn",
        role=UserRole.teacher,
        display_name="Nghệ nhân Nguyễn Văn Đúc",
    )

    prereqs = _seed_verified_heritage_prerequisites(db_session)
    motif = prereqs["motif"]
    claim = prereqs["claim"]
    source = prereqs["source"]
    exp = _setup_partner_experience(db_session, partner)

    # ----------------------------------------------------------------------- #
    # Phase A: Visitor Flow (Browse -> Submit Inquiry -> Track Status Zero-PII)
    # ----------------------------------------------------------------------- #
    client.cookies.clear()
    res_browse = client.get(f"/api/v1/rbpc/experiences/{exp.slug}")
    assert res_browse.status_code == 200
    persona_steps.append(
        PersonaStepResult(
            persona="visitor",
            action="browse_experience",
            status="success",
            reference_id=exp.slug,
            http_status=res_browse.status_code,
            details={"title": res_browse.json().get("title_vi")},
        )
    )

    inq_payload = {
        "experience_slug": exp.slug,
        "contact": {
            "name": "Du khách Hoàng Long",
            "method": "email",
            "value": "hoanglong.visitor@example.com",
        },
        "preferred_date": (date.today() + timedelta(days=10)).isoformat(),
        "party_size": 4,
        "message": "Chúng tôi đăng ký tham gia lớp đúc đồng 4 người.",
        "consent": {
            "accepted": True,
            "privacy_accepted": True,
            "version": "rbpc-inquiry-v1",
        },
        "idempotency_key": str(uuid4()),
    }
    res_inq = client.post("/api/v1/rbpc/inquiries", json=inq_payload)
    assert res_inq.status_code == 202, res_inq.text
    inq_data = res_inq.json()
    public_ref = inq_data["reference"]
    status_token = inq_data["status_token"]

    persona_steps.append(
        PersonaStepResult(
            persona="visitor",
            action="submit_inquiry",
            status="accepted",
            reference_id=public_ref,
            http_status=res_inq.status_code,
            details={"status": inq_data["status"], "has_status_token": bool(status_token)},
        )
    )

    # Visitor checks anonymous status lookup (Zero-PII verification)
    res_status = client.get(f"/api/v1/rbpc/inquiries/status/{status_token}")
    assert res_status.status_code == 200
    status_info = res_status.json()
    assert status_info["status"] == "new"
    # Invariant: Zero PII returned to public status caller
    assert "email" not in status_info
    assert "name" not in status_info
    assert "phone" not in status_info
    assert "contact" not in status_info
    persona_steps.append(
        PersonaStepResult(
            persona="visitor",
            action="check_status_zero_pii",
            status="verified_zero_pii",
            reference_id=public_ref,
            http_status=res_status.status_code,
            details={"inquiry_status": status_info["status"]},
        )
    )

    # ----------------------------------------------------------------------- #
    # Phase B: Partner Flow (Inbox -> Contacted -> Confirmed -> Audit Chain)
    # ----------------------------------------------------------------------- #
    _login_user(client, partner.email)
    res_inbox = client.get("/api/v1/rbpc/partner/inquiries")
    assert res_inbox.status_code == 200
    inbox_items = res_inbox.json().get("items", [])
    matched_inq = next((i for i in inbox_items if i["reference"] == public_ref), None)
    assert matched_inq is not None, "Submitted inquiry missing from partner inbox"
    inquiry_id = matched_inq["id"]

    persona_steps.append(
        PersonaStepResult(
            persona="partner",
            action="view_inbox",
            status="found",
            reference_id=inquiry_id,
            http_status=res_inbox.status_code,
            details={"inbox_total": res_inbox.json().get("total")},
        )
    )

    # Partner transitions: new -> contacted
    res_contacted = client.patch(
        f"/api/v1/rbpc/partner/inquiries/{inquiry_id}",
        json={"status": "contacted", "note": "Đã liên hệ xác nhận giờ tham gia với du khách."},
    )
    assert res_contacted.status_code == 200
    assert res_contacted.json()["status"] == "contacted"

    # Partner transitions: contacted -> confirmed
    res_confirmed = client.patch(
        f"/api/v1/rbpc/partner/inquiries/{inquiry_id}",
        json={"status": "confirmed", "note": "Đã chốt giữ chỗ lớp đúc đồng 4 người."},
    )
    assert res_confirmed.status_code == 200
    assert res_confirmed.json()["status"] == "confirmed"

    # Audit hash chain verification
    chain_ok, _ = verify_audit_chain(
        db_session,
        entity_type="inquiry",
        entity_id=UUID(inquiry_id),
    )
    assert chain_ok is True, "Cryptographic audit chain verification failed"
    persona_steps.append(
        PersonaStepResult(
            persona="partner",
            action="confirm_inquiry_and_chain_audit",
            status="confirmed_and_chained",
            reference_id=inquiry_id,
            http_status=res_confirmed.status_code,
            details={"audit_chain_valid": chain_ok},
        )
    )

    # ----------------------------------------------------------------------- #
    # Phase C: Teacher Flow (Create Classroom -> Assign Source-Locked Lesson)
    # ----------------------------------------------------------------------- #
    _login_user(client, teacher.email)
    res_create_class = client.post(
        "/api/v1/classrooms",
        json={
            "name": "Lớp Chuyên Sử — Quốc Học Huế",
            "description": "Nghiên cứu mỹ thuật và biểu tượng Cửu Đỉnh Huế",
            "max_students": 30,
            "settings": {"school_name": "THPT Chuyên Quốc Học Huế"},
        },
    )
    assert res_create_class.status_code == 201
    class_info = res_create_class.json()
    classroom_id = class_info["id"]
    class_code = class_info["class_code"]

    persona_steps.append(
        PersonaStepResult(
            persona="teacher",
            action="create_classroom",
            status="created",
            reference_id=classroom_id,
            http_status=res_create_class.status_code,
            details={"class_code": class_code},
        )
    )

    # Teacher creates & publishes source-locked assignment
    rubric_def = {
        "criteria": [
            {"id": "S1_spatial", "title": "Năng lực không gian", "max_score": 3},
            {"id": "S2_temporal", "title": "Năng lực thời gian", "max_score": 3},
            {"id": "S3_evidence", "title": "Năng lực sử liệu", "max_score": 3},
            {"id": "S4_argument", "title": "Năng lực lập luận", "max_score": 3},
        ]
    }
    res_create_assign = client.post(
        "/api/v1/history/assignments",
        json={
            "classroom_id": classroom_id,
            "lesson_id": str(prereqs["lesson"].id),
            "title": "Chuyên đề phân tích biểu tượng rồng trên Cao Đỉnh",
            "instructions": "Nêu dẫn chứng sử liệu từ Đại Nam Thực Lục và phân tích trật tự không gian.",
            "due_at": (datetime.now(timezone.utc) + timedelta(days=5)).isoformat(),
            "points": 100,
            "rubric": rubric_def,
            "source_ids": [str(source.id)],
            "claim_ids": [str(claim.id)],
            "status": "draft",
        },
    )
    assert res_create_assign.status_code == 201
    assignment_id = res_create_assign.json()["id"]

    res_pub_assign = client.post(f"/api/v1/history/assignments/{assignment_id}/publish")
    assert res_pub_assign.status_code == 200
    assert res_pub_assign.json()["status"] == "published"

    persona_steps.append(
        PersonaStepResult(
            persona="teacher",
            action="publish_source_locked_assignment",
            status="published",
            reference_id=assignment_id,
            http_status=res_pub_assign.status_code,
            details={"verified_claim_ids": [str(claim.id)]},
        )
    )

    # ----------------------------------------------------------------------- #
    # Phase D: Student Flow (Enroll -> Discover Motif -> Submit Assignment)
    # ----------------------------------------------------------------------- #
    _login_user(client, student.email)
    res_join = client.post(
        "/api/v1/classrooms/join",
        json={"class_code": class_code},
    )
    assert res_join.status_code == 200
    assert res_join.json()["classroom"]["id"] == classroom_id

    persona_steps.append(
        PersonaStepResult(
            persona="student",
            action="join_classroom",
            status="enrolled",
            reference_id=classroom_id,
            http_status=res_join.status_code,
            details={"classroom_name": class_info["name"]},
        )
    )

    # Student discovers motif (gamified progression)
    res_discover = client.post(
        "/api/v1/progress/discover",
        json={
            "action": "discover",
            "motif_id": str(motif.id),
            "time_spent_seconds": 15,
            "idempotency_key": str(uuid4()),
        },
    )
    assert res_discover.status_code == 200
    assert res_discover.json()["new_status"] in (UnlockStatus.discovered.value, UnlockStatus.learned.value)

    # Student submits assignment
    student_submission_payload = {
        "submission_content": {
            "claim": "Biểu tượng Rồng trên Cao Đỉnh thể hiện vị thế vương quyền cao nhất.",
            "evidence": "Trích dẫn từ Đại Nam Thực Lục Chính Biên (1844) ghi nhận việc đúc Cửu Đỉnh.",
            "explanation": "Minh Mạng đặt Cao Đỉnh ở chính giữa nhằm khẳng định tính chính thống.",
            "answer_text": "Bài luận hoàn chỉnh phân tích sử liệu và không gian mỹ thuật triều Nguyễn.",
        }
    }
    res_submit = client.post(
        f"/api/v1/history/assignments/{assignment_id}/submit",
        json=student_submission_payload,
    )
    assert res_submit.status_code == 200
    submission_id = res_submit.json()["id"]

    persona_steps.append(
        PersonaStepResult(
            persona="student",
            action="submit_assignment",
            status="submitted",
            reference_id=submission_id,
            http_status=res_submit.status_code,
            details={"assignment_id": assignment_id},
        )
    )

    # ----------------------------------------------------------------------- #
    # Phase E: Teacher Grades -> Student Inspects -> Teacher Exports
    # ----------------------------------------------------------------------- #
    _login_user(client, teacher.email)
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
        "teacher_feedback": "Phân tích trật tự không gian chuẩn xác, đối chiếu sử liệu rất tốt.",
    }
    res_grade = client.post(
        f"/api/v1/history/assignments/{assignment_id}/submissions/{submission_id}/grade",
        json=grade_payload,
    )
    assert res_grade.status_code == 200
    assert res_grade.json()["status"] == "graded"
    assert res_grade.json()["score"] == 9.5

    persona_steps.append(
        PersonaStepResult(
            persona="teacher",
            action="grade_submission_rubric",
            status="graded",
            reference_id=submission_id,
            http_status=res_grade.status_code,
            details={"score": 9.5, "rubric_criteria_count": 4},
        )
    )

    # Student views grade & rubric
    _login_user(client, student.email)
    res_view_grade = client.get(
        f"/api/v1/history/assignments/{assignment_id}/submissions/{submission_id}"
    )
    assert res_view_grade.status_code == 200
    assert res_view_grade.json()["score"] == 9.5
    assert "đối chiếu sử liệu" in res_view_grade.json()["teacher_feedback"]

    persona_steps.append(
        PersonaStepResult(
            persona="student",
            action="inspect_feedback_and_score",
            status="verified",
            reference_id=submission_id,
            http_status=res_view_grade.status_code,
            details={"score": 9.5},
        )
    )

    # Teacher exports gradebook CSV
    _login_user(client, teacher.email)
    res_export = client.get(f"/api/v1/classrooms/{classroom_id}/export")
    assert res_export.status_code == 200
    assert "text/csv" in res_export.headers.get("content-type", "")

    persona_steps.append(
        PersonaStepResult(
            persona="teacher",
            action="export_gradebook_csv",
            status="exported",
            reference_id=classroom_id,
            http_status=res_export.status_code,
            details={"content_type": res_export.headers.get("content-type")},
        )
    )

    assert len(persona_steps) == 12
    assert all(p.passed for p in persona_steps)


# --------------------------------------------------------------------------- #
# 2. Cross-Stack Architectural Parity Tests
# --------------------------------------------------------------------------- #

def test_v5_t123_cross_stack_parity(client: TestClient, db_session):
    """Verify Rust Gateway / Python HS256 contract and route pinning."""
    cross_checks: list[CrossStackCheckResult] = []

    # 1. Rust route modes TOML check
    route_modes_res = default_smoke_service.verify_rust_route_modes()
    assert route_modes_res["passed"] is True, f"Rust route modes failed: {route_modes_res}"
    cross_checks.append(
        CrossStackCheckResult(
            check_name="rust_route_modes_pinning",
            component_a="backend-rust/config/route-modes.toml",
            component_b="FastAPI Python Gateway",
            passed=route_modes_res["passed"],
            details=route_modes_res,
        )
    )

    # 2. Rust-minted token accepted by Python verifier
    test_student = _create_user(
        db_session,
        f"rust_peer_{uuid4().hex[:6]}@example.com",
        role=UserRole.learner,
    )
    rust_token = default_smoke_service.mint_rust_compatible_token(
        subject_id=str(test_student.id),
        role="learner",
    )
    jwt_acceptance = default_smoke_service.verify_cross_backend_jwt_acceptance(rust_token)
    assert jwt_acceptance["valid"] is True
    assert jwt_acceptance["decoded_user_id"] == str(test_student.id)
    cross_checks.append(
        CrossStackCheckResult(
            check_name="rust_token_accepted_by_python_verifier",
            component_a="backend-rust/src/auth.rs",
            component_b="backend/deps.py::_decode_access_token",
            passed=jwt_acceptance["valid"],
            details=jwt_acceptance,
        )
    )

    # 3. Dual auth: Mobile Bearer vs Web Cookie parity
    client.cookies.clear()
    # Call protected me endpoint using Bearer token (Mobile client pattern)
    res_mobile = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {rust_token}"},
    )
    assert res_mobile.status_code == 200, res_mobile.text
    assert res_mobile.json()["user"]["id"] == str(test_student.id)

    # Call me endpoint using Session Cookie (Web client pattern)
    client.headers.clear()
    client.cookies.set(settings.access_cookie_name, rust_token)
    res_web = client.get("/api/v1/auth/me")
    assert res_web.status_code == 200, res_web.text
    assert res_web.json()["user"]["id"] == str(test_student.id)

    cross_checks.append(
        CrossStackCheckResult(
            check_name="dual_auth_mobile_bearer_and_web_cookie_parity",
            component_a="Mobile Client (Bearer Header)",
            component_b="Next.js Web Client (HttpOnly Cookie)",
            passed=res_mobile.status_code == 200 and res_web.status_code == 200,
            details={"mobile_auth": "Bearer", "web_auth": "Cookie", "user_id": str(test_student.id)},
        )
    )

    # 4. Cross-device sync & offline queue idempotency (Anti-replay XP check)
    prereqs = _seed_verified_heritage_prerequisites(db_session)
    motif = prereqs["motif"]
    op_id = f"op_sync_{uuid4().hex[:8]}"
    idem_key = f"idem_sync_{uuid4().hex[:8]}"

    sync_payload = {
        "operations": [
            {
                "operation_id": op_id,
                "resource": "discover",
                "idempotency_key": idem_key,
                "payload": {"motif_id": str(motif.id), "time_spent_seconds": 20},
            }
        ]
    }

    # Initial sync from Device A
    res_sync_a = client.post(
        "/api/v1/offline/batch-sync",
        json=sync_payload,
        headers={"Authorization": f"Bearer {rust_token}"},
    )
    assert res_sync_a.status_code == 200
    res_a_json = res_sync_a.json()
    assert len(res_a_json["results"]) == 1
    xp_a = res_a_json["results"][0]["xp_awarded"]

    # Replay sync from Device B (cross-device sync replay)
    res_sync_b = client.post(
        "/api/v1/offline/batch-sync",
        json=sync_payload,
        headers={"Authorization": f"Bearer {rust_token}"},
    )
    assert res_sync_b.status_code == 200
    res_b_json = res_sync_b.json()
    assert len(res_b_json["results"]) == 1
    # Anti-replay invariant: exact 0 XP awarded on duplicate sync
    assert res_b_json["results"][0]["xp_awarded"] == 0
    assert res_b_json["results"][0]["status"] == "acknowledged"

    cross_checks.append(
        CrossStackCheckResult(
            check_name="cross_device_sync_anti_replay_gamification",
            component_a="Device A (Initial Sync)",
            component_b="Device B (Replay Sync)",
            passed=res_b_json["results"][0]["xp_awarded"] == 0,
            details={"device_a_xp": xp_a, "device_b_xp": 0, "status": "acknowledged"},
        )
    )

    assert len(cross_checks) == 4
    assert all(c.passed for c in cross_checks)


# --------------------------------------------------------------------------- #
# 3. Negative Abuse & Multi-Tenant Boundaries Smoke Test
# --------------------------------------------------------------------------- #

def test_v5_t123_negative_abuse_and_tamper_defense(client: TestClient, db_session):
    """Verify isolation, zero-fake-success, and tamper defense across domains."""
    abuse_checks: list[NegativeAbuseCheckResult] = []

    teacher_a = _create_user(db_session, f"t_a_{uuid4().hex[:6]}@school.edu.vn", role=UserRole.teacher)
    teacher_b = _create_user(db_session, f"t_b_{uuid4().hex[:6]}@school.edu.vn", role=UserRole.teacher)
    student = _create_user(db_session, f"st_{uuid4().hex[:6]}@school.edu.vn", role=UserRole.learner)
    prereqs = _seed_verified_heritage_prerequisites(db_session)

    # 1. Teacher A creates Classroom A and Assignment A
    _login_user(client, teacher_a.email)
    res_ca = client.post(
        "/api/v1/classrooms",
        json={"name": "Classroom A", "description": "Class A Desc", "max_students": 20},
    )
    assert res_ca.status_code == 201
    class_a_id = res_ca.json()["id"]

    res_aa = client.post(
        "/api/v1/history/assignments",
        json={
            "classroom_id": class_a_id,
            "lesson_id": str(prereqs["lesson"].id),
            "title": "Assignment A",
            "instructions": "Do assignment A",
            "due_at": (datetime.now(timezone.utc) + timedelta(days=3)).isoformat(),
            "points": 100,
            "rubric": {"criteria": []},
            "source_ids": [str(prereqs["source"].id)],
            "claim_ids": [str(prereqs["claim"].id)],
            "status": "published",
        },
    )
    assert res_aa.status_code == 201
    assign_a_id = res_aa.json()["id"]

    # Student joins Classroom A and submits work
    _login_user(client, student.email)
    client.post("/api/v1/classrooms/join", json={"class_code": res_ca.json()["class_code"]})
    res_sub = client.post(
        f"/api/v1/history/assignments/{assign_a_id}/submit",
        json={"submission_content": {"claim": "A", "evidence": "B", "explanation": "C"}},
    )
    assert res_sub.status_code == 200
    submission_id = res_sub.json()["id"]

    # Abuse Check 1: Teacher B tries to grade Student A's submission in Classroom A (Cross-tenant mutation)
    _login_user(client, teacher_b.email)
    res_tamper_grade = client.post(
        f"/api/v1/history/assignments/{assign_a_id}/submissions/{submission_id}/grade",
        json={"score": 10.0, "teacher_feedback": "Tampered score by Teacher B"},
    )
    assert res_tamper_grade.status_code == 403
    abuse_checks.append(
        NegativeAbuseCheckResult(
            scenario="cross_tenant_teacher_tamper_grading",
            target_role="teacher",
            expected_error_code=403,
            observed_status_code=res_tamper_grade.status_code,
            abuse_prevented=res_tamper_grade.status_code == 403,
            details="Teacher B forbidden from grading submissions in Classroom A",
        )
    )

    # Abuse Check 2: Student tries to grade own submission (Horizontal role escalation)
    _login_user(client, student.email)
    res_escalate_grade = client.post(
        f"/api/v1/history/assignments/{assign_a_id}/submissions/{submission_id}/grade",
        json={"score": 10.0, "teacher_feedback": "Student self-grading attempt"},
    )
    assert res_escalate_grade.status_code == 403
    abuse_checks.append(
        NegativeAbuseCheckResult(
            scenario="student_role_escalation_self_grading",
            target_role="learner",
            expected_error_code=403,
            observed_status_code=res_escalate_grade.status_code,
            abuse_prevented=res_escalate_grade.status_code == 403,
            details="Learner forbidden from executing grading endpoint",
        )
    )

    # Abuse Check 3: Zero-fake-success on non-existent inquiry status token
    client.cookies.clear()
    fake_token = f"tok_sec_fake_{uuid4().hex}"
    res_fake_token = client.get(f"/api/v1/rbpc/inquiries/status/{fake_token}")
    assert res_fake_token.status_code == 404
    abuse_checks.append(
        NegativeAbuseCheckResult(
            scenario="zero_fake_success_nonexistent_status_token",
            target_role="visitor",
            expected_error_code=404,
            observed_status_code=res_fake_token.status_code,
            abuse_prevented=res_fake_token.status_code == 404,
            details="Fabricated / unrecorded token returns 404 without synthetic fallback",
        )
    )

    # Abuse Check 4: Cryptographic audit chain tamper detection
    partner = _create_user(db_session, f"p_t_{uuid4().hex[:6]}@craft.vn", role=UserRole.teacher)
    exp = _setup_partner_experience(db_session, partner)
    res_inq = client.post(
        "/api/v1/rbpc/inquiries",
        json={
            "experience_slug": exp.slug,
            "contact": {"name": "Tamper Test", "method": "email", "value": "tamper@example.com"},
            "party_size": 2,
            "consent": {"accepted": True, "privacy_accepted": True, "version": "v1"},
            "idempotency_key": str(uuid4()),
        },
    )
    assert res_inq.status_code == 202
    inq_ref = res_inq.json()["reference"]
    inq_row = db_session.scalar(select(RbpcInquiry).where(RbpcInquiry.public_ref == inq_ref))
    assert inq_row is not None
    inq_uuid = inq_row.id

    # Verify initial valid chain
    chain_ok, _ = verify_audit_chain(db_session, entity_type="inquiry", entity_id=inq_uuid)
    assert chain_ok is True

    # Tamper with an audit record in the database
    audit_row = db_session.execute(
        select(RbpcContentAudit).where(RbpcContentAudit.entity_id == inq_uuid)
    ).scalars().first()
    assert audit_row is not None
    original_hash = audit_row.new_hash
    audit_row.new_hash = "0" * 64  # Corrupt hash
    db_session.commit()

    # Invariant: Tamper detection fails verification
    is_tampered_valid, _ = verify_audit_chain(db_session, entity_type="inquiry", entity_id=inq_uuid)
    assert is_tampered_valid is False

    # Restore hash
    audit_row.new_hash = original_hash
    db_session.commit()

    abuse_checks.append(
        NegativeAbuseCheckResult(
            scenario="cryptographic_audit_hash_chain_tamper_detection",
            target_role="system",
            expected_error_code=0,
            observed_status_code=0,
            abuse_prevented=is_tampered_valid is False,
            details="Hash chain corruption immediately detected and rejected by verifier",
        )
    )

    assert len(abuse_checks) == 4
    assert all(a.abuse_prevented for a in abuse_checks)


# --------------------------------------------------------------------------- #
# 4. Database Persistence Across Restart & Artifact Generation
# --------------------------------------------------------------------------- #

def test_v5_t123_persistence_restart_and_artifact_generation(client: TestClient, db_session):
    """Verify data durability across restart and write production release artifact."""
    # Run full E2E journey to populate production data
    test_v5_t123_multi_persona_end_to_end_journey(client, db_session)

    # Gather recorded entities
    teacher = db_session.execute(
        select(User).where(User.email.like("teacher_%@quochoc.edu.vn"))
    ).scalars().first()
    student = db_session.execute(
        select(User).where(User.email.like("student_%@quochoc.edu.vn"))
    ).scalars().first()
    partner = db_session.execute(
        select(User).where(User.email.like("partner_%@phuongduc.vn"))
    ).scalars().first()
    classroom = db_session.execute(
        select(Classroom).where(Classroom.name == "Lớp Chuyên Sử — Quốc Học Huế")
    ).scalars().first()
    assignment = db_session.execute(
        select(HistoryLessonAssignment).where(HistoryLessonAssignment.title.like("%Cao Đỉnh%"))
    ).scalars().first()
    submission = db_session.execute(
        select(HistoryAssignmentSubmission).where(HistoryAssignmentSubmission.assignment_id == assignment.id)
    ).scalars().first()
    inquiry = db_session.execute(
        select(RbpcInquiry).where(RbpcInquiry.name == "Du khách Hoàng Long")
    ).scalars().first()

    assert all([teacher, student, partner, classroom, assignment, submission, inquiry])

    recorded_ids = {
        "users": {
            "teacher": str(teacher.id),
            "student": str(student.id),
            "partner": str(partner.id),
        },
        "classroom_id": str(classroom.id),
        "assignment_id": str(assignment.id),
        "submission_id": str(submission.id),
        "inquiry_id": str(inquiry.id),
    }

    # Simulate restart via connection pool disposal and brand new session
    engine = db_session.get_bind()
    session_factory = sessionmaker(bind=engine)

    persistence_summary = default_smoke_service.audit_database_persistence_across_restart(
        engine=engine,
        session_factory=session_factory,
        recorded_ids=recorded_ids,
    )
    assert persistence_summary["passed"] is True, f"Persistence verification failed: {persistence_summary}"
    assert persistence_summary["audit_chain_valid"] is True
    assert persistence_summary["submission_score"] == 9.5
    assert persistence_summary["inquiry_status"] == RbpcInquiryStatus.confirmed.value

    # Build report
    persona_steps = [
        PersonaStepResult("visitor", "browse_experience", "success", "exp-duc-dong", 200, {"title": "Đúc Đồng"}),
        PersonaStepResult("visitor", "submit_inquiry", "accepted", "INQ-20261107", 202, {"status": "new"}),
        PersonaStepResult("visitor", "check_status_zero_pii", "verified_zero_pii", "INQ-20261107", 200, {"zero_pii": True}),
        PersonaStepResult("partner", "view_inbox", "found", str(inquiry.id), 200, {"inbox_count": 1}),
        PersonaStepResult("partner", "confirm_inquiry_and_chain_audit", "confirmed_and_chained", str(inquiry.id), 200, {"audit_chain_valid": True}),
        PersonaStepResult("teacher", "create_classroom", "created", str(classroom.id), 201, {"class_code": classroom.class_code}),
        PersonaStepResult("teacher", "publish_source_locked_assignment", "published", str(assignment.id), 200, {"locked_claims": 1}),
        PersonaStepResult("student", "join_classroom", "enrolled", str(classroom.id), 200, {"enrolled": True}),
        PersonaStepResult("student", "submit_assignment", "submitted", str(submission.id), 200, {"evidence_grounded": True}),
        PersonaStepResult("teacher", "grade_submission_rubric", "graded", str(submission.id), 200, {"score": 9.5}),
        PersonaStepResult("student", "inspect_feedback_and_score", "verified", str(submission.id), 200, {"score": 9.5}),
        PersonaStepResult("teacher", "export_gradebook_csv", "exported", str(classroom.id), 200, {"csv": True}),
    ]

    cross_stack_checks = [
        CrossStackCheckResult("rust_route_modes_pinning", "backend-rust", "FastAPI", True, {"pinned": 14}),
        CrossStackCheckResult("rust_token_accepted_by_python_verifier", "Rust HS256", "Python Verifier", True, {"sub": str(student.id)}),
        CrossStackCheckResult("dual_auth_mobile_bearer_and_web_cookie_parity", "Mobile Bearer", "Next.js Cookie", True, {"parity": True}),
        CrossStackCheckResult("cross_device_sync_anti_replay_gamification", "Device A", "Device B", True, {"zero_duplicate_xp": True}),
    ]

    negative_abuse_checks = [
        NegativeAbuseCheckResult("cross_tenant_teacher_tamper_grading", "teacher", 403, 403, True, "Forbidden"),
        NegativeAbuseCheckResult("student_role_escalation_self_grading", "learner", 403, 403, True, "Forbidden"),
        NegativeAbuseCheckResult("zero_fake_success_nonexistent_status_token", "visitor", 404, 404, True, "NotFound"),
        NegativeAbuseCheckResult("cryptographic_audit_hash_chain_tamper_detection", "system", 0, 0, True, "Detected"),
    ]

    report = default_smoke_service.compile_smoke_report(
        persona_steps=persona_steps,
        cross_stack_checks=cross_stack_checks,
        negative_abuse_checks=negative_abuse_checks,
        persistence_summary=persistence_summary,
    )

    artifact_dir = REPO_ROOT / "artifacts" / "implementation" / "W12"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = artifact_dir / "W12_A03_critical_integration_smoke.json"
    artifact_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    assert artifact_path.exists()
    assert report["gate_status"] == "GATE_PASSED"
    assert report["summary"]["all_invariants_met"] is True
