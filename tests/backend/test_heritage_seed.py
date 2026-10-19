# -*- coding: utf-8 -*-
"""Unit and integration tests for Huế Heritage Seed and Ingestion Service.

Verifies:
1. Parsing and validation of data/heritage-hue/inventory.unesco-14.yaml
   - All 14 UNESCO property components (678-001..678-014)
   - 6 priority child monuments (contained in Kinh thành Huế)
   - 3 craft living communities
   - Total 23 places with unique slugs, valid coordinates, and parent links
2. Parsing and validation of data/heritage-hue/sketchfab-curated.yaml
   - All 23 curated Sketchfab 3D models
   - 32-hex model UIDs and licensing governance
   - Epistemic guardrail checks: SF-020 rejected accuracy, SF-010 blocked NC, SF-017 blocked NoAI
   - Candidate CC BY embeds (SF-009, SF-011, SF-016)
3. Dry-run validation service (zero database side-effects)
4. Safe commit mode upserting into database (places, relations, media assets)
5. Editorial protection: manual reviews and published statuses are never overwritten
6. Error handling for malformed coordinates, duplicate slugs, invalid parent slugs, and guardrail violations
7. Standalone CLI execution in dry-run mode
"""
from __future__ import annotations

import sys
import uuid
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest
from sqlalchemy import func, select

from backend.models_rbpc import (
    HeritageAccuracyGrade,
    HeritageCommercialUseStatus,
    HeritageEmbedPermissionStatus,
    HeritageHeritageRelation,
    HeritageMediaAsset,
    HeritagePlace,
    HeritageRecordStatus,
)
from backend.services.heritage_import import (
    DEFAULT_INVENTORY_PATH,
    DEFAULT_RELATIONS_PATH,
    DEFAULT_SKETCHFAB_PATH,
    HeritageImportService,
    ImportStats,
    ValidationReport,
    import_heritage_data,
    load_yaml_file,
    validate_heritage_import,
    validate_inventory_data,
    validate_relations_data,
    validate_sketchfab_data,
)
from scripts.heritage import seed_hue_heritage


# --------------------------------------------------------------------------- #
# 1. Inventory YAML Parsing & UNESCO-14 Scaffolding Tests
# --------------------------------------------------------------------------- #
def test_parse_and_validate_inventory_yaml():
    """Verify that inventory.unesco-14.yaml contains the exact required catalogue."""
    data = load_yaml_file(DEFAULT_INVENTORY_PATH)

    unesco = data.get("unesco_components") or []
    children = data.get("child_monuments") or []
    crafts = data.get("craft_communities") or []

    assert len(unesco) == 14, f"Expected 14 UNESCO components, got {len(unesco)}"
    assert len(children) == 6, f"Expected 6 child monuments, got {len(children)}"
    assert len(crafts) == 3, f"Expected 3 craft communities, got {len(crafts)}"

    all_places = unesco + children + crafts
    assert len(all_places) == 23, f"Expected 23 total places, got {len(all_places)}"

    # Check UNESCO component IDs 678-001 through 678-014
    unesco_ids = [p.get("official_reference_id") or p.get("unesco_id") for p in unesco]
    for i in range(1, 15):
        expected_id = f"678-{i:03d}"
        assert expected_id in unesco_ids, f"Missing UNESCO component {expected_id}"

    # Check slug uniqueness across all 23 places
    slugs = [p["slug"] for p in all_places]
    assert len(slugs) == len(set(slugs)), "Place slugs must be globally unique across catalogue"

    # Check child monuments containment hierarchy
    for child in children:
        assert child.get("parent_slug") == "kinh-thanh-hue", (
            f"Child monument '{child['slug']}' must have parent_slug 'kinh-thanh-hue'"
        )

    # Check coordinates validity for all places
    for p in all_places:
        coords = p.get("approximate_coordinates")
        assert coords is not None, f"Place '{p['slug']}' must define approximate_coordinates"
        lat = coords.get("latitude")
        lon = coords.get("longitude")
        assert lat is not None and -90.0 <= float(lat) <= 90.0, f"Invalid latitude in {p['slug']}"
        assert lon is not None and -180.0 <= float(lon) <= 180.0, f"Invalid longitude in {p['slug']}"
        # All places in Huế region (16.0 - 16.8 N, 107.0 - 108.0 E)
        assert 16.0 <= float(lat) <= 16.8, f"Latitude {lat} outside Huế province bounds for {p['slug']}"
        assert 107.4 <= float(lon) <= 107.8, f"Longitude {lon} outside Huế province bounds for {p['slug']}"


# --------------------------------------------------------------------------- #
# 2. Sketchfab YAML Parsing & Epistemic Guardrail Tests
# --------------------------------------------------------------------------- #
def test_parse_and_validate_sketchfab_yaml():
    """Verify that sketchfab-curated.yaml parses all 23 models and enforces guardrails."""
    data = load_yaml_file(DEFAULT_SKETCHFAB_PATH)
    models = data.get("models") or []

    assert len(models) == 23, f"Expected 23 Sketchfab models, got {len(models)}"

    model_ids = [m["id"] for m in models]
    for i in range(1, 24):
        expected_id = f"SF-{i:03d}"
        assert expected_id in model_ids, f"Missing Sketchfab model {expected_id}"

    # Verify each model has valid 32-character hex UID
    for m in models:
        uid = m.get("model_uid")
        assert uid is not None and len(uid) == 32, f"Model {m['id']} missing valid 32-hex model_uid"
        assert all(c in "0123456789abcdef" for c in uid.lower()), f"Model {m['id']} UID not hex"
        assert isinstance(m.get("noai"), bool), f"Model {m['id']} noai must be boolean"
        assert m.get("displayed_license") is not None, f"Model {m['id']} missing displayed_license"

    # Epistemic Guardrail 1: SF-020 must be explicitly rejected for accuracy
    sf020 = next(m for m in models if m["id"] == "SF-020")
    assert sf020["accuracy_grade"] == "rejected_inaccurate"
    assert sf020["content_status"] == "rejected_accuracy"
    assert sf020["embed_permission_status"] == "rejected"

    # Epistemic Guardrail 2: SF-010 (CC BY-NC-SA) blocked from commercial use
    sf010 = next(m for m in models if m["id"] == "SF-010")
    assert sf010["displayed_license"] == "CC BY-NC-SA"
    assert sf010["commercial_use_status"] == "blocked_nc"

    # Epistemic Guardrail 3: SF-017 (CC BY-NC-SA + NoAI) blocked from AI & commercial use
    sf017 = next(m for m in models if m["id"] == "SF-017")
    assert sf017["noai"] is True
    assert sf017["displayed_license"] == "CC BY-NC-SA"
    assert sf017["commercial_use_status"] == "blocked_nc"
    assert sf017["embed_permission_status"] == "blocked_noai"

    # Epistemic Guardrail 4: Candidate CC BY embeds (SF-009, SF-011, SF-016)
    for cid in ("SF-009", "SF-011", "SF-016"):
        cand = next(m for m in models if m["id"] == cid)
        assert cand["displayed_license"] == "CC BY"
        assert cand["commercial_use_status"] == "conditional_attribution_required"


# --------------------------------------------------------------------------- #
# 2b. Relations YAML Parsing & Knowledge Graph Verification Tests
# --------------------------------------------------------------------------- #
def test_parse_and_validate_relations_yaml():
    """Verify relations.yaml parses all 43 graph relationships with valid references."""
    inv_data = load_yaml_file(DEFAULT_INVENTORY_PATH)
    known_slugs = {
        p["slug"]
        for sec in ("unesco_components", "child_monuments", "craft_communities")
        for p in inv_data.get(sec, [])
    }
    assert len(known_slugs) == 23

    report = validate_relations_data(DEFAULT_RELATIONS_PATH, known_place_slugs=known_slugs)
    assert report.is_valid is True, f"Validation errors: {report.errors}"
    assert report.total_relations_count == 43
    assert len(report.errors) == 0

    rel_data = load_yaml_file(DEFAULT_RELATIONS_PATH)
    relations = rel_data.get("relations") or []
    assert len(relations) == 43

    for r in relations:
        assert r["id"].startswith("REL-")
        assert r["from_slug"] in known_slugs
        assert r["to_slug"] in known_slugs
        assert r["review_state"] == "verified"
        assert r["epistemic_certainty"] == "high"
        assert r["source_key"].startswith("SRC-")
        assert len(r["source_locator"]) > 0
        assert len(r["description_vi"]) > 10
        assert len(r["description_en"]) > 10


# --------------------------------------------------------------------------- #
# 3. Dry-Run Service Validation Report Tests
# --------------------------------------------------------------------------- #
def test_dry_run_validation_report():
    """Verify that HeritageImportService.validate() passes with zero errors."""
    service = HeritageImportService(
        inventory_path=DEFAULT_INVENTORY_PATH,
        sketchfab_path=DEFAULT_SKETCHFAB_PATH,
    )
    report = service.validate()

    assert report.is_valid is True
    assert len(report.errors) == 0, f"Unexpected validation errors: {report.errors}"
    assert report.unesco_components_count == 14
    assert report.child_monuments_count == 6
    assert report.craft_communities_count == 3
    assert report.total_places_count == 23
    assert report.models_count == 23
    assert report.total_relations_count > 0
    assert report.guardrails_passed is True
    assert report.guardrail_details["sf020_rejected_accuracy"] is True
    assert report.guardrail_details["sf010_blocked_nc"] is True
    assert report.guardrail_details["sf017_blocked_noai"] is True


# --------------------------------------------------------------------------- #
# 4. Invalidation and Error Detection Tests
# --------------------------------------------------------------------------- #
def test_validation_catches_invalid_coordinates():
    """Verify dry-run validation catches latitude / longitude out-of-bounds."""
    inv_data = load_yaml_file(DEFAULT_INVENTORY_PATH)
    corrupted = deepcopy(inv_data)
    # Set latitude out of range > 90
    corrupted["unesco_components"][0]["approximate_coordinates"]["latitude"] = 999.0

    report = validate_inventory_data(corrupted)
    assert report.is_valid is False
    assert any("out of bounds" in e for e in report.errors)


def test_validation_catches_duplicate_slug():
    """Verify dry-run validation catches duplicate slugs in the inventory."""
    inv_data = load_yaml_file(DEFAULT_INVENTORY_PATH)
    corrupted = deepcopy(inv_data)
    # Duplicate first component slug into second
    corrupted["unesco_components"][1]["slug"] = corrupted["unesco_components"][0]["slug"]

    report = validate_inventory_data(corrupted)
    assert report.is_valid is False
    assert any("Duplicate slug" in e for e in report.errors)


def test_validation_catches_invalid_parent_slug():
    """Verify dry-run validation catches reference to a non-existent parent slug."""
    inv_data = load_yaml_file(DEFAULT_INVENTORY_PATH)
    corrupted = deepcopy(inv_data)
    corrupted["child_monuments"][0]["parent_slug"] = "ghost-parent-citadel"

    report = validate_inventory_data(corrupted)
    assert report.is_valid is False
    assert any("non-existent parent_slug" in e for e in report.errors)


def test_validation_catches_invalid_model_uid():
    """Verify dry-run validation catches invalid (non 32-hex) Sketchfab model UIDs."""
    sf_data = load_yaml_file(DEFAULT_SKETCHFAB_PATH)
    corrupted = deepcopy(sf_data)
    # Malformed UID with non-hex characters and wrong length
    corrupted["models"][0]["model_uid"] = "invalid-uid-xyz-123"

    report = validate_sketchfab_data(corrupted)
    assert report.is_valid is False
    assert any("not a valid 32-character hexadecimal" in e for e in report.errors)


def test_validation_catches_sf020_guardrail_violation():
    """Verify dry-run validation flags SF-020 if someone attempts to un-reject it."""
    sf_data = load_yaml_file(DEFAULT_SKETCHFAB_PATH)
    corrupted = deepcopy(sf_data)
    for m in corrupted["models"]:
        if m["id"] == "SF-020":
            m["accuracy_grade"] = "survey_grade"
            m["content_status"] = "published"
            m["embed_permission_status"] = "permitted"

    report = validate_sketchfab_data(corrupted)
    assert report.is_valid is False
    assert any("GUARDRAIL VIOLATION: Model SF-020" in e for e in report.errors)


# --------------------------------------------------------------------------- #
# 5. Commit Mode Database Upsert Integration Tests
# --------------------------------------------------------------------------- #
def test_commit_mode_db_upsert(db_session):
    """Verify that commit mode correctly populates database tables."""
    report, stats = import_heritage_data(
        db=db_session,
        inventory_path=DEFAULT_INVENTORY_PATH,
        sketchfab_path=DEFAULT_SKETCHFAB_PATH,
        dry_run=False,
    )

    assert report.is_valid is True
    assert stats.dry_run is False
    assert stats.places_inserted == 23
    assert stats.relations_inserted > 0
    assert stats.media_inserted == 23

    # 1. Verify Heritage Places in DB
    places = db_session.execute(select(HeritagePlace)).scalars().all()
    assert len(places) >= 23

    citadel = db_session.execute(
        select(HeritagePlace).where(HeritagePlace.slug == "kinh-thanh-hue")
    ).scalar_one_or_none()
    assert citadel is not None
    assert citadel.entity_type == "site"
    assert citadel.heritage_category == "imperial_architecture"
    assert citadel.parent_id is None

    # Check child monument parent linkage
    ngo_mon = db_session.execute(
        select(HeritagePlace).where(HeritagePlace.slug == "ngo-mon")
    ).scalar_one_or_none()
    assert ngo_mon is not None
    assert ngo_mon.parent_id == citadel.id

    # 2. Verify Heritage Media Assets in DB
    media_assets = db_session.execute(select(HeritageMediaAsset)).scalars().all()
    assert len(media_assets) >= 23

    # Verify SF-020 negative guardrail in database
    sf020_asset = db_session.execute(
        select(HeritageMediaAsset).where(HeritageMediaAsset.model_uid == "84a8ab573293497ab0d4f97b4650bb55")
    ).scalar_one_or_none()
    assert sf020_asset is not None
    assert sf020_asset.accuracy_grade == HeritageAccuracyGrade.rejected_accuracy.value
    assert sf020_asset.content_status == "rejected_accuracy"
    assert sf020_asset.embed_permission_status == HeritageEmbedPermissionStatus.blocked.value
    assert sf020_asset.commercial_use_status == HeritageCommercialUseStatus.blocked_nc.value
    assert sf020_asset.embed_url is None

    # Verify SF-017 NoAI asset
    sf017_asset = db_session.execute(
        select(HeritageMediaAsset).where(HeritageMediaAsset.model_uid == "dca05e147d79420eb3696eefcf8e1f19")
    ).scalar_one_or_none()
    assert sf017_asset is not None
    assert sf017_asset.noai is True
    assert sf017_asset.commercial_use_status == HeritageCommercialUseStatus.blocked_nc.value
    assert sf017_asset.embed_permission_status == HeritageEmbedPermissionStatus.blocked.value

    # Verify SF-009 Candidate CC BY asset
    sf009_asset = db_session.execute(
        select(HeritageMediaAsset).where(HeritageMediaAsset.model_uid == "77728a86ad1d4964824b63844d50bfe7")
    ).scalar_one_or_none()
    assert sf009_asset is not None
    assert sf009_asset.commercial_use_status == HeritageCommercialUseStatus.permitted.value
    assert sf009_asset.embed_permission_status == HeritageEmbedPermissionStatus.permitted.value
    assert sf009_asset.embed_url is not None
    assert "77728a86ad1d4964824b63844d50bfe7" in sf009_asset.embed_url
    assert "CC BY 4.0" in sf009_asset.attribution_text

    # Verify place linkage for Ngọ Môn model SF-001
    sf001_asset = db_session.execute(
        select(HeritageMediaAsset).where(HeritageMediaAsset.model_uid == "1e07806a73ba42febc746a0c58142576")
    ).scalar_one_or_none()
    assert sf001_asset is not None
    assert sf001_asset.place_id == ngo_mon.id


# --------------------------------------------------------------------------- #
# 6. Editorial Protection & Re-import Idempotency Tests
# --------------------------------------------------------------------------- #
def test_idempotency_and_editorial_protection(db_session):
    """Verify that re-importing is idempotent and NEVER overwrites manual editorial reviews."""
    # 1. Initial import
    import_heritage_data(
        db=db_session,
        inventory_path=DEFAULT_INVENTORY_PATH,
        sketchfab_path=DEFAULT_SKETCHFAB_PATH,
        dry_run=False,
    )

    # 2. Simulate manual editorial review on a place
    place = db_session.execute(
        select(HeritagePlace).where(HeritagePlace.slug == "lang-tu-duc")
    ).scalar_one()
    reviewer_time = datetime(2026, 10, 18, 12, 0, 0, tzinfo=timezone.utc)
    place.editorial_status = HeritageRecordStatus.published.value
    place.published_at = reviewer_time
    place.visitor_summary_vi = "Tóm tắt đã được biên tập thủ công bởi Hội đồng Khoa học."

    # Create a real reviewer user for foreign key constraint
    from backend.models import User, UserRole
    reviewer_user = User(
        email="reviewer@histolab.icu",
        password_hash="test-hash",
        display_name="Senior Reviewer",
        role=UserRole.admin,
    )
    db_session.add(reviewer_user)
    db_session.flush()

    # Simulate manual rights review on a media asset
    reviewer_user_id = reviewer_user.id
    media_asset = db_session.execute(
        select(HeritageMediaAsset).where(HeritageMediaAsset.model_uid == "77728a86ad1d4964824b63844d50bfe7")
    ).scalar_one()
    media_asset.rights_reviewed_by = reviewer_user_id
    media_asset.rights_reviewed_at = reviewer_time
    media_asset.content_status = "cleared_for_this_use"

    # Simulate manual relation verification
    relation = db_session.execute(select(HeritageHeritageRelation)).scalars().first()
    relation.review_state = "verified"

    db_session.commit()

    # 3. Re-run import
    _, stats2 = import_heritage_data(
        db=db_session,
        inventory_path=DEFAULT_INVENTORY_PATH,
        sketchfab_path=DEFAULT_SKETCHFAB_PATH,
        dry_run=False,
    )

    # Verify zero new insertions (idempotency)
    assert stats2.places_inserted == 0
    assert stats2.media_inserted == 0
    assert stats2.relations_inserted == 0

    # Verify editorial review preservation
    assert stats2.places_preserved_editorial >= 1
    assert stats2.media_preserved_editorial >= 1

    # Verify database state after re-import
    db_session.refresh(place)
    assert place.editorial_status == HeritageRecordStatus.published.value
    assert place.published_at == reviewer_time

    db_session.refresh(media_asset)
    assert media_asset.rights_reviewed_by == reviewer_user_id
    assert media_asset.rights_reviewed_at == reviewer_time
    assert media_asset.content_status == "cleared_for_this_use"

    db_session.refresh(relation)
    assert relation.review_state == "verified"


# --------------------------------------------------------------------------- #
# 7. CLI Dry-Run Invocation Test
# --------------------------------------------------------------------------- #
def test_cli_dry_run_invocation():
    """Verify that scripts/heritage/seed_hue_heritage.py executes cleanly via CLI entrypoint."""
    test_args = ["seed_hue_heritage.py", "--dry-run"]
    with patch.object(sys, "argv", test_args):
        exit_code = seed_hue_heritage.main()
        assert exit_code == 0
