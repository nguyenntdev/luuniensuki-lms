#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate independent 120-case holdout dataset for LN-09.

Evaluates Evidence-Grounded Learning Analytics & Teacher Intervention Rules.
5 fault types × 24 cases = 120 total cases:
1. nominal: Verified assessment items, fresh data (<=30d), no signal conflict, k-anonymity satisfied.
2. missing_interaction_logs: Zero LMS interaction logs or assessment submissions (INV-LN-09-01).
3. conflicting_assessment_signals: Contradictory performance signals across assessment modalities (INV-LN-09-05).
4. unverified_curriculum_task: Evidence derived from uncalibrated or unverified source tasks (INV-LN-09-02).
5. stale_mastery_data: Outdated mastery observations (>30 days old) requiring knowledge refresh.
"""
import hashlib
import json
import pathlib

HERITAGE_CONTENTS = [
    {"id": "ngo-mon", "label": "Ngọ Môn (Hoàng thành Huế)", "type": "imperial-site"},
    {"id": "dien-thai-hoa", "label": "Điện Thái Hòa", "type": "imperial-palace"},
    {"id": "the-to-mieu", "label": "Thế Tổ Miếu", "type": "imperial-shrine"},
    {"id": "cao-dinh", "label": "Cao Đỉnh (Cửu Đỉnh)", "type": "dynastic-urn"},
    {"id": "nhan-dinh", "label": "Nhân Đỉnh (Cửu Đỉnh)", "type": "dynastic-urn"},
    {"id": "chuong-dinh", "label": "Chương Đỉnh (Cửu Đỉnh)", "type": "dynastic-urn"},
    {"id": "anh-dinh", "label": "Anh Đỉnh (Cửu Đỉnh)", "type": "dynastic-urn"},
    {"id": "nghi-dinh", "label": "Nghị Đỉnh (Cửu Đỉnh)", "type": "dynastic-urn"},
    {"id": "thuan-dinh", "label": "Thuần Đỉnh (Cửu Đỉnh)", "type": "dynastic-urn"},
    {"id": "tuyen-dinh", "label": "Tuyên Đỉnh (Cửu Đỉnh)", "type": "dynastic-urn"},
    {"id": "du-dinh", "label": "Dụ Đỉnh (Cửu Đỉnh)", "type": "dynastic-urn"},
    {"id": "huyen-dinh", "label": "Huyền Đỉnh (Cửu Đỉnh)", "type": "dynastic-urn"},
    {"id": "lang-tu-duc", "label": "Lăng Tự Đức (Khiêm Lăng)", "type": "imperial-tomb"},
    {"id": "lang-khai-dinh", "label": "Lăng Khải Định (Ứng Lăng)", "type": "imperial-tomb"},
    {"id": "dan-nam-giao", "label": "Đàn Nam Giao", "type": "altar"},
    {"id": "song-huong", "label": "Sông Hương (Hương Giang)", "type": "natural-heritage"},
    {"id": "chua-thien-mu", "label": "Chùa Thiên Mụ", "type": "religious-site"},
    {"id": "ky-dai", "label": "Kỳ Đài Huế", "type": "fortification"},
    {"id": "dien-kien-trung", "label": "Điện Kiến Trung", "type": "imperial-palace"},
    {"id": "hien-lam-cac", "label": "Hiển Lâm Các", "type": "imperial-pavilion"},
    {"id": "cua-thuong-tu", "label": "Cửa Thượng Tứ", "type": "citadel-gate"},
    {"id": "ho-tinh-tam", "label": "Hồ Tịnh Tâm", "type": "imperial-garden"},
    {"id": "luc-bo", "label": "Lục Bộ Triều Nguyễn", "type": "administrative-site"},
    {"id": "quoc-tu-giam", "label": "Quốc Tử Giám Huế", "type": "educational-site"},
]

LEARNER_PROFILES = [
    ("SYN-NOVICE", {"S1": 0.1, "S2": 0.2, "S3": 0.1, "S4": 0.1}, True),
    ("SYN-SPATIAL", {"S1": 0.9, "S2": 0.4, "S3": 0.2, "S4": 0.2}, False),
    ("SYN-SOURCE", {"S1": 0.3, "S2": 0.8, "S3": 0.3, "S4": 0.2}, False),
    ("SYN-PARTIAL", {"S1": 0.5, "S2": 0.5, "S3": 0.1, "S4": 0.2}, False),
    ("SYN-ADVANCED", {"S1": 0.9, "S2": 0.8, "S3": 0.9, "S4": 0.8}, False),
    ("SYN-LOWNET", {"S1": 0.4, "S2": 0.3, "S3": 0.4, "S4": 0.2}, True),
    ("SYN-NO3D", {"S1": 0.6, "S2": 0.2, "S3": 0.5, "S4": 0.3}, False),
    ("SYN-KEYBOARD", {"S1": 0.7, "S2": 0.7, "S3": 0.4, "S4": 0.3}, False),
    ("SYN-CONFLICT", {"S1": 0.4, "S2": 0.6, "S3": 0.7, "S4": 0.5}, False),
    ("SYN-ARGUMENT", {"S1": 0.2, "S2": 0.7, "S3": 0.8, "S4": 0.6}, False),
    ("SYN-SKEWED", {"S1": 0.8, "S2": 0.1, "S3": 0.3, "S4": 0.1}, False),
    ("SYN-EMPTY", {"S1": 0.0, "S2": 0.0, "S3": 0.0, "S4": 0.0}, True),
]

CANDIDATE_INTERVENTIONS = [
    ("additional_source_comparison_activity", "evidence_use", "source_task"),
    ("additional_spatial_orientation_activity", "spatial", "quiz"),
    ("additional_chronology_exercise", "temporal", "timeline_ordering"),
    ("additional_argumentation_workshop", "argument", "rubric_rubbing"),
]


def generate_holdout_cases():
    cases = []
    fault_types = [
        "nominal",
        "missing_interaction_logs",
        "conflicting_assessment_signals",
        "unverified_curriculum_task",
        "stale_mastery_data",
    ]

    case_num = 1
    for fault_id in fault_types:
        for i in range(24):
            case_id = f"LN-09-HOLD-{case_num:05d}"
            content = HERITAGE_CONTENTS[i % len(HERITAGE_CONTENTS)]
            prof_id, comps, is_new = LEARNER_PROFILES[i % len(LEARNER_PROFILES)]
            intervention, competency, default_task_type = CANDIDATE_INTERVENTIONS[i % len(CANDIDATE_INTERVENTIONS)]
            seed = 20261201 + case_num

            # Base values
            cohort_size = 25 + (i % 10)
            obs_age_days = 1 + (i % 6)
            signals_conflict = False
            learning_evidence = [
                {"outcome": competency, "score": 0.2 + (i % 3) * 0.1, "type": default_task_type, "verified": True},
                {"outcome": "spatial" if competency != "spatial" else "evidence_use", "score": 0.35, "type": "quiz", "verified": True},
            ]

            if fault_id == "nominal":
                oracle_decision = "propose_explained_action"
                oracle_reason = "Tín hiệu có đủ nguồn và hành động"
            elif fault_id == "missing_interaction_logs":
                learning_evidence = []
                oracle_decision = "abstain_missing_evidence"
                oracle_reason = "Không đủ dữ liệu LMS"
            elif fault_id == "conflicting_assessment_signals":
                signals_conflict = True
                learning_evidence.append(
                    {"outcome": competency, "score": 0.95, "type": "field_work", "verified": True}
                )
                oracle_decision = "abstain_conflict"
                oracle_reason = "Dấu hiệu mâu thuẫn không phân giải"
            elif fault_id == "unverified_curriculum_task":
                learning_evidence = [
                    {"outcome": competency, "score": 0.25, "type": default_task_type, "verified": False},
                    {"outcome": "spatial", "score": 0.3, "type": "quiz", "verified": True},
                ]
                oracle_decision = "abstain_unverified_source"
                oracle_reason = "Điểm nhiệm vụ không đủ giá trị diễn giải"
            elif fault_id == "stale_mastery_data":
                obs_age_days = 45 + (i * 5)  # 45 to 160 days (> 30 days)
                oracle_decision = "request_refresh"
                oracle_reason = "Điểm năng lực đã cũ"
            else:
                raise ValueError(f"Unknown fault: {fault_id}")

            case_input = {
                "case_id": case_id,
                "candidate_intervention": intervention,
                "class_context": {"grade": 12, "subject": "GDĐP", "synthetic": True},
                "cohort_size": cohort_size,
                "content": content,
                "learner": {
                    "access": "standard",
                    "competencies": comps,
                    "event_condition": "regular",
                    "is_new": is_new,
                    "profile_id": prof_id,
                    "synthetic": True,
                },
                "learning_evidence": learning_evidence,
                "observation_age_days": obs_age_days,
                "required_signal_types": [default_task_type, "quiz"],
                "seed": seed,
                "signals_conflict": signals_conflict,
            }

            input_bytes = json.dumps(case_input, sort_keys=True).encode("utf-8")
            input_hash = hashlib.sha256(input_bytes).hexdigest()

            row = {
                "case_id": case_id,
                "cohort": "INDEPENDENT_HOLDOUT",
                "fault_id": fault_id,
                "canonical_fault": {
                    "nominal": "nominal",
                    "missing_interaction_logs": "missing_logs",
                    "conflicting_assessment_signals": "conflicting_signals",
                    "unverified_curriculum_task": "unverified_task",
                    "stale_mastery_data": "stale_mastery",
                }[fault_id],
                "input": case_input,
                "input_hash": input_hash,
                "materializer_version": "2.1-holdout",
                "oracle": {
                    "basis": "INSTRUCTIONAL_RECOMMENDATIONS_DOMAIN_INVARIANT",
                    "expected_decision": oracle_decision,
                    "reason": oracle_reason,
                },
                "paper_id": "LN-09",
                "source_commit": "54da2beb71f3df70e1f00b215ae0fb1a850eb263",
            }
            cases.append(row)
            case_num += 1

    return cases


def main():
    cases = generate_holdout_cases()
    out_path = pathlib.Path("research/fixtures/holdout/LN-09_holdout.jsonl")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        for c in cases:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")

    print(f"Generated {len(cases)} holdout cases at {out_path}")
    fault_counts = {}
    for c in cases:
        fid = c["fault_id"]
        fault_counts[fid] = fault_counts.get(fid, 0) + 1
    print("Fault breakdown:", fault_counts)


if __name__ == "__main__":
    main()
