# -*- coding: utf-8 -*-
"""LƯU NIÊN — RBPC 2026: Live Demo API Reliability & Error Envelope Verification.

Phase 6 / AGENT 02:
- End-to-end sequential verification of the live demo API chain:
  1. GET /api/v1/rbpc/config -> 200 OK
  2. GET /api/v1/heritage/places?limit=10 -> 200 OK
  3. GET /api/v1/heritage/places/lang-tu-duc/detail -> 200 OK with citations
  4. POST /api/v1/rbpc/cultural-bridge -> 200 OK with grounded answer and citations
  5. GET /api/v1/rbpc/creators/nghe-nhan-nguyen-van-sinh -> 200 OK with consent verified
  6. GET /api/v1/experiences/workshop-duc-dong-phuong-duc -> 200 OK with inquiry_only mode
  7. POST /api/v1/rbpc/inquiries -> 202 Accepted with non-sequential public_ref and opaque_token
  8. GET /api/v1/rbpc/inquiries/status/{opaqueToken} -> 200 OK with zero PII
  9. GET /api/v1/rbpc/impact -> 200 OK with verified 202,360,638 VND in-kind support
- Error state reliability & standard error envelope enforcement:
  Standard shape: {"error": {"code": str, "message": str, "details": dict}}
  Covers: 400 Bad Request, 404 Not Found, 409 Conflict, 422 Unprocessable Entity, 429 Too Many Requests
- Hardening invariants:
  * Idempotency replay (202 identical token reuse) vs payload conflict (409)
  * Public inquiry status zero-PII leakage invariant
  * IP-based rate limiting (5 req/hour) with Retry-After header
  * Anti-spam and script injection guardrails
  * Fail-closed Cultural Bridge fallback when evidence is insufficient
"""
from __future__ import annotations

import re
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Any

import pytest
from sqlalchemy import select, update

from backend.apischemas.heritage import HeritageEntityType
from backend.models_rbpc import (
    HeritagePlace,
    HeritageRecordStatus,
    HeritageSourceEvidence,
    RbpcConsentStatus,
    RbpcCreator,
    RbpcExperience,
    RbpcInquiry,
)
from backend.routers.rbpc import _inquiry_rate_limit_store
from backend.services.heritage_import import (
    DEFAULT_CREATORS_PATH,
    DEFAULT_EXPERIENCES_PATH,
    DEFAULT_INVENTORY_PATH,
    DEFAULT_SKETCHFAB_PATH,
    DEFAULT_STORIES_PATH,
    import_heritage_data,
)


# --------------------------------------------------------------------------- #
# Fixtures & Test Setup
# --------------------------------------------------------------------------- #
@pytest.fixture(autouse=True)
def clean_inquiry_rate_limiter():
    """Reset inquiry rate limiter state before each test for test isolation."""
    _inquiry_rate_limit_store.clear()
    yield
    _inquiry_rate_limit_store.clear()


@pytest.fixture
def seeded_demo_data(db_session):
    """Seed comprehensive RBPC Huế heritage catalogue, commercial offerings, and sources."""
    # 1. Ingest base catalogue (23 places, 3 creators, 3 experiences, 3 stories, 6 claims)
    import_heritage_data(
        db=db_session,
        inventory_path=DEFAULT_INVENTORY_PATH,
        sketchfab_path=DEFAULT_SKETCHFAB_PATH,
        stories_path=DEFAULT_STORIES_PATH,
        creators_path=DEFAULT_CREATORS_PATH,
        experiences_path=DEFAULT_EXPERIENCES_PATH,
        dry_run=False,
    )

    # 2. Publish all heritage places for public catalogue availability
    db_session.execute(
        update(HeritagePlace).values(
            editorial_status=HeritageRecordStatus.published.value,
            published_at=datetime.now(timezone.utc),
        )
    )

    # 3. Add verified bibliographic source citations for Lăng Tự Đức (lang-tu-duc)
    tu_duc = db_session.scalar(
        select(HeritagePlace).where(HeritagePlace.slug == "lang-tu-duc")
    )
    assert tu_duc is not None, "Place 'lang-tu-duc' must exist after import"

    unesco_source = HeritageSourceEvidence(
        place_id=tu_duc.id,
        source_title="Complex of Hué Monuments - UNESCO World Heritage Centre",
        source_url="https://whc.unesco.org/en/list/678",
        source_author="UNESCO World Heritage Centre",
        publisher="UNESCO",
        publication_year=1993,
        cited_section="Component 678-007: Khiêm Lăng (Tomb of Tự Đức)",
        cited_page="Criteria (iii), (iv)",
        statement="Lăng Tự Đức (Khiêm Lăng) được UNESCO ghi danh Di sản Văn hóa Thế giới năm 1993 trong Quần thể Di tích Cố đô Huế.",
        interpretation_note="Thành tố số 678-007 trong hồ sơ di sản thế giới của UNESCO.",
        evidence_status="verified",
        reuse_rights="public_domain",
        content_scope="RBPC_HUE",
    )
    dntl_source = HeritageSourceEvidence(
        place_id=tu_duc.id,
        source_title="Đại Nam Thực Lục Chính Biên - Đệ Tứ Kỷ",
        source_author="Quốc Sử Quán Triều Nguyễn",
        publisher="NXB Giáo Dục",
        publication_year=2007,
        cited_section="Quyển 30: Kỷ Dực Tông Anh Hoàng Đế",
        cited_page="Tập 7, tr. 842-845",
        source_url="https://heritage.example.vn/dai-nam-thuc-luc-tu-duc",
        statement="Khiêm Lăng được khởi công xây dựng vào năm Giáp Tý (1864) dưới sự giám sát của Đổng công Đặng Huy Trứ.",
        interpretation_note="Tài liệu chính sử xác thực niên đại xây dựng.",
        evidence_status="verified",
        reuse_rights="public_domain",
        content_scope="RBPC_HUE",
    )
    db_session.add_all([unesco_source, dntl_source])

    # 4. Seed an unpublished draft place for negative isolation testing
    draft_place = HeritagePlace(
        slug="draft-secret-shrine",
        name_vi="Miếu Thờ Bản Nháp Chưa Công Bố",
        entity_type="monument",
        heritage_category="imperial_architecture",
        editorial_status=HeritageRecordStatus.draft.value,
        content_scope="RBPC_HUE",
    )
    db_session.add(draft_place)

    # 5. Seed a creator with revoked consent for negative isolation testing
    revoked_creator_id = uuid.uuid4()
    revoked_creator = RbpcCreator(
        id=revoked_creator_id,
        slug="nghe-nhan-rut-dong-thuan",
        public_name="Nghệ nhân Chưa Đồng Thuận",
        craft_tradition="Chạm xà cừ",
        approved_bio_vi="Tiểu sử chưa được xuất bản.",
        consent_status=RbpcConsentStatus.revoked.value,
    )
    db_session.add(revoked_creator)
    db_session.flush()

    # 6. Seed a draft experience for negative isolation testing
    draft_exp = RbpcExperience(
        id=uuid.uuid4(),
        slug="workshop-nhap-chua-xuat-ban",
        creator_id=revoked_creator.id,
        provider_name="Xưởng Thử Nghiệm",
        title_vi="Workshop Bản Nháp",
        description_vi="Chưa mở công khai.",
        area_public="Huế",
        publication_state="draft",
        availability_mode="inquiry_only",
    )
    db_session.add(draft_exp)

    db_session.commit()
    return tu_duc


# --------------------------------------------------------------------------- #
# Error Envelope Validation Helper
# --------------------------------------------------------------------------- #
def assert_error_envelope(response, expected_status: int, expected_code: str | None = None) -> dict[str, Any]:
    """Validate that response strictly complies with standard error envelope specification.

    Contract:
    - HTTP status code == expected_status
    - Top-level JSON has 'error' key
    - 'error' object contains 'code' (non-empty str), 'message' (non-empty str), and 'details' (dict)
    - If expected_code is provided, 'code' must match exactly
    """
    assert response.status_code == expected_status, (
        f"Expected status {expected_status}, got {response.status_code}: {response.text}"
    )
    data = response.json()
    assert isinstance(data, dict), f"Response is not a JSON object: {data}"
    assert "error" in data, f"Missing 'error' in response body: {data}"
    err = data["error"]
    assert isinstance(err, dict), f"'error' is not a dictionary: {err}"
    assert "code" in err, f"Missing 'code' in error: {err}"
    assert "message" in err, f"Missing 'message' in error: {err}"
    assert "details" in err, f"Missing 'details' in error: {err}"
    assert isinstance(err["code"], str) and len(err["code"]) > 0, f"Invalid code: {err.get('code')}"
    assert isinstance(err["message"], str) and len(err["message"]) > 0, f"Invalid message: {err.get('message')}"
    assert isinstance(err["details"], dict), f"details must be a dict: {type(err.get('details'))}"
    if expected_code:
        assert err["code"] == expected_code, f"Expected error code '{expected_code}', got '{err['code']}'"
    return err


# --------------------------------------------------------------------------- #
# End-to-End Sequential Live Demo Chain
# --------------------------------------------------------------------------- #
def test_demo_api_chain_sequential(client, seeded_demo_data):
    """Test the full end-to-end demo API chain in exact sequence.

    Steps:
      1. GET /api/v1/rbpc/config -> 200 OK
      2. GET /api/v1/heritage/places?limit=10 -> 200 OK
      3. GET /api/v1/heritage/places/lang-tu-duc/detail -> 200 OK with citations
      4. POST /api/v1/rbpc/cultural-bridge -> 200 OK with grounded answer and citations
      5. GET /api/v1/rbpc/creators/nghe-nhan-nguyen-van-sinh -> 200 OK with consent verified
      6. GET /api/v1/experiences/workshop-duc-dong-phuong-duc -> 200 OK with inquiry_only mode
      7. POST /api/v1/rbpc/inquiries -> 202 Accepted with non-sequential public_ref and opaque_token
      8. GET /api/v1/rbpc/inquiries/status/{opaqueToken} -> 200 OK with zero PII
      9. GET /api/v1/rbpc/impact -> 200 OK with verified 202,360,638 VND in-kind support
    """
    # -------------------------------------------------------------------------
    # 1. GET /api/v1/rbpc/config -> 200 OK
    # -------------------------------------------------------------------------
    res_cfg = client.get("/api/v1/rbpc/config")
    assert res_cfg.status_code == 200, res_cfg.text
    cfg = res_cfg.json()
    assert cfg["enabled"] is True
    assert cfg["ai_enabled"] is True
    assert cfg["inquiry_enabled"] is True
    assert cfg["demo_mode"] is True
    assert "vi" in cfg["supported_locales"]
    assert "en" in cfg["supported_locales"]
    assert cfg["consent_version"] == "rbpc-inquiry-v1"
    assert cfg["version"] == "1.0.0"

    # -------------------------------------------------------------------------
    # 2. GET /api/v1/heritage/places?limit=10 -> 200 OK
    # -------------------------------------------------------------------------
    res_places = client.get("/api/v1/heritage/places", params={"limit": 10})
    assert res_places.status_code == 200, res_places.text
    places_data = res_places.json()
    assert "items" in places_data
    assert "total_count" in places_data
    assert len(places_data["items"]) == 10
    assert places_data["total_count"] >= 10

    # Verify first page items are properly shaped
    for item in places_data["items"]:
        assert item["slug"]
        assert item["name_vi"]
        assert item["editorial_status"] == "published"
        assert item["content_scope"] == "RBPC_HUE"
        assert item["entity_type"] in [e.value for e in HeritageEntityType]

    # -------------------------------------------------------------------------
    # 3. GET /api/v1/heritage/places/lang-tu-duc/detail -> 200 OK with citations
    # -------------------------------------------------------------------------
    res_detail = client.get("/api/v1/heritage/places/lang-tu-duc/detail")
    assert res_detail.status_code == 200, res_detail.text
    detail = res_detail.json()
    assert detail["slug"] == "lang-tu-duc"
    assert "Lăng Tự Đức" in detail["name_vi"]
    assert detail["heritage_category"] == "royal_tomb"
    assert detail["editorial_status"] == "published"

    # Verify citations presence and structure
    assert "sources" in detail
    assert len(detail["sources"]) >= 2
    for src in detail["sources"]:
        assert src["source_title"]
        assert src["statement"]
        assert src["evidence_status"] == "verified"
        assert src["content_scope"] == "RBPC_HUE"

    # Verify UNESCO reference
    unesco_src = next((s for s in detail["sources"] if "UNESCO" in s["source_title"]), None)
    assert unesco_src is not None
    assert "678" in unesco_src["source_url"]

    # -------------------------------------------------------------------------
    # 4. POST /api/v1/rbpc/cultural-bridge -> 200 OK with grounded answer & citations
    # -------------------------------------------------------------------------
    res_ai = client.post(
        "/api/v1/rbpc/cultural-bridge",
        json={
            "story_slug": "tieng-chuong-khiem-cung",
            "question": "Vì sao kỹ thuật đúc đồng Phường Đúc lại gắn liền với lịch sử triều Nguyễn?",
            "locale": "vi",
        },
    )
    assert res_ai.status_code == 200, res_ai.text
    ai_data = res_ai.json()
    assert ai_data["status"] == "supported"
    assert ai_data["locale"] == "vi"
    assert isinstance(ai_data["answer"], str) and len(ai_data["answer"]) > 50

    # Grounded citations check
    assert "citations" in ai_data
    assert len(ai_data["citations"]) >= 1
    for c in ai_data["citations"]:
        assert c["source_id"]
        assert c["title"]
        assert c["support"] in ("direct", "contextual", "interpretation")
        assert c["locator"]

    # Invariants: context boundary and model version
    assert "nghệ nhân" in ai_data["context_boundary"] or "lịch sử" in ai_data["context_boundary"]
    assert ai_data["model_version"] == "clara-gemini-3.8-flash-tiered-v1"
    assert ai_data["epistemic_certainty"] in ("high", "medium")

    # -------------------------------------------------------------------------
    # 5. GET /api/v1/rbpc/creators/nghe-nhan-nguyen-van-sinh -> 200 OK with consent verified
    # -------------------------------------------------------------------------
    res_creator = client.get("/api/v1/rbpc/creators/nghe-nhan-nguyen-van-sinh")
    assert res_creator.status_code == 200, res_creator.text
    creator = res_creator.json()
    assert creator["slug"] == "nghe-nhan-nguyen-van-sinh"
    assert creator["public_name"] == "Nghệ nhân Nhân dân Nguyễn Văn Sinh"
    assert creator["craft_tradition_vi"] == "Đúc đồng Phường Đúc"
    assert creator["consent_status"] == "consented"
    assert "workshop-duc-dong-phuong-duc" in creator["experience_slugs"]
    assert "tieng-chuong-khiem-cung" in creator["approved_story_slugs"]

    # -------------------------------------------------------------------------
    # 6. GET /api/v1/rbpc/experiences/workshop-duc-dong-phuong-duc -> 200 OK (inquiry_only)
    # -------------------------------------------------------------------------
    res_exp = client.get("/api/v1/rbpc/experiences/workshop-duc-dong-phuong-duc")
    assert res_exp.status_code == 200, res_exp.text
    exp = res_exp.json()
    assert exp["slug"] == "workshop-duc-dong-phuong-duc"
    assert exp["creator_slug"] == "nghe-nhan-nguyen-van-sinh"
    assert exp["availability_mode"] == "inquiry_only"
    assert exp["indicative_price_amount"] is not None and exp["indicative_price_amount"] > 0
    assert exp["currency"] == "VND"
    # Commercial honesty notice check
    assert "không phải" in exp["notice"] or "không thu phí" in exp["notice"] or "liên hệ" in exp["notice"]

    # -------------------------------------------------------------------------
    # 7. POST /api/v1/rbpc/inquiries -> 202 Accepted (non-sequential ref & opaque token)
    # -------------------------------------------------------------------------
    future_date = (date.today() + timedelta(days=14)).isoformat()
    unique_idem_key = str(uuid.uuid4())
    inquiry_payload = {
        "experience_slug": "workshop-duc-dong-phuong-duc",
        "contact": {
            "name": "Nguyễn Hoàng Nam",
            "method": "email",
            "value": "nam.nguyen@heritage.vn",
        },
        "preferred_date": future_date,
        "party_size": 2,
        "message": "Gia đình muốn tham gia trải nghiệm tìm hiểu khuôn sáp và đúc chuông.",
        "consent": {
            "version": "rbpc-inquiry-v1",
            "accepted": True,
            "privacy_accepted": True,
        },
        "idempotency_key": unique_idem_key,
    }

    res_inq = client.post("/api/v1/rbpc/inquiries", json=inquiry_payload)
    assert res_inq.status_code == 202, res_inq.text
    inq_res = res_inq.json()
    assert inq_res["status"] == "new"

    # Non-sequential public reference code verification (INQ-XXXX-XXXX)
    public_ref = inq_res["reference"]
    assert re.match(r"^INQ-[A-Z0-9]{4}-[A-Z0-9]{4}$", public_ref), f"Invalid non-sequential format: {public_ref}"

    # High-entropy opaque secret token verification (tok_sec_...)
    status_token = inq_res["status_token"]
    assert status_token.startswith("tok_sec_"), f"Invalid token format: {status_token}"
    assert len(status_token) >= 24

    # -------------------------------------------------------------------------
    # 8. GET /api/v1/rbpc/inquiries/status/{opaqueToken} -> 200 OK (Zero PII)
    # -------------------------------------------------------------------------
    res_status = client.get(f"/api/v1/rbpc/inquiries/status/{status_token}")
    assert res_status.status_code == 200, res_status.text
    st_data = res_status.json()
    assert st_data["reference"] == public_ref
    assert st_data["status"] == "new"
    assert st_data["party_size"] == 2
    assert st_data["preferred_date"] == future_date
    assert len(st_data["experience_title"]) > 0

    # STRICT ZERO PII INVARIANT ASSERTIONS:
    FORBIDDEN_PII = {
        "email", "phone", "name", "contact", "message",
        "internal_note", "contact_value", "contact_channel",
        "user_id", "guest_name", "phone_number", "customer_name"
    }
    for forbidden_key in FORBIDDEN_PII:
        assert forbidden_key not in st_data, f"CRITICAL LEAK: Found PII key '{forbidden_key}' in public inquiry status!"

    # -------------------------------------------------------------------------
    # 9. GET /api/v1/rbpc/impact -> 200 OK (Verified 202,360,638 VND Support)
    # -------------------------------------------------------------------------
    res_impact = client.get("/api/v1/rbpc/impact")
    assert res_impact.status_code == 200, res_impact.text
    impact = res_impact.json()

    assert impact["scope"] == "RBPC_HUE"
    observed = impact["observed_metrics"]
    projected = impact["projected_metrics"]

    # Exact verification: 202,360,638 VND sponsor in-kind support (BNIX + Phổ Tuệ)
    assert observed["sponsor_support_vnd_verified"] == 202360638.0
    assert observed["total_inquiries_received"] >= 1
    assert observed["published_stories_count"] >= 3
    assert observed["consented_creators_count"] >= 3
    assert observed["active_experiences_count"] >= 3
    assert observed["verified_heritage_places_count"] >= 1
    assert observed["verified_source_citations_count"] >= 1

    # Commercial projection basis disclosure
    assert projected["estimated_monthly_demand"] > 0
    assert projected["projected_local_value_addition_vnd"] > 0
    assert "giả định" in projected["projection_basis"]


# --------------------------------------------------------------------------- #
# Error Handling & Standard Envelope Tests
# --------------------------------------------------------------------------- #
def test_heritage_error_envelopes(client, seeded_demo_data):
    """Test standard error envelope on heritage catalogue failure modes."""
    # 1. Unknown place slug -> 404 HERITAGE_PLACE_NOT_FOUND
    res_404 = client.get("/api/v1/heritage/places/unknown-palace-slug/detail")
    err_404 = assert_error_envelope(res_404, 404, "HERITAGE_PLACE_NOT_FOUND")
    assert "unknown-palace-slug" in err_404["message"]

    # 2. Malformed place slug -> 400 INVALID_INPUT
    res_bad_slug = client.get("/api/v1/heritage/places/invalid!slug@format#/detail")
    err_bad_slug = assert_error_envelope(res_bad_slug, 400, "INVALID_INPUT")
    assert "Malformed slug" in err_bad_slug["message"]

    # 3. Foreign scope leak -> 400 FORBIDDEN_SCOPE
    res_bad_scope = client.get("/api/v1/heritage/places", params={"content_scope": "UNAUTHORIZED_SCOPE"})
    err_bad_scope = assert_error_envelope(res_bad_scope, 400, "FORBIDDEN_SCOPE")
    assert "RBPC_HUE" in err_bad_scope["message"]

    # 4. Limit validation violation (> 100) -> 422 VALIDATION_ERROR
    res_limit = client.get("/api/v1/heritage/places", params={"limit": 500})
    err_limit = assert_error_envelope(res_limit, 422, "VALIDATION_ERROR")
    assert "errors" in err_limit["details"]

    # 5. Public access to draft place -> 404 HERITAGE_PLACE_NOT_FOUND
    res_draft = client.get("/api/v1/heritage/places/draft-secret-shrine/detail")
    assert_error_envelope(res_draft, 404, "HERITAGE_PLACE_NOT_FOUND")


def test_cultural_bridge_error_envelopes_and_fail_closed(client, seeded_demo_data):
    """Test Cultural Bridge failure modes and fail-closed structured responses."""
    # 1. Missing required payload fields -> 422 VALIDATION_ERROR
    res_invalid = client.post("/api/v1/rbpc/cultural-bridge", json={})
    err_invalid = assert_error_envelope(res_invalid, 422, "VALIDATION_ERROR")
    assert "errors" in err_invalid["details"]

    # 2. Malformed story slug -> 400 INVALID_INPUT
    res_bad_slug = client.post(
        "/api/v1/rbpc/cultural-bridge",
        json={
            "story_slug": "invalid/story/slug!",
            "question": "Tìm hiểu di sản?",
            "locale": "vi",
        },
    )
    assert_error_envelope(res_bad_slug, 400, "INVALID_INPUT")

    # 3. Unknown story slug -> 200 fail-closed structured refusal (zero hallucination)
    res_unknown = client.post(
        "/api/v1/rbpc/cultural-bridge",
        json={
            "story_slug": "non-existent-story-slug",
            "question": "Bí mật chế tác là gì?",
            "locale": "vi",
        },
    )
    assert res_unknown.status_code == 200
    unknown_data = res_unknown.json()
    assert unknown_data["status"] == "insufficient_evidence"
    assert unknown_data["citations"] == []
    assert unknown_data["epistemic_certainty"] == "insufficient_sources"
    assert unknown_data["review_status"] == "editorial_fallback"


def test_creator_error_envelopes(client, seeded_demo_data):
    """Test standard error envelope on creator profile endpoints."""
    # 1. Unknown creator slug -> 404 RBPC_CREATOR_NOT_FOUND
    res_404 = client.get("/api/v1/rbpc/creators/unknown-artisan-xyz")
    err_404 = assert_error_envelope(res_404, 404, "RBPC_CREATOR_NOT_FOUND")
    assert "unknown-artisan-xyz" in err_404["message"]

    # 2. Malformed slug -> 400 INVALID_INPUT
    res_bad_slug = client.get("/api/v1/rbpc/creators/invalid!creator@#")
    assert_error_envelope(res_bad_slug, 400, "INVALID_INPUT")

    # 3. Creator with revoked consent -> 404 RBPC_CREATOR_NOT_FOUND (Consent gate)
    res_revoked = client.get("/api/v1/rbpc/creators/nghe-nhan-rut-dong-thuan")
    assert_error_envelope(res_revoked, 404, "RBPC_CREATOR_NOT_FOUND")


def test_experience_error_envelopes(client, seeded_demo_data):
    """Test standard error envelope on experience offerings."""
    # 1. Unknown experience slug -> 404 RBPC_EXPERIENCE_NOT_FOUND
    res_404 = client.get("/api/v1/rbpc/experiences/unknown-workshop-xyz")
    err_404 = assert_error_envelope(res_404, 404, "RBPC_EXPERIENCE_NOT_FOUND")
    assert "unknown-workshop-xyz" in err_404["message"]

    # 2. Malformed experience slug -> 400 INVALID_INPUT
    res_bad_slug = client.get("/api/v1/experiences/bad!slug@#")
    # Note: /api/v1/experiences does not match /api/v1/rbpc/experiences, test full route
    res_bad_slug_rbpc = client.get("/api/v1/rbpc/experiences/bad!slug@#")
    assert_error_envelope(res_bad_slug_rbpc, 400, "INVALID_INPUT")

    # 3. Draft/unpublished experience -> 404 RBPC_EXPERIENCE_NOT_FOUND
    res_draft = client.get("/api/v1/rbpc/experiences/workshop-nhap-chua-xuat-ban")
    assert_error_envelope(res_draft, 404, "RBPC_EXPERIENCE_NOT_FOUND")


def test_inquiry_error_envelopes_and_hardening(client, seeded_demo_data):
    """Test standard error envelope on inquiry validation, anti-spam, and security rules."""
    future_date = (date.today() + timedelta(days=7)).isoformat()
    past_date = (date.today() - timedelta(days=2)).isoformat()
    unique_key = str(uuid.uuid4())

    base_payload = {
        "experience_slug": "workshop-duc-dong-phuong-duc",
        "contact": {
            "name": "Trần Thị Bích",
            "method": "email",
            "value": "bich.tran@example.vn",
        },
        "preferred_date": future_date,
        "party_size": 2,
        "message": "Đăng ký tham quan xưởng đúc đồng.",
        "consent": {
            "version": "rbpc-inquiry-v1",
            "accepted": True,
            "privacy_accepted": True,
        },
        "idempotency_key": unique_key,
    }

    # 1. Unaccepted explicit consent -> 422 standard error envelope (VALIDATION_ERROR)
    payload_no_consent = dict(base_payload)
    payload_no_consent["consent"] = {"version": "rbpc-inquiry-v1", "accepted": False, "privacy_accepted": True}
    res_no_consent = client.post("/api/v1/rbpc/inquiries", json=payload_no_consent)
    err_no_consent = assert_error_envelope(res_no_consent, 422)
    assert err_no_consent["code"] in ("VALIDATION_ERROR", "RBPC_CONSENT_REQUIRED")

    # 2. Unaccepted privacy policy -> 422 standard error envelope (VALIDATION_ERROR)
    payload_no_privacy = dict(base_payload)
    payload_no_privacy["consent"] = {"version": "rbpc-inquiry-v1", "accepted": True, "privacy_accepted": False}
    res_no_privacy = client.post("/api/v1/rbpc/inquiries", json=payload_no_privacy)
    err_no_privacy = assert_error_envelope(res_no_privacy, 422)
    assert err_no_privacy["code"] in ("VALIDATION_ERROR", "RBPC_CONSENT_REQUIRED")

    # 3. Preferred date in the past -> 422 standard error envelope (VALIDATION_ERROR or RBPC_DATE_PAST)
    payload_past_date = dict(base_payload)
    payload_past_date["preferred_date"] = past_date
    res_past = client.post("/api/v1/rbpc/inquiries", json=payload_past_date)
    err_past = assert_error_envelope(res_past, 422)
    assert err_past["code"] in ("VALIDATION_ERROR", "RBPC_DATE_PAST")

    # 4. Anti-spam: XSS Script tag injection -> 422 RBPC_SPAM_DETECTED
    payload_xss = dict(base_payload)
    payload_xss["message"] = "Đăng ký xem <script>alert('pwned')</script> xưởng"
    res_xss = client.post("/api/v1/rbpc/inquiries", json=payload_xss)
    assert_error_envelope(res_xss, 422, "RBPC_SPAM_DETECTED")

    # 5. Anti-spam: Commercial spam keywords -> 422 RBPC_SPAM_DETECTED
    payload_spam = dict(base_payload)
    payload_spam["message"] = "Join our online crypto casino and win free spins"
    res_spam = client.post("/api/v1/rbpc/inquiries", json=payload_spam)
    assert_error_envelope(res_spam, 422, "RBPC_SPAM_DETECTED")

    # 6. Unknown experience slug -> 404 RBPC_EXPERIENCE_NOT_FOUND
    payload_unknown_exp = dict(base_payload)
    payload_unknown_exp["experience_slug"] = "unknown-experience-xyz"
    res_unknown_exp = client.post("/api/v1/rbpc/inquiries", json=payload_unknown_exp)
    assert_error_envelope(res_unknown_exp, 404, "RBPC_EXPERIENCE_NOT_FOUND")

    # 7. Invalid idempotency key format -> 422 standard error envelope
    payload_bad_key = dict(base_payload)
    payload_bad_key["idempotency_key"] = "not-a-valid-uuid-key"
    res_bad_key = client.post("/api/v1/rbpc/inquiries", json=payload_bad_key)
    err_bad_key = assert_error_envelope(res_bad_key, 422)
    assert err_bad_key["code"] in ("VALIDATION_ERROR", "RBPC_INVALID_IDEMPOTENCY_KEY")

    # 8. Successful initial creation -> 202
    res_initial = client.post("/api/v1/rbpc/inquiries", json=base_payload)
    assert res_initial.status_code == 202

    # 9. Idempotency Conflict: same key with modified party_size -> 409 RBPC_IDEMPOTENCY_CONFLICT
    payload_conflict = dict(base_payload)
    payload_conflict["party_size"] = 10
    res_conflict = client.post("/api/v1/rbpc/inquiries", json=payload_conflict)
    err_conflict = assert_error_envelope(res_conflict, 409, "RBPC_IDEMPOTENCY_CONFLICT")
    assert "differing" in err_conflict["message"] or "idempotency" in err_conflict["message"].lower()


def test_inquiry_rate_limiting_enforcement(client, seeded_demo_data):
    """Test rate limiting enforcement (max 5 requests per IP/hour) returning standard 429 envelope."""
    _inquiry_rate_limit_store.clear()

    future_date = (date.today() + timedelta(days=10)).isoformat()
    base_payload = {
        "experience_slug": "workshop-duc-dong-phuong-duc",
        "contact": {
            "name": "Lê Bảo Trâm",
            "method": "email",
            "value": "tram.le@example.vn",
        },
        "preferred_date": future_date,
        "party_size": 2,
        "message": "Kiểm tra giới hạn tần suất gửi yêu cầu trải nghiệm.",
        "consent": {
            "version": "rbpc-inquiry-v1",
            "accepted": True,
            "privacy_accepted": True,
        },
    }

    # First 5 inquiries within the window succeed with 202 Accepted
    for _ in range(5):
        p = dict(base_payload)
        p["idempotency_key"] = str(uuid.uuid4())
        res = client.post("/api/v1/rbpc/inquiries", json=p)
        assert res.status_code == 202, res.text

    # 6th inquiry must be blocked with HTTP 429 RATE_LIMIT_EXCEEDED
    p_blocked = dict(base_payload)
    p_blocked["idempotency_key"] = str(uuid.uuid4())
    res_rate = client.post("/api/v1/rbpc/inquiries", json=p_blocked)
    err_rate = assert_error_envelope(res_rate, 429, "RATE_LIMIT_EXCEEDED")
    assert "Retry-After" in res_rate.headers
    assert res_rate.headers.get("X-RateLimit-Remaining") == "0"
    assert "tối đa 5 yêu cầu/giờ" in err_rate["message"]


def test_inquiry_status_error_envelopes(client, seeded_demo_data):
    """Test standard error envelope on inquiry status lookup failure modes."""
    # 1. Unknown token -> 404 RBPC_INQUIRY_NOT_FOUND
    res_unknown = client.get("/api/v1/rbpc/inquiries/status/tok_sec_nonexistent123456789")
    assert_error_envelope(res_unknown, 404, "RBPC_INQUIRY_NOT_FOUND")

    # 2. Whitespace token -> 404 RBPC_INQUIRY_NOT_FOUND
    res_blank = client.get("/api/v1/rbpc/inquiries/status/%20")
    assert_error_envelope(res_blank, 404, "RBPC_INQUIRY_NOT_FOUND")


def test_inquiry_idempotent_replay_reliability(client, db_session, seeded_demo_data):
    """Test that idempotent replay returns identical tokens and does not create duplicate DB records."""
    future_date = (date.today() + timedelta(days=20)).isoformat()
    unique_key = str(uuid.uuid4())

    payload = {
        "experience_slug": "workshop-duc-dong-phuong-duc",
        "contact": {
            "name": "Hoàng Minh Tuấn",
            "method": "email",
            "value": "tuan.hoang@example.vn",
        },
        "preferred_date": future_date,
        "party_size": 4,
        "message": "Trải nghiệm văn hóa cuối tuần cho nhóm 4 người.",
        "consent": {
            "version": "rbpc-inquiry-v1",
            "accepted": True,
            "privacy_accepted": True,
        },
        "idempotency_key": unique_key,
    }

    # Initial submission -> 202
    res_first = client.post("/api/v1/rbpc/inquiries", json=payload)
    assert res_first.status_code == 202
    data_first = res_first.json()

    # Replay submission with exact same key & payload -> 202 with identical tokens
    res_second = client.post("/api/v1/rbpc/inquiries", json=payload)
    assert res_second.status_code == 202
    data_second = res_second.json()

    assert data_second["reference"] == data_first["reference"]
    assert data_second["status_token"] == data_first["status_token"]
    assert data_second["status"] == data_first["status"]

    # Verify database has exactly 1 record for this idempotency key
    inquiries = list(db_session.scalars(select(RbpcInquiry).where(RbpcInquiry.idempotency_key == unique_key)))
    assert len(inquiries) == 1, f"Expected exactly 1 inquiry in DB, found {len(inquiries)}"
