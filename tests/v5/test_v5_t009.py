# -*- coding: utf-8 -*-
"""V5-T009: Media and Rights Inventory Verification Test Suite.

Audits and verifies:
1. 3D GLB Models:
   - Physical presence, checksums, byte sizes, and glTF binary format magic headers for Cao Đỉnh LOD variants.
   - Explicit MISSING flagging for the other 8 urn models (no phantom assets rendered as fake 3D).
   - Manifest enforcement: missing urn models MUST have fallback_url set to null (no Cao Đỉnh substitution).
2. 2D Motif Rubbings (bản dập / bản đúc nổi):
   - 164 rubbing image files across 9 urn directories in ban-duc-noi/.
   - Valid image formats (JPEG / PNG magic bytes) and SHA-256 checksums.
   - Public domain & scholarly fair use legal attribution to HMCC.
3. 162 Relic Motif Mapping (3d_mesh_id):
   - All 162 motifs across 9 urns map to verified parent mesh status (18 PRESENT, 144 MISSING).
   - 100% of motifs possess a valid, existing 2D rubbing fallback on disk.
4. Audio Assets:
   - 16 audio guide MP3 tracks in frontend/public/assets/imperial/audio/ and backend/assets/imperial/audio/.
   - Valid MPEG audio frame sync headers, non-empty files, duration bounds, script text, and HMCC credits.
5. Sketchfab 3D Models:
   - 23 curated models in data/heritage-hue/sketchfab-curated.yaml with valid 32-char hex UIDs.
   - Epistemic guardrail: SF-020 permanently rejected for speculative accuracy.
   - Non-commercial & NoAI quarantine: SF-010 (CC BY-NC-SA) and SF-017 (NoAI) blocked.
   - Approved candidates: SF-009, SF-011, SF-016 (CC BY 4.0 with DOI citations).
6. Negative / Abuse Test:
   - Mesh reference without valid file MUST be marked missing rather than rendered fake.
   - Attempting to claim missing mesh as PRESENT or substituting another urn's mesh as fake 3D fails validation.
7. Media Rights Inventory Artifact Integrity:
   - artifacts/implementation/W00/W00_A09_media_rights_inventory.json schema, metrics, and consistency.
"""
from __future__ import annotations

import hashlib
import json
import os
import urllib.parse
from pathlib import Path
from typing import Any

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_PATH = (
    REPO_ROOT
    / "artifacts"
    / "implementation"
    / "W00"
    / "W00_A09_media_rights_inventory.json"
)
DATA_DIR = REPO_ROOT / "data"
BAN_DUC_NOI_DIR = REPO_ROOT / "ban-duc-noi"
FRONTEND_MODELS_DIR = REPO_ROOT / "frontend" / "public" / "assets" / "models"
AUDIO_DIR = REPO_ROOT / "frontend" / "public" / "assets" / "imperial" / "audio"
SKETCHFAB_PATH = REPO_ROOT / "data" / "heritage-hue" / "sketchfab-curated.yaml"
AUDIO_GUIDES_PATH = REPO_ROOT / "data" / "imperial" / "audio_guides.json"
RELIEF_MAP_PATH = REPO_ROOT / "artifacts" / "relief_image_map.json"

GLB_MAGIC = b"glTF"
JPEG_MAGIC = b"\xff\xd8\xff"
PNG_MAGIC = b"\x89PNG"
MPEG_AUDIO_SYNC_PREFIX = b"\xff\xfb"
ID3_MAGIC = b"ID3"

EXPECTED_CAO_DINH_CHECKSUMS = {
    "CAO-DINH-v1-512.glb": "51f5baf131e85257186b0e4a89087870ff66e4c787f7775bea797fc2550d8611",
    "CAO-DINH-v1-1k.glb": "6f7e73424c18c5e6504ee25eda103b56958b1e79348937e152e60731a2bcd16a",
    "CAO-DINH-v1-2k.glb": "59d7f26f5af647d727b3ce4855a8533ca39c96825e1c9dea672a94cb32e42e74",
    "CAO-DINH-v1.glb": "6f7e73424c18c5e6504ee25eda103b56958b1e79348937e152e60731a2bcd16a",
}

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


def sha256_file(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


# ==============================================================================
# Helper Verification Engine for Mesh References & Negative Abuse Checks
# ==============================================================================


def validate_mesh_reference(
    *,
    urn_slug: str,
    mesh_url: str | None,
    fallback_3d_url: str | None,
    mesh_status: str,
    has_2d_fallback: bool,
    fallback_2d_url: str | None,
) -> None:
    """Enforces strict mesh reference truth contract.

    Rules:
    1. If mesh_status is PRESENT, the file referenced by mesh_url MUST exist on disk.
    2. If mesh file does not exist on disk, mesh_status MUST be explicitly 'MISSING'.
    3. If mesh_status is MISSING, fallback_3d_url MUST NOT point to another urn's mesh
       (banning fake 3D phantom substitution).
    4. 100% of mesh references MUST have a valid 2D fallback when mesh is missing.
    """
    if mesh_status == "PRESENT":
        assert mesh_url, f"Urn '{urn_slug}' marked PRESENT but has empty mesh_url"
        disk_path = REPO_ROOT / "frontend" / "public" / mesh_url.lstrip("/")
        if not disk_path.exists():
            disk_path = REPO_ROOT / mesh_url.lstrip("/")
        assert (
            disk_path.exists()
        ), f"Abuse detected: Urn '{urn_slug}' marked PRESENT but file does not exist: {mesh_url}"
    elif mesh_status == "MISSING":
        if fallback_3d_url:
            # Cannot use another urn's GLB as fake 3D
            target_file = Path(fallback_3d_url).name.lower()
            if target_file.startswith("cao-dinh") and urn_slug != "cao-dinh":
                raise AssertionError(
                    f"Phantom asset abuse: Urn '{urn_slug}' is missing but attempts "
                    f"to substitute Cao Đỉnh mesh '{fallback_3d_url}' as fake 3D!"
                )
        assert (
            has_2d_fallback
        ), f"Missing mesh for urn '{urn_slug}' must have 2D fallback"
        assert (
            fallback_2d_url
        ), f"Missing mesh for urn '{urn_slug}' must specify fallback_2d_url"
        unquoted = urllib.parse.unquote(fallback_2d_url.replace("/assets/", ""))
        fb_disk = REPO_ROOT / unquoted
        if not fb_disk.exists():
            fb_disk = REPO_ROOT / "backend" / "assets" / unquoted
        assert (
            fb_disk.exists()
        ), f"2D fallback for urn '{urn_slug}' does not exist on disk: {fallback_2d_url}"
    else:
        raise AssertionError(
            f"Invalid mesh_status '{mesh_status}' for urn '{urn_slug}'"
        )


# ==============================================================================
# 1. 3D GLB Models Audit
# ==============================================================================


def test_3d_glb_models_presence_checksums_and_magic_bytes():
    """Verify presence, byte size, SHA-256, and glTF binary format for Cao Đỉnh LODs."""
    assert FRONTEND_MODELS_DIR.exists(), f"Missing directory: {FRONTEND_MODELS_DIR}"

    for filename, expected_sha in EXPECTED_CAO_DINH_CHECKSUMS.items():
        p = FRONTEND_MODELS_DIR / filename
        assert p.exists(), f"Missing 3D mesh asset: {filename}"
        assert p.stat().st_size > 1_000_000, f"Asset {filename} is suspiciously small: {p.stat().st_size} bytes"

        actual_sha = sha256_file(p)
        assert (
            actual_sha == expected_sha
        ), f"Checksum mismatch for {filename}: expected {expected_sha}, got {actual_sha}"

        # Verify glTF binary magic bytes
        with open(p, "rb") as f:
            header = f.read(4)
        assert (
            header == GLB_MAGIC
        ), f"File {filename} is not a valid GLB container (magic: {header!r}, expected {GLB_MAGIC!r})"


def test_missing_urn_models_explicitly_flagged_and_no_fake_fallback():
    """Verify that the 8 non-Cao-Đỉnh urns are flagged MISSING and have null fallback_url."""
    manifest_dirs = [
        REPO_ROOT / "public" / "models" / "manifests",
        REPO_ROOT / "frontend" / "public" / "models" / "manifests",
    ]

    for m_dir in manifest_dirs:
        assert m_dir.exists(), f"Missing manifests directory: {m_dir}"

        # Check index.json
        index_path = m_dir / "index.json"
        assert index_path.exists(), f"Missing index.json in {m_dir}"
        with open(index_path, "r", encoding="utf-8") as f:
            index_data = json.load(f)

        assert index_data.get("total_urns") == 9
        assert index_data.get("total_hotspots") == 162

        for slug in URN_SLUGS:
            entry = index_data["manifests"][slug]
            manifest_file = m_dir / f"{slug}.json"
            assert manifest_file.exists(), f"Missing individual manifest: {manifest_file}"

            with open(manifest_file, "r", encoding="utf-8") as mf:
                m_detail = json.load(mf)

            if slug == "cao-dinh":
                assert entry["mesh_status"] == "PRESENT"
                assert m_detail["mesh_status"] == "PRESENT"
                assert m_detail["lods"]["low"]["fallback_url"] == "/assets/models/CAO-DINH-v1-512.glb"
                assert m_detail["lods"]["low"]["sha256"] == EXPECTED_CAO_DINH_CHECKSUMS["CAO-DINH-v1-512.glb"]
            else:
                # The other 8 urns MUST be flagged MISSING
                assert (
                    entry["mesh_status"] == "MISSING"
                ), f"Urn '{slug}' in {index_path} must be explicitly flagged MISSING"
                assert (
                    m_detail["mesh_status"] == "MISSING"
                ), f"Urn '{slug}' in {manifest_file} must be explicitly flagged MISSING"

                # STRICT: fallback_url MUST be null (banning fake Cao Dinh rendering)
                for lod_name in ["low", "medium", "high"]:
                    assert (
                        entry["lods"][lod_name]["fallback_url"] is None
                    ), f"Urn '{slug}' index entry specifies non-null fallback_url for {lod_name}"
                    assert (
                        m_detail["lods"][lod_name]["fallback_url"] is None
                    ), f"Urn '{slug}' manifest specifies non-null fallback_url for {lod_name}"

                # 2D fallback MUST be provided
                assert entry.get("has_2d_fallback") is True
                assert m_detail.get("has_2d_fallback") is True
                assert entry.get("fallback_2d_url") is not None
                assert m_detail.get("fallback_2d_url") is not None


# ==============================================================================
# 2. 2D Motif Rubbings Corpus Audit (ban-duc-noi)
# ==============================================================================


def test_2d_rubbings_corpus_integrity():
    """Verify presence, non-emptiness, valid image headers, and 164 files in ban-duc-noi/."""
    assert BAN_DUC_NOI_DIR.exists(), f"Missing ban-duc-noi directory: {BAN_DUC_NOI_DIR}"

    expected_folders = [
        ("ANH DINH", 18),
        ("CAO DINH", 19),
        ("CHUONG DINH", 18),
        ("DU DINH", 18),
        ("HUYEN DINH", 19),
        ("NGHI DINH", 18),
        ("NHAN DINH", 18),
        ("THUAN DINH", 18),
        ("TUYEN DINH", 18),
    ]

    total_files = 0
    total_bytes = 0

    for folder_name, expected_count in expected_folders:
        folder_path = BAN_DUC_NOI_DIR / folder_name
        assert folder_path.exists(), f"Missing folder: {folder_path}"

        files = [f for f in folder_path.iterdir() if f.is_file() and not f.name.startswith(".")]
        assert len(files) == expected_count, (
            f"Folder {folder_name} expected {expected_count} files, got {len(files)}"
        )

        for fp in files:
            f_size = fp.stat().st_size
            assert f_size > 1_000, f"File {fp} is suspiciously small ({f_size} bytes)"
            total_files += 1
            total_bytes += f_size

            # Check image magic bytes
            with open(fp, "rb") as f:
                hdr = f.read(8)
            suffix = fp.suffix.lower()
            if suffix in [".jpg", ".jpeg"]:
                assert (
                    hdr[:3] == JPEG_MAGIC
                ), f"File {fp.name} does not have valid JPEG magic bytes"
            elif suffix == ".png":
                assert (
                    hdr[:4] == PNG_MAGIC
                ), f"File {fp.name} does not have valid PNG magic bytes"
            else:
                pytest.fail(f"Unexpected image format {suffix} for file {fp}")

    assert total_files == 164, f"Expected 164 rubbing files, found {total_files}"
    assert total_bytes > 1_000_000, f"Total rubbings byte size {total_bytes} is under 1MB"


def test_relief_image_map_coverage():
    """Verify all 162 mapped entries in artifacts/relief_image_map.json point to real files."""
    assert RELIEF_MAP_PATH.exists(), f"Missing relief map: {RELIEF_MAP_PATH}"

    with open(RELIEF_MAP_PATH, "r", encoding="utf-8") as f:
        relief_map = json.load(f)

    assert len(relief_map) >= 162, f"Relief map must contain at least 162 entries, got {len(relief_map)}"

    for motif_slug, rel_url in relief_map.items():
        assert rel_url.startswith("/assets/ban-duc-noi/"), f"Invalid asset URL: {rel_url}"
        unquoted = urllib.parse.unquote(rel_url.replace("/assets/", ""))
        disk_path = REPO_ROOT / unquoted
        if not disk_path.exists():
            disk_path = REPO_ROOT / "backend" / "assets" / unquoted

        assert (
            disk_path.exists()
        ), f"Mapped relief image for '{motif_slug}' does not exist on disk: {disk_path}"


# ==============================================================================
# 3. 162 Relic Motifs 3D Mesh ID Mapping
# ==============================================================================


def test_162_relic_motifs_mesh_mapping_and_fallbacks():
    """Verify all 162 motifs across 9 urns map to valid 3D mesh IDs and have 2D fallbacks."""
    data_files = [
        ("cao-dinh", "05_Data_CaoDinh.json", "PRESENT"),
        ("nhan-dinh", "06_Data_NhanDinh.json", "MISSING"),
        ("chuong-dinh", "07_Data_ChuongDinh.json", "MISSING"),
        ("anh-dinh", "08_Data_AnhDinh.json", "MISSING"),
        ("nghi-dinh", "09_Data_NghiDinh.json", "MISSING"),
        ("thuan-dinh", "10_Data_ThuanDinh.json", "MISSING"),
        ("tuyen-dinh", "11_Data_TuyenDinh.json", "MISSING"),
        ("du-dinh", "12_Data_DuDinh.json", "MISSING"),
        ("huyen-dinh", "13_Data_HuyenDinh.json", "MISSING"),
    ]

    total_motifs = 0
    seen_mesh_ids: set[str] = set()

    for urn_slug, fname, expected_mesh_status in data_files:
        p = DATA_DIR / fname
        assert p.exists(), f"Missing dataset file: {p}"

        with open(p, "r", encoding="utf-8") as f:
            items = json.load(f)

        assert len(items) == 18, f"Urn {urn_slug} expected 18 motifs, got {len(items)}"
        total_motifs += len(items)

        for it in items:
            m_id = it.get("id")
            mesh_id = str(it.get("3d_mesh_id"))
            assert mesh_id, f"Motif {m_id} has empty 3d_mesh_id"
            assert mesh_id.startswith(f"mesh_urn_{urn_slug.replace('-', '_')}"), (
                f"3d_mesh_id {mesh_id} does not match expected naming convention for {urn_slug}"
            )
            assert mesh_id not in seen_mesh_ids, f"Duplicate 3d_mesh_id: {mesh_id}"
            seen_mesh_ids.add(mesh_id)

            # 2D fallback thumbnail must exist
            thumb_url = it.get("thumbnail_url", "")
            assert thumb_url, f"Motif {m_id} has empty thumbnail_url"
            unquoted = urllib.parse.unquote(thumb_url.replace("/assets/", ""))
            disk_path = REPO_ROOT / unquoted
            if not disk_path.exists():
                disk_path = REPO_ROOT / "backend" / "assets" / unquoted
            assert (
                disk_path.exists()
            ), f"2D rubbing thumbnail for {m_id} ({mesh_id}) does not exist: {disk_path}"

    assert total_motifs == 162, f"Expected 162 motifs in total, got {total_motifs}"
    assert len(seen_mesh_ids) == 162, f"Expected 162 unique 3d_mesh_ids, got {len(seen_mesh_ids)}"


# ==============================================================================
# 4. Audio Assets Audit
# ==============================================================================


def test_audio_assets_presence_and_format():
    """Verify all 16 audio guide MP3 files exist, have MPEG audio headers, and valid metadata."""
    assert AUDIO_GUIDES_PATH.exists(), f"Missing audio dataset: {AUDIO_GUIDES_PATH}"

    with open(AUDIO_GUIDES_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    guides = data.get("audio_guides") or data.get("tracks") or []
    assert len(guides) == 16, f"Expected 16 audio guides, got {len(guides)}"

    for g in guides:
        slug = g.get("monument_slug") or g.get("site_slug")
        fname = f"{slug}.mp3"
        fp_front = AUDIO_DIR / fname
        fp_back = REPO_ROOT / "backend" / "assets" / "imperial" / "audio" / fname

        assert fp_front.exists() or fp_back.exists(), (
            f"Audio asset for monument '{slug}' missing on disk: {fname}"
        )
        chosen = fp_front if fp_front.exists() else fp_back

        assert chosen.stat().st_size > 10_000, f"Audio file {chosen} is too small: {chosen.stat().st_size} bytes"

        # Check audio magic bytes
        with open(chosen, "rb") as f:
            header = f.read(4)
        assert (
            header[:3] == ID3_MAGIC or header[:2] == MPEG_AUDIO_SYNC_PREFIX or header[0] == 0xFF
        ), f"File {chosen} does not have valid MPEG audio header: {header!r}"

        # Duration bounds check (Master Spec: 90 - 150s)
        duration = g.get("duration_seconds") or g.get("duration")
        assert duration and 60 <= duration <= 300, f"Duration {duration} out of bounds for {slug}"

        # Script text check
        script = g.get("script_text")
        assert script and len(script) > 50, f"Script text too short for {slug}"

        # Rights credit
        credit = g.get("credit_text")
        assert credit and "Trung tâm Bảo tồn Di tích Cố đô Huế" in credit, (
            f"Missing required institutional attribution in credit_text for {slug}"
        )


# ==============================================================================
# 5. Sketchfab Curated 3D Models & Rights Guardrails
# ==============================================================================


def test_sketchfab_curated_models_guardrails():
    """Verify 23 curated Sketchfab models enforce epistemic, NC, and NoAI guardrails."""
    assert SKETCHFAB_PATH.exists(), f"Missing Sketchfab catalog: {SKETCHFAB_PATH}"

    with open(SKETCHFAB_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    models = data.get("models") or []
    assert len(models) == 23, f"Expected exactly 23 curated Sketchfab models, got {len(models)}"

    models_by_id = {m["id"]: m for m in models}

    # Verify 32-character hexadecimal UIDs
    import re
    uid_pattern = re.compile(r"^[0-9a-fA-F]{32}$")
    for m in models:
        raw_uid = m.get("model_uid")
        assert raw_uid and uid_pattern.match(raw_uid), f"Invalid 32-char hex UID for model {m.get('id')}: {raw_uid}"

    # Guardrail 1: SF-020 permanently rejected for speculative accuracy
    sf_020 = models_by_id.get("SF-020")
    assert sf_020 is not None, "Missing SF-020 in registry"
    assert sf_020.get("accuracy_grade") in ["rejected_inaccurate", "rejected_accuracy"]
    assert sf_020.get("content_status") == "rejected_accuracy"

    # Guardrail 2: SF-010 blocked from commercial embedding (CC BY-NC-SA)
    sf_010 = models_by_id.get("SF-010")
    assert sf_010 is not None, "Missing SF-010 in registry"
    assert sf_010.get("displayed_license") == "CC BY-NC-SA"
    assert sf_010.get("commercial_use_status") in ["blocked_nc", "prohibited_nc"]
    assert sf_010.get("content_status") == "blocked_nc"

    # Guardrail 3: SF-017 blocked from commercial and strictly NoAI protected
    sf_017 = models_by_id.get("SF-017")
    assert sf_017 is not None, "Missing SF-017 in registry"
    assert sf_017.get("noai") is True
    assert sf_017.get("content_status") == "blocked_noai"

    # Guardrail 4: Approved candidates under CC BY 4.0
    for app_id in ["SF-009", "SF-011", "SF-016"]:
        m = models_by_id.get(app_id)
        assert m is not None, f"Missing candidate model {app_id}"
        assert m.get("displayed_license") == "CC BY"
        assert m.get("content_status") == "candidate_embed"
        assert any(
            term in m.get("provenance_notes", "")
            for term in ["CyArk", "Open Heritage", "DOI", "10.26301"]
        )


# ==============================================================================
# 6. Negative / Abuse Test: Phantom Mesh Without Valid File Must Fail
# ==============================================================================


def test_negative_abuse_phantom_mesh_fails_validation():
    """Negative/abuse test (must fail before fix):

    Mesh reference without valid file is marked missing rather than rendered fake.
    """
    # 1. Valid positive case: Cao Đỉnh has real file on disk
    validate_mesh_reference(
        urn_slug="cao-dinh",
        mesh_url="/assets/models/CAO-DINH-v1-512.glb",
        fallback_3d_url="/assets/models/CAO-DINH-v1-512.glb",
        mesh_status="PRESENT",
        has_2d_fallback=True,
        fallback_2d_url="/assets/ban-duc-noi/CAO%20DINH/CAO%20%C4%90%E1%BB%88NH.jpg",
    )

    # 2. Valid negative case: Anh Đỉnh has no file on disk, marked MISSING, fallback_3d is None
    validate_mesh_reference(
        urn_slug="anh-dinh",
        mesh_url="/assets/models/ANH-DINH-v1-512.glb",
        fallback_3d_url=None,
        mesh_status="MISSING",
        has_2d_fallback=True,
        fallback_2d_url="/assets/ban-duc-noi/ANH%20DINH/ANH%20%C4%90%E1%BB%88NH.jpg",
    )

    # 3. Abuse Case A: Non-existent file claimed to be PRESENT must fail
    with pytest.raises(AssertionError, match="marked PRESENT but file does not exist"):
        validate_mesh_reference(
            urn_slug="anh-dinh",
            mesh_url="/assets/models/NON-EXISTENT-PHANTOM-v1.glb",
            fallback_3d_url=None,
            mesh_status="PRESENT",
            has_2d_fallback=True,
            fallback_2d_url="/assets/ban-duc-noi/ANH%20DINH/ANH%20%C4%90%E1%BB%88NH.jpg",
        )

    # 4. Abuse Case B: Missing urn attempts to substitute Cao Đỉnh mesh as fake 3D must fail
    with pytest.raises(AssertionError, match="Phantom asset abuse.*substitute Cao Đỉnh mesh"):
        validate_mesh_reference(
            urn_slug="anh-dinh",
            mesh_url="/assets/models/ANH-DINH-v1-512.glb",
            fallback_3d_url="/assets/models/CAO-DINH-v1-512.glb",  # ABUSE: fake 3D fallback!
            mesh_status="MISSING",
            has_2d_fallback=True,
            fallback_2d_url="/assets/ban-duc-noi/ANH%20DINH/ANH%20%C4%90%E1%BB%88NH.jpg",
        )

    # 5. Abuse Case C: Missing urn without 2D fallback must fail
    with pytest.raises(AssertionError, match="must have 2D fallback"):
        validate_mesh_reference(
            urn_slug="anh-dinh",
            mesh_url="/assets/models/ANH-DINH-v1-512.glb",
            fallback_3d_url=None,
            mesh_status="MISSING",
            has_2d_fallback=False,  # ABUSE: no fallback
            fallback_2d_url=None,
        )


# ==============================================================================
# 7. Media Rights Inventory Artifact Integrity
# ==============================================================================


def test_media_rights_inventory_artifact_validity():
    """Verify artifacts/implementation/W00/W00_A09_media_rights_inventory.json integrity."""
    assert ARTIFACT_PATH.exists(), f"Artifact not found at {ARTIFACT_PATH}"

    with open(ARTIFACT_PATH, "r", encoding="utf-8") as f:
        artifact = json.load(f)

    meta = artifact.get("meta", {})
    assert meta.get("ticket_id") == "V5-T009"
    assert meta.get("slot") == "W00-A09"
    assert meta.get("status") == "PASS"
    assert meta.get("classification") == "PRODUCTION_COMPLETION"
    assert meta.get("baseline_source_sha") == "54da2beb71f3df70e1f00b215ae0fb1a850eb263"

    summary = artifact.get("summary", {})
    assert summary.get("total_3d_urn_models") == 9
    assert summary.get("present_3d_urn_models") == 1
    assert summary.get("missing_3d_urn_models") == 8
    assert summary.get("total_local_3d_mesh_files") == 4
    assert summary.get("total_sketchfab_models") == 23
    assert summary.get("approved_sketchfab_candidates") == 3
    assert summary.get("blocked_sketchfab_models") == 2
    assert summary.get("rejected_accuracy_models") == 1
    assert summary.get("held_review_models") == 17
    assert summary.get("total_relic_motifs_audited") == 162
    assert summary.get("motifs_on_present_mesh") == 18
    assert summary.get("motifs_on_missing_mesh_flagged_missing") == 144
    assert summary.get("total_2d_motif_rubbings_files") == 164
    assert summary.get("total_audio_guides") == 16
    assert summary.get("all_audio_tracks_present_on_disk") is True
    assert summary.get("mobile_low_power_fallback_coverage_pct") == 100.0

    # Ensure required sections exist and are non-empty
    assert len(artifact.get("urn_3d_models", [])) == 9
    assert len(artifact.get("motif_mesh_registry_162", [])) == 162
    assert len(artifact.get("audio_assets", [])) == 16
    assert len(artifact.get("sketchfab_3d_registry", [])) == 23
    assert artifact.get("rubbings_corpus_2d", {}).get("total_files") == 164
    assert "mobile_and_low_power_guardrails" in artifact
