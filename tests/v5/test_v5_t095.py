# -*- coding: utf-8 -*-
"""V5-T095 (Wave W09, Slot A05): Curriculum competency catalog & teacher editing/flagging.

Verifies:
1. Standard historical competencies under Vietnam 2018 General Education Program (GDPT 2018):
   - Historical Literacy (Tìm hiểu lịch sử)
   - Source Criticism & Epistemic Reasoning (Khảo chứng tư liệu)
   - Historical Empathy & Perspective Taking (Đồng cảm lịch sử)
   - Historical Communication & Argumentation (Giao tiếp lịch sử)
   - Framework VN_GDPT_2018 with descriptors across grade bands (Grades 6–12).
2. Relic mappings to real relics (Cửu Đỉnh 9 Urns and 162 Motifs, historical entities).
3. Review warning invariant:
   - Unreviewed mappings strictly surface review warning banners.
4. Teacher editable workflow:
   - Teachers can create and edit competency mappings with grade range validation (6–12).
5. Negative abuse defense:
   - Non-teacher users (learners, guests) are strictly blocked with HTTP 403 from creating/editing mappings.
   - Out-of-range grades (<6, >12, or min > max) are rejected with HTTP 422.
   - Non-teacher users are blocked with HTTP 403 from flagging mappings.
   - Invalid flag reasons or empty commentary are rejected with HTTP 422.
6. Teacher flagging of inaccurate competency mappings:
   - Inaccurate mappings are flagged with structured reasons and comments.
   - Mapping status immediately transitions to 'flagged' and review warning surfaces the reason.
   - Admins/staff can resolve flags and verify mappings, clearing review warnings.
"""
from __future__ import annotations

import uuid
from typing import Any, Dict

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.history_models import (
    CompetencyFlagReason,
    CompetencyGradeBand,
    CompetencyMappingStatus,
    CurriculumCompetency,
    CurriculumCompetencyFlag,
    CurriculumCompetencyRelicMapping,
    StandardCompetencyDomain,
)
from backend.models import User, UserRole
from backend.security import hash_password
from backend.services import curriculum_competency as cc_svc


# --------------------------------------------------------------------------- #
# Helpers & Fixtures
# --------------------------------------------------------------------------- #

def _create_user(
    db_session: Session,
    email: str,
    role: UserRole = UserRole.learner,
    display_name: str | None = None,
) -> User:
    """Create and return a user with a specific role."""
    existing = db_session.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if existing:
        return existing
    user = User(
        email=email,
        password_hash=hash_password("Password123!"),
        display_name=display_name or f"User {email.split('@')[0]}",
        username=f"u_{uuid.uuid4().hex[:8]}",
        role=role,
        is_profile_public=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _auth_headers(client: TestClient, email: str, password: str = "Password123!") -> dict[str, str]:
    """Log in and return Authorization Bearer headers."""
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    token = res.headers.get("X-Access-Token") or client.cookies.get("luuniensuki_access")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=True)
def _reset_auth_rate_limit():
    """Reset auth rate limit before each test."""
    import backend.main as main

    if hasattr(main, "_auth_rate_limit_state"):
        main._auth_rate_limit_state.clear()
    yield
    if hasattr(main, "_auth_rate_limit_state"):
        main._auth_rate_limit_state.clear()


@pytest.fixture(autouse=True)
def _seed_competencies(db_session: Session):
    """Seed standard competencies and mappings into db_session for each test."""
    cc_svc.ensure_default_competencies(db_session)


# --------------------------------------------------------------------------- #
# Test 1: Standard Historical Competencies Catalog (VN GDPT 2018)
# --------------------------------------------------------------------------- #

def test_curriculum_competencies_standard_gdpt_2018_catalog(client: TestClient, db_session: Session):
    """Verifies that all 4 standard competencies under Vietnam 2018 General Education Program exist."""
    res = client.get("/api/v1/history/curriculum/competencies")
    assert res.status_code == 200, res.text
    data = res.json()

    assert "items" in data
    assert data["total"] >= 4

    codes = {item["code"] for item in data["items"]}
    expected_codes = {
        "COMP_HIST_LITERACY",
        "COMP_SOURCE_CRITICISM",
        "COMP_HIST_EMPATHY",
        "COMP_HIST_COMMUNICATION",
    }
    assert expected_codes.issubset(codes), f"Missing standard competencies: {expected_codes - codes}"

    # Verify Vietnam 2018 framework and grade band descriptors
    for comp in data["items"]:
        assert comp["standard_framework"] == "VN_GDPT_2018"
        assert comp["name_vi"]
        assert comp["name_en"]
        assert comp["description_vi"]
        descriptors = comp["grade_band_descriptors"]
        assert "GRADE_6_7" in descriptors
        assert "GRADE_8_9" in descriptors
        assert "GRADE_10_12" in descriptors
        assert descriptors["GRADE_6_7"]["min_grade"] == 6
        assert descriptors["GRADE_10_12"]["max_grade"] == 12

    # Verify single fetch by code
    res_single = client.get("/api/v1/history/curriculum/competencies/COMP_HIST_LITERACY")
    assert res_single.status_code == 200
    comp_single = res_single.json()
    assert comp_single["domain"] == "historical_literacy"
    assert "Tìm hiểu Lịch sử" in comp_single["name_vi"]


# --------------------------------------------------------------------------- #
# Test 2: Relic Mappings Across Real Relics and Grade Bands (Grades 6–12)
# --------------------------------------------------------------------------- #

def test_curriculum_competency_mappings_real_relics_and_grade_filters(client: TestClient, db_session: Session):
    """Verifies competency mappings link to real relics (Cao Đỉnh, Nhân Đỉnh, etc.) and support grade filtering."""
    res = client.get("/api/v1/history/curriculum/competencies/mappings")
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["total"] >= 4

    # Verify mappings reference authentic relics
    relic_slugs = {m["relic_urn_slug"] for m in data["items"] if m.get("relic_urn_slug")}
    assert "cao-dinh" in relic_slugs
    assert "nhan-dinh" in relic_slugs

    # Filter by grade 7 (THCS)
    res_g7 = client.get("/api/v1/history/curriculum/competencies/mappings?grade=7")
    assert res_g7.status_code == 200
    for m in res_g7.json()["items"]:
        assert m["min_grade"] <= 7 <= m["max_grade"]

    # Filter by grade 11 (THPT)
    res_g11 = client.get("/api/v1/history/curriculum/competencies/mappings?grade=11")
    assert res_g11.status_code == 200
    for m in res_g11.json()["items"]:
        assert m["min_grade"] <= 11 <= m["max_grade"]

    # Filter by relic urn slug
    res_cao = client.get("/api/v1/history/curriculum/competencies/mappings?urn_slug=cao-dinh")
    assert res_cao.status_code == 200
    assert len(res_cao.json()["items"]) >= 1
    for m in res_cao.json()["items"]:
        assert m["relic_urn_slug"] == "cao-dinh"


# --------------------------------------------------------------------------- #
# Test 3: Review Warning Invariant on Unreviewed Mappings
# --------------------------------------------------------------------------- #

def test_unreviewed_mappings_display_review_warnings(client: TestClient, db_session: Session):
    """Verifies that unreviewed mappings strictly surface review warning banners."""
    res = client.get("/api/v1/history/curriculum/competencies/mappings?status=unreviewed")
    assert res.status_code == 200
    items = res.json()["items"]
    assert len(items) >= 1

    for unreviewed in items:
        assert unreviewed["is_reviewed"] is False
        assert unreviewed["status"] == "unreviewed"
        assert unreviewed["review_warning"] is not None
        assert "Cảnh báo" in unreviewed["review_warning"]
        assert "thẩm định" in unreviewed["review_warning"]

        # Also verify single item endpoint returns the warning
        res_single = client.get(f"/api/v1/history/curriculum/competencies/mappings/{unreviewed['id']}")
        assert res_single.status_code == 200
        single_data = res_single.json()
        assert single_data["review_warning"] == unreviewed["review_warning"]


# --------------------------------------------------------------------------- #
# Test 4: Teacher Editable Workflow (Create & Edit Mapping)
# --------------------------------------------------------------------------- #

def test_teacher_can_create_and_edit_competency_mapping(client: TestClient, db_session: Session):
    """Verifies that a teacher can create a new mapping and edit it, maintaining unreviewed warning."""
    teacher = _create_user(db_session, "teacher_t095_1@example.com", role=UserRole.teacher)
    headers = _auth_headers(client, teacher.email)

    # Fetch competency ID for COMP_HIST_EMPATHY
    comp = db_session.execute(
        select(CurriculumCompetency).where(CurriculumCompetency.code == "COMP_HIST_EMPATHY")
    ).scalar_one()

    # 1. Teacher creates new mapping
    payload = {
        "competency_id": str(comp.id),
        "relic_urn_slug": "anh-dinh",
        "relic_motif_id": "urn_anh_dinh_01",
        "entity_slug": "anh-dinh",
        "grade_band": "GRADE_8_9",
        "min_grade": 8,
        "max_grade": 9,
        "learning_activity_vi": "Khảo cứu tinh thần thượng võ và kỹ thuật chạm khắc binh khí thời Nguyễn trên Anh Đỉnh.",
        "learning_activity_en": "Examine martial spirit and weapon engraving techniques on Anh Đỉnh.",
        "evidence_requirement_vi": "Học sinh đối chiếu các bản vẽ vũ khí trong Khâm Định Đại Nam Hội Điển Sự Lệ.",
        "evidence_requirement_en": "Students cross-reference weapon blueprints in imperial statutes.",
    }

    create_res = client.post("/api/v1/history/curriculum/competencies/mappings", json=payload, headers=headers)
    assert create_res.status_code == 201, create_res.text
    created = create_res.json()

    assert created["relic_urn_slug"] == "anh-dinh"
    assert created["min_grade"] == 8
    assert created["max_grade"] == 9
    assert created["is_reviewed"] is False
    assert created["status"] == "unreviewed"
    assert created["review_warning"] is not None

    mapping_id = created["id"]

    # 2. Teacher updates the mapping
    update_payload = {
        "learning_activity_vi": "Khảo cứu nâng cao tinh thần thượng võ và so sánh với thư tịch Nội Các triều Nguyễn.",
        "min_grade": 9,
        "max_grade": 10,
        "grade_band": "GRADE_8_9",
    }
    update_res = client.put(
        f"/api/v1/history/curriculum/competencies/mappings/{mapping_id}",
        json=update_payload,
        headers=headers,
    )
    assert update_res.status_code == 200, update_res.text
    updated = update_res.json()
    assert updated["min_grade"] == 9
    assert updated["max_grade"] == 10
    assert "nâng cao" in updated["learning_activity_vi"]
    assert updated["is_reviewed"] is False


# --------------------------------------------------------------------------- #
# Test 5: Negative Abuse — Non-Teacher Cannot Create or Edit Mappings
# --------------------------------------------------------------------------- #

def test_negative_abuse_learner_or_guest_cannot_mutate_mappings(client: TestClient, db_session: Session):
    """Verifies that non-teacher users (learner, guest, unauthenticated) are rejected with 403 or 401."""
    learner = _create_user(db_session, "learner_t095@example.com", role=UserRole.learner)
    learner_headers = _auth_headers(client, learner.email)

    comp = db_session.execute(select(CurriculumCompetency)).scalars().first()
    assert comp is not None

    payload = {
        "competency_id": str(comp.id),
        "relic_urn_slug": "du-dinh",
        "min_grade": 6,
        "max_grade": 7,
        "learning_activity_vi": "Học sinh tự tạo hoạt động tùy tiện",
        "evidence_requirement_vi": "Không có chứng cứ",
    }

    # 1. Learner attempts create -> 403 Forbidden
    res_learner = client.post("/api/v1/history/curriculum/competencies/mappings", json=payload, headers=learner_headers)
    assert res_learner.status_code == 403, res_learner.text
    assert res_learner.json()["error"]["code"] == "FORBIDDEN_TEACHER_ACTION"

    # 2. Unauthenticated client attempts create -> 401 Unauthorized
    client.cookies.clear()
    res_anon = client.post("/api/v1/history/curriculum/competencies/mappings", json=payload)
    assert res_anon.status_code == 401

    # 3. Learner attempts update on an existing mapping -> 403 Forbidden
    mapping = db_session.execute(select(CurriculumCompetencyRelicMapping)).scalars().first()
    assert mapping is not None
    res_update = client.put(
        f"/api/v1/history/curriculum/competencies/mappings/{mapping.id}",
        json={"learning_activity_vi": "Thay đổi trái phép"},
        headers=learner_headers,
    )
    assert res_update.status_code == 403
    assert res_update.json()["error"]["code"] == "FORBIDDEN_TEACHER_ACTION"


# --------------------------------------------------------------------------- #
# Test 6: Negative Abuse — Invalid Grade Bounds Validation (Grades 6–12)
# --------------------------------------------------------------------------- #

def test_negative_abuse_invalid_grade_range_rejected(client: TestClient, db_session: Session):
    """Verifies that grade levels outside Grades 6–12 or min > max are strictly rejected with 422."""
    teacher = _create_user(db_session, "teacher_t095_grades@example.com", role=UserRole.teacher)
    headers = _auth_headers(client, teacher.email)
    comp = db_session.execute(select(CurriculumCompetency)).scalars().first()

    # Case A: Grade too low (grade 5 - primary school)
    payload_low = {
        "competency_id": str(comp.id),
        "relic_urn_slug": "cao-dinh",
        "min_grade": 5,
        "max_grade": 8,
        "learning_activity_vi": "Hoạt động lớp 5",
        "evidence_requirement_vi": "Chứng cứ lịch sử",
    }
    res_low = client.post("/api/v1/history/curriculum/competencies/mappings", json=payload_low, headers=headers)
    assert res_low.status_code == 422, res_low.text

    # Case B: Grade too high (grade 13 - tertiary)
    payload_high = {
        "competency_id": str(comp.id),
        "relic_urn_slug": "cao-dinh",
        "min_grade": 10,
        "max_grade": 13,
        "learning_activity_vi": "Hoạt động đại học",
        "evidence_requirement_vi": "Chứng cứ đại học",
    }
    res_high = client.post("/api/v1/history/curriculum/competencies/mappings", json=payload_high, headers=headers)
    assert res_high.status_code == 422, res_high.text

    # Case C: min_grade > max_grade
    payload_inverted = {
        "competency_id": str(comp.id),
        "relic_urn_slug": "cao-dinh",
        "min_grade": 11,
        "max_grade": 8,
        "learning_activity_vi": "Lớp đảo ngược",
        "evidence_requirement_vi": "Chứng cứ",
    }
    res_inverted = client.post("/api/v1/history/curriculum/competencies/mappings", json=payload_inverted, headers=headers)
    assert res_inverted.status_code == 422, res_inverted.text


# --------------------------------------------------------------------------- #
# Test 7: Teacher Flagging Inaccurate Competency Mappings
# --------------------------------------------------------------------------- #

def test_teacher_can_flag_inaccurate_competency_mapping(client: TestClient, db_session: Session):
    """Verifies teacher flagging flow: mapping status transitions to 'flagged' and surfaces warning."""
    teacher = _create_user(db_session, "teacher_flagger@example.com", role=UserRole.teacher)
    headers = _auth_headers(client, teacher.email)

    # Pick an existing mapping
    mapping = db_session.execute(select(CurriculumCompetencyRelicMapping)).scalars().first()
    assert mapping is not None

    flag_payload = {
        "reason": "inaccurate_grade_level",
        "commentary": "Họa tiết này đòi hỏi kiến thức chuyên sâu Lịch sử 11, không phù hợp cho học sinh lớp 6.",
        "suggested_correction": {"suggested_min_grade": 10, "suggested_max_grade": 12},
    }

    flag_res = client.post(
        f"/api/v1/history/curriculum/competencies/mappings/{mapping.id}/flag",
        json=flag_payload,
        headers=headers,
    )
    assert flag_res.status_code == 201, flag_res.text
    flag_data = flag_res.json()

    assert flag_data["reason"] == "inaccurate_grade_level"
    assert flag_data["status"] == "pending"
    assert flag_data["commentary"] == flag_payload["commentary"]

    # Verify that the mapping itself now has status='flagged' and active review warning
    get_res = client.get(f"/api/v1/history/curriculum/competencies/mappings/{mapping.id}")
    assert get_res.status_code == 200
    mapping_data = get_res.json()

    assert mapping_data["status"] == "flagged"
    assert mapping_data["is_reviewed"] is False
    assert mapping_data["flag_count"] >= 1
    assert "inaccurate_grade_level" in mapping_data["review_warning"]


# --------------------------------------------------------------------------- #
# Test 8: Negative Abuse — Non-Teacher Cannot Flag Mappings
# --------------------------------------------------------------------------- #

def test_negative_abuse_learner_or_guest_cannot_flag_mapping(client: TestClient, db_session: Session):
    """Verifies that learners or guests cannot flag mappings (403 Forbidden)."""
    learner = _create_user(db_session, "learner_hacker@example.com", role=UserRole.learner)
    learner_headers = _auth_headers(client, learner.email)

    mapping = db_session.execute(select(CurriculumCompetencyRelicMapping)).scalars().first()
    assert mapping is not None

    payload = {
        "reason": "inaccurate_grade_level",
        "commentary": "Học sinh cố tình gắn cờ lung tung",
    }

    res_learner = client.post(
        f"/api/v1/history/curriculum/competencies/mappings/{mapping.id}/flag",
        json=payload,
        headers=learner_headers,
    )
    assert res_learner.status_code == 403
    assert res_learner.json()["error"]["code"] == "FORBIDDEN_TEACHER_ACTION"

    # Guest user
    guest = _create_user(db_session, "guest_user@example.com", role=UserRole.guest)
    guest_headers = _auth_headers(client, guest.email)
    res_guest = client.post(
        f"/api/v1/history/curriculum/competencies/mappings/{mapping.id}/flag",
        json=payload,
        headers=guest_headers,
    )
    assert res_guest.status_code == 403


# --------------------------------------------------------------------------- #
# Test 9: Negative Abuse — Invalid Flag Parameters Rejected
# --------------------------------------------------------------------------- #

def test_negative_abuse_invalid_flag_parameters_rejected(client: TestClient, db_session: Session):
    """Verifies that invalid flag reasons or insufficient commentary length are rejected with 422."""
    teacher = _create_user(db_session, "teacher_validator@example.com", role=UserRole.teacher)
    headers = _auth_headers(client, teacher.email)
    mapping = db_session.execute(select(CurriculumCompetencyRelicMapping)).scalars().first()

    # Case A: Invalid reason
    res_reason = client.post(
        f"/api/v1/history/curriculum/competencies/mappings/{mapping.id}/flag",
        json={"reason": "bogus_unsupported_reason", "commentary": "Lý do không hợp lệ"},
        headers=headers,
    )
    assert res_reason.status_code == 422
    assert res_reason.json()["error"]["code"] == "INVALID_FLAG_REASON"

    # Case B: Commentary too short (< 5 chars)
    res_short = client.post(
        f"/api/v1/history/curriculum/competencies/mappings/{mapping.id}/flag",
        json={"reason": "pedagogical_concern", "commentary": "abc"},
        headers=headers,
    )
    assert res_short.status_code == 422


# --------------------------------------------------------------------------- #
# Test 10: Staff/Admin Flag Resolution & Mapping Verification
# --------------------------------------------------------------------------- #

def test_admin_resolves_flag_and_verifies_mapping(client: TestClient, db_session: Session):
    """Verifies that an administrator can resolve a flag and verify the mapping, clearing warnings."""
    teacher = _create_user(db_session, "teacher_flagger2@example.com", role=UserRole.teacher)
    teacher_headers = _auth_headers(client, teacher.email)

    admin = _create_user(db_session, "admin_t095@example.com", role=UserRole.admin)
    admin_headers = _auth_headers(client, admin.email)

    mapping = db_session.execute(select(CurriculumCompetencyRelicMapping)).scalars().first()
    assert mapping is not None

    # 1. Teacher flags mapping
    flag_res = client.post(
        f"/api/v1/history/curriculum/competencies/mappings/{mapping.id}/flag",
        json={"reason": "pedagogical_concern", "commentary": "Cần bổ sung nguồn thư tịch Đại Nam Thực Lục"},
        headers=teacher_headers,
    )
    assert flag_res.status_code == 201
    flag_id = flag_res.json()["id"]

    # 2. Teacher checks flags list
    flags_res = client.get(
        f"/api/v1/history/curriculum/competencies/mappings/{mapping.id}/flags",
        headers=teacher_headers,
    )
    assert flags_res.status_code == 200
    assert any(f["id"] == flag_id for f in flags_res.json())

    # 3. Admin resolves flag
    resolve_res = client.post(
        f"/api/v1/history/curriculum/competencies/flags/{flag_id}/resolve",
        json={
            "action": "resolved",
            "resolution_notes": "Đã đối chiếu bổ sung trích đoạn Đại Nam Thực Lục quyển 12 tờ 5.",
            "updated_mapping_status": "unreviewed",
        },
        headers=admin_headers,
    )
    assert resolve_res.status_code == 200
    assert resolve_res.json()["status"] == "resolved"

    # 4. Admin verifies the mapping (clearing review warnings)
    verify_res = client.post(
        f"/api/v1/history/curriculum/competencies/mappings/{mapping.id}/verify",
        headers=admin_headers,
    )
    assert verify_res.status_code == 200
    verified = verify_res.json()

    assert verified["is_reviewed"] is True
    assert verified["status"] == "verified"
    assert verified["review_warning"] is None
