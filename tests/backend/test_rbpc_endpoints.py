# -*- coding: utf-8 -*-
"""Unit and integration tests for LƯU NIÊN RBPC 2026 API endpoints.

Covers:
- Heritage Catalogue public read and detail access.
- Unpublished / draft content isolation guardrails (public 404 vs staff access).
- Sketchfab 3D accuracy grade filtering (blocking SF-020 rejected accuracy).
- Full-text diacritic-tolerant accent-insensitive search.
- Curated cultural stories and source evidence.
- Source-grounded Cultural Bridge AI query scoped strictly to RBPC_HUE.
- Consented creator and inquiry-only experience offerings.
- Inquiry creation with idempotency replay, payload conflict detection, and validation.
- Visitor inquiry status lookup with ZERO PII leakage invariant.
- Verified platform impact metrics (202,360,638 VND sponsor support).
- Authenticated partner inbox and scoped inquiry state transitions.
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
    HeritageHeritageRelation,
    HeritageMediaAsset,
    HeritageMediaType,
    HeritagePlace,
    HeritageRecordStatus,
    HeritageSourceEvidence,
    RbpcClaimEvidence,
    RbpcConsentStatus,
    RbpcCreator,
    RbpcExperience,
    RbpcInquiry,
    RbpcInquiryStatus,
    RbpcStory,
)
from backend.security import hash_password


# --------------------------------------------------------------------------- #
# Test Helpers
# --------------------------------------------------------------------------- #
def _create_user(db_session, email: str, role: UserRole = UserRole.learner) -> User:
    """Helper to create and persist a test user."""
    user = User(
        email=email,
        password_hash=hash_password("password123"),
        display_name=f"User {email.split('@')[0]}",
        role=role,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _login_user(client, email: str) -> None:
    """Helper to log in a user and set access session cookies on client."""
    res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "password123"},
    )
    assert res.status_code == 200, res.text


# --------------------------------------------------------------------------- #
# Test Cases: Heritage Catalogue
# --------------------------------------------------------------------------- #
def test_public_access_heritage_catalogue(client, db_session):
    """Test public browsing and detail view of published heritage places."""
    # 1. Seed a published place with relations, source evidence, and media
    place = HeritagePlace(
        slug="lang-tu-duc",
        name_vi="Lăng Tự Đức",
        name_en="Tomb of Tu Duc",
        entity_type="site",
        heritage_category="royal_tomb",
        official_designation="UNESCO World Heritage Component",
        official_reference_id="678-007",
        editorial_status=HeritageRecordStatus.published.value,
        content_scope="RBPC_HUE",
        location_lat=16.4328,
        location_lon=107.5656,
        visitor_summary_vi="Quần thể lăng tẩm thơ mộng hòa hợp tuyệt đối với thiên nhiên xứ Huế.",
        visitor_summary_en="An imperial tomb complex noted for poetic harmony.",
        historical_summary_vi="Khiêm Lăng được Hoàng đế Tự Đức tự quy hoạch năm 1864.",
    )
    db_session.add(place)
    db_session.flush()

    source = HeritageSourceEvidence(
        place_id=place.id,
        source_title="Complex of Hué Monuments - UNESCO World Heritage Centre",
        source_url="https://whc.unesco.org/en/list/678",
        statement="Lăng Tự Đức được ghi danh trong Quần thể Di tích Cố đô Huế.",
        evidence_status="verified",
        reuse_rights="public_domain",
        content_scope="RBPC_HUE",
    )
    db_session.add(source)

    media = HeritageMediaAsset(
        place_id=place.id,
        media_type=HeritageMediaType.sketchfab_embed.value,
        original_url="https://sketchfab.com/3d-models/tomb-of-tu-duc-77728a86ad1d4964824b63844d50bfe7",
        title="Tomb of Tu Duc",
        creator_name="matousekfoto",
        model_uid="77728a86ad1d4964824b63844d50bfe7",
        accuracy_grade=HeritageAccuracyGrade.measured_photogrammetry.value,
        content_status="cleared_for_this_use",
        commercial_use_status=HeritageCommercialUseStatus.permitted.value,
        embed_permission_status=HeritageEmbedPermissionStatus.permitted.value,
        content_scope="RBPC_HUE",
    )
    db_session.add(media)
    db_session.commit()

    # 2. Public list places without authentication
    res = client.get("/api/v1/heritage/places")
    assert res.status_code == 200, res.text
    data = res.json()
    assert "items" in data
    assert data["total_count"] >= 1
    item = next((i for i in data["items"] if i["slug"] == "lang-tu-duc"), None)
    assert item is not None
    assert item["name_vi"] == "Lăng Tự Đức"
    assert item["has_3d"] is True

    # 3. Public get detail
    res_detail = client.get("/api/v1/heritage/places/lang-tu-duc")
    assert res_detail.status_code == 200, res_detail.text
    detail = res_detail.json()
    assert detail["slug"] == "lang-tu-duc"
    assert detail["historical_summary_vi"] is not None
    assert len(detail["sources"]) >= 1
    assert detail["sources"][0]["source_title"] == "Complex of Hué Monuments - UNESCO World Heritage Centre"
    assert len(detail["media"]) >= 1

    # 4. Public get media
    res_media = client.get("/api/v1/heritage/places/lang-tu-duc/media")
    assert res_media.status_code == 200
    media_list = res_media.json()
    assert len(media_list) >= 1
    assert media_list[0]["model_uid"] == "77728a86ad1d4964824b63844d50bfe7"

    # 5. Public get 3D models
    res_3d = client.get("/api/v1/heritage/places/lang-tu-duc/3d")
    assert res_3d.status_code == 200
    models_3d = res_3d.json()
    assert len(models_3d) >= 1
    assert models_3d[0]["accuracy_grade"] == "measured_photogrammetry"

    # 6. Unknown place 404
    res_404 = client.get("/api/v1/heritage/places/unknown-slug-xyz")
    assert res_404.status_code == 404
    assert res_404.json()["error"]["code"] == "HERITAGE_PLACE_NOT_FOUND"

    # 7. Malformed slug parameter -> 400 Bad Request
    res_bad_slug = client.get("/api/v1/heritage/places/invalid!slug@format#")
    assert res_bad_slug.status_code == 400
    assert res_bad_slug.json()["error"]["code"] == "INVALID_INPUT"

    # 8. Foreign content_scope leak attempt -> 400 Bad Request
    res_leak = client.get("/api/v1/heritage/places", params={"content_scope": "CUU_DINH"})
    assert res_leak.status_code == 400
    assert res_leak.json()["error"]["code"] == "FORBIDDEN_SCOPE"


def test_sf020_accuracy_guardrail_blocking(client, db_session):
    """Verify that SF-020 and any models with accuracy_grade='rejected_accuracy' are strictly blocked."""
    place = HeritagePlace(
        slug="dai-noi-hue-test",
        name_vi="Đại Nội Huế",
        entity_type="monument",
        heritage_category="imperial_architecture",
        editorial_status=HeritageRecordStatus.published.value,
        content_scope="RBPC_HUE",
    )
    db_session.add(place)
    db_session.flush()

    # Good model: measured photogrammetry
    good_model = HeritageMediaAsset(
        place_id=place.id,
        media_type=HeritageMediaType.sketchfab_embed.value,
        original_url="https://sketchfab.com/3d-models/good-photogrammetry-model",
        title="Verified Meridian Gate",
        model_uid="good_uid_12345",
        accuracy_grade=HeritageAccuracyGrade.measured_photogrammetry.value,
        content_status="cleared_for_this_use",
        embed_permission_status=HeritageEmbedPermissionStatus.permitted.value,
        commercial_use_status=HeritageCommercialUseStatus.permitted.value,
        content_scope="RBPC_HUE",
    )
    # Bad model (SF-020): rejected accuracy
    sf020 = HeritageMediaAsset(
        place_id=place.id,
        media_type=HeritageMediaType.sketchfab_embed.value,
        original_url="https://sketchfab.com/3d-models/ai-noi-hue-van-hoa-viet-nam-84a8ab573293497ab0d4f97b4650bb55",
        title="SF-020 Imagined Architecture",
        creator_name="nguyenduc0",
        model_uid="84a8ab573293497ab0d4f97b4650bb55",
        accuracy_grade=HeritageAccuracyGrade.rejected_accuracy.value,
        content_status="rejected_accuracy",
        embed_permission_status=HeritageEmbedPermissionStatus.blocked.value,
        commercial_use_status=HeritageCommercialUseStatus.blocked_nc.value,
        content_scope="RBPC_HUE",
    )
    db_session.add_all([good_model, sf020])
    db_session.commit()

    # Query 3D models endpoint
    res = client.get("/api/v1/heritage/places/dai-noi-hue-test/3d")
    assert res.status_code == 200
    models = res.json()
    uids = [m["model_uid"] for m in models]

    # Verify good model is present and SF-020 is strictly excluded!
    assert "good_uid_12345" in uids
    assert "84a8ab573293497ab0d4f97b4650bb55" not in uids
    for m in models:
        assert m["accuracy_grade"] != "rejected_accuracy"


def test_heritage_accent_insensitive_search(client, db_session):
    """Test full-text search with diacritic-tolerant matching across names and summaries."""
    place = HeritagePlace(
        slug="chua-thien-mu-search",
        name_vi="Chùa Thiên Mụ",
        name_en="Thien Mu Pagoda",
        entity_type="monument",
        heritage_category="religious_ritual",
        visitor_summary_vi="Ngôi chùa cổ kính soi bóng bên bờ sông Hương xứ Huế.",
        editorial_status=HeritageRecordStatus.published.value,
        content_scope="RBPC_HUE",
    )
    db_session.add(place)
    db_session.commit()

    # Search without diacritics: "thien mu"
    res1 = client.get("/api/v1/heritage/search", params={"q": "thien mu"})
    assert res1.status_code == 200
    items1 = res1.json()["items"]
    assert any(i["slug"] == "chua-thien-mu-search" for i in items1)

    # Search with diacritics: "Thiên Mụ"
    res2 = client.get("/api/v1/heritage/search", params={"q": "Thiên Mụ"})
    assert res2.status_code == 200
    items2 = res2.json()["items"]
    assert any(i["slug"] == "chua-thien-mu-search" for i in items2)

    # Search summary content without diacritics: "song huong"
    res3 = client.get("/api/v1/heritage/search", params={"q": "song huong"})
    assert res3.status_code == 200
    items3 = res3.json()["items"]
    assert any(i["slug"] == "chua-thien-mu-search" for i in items3)

    # Search with foreign scope -> 400 Bad Request (strictly isolated to RBPC_HUE)
    res_bad_scope = client.get("/api/v1/heritage/search", params={"q": "thien mu", "scope": "CUU_DINH"})
    assert res_bad_scope.status_code == 400
    assert res_bad_scope.json()["error"]["code"] == "FORBIDDEN_SCOPE"


def test_unpublished_filtering_guardrails(client, db_session):
    """Test that public visitors cannot access draft/unpublished records while staff can."""
    # 1. Seed draft place
    draft_place = HeritagePlace(
        slug="draft-place-secret",
        name_vi="Di tích bản nháp bí mật",
        entity_type="monument",
        heritage_category="imperial_architecture",
        editorial_status=HeritageRecordStatus.draft.value,
        content_scope="RBPC_HUE",
    )
    # 2. Seed draft story
    draft_story = RbpcStory(
        slug="draft-story-secret",
        title_vi="Câu chuyện nháp chưa xuất bản",
        intro_vi="Nội dung nháp...",
        status="draft",
        content_scope="RBPC_HUE",
    )
    # 3. Seed revoked creator
    revoked_creator = RbpcCreator(
        slug="artisan-revoked",
        public_name="Nghệ nhân rút đồng thuận",
        craft_tradition="Đúc đồng",
        approved_bio_vi="Tiểu sử...",
        consent_status=RbpcConsentStatus.revoked.value,
    )
    db_session.add_all([draft_place, draft_story, revoked_creator])
    db_session.commit()

    # 4. Anonymous public visitor tests
    # Public list places should not contain draft
    res_places = client.get("/api/v1/heritage/places")
    assert res_places.status_code == 200
    place_slugs = [p["slug"] for p in res_places.json()["items"]]
    assert "draft-place-secret" not in place_slugs

    # Public get draft place -> 404
    res_place = client.get("/api/v1/heritage/places/draft-place-secret")
    assert res_place.status_code == 404
    assert res_place.json()["error"]["code"] == "HERITAGE_PLACE_NOT_FOUND"

    # Public list stories should not contain draft
    res_stories = client.get("/api/v1/rbpc/stories")
    assert res_stories.status_code == 200
    story_slugs = [s["slug"] for s in res_stories.json()["items"]]
    assert "draft-story-secret" not in story_slugs

    # Public get draft story -> 404
    res_story = client.get("/api/v1/rbpc/stories/draft-story-secret")
    assert res_story.status_code == 404
    assert res_story.json()["error"]["code"] == "RBPC_STORY_NOT_FOUND"

    # Public get revoked creator -> 404
    res_creator = client.get("/api/v1/rbpc/creators/artisan-revoked")
    assert res_creator.status_code == 404
    assert res_creator.json()["error"]["code"] == "RBPC_CREATOR_NOT_FOUND"

    # 5. Staff user tests: staff can access drafts
    staff_user = _create_user(db_session, "staff@example.com", role=UserRole.admin)
    _login_user(client, staff_user.email)

    # Staff can filter by editorial_status=draft
    res_staff_places = client.get("/api/v1/heritage/places", params={"editorial_status": "draft"})
    assert res_staff_places.status_code == 200
    staff_place_slugs = [p["slug"] for p in res_staff_places.json()["items"]]
    assert "draft-place-secret" in staff_place_slugs

    # Staff can view draft place detail
    res_staff_detail = client.get("/api/v1/heritage/places/draft-place-secret")
    assert res_staff_detail.status_code == 200
    assert res_staff_detail.json()["slug"] == "draft-place-secret"

    # Staff can view draft story detail
    res_staff_story = client.get("/api/v1/rbpc/stories/draft-story-secret")
    assert res_staff_story.status_code == 200
    assert res_staff_story.json()["slug"] == "draft-story-secret"


# --------------------------------------------------------------------------- #
# Test Cases: RBPC Commercial Slice & Inquiries
# --------------------------------------------------------------------------- #
def test_rbpc_config_and_published_story(client, db_session):
    """Test platform configuration and published story retrieval with verified claims."""
    # 1. Config endpoint
    res_cfg = client.get("/api/v1/rbpc/config")
    assert res_cfg.status_code == 200
    cfg = res_cfg.json()
    assert cfg["enabled"] is True
    assert cfg["demo_mode"] is True
    assert "vi" in cfg["supported_locales"]
    assert "en" in cfg["supported_locales"]

    # 2. Seed creator, experience, story, and claim
    creator = RbpcCreator(
        slug="nghe-nhan-tran-van-test",
        public_name="Nghệ nhân Trần Văn A",
        craft_tradition="Đúc đồng Phường Đúc",
        approved_bio_vi="Hơn 40 năm kinh nghiệm gìn giữ lửa nghề.",
        consent_status=RbpcConsentStatus.consented.value,
        public_region="Phường Đúc, Huế",
    )
    db_session.add(creator)
    db_session.flush()

    exp = RbpcExperience(
        slug="workshop-duc-chuong-test",
        creator_id=creator.id,
        provider_name="Xưởng Đúc Đồng Trần Văn",
        title_vi="Trải nghiệm tạo tác khuôn sáp và đúc đồng",
        description_vi="Tự tay chạm khắc hoa văn trên khuôn sáp.",
        area_public="Phường Đúc, Huế",
        duration_minutes=150,
        indicative_price_amount=450000,
        publication_state="published",
        availability_mode="inquiry_only",
    )
    db_session.add(exp)
    db_session.flush()

    story = RbpcStory(
        slug="tieng-dong-phuong-duc-test",
        title_vi="Tiếng đồng Phường Đúc",
        intro_vi="Lò đúc Phường Đúc đã đỏ lửa bốn trăm năm.",
        creator_id=creator.id,
        experience_id=exp.id,
        status="published",
        content_scope="RBPC_HUE",
    )
    db_session.add(story)
    db_session.flush()

    claim = RbpcClaimEvidence(
        story_id=story.id,
        statement="Nghề đúc đồng Phường Đúc có nguồn gốc từ thế kỷ XVII.",
        locale="vi",
        source_title="Đại Nam Nhất Thống Chí",
        support_type="direct",
        review_status="verified",
        citation_label="ĐNNTC, Tập Kinh Sư, tr. 142",
    )
    db_session.add(claim)
    db_session.commit()

    # 3. Retrieve published story detail
    res_story = client.get("/api/v1/rbpc/stories/tieng-dong-phuong-duc-test")
    assert res_story.status_code == 200
    s_data = res_story.json()
    assert s_data["title_vi"] == "Tiếng đồng Phường Đúc"
    assert len(s_data["evidence_claims"]) == 1
    assert s_data["creator"]["public_name"] == "Nghệ nhân Trần Văn A"
    assert s_data["experience"]["slug"] == "workshop-duc-chuong-test"

    # 4. Retrieve creator profile
    res_cr = client.get("/api/v1/rbpc/creators/nghe-nhan-tran-van-test")
    assert res_cr.status_code == 200
    cr_data = res_cr.json()
    assert cr_data["public_name"] == "Nghệ nhân Trần Văn A"
    assert "tieng-dong-phuong-duc-test" in cr_data["approved_story_slugs"]
    assert "workshop-duc-chuong-test" in cr_data["experience_slugs"]

    # 5. Retrieve experience offering
    res_ex = client.get("/api/v1/rbpc/experiences/workshop-duc-chuong-test")
    assert res_ex.status_code == 200
    ex_data = res_ex.json()
    assert ex_data["availability_mode"] == "inquiry_only"
    assert "không phải giao dịch thanh toán" in ex_data["notice"]


def test_cultural_bridge_ai_endpoint(client, db_session):
    """Test AI Cultural Bridge question answering constrained strictly to RBPC_HUE and verified claims."""
    # Seed story with claim
    story = RbpcStory(
        slug="cau-chuyen-cultural-bridge-test",
        title_vi="Nghề chạm khảm xà cừ Huế",
        intro_vi="Nghệ thuật khảm cẩn xà cừ tinh xảo thời Nguyễn.",
        status="published",
        content_scope="RBPC_HUE",
    )
    db_session.add(story)
    db_session.flush()

    claim = RbpcClaimEvidence(
        story_id=story.id,
        statement="Kỹ nghệ khảm xà cừ dùng vỏ trai, ốc biển mài mỏng để cẩn lên gỗ quý.",
        locale="vi",
        source_title="Kỹ thuật khảm xà cừ cổ truyền Việt Nam",
        support_type="direct",
        review_status="verified",
        citation_label="Tr. 45-48",
    )
    db_session.add(claim)
    db_session.commit()

    # Query cultural bridge
    res = client.post(
        "/api/v1/rbpc/cultural-bridge",
        json={
            "story_slug": "cau-chuyen-cultural-bridge-test",
            "question": "Vật liệu chính trong nghề khảm xà cừ là gì?",
            "locale": "vi",
        },
    )
    assert res.status_code == 200, res.text
    ans = res.json()
    assert ans["locale"] == "vi"
    assert "answer" in ans
    assert ans["context_boundary"] is not None
    assert ans["model_version"] == "clara-gemini-3.8-flash-tiered-v1"


def test_inquiry_creation_validation_and_idempotency(client, db_session):
    """Test inquiry creation with consent checks, date validation, and idempotency replay/conflict."""
    # Seed experience
    creator = RbpcCreator(
        slug="artisan-for-inquiry-test",
        public_name="Nghệ nhân B",
        craft_tradition="Làm nón lá",
        approved_bio_vi="Tiểu sử...",
        consent_status=RbpcConsentStatus.consented.value,
    )
    db_session.add(creator)
    db_session.flush()

    exp = RbpcExperience(
        slug="workshop-non-la-test",
        creator_id=creator.id,
        provider_name="Xưởng Nón Lá B",
        title_vi="Workshop chằm nón lá bài thơ",
        description_vi="Học chằm nón bài thơ truyền thống.",
        area_public="Huế",
        publication_state="published",
        availability_mode="inquiry_only",
    )
    db_session.add(exp)
    db_session.commit()

    future_date = (date.today() + timedelta(days=10)).isoformat()
    past_date = (date.today() - timedelta(days=2)).isoformat()
    unique_key = f"idem-key-{uuid.uuid4().hex}"

    # 1. Validation failure: consent not accepted
    res_no_consent = client.post(
        "/api/v1/rbpc/inquiries",
        json={
            "experience_slug": "workshop-non-la-test",
            "contact": {"name": "Nguyễn Văn C", "method": "email", "value": "c@example.com"},
            "preferred_date": future_date,
            "party_size": 2,
            "consent": {"version": "rbpc-inquiry-v1", "accepted": False},
            "idempotency_key": unique_key,
        },
    )
    assert res_no_consent.status_code == 422 or res_no_consent.status_code == 400

    # 2. Validation failure: past preferred date
    res_past_date = client.post(
        "/api/v1/rbpc/inquiries",
        json={
            "experience_slug": "workshop-non-la-test",
            "contact": {"name": "Nguyễn Văn C", "method": "email", "value": "c@example.com"},
            "preferred_date": past_date,
            "party_size": 2,
            "consent": {"version": "rbpc-inquiry-v1", "accepted": True},
            "idempotency_key": unique_key,
        },
    )
    assert res_past_date.status_code == 422 or res_past_date.status_code == 400

    # 3. Successful inquiry creation
    valid_payload = {
        "experience_slug": "workshop-non-la-test",
        "contact": {"name": "Nguyễn Văn C", "method": "email", "value": "c@example.com"},
        "preferred_date": future_date,
        "party_size": 2,
        "message": "Cần hỗ trợ tiếng Anh.",
        "consent": {"version": "rbpc-inquiry-v1", "accepted": True, "privacy_accepted": True},
        "idempotency_key": unique_key,
    }
    res_create = client.post("/api/v1/rbpc/inquiries", json=valid_payload)
    assert res_create.status_code == 202, res_create.text
    inq_data = res_create.json()
    assert inq_data["status"] == "new"
    assert inq_data["reference"].startswith("INQ-")
    status_token = inq_data["status_token"]
    assert status_token.startswith("tok_sec_")

    # 4. Idempotency replay: same key + same payload returns 202 with identical tokens
    res_replay = client.post("/api/v1/rbpc/inquiries", json=valid_payload)
    assert res_replay.status_code == 202
    replay_data = res_replay.json()
    assert replay_data["reference"] == inq_data["reference"]
    assert replay_data["status_token"] == inq_data["status_token"]

    # Verify no duplicate records created in DB
    db_inquiries = list(db_session.scalars(select(RbpcInquiry).where(RbpcInquiry.idempotency_key == unique_key)))
    assert len(db_inquiries) == 1

    # 5. Idempotency conflict: same key with conflicting party_size
    conflicting_payload = dict(valid_payload)
    conflicting_payload["party_size"] = 8
    res_conflict = client.post("/api/v1/rbpc/inquiries", json=conflicting_payload)
    assert res_conflict.status_code == 409
    assert res_conflict.json()["error"]["code"] == "RBPC_IDEMPOTENCY_CONFLICT"

    # 6. Status check via opaque token (ZERO PII Invariant)
    res_status = client.get(f"/api/v1/rbpc/inquiries/status/{status_token}")
    assert res_status.status_code == 200
    st_data = res_status.json()
    assert st_data["reference"] == inq_data["reference"]
    assert st_data["status"] == "new"
    assert st_data["experience_title"] == "Workshop chằm nón lá bài thơ"
    assert st_data["party_size"] == 2

    # CRITICAL ZERO PII ASSERTIONS:
    assert "email" not in st_data
    assert "phone" not in st_data
    assert "name" not in st_data
    assert "contact" not in st_data
    assert "message" not in st_data
    assert "internal_note" not in st_data


def test_rbpc_impact_metrics_verified(client, db_session):
    """Test impact metrics endpoint returns observed counts and verified sponsor support."""
    res = client.get("/api/v1/rbpc/impact")
    assert res.status_code == 200
    data = res.json()

    assert "observed_metrics" in data
    assert "projected_metrics" in data
    # Exactly verified 202,360,638 VND sponsor in-kind support (BNIX + Phổ Tuệ)
    assert data["observed_metrics"]["sponsor_support_vnd_verified"] == 202360638.0
    assert data["scope"] == "RBPC_HUE"
    assert data["projected_metrics"]["projection_basis"] is not None


def test_partner_inquiry_scoping_and_status_update(client, db_session):
    """Test authenticated partner inquiry scoping and status transitions."""
    # 1. Create two partners
    partner_a = _create_user(db_session, "partner_a@example.com", role=UserRole.teacher)
    partner_b = _create_user(db_session, "partner_b@example.com", role=UserRole.teacher)

    creator_a = RbpcCreator(
        slug="creator-a",
        public_name="Nghệ nhân A",
        craft_tradition="Nghề A",
        approved_bio_vi="...",
        consent_status=RbpcConsentStatus.consented.value,
    )
    creator_b = RbpcCreator(
        slug="creator-b",
        public_name="Nghệ nhân B",
        craft_tradition="Nghề B",
        approved_bio_vi="...",
        consent_status=RbpcConsentStatus.consented.value,
    )
    db_session.add_all([creator_a, creator_b])
    db_session.flush()

    exp_a = RbpcExperience(
        slug="exp-partner-a",
        creator_id=creator_a.id,
        provider_name="Xưởng A",
        provider_id=partner_a.id,
        title_vi="Trải nghiệm A",
        description_vi="...",
        area_public="Huế",
        publication_state="published",
    )
    exp_b = RbpcExperience(
        slug="exp-partner-b",
        creator_id=creator_b.id,
        provider_name="Xưởng B",
        provider_id=partner_b.id,
        title_vi="Trải nghiệm B",
        description_vi="...",
        area_public="Huế",
        publication_state="published",
    )
    db_session.add_all([exp_a, exp_b])
    db_session.flush()

    inquiry_a = RbpcInquiry(
        public_ref="INQ-AAAA-1111",
        experience_id=exp_a.id,
        provider_id=partner_a.id,
        name="Khách của A",
        contact_channel="email",
        contact_value="guest_a@example.com",
        party_size=2,
        state=RbpcInquiryStatus.new.value,
        idempotency_key=f"idem-a-{uuid.uuid4().hex}",
        opaque_token=f"tok_sec_a_{uuid.uuid4().hex}",
    )
    inquiry_b = RbpcInquiry(
        public_ref="INQ-BBBB-2222",
        experience_id=exp_b.id,
        provider_id=partner_b.id,
        name="Khách của B",
        contact_channel="email",
        contact_value="guest_b@example.com",
        party_size=4,
        state=RbpcInquiryStatus.new.value,
        idempotency_key=f"idem-b-{uuid.uuid4().hex}",
        opaque_token=f"tok_sec_b_{uuid.uuid4().hex}",
    )
    db_session.add_all([inquiry_a, inquiry_b])
    db_session.commit()

    # 2. Login as Partner A
    _login_user(client, partner_a.email)

    # Partner A can only see Inquiry A, NOT Inquiry B!
    res_list_a = client.get("/api/v1/rbpc/partner/inquiries")
    assert res_list_a.status_code == 200
    refs = [i["reference"] for i in res_list_a.json()["items"]]
    assert "INQ-AAAA-1111" in refs
    assert "INQ-BBBB-2222" not in refs

    # Partner A attempts to update Partner B's inquiry -> 403 Forbidden Scope
    res_forbidden = client.patch(
        f"/api/v1/rbpc/partner/inquiries/{inquiry_b.id}",
        json={"status": "contacted", "note": "Partner A snooping"},
    )
    assert res_forbidden.status_code == 403
    assert res_forbidden.json()["error"]["code"] == "FORBIDDEN_SCOPE"

    # Partner A updates own Inquiry A -> Success
    res_update_a = client.patch(
        f"/api/v1/rbpc/partner/inquiries/{inquiry_a.id}",
        json={"status": "contacted", "note": "Đã gọi điện thoại xác nhận với khách"},
    )
    assert res_update_a.status_code == 200
    assert res_update_a.json()["status"] == "contacted"
    assert res_update_a.json()["contact_name"] == "Khách của A"
