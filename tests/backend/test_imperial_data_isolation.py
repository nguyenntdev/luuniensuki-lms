"""Automated tests for STTT Imperial data isolation and content integrity.

Tests:
1. Data isolation: zero forbidden legacy terms in any imperial directory or file.
2. Crawler sensitivity: verify detection of forbidden terms in positive controls.
3. Content integrity validation: full schema check with 0 errors.
4. Structural compliance: 4 zones, 16 monuments, >=8 L2_LEARNING_READY sites with full inquiry dossiers.
5. Aerial manifest & normalized UV coordinates: 4096x3072, licensed status, 0.0 <= u,v <= 1.0.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.imperial.audit_no_legacy_content import (
    FORBIDDEN_TERMS,
    audit_scope,
    scan_file_for_violations,
)
from scripts.imperial.validate_imperial_content import (
    EXPECTED_L2_SITES,
    REQUIRED_SITES,
    REQUIRED_ZONES,
    validate_imperial_content,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_no_legacy_content_in_imperial_scope():
    """Verify no forbidden terms exist in any imperial codebase scope."""
    violations = audit_scope(REPO_ROOT)
    assert violations == [], (
        f"Found {len(violations)} forbidden term violation(s) in STTT scope:\n"
        + "\n".join(f"  {v.file_path}:{v.line_number} -> {v.matched_term}" for v in violations)
    )


def test_audit_crawler_catches_forbidden_terms(tmp_path: Path):
    """Verify that scan_file_for_violations reliably flags forbidden terms."""
    clean_file = tmp_path / "clean.json"
    clean_file.write_text(json.dumps({"monument": "Ngọ Môn", "reign": "Minh Mạng"}), encoding="utf-8")
    assert scan_file_for_violations(clean_file) == []

    for term in ("cửu đỉnh", "cuu dinh", "162", "bản đúc nổi", "relief motif"):
        dirty_file = tmp_path / f"dirty_{term.replace(' ', '_')}.txt"
        dirty_file.write_text(f"Line 1: safe\nLine 2: Contains {term} in sentence.\nLine 3: safe", encoding="utf-8")
        violations = scan_file_for_violations(dirty_file)
        assert len(violations) >= 1, f"Crawler failed to catch forbidden term: {term}"
        assert violations[0].matched_term == term
        assert violations[0].line_number == 2


def test_imperial_content_integrity_validation():
    """Run standalone content integrity validator and assert zero errors."""
    result = validate_imperial_content(REPO_ROOT)
    assert result["success"] is True, f"Validation failed with errors: {result['errors']}"
    assert result["errors"] == []
    assert result["zones_stats"]["zone_count"] == 4
    assert result["zones_stats"]["site_count"] == 16
    assert result["zones_stats"]["l2_site_count"] >= 8
    assert result["manifest_stats"]["valid_uv_count"] == 16


def test_zones_and_sites_structure():
    """Verify 4 spatial zones and 16 historical monuments meet all pedadogical requirements."""
    zones_file = REPO_ROOT / "data" / "imperial" / "zones_and_sites.json"
    assert zones_file.exists(), f"Missing {zones_file}"

    data = json.loads(zones_file.read_text(encoding="utf-8"))
    assert data.get("content_scope") == "STTT_IMPERIAL_CITY"

    # 4 spatial zones
    zones = data.get("zones", [])
    zone_slugs = {z["slug"] for z in zones}
    assert len(zones) == 4
    for rz in REQUIRED_ZONES:
        assert rz in zone_slugs, f"Missing required zone: {rz}"

    # 16 historical monuments
    sites = data.get("sites", [])
    assert len(sites) == 16
    site_slugs = {s["slug"] for s in sites}
    for rs in REQUIRED_SITES:
        assert rs in site_slugs, f"Missing required site: {rs}"

    # Check L2 sites
    l2_sites = [s for s in sites if s.get("learning_level") == "L2_LEARNING_READY"]
    assert len(l2_sites) >= 8, f"Found only {len(l2_sites)} L2 sites, expected at least 8"

    for site in l2_sites:
        slug = site["slug"]
        assert slug in EXPECTED_L2_SITES

        # 1. Guiding inquiry question
        question = site.get("guiding_inquiry_question") or site.get("guiding_question")
        assert question and len(question.strip()) > 10, f"Site {slug} missing inquiry question"

        # 2. Historical summary
        summary = site.get("historical_summary")
        assert summary and len(summary.strip()) > 20, f"Site {slug} missing summary"

        # 3. Condition
        condition = site.get("condition")
        assert condition and len(condition.strip()) > 0, f"Site {slug} missing condition"

        # 4. Verified primary source reference
        sources = site.get("primary_sources") or [site.get("source_reference")]
        assert sources and len(sources) >= 1, f"Site {slug} missing primary sources"
        for s in sources:
            title = s.get("source_title") or s.get("primary_source")
            assert title and len(title.strip()) > 0, f"Site {slug} source missing title"

        # 5. Rubrics S1-S4
        rubrics = site.get("rubrics", {})
        assert isinstance(rubrics, dict)
        assert any(k in rubrics for k in ("S1_spatial", "S1")), f"Site {slug} missing S1 rubric"
        assert any(k in rubrics for k in ("S2_temporal", "S2")), f"Site {slug} missing S2 rubric"
        assert any(k in rubrics for k in ("S3_evidence", "S3")), f"Site {slug} missing S3 rubric"
        assert any(k in rubrics for k in ("S4_argument", "S4_reasoning", "S4")), f"Site {slug} missing S4 rubric"

        # 6. Pedagogical task prompt
        task = site.get("pedagogical_task", {})
        prompt = task.get("task_prompt")
        assert prompt and len(prompt.strip()) > 10, f"Site {slug} missing pedagogical task prompt"


def test_aerial_map_manifest_and_uv_coords():
    """Verify aerial map manifest licensing, dimension standards, and normalized UV bounds."""
    manifest_file = REPO_ROOT / "data" / "imperial" / "aerial_map_manifest.json"
    assert manifest_file.exists(), f"Missing {manifest_file}"

    data = json.loads(manifest_file.read_text(encoding="utf-8"))
    assert data.get("content_scope") == "STTT_IMPERIAL_CITY"
    assert data.get("slug") == "dai-noi-aerial-v1"
    assert data.get("version") == 1
    assert data.get("width_px") == 4096
    assert data.get("height_px") == 3072
    assert data.get("mime_type") == "image/webp"
    assert len(data.get("image_sha256", "")) == 64
    assert data.get("license_kind") == "educational_fair_use"
    assert data.get("license_status") == "approved"
    assert data.get("review_status") == "published"
    assert data.get("is_active") is True

    annotations = data.get("initial_annotations", [])
    assert len(annotations) == 16

    annotated_slugs = set()
    for anno in annotations:
        slug = anno["site_slug"]
        assert slug not in annotated_slugs, f"Duplicate annotation for {slug}"
        annotated_slugs.add(slug)

        u = float(anno["u"])
        v = float(anno["v"])
        assert 0.0 <= u <= 1.0, f"Annotation {slug} u={u} outside [0.0, 1.0]"
        assert 0.0 <= v <= 1.0, f"Annotation {slug} v={v} outside [0.0, 1.0]"

    for rs in REQUIRED_SITES:
        assert rs in annotated_slugs, f"Missing annotation for monument: {rs}"


def test_cross_dataset_integrity():
    """Verify 1-to-1 matching between zones_and_sites.json and aerial_map_manifest.json."""
    zones_file = REPO_ROOT / "data" / "imperial" / "zones_and_sites.json"
    manifest_file = REPO_ROOT / "data" / "imperial" / "aerial_map_manifest.json"

    zones_data = json.loads(zones_file.read_text(encoding="utf-8"))
    manifest_data = json.loads(manifest_file.read_text(encoding="utf-8"))

    site_map = {s["slug"]: s for s in zones_data["sites"]}
    anno_map = {a["site_slug"]: a for a in manifest_data["initial_annotations"]}

    assert set(site_map.keys()) == set(anno_map.keys()), "Sites and annotations slugs mismatch"

    for slug, site in site_map.items():
        anno = anno_map[slug]
        assert anno["site_id"] == site["id"]
        assert anno["name_vi"] == site["name_vi"]
