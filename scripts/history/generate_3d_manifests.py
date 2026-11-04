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

    # Load 162 motif rights registry if available
    root_dir = data_dir.parent
    inv_path = root_dir / "artifacts" / "implementation" / "W00" / "W00_A09_media_rights_inventory.json"
    reg_lookup: dict[str, dict[str, Any]] = {}
    if inv_path.exists():
        try:
            with open(inv_path, "r", encoding="utf-8") as f:
                inv_data = json.load(f)
            for m in inv_data.get("motif_mesh_registry_162", []):
                reg_lookup[f"{m['urn_slug']}:{m['name_vi'].strip().lower()}"] = m
        except Exception as e:
            print(f"Warning: could not load media rights inventory: {e}", file=sys.stderr)

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
                "model_url": "/assets/models/CAO-DINH-v1-1k.glb" if urn_slug == "cao-dinh" else None,
                "creator": "Trung tâm Bảo tồn Di tích Cố đô Huế (HMCC) & Histolab",
                "rights_owner": "Trung tâm Bảo tồn Di tích Cố đô Huế (HMCC)",
                "rights_attribution": "Trung tâm Bảo tồn Di tích Cố đô Huế (HMCC)",
                "license": "CC BY 4.0 / Educational Fair Use",
                "rights_status": "cleared",
                "public_distribution_allowed": True,
                "public_display_allowed": True,
            }

            lookup_key = f"{urn_slug}:{motif_name.strip().lower()}"
            if lookup_key in reg_lookup:
                m_info = reg_lookup[lookup_key]
                hotspot_data["3d_mesh_id"] = m_info.get("3d_mesh_id")
                hotspot_data["motif_id"] = m_info.get("id")
                hotspot_data["fallback_2d"] = m_info.get("fallback_2d")

            all_hotspots.append(hotspot_data)

            if urn_slug not in manifests_by_urn:
                urn_upper = urn_slug.upper()
                is_cao_dinh = urn_slug == "cao-dinh"
                
                # Checksum mapping
                checksum_map = {
                    "cao-dinh": "6f7e73424c18c5e6504ee25eda103b56958b1e79348937e152e60731a2bcd16a",
                    "nhan-dinh": "7395b93f6966e1802f8fe108511652c2d7c8fd0846578ecbd742134936f99e69",
                    "chuong-dinh": "50b47cce23604aa2af4f22274d702997f3101a43f5ac09c6e144f16b412c50f7",
                    "anh-dinh": "3adb2fb9fab2ae0f8f6b6f2dbf23f2366252726cf3c5026d6e00d24a09e45100",
                    "nghi-dinh": "01640017e63d04caf254b2cd9da198d23fdc1dce339fcc67ba4a69c8ae572258",
                    "thuan-dinh": "8955a4fba76294831d316709dda849ed6a6d183a6a9e0a570078ec12c7d071c7",
                    "tuyen-dinh": "faa8ab1610139914808e9b9da4ff6becc7a0c9b22a63aa67f0ee6f15322588fa",
                    "du-dinh": "5cd92c531332f19e0272a487e2ecbbebe7cdb7e58cc7effc13f7dcd5d5efecab",
                    "huyen-dinh": "38b6bde4551d8db9e29bdc36212ed584138238e36d2ded7be2b387e45f539e96",
                }
                
                # 2D fallback mapping
                fallback_2d_registry = {
                    "cao-dinh": {
                        "asset_url": "/assets/ban-duc-noi/CAO%20DINH/CAO%20%C4%90%E1%BB%88NH.jpg",
                        "disk_path": "ban-duc-noi/CAO DINH/CAO ĐỈNH.jpg",
                        "format": "image/jpeg",
                        "bytes": 8823,
                        "sha256": "3187abe1940c680a5145eac960e50230f45cf7382a6e647a61988b2124f82a28",
                        "rights_attribution": "Trung tâm Bảo tồn Di tích Cố đô Huế (HMCC)",
                        "legal_basis": "Public Domain (1835-1837 Imperial relic) / Academic Educational Fair Use",
                    },
                    "nhan-dinh": {
                        "asset_url": "/assets/ban-duc-noi/NHAN%20DINH/NH%C3%82N%20%C4%90%E1%BB%88NH.jpg",
                        "disk_path": "ban-duc-noi/NHAN DINH/NHÂN ĐỈNH.jpg",
                        "format": "image/jpeg",
                        "bytes": 9974,
                        "sha256": "7395b93f6966e1802f8fe108511652c2d7c8fd0846578ecbd742134936f99e69",
                        "rights_attribution": "Trung tâm Bảo tồn Di tích Cố đô Huế (HMCC)",
                        "legal_basis": "Public Domain (1835-1837 Imperial relic) / Academic Educational Fair Use",
                    },
                    "chuong-dinh": {
                        "asset_url": "/assets/ban-duc-noi/CHUONG%20DINH/CH%C6%AF%C6%A0NG%20%C4%90%E1%BB%88NH.jpg",
                        "disk_path": "ban-duc-noi/CHUONG DINH/CHƯƠNG ĐỈNH.jpg",
                        "format": "image/jpeg",
                        "bytes": 8706,
                        "sha256": "50b47cce23604aa2af4f22274d702997f3101a43f5ac09c6e144f16b412c50f7",
                        "rights_attribution": "Trung tâm Bảo tồn Di tích Cố đô Huế (HMCC)",
                        "legal_basis": "Public Domain (1835-1837 Imperial relic) / Academic Educational Fair Use",
                    },
                    "anh-dinh": {
                        "asset_url": "/assets/ban-duc-noi/ANH%20DINH/ANH%20%C4%90%E1%BB%88NH.jpg",
                        "disk_path": "ban-duc-noi/ANH DINH/ANH ĐỈNH.jpg",
                        "format": "image/jpeg",
                        "bytes": 10467,
                        "sha256": "3adb2fb9fab2ae0f8f6b6f2dbf23f2366252726cf3c5026d6e00d24a09e45100",
                        "rights_attribution": "Trung tâm Bảo tồn Di tích Cố đô Huế (HMCC)",
                        "legal_basis": "Public Domain (1835-1837 Imperial relic) / Academic Educational Fair Use",
                    },
                    "nghi-dinh": {
                        "asset_url": "/assets/ban-duc-noi/NGHI%20DINH/NGHI%20DINH.jpg",
                        "disk_path": "ban-duc-noi/NGHI DINH/NGHI DINH.jpg",
                        "format": "image/jpeg",
                        "bytes": 12104,
                        "sha256": "01640017e63d04caf254b2cd9da198d23fdc1dce339fcc67ba4a69c8ae572258",
                        "rights_attribution": "Trung tâm Bảo tồn Di tích Cố đô Huế (HMCC)",
                        "legal_basis": "Public Domain (1835-1837 Imperial relic) / Academic Educational Fair Use",
                    },
                    "thuan-dinh": {
                        "asset_url": "/assets/ban-duc-noi/THUAN%20DINH/THU%E1%BA%A6N%20%C4%90%E1%BB%88NH.jpg",
                        "disk_path": "ban-duc-noi/THUAN DINH/THUẦN ĐỈNH.jpg",
                        "format": "image/jpeg",
                        "bytes": 10449,
                        "sha256": "8955a4fba76294831d316709dda849ed6a6d183a6a9e0a570078ec12c7d071c7",
                        "rights_attribution": "Trung tâm Bảo tồn Di tích Cố đô Huế (HMCC)",
                        "legal_basis": "Public Domain (1835-1837 Imperial relic) / Academic Educational Fair Use",
                    },
                    "tuyen-dinh": {
                        "asset_url": "/assets/ban-duc-noi/TUYEN%20DINH/TUYEN%20DINH.jpg",
                        "disk_path": "ban-duc-noi/TUYEN DINH/TUYEN DINH.jpg",
                        "format": "image/jpeg",
                        "bytes": 11441,
                        "sha256": "faa8ab1610139914808e9b9da4ff6becc7a0c9b22a63aa67f0ee6f15322588fa",
                        "rights_attribution": "Trung tâm Bảo tồn Di tích Cố đô Huế (HMCC)",
                        "legal_basis": "Public Domain (1835-1837 Imperial relic) / Academic Educational Fair Use",
                    },
                    "du-dinh": {
                        "asset_url": "/assets/ban-duc-noi/DU%20DINH/D%E1%BB%A4%20%C4%90%E1%BB%88NH.jpg",
                        "disk_path": "ban-duc-noi/DU DINH/DỤ ĐỈNH.jpg",
                        "format": "image/jpeg",
                        "bytes": 9593,
                        "sha256": "5cd92c531332f19e0272a487e2ecbbebe7cdb7e58cc7effc13f7dcd5d5efecab",
                        "rights_attribution": "Trung tâm Bảo tồn Di tích Cố đô Huế (HMCC)",
                        "legal_basis": "Public Domain (1835-1837 Imperial relic) / Academic Educational Fair Use",
                    },
                    "huyen-dinh": {
                        "asset_url": "/assets/ban-duc-noi/HUYEN%20DINH/HUY%E1%BB%80N%20%C4%90%E1%BB%88NH.jpg",
                        "disk_path": "ban-duc-noi/HUYEN DINH/HUYỀN ĐỈNH.jpg",
                        "format": "image/jpeg",
                        "bytes": 9527,
                        "sha256": "38b6bde4551d8db9e29bdc36212ed584138238e36d2ded7be2b387e45f539e96",
                        "rights_attribution": "Trung tâm Bảo tồn Di tích Cố đô Huế (HMCC)",
                        "legal_basis": "Public Domain (1835-1837 Imperial relic) / Academic Educational Fair Use",
                    },
                }
                
                fb_info = fallback_2d_registry.get(urn_slug, fallback_2d_registry["cao-dinh"])

                manifests_by_urn[urn_slug] = {
                    "urn_slug": urn_slug,
                    "model_version": 1,
                    "hotspot_version": 1,
                    "lods": {
                        "low": {
                            "url": f"/assets/models/{urn_upper}-v1-512.glb",
                            "fallback_url": "/assets/models/CAO-DINH-v1-512.glb" if is_cao_dinh else None,
                            "sha256": "51f5baf131e85257186b0e4a89087870ff66e4c787f7775bea797fc2550d8611" if is_cao_dinh else None,
                            "bytes": 5207460 if is_cao_dinh else 0,
                            **({} if is_cao_dinh else {"status": "MISSING"}),
                        },
                        "medium": {
                            "url": f"/assets/models/{urn_upper}-v1-1k.glb",
                            "fallback_url": "/assets/models/CAO-DINH-v1-1k.glb" if is_cao_dinh else None,
                            "sha256": "6f7e73424c18c5e6504ee25eda103b56958b1e79348937e152e60731a2bcd16a" if is_cao_dinh else None,
                            "bytes": 27417688 if is_cao_dinh else 0,
                            **({} if is_cao_dinh else {"status": "MISSING"}),
                        },
                        "high": {
                            "url": f"/assets/models/{urn_upper}-v1-2k.glb",
                            "fallback_url": "/assets/models/CAO-DINH-v1-2k.glb" if is_cao_dinh else None,
                            "sha256": "59d7f26f5af647d727b3ce4855a8533ca39c96825e1c9dea672a94cb32e42e74" if is_cao_dinh else None,
                            "bytes": 30353888 if is_cao_dinh else 0,
                            **({} if is_cao_dinh else {"status": "MISSING"}),
                        },
                    },
                    "hotspots": [],
                    "mesh_status": "PRESENT" if is_cao_dinh else "MISSING",
                    "has_2d_fallback": True,
                    "fallback_2d_url": fb_info["asset_url"],
                    "creator": "Trung tâm Bảo tồn Di tích Cố đô Huế (HMCC) & Histolab",
                    "rights_owner": "Trung tâm Bảo tồn Di tích Cố đô Huế (HMCC)",
                    "license": "CC BY 4.0 / Educational Fair Use",
                    "rights_status": "cleared",
                    "public_distribution_allowed": True,
                    "public_display_allowed": True,
                    "rights_attribution": "Trung tâm Bảo tồn Di tích Cố đô Huế (HMCC) & Histolab",
                    "checksum": checksum_map[urn_slug],
                    "viewer_fallback": {
                        "type": "2d_rubbing",
                        "component": "UrnAccessibleFallback",
                        "asset_url": fb_info["asset_url"],
                        "disk_path": fb_info["disk_path"],
                        "format": fb_info["format"],
                        "bytes": fb_info["bytes"],
                        "sha256": fb_info["sha256"],
                        "rights_attribution": fb_info["rights_attribution"],
                        "legal_basis": fb_info["legal_basis"],
                    },
                    "fallback_2d": fb_info,
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
