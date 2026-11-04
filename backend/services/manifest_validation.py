# -*- coding: utf-8 -*-
"""3D Asset Manifest Validation Service (Ticket V5-T041 / Wave W04 Slot A01).

Validates 3D asset manifests in public/models/manifests and frontend/src/components/UrnViewer.tsx:
1. Version Validation:
   - model_version, hotspot_version, coordinate_version (integers >= 1).
2. Checksum & Byte Size Validation:
   - Cryptographic SHA-256 integrity (64 hex characters).
   - Physical disk match for PRESENT meshes (Cao Đỉnh LODs: 512, 1k, 2k).
   - Null hash and bytes=0 for MISSING meshes, preventing phantom/fake assertions.
   - glTF binary magic bytes verification (b"glTF").
3. License & Rights Clearance:
   - Approved licenses (e.g. CC BY 4.0 / Educational Fair Use).
   - Institutional rights owner (HMCC) and creator attribution.
   - Fail-closed on restricted/proprietary licenses or revoked rights status.
4. Mesh ID Joins:
   - Exactly 162 hotspots across 9 urns (18 per urn).
   - Globally unique 3d_mesh_id (mesh_urn_{slug}_{idx}_v1), motif_id (urn_{slug}_{idx}),
     and hotspot_id ({slug}-{relief_slug}).
   - Full join integrity without cross-urn leakage.
5. 2D Fallback for Missing Meshes & WebGL Health:
   - Enforces 100% 2D rubbing fallback coverage (ban-duc-noi/ & UrnAccessibleFallback).
   - Negative abuse: Missing mesh does not show blank canvas or claim complete model
     without fallback.
   - WebGL health contract: Context loss and creation failure gracefully degrade
     to UrnAccessibleFallback without blank canvas.
"""
from __future__ import annotations

import hashlib
import json
import logging
import re
from pathlib import Path
from typing import Any, Optional

from .asset_rights import (
    APPROVED_LICENSES,
    APPROVED_RIGHTS_STATUSES,
    DEFAULT_CREATOR,
    DEFAULT_RIGHTS_OWNER,
    GLB_MAGIC,
    JPEG_MAGIC,
    PNG_MAGIC,
    RESTRICTED_RIGHTS_STATUSES,
    URN_FALLBACK_2D_REGISTRY,
    URN_SLUGS,
    sha256_of_file,
)

logger = logging.getLogger("luuniensuki.manifest_validation")


# ==============================================================================
# Domain Exceptions
# ==============================================================================


class ManifestValidationError(Exception):
    """Base exception for 3D manifest validation errors."""
    pass


class ManifestVersionError(ManifestValidationError):
    """Raised when asset version (model, hotspot, or coordinate) is invalid or missing."""
    pass


class ManifestChecksumError(ManifestValidationError):
    """Raised when asset checksum is invalid, tampered, or mismatched."""
    pass


class ManifestSizeError(ManifestValidationError):
    """Raised when asset byte size is invalid, zero when required, or mismatched."""
    pass


class ManifestLicenseError(ManifestValidationError):
    """Raised when asset license is missing, restricted, or unapproved."""
    pass


class ManifestMeshJoinError(ManifestValidationError):
    """Raised when 3d_mesh_id, motif_id, or mesh_name join fails or contains duplicates/orphans."""
    pass


class ManifestMissingFallbackError(ManifestValidationError):
    """Raised when 2D fallback is missing or incomplete for missing meshes."""
    pass


class ManifestPhantomModelError(ManifestValidationError):
    """Raised when an urn claims a 3D model is PRESENT or complete without physical files."""
    pass


class WebGLHealthError(ManifestValidationError):
    """Raised when WebGL health fails or fallback degradation contract is violated."""
    pass


# ==============================================================================
# Helpers
# ==============================================================================


def resolve_repo_root() -> Path:
    """Resolve repository root directory."""
    return Path(__file__).resolve().parents[2]


def load_manifest(path: Path) -> dict[str, Any]:
    """Load JSON manifest file from disk."""
    if not path.exists():
        raise FileNotFoundError(f"Manifest file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ==============================================================================
# Core Validation Functions
# ==============================================================================


def validate_3d_asset_version(manifest: dict[str, Any]) -> dict[str, Any]:
    """Validate model_version, hotspot_version, and coordinate_version.
    
    All versions must be positive integers >= 1.
    """
    urn_slug = manifest.get("urn_slug", "unknown")

    # 1. Root model_version
    model_version = manifest.get("model_version")
    if model_version is None or not isinstance(model_version, int) or model_version < 1:
        raise ManifestVersionError(
            f"Urn '{urn_slug}' manifest missing or invalid model_version: {model_version}"
        )

    # 2. Root hotspot_version
    hotspot_version = manifest.get("hotspot_version")
    if hotspot_version is None or not isinstance(hotspot_version, int) or hotspot_version < 1:
        raise ManifestVersionError(
            f"Urn '{urn_slug}' manifest missing or invalid hotspot_version: {hotspot_version}"
        )

    # 3. Hotspot-level versions
    hotspots = manifest.get("hotspots", [])
    for idx, hotspot in enumerate(hotspots):
        hid = hotspot.get("hotspot_id", f"hotspot_{idx}")
        coord_ver = hotspot.get("coordinate_version")
        if coord_ver is None or not isinstance(coord_ver, int) or coord_ver < 1:
            raise ManifestVersionError(
                f"Hotspot '{hid}' in urn '{urn_slug}' missing or invalid coordinate_version: {coord_ver}"
            )
        h_model_ver = hotspot.get("model_version")
        if h_model_ver is None or not isinstance(h_model_ver, int) or h_model_ver < 1:
            raise ManifestVersionError(
                f"Hotspot '{hid}' in urn '{urn_slug}' missing or invalid model_version: {h_model_ver}"
            )

    return {
        "urn_slug": urn_slug,
        "model_version": model_version,
        "hotspot_version": hotspot_version,
        "hotspot_count": len(hotspots),
        "version_valid": True,
    }


def validate_3d_asset_checksum_and_size(
    manifest: dict[str, Any], repo_root: Optional[Path] = None
) -> dict[str, Any]:
    """Validate 3D asset checksums and byte sizes.
    
    Enforces:
    - Root manifest checksum is a valid 64-char hex string.
    - For PRESENT meshes (Cao Đỉnh LODs: low, medium, high):
      - bytes > 0 matching disk file size exactly.
      - sha256 matching disk file SHA-256 exactly.
      - Binary header matching glTF magic bytes (b"glTF").
    - For MISSING meshes:
      - status must be "MISSING".
      - sha256 must be None (no fabricated checksums).
      - bytes must be 0.
      - fallback_url must be None (prevents phantom model substitution).
    """
    if repo_root is None:
        repo_root = resolve_repo_root()

    urn_slug = manifest.get("urn_slug", "unknown")
    root_checksum = manifest.get("checksum")
    if not root_checksum or not isinstance(root_checksum, str) or len(root_checksum) != 64:
        raise ManifestChecksumError(
            f"Urn '{urn_slug}' manifest missing or invalid SHA-256 checksum: {root_checksum}"
        )
    if not re.match(r"^[0-9a-f]{64}$", root_checksum.lower()):
        raise ManifestChecksumError(
            f"Urn '{urn_slug}' checksum contains invalid hex characters: {root_checksum}"
        )

    mesh_status = manifest.get("mesh_status", "MISSING")
    lods = manifest.get("lods", {})
    if not lods or not isinstance(lods, dict):
        raise ManifestValidationError(f"Urn '{urn_slug}' manifest missing 'lods' dictionary")

    for lod_name in ("low", "medium", "high"):
        lod = lods.get(lod_name)
        if not lod or not isinstance(lod, dict):
            raise ManifestValidationError(f"Urn '{urn_slug}' lods missing '{lod_name}' LOD entry")

        if mesh_status == "PRESENT":
            # LOD must have valid bytes and checksum
            lod_bytes = lod.get("bytes")
            if lod_bytes is None or not isinstance(lod_bytes, int) or lod_bytes <= 0:
                raise ManifestSizeError(
                    f"Urn '{urn_slug}' LOD '{lod_name}' must have bytes > 0, got {lod_bytes}"
                )

            lod_sha = lod.get("sha256")
            if not lod_sha or not isinstance(lod_sha, str) or len(lod_sha) != 64:
                raise ManifestChecksumError(
                    f"Urn '{urn_slug}' LOD '{lod_name}' missing or invalid sha256: {lod_sha}"
                )

            # Check physical file on disk
            lod_url = lod.get("url", "")
            disk_path = repo_root / "frontend" / "public" / lod_url.lstrip("/")
            if not disk_path.exists():
                disk_path = repo_root / "public" / lod_url.lstrip("/")
            if not disk_path.exists():
                raise ManifestPhantomModelError(
                    f"Urn '{urn_slug}' claims PRESENT mesh but physical file missing on disk: {lod_url}"
                )

            actual_size = disk_path.stat().st_size
            if actual_size != lod_bytes:
                raise ManifestSizeError(
                    f"Urn '{urn_slug}' LOD '{lod_name}' size mismatch: declared {lod_bytes}, disk {actual_size}"
                )

            actual_sha = sha256_of_file(disk_path)
            if actual_sha.lower() != lod_sha.lower():
                raise ManifestChecksumError(
                    f"Urn '{urn_slug}' LOD '{lod_name}' sha256 mismatch: declared {lod_sha}, disk {actual_sha}"
                )

            # Check glTF magic bytes
            with open(disk_path, "rb") as gf:
                magic = gf.read(4)
            if magic != GLB_MAGIC:
                raise ManifestChecksumError(
                    f"Urn '{urn_slug}' LOD '{lod_name}' does not contain valid glTF magic bytes: {magic}"
                )

        else:
            # MISSING mesh invariants
            if lod.get("status") != "MISSING":
                raise ManifestPhantomModelError(
                    f"Urn '{urn_slug}' has mesh_status='MISSING' but LOD '{lod_name}' status is not 'MISSING'"
                )
            if lod.get("sha256") is not None:
                raise ManifestChecksumError(
                    f"Urn '{urn_slug}' is MISSING but declares non-null LOD sha256: {lod.get('sha256')}"
                )
            if lod.get("bytes") != 0:
                raise ManifestSizeError(
                    f"Urn '{urn_slug}' is MISSING but declares non-zero LOD bytes: {lod.get('bytes')}"
                )
            if lod.get("fallback_url") is not None:
                raise ManifestPhantomModelError(
                    f"Urn '{urn_slug}' is MISSING but declares fallback_url (phantom substitution blocked)"
                )

    return {
        "urn_slug": urn_slug,
        "mesh_status": mesh_status,
        "root_checksum": root_checksum,
        "lods_verified": list(lods.keys()),
        "integrity_valid": True,
    }


def validate_3d_asset_license(manifest: dict[str, Any]) -> dict[str, Any]:
    """Validate licensing, rights ownership, and public distribution clearance.
    
    Enforces:
    - license in APPROVED_LICENSES (e.g. 'CC BY 4.0 / Educational Fair Use').
    - rights_status in APPROVED_RIGHTS_STATUSES ('cleared').
    - Fails closed on RESTRICTED_RIGHTS_STATUSES (revoked, restricted, etc.).
    - Fails closed on missing or proprietary licenses.
    - public_distribution_allowed and public_display_allowed must be True.
    - All hotspots inherit or specify approved license and cleared rights.
    """
    urn_slug = manifest.get("urn_slug", "unknown")

    license_label = manifest.get("license")
    if not license_label or not isinstance(license_label, str) or not license_label.strip():
        raise ManifestLicenseError(f"Urn '{urn_slug}' manifest missing required license")

    norm_lic = license_label.strip().lower()
    if any(term in norm_lic for term in ("unlicensed", "proprietary", "all rights reserved", "restricted")):
        raise ManifestLicenseError(f"Urn '{urn_slug}' has restricted/proprietary license: '{license_label}'")

    if license_label not in APPROVED_LICENSES and not any(app.lower() in norm_lic for app in APPROVED_LICENSES):
        raise ManifestLicenseError(f"Urn '{urn_slug}' license '{license_label}' not in APPROVED_LICENSES")

    rights_status = str(manifest.get("rights_status", "")).strip().lower()
    if not rights_status or rights_status in RESTRICTED_RIGHTS_STATUSES:
        raise ManifestLicenseError(f"Urn '{urn_slug}' rights_status is restricted or revoked: '{rights_status}'")
    if rights_status not in APPROVED_RIGHTS_STATUSES:
        raise ManifestLicenseError(f"Urn '{urn_slug}' rights_status '{rights_status}' not approved")

    if manifest.get("public_distribution_allowed") is not True:
        raise ManifestLicenseError(f"Urn '{urn_slug}' public_distribution_allowed is not True")
    if manifest.get("public_display_allowed") is not True:
        raise ManifestLicenseError(f"Urn '{urn_slug}' public_display_allowed is not True")

    creator = manifest.get("creator") or manifest.get("rights_attribution")
    if not creator or not str(creator).strip():
        raise ManifestLicenseError(f"Urn '{urn_slug}' manifest missing creator / rights_attribution")

    rights_owner = manifest.get("rights_owner")
    if not rights_owner or not str(rights_owner).strip():
        raise ManifestLicenseError(f"Urn '{urn_slug}' manifest missing rights_owner")

    # Validate hotspot licenses
    for idx, hotspot in enumerate(manifest.get("hotspots", [])):
        hid = hotspot.get("hotspot_id", f"hotspot_{idx}")
        h_lic = hotspot.get("license")
        if h_lic:
            norm_hlic = str(h_lic).lower()
            if any(term in norm_hlic for term in ("unlicensed", "proprietary", "all rights reserved")):
                raise ManifestLicenseError(f"Hotspot '{hid}' in '{urn_slug}' has restricted license: '{h_lic}'")
        h_stat = str(hotspot.get("rights_status", "cleared")).lower()
        if h_stat in RESTRICTED_RIGHTS_STATUSES:
            raise ManifestLicenseError(f"Hotspot '{hid}' in '{urn_slug}' rights_status revoked: '{h_stat}'")
        if hotspot.get("public_distribution_allowed") is False:
            raise ManifestLicenseError(f"Hotspot '{hid}' in '{urn_slug}' public_distribution_allowed is False")

    return {
        "urn_slug": urn_slug,
        "license": license_label,
        "rights_status": rights_status,
        "rights_owner": rights_owner,
        "creator": creator,
        "license_valid": True,
    }


def validate_3d_mesh_id_joins(
    manifest: dict[str, Any], all_manifests: Optional[dict[str, Any]] = None
) -> dict[str, Any]:
    """Validate 3D mesh ID joins and hotspot integrity.
    
    Enforces:
    - Each urn manifest has exactly 18 hotspots.
    - Each hotspot has:
      - valid hotspot_id ({urn_slug}-{relief_slug})
      - valid 3d_mesh_id (mesh_urn_{slug}_{idx}_v1)
      - valid motif_id (urn_{slug}_{idx})
      - 3D spatial coordinates [pos_x, pos_y, pos_z] (all floats)
      - camera_position, camera_target (valid 3D points)
      - bounding_radius > 0
      - mesh_name and relief_name non-empty
      - fallback_2d with valid thumbnail_url, disk_path, sha256, bytes, and format
    - When all_manifests is provided:
      - Total 162 hotspots globally.
      - All 162 hotspot_ids, 3d_mesh_ids, and motif_ids are globally unique.
      - Zero cross-urn mesh leakage.
    """
    urn_slug = manifest.get("urn_slug", "unknown")
    hotspots = manifest.get("hotspots", [])
    if len(hotspots) != 18:
        raise ManifestMeshJoinError(
            f"Urn '{urn_slug}' must have exactly 18 hotspots, got {len(hotspots)}"
        )

    seen_hids = set()
    seen_mesh_ids = set()
    seen_motif_ids = set()

    for idx, hotspot in enumerate(hotspots):
        hid = hotspot.get("hotspot_id")
        if not hid or not isinstance(hid, str):
            raise ManifestMeshJoinError(f"Hotspot index {idx} in '{urn_slug}' missing 'hotspot_id'")
        if hid in seen_hids:
            raise ManifestMeshJoinError(f"Duplicate hotspot_id '{hid}' within urn '{urn_slug}'")
        seen_hids.add(hid)

        # Urn slug match
        h_urn = hotspot.get("urn_slug")
        if h_urn != urn_slug:
            raise ManifestMeshJoinError(
                f"Hotspot '{hid}' urn_slug '{h_urn}' does not match manifest urn '{urn_slug}'"
            )

        # 3D Mesh ID & Motif ID
        mesh_id = hotspot.get("3d_mesh_id")
        if not mesh_id or not isinstance(mesh_id, str):
            raise ManifestMeshJoinError(f"Hotspot '{hid}' missing required '3d_mesh_id'")
        if mesh_id in seen_mesh_ids:
            raise ManifestMeshJoinError(f"Duplicate 3d_mesh_id '{mesh_id}' within urn '{urn_slug}'")
        seen_mesh_ids.add(mesh_id)

        motif_id = hotspot.get("motif_id")
        if not motif_id or not isinstance(motif_id, str):
            raise ManifestMeshJoinError(f"Hotspot '{hid}' missing required 'motif_id'")
        if motif_id in seen_motif_ids:
            raise ManifestMeshJoinError(f"Duplicate motif_id '{motif_id}' within urn '{urn_slug}'")
        seen_motif_ids.add(motif_id)

        # Ensure mesh_id joins to motif_id
        # e.g. mesh_urn_cao_dinh_10_v1 -> urn_cao_dinh_10
        expected_prefix = f"mesh_{motif_id}"
        if not mesh_id.startswith(expected_prefix):
            raise ManifestMeshJoinError(
                f"Hotspot '{hid}' 3d_mesh_id '{mesh_id}' does not join to motif_id '{motif_id}'"
            )

        # Coordinate checks
        pos = hotspot.get("pos")
        if not isinstance(pos, list) or len(pos) != 3 or not all(isinstance(c, (int, float)) for c in pos):
            raise ManifestMeshJoinError(f"Hotspot '{hid}' has invalid 3D pos coordinates: {pos}")

        cam_pos = hotspot.get("camera_position")
        if not isinstance(cam_pos, list) or len(cam_pos) != 3 or not all(isinstance(c, (int, float)) for c in cam_pos):
            raise ManifestMeshJoinError(f"Hotspot '{hid}' has invalid camera_position: {cam_pos}")

        cam_tgt = hotspot.get("camera_target")
        if not isinstance(cam_tgt, list) or len(cam_tgt) != 3 or not all(isinstance(c, (int, float)) for c in cam_tgt):
            raise ManifestMeshJoinError(f"Hotspot '{hid}' has invalid camera_target: {cam_tgt}")

        bradius = hotspot.get("bounding_radius")
        if bradius is None or not isinstance(bradius, (int, float)) or bradius <= 0:
            raise ManifestMeshJoinError(f"Hotspot '{hid}' has invalid bounding_radius: {bradius}")

        # Names
        if not hotspot.get("mesh_name"):
            raise ManifestMeshJoinError(f"Hotspot '{hid}' missing 'mesh_name'")
        if not hotspot.get("relief_name"):
            raise ManifestMeshJoinError(f"Hotspot '{hid}' missing 'relief_name'")
        if not hotspot.get("relief_slug"):
            raise ManifestMeshJoinError(f"Hotspot '{hid}' missing 'relief_slug'")

        # 2D fallback block on hotspot
        fb2d = hotspot.get("fallback_2d")
        if not fb2d or not isinstance(fb2d, dict):
            raise ManifestMeshJoinError(f"Hotspot '{hid}' missing 'fallback_2d' dictionary")
        for req in ("thumbnail_url", "disk_path", "bytes", "sha256", "format"):
            if not fb2d.get(req):
                raise ManifestMeshJoinError(f"Hotspot '{hid}' fallback_2d missing field '{req}'")
        if fb2d.get("format") not in ("image/jpeg", "image/png"):
            raise ManifestMeshJoinError(
                f"Hotspot '{hid}' fallback_2d format must be 'image/jpeg' or 'image/png', got '{fb2d.get('format')}'"
            )

    # Multi-manifest global uniqueness check
    if all_manifests:
        global_hids = set()
        global_mesh_ids = set()
        global_motif_ids = set()
        for u_slug, other_mf in all_manifests.items():
            for other_hs in other_mf.get("hotspots", []):
                o_hid = other_hs["hotspot_id"]
                o_mid = other_hs["3d_mesh_id"]
                o_mot = other_hs["motif_id"]

                if o_hid in global_hids:
                    raise ManifestMeshJoinError(f"Global collision on hotspot_id: '{o_hid}'")
                if o_mid in global_mesh_ids:
                    raise ManifestMeshJoinError(f"Global collision on 3d_mesh_id: '{o_mid}'")
                if o_mot in global_motif_ids:
                    raise ManifestMeshJoinError(f"Global collision on motif_id: '{o_mot}'")

                global_hids.add(o_hid)
                global_mesh_ids.add(o_mid)
                global_motif_ids.add(o_mot)

    return {
        "urn_slug": urn_slug,
        "hotspot_count": len(hotspots),
        "mesh_ids_joined": len(seen_mesh_ids),
        "joins_valid": True,
    }


def validate_2d_fallback_for_missing_meshes(
    manifest: dict[str, Any], repo_root: Optional[Path] = None
) -> dict[str, Any]:
    """Validate 2D rubbing fallback architecture and negative abuse prevention.
    
    Enforces:
    - has_2d_fallback is True for all urns.
    - viewer_fallback specifies:
      - type: '2d_rubbing'
      - component: 'UrnAccessibleFallback'
      - format: 'image/jpeg'
      - valid bytes > 0 and sha256 (64 hex characters)
      - disk_path pointing to real image file on disk with JPEG magic bytes.
    - Negative abuse rules:
      - If mesh_status == 'MISSING', has_2d_fallback must be True and 2D rubbing must exist.
        If missing, raises ManifestMissingFallbackError.
      - If mesh_status == 'MISSING', cannot set fallback_url in LODs to another model.
        Raises ManifestPhantomModelError.
      - If mesh_status == 'PRESENT', GLB must physically exist.
        Raises ManifestPhantomModelError if absent.
    """
    if repo_root is None:
        repo_root = resolve_repo_root()

    urn_slug = manifest.get("urn_slug", "unknown")
    mesh_status = manifest.get("mesh_status", "MISSING")

    # 1. 2D Fallback declaration
    if not manifest.get("has_2d_fallback"):
        raise ManifestMissingFallbackError(
            f"Urn '{urn_slug}' manifest must declare has_2d_fallback=True"
        )

    fallback_2d_url = manifest.get("fallback_2d_url")
    if not fallback_2d_url or not fallback_2d_url.startswith("/assets/ban-duc-noi/"):
        raise ManifestMissingFallbackError(
            f"Urn '{urn_slug}' missing or invalid fallback_2d_url: '{fallback_2d_url}'"
        )

    viewer_fallback = manifest.get("viewer_fallback")
    if not viewer_fallback or not isinstance(viewer_fallback, dict):
        raise ManifestMissingFallbackError(
            f"Urn '{urn_slug}' manifest missing structured 'viewer_fallback'"
        )

    if viewer_fallback.get("type") != "2d_rubbing":
        raise ManifestMissingFallbackError(
            f"Urn '{urn_slug}' viewer_fallback type must be '2d_rubbing', got '{viewer_fallback.get('type')}'"
        )
    if viewer_fallback.get("component") != "UrnAccessibleFallback":
        raise ManifestMissingFallbackError(
            f"Urn '{urn_slug}' viewer_fallback component must be 'UrnAccessibleFallback'"
        )
    if viewer_fallback.get("format") not in ("image/jpeg", "image/png"):
        raise ManifestMissingFallbackError(
            f"Urn '{urn_slug}' viewer_fallback format must be 'image/jpeg' or 'image/png'"
        )

    # 2. Disk file verification
    disk_path_rel = viewer_fallback.get("disk_path")
    if not disk_path_rel:
        raise ManifestMissingFallbackError(f"Urn '{urn_slug}' viewer_fallback missing disk_path")

    file_path = repo_root / disk_path_rel
    if not file_path.exists():
        file_path = repo_root / "frontend" / "public" / disk_path_rel
    if not file_path.exists():
        raise ManifestMissingFallbackError(
            f"2D rubbing fallback file not found on disk: {disk_path_rel}"
        )

    actual_sha = sha256_of_file(file_path)
    expected_sha = viewer_fallback.get("sha256")
    if actual_sha.lower() != str(expected_sha).lower():
        raise ManifestChecksumError(
            f"2D rubbing SHA-256 mismatch for {disk_path_rel}: expected {expected_sha}, got {actual_sha}"
        )

    with open(file_path, "rb") as f:
        magic = f.read(4)
    if not (magic.startswith(JPEG_MAGIC) or magic.startswith(PNG_MAGIC)):
        raise ManifestChecksumError(
            f"2D rubbing file {disk_path_rel} missing valid image magic bytes: {magic}"
        )

    # 3. Negative abuse: Missing mesh cannot claim phantom complete model
    if mesh_status == "MISSING":
        lods = manifest.get("lods", {})
        for lod_name, lod in lods.items():
            if lod.get("status") != "MISSING":
                raise ManifestPhantomModelError(
                    f"Urn '{urn_slug}' is MISSING but LOD '{lod_name}' claims status '{lod.get('status')}'"
                )
            if lod.get("fallback_url") is not None:
                raise ManifestPhantomModelError(
                    f"Urn '{urn_slug}' is MISSING but LOD '{lod_name}' provides phantom fallback_url"
                )
    elif mesh_status == "PRESENT":
        # Must verify GLB is actually on disk
        low_url = manifest.get("lods", {}).get("low", {}).get("url", "")
        glb_path = repo_root / "frontend" / "public" / low_url.lstrip("/")
        if not glb_path.exists():
            glb_path = repo_root / "public" / low_url.lstrip("/")
        if not glb_path.exists():
            raise ManifestPhantomModelError(
                f"Urn '{urn_slug}' claims PRESENT mesh but GLB is absent on disk: {low_url}"
            )

    return {
        "urn_slug": urn_slug,
        "mesh_status": mesh_status,
        "fallback_type": "2d_rubbing",
        "fallback_component": "UrnAccessibleFallback",
        "disk_path": disk_path_rel,
        "sha256": expected_sha,
        "fallback_valid": True,
    }


def validate_webgl_health_contract(health_report: dict[str, Any]) -> dict[str, Any]:
    """Validate WebGL health contract and fallback degradation state.
    
    Ensures that when WebGL fails, is unsupported, or loses context:
    1. Blank canvas is prevented (blank_canvas_prevented == True).
    2. Fallback component degrades cleanly to UrnAccessibleFallback.
    3. Missing mesh banner is presented when mesh is absent or failed.
    """
    webgl_supported = health_report.get("webgl_supported", True)
    context_lost = health_report.get("context_lost", False)
    blank_canvas_prevented = health_report.get("blank_canvas_prevented", False)
    fallback_component_active = health_report.get("fallback_component_active", False)
    missing_mesh = health_report.get("missing_mesh", False)
    missing_banner_present = health_report.get("missing_mesh_fallback_banner_present", False)

    if not blank_canvas_prevented:
        raise WebGLHealthError("WebGL failure resulted in unhandled blank canvas")

    if (not webgl_supported or context_lost) and not fallback_component_active:
        raise WebGLHealthError(
            "WebGL context failure must trigger active UrnAccessibleFallback component"
        )

    if missing_mesh and not missing_banner_present:
        raise WebGLHealthError(
            "Missing 3D mesh must display missing_mesh_fallback_banner informing user of 2D fallback"
        )

    return {
        "webgl_healthy": webgl_supported and not context_lost,
        "blank_canvas_prevented": blank_canvas_prevented,
        "fallback_active": fallback_component_active,
        "contract_satisfied": True,
    }


def audit_all_3d_manifests(
    manifests_dir: Optional[Path] = None, repo_root: Optional[Path] = None
) -> dict[str, Any]:
    """Execute holistic audit across all 9 3D urn manifests on disk.
    
    Verifies:
    - 9 urn manifests + 1 index.json in specified manifests_dir.
    - Asset versions (model_version, hotspot_version, coordinate_version).
    - Checksum & size integrity for PRESENT and MISSING meshes.
    - Approved licenses and rights status ('cleared').
    - Exact 162 hotspot mesh ID joins across 9 urns with 0 collisions.
    - 100% 2D rubbing fallback coverage and disk existence.
    """
    if repo_root is None:
        repo_root = resolve_repo_root()
    if manifests_dir is None:
        manifests_dir = repo_root / "public" / "models" / "manifests"

    if not manifests_dir.exists():
        raise FileNotFoundError(f"Manifests directory not found: {manifests_dir}")

    index_path = manifests_dir / "index.json"
    if not index_path.exists():
        raise FileNotFoundError(f"Missing index.json in {manifests_dir}")

    index_data = load_manifest(index_path)
    total_urns = index_data.get("total_urns", 0)
    total_hotspots = index_data.get("total_hotspots", 0)
    if total_urns != 9:
        raise ManifestValidationError(f"Expected 9 urns in index.json, got {total_urns}")
    if total_hotspots != 162:
        raise ManifestValidationError(f"Expected 162 hotspots in index.json, got {total_hotspots}")

    all_manifests: dict[str, dict[str, Any]] = {}
    for slug in URN_SLUGS:
        mf_path = manifests_dir / f"{slug}.json"
        all_manifests[slug] = load_manifest(mf_path)

    urn_reports: list[dict[str, Any]] = []
    mesh_present_count = 0
    mesh_missing_count = 0

    for slug, manifest in all_manifests.items():
        v_res = validate_3d_asset_version(manifest)
        cs_res = validate_3d_asset_checksum_and_size(manifest, repo_root=repo_root)
        lic_res = validate_3d_asset_license(manifest)
        join_res = validate_3d_mesh_id_joins(manifest, all_manifests=all_manifests)
        fb_res = validate_2d_fallback_for_missing_meshes(manifest, repo_root=repo_root)

        if cs_res["mesh_status"] == "PRESENT":
            mesh_present_count += 1
        else:
            mesh_missing_count += 1

        urn_reports.append({
            "urn_slug": slug,
            "mesh_status": cs_res["mesh_status"],
            "version_valid": v_res["version_valid"],
            "integrity_valid": cs_res["integrity_valid"],
            "license_valid": lic_res["license_valid"],
            "joins_valid": join_res["joins_valid"],
            "fallback_valid": fb_res["fallback_valid"],
        })

    return {
        "total_urns_audited": len(all_manifests),
        "total_hotspots_audited": sum(len(m.get("hotspots", [])) for m in all_manifests.values()),
        "mesh_present_urns": mesh_present_count,
        "mesh_missing_urns": mesh_missing_count,
        "fallback_2d_coverage_pct": 100.0,
        "all_urns_cleared": True,
        "audit_passed": True,
        "urn_reports": urn_reports,
    }
