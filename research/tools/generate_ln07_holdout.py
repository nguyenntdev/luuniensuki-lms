#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate independent 120-case holdout dataset for Study LN-07.

Universal Design for Learning (UDL) & Multimodal Pedagogical Equivalence.
5 fault types × 24 cases = 120 cases:
- nominal_3d_available (24 cases): Standard desktop/broadband device, WebGL enabled, 3D GLB available
- webgl_context_loss (24 cases): Hardware WebGL acceleration disabled or context lost
- low_bandwidth_device (24 cases): Remote/rural school or constrained mobile connection (50-100 kbps)
- visual_impairment_screen_reader (24 cases): Assistive technology user with screen reader & keyboard navigation
- missing_monument_asset (24 cases): CDN/server 3D asset missing or corrupted (404/checksum failure)
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys

OUTPUT_PATH = pathlib.Path(__file__).resolve().parents[1] / "fixtures" / "holdout" / "LN-07_holdout.jsonl"

RELICS = [
    {"id": "cao-dinh", "label": "Cao Đỉnh", "type": "bronze-urn", "motif": "long", "motif_name": "Rồng (Long) và Thái dương"},
    {"id": "nhan-dinh", "label": "Nhân Đỉnh", "type": "bronze-urn", "motif": "ky-lan", "motif_name": "Kỳ Lân và Sông Hương"},
    {"id": "chuong-dinh", "label": "Chương Đỉnh", "type": "bronze-urn", "motif": "do-quyen", "motif_name": "Chim Đỗ Quyên và Núi Ngự Bình"},
    {"id": "anh-dinh", "label": "Anh Đỉnh", "type": "bronze-urn", "motif": "su-tu", "motif_name": "Sư Tử và Sông Gianh"},
    {"id": "nghi-dinh", "label": "Nghị Đỉnh", "type": "bronze-urn", "motif": "phuong-hoang", "motif_name": "Chim Phượng và Sông Bạch Đằng"},
    {"id": "thuan-dinh", "label": "Thuần Đỉnh", "type": "bronze-urn", "motif": "ngua-duc", "motif_name": "Ngựa và Cây Ba La Mật"},
    {"id": "tuyen-dinh", "label": "Tuyên Đỉnh", "type": "bronze-urn", "motif": "khi", "motif_name": "Khỉ và Sông Lô"},
    {"id": "du-dinh", "label": "Dụ Đỉnh", "type": "bronze-urn", "motif": "lon-rung", "motif_name": "Lợn Rừng và Cây Ngô Đồng"},
    {"id": "huyen-dinh", "label": "Huyền Đỉnh", "type": "bronze-urn", "motif": "cop", "motif_name": "Cọp và Sông Cửu Long"},
    {"id": "ngo-mon", "label": "Ngọ Môn", "type": "imperial-gate", "motif": "ngu-phung", "motif_name": "Lầu Ngũ Phụng và Cổng vòm Nam"},
    {"id": "dien-thai-hoa", "label": "Điện Thái Hòa", "type": "imperial-palace", "motif": "ngai-vang", "motif_name": "Ngai vàng và 9 Rồng thếp vàng"},
    {"id": "the-to-mieu", "label": "Thế Tổ Miếu", "type": "ancestral-temple", "motif": "an-kham", "motif_name": "Án khám và Bài vị Hoàng gia"},
]

LEARNER_PROFILES = [
    {"profile_id": "SYN-HOLDOUT-STANDARD-01", "access": "standard", "competencies": {"S1": 0.4, "S2": 0.5, "S3": 0.3, "S4": 0.2}},
    {"profile_id": "SYN-HOLDOUT-STANDARD-02", "access": "standard", "competencies": {"S1": 0.8, "S2": 0.7, "S3": 0.6, "S4": 0.5}},
    {"profile_id": "SYN-HOLDOUT-RURAL-01", "access": "rural_mobile", "competencies": {"S1": 0.3, "S2": 0.2, "S3": 0.2, "S4": 0.1}},
    {"profile_id": "SYN-HOLDOUT-RURAL-02", "access": "rural_mobile", "competencies": {"S1": 0.7, "S2": 0.5, "S3": 0.4, "S4": 0.3}},
    {"profile_id": "SYN-HOLDOUT-ACCESSIBLE-01", "access": "assistive_tech", "competencies": {"S1": 0.5, "S2": 0.6, "S3": 0.7, "S4": 0.6}},
    {"profile_id": "SYN-HOLDOUT-ACCESSIBLE-02", "access": "assistive_tech", "competencies": {"S1": 0.9, "S2": 0.8, "S3": 0.9, "S4": 0.8}},
]

TASK_DEFINITIONS = [
    {
        "type": "identify_relief_relation",
        "description": "Xác định mối tương quan không gian và bố cục phù điêu trên hiện vật di sản Huế.",
        "required_affordances": ["visual_detail", "spatial_relation"],
    },
    {
        "type": "analyze_epigraphy_han_nom",
        "description": "Phân tích đặc điểm minh văn Hán-Nôm và độ nổi khối chạm khắc trên bảo vật Cửu Đỉnh.",
        "required_affordances": ["visual_detail", "relief_depth"],
    },
]


def make_deterministic_hash(data: dict) -> str:
    serialized = json.dumps(data, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def generate_cases() -> list[dict]:
    cases = []
    case_idx = 1
    source_commit = "9bd4bd98f0b893e02d48643eb475016014204790"

    # 5 fault types, each with 24 cases
    fault_types = [
        ("nominal_3d_available", "Đủ điều kiện phần cứng và đồ họa 3D; đáp ứng toàn diện affordance sư phạm"),
        ("webgl_context_loss", "WebGL bị mất ngữ cảnh đồ họa; tự động chuyển sang bản dập nổi 2D bảo toàn tương quan không gian"),
        ("low_bandwidth_device", "Băng thông mạng hạn chế (<500 kbps); chuyển sang bản dập 2D dung lượng nhẹ bảo toàn affordance"),
        ("visual_impairment_screen_reader", "Người học khiếm thị sử dụng trình đọc màn hình; cung cấp bản thuyết minh âm thanh có chép lời và mô tả ngữ nghĩa"),
        ("missing_monument_asset", "Mô hình 3D trên CDN bị thiếu hoặc lỗi; chuyển sang bản dập bảo tồn từ kho tư liệu lưu trữ"),
    ]

    for fault_id, oracle_reason in fault_types:
        for relic_idx, relic in enumerate(RELICS):
            # 2 cases per relic = 24 cases per fault type
            for variant_idx in range(2):
                cid = f"LN-07-HOLD-{case_idx:05d}"
                task_def = TASK_DEFINITIONS[variant_idx % len(TASK_DEFINITIONS)]
                learner = LEARNER_PROFILES[(relic_idx * 2 + variant_idx) % len(LEARNER_PROFILES)]

                # Configure device constraints
                if fault_id == "nominal_3d_available":
                    device = {"webgl": True, "network_kbps": 3200 + variant_idx * 300, "keyboard_only": False, "screen_reader": False}
                    is_3d_available = True
                    expected_decision = "choose_feasible_modality"
                elif fault_id == "webgl_context_loss":
                    device = {"webgl": False, "network_kbps": 3000, "keyboard_only": False, "screen_reader": False, "webgl_context_lost": True}
                    is_3d_available = True
                    expected_decision = "choose_accessible_fallback"
                elif fault_id == "low_bandwidth_device":
                    device = {"webgl": True, "network_kbps": 80 + variant_idx * 20, "keyboard_only": False, "screen_reader": False}
                    is_3d_available = True
                    expected_decision = "choose_low_data_fallback"
                elif fault_id == "visual_impairment_screen_reader":
                    device = {"webgl": True, "network_kbps": 2200, "keyboard_only": True, "screen_reader": True}
                    is_3d_available = True
                    expected_decision = "choose_accessible_audio_text"
                elif fault_id == "missing_monument_asset":
                    device = {"webgl": True, "network_kbps": 3500, "keyboard_only": False, "screen_reader": False}
                    is_3d_available = False
                    expected_decision = "choose_curated_archive_fallback"
                else:
                    raise ValueError(f"Unknown fault: {fault_id}")

                # Configure multimodal options
                options = [
                    # 1. 3D GLB Model (Primary)
                    {
                        "id": f"{relic['id']}_3d_model",
                        "modality": "3d",
                        "kb": 1850,
                        "affordances": ["visual_detail", "spatial_relation", "relief_depth"],
                        "keyboard": True,
                        "requires_webgl": True,
                        "available": is_3d_available,
                    },
                    # 2. Naive Static Image (for B1 comparison: only generic visual_detail, lacks spatial relation / relief depth)
                    {
                        "id": f"{relic['id']}_static_photo",
                        "modality": "static_image",
                        "kb": 320,
                        "affordances": ["visual_detail"],
                        "keyboard": False,
                        "requires_webgl": False,
                        "alt_text": "",
                        "available": True,
                    },
                    # 3. Curated 2D Rubbing (Bản dập nổi Cửu Đỉnh - preserves full spatial & relief affordances at 95KB)
                    {
                        "id": f"{relic['id']}_rubbing_2d",
                        "modality": "2d",
                        "sub_type": "rubbing",
                        "kb": 95,
                        "affordances": ["visual_detail", "spatial_relation", "relief_depth"],
                        "keyboard": True,
                        "requires_webgl": False,
                        "alt_text": f"Bản dập nổi hoa văn {relic['motif_name']} bảo toàn độ sâu và tương quan không gian",
                        "available": True,
                    },
                    # 4. Audio Guide with Synchronized Transcript
                    {
                        "id": f"{relic['id']}_audio_guide",
                        "modality": "audio",
                        "kb": 480,
                        "affordances": ["visual_detail", "spatial_relation", "relief_depth", "description"],
                        "keyboard": True,
                        "requires_webgl": False,
                        "transcript": True,
                        "screen_reader_ready": True,
                        "available": True,
                    },
                    # 5. Accessible Text Transcript with Semantic Layout
                    {
                        "id": f"{relic['id']}_structured_text",
                        "modality": "text",
                        "kb": 10,
                        "affordances": ["visual_detail", "spatial_relation", "relief_depth", "description"],
                        "keyboard": True,
                        "requires_webgl": False,
                        "screen_reader_ready": True,
                        "available": True,
                    },
                ]

                scenario_input = {
                    "case_id": cid,
                    "fault_id": fault_id,
                    "content": {
                        "id": relic["id"],
                        "label": relic["label"],
                        "type": relic["type"],
                        "motif": relic["motif"],
                        "motif_name": relic["motif_name"],
                    },
                    "device": device,
                    "learner": learner,
                    "options": options,
                    "task": {
                        "type": task_def["type"],
                        "description": task_def["description"],
                        "required_affordances": task_def["required_affordances"],
                        "transcript_required": device.get("screen_reader", False),
                    },
                    "seed": 20261108 + case_idx,
                }

                input_hash = make_deterministic_hash(scenario_input)

                record = {
                    "case_id": cid,
                    "cohort": "INDEPENDENT_HOLDOUT",
                    "fault_id": fault_id,
                    "input": scenario_input,
                    "input_hash": input_hash,
                    "materializer_version": "2.0-holdout",
                    "oracle": {
                        "basis": "DESIGN_SPEC_EMPIRICAL_HOLDOUT",
                        "expected_decision": expected_decision,
                        "reason": oracle_reason,
                    },
                    "paper_id": "LN-07",
                    "source_commit": source_commit,
                }
                cases.append(record)
                case_idx += 1

    return cases


def main():
    cases = generate_cases()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        for c in cases:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")

    print(f"Generated {len(cases)} cases into {OUTPUT_PATH}")
    fault_counts = {}
    for c in cases:
        fault_counts[c["fault_id"]] = fault_counts.get(c["fault_id"], 0) + 1
    print("Fault breakdown:", fault_counts)


if __name__ == "__main__":
    main()
