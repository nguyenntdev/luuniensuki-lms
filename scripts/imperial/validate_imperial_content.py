#!/usr/bin/env python3
"""Standalone content integrity validator for STTT Imperial City dataset.

Validates:
1. data/imperial/zones_and_sites.json:
   - 4 required spatial zones
   - 16 required historical monuments
   - At least 8 sites marked L2_LEARNING_READY
   - Complete pedagogical tasks, inquiry questions, primary sources, and S1-S4 rubrics for L2 sites
2. data/imperial/aerial_map_manifest.json:
   - Licensed metadata (slug, title_vi, 4096x3072, image/webp, sha256, license_kind, license_status)
   - Normalized UV coordinates (0.0 <= u <= 1.0, 0.0 <= v <= 1.0)
   - Cross-referencing: site_id / site_slug in annotations match existing sites without duplicates

Usage:
    python -m scripts.imperial.validate_imperial_content [--repo-root PATH] [--out PATH] [--fail-on-warn]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

REQUIRED_ZONES: tuple[str, ...] = (
    "central-ceremonial-axis",
    "ancestral-worship-space",
    "purple-forbidden-city",
    "royal-living-gardens",
)

REQUIRED_SITES: tuple[str, ...] = (
    "ngo-mon",
    "cau-trung-dao",
    "san-dai-trieu-nghi",
    "dien-thai-hoa",
    "the-to-mieu",
    "hien-lam-cac",
    "hung-to-mieu",
    "trieu-to-mieu",
    "dai-cung-mon",
    "dien-can-chanh",
    "dien-kien-trung",
    "duyet-thi-duong",
    "thai-binh-lau",
    "cung-dien-tho",
    "cung-truong-sanh",
    "dien-phung-tien",
)

EXPECTED_L2_SITES: tuple[str, ...] = (
    "ngo-mon",
    "san-dai-trieu-nghi",
    "dien-thai-hoa",
    "the-to-mieu",
    "hien-lam-cac",
    "dien-can-chanh",
    "dien-kien-trung",
    "duyet-thi-duong",
    "cung-dien-tho",
)

RUBRIC_KEYS: tuple[tuple[str, ...], ...] = (
    ("S1_spatial", "S1", "s1_spatial"),
    ("S2_temporal", "S2", "s2_temporal"),
    ("S3_evidence", "S3", "s3_evidence"),
    ("S4_argument", "S4_reasoning", "S4", "s4_argument"),
)


def validate_zones_and_sites(
    data: dict[str, Any], errors: list[str], warnings: list[str]
) -> dict[str, Any]:
    """Validate data/imperial/zones_and_sites.json structure and educational rubrics."""
    stats: dict[str, Any] = {
        "zone_count": 0,
        "site_count": 0,
        "l2_site_count": 0,
        "l1_site_count": 0,
    }

    if data.get("content_scope") != "STTT_IMPERIAL_CITY":
        errors.append(f"zones_and_sites: invalid or missing content_scope '{data.get('content_scope')}'")

    zones = data.get("zones", [])
    if not isinstance(zones, list):
        errors.append("zones_and_sites: 'zones' must be a list")
        zones = []
    stats["zone_count"] = len(zones)

    zone_slugs: set[str] = set()
    for z in zones:
        slug = z.get("slug")
        if not slug:
            errors.append(f"zones_and_sites: zone missing slug: {z}")
            continue
        if slug in zone_slugs:
            errors.append(f"zones_and_sites: duplicate zone slug: '{slug}'")
        zone_slugs.add(slug)
        if not z.get("title_vi"):
            errors.append(f"zones_and_sites: zone '{slug}' missing title_vi")

    for req_zone in REQUIRED_ZONES:
        if req_zone not in zone_slugs:
            errors.append(f"zones_and_sites: missing required spatial zone '{req_zone}'")

    sites = data.get("sites", [])
    if not isinstance(sites, list):
        errors.append("zones_and_sites: 'sites' must be a list")
        sites = []
    stats["site_count"] = len(sites)

    site_slugs: set[str] = set()
    site_ids: set[str] = set()

    for site in sites:
        slug = site.get("slug")
        site_id = site.get("id")
        name_vi = site.get("name_vi")
        zone_slug = site.get("zone_slug")
        level = site.get("learning_level")
        condition = site.get("condition")

        if not slug:
            errors.append(f"zones_and_sites: site missing slug: {site}")
            continue
        if slug in site_slugs:
            errors.append(f"zones_and_sites: duplicate site slug: '{slug}'")
        site_slugs.add(slug)

        if not site_id:
            errors.append(f"zones_and_sites: site '{slug}' missing id")
        else:
            if site_id in site_ids:
                errors.append(f"zones_and_sites: duplicate site id: '{site_id}'")
            site_ids.add(site_id)

        if not name_vi:
            errors.append(f"zones_and_sites: site '{slug}' missing name_vi")

        if zone_slug not in zone_slugs:
            errors.append(f"zones_and_sites: site '{slug}' references unknown zone '{zone_slug}'")

        if not condition:
            errors.append(f"zones_and_sites: site '{slug}' missing condition")

        if not site.get("historical_summary"):
            errors.append(f"zones_and_sites: site '{slug}' missing historical_summary")

        if level == "L2_LEARNING_READY":
            stats["l2_site_count"] += 1
            # Check L2 required fields
            inquiry_q = site.get("guiding_inquiry_question") or site.get("guiding_question")
            if not inquiry_q or not str(inquiry_q).strip():
                errors.append(f"zones_and_sites: L2 site '{slug}' missing guiding inquiry question")

            sources = site.get("primary_sources") or (
                [site.get("source_reference")] if site.get("source_reference") else []
            )
            if not sources or not isinstance(sources, list) or len(sources) == 0:
                errors.append(f"zones_and_sites: L2 site '{slug}' missing verified primary source reference")
            else:
                for s in sources:
                    stitle = s.get("source_title") or s.get("primary_source")
                    if not stitle:
                        errors.append(f"zones_and_sites: L2 site '{slug}' source missing title")

            rubrics = site.get("rubrics", {})
            if not isinstance(rubrics, dict):
                errors.append(f"zones_and_sites: L2 site '{slug}' rubrics must be an object")
            else:
                for rubric_group in RUBRIC_KEYS:
                    if not any(k in rubrics for k in rubric_group):
                        errors.append(
                            f"zones_and_sites: L2 site '{slug}' missing rubric from group {rubric_group}"
                        )

            task = site.get("pedagogical_task")
            if not isinstance(task, dict):
                errors.append(f"zones_and_sites: L2 site '{slug}' missing pedagogical_task object")
            else:
                if not task.get("task_prompt") or not str(task.get("task_prompt")).strip():
                    errors.append(f"zones_and_sites: L2 site '{slug}' pedagogical_task missing task_prompt")
        elif level == "L1_DOCUMENTED":
            stats["l1_site_count"] += 1
        else:
            errors.append(f"zones_and_sites: site '{slug}' has unrecognized learning_level '{level}'")

    for req_site in REQUIRED_SITES:
        if req_site not in site_slugs:
            errors.append(f"zones_and_sites: missing required monument '{req_site}'")

    if stats["l2_site_count"] < 8:
        errors.append(
            f"zones_and_sites: expected at least 8 L2_LEARNING_READY sites, found {stats['l2_site_count']}"
        )

    stats["site_slugs"] = site_slugs
    stats["site_ids"] = site_ids
    return stats


def validate_aerial_manifest(
    data: dict[str, Any],
    valid_site_slugs: set[str],
    valid_site_ids: set[str],
    errors: list[str],
    warnings: list[str],
) -> dict[str, Any]:
    """Validate data/imperial/aerial_map_manifest.json and normalized UV coordinates."""
    stats: dict[str, Any] = {
        "annotation_count": 0,
        "valid_uv_count": 0,
    }

    if data.get("content_scope") != "STTT_IMPERIAL_CITY":
        errors.append(f"aerial_manifest: invalid content_scope '{data.get('content_scope')}'")

    if data.get("slug") != "dai-noi-aerial-v1":
        errors.append(f"aerial_manifest: expected slug 'dai-noi-aerial-v1', got '{data.get('slug')}'")

    if not data.get("title_vi"):
        errors.append("aerial_manifest: missing title_vi")

    if data.get("version") != 1:
        warnings.append(f"aerial_manifest: version is {data.get('version')}, expected 1")

    if data.get("width_px") != 4096:
        errors.append(f"aerial_manifest: expected width_px 4096, got {data.get('width_px')}")

    if data.get("height_px") != 3072:
        errors.append(f"aerial_manifest: expected height_px 3072, got {data.get('height_px')}")

    if data.get("mime_type") != "image/webp":
        errors.append(f"aerial_manifest: expected mime_type 'image/webp', got '{data.get('mime_type')}'")

    sha = data.get("image_sha256", "")
    if not re.fullmatch(r"^[0-9a-f]{64}$", sha):
        errors.append(f"aerial_manifest: image_sha256 must be a 64-char lowercase hex hash, got '{sha}'")

    if not data.get("source_title"):
        errors.append("aerial_manifest: missing source_title")

    if not data.get("credit_text"):
        errors.append("aerial_manifest: missing credit_text")

    if data.get("license_kind") != "educational_fair_use":
        errors.append(f"aerial_manifest: expected license_kind 'educational_fair_use', got '{data.get('license_kind')}'")

    if data.get("license_status") != "approved":
        errors.append(f"aerial_manifest: expected license_status 'approved', got '{data.get('license_status')}'")

    annotations = data.get("initial_annotations", [])
    if not isinstance(annotations, list):
        errors.append("aerial_manifest: 'initial_annotations' must be a list")
        annotations = []
    stats["annotation_count"] = len(annotations)

    annotated_site_slugs: set[str] = set()

    for idx, anno in enumerate(annotations):
        u = anno.get("u")
        v = anno.get("v")
        site_slug = anno.get("site_slug")
        site_id = anno.get("site_id")

        if site_slug:
            if site_slug in annotated_site_slugs:
                errors.append(f"aerial_manifest: duplicate annotation for site_slug '{site_slug}'")
            annotated_site_slugs.add(site_slug)

            if valid_site_slugs and site_slug not in valid_site_slugs:
                errors.append(f"aerial_manifest: annotation references non-existent site_slug '{site_slug}'")

        if site_id and valid_site_ids and site_id not in valid_site_ids:
            errors.append(f"aerial_manifest: annotation references non-existent site_id '{site_id}'")

        if u is None or not isinstance(u, (int, float)):
            errors.append(f"aerial_manifest: annotation [{idx}] missing or non-numeric u")
        elif not (0.0 <= float(u) <= 1.0):
            errors.append(f"aerial_manifest: annotation [{idx}] u={u} outside [0.0, 1.0] bounds")

        if v is None or not isinstance(v, (int, float)):
            errors.append(f"aerial_manifest: annotation [{idx}] missing or non-numeric v")
        elif not (0.0 <= float(v) <= 1.0):
            errors.append(f"aerial_manifest: annotation [{idx}] v={v} outside [0.0, 1.0] bounds")

        if u is not None and v is not None and 0.0 <= float(u) <= 1.0 and 0.0 <= float(v) <= 1.0:
            stats["valid_uv_count"] += 1

    for req_site in REQUIRED_SITES:
        if req_site not in annotated_site_slugs:
            errors.append(f"aerial_manifest: missing annotation for monument '{req_site}'")

    return stats


def validate_imperial_content(repo_root: Path | None = None) -> dict[str, Any]:
    """Execute full content integrity validation across imperial dataset files."""
    if repo_root is None:
        repo_root = Path(__file__).resolve().parents[2]

    zones_path = repo_root / "data" / "imperial" / "zones_and_sites.json"
    manifest_path = repo_root / "data" / "imperial" / "aerial_map_manifest.json"

    errors: list[str] = []
    warnings: list[str] = []

    if not zones_path.exists():
        errors.append(f"Missing required file: {zones_path}")
        zones_data: dict[str, Any] = {}
    else:
        try:
            zones_data = json.loads(zones_path.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"Failed to parse {zones_path}: {exc}")
            zones_data = {}

    if not manifest_path.exists():
        errors.append(f"Missing required file: {manifest_path}")
        manifest_data: dict[str, Any] = {}
    else:
        try:
            manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"Failed to parse {manifest_path}: {exc}")
            manifest_data = {}

    zones_stats = validate_zones_and_sites(zones_data, errors, warnings)
    manifest_stats = validate_aerial_manifest(
        manifest_data,
        zones_stats.get("site_slugs", set()),
        zones_stats.get("site_ids", set()),
        errors,
        warnings,
    )

    return {
        "success": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "zones_stats": {
            "zone_count": zones_stats.get("zone_count", 0),
            "site_count": zones_stats.get("site_count", 0),
            "l2_site_count": zones_stats.get("l2_site_count", 0),
            "l1_site_count": zones_stats.get("l1_site_count", 0),
        },
        "manifest_stats": manifest_stats,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate STTT Imperial City historical dataset")
    parser.add_argument("--repo-root", type=Path, default=None)
    parser.add_argument("--out", type=Path, default=None, help="Output validation report JSON")
    parser.add_argument("--fail-on-warn", action="store_true", help="Fail if any warning occurs")
    args = parser.parse_args()

    repo_root = args.repo_root or Path(__file__).resolve().parents[2]
    result = validate_imperial_content(repo_root)

    print(f"[VALIDATE] Validated STTT Imperial dataset at {repo_root}")
    print(f"  Zones: {result['zones_stats']['zone_count']} zones, {result['zones_stats']['site_count']} sites")
    print(f"  Learning Levels: {result['zones_stats']['l2_site_count']} L2 ready, {result['zones_stats']['l1_site_count']} L1 documented")
    print(f"  Map Annotations: {result['manifest_stats']['annotation_count']} annotations, {result['manifest_stats']['valid_uv_count']} valid UV")

    if result["warnings"]:
        print(f"\n[WARN] {len(result['warnings'])} warning(s):")
        for w in result["warnings"]:
            print(f"  - {w}")

    if result["errors"]:
        print(f"\n[FAIL] {len(result['errors'])} error(s):")
        for err in result["errors"]:
            print(f"  - {err}")

    if args.out:
        out_path = args.out
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\n[REPORT] Saved validation summary to {out_path}")

    if not result["success"] or (args.fail_on_warn and result["warnings"]):
        return 1

    print("\n[SUCCESS] Content integrity validation passed with zero errors!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
