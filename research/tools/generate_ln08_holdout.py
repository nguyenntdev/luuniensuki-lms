#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate independent 120-case holdout dataset for Study LN-08.

5 fault types × 24 cases = 120 cases:
- nominal_correct (24 cases): Authentic claims with valid canonical keywords and verified sources
- logical_negation_misconception (24 cases): Keyword-rich sentences containing logical negation inverting truth
- synonym_variation (24 cases): Genuine historical equivalents using ritual space synonyms without exact canonical keywords
- partial_reasoning (24 cases): Incomplete generic statements lacking spatial-ritual linkage
- unverified_historical_assertion (24 cases): Claims citing untrusted, unverified, or fabricated sources
"""
from __future__ import annotations

import hashlib
import json
import pathlib

OUTPUT_PATH = pathlib.Path(__file__).resolve().parents[1] / "fixtures" / "holdout" / "LN-08_holdout.jsonl"

RELICS = [
    {"id": "ngo-mon", "label": "Ngọ Môn", "type": "imperial-gate"},
    {"id": "dien-thai-hoa", "label": "Điện Thái Hòa", "type": "imperial-palace"},
    {"id": "the-to-mieu", "label": "Thế Tổ Miếu", "type": "ancestral-temple"},
    {"id": "hien-lam-cac", "label": "Hiển Lâm Các", "type": "memorial-pavilion"},
    {"id": "cao-dinh", "label": "Cao Đỉnh", "type": "bronze-urn"},
    {"id": "nhan-dinh", "label": "Nhân Đỉnh", "type": "bronze-urn"},
    {"id": "chuong-dinh", "label": "Chương Đỉnh", "type": "bronze-urn"},
    {"id": "anh-dinh", "label": "Anh Đỉnh", "type": "bronze-urn"},
    {"id": "nghi-dinh", "label": "Nghị Đỉnh", "type": "bronze-urn"},
    {"id": "thuan-dinh", "label": "Thuần Đỉnh", "type": "bronze-urn"},
    {"id": "tuyen-dinh", "label": "Tuyên Đỉnh", "type": "bronze-urn"},
    {"id": "du-dinh", "label": "Dụ Đỉnh", "type": "bronze-urn"},
    {"id": "huyen-dinh", "label": "Huyền Đỉnh", "type": "bronze-urn"},
    {"id": "ky-dai", "label": "Kỳ Đài", "type": "flag-tower"},
    {"id": "dien-can-chanh", "label": "Điện Cần Chánh", "type": "court-hall"},
    {"id": "dien-can-thanh", "label": "Điện Càn Thành", "type": "inner-residence"},
    {"id": "dien-khon-thai", "label": "Điện Khôn Thái", "type": "inner-residence"},
    {"id": "dien-kien-trung", "label": "Điện Kiến Trung", "type": "palace-pavilion"},
    {"id": "cua-hien-nhon", "label": "Cửa Hiển Nhơn", "type": "citadel-gate"},
    {"id": "cua-chuong-duc", "label": "Cửa Chương Đức", "type": "citadel-gate"},
    {"id": "cung-dien-tho", "label": "Cung Diên Thọ", "type": "queen-mother-palace"},
    {"id": "cung-truong-sanh", "label": "Cung Trường Sanh", "type": "imperial-garden-palace"},
    {"id": "trieu-to-mieu", "label": "Triệu Tổ Miếu", "type": "ancestral-temple"},
    {"id": "hung-to-mieu", "label": "Hưng Tổ Miếu", "type": "ancestral-temple"},
]

# Negation variants
NEGATION_TEMPLATES = [
    "{label} không thuộc trục nghi lễ theo điển chế triều Nguyễn.",
    "Tư liệu lịch sử chứng minh {label} không nằm trên trục nghi lễ.",
    "{label} không phải là công trình trên trục nghi lễ của Hoàng thành.",
    "Khảo sát cho thấy {label} không được bố trí trên trục nghi lễ.",
    "{label} trái với quy chuẩn không gian trên trục nghi lễ.",
    "Ghi chép cho thấy {label} chẳng phải bộ phận của trục nghi lễ.",
    "{label} chưa từng tọa lạc trên trục nghi lễ của kinh thành.",
    "Luận điểm này phủ nhận việc {label} nằm trên trục nghi lễ.",
    "Sử liệu bác bỏ quan điểm cho rằng {label} thuộc trục nghi lễ.",
    "{label} ngược lại hoàn toàn không nằm trong trục nghi lễ.",
    "Khẳng định {label} thuộc trục nghi lễ là sai lệch so với nguồn sử liệu.",
    "{label} không hề thuộc trục nghi lễ của Đại Nội.",
]

# Synonym variants using valid domain phrases (avoiding exact 'trục nghi lễ' or 'nghi lễ')
SYNONYM_TEMPLATES = [
    "Theo tư liệu, vị trí {label} nằm trên tuyến không gian phục vụ nghi thức.",
    "Sử liệu xác nhận {label} toạ lạc trên trục trung tâm nghi thức của hoàng thành.",
    "Văn bản chính sử ghi rõ {label} được bố trí trên tuyến không gian phục vụ nghi thức triều đình.",
    "Theo chính sử, {label} toạ lạc trên tuyến không gian nghi thức tôn nghiêm.",
    "{label} nằm trong không gian phục vụ nghi thức tế tự của hoàng cung.",
    "Tư liệu chuẩn ghi nhận {label} thuộc về trục nghi thức quy chuẩn của kinh thành.",
    "Theo thư tịch cổ, {label} được bố trí trên trục trung tâm nghi thức của triều đình.",
    "Nghiên cứu sử liệu cho thấy {label} nằm trên tuyến không gian phục vụ nghi thức cung đình.",
    "Theo văn bản lưu trữ, {label} toạ lạc trên trục nghi thức thời Nguyễn.",
    "Ghi chép chính thức xác định {label} thuộc về không gian phục vụ nghi thức tế lễ.",
    "Tài liệu hội điển ghi nhận {label} nằm trên trục trung tâm nghi thức hoàng gia.",
    "{label} được bố trí trên tuyến không gian nghi thức theo đồ án kiến trúc cổ.",
]

# Partial reasoning templates (mention generic architecture without ritual axis connection)
PARTIAL_TEMPLATES = [
    "{label} là một công trình kiến trúc thời Nguyễn.",
    "{label} là di tích lịch sử nổi tiếng tại Cố đô Huế.",
    "{label} là công trình kiến trúc có giá trị nghệ thuật cao.",
    "{label} là một di tích được bảo tồn trong quần thể di tích Cố đô Huế.",
    "{label} là một công trình kiến trúc độc đáo bằng gỗ và đá.",
    "{label} là di tích gắn liền với lịch sử triều Nguyễn.",
]

# Sources
VERIFIED_SOURCES = [
    "SOURCE-DNTL-001",  # Đại Nam Thực Lục
    "SOURCE-HD-001",    # Khâm Định Đại Nam Hội Điển Sự Lệ
    "SOURCE-DNSG-001",  # Đại Nam Nhất Thống Chí
]

UNVERIFIED_SOURCES = [
    ("SOURCE-FABRICATED", True),
    ("SOURCE-UNVERIFIED", False),
    ("SOURCE-SYN-WRONG", True),
    ("SOURCE-DNTL-001", False),
]

def make_hash(data: dict) -> str:
    serialized = json.dumps(data, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

def generate_holdout() -> list[dict]:
    cases = []
    case_num = 1

    # 1. NOMINAL CORRECT (24 cases)
    for i, relic in enumerate(RELICS):
        src = VERIFIED_SOURCES[i % len(VERIFIED_SOURCES)]
        case_id = f"LN-08-HOLD-{case_num:05d}"
        ans = f"{relic['label']} thuộc trục nghi lễ được mô tả chuẩn xác trong nguồn tư liệu."
        inp = {
            "case_id": case_id,
            "prompt": "Dựa vào nguồn sử liệu, hãy xác định và giải thích mối quan hệ không gian - nghi lễ của công trình.",
            "answer": ans,
            "content": relic,
            "evidence": {
                "claim_id": f"CLAIM-HD-{case_num:03d}",
                "source_id": src,
                "verified": True,
            },
            "expected_conclusion": "spatial_ritual_relationship",
            "language": "vi",
            "learner": {
                "profile_id": f"HOLDOUT-STUDENT-{i+1:03d}",
                "competencies": {"S1": 0.8, "S2": 0.8, "S3": 0.8, "S4": 0.8},
                "synthetic": True,
                "evaluation_mode": "programmatic_synthetic_scenario",
                "holdout": True,
            },
            "score_scale": "rubric_s1_s4",
            "seed": 90000 + case_num,
        }
        cases.append({
            "case_id": case_id,
            "cohort": "INDEPENDENT_HOLDOUT",
            "fault_id": "nominal_correct",
            "input": inp,
            "input_hash": make_hash(inp),
            "materializer_version": "2.0",
            "oracle": {
                "expected_decision": "feedback_supported",
                "expected_category": "supported",
                "reason": "Đáp án chuẩn xác, dẫn chứng phù hợp với tư liệu lịch sử được cung cấp.",
            },
            "paper_id": "LN-08",
        })
        case_num += 1

    # 2. LOGICAL NEGATION MISCONCEPTION (24 cases)
    for i, relic in enumerate(RELICS):
        src = VERIFIED_SOURCES[i % len(VERIFIED_SOURCES)]
        case_id = f"LN-08-HOLD-{case_num:05d}"
        tmpl = NEGATION_TEMPLATES[i % len(NEGATION_TEMPLATES)]
        ans = tmpl.format(label=relic["label"])
        inp = {
            "case_id": case_id,
            "prompt": "Dựa vào nguồn sử liệu, hãy xác định và giải thích mối quan hệ không gian - nghi lễ của công trình.",
            "answer": ans,
            "content": relic,
            "evidence": {
                "claim_id": f"CLAIM-HD-{case_num:03d}",
                "source_id": src,
                "verified": True,
            },
            "expected_conclusion": "spatial_ritual_relationship",
            "language": "vi",
            "learner": {
                "profile_id": f"HOLDOUT-STUDENT-{i+1:03d}",
                "competencies": {"S1": 0.5, "S2": 0.4, "S3": 0.6, "S4": 0.3},
                "synthetic": True,
                "evaluation_mode": "programmatic_synthetic_scenario",
                "holdout": True,
            },
            "score_scale": "rubric_s1_s4",
            "seed": 90000 + case_num,
        }
        cases.append({
            "case_id": case_id,
            "cohort": "INDEPENDENT_HOLDOUT",
            "fault_id": "logical_negation_misconception",
            "input": inp,
            "input_hash": make_hash(inp),
            "materializer_version": "2.0",
            "oracle": {
                "expected_decision": "classify_contradiction",
                "expected_category": "contradiction",
                "reason": "Phủ định biến câu đúng thành sai, làm đảo ngược quan hệ không gian nghi lễ.",
            },
            "paper_id": "LN-08",
        })
        case_num += 1

    # 3. SYNONYM VARIATION (24 cases)
    for i, relic in enumerate(RELICS):
        src = VERIFIED_SOURCES[i % len(VERIFIED_SOURCES)]
        case_id = f"LN-08-HOLD-{case_num:05d}"
        tmpl = SYNONYM_TEMPLATES[i % len(SYNONYM_TEMPLATES)]
        ans = tmpl.format(label=relic["label"])
        inp = {
            "case_id": case_id,
            "prompt": "Dựa vào nguồn sử liệu, hãy xác định và giải thích mối quan hệ không gian - nghi lễ của công trình.",
            "answer": ans,
            "content": relic,
            "evidence": {
                "claim_id": f"CLAIM-HD-{case_num:03d}",
                "source_id": src,
                "verified": True,
            },
            "expected_conclusion": "spatial_ritual_relationship",
            "language": "vi",
            "learner": {
                "profile_id": f"HOLDOUT-STUDENT-{i+1:03d}",
                "competencies": {"S1": 0.9, "S2": 0.8, "S3": 0.8, "S4": 0.9},
                "synthetic": True,
                "evaluation_mode": "programmatic_synthetic_scenario",
                "holdout": True,
            },
            "score_scale": "rubric_s1_s4",
            "seed": 90000 + case_num,
        }
        cases.append({
            "case_id": case_id,
            "cohort": "INDEPENDENT_HOLDOUT",
            "fault_id": "synonym_variation",
            "input": inp,
            "input_hash": make_hash(inp),
            "materializer_version": "2.0",
            "oracle": {
                "expected_decision": "preserve_semantics",
                "expected_category": "supported_equivalent",
                "reason": "Diễn đạt bằng từ đồng nghĩa phong phú nhưng bảo toàn mệnh đề lịch sử chuẩn xác.",
            },
            "paper_id": "LN-08",
        })
        case_num += 1

    # 4. PARTIAL REASONING (24 cases)
    for i, relic in enumerate(RELICS):
        src = VERIFIED_SOURCES[i % len(VERIFIED_SOURCES)]
        case_id = f"LN-08-HOLD-{case_num:05d}"
        tmpl = PARTIAL_TEMPLATES[i % len(PARTIAL_TEMPLATES)]
        ans = tmpl.format(label=relic["label"])
        inp = {
            "case_id": case_id,
            "prompt": "Dựa vào nguồn sử liệu, hãy xác định và giải thích mối quan hệ không gian - nghi lễ của công trình.",
            "answer": ans,
            "content": relic,
            "evidence": {
                "claim_id": f"CLAIM-HD-{case_num:03d}",
                "source_id": src,
                "verified": True,
            },
            "expected_conclusion": "spatial_ritual_relationship",
            "language": "vi",
            "learner": {
                "profile_id": f"HOLDOUT-STUDENT-{i+1:03d}",
                "competencies": {"S1": 0.4, "S2": 0.3, "S3": 0.4, "S4": 0.2},
                "synthetic": True,
                "evaluation_mode": "programmatic_synthetic_scenario",
                "holdout": True,
            },
            "score_scale": "rubric_s1_s4",
            "seed": 90000 + case_num,
        }
        cases.append({
            "case_id": case_id,
            "cohort": "INDEPENDENT_HOLDOUT",
            "fault_id": "partial_reasoning",
            "input": inp,
            "input_hash": make_hash(inp),
            "materializer_version": "2.0",
            "oracle": {
                "expected_decision": "feedback_incomplete",
                "expected_category": "incomplete",
                "reason": "Câu trả lời đúng một phần nhưng thiếu liên kết không gian - nghi lễ cốt lõi.",
            },
            "paper_id": "LN-08",
        })
        case_num += 1

    # 5. UNVERIFIED HISTORICAL ASSERTION (24 cases)
    for i, relic in enumerate(RELICS):
        src, is_ver = UNVERIFIED_SOURCES[i % len(UNVERIFIED_SOURCES)]
        case_id = f"LN-08-HOLD-{case_num:05d}"
        ans = f"{relic['label']} thuộc trục nghi lễ được mô tả trong nguồn sử liệu."
        inp = {
            "case_id": case_id,
            "prompt": "Dựa vào nguồn sử liệu, hãy xác định và giải thích mối quan hệ không gian - nghi lễ của công trình.",
            "answer": ans,
            "content": relic,
            "evidence": {
                "claim_id": f"CLAIM-HD-{case_num:03d}",
                "source_id": src,
                "verified": is_ver,
            },
            "expected_conclusion": "spatial_ritual_relationship",
            "language": "vi",
            "learner": {
                "profile_id": f"HOLDOUT-STUDENT-{i+1:03d}",
                "competencies": {"S1": 0.6, "S2": 0.2, "S3": 0.2, "S4": 0.4},
                "synthetic": True,
                "evaluation_mode": "programmatic_synthetic_scenario",
                "holdout": True,
            },
            "score_scale": "rubric_s1_s4",
            "seed": 90000 + case_num,
        }
        cases.append({
            "case_id": case_id,
            "cohort": "INDEPENDENT_HOLDOUT",
            "fault_id": "unverified_historical_assertion",
            "input": inp,
            "input_hash": make_hash(inp),
            "materializer_version": "2.0",
            "oracle": {
                "expected_decision": "classify_source_error",
                "expected_category": "source_error",
                "reason": "Nguồn dẫn chứng không được xác thực hoặc không có trong cơ sở sử liệu chuẩn.",
            },
            "paper_id": "LN-08",
        })
        case_num += 1

    return cases

def main():
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    cases = generate_holdout()
    assert len(cases) == 120, f"Expected 120 cases, got {len(cases)}"
    
    # Check 24 per fault
    fault_counts = {}
    for c in cases:
        fault_counts[c["fault_id"]] = fault_counts.get(c["fault_id"], 0) + 1
    print(f"Fault counts: {fault_counts}")
    assert all(cnt == 24 for cnt in fault_counts.values())

    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        for c in cases:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    print(f"Successfully wrote {len(cases)} cases to {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
