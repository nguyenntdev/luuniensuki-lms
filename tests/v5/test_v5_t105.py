# -*- coding: utf-8 -*-
"""V5-T105 (Wave W10, Slot A05): Curator-controlled story recommendations.

Priority: P2; Classification: NEW_PRODUCT_FEATURE
Goal: Curator-controlled story recommendations in backend/services/rbpc_ai.py and frontend.
Rule-based object -> craft workshop linkages with verified historical relationships and no implied fake imperial lineage.
Negative abuse: Unverified artisan relationships or commercial claims are strictly hidden.
"""
from __future__ import annotations

import uuid
from typing import Any
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from backend.models import (
    HistoricalClaim,
    HistoricalEntity,
    HistoricalSource,
    User,
    UserRole,
)
from backend.models_rbpc import (
    HeritageHeritageRelation,
    HeritagePlace,
    RbpcClaimEvidence,
    RbpcConsentStatus,
    RbpcCreator,
    RbpcExperience,
    RbpcStory,
    RbpcSupportType,
)
from backend.services import rbpc_ai


# --------------------------------------------------------------------------- #
# Helpers & Seeding Fixtures
# --------------------------------------------------------------------------- #
def _seed_curator_ecosystem(db: Session):
    """Seed places, relational links, creators, experiences, and stories."""
    # Place 1: Thế Miếu (Imperial ancestral temple enclosing Nine Dynastic Urns)
    the_mieu = HeritagePlace(
        slug=f"the-mieu-{uuid.uuid4().hex[:6]}",
        name_vi="Thế Miếu",
        name_en="The Mieu Ancestral Temple",
        entity_type="building",
        heritage_category="monument",
        content_scope="RBPC_HUE",
        editorial_status="approved",
    )
    # Place 2: Phường Đúc (Living bronze casting craft village)
    phuong_duc_place = HeritagePlace(
        slug=f"duc-dong-phuong-duc-{uuid.uuid4().hex[:6]}",
        name_vi="Làng Đúc Đồng Phường Đúc",
        name_en="Phuong Duc Bronze Casting Quarter",
        entity_type="site",
        heritage_category="traditional_craft",
        content_scope="RBPC_HUE",
        editorial_status="approved",
    )
    db.add_all([the_mieu, phuong_duc_place])
    db.flush()

    # Relational link: Thế Miếu - associated_craft -> Phường Đúc
    rel = HeritageHeritageRelation(
        from_place_id=the_mieu.id,
        to_place_id=phuong_duc_place.id,
        relationship_type="associated_craft",
        review_state="verified",
    )
    db.add(rel)
    db.flush()

    # Creator 1: Verified, consented master artisan
    creator_valid = RbpcCreator(
        slug=f"nguyen-van-sinh-{uuid.uuid4().hex[:6]}",
        public_name="Nghệ nhân Nhân dân Nguyễn Văn Sinh",
        craft_tradition="Đúc đồng Phường Đúc",
        approved_bio_vi="Gìn giữ phương pháp đúc khuôn sáp và hợp kim đồng truyền thống hơn 50 năm.",
        consent_status=RbpcConsentStatus.consented.value,
        is_verified=True,
        generation_lineage="Hậu duệ đời thứ 11 dòng họ đúc đồng Nguyễn Văn",
        public_region="Phường Đúc, TP. Huế",
    )
    # Creator 2: Unverified artisan (should be hidden by negative abuse guardrail)
    creator_unverified = RbpcCreator(
        slug=f"artisan-unverified-{uuid.uuid4().hex[:6]}",
        public_name="Thợ Đúc Chưa Thẩm Định",
        craft_tradition="Đúc kim loại",
        approved_bio_vi="Mới bắt đầu xưởng đúc thương mại.",
        consent_status=RbpcConsentStatus.pending_review.value,
        is_verified=False,
    )
    # Creator 3: Revoked consent artisan (must be hidden)
    creator_revoked = RbpcCreator(
        slug=f"artisan-revoked-{uuid.uuid4().hex[:6]}",
        public_name="Nghệ nhân Rút Đồng Thuận",
        craft_tradition="Đúc đồng",
        approved_bio_vi="Nghệ nhân đã yêu cầu rút thông tin.",
        consent_status=RbpcConsentStatus.revoked.value,
        is_verified=True,
    )
    # Creator 4: Artisan claiming fake imperial lineage (must be hidden)
    creator_fake_lineage = RbpcCreator(
        slug=f"artisan-fake-{uuid.uuid4().hex[:6]}",
        public_name="Xưởng Đúc Mạo Danh",
        craft_tradition="Đúc đồng hoàng gia",
        approved_bio_vi="Tự xưng là hậu duệ trực tiếp của nghệ nhân đúc cửu đỉnh 1835 và hoàng gia ủy quyền sản xuất cổ vật.",
        generation_lineage="Dòng dõi vua ban quyền đúc đỉnh",
        consent_status=RbpcConsentStatus.consented.value,
        is_verified=True,
    )
    db.add_all([creator_valid, creator_unverified, creator_revoked, creator_fake_lineage])
    db.flush()

    # Experience for Creator 1: Verified & Published
    exp_valid = RbpcExperience(
        slug=f"workshop-duc-dong-{uuid.uuid4().hex[:6]}",
        creator_id=creator_valid.id,
        provider_name="Xưởng Đúc Đồng Sinh Long",
        title_vi="Trải nghiệm Đúc Đồng Thủ Công Cùng Nghệ Nhân",
        description_vi="Tìm hiểu kỹ thuật tạo khuôn đất và rót đồng truyền thống.",
        area_public="Phường Đúc, TP. Huế",
        availability_mode="inquiry_only",
        publication_state="published",
    )
    # Experience for Creator 2 (Unverified creator)
    exp_unverified = RbpcExperience(
        slug=f"workshop-unverified-{uuid.uuid4().hex[:6]}",
        creator_id=creator_unverified.id,
        provider_name="Xưởng Thương Mại Chưa Duyệt",
        title_vi="Mua sắm chuông đồng lưu niệm",
        description_vi="Bán hàng lưu niệm không qua kiểm chứng.",
        area_public="TP. Huế",
        availability_mode="inquiry_only",
        publication_state="published",
    )
    db.add_all([exp_valid, exp_unverified])
    db.flush()

    # Story 1: Anchor Story on Thế Miếu
    story_anchor = RbpcStory(
        slug=f"chuyen-the-mieu-{uuid.uuid4().hex[:6]}",
        title_vi="Thế Miếu và Báu Vật Hoàng Cung",
        intro_vi="Nơi tôn nghiêm ghi dấu lịch sử vương triều Nguyễn.",
        approved_summary_vi="Tổng quan kiến trúc và ý nghĩa văn hóa Thế Miếu.",
        place_id=the_mieu.id,
        status="published",
        content_scope="RBPC_HUE",
    )
    # Story 2: Associated Craft Story on Phường Đúc with valid creator & experience
    story_craft_valid = RbpcStory(
        slug=f"tieng-dong-phuong-duc-{uuid.uuid4().hex[:6]}",
        title_vi="Tiếng Đồng Phường Đúc",
        intro_vi="Kỹ nghệ đúc đồng cổ truyền 400 năm.",
        approved_summary_vi="Hành trình nghề đúc bên bờ sông Hương.",
        place_id=phuong_duc_place.id,
        creator_id=creator_valid.id,
        experience_id=exp_valid.id,
        status="published",
        content_scope="RBPC_HUE",
    )
    # Story 3: Unverified Artisan Story (Should be rejected from recommendations)
    story_unverified = RbpcStory(
        slug=f"story-unverified-{uuid.uuid4().hex[:6]}",
        title_vi="Câu Chuyện Chưa Thẩm Định",
        intro_vi="Nội dung thương mại tự phát.",
        approved_summary_vi="Chưa qua biên tập duyệt.",
        creator_id=creator_unverified.id,
        experience_id=exp_unverified.id,
        status="published",
        content_scope="RBPC_HUE",
    )
    # Story 4: Fake Imperial Lineage Story (Should be rejected from recommendations)
    story_fake_lineage = RbpcStory(
        slug=f"story-fake-{uuid.uuid4().hex[:6]}",
        title_vi="Huyền Thoại Hoàng Tộc Tự Xưng",
        intro_vi="Bịa đặt quan hệ hoàng tộc.",
        approved_summary_vi="Mạo danh quyền năng triều đình.",
        creator_id=creator_fake_lineage.id,
        status="published",
        content_scope="RBPC_HUE",
    )
    db.add_all([story_anchor, story_craft_valid, story_unverified, story_fake_lineage])
    db.commit()

    return {
        "the_mieu": the_mieu,
        "phuong_duc": phuong_duc_place,
        "story_anchor": story_anchor,
        "story_craft_valid": story_craft_valid,
        "story_unverified": story_unverified,
        "story_fake_lineage": story_fake_lineage,
        "creator_valid": creator_valid,
        "creator_unverified": creator_unverified,
        "creator_fake_lineage": creator_fake_lineage,
        "exp_valid": exp_valid,
    }


# --------------------------------------------------------------------------- #
# Test 1: Fake Imperial Lineage Detector Unit Checks
# --------------------------------------------------------------------------- #
def test_fake_imperial_lineage_detection():
    """Verify check_fake_imperial_lineage detects and flags fake imperial assertions."""
    # 1. Clean authentic texts
    is_fake, _ = rbpc_ai.check_fake_imperial_lineage(
        "Nghệ nhân Nhân dân Nguyễn Văn Sinh, hậu duệ đời thứ 11 làng đúc đồng Phường Đúc."
    )
    assert not is_fake

    # 2. Fake claims: royal authorized reproduction / direct urn caster descendant
    is_fake_1, reason_1 = rbpc_ai.check_fake_imperial_lineage(
        "Cơ sở chúng tôi là hậu duệ trực tiếp của nghệ nhân đúc cửu đỉnh 1835."
    )
    assert is_fake_1
    assert "hậu duệ trực tiếp của nghệ nhân đúc cửu đỉnh 1835" in reason_1

    is_fake_2, reason_2 = rbpc_ai.check_fake_imperial_lineage(
        "Sản phẩm được hoàng gia ủy quyền sản xuất làm đồ lưu niệm."
    )
    assert is_fake_2
    assert "hoàng gia ủy quyền sản xuất" in reason_2

    # 3. Safe negated text (anti-conflation disclaimer)
    is_fake_safe, _ = rbpc_ai.check_fake_imperial_lineage(
        "Nghệ nhân đương đại không phải là thợ đúc triều đình năm 1835 và không có ủy quyền hoàng gia."
    )
    assert not is_fake_safe


# --------------------------------------------------------------------------- #
# Test 2: Rule-Based Object -> Craft Workshop Linkages (Positive Recommendation)
# --------------------------------------------------------------------------- #
def test_curator_story_recommendations_rule_based_linkage(db_session: Session):
    """Verify rule-based linkage recommends verified craft workshops associated with historical objects."""
    eco = _seed_curator_ecosystem(db_session)
    anchor = eco["story_anchor"]

    # Request recommendations for the anchor story (Thế Miếu)
    recs = rbpc_ai.get_curator_story_recommendations(
        db=db_session,
        story_slug=anchor.slug,
        locale="vi",
        limit=5,
    )

    # Must contain the associated craft story (Tiếng Đồng Phường Đúc)
    rec_slugs = [r["story_slug"] for r in recs]
    assert eco["story_craft_valid"].slug in rec_slugs

    craft_rec = next(r for r in recs if r["story_slug"] == eco["story_craft_valid"].slug)
    assert craft_rec["linkage_type"] == "object_associated_craft"
    assert "Mối liên kết lịch sử đã thẩm định" in craft_rec["historical_justification"]
    assert craft_rec["verified_historical_relationship"] is True
    assert craft_rec["no_implied_fake_imperial_lineage"] is True

    # Workshop link must be populated with verified artisan & dignity note
    ws = craft_rec["workshop"]
    assert ws is not None
    assert ws["creator_name"] == "Nghệ nhân Nhân dân Nguyễn Văn Sinh"
    assert ws["experience_title"] == "Trải nghiệm Đúc Đồng Thủ Công Cùng Nghệ Nhân"
    assert ws["is_verified_artisan"] is True
    assert ws["availability_mode"] == "inquiry_only"
    assert "hoàn toàn tách biệt với cổ vật hoàng gia năm 1835" in ws["artisan_dignity_note"]


# --------------------------------------------------------------------------- #
# Test 3: Negative Abuse - Unverified Artisan & Commercial Claims Strictly Hidden
# --------------------------------------------------------------------------- #
def test_negative_abuse_unverified_artisan_and_commercial_claims_hidden(db_session: Session):
    """Negative Abuse Invariant: Unverified artisan relationships or commercial claims are strictly hidden."""
    eco = _seed_curator_ecosystem(db_session)
    anchor = eco["story_anchor"]

    recs = rbpc_ai.get_curator_story_recommendations(
        db=db_session,
        story_slug=anchor.slug,
        locale="vi",
        limit=10,
    )

    rec_slugs = [r["story_slug"] for r in recs]

    # Negative assertion 1: Unverified story/artisan is NOT recommended
    assert eco["story_unverified"].slug not in rec_slugs

    # Negative assertion 2: Fake imperial lineage claim story is NOT recommended
    assert eco["story_fake_lineage"].slug not in rec_slugs

    # Negative assertion 3: Verify none of returned recommendations feature unverified creators
    for r in recs:
        if r.get("workshop"):
            assert r["workshop"]["is_verified_artisan"] is True
            assert r["workshop"]["consent_status"] in ("consented", "verified_written_consent")


# --------------------------------------------------------------------------- #
# Test 4: Negative Abuse - Object Slug Filter & Non-Existent Entities Fail Closed
# --------------------------------------------------------------------------- #
def test_curator_story_recommendations_fail_closed(db_session: Session):
    """Verify non-existent stories or objects gracefully return empty list without leaking or crashing."""
    # Non-existent story slug
    recs_empty = rbpc_ai.get_curator_story_recommendations(
        db=db_session,
        story_slug="non-existent-story-slug-12345",
        locale="vi",
    )
    assert isinstance(recs_empty, list)
    # Does not crash, returns valid or empty list
    for r in recs_empty:
        assert r["verified_historical_relationship"] is True

    # Query with non-existent object slug
    recs_obj_empty = rbpc_ai.get_curator_story_recommendations(
        db=db_session,
        object_slug="non-existent-object-slug-9999",
        locale="en",
    )
    assert isinstance(recs_obj_empty, list)


# --------------------------------------------------------------------------- #
# Test 5: Cultural Bridge Q&A Integration with Curator Workshop Linkage
# --------------------------------------------------------------------------- #
def test_answer_cultural_question_integrates_verified_workshop(db_session: Session):
    """Verify answer_cultural_question populates verified workshop metadata while excluding unverified."""
    eco = _seed_curator_ecosystem(db_session)
    valid_story = eco["story_craft_valid"]

    # Cultural Bridge Q&A for the valid story
    res = rbpc_ai.answer_cultural_question(
        db=db_session,
        story_slug=valid_story.slug,
        question="Nghệ nhân thực hiện kỹ nghệ rót đồng như thế nào?",
        locale="vi",
        use_llm=False,
    )

    assert res["status"] in ("supported", "insufficient_evidence")
    assert res["linked_creator_slug"] == eco["creator_valid"].slug
    assert res["linked_creator_name"] == "Nghệ nhân Nhân dân Nguyễn Văn Sinh"
    assert res["linked_experience_slug"] == eco["exp_valid"].slug
    assert res["linked_experience_title"] == "Trải nghiệm Đúc Đồng Thủ Công Cùng Nghệ Nhân"


# --------------------------------------------------------------------------- #
# Test 6: REST API Endpoint GET /api/v1/rbpc/stories/{slug}/recommendations
# --------------------------------------------------------------------------- #
def test_api_curator_story_recommendations_endpoint(client: TestClient, db_session: Session):
    """Verify REST API endpoint returns structured curator recommendations with historical linkage."""
    eco = _seed_curator_ecosystem(db_session)
    anchor = eco["story_anchor"]

    # 1. 200 OK for existing story
    res = client.get(f"/api/v1/rbpc/stories/{anchor.slug}/recommendations?locale=vi&limit=5")
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["story_slug"] == anchor.slug
    assert "recommendations" in data
    assert isinstance(data["recommendations"], list)
    assert len(data["recommendations"]) >= 1

    rec0 = data["recommendations"][0]
    assert "historical_justification" in rec0
    assert rec0["verified_historical_relationship"] is True
    assert rec0["no_implied_fake_imperial_lineage"] is True

    # 2. 404 for non-existent story
    res_404 = client.get("/api/v1/rbpc/stories/non-existent-slug-xyz/recommendations")
    assert res_404.status_code == 404
