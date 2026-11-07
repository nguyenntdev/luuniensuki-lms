# -*- coding: utf-8 -*-
"""V5-T121 (Wave W12, Slot A01): Source/rights publication gate final test suite.

Audits and verifies:
1. Completeness Report across all 9 Urns and 162 Motifs:
   - Endpoint GET /api/v1/heritage/publication-gate/report
   - 5 mandatory quality criteria (canonical_entity, spatial_3d_coordinates,
     rubbing_2d_assets, han_nom_review, sourced_claims_verification).
   - Accurate tracking of ready vs blocked items across all 162 motifs.
2. Sampling Verification across Urns and Motifs:
   - Endpoint GET /api/v1/heritage/publication-gate/sampling-verify
   - Verifies 2D rubbing existence on disk, 3D coordinate bounds,
     and guarantees 0 unapproved claims and 0 revoked media assets in sample.
3. Retract Wrong Claim (Staff Mutation & Immediate Public Gate):
   - Endpoint POST /api/v1/heritage/claims/{claim_id}/retract
   - Demotes wrong/contested claims to 'rejected' or 'disputed' with is_current=False.
   - Appends immutable audit entry to historical_content_audit_log.
   - Public motif claims endpoint immediately excludes retracted claim (zero leak).
4. Revoke Media Asset (Staff Mutation & Immediate Public Gate):
   - Endpoint POST /api/v1/heritage/media/{asset_id}/revoke
   - Invalidation of rights across HistoricalAsset and HeritageMediaAsset.
   - Immediate issuance of anti-stale cache headers and registration in asset_cache_revocations.
   - Public place media and 3D endpoints immediately exclude revoked media.
5. Role-Based Access Control (RBAC):
   - Anonymous visitors get 401 Unauthorized for mutations.
   - Regular learners/students get 403 Forbidden.
   - Only staff/admin roles are authorized to retract claims or revoke media.
6. Negative Abuse Protection (Public Random Audit):
   - Endpoint GET /api/v1/heritage/audit/random-audit
   - Invariant: Exactly 0 unapproved claims or revoked media assets are visible on public random audit.
7. Completion Artifact Verification:
   - Validates artifacts/implementation/W12/W12_A01_source_rights_gate_final.json.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.history_models import (
    AssetCacheRevocation,
    HistoricalAsset,
    HistoricalClaim,
    HistoricalContentAuditLog,
    HistoricalEntity,
    HistoricalSource,
)
from backend.models import User, UserRole
from backend.models_rbpc import (
    HeritageMediaAsset,
    HeritagePlace,
    HeritageRecordStatus,
)
from backend.services.offline_licensing import is_asset_revoked

REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_PATH = REPO_ROOT / "artifacts" / "implementation" / "W12" / "W12_A01_source_rights_gate_final.json"


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _create_user(client: TestClient, db_session: Session, email: str, role: UserRole = UserRole.admin) -> User:
    """Register and login a test user with designated role."""
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password123!", "display_name": f"User {role.value}"},
    )
    user = db_session.execute(select(User).where(User.email == email)).scalar_one()
    user.role = role
    db_session.commit()
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Password123!"},
    )
    assert login_res.status_code == 200, f"Login failed for {email}: {login_res.text}"
    return user


def _seed_motif_entity(db_session: Session, slug: str = "cao-dinh-01", name_vi: str = "Cao Đỉnh 01") -> HistoricalEntity:
    """Seed historical entity for a motif."""
    ent = db_session.scalar(select(HistoricalEntity).where(HistoricalEntity.slug == slug))
    if not ent:
        ent = HistoricalEntity(
            entity_type="relief",
            slug=slug,
            name_vi=name_vi,
            publication_status="published",
        )
        db_session.add(ent)
        db_session.flush()
    return ent


def _seed_claim(
    db_session: Session,
    entity: HistoricalEntity,
    statement_vi: str,
    *,
    claim_type: str = "identification",
    verification_status: str = "published",
    confidence: str = "high",
    is_current: bool = True,
) -> HistoricalClaim:
    """Seed an atomic historical claim."""
    claim = HistoricalClaim(
        entity_id=entity.id,
        claim_type=claim_type,
        statement_vi=statement_vi,
        verification_status=verification_status,
        confidence=confidence,
        origin="editorial",
        is_current=is_current,
    )
    db_session.add(claim)
    db_session.flush()
    return claim


def _seed_place(
    db_session: Session,
    slug: str = "test-monument-gate",
    name_vi: str = "Di tích Thử nghiệm",
) -> HeritagePlace:
    """Seed a heritage place."""
    place = db_session.scalar(select(HeritagePlace).where(HeritagePlace.slug == slug))
    if not place:
        place = HeritagePlace(
            slug=slug,
            name_vi=name_vi,
            entity_type="monument",
            heritage_category="imperial_architecture",
            editorial_status=HeritageRecordStatus.published.value,
            content_scope="RBPC_HUE",
        )
        db_session.add(place)
        db_session.flush()
    return place


# --------------------------------------------------------------------------- #
# Tests
# --------------------------------------------------------------------------- #
def test_completeness_report_structure_and_counts(client: TestClient, db_session: Session):
    """Test completeness report returns 9 urns, 162 motifs, and all 5 criteria."""
    res = client.get("/api/v1/heritage/publication-gate/report")
    assert res.status_code == 200, res.text
    data = res.json()

    assert data["ticket"] == "V5-T121"
    assert data["slot"] == "W12-A01"
    assert data["status"] == "COMPLETED"
    assert data["total_urns"] == 9
    assert data["total_motifs"] == 162
    assert data["ready_count"] + data["blocked_count"] == 162

    crit = data["criteria_summary"]
    assert "canonical_entity" in crit
    assert "spatial_3d_coordinates" in crit
    assert "rubbing_2d_assets" in crit
    assert "han_nom_review" in crit
    assert "sourced_claims_verification" in crit

    assert crit["canonical_entity"]["passed"] == 162
    assert crit["spatial_3d_coordinates"]["passed"] == 162
    assert crit["rubbing_2d_assets"]["passed"] == 162
    assert crit["han_nom_review"]["passed"] == 158
    assert crit["han_nom_review"]["failed"] == 4


def test_sampling_verification_across_urns_and_motifs(client: TestClient, db_session: Session):
    """Test sampling verification across urns and motifs succeeds without violations."""
    res = client.get("/api/v1/heritage/publication-gate/sampling-verify?sample_size=30&seed=42")
    assert res.status_code == 200, res.text
    data = res.json()

    assert data["sample_size"] == 30
    assert len(data["sampled_identifiers"]) == 30
    assert data["violations_found"] == 0
    assert data["unapproved_claims_detected"] == 0
    assert data["revoked_media_detected"] == 0
    assert data["sampling_passed"] is True


def test_retract_wrong_claim_staff_success(client: TestClient, db_session: Session):
    """Test staff retraction of a wrong claim immediately demotes it and hides from public."""
    # Seed motif and claim
    ent = _seed_motif_entity(db_session, slug="cao-dinh-01", name_vi="Cao Đỉnh 01")
    claim = _seed_claim(
        db_session,
        ent,
        "Họa tiết đúc hình Rồng thời Minh Mạng năm 1836.",
        verification_status="published",
        confidence="high",
        is_current=True,
    )
    db_session.commit()

    # Public claims endpoint initially returns this claim
    pub_res = client.get("/api/v1/heritage/catalog/motifs/urn_cao_dinh_01/claims")
    assert pub_res.status_code == 200, pub_res.text
    pub_claims = pub_res.json()["claims"]
    assert any(c["id"] == str(claim.id) for c in pub_claims)

    # Make staff user and retract the claim
    admin = _create_user(client, db_session, "staff_retract@histolab.vn", role=UserRole.admin)

    retract_res = client.post(
        f"/api/v1/heritage/claims/{claim.id}/retract",
        json={
            "claim_id": str(claim.id),
            "reason": "Historical erratum: misattributed motif animal class.",
            "new_status": "rejected",
        },
    )
    assert retract_res.status_code == 200, retract_res.text
    retract_data = retract_res.json()
    assert retract_data["status"] == "success"
    assert retract_data["is_current"] is False
    assert retract_data["verification_status"] == "rejected"
    assert retract_data["confidence"] == "contested"

    # Verify DB state
    db_session.refresh(claim)
    assert claim.is_current is False
    assert claim.verification_status == "rejected"
    assert claim.confidence == "contested"
    assert "[RETRACTED]" in (claim.review_notes or "")
    assert claim.is_retracted is True
    assert claim.is_approved is False

    # Verify audit log was recorded
    audit = db_session.scalar(
        select(HistoricalContentAuditLog).where(
            HistoricalContentAuditLog.resource_id == claim.id,
            HistoricalContentAuditLog.action == "retract_claim",
        )
    )
    assert audit is not None
    assert audit.reason == "Historical erratum: misattributed motif animal class."

    # Negative abuse check: public call now strictly omits the retracted claim (0 leak)
    client.post("/api/v1/auth/logout")
    pub_res2 = client.get("/api/v1/heritage/catalog/motifs/urn_cao_dinh_01/claims")
    assert pub_res2.status_code == 200
    pub_claims2 = pub_res2.json()["claims"]
    assert not any(c["id"] == str(claim.id) for c in pub_claims2)


def test_retract_claim_unauthorized_and_forbidden(client: TestClient, db_session: Session):
    """Test retract claim enforces RBAC: 401 for anonymous, 403 for learner."""
    ent = _seed_motif_entity(db_session, slug="nhan-dinh-01", name_vi="Nhân Đỉnh 01")
    claim = _seed_claim(db_session, ent, "Họa tiết thử nghiệm RBAC.", verification_status="published")
    db_session.commit()

    # Anonymous call -> 401
    client.post("/api/v1/auth/logout")
    anon_res = client.post(
        f"/api/v1/heritage/claims/{claim.id}/retract",
        json={"claim_id": str(claim.id), "reason": "Unauthorized attempt."},
    )
    assert anon_res.status_code == 401

    # Student/learner call -> 403
    _create_user(client, db_session, "learner_retract@histolab.vn", role=UserRole.learner)
    student_res = client.post(
        f"/api/v1/heritage/claims/{claim.id}/retract",
        json={"claim_id": str(claim.id), "reason": "Student attempt."},
    )
    assert student_res.status_code == 403

    # Mismatched claim_id path vs body -> 400
    _create_user(client, db_session, "admin_mismatch@histolab.vn", role=UserRole.admin)
    other_id = uuid.uuid4()
    bad_res = client.post(
        f"/api/v1/heritage/claims/{claim.id}/retract",
        json={"claim_id": str(other_id), "reason": "Mismatched ID."},
    )
    assert bad_res.status_code == 400


def test_revoke_media_asset_historical_asset_staff(client: TestClient, db_session: Session):
    """Test staff revocation of a HistoricalAsset immediately sets no-cache headers and purges CDN."""
    admin = _create_user(client, db_session, "staff_asset_revoke@histolab.vn", role=UserRole.admin)

    asset = HistoricalAsset(
        asset_type="3d_model",
        storage_url="https://assets.luunien.vn/models/urn_du_dinh.glb",
        rights_status="cleared",
        public_display_allowed=True,
    )
    db_session.add(asset)
    db_session.commit()

    assert asset.is_approved is True
    assert asset.is_revoked is False

    revoke_res = client.post(
        f"/api/v1/heritage/media/{asset.id}/revoke",
        json={
            "asset_id": str(asset.id),
            "reason": "Copyright withdrawal request by rights holder.",
            "cdn_purge": True,
        },
    )
    assert revoke_res.status_code == 200, revoke_res.text
    data = revoke_res.json()
    assert data["status"] == "success"
    assert data["cdn_purged"] is True
    assert "no-cache" in data["cache_headers"]["Cache-Control"]

    # Verify DB state
    db_session.refresh(asset)
    assert asset.is_revoked is True
    assert asset.is_approved is False
    assert asset.public_display_allowed is False
    assert asset.rights_status == "revoked"

    # Verify AssetCacheRevocation ledger row
    rev_row = db_session.scalar(
        select(AssetCacheRevocation).where(AssetCacheRevocation.asset_id == str(asset.id))
    )
    assert rev_row is not None
    assert rev_row.cdn_purged is True
    assert is_asset_revoked(str(asset.id)) is True


def test_revoke_media_asset_heritage_media_staff(client: TestClient, db_session: Session):
    """Test staff revocation of a HeritageMediaAsset immediately hides it from place media."""
    admin = _create_user(client, db_session, "staff_media_revoke@histolab.vn", role=UserRole.admin)

    place = _seed_place(db_session, slug="monument-revocation-test")
    media = HeritageMediaAsset(
        place_id=place.id,
        media_type="photo",
        original_url="https://assets.luunien.vn/photos/monument-01.jpg",
        content_status="candidate",
        embed_permission_status="permitted",
        accuracy_grade="historian_reviewed",
        content_scope="RBPC_HUE",
    )
    db_session.add(media)
    db_session.commit()

    # Public media initially returns this asset
    client.post("/api/v1/auth/logout")
    m_res = client.get(f"/api/v1/heritage/places/{place.slug}/media")
    assert m_res.status_code == 200
    assert any(m["id"] == str(media.id) for m in m_res.json())

    # Staff revokes media asset
    client.post(
        "/api/v1/auth/login",
        json={"email": "staff_media_revoke@histolab.vn", "password": "Password123!"},
    )
    rev_res = client.post(
        f"/api/v1/heritage/media/{media.id}/revoke",
        json={
            "asset_id": str(media.id),
            "reason": "Photographer requested image retraction.",
            "cdn_purge": True,
        },
    )
    assert rev_res.status_code == 200, rev_res.text

    # Verify DB state
    db_session.refresh(media)
    assert media.content_status == "revoked"
    assert media.embed_permission_status == "blocked"

    # Public media endpoint now strictly omits revoked media (0 leak)
    client.post("/api/v1/auth/logout")
    m_res2 = client.get(f"/api/v1/heritage/places/{place.slug}/media")
    assert m_res2.status_code == 200
    assert not any(m["id"] == str(media.id) for m in m_res2.json())


def test_revoke_media_unauthorized_and_forbidden(client: TestClient, db_session: Session):
    """Test revoke media enforces RBAC: 401 for anonymous, 403 for student."""
    place = _seed_place(db_session, slug="monument-rbac-test")
    media = HeritageMediaAsset(
        place_id=place.id,
        media_type="photo",
        original_url="https://assets.luunien.vn/photos/test-rbac.jpg",
        content_status="candidate",
        embed_permission_status="permitted",
        content_scope="RBPC_HUE",
    )
    db_session.add(media)
    db_session.commit()

    # Anonymous -> 401
    client.post("/api/v1/auth/logout")
    anon = client.post(
        f"/api/v1/heritage/media/{media.id}/revoke",
        json={"asset_id": str(media.id), "reason": "Anon attempt."},
    )
    assert anon.status_code == 401

    # Student/learner -> 403
    _create_user(client, db_session, "learner_media_revoke@histolab.vn", role=UserRole.learner)
    stud = client.post(
        f"/api/v1/heritage/media/{media.id}/revoke",
        json={"asset_id": str(media.id), "reason": "Student attempt."},
    )
    assert stud.status_code == 403


def test_negative_abuse_random_public_audit(client: TestClient, db_session: Session):
    """Negative abuse invariant: random public audit finds exactly 0 unapproved claims or revoked media."""
    # Seed a mixture of approved and unapproved items
    ent = _seed_motif_entity(db_session, slug="anh-dinh-01", name_vi="Anh Đỉnh 01")
    _seed_claim(db_session, ent, "Claim A approved", verification_status="published", confidence="high")
    _seed_claim(db_session, ent, "Claim B draft unapproved", verification_status="unreviewed", confidence="unknown")
    _seed_claim(db_session, ent, "Claim C disputed", verification_status="disputed", confidence="contested")
    _seed_claim(db_session, ent, "Claim D retracted", verification_status="rejected", is_current=False)

    place = _seed_place(db_session, slug="monument-audit-test")
    # Cleared media
    db_session.add(
        HeritageMediaAsset(
            place_id=place.id,
            media_type="photo",
            original_url="https://assets.luunien.vn/photos/cleared.jpg",
            content_status="published",
            embed_permission_status="permitted",
            accuracy_grade="historian_reviewed",
            content_scope="RBPC_HUE",
        )
    )
    # Revoked media
    db_session.add(
        HeritageMediaAsset(
            place_id=place.id,
            media_type="photo",
            original_url="https://assets.luunien.vn/photos/revoked.jpg",
            content_status="revoked",
            embed_permission_status="blocked",
            accuracy_grade="historian_reviewed",
            content_scope="RBPC_HUE",
        )
    )
    db_session.commit()

    # Anonymous public audit call
    client.post("/api/v1/auth/logout")
    audit_res = client.get("/api/v1/heritage/audit/random-audit?iterations=50")
    assert audit_res.status_code == 200, audit_res.text
    audit_data = audit_res.json()

    assert audit_data["iterations"] == 50
    assert audit_data["unapproved_claims_leaked"] == 0
    assert audit_data["revoked_media_leaked"] == 0
    assert audit_data["passed"] is True


def test_place_detail_and_3d_guardrails_omit_revoked_models(client: TestClient, db_session: Session):
    """Test 3D model queries and place detail omit revoked 3D assets."""
    place = _seed_place(db_session, slug="monument-3d-guardrail")
    model = HeritageMediaAsset(
        place_id=place.id,
        media_type="glb",
        original_url="https://assets.luunien.vn/models/monument.glb",
        content_status="revoked",
        embed_permission_status="blocked",
        accuracy_grade="survey_grade",
        content_scope="RBPC_HUE",
    )
    db_session.add(model)
    db_session.commit()

    # 3D endpoint returns empty array (graceful 2D fallback)
    res_3d = client.get(f"/api/v1/heritage/places/{place.slug}/3d")
    assert res_3d.status_code == 200
    assert res_3d.json() == []

    # Detail view has has_3d=False
    detail_res = client.get(f"/api/v1/heritage/places/{place.slug}/detail")
    assert detail_res.status_code == 200
    assert detail_res.json()["has_3d"] is False


def test_artifact_metadata_integrity():
    """Verify W12-A01 implementation artifact exists and matches contract specifications."""
    assert ARTIFACT_PATH.is_file(), f"Artifact missing at {ARTIFACT_PATH}"
    with open(ARTIFACT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["ticket"] == "V5-T121"
    assert data["slot"] == "W12-A01"
    assert data["priority"] == "P0"
    assert data["classification"] == "PRODUCTION_COMPLETION"
    assert data["status"] == "COMPLETED"
    assert data["completeness"]["total_urns"] == 9
    assert data["completeness"]["total_motifs"] == 162
    assert data["negative_abuse_verified"]["unapproved_claims_leaked"] == 0
    assert data["negative_abuse_verified"]["revoked_media_leaked"] == 0
