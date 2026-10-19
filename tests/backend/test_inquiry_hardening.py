# -*- coding: utf-8 -*-
"""Automated unit and integration tests for Experience & Inquiry API hardening.

Phase 3 / AGENT 02:
- Strict input sanitization and anti-spam validation.
- Missing or unaccepted explicit consent rejection (HTTP 422).
- Client UUID idempotency key checking and idempotent replay (HTTP 202).
- Zero PII leakage invariant on public status lookup via opaque token.
- Inquiry submission rate-limiting (max 5 requests per IP/hour, HTTP 429).
- Bibliographic source evidence and rights-cleared media on heritage endpoints.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from backend.models import User, UserRole
from backend.models_rbpc import (
    HeritageAccuracyGrade,
    HeritageCommercialUseStatus,
    HeritageEmbedPermissionStatus,
    HeritageMediaAsset,
    HeritageMediaType,
    HeritagePlace,
    HeritageRecordStatus,
    HeritageSourceEvidence,
    RbpcConsentStatus,
    RbpcCreator,
    RbpcExperience,
    RbpcInquiry,
    RbpcInquiryStatus,
)
from backend.routers.rbpc import _inquiry_rate_limit_store
from backend.security import hash_password


@pytest.fixture(autouse=True)
def clean_inquiry_rate_limiter():
    """Reset rate limiter state before each test for deterministic test isolation."""
    _inquiry_rate_limit_store.clear()
    yield
    _inquiry_rate_limit_store.clear()


def _seed_test_experience(db_session, slug="workshop-hardening-test") -> tuple[RbpcCreator, RbpcExperience]:
    """Helper to seed a consented creator and published experience."""
    creator = RbpcCreator(
        slug=f"artisan-{slug}",
        public_name="Nghệ nhân Đỗ Kỳ",
        craft_tradition="Đúc đồng Phường Đúc",
        approved_bio_vi="Nghệ nhân ưu tú kế thừa kỹ nghệ đúc đồng gia truyền.",
        approved_bio_en="Master bronze caster carrying on ancestral casting traditions.",
        consent_status=RbpcConsentStatus.consented.value,
    )
    db_session.add(creator)
    db_session.flush()

    exp = RbpcExperience(
        slug=slug,
        creator_id=creator.id,
        provider_name="Phường Đúc Đồng Đỗ Kỳ",
        title_vi="Workshop đúc chuông đồng mini Huế",
        title_en="Hue Mini Bronze Bell Casting Workshop",
        description_vi="Trải nghiệm tạo khuôn đất và rót đồng nóng chảy cùng nghệ nhân.",
        description_en="Experience clay mold crafting and molten bronze casting with the master.",
        area_public="Phường Đúc, TP. Huế",
        duration_minutes=180,
        pricing_display="450.000 VND / khách",
        indicative_price_amount=450000.0,
        currency="VND",
        publication_state="published",
        availability_mode="inquiry_only",
        notice="Yêu cầu trải nghiệm chỉ là bước liên hệ xác nhận lịch trống, không phải thanh toán tức thì.",
    )
    db_session.add(exp)
    db_session.commit()
    db_session.refresh(exp)
    return creator, exp


# --------------------------------------------------------------------------- #
# 1. Consent Enforcement Tests (HTTP 422)
# --------------------------------------------------------------------------- #
def test_missing_or_unaccepted_consent_rejection(client, db_session):
    """Verify that requests with missing consent, accepted=False, or privacy_accepted=False are rejected with HTTP 422."""
    _, exp = _seed_test_experience(db_session, "exp-consent-test")
    future_date = (date.today() + timedelta(days=7)).isoformat()
    valid_key = str(uuid.uuid4())

    base_payload = {
        "experience_slug": exp.slug,
        "contact": {
            "name": "Trần Thị Mai",
            "method": "email",
            "value": "mai.tran@example.com",
        },
        "preferred_date": future_date,
        "party_size": 2,
        "message": "Mong muốn trải nghiệm vào buổi sáng.",
        "idempotency_key": valid_key,
    }

    # Case 1: Missing consent object entirely
    payload_missing = dict(base_payload)
    res_missing = client.post("/api/v1/rbpc/inquiries", json=payload_missing)
    assert res_missing.status_code == 422, res_missing.text

    # Case 2: Explicit consent checkbox is False
    payload_unaccepted = dict(base_payload)
    payload_unaccepted["consent"] = {
        "version": "rbpc-inquiry-v1",
        "accepted": False,
        "privacy_accepted": True,
    }
    payload_unaccepted["idempotency_key"] = str(uuid.uuid4())
    res_unaccepted = client.post("/api/v1/rbpc/inquiries", json=payload_unaccepted)
    assert res_unaccepted.status_code == 422, res_unaccepted.text

    # Case 3: Privacy policy acceptance is False
    payload_privacy_false = dict(base_payload)
    payload_privacy_false["consent"] = {
        "version": "rbpc-inquiry-v1",
        "accepted": True,
        "privacy_accepted": False,
    }
    payload_privacy_false["idempotency_key"] = str(uuid.uuid4())
    res_privacy = client.post("/api/v1/rbpc/inquiries", json=payload_privacy_false)
    assert res_privacy.status_code == 422, res_privacy.text


# --------------------------------------------------------------------------- #
# 2. Idempotency Key Checking & Replay (HTTP 202)
# --------------------------------------------------------------------------- #
def test_idempotency_replay_and_conflict(client, db_session):
    """Verify that idempotent submission returns identical non-duplicate receipt (HTTP 202), and conflict returns HTTP 409."""
    _, exp = _seed_test_experience(db_session, "exp-idempotency-test")
    future_date = (date.today() + timedelta(days=14)).isoformat()
    client_uuid = str(uuid.uuid4())

    valid_payload = {
        "experience_slug": exp.slug,
        "contact": {
            "name": "Lê Hoàng Nam",
            "method": "email",
            "value": "nam.le@example.org",
        },
        "preferred_date": future_date,
        "party_size": 3,
        "message": "Có đoàn khách nước ngoài cần phiên dịch tiếng Anh.",
        "consent": {
            "version": "rbpc-inquiry-v1",
            "accepted": True,
            "privacy_accepted": True,
        },
        "idempotency_key": client_uuid,
    }

    # 1. First submission -> Accepted (HTTP 202)
    res_first = client.post("/api/v1/rbpc/inquiries", json=valid_payload)
    assert res_first.status_code == 202, res_first.text
    first_data = res_first.json()
    assert first_data["status"] == "new"
    assert first_data["reference"].startswith("INQ-")
    assert first_data["status_token"].startswith("tok_sec_")

    # 2. Idempotent replay: exact same payload and key -> returns identical receipt
    res_replay = client.post("/api/v1/rbpc/inquiries", json=valid_payload)
    assert res_replay.status_code == 202, res_replay.text
    replay_data = res_replay.json()
    assert replay_data["reference"] == first_data["reference"]
    assert replay_data["status_token"] == first_data["status_token"]
    assert replay_data["status"] == first_data["status"]

    # Invariant: DB contains exactly 1 record for this idempotency key
    records = list(db_session.scalars(select(RbpcInquiry).where(RbpcInquiry.idempotency_key == client_uuid)))
    assert len(records) == 1

    # 3. Idempotency conflict: same key but differing party_size -> HTTP 409 Conflict
    conflict_payload = dict(valid_payload)
    conflict_payload["party_size"] = 12
    res_conflict = client.post("/api/v1/rbpc/inquiries", json=conflict_payload)
    assert res_conflict.status_code == 409, res_conflict.text
    assert res_conflict.json()["error"]["code"] == "RBPC_IDEMPOTENCY_CONFLICT"


def test_invalid_client_uuid_idempotency_key(client, db_session):
    """Verify that a non-UUID idempotency key is rejected with HTTP 422."""
    _, exp = _seed_test_experience(db_session, "exp-invalid-uuid-test")
    future_date = (date.today() + timedelta(days=5)).isoformat()

    payload = {
        "experience_slug": exp.slug,
        "contact": {"name": "Test User", "method": "email", "value": "test@example.com"},
        "preferred_date": future_date,
        "party_size": 1,
        "consent": {"version": "v1", "accepted": True, "privacy_accepted": True},
        "idempotency_key": "not-a-valid-uuid-at-all",
    }
    res = client.post("/api/v1/rbpc/inquiries", json=payload)
    assert res.status_code == 422, res.text


# --------------------------------------------------------------------------- #
# 3. Status Lookup via Opaque Token with Zero PII Leakage
# --------------------------------------------------------------------------- #
def test_status_lookup_zero_pii_leakage(client, db_session):
    """Verify status query by high-entropy opaque token returns only lifecycle info with ZERO PII leakage."""
    _, exp = _seed_test_experience(db_session, "exp-status-pii-test")
    future_date = (date.today() + timedelta(days=20)).isoformat()
    client_uuid = str(uuid.uuid4())

    submit_payload = {
        "experience_slug": exp.slug,
        "contact": {
            "name": "Nguyễn Hoàng Minh",
            "method": "email",
            "value": "minh.nguyen@example.com",
        },
        "preferred_date": future_date,
        "party_size": 4,
        "message": "Số điện thoại dự phòng: 0912345678. Tôi ăn chay trường.",
        "consent": {
            "version": "rbpc-inquiry-v1",
            "accepted": True,
            "privacy_accepted": True,
        },
        "idempotency_key": client_uuid,
    }

    res_submit = client.post("/api/v1/rbpc/inquiries", json=submit_payload)
    assert res_submit.status_code == 202
    opaque_token = res_submit.json()["status_token"]
    reference = res_submit.json()["reference"]

    # Status check via token
    res_status = client.get(f"/api/v1/rbpc/inquiries/status/{opaque_token}")
    assert res_status.status_code == 200, res_status.text
    st_data = res_status.json()

    # Allowed non-sensitive lifecycle fields
    assert st_data["reference"] == reference
    assert st_data["experience_title"] == exp.title_vi
    assert st_data["status"] == "new"
    assert "tiếp nhận" in st_data["status_message"].lower()
    assert st_data["preferred_date"] == future_date
    assert st_data["party_size"] == 4
    assert "last_updated_at" in st_data

    # STRICT ZERO PII INVARIANT ASSERTIONS:
    assert "name" not in st_data
    assert "email" not in st_data
    assert "phone" not in st_data
    assert "contact" not in st_data
    assert "contact_value" not in st_data
    assert "contact_channel" not in st_data
    assert "message" not in st_data
    assert "internal_note" not in st_data
    assert "user_id" not in st_data
    assert "provider_id" not in st_data
    assert "ip_address" not in st_data

    # Raw response body check: submitted sensitive values must not be present
    raw_text = res_status.text.lower()
    assert "minh.nguyen@example.com" not in raw_text
    assert "nguyễn hoàng minh" not in raw_text
    assert "0912345678" not in raw_text
    assert "ăn chay" not in raw_text

    # Unknown token returns 404
    res_404 = client.get(f"/api/v1/rbpc/inquiries/status/tok_sec_nonexistent_token_123456789")
    assert res_404.status_code == 404
    assert res_404.json()["error"]["code"] == "RBPC_INQUIRY_NOT_FOUND"


# --------------------------------------------------------------------------- #
# 4. Rate Limit Enforcement (Max 5 requests per IP / hour)
# --------------------------------------------------------------------------- #
def test_rate_limit_enforcement(client, db_session):
    """Verify rate-limiting on inquiry submissions enforces max 5 requests per IP/hour (HTTP 429)."""
    _, exp = _seed_test_experience(db_session, "exp-rate-limit-test")
    future_date = (date.today() + timedelta(days=10)).isoformat()
    test_ip = "198.51.100.99"

    # Send 5 valid inquiries from test_ip -> all must succeed with 202
    for i in range(5):
        payload = {
            "experience_slug": exp.slug,
            "contact": {
                "name": f"Khách Hàng {i}",
                "method": "email",
                "value": f"user{i}@example.com",
            },
            "preferred_date": future_date,
            "party_size": 2,
            "consent": {
                "version": "rbpc-inquiry-v1",
                "accepted": True,
                "privacy_accepted": True,
            },
            "idempotency_key": str(uuid.uuid4()),
        }
        res = client.post(
            "/api/v1/rbpc/inquiries",
            json=payload,
            headers={"X-Forwarded-For": test_ip},
        )
        assert res.status_code == 202, f"Request {i+1} failed: {res.text}"

    # 6th inquiry from the same IP -> must be rejected with HTTP 429 Too Many Requests
    payload_6th = {
        "experience_slug": exp.slug,
        "contact": {
            "name": "Khách Hàng Thứ Sáu",
            "method": "email",
            "value": "user6@example.com",
        },
        "preferred_date": future_date,
        "party_size": 2,
        "consent": {
            "version": "rbpc-inquiry-v1",
            "accepted": True,
            "privacy_accepted": True,
        },
        "idempotency_key": str(uuid.uuid4()),
    }
    res_6th = client.post(
        "/api/v1/rbpc/inquiries",
        json=payload_6th,
        headers={"X-Forwarded-For": test_ip},
    )
    assert res_6th.status_code == 429, res_6th.text
    err_json = res_6th.json()
    assert err_json["error"]["code"] == "RATE_LIMIT_EXCEEDED"
    assert "tối đa 5 yêu cầu/giờ" in err_json["error"]["message"]

    # Rate limit headers check
    assert res_6th.headers.get("X-RateLimit-Limit") == "5"
    assert res_6th.headers.get("X-RateLimit-Remaining") == "0"
    assert "Retry-After" in res_6th.headers
    assert int(res_6th.headers["Retry-After"]) > 0

    # Different IP is not affected (per-IP rate limiting isolation)
    different_ip = "198.51.100.100"
    payload_diff_ip = dict(payload_6th)
    payload_diff_ip["idempotency_key"] = str(uuid.uuid4())
    res_diff = client.post(
        "/api/v1/rbpc/inquiries",
        json=payload_diff_ip,
        headers={"X-Forwarded-For": different_ip},
    )
    assert res_diff.status_code == 202, f"Different IP should succeed: {res_diff.text}"


# --------------------------------------------------------------------------- #
# 5. Input Sanitization & Anti-Spam Validation
# --------------------------------------------------------------------------- #
def test_input_sanitization_and_anti_spam(client, db_session):
    """Verify input sanitization strips HTML tags and anti-spam blocks malicious payloads."""
    _, exp = _seed_test_experience(db_session, "exp-anti-spam-test")
    future_date = (date.today() + timedelta(days=12)).isoformat()

    # Case 1: Script injection in name -> HTTP 422 RBPC_SPAM_DETECTED
    res_script = client.post(
        "/api/v1/rbpc/inquiries",
        json={
            "experience_slug": exp.slug,
            "contact": {
                "name": "<script>alert('xss')</script>",
                "method": "email",
                "value": "bot@spam.com",
            },
            "preferred_date": future_date,
            "party_size": 1,
            "consent": {"version": "v1", "accepted": True, "privacy_accepted": True},
            "idempotency_key": str(uuid.uuid4()),
        },
    )
    assert res_script.status_code == 422
    assert res_script.json()["error"]["code"] == "RBPC_SPAM_DETECTED"

    # Case 2: Spam keyword in message -> HTTP 422 RBPC_SPAM_DETECTED
    res_spam_kw = client.post(
        "/api/v1/rbpc/inquiries",
        json={
            "experience_slug": exp.slug,
            "contact": {
                "name": "Casino Bot",
                "method": "email",
                "value": "promo@crypto-casino.com",
            },
            "preferred_date": future_date,
            "party_size": 1,
            "message": "Visit our casino website for free crypto spins!",
            "consent": {"version": "v1", "accepted": True, "privacy_accepted": True},
            "idempotency_key": str(uuid.uuid4()),
        },
    )
    assert res_spam_kw.status_code == 422
    assert res_spam_kw.json()["error"]["code"] == "RBPC_SPAM_DETECTED"

    # Case 3: Excessive links in message -> HTTP 422 RBPC_SPAM_DETECTED
    res_links = client.post(
        "/api/v1/rbpc/inquiries",
        json={
            "experience_slug": exp.slug,
            "contact": {
                "name": "Link Spammer",
                "method": "email",
                "value": "spammer@links.com",
            },
            "preferred_date": future_date,
            "party_size": 1,
            "message": "Check https://spam1.com and https://spam2.com and https://spam3.com now!",
            "consent": {"version": "v1", "accepted": True, "privacy_accepted": True},
            "idempotency_key": str(uuid.uuid4()),
        },
    )
    assert res_links.status_code == 422
    assert res_links.json()["error"]["code"] == "RBPC_SPAM_DETECTED"

    # Case 4: Repetitive character flooding -> HTTP 422 RBPC_SPAM_DETECTED
    res_repeat = client.post(
        "/api/v1/rbpc/inquiries",
        json={
            "experience_slug": exp.slug,
            "contact": {
                "name": "A" * 25,
                "method": "email",
                "value": "bot@repeat.com",
            },
            "preferred_date": future_date,
            "party_size": 1,
            "consent": {"version": "v1", "accepted": True, "privacy_accepted": True},
            "idempotency_key": str(uuid.uuid4()),
        },
    )
    assert res_repeat.status_code == 422
    assert res_repeat.json()["error"]["code"] == "RBPC_SPAM_DETECTED"


# --------------------------------------------------------------------------- #
# 6. Heritage Detail Bibliographic Sources & Rights-Cleared Media
# --------------------------------------------------------------------------- #
def test_heritage_detail_bibliographic_sources_and_rights_cleared_media(client, db_session):
    """Verify heritage place detail returns complete bibliographic source citations and rights-cleared media."""
    place = HeritagePlace(
        slug="dien-kien-trung-hardening-test",
        name_vi="Điện Kiến Trung",
        name_en="Kien Trung Palace",
        entity_type="monument",
        heritage_category="imperial_architecture",
        official_designation="UNESCO World Heritage Component",
        official_reference_id="678-001-KT",
        editorial_status=HeritageRecordStatus.published.value,
        content_scope="RBPC_HUE",
        location_lat=16.4712,
        location_lon=107.5789,
        visitor_summary_vi="Kiến trúc cung điện đỉnh cao kết hợp tinh hoa Âu - Á thời Nguyễn.",
        visitor_summary_en="An imperial palace blending French neoclassical and traditional Vietnamese arts.",
        historical_summary_vi="Khởi công xây dựng dưới triều Khải Định năm 1921 và hoàn tất năm 1923.",
    )
    db_session.add(place)
    db_session.flush()

    # 1. Complete bibliographic source citation
    source = HeritageSourceEvidence(
        place_id=place.id,
        source_title="Đại Nam Thực Lục Chính Biên - Đệ Thất Kỷ",
        source_author="Quốc Sử Quán Triều Nguyễn",
        publisher="NXB Giáo Dục",
        publication_year=2007,
        cited_section="Quyển 4: Kỷ Khải Định Hoàng Đế",
        cited_page="Trang 182-185",
        source_url="https://heritage.example.vn/dai-nam-thuc-luc-kien-trung",
        statement="Điện Kiến Trung được xây dựng làm nơi sinh hoạt và làm việc chính của Hoàng đế Khải Định.",
        interpretation_note="Tài liệu chính sử triều Nguyễn ghi chép chuẩn xác về thời điểm đặt viên đá đầu tiên.",
        evidence_status="verified",
        reuse_rights="public_domain",
        content_scope="RBPC_HUE",
    )
    db_session.add(source)

    # 2. Rights-cleared media asset
    cleared_media = HeritageMediaAsset(
        place_id=place.id,
        media_type=HeritageMediaType.sketchfab_embed.value,
        original_url="https://sketchfab.com/3d-models/kien-trung-palace-verified",
        title="Điện Kiến Trung 3D Photogrammetry",
        creator_name="HueHeritageLab",
        model_uid="kien_trung_cleared_uid_123",
        accuracy_grade=HeritageAccuracyGrade.measured_photogrammetry.value,
        content_status="cleared_for_this_use",
        commercial_use_status=HeritageCommercialUseStatus.permitted.value,
        embed_permission_status=HeritageEmbedPermissionStatus.permitted.value,
        content_scope="RBPC_HUE",
    )

    # 3. Blocked media asset (must be excluded from public detail)
    blocked_media = HeritageMediaAsset(
        place_id=place.id,
        media_type=HeritageMediaType.sketchfab_embed.value,
        original_url="https://sketchfab.com/3d-models/kien-trung-blocked",
        title="Điện Kiến Trung Không Phép",
        creator_name="UnknownScraper",
        model_uid="blocked_uid_999",
        accuracy_grade=HeritageAccuracyGrade.rejected_accuracy.value,
        content_status="rejected_accuracy",
        commercial_use_status=HeritageCommercialUseStatus.blocked_nc.value,
        embed_permission_status=HeritageEmbedPermissionStatus.blocked.value,
        content_scope="RBPC_HUE",
    )

    db_session.add_all([cleared_media, blocked_media])
    db_session.commit()

    # Query place detail endpoint
    res_detail = client.get("/api/v1/heritage/places/dien-kien-trung-hardening-test/detail")
    assert res_detail.status_code == 200, res_detail.text
    detail = res_detail.json()

    # Verify complete bibliographic citation
    assert len(detail["sources"]) == 1
    src = detail["sources"][0]
    assert src["source_title"] == "Đại Nam Thực Lục Chính Biên - Đệ Thất Kỷ"
    assert src["source_author"] == "Quốc Sử Quán Triều Nguyễn"
    assert src["publisher"] == "NXB Giáo Dục"
    assert src["publication_year"] == 2007
    assert src["cited_section"] == "Quyển 4: Kỷ Khải Định Hoàng Đế"
    assert src["cited_page"] == "Trang 182-185"
    assert src["evidence_status"] == "verified"
    assert src["reuse_rights"] == "public_domain"
    assert src["statement"] is not None

    # Verify rights-cleared media (blocked asset strictly omitted)
    assert len(detail["media"]) == 1
    m = detail["media"][0]
    assert m["model_uid"] == "kien_trung_cleared_uid_123"
    assert m["accuracy_grade"] == "measured_photogrammetry"

    # Query media endpoint directly
    res_media = client.get("/api/v1/heritage/places/dien-kien-trung-hardening-test/media")
    assert res_media.status_code == 200
    media_list = res_media.json()
    assert len(media_list) == 1
    assert media_list[0]["model_uid"] == "kien_trung_cleared_uid_123"
