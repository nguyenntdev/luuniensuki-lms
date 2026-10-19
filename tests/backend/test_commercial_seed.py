# -*- coding: utf-8 -*-
"""Unit and integration tests for LƯU NIÊN — RBPC 2026 Commercial Slice Seeding.

Verifies:
1. Parsing and validation of data/heritage-hue/creators.yaml
   - 3 consented artisan profiles (Nguyễn Văn Sinh, Đỗ Hữu Triết, Thân Văn Huy)
   - Written consent release references (CONSENT-PD-001, CONSENT-PL-002, CONSENT-TT-003)
   - Associated heritage place linkage (Kinh thành Huế, Điện Thái Hòa, Điện Hòn Chén)
2. Parsing and validation of data/heritage-hue/experiences.yaml
   - 3 cultural workshop masterclasses
   - Commercial Honesty Invariant: strictly inquiry_only availability_mode (NEVER instant payment)
   - Indicative price parsing, duration, languages, party size bounds
   - Referential integrity: valid creator_slug linkages
3. Parsing and validation of data/heritage-hue/stories.yaml
   - 3 curated cultural stories
   - Referential integrity: valid place_slug, creator_slug, and experience_slug
   - 6 total grounded evidence claims with bibliographic citations
4. Dry-run validation service (HeritageImportService) with zero side effects
5. Commercial Honesty Guardrail violation detection (instant booking rejection)
6. Database commit mode upserting and foreign key preservation:
   - story.place_id -> heritage_places.id
   - story.creator_id -> rbpc_creators.id
   - story.experience_id -> rbpc_experiences.id
   - experience.creator_id -> rbpc_creators.id
   - creator.heritage_place_id -> heritage_places.id
   - story.claims -> rbpc_claim_evidence.story_id
7. Idempotency and manual consent revocation preservation
8. Public API endpoints functionality with real seeded commercial catalogue
9. CLI dry-run invocation with commercial dataset flags
"""
from __future__ import annotations

import sys
import uuid
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest
from sqlalchemy import select

from backend.models import User, UserRole
from backend.models_rbpc import (
    HeritagePlace,
    RbpcAvailabilityMode,
    RbpcClaimEvidence,
    RbpcConsentStatus,
    RbpcCreator,
    RbpcExperience,
    RbpcStory,
    RbpcStoryStatus,
    RbpcSupportType,
)
from backend.services.heritage_import import (
    DEFAULT_CREATORS_PATH,
    DEFAULT_EXPERIENCES_PATH,
    DEFAULT_INVENTORY_PATH,
    DEFAULT_SKETCHFAB_PATH,
    DEFAULT_STORIES_PATH,
    HeritageImportService,
    ImportStats,
    ValidationReport,
    import_heritage_data,
    load_yaml_file,
    parse_entity_uuid,
    parse_price,
    validate_creators_data,
    validate_experiences_data,
    validate_heritage_import,
    validate_stories_data,
)
from scripts.heritage import seed_hue_heritage


# --------------------------------------------------------------------------- #
# 1. Creators YAML Parsing & Validation
# --------------------------------------------------------------------------- #
def test_parse_and_validate_creators_yaml():
    """Verify creators.yaml parses all 3 pilot consented artisans with valid metadata."""
    data = load_yaml_file(DEFAULT_CREATORS_PATH)
    creators = data.get("creators") or []

    assert len(creators) == 3, f"Expected 3 pilot creators, got {len(creators)}"

    expected_slugs = {
        "nghe-nhan-nguyen-van-sinh",
        "nghe-nhan-do-huu-triet",
        "nghe-nhan-than-van-huy",
    }
    actual_slugs = {c["slug"] for c in creators}
    assert actual_slugs == expected_slugs, f"Mismatch in creator slugs: {actual_slugs}"

    for c in creators:
        # Check UUID
        parsed_id = parse_entity_uuid(c["id"])
        assert isinstance(parsed_id, uuid.UUID)

        # Check required fields
        assert c["public_name"] and isinstance(c["public_name"], str)
        assert c["craft_tradition"] and isinstance(c["craft_tradition"], str)
        assert c["approved_bio_vi"] and len(c["approved_bio_vi"]) > 50
        assert c["approved_bio_en"] and len(c["approved_bio_en"]) > 50

        # Check consent invariants
        assert c["consent_status"] == RbpcConsentStatus.consented.value
        assert c["is_verified"] is True
        assert c["display_consent_ref"] is not None
        assert c["display_consent_ref"].startswith("CONSENT-")

        # Check craft experience
        assert isinstance(c["years_of_practice"], int) and c["years_of_practice"] >= 20
        assert c["generation_lineage"] and isinstance(c["generation_lineage"], str)

        # Check portrait asset
        assert c.get("portrait_asset_url") or c.get("approved_portrait_url")
        assert c["portrait_asset_url"].startswith("/assets/creators/")

        # Check associated places list
        assoc_places = c.get("associated_places") or []
        assert len(assoc_places) >= 1


# --------------------------------------------------------------------------- #
# 2. Experiences YAML Parsing & Commercial Honesty Invariant
# --------------------------------------------------------------------------- #
def test_parse_and_validate_experiences_yaml():
    """Verify experiences.yaml parses all 3 masterclasses and enforces inquiry_only."""
    data = load_yaml_file(DEFAULT_EXPERIENCES_PATH)
    experiences = data.get("experiences") or []

    assert len(experiences) == 3, f"Expected 3 pilot experiences, got {len(experiences)}"

    expected_exp_slugs = {
        "workshop-duc-dong-phuong-duc",
        "workshop-phap-lam-hue",
        "workshop-hoa-giay-thanh-tien",
    }
    actual_exp_slugs = {e["slug"] for e in experiences}
    assert actual_exp_slugs == expected_exp_slugs

    for exp in experiences:
        # Check UUID
        parsed_id = parse_entity_uuid(exp["id"])
        assert isinstance(parsed_id, uuid.UUID)

        # Commercial Honesty Invariant: strictly inquiry_only
        assert exp["availability_mode"] == RbpcAvailabilityMode.inquiry_only.value, (
            f"Experience '{exp['slug']}' must have availability_mode 'inquiry_only'"
        )

        # Check creator linkage
        assert exp["creator_slug"] in {
            "nghe-nhan-nguyen-van-sinh",
            "nghe-nhan-do-huu-triet",
            "nghe-nhan-than-van-huy",
        }

        # Check duration and party size
        assert isinstance(exp["duration_minutes"], int) and exp["duration_minutes"] >= 60
        assert 1 <= exp["max_party_size"] <= 50

        # Check pricing
        assert exp["currency"] == "VND"
        parsed_price = parse_price(exp["pricing_display"])
        assert parsed_price is not None and parsed_price >= 300000.0

        # Check languages & transparency notice
        assert "vi" in exp["languages_supported"]
        notice = exp.get("notice", "")
        assert (
            "không thu phí trực tuyến" in notice
            or "không phải giao dịch thanh toán" in notice
            or "thanh toán thực hiện trực tiếp" in notice
        )

        # Check syllabus
        syllabus = exp.get("syllabus") or []
        assert len(syllabus) >= 4, f"Experience {exp['slug']} expected at least 4 syllabus steps"
        for step in syllabus:
            assert step["step"] > 0
            assert step["title_vi"] and step["title_en"]
            assert step["duration_minutes"] > 0


# --------------------------------------------------------------------------- #
# 3. Stories YAML Parsing & Evidence Claims
# --------------------------------------------------------------------------- #
def test_parse_and_validate_stories_yaml():
    """Verify stories.yaml parses all 3 stories with verified claim citations."""
    data = load_yaml_file(DEFAULT_STORIES_PATH)
    stories = data.get("stories") or []

    assert len(stories) == 3, f"Expected 3 pilot stories, got {len(stories)}"

    expected_story_slugs = {
        "tieng-chuong-khiem-cung",
        "nghe-thuat-phap-lam-hue",
        "hoa-giay-thanh-tien",
    }
    actual_story_slugs = {s["slug"] for s in stories}
    assert actual_story_slugs == expected_story_slugs

    total_claims = 0
    for s in stories:
        parsed_id = parse_entity_uuid(s["id"])
        assert isinstance(parsed_id, uuid.UUID)

        assert s["status"] == "published"
        assert s["title_vi"] and s["title_en"]
        assert s["intro_vi"] and s["intro_en"]
        assert s["primary_asset_url"] and s["primary_asset_url"].startswith("/assets/stories/")

        # Check foreign references
        assert s["place_slug"] in {"lang-tu-duc", "dien-thai-hoa", "chua-thien-mu"}
        assert s["creator_slug"] in {
            "nghe-nhan-nguyen-van-sinh",
            "nghe-nhan-do-huu-triet",
            "nghe-nhan-than-van-huy",
        }
        assert s["experience_slug"] in {
            "workshop-duc-dong-phuong-duc",
            "workshop-phap-lam-hue",
            "workshop-hoa-giay-thanh-tien",
        }

        # Check claims
        claims = s.get("claims") or []
        assert len(claims) == 2, f"Story {s['slug']} must have exactly 2 backing claims"
        total_claims += len(claims)

        for c in claims:
            assert c["statement_vi"] and len(c["statement_vi"]) > 20
            assert c["statement_en"] and len(c["statement_en"]) > 20
            assert c["source_title"] and len(c["source_title"]) > 5
            assert c["source_locator"] and len(c["source_locator"]) > 2
            assert c["support_type"] == "direct"
            assert c["epistemic_certainty"] == "verified_source"

        # Check chapters
        chapters = s.get("chapters") or []
        assert len(chapters) >= 2, f"Story {s['slug']} must have at least 2 chapters"
        for ch in chapters:
            assert ch["chapter_number"] > 0
            assert ch["title_vi"] and ch["title_en"]
            assert ch["content_vi"] and ch["content_en"]

    assert total_claims == 6, f"Expected 6 total claims across 3 stories, got {total_claims}"


# --------------------------------------------------------------------------- #
# 4. Dry-Run Validation Integration
# --------------------------------------------------------------------------- #
def test_dry_run_validation_all_datasets():
    """Verify HeritageImportService dry-run validates all 5 datasets cleanly."""
    service = HeritageImportService(
        inventory_path=DEFAULT_INVENTORY_PATH,
        sketchfab_path=DEFAULT_SKETCHFAB_PATH,
        stories_path=DEFAULT_STORIES_PATH,
        creators_path=DEFAULT_CREATORS_PATH,
        experiences_path=DEFAULT_EXPERIENCES_PATH,
    )
    report = service.validate()

    assert report.is_valid is True
    assert len(report.errors) == 0, f"Unexpected validation errors: {report.errors}"
    assert report.unesco_components_count == 14
    assert report.child_monuments_count == 6
    assert report.craft_communities_count == 3
    assert report.total_places_count == 23
    assert report.models_count == 23
    assert report.creators_count == 3
    assert report.experiences_count == 3
    assert report.stories_count == 3
    assert report.claims_count == 6
    assert report.guardrails_passed is True


# --------------------------------------------------------------------------- #
# 5. Negative Guardrail Tests
# --------------------------------------------------------------------------- #
def test_validation_catches_commercial_honesty_violation():
    """Verify validation rejects prohibited instant booking / payment modes."""
    exp_data = load_yaml_file(DEFAULT_EXPERIENCES_PATH)
    corrupted = deepcopy(exp_data)
    corrupted["experiences"][0]["availability_mode"] = "instant_checkout"

    report = validate_experiences_data(corrupted)
    assert report.is_valid is False
    assert any("COMMERCIAL HONESTY VIOLATION" in e for e in report.errors)


def test_validation_catches_invalid_creator_reference():
    """Verify validation catches an experience referencing a non-existent creator."""
    exp_data = load_yaml_file(DEFAULT_EXPERIENCES_PATH)
    corrupted = deepcopy(exp_data)
    corrupted["experiences"][0]["creator_slug"] = "ghost-artisan-404"

    valid_creators = {"nghe-nhan-nguyen-van-sinh", "nghe-nhan-do-huu-triet", "nghe-nhan-than-van-huy"}
    report = validate_experiences_data(corrupted, valid_creator_slugs=valid_creators)
    assert report.is_valid is False
    assert any("references unknown creator_slug" in e for e in report.errors)


def test_validation_catches_invalid_story_place_reference():
    """Verify validation catches a story referencing a non-existent place."""
    stories_data = load_yaml_file(DEFAULT_STORIES_PATH)
    corrupted = deepcopy(stories_data)
    corrupted["stories"][0]["place_slug"] = "non-existent-palace"

    valid_places = {"lang-tu-duc", "dien-thai-hoa", "chua-thien-mu"}
    report = validate_stories_data(corrupted, valid_place_slugs=valid_places)
    assert report.is_valid is False
    assert any("references unknown place_slug" in e for e in report.errors)


# --------------------------------------------------------------------------- #
# 6. Database Commit Mode & Foreign Key Integrity
# --------------------------------------------------------------------------- #
def test_commit_mode_commercial_upsert_and_relationships(db_session):
    """Verify commit mode imports 3 stories, 3 creators, 3 experiences with all FKs preserved."""
    report, stats = import_heritage_data(
        db=db_session,
        inventory_path=DEFAULT_INVENTORY_PATH,
        sketchfab_path=DEFAULT_SKETCHFAB_PATH,
        stories_path=DEFAULT_STORIES_PATH,
        creators_path=DEFAULT_CREATORS_PATH,
        experiences_path=DEFAULT_EXPERIENCES_PATH,
        dry_run=False,
    )

    assert report.is_valid is True
    assert stats.dry_run is False
    assert stats.places_inserted == 23
    assert stats.media_inserted == 23
    assert stats.creators_inserted == 3
    assert stats.experiences_inserted == 3
    assert stats.stories_inserted == 3
    assert stats.claims_inserted == 6

    # 1. Verify 3 Creators in DB
    creators = db_session.execute(select(RbpcCreator)).scalars().all()
    assert len(creators) == 3
    creators_by_slug = {c.slug: c for c in creators}

    sinh = creators_by_slug["nghe-nhan-nguyen-van-sinh"]
    triet = creators_by_slug["nghe-nhan-do-huu-triet"]
    huy = creators_by_slug["nghe-nhan-than-van-huy"]

    assert sinh.public_name == "Nghệ nhân Nhân dân Nguyễn Văn Sinh"
    assert sinh.craft_tradition == "Đúc đồng Phường Đúc"
    assert sinh.consent_status == "consented"
    assert sinh.is_verified is True
    assert sinh.years_of_practice == 52
    assert sinh.heritage_place_id is not None
    # Sinh linked to Kinh thành Huế
    citadel = db_session.execute(select(HeritagePlace).where(HeritagePlace.slug == "kinh-thanh-hue")).scalar_one()
    assert sinh.heritage_place_id == citadel.id

    assert triet.public_name == "Thạc sĩ - Nghệ nhân Đỗ Hữu Triết"
    assert triet.craft_tradition == "Nghệ thuật Pháp lam Huế"
    # Triết linked to Điện Thái Hòa
    thai_hoa = db_session.execute(select(HeritagePlace).where(HeritagePlace.slug == "dien-thai-hoa")).scalar_one()
    assert triet.heritage_place_id == thai_hoa.id

    assert huy.public_name == "Nghệ nhân Ưu tú Thân Văn Huy"
    assert huy.craft_tradition == "Nghề làm hoa giấy truyền thống Thanh Tiên"
    # Huy linked to Điện Hòn Chén
    hon_chen = db_session.execute(select(HeritagePlace).where(HeritagePlace.slug == "dien-hon-chen")).scalar_one()
    assert huy.heritage_place_id == hon_chen.id

    # 2. Verify 3 Experiences in DB & Creator Foreign Key Linkage
    experiences = db_session.execute(select(RbpcExperience)).scalars().all()
    assert len(experiences) == 3
    experiences_by_slug = {e.slug: e for e in experiences}

    exp_bronze = experiences_by_slug["workshop-duc-dong-phuong-duc"]
    exp_enamel = experiences_by_slug["workshop-phap-lam-hue"]
    exp_paper = experiences_by_slug["workshop-hoa-giay-thanh-tien"]

    # Foreign key: creator_id
    assert exp_bronze.creator_id == sinh.id
    assert exp_bronze.creator.slug == "nghe-nhan-nguyen-van-sinh"
    assert float(exp_bronze.indicative_price_amount) == 650000.0
    assert exp_bronze.duration_minutes == 180
    assert exp_bronze.availability_mode == "inquiry_only"

    assert exp_enamel.creator_id == triet.id
    assert exp_enamel.creator.slug == "nghe-nhan-do-huu-triet"
    assert float(exp_enamel.indicative_price_amount) == 550000.0
    assert exp_enamel.duration_minutes == 150
    assert exp_enamel.availability_mode == "inquiry_only"

    assert exp_paper.creator_id == huy.id
    assert exp_paper.creator.slug == "nghe-nhan-than-van-huy"
    assert float(exp_paper.indicative_price_amount) == 350000.0
    assert exp_paper.duration_minutes == 120
    assert exp_paper.availability_mode == "inquiry_only"

    # 3. Verify 3 Stories in DB & 3-way Foreign Key Linkage (Place, Creator, Experience)
    stories = db_session.execute(select(RbpcStory)).scalars().all()
    assert len(stories) == 3
    stories_by_slug = {s.slug: s for s in stories}

    story_bronze = stories_by_slug["tieng-chuong-khiem-cung"]
    story_enamel = stories_by_slug["nghe-thuat-phap-lam-hue"]
    story_paper = stories_by_slug["hoa-giay-thanh-tien"]

    tu_duc = db_session.execute(select(HeritagePlace).where(HeritagePlace.slug == "lang-tu-duc")).scalar_one()
    thien_mu = db_session.execute(select(HeritagePlace).where(HeritagePlace.slug == "chua-thien-mu")).scalar_one()

    # Story 1 linkages
    assert story_bronze.place_id == tu_duc.id
    assert story_bronze.creator_id == sinh.id
    assert story_bronze.experience_id == exp_bronze.id
    assert story_bronze.status == "published"
    assert story_bronze.published_at is not None
    assert len(story_bronze.claims) == 2

    # Story 2 linkages
    assert story_enamel.place_id == thai_hoa.id
    assert story_enamel.creator_id == triet.id
    assert story_enamel.experience_id == exp_enamel.id
    assert story_enamel.status == "published"
    assert story_enamel.published_at is not None
    assert len(story_enamel.claims) == 2

    # Story 3 linkages
    assert story_paper.place_id == thien_mu.id
    assert story_paper.creator_id == huy.id
    assert story_paper.experience_id == exp_paper.id
    assert story_paper.status == "published"
    assert story_paper.published_at is not None
    assert len(story_paper.claims) == 2

    # 4. Verify Evidence Claims in DB
    all_claims = db_session.execute(select(RbpcClaimEvidence)).scalars().all()
    assert len(all_claims) == 6

    for c in all_claims:
        assert c.story_id in {story_bronze.id, story_enamel.id, story_paper.id}
        assert c.locale == "vi"
        assert c.support_type == "direct"
        assert c.review_status == "verified"
        assert c.citation_label is not None
        assert len(c.statement) > 20
        assert c.source_title is not None
        assert c.evidence_excerpt_private is not None  # English translation preserved in private excerpt


# --------------------------------------------------------------------------- #
# 7. Idempotency & Manual Consent Revocation Preservation
# --------------------------------------------------------------------------- #
def test_commercial_idempotency_and_revocation_preservation(db_session):
    """Verify re-import is idempotent and preserves manual consent revocations and reviews."""
    # 1. Initial import
    import_heritage_data(
        db=db_session,
        inventory_path=DEFAULT_INVENTORY_PATH,
        sketchfab_path=DEFAULT_SKETCHFAB_PATH,
        stories_path=DEFAULT_STORIES_PATH,
        creators_path=DEFAULT_CREATORS_PATH,
        experiences_path=DEFAULT_EXPERIENCES_PATH,
        dry_run=False,
    )

    # 2. Simulate manual consent revocation on artisan Đỗ Hữu Triết
    triet = db_session.execute(
        select(RbpcCreator).where(RbpcCreator.slug == "nghe-nhan-do-huu-triet")
    ).scalar_one()
    triet.consent_status = RbpcConsentStatus.revoked.value

    # 3. Simulate manual editorial review on story
    story = db_session.execute(
        select(RbpcStory).where(RbpcStory.slug == "tieng-chuong-khiem-cung")
    ).scalar_one()

    reviewer = User(
        email="story_curator@histolab.icu",
        password_hash="test-hash",
        display_name="Senior Story Curator",
        role=UserRole.admin,
    )
    db_session.add(reviewer)
    db_session.flush()

    reviewed_timestamp = datetime(2026, 10, 18, 14, 30, tzinfo=timezone.utc)
    story.reviewed_by = reviewer.id
    story.reviewed_at = reviewed_timestamp
    story.status = RbpcStoryStatus.published.value

    db_session.commit()

    # 4. Re-run import
    _, stats2 = import_heritage_data(
        db=db_session,
        inventory_path=DEFAULT_INVENTORY_PATH,
        sketchfab_path=DEFAULT_SKETCHFAB_PATH,
        stories_path=DEFAULT_STORIES_PATH,
        creators_path=DEFAULT_CREATORS_PATH,
        experiences_path=DEFAULT_EXPERIENCES_PATH,
        dry_run=False,
    )

    # Verify zero new insertions across all models
    assert stats2.places_inserted == 0
    assert stats2.media_inserted == 0
    assert stats2.creators_inserted == 0
    assert stats2.experiences_inserted == 0
    assert stats2.stories_inserted == 0
    assert stats2.claims_inserted == 0

    # Verify consent revocation was preserved (NOT overwritten with 'consented')
    assert stats2.creators_preserved_consent >= 1
    db_session.refresh(triet)
    assert triet.consent_status == RbpcConsentStatus.revoked.value

    # Verify story manual review was preserved
    assert stats2.stories_preserved_editorial >= 1
    db_session.refresh(story)
    assert story.reviewed_by == reviewer.id
    assert story.reviewed_at == reviewed_timestamp


# --------------------------------------------------------------------------- #
# 8. API Endpoints Functionality with Seeded Commercial Catalogue
# --------------------------------------------------------------------------- #
def test_api_rbpc_endpoints_with_seeded_data(client, db_session):
    """Verify FastAPI endpoints serve seeded commercial slice with complete relations."""
    # Seed data
    import_heritage_data(
        db=db_session,
        inventory_path=DEFAULT_INVENTORY_PATH,
        sketchfab_path=DEFAULT_SKETCHFAB_PATH,
        stories_path=DEFAULT_STORIES_PATH,
        creators_path=DEFAULT_CREATORS_PATH,
        experiences_path=DEFAULT_EXPERIENCES_PATH,
        dry_run=False,
    )

    # 1. GET /api/v1/rbpc/creators/{slug} for all 3 creators
    for slug, expected_name in [
        ("nghe-nhan-nguyen-van-sinh", "Nghệ nhân Nhân dân Nguyễn Văn Sinh"),
        ("nghe-nhan-do-huu-triet", "Thạc sĩ - Nghệ nhân Đỗ Hữu Triết"),
        ("nghe-nhan-than-van-huy", "Nghệ nhân Ưu tú Thân Văn Huy"),
    ]:
        res = client.get(f"/api/v1/rbpc/creators/{slug}")
        assert res.status_code == 200, res.text
        data = res.json()
        assert data["public_name"] == expected_name
        assert data["consent_status"] == "consented"
        assert len(data["experience_slugs"]) >= 1

    # 2. Detail checks for artisan Sinh
    res_sinh = client.get("/api/v1/rbpc/creators/nghe-nhan-nguyen-van-sinh")
    sinh_data = res_sinh.json()
    assert sinh_data["public_name"] == "Nghệ nhân Nhân dân Nguyễn Văn Sinh"
    assert sinh_data["craft_tradition_vi"] == "Đúc đồng Phường Đúc"
    assert "workshop-duc-dong-phuong-duc" in sinh_data["experience_slugs"]
    assert "tieng-chuong-khiem-cung" in sinh_data["approved_story_slugs"]

    # 3. GET /api/v1/rbpc/experiences/{slug} for all 3 experiences
    for exp_slug, expected_creator in [
        ("workshop-duc-dong-phuong-duc", "nghe-nhan-nguyen-van-sinh"),
        ("workshop-phap-lam-hue", "nghe-nhan-do-huu-triet"),
        ("workshop-hoa-giay-thanh-tien", "nghe-nhan-than-van-huy"),
    ]:
        res_exp = client.get(f"/api/v1/rbpc/experiences/{exp_slug}")
        assert res_exp.status_code == 200, res_exp.text
        exp_data = res_exp.json()
        assert exp_data["availability_mode"] == "inquiry_only"
        assert exp_data["creator_slug"] == expected_creator
        assert exp_data["indicative_price_amount"] > 0

    # 5. GET /api/v1/rbpc/stories
    res_stories = client.get("/api/v1/rbpc/stories")
    assert res_stories.status_code == 200
    stories_json = res_stories.json()
    assert stories_json["total"] == 3

    # 6. GET /api/v1/rbpc/stories/{slug} (Deep Story Detail)
    res_story_detail = client.get("/api/v1/rbpc/stories/tieng-chuong-khiem-cung")
    assert res_story_detail.status_code == 200
    story_data = res_story_detail.json()
    assert story_data["slug"] == "tieng-chuong-khiem-cung"
    assert story_data["title_vi"] == "Tiếng Đồng Phường Đúc & Chuông Vọng Khiêm Cung"
    assert story_data["creator"] is not None
    assert story_data["creator"]["slug"] == "nghe-nhan-nguyen-van-sinh"
    assert story_data["experience"] is not None
    assert story_data["experience"]["slug"] == "workshop-duc-dong-phuong-duc"
    assert len(story_data["evidence_claims"]) == 2
    assert story_data["evidence_claims"][0]["support_type"] == "direct"


# --------------------------------------------------------------------------- #
# 9. CLI Standalone Invocation
# --------------------------------------------------------------------------- #
def test_cli_commercial_seed_dry_run():
    """Verify seed_hue_heritage.py executes cleanly via CLI with all commercial datasets."""
    test_args = ["seed_hue_heritage.py", "--dry-run"]
    with patch.object(sys, "argv", test_args):
        exit_code = seed_hue_heritage.main()
        assert exit_code == 0
