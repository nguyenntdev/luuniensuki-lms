"""
Generate 162 Relic Dataset Inventory for W00-A08 (V5-T008).
Performs static audit of all 9 Urns and 162 motifs in data/*Data*Dinh.json and
cross-references with data/motif-coordinates-*.json and mesh assets.
"""

import json
import glob
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
ARTIFACT_PATH = ROOT_DIR / "artifacts/implementation/W00/W00_A08_162_relic_inventory.json"

URN_MAP = [
    ("cao_dinh", "data/05_Data_CaoDinh.json", "data/motif-coordinates-cao-dinh.json", "Cao Đỉnh", "高鼎"),
    ("nhan_dinh", "data/06_Data_NhanDinh.json", "data/motif-coordinates-nhan-dinh.json", "Nhân Đỉnh", "仁鼎"),
    ("chuong_dinh", "data/07_Data_ChuongDinh.json", "data/motif-coordinates-chuong-dinh.json", "Chương Đỉnh", "章鼎"),
    ("anh_dinh", "data/08_Data_AnhDinh.json", "data/motif-coordinates-anh-dinh.json", "Anh Đỉnh", "英鼎"),
    ("nghi_dinh", "data/09_Data_NghiDinh.json", "data/motif-coordinates-nghi-dinh.json", "Nghị Đỉnh", "毅鼎"),
    ("thuan_dinh", "data/10_Data_ThuanDinh.json", "data/motif-coordinates-thuan-dinh.json", "Thuần Đỉnh", "純鼎"),
    ("tuyen_dinh", "data/11_Data_TuyenDinh.json", "data/motif-coordinates-tuyen-dinh.json", "Tuyên Đỉnh", "宣鼎"),
    ("du_dinh", "data/12_Data_DuDinh.json", "data/motif-coordinates-du-dinh.json", "Dụ Đỉnh", "裕鼎"),
    ("huyen_dinh", "data/13_Data_HuyenDinh.json", "data/motif-coordinates-huyen-dinh.json", "Huyền Đỉnh", "玄鼎"),
]

def generate_inventory():
    all_urns_data = []
    all_motifs = []
    missing_han_nom = []
    category_counts = {}

    for slug, json_file, coord_file, name_vi, name_han in URN_MAP:
        p_json = ROOT_DIR / json_file
        p_coord = ROOT_DIR / coord_file

        with open(p_json, "r", encoding="utf-8") as f:
            motifs = json.load(f)

        coords_dict = {}
        if p_coord.exists():
            with open(p_coord, "r", encoding="utf-8") as f:
                coords_list = json.load(f)
                coords_dict = {c["motif_name"]: c for c in coords_list}

        urn_entry = {
            "slug": slug,
            "name_vi": name_vi,
            "name_han_nom": name_han,
            "data_file": json_file,
            "coord_file": coord_file,
            "motif_count": len(motifs)
        }
        all_urns_data.append(urn_entry)

        for m in motifs:
            mid = m["id"]
            name_vi_val = m.get("name_vi")
            han_nom = m.get("name_han_nom") or ""
            has_han = bool(han_nom.strip())
            if not has_han:
                missing_han_nom.append({
                    "id": mid,
                    "urn": slug,
                    "name_vi": name_vi_val
                })

            cat = m.get("category", "unknown")
            category_counts[cat] = category_counts.get(cat, 0) + 1

            coord_entry = coords_dict.get(name_vi_val)

            motif_record = {
                "id": mid,
                "urn_slug": slug,
                "name_vi": name_vi_val,
                "name_en": m.get("name_en"),
                "name_han_nom": han_nom,
                "has_han_nom": has_han,
                "category": cat,
                "rarity": m.get("rarity"),
                "urn_location": m.get("urn_location"),
                "is_ai_generated": m.get("is_ai_generated", False),
                "has_coordinates": coord_entry is not None,
                "coordinates": coord_entry if coord_entry else None,
                "mesh_3d_id": m.get("3d_mesh_id"),
                "thumbnail_url": m.get("thumbnail_url")
            }
            all_motifs.append(motif_record)

    artifact = {
        "version": "v6.0-w00",
        "baseline_source_sha": "54da2beb71f3df70e1f00b215ae0fb1a850eb263",
        "summary": {
            "total_urns": len(all_urns_data),
            "total_motifs": len(all_motifs),
            "unique_motif_ids": len(set(m["id"] for m in all_motifs)),
            "expected_motifs": 162,
            "motifs_per_urn_expected": 18,
            "coordinates_coverage": f"{sum(1 for m in all_motifs if m['has_coordinates'])}/{len(all_motifs)}",
            "valid_han_nom_count": len(all_motifs) - len(missing_han_nom),
            "missing_han_nom_count": len(missing_han_nom),
            "category_distribution": category_counts,
        },
        "urns": all_urns_data,
        "missing_han_nom_motifs": missing_han_nom,
        "motifs": all_motifs
    }

    ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(ARTIFACT_PATH, "w", encoding="utf-8") as f:
        json.dump(artifact, f, indent=2, ensure_ascii=False)

    print(f"Generated relic inventory at {ARTIFACT_PATH}")
    print(f"Total Urns: {len(all_urns_data)}, Total Motifs: {len(all_motifs)}")
    print(f"Coordinates coverage: {artifact['summary']['coordinates_coverage']}")
    print(f"Missing Hán-Nôm count: {len(missing_han_nom)}")

if __name__ == "__main__":
    generate_inventory()
