# -*- coding: utf-8 -*-
"""V5-T029 (Wave W02, Slot A09): Source-guided curriculum mapping & publishing gate.

Audits and verifies:
1. Source-guided curriculum mapping in backend/services/history_learning.py and
   backend/routers/history_learning.py:
   - Curriculum objectives map directly to verified historical entities and
     source-backed claims.
   - Objectives define historical competencies: S1_SPATIAL, S2_TEMPORAL,
     S3_EVIDENCE, S4_ARGUMENT.
   - Includes 2D rubbing asset fallback for low-bandwidth educational environments.
2. Publishing gate invariant (Spec 32.2 / V5-T029):
   - A learning module or lesson CANNOT be published if its core required
     historical claims are unreviewed, disputed, or rejected.
   - Setting content_validation_status='blocked_for_authoritative_learning' and
     rejecting publication with HTTP 422 LESSON_UNVERIFIED_CLAIMS.
   - Authoritative publication is unlocked only when all backing claims reach
     verified status ('expert_verified' or 'editor_reviewed').
3. 2D rubbing fallback integrity:
   - Every curriculum module has a verifiable 2D rubbing asset fallback on disk.
   - High-resolution rubbing files in ban-duc-noi/ are confirmed accessible.
4. Frontend learn page and modules contract:
   - frontend/src/lib/rbpc/learnModules.ts defines 2D rubbing fallbacks and
     curriculum competency mappings.
   - frontend/src/app/learn/page.tsx renders 2D fallback button and verified
     evidence indicators for low-bandwidth classrooms.
"""
from __future__ import annotations

import json
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select

from backend.models import (
    ContentStatus,
    HistoricalClaim,
    HistoricalEntity,
    HistoricalSource,
    LessonContent,
    Motif,
    MotifCategory,
    MotifRarity,
    QuizQuestion,
    Urn,
    User,
    UserRole,
)
from backend.services import history_learning as hl

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


def _make_user(client, db_session, email, display_name, role=UserRole.admin):
    res = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "display_name": display_name},
    )
    assert res.status_code == 201, res.text
    user = db_session.execute(select(User).where(User.email == email)).scalar_one()
    user.role = role
    db_session.commit()
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "password123"},
    )
    assert login_res.status_code == 200, login_res.text
    return user


def _seed_urn_and_motif(db_session, urn_name="Cao Đỉnh", mesh_name=None):
    mesh = mesh_name or f"mesh_motif_{uuid4().hex[:8]}"
    urn_slug = f"urn-{uuid4().hex[:8]}"
    urn = Urn(
        slug=urn_slug,
        name=urn_name,
        model_url=f"/models/{urn_slug}.glb",
        display_order=1,
    )
    db_session.add(urn)
    db_session.flush()

    motif = Motif(
        urn_id=urn.id,
        mesh_name=mesh,
        name="Hổ",
        name_en="Tiger",
        category=MotifCategory.dong_vat,
        rarity=MotifRarity.common,
        pos_x=0.0,
        pos_y=0.0,
        pos_z=0.0,
        bounding_radius=1.0,
    )
    db_session.add(motif)
    db_session.flush()
    return urn, motif


def _seed_historical_entity(db_session, slug="cao-dinh", name_vi="Cao Đỉnh"):
    entity = db_session.scalar(
        select(HistoricalEntity).where(HistoricalEntity.slug == slug)
    )
    if not entity:
        entity = HistoricalEntity(
            entity_type="urn",
            slug=slug,
            name_vi=name_vi,
            publication_status="verified",
        )
        db_session.add(entity)
        db_session.flush()
    return entity


def _seed_historical_claim(
    db_session,
    entity_id: UUID,
    claim_key: str,
    verification_status: str = "expert_verified",
    statement_vi: str = "Tuyên bố lịch sử đã kiểm chứng.",
):
    claim = db_session.scalar(
        select(HistoricalClaim).where(HistoricalClaim.claim_key == claim_key)
    )
    if not claim:
        claim = HistoricalClaim(
            entity_id=entity_id,
            claim_key=claim_key,
            claim_type="factual",
            statement_vi=statement_vi,
            verification_status=verification_status,
            origin="editorial",
            risk_level="normal",
        )
        db_session.add(claim)
    else:
        claim.verification_status = verification_status
    db_session.flush()
    return claim


# =========================================================================== #
# Test 1: Curriculum objectives link to verified historical entities & claims
# =========================================================================== #
def test_curriculum_objectives_link_to_verified_historical_claims(client, db_session):
    """Test that curriculum learning modules map objectives to verified historical entities and claims."""
    # 1. Fetch modules via API
    res = client.get("/api/v1/history/curriculum/modules")
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["total"] >= 4
    modules = data["items"]

    # Verify key modules exist
    slugs = {m["slug"] for m in modules}
    assert "giai-ma-18-ban-duc-cao-dinh" in slugs
    assert "ky-thuat-duc-rong-thuan-dinh" in slugs
    assert "kham-dinh-dai-nam-hoi-dien" in slugs

    # 2. Inspect Cao Đỉnh curriculum module
    cao_res = client.get("/api/v1/history/curriculum/modules/giai-ma-18-ban-duc-cao-dinh")
    assert cao_res.status_code == 200, cao_res.text
    cao_mod = cao_res.json()

    assert cao_mod["era"] == "Triều Minh Mạng (1835–1837)"
    assert "2018" in cao_mod["curriculum_framework"]
    assert set(cao_mod["historical_competencies"]) == {
        "S1_SPATIAL",
        "S2_TEMPORAL",
        "S3_EVIDENCE",
        "S4_ARGUMENT",
    }

    objectives = cao_mod["learning_objectives"]
    assert len(objectives) >= 4
    competencies_found = {obj["competency"] for obj in objectives}
    assert competencies_found == {"S1_SPATIAL", "S2_TEMPORAL", "S3_EVIDENCE", "S4_ARGUMENT"}

    for obj in objectives:
        assert obj["code"].startswith("OBJ-CAO-DINH")
        assert obj["target_entity_slug"] == "cao-dinh"
        assert len(obj["target_claim_keys"]) > 0

    # 3. Seed historical entities and claims in DB to test live DB verification
    entity = _seed_historical_entity(db_session, slug="cao-dinh", name_vi="Cao Đỉnh")
    _seed_historical_claim(
        db_session,
        entity.id,
        "claim-cao-dinh-01",
        verification_status="expert_verified",
        statement_vi="Cao Đỉnh đặt ở vị trí trung tâm trong cụm 9 đỉnh trước Thế Miếu.",
    )
    _seed_historical_claim(
        db_session,
        entity.id,
        "claim-cao-dinh-02",
        verification_status="expert_verified",
        statement_vi="Cao Đỉnh khởi đúc tháng 10 năm 1835 và hoàn thành năm 1837.",
    )
    _seed_historical_claim(
        db_session,
        entity.id,
        "claim-cao-dinh-03",
        verification_status="editor_reviewed",
        statement_vi="18 bản đúc trên Cao Đỉnh được đối chiếu trong Hội Điển Sự Lệ.",
    )
    db_session.commit()

    # 4. Verify curriculum claims validation
    is_valid, obj_reports = hl.validate_curriculum_objective_claims(
        db_session, "giai-ma-18-ban-duc-cao-dinh"
    )
    assert is_valid is True
    for r in obj_reports:
        assert r["claims_verified"] is True
        assert len(r["unverified_keys"]) == 0


# =========================================================================== #
# Test 2: Negative abuse test — unreviewed/disputed claims fail publishing gate
# =========================================================================== #
def test_negative_abuse_lesson_unreviewed_or_disputed_claims_fails_publication_gate(
    client, db_session
):
    """Negative abuse test: A lesson containing unreviewed or disputed claims FAILS publication."""
    staff = _make_user(
        client, db_session, "staff_curriculum@example.com", "Curriculum Staff", role=UserRole.admin
    )
    _, motif = _seed_urn_and_motif(db_session)
    entity = _seed_historical_entity(db_session, slug="test-entity", name_vi="Thực thể kiểm thử")

    # Seed an UNREVIEWED claim
    unreviewed_claim = _seed_historical_claim(
        db_session,
        entity.id,
        claim_key=f"claim-unreviewed-{uuid4().hex[:6]}",
        verification_status="unreviewed",
        statement_vi="Tuyên bố chưa được chuyên gia thẩm định.",
    )

    # Seed a DISPUTED claim
    disputed_claim = _seed_historical_claim(
        db_session,
        entity.id,
        claim_key=f"claim-disputed-{uuid4().hex[:6]}",
        verification_status="disputed",
        statement_vi="Tuyên bố đang có tranh biện học thuật.",
    )

    # Seed a REJECTED claim
    rejected_claim = _seed_historical_claim(
        db_session,
        entity.id,
        claim_key=f"claim-rejected-{uuid4().hex[:6]}",
        verification_status="rejected",
        statement_vi="Tuyên bố bị bác bỏ do sai lệch sử liệu.",
    )

    # Create a draft lesson with the unreviewed claim attached
    lesson = LessonContent(
        motif_id=motif.id,
        description="Bài học di sản về Cao Đỉnh với tư liệu chưa kiểm duyệt",
        status=ContentStatus.draft,
        is_published=False,
        content_validation_status="valid",
        additional_images={"required_claim_ids": [str(unreviewed_claim.id)]},
    )
    db_session.add(lesson)
    db_session.commit()
    db_session.refresh(lesson)

    # 1. Direct service validation must report invalid
    is_valid, issues = hl.validate_lesson_for_publication(db_session, lesson)
    assert is_valid is False
    assert len(issues) > 0
    assert "ineligible verification_status 'unreviewed'" in issues[0]

    # 2. Dry-run API validation endpoint must return can_publish=False
    val_res = client.post(
        "/api/v1/history/curriculum/validate-publish",
        json={"lesson_id": str(lesson.id)},
    )
    assert val_res.status_code == 200, val_res.text
    val_data = val_res.json()
    assert val_data["can_publish"] is False
    assert val_data["validation_status"] == "blocked_for_authoritative_learning"
    assert len(val_data["issues"]) > 0

    # 3. Attempting to publish via /api/v1/history/lessons/{lesson.id}/publish MUST fail with 422
    pub_res = client.post(
        f"/api/v1/history/lessons/{lesson.id}/publish",
        json={"claim_ids": [str(unreviewed_claim.id)]},
    )
    assert pub_res.status_code == 422, pub_res.text
    error_env = pub_res.json()["error"]
    assert error_env["code"] == "LESSON_UNVERIFIED_CLAIMS"

    # DB state check: lesson must remain unpublished and flagged as blocked
    db_session.refresh(lesson)
    assert lesson.is_published is False
    assert lesson.content_validation_status == "blocked_for_authoritative_learning"

    # Admin approval endpoint must ALSO reject with 422 LESSON_UNVERIFIED_CLAIMS
    admin_approve_res = client.post(
        f"/api/v1/admin/lessons/{lesson.id}/approve",
        json={"review_notes": "Attempting unauthorized approval"},
    )
    assert admin_approve_res.status_code == 422, admin_approve_res.text
    assert admin_approve_res.json()["error"]["code"] == "LESSON_UNVERIFIED_CLAIMS"

    # 4. Test with DISPUTED claim
    val_disputed = client.post(
        "/api/v1/history/curriculum/validate-publish",
        json={"claim_ids": [str(disputed_claim.id)]},
    )
    assert val_disputed.status_code == 200
    assert val_disputed.json()["can_publish"] is False
    assert val_disputed.json()["validation_status"] == "blocked_for_authoritative_learning"

    # 5. Test with REJECTED claim
    val_rejected = client.post(
        "/api/v1/history/curriculum/validate-publish",
        json={"claim_ids": [str(rejected_claim.id)]},
    )
    assert val_rejected.status_code == 200
    assert val_rejected.json()["can_publish"] is False

    # 6. Test with non-existent claim UUID
    fake_uuid = str(uuid4())
    val_fake = client.post(
        "/api/v1/history/curriculum/validate-publish",
        json={"claim_ids": [fake_uuid]},
    )
    assert val_fake.status_code == 200
    assert val_fake.json()["can_publish"] is False
    assert "not found in database" in val_fake.json()["issues"][0]


# =========================================================================== #
# Test 3: Publishing gate passes when claims are verified
# =========================================================================== #
def test_publishing_gate_allows_publication_when_claims_are_verified(client, db_session):
    """Test that a lesson is successfully published when all claims are verified."""
    staff = _make_user(
        client, db_session, "staff_verified@example.com", "Verified Staff", role=UserRole.admin
    )
    _, motif = _seed_urn_and_motif(db_session)
    entity = _seed_historical_entity(db_session, slug="cao-dinh-verified", name_vi="Cao Đỉnh")

    # Seed an expert verified claim
    verified_claim = _seed_historical_claim(
        db_session,
        entity.id,
        claim_key=f"claim-verified-{uuid4().hex[:6]}",
        verification_status="expert_verified",
        statement_vi="Khâm Định Đại Nam Hội Điển Sự Lệ ghi chép quy chuẩn đúc Cửu Đỉnh.",
    )

    lesson = LessonContent(
        motif_id=motif.id,
        description="Bài học di sản chuẩn GDPT 2018 với bằng chứng đầy đủ",
        status=ContentStatus.draft,
        is_published=False,
        content_validation_status="valid",
        additional_images={"required_claim_ids": [str(verified_claim.id)]},
    )
    db_session.add(lesson)
    db_session.commit()
    db_session.refresh(lesson)

    # 1. Validation check must return can_publish = True
    val_res = client.post(
        "/api/v1/history/curriculum/validate-publish",
        json={"lesson_id": str(lesson.id)},
    )
    assert val_res.status_code == 200
    assert val_res.json()["can_publish"] is True
    assert val_res.json()["validation_status"] == "valid"
    assert len(val_res.json()["issues"]) == 0

    # 2. Publish lesson via API
    pub_res = client.post(
        f"/api/v1/history/lessons/{lesson.id}/publish",
        json={"claim_ids": [str(verified_claim.id)], "review_notes": "Đã đối chiếu chính sử"},
    )
    assert pub_res.status_code == 200, pub_res.text
    pub_data = pub_res.json()
    assert pub_data["is_published"] is True
    assert pub_data["content_validation_status"] == "valid"
    assert pub_data["status"] == "published"
    assert str(verified_claim.id) in pub_data["verified_claim_ids"]

    # 3. Check DB persistence
    db_session.refresh(lesson)
    assert lesson.is_published is True
    assert lesson.content_validation_status == "valid"
    assert lesson.status == ContentStatus.published
    assert lesson.published_at is not None
    assert lesson.reviewed_by_id == staff.id


# =========================================================================== #
# Test 4: 2D rubbing asset fallback availability and disk integrity
# =========================================================================== #
def test_2d_rubbing_asset_fallback_availability_and_disk_integrity(client):
    """Test 2D rubbing asset fallback availability for low-bandwidth environments."""
    # 1. Direct resolver check for major urns
    for urn_slug, rel_path in hl.URN_RUBBING_MAP.items():
        fallback = hl.resolve_2d_rubbing_fallback(urn_slug)
        assert fallback["available"] is True, f"2D fallback for {urn_slug} reported unavailable"
        assert fallback["asset_type"] == "2d_rubbing"
        assert fallback["local_file_path"] == rel_path

        full_disk_path = REPO_ROOT / rel_path
        assert full_disk_path.is_file(), f"Rubbing file on disk missing: {full_disk_path}"
        assert full_disk_path.stat().st_size > 5000, f"Rubbing file too small: {full_disk_path}"

    # 2. API fallback endpoint check
    cao_fallback_res = client.get("/api/v1/history/curriculum/fallbacks/cao-dinh")
    assert cao_fallback_res.status_code == 200, cao_fallback_res.text
    cao_fb = cao_fallback_res.json()
    assert cao_fb["available"] is True
    assert "/assets/ban-duc-noi/CAO" in cao_fb["url"]
    assert cao_fb["byte_size"] > 5000

    thuan_fallback_res = client.get("/api/v1/history/curriculum/fallbacks/thuan-dinh")
    assert thuan_fallback_res.status_code == 200
    thuan_fb = thuan_fallback_res.json()
    assert thuan_fb["available"] is True
    assert "/assets/ban-duc-noi/THUAN" in thuan_fb["url"]

    # 3. Verify all curriculum modules have valid 2D fallbacks
    modules_res = client.get("/api/v1/history/curriculum/modules")
    assert modules_res.status_code == 200
    for mod in modules_res.json()["items"]:
        fb = mod.get("media_fallback_2d")
        assert fb is not None, f"Module {mod['slug']} missing media_fallback_2d"
        assert fb["available"] is True
        assert fb["asset_type"] == "2d_rubbing"
        assert fb["byte_size"] > 5000


# =========================================================================== #
# Test 5: Frontend learn page and modules contract verification
# =========================================================================== #
def test_frontend_curriculum_mapping_and_rubbing_fallback_contract():
    """Verify frontend/src/lib/rbpc/learnModules.ts and frontend/src/app/learn/page.tsx."""
    learn_modules_path = REPO_ROOT / "frontend/src/lib/rbpc/learnModules.ts"
    learn_page_path = REPO_ROOT / "frontend/src/app/learn/page.tsx"
    types_path = REPO_ROOT / "frontend/src/types/rbpc.ts"

    assert learn_modules_path.is_file(), f"Missing file: {learn_modules_path}"
    assert learn_page_path.is_file(), f"Missing file: {learn_page_path}"
    assert types_path.is_file(), f"Missing file: {types_path}"

    modules_content = learn_modules_path.read_text(encoding="utf-8")
    page_content = learn_page_path.read_text(encoding="utf-8")
    types_content = types_path.read_text(encoding="utf-8")

    # 1. Type definitions contract
    assert "CurriculumObjectiveMapping" in types_content
    assert "fallback2dRubbingUrl?: string" in types_content
    assert "curriculumObjectives?: CurriculumObjectiveMapping[]" in types_content

    # 2. Modules contract
    assert "fallback2dRubbingUrl:" in modules_content
    assert "curriculumObjectives:" in modules_content
    assert "S1_SPATIAL" in modules_content
    assert "S2_TEMPORAL" in modules_content
    assert "S3_EVIDENCE" in modules_content
    assert "S4_ARGUMENT" in modules_content
    assert "claim-cao-dinh-01" in modules_content

    # 3. UI page contract
    assert "fallback2dRubbingUrl" in page_content
    assert "curriculumObjectives" in page_content
    assert "Low-Bandwidth" in page_content or "băng thông thấp" in page_content
    assert "Source-Verified" in page_content or "Chứng cứ đã kiểm chứng" in page_content
