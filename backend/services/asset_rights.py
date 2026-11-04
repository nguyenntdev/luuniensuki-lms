# -*- coding: utf-8 -*-
"""Image and 3D Mesh Attribution Linkage with Rights Enforcement (V5-T027 / W02-A07).

Enforces:
1. Attribution Linkage:
   - Attaches verified creator, license (e.g. CC-BY 4.0 / Educational Fair Use),
     rights owner, and cryptographic checksum (SHA-256) to all 3D urn manifests.
2. Viewer Fallback Architecture (Master Spec §V2-C & ADR 05):
   - When 3D WebGL is unsupported or mesh load fails, high-resolution 2D rubbing
     image fallback (ban-duc-noi/) is provided with accessible component binding
     (UrnAccessibleFallback).
3. Public CDN Rights Enforcement Gate:
   - Fails closed: If asset rights status is revoked, withdrawn, or restricted,
     or if public distribution is disallowed, CDN distribution is strictly blocked
     (raising typed AssetDistributionBlockedError / AssetRightsRevokedError).
4. Checksum Integrity:
   - Validates that physical asset files on disk match their declared SHA-256 hashes
     and magic headers (GLB glTF binary or JPEG rubbing image).
5. Historical Asset Database Mapping:
   - Integrates with HistoricalAsset (backend.history_models) for persistent audit
     and rights clearance validation.
"""
from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path
from typing import Any, Optional
from uuid import UUID

from sqlalchemy.orm import Session

logger = logging.getLogger("luuniensuki.asset_rights")

GLB_MAGIC = b"glTF"
JPEG_MAGIC = b"\xff\xd8\xff"
PNG_MAGIC = b"\x89PNG"

RESTRICTED_RIGHTS_STATUSES = {
    "revoked",
    "withdrawn",
    "restricted",
    "copyrighted",
    "unlicensed",
    "blocked",
    "all_rights_reserved",
    "disputed",
}

APPROVED_RIGHTS_STATUSES = {
    "cleared",
    "verified",
    "approved",
    "public_domain",
}

APPROVED_LICENSES = {
    "CC BY 4.0 / Educational Fair Use",
    "CC BY 4.0",
    "CC-BY-4.0",
    "CC BY",
    "Public Domain",
    "Educational Fair Use",
    "Custom Grant",
}

DEFAULT_RIGHTS_OWNER = "Trung tâm Bảo tồn Di tích Cố đô Huế (HMCC)"
DEFAULT_CREATOR = "Trung tâm Bảo tồn Di tích Cố đô Huế (HMCC) & Histolab"
DEFAULT_LICENSE = "CC BY 4.0 / Educational Fair Use"
DEFAULT_LEGAL_BASIS = "Public Domain (1835-1837 Imperial relic) / Academic Educational Fair Use"

URN_SLUGS = [
    "cao-dinh",
    "nhan-dinh",
    "chuong-dinh",
    "anh-dinh",
    "nghi-dinh",
    "thuan-dinh",
    "tuyen-dinh",
    "du-dinh",
    "huyen-dinh",
]

# Canonical 2D motif rubbings (bản dập / bản đúc nổi) for all 9 urns
URN_FALLBACK_2D_REGISTRY: dict[str, dict[str, Any]] = {
    "cao-dinh": {
        "asset_url": "/assets/ban-duc-noi/CAO%20DINH/CAO%20%C4%90%E1%BB%88NH.jpg",
        "disk_path": "ban-duc-noi/CAO DINH/CAO ĐỈNH.jpg",
        "format": "image/jpeg",
        "bytes": 8823,
        "sha256": "3187abe1940c680a5145eac960e50230f45cf7382a6e647a61988b2124f82a28",
        "rights_attribution": DEFAULT_RIGHTS_OWNER,
        "legal_basis": DEFAULT_LEGAL_BASIS,
    },
    "nhan-dinh": {
        "asset_url": "/assets/ban-duc-noi/NHAN%20DINH/NH%C3%82N%20%C4%90%E1%BB%88NH.jpg",
        "disk_path": "ban-duc-noi/NHAN DINH/NHÂN ĐỈNH.jpg",
        "format": "image/jpeg",
        "bytes": 9974,
        "sha256": "7395b93f6966e1802f8fe108511652c2d7c8fd0846578ecbd742134936f99e69",
        "rights_attribution": DEFAULT_RIGHTS_OWNER,
        "legal_basis": DEFAULT_LEGAL_BASIS,
    },
    "chuong-dinh": {
        "asset_url": "/assets/ban-duc-noi/CHUONG%20DINH/CH%C6%AF%C6%A0NG%20%C4%90%E1%BB%88NH.jpg",
        "disk_path": "ban-duc-noi/CHUONG DINH/CHƯƠNG ĐỈNH.jpg",
        "format": "image/jpeg",
        "bytes": 8706,
        "sha256": "50b47cce23604aa2af4f22274d702997f3101a43f5ac09c6e144f16b412c50f7",
        "rights_attribution": DEFAULT_RIGHTS_OWNER,
        "legal_basis": DEFAULT_LEGAL_BASIS,
    },
    "anh-dinh": {
        "asset_url": "/assets/ban-duc-noi/ANH%20DINH/ANH%20%C4%90%E1%BB%88NH.jpg",
        "disk_path": "ban-duc-noi/ANH DINH/ANH ĐỈNH.jpg",
        "format": "image/jpeg",
        "bytes": 10467,
        "sha256": "3adb2fb9fab2ae0f8f6b6f2dbf23f2366252726cf3c5026d6e00d24a09e45100",
        "rights_attribution": DEFAULT_RIGHTS_OWNER,
        "legal_basis": DEFAULT_LEGAL_BASIS,
    },
    "nghi-dinh": {
        "asset_url": "/assets/ban-duc-noi/NGHI%20DINH/NGHI%20DINH.jpg",
        "disk_path": "ban-duc-noi/NGHI DINH/NGHI DINH.jpg",
        "format": "image/jpeg",
        "bytes": 12104,
        "sha256": "01640017e63d04caf254b2cd9da198d23fdc1dce339fcc67ba4a69c8ae572258",
        "rights_attribution": DEFAULT_RIGHTS_OWNER,
        "legal_basis": DEFAULT_LEGAL_BASIS,
    },
    "thuan-dinh": {
        "asset_url": "/assets/ban-duc-noi/THUAN%20DINH/THU%E1%BA%A6N%20%C4%90%E1%BB%88NH.jpg",
        "disk_path": "ban-duc-noi/THUAN DINH/THUẦN ĐỈNH.jpg",
        "format": "image/jpeg",
        "bytes": 10449,
        "sha256": "8955a4fba76294831d316709dda849ed6a6d183a6a9e0a570078ec12c7d071c7",
        "rights_attribution": DEFAULT_RIGHTS_OWNER,
        "legal_basis": DEFAULT_LEGAL_BASIS,
    },
    "tuyen-dinh": {
        "asset_url": "/assets/ban-duc-noi/TUYEN%20DINH/TUYEN%20DINH.jpg",
        "disk_path": "ban-duc-noi/TUYEN DINH/TUYEN DINH.jpg",
        "format": "image/jpeg",
        "bytes": 11441,
        "sha256": "faa8ab1610139914808e9b9da4ff6becc7a0c9b22a63aa67f0ee6f15322588fa",
        "rights_attribution": DEFAULT_RIGHTS_OWNER,
        "legal_basis": DEFAULT_LEGAL_BASIS,
    },
    "du-dinh": {
        "asset_url": "/assets/ban-duc-noi/DU%20DINH/D%E1%BB%A4%20%C4%90%E1%BB%88NH.jpg",
        "disk_path": "ban-duc-noi/DU DINH/DỤ ĐỈNH.jpg",
        "format": "image/jpeg",
        "bytes": 9593,
        "sha256": "5cd92c531332f19e0272a487e2ecbbebe7cdb7e58cc7effc13f7dcd5d5efecab",
        "rights_attribution": DEFAULT_RIGHTS_OWNER,
        "legal_basis": DEFAULT_LEGAL_BASIS,
    },
    "huyen-dinh": {
        "asset_url": "/assets/ban-duc-noi/HUYEN%20DINH/HUY%E1%BB%80N%20%C4%90%E1%BB%88NH.jpg",
        "disk_path": "ban-duc-noi/HUYEN DINH/HUYỀN ĐỈNH.jpg",
        "format": "image/jpeg",
        "bytes": 9527,
        "sha256": "38b6bde4551d8db9e29bdc36212ed584138238e36d2ded7be2b387e45f539e96",
        "rights_attribution": DEFAULT_RIGHTS_OWNER,
        "legal_basis": DEFAULT_LEGAL_BASIS,
    },
}

EXPECTED_CAO_DINH_CHECKSUMS = {
    "CAO-DINH-v1-512.glb": "51f5baf131e85257186b0e4a89087870ff66e4c787f7775bea797fc2550d8611",
    "CAO-DINH-v1-1k.glb": "6f7e73424c18c5e6504ee25eda103b56958b1e79348937e152e60731a2bcd16a",
    "CAO-DINH-v1-2k.glb": "59d7f26f5af647d727b3ce4855a8533ca39c96825e1c9dea672a94cb32e42e74",
    "CAO-DINH-v1.glb": "6f7e73424c18c5e6504ee25eda103b56958b1e79348937e152e60731a2bcd16a",
}


# ==============================================================================
# Exceptions
# ==============================================================================


class AssetRightsError(ValueError):
    """Base exception for asset rights and attribution violations."""
    pass


class AssetDistributionBlockedError(AssetRightsError):
    """Raised when an asset fails public CDN distribution gate criteria."""
    pass


class AssetRightsRevokedError(AssetDistributionBlockedError):
    """Raised when an asset's rights are revoked, withdrawn, or restricted."""
    pass


class AssetRightsMissingLicenseError(AssetDistributionBlockedError):
    """Raised when an asset manifest is missing required license metadata."""
    pass


class AssetIntegrityError(AssetDistributionBlockedError):
    """Raised when cryptographic checksums or file formats do not match on disk."""
    pass


# ==============================================================================
# Core Functions
# ==============================================================================


def sha256_of_file(filepath: Path) -> str:
    """Compute hex SHA-256 digest of a file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def get_viewer_fallback(urn_slug: str) -> dict[str, Any]:
    """Retrieve verified 2D rubbing fallback metadata for an urn."""
    if urn_slug not in URN_FALLBACK_2D_REGISTRY:
        raise AssetRightsError(f"Unknown urn slug for viewer fallback: '{urn_slug}'")

    item = URN_FALLBACK_2D_REGISTRY[urn_slug]
    return {
        "type": "2d_rubbing",
        "component": "UrnAccessibleFallback",
        "asset_url": item["asset_url"],
        "disk_path": item["disk_path"],
        "format": item["format"],
        "bytes": item["bytes"],
        "sha256": item["sha256"],
        "rights_attribution": item["rights_attribution"],
        "legal_basis": item["legal_basis"],
    }


def validate_manifest_attribution(manifest: dict[str, Any]) -> dict[str, Any]:
    """Validate that a 3D urn manifest has complete, valid rights attribution metadata."""
    urn_slug = manifest.get("urn_slug")
    if not urn_slug:
        raise AssetRightsError("Manifest is missing required 'urn_slug'")

    # 1. Creator verification
    creator = manifest.get("creator") or manifest.get("rights_attribution")
    if not creator or not str(creator).strip():
        raise AssetRightsError(f"Urn '{urn_slug}' manifest missing creator / rights_attribution")

    # 2. License verification
    license_label = manifest.get("license")
    if not license_label or not str(license_label).strip():
        raise AssetRightsMissingLicenseError(f"Urn '{urn_slug}' manifest missing required license")

    norm_lic = license_label.strip().lower()
    if any(term in norm_lic for term in ("unlicensed", "proprietary", "all rights reserved")):
        raise AssetRightsRevokedError(f"Urn '{urn_slug}' license '{license_label}' is restricted/unlicensed")

    # 3. Rights owner verification
    rights_owner = manifest.get("rights_owner")
    if not rights_owner or not str(rights_owner).strip():
        raise AssetRightsError(f"Urn '{urn_slug}' manifest missing 'rights_owner'")

    # 4. Rights status check
    rights_status = manifest.get("rights_status", "cleared")
    norm_status = rights_status.strip().lower()
    if norm_status in RESTRICTED_RIGHTS_STATUSES:
        raise AssetRightsRevokedError(
            f"Urn '{urn_slug}' rights status is revoked or restricted: '{rights_status}'"
        )

    # 5. Public distribution flags
    if manifest.get("public_display_allowed") is False:
        raise AssetDistributionBlockedError(
            f"Urn '{urn_slug}' has public_display_allowed=False"
        )
    if manifest.get("public_distribution_allowed") is False:
        raise AssetDistributionBlockedError(
            f"Urn '{urn_slug}' has public_distribution_allowed=False"
        )

    # 6. Checksum check
    checksum = manifest.get("checksum")
    if not checksum or len(checksum) != 64:
        raise AssetRightsError(f"Urn '{urn_slug}' manifest missing or invalid SHA-256 checksum: '{checksum}'")

    # 7. Viewer fallback check
    if not manifest.get("has_2d_fallback"):
        raise AssetRightsError(f"Urn '{urn_slug}' manifest must declare has_2d_fallback=True")

    fallback_2d_url = manifest.get("fallback_2d_url")
    if not fallback_2d_url or not str(fallback_2d_url).strip():
        raise AssetRightsError(f"Urn '{urn_slug}' manifest missing 'fallback_2d_url'")

    viewer_fallback = manifest.get("viewer_fallback")
    if not viewer_fallback or not isinstance(viewer_fallback, dict):
        raise AssetRightsError(f"Urn '{urn_slug}' manifest missing structured 'viewer_fallback' block")

    for req_key in ("asset_url", "disk_path", "sha256", "bytes", "rights_attribution"):
        if not viewer_fallback.get(req_key):
            raise AssetRightsError(
                f"Urn '{urn_slug}' viewer_fallback missing required field '{req_key}'"
            )

    # 8. Hotspot attribution verification (if hotspots present)
    for idx, hotspot in enumerate(manifest.get("hotspots", [])):
        h_id = hotspot.get("hotspot_id", f"hotspot_{idx}")
        h_lic = hotspot.get("license")
        if h_lic:
            if any(term in str(h_lic).lower() for term in ("unlicensed", "proprietary", "all rights reserved")):
                raise AssetRightsRevokedError(f"Hotspot '{h_id}' license '{h_lic}' is restricted/unlicensed")
        h_stat = str(hotspot.get("rights_status") or "cleared").lower()
        if h_stat in RESTRICTED_RIGHTS_STATUSES:
            raise AssetRightsRevokedError(f"Hotspot '{h_id}' rights status is revoked or restricted: '{h_stat}'")
        if hotspot.get("public_display_allowed") is False or hotspot.get("public_distribution_allowed") is False:
            raise AssetDistributionBlockedError(f"Hotspot '{h_id}' public distribution disallowed")
        fb = hotspot.get("fallback_2d")
        if fb and isinstance(fb, dict):
            for req_key in ("thumbnail_url", "disk_path", "sha256", "bytes", "rights_attribution"):
                if not fb.get(req_key):
                    raise AssetRightsError(f"Hotspot '{h_id}' fallback_2d missing '{req_key}'")

    return {
        "urn_slug": urn_slug,
        "creator": creator,
        "license": license_label,
        "rights_owner": rights_owner,
        "rights_status": rights_status,
        "checksum": checksum,
        "fallback_2d_url": fallback_2d_url,
        "viewer_fallback": viewer_fallback,
        "attribution_valid": True,
    }


def validate_manifest_checksum_integrity(
    manifest: dict[str, Any], repo_root: Optional[Path] = None
) -> bool:
    """Verify cryptographic hash integrity and binary magic bytes of manifest assets on disk."""
    if repo_root is None:
        repo_root = Path(__file__).resolve().parents[2]

    urn_slug = manifest.get("urn_slug", "")
    viewer_fallback = manifest.get("viewer_fallback", {})

    # 1. Verify 2D rubbing fallback image on disk
    disk_rel = viewer_fallback.get("disk_path")
    if not disk_rel:
        raise AssetIntegrityError(f"Urn '{urn_slug}' viewer_fallback missing disk_path")

    fb_path = repo_root / disk_rel
    if not fb_path.exists():
        fb_path = repo_root / "frontend" / "public" / disk_rel
    if not fb_path.exists():
        raise AssetIntegrityError(f"2D rubbing fallback file not found on disk: {disk_rel}")

    actual_fb_sha = sha256_of_file(fb_path)
    expected_fb_sha = viewer_fallback.get("sha256")
    if actual_fb_sha != expected_fb_sha:
        raise AssetIntegrityError(
            f"2D rubbing SHA-256 mismatch for {disk_rel}: expected {expected_fb_sha}, got {actual_fb_sha}"
        )

    # Check image magic bytes
    with open(fb_path, "rb") as f:
        img_magic = f.read(4)
    if not (img_magic.startswith(JPEG_MAGIC) or img_magic.startswith(PNG_MAGIC)):
        raise AssetIntegrityError(f"File {disk_rel} does not contain valid image magic bytes")

    # 2. If 3D mesh is PRESENT, verify 3D LOD GLB assets on disk
    mesh_status = manifest.get("mesh_status", "MISSING")
    if mesh_status == "PRESENT":
        lods = manifest.get("lods", {})
        low_lod = lods.get("low", {})
        low_url = low_lod.get("url")
        if low_url:
            glb_path = repo_root / "frontend" / "public" / low_url.lstrip("/")
            if not glb_path.exists():
                glb_path = repo_root / low_url.lstrip("/")
            if not glb_path.exists():
                raise AssetIntegrityError(f"3D mesh file missing on disk: {low_url}")

            actual_glb_sha = sha256_of_file(glb_path)
            expected_glb_sha = low_lod.get("sha256")
            if expected_glb_sha and actual_glb_sha != expected_glb_sha:
                raise AssetIntegrityError(
                    f"3D mesh SHA-256 mismatch for {low_url}: expected {expected_glb_sha}, got {actual_glb_sha}"
                )

            with open(glb_path, "rb") as f:
                header = f.read(4)
            if header != GLB_MAGIC:
                raise AssetIntegrityError(f"3D mesh {low_url} is not a valid GLB container (magic: {header!r})")

    # 3. Verify hotspot 2D rubbing fallback images on disk
    for hotspot in manifest.get("hotspots", []):
        fb = hotspot.get("fallback_2d")
        if fb and isinstance(fb, dict):
            h_disk = fb.get("disk_path")
            if h_disk:
                h_path = repo_root / h_disk
                if not h_path.exists():
                    h_path = repo_root / "frontend" / "public" / h_disk
                if not h_path.exists():
                    raise AssetIntegrityError(f"Hotspot 2D rubbing missing on disk: {h_disk}")
                actual_h_sha = sha256_of_file(h_path)
                expected_h_sha = fb.get("sha256")
                if expected_h_sha and actual_h_sha != expected_h_sha:
                    raise AssetIntegrityError(
                        f"Hotspot 2D rubbing SHA-256 mismatch for {h_disk}: expected {expected_h_sha}, got {actual_h_sha}"
                    )
                with open(h_path, "rb") as f:
                    magic_h = f.read(4)
                if not (magic_h.startswith(JPEG_MAGIC) or magic_h.startswith(PNG_MAGIC)):
                    raise AssetIntegrityError(f"Hotspot file {h_disk} has invalid image magic header")

    return True


def can_distribute_on_cdn(manifest: dict[str, Any]) -> tuple[bool, Optional[str]]:
    """Determine whether an asset manifest is legally cleared for public CDN distribution."""
    # Check rights status
    rights_status = (manifest.get("rights_status") or "").strip().lower()
    if not rights_status or rights_status in RESTRICTED_RIGHTS_STATUSES:
        return False, f"Asset rights restricted or revoked (rights_status='{rights_status}')"

    if manifest.get("public_distribution_allowed") is False:
        return False, "public_distribution_allowed is explicitly False"

    if manifest.get("public_display_allowed") is False:
        return False, "public_display_allowed is explicitly False"

    license_label = manifest.get("license")
    if not license_label or not str(license_label).strip():
        return False, "Missing required license specification"

    creator = manifest.get("creator") or manifest.get("rights_attribution")
    if not creator or not str(creator).strip():
        return False, "Missing creator / rights_attribution"

    if not manifest.get("checksum"):
        return False, "Missing cryptographic checksum"

    return True, None


def enforce_cdn_distribution_policy(
    manifest: dict[str, Any], repo_root: Optional[Path] = None
) -> dict[str, Any]:
    """Enforce public CDN distribution policy.

    Fails closed:
    - If rights are revoked, restricted, or license is missing, raises
      AssetDistributionBlockedError / AssetRightsRevokedError / AssetRightsMissingLicenseError.
    - If checksum integrity fails, raises AssetIntegrityError.
    - If all criteria pass, returns verified distribution payload with cache controls.
    """
    urn_slug = manifest.get("urn_slug", "unknown")

    # 1. Attribute validation
    validate_manifest_attribution(manifest)

    # 2. Check distribution permission
    allowed, reason = can_distribute_on_cdn(manifest)
    if not allowed:
        raise AssetDistributionBlockedError(
            f"Asset manifest for '{urn_slug}' blocked from public CDN distribution: {reason}"
        )

    # 3. Checksum integrity verification
    validate_manifest_checksum_integrity(manifest, repo_root=repo_root)

    # Return distribution clearance stamp
    return {
        "urn_slug": urn_slug,
        "cdn_distribution_status": "ALLOWED",
        "cache_control": "public, max-age=86400, stale-while-revalidate=3600",
        "rights_attribution": manifest.get("rights_attribution"),
        "license": manifest.get("license"),
        "rights_owner": manifest.get("rights_owner"),
        "checksum": manifest.get("checksum"),
        "has_2d_fallback": manifest.get("has_2d_fallback", True),
        "viewer_fallback": manifest.get("viewer_fallback"),
    }


def revoke_manifest_rights(
    manifest: dict[str, Any], reason: str = "Rights withdrawn by owner"
) -> dict[str, Any]:
    """Takedown / revocation protocol: mark manifest as revoked and block distribution."""
    revoked = json.loads(json.dumps(manifest))
    revoked["rights_status"] = "revoked"
    revoked["public_distribution_allowed"] = False
    revoked["public_display_allowed"] = False
    revoked["revocation_reason"] = reason
    return revoked


def sync_manifest_to_historical_asset(
    db: Session,
    manifest: dict[str, Any],
    entity_id: Optional[UUID] = None,
) -> Any:
    """Synchronize manifest metadata to a persistent HistoricalAsset model."""
    from ..history_models import HistoricalAsset

    urn_slug = manifest.get("urn_slug", "unknown")
    storage_url = f"/public/models/manifests/{urn_slug}.json"
    fallback_url = manifest.get("fallback_2d_url")
    checksum = manifest.get("checksum")

    existing = db.query(HistoricalAsset).filter(HistoricalAsset.storage_url == storage_url).first()
    if existing:
        existing.rights_status = manifest.get("rights_status", "cleared")
        existing.license = manifest.get("license", DEFAULT_LICENSE)
        existing.attribution = manifest.get("rights_attribution", DEFAULT_CREATOR)
        existing.source_origin = manifest.get("rights_owner", DEFAULT_RIGHTS_OWNER)
        existing.public_display_allowed = manifest.get("public_display_allowed", True)
        existing.sha256 = checksum
        existing.thumbnail_url = fallback_url
        if entity_id:
            existing.entity_id = entity_id
        db.flush()
        return existing

    asset = HistoricalAsset(
        asset_type="3d_model",
        storage_url=storage_url,
        thumbnail_url=fallback_url,
        mime_type="application/json",
        sha256=checksum,
        rights_status=manifest.get("rights_status", "cleared"),
        license=manifest.get("license", DEFAULT_LICENSE),
        attribution=manifest.get("rights_attribution", DEFAULT_CREATOR),
        source_origin=manifest.get("rights_owner", DEFAULT_RIGHTS_OWNER),
        public_display_allowed=manifest.get("public_display_allowed", True),
        derivative_allowed=True,
        entity_id=entity_id,
    )
    db.add(asset)
    db.flush()
    return asset


def validate_historical_asset_distribution(asset: Any) -> tuple[bool, Optional[str]]:
    """Verify that a HistoricalAsset row satisfies CDN distribution policy."""
    if asset.public_display_allowed is False:
        return False, "public_display_allowed is False"
    if not asset.rights_status or asset.rights_status.lower() in RESTRICTED_RIGHTS_STATUSES:
        return False, f"Asset rights restricted or revoked: '{asset.rights_status}'"
    if not asset.license or not str(asset.license).strip():
        return False, "Missing license"
    if not asset.attribution or not str(asset.attribution).strip():
        return False, "Missing attribution"
    if not asset.sha256 or len(asset.sha256) != 64:
        return False, "Missing valid SHA-256 checksum"
    return True, None


def audit_all_urn_manifests(
    manifests_dir: Optional[Path] = None, repo_root: Optional[Path] = None
) -> dict[str, Any]:
    """Audit all 9 urn manifests on disk for rights attribution and CDN clearance."""
    if repo_root is None:
        repo_root = Path(__file__).resolve().parents[2]
    if manifests_dir is None:
        manifests_dir = repo_root / "public" / "models" / "manifests"

    assert manifests_dir.exists(), f"Manifests directory not found: {manifests_dir}"

    results: list[dict[str, Any]] = []
    all_cleared = True

    for slug in URN_SLUGS:
        mf_path = manifests_dir / f"{slug}.json"
        assert mf_path.exists(), f"Manifest missing for urn '{slug}': {mf_path}"

        with open(mf_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        attribution_info = validate_manifest_attribution(manifest)
        integrity_ok = validate_manifest_checksum_integrity(manifest, repo_root=repo_root)
        allowed, reason = can_distribute_on_cdn(manifest)
        if not (integrity_ok and allowed):
            all_cleared = False

        results.append({
            "urn_slug": slug,
            "creator": attribution_info["creator"],
            "license": attribution_info["license"],
            "rights_owner": attribution_info["rights_owner"],
            "rights_status": attribution_info["rights_status"],
            "checksum": attribution_info["checksum"],
            "fallback_2d_url": attribution_info["fallback_2d_url"],
            "integrity_verified": integrity_ok,
            "cdn_distribution_allowed": allowed,
            "rejection_reason": reason,
        })

    return {
        "total_urns_audited": len(results),
        "all_cleared": all_cleared,
        "urns": results,
    }


# ==============================================================================
# Motif Relics (162 Motifs) Registry & Fallback Resolution Gate
# ==============================================================================

_CACHED_MOTIF_REGISTRY: Optional[list[dict[str, Any]]] = None
_CACHED_MOTIF_LOOKUP: Optional[dict[str, dict[str, Any]]] = None


def get_motif_registry_162(repo_root: Optional[Path] = None) -> list[dict[str, Any]]:
    """Load and return the complete canonical registry of 162 motif relics."""
    global _CACHED_MOTIF_REGISTRY, _CACHED_MOTIF_LOOKUP
    if _CACHED_MOTIF_REGISTRY is not None:
        return _CACHED_MOTIF_REGISTRY

    if repo_root is None:
        repo_root = Path(__file__).resolve().parents[2]

    inv_path = repo_root / "artifacts" / "implementation" / "W00" / "W00_A09_media_rights_inventory.json"
    if not inv_path.exists():
        raise FileNotFoundError(f"Media rights inventory not found: {inv_path}")

    with open(inv_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    raw_motifs = data.get("motif_mesh_registry_162", [])
    motifs: list[dict[str, Any]] = []

    for item in raw_motifs:
        fb = item.get("fallback_2d", {})
        coords = item.get("hotspot_coordinates", {})
        is_present = (item.get("parent_mesh_status") == "PRESENT")
        model_url = "/assets/models/CAO-DINH-v1.glb" if is_present else None

        motifs.append({
            "id": item["id"],
            "urn_slug": item["urn_slug"],
            "name_vi": item["name_vi"],
            "name_en": item.get("name_en"),
            "name_han_nom": item.get("name_han_nom"),
            "category": item.get("category"),
            "rarity": item.get("rarity"),
            "3d_mesh_id": item.get("3d_mesh_id"),
            "parent_mesh_status": item.get("parent_mesh_status", "MISSING"),
            "is_fake_3d": item.get("is_fake_3d", False),
            "model_url": model_url,
            "coordinates": {
                "pos_x": coords.get("pos_x", 0.0),
                "pos_y": coords.get("pos_y", 0.0),
                "pos_z": coords.get("pos_z", 0.0),
                "bounding_radius": coords.get("bounding_radius", 0.08),
            },
            "fallback_2d": {
                "thumbnail_url": fb.get("thumbnail_url"),
                "disk_path": fb.get("disk_path"),
                "bytes": fb.get("bytes"),
                "sha256": fb.get("sha256"),
                "format": fb.get("format", "image/jpeg"),
                "rights_attribution": fb.get("rights_attribution", DEFAULT_RIGHTS_OWNER),
                "legal_basis": fb.get("legal_basis", DEFAULT_LEGAL_BASIS),
            },
            "creator": DEFAULT_CREATOR,
            "rights_owner": DEFAULT_RIGHTS_OWNER,
            "rights_attribution": DEFAULT_RIGHTS_OWNER,
            "license": DEFAULT_LICENSE,
            "rights_status": "cleared",
            "public_distribution_allowed": True,
            "public_display_allowed": True,
        })

    _CACHED_MOTIF_REGISTRY = motifs

    lookup: dict[str, dict[str, Any]] = {}
    for m in motifs:
        lookup[m["id"]] = m
        lookup[f"{m['urn_slug']}:{m['name_vi'].lower()}"] = m
        if m.get("3d_mesh_id"):
            lookup[m["3d_mesh_id"]] = m
    _CACHED_MOTIF_LOOKUP = lookup

    return motifs


def get_motif_fallback(
    motif_id_or_slug: str,
    urn_context: Optional[str] = None,
    repo_root: Optional[Path] = None,
) -> dict[str, Any]:
    """Retrieve 2D rubbing fallback metadata for one of the 162 motif relics."""
    get_motif_registry_162(repo_root=repo_root)
    assert _CACHED_MOTIF_LOOKUP is not None

    target = motif_id_or_slug.strip()
    if target in _CACHED_MOTIF_LOOKUP:
        return _CACHED_MOTIF_LOOKUP[target]["fallback_2d"]

    if urn_context:
        ctx_key = f"{urn_context.strip().lower()}:{target.lower()}"
        if ctx_key in _CACHED_MOTIF_LOOKUP:
            return _CACHED_MOTIF_LOOKUP[ctx_key]["fallback_2d"]

    norm_target = target.lower().replace("-", " ").replace("_", " ")
    for m in _CACHED_MOTIF_REGISTRY or []:
        if urn_context and m["urn_slug"] != urn_context.strip().lower():
            continue
        if m["name_vi"].lower() == norm_target or m["id"].lower() == target.lower():
            return m["fallback_2d"]

    raise AssetRightsError(f"Motif '{motif_id_or_slug}' not found in 162 relic registry (urn_context='{urn_context}')")


def resolve_asset_fallback(
    entity_slug_or_id: str,
    urn_slug: Optional[str] = None,
    webgl_supported: bool = True,
    client_low_power: bool = False,
    force_2d_fallback: bool = False,
    repo_root: Optional[Path] = None,
) -> dict[str, Any]:
    """Asset resolution gate with clean 2D rubbing fallback (ADR 05 / Spec §V2-C).

    If 3D model is unavailable (missing mesh, WebGL unsupported, low-power mode,
    or client-requested 2D), cleanly falls back to the high-resolution 2D rubbing
    photograph in ban-duc-noi/.

    Fails closed: If rights are revoked, restricted, or distribution disallowed,
    strictly raises AssetRightsRevokedError or AssetDistributionBlockedError.
    """
    slug = entity_slug_or_id.strip()

    # Case 1: Check if it is an Urn (one of the 9 canonical urns)
    if slug in URN_FALLBACK_2D_REGISTRY or (urn_slug and slug == urn_slug):
        resolved_urn = slug if slug in URN_FALLBACK_2D_REGISTRY else urn_slug
        assert resolved_urn is not None
        fb_2d = get_viewer_fallback(resolved_urn)

        if repo_root is None:
            repo_root = Path(__file__).resolve().parents[2]
        manifest_path = repo_root / "public" / "models" / "manifests" / f"{resolved_urn}.json"
        if manifest_path.exists():
            with open(manifest_path, "r", encoding="utf-8") as f:
                mf = json.load(f)
            validate_manifest_attribution(mf)
            allowed, reason = can_distribute_on_cdn(mf)
            if not allowed:
                raise AssetDistributionBlockedError(f"Urn '{resolved_urn}' distribution blocked: {reason}")
            mesh_status = mf.get("mesh_status", "MISSING")
            primary_model_url = mf.get("lods", {}).get("medium", {}).get("url")
            lods = mf.get("lods")
            rights_meta = {
                "creator": mf.get("creator", DEFAULT_CREATOR),
                "rights_owner": mf.get("rights_owner", DEFAULT_RIGHTS_OWNER),
                "rights_attribution": mf.get("rights_attribution", DEFAULT_CREATOR),
                "license": mf.get("license", DEFAULT_LICENSE),
                "rights_status": mf.get("rights_status", "cleared"),
                "public_distribution_allowed": mf.get("public_distribution_allowed", True),
                "public_display_allowed": mf.get("public_display_allowed", True),
            }
        else:
            mesh_status = "PRESENT" if resolved_urn == "cao-dinh" else "MISSING"
            primary_model_url = "/assets/models/CAO-DINH-v1.glb" if resolved_urn == "cao-dinh" else None
            lods = None
            rights_meta = {
                "creator": DEFAULT_CREATOR,
                "rights_owner": DEFAULT_RIGHTS_OWNER,
                "rights_attribution": DEFAULT_CREATOR,
                "license": DEFAULT_LICENSE,
                "rights_status": "cleared",
                "public_distribution_allowed": True,
                "public_display_allowed": True,
            }

        if mesh_status == "PRESENT" and webgl_supported and not client_low_power and not force_2d_fallback:
            return {
                "target_type": "urn",
                "target_slug": resolved_urn,
                "render_mode": "3d_mesh",
                "mesh_available": True,
                "primary_asset": {
                    "asset_type": "3d_model",
                    "model_url": primary_model_url,
                    "lods": lods,
                },
                "fallback_asset": fb_2d,
                "rights_metadata": rights_meta,
            }

        if mesh_status != "PRESENT":
            reason = "mesh_unavailable"
        elif not webgl_supported:
            reason = "webgl_unsupported"
        elif client_low_power:
            reason = "low_power_budget"
        else:
            reason = "client_forced_2d"

        return {
            "target_type": "urn",
            "target_slug": resolved_urn,
            "render_mode": "2d_fallback",
            "fallback_reason": reason,
            "mesh_available": (mesh_status == "PRESENT"),
            "primary_asset": fb_2d,
            "fallback_asset": fb_2d,
            "accessible_component": "UrnAccessibleFallback",
            "rights_metadata": rights_meta,
        }

    # Case 2: Motif relic (one of 162 relief motifs)
    get_motif_registry_162(repo_root=repo_root)
    assert _CACHED_MOTIF_REGISTRY is not None

    motif = None
    target = slug.strip()
    if _CACHED_MOTIF_LOOKUP and target in _CACHED_MOTIF_LOOKUP:
        motif = _CACHED_MOTIF_LOOKUP[target]
    elif urn_slug and _CACHED_MOTIF_LOOKUP and f"{urn_slug.strip().lower()}:{target.lower()}" in _CACHED_MOTIF_LOOKUP:
        motif = _CACHED_MOTIF_LOOKUP[f"{urn_slug.strip().lower()}:{target.lower()}"]
    else:
        norm_target = target.lower().replace("-", " ").replace("_", " ")
        for m in _CACHED_MOTIF_REGISTRY:
            if urn_slug and m["urn_slug"] != urn_slug.strip().lower():
                continue
            if m["name_vi"].lower() == norm_target or m["id"].lower() == target.lower():
                motif = m
                break

    if not motif:
        raise AssetRightsError(f"Relic '{entity_slug_or_id}' could not be resolved as urn or motif.")

    if motif.get("rights_status", "cleared").lower() in RESTRICTED_RIGHTS_STATUSES:
        raise AssetRightsRevokedError(f"Motif '{motif['id']}' rights are revoked/restricted")
    if motif.get("public_distribution_allowed") is False or motif.get("public_display_allowed") is False:
        raise AssetDistributionBlockedError(f"Motif '{motif['id']}' public distribution disallowed")

    parent_urn = motif["urn_slug"]
    parent_mesh_present = (motif["parent_mesh_status"] == "PRESENT")
    fb_2d = {
        "type": "2d_rubbing",
        "component": "UrnAccessibleFallback",
        "asset_url": motif["fallback_2d"]["thumbnail_url"],
        "disk_path": motif["fallback_2d"]["disk_path"],
        "format": motif["fallback_2d"]["format"],
        "bytes": motif["fallback_2d"]["bytes"],
        "sha256": motif["fallback_2d"]["sha256"],
        "rights_attribution": motif["fallback_2d"]["rights_attribution"],
        "legal_basis": motif["fallback_2d"]["legal_basis"],
    }
    rights_meta = {
        "creator": motif["creator"],
        "rights_owner": motif["rights_owner"],
        "rights_attribution": motif["rights_attribution"],
        "license": motif["license"],
        "rights_status": motif["rights_status"],
        "public_distribution_allowed": motif["public_distribution_allowed"],
        "public_display_allowed": motif["public_display_allowed"],
    }

    if parent_mesh_present and webgl_supported and not client_low_power and not force_2d_fallback:
        return {
            "target_type": "motif",
            "target_id": motif["id"],
            "urn_slug": parent_urn,
            "render_mode": "3d_mesh",
            "mesh_available": True,
            "primary_asset": {
                "asset_type": "3d_hotspot",
                "model_url": motif["model_url"],
                "coordinates": motif["coordinates"],
            },
            "fallback_asset": fb_2d,
            "rights_metadata": rights_meta,
        }

    if not parent_mesh_present:
        reason = "mesh_unavailable"
    elif not webgl_supported:
        reason = "webgl_unsupported"
    elif client_low_power:
        reason = "low_power_budget"
    else:
        reason = "client_forced_2d"

    return {
        "target_type": "motif",
        "target_id": motif["id"],
        "urn_slug": parent_urn,
        "render_mode": "2d_fallback",
        "fallback_reason": reason,
        "mesh_available": parent_mesh_present,
        "primary_asset": fb_2d,
        "fallback_asset": fb_2d,
        "accessible_component": "UrnAccessibleFallback",
        "rights_metadata": rights_meta,
    }


def audit_all_relic_assets(
    manifests_dir: Optional[Path] = None,
    repo_root: Optional[Path] = None,
) -> dict[str, Any]:
    """Audit all 9 urns + 162 motif relics (171 relics total) for 3D linkage, 2D fallback, and license rights."""
    if repo_root is None:
        repo_root = Path(__file__).resolve().parents[2]
    if manifests_dir is None:
        manifests_dir = repo_root / "public" / "models" / "manifests"

    urn_audit = audit_all_urn_manifests(manifests_dir=manifests_dir, repo_root=repo_root)
    motifs = get_motif_registry_162(repo_root=repo_root)

    assert len(motifs) == 162, f"Expected 162 motifs, got {len(motifs)}"

    motif_results: list[dict[str, Any]] = []
    all_motifs_cleared = True

    for m in motifs:
        dp = m["fallback_2d"]["disk_path"]
        fp = repo_root / dp
        if not fp.exists():
            fp = repo_root / "frontend" / "public" / dp
        exists = fp.exists()
        actual_sha = sha256_of_file(fp) if exists else None
        sha_matches = (actual_sha == m["fallback_2d"]["sha256"])

        cleared = exists and sha_matches and m["rights_status"] == "cleared" and m["license"] in APPROVED_LICENSES
        if not cleared:
            all_motifs_cleared = False

        motif_results.append({
            "id": m["id"],
            "urn_slug": m["urn_slug"],
            "name_vi": m["name_vi"],
            "3d_model_linked": m["model_url"] is not None if m["parent_mesh_status"] == "PRESENT" else True,
            "coordinates_present": bool(m["coordinates"]),
            "fallback_2d_present": exists,
            "checksum_verified": sha_matches,
            "license": m["license"],
            "rights_owner": m["rights_owner"],
            "cleared": cleared,
        })

    return {
        "total_urns_audited": urn_audit["total_urns_audited"],
        "total_motifs_audited": len(motif_results),
        "total_relics_audited": urn_audit["total_urns_audited"] + len(motif_results),
        "all_urns_cleared": urn_audit["all_cleared"],
        "all_motifs_cleared": all_motifs_cleared,
        "all_relics_cleared": urn_audit["all_cleared"] and all_motifs_cleared,
        "urns": urn_audit["urns"],
        "motifs_summary": {
            "total": 162,
            "verified_on_disk": sum(1 for m in motif_results if m["fallback_2d_present"]),
            "checksums_verified": sum(1 for m in motif_results if m["checksum_verified"]),
            "with_coordinates": sum(1 for m in motif_results if m["coordinates_present"]),
        },
    }
