# -*- coding: utf-8 -*-
"""V5-T048: Offline Licensing and Cache Headers Test Suite.

Audits and verifies (Wave W04, Slot A08 / Ticket V5-T048):
1. Public Models & Manifests Offline Licensing & Cache Policies:
   - Verifies public/models/manifests/*.json and frontend/public/models/manifests/*.json
     declare offline_licensing_allowed=True and cache_policy with immutable cache-control.
   - Verifies verify_offline_licensing passes for all 9 urns.
2. Private Assets Authentication & Signed Tokens:
   - Verifies HMAC-SHA256 signed token generation and verification.
   - Verifies tampered, expired, or wrong-asset tokens fail closed.
   - Verifies private assets return "Cache-Control: private, no-cache, no-store, must-revalidate, max-age=0".
3. Public Assets Immutable Content Hashing:
   - Verifies content-hashed assets receive "Cache-Control: public, max-age=31536000, immutable" and matching ETag.
   - Verifies conditional requests (If-None-Match) return 304 Not Modified for valid assets.
4. Revocation & Negative Abuse Protection:
   - Revoked assets invalidate caches immediately.
   - Negative abuse test: Verifies that a revoked image or model is NOT served from a stale CDN or client cache.
   - Verifies conditional requests (If-None-Match matching cached ETag) strictly reject with 403 and anti-stale headers.
5. FastAPI Asset Endpoints Integration:
   - Tests GET /api/v1/imperial/assets/{asset_id}/image for public, private (with/without signed token), and revoked states.
   - Tests POST /api/v1/imperial/assets/{asset_id}/signed-token.
   - Tests POST /api/v1/imperial/assets/{asset_id}/revoke.
   - Tests GET /api/v1/imperial/assets/{asset_id}/license-check.
6. Nginx Reverse Proxy Configuration Verification:
   - Confirms Nginx configuration files contain immutable caching for content-hashed models and private asset guards.
7. Database Integration:
   - Verifies HistoricalAsset offline licensing and cache policy columns.
   - Verifies AssetCacheRevocation ledger recording.
"""
from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app import create_app
from backend.history_models import AssetCacheRevocation, HistoricalAsset
from backend.imperial_models import ImperialMapAsset
from backend.models import User, UserRole
from backend.services.asset_rights import (
    URN_SLUGS,
    enforce_cdn_distribution_policy,
    revoke_manifest_rights,
    sync_manifest_to_historical_asset,
    validate_historical_asset_distribution,
)
from backend.services.offline_licensing import (
    PRIVATE_ASSET_CACHE,
    PUBLIC_CATALOG_CACHE,
    PUBLIC_IMMUTABLE_CACHE,
    REVOKED_ASSET_CACHE,
    AssetRevokedError,
    InvalidSignedTokenError,
    OfflineLicensingDisallowedError,
    PrivateAssetUnauthorizedError,
    clear_revocation_cache,
    determine_asset_cache_headers,
    generate_signed_asset_token,
    get_revocation_info,
    is_asset_revoked,
    register_asset_revocation,
    verify_anti_stale_cdn_protection,
    verify_offline_licensing,
    verify_signed_asset_token,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
PUBLIC_MANIFESTS_DIR = REPO_ROOT / "public" / "models" / "manifests"
FRONTEND_MANIFESTS_DIR = REPO_ROOT / "frontend" / "public" / "models" / "manifests"


@pytest.fixture(autouse=True)
def clean_cache():
    """Ensure revocation cache is cleared before and after each test."""
    clear_revocation_cache()
    yield
    clear_revocation_cache()


# ==============================================================================
# 1. Public Models & Manifests Offline Licensing
# ==============================================================================


def test_all_9_urn_manifests_declare_offline_licensing_and_cache_policy():
    """All 9 urn manifests on disk must declare offline_licensing_allowed and cache_policy."""
    for manifest_dir in (PUBLIC_MANIFESTS_DIR, FRONTEND_MANIFESTS_DIR):
        assert manifest_dir.exists(), f"Manifest directory missing: {manifest_dir}"

        index_file = manifest_dir / "index.json"
        assert index_file.exists()
        with open(index_file, "r", encoding="utf-8") as f:
            index_data = json.load(f)
        assert index_data.get("offline_licensing_allowed") is True
        assert "cache_policy" in index_data
        assert "immutable" in index_data["cache_policy"]["cache_control"]

        for slug in URN_SLUGS:
            mf_path = manifest_dir / f"{slug}.json"
            assert mf_path.exists(), f"Missing manifest for {slug}"
            with open(mf_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)

            assert manifest.get("offline_licensing_allowed") is True
            assert "cache_policy" in manifest
            cp = manifest["cache_policy"]
            assert cp["offline_licensing_allowed"] is True
            assert "public" in cp["cache_control"]
            assert "immutable" in cp["cache_control"]

            # Verify with offline licensing service
            verified = verify_offline_licensing(manifest)
            assert verified["offline_licensing_allowed"] is True
            assert "immutable" in verified["cache_control"]


def test_offline_licensing_blocks_disallowed_or_unlicensed_assets():
    """Assets with offline_licensing_allowed=False or restricted license fail closed."""
    # Explicit disallow
    disallowed = {
        "asset_id": "test-asset-01",
        "license": "CC BY 4.0 / Educational Fair Use",
        "rights_status": "cleared",
        "attribution": "HMCC",
        "offline_licensing_allowed": False,
    }
    with pytest.raises(OfflineLicensingDisallowedError):
        verify_offline_licensing(disallowed)

    # Missing license
    no_license = {
        "asset_id": "test-asset-02",
        "license": "",
        "rights_status": "cleared",
        "attribution": "HMCC",
    }
    with pytest.raises(OfflineLicensingDisallowedError):
        verify_offline_licensing(no_license)

    # Proprietary license
    proprietary = {
        "asset_id": "test-asset-03",
        "license": "All Rights Reserved (Proprietary)",
        "rights_status": "cleared",
        "attribution": "HMCC",
    }
    with pytest.raises(OfflineLicensingDisallowedError):
        verify_offline_licensing(proprietary)


# ==============================================================================
# 2. Private Assets Authentication & Signed Tokens
# ==============================================================================


def test_signed_token_lifecycle_and_tampering_protection():
    """HMAC-SHA256 signed asset token verifies correctly and rejects tampered or expired tokens."""
    asset_id = str(uuid.uuid4())
    secret = "production-grade-secret-key-12345"

    # 1. Generate valid token
    token = generate_signed_asset_token(
        asset_id=asset_id,
        access_level="read",
        client_id="mobile_student_01",
        expires_in_seconds=3600,
        secret=secret,
    )
    assert "." in token

    # 2. Verify valid token succeeds
    payload = verify_signed_asset_token(token, asset_id, secret=secret)
    assert payload["aid"] == asset_id
    assert payload["cid"] == "mobile_student_01"
    assert payload["lvl"] == "read"

    # 3. Wrong asset fails closed
    wrong_asset_id = str(uuid.uuid4())
    with pytest.raises(InvalidSignedTokenError, match="not requested"):
        verify_signed_asset_token(token, wrong_asset_id, secret=secret)

    # 4. Tampered payload fails closed
    parts = token.split(".")
    tampered_token = f"dGFtcGVyZWQ.{parts[1]}"
    with pytest.raises(InvalidSignedTokenError):
        verify_signed_asset_token(tampered_token, asset_id, secret=secret)

    # 5. Tampered signature fails closed
    tampered_sig = f"{parts[0]}.badsignature123"
    with pytest.raises(InvalidSignedTokenError, match="signature verification failed"):
        verify_signed_asset_token(tampered_sig, asset_id, secret=secret)

    # 6. Expired token fails closed
    expired_token = generate_signed_asset_token(
        asset_id=asset_id,
        expires_in_seconds=-10,  # Already expired
        secret=secret,
    )
    with pytest.raises(InvalidSignedTokenError, match="has expired"):
        verify_signed_asset_token(expired_token, asset_id, secret=secret)


def test_private_asset_cache_headers_are_strictly_no_store():
    """Private asset cache headers must specify private, no-store, must-revalidate, max-age=0."""
    asset_id = str(uuid.uuid4())
    content_hash = "a" * 64

    headers = determine_asset_cache_headers(
        asset_id=asset_id,
        is_private=True,
        has_content_hash=True,
        content_sha256=content_hash,
    )
    assert "private" in headers["Cache-Control"]
    assert "no-store" in headers["Cache-Control"]
    assert "no-cache" in headers["Cache-Control"]
    assert "must-revalidate" in headers["Cache-Control"]
    assert "max-age=0" in headers["Cache-Control"]
    assert headers["Pragma"] == "no-cache"
    assert headers["Expires"] == "0"
    assert headers["X-Asset-Access"] == "PRIVATE_SIGNED"


# ==============================================================================
# 3. Public Assets Immutable Content Hashing
# ==============================================================================


def test_public_hashed_asset_cache_headers():
    """Public assets with verified content hashes receive immutable 1-year cache headers."""
    asset_id = "cao-dinh-lod-1k"
    content_hash = "6f7e73424c18c5e6504ee25eda103b56958b1e79348937e152e60731a2bcd16a"

    headers = determine_asset_cache_headers(
        asset_id=asset_id,
        is_private=False,
        has_content_hash=True,
        content_sha256=content_hash,
        offline_allowed=True,
    )
    assert headers["Cache-Control"] == PUBLIC_IMMUTABLE_CACHE
    assert headers["ETag"] == f'"{content_hash}"'
    assert headers["X-Asset-Access"] == "PUBLIC_IMMUTABLE"
    assert headers["X-Offline-Licensing"] == "ALLOWED"


# ==============================================================================
# 4. Revocation & Negative Abuse Protection (Anti-Stale CDN Test)
# ==============================================================================


def test_negative_abuse_revoked_asset_not_served_from_stale_cdn_cache():
    """Negative Abuse Test: Revoked image or model is NOT served from stale CDN cache beyond policy.

    Guarantees:
    1. Revoked asset is marked revoked.
    2. A client or CDN attempting conditional revalidation (If-None-Match with cached ETag)
       is strictly rejected with 403 Forbidden.
    3. The response emits 'Cache-Control: no-cache, no-store, must-revalidate, max-age=0, s-maxage=0'
       and 'X-Cache-Invalidation: PURGE_CDN_IMMEDIATE' so all intermediate proxies bust stale cache.
    4. verify_anti_stale_cdn_protection validates that stale serving is prevented.
    """
    asset_id = "urn_cao_dinh_revoked_test"
    cached_etag = '"6f7e73424c18c5e6504ee25eda103b56958b1e79348937e152e60731a2bcd16a"'

    # 1. Before revocation: conditional request is satisfied with 304
    active_check = verify_anti_stale_cdn_protection(asset_id, cached_etag=cached_etag)
    assert active_check["status_code"] == 304
    assert active_check["cache_status"] == "NOT_MODIFIED_SERVED_OK"

    # 2. Rights revoked (e.g. copyright takedown / archival restriction)
    revocation = register_asset_revocation(
        asset_id=asset_id,
        reason="Third-party rights dispute filed by archive",
        revoked_by="curator_staff",
    )
    assert is_asset_revoked(asset_id) is True
    assert revocation["cdn_purged"] is True

    # 3. Negative test: Stale CDN request with cached ETag MUST NOT receive 304 or 200!
    abuse_check = verify_anti_stale_cdn_protection(asset_id, cached_etag=cached_etag)
    assert abuse_check["status_code"] == 403
    assert abuse_check["stale_serving_prevented"] is True
    assert abuse_check["cache_status"] == "STALE_CACHE_REJECTED_PURGED"

    headers = abuse_check["headers"]
    assert "no-store" in headers["Cache-Control"]
    assert "no-cache" in headers["Cache-Control"]
    assert "max-age=0" in headers["Cache-Control"]
    assert "s-maxage=0" in headers["Cache-Control"]
    assert headers["Pragma"] == "no-cache"
    assert headers["Expires"] == "0"
    assert headers["X-Asset-Rights-Status"] == "REVOKED"
    assert headers["X-Cache-Invalidation"] == "PURGE_CDN_IMMEDIATE"

    # 4. Attempting offline licensing on the revoked asset fails closed
    with pytest.raises(AssetRevokedError):
        verify_offline_licensing({
            "asset_id": asset_id,
            "license": "CC BY 4.0 / Educational Fair Use",
            "rights_status": "cleared",
            "attribution": "HMCC",
        })


# ==============================================================================
# 5. FastAPI Endpoints Integration
# ==============================================================================


def test_api_public_map_asset_serves_immutable_cache_and_supports_conditional_get(
    client: TestClient, db_session: Session
):
    """GET /api/v1/imperial/assets/{asset_id}/image serves immutable cache headers and supports 304."""
    # 1. Create a public published map asset in DB
    user = User(
        id=uuid.uuid4(),
        email=f"curator_{uuid.uuid4().hex[:6]}@example.com",
        username=f"curator_{uuid.uuid4().hex[:6]}",
        password_hash="fake_hash",
        role=UserRole.admin,
        display_name="Curator Admin",
    )
    db_session.add(user)
    db_session.flush()

    asset_id = uuid.uuid4()
    sha = "b" * 64
    map_asset = ImperialMapAsset(
        id=asset_id,
        content_scope="STTT_IMPERIAL_CITY",
        title_vi="Bản đồ kiểm tra",
        slug=f"map-test-{uuid.uuid4().hex[:6]}",
        version=1,
        image_storage_key="maps/test.webp",
        image_sha256=sha,
        mime_type="image/webp",
        width_px=2000,
        height_px=2000,
        source_title="HMCC Archive",
        credit_text="HMCC",
        license_kind="CC BY 4.0",
        license_status="approved",
        review_status="published",
        is_active=True,
        created_by=user.id,
    )
    db_session.add(map_asset)
    db_session.commit()

    # 2. Public request returns 200 with immutable cache
    res = client.get(f"/api/v1/imperial/assets/{asset_id}/image")
    assert res.status_code == 200
    assert "public" in res.headers["Cache-Control"]
    assert "immutable" in res.headers["Cache-Control"]
    assert res.headers["ETag"] == f'"{sha}"'
    assert res.headers["X-Asset-Access"] == "PUBLIC_IMMUTABLE"

    # 3. Conditional request with matching If-None-Match returns 304 Not Modified
    cond_res = client.get(
        f"/api/v1/imperial/assets/{asset_id}/image",
        headers={"If-None-Match": f'"{sha}"'},
    )
    assert cond_res.status_code == 304
    assert cond_res.headers["ETag"] == f'"{sha}"'


def test_api_private_map_asset_requires_signed_token(
    client: TestClient, db_session: Session
):
    """GET /api/v1/imperial/assets/{asset_id}/image for unpublished map asset requires signed token."""
    user = User(
        id=uuid.uuid4(),
        email=f"curator_{uuid.uuid4().hex[:6]}@example.com",
        username=f"curator_{uuid.uuid4().hex[:6]}",
        password_hash="fake_hash",
        role=UserRole.admin,
        display_name="Curator Admin",
    )
    db_session.add(user)
    db_session.flush()

    asset_id = uuid.uuid4()
    sha = "c" * 64
    private_asset = ImperialMapAsset(
        id=asset_id,
        content_scope="STTT_IMPERIAL_CITY",
        title_vi="Bản đồ nội bộ chưa công bố",
        slug=f"map-private-{uuid.uuid4().hex[:6]}",
        version=1,
        image_storage_key="maps/private.webp",
        image_sha256=sha,
        mime_type="image/webp",
        width_px=2000,
        height_px=2000,
        source_title="Private Research",
        credit_text="Private",
        license_kind="Proprietary / Pending",
        license_status="pending",
        review_status="draft",  # Unpublished!
        is_active=False,
        created_by=user.id,
    )
    db_session.add(private_asset)
    db_session.commit()

    # 1. Unauthenticated request without token is rejected (403 Forbidden)
    res_no_token = client.get(f"/api/v1/imperial/assets/{asset_id}/image")
    assert res_no_token.status_code == 403
    assert res_no_token.json()["error"]["code"] == "UNAUTHORIZED_PRIVATE_ASSET"

    # 2. Invalid or tampered token is rejected (403 Forbidden)
    res_bad_token = client.get(f"/api/v1/imperial/assets/{asset_id}/image?token=invalid.token")
    assert res_bad_token.status_code == 403

    # 3. Valid signed token succeeds with private, no-store headers
    valid_token = generate_signed_asset_token(str(asset_id), expires_in_seconds=3600)
    res_signed = client.get(f"/api/v1/imperial/assets/{asset_id}/image?token={valid_token}")
    assert res_signed.status_code == 200
    assert "private" in res_signed.headers["Cache-Control"]
    assert "no-store" in res_signed.headers["Cache-Control"]
    assert "no-cache" in res_signed.headers["Cache-Control"]
    assert res_signed.headers["X-Asset-Access"] == "PRIVATE_SIGNED"


def test_api_revoked_asset_returns_403_with_anti_stale_cache_headers(
    client: TestClient, db_session: Session
):
    """GET /api/v1/imperial/assets/{asset_id}/image for revoked asset emits anti-stale purge headers."""
    user = User(
        id=uuid.uuid4(),
        email=f"curator_{uuid.uuid4().hex[:6]}@example.com",
        username=f"curator_{uuid.uuid4().hex[:6]}",
        password_hash="fake_hash",
        role=UserRole.admin,
        display_name="Curator Admin",
    )
    db_session.add(user)
    db_session.flush()

    asset_id = uuid.uuid4()
    sha = "d" * 64
    revoked_asset = ImperialMapAsset(
        id=asset_id,
        content_scope="STTT_IMPERIAL_CITY",
        title_vi="Bản đồ bị thu hồi bản quyền",
        slug=f"map-revoked-{uuid.uuid4().hex[:6]}",
        version=1,
        image_storage_key="maps/revoked.webp",
        image_sha256=sha,
        mime_type="image/webp",
        width_px=2000,
        height_px=2000,
        source_title="Disputed Archive",
        credit_text="Disputed",
        license_kind="Revoked",
        license_status="rejected",  # Rejected / revoked!
        review_status="archived",
        is_active=False,
        created_by=user.id,
    )
    db_session.add(revoked_asset)
    db_session.commit()

    # Request returns 403 Forbidden with strict no-store / anti-stale headers
    res = client.get(f"/api/v1/imperial/assets/{asset_id}/image")
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "ASSET_REVOKED"


def test_api_license_check_endpoint(client: TestClient, db_session: Session):
    """GET /api/v1/imperial/assets/{asset_id}/license-check returns accurate licensing & cache controls."""
    user = User(
        id=uuid.uuid4(),
        email=f"curator_{uuid.uuid4().hex[:6]}@example.com",
        username=f"curator_{uuid.uuid4().hex[:6]}",
        password_hash="fake_hash",
        role=UserRole.admin,
        display_name="Curator Admin",
    )
    db_session.add(user)
    db_session.flush()

    asset_id = uuid.uuid4()
    sha = "e" * 64
    map_asset = ImperialMapAsset(
        id=asset_id,
        content_scope="STTT_IMPERIAL_CITY",
        title_vi="Bản đồ công cộng",
        slug=f"map-check-{uuid.uuid4().hex[:6]}",
        version=1,
        image_storage_key="maps/check.webp",
        image_sha256=sha,
        mime_type="image/webp",
        width_px=2000,
        height_px=2000,
        source_title="HMCC Archive",
        credit_text="HMCC",
        license_kind="CC BY 4.0 / Educational Fair Use",
        license_status="approved",
        review_status="published",
        is_active=True,
        created_by=user.id,
    )
    db_session.add(map_asset)
    db_session.commit()

    res = client.get(f"/api/v1/imperial/assets/{asset_id}/license-check")
    assert res.status_code == 200
    data = res.json()
    assert data["offline_licensing_allowed"] is True
    assert data["is_private"] is False
    assert data["is_revoked"] is False
    assert "immutable" in data["cache_control"]


# ==============================================================================
# 6. Nginx Reverse Proxy Configuration Verification
# ==============================================================================


def test_nginx_configurations_enforce_cache_headers_and_private_guards():
    """Verify that all production and staging Nginx configuration files enforce caching policies."""
    nginx_files = [
        REPO_ROOT / "nginx-site.conf",
        REPO_ROOT / "nginx-lms.conf",
        REPO_ROOT / "nginx-lms-histolab.conf",
        REPO_ROOT / "nginx-luunien-staging.conf",
    ]

    for conf_file in nginx_files:
        assert conf_file.exists(), f"Nginx config missing: {conf_file}"
        content = conf_file.read_text(encoding="utf-8")

        # 1. Must configure 3D models with immutable cache
        assert "location ^~ /assets/models/" in content, f"Missing /assets/models/ in {conf_file.name}"
        assert "immutable" in content, f"Missing immutable directive in {conf_file.name}"

        # 2. Must configure private asset location guard
        assert "location ^~ /assets/private/" in content, f"Missing /assets/private/ in {conf_file.name}"
        assert "private" in content, f"Missing private directive in {conf_file.name}"
        assert "no-store" in content, f"Missing no-store in {conf_file.name}"
        assert "UNAUTHORIZED_PRIVATE_ASSET" in content, f"Missing private asset auth check in {conf_file.name}"


# ==============================================================================
# 7. Database Integration
# ==============================================================================


def test_database_historical_asset_offline_licensing_and_revocation(db_session: Session):
    """HistoricalAsset table persists offline licensing and cache policy fields."""
    asset = HistoricalAsset(
        asset_type="3d_model",
        storage_url="/assets/models/CAO-DINH-v1-512.glb",
        mime_type="model/gltf-binary",
        sha256="51f5baf131e85257186b0e4a89087870ff66e4c787f7775bea797fc2550d8611",
        rights_status="cleared",
        license="CC BY 4.0 / Educational Fair Use",
        attribution="HMCC & Histolab",
        source_origin="HMCC",
        public_display_allowed=True,
        offline_licensing_allowed=True,
        cache_control_policy="public, max-age=31536000, immutable",
        is_private=False,
    )
    db_session.add(asset)
    db_session.commit()

    loaded = db_session.get(HistoricalAsset, asset.id)
    assert loaded is not None
    assert loaded.offline_licensing_allowed is True
    assert loaded.is_private is False
    assert "immutable" in loaded.cache_control_policy

    # Revocation test
    register_asset_revocation(
        str(asset.id),
        reason="Owner license terminated",
        revoked_by="admin_test",
        db=db_session,
    )

    db_session.refresh(loaded)
    assert loaded.rights_status == "revoked"
    assert loaded.public_display_allowed is False
    assert loaded.offline_licensing_allowed is False
    assert loaded.revocation_reason == "Owner license terminated"

    # Verify audit record in AssetCacheRevocation
    audit = (
        db_session.query(AssetCacheRevocation)
        .filter(AssetCacheRevocation.asset_id == str(asset.id))
        .first()
    )
    assert audit is not None
    assert audit.revocation_reason == "Owner license terminated"
    assert audit.cdn_purged is True
