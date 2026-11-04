# -*- coding: utf-8 -*-
"""V5-T044 (Wave W04, Slot A04): Hotspot and claim binding test suite.

Requirements & Invariants:
1. Persist 3D hotspot coordinates linked to approved source-based historical claim,
   historical entity/object, and asset revision.
2. Negative abuse: Hotspot cannot bind unpublished or invalid historical claims
   (fails validation with HTTP 422 HOTSPOT_CLAIM_UNPUBLISHED_OR_INVALID).
3. Negative abuse: Disputed historical claims cannot be bound to hotspots
   (fails validation with HTTP 422 HOTSPOT_CLAIM_DISPUTED).
4. Negative abuse: Claim entity mismatch is strictly rejected
   (fails validation with HTTP 422 HOTSPOT_CLAIM_ENTITY_MISMATCH).
5. Positive persistence: Hotspot with approved claim, entity, and asset revision
   persists cleanly and updates correctly through both creation and patch endpoints.
6. Non-existent claim / entity references return appropriate 404 errors.
"""
from __future__ import annotations

import uuid
from typing import Generator
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.history_models import (
    HistoricalClaim,
    HistoricalEntity,
    HistoricalSource,
    HistoricalVerificationStatus,
)
from backend.imperial_models import ImperialSite, ImperialZone
from backend.imperial_v51_models import (
    ImperialLearningMedia,
    ImperialMediaHotspot,
)
from backend.models import User, UserRole


# --------------------------------------------------------------------------- #
# Helpers & Fixtures
# --------------------------------------------------------------------------- #
def _create_staff_user(client: TestClient, db: Session, email_prefix: str = "staff") -> User:
    email = f"{email_prefix}_{uuid.uuid4().hex[:6]}@example.com"
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password123!", "display_name": "Imperial Staff"},
    )
    user = db.scalar(select(User).where(User.email == email))
    user.role = UserRole.admin
    db.commit()

    # Login to set session cookies
    client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Password123!"},
    )
    return user


def _seed_sample_site(db: Session) -> tuple[ImperialZone, ImperialSite]:
    zone_slug = f"zone-t044-{uuid.uuid4().hex[:6]}"
    zone = ImperialZone(
        title_vi="Khu vực khảo sát",
        slug=zone_slug,
        display_order=1,
    )
    db.add(zone)
    db.flush()

    site_slug = f"site-t044-{uuid.uuid4().hex[:6]}"
    site = ImperialSite(
        zone_id=zone.id,
        name_vi="Điện Thái Hòa",
        slug=site_slug,
        learning_level="L1_DOCUMENTED",
        is_published=True,
    )
    db.add(site)
    db.commit()
    db.refresh(site)
    return zone, site


def _seed_historical_entity(db: Session, slug_prefix: str = "ngai-vang") -> HistoricalEntity:
    entity = HistoricalEntity(
        entity_type="relic",
        slug=f"{slug_prefix}-{uuid.uuid4().hex[:6]}",
        name_vi="Ngai vàng triều Nguyễn",
        publication_status="published",
    )
    db.add(entity)
    db.commit()
    db.refresh(entity)
    return entity


def _seed_historical_claim(
    db: Session,
    entity: HistoricalEntity,
    verification_status: str = "expert_verified",
    confidence: str = "high",
) -> HistoricalClaim:
    claim = HistoricalClaim(
        entity_id=entity.id,
        claim_type="factual",
        statement_vi="Ngai vàng được chế tác dưới thời vua Gia Long vào năm 1802.",
        confidence=confidence,
        verification_status=verification_status,
        origin="archival_curation",
        is_current=True,
    )
    db.add(claim)
    db.commit()
    db.refresh(claim)
    return claim


def _seed_learning_media(
    db: Session,
    site: ImperialSite,
    kind: str = "model3d",
    asset_revision: int = 2,
) -> ImperialLearningMedia:
    media = ImperialLearningMedia(
        site_id=site.id,
        kind=kind,
        media_url="https://assets.histolab.icu/models/thai_hoa_interior.glb",
        asset_revision=asset_revision,
        license_status="approved",
        review_status="published",
    )
    db.add(media)
    db.commit()
    db.refresh(media)
    return media


# --------------------------------------------------------------------------- #
# Test Cases
# --------------------------------------------------------------------------- #
class TestHotspotClaimBinding:
    """Test suite for V5-T044: Hotspot and claim binding."""

    def test_positive_persist_3d_hotspot_linked_to_approved_claim_and_entity(
        self, client: TestClient, db_session: Session
    ):
        """Verifies 3D hotspot coordinates persist cleanly when bound to an approved claim, entity, and asset revision."""
        _create_staff_user(client, db_session)
        _, site = _seed_sample_site(db_session)
        media = _seed_learning_media(db_session, site, kind="model3d", asset_revision=3)
        entity = _seed_historical_entity(db_session)
        claim = _seed_historical_claim(db_session, entity, verification_status="expert_verified")

        payload = {
            "point_kind": "point",
            "u": 0.3542,
            "v": 0.6219,
            "title": "Vị trí ngai vàng trên mô hình 3D",
            "description": "Tọa độ 3D và góc nhìn chính diện ngai vàng",
            "position_payload": {
                "x": 1.25,
                "y": 0.85,
                "z": -2.40,
                "normal": [0.0, 1.0, 0.0],
                "mesh_name": "Throne_Base_Mesh_01",
            },
            "claim_id": str(claim.id),
            "entity_id": str(entity.id),
            "asset_revision": 3,
            "review_status": "published",
        }

        res = client.post(
            f"/api/v1/imperial/admin/media/{media.id}/hotspots",
            json=payload,
        )
        assert res.status_code == 201, res.text
        data = res.json()
        assert data["title"] == payload["title"]
        assert data["claim_id"] == str(claim.id)
        assert data["entity_id"] == str(entity.id)
        assert data["asset_revision"] == 3
        assert data["position_payload"]["mesh_name"] == "Throne_Base_Mesh_01"

        # Verify DB persistence directly
        hotspot_id = data["id"]
        hotspot_db = db_session.get(ImperialMediaHotspot, uuid.UUID(hotspot_id))
        assert hotspot_db is not None
        assert hotspot_db.claim_id == claim.id
        assert hotspot_db.entity_id == entity.id
        assert hotspot_db.asset_revision == 3
        assert hotspot_db.position_payload["x"] == 1.25

    def test_negative_abuse_hotspot_cannot_bind_unpublished_or_unreviewed_claim(
        self, client: TestClient, db_session: Session
    ):
        """Negative abuse: Hotspot cannot bind unreviewed, needs_source, or draft historical claim."""
        _create_staff_user(client, db_session)
        _, site = _seed_sample_site(db_session)
        media = _seed_learning_media(db_session, site)
        entity = _seed_historical_entity(db_session)

        # 1. Unreviewed claim
        claim_unreviewed = _seed_historical_claim(
            db_session, entity, verification_status="unreviewed"
        )
        payload = {
            "point_kind": "point",
            "u": 0.4,
            "v": 0.5,
            "title": "Unreviewed Hotspot",
            "claim_id": str(claim_unreviewed.id),
            "entity_id": str(entity.id),
        }
        res = client.post(f"/api/v1/imperial/admin/media/{media.id}/hotspots", json=payload)
        assert res.status_code == 422
        assert "HOTSPOT_CLAIM_UNPUBLISHED_OR_INVALID" in res.text

        # 2. Needs source claim
        claim_needs_source = _seed_historical_claim(
            db_session, entity, verification_status="needs_source"
        )
        payload["claim_id"] = str(claim_needs_source.id)
        res2 = client.post(f"/api/v1/imperial/admin/media/{media.id}/hotspots", json=payload)
        assert res2.status_code == 422
        assert "HOTSPOT_CLAIM_UNPUBLISHED_OR_INVALID" in res2.text

    def test_negative_abuse_hotspot_cannot_bind_disputed_claim(
        self, client: TestClient, db_session: Session
    ):
        """Negative abuse: Hotspot cannot bind disputed or contested claim."""
        _create_staff_user(client, db_session)
        _, site = _seed_sample_site(db_session)
        media = _seed_learning_media(db_session, site)
        entity = _seed_historical_entity(db_session)

        # Claim with confidence="disputed"
        claim_disputed = _seed_historical_claim(
            db_session, entity, verification_status="disputed", confidence="disputed"
        )
        payload = {
            "point_kind": "point",
            "u": 0.5,
            "v": 0.5,
            "title": "Disputed Hotspot",
            "claim_id": str(claim_disputed.id),
            "entity_id": str(entity.id),
        }
        res = client.post(f"/api/v1/imperial/admin/media/{media.id}/hotspots", json=payload)
        assert res.status_code == 422

    def test_negative_abuse_hotspot_claim_entity_mismatch_rejected(
        self, client: TestClient, db_session: Session
    ):
        """Negative abuse: If hotspot specifies entity_id, claim must belong to that entity."""
        _create_staff_user(client, db_session)
        _, site = _seed_sample_site(db_session)
        media = _seed_learning_media(db_session, site)
        entity1 = _seed_historical_entity(db_session, slug_prefix="ngai-vang-1")
        entity2 = _seed_historical_entity(db_session, slug_prefix="cot-co-2")
        claim1 = _seed_historical_claim(db_session, entity1, verification_status="expert_verified")

        payload = {
            "point_kind": "point",
            "u": 0.5,
            "v": 0.5,
            "title": "Mismatched Entity Hotspot",
            "claim_id": str(claim1.id),
            "entity_id": str(entity2.id),  # Mismatched entity
        }
        res = client.post(f"/api/v1/imperial/admin/media/{media.id}/hotspots", json=payload)
        assert res.status_code == 422
        assert "HOTSPOT_CLAIM_ENTITY_MISMATCH" in res.text

    def test_hotspot_patch_binding_update_and_validation(
        self, client: TestClient, db_session: Session
    ):
        """Verifies patching an existing hotspot to bind claim and entity enforces the same strict gates."""
        _create_staff_user(client, db_session)
        _, site = _seed_sample_site(db_session)
        media = _seed_learning_media(db_session, site, asset_revision=1)
        entity = _seed_historical_entity(db_session)
        claim_verified = _seed_historical_claim(db_session, entity, verification_status="editor_reviewed")
        claim_unverified = _seed_historical_claim(db_session, entity, verification_status="rejected")

        # 1. Create plain hotspot without claims
        res_create = client.post(
            f"/api/v1/imperial/admin/media/{media.id}/hotspots",
            json={"point_kind": "point", "u": 0.1, "v": 0.2, "title": "Base Hotspot"},
        )
        assert res_create.status_code == 201
        hotspot_id = res_create.json()["id"]

        # 2. Patch with invalid rejected claim -> Rejected 422
        res_patch_invalid = client.patch(
            f"/api/v1/imperial/admin/hotspots/{hotspot_id}",
            json={"claim_id": str(claim_unverified.id)},
        )
        assert res_patch_invalid.status_code == 422
        assert "HOTSPOT_CLAIM_UNPUBLISHED_OR_INVALID" in res_patch_invalid.text

        # 3. Patch with valid approved claim & entity -> Success 200
        res_patch_valid = client.patch(
            f"/api/v1/imperial/admin/hotspots/{hotspot_id}",
            json={
                "claim_id": str(claim_verified.id),
                "entity_id": str(entity.id),
                "asset_revision": 2,
            },
        )
        assert res_patch_valid.status_code == 200
        data = res_patch_valid.json()
        assert data["claim_id"] == str(claim_verified.id)
        assert data["entity_id"] == str(entity.id)
        assert data["asset_revision"] == 2

    def test_hotspot_binding_nonexistent_ids_return_404(
        self, client: TestClient, db_session: Session
    ):
        """Non-existent claim or entity IDs return 404."""
        _create_staff_user(client, db_session)
        _, site = _seed_sample_site(db_session)
        media = _seed_learning_media(db_session, site)
        fake_uuid = str(uuid.uuid4())

        # Non-existent claim
        res1 = client.post(
            f"/api/v1/imperial/admin/media/{media.id}/hotspots",
            json={"point_kind": "point", "u": 0.2, "v": 0.3, "title": "Test", "claim_id": fake_uuid},
        )
        assert res1.status_code == 404
        assert "HISTORICAL_CLAIM_NOT_FOUND" in res1.text

        # Non-existent entity
        res2 = client.post(
            f"/api/v1/imperial/admin/media/{media.id}/hotspots",
            json={"point_kind": "point", "u": 0.2, "v": 0.3, "title": "Test", "entity_id": fake_uuid},
        )
        assert res2.status_code == 404
        assert "HISTORICAL_ENTITY_NOT_FOUND" in res2.text
