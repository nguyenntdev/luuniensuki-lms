# -*- coding: utf-8 -*-
"""V5-T027: Image and 3D Mesh Attribution Linkage with Rights Enforcement Test Suite.

Audits and verifies (Wave W02, Slot A07 / Ticket V5-T027):
1. Rights Attribution on all 9 3D Urn Manifests:
   - Checks public/models/manifests/*.json and frontend/public/models/manifests/*.json.
   - Verifies creator, license (CC BY 4.0 / Educational Fair Use), rights owner (HMCC),
     and cryptographic checksum/hash.
   - Verifies 2D rubbing viewer fallback linkage (UrnAccessibleFallback & ban-duc-noi/).
2. Checksum Integrity:
   - Verifies physical presence and SHA-256 hash match of 3D GLB meshes for Cao Đỉnh.
   - Verifies physical presence and SHA-256 hash match of 2D rubbing files for all 9 urns.
   - Verifies GLB binary magic bytes (glTF) and image magic bytes (JPEG).
3. Public CDN Rights Enforcement Gate:
   - Validates that cleared manifests are permitted for CDN distribution.
   - Fails closed on revoked, withdrawn, or restricted rights status.
   - Fails closed on missing or invalid licenses.
   - Fails closed on public_distribution_allowed=False.
   - Fails closed on checksum mismatches or missing fallback assets.
4. Database Integration (backend.history_models.HistoricalAsset):
   - Verifies synchronization to persistent HistoricalAsset table.
   - Validates rights clearance enforcement on database entity level.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy.orm import Session

from backend.history_models import HistoricalAsset, HistoricalEntity
from backend.services.asset_rights import (
    APPROVED_LICENSES,
    DEFAULT_CREATOR,
    DEFAULT_RIGHTS_OWNER,
    EXPECTED_CAO_DINH_CHECKSUMS,
    GLB_MAGIC,
    JPEG_MAGIC,
    RESTRICTED_RIGHTS_STATUSES,
    URN_FALLBACK_2D_REGISTRY,
    URN_SLUGS,
    AssetRightsError,
    AssetDistributionBlockedError,
    AssetIntegrityError,
    AssetRightsMissingLicenseError,
    AssetRightsRevokedError,
    audit_all_relic_assets,
    audit_all_urn_manifests,
    can_distribute_on_cdn,
    enforce_cdn_distribution_policy,
    get_motif_fallback,
    get_motif_registry_162,
    get_viewer_fallback,
    resolve_asset_fallback,
    revoke_manifest_rights,
    sha256_of_file,
    sync_manifest_to_historical_asset,
    validate_historical_asset_distribution,
    validate_manifest_attribution,
    validate_manifest_checksum_integrity,
)
from backend.services.heritage_import import (
    HeritageImportService,
    sync_cuu_dinh_manifests_to_db,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
PUBLIC_MANIFESTS_DIR = REPO_ROOT / "public" / "models" / "manifests"
FRONTEND_MANIFESTS_DIR = REPO_ROOT / "frontend" / "public" / "models" / "manifests"
BAN_DUC_NOI_DIR = REPO_ROOT / "ban-duc-noi"


# ==============================================================================
# 1. 3D Urn Manifests Rights Attribution Verification (Positive Tests)
# ==============================================================================


def test_all_9_urn_manifests_have_valid_attribution_and_fallbacks():
    """Verify that all 9 urn manifests have valid creator, license, rights owner, checksum, and 2D fallback."""
    manifest_dirs = [PUBLIC_MANIFESTS_DIR, FRONTEND_MANIFESTS_DIR]

    for m_dir in manifest_dirs:
        assert m_dir.exists(), f"Manifests directory missing: {m_dir}"

        index_path = m_dir / "index.json"
        assert index_path.exists(), f"Missing index.json in {m_dir}"
        with open(index_path, "r", encoding="utf-8") as f:
            index_data = json.load(f)

        assert index_data.get("total_urns") == 9
        assert index_data.get("total_hotspots") == 162

        for slug in URN_SLUGS:
            mf_path = m_dir / f"{slug}.json"
            assert mf_path.exists(), f"Missing individual manifest: {mf_path}"

            with open(mf_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)

            # 1. Creator and rights attribution
            assert manifest.get("creator") == DEFAULT_CREATOR, f"Invalid creator in {slug}"
            assert manifest.get("rights_owner") == DEFAULT_RIGHTS_OWNER, f"Invalid rights owner in {slug}"
            assert manifest.get("rights_attribution") == DEFAULT_CREATOR

            # 2. License check
            assert manifest.get("license") in APPROVED_LICENSES, f"Unapproved license in {slug}: {manifest.get('license')}"

            # 3. Rights status and distribution clearance
            assert manifest.get("rights_status") == "cleared", f"Urn {slug} rights_status must be 'cleared'"
            assert manifest.get("public_distribution_allowed") is True
            assert manifest.get("public_display_allowed") is True

            # 4. Checksum
            checksum = manifest.get("checksum")
            assert checksum and len(checksum) == 64, f"Invalid SHA-256 checksum in {slug}: {checksum}"

            # 5. 2D Rubbing fallback
            assert manifest.get("has_2d_fallback") is True
            fallback_2d_url = manifest.get("fallback_2d_url")
            assert fallback_2d_url and fallback_2d_url.startswith("/assets/ban-duc-noi/")

            viewer_fallback = manifest.get("viewer_fallback")
            assert viewer_fallback is not None, f"Missing viewer_fallback in {slug}"
            assert viewer_fallback.get("type") == "2d_rubbing"
            assert viewer_fallback.get("component") == "UrnAccessibleFallback"
            assert viewer_fallback.get("format") == "image/jpeg"
            assert viewer_fallback.get("rights_attribution") == DEFAULT_RIGHTS_OWNER
            assert viewer_fallback.get("bytes", 0) > 5000

            # Also check index.json manifest entry parity
            entry = index_data["manifests"][slug]
            assert entry.get("creator") == DEFAULT_CREATOR
            assert entry.get("license") in APPROVED_LICENSES
            assert entry.get("rights_owner") == DEFAULT_RIGHTS_OWNER
            assert entry.get("checksum") == checksum
            assert entry.get("has_2d_fallback") is True
            assert entry.get("viewer_fallback") is not None


def test_manifest_attribution_validation_service():
    """Verify validate_manifest_attribution function on all 9 urn manifests."""
    for slug in URN_SLUGS:
        mf_path = PUBLIC_MANIFESTS_DIR / f"{slug}.json"
        with open(mf_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        validated = validate_manifest_attribution(manifest)
        assert validated["attribution_valid"] is True
        assert validated["urn_slug"] == slug
        assert validated["creator"] == DEFAULT_CREATOR
        assert validated["rights_owner"] == DEFAULT_RIGHTS_OWNER
        assert validated["rights_status"] == "cleared"
        assert len(validated["checksum"]) == 64


# ==============================================================================
# 2. Checksum Integrity & Physical Disk File Verification
# ==============================================================================


def test_3d_and_2d_checksum_integrity_on_disk():
    """Verify that all manifest checksums match real physical files and binary formats on disk."""
    for slug in URN_SLUGS:
        mf_path = PUBLIC_MANIFESTS_DIR / f"{slug}.json"
        with open(mf_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        # 1. Service checksum integrity verification
        assert validate_manifest_checksum_integrity(manifest, repo_root=REPO_ROOT) is True

        # 2. Verify 2D rubbing file on disk directly
        expected_fb = URN_FALLBACK_2D_REGISTRY[slug]
        fb_disk_path = REPO_ROOT / expected_fb["disk_path"]
        assert fb_disk_path.exists(), f"2D rubbing missing on disk: {fb_disk_path}"

        actual_fb_sha = sha256_of_file(fb_disk_path)
        assert actual_fb_sha == expected_fb["sha256"], f"SHA mismatch for {slug} 2D fallback"
        assert fb_disk_path.stat().st_size == expected_fb["bytes"]

        # Check JPEG magic bytes
        with open(fb_disk_path, "rb") as f:
            magic = f.read(3)
        assert magic == JPEG_MAGIC, f"File {fb_disk_path} does not have JPEG magic header"


def test_cao_dinh_3d_mesh_lod_checksum_integrity():
    """Verify Cao Đỉnh 3D GLB mesh LOD variants have authentic binary headers and exact hashes."""
    cao_manifest_path = PUBLIC_MANIFESTS_DIR / "cao-dinh.json"
    with open(cao_manifest_path, "r", encoding="utf-8") as f:
        cao_manifest = json.load(f)

    assert cao_manifest["mesh_status"] == "PRESENT"
    assert cao_manifest["checksum"] == EXPECTED_CAO_DINH_CHECKSUMS["CAO-DINH-v1-1k.glb"]

    for filename, expected_sha in EXPECTED_CAO_DINH_CHECKSUMS.items():
        glb_path = REPO_ROOT / "frontend" / "public" / "assets" / "models" / filename
        assert glb_path.exists(), f"GLB file missing: {glb_path}"
        assert glb_path.stat().st_size > 1_000_000

        actual_sha = sha256_of_file(glb_path)
        assert actual_sha == expected_sha, f"GLB SHA mismatch on {filename}"

        with open(glb_path, "rb") as f:
            header = f.read(4)
        assert header == GLB_MAGIC, f"File {filename} is not a valid GLB binary container"


def test_missing_urn_models_suppress_phantom_substitution():
    """Verify that the 8 non-Cao-Đỉnh urns are marked MISSING and have null fallback_url."""
    for slug in URN_SLUGS:
        if slug == "cao-dinh":
            continue

        mf_path = PUBLIC_MANIFESTS_DIR / f"{slug}.json"
        with open(mf_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        assert manifest["mesh_status"] == "MISSING"
        for lod in ["low", "medium", "high"]:
            assert manifest["lods"][lod]["fallback_url"] is None, (
                f"Urn {slug} illegally references fallback_url in {lod}"
            )
            assert manifest["lods"][lod]["status"] == "MISSING"


# ==============================================================================
# 3. Public CDN Rights Enforcement Gate (Positive Flows)
# ==============================================================================


def test_positive_cdn_distribution_clearance_all_9_urns():
    """Verify that all 9 valid manifests pass CDN distribution clearance."""
    for slug in URN_SLUGS:
        mf_path = PUBLIC_MANIFESTS_DIR / f"{slug}.json"
        with open(mf_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        allowed, reason = can_distribute_on_cdn(manifest)
        assert allowed is True, f"Urn {slug} rejected from CDN distribution: {reason}"
        assert reason is None

        # Enforce policy stamp
        clearance = enforce_cdn_distribution_policy(manifest, repo_root=REPO_ROOT)
        assert clearance["cdn_distribution_status"] == "ALLOWED"
        assert clearance["urn_slug"] == slug
        assert "max-age=" in clearance["cache_control"]
        assert clearance["has_2d_fallback"] is True
        assert clearance["viewer_fallback"]["component"] == "UrnAccessibleFallback"


def test_audit_all_urn_manifests_service():
    """Verify comprehensive audit_all_urn_manifests service passes for all 9 urns."""
    audit_report = audit_all_urn_manifests(
        manifests_dir=PUBLIC_MANIFESTS_DIR, repo_root=REPO_ROOT
    )
    assert audit_report["total_urns_audited"] == 9
    assert audit_report["all_cleared"] is True

    for u in audit_report["urns"]:
        assert u["integrity_verified"] is True
        assert u["cdn_distribution_allowed"] is True
        assert u["rejection_reason"] is None
        assert u["license"] in APPROVED_LICENSES
        assert u["rights_owner"] == DEFAULT_RIGHTS_OWNER


# ==============================================================================
# 4. Negative / Abuse Tests: Rights Enforcement & Takedown Gate
# ==============================================================================


def test_negative_revoked_rights_blocks_cdn_distribution():
    """Negative Abuse Test: When rights are revoked, CDN distribution is blocked."""
    mf_path = PUBLIC_MANIFESTS_DIR / "cao-dinh.json"
    with open(mf_path, "r", encoding="utf-8") as f:
        clean_manifest = json.load(f)

    # Revoke rights
    revoked_manifest = revoke_manifest_rights(clean_manifest, reason="HMCC license expired")

    allowed, reason = can_distribute_on_cdn(revoked_manifest)
    assert allowed is False
    assert "restricted or revoked" in reason

    with pytest.raises(AssetRightsRevokedError, match="rights status is revoked"):
        validate_manifest_attribution(revoked_manifest)

    with pytest.raises(AssetDistributionBlockedError):
        enforce_cdn_distribution_policy(revoked_manifest, repo_root=REPO_ROOT)


def test_negative_restricted_statuses_block_cdn():
    """Negative Abuse Test: Various restricted rights statuses are blocked."""
    mf_path = PUBLIC_MANIFESTS_DIR / "nhan-dinh.json"
    with open(mf_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    for bad_status in ["withdrawn", "restricted", "copyrighted", "unlicensed", "blocked"]:
        tampered = json.loads(json.dumps(manifest))
        tampered["rights_status"] = bad_status

        allowed, reason = can_distribute_on_cdn(tampered)
        assert allowed is False, f"Status '{bad_status}' should have been blocked"

        with pytest.raises(AssetRightsRevokedError, match="revoked or restricted"):
            validate_manifest_attribution(tampered)


def test_negative_missing_or_proprietary_license_blocks_cdn():
    """Negative Abuse Test: Missing license or proprietary license blocks CDN distribution."""
    mf_path = PUBLIC_MANIFESTS_DIR / "chuong-dinh.json"
    with open(mf_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    # 1. Missing license
    no_lic = json.loads(json.dumps(manifest))
    no_lic["license"] = ""
    with pytest.raises(AssetRightsMissingLicenseError, match="missing required license"):
        validate_manifest_attribution(no_lic)

    # 2. None license
    none_lic = json.loads(json.dumps(manifest))
    none_lic["license"] = None
    with pytest.raises(AssetRightsMissingLicenseError, match="missing required license"):
        validate_manifest_attribution(none_lic)

    # 3. Proprietary / All Rights Reserved
    prop_lic = json.loads(json.dumps(manifest))
    prop_lic["license"] = "All Rights Reserved - Proprietary Corporate Grant"
    with pytest.raises(AssetRightsRevokedError, match="is restricted/unlicensed"):
        validate_manifest_attribution(prop_lic)


def test_negative_disallowed_public_distribution_blocks_cdn():
    """Negative Abuse Test: public_distribution_allowed=False blocks CDN distribution."""
    mf_path = PUBLIC_MANIFESTS_DIR / "anh-dinh.json"
    with open(mf_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    # Distribution disallowed
    no_dist = json.loads(json.dumps(manifest))
    no_dist["public_distribution_allowed"] = False
    with pytest.raises(AssetDistributionBlockedError, match="public_distribution_allowed=False"):
        validate_manifest_attribution(no_dist)

    # Display disallowed
    no_disp = json.loads(json.dumps(manifest))
    no_disp["public_display_allowed"] = False
    with pytest.raises(AssetDistributionBlockedError, match="public_display_allowed=False"):
        validate_manifest_attribution(no_disp)


def test_negative_checksum_tampering_fails_integrity():
    """Negative Abuse Test: Modified or mismatched checksum fails integrity verification."""
    mf_path = PUBLIC_MANIFESTS_DIR / "tuyen-dinh.json"
    with open(mf_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    # Mismatched 2D rubbing hash
    tampered = json.loads(json.dumps(manifest))
    tampered["viewer_fallback"]["sha256"] = "0000000000000000000000000000000000000000000000000000000000000000"

    with pytest.raises(AssetIntegrityError, match="SHA-256 mismatch"):
        validate_manifest_checksum_integrity(tampered, repo_root=REPO_ROOT)

    with pytest.raises(AssetIntegrityError):
        enforce_cdn_distribution_policy(tampered, repo_root=REPO_ROOT)


def test_negative_missing_fallback_2d_fails_validation():
    """Negative Abuse Test: Missing 2D viewer fallback fails validation."""
    mf_path = PUBLIC_MANIFESTS_DIR / "du-dinh.json"
    with open(mf_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    no_fb = json.loads(json.dumps(manifest))
    no_fb["has_2d_fallback"] = False
    no_fb["viewer_fallback"] = None

    with pytest.raises(AssetRightsError, match="has_2d_fallback=True"):
        validate_manifest_attribution(no_fb)


# ==============================================================================
# 5. Database Integration & HistoricalAsset Sync Tests
# ==============================================================================


def test_database_historical_asset_sync_and_rights_enforcement(db_session: Session):
    """Verify syncing manifests to HistoricalAsset model and database-level rights validation."""
    # Read Cao Đỉnh manifest
    mf_path = PUBLIC_MANIFESTS_DIR / "cao-dinh.json"
    with open(mf_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    # 1. Sync to HistoricalAsset
    asset = sync_manifest_to_historical_asset(db_session, manifest)
    db_session.commit()

    assert asset.id is not None
    assert asset.asset_type == "3d_model"
    assert asset.rights_status == "cleared"
    assert asset.license == "CC BY 4.0 / Educational Fair Use"
    assert asset.attribution == DEFAULT_CREATOR
    assert asset.source_origin == DEFAULT_RIGHTS_OWNER
    assert asset.public_display_allowed is True
    assert asset.sha256 == manifest["checksum"]

    # 2. Positive DB validation
    allowed, reason = validate_historical_asset_distribution(asset)
    assert allowed is True
    assert reason is None

    # 3. Negative DB validation: Revoked status
    asset.rights_status = "revoked"
    db_session.commit()
    allowed_revoked, reason_revoked = validate_historical_asset_distribution(asset)
    assert allowed_revoked is False
    assert "revoked" in reason_revoked

    # 4. Negative DB validation: Display disallowed
    asset.rights_status = "cleared"
    asset.public_display_allowed = False
    db_session.commit()
    allowed_nodisp, reason_nodisp = validate_historical_asset_distribution(asset)
    assert allowed_nodisp is False
    assert "public_display_allowed is False" in reason_nodisp

    # 5. Negative DB validation: Missing checksum
    asset.public_display_allowed = True
    asset.sha256 = None
    db_session.commit()
    allowed_nosha, reason_nosha = validate_historical_asset_distribution(asset)
    assert allowed_nosha is False
    assert "Missing valid SHA-256 checksum" in reason_nosha


# ==============================================================================
# 6. Relic Motifs (162 Motifs) Attribution, Linkage & Fallback Resolution
# ==============================================================================


def test_all_162_motifs_hotspots_link_coordinates_rubbing_and_rights():
    """Verify that all 162 relief motifs link coordinates, 3D GLB path, 2D rubbing, and license metadata."""
    manifest_dirs = [PUBLIC_MANIFESTS_DIR, FRONTEND_MANIFESTS_DIR]

    for m_dir in manifest_dirs:
        total_hotspots = 0

        for slug in URN_SLUGS:
            mf_path = m_dir / f"{slug}.json"
            with open(mf_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)

            hotspots = manifest.get("hotspots", [])
            assert len(hotspots) == 18, f"Urn {slug} must have exactly 18 relief hotspots, found {len(hotspots)}"
            total_hotspots += len(hotspots)

            is_cao = (slug == "cao-dinh")

            for h in hotspots:
                # 1. 3D GLB model path & coordinates
                if is_cao:
                    assert h.get("model_url") == "/assets/models/CAO-DINH-v1-1k.glb"
                else:
                    assert h.get("model_url") is None

                assert "pos" in h and len(h["pos"]) == 3
                assert "camera_position" in h and len(h["camera_position"]) == 3
                assert "camera_target" in h and len(h["camera_target"]) == 3
                assert h.get("bounding_radius", 0) > 0

                # 2. 2D rubbing image in ban-duc-noi/
                fb = h.get("fallback_2d")
                assert fb is not None, f"Hotspot {h.get('hotspot_id')} missing fallback_2d"
                disk_path = fb.get("disk_path")
                assert disk_path and disk_path.startswith("ban-duc-noi/")

                full_disk = REPO_ROOT / disk_path
                assert full_disk.exists(), f"Rubbing image file not found on disk: {full_disk}"

                actual_sha = sha256_of_file(full_disk)
                assert actual_sha == fb.get("sha256"), f"SHA-256 mismatch for {disk_path}"
                assert full_disk.stat().st_size == fb.get("bytes")

                # 3. Asset license and rights owner metadata
                assert h.get("license") in APPROVED_LICENSES
                assert h.get("rights_owner") == DEFAULT_RIGHTS_OWNER
                assert h.get("rights_status") == "cleared"
                assert h.get("public_distribution_allowed") is True
                assert h.get("public_display_allowed") is True

        assert total_hotspots == 162, f"Expected 162 total hotspots, found {total_hotspots}"


def test_resolve_asset_fallback_urn_matrix():
    """Verify clean 2D fallback resolution for Urns across device capabilities and mesh presence."""
    # 1. Cao Đỉnh (3D mesh available) with WebGL enabled -> 3D mesh render mode
    res_cao_3d = resolve_asset_fallback("cao-dinh", webgl_supported=True, repo_root=REPO_ROOT)
    assert res_cao_3d["render_mode"] == "3d_mesh"
    assert res_cao_3d["mesh_available"] is True
    assert res_cao_3d["primary_asset"]["asset_type"] == "3d_model"
    assert res_cao_3d["fallback_asset"]["type"] == "2d_rubbing"
    assert res_cao_3d["rights_metadata"]["license"] in APPROVED_LICENSES

    # 2. Cao Đỉnh with WebGL disabled -> Falls back to 2D rubbing photograph
    res_cao_no_webgl = resolve_asset_fallback("cao-dinh", webgl_supported=False, repo_root=REPO_ROOT)
    assert res_cao_no_webgl["render_mode"] == "2d_fallback"
    assert res_cao_no_webgl["fallback_reason"] == "webgl_unsupported"
    assert res_cao_no_webgl["primary_asset"]["format"] == "image/jpeg"
    assert res_cao_no_webgl["accessible_component"] == "UrnAccessibleFallback"

    # 3. Cao Đỉnh with low power client mode -> Falls back to 2D rubbing photograph
    res_cao_low_power = resolve_asset_fallback("cao-dinh", client_low_power=True, repo_root=REPO_ROOT)
    assert res_cao_low_power["render_mode"] == "2d_fallback"
    assert res_cao_low_power["fallback_reason"] == "low_power_budget"

    # 4. Cao Đỉnh with force_2d_fallback -> Falls back to 2D rubbing photograph
    res_cao_force_2d = resolve_asset_fallback("cao-dinh", force_2d_fallback=True, repo_root=REPO_ROOT)
    assert res_cao_force_2d["render_mode"] == "2d_fallback"
    assert res_cao_force_2d["fallback_reason"] == "client_forced_2d"

    # 5. Missing mesh urns (e.g. Nhân Đỉnh, Chương Đỉnh, Thuần Đỉnh) -> Always fallback to 2D rubbing
    for slug in ["nhan-dinh", "chuong-dinh", "thuan-dinh", "huyen-dinh"]:
        res_missing = resolve_asset_fallback(slug, webgl_supported=True, repo_root=REPO_ROOT)
        assert res_missing["render_mode"] == "2d_fallback"
        assert res_missing["fallback_reason"] == "mesh_unavailable"
        assert res_missing["primary_asset"]["disk_path"].startswith("ban-duc-noi/")
        assert res_missing["primary_asset"]["bytes"] > 5000


def test_resolve_asset_fallback_motif_matrix():
    """Verify clean 2D fallback resolution for individual Motifs."""
    # 1. Cao Đỉnh Motif (Long) with WebGL supported -> 3D hotspot render mode
    res_long_3d = resolve_asset_fallback(
        "urn_cao_dinh_02", urn_slug="cao-dinh", webgl_supported=True, repo_root=REPO_ROOT
    )
    assert res_long_3d["render_mode"] == "3d_mesh"
    assert res_long_3d["target_type"] == "motif"
    assert res_long_3d["primary_asset"]["asset_type"] == "3d_hotspot"
    assert res_long_3d["primary_asset"]["model_url"] is not None
    assert res_long_3d["primary_asset"]["coordinates"]["bounding_radius"] == 0.08
    assert res_long_3d["fallback_asset"]["disk_path"] == "ban-duc-noi/CAO DINH/LONG.jpg"

    # 2. Cao Đỉnh Motif (Long) with WebGL disabled -> Falls back to 2D rubbing
    res_long_2d = resolve_asset_fallback(
        "urn_cao_dinh_02", urn_slug="cao-dinh", webgl_supported=False, repo_root=REPO_ROOT
    )
    assert res_long_2d["render_mode"] == "2d_fallback"
    assert res_long_2d["fallback_reason"] == "webgl_unsupported"
    assert res_long_2d["primary_asset"]["disk_path"] == "ban-duc-noi/CAO DINH/LONG.jpg"

    # 3. Missing mesh motif (e.g. Nhân Đỉnh - Ngô Đồng) -> Falls back to 2D rubbing
    res_ngo_dong = resolve_asset_fallback(
        "urn_nhan_dinh_02", urn_slug="nhan-dinh", webgl_supported=True, repo_root=REPO_ROOT
    )
    assert res_ngo_dong["render_mode"] == "2d_fallback"
    assert res_ngo_dong["fallback_reason"] == "mesh_unavailable"
    assert res_ngo_dong["primary_asset"]["disk_path"] == "ban-duc-noi/NHAN DINH/NGÔ ĐỒNG.jpg"


def test_negative_motif_rights_restriction_fails_closed():
    """Negative Abuse Test: Revoked or restricted motif rights fail closed and block distribution."""
    # 1. Tampered manifest with revoked hotspot rights
    mf_path = PUBLIC_MANIFESTS_DIR / "cao-dinh.json"
    with open(mf_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    tampered = json.loads(json.dumps(manifest))
    tampered["hotspots"][1]["rights_status"] = "revoked"

    with pytest.raises(AssetRightsRevokedError, match="rights status is revoked or restricted"):
        validate_manifest_attribution(tampered)

    # 2. Tampered manifest with proprietary hotspot license
    tampered_lic = json.loads(json.dumps(manifest))
    tampered_lic["hotspots"][0]["license"] = "All Rights Reserved - Proprietary"

    with pytest.raises(AssetRightsRevokedError, match="is restricted/unlicensed"):
        validate_manifest_attribution(tampered_lic)

    # 3. Tampered hotspot checksum fails integrity
    tampered_sha = json.loads(json.dumps(manifest))
    tampered_sha["hotspots"][0]["fallback_2d"]["sha256"] = "1111111111111111111111111111111111111111111111111111111111111111"

    with pytest.raises(AssetIntegrityError, match="Hotspot 2D rubbing SHA-256 mismatch"):
        validate_manifest_checksum_integrity(tampered_sha, repo_root=REPO_ROOT)


def test_audit_all_relic_assets_171_relics_coverage():
    """Verify comprehensive audit of 171 relics (9 urns + 162 motifs) with 100% verification."""
    report = audit_all_relic_assets(manifests_dir=PUBLIC_MANIFESTS_DIR, repo_root=REPO_ROOT)

    assert report["total_urns_audited"] == 9
    assert report["total_motifs_audited"] == 162
    assert report["total_relics_audited"] == 171
    assert report["all_urns_cleared"] is True
    assert report["all_motifs_cleared"] is True
    assert report["all_relics_cleared"] is True

    summary = report["motifs_summary"]
    assert summary["total"] == 162
    assert summary["verified_on_disk"] == 162
    assert summary["checksums_verified"] == 162
    assert summary["with_coordinates"] == 162


def test_heritage_import_service_cuu_dinh_sync(db_session: Session):
    """Verify HeritageImportService synchronizes Cửu Đỉnh manifests into HistoricalAsset table."""
    service = HeritageImportService(db=db_session)
    stats = service.sync_cuu_dinh_manifests(
        manifests_dir=PUBLIC_MANIFESTS_DIR, repo_root=REPO_ROOT
    )

    assert stats["synced_urns"] == 9
    assert stats["total_motifs_audited"] == 162
    assert stats["total_relics"] == 171

    # Verify query in database
    assets = db_session.query(HistoricalAsset).filter(
        HistoricalAsset.asset_type == "3d_model"
    ).all()
    assert len(assets) >= 9
    for a in assets:
        assert a.rights_status == "cleared"
        assert a.public_display_allowed is True
        assert a.license in APPROVED_LICENSES
        assert a.attribution == DEFAULT_CREATOR

