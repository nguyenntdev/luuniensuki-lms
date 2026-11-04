# -*- coding: utf-8 -*-
"""V5-T041: 3D Asset Manifest Validation in public/models/ and frontend/src/components/UrnViewer.tsx.

Wave W04, Slot A01 / Priority: P1 / Classification: PRODUCTION_COMPLETION.

Verifies:
1. 3D Asset Version Validation:
   - model_version, hotspot_version, coordinate_version (integers >= 1).
   - Negative abuse: Missing or non-positive versions fail closed.
2. Checksum and Size Validation:
   - Cryptographic SHA-256 integrity (64 hex characters).
   - Physical disk match for PRESENT meshes (Cao Đỉnh LODs: 512, 1k, 2k).
   - Null hash and bytes=0 for MISSING meshes, preventing phantom/fake assertions.
   - glTF binary magic bytes verification (b"glTF").
   - Negative abuse: Tampered hashes, altered file sizes, or corrupted magic bytes fail closed.
3. License and Rights Clearance:
   - Approved licenses (CC BY 4.0 / Educational Fair Use).
   - Institutional rights owner (HMCC) and creator attribution.
   - Negative abuse: Restricted/proprietary licenses, revoked rights status, or disallowed
     distribution fail closed.
4. Mesh ID Joins and Spatial Hotspots:
   - Exactly 162 hotspots across 9 urns (18 per urn).
   - Globally unique 3d_mesh_id (mesh_urn_{slug}_{idx}_v1), motif_id (urn_{slug}_{idx}),
     and hotspot_id ({slug}-{relief_slug}).
   - Full join integrity without cross-urn leakage.
   - Negative abuse: Orphan meshes, cross-urn ID mismatches, and duplicates fail closed.
5. 2D Fallback for Missing Meshes:
   - 100% 2D rubbing fallback coverage (ban-duc-noi/ & UrnAccessibleFallback).
   - Negative abuse: Missing mesh does not show blank canvas or claim complete model
     without fallback.
   - Negative abuse: Urn with missing mesh cannot substitute another urn's 3D model.
6. WebGL Health Contract & UrnViewer.tsx Integration:
   - WebGL context loss and creation failures gracefully degrade to UrnAccessibleFallback.
   - Missing mesh fallback banner prevents claiming complete 3D digital twins.
   - Zero blank canvas invariant.
7. Holistic 3D Manifest Audit:
   - Complete audit across public/models/manifests/ and frontend/public/models/manifests/.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from backend.history_models import (
    APPROVED_LICENSES,
    APPROVED_RIGHTS_STATUSES,
    DEFAULT_CREATOR,
    DEFAULT_RIGHTS_OWNER,
    GLB_MAGIC,
    JPEG_MAGIC,
    PNG_MAGIC,
    RESTRICTED_RIGHTS_STATUSES,
    URN_SLUGS,
    ManifestChecksumError,
    ManifestLicenseError,
    ManifestMeshJoinError,
    ManifestMissingFallbackError,
    ManifestPhantomModelError,
    ManifestSizeError,
    ManifestValidationError,
    ManifestVersionError,
    WebGLHealthError,
    audit_all_3d_manifests,
    load_manifest,
    validate_2d_fallback_for_missing_meshes,
    validate_3d_asset_checksum_and_size,
    validate_3d_asset_license,
    validate_3d_asset_version,
    validate_3d_mesh_id_joins,
    validate_webgl_health_contract,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
PUBLIC_MANIFESTS_DIR = REPO_ROOT / "public" / "models" / "manifests"
FRONTEND_MANIFESTS_DIR = REPO_ROOT / "frontend" / "public" / "models" / "manifests"
URN_VIEWER_TSX = REPO_ROOT / "frontend" / "src" / "components" / "UrnViewer.tsx"


# ==============================================================================
# 1. 3D Asset Version Validation Tests
# ==============================================================================


def test_all_9_urn_manifests_version_validity():
    """Verify that all 9 urn manifests have valid model_version and hotspot_version."""
    for m_dir in [PUBLIC_MANIFESTS_DIR, FRONTEND_MANIFESTS_DIR]:
        assert m_dir.exists(), f"Directory missing: {m_dir}"
        for slug in URN_SLUGS:
            mf = load_manifest(m_dir / f"{slug}.json")
            res = validate_3d_asset_version(mf)
            assert res["version_valid"] is True
            assert res["model_version"] >= 1
            assert res["hotspot_version"] >= 1
            assert res["hotspot_count"] == 18


def test_negative_invalid_or_missing_version_fails():
    """Negative abuse: Non-positive or missing model_version / hotspot_version fails closed."""
    valid_mf = load_manifest(PUBLIC_MANIFESTS_DIR / "cao-dinh.json")

    # Missing model_version
    bad_mf1 = copy.deepcopy(valid_mf)
    del bad_mf1["model_version"]
    with pytest.raises(ManifestVersionError, match="missing or invalid model_version"):
        validate_3d_asset_version(bad_mf1)

    # model_version = 0
    bad_mf2 = copy.deepcopy(valid_mf)
    bad_mf2["model_version"] = 0
    with pytest.raises(ManifestVersionError, match="missing or invalid model_version"):
        validate_3d_asset_version(bad_mf2)

    # Negative model_version
    bad_mf3 = copy.deepcopy(valid_mf)
    bad_mf3["model_version"] = -1
    with pytest.raises(ManifestVersionError, match="missing or invalid model_version"):
        validate_3d_asset_version(bad_mf3)

    # Missing hotspot_version
    bad_mf4 = copy.deepcopy(valid_mf)
    bad_mf4["hotspot_version"] = None
    with pytest.raises(ManifestVersionError, match="missing or invalid hotspot_version"):
        validate_3d_asset_version(bad_mf4)


def test_negative_hotspot_version_missing_fails():
    """Negative abuse: Hotspot with missing or zero coordinate_version fails closed."""
    valid_mf = load_manifest(PUBLIC_MANIFESTS_DIR / "anh-dinh.json")

    bad_mf = copy.deepcopy(valid_mf)
    bad_mf["hotspots"][0]["coordinate_version"] = 0
    with pytest.raises(ManifestVersionError, match="missing or invalid coordinate_version"):
        validate_3d_asset_version(bad_mf)

    bad_mf2 = copy.deepcopy(valid_mf)
    bad_mf2["hotspots"][0]["model_version"] = None
    with pytest.raises(ManifestVersionError, match="missing or invalid model_version"):
        validate_3d_asset_version(bad_mf2)


# ==============================================================================
# 2. Checksum and Size Validation Tests
# ==============================================================================


def test_cao_dinh_mesh_present_checksum_and_size_integrity():
    """Verify Cao Đỉnh PRESENT mesh checksums, byte sizes, and physical disk match."""
    mf = load_manifest(PUBLIC_MANIFESTS_DIR / "cao-dinh.json")
    res = validate_3d_asset_checksum_and_size(mf, repo_root=REPO_ROOT)
    assert res["integrity_valid"] is True
    assert res["mesh_status"] == "PRESENT"
    assert len(res["root_checksum"]) == 64
    assert set(res["lods_verified"]) == {"low", "medium", "high"}

    # Verify actual GLB file headers
    for lod_name in ("low", "medium", "high"):
        url = mf["lods"][lod_name]["url"]
        glb_file = REPO_ROOT / "frontend" / "public" / url.lstrip("/")
        assert glb_file.exists()
        assert glb_file.stat().st_size == mf["lods"][lod_name]["bytes"]
        with open(glb_file, "rb") as gf:
            assert gf.read(4) == GLB_MAGIC


def test_missing_mesh_urns_declare_zero_bytes_and_null_hash():
    """Verify the 8 missing urns declare status MISSING, bytes=0, and null sha256."""
    for slug in URN_SLUGS:
        if slug == "cao-dinh":
            continue
        mf = load_manifest(PUBLIC_MANIFESTS_DIR / f"{slug}.json")
        res = validate_3d_asset_checksum_and_size(mf, repo_root=REPO_ROOT)
        assert res["integrity_valid"] is True
        assert res["mesh_status"] == "MISSING"

        for lod_name in ("low", "medium", "high"):
            lod = mf["lods"][lod_name]
            assert lod["status"] == "MISSING"
            assert lod["bytes"] == 0
            assert lod["sha256"] is None
            assert lod["fallback_url"] is None


def test_negative_checksum_tampering_rejected():
    """Negative abuse: Tampering with manifest root checksum or LOD sha256 fails closed."""
    mf = load_manifest(PUBLIC_MANIFESTS_DIR / "cao-dinh.json")

    # Corrupted root checksum
    bad_mf1 = copy.deepcopy(mf)
    bad_mf1["checksum"] = "badhash1234"
    with pytest.raises(ManifestChecksumError, match="missing or invalid SHA-256"):
        validate_3d_asset_checksum_and_size(bad_mf1, repo_root=REPO_ROOT)

    # Tampered root checksum with valid length but fake characters
    bad_mf2 = copy.deepcopy(mf)
    bad_mf2["checksum"] = "z" * 64
    with pytest.raises(ManifestChecksumError, match="invalid hex characters"):
        validate_3d_asset_checksum_and_size(bad_mf2, repo_root=REPO_ROOT)

    # Tampered LOD sha256
    bad_mf3 = copy.deepcopy(mf)
    bad_mf3["lods"]["low"]["sha256"] = "0" * 64
    with pytest.raises(ManifestChecksumError, match="sha256 mismatch"):
        validate_3d_asset_checksum_and_size(bad_mf3, repo_root=REPO_ROOT)


def test_negative_size_tampering_rejected():
    """Negative abuse: Tampering with declared byte sizes fails closed."""
    mf = load_manifest(PUBLIC_MANIFESTS_DIR / "cao-dinh.json")

    # LOD bytes mismatch
    bad_mf = copy.deepcopy(mf)
    bad_mf["lods"]["low"]["bytes"] = 12345
    with pytest.raises(ManifestSizeError, match="size mismatch"):
        validate_3d_asset_checksum_and_size(bad_mf, repo_root=REPO_ROOT)

    # Missing mesh declaring non-zero bytes
    missing_mf = load_manifest(PUBLIC_MANIFESTS_DIR / "nhan-dinh.json")
    bad_missing = copy.deepcopy(missing_mf)
    bad_missing["lods"]["low"]["bytes"] = 5000000
    with pytest.raises(ManifestSizeError, match="declares non-zero LOD bytes"):
        validate_3d_asset_checksum_and_size(bad_missing, repo_root=REPO_ROOT)


# ==============================================================================
# 3. License and Rights Clearance Tests
# ==============================================================================


def test_all_9_urns_and_162_hotspots_have_approved_licenses():
    """Verify all 9 urns and all 162 hotspots have valid license and cleared rights."""
    for slug in URN_SLUGS:
        mf = load_manifest(PUBLIC_MANIFESTS_DIR / f"{slug}.json")
        res = validate_3d_asset_license(mf)
        assert res["license_valid"] is True
        assert res["license"] in APPROVED_LICENSES
        assert res["rights_status"] == "cleared"
        assert res["rights_owner"] == DEFAULT_RIGHTS_OWNER
        assert res["creator"] == DEFAULT_CREATOR


def test_negative_unapproved_or_missing_license_fails_closed():
    """Negative abuse: Missing or proprietary license fails closed."""
    mf = load_manifest(PUBLIC_MANIFESTS_DIR / "cao-dinh.json")

    bad_mf1 = copy.deepcopy(mf)
    bad_mf1["license"] = None
    with pytest.raises(ManifestLicenseError, match="missing required license"):
        validate_3d_asset_license(bad_mf1)

    bad_mf2 = copy.deepcopy(mf)
    bad_mf2["license"] = "Proprietary Commercial All Rights Reserved"
    with pytest.raises(ManifestLicenseError, match="restricted/proprietary license"):
        validate_3d_asset_license(bad_mf2)


def test_negative_restricted_or_revoked_rights_fails_closed():
    """Negative abuse: Revoked or restricted rights status fails closed."""
    mf = load_manifest(PUBLIC_MANIFESTS_DIR / "anh-dinh.json")

    for stat in ["revoked", "withdrawn", "restricted", "disputed"]:
        bad_mf = copy.deepcopy(mf)
        bad_mf["rights_status"] = stat
        with pytest.raises(ManifestLicenseError, match="rights_status is restricted or revoked"):
            validate_3d_asset_license(bad_mf)


def test_negative_disallowed_distribution_fails_closed():
    """Negative abuse: Disallowed public distribution or display fails closed."""
    mf = load_manifest(PUBLIC_MANIFESTS_DIR / "du-dinh.json")

    bad_mf1 = copy.deepcopy(mf)
    bad_mf1["public_distribution_allowed"] = False
    with pytest.raises(ManifestLicenseError, match="public_distribution_allowed is not True"):
        validate_3d_asset_license(bad_mf1)

    bad_mf2 = copy.deepcopy(mf)
    bad_mf2["public_display_allowed"] = False
    with pytest.raises(ManifestLicenseError, match="public_display_allowed is not True"):
        validate_3d_asset_license(bad_mf2)


# ==============================================================================
# 4. Mesh ID Joins and Spatial Hotspots Tests
# ==============================================================================


def test_exact_162_hotspots_across_9_urns():
    """Verify that each of the 9 urn manifests contains exactly 18 hotspots."""
    total_hotspots = 0
    for slug in URN_SLUGS:
        mf = load_manifest(PUBLIC_MANIFESTS_DIR / f"{slug}.json")
        res = validate_3d_mesh_id_joins(mf)
        assert res["joins_valid"] is True
        assert res["hotspot_count"] == 18
        assert res["mesh_ids_joined"] == 18
        total_hotspots += res["hotspot_count"]
    assert total_hotspots == 162


def test_global_uniqueness_of_mesh_ids_and_motif_ids():
    """Verify that all 162 3d_mesh_ids, motif_ids, and hotspot_ids are globally unique."""
    all_manifests = {
        slug: load_manifest(PUBLIC_MANIFESTS_DIR / f"{slug}.json")
        for slug in URN_SLUGS
    }

    # Cross-manifest join verification
    for slug, mf in all_manifests.items():
        res = validate_3d_mesh_id_joins(mf, all_manifests=all_manifests)
        assert res["joins_valid"] is True

    # Aggregate check
    all_mesh_ids = set()
    all_motif_ids = set()
    all_hids = set()
    for mf in all_manifests.values():
        for hs in mf["hotspots"]:
            all_mesh_ids.add(hs["3d_mesh_id"])
            all_motif_ids.add(hs["motif_id"])
            all_hids.add(hs["hotspot_id"])

    assert len(all_mesh_ids) == 162
    assert len(all_motif_ids) == 162
    assert len(all_hids) == 162


def test_mesh_id_joins_to_motif_id():
    """Verify that every 3d_mesh_id cleanly maps to its parent motif_id."""
    for slug in URN_SLUGS:
        mf = load_manifest(PUBLIC_MANIFESTS_DIR / f"{slug}.json")
        for hs in mf["hotspots"]:
            mesh_id = hs["3d_mesh_id"]
            motif_id = hs["motif_id"]
            assert mesh_id.startswith(f"mesh_{motif_id}"), (
                f"Mismatch: mesh_id {mesh_id} does not map to motif_id {motif_id}"
            )


def test_hotspot_3d_coordinates_validity():
    """Verify that all 162 hotspots have valid 3D floats for pos, camera_position, and camera_target."""
    for slug in URN_SLUGS:
        mf = load_manifest(PUBLIC_MANIFESTS_DIR / f"{slug}.json")
        for hs in mf["hotspots"]:
            for field in ("pos", "camera_position", "camera_target"):
                coords = hs[field]
                assert isinstance(coords, list) and len(coords) == 3
                assert all(isinstance(c, (int, float)) for c in coords)
            assert hs["bounding_radius"] > 0


def test_negative_mesh_id_cross_urn_mismatch_rejected():
    """Negative abuse: Hotspot with mismatched 3d_mesh_id or motif_id is rejected."""
    mf = load_manifest(PUBLIC_MANIFESTS_DIR / "anh-dinh.json")
    bad_mf = copy.deepcopy(mf)

    # Infiltrate a Cao Đỉnh mesh ID into Anh Đỉnh hotspot
    bad_mf["hotspots"][0]["3d_mesh_id"] = "mesh_urn_cao_dinh_10_v1"
    with pytest.raises(ManifestMeshJoinError, match="does not join to motif_id"):
        validate_3d_mesh_id_joins(bad_mf)


def test_negative_duplicate_hotspot_or_missing_mesh_id_rejected():
    """Negative abuse: Duplicate hotspot ID or missing 3d_mesh_id fails closed."""
    mf = load_manifest(PUBLIC_MANIFESTS_DIR / "tuyen-dinh.json")

    # Duplicate hotspot_id
    bad_mf1 = copy.deepcopy(mf)
    bad_mf1["hotspots"][1]["hotspot_id"] = bad_mf1["hotspots"][0]["hotspot_id"]
    with pytest.raises(ManifestMeshJoinError, match="Duplicate hotspot_id"):
        validate_3d_mesh_id_joins(bad_mf1)

    # Missing 3d_mesh_id
    bad_mf2 = copy.deepcopy(mf)
    bad_mf2["hotspots"][0]["3d_mesh_id"] = ""
    with pytest.raises(ManifestMeshJoinError, match="missing required '3d_mesh_id'"):
        validate_3d_mesh_id_joins(bad_mf2)


# ==============================================================================
# 5. 2D Fallback for Missing Meshes Tests
# ==============================================================================


def test_all_9_urns_have_verified_2d_rubbing_fallback():
    """Verify that all 9 urn manifests have 100% verified 2D rubbing fallback."""
    for slug in URN_SLUGS:
        mf = load_manifest(PUBLIC_MANIFESTS_DIR / f"{slug}.json")
        res = validate_2d_fallback_for_missing_meshes(mf, repo_root=REPO_ROOT)
        assert res["fallback_valid"] is True
        assert res["fallback_type"] == "2d_rubbing"
        assert res["fallback_component"] == "UrnAccessibleFallback"
        assert len(res["sha256"]) == 64


def test_negative_missing_mesh_without_2d_fallback_fails_closed():
    """Negative abuse: Missing mesh without declared 2D fallback fails closed."""
    mf = load_manifest(PUBLIC_MANIFESTS_DIR / "huyen-dinh.json")

    bad_mf = copy.deepcopy(mf)
    bad_mf["has_2d_fallback"] = False
    with pytest.raises(ManifestMissingFallbackError, match="must declare has_2d_fallback=True"):
        validate_2d_fallback_for_missing_meshes(bad_mf, repo_root=REPO_ROOT)


def test_negative_missing_mesh_cannot_claim_phantom_model():
    """Negative abuse: Missing mesh urn cannot substitute another urn's 3D model."""
    mf = load_manifest(PUBLIC_MANIFESTS_DIR / "nghi-dinh.json")

    # Attempt phantom substitution
    bad_mf = copy.deepcopy(mf)
    bad_mf["lods"]["low"]["fallback_url"] = "/assets/models/CAO-DINH-v1-512.glb"
    with pytest.raises(ManifestPhantomModelError, match="phantom fallback_url"):
        validate_2d_fallback_for_missing_meshes(bad_mf, repo_root=REPO_ROOT)


def test_negative_present_mesh_without_disk_file_fails_phantom_check():
    """Negative abuse: Claiming PRESENT mesh when GLB is physically missing fails closed."""
    mf = load_manifest(PUBLIC_MANIFESTS_DIR / "thuan-dinh.json")

    # Falsely claim Thuần Đỉnh has PRESENT mesh
    bad_mf = copy.deepcopy(mf)
    bad_mf["mesh_status"] = "PRESENT"
    bad_mf["lods"]["low"]["status"] = "PRESENT"
    bad_mf["lods"]["low"]["url"] = "/assets/models/NON-EXISTENT-MODEL.glb"
    bad_mf["lods"]["low"]["bytes"] = 12345
    bad_mf["lods"]["low"]["sha256"] = "1" * 64

    with pytest.raises(ManifestPhantomModelError, match="GLB is absent on disk"):
        validate_2d_fallback_for_missing_meshes(bad_mf, repo_root=REPO_ROOT)


# ==============================================================================
# 6. WebGL Health Contract & UrnViewer.tsx Source Code Integration Tests
# ==============================================================================


def test_webgl_health_contract_graceful_degradation():
    """Verify that WebGL health contract enforces fallback and prevents blank canvas."""
    # Scenario A: Healthy WebGL
    healthy = validate_webgl_health_contract({
        "webgl_supported": True,
        "context_lost": False,
        "blank_canvas_prevented": True,
        "fallback_component_active": False,
        "missing_mesh": False,
    })
    assert healthy["webgl_healthy"] is True
    assert healthy["contract_satisfied"] is True

    # Scenario B: WebGL context lost -> degrades cleanly to accessible fallback
    degraded = validate_webgl_health_contract({
        "webgl_supported": True,
        "context_lost": True,
        "blank_canvas_prevented": True,
        "fallback_component_active": True,
        "missing_mesh": False,
    })
    assert degraded["webgl_healthy"] is False
    assert degraded["fallback_active"] is True
    assert degraded["contract_satisfied"] is True

    # Scenario C: Missing 3D mesh -> fallback banner active, no blank canvas
    missing_mesh_ok = validate_webgl_health_contract({
        "webgl_supported": True,
        "context_lost": False,
        "blank_canvas_prevented": True,
        "fallback_component_active": False,
        "missing_mesh": True,
        "missing_mesh_fallback_banner_present": True,
    })
    assert missing_mesh_ok["contract_satisfied"] is True


def test_negative_webgl_failure_without_fallback_rejected():
    """Negative abuse: WebGL failure without active fallback component fails closed."""
    with pytest.raises(WebGLHealthError, match="unhandled blank canvas"):
        validate_webgl_health_contract({
            "webgl_supported": False,
            "blank_canvas_prevented": False,
        })

    with pytest.raises(WebGLHealthError, match="must trigger active UrnAccessibleFallback"):
        validate_webgl_health_contract({
            "webgl_supported": False,
            "blank_canvas_prevented": True,
            "fallback_component_active": False,
        })


def test_negative_missing_mesh_without_banner_rejected():
    """Negative abuse: Missing mesh without fallback banner fails contract."""
    with pytest.raises(WebGLHealthError, match="must display missing_mesh_fallback_banner"):
        validate_webgl_health_contract({
            "webgl_supported": True,
            "context_lost": False,
            "blank_canvas_prevented": True,
            "missing_mesh": True,
            "missing_mesh_fallback_banner_present": False,
        })


def test_urn_viewer_source_code_verifies_webgl_health_and_fallback():
    """Verify frontend/src/components/UrnViewer.tsx source code handles WebGL loss and 2D fallback."""
    assert URN_VIEWER_TSX.exists(), f"UrnViewer.tsx missing at {URN_VIEWER_TSX}"
    code = URN_VIEWER_TSX.read_text(encoding="utf-8")

    # 1. WebGL context loss handling
    assert "webglcontextlost" in code, "UrnViewer must listen for webglcontextlost event"
    assert "webglcontextrestored" in code, "UrnViewer must listen for webglcontextrestored event"
    assert "setWebglFailed" in code, "UrnViewer must update webglFailed state on context loss"

    # 2. UrnAccessibleFallback integration
    assert "UrnAccessibleFallback" in code, "UrnViewer must import and render UrnAccessibleFallback"
    assert "showAccessibleView" in code, "UrnViewer must provide accessible view state"
    assert "onReturnTo3D" in code, "UrnViewer must allow returning to 3D when ready"

    # 3. Model error boundary and load failure handling
    assert "ModelErrorBoundary" in code, "UrnViewer must wrap model in ModelErrorBoundary"
    assert "setModelLoadError" in code, "UrnViewer must track model load errors"
    assert "onError" in code, "ModelErrorBoundary must accept onError prop"

    # 4. Missing mesh fallback banner preventing blank canvas or false twin claim
    assert "missing-mesh-fallback-banner" in code, (
        "UrnViewer must render missing-mesh-fallback-banner when 3D model is missing"
    )
    assert "Mô hình 3D đang phục chế" in code, (
        "UrnViewer banner must announce archival reconstruction status"
    )
    assert "Bản dập 2D thay thế" in code, (
        "UrnViewer banner must announce 2D rubbing replacement"
    )


# ==============================================================================
# 7. Holistic 3D Manifest Audit Tests
# ==============================================================================


def test_audit_all_3d_manifests_public_and_frontend():
    """Verify full audit passes across public/models/manifests and frontend/public/models/manifests."""
    for m_dir in [PUBLIC_MANIFESTS_DIR, FRONTEND_MANIFESTS_DIR]:
        audit_res = audit_all_3d_manifests(manifests_dir=m_dir, repo_root=REPO_ROOT)
        assert audit_res["audit_passed"] is True
        assert audit_res["total_urns_audited"] == 9
        assert audit_res["total_hotspots_audited"] == 162
        assert audit_res["mesh_present_urns"] == 1
        assert audit_res["mesh_missing_urns"] == 8
        assert audit_res["fallback_2d_coverage_pct"] == 100.0
        assert audit_res["all_urns_cleared"] is True

        for rep in audit_res["urn_reports"]:
            assert rep["version_valid"] is True
            assert rep["integrity_valid"] is True
            assert rep["license_valid"] is True
            assert rep["joins_valid"] is True
            assert rep["fallback_valid"] is True
