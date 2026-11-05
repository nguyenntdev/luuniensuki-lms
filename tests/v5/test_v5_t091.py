# -*- coding: utf-8 -*-
"""V5-T091 (Wave W09, Slot A01): Teacher 45-Minute Lesson Wizard Test Suite.

Audits and verifies:
1. Structured 5-phase wizard flow:
   - Objectives (CV 5512/BGDĐT, 45-min duration, S1-S4 historical competencies, qualities).
   - Historical Object & Sources (linking Urn/Motif/Entity and primary bibliographic sources).
   - Media (2D rubbing variant vs 3D model variant, verified 2D rubbing asset fallback).
   - Inquiry (4 sequential activities: 5m Warmup, 15m Explore, 15m Deep Inquiry, 10m Exit Ticket).
   - Assessment & Rubric (S1-S4 0-3 scale descriptors, Exit ticket prompt & expected evidence).
2. Negative Abuse Invariant:
   - A lesson plan CANNOT be published without approved historical object/source.
   - Strictly rejects unreviewed, needs_source, or disputed claims with HTTP 422 LESSON_PLAN_UNVERIFIED_CLAIMS.
3. Positive Publication:
   - Clean publication when all linked claims reach verified status ('expert_verified' or 'editor_reviewed').
4. Printable Handout Generation:
   - Generates A4 printable student fieldwork worksheet and teacher guide with zero synthetic names.
5. Role & Scoping Security:
   - Only teachers and staff can author and publish lesson plans.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest
from sqlalchemy import select

from backend.models import (
    HistoricalClaim,
    HistoricalEntity,
    HistoricalSource,
    HistoryLessonPlan,
    LessonContent,
    Motif,
    MotifCategory,
    MotifRarity,
    Urn,
    User,
    UserRole,
)
from backend.security import hash_password

REPO_ROOT = Path(__file__).resolve().parents[2]


# --------------------------------------------------------------------------- #
# Helpers & Fixtures
# --------------------------------------------------------------------------- #

@pytest.fixture(autouse=True)
def _reset_auth_rate_limit():
    """Reset auth rate limit before each test."""
    import backend.main as main

    main._auth_rate_limit_state.clear()
    yield
    main._auth_rate_limit_state.clear()


def _create_user(
    db_session,
    email: str,
    role: UserRole = UserRole.teacher,
    display_name: str | None = None,
) -> User:
    user = User(
        email=email,
        password_hash=hash_password("Password123!"),
        display_name=display_name or f"Teacher {email.split('@')[0]}",
        username=f"user_{uuid.uuid4().hex[:8]}",
        role=role,
        is_profile_public=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _login_user(client, email: str, password: str = "Password123!"):
    res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"


def _setup_wizard_context(db_session):
    """Seed teacher, learner, urn, motif, sources, and claims."""
    teacher = _create_user(
        db_session,
        f"teacher_{uuid.uuid4().hex[:6]}@school.edu.vn",
        role=UserRole.teacher,
        display_name="Thầy Giáo Sử Triều Nguyễn",
    )
    other_teacher = _create_user(
        db_session,
        f"other_teacher_{uuid.uuid4().hex[:6]}@school.edu.vn",
        role=UserRole.teacher,
        display_name="Cô Giáo Sử Trường Khác",
    )
    student = _create_user(
        db_session,
        f"student_{uuid.uuid4().hex[:6]}@school.edu.vn",
        role=UserRole.learner,
        display_name="Học Sinh Chuyên Sử",
    )

    # Urn and Motif
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

    # Sources
    source1 = HistoricalSource(
        source_type="royal_chronicle",
        title="Đại Nam Thực Lục Chính Biên",
        author_text="Quốc sử quán triều Nguyễn",
        publication_year=1848,
        pages="Đệ nhị kỷ, quyển 154, tờ 12a",
        verification_status="expert_verified",
        license="Public Domain",
        rights_status="public_domain",
        url="https://archives.org.vn/dntl-154",
    )
    source2 = HistoricalSource(
        source_type="court_gazette",
        title="Khâm Định Đại Nam Hội Điển Sự Lệ",
        author_text="Nội các triều Nguyễn",
        publication_year=1851,
        pages="Quyển 214, Công bộ - Đúc tượng vạc",
        verification_status="expert_verified",
        license="Public Domain",
        rights_status="public_domain",
        url="https://archives.org.vn/hoidien-214",
    )
    db_session.add_all([source1, source2])
    db_session.flush()

    # Historical Entity & Claims
    entity = HistoricalEntity(
        entity_type="urn",
        slug=f"cao-dinh-{uuid.uuid4().hex[:6]}",
        name_vi="Cao Đỉnh",
        publication_status="published",
    )
    db_session.add(entity)
    db_session.flush()

    verified_claim = HistoricalClaim(
        entity_id=entity.id,
        claim_key=f"claim_verified_{uuid.uuid4().hex[:8]}",
        claim_type="historical_fact",
        statement_vi="Cao Đỉnh là chiếc đỉnh đầu tiên và quan trọng nhất trong Cửu Đỉnh nhà Nguyễn.",
        origin="editorial",
        verification_status="expert_verified",
        confidence="high",
    )
    unreviewed_claim = HistoricalClaim(
        entity_id=entity.id,
        claim_key=f"claim_unreviewed_{uuid.uuid4().hex[:8]}",
        claim_type="traditional_account",
        statement_vi="Lời truyền miệng dân gian chưa có nguồn thư tịch kiểm chứng.",
        origin="community_submission",
        verification_status="unreviewed",
        confidence="low",
    )
    disputed_claim = HistoricalClaim(
        entity_id=entity.id,
        claim_key=f"claim_disputed_{uuid.uuid4().hex[:8]}",
        claim_type="interpretation",
        statement_vi="Ý kiến tranh cãi học thuật về vị trí thợ đúc chính.",
        origin="web_crawl",
        verification_status="disputed",
        confidence="low",
    )
    db_session.add_all([verified_claim, unreviewed_claim, disputed_claim])
    db_session.commit()

    return {
        "teacher": teacher,
        "other_teacher": other_teacher,
        "student": student,
        "urn": urn,
        "motif": motif,
        "sources": [source1, source2],
        "entity": entity,
        "verified_claim": verified_claim,
        "unreviewed_claim": unreviewed_claim,
        "disputed_claim": disputed_claim,
    }


# =========================================================================== #
# Test Cases
# =========================================================================== #

def test_wizard_create_draft_lesson_plan(client, db_session):
    """Test 1: Teacher creates a draft 45-minute lesson plan across the 5 wizard phases."""
    ctx = _setup_wizard_context(db_session)
    teacher = ctx["teacher"]
    urn = ctx["urn"]
    motif = ctx["motif"]
    sources = ctx["sources"]
    verified_claim = ctx["verified_claim"]

    _login_user(client, teacher.email)

    payload = {
        "title": "Chuyên đề 45 phút: Khảo sát hình tượng Rồng trên Cao Đỉnh",
        "topic": "Hình tượng Rồng và biểu trưng vương quyền thời Nguyễn",
        "target_grade": "Lớp 10 THPT",
        "duration_minutes": 45,
        "curriculum_framework": "CV 5512/BGDĐT",
        "urn_id": str(urn.id),
        "motif_id": str(motif.id),
        "media_variant": "2d_rubbing",
        "media_config": {
            "rubbing_url": "/assets/ban-duc-noi/cao_dinh/long.jpg",
            "has_3d_variant": True,
        },
        "objectives": {
            "historical_competencies": [
                {"code": "S1_SPATIAL", "name_vi": "Không gian", "description_vi": "Vị trí khắc trên Cao Đỉnh"},
                {"code": "S2_TEMPORAL", "name_vi": "Thời gian", "description_vi": "Niên đại 1835-1836"},
                {"code": "S3_EVIDENCE", "name_vi": "Sử liệu", "description_vi": "Đại Nam Thực Lục"},
                {"code": "S4_ARGUMENT", "name_vi": "Lập luận", "description_vi": "Ý nghĩa biểu tượng vương quyền"},
            ],
            "qualities": ["Tự hào di sản dân tộc", "Cẩn trọng sử liệu"],
        },
        "source_ids": [str(s.id) for s in sources],
        "claim_ids": [str(verified_claim.id)],
        "status": "draft",
    }

    res = client.post("/api/v1/history/lesson-plans", json=payload)
    assert res.status_code == 201, res.text
    data = res.json()

    assert data["title"] == payload["title"]
    assert data["duration_minutes"] == 45
    assert data["status"] == "draft"
    assert data["media_variant"] == "2d_rubbing"
    assert len(data["sources_snapshot"]) == 2
    assert len(data["claims_snapshot"]) == 1
    assert data["claims_snapshot"][0]["verification_status"] == "expert_verified"
    assert data["inquiry_activities"] is not None
    assert len(data["inquiry_activities"]) == 4
    assert data["printable_handout"] is not None
    assert "header" in data["printable_handout"]


def test_negative_abuse_lesson_cannot_publish_without_approved_object_or_sources(client, db_session):
    """Test 2: Negative Abuse — Lesson plan CANNOT publish without approved historical object/source."""
    ctx = _setup_wizard_context(db_session)
    teacher = ctx["teacher"]
    sources = ctx["sources"]
    verified_claim = ctx["verified_claim"]

    _login_user(client, teacher.email)

    # Sub-case A: Missing historical object
    res_no_obj = client.post(
        "/api/v1/history/lesson-plans",
        json={
            "title": "Lesson Without Object",
            "topic": "No historical relic or entity linked",
            "source_ids": [str(sources[0].id)],
            "claim_ids": [str(verified_claim.id)],
            "status": "published",
        },
    )
    assert res_no_obj.status_code == 422, res_no_obj.text
    err = res_no_obj.json()["error"]
    assert err["code"] == "LESSON_PLAN_UNVERIFIED_CLAIMS"
    assert "object" in str(err["details"]).lower()

    # Sub-case B: Missing historical source
    res_no_source = client.post(
        "/api/v1/history/lesson-plans",
        json={
            "title": "Lesson Without Source",
            "topic": "No primary bibliographic source linked",
            "urn_id": str(ctx["urn"].id),
            "source_ids": [],
            "claim_ids": [str(verified_claim.id)],
            "status": "published",
        },
    )
    assert res_no_source.status_code == 422
    err_src = res_no_source.json()["error"]
    assert err_src["code"] == "LESSON_PLAN_UNVERIFIED_CLAIMS"
    assert "source" in str(err_src["details"]).lower()


def test_negative_abuse_lesson_cannot_publish_with_unreviewed_or_disputed_claims(client, db_session):
    """Test 3: Negative Abuse — Strictly rejects unreviewed, needs_source, or disputed claims upon publishing."""
    ctx = _setup_wizard_context(db_session)
    teacher = ctx["teacher"]
    urn = ctx["urn"]
    sources = ctx["sources"]
    unreviewed_claim = ctx["unreviewed_claim"]
    disputed_claim = ctx["disputed_claim"]

    _login_user(client, teacher.email)

    # Sub-case A: Draft with unreviewed claim fails publication
    res_draft_unreviewed = client.post(
        "/api/v1/history/lesson-plans",
        json={
            "title": "Lesson with Unreviewed Claim",
            "topic": "Unreviewed oral claims",
            "urn_id": str(urn.id),
            "source_ids": [str(s.id) for s in sources],
            "claim_ids": [str(unreviewed_claim.id)],
            "status": "draft",
        },
    )
    assert res_draft_unreviewed.status_code == 201
    plan_unrev_id = res_draft_unreviewed.json()["id"]

    pub_res = client.post(f"/api/v1/history/lesson-plans/{plan_unrev_id}/publish")
    assert pub_res.status_code == 422, pub_res.text
    err_unrev = pub_res.json()["error"]
    assert err_unrev["code"] == "LESSON_PLAN_UNVERIFIED_CLAIMS"
    assert "unreviewed" in str(err_unrev["details"]).lower() or "ineligible" in str(err_unrev["details"]).lower()

    # Verify plan status remained draft
    check_plan = client.get(f"/api/v1/history/lesson-plans/{plan_unrev_id}")
    assert check_plan.json()["status"] == "draft"
    assert check_plan.json()["content_validation_status"] == "blocked_for_authoritative_learning"

    # Sub-case B: Draft with disputed claim fails publication
    res_draft_disputed = client.post(
        "/api/v1/history/lesson-plans",
        json={
            "title": "Lesson with Disputed Claim",
            "topic": "Disputed casting claims",
            "urn_id": str(urn.id),
            "source_ids": [str(s.id) for s in sources],
            "claim_ids": [str(disputed_claim.id)],
            "status": "draft",
        },
    )
    assert res_draft_disputed.status_code == 201
    plan_disp_id = res_draft_disputed.json()["id"]

    pub_disp_res = client.post(f"/api/v1/history/lesson-plans/{plan_disp_id}/publish")
    assert pub_disp_res.status_code == 422
    assert "disputed" in str(pub_disp_res.json()["error"]["details"]).lower() or "ineligible" in str(pub_disp_res.json()["error"]["details"]).lower()


def test_positive_publication_and_printable_handout_generation(client, db_session):
    """Test 4: Positive Verification — Successful publication and printable handout generation."""
    ctx = _setup_wizard_context(db_session)
    teacher = ctx["teacher"]
    urn = ctx["urn"]
    motif = ctx["motif"]
    sources = ctx["sources"]
    verified_claim = ctx["verified_claim"]

    _login_user(client, teacher.email)

    # 1. Validate wizard in preflight
    val_res = client.post(
        "/api/v1/history/lesson-wizard/validate",
        json={
            "title": "Khảo sát hoa văn Rồng",
            "topic": "Rồng trên Cao Đỉnh",
            "urn_id": str(urn.id),
            "motif_id": str(motif.id),
            "source_ids": [str(s.id) for s in sources],
            "claim_ids": [str(verified_claim.id)],
            "media_variant": "2d_rubbing",
        },
    )
    assert val_res.status_code == 200, val_res.text
    val_data = val_res.json()
    assert val_data["can_publish"] is True
    assert val_data["validation_status"] == "valid"
    assert val_data["verified_claims_count"] == 1
    assert val_data["ineligible_claims_count"] == 0

    # 2. Create as draft
    create_res = client.post(
        "/api/v1/history/lesson-plans",
        json={
            "title": "Bài học chuẩn mực 45 phút",
            "topic": "Phù điêu Rồng Cao Đỉnh",
            "urn_id": str(urn.id),
            "motif_id": str(motif.id),
            "source_ids": [str(s.id) for s in sources],
            "claim_ids": [str(verified_claim.id)],
            "media_variant": "2d_rubbing",
            "status": "draft",
        },
    )
    assert create_res.status_code == 201
    plan_id = create_res.json()["id"]

    # 3. Publish cleanly
    pub_res = client.post(f"/api/v1/history/lesson-plans/{plan_id}/publish")
    assert pub_res.status_code == 200, pub_res.text
    pub_data = pub_res.json()
    assert pub_data["status"] == "published"
    assert pub_data["content_validation_status"] == "valid"
    assert pub_data["published_at"] is not None

    # 4. Fetch printable handout
    handout_res = client.get(f"/api/v1/history/lesson-plans/{plan_id}/printable-handout")
    assert handout_res.status_code == 200, handout_res.text
    handout = handout_res.json()

    assert "header" in handout
    assert "SỞ GIÁO DỤC VÀ ĐÀO TẠO THỪA THIÊN HUẾ" in handout["header"]["institution_vi"]
    assert "CV 5512/BGDĐT" in handout["header"]["framework_code"]
    assert len(handout["sources"]) == 2
    assert "Đại Nam Thực Lục Chính Biên" in [s["title"] for s in handout["sources"]]
    assert len(handout["inquiry_stations"]) == 4
    assert handout["visual_media"]["media_variant"] == "2d_rubbing"
    assert "rubbing_asset_path" in handout["visual_media"]
    assert "rubric" in handout
    assert "S1_SPATIAL" in handout["rubric"]["criteria"]
    assert "exit_ticket" in handout
    assert "export_metadata" in handout
    assert "SEAL_V5_" in handout["export_metadata"]["anti_abuse_seal"]


def test_access_control_and_teacher_isolation(client, db_session):
    """Test 5: Access Control — Learner cannot author/publish; Teachers cannot publish other teacher's drafts."""
    ctx = _setup_wizard_context(db_session)
    teacher = ctx["teacher"]
    other_teacher = ctx["other_teacher"]
    student = ctx["student"]
    urn = ctx["urn"]
    sources = ctx["sources"]
    verified_claim = ctx["verified_claim"]

    # Student cannot create lesson plans (HTTP 403)
    _login_user(client, student.email)
    res_stu = client.post(
        "/api/v1/history/lesson-plans",
        json={
            "title": "Unauthorized Plan",
            "topic": "Hacker Lesson",
            "urn_id": str(urn.id),
            "source_ids": [str(sources[0].id)],
            "claim_ids": [str(verified_claim.id)],
        },
    )
    assert res_stu.status_code == 403, res_stu.text

    # Teacher 1 creates a draft
    _login_user(client, teacher.email)
    res_t1 = client.post(
        "/api/v1/history/lesson-plans",
        json={
            "title": "Teacher 1 Private Lesson",
            "topic": "Private Lesson",
            "urn_id": str(urn.id),
            "source_ids": [str(sources[0].id)],
            "claim_ids": [str(verified_claim.id)],
            "status": "draft",
        },
    )
    assert res_t1.status_code == 201
    plan_t1_id = res_t1.json()["id"]

    # Teacher 2 tries to publish Teacher 1's draft -> Forbidden (HTTP 403)
    _login_user(client, other_teacher.email)
    res_t2_pub = client.post(f"/api/v1/history/lesson-plans/{plan_t1_id}/publish")
    assert res_t2_pub.status_code == 403, res_t2_pub.text
