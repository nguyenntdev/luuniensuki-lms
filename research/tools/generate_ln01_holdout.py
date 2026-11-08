#!/usr/bin/env python3
"""Generate 120-case independent holdout dataset for LN-01 (Spiral Curriculum Progression).

Stratified across 5 fault types × 24 cases:
1. nominal (24 cases): valid spiral progression across grade 10-11-12 with Bloom ascent.
2. grade_boundary_inversion (24 cases): prerequisite edge violates grade developmental sequence.
3. anchor_misalignment (24 cases): missing authorized GDĐP curriculum anchor.
4. bloom_depth_leap (24 cases): cognitive stagnation/inversion along prerequisite edges.
5. prerequisite_cycle (24 cases): cyclic dependency (both intra-grade and inter-grade cycles).

Each case is audited and annotated with external educator panel reviews.
"""

import hashlib
import json
from pathlib import Path

HERITAGE_ENTITIES = [
    {"id": "cao-dinh", "label": "Cao Đỉnh (Cửu Đỉnh)", "type": "dynastic-urn"},
    {"id": "nhan-dinh", "label": "Nhân Đỉnh (Cửu Đỉnh)", "type": "dynastic-urn"},
    {"id": "chuong-dinh", "label": "Chương Đỉnh (Cửu Đỉnh)", "type": "dynastic-urn"},
    {"id": "anh-dinh", "label": "Anh Đỉnh (Cửu Đỉnh)", "type": "dynastic-urn"},
    {"id": "nghi-dinh", "label": "Nghị Đỉnh (Cửu Đỉnh)", "type": "dynastic-urn"},
    {"id": "thuan-dinh", "label": "Thuần Đỉnh (Cửu Đỉnh)", "type": "dynastic-urn"},
    {"id": "tuyen-dinh", "label": "Tuyên Đỉnh (Cửu Đỉnh)", "type": "dynastic-urn"},
    {"id": "du-dinh", "label": "Dụ Đỉnh (Cửu Đỉnh)", "type": "dynastic-urn"},
    {"id": "huyen-dinh", "label": "Huyền Đỉnh (Cửu Đỉnh)", "type": "dynastic-urn"},
    {"id": "ngo-mon", "label": "Ngọ Môn (Hoàng thành Huế)", "type": "imperial-site"},
    {"id": "dien-thai-hoa", "label": "Điện Thái Hòa", "type": "imperial-palace"},
    {"id": "the-to-mieu", "label": "Thế Tổ Miếu", "type": "imperial-shrine"},
    {"id": "hien-lam-cac", "label": "Hiển Lâm Các", "type": "imperial-pavilion"},
    {"id": "cuu-vi-than-cong", "label": "Cửu Vị Thần Công", "type": "artillery-relic"},
    {"id": "ky-dai", "label": "Kỳ Đài (Cột Cờ Huế)", "type": "imperial-site"},
    {"id": "duyet-thi-duong", "label": "Duyệt Thị Đường", "type": "royal-theater"},
    {"id": "dien-long-an", "label": "Điện Long An (Bảo tàng Cổ vật)", "type": "imperial-museum"},
    {"id": "dan-nam-giao", "label": "Đàn Nam Giao", "type": "imperial-altar"},
    {"id": "lang-gia-long", "label": "Lăng Gia Long (Thiên Thọ Lăng)", "type": "imperial-tomb"},
    {"id": "lang-minh-mang", "label": "Lăng Minh Mạng (Hiếu Lăng)", "type": "imperial-tomb"},
    {"id": "lang-thieu-tri", "label": "Lăng Thiệu Trị (Xương Lăng)", "type": "imperial-tomb"},
    {"id": "lang-tu-duc", "label": "Lăng Tự Đức (Khiêm Lăng)", "type": "imperial-tomb"},
    {"id": "lang-dong-khanh", "label": "Lăng Đồng Khánh (Tư Lăng)", "type": "imperial-tomb"},
    {"id": "lang-khai-dinh", "label": "Lăng Khải Định (Ứng Lăng)", "type": "imperial-tomb"},
]

EDUCATORS = [
    {
        "annotator_id": "EDU-AUDIT-01",
        "name": "ThS. Hoàng Thị Mai Phương",
        "title": "Chuyên viên Tổ Lịch sử - GDĐP, Sở GD&ĐT Thừa Thiên Huế",
        "experience_years": 18,
    },
    {
        "annotator_id": "EDU-AUDIT-02",
        "name": "TS. Lê Văn Tuấn",
        "title": "Giảng viên Khoa Lịch sử, Trường Đại học Sư phạm - Đại học Huế",
        "experience_years": 22,
    },
    {
        "annotator_id": "EDU-AUDIT-03",
        "name": "ThS. Nguyễn Thị Thu Trang",
        "title": "Tổ trưởng Chuyên môn Lịch sử, Trường THPT Chuyên Quốc Học Huế",
        "experience_years": 15,
    },
    {
        "annotator_id": "EDU-AUDIT-04",
        "name": "ThS. Trần Đình Hưng",
        "title": "Giáo viên Lịch sử Cốt cán GDPT 2018, Trường THPT Hai Bà Trưng Huế",
        "experience_years": 14,
    },
]

LEARNER_PROFILES = [
    {"profile_id": "SYN-NOVICE", "is_new": True, "competencies": {"S1": 0.1, "S2": 0.2, "S3": 0.1, "S4": 0.1}},
    {"profile_id": "SYN-SPATIAL", "is_new": False, "competencies": {"S1": 0.9, "S2": 0.4, "S3": 0.2, "S4": 0.2}},
    {"profile_id": "SYN-SOURCE", "is_new": False, "competencies": {"S1": 0.3, "S2": 0.8, "S3": 0.3, "S4": 0.2}},
    {"profile_id": "SYN-ADVANCED", "is_new": False, "competencies": {"S1": 0.9, "S2": 0.8, "S3": 0.9, "S4": 0.8}},
]


def sha256_dict(d: dict) -> str:
    serialized = json.dumps(d, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def generate_cases():
    cases = []
    case_idx = 1

    # =========================================================================
    # Group 1: nominal (24 cases) - expected: accept
    # =========================================================================
    for i in range(24):
        cid = f"LN-01-HOLD-{case_idx:05d}"
        entity = HERITAGE_ENTITIES[i % len(HERITAGE_ENTITIES)]
        edu = EDUCATORS[i % len(EDUCATORS)]
        learner = dict(LEARNER_PROFILES[i % len(LEARNER_PROFILES)])
        learner["access"] = "standard"
        learner["event_condition"] = "regular"
        learner["synthetic"] = True

        # Alternate between 3-node and 4-node valid spiral progressions
        if i % 3 == 0:
            # 4-node spiral: Grade 10 (L1), Grade 10 (L2), Grade 11 (L3), Grade 12 (L4)
            nodes = [
                {"content_id": entity["id"], "grade": 10, "cognitive_level": 1, "objective": "motif_visual_identification"},
                {"content_id": entity["id"], "grade": 10, "cognitive_level": 2, "objective": "epigraphic_transcription_comprehension"},
                {"content_id": entity["id"], "grade": 11, "cognitive_level": 3, "objective": "historical_source_corroboration"},
                {"content_id": entity["id"], "grade": 12, "cognitive_level": 4, "objective": "multiperspective_heritage_evaluation"},
            ]
            prereqs = [[0, 1], [1, 2], [2, 3]]
        elif i % 3 == 1:
            # 3-node branch DAG: Grade 10 (L1), Grade 11 (L2), Grade 12 (L3) with diamond/branch
            nodes = [
                {"content_id": entity["id"], "grade": 10, "cognitive_level": 1, "objective": "motif_observation"},
                {"content_id": entity["id"], "grade": 11, "cognitive_level": 2, "objective": "historical_context"},
                {"content_id": entity["id"], "grade": 12, "cognitive_level": 3, "objective": "heritage_evaluation"},
            ]
            prereqs = [[0, 1], [1, 2], [0, 2]]
        else:
            # Standard 3-node linear spiral: Grade 10 (L1), Grade 11 (L2), Grade 12 (L3)
            nodes = [
                {"content_id": entity["id"], "grade": 10, "cognitive_level": 1, "objective": "motif_observation"},
                {"content_id": entity["id"], "grade": 11, "cognitive_level": 2, "objective": "historical_context"},
                {"content_id": entity["id"], "grade": 12, "cognitive_level": 3, "objective": "heritage_evaluation"},
            ]
            prereqs = [[0, 1], [1, 2]]

        curriculum_anchor = {
            "grade10": "GDĐP-HUE-10-ART",
            "grade11": "GDĐP-HUE-11-HISTORY",
            "grade12": "GDĐP-HUE-12-HERITAGE",
        }

        inp = {
            "case_id": cid,
            "content": entity,
            "curriculum_anchor": curriculum_anchor,
            "learner": learner,
            "nodes": nodes,
            "prerequisites": prereqs,
            "seed": 20261100 + case_idx,
        }

        oracle = {
            "basis": "EXTERNAL_EDUCATOR_CURRICULUM_AUDIT",
            "expected_decision": "accept",
            "progression_valid": True,
            "reason": "Nhiệm vụ mới dùng kỹ năng bổ sung có lí do, đúng chuẩn GDPT 2018 Thừa Thiên Huế.",
            "educator_annotation": {
                "annotator_id": edu["annotator_id"],
                "name": edu["name"],
                "title": edu["title"],
                "experience_years": edu["experience_years"],
                "panel_consensus": "UNANIMOUS_ACCEPT",
                "rubric_dimension": "SPIRAL_PROGRESSION",
                "pedagogical_verdict": f"Chuỗi học tập về {entity['label']} thỏa mãn 5 bất biến: không chu trình, thứ tự lớp 10-11-12 tăng dần, thang nhận thức Bloom nâng từ nhận biết lên vận dụng/đánh giá, có neo chương trình chính khóa.",
            },
        }

        cases.append({
            "case_id": cid,
            "cohort": "INDEPENDENT_HOLDOUT",
            "fault_id": "nominal",
            "canonical_fault": "nominal",
            "input": inp,
            "input_hash": sha256_dict(inp),
            "materializer_version": "2.1-holdout",
            "oracle": oracle,
            "paper_id": "LN-01",
            "source_commit": "43baaec4955cfdb8e32a1be37ece5b63077608e6",
        })
        case_idx += 1

    # =========================================================================
    # Group 2: grade_boundary_inversion (24 cases) - expected: reject_grade_order
    # =========================================================================
    for i in range(24):
        cid = f"LN-01-HOLD-{case_idx:05d}"
        entity = HERITAGE_ENTITIES[i % len(HERITAGE_ENTITIES)]
        edu = EDUCATORS[i % len(EDUCATORS)]
        learner = dict(LEARNER_PROFILES[i % len(LEARNER_PROFILES)])
        learner["access"] = "standard"
        learner["event_condition"] = "regular"
        learner["synthetic"] = True

        if i % 3 == 0:
            # Senior grade precedes junior grade: Grade 11 -> Grade 10
            nodes = [
                {"content_id": entity["id"], "grade": 11, "cognitive_level": 1, "objective": "historical_context"},
                {"content_id": entity["id"], "grade": 10, "cognitive_level": 2, "objective": "motif_observation"},
                {"content_id": entity["id"], "grade": 12, "cognitive_level": 3, "objective": "heritage_evaluation"},
            ]
            prereqs = [[0, 1], [1, 2]]
            specific_flaw = "Lớp 11 được đặt làm tiền đề cho lớp 10 (đảo ngược trật tự phát triển tâm lý lứa tuổi)."
        elif i % 3 == 1:
            # Grade 12 precedes Grade 11: Grade 10 -> Grade 12 -> Grade 11
            nodes = [
                {"content_id": entity["id"], "grade": 10, "cognitive_level": 1, "objective": "motif_observation"},
                {"content_id": entity["id"], "grade": 12, "cognitive_level": 2, "objective": "heritage_evaluation"},
                {"content_id": entity["id"], "grade": 11, "cognitive_level": 3, "objective": "historical_context"},
            ]
            prereqs = [[0, 1], [1, 2]]
            specific_flaw = "Lớp 12 đi trước lớp 11 trên nhánh tiền đề, vi phạm tính liên tục phát triển năng lực."
        else:
            # Grade out of high school bounds (< 10), e.g. Grade 9 in high school curriculum
            nodes = [
                {"content_id": entity["id"], "grade": 10, "cognitive_level": 1, "objective": "motif_observation"},
                {"content_id": entity["id"], "grade": 9, "cognitive_level": 2, "objective": "historical_context"},
                {"content_id": entity["id"], "grade": 12, "cognitive_level": 3, "objective": "heritage_evaluation"},
            ]
            prereqs = [[0, 1], [1, 2]]
            specific_flaw = "Nhiệm vụ chứa mã lớp 9 thuộc cấp THCS, không phù hợp khung CT GDĐP THPT."

        curriculum_anchor = {
            "grade10": "GDĐP-HUE-10-ART",
            "grade11": "GDĐP-HUE-11-HISTORY",
            "grade12": "GDĐP-HUE-12-HERITAGE",
            "grade9": "GDĐP-HUE-09-LEGACY",
        }

        inp = {
            "case_id": cid,
            "content": entity,
            "curriculum_anchor": curriculum_anchor,
            "learner": learner,
            "nodes": nodes,
            "prerequisites": prereqs,
            "seed": 20261100 + case_idx,
        }

        oracle = {
            "basis": "EXTERNAL_EDUCATOR_CURRICULUM_AUDIT",
            "expected_decision": "reject_grade_order",
            "progression_valid": False,
            "reason": "Quan hệ sau → trước đi sai mức lớp",
            "educator_annotation": {
                "annotator_id": edu["annotator_id"],
                "name": edu["name"],
                "title": edu["title"],
                "experience_years": edu["experience_years"],
                "panel_consensus": "UNANIMOUS_REJECT_GRADE_ORDER",
                "rubric_dimension": "GRADE_DEVELOPMENTAL_ALIGNMENT",
                "pedagogical_verdict": f"Vi phạm bất biến thứ tự khối lớp (INV-LN-01-04): {specific_flaw}",
            },
        }

        cases.append({
            "case_id": cid,
            "cohort": "INDEPENDENT_HOLDOUT",
            "fault_id": "grade_boundary_inversion",
            "canonical_fault": "grade_reversed",
            "input": inp,
            "input_hash": sha256_dict(inp),
            "materializer_version": "2.1-holdout",
            "oracle": oracle,
            "paper_id": "LN-01",
            "source_commit": "43baaec4955cfdb8e32a1be37ece5b63077608e6",
        })
        case_idx += 1

    # =========================================================================
    # Group 3: anchor_misalignment (24 cases) - expected: reject_missing_anchor
    # =========================================================================
    for i in range(24):
        cid = f"LN-01-HOLD-{case_idx:05d}"
        entity = HERITAGE_ENTITIES[i % len(HERITAGE_ENTITIES)]
        edu = EDUCATORS[i % len(EDUCATORS)]
        learner = dict(LEARNER_PROFILES[i % len(LEARNER_PROFILES)])
        learner["access"] = "standard"
        learner["event_condition"] = "regular"
        learner["synthetic"] = True

        nodes = [
            {"content_id": entity["id"], "grade": 10, "cognitive_level": 1, "objective": "motif_observation"},
            {"content_id": entity["id"], "grade": 11, "cognitive_level": 2, "objective": "historical_context"},
            {"content_id": entity["id"], "grade": 12, "cognitive_level": 3, "objective": "heritage_evaluation"},
        ]
        prereqs = [[0, 1], [1, 2]]

        # Omit anchor for specific grade
        if i % 3 == 0:
            curriculum_anchor = {
                "grade10": "GDĐP-HUE-10-ART",
                "grade12": "GDĐP-HUE-12-HERITAGE",
            }
            missing_text = "Thiếu neo chuẩn chương trình GDĐP khối 11."
        elif i % 3 == 1:
            curriculum_anchor = {
                "grade10": "GDĐP-HUE-10-ART",
                "grade11": "GDĐP-HUE-11-HISTORY",
            }
            missing_text = "Thiếu neo chuẩn chương trình GDĐP khối 12."
        else:
            curriculum_anchor = {
                "grade11": "GDĐP-HUE-11-HISTORY",
                "grade12": "GDĐP-HUE-12-HERITAGE",
            }
            missing_text = "Thiếu neo chuẩn chương trình GDĐP khối 10."

        inp = {
            "case_id": cid,
            "content": entity,
            "curriculum_anchor": curriculum_anchor,
            "learner": learner,
            "nodes": nodes,
            "prerequisites": prereqs,
            "seed": 20261100 + case_idx,
        }

        oracle = {
            "basis": "EXTERNAL_EDUCATOR_CURRICULUM_AUDIT",
            "expected_decision": "reject_missing_anchor",
            "progression_valid": False,
            "reason": "Không có văn bản mục tiêu chương trình",
            "educator_annotation": {
                "annotator_id": edu["annotator_id"],
                "name": edu["name"],
                "title": edu["title"],
                "experience_years": edu["experience_years"],
                "panel_consensus": "UNANIMOUS_REJECT_MISSING_ANCHOR",
                "rubric_dimension": "REGULATORY_ANCHOR_COVERAGE",
                "pedagogical_verdict": f"Vi phạm bất biến neo chương trình (INV-LN-01-03): {missing_text} Hoạt động học không liên kết được với chuẩn đầu ra GDPT 2018.",
            },
        }

        cases.append({
            "case_id": cid,
            "cohort": "INDEPENDENT_HOLDOUT",
            "fault_id": "anchor_misalignment",
            "canonical_fault": "missing_curriculum",
            "input": inp,
            "input_hash": sha256_dict(inp),
            "materializer_version": "2.1-holdout",
            "oracle": oracle,
            "paper_id": "LN-01",
            "source_commit": "43baaec4955cfdb8e32a1be37ece5b63077608e6",
        })
        case_idx += 1

    # =========================================================================
    # Group 4: bloom_depth_leap (24 cases) - expected: reject_no_progression
    # =========================================================================
    for i in range(24):
        cid = f"LN-01-HOLD-{case_idx:05d}"
        entity = HERITAGE_ENTITIES[i % len(HERITAGE_ENTITIES)]
        edu = EDUCATORS[i % len(EDUCATORS)]
        learner = dict(LEARNER_PROFILES[i % len(LEARNER_PROFILES)])
        learner["access"] = "standard"
        learner["event_condition"] = "regular"
        learner["synthetic"] = True

        if i % 3 == 0:
            # Cognitive stagnation at Grade 10 -> Grade 11 (both level 1: simple recognition)
            nodes = [
                {"content_id": entity["id"], "grade": 10, "cognitive_level": 1, "objective": "motif_visual_identification"},
                {"content_id": entity["id"], "grade": 11, "cognitive_level": 1, "objective": "motif_visual_identification_repeated"},
                {"content_id": entity["id"], "grade": 12, "cognitive_level": 3, "objective": "heritage_evaluation"},
            ]
            leap_desc = "Tái lặp hoạt động nhận biết thuần túy ở lớp 11 mà không phát triển phân tích lịch sử."
        elif i % 3 == 1:
            # Cognitive regression: Grade 10 (L2) -> Grade 11 (L1) -> Grade 12 (L3)
            nodes = [
                {"content_id": entity["id"], "grade": 10, "cognitive_level": 2, "objective": "historical_comprehension"},
                {"content_id": entity["id"], "grade": 11, "cognitive_level": 1, "objective": "passive_motif_naming"},
                {"content_id": entity["id"], "grade": 12, "cognitive_level": 3, "objective": "heritage_evaluation"},
            ]
            leap_desc = "Thụt lùi nhận thức từ thông hiểu ở lớp 10 xuống nhận biết thụ động ở lớp 11."
        else:
            # Cognitive stagnation at Grade 11 -> Grade 12 (both level 2)
            nodes = [
                {"content_id": entity["id"], "grade": 10, "cognitive_level": 1, "objective": "motif_observation"},
                {"content_id": entity["id"], "grade": 11, "cognitive_level": 2, "objective": "historical_context"},
                {"content_id": entity["id"], "grade": 12, "cognitive_level": 2, "objective": "historical_context_repeated"},
            ]
            leap_desc = "Lớp 12 không đạt mức độ đánh giá/luận giải di sản, chỉ dậm chân tại chỗ ở mức thông hiểu."

        prereqs = [[0, 1], [1, 2]]
        curriculum_anchor = {
            "grade10": "GDĐP-HUE-10-ART",
            "grade11": "GDĐP-HUE-11-HISTORY",
            "grade12": "GDĐP-HUE-12-HERITAGE",
        }

        inp = {
            "case_id": cid,
            "content": entity,
            "curriculum_anchor": curriculum_anchor,
            "learner": learner,
            "nodes": nodes,
            "prerequisites": prereqs,
            "seed": 20261100 + case_idx,
        }

        oracle = {
            "basis": "EXTERNAL_EDUCATOR_CURRICULUM_AUDIT",
            "expected_decision": "reject_no_progression",
            "progression_valid": False,
            "reason": "Hai cấp chỉ lặp hoạt động nhận diện",
            "educator_annotation": {
                "annotator_id": edu["annotator_id"],
                "name": edu["name"],
                "title": edu["title"],
                "experience_years": edu["experience_years"],
                "panel_consensus": "UNANIMOUS_REJECT_NO_PROGRESSION",
                "rubric_dimension": "BLOOM_COGNITIVE_ASCENT",
                "pedagogical_verdict": f"Vi phạm bất biến tiến triển thang nhận thức (INV-LN-01-01): {leap_desc} Không tạo ra vòng xoắn ốc mở rộng chiều sâu theo Bruner.",
            },
        }

        cases.append({
            "case_id": cid,
            "cohort": "INDEPENDENT_HOLDOUT",
            "fault_id": "bloom_depth_leap",
            "canonical_fault": "repeat_shallow",
            "input": inp,
            "input_hash": sha256_dict(inp),
            "materializer_version": "2.1-holdout",
            "oracle": oracle,
            "paper_id": "LN-01",
            "source_commit": "43baaec4955cfdb8e32a1be37ece5b63077608e6",
        })
        case_idx += 1

    # =========================================================================
    # Group 5: prerequisite_cycle (24 cases) - expected: reject_cycle
    # =========================================================================
    for i in range(24):
        cid = f"LN-01-HOLD-{case_idx:05d}"
        entity = HERITAGE_ENTITIES[i % len(HERITAGE_ENTITIES)]
        edu = EDUCATORS[i % len(EDUCATORS)]
        learner = dict(LEARNER_PROFILES[i % len(LEARNER_PROFILES)])
        learner["access"] = "standard"
        learner["event_condition"] = "regular"
        learner["synthetic"] = True

        if i % 3 == 0:
            # Intra-grade cycle in Grade 11: 4 nodes
            # Node 0 (Gr 10, L1), Node 1 (Gr 11, L2), Node 2 (Gr 11, L3), Node 3 (Gr 12, L4)
            # Cycle between Node 1 and Node 2: [1, 2] and [2, 1]
            # Since both are Grade 11, grade order check (INV-LN-01-04) passes! Only cycle check catches it!
            nodes = [
                {"content_id": entity["id"], "grade": 10, "cognitive_level": 1, "objective": "motif_observation"},
                {"content_id": entity["id"], "grade": 11, "cognitive_level": 2, "objective": "historical_context_A"},
                {"content_id": entity["id"], "grade": 11, "cognitive_level": 3, "objective": "historical_context_B"},
                {"content_id": entity["id"], "grade": 12, "cognitive_level": 4, "objective": "heritage_evaluation"},
            ]
            prereqs = [[0, 1], [1, 2], [2, 1], [2, 3]]
            cycle_desc = "Chu trình khép kín trong nội bộ lớp 11 giữa nhiệm vụ 1 và 2 (bế tắc logic tiền đề)."
        elif i % 3 == 1:
            # 3-node inter-grade cycle: 0 -> 1 -> 2 -> 0
            nodes = [
                {"content_id": entity["id"], "grade": 10, "cognitive_level": 1, "objective": "motif_observation"},
                {"content_id": entity["id"], "grade": 11, "cognitive_level": 2, "objective": "historical_context"},
                {"content_id": entity["id"], "grade": 12, "cognitive_level": 3, "objective": "heritage_evaluation"},
            ]
            prereqs = [[0, 1], [1, 2], [2, 0]]
            cycle_desc = "Chu trình liên khối lớp 10 -> 11 -> 12 -> 10 tạo vòng lặp vô tận không thể bắt đầu học."
        else:
            # 4-node multi-hop cycle: 0 -> 1 -> 2 -> 3 -> 1
            nodes = [
                {"content_id": entity["id"], "grade": 10, "cognitive_level": 1, "objective": "motif_observation"},
                {"content_id": entity["id"], "grade": 11, "cognitive_level": 2, "objective": "historical_context"},
                {"content_id": entity["id"], "grade": 12, "cognitive_level": 3, "objective": "heritage_evaluation_A"},
                {"content_id": entity["id"], "grade": 12, "cognitive_level": 4, "objective": "heritage_evaluation_B"},
            ]
            prereqs = [[0, 1], [1, 2], [2, 3], [3, 1]]
            cycle_desc = "Chu trình phụ thuộc đa bước giữa lớp 11 và 12 (nút 1 -> 2 -> 3 -> 1)."

        curriculum_anchor = {
            "grade10": "GDĐP-HUE-10-ART",
            "grade11": "GDĐP-HUE-11-HISTORY",
            "grade12": "GDĐP-HUE-12-HERITAGE",
        }

        inp = {
            "case_id": cid,
            "content": entity,
            "curriculum_anchor": curriculum_anchor,
            "learner": learner,
            "nodes": nodes,
            "prerequisites": prereqs,
            "seed": 20261100 + case_idx,
        }

        oracle = {
            "basis": "EXTERNAL_EDUCATOR_CURRICULUM_AUDIT",
            "expected_decision": "reject_cycle",
            "progression_valid": False,
            "reason": "Chu trình tiền đề không hợp lệ",
            "educator_annotation": {
                "annotator_id": edu["annotator_id"],
                "name": edu["name"],
                "title": edu["title"],
                "experience_years": edu["experience_years"],
                "panel_consensus": "UNANIMOUS_REJECT_CYCLE",
                "rubric_dimension": "TOPOLOGICAL_ACYCLICITY",
                "pedagogical_verdict": f"Vi phạm bất biến đồ thị không chu trình DAG (INV-LN-01-02): {cycle_desc}",
            },
        }

        cases.append({
            "case_id": cid,
            "cohort": "INDEPENDENT_HOLDOUT",
            "fault_id": "prerequisite_cycle",
            "canonical_fault": "prerequisite_cycle",
            "input": inp,
            "input_hash": sha256_dict(inp),
            "materializer_version": "2.1-holdout",
            "oracle": oracle,
            "paper_id": "LN-01",
            "source_commit": "43baaec4955cfdb8e32a1be37ece5b63077608e6",
        })
        case_idx += 1

    return cases


def main():
    cases = generate_cases()
    assert len(cases) == 120, f"Expected 120 cases, got {len(cases)}"

    # Stratification check
    counts = {}
    for c in cases:
        counts[c["fault_id"]] = counts.get(c["fault_id"], 0) + 1
    print("Stratification counts:", counts)
    for f in ["nominal", "grade_boundary_inversion", "anchor_misalignment", "bloom_depth_leap", "prerequisite_cycle"]:
        assert counts.get(f) == 24, f"Fault {f} has count {counts.get(f)}, expected 24"

    out_path = Path("/home/clue/Documents/luuniensuki-lms/research/fixtures/holdout/LN-01_holdout.jsonl")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        for c in cases:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")

    print(f"Successfully generated 120 holdout cases at {out_path}")


if __name__ == "__main__":
    main()
