# -*- coding: utf-8 -*-
"""Test suite for V5-T030 (Wave W02, Slot A10).

Goal: Reproducible 162 publication audit CLI tool.
Validates:
  1. CLI execution produces a valid audit report JSON.
  2. Negative abuse test: Report must NEVER output "162/162 READY" if any required asset
     or verification is missing.
  3. Negative abuse test: Simulated missing asset causes CLI to exit with code 1 and flag BLOCKED.
  4. Manifest validation strictly fails with non-zero exit code if unverified or failing items
     are marked READY.
  5. Accurate tracking of READY vs BLOCKED items across all 5 quality criteria:
     (a) Canonical slug & valid entity row
     (b) 3D coordinate mapping
     (c) 2D rubbing asset existence
     (d) Hán-Nôm review status
     (e) Sourced claims count and verification status
  6. Database auditing integration for HistoricalEntity and Motifs.
  7. Per-object ASCII table output generation.
  8. Completion artifact structure and integrity.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from scripts.dev.audit_162_publication import (
    DEFAULT_OUTPUT_PATH,
    KNOWN_MISSING_HAN_NOM_IDS,
    REPO_ROOT,
    URN_SPECS,
    audit_all_motifs,
    audit_database,
    audit_single_motif,
    validate_manifest_file,
    validate_publication_safety,
)

CLI_SCRIPT = REPO_ROOT / "scripts" / "dev" / "audit_162_publication.py"


def test_cli_execution_produces_valid_audit_report(tmp_path: Path):
    """Test that executing the CLI produces a valid audit report JSON."""
    out_file = tmp_path / "test_audit_report.json"
    res = subprocess.run(
        [
            sys.executable,
            str(CLI_SCRIPT),
            "--output",
            str(out_file),
        ],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, f"CLI execution failed with returncode {res.returncode}:\n{res.stderr}"
    assert out_file.exists(), f"Expected report at {out_file}"

    with open(out_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Validate top-level metadata
    assert data["ticket"] == "V5-T030"
    assert data["slot"] == "W02-A10"
    assert data["status"] == "COMPLETED"
    assert data["classification"] == "PRODUCTION_COMPLETION"
    assert data["version"] == "v6.0-w02"

    # Validate summary structure
    summary = data["summary"]
    assert summary["total_urns"] == 9
    assert summary["total_motifs"] == 162
    assert summary["unique_motif_ids"] == 162
    assert summary["ready_count"] + summary["blocked_count"] == 162

    # Validate 5 mandatory criteria in criteria_summary
    crit_sum = summary["criteria_summary"]
    assert "canonical_entity" in crit_sum
    assert "spatial_3d_coordinates" in crit_sum
    assert "rubbing_2d_assets" in crit_sum
    assert "han_nom_review" in crit_sum
    assert "sourced_claims_verification" in crit_sum

    # Also validate backwards compatible keys
    assert "han_nom_presence" in crit_sum
    assert "bibliographic_citations" in crit_sum
    assert "verification_status" in crit_sum

    # Validate per-object table exists in summary
    assert "per_object_table" in summary
    assert len(summary["per_object_table"]) == 162

    # Validate list counts
    assert len(data["urns"]) == 9
    assert len(data["motifs"]) == 162

    for urn in data["urns"]:
        assert urn["motif_count"] == 18
        assert urn["publication_status"] in ("READY", "BLOCKED")

    for motif in data["motifs"]:
        assert motif["publication_status"] in ("READY", "BLOCKED")
        assert "criteria" in motif
        assert len(motif["criteria"]) >= 5
        assert "canonical_slug" in motif


def test_negative_abuse_never_reports_162_ready_when_checks_fail():
    """Negative abuse test: Script does NOT report 162/162 READY when required checks fail.

    Verifies:
      1. Overall ready_count is not 162 (publication_ready must be False).
      2. The 4 known relics missing Hán-Nôm glyphs are flagged and strictly BLOCKED.
      3. Items with unreviewed AI-generated prose are flagged as unverified and BLOCKED.
    """
    report = audit_all_motifs(root_dir=REPO_ROOT)
    summary = report["summary"]

    # 1. Negative assertion: Cannot report publication_ready=True on unverified baseline data
    assert summary["publication_ready"] is False, "Must NOT report publication_ready=True on baseline data"
    assert summary["ready_count"] < 162, f"ready_count should be < 162, got {summary['ready_count']}"
    assert summary["ready_ratio"] != "162/162"
    assert summary["blocked_count"] > 0

    # 2. Verify all 4 known missing Hán-Nôm motifs are flagged and BLOCKED
    flagged_ids = {item["id"] for item in summary["flagged_missing_han_nom"]}
    assert flagged_ids == KNOWN_MISSING_HAN_NOM_IDS, (
        f"Flagged missing Hán-Nôm set mismatch: {flagged_ids} vs {KNOWN_MISSING_HAN_NOM_IDS}"
    )

    motifs_by_id = {m["id"]: m for m in report["motifs"]}
    for mid in KNOWN_MISSING_HAN_NOM_IDS:
        m_entry = motifs_by_id[mid]
        assert m_entry["publication_status"] == "BLOCKED"
        assert m_entry["criteria"]["han_nom_review"]["passed"] is False
        assert any("hán-nôm" in r.lower() for r in m_entry["blocking_reasons"])

    # 3. Verify unreviewed AI content is strictly BLOCKED
    for m_entry in report["motifs"]:
        # In baseline data, legacy content has no expert signoff and no citations
        assert m_entry["publication_status"] == "BLOCKED"
        assert m_entry["criteria"]["sourced_claims_verification"]["passed"] is False


def test_negative_abuse_simulated_missing_asset_causes_cli_exit_code_1_and_flags_blocked(tmp_path: Path):
    """Negative abuse: Simulated missing asset causes CLI to exit with code 1 and flag BLOCKED."""
    sim_data_dir = tmp_path / "sim_data"
    sim_data_dir.mkdir(parents=True)

    # Copy coordinate points manifest
    with open(REPO_ROOT / "data" / "cuu_dinh_coordinate_points.json", "r", encoding="utf-8") as f:
        coords = json.load(f)
    with open(sim_data_dir / "cuu_dinh_coordinate_points.json", "w", encoding="utf-8") as f:
        json.dump(coords, f)

    # Copy urn data files, corrupting one motif's rubbing asset path in Cao Đỉnh
    for spec in URN_SPECS:
        src_file = REPO_ROOT / spec["data_file"]
        with open(src_file, "r", encoding="utf-8") as f:
            urn_data = json.load(f)
        if spec["slug"] == "cao_dinh":
            urn_data[0]["thumbnail_url"] = "/assets/missing_rubbing_non_existent_9999.jpg"
            urn_data[0]["name_vi"] = "Họa Tiết Thiếu File Ảnh"
        dst_file = sim_data_dir / Path(spec["data_file"]).name
        with open(dst_file, "w", encoding="utf-8") as f:
            json.dump(urn_data, f)
        src_coord = REPO_ROOT / spec["coord_file"]
        if src_coord.exists():
            with open(src_coord, "r", encoding="utf-8") as f:
                c_data = json.load(f)
            with open(sim_data_dir / Path(spec["coord_file"]).name, "w", encoding="utf-8") as f:
                json.dump(c_data, f)

    out_file = tmp_path / "sim_audit_report.json"

    # Run CLI with --strict against the simulated dataset
    res = subprocess.run(
        [
            sys.executable,
            str(CLI_SCRIPT),
            "--data-dir",
            str(sim_data_dir),
            "--output",
            str(out_file),
            "--strict",
            "--quiet",
        ],
        capture_output=True,
        text=True,
    )

    # Must exit with non-zero code 1
    assert res.returncode == 1, f"Expected returncode 1, got {res.returncode}:\n{res.stderr}"
    assert "STRICT GATE FAILURE" in res.stderr

    # Audit report must flag missing asset and BLOCKED status
    assert out_file.exists()
    with open(out_file, "r", encoding="utf-8") as f:
        report = json.load(f)

    motif_01 = next(m for m in report["motifs"] if m["id"] == "urn_cao_dinh_01")
    assert motif_01["publication_status"] == "BLOCKED"
    assert motif_01["criteria"]["rubbing_2d_asset"]["passed"] is False
    assert any("2D rubbing" in r for r in motif_01["blocking_reasons"])
    assert report["summary"]["publication_ready"] is False


def test_cli_fails_when_unverified_items_marked_ready(tmp_path: Path):
    """Negative abuse test: CLI fails with non-zero exit code if unverified items are marked READY."""
    tampered_manifest = {
        "version": "v6.0-w02",
        "summary": {"total_motifs": 1, "ready_count": 1, "blocked_count": 0},
        "motifs": [
            {
                "id": "urn_cao_dinh_01",
                "name_vi": "Cao Đỉnh",
                "publication_status": "READY",
                "criteria": {
                    "canonical_entity": {"passed": True},
                    "spatial_3d_coordinates": {"passed": True},
                    "rubbing_2d_asset": {"passed": True},
                    "han_nom_review": {"passed": True},
                    "sourced_claims_verification": {
                        "passed": False,
                        "details": {"status": "unreviewed"},
                        "reason": "Status unreviewed",
                    },
                    "verification_status": {
                        "passed": False,
                        "details": {"status": "unreviewed"},
                        "reason": "Status unreviewed",
                    },
                },
                "blocking_reasons": ["Status unreviewed"],
            }
        ],
    }
    tampered_file = tmp_path / "tampered_manifest.json"
    with open(tampered_file, "w", encoding="utf-8") as f:
        json.dump(tampered_manifest, f)

    res = subprocess.run(
        [
            sys.executable,
            str(CLI_SCRIPT),
            "--validate-manifest",
            str(tampered_file),
        ],
        capture_output=True,
        text=True,
    )
    assert res.returncode != 0, "CLI MUST fail with non-zero exit code when unverified item is marked READY"
    assert "CRITICAL PUBLICATION SAFETY VIOLATION" in res.stderr
    assert "urn_cao_dinh_01" in res.stderr


def test_programmatic_safety_validator_catches_all_failing_ready_items():
    """Verify programmatic validate_publication_safety catches violations across all 5 criteria."""
    # Case 1: unverified claims status
    corrupt_1 = {
        "motifs": [
            {
                "id": "item_1",
                "publication_status": "READY",
                "criteria": {
                    "sourced_claims_verification": {"passed": False, "details": {"status": "draft"}},
                    "verification_status": {"passed": False, "details": {"status": "draft"}},
                },
            }
        ]
    }
    is_safe, violations = validate_publication_safety(corrupt_1)
    assert not is_safe
    assert len(violations) > 0

    # Case 2: missing Hán-Nôm marked READY
    corrupt_2 = {
        "motifs": [
            {
                "id": "item_2",
                "publication_status": "READY",
                "criteria": {
                    "verification_status": {"passed": True, "details": {"status": "verified"}},
                    "han_nom_review": {"passed": False, "reason": "Missing glyph"},
                },
            }
        ]
    }
    is_safe, violations = validate_publication_safety(corrupt_2)
    assert not is_safe
    assert any("Hán-Nôm" in v for v in violations)

    # Case 3: missing rubbing asset marked READY
    corrupt_3 = {
        "motifs": [
            {
                "id": "item_3",
                "publication_status": "READY",
                "criteria": {
                    "rubbing_2d_asset": {"passed": False, "reason": "Missing image"},
                },
            }
        ]
    }
    is_safe, violations = validate_publication_safety(corrupt_3)
    assert not is_safe
    assert any("rubbing" in v.lower() for v in violations)

    # Case 4: missing 3D coordinates marked READY
    corrupt_4 = {
        "motifs": [
            {
                "id": "item_4",
                "publication_status": "READY",
                "criteria": {
                    "spatial_3d_coordinates": {"passed": False, "reason": "Missing 3D coords"},
                },
            }
        ]
    }
    is_safe, violations = validate_publication_safety(corrupt_4)
    assert not is_safe
    assert any("3d" in v.lower() for v in violations)

    # Case 5: failed canonical entity marked READY
    corrupt_5 = {
        "motifs": [
            {
                "id": "item_5",
                "publication_status": "READY",
                "criteria": {
                    "canonical_entity": {"passed": False, "reason": "Unknown slug"},
                },
            }
        ]
    }
    is_safe, violations = validate_publication_safety(corrupt_5)
    assert not is_safe
    assert any("canonical" in v.lower() for v in violations)

    # Valid verified READY item
    valid_ready = {
        "motifs": [
            {
                "id": "item_valid",
                "publication_status": "READY",
                "criteria": {
                    "canonical_entity": {"passed": True},
                    "spatial_3d_coordinates": {"passed": True},
                    "rubbing_2d_asset": {"passed": True},
                    "han_nom_review": {"passed": True},
                    "sourced_claims_verification": {"passed": True, "details": {"status": "verified"}},
                    "verification_status": {"passed": True, "details": {"status": "verified"}},
                },
            }
        ]
    }
    is_safe, violations = validate_publication_safety(valid_ready)
    assert is_safe
    assert len(violations) == 0


def test_accurate_tracking_of_ready_vs_blocked():
    """Verify accurate tracking of READY vs BLOCKED items across all 5 quality criteria."""
    report = audit_all_motifs(root_dir=REPO_ROOT)

    # 1. Verify 100% canonical slug resolution on dataset
    assert report["summary"]["criteria_summary"]["canonical_entity"]["passed"] == 162
    assert report["summary"]["criteria_summary"]["canonical_entity"]["failed"] == 0

    # 2. Verify 100% 3D spatial coordinate binding on existing dataset
    assert report["summary"]["criteria_summary"]["spatial_3d_coordinates"]["passed"] == 162
    assert report["summary"]["criteria_summary"]["spatial_3d_coordinates"]["failed"] == 0

    # 3. Verify 100% 2D rubbing asset presence on existing dataset
    assert report["summary"]["criteria_summary"]["rubbing_2d_assets"]["passed"] == 162
    assert report["summary"]["criteria_summary"]["rubbing_2d_assets"]["failed"] == 0

    # 4. Verify exactly 158 passed and 4 failed for Hán-Nôm glyph/reading
    assert report["summary"]["criteria_summary"]["han_nom_review"]["passed"] == 158
    assert report["summary"]["criteria_summary"]["han_nom_review"]["failed"] == 4

    # 5. Item-level criteria evaluation function
    coords_dict = {
        "Long": {"pos_x": 0.5, "pos_y": 0.5, "pos_z": 1.0, "bounding_radius": 0.08}
    }

    # Positive test: all 5 criteria satisfied -> READY
    perfect_motif = {
        "id": "urn_cao_dinh_02",
        "name_vi": "Long",
        "name_han_nom": "龍",
        "category": "linh_thu",
        "thumbnail_url": "/assets/ban-duc-noi/CAO%20DINH/LONG.jpg",
        "citations": [{"source_title": "Đại Nam Thực Lục", "source_type": "primary_source"}],
        "verification_status": "verified",
        "is_ai_generated": False,
    }
    res_perfect = audit_single_motif(
        motif=perfect_motif,
        coords_dict=coords_dict,
        urn_slug="cao_dinh",
        urn_name_vi="Cao Đỉnh",
        root_dir=REPO_ROOT,
    )
    assert res_perfect["publication_status"] == "READY"
    assert len(res_perfect["blocking_reasons"]) == 0
    assert res_perfect["criteria"]["canonical_entity"]["passed"] is True
    assert res_perfect["criteria"]["spatial_3d_coordinates"]["passed"] is True
    assert res_perfect["criteria"]["rubbing_2d_asset"]["passed"] is True
    assert res_perfect["criteria"]["han_nom_review"]["passed"] is True
    assert res_perfect["criteria"]["sourced_claims_verification"]["passed"] is True

    # Negative variation 1: Missing coordinates -> BLOCKED
    no_coords_motif = dict(perfect_motif)
    res_no_coords = audit_single_motif(
        motif=no_coords_motif,
        coords_dict={},
        urn_slug="cao_dinh",
        urn_name_vi="Cao Đỉnh",
        root_dir=REPO_ROOT,
    )
    assert res_no_coords["publication_status"] == "BLOCKED"
    assert res_no_coords["criteria"]["spatial_3d_coordinates"]["passed"] is False

    # Negative variation 2: Missing rubbing asset -> BLOCKED
    no_img_motif = dict(perfect_motif, thumbnail_url="/assets/non_existent_rubbing.jpg")
    res_no_img = audit_single_motif(
        motif=no_img_motif,
        coords_dict=coords_dict,
        urn_slug="cao_dinh",
        urn_name_vi="Cao Đỉnh",
        root_dir=REPO_ROOT,
    )
    assert res_no_img["publication_status"] == "BLOCKED"
    assert res_no_img["criteria"]["rubbing_2d_asset"]["passed"] is False

    # Negative variation 3: Missing Hán-Nôm -> BLOCKED
    no_han_motif = dict(perfect_motif, name_han_nom="")
    res_no_han = audit_single_motif(
        motif=no_han_motif,
        coords_dict=coords_dict,
        urn_slug="cao_dinh",
        urn_name_vi="Cao Đỉnh",
        root_dir=REPO_ROOT,
    )
    assert res_no_han["publication_status"] == "BLOCKED"
    assert res_no_han["criteria"]["han_nom_review"]["passed"] is False

    # Negative variation 4: Missing citation -> BLOCKED
    no_cite_motif = dict(perfect_motif, citations=[])
    res_no_cite = audit_single_motif(
        motif=no_cite_motif,
        coords_dict=coords_dict,
        urn_slug="cao_dinh",
        urn_name_vi="Cao Đỉnh",
        root_dir=REPO_ROOT,
    )
    assert res_no_cite["publication_status"] == "BLOCKED"
    assert res_no_cite["criteria"]["sourced_claims_verification"]["passed"] is False

    # Negative variation 5: Unreviewed status -> BLOCKED
    unreviewed_motif = dict(perfect_motif, verification_status="unreviewed")
    res_unreviewed = audit_single_motif(
        motif=unreviewed_motif,
        coords_dict=coords_dict,
        urn_slug="cao_dinh",
        urn_name_vi="Cao Đỉnh",
        root_dir=REPO_ROOT,
    )
    assert res_unreviewed["publication_status"] == "BLOCKED"
    assert res_unreviewed["criteria"]["sourced_claims_verification"]["passed"] is False


def test_cli_strict_gate_fails_on_blocked_items():
    """Verify that running CLI with --strict fails with exit code 1 when items are blocked."""
    res = subprocess.run(
        [
            sys.executable,
            str(CLI_SCRIPT),
            "--strict",
            "--quiet",
        ],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 1
    assert "STRICT GATE FAILURE" in res.stderr


def test_database_auditing_integration():
    """Verify database auditing integration with PostgreSQL."""
    db_url = os.environ.get("DATABASE_URL")
    res = audit_database(db_url)
    if db_url:
        assert res["audited"] is True
        assert res["connected"] is True
        assert "urns_in_db" in res
        assert "reliefs_in_db" in res
    else:
        assert res["audited"] is False
        assert res["connected"] is False


def test_cli_table_output():
    """Verify CLI prints formatted per-object status table when --table is passed."""
    res = subprocess.run(
        [
            sys.executable,
            str(CLI_SCRIPT),
            "--table",
        ],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    assert "PER-OBJECT STATUS TABLE:" in res.stdout
    assert "urn_cao_dinh_01" in res.stdout
    assert "cao-dinh-01" in res.stdout
    assert "urn_huyen_dinh_18" in res.stdout


def test_publication_audit_artifact_integrity():
    """Verify the committed completion artifact exists and conforms to specifications."""
    assert DEFAULT_OUTPUT_PATH.exists(), f"Artifact not found at {DEFAULT_OUTPUT_PATH}"
    with open(DEFAULT_OUTPUT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["ticket"] == "V5-T030"
    assert data["slot"] == "W02-A10"
    assert data["status"] == "COMPLETED"
    assert data["summary"]["total_motifs"] == 162
    assert data["summary"]["total_urns"] == 9
    assert len(data["motifs"]) == 162
    assert len(data["urns"]) == 9
    assert len(data["summary"]["flagged_missing_han_nom"]) == 4

    # Verify no unverified item is marked READY in the artifact
    is_safe, violations = validate_publication_safety(data)
    assert is_safe, f"Artifact contains illegal READY items: {violations}"
