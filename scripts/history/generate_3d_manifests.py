#!/usr/bin/env python3
"""3D Manifest & Hotspot Registry Generator (Spec Section 43).

Reads coordinate entries from data/motif-coordinates-*.json (162 total across 9 urns)
and generates 3D model manifests with urn_slug, model_version, hotspot_version,
LODs (low/medium/high), and relief hotspot targets (camera_position, camera_target, bounding_radius).

Writes outputs to:
- frontend/public/models/manifests/{urn_slug}.json
- public/models/manifests/{urn_slug}.json
- frontend/public/models/manifests/index.json

Usage:
    python -m scripts.history.generate_3d_manifests
"""
from __future__ import annotations

import json
import math
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any


def slugify(text: str) -> str:
    """Convert string to canonical URL slug handling Vietnamese diacritics."""
    text = text.lower().strip()
    text = re.sub(r'[đĐ]', 'd', text)
    text = unicodedata.normalize('NFKD', text)
    text = ''.join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')


def calculate_camera_position(pos_x: float, pos_y: float, pos_z: float, offset_distance: float = 1.5) -> list[float]:
    """Calculate an optimal camera focal position facing the relief hotspot."""
    dist = math.sqrt(pos_x * pos_x + pos_z * pos_z)
    if dist > 0.001:
        nx = pos_x / dist
        nz = pos_z / dist
    else:
        nx, nz = 0.0, 1.0

    cam_x = round(pos_x + nx * offset_distance, 4)
    cam_y = round(pos_y + 0.2, 4)
    cam_z = round(pos_z + nz * offset_distance, 4)
    return [cam_x, cam_y, cam_z]


def generate_manifests(data_dir: Path, output_dirs: list[Path]) -> dict[str, Any]:
    coord_files = sorted(data_dir.glob("motif-coordinates-*.json"))
    if not coord_files:
        raise FileNotFoundError(f"No coordinate files matching motif-coordinates-*.json found in {data_dir}")

    all_hotspots: list[dict[str, Any]] = []
    manifests_by_urn: dict[str, dict[str, Any]] = {}

    for file_path in coord_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                entries = json.load(f)
        except Exception as exc:
            print(f"Error reading {file_path}: {exc}", file=sys.stderr)
            continue

        if not isinstance(entries, list):
            continue

        for entry in entries:
            if not isinstance(entry, dict):
                continue

            urn_slug = str(entry.get("urn_slug") or "").strip()
            motif_name = str(entry.get("motif_name") or "").strip()
            mesh_name = str(entry.get("mesh_name") or motif_name).strip()
            pos_x = float(entry.get("pos_x", 0.0))
            pos_y = float(entry.get("pos_y", 0.0))
            pos_z = float(entry.get("pos_z", 0.0))
            bounding_radius = float(entry.get("bounding_radius", 0.08))

            if not urn_slug or not motif_name:
                continue

            relief_slug = slugify(motif_name)
            hotspot_id = f"{urn_slug}-{relief_slug}"
            cam_pos = calculate_camera_position(pos_x, pos_y, pos_z)
            cam_target = [round(pos_x, 4), round(pos_y, 4), round(pos_z, 4)]

            hotspot_data = {
                "hotspot_id": hotspot_id,
                "urn_slug": urn_slug,
                "relief_slug": relief_slug,
                "relief_name": motif_name,
                "mesh_name": mesh_name,
                "pos": [round(pos_x, 4), round(pos_y, 4), round(pos_z, 4)],
                "camera_position": cam_pos,
                "camera_target": cam_target,
                "bounding_radius": bounding_radius,
                "coordinate_version": 1,
                "model_version": 1,
            }
            all_hotspots.append(hotspot_data)

            if urn_slug not in manifests_by_urn:
                urn_upper = urn_slug.upper()
                manifests_by_urn[urn_slug] = {
                    "urn_slug": urn_slug,
                    "model_version": 1,
                    "hotspot_version": 1,
                    "lods": {
                        "low": {
                            "url": f"/assets/models/{urn_upper}-v1-512.glb",
                            "fallback_url": "/assets/models/CAO-DINH-v1-512.glb",
                            "sha256": "placeholder-sha256-512",
                            "bytes": 524288,
                        },
                        "medium": {
                            "url": f"/assets/models/{urn_upper}-v1-1k.glb",
                            "fallback_url": "/assets/models/CAO-DINH-v1-1k.glb",
                            "sha256": "placeholder-sha256-1k",
                            "bytes": 1048576,
                        },
                        "high": {
                            "url": f"/assets/models/{urn_upper}-v1-2k.glb",
                            "fallback_url": "/assets/models/CAO-DINH-v1-2k.glb",
                            "sha256": "placeholder-sha256-2k",
                            "bytes": 2097152,
                        },
                    },
                    "hotspots": [],
                }
            manifests_by_urn[urn_slug]["hotspots"].append(hotspot_data)

    print(f"Processed {len(all_hotspots)} hotspot entries across {len(manifests_by_urn)} urns.")

    # Write output manifests
    for out_dir in output_dirs:
        out_dir.mkdir(parents=True, exist_ok=True)
        for urn_slug, manifest in manifests_by_urn.items():
            urn_path = out_dir / f"{urn_slug}.json"
            with open(urn_path, "w", encoding="utf-8") as f:
                json.dump(manifest, f, ensure_ascii=False, indent=2)

        index_path = out_dir / "index.json"
        with open(index_path, "w", encoding="utf-8") as f:
            json.dump({
                "total_urns": len(manifests_by_urn),
                "total_hotspots": len(all_hotspots),
                "urns": list(manifests_by_urn.keys()),
                "manifests": manifests_by_urn,
            }, f, ensure_ascii=False, indent=2)

        print(f"✅ Generated manifests in {out_dir}")

    return manifests_by_urn


def main() -> int:
    root_dir = Path(__file__).resolve().parents[2]
    data_dir = root_dir / "data"
    output_dirs = [
        root_dir / "frontend" / "public" / "models" / "manifests",
        root_dir / "public" / "models" / "manifests",
    ]

    generate_manifests(data_dir, output_dirs)
    return 0


if __name__ == "__main__":
    sys.exit(main())
