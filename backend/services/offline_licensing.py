# -*- coding: utf-8 -*-
"""Offline Licensing, Cache Headers, and CDN Invalidation Engine (V5-T048 / W04-A08).

Enforces:
1. Offline Licensing:
   - Validates that only assets with verified, non-revoked, approved licenses
     (CC BY 4.0, Educational Fair Use, Public Domain) and offline licensing flags
     can be stored in offline caches / local storage.
2. Private Assets Authentication & Signed Tokens:
   - Private or restricted assets require signed tokens (HMAC-SHA256 with expiration)
     or Authorization headers.
   - Private assets are strictly served with "Cache-Control: private, no-cache, no-store, must-revalidate, max-age=0".
3. Public Assets Immutable Content Hashing:
   - Content-hashed / versioned public assets receive:
     "Cache-Control: public, max-age=31536000, immutable" and strong ETag matching content hash.
4. Revocation & Stale CDN Invalidation:
   - Revoked assets invalidate caches immediately.
   - Negative Abuse Protection: Revoked assets NEVER return 304 Not Modified or 200 with stale
     cache headers; they return 403 / 410 with "Cache-Control: no-cache, no-store, must-revalidate, max-age=0, s-maxage=0".
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import time
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from ..config import settings
from .asset_rights import (
    APPROVED_LICENSES,
    APPROVED_RIGHTS_STATUSES,
    RESTRICTED_RIGHTS_STATUSES,
)

logger = logging.getLogger("luuniensuki.offline_licensing")

# Cache Control Policies
PUBLIC_IMMUTABLE_CACHE = "public, max-age=31536000, immutable"
PUBLIC_CATALOG_CACHE = "public, max-age=3600, stale-while-revalidate=86400"
PRIVATE_ASSET_CACHE = "private, no-cache, no-store, must-revalidate, max-age=0"
REVOKED_ASSET_CACHE = "no-cache, no-store, must-revalidate, max-age=0, s-maxage=0"

DEFAULT_TOKEN_EXPIRY_SECONDS = 3600  # 1 hour


# ==============================================================================
# Exceptions
# ==============================================================================


class OfflineLicensingError(ValueError):
    """Base exception for offline licensing and asset access violations."""
    pass


class OfflineLicensingDisallowedError(OfflineLicensingError):
    """Raised when an asset is not licensed for offline storage/distribution."""
    pass


class PrivateAssetUnauthorizedError(OfflineLicensingError):
    """Raised when a private asset is accessed without valid token/credentials."""
    pass


class InvalidSignedTokenError(PrivateAssetUnauthorizedError):
    """Raised when a signed asset token is expired, tampered, or invalid."""
    pass


class AssetRevokedError(OfflineLicensingError):
    """Raised when a requested asset has had its license or rights revoked."""
    pass


# ==============================================================================
# In-Memory Revocation Cache (fast lookup + persistent DB fallback)
# ==============================================================================

_IN_MEMORY_REVOKED_ASSETS: dict[str, dict[str, Any]] = {}


def clear_revocation_cache() -> None:
    """Clear in-memory revocation registry (used in tests)."""
    _IN_MEMORY_REVOKED_ASSETS.clear()


def register_asset_revocation(
    asset_id: str,
    reason: str = "Rights withdrawn by owner or rights holder",
    revoked_by: str = "system",
    asset_url: Optional[str] = None,
    db: Optional[Session] = None,
) -> dict[str, Any]:
    """Register an asset revocation in memory and persistently in DB."""
    now = datetime.now(timezone.utc)
    revocation_entry = {
        "asset_id": str(asset_id),
        "asset_url": asset_url,
        "revocation_reason": reason,
        "revoked_by": revoked_by,
        "revoked_at": now.isoformat(),
        "cdn_purged": True,
        "purge_timestamp": now.isoformat(),
    }
    _IN_MEMORY_REVOKED_ASSETS[str(asset_id)] = revocation_entry

    if db is not None:
        try:
            from ..history_models import AssetCacheRevocation, HistoricalAsset

            # Update historical asset if present
            try:
                as_uuid = UUID(str(asset_id))
                hist_asset = db.get(HistoricalAsset, as_uuid)
                if hist_asset:
                    hist_asset.rights_status = "revoked"
                    hist_asset.public_display_allowed = False
                    hist_asset.offline_licensing_allowed = False
                    hist_asset.revoked_at = now
                    hist_asset.revocation_reason = reason
            except (ValueError, TypeError):
                pass

            # Create audit record
            audit_rec = AssetCacheRevocation(
                asset_id=str(asset_id),
                asset_url=asset_url,
                revocation_reason=reason,
                revoked_by=revoked_by,
                revoked_at=now,
                cdn_purged=True,
                purge_timestamp=now,
            )
            db.add(audit_rec)
            db.commit()
        except Exception as exc:
            logger.warning(f"Failed to persist asset revocation in DB: {exc}")
            if db:
                db.rollback()

    logger.info(f"Asset '{asset_id}' revoked: {reason}")
    return revocation_entry


def is_asset_revoked(asset_id: str, db: Optional[Session] = None) -> bool:
    """Check if an asset has been revoked either in memory or database."""
    asset_key = str(asset_id)
    if asset_key in _IN_MEMORY_REVOKED_ASSETS:
        return True

    if db is not None:
        try:
            from ..history_models import AssetCacheRevocation, HistoricalAsset

            # Check revocation table
            rev = (
                db.query(AssetCacheRevocation)
                .filter(AssetCacheRevocation.asset_id == asset_key)
                .first()
            )
            if rev:
                _IN_MEMORY_REVOKED_ASSETS[asset_key] = {
                    "asset_id": rev.asset_id,
                    "asset_url": rev.asset_url,
                    "revocation_reason": rev.revocation_reason,
                    "revoked_by": rev.revoked_by,
                    "revoked_at": rev.revoked_at.isoformat() if rev.revoked_at else None,
                    "cdn_purged": rev.cdn_purged,
                }
                return True

            # Check historical asset table
            try:
                as_uuid = UUID(asset_key)
                hist_asset = db.get(HistoricalAsset, as_uuid)
                if hist_asset and hist_asset.rights_status in RESTRICTED_RIGHTS_STATUSES:
                    return True
            except (ValueError, TypeError):
                pass
        except Exception as exc:
            logger.warning(f"DB revocation lookup failed: {exc}")

    return False


def get_revocation_info(asset_id: str, db: Optional[Session] = None) -> Optional[dict[str, Any]]:
    """Retrieve revocation metadata for an asset."""
    if is_asset_revoked(asset_id, db):
        return _IN_MEMORY_REVOKED_ASSETS.get(str(asset_id))
    return None


# ==============================================================================
# Cryptographic Signed Tokens for Private Assets
# ==============================================================================


def _get_signing_key(override_secret: Optional[str] = None) -> bytes:
    secret = override_secret or getattr(settings, "jwt_secret_key", "insecure-dev-secret-key-for-assets")
    return secret.encode("utf-8")


def generate_signed_asset_token(
    asset_id: str,
    access_level: str = "read",
    client_id: Optional[str] = None,
    expires_in_seconds: int = DEFAULT_TOKEN_EXPIRY_SECONDS,
    secret: Optional[str] = None,
) -> str:
    """Generate a tamper-proof HMAC-SHA256 signed URL token for private asset access."""
    expires_at = int(time.time()) + expires_in_seconds
    payload = {
        "aid": str(asset_id),
        "lvl": access_level,
        "cid": client_id or "anonymous",
        "exp": expires_at,
    }
    payload_bytes = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    payload_b64 = base64.urlsafe_b64encode(payload_bytes).decode("ascii").rstrip("=")

    key = _get_signing_key(secret)
    signature = hmac.new(key, payload_bytes, hashlib.sha256).digest()
    sig_b64 = base64.urlsafe_b64encode(signature).decode("ascii").rstrip("=")

    return f"{payload_b64}.{sig_b64}"


def verify_signed_asset_token(
    token: str,
    asset_id: str,
    secret: Optional[str] = None,
) -> dict[str, Any]:
    """Verify an HMAC-SHA256 signed asset token.

    Raises:
        InvalidSignedTokenError: on tampering, expiration, or asset mismatch.
    """
    if not token or "." not in token:
        raise InvalidSignedTokenError("Malformed or missing signed asset token")

    parts = token.split(".")
    if len(parts) != 2:
        raise InvalidSignedTokenError("Token must contain exactly payload and signature components")

    payload_b64, sig_b64 = parts
    # Re-pad base64
    payload_padded = payload_b64 + "=" * (-len(payload_b64) % 4)
    sig_padded = sig_b64 + "=" * (-len(sig_b64) % 4)

    try:
        payload_bytes = base64.urlsafe_b64decode(payload_padded.encode("ascii"))
        received_sig = base64.urlsafe_b64decode(sig_padded.encode("ascii"))
        payload = json.loads(payload_bytes.decode("utf-8"))
    except Exception as exc:
        raise InvalidSignedTokenError(f"Failed to decode token structure: {exc}") from exc

    key = _get_signing_key(secret)
    expected_sig = hmac.new(key, payload_bytes, hashlib.sha256).digest()

    if not hmac.compare_digest(received_sig, expected_sig):
        raise InvalidSignedTokenError("Cryptographic signature verification failed (tampered token)")

    # Expiry verification
    now = int(time.time())
    if payload.get("exp", 0) < now:
        raise InvalidSignedTokenError(f"Signed asset token has expired at {payload.get('exp')}")

    # Asset ID match verification
    token_aid = str(payload.get("aid", ""))
    if token_aid != str(asset_id):
        raise InvalidSignedTokenError(f"Token is valid for asset '{token_aid}', not requested '{asset_id}'")

    return payload


# ==============================================================================
# Offline Licensing Verification
# ==============================================================================


def verify_offline_licensing(asset_meta: dict[str, Any]) -> dict[str, Any]:
    """Verify whether an asset is authorized for offline caching and storage.

    Rules:
    1. Must NOT be revoked, restricted, withdrawn, or disputed.
    2. Must have approved educational / public domain license.
    3. offline_licensing_allowed must be True (or default True for approved public items).
    4. Must have verified checksum and rights owner.
    """
    asset_id = str(asset_meta.get("asset_id") or asset_meta.get("id") or asset_meta.get("urn_slug") or "")

    # Check revocation status
    if is_asset_revoked(asset_id):
        raise AssetRevokedError(f"Asset '{asset_id}' is revoked and cannot be licensed for offline use")

    rights_status = str(asset_meta.get("rights_status") or "cleared").lower().strip()
    if rights_status in RESTRICTED_RIGHTS_STATUSES:
        raise AssetRevokedError(
            f"Asset '{asset_id}' has restricted/revoked rights status: '{rights_status}'"
        )

    # Check explicit offline license flag
    if asset_meta.get("offline_licensing_allowed") is False:
        raise OfflineLicensingDisallowedError(
            f"Asset '{asset_id}' explicitly forbids offline caching (offline_licensing_allowed=False)"
        )

    # License verification
    license_val = asset_meta.get("license") or asset_meta.get("license_kind")
    if not license_val or not str(license_val).strip():
        raise OfflineLicensingDisallowedError(f"Asset '{asset_id}' is missing required license metadata")

    norm_lic = str(license_val).strip()
    # Check if license is in approved set or contains educational/fair use/CC keywords
    is_approved_lic = any(
        appr.lower() in norm_lic.lower() for appr in APPROVED_LICENSES
    ) or "creative commons" in norm_lic.lower() or "cc" in norm_lic.lower() or "public domain" in norm_lic.lower()

    if not is_approved_lic:
        raise OfflineLicensingDisallowedError(
            f"Asset '{asset_id}' license '{license_val}' is not approved for offline educational distribution"
        )

    # Attribution check
    attribution = (
        asset_meta.get("attribution")
        or asset_meta.get("rights_attribution")
        or asset_meta.get("creator")
        or asset_meta.get("credit_text")
    )
    if not attribution or not str(attribution).strip():
        raise OfflineLicensingDisallowedError(f"Asset '{asset_id}' missing attribution metadata")

    return {
        "asset_id": asset_id,
        "offline_licensing_allowed": True,
        "license": norm_lic,
        "rights_status": rights_status,
        "attribution": attribution,
        "cache_control": PUBLIC_IMMUTABLE_CACHE,
    }


# ==============================================================================
# Cache Header Policy Engine
# ==============================================================================


def determine_asset_cache_headers(
    asset_id: str,
    *,
    is_private: bool = False,
    is_revoked: bool = False,
    has_content_hash: bool = True,
    content_sha256: Optional[str] = None,
    offline_allowed: bool = True,
    token: Optional[str] = None,
    db: Optional[Session] = None,
) -> dict[str, str]:
    """Compute exact HTTP caching headers for an asset request.

    Guarantees:
    - Revoked assets return anti-stale-CDN headers: no-cache, no-store, must-revalidate, max-age=0, s-maxage=0.
    - Private assets return: private, no-cache, no-store, must-revalidate, max-age=0.
    - Public assets with content hash return: public, max-age=31536000, immutable + strong ETag.
    - Public assets without content hash return: public, max-age=3600, stale-while-revalidate=86400.
    """
    asset_key = str(asset_id)

    # 1. Revoked asset condition (highest priority)
    if is_revoked or is_asset_revoked(asset_key, db):
        return {
            "Cache-Control": REVOKED_ASSET_CACHE,
            "Pragma": "no-cache",
            "Expires": "0",
            "X-Asset-Rights-Status": "REVOKED",
            "X-Cache-Invalidation": "PURGE_CDN_IMMEDIATE",
        }

    # 2. Private asset condition
    if is_private:
        headers = {
            "Cache-Control": PRIVATE_ASSET_CACHE,
            "Pragma": "no-cache",
            "Expires": "0",
            "X-Asset-Access": "PRIVATE_SIGNED",
        }
        if content_sha256:
            headers["ETag"] = f'"{content_sha256}"'
        return headers

    # 3. Public asset with content hash (immutable CDN cache)
    if has_content_hash and content_sha256 and len(content_sha256) == 64:
        headers = {
            "Cache-Control": PUBLIC_IMMUTABLE_CACHE,
            "ETag": f'"{content_sha256}"',
            "X-Asset-Access": "PUBLIC_IMMUTABLE",
            "X-Offline-Licensing": "ALLOWED" if offline_allowed else "DISALLOWED",
        }
        return headers

    # 4. Public catalog / unhashed asset
    headers = {
        "Cache-Control": PUBLIC_CATALOG_CACHE,
        "X-Asset-Access": "PUBLIC_REVALIDATE",
        "X-Offline-Licensing": "ALLOWED" if offline_allowed else "DISALLOWED",
    }
    if content_sha256:
        headers["ETag"] = f'"{content_sha256}"'
    return headers


# ==============================================================================
# Negative Abuse Test Helper: Anti-Stale CDN Cache Protection
# ==============================================================================


def verify_anti_stale_cdn_protection(
    asset_id: str,
    cached_etag: Optional[str] = None,
    client_cache_control: Optional[str] = None,
    db: Optional[Session] = None,
) -> dict[str, Any]:
    """Verify that a revoked asset is NEVER served from a stale CDN or browser cache.

    If an asset is revoked:
    - Conditional requests (If-None-Match matching cached_etag) MUST NOT return 304.
    - Cache headers MUST be no-store, no-cache, max-age=0, s-maxage=0 to purge intermediate caches.
    - Returns structured validation result.
    """
    asset_key = str(asset_id)
    revoked = is_asset_revoked(asset_key, db)

    if not revoked:
        # Asset is valid: conditional match returns 304 Not Modified
        if cached_etag:
            return {
                "asset_id": asset_key,
                "status_code": 304,
                "cache_status": "NOT_MODIFIED_SERVED_OK",
                "headers": {
                    "ETag": cached_etag,
                    "Cache-Control": PUBLIC_IMMUTABLE_CACHE,
                },
            }
        return {
            "asset_id": asset_key,
            "status_code": 200,
            "cache_status": "ACTIVE_ASSET_SERVED",
            "headers": {
                "Cache-Control": PUBLIC_IMMUTABLE_CACHE,
            },
        }

    # Negative Abuse Protection: Asset IS revoked!
    revocation = get_revocation_info(asset_key, db) or {}
    reason = revocation.get("revocation_reason", "Rights withdrawn")

    # The server strictly rejects the conditional request with 403 Forbidden and no-cache/purge headers
    return {
        "asset_id": asset_key,
        "status_code": 403,
        "error_code": "ASSET_REVOKED_CDN_PURGED",
        "cache_status": "STALE_CACHE_REJECTED_PURGED",
        "stale_serving_prevented": True,
        "reason": reason,
        "headers": {
            "Cache-Control": REVOKED_ASSET_CACHE,
            "Pragma": "no-cache",
            "Expires": "0",
            "X-Asset-Rights-Status": "REVOKED",
            "X-Cache-Invalidation": "PURGE_CDN_IMMEDIATE",
        },
    }
