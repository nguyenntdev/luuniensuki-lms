# -*- coding: utf-8 -*-
"""V5-T053: Mobile Catalog + Metadata Parity Test Suite.

Wave W05, Slot A03 (Priority: P1, Classification: PRODUCTION_COMPLETION).
Verifies:
1. Canonical Urn and Motif Catalog Parity:
   - Exactly 9 canonical Urns (cao-dinh .. huyen-dinh) in spatial display order (1..9).
   - Exactly 162 canonical Motifs (strictly 18 per urn) with stable IDs (urn_cao_dinh_01..18 .. urn_huyen_dinh_01..18).
   - Slugs, display orders, reign titles, temple names, Hán-Nôm names, 3D meshes, and spatial coordinates.
2. Evidence Status Labels matching Web Platform:
   - Epistemic status labels: verified, needs_review, disputed, rejected.
   - The 4 known unconfirmed motifs from W02-A06 (urn_nghi_dinh_03, urn_thuan_dinh_13,
     urn_tuyen_dinh_11, urn_huyen_dinh_12) strictly default to 'needs_review'.
   - Confirmed motifs default to 'verified'.
3. ETag / HTTP Conditional Caching:
   - GET /api/v1/heritage/catalog returns 200 with ETag and Cache-Control headers.
   - Subsequent GET with matching If-None-Match returns HTTP 304 Not Modified with empty body.
   - Single Urn and Motif endpoints support conditional GET with ETag.
4. Negative Abuse Test (Server Revision Update & Client Refresh Anti-Drift):
   - When server updates an approved revision of an urn or motif, the catalog ETag is recalculated.
   - Client refresh with previous cached ETag receives HTTP 200 OK (NOT 304) with the new revision and new ETag.
   - Prevents stale mock drift or outdated client cache retention.
5. Error Handling & RBAC Protection:
   - Unauthenticated or learner users attempting revision update receive 401/403.
   - Invalid evidence status or unknown identifiers strictly return 400/404.
"""
from __future__ import annotations

import uuid
import pytest
from fastapi.testclient import TestClient

from backend.domain.canonical_urn_mapping import (
    CANONICAL_URNS,
    CANONICAL_URN_SLUGS,
    MOTIFS_PER_URN,
    TOTAL_MOTIFS,
    TOTAL_URNS,
)
from backend.domain.han_nom_review import KNOWN_MISSING_HAN_NOM_MOTIF_IDS
from backend.models import User, UserRole
from backend.security import hash_password
from backend.services import heritage_catalog


@pytest.fixture(autouse=True)
def reset_catalog_state():
    """Ensure catalog revision state is reset before and after each test."""
    heritage_catalog.reset_catalog_revisions()
    yield
    heritage_catalog.reset_catalog_revisions()


def _create_user(
    db_session,
    email: str,
    role: UserRole = UserRole.learner,
    display_name: str | None = None,
) -> User:
    """Create a test user with designated role."""
    user = User(
        email=email,
        password_hash=hash_password("Password123!"),
        display_name=display_name or f"User {email.split('@')[0]}",
        username=f"usr_{uuid.uuid4().hex[:8]}",
        role=role,
        is_profile_public=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _login(client: TestClient, email: str, password: str = "Password123!") -> dict:
    """Authenticate user and store session cookie."""
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    return res.json()


# ==============================================================================
# 1. Canonical Catalog Parity (9 Urns & 162 Motifs)
# ==============================================================================


def test_canonical_catalog_parity_9_urns_and_162_motifs(client: TestClient):
    """Verify that GET /api/v1/heritage/catalog returns the 9 canonical urns and 162 motifs."""
    res = client.get("/api/v1/heritage/catalog")
    assert res.status_code == 200
    assert "ETag" in res.headers
    assert "Cache-Control" in res.headers

    data = res.json()
    assert data["total_urns"] == TOTAL_URNS == 9
    assert data["total_motifs"] == TOTAL_MOTIFS == 162
    assert data["catalog_version"] == "v1.0"
    assert data["global_revision"] >= 1
    assert len(data["urns"]) == 9

    # Verify all 9 canonical slugs in spatial order
    returned_slugs = [u["slug"] for u in data["urns"]]
    assert tuple(returned_slugs) == CANONICAL_URN_SLUGS

    total_motifs_count = 0
    all_stable_ids = set()

    for idx, urn in enumerate(data["urns"]):
        expected_slug = CANONICAL_URN_SLUGS[idx]
        assert urn["slug"] == expected_slug
        assert urn["order"] == idx + 1
        assert urn["motif_count"] == MOTIFS_PER_URN == 18
        assert urn["name_vi"] == CANONICAL_URNS[expected_slug].name_vi
        assert urn["name_en"] == CANONICAL_URNS[expected_slug].name_en
        assert urn["name_han_nom"] == CANONICAL_URNS[expected_slug].name_han_nom
        assert urn["reign_title"] == CANONICAL_URNS[expected_slug].reign_title
        assert urn["temple_name"] == CANONICAL_URNS[expected_slug].temple_name
        assert urn["evidence_status"] == "verified"
        assert len(urn["motifs"]) == 18

        # Verify motifs on this urn
        for m_idx, motif in enumerate(urn["motifs"]):
            assert motif["order"] == m_idx + 1
            assert motif["urn_slug"] == expected_slug
            assert motif["slug"].startswith(f"{expected_slug}-")
            assert motif["id"].startswith(f"urn_{expected_slug.replace('-', '_')}_")
            assert motif["name_vi"]
            assert motif["mesh_name"]
            assert motif["pos_x"] is not None
            assert motif["pos_y"] is not None
            assert motif["pos_z"] is not None
            assert motif["bounding_radius"] > 0
            all_stable_ids.add(motif["id"])
            total_motifs_count += 1

    assert total_motifs_count == 162
    assert len(all_stable_ids) == 162


def test_canonical_catalog_filter_by_urn_slug(client: TestClient):
    """Filter catalog by single urn slug."""
    res = client.get("/api/v1/heritage/catalog?urn_slug=cao-dinh")
    assert res.status_code == 200
    data = res.json()
    assert data["total_urns"] == 1
    assert data["total_motifs"] == 18
    assert data["urns"][0]["slug"] == "cao-dinh"
    assert len(data["urns"][0]["motifs"]) == 18


# ==============================================================================
# 2. Evidence Status Labels Matching Web Platform
# ==============================================================================


def test_evidence_status_labels_and_unreviewed_motif_tracking(client: TestClient):
    """Verify evidence status labels and ensure the 4 unconfirmed motifs default to needs_review."""
    res = client.get("/api/v1/heritage/catalog")
    assert res.status_code == 200
    data = res.json()

    for urn in data["urns"]:
        for motif in urn["motifs"]:
            motif_id = motif["id"]
            if motif_id in KNOWN_MISSING_HAN_NOM_MOTIF_IDS:
                assert motif["evidence_status"] == "needs_review", (
                    f"Known incomplete motif {motif_id} must have status needs_review, got {motif['evidence_status']}"
                )
            else:
                assert motif["evidence_status"] == "verified", (
                    f"Canonical motif {motif_id} should default to verified, got {motif['evidence_status']}"
                )


# ==============================================================================
# 3. ETag / HTTP Conditional Caching (304 Not Modified)
# ==============================================================================


def test_catalog_etag_caching_and_304_not_modified(client: TestClient):
    """Verify If-None-Match conditional caching returning 304 for matching ETag."""
    # 1. Initial request -> 200 OK with ETag
    res1 = client.get("/api/v1/heritage/catalog")
    assert res1.status_code == 200
    etag1 = res1.headers.get("ETag")
    assert etag1 is not None

    # 2. Conditional request with matching ETag -> 304 Not Modified with empty body
    res2 = client.get("/api/v1/heritage/catalog", headers={"If-None-Match": etag1})
    assert res2.status_code == 304
    assert res2.text == ""
    assert res2.headers.get("ETag") == etag1

    # 3. Conditional request with mismatched ETag -> 200 OK with full body
    res3 = client.get("/api/v1/heritage/catalog", headers={"If-None-Match": '"different-etag"'})
    assert res3.status_code == 200
    assert len(res3.json()["urns"]) == 9


def test_single_urn_and_motif_endpoints_with_etag(client: TestClient):
    """Verify single urn and single motif endpoints support ETag caching."""
    # Single Urn
    res_urn = client.get("/api/v1/heritage/catalog/cao-dinh")
    assert res_urn.status_code == 200
    urn_etag = res_urn.headers.get("ETag")
    assert urn_etag is not None
    assert res_urn.json()["slug"] == "cao-dinh"
    assert len(res_urn.json()["motifs"]) == 18

    # Conditional GET single Urn
    res_urn_cached = client.get("/api/v1/heritage/catalog/cao-dinh", headers={"If-None-Match": urn_etag})
    assert res_urn_cached.status_code == 304

    # Single Motif
    res_motif = client.get("/api/v1/heritage/catalog/motifs/urn_cao_dinh_01")
    assert res_motif.status_code == 200
    motif_etag = res_motif.headers.get("ETag")
    assert motif_etag is not None
    assert res_motif.json()["id"] == "urn_cao_dinh_01"
    assert res_motif.json()["slug"] == "cao-dinh-01"

    # Conditional GET single Motif
    res_motif_cached = client.get(
        "/api/v1/heritage/catalog/motifs/urn_cao_dinh_01",
        headers={"If-None-Match": motif_etag},
    )
    assert res_motif_cached.status_code == 304


# ==============================================================================
# 4. Negative Abuse Test: Updated Approved Revision Anti-Drift
# ==============================================================================


def test_negative_abuse_updated_approved_revision_appears_on_refresh_without_stale_drift(
    client: TestClient, db_session
):
    """Negative abuse test: Client holding cached ETag MUST receive 200 with updated revision on refresh.

    When the server approves an updated revision (e.g. promoting urn_nghi_dinh_03 from needs_review
    to verified or updating revision content), the ETag strictly changes, invalidating the old client
    cache and delivering the approved revision immediately without stale mock drift.
    """
    staff_user = _create_user(db_session, "staff-t053@histolab.icu", role=UserRole.teacher)
    _login(client, staff_user.email)

    # 1. Client fetches initial catalog state
    res_initial = client.get("/api/v1/heritage/catalog")
    assert res_initial.status_code == 200
    initial_etag = res_initial.headers["ETag"]
    initial_data = res_initial.json()
    assert initial_data["global_revision"] == 1

    # Verify initial state of unreviewed motif
    nghi_dinh_urn = next(u for u in initial_data["urns"] if u["slug"] == "nghi-dinh")
    motif_03_before = next(m for m in nghi_dinh_urn["motifs"] if m["id"] == "urn_nghi_dinh_03")
    assert motif_03_before["evidence_status"] == "needs_review"
    assert motif_03_before["revision"] == 1

    # 2. Client verifies cache works before update (304)
    res_cached = client.get("/api/v1/heritage/catalog", headers={"If-None-Match": initial_etag})
    assert res_cached.status_code == 304

    # 3. Server updates approved revision for urn_nghi_dinh_03
    update_res = client.post(
        "/api/v1/heritage/catalog/revision",
        json={
            "identifier": "urn_nghi_dinh_03",
            "revision": 2,
            "evidence_status": "verified",
            "name_vi": "Khẩu Xà (Đã giám định)",
            "reviewer_notes": "Expert epigrapher verified glyph from Khâm Định Đại Nam Hội Điển Sự Lệ",
        },
    )
    assert update_res.status_code == 200
    assert update_res.json()["global_revision"] == 2

    # 4. Client refreshes sending OLD cached ETag (If-None-Match)
    # Must NOT return 304 and must NOT return stale mock data!
    res_refresh = client.get("/api/v1/heritage/catalog", headers={"If-None-Match": initial_etag})
    assert res_refresh.status_code == 200, (
        f"Server must return 200 on refresh after revision update, got {res_refresh.status_code}"
    )

    new_etag = res_refresh.headers["ETag"]
    assert new_etag != initial_etag, "ETag must change after revision update"

    refreshed_data = res_refresh.json()
    assert refreshed_data["global_revision"] == 2

    # Verify updated approved revision appears immediately
    nghi_dinh_refreshed = next(u for u in refreshed_data["urns"] if u["slug"] == "nghi-dinh")
    motif_03_after = next(m for m in nghi_dinh_refreshed["motifs"] if m["id"] == "urn_nghi_dinh_03")
    assert motif_03_after["evidence_status"] == "verified"
    assert motif_03_after["revision"] == 2
    assert motif_03_after["name_vi"] == "Khẩu Xà (Đã giám định)"


# ==============================================================================
# 5. Error Handling & RBAC Access Control
# ==============================================================================


def test_unknown_urn_and_motif_return_404(client: TestClient):
    """Verify 404 is returned for non-existent urn or motif identifiers."""
    res1 = client.get("/api/v1/heritage/catalog/invalid-urn-slug")
    assert res1.status_code == 404

    res2 = client.get("/api/v1/heritage/catalog/motifs/invalid_motif_id")
    assert res2.status_code == 404


def test_revision_update_rbac_forbidden_for_learners(client: TestClient, db_session):
    """Learners or unauthenticated users cannot update catalog revisions."""
    # 1. Unauthenticated request
    res1 = client.post(
        "/api/v1/heritage/catalog/revision",
        json={"identifier": "cao-dinh", "revision": 2},
    )
    assert res1.status_code in (401, 403)

    # 2. Learner user request
    learner = _create_user(db_session, "learner-t053@histolab.icu", role=UserRole.learner)
    _login(client, learner.email)

    res2 = client.post(
        "/api/v1/heritage/catalog/revision",
        json={"identifier": "cao-dinh", "revision": 2},
    )
    assert res2.status_code == 403


def test_revision_update_invalid_status_rejected_400(client: TestClient, db_session):
    """Updating with invalid evidence status is strictly rejected."""
    staff = _create_user(db_session, "staff-val-t053@histolab.icu", role=UserRole.teacher)
    _login(client, staff.email)

    res = client.post(
        "/api/v1/heritage/catalog/revision",
        json={
            "identifier": "cao-dinh",
            "evidence_status": "unapproved_fabricated_status",
        },
    )
    assert res.status_code in (400, 422)


def test_legacy_aliases_resolve_cleanly_in_catalog_endpoints(client: TestClient):
    """Verify legacy aliases and slugs resolve correctly in catalog sub-endpoints."""
    # Underscored slug
    res1 = client.get("/api/v1/heritage/catalog/cao_dinh")
    assert res1.status_code == 200
    assert res1.json()["slug"] == "cao-dinh"

    # Vietnamese name alias
    res2 = client.get("/api/v1/heritage/catalog/Cao%20%C4%90%E1%BB%88nh")
    assert res2.status_code == 200
    assert res2.json()["slug"] == "cao-dinh"

    # Motif by canonical relief slug
    res3 = client.get("/api/v1/heritage/catalog/motifs/cao-dinh-01")
    assert res3.status_code == 200
    assert res3.json()["id"] == "urn_cao_dinh_01"


def test_urn_revision_update_invalidates_catalog_etag(client: TestClient, db_session):
    """Updating urn revision invalidates global catalog ETag."""
    admin = _create_user(db_session, "admin-rev-t053@histolab.icu", role=UserRole.admin)
    _login(client, admin.email)

    res_init = client.get("/api/v1/heritage/catalog")
    etag_init = res_init.headers["ETag"]

    # Update urn revision
    res_up = client.post(
        "/api/v1/heritage/catalog/revision",
        json={
            "identifier": "nhan-dinh",
            "revision": 3,
            "evidence_status": "verified",
        },
    )
    assert res_up.status_code == 200

    # Catalog ETag must have changed
    res_after = client.get("/api/v1/heritage/catalog")
    assert res_after.headers["ETag"] != etag_init
    nhan_dinh = next(u for u in res_after.json()["urns"] if u["slug"] == "nhan-dinh")
    assert nhan_dinh["revision"] == 3


def test_mobile_catalog_contract_schema_compatibility(client: TestClient):
    """Verify that catalog response exactly satisfies mobile Urn and ExploreMotif requirements."""
    res = client.get("/api/v1/heritage/catalog")
    assert res.status_code == 200
    data = res.json()

    for urn in data["urns"]:
        # Mobile Urn required fields
        assert "id" in urn
        assert "slug" in urn
        assert "name_vi" in urn
        assert "order" in urn
        assert "motif_count" in urn
        assert "evidence_status" in urn
        assert "revision" in urn
        assert "motifs" in urn

        for motif in urn["motifs"]:
            # Mobile ExploreMotif required fields
            assert "id" in motif
            assert "slug" in motif
            assert "urn_slug" in motif
            assert "order" in motif
            assert "name_vi" in motif
            assert "evidence_status" in motif
            assert "revision" in motif
            assert "pos_x" in motif
            assert "pos_y" in motif
            assert "pos_z" in motif
            assert "mesh_name" in motif

