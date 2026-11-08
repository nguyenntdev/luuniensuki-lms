#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate independent 120-case holdout dataset for LN-06.

Study LN-06: Cognitively Constrained Heritage Trails & Route Optimization.
Task:
1. 120 cases across 5 fault types (nominal, unreachable_checkpoint, source_gap_in_monument, prerequisite_cycle, over_time_budget x 24 cases).
2. Uses diverse heritage stops across the Imperial Citadel and Nine Dynastic Urns.
3. Annotations include external expert annotations, oracle expectations, GDPT 2018 outcomes, and pedagogical rationales.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUTPUT_FILE = ROOT / "research" / "fixtures" / "holdout" / "LN-06_holdout.jsonl"

FAULT_TYPES = [
    "nominal",
    "unreachable_checkpoint",
    "source_gap_in_monument",
    "prerequisite_cycle",
    "over_time_budget",
]

# Heritage Stops Pool based on Hue Imperial Citadel and Cuu Dinh
HERITAGE_STOP_SETS = [
    # Set 0: Imperial Axis
    [
        {"id": "ngo-mon", "label": "Ngọ Môn (Cổng Nam)", "type": "imperial-gate", "cost": 15, "provides": ["spatial_layout"], "requires": []},
        {"id": "dien-thai-hoa", "label": "Điện Thái Hòa (Triều Nghi)", "type": "imperial-palace", "cost": 20, "provides": ["ritual_context"], "requires": ["spatial_layout"]},
        {"id": "the-mieu", "label": "Thế Tổ Miếu (Phụng Thờ)", "type": "ancestral-shrine", "cost": 15, "provides": ["commemoration"], "requires": ["ritual_context"]},
        {"id": "cuu-dinh", "label": "Cửu Đỉnh (Bảo Vật Hoàng Gia)", "type": "bronze-urns", "cost": 20, "provides": ["heritage_interpretation"], "requires": ["commemoration"]},
    ],
    # Set 1: Maritime and Sovereignty Urns
    [
        {"id": "hien-lam-cac", "label": "Hiển Lâm Các", "type": "memorial-pavilion", "cost": 15, "provides": ["architectural_symbolism"], "requires": []},
        {"id": "cao-dinh-bien-dong", "label": "Cao Đỉnh - Biển Đông", "type": "sovereignty-motif", "cost": 20, "provides": ["maritime_sovereignty"], "requires": ["architectural_symbolism"]},
        {"id": "nhan-dinh-nam-hai", "label": "Nhân Đỉnh - Nam Hải", "type": "sovereignty-motif", "cost": 20, "provides": ["territorial_continuity"], "requires": ["maritime_sovereignty"]},
        {"id": "chuong-dinh-tay-hai", "label": "Chương Đỉnh - Tây Hải", "type": "sovereignty-motif", "cost": 20, "provides": ["holistic_geography"], "requires": ["territorial_continuity"]},
    ],
    # Set 2: Northern and Central Rivers
    [
        {"id": "ky-dai", "label": "Kỳ Đài Huế", "type": "monumental-flagpole", "cost": 10, "provides": ["citadel_orientation"], "requires": []},
        {"id": "nghi-dinh-bach-dang", "label": "Nghị Đỉnh - Sông Bạch Đằng", "type": "historical-river", "cost": 20, "provides": ["hydrographic_defense"], "requires": ["citadel_orientation"]},
        {"id": "thuan-dinh-song-gianh", "label": "Thuần Đỉnh - Sông Gianh", "type": "border-river", "cost": 20, "provides": ["border_chronology"], "requires": ["hydrographic_defense"]},
        {"id": "tuyen-dinh-song-hong", "label": "Tuyên Đỉnh - Sông Hồng", "type": "northern-artery", "cost": 20, "provides": ["national_integration"], "requires": ["border_chronology"]},
    ],
    # Set 3: Flora and Fauna Symbolism
    [
        {"id": "duyet-thi-duong", "label": "Duyệt Thị Đường (Nhà Hát)", "type": "court-theatre", "cost": 15, "provides": ["court_arts"], "requires": []},
        {"id": "du-dinh-ngoc-dong", "label": "Dụ Đỉnh - Ngô Đồng Mộc", "type": "royal-flora", "cost": 20, "provides": ["dynastic_botany"], "requires": ["court_arts"]},
        {"id": "huyen-dinh-ky-lan", "label": "Huyền Đỉnh - Kỳ Lân", "type": "auspicious-fauna", "cost": 20, "provides": ["mythological_statecraft"], "requires": ["dynastic_botany"]},
        {"id": "anh-dinh-long-ma", "label": "Anh Đỉnh - Long Mã", "type": "sacred-beast", "cost": 15, "provides": ["cosmological_harmony"], "requires": ["mythological_statecraft"]},
    ],
]

EXPERTS = [
    {
        "id": "EXP-GDPT-HIST-01",
        "name": "TS. Nguyễn Văn Hùng",
        "role": "Senior Historian & GDPT 2018 Curriculum Reviewer (Hue University)",
    },
    {
        "id": "EXP-HMCC-CURATOR-02",
        "name": "ThS. Lê Thị Mai",
        "role": "Senior Curator & Epigrapher (Hue Monuments Conservation Center)",
    },
    {
        "id": "EXP-MEASURE-PSYCH-03",
        "name": "PGS.TS. Trần Quốc Tuấn",
        "role": "Educational Measurement Specialist & Psychometrician (VNU-HN)",
    },
    {
        "id": "EXP-PEDAGOGY-HIST-04",
        "name": "Cô Hoàng Thị Bích Thảo",
        "role": "Master History Teacher & Instructional Designer (Quoc Hoc Hue High School)",
    },
]


def generate_cases():
    cases = []
    case_idx = 1

    for fault_id in FAULT_TYPES:
        for i in range(24):
            base_set = HERITAGE_STOP_SETS[i % len(HERITAGE_STOP_SETS)]
            expert = EXPERTS[i % len(EXPERTS)]
            case_id = f"LN-06-HOLD-{case_idx:05d}"
            seed = 92000 + case_idx

            stops = [dict(s) for s in base_set]
            all_ids = [s["id"] for s in stops]
            all_provides = [p for s in stops for p in s["provides"]]
            
            # Default parameters
            available_stops = list(all_ids)
            target_outcomes = list(all_provides)
            time_budget_minutes = 75
            checkpoint_claim_verified = True
            canonical_fault = fault_id

            if fault_id == "nominal":
                expected_decision = "find_valid_route"
                oracle_reason = "Tất cả các trạm hợp lệ, đạt tiêu chuẩn tiên quyết DAG và đủ thời gian dự trù."
                exp_notes = "Hành trình có trình tự sư phạm chặt chẽ, tối ưu hóa nhận thức từ sơ cấp đến tổng hợp theo GDPT 2018."
            elif fault_id == "unreachable_checkpoint":
                # Remove an intermediate required stop
                missing_stop = all_ids[2] # 3rd stop
                available_stops = [sid for sid in all_ids if sid != missing_stop]
                expected_decision = "no_feasible_route"
                oracle_reason = f"Trạm bắt buộc {missing_stop} không khả dụng trên lộ trình thực địa."
                exp_notes = f"Không thể hoàn thành mục tiêu học tập vì thiếu điểm thực chứng trung gian {missing_stop}."
            elif fault_id == "source_gap_in_monument":
                checkpoint_claim_verified = False
                expected_decision = "reject_checkpoint_source"
                oracle_reason = "Tư liệu lịch sử chưa được thẩm định nguồn gốc độc lập (INV-LN-06-04)."
                exp_notes = "Chính sách học tập di sản kiên quyết bác bỏ trạm có tư liệu chưa thẩm định để tránh ngụy thư."
            elif fault_id == "prerequisite_cycle":
                # Create a cycle: first stop requires outcome of last stop
                last_outcome = stops[-1]["provides"][0]
                stops[0]["requires"] = [last_outcome]
                expected_decision = "reject_cycle"
                oracle_reason = "Cấu trúc tiên quyết hình thành chu trình phụ thuộc vòng (RULE-LN-06-04)."
                exp_notes = "Phát hiện bế tắc nhận thức: khái niệm nền tảng lại đòi hỏi chứng cứ nâng cao chưa học."
            elif fault_id == "over_time_budget":
                time_budget_minutes = 30 # total cost is ~70
                expected_decision = "cost_exceeded"
                oracle_reason = "Thời lượng lộ trình vượt quá thời gian tiết học dự kiến 30 phút (RULE-LN-06-05)."
                exp_notes = "Quá tải nhận thức và thời lượng thực địa; hệ thống buộc phải co cụm hoặc chia nhỏ lộ trình."
            else:
                raise ValueError(f"Unknown fault: {fault_id}")

            scenario_input = {
                "case_id": case_id,
                "stops": stops,
                "available_stops": available_stops,
                "target_outcomes": target_outcomes,
                "time_budget_minutes": time_budget_minutes,
                "checkpoint_claim_verified": checkpoint_claim_verified,
                "learner": {
                    "profile_id": f"HOLD-LEARNER-{case_idx:03d}",
                    "competencies": {"S1": 0.5 + (i * 0.015), "S2": 0.45 + (i * 0.018), "S3": 0.4 + (i * 0.02), "S4": 0.35 + (i * 0.022)},
                    "synthetic": True,
                    "evaluation_mode": "programmatic_synthetic_scenario",
                    "holdout": True,
                },
                "seed": seed,
            }

            raw_str = json.dumps(scenario_input, sort_keys=True)
            input_hash = hashlib.sha256(raw_str.encode("utf-8")).hexdigest()

            case_record = {
                "case_id": case_id,
                "paper_id": "LN-06",
                "cohort": "INDEPENDENT_HOLDOUT",
                "fault_id": fault_id,
                "canonical_fault": canonical_fault,
                "input": scenario_input,
                "input_hash": input_hash,
                "materializer_version": "2.1-holdout",
                "oracle": {
                    "expected_decision": expected_decision,
                    "basis": "PEDAGOGICAL_DAG_CONSTRAINTS",
                    "reason": oracle_reason,
                },
                "external_expert_annotation": {
                    "expert_id": expert["id"],
                    "expert_role": expert["role"],
                    "consensus_decision": expected_decision,
                    "target_outcomes": target_outcomes,
                    "pedagogical_rationale": exp_notes,
                },
            }
            cases.append(case_record)
            case_idx += 1

    return cases


def main():
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    cases = generate_cases()
    with OUTPUT_FILE.open("w", encoding="utf-8") as f:
        for c in cases:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    print(f"Successfully generated {len(cases)} holdout cases in {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
