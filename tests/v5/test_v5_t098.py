# -*- coding: utf-8 -*-
"""V5-T098 (Wave W09, Slot A08): Multilingual Learning Supports & Pedagogical Glossary Test Suite.

Audits and verifies:
1. Pedagogical Bilingual Glossary API (GET /api/v1/history/glossary):
   - Bilingual Vietnamese/English definitions, contextual usage, and categories.
   - Hán–Nôm epigraphy readings (glyphs and Sino-Vietnamese reading_quoc_ngu).
   - Category filtering (relic, epigraphy, geography, flora_fauna, technique, etc.).
   - Bilingual full-text search across Vietnamese, English, and transliterations.
2. Translation Provenance & Bilingual Citation Linkage:
   - Structured translation provenance metadata (origin, reviewer, confidence, locator).
   - Authoritative source citations linked to primary historical texts.
3. Access Control & RBAC:
   - Public GET /api/v1/history/glossary requires no authentication.
   - Staff/admin mutations under /api/v1/admin/history/glossary enforce STAFF_ROLES.
   - Learners and guests receive HTTP 403 Forbidden on mutation endpoints.
4. Negative Abuse Defense 1 - Mismatched or placeholder translations:
   - Submissions with placeholder English ("placeholder", "unknown", "TODO", "n/a")
     cannot be promoted to verified (HTTP 422).
   - Untranslated Vietnamese copied verbatim into English definition cannot be verified (HTTP 422).
   - Draft submissions with placeholders are strictly flagged with is_uncertain=True and uncertainty labels.
5. Negative Abuse Defense 2 - Machine-translated gloss verification block:
   - Machine-translated or AI-generated glosses CANNOT be promoted to verified without human
     epigrapher sign-off (HTTP 422).
   - When displayed, unreviewed machine translations strictly carry prominent uncertainty warnings.
6. Negative Abuse Defense 3 - Citation and Epigraphy Completeness:
   - Terms cannot be promoted to verified without valid scholarly source citation (HTTP 422).
   - Hán-Nôm terms cannot be verified without Sino-Vietnamese reading (reading_quoc_ngu) (HTTP 422).
7. Review & Epigrapher Promotion Workflow:
   - Expert reviewer signs off on provisional term with citation locator.
   - Transitions term to verified with immutable audit trail.
"""
from __future__ import annotations

import uuid
from typing import Any
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from backend.domain.multilingual_glossary import (
    GlossaryCategory,
    GlossaryReviewStatus,
    GlossaryValidationError,
    MismatchedTranslationError,
    TranslationOrigin,
    UnreviewedTranslationPromotionError,
    build_translation_provenance,
    detect_translation_mismatch,
    validate_glossary_term_invariants,
)
from backend.history_models import (
    HistoricalContentAuditLog,
    HistoricalGlossaryTerm,
    HistoricalSource,
)
from backend.models import User, UserRole
from backend.security import hash_password


# --------------------------------------------------------------------------- #
# Helpers & Seeders
# --------------------------------------------------------------------------- #
def _create_user(db_session, email: str, role: UserRole, display_name: str) -> User:
    user = db_session.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if not user:
        user = User(
            email=email,
            password_hash=hash_password("Password123!"),
            display_name=display_name,
            username=f"u_{uuid.uuid4().hex[:8]}",
            role=role,
            is_profile_public=True,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
    else:
        user.role = role
        db_session.commit()
    return user


def _login(client: TestClient, email: str, password: str = "Password123!") -> dict[str, str]:
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    token = client.cookies.get("luuniensuki_access") or res.cookies.get("luuniensuki_access") or ""
    return {"Authorization": f"Bearer {token}"}


# --------------------------------------------------------------------------- #
# Unit Domain Invariant & Negative Abuse Tests
# --------------------------------------------------------------------------- #
def test_domain_detect_translation_mismatch():
    # 1. Valid translation
    is_mismatched, reason = detect_translation_mismatch(
        term_vi="Cao Đỉnh",
        term_en="Cao Urn",
        definition_vi="Chiếc đỉnh đặt ở trung tâm.",
        definition_en="The central dynastic urn.",
    )
    assert not is_mismatched
    assert reason is None

    # 2. Placeholder detection
    is_mismatched, reason = detect_translation_mismatch(
        term_vi="Cao Đỉnh",
        term_en="placeholder",
    )
    assert is_mismatched
    assert "placeholder" in reason

    # 3. Untranslated duplicate definition detection
    identical_text = "Chiếc đỉnh lớn nhất đúc bằng đồng đặt tại Thế Miếu hoàng thành Huế"
    is_mismatched, reason = detect_translation_mismatch(
        term_vi="Cao Đỉnh",
        term_en="Cao Urn",
        definition_vi=identical_text,
        definition_en=identical_text,
    )
    assert is_mismatched
    assert "untranslated copy" in reason


def test_domain_negative_abuse_unreviewed_promotion_blocked():
    # Attempting verified status without sign-off must raise UnreviewedTranslationPromotionError
    with pytest.raises(UnreviewedTranslationPromotionError) as exc_info:
        validate_glossary_term_invariants(
            term_key="test-term",
            term_vi="Nghị Đỉnh",
            term_en="Nghi Urn",
            definition_vi="Đỉnh thứ hai trong Cửu Đỉnh.",
            definition_en="The second urn in the Nine Dynastic Urns.",
            review_status="verified",
            origin="machine_translated",
            is_machine_translated=True,
            epigrapher_signoff=None,  # Missing signoff!
            source_id="11111111-1111-1111-1111-111111111111",
            citation_locator="Quyển 162",
        )
    assert "Machine-translated glosses cannot be marked verified" in str(exc_info.value)


def test_domain_negative_abuse_mismatched_promotion_blocked():
    # Attempting verified status with placeholder English must raise MismatchedTranslationError
    with pytest.raises(MismatchedTranslationError) as exc_info:
        validate_glossary_term_invariants(
            term_key="test-placeholder",
            term_vi="Thuần Đỉnh",
            term_en="TODO",
            definition_vi="Đỉnh thứ năm biểu trưng sự thuần khiết.",
            definition_en="TODO translation pending",
            review_status="verified",
            origin="human_epigrapher",
            epigrapher_signoff="Dr. Epigrapher",
            citation_locator="Quyển 214",
        )
    assert "Mismatched or placeholder translation cannot be verified" in str(exc_info.value)


def test_domain_negative_abuse_verified_without_citation_blocked():
    with pytest.raises(UnreviewedTranslationPromotionError) as exc_info:
        validate_glossary_term_invariants(
            term_key="test-no-citation",
            term_vi="Bạch Đằng Giang",
            term_en="Bach Dang River",
            definition_vi="Dòng sông lịch sử ba lần đại thắng.",
            definition_en="The historic river of three historic victories.",
            review_status="verified",
            origin="human_epigrapher",
            epigrapher_signoff="Dr. Epigrapher",
            source_id=None,
            citation_locator=None,  # Missing citation!
        )
    assert "must include an authoritative source citation" in str(exc_info.value)


def test_domain_draft_placeholder_flagged_with_uncertainty():
    # When in provisional/draft status, placeholder text does not halt creation,
    # but strictly enforces is_uncertain=True and uncertainty_label.
    res = validate_glossary_term_invariants(
        term_key="draft-placeholder",
        term_vi="Đàn Mộc",
        term_en="placeholder",
        definition_vi="Cây đàn mộc trên Nghị Đỉnh.",
        definition_en="Sandalwood tree.",
        review_status="provisional",
        origin="ai_generated",
        is_machine_translated=False,
    )
    assert res["is_uncertain"] is True
    assert "Bản dịch đối chiếu chưa hoàn thiện" in res["uncertainty_label"]


# --------------------------------------------------------------------------- #
# Integration API Tests (Public & Authenticated Endpoints)
# --------------------------------------------------------------------------- #
def test_public_glossary_listing_and_canonical_seeds(client: TestClient, db_session):
    # 1. Unauthenticated public request
    resp = client.get("/api/v1/history/glossary")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert data["total"] >= 5

    keys = [it["term_key"] for it in data["items"]]
    assert "cao-dinh" in keys
    assert "huyen-dinh" in keys
    assert "bach-dang-giang" in keys
    assert "phap-lam" in keys


def test_public_glossary_filtering_and_search(client: TestClient, db_session):
    # 1. Filter by category relic
    resp_relic = client.get("/api/v1/history/glossary?category=relic")
    assert resp_relic.status_code == 200
    data_relic = resp_relic.json()
    assert len(data_relic["items"]) >= 2
    for it in data_relic["items"]:
        assert it["category"] == "relic"

    # 2. Search in Vietnamese
    resp_vi = client.get("/api/v1/history/glossary?search=Bạch%20Đằng")
    assert resp_vi.status_code == 200
    data_vi = resp_vi.json()
    assert any(it["term_key"] == "bach-dang-giang" for it in data_vi["items"])

    # 3. Search in English
    resp_en = client.get("/api/v1/history/glossary?search=enamelware")
    assert resp_en.status_code == 200
    data_en = resp_en.json()
    assert any(it["term_key"] == "phap-lam" for it in data_en["items"])


def test_public_glossary_single_term_and_provenance(client: TestClient, db_session):
    # Retrieve Cao Đỉnh detail
    resp = client.get("/api/v1/history/glossary/cao-dinh")
    assert resp.status_code == 200
    term = resp.json()
    assert term["term_key"] == "cao-dinh"
    assert term["term_vi"] == "Cao Đỉnh"
    assert term["term_han_nom"] == "高鼎"
    assert term["reading_quoc_ngu"] == "Cao Đỉnh"
    assert term["review_status"] == "verified"
    assert term["is_uncertain"] is False
    assert term["epigrapher_signoff"] is not None

    # Translation provenance inspection
    prov = term["translation_provenance"]
    assert prov["origin"] == "human_epigrapher"
    assert "Nguyen Dinh Chien" in prov["translator_or_reviewer"]
    assert "Quyển 162" in prov["citation_locator"]


def test_public_glossary_nonexistent_term_returns_404(client: TestClient, db_session):
    resp = client.get("/api/v1/history/glossary/non-existent-xyz-term")
    assert resp.status_code == 404
    body = resp.json()
    assert body["error"]["code"] == "GLOSSARY_TERM_NOT_FOUND"


def test_unreviewed_and_machine_terms_carry_uncertainty_labels(client: TestClient, db_session):
    # Check Đăng Sơn Ngư (machine translated seed)
    resp = client.get("/api/v1/history/glossary/dang-son-ngu")
    assert resp.status_code == 200
    term = resp.json()
    assert term["is_machine_translated"] is True
    assert term["is_uncertain"] is True
    assert "Bản dịch máy tự động" in term["uncertainty_label"]


def test_rbac_admin_glossary_mutations_forbidden_for_learners(client: TestClient, db_session):
    learner = _create_user(db_session, "learner_t098@example.com", UserRole.learner, "Student Learner")
    headers = _login(client, "learner_t098@example.com")

    payload = {
        "term_key": "forbidden-term",
        "term_vi": "Thuật ngữ",
        "term_en": "Term",
        "definition_vi": "Mô tả",
        "definition_en": "Description",
    }
    # POST
    resp_post = client.post("/api/v1/admin/history/glossary", json=payload, headers=headers)
    assert resp_post.status_code == 403

    # PATCH
    resp_patch = client.patch("/api/v1/admin/history/glossary/cao-dinh", json=payload, headers=headers)
    assert resp_patch.status_code == 403

    # Review
    resp_rev = client.post(
        "/api/v1/admin/history/glossary/cao-dinh/review",
        json={"review_status": "verified"},
        headers=headers,
    )
    assert resp_rev.status_code == 403


def test_negative_abuse_admin_rejects_unreviewed_machine_translation_promotion(client: TestClient, db_session):
    staff = _create_user(db_session, "staff_t098@example.com", UserRole.admin, "Staff Admin")
    headers = _login(client, "staff_t098@example.com")

    # Attempting to verify machine-translated gloss without human reviewer sign-off
    payload = {
        "term_key": "abusive-unreviewed-machine",
        "term_vi": "Ngũ Nhược",
        "term_en": "Five Fragrances",
        "category": "symbolism",
        "definition_vi": "Năm mùi hương biểu trưng cho đức hạnh.",
        "definition_en": "Five fragrances symbolizing courtly virtue.",
        "review_status": "verified",  # Attempting verified!
        "origin": "machine_translated",
        "is_machine_translated": True,
        "epigrapher_signoff": None,  # No human sign-off!
        "citation_locator": "Đại Nam Nhất Thống Chí",
    }
    resp = client.post("/api/v1/admin/history/glossary", json=payload, headers=headers)
    assert resp.status_code == 422
    body = resp.json()
    assert body["error"]["code"] == "GLOSSARY_VALIDATION_ERROR"
    assert "Machine-translated glosses cannot be marked verified" in body["error"]["message"]


def test_negative_abuse_admin_rejects_mismatched_untranslated_copy(client: TestClient, db_session):
    staff = _create_user(db_session, "staff_t098_b@example.com", UserRole.admin, "Staff Admin B")
    headers = _login(client, "staff_t098_b@example.com")

    # English definition is exact duplicate copy of Vietnamese definition
    vietnamese_def = "Bản dập thác bản minh văn trên thân đỉnh đồng Thế Miếu triều Nguyễn."
    payload = {
        "term_key": "abusive-untranslated-copy",
        "term_vi": "Thác bản Cửu Đỉnh",
        "term_en": "Nine Urns Rubbings",
        "category": "epigraphy",
        "definition_vi": vietnamese_def,
        "definition_en": vietnamese_def,  # Copied Vietnamese!
        "review_status": "verified",
        "origin": "human_epigrapher",
        "epigrapher_signoff": "Dr. Epigrapher",
        "citation_locator": "Văn bia Cửu Đỉnh",
    }
    resp = client.post("/api/v1/admin/history/glossary", json=payload, headers=headers)
    assert resp.status_code == 422
    body = resp.json()
    assert body["error"]["code"] == "GLOSSARY_VALIDATION_ERROR"
    assert "untranslated copy" in body["error"]["message"]


def test_staff_create_provisional_glossary_term_and_verify_audit(client: TestClient, db_session):
    staff = _create_user(db_session, "staff_t098_c@example.com", UserRole.admin, "Staff Admin C")
    headers = _login(client, "staff_t098_c@example.com")

    payload = {
        "term_key": "ngu-phung-lau",
        "term_vi": "Lầu Ngũ Phụng",
        "term_en": "Five-Phoenix Pavilion",
        "term_han_nom": "五鳳樓",
        "reading_quoc_ngu": "Ngũ Phụng Lâu",
        "category": "architecture",
        "definition_vi": "Tầng trên của cửa Ngọ Môn gồm hai tầng gác chín bộ mái.",
        "definition_en": "The upper pavilion of the Noon Gate featuring nine roof sections.",
        "contextual_usage_vi": "Lầu Ngũ Phụng là nơi diễn ra các đại lễ triều đình như lễ Truyền lô và lễ Ban sóc.",
        "contextual_usage_en": "The Five-Phoenix Pavilion hosted major royal ceremonies including the calendar promulgation.",
        "review_status": "provisional",
        "origin": "scholarly_lexicon",
        "is_machine_translated": False,
        "is_uncertain": True,
        "uncertainty_label": "Đang đối chiếu tài liệu kiến trúc Trung tâm Bảo tồn Di tích Cố đô Huế.",
    }

    # 1. Create provisional term
    resp = client.post("/api/v1/admin/history/glossary", json=payload, headers=headers)
    assert resp.status_code == 200
    created = resp.json()
    assert created["term_key"] == "ngu-phung-lau"
    assert created["review_status"] == "provisional"
    assert created["is_uncertain"] is True

    # 2. Verify audit log entry was created
    audit = db_session.execute(
        select(HistoricalContentAuditLog).where(
            HistoricalContentAuditLog.resource_type == "glossary_term",
            HistoricalContentAuditLog.action == "create",
        )
    ).scalars().first()
    assert audit is not None
    assert audit.after_json["term_key"] == "ngu-phung-lau"


def test_staff_review_promotion_lifecycle_and_public_update(client: TestClient, db_session):
    staff = _create_user(db_session, "epigrapher_t098@example.com", UserRole.admin, "Expert Epigrapher")
    headers = _login(client, "epigrapher_t098@example.com")

    # 1. Create a draft term needing review
    create_payload = {
        "term_key": "an-dinh",
        "term_vi": "Anh Đỉnh",
        "term_en": "Anh Urn (The Heroic Urn)",
        "term_han_nom": "英鼎",
        "reading_quoc_ngu": "Anh Đỉnh",
        "category": "relic",
        "definition_vi": "Chiếc đỉnh thứ tư trong Cửu Đỉnh, biểu trưng cho vua Dực Tổ Anh Hoàng Đế (Tự Đức).",
        "definition_en": "The fourth urn in the Nine Dynastic Urns, dedicated to Emperor Tu Duc.",
        "review_status": "provisional",
        "origin": "provisional_draft",
        "is_uncertain": True,
    }
    resp_create = client.post("/api/v1/admin/history/glossary", json=create_payload, headers=headers)
    assert resp_create.status_code == 200

    # 2. Epigrapher review & promotion to verified with full sign-off and citation
    review_payload = {
        "review_status": "verified",
        "epigrapher_signoff": "Prof. Le Van Hao / Hue Epigraphy Board",
        "citation_locator": "Khâm Định Đại Nam Hội Điển Sự Lệ, Quyển 214, tờ 3b",
        "notes": "Verified against rubbing stamp inventory and 1835 founding records.",
    }
    resp_rev = client.post(
        "/api/v1/admin/history/glossary/an-dinh/review",
        json=review_payload,
        headers=headers,
    )
    assert resp_rev.status_code == 200
    verified = resp_rev.json()
    assert verified["review_status"] == "verified"
    assert verified["is_uncertain"] is False
    assert verified["epigrapher_signoff"] == "Prof. Le Van Hao / Hue Epigraphy Board"
    assert verified["translation_provenance"]["confidence"] >= 0.90

    # 3. Public GET confirms updated verified status
    resp_pub = client.get("/api/v1/history/glossary/an-dinh")
    assert resp_pub.status_code == 200
    pub_term = resp_pub.json()
    assert pub_term["review_status"] == "verified"
    assert pub_term["is_uncertain"] is False


def test_staff_patch_update_glossary_term(client: TestClient, db_session):
    staff = _create_user(db_session, "staff_t098_patch@example.com", UserRole.admin, "Staff Patcher")
    headers = _login(client, "staff_t098_patch@example.com")

    # Update contextual usage on cao-dinh
    patch_payload = {
        "contextual_usage_en": "Cao Dinh stands prominently in front of the central chamber of The Mieu.",
    }
    resp = client.patch("/api/v1/admin/history/glossary/cao-dinh", json=patch_payload, headers=headers)
    assert resp.status_code == 200
    updated = resp.json()
    assert updated["contextual_usage_en"] == "Cao Dinh stands prominently in front of the central chamber of The Mieu."
    assert updated["term_vi"] == "Cao Đỉnh"  # Preserved
