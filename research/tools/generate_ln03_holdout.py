#!/usr/bin/env python3
"""Generate independent 120-case holdout dataset for LN-03 (Dual-Mode Spaced Learning).

Fault types:
1. nominal (24 cases)
2. missing_fact_base (24 cases)
3. not_due_for_review (24 cases)
4. non_finite_stability_weight (24 cases)
5. unverified_source_claim (24 cases)
Total: 120 cases.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERITAGE_ENTITIES = [
    {"id": "urn_cao_dinh_rong", "label": "Cao Đỉnh - Phi Long (Rồng bay)", "type": "relic-motif"},
    {"id": "urn_nhan_dinh_ngo_mon", "label": "Nhân Đỉnh - Cửa Ngọ Môn", "type": "imperial-site"},
    {"id": "urn_chuong_dinh_song_huong", "label": "Chương Đỉnh - Hương Giang (Sông Hương)", "type": "geographic-motif"},
    {"id": "urn_anh_dinh_nui_ngu_binh", "label": "Anh Đỉnh - Ngự Bình Sơn", "type": "geographic-motif"},
    {"id": "urn_nghi_dinh_bach_dang", "label": "Nghị Đỉnh - Bạch Đằng Giang", "type": "historical-site"},
    {"id": "urn_thuan_dinh_thuan_thien", "label": "Thuần Đỉnh - Thuận Thiên Kiếm", "type": "relic-motif"},
    {"id": "urn_tuyen_dinh_dien_thai_hoa", "label": "Tuyên Đỉnh - Điện Thái Hòa", "type": "imperial-site"},
    {"id": "urn_du_dinh_the_mieu", "label": "Dụ Đỉnh - Thế Miếu", "type": "imperial-site"},
    {"id": "urn_huyen_dinh_hien_lam_cac", "label": "Huyền Đỉnh - Hiển Lâm Các", "type": "imperial-site"},
    {"id": "urn_cao_dinh_mat_troi", "label": "Cao Đỉnh - Thái Dương (Mặt trời)", "type": "astronomical-motif"},
    {"id": "urn_nhan_dinh_mat_trang", "label": "Nhân Đỉnh - Thái Âm (Mặt trăng)", "type": "astronomical-motif"},
    {"id": "urn_chuong_dinh_bien_dong", "label": "Chương Đỉnh - Đông Hải (Biển Đông)", "type": "geographic-motif"},
]

LEARNER_PROFILES = [
    {"profile_id": "SYN-HO-NOVICE", "is_new": True, "access": "standard", "event_condition": "regular", "competencies": {"S1": 0.1, "S2": 0.15, "S3": 0.1, "S4": 0.1}},
    {"profile_id": "SYN-HO-INTERMEDIATE", "is_new": False, "access": "standard", "event_condition": "regular", "competencies": {"S1": 0.5, "S2": 0.5, "S3": 0.45, "S4": 0.4}},
    {"profile_id": "SYN-HO-ADVANCED", "is_new": False, "access": "standard", "event_condition": "regular", "competencies": {"S1": 0.85, "S2": 0.9, "S3": 0.8, "S4": 0.85}},
    {"profile_id": "SYN-HO-SOURCE-ANALYST", "is_new": False, "access": "standard", "event_condition": "regular", "competencies": {"S1": 0.3, "S2": 0.6, "S3": 0.95, "S4": 0.7}},
    {"profile_id": "SYN-HO-SPATIAL-HISTORIAN", "is_new": False, "access": "standard", "event_condition": "regular", "competencies": {"S1": 0.95, "S2": 0.4, "S3": 0.3, "S4": 0.5}},
    {"profile_id": "SYN-HO-ARGUMENTATIVE", "is_new": False, "access": "standard", "event_condition": "regular", "competencies": {"S1": 0.4, "S2": 0.5, "S3": 0.6, "S4": 0.9}},
]

NON_FINITE_WEIGHTS = ["NaN", "Inf", "-Inf", None, "nan", "inf", "-inf", "undefined"]


def canonical_hash(obj: dict) -> str:
    s = json.dumps(obj, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def generate_cases():
    cases = []
    case_idx = 1
    now_utc = "2026-11-08T12:00:00Z"
    due_past = "2026-11-02T12:00:00Z"
    due_future = "2026-11-20T12:00:00Z"
    last_review = "2026-10-25T12:00:00Z"

    # 1. nominal: 24 cases
    for i in range(24):
        cid = f"LN-03-HO-{case_idx:05d}"
        entity = HERITAGE_ENTITIES[i % len(HERITAGE_ENTITIES)]
        learner = dict(LEARNER_PROFILES[i % len(LEARNER_PROFILES)])
        learner["synthetic"] = True
        weight = 1.0 + (i % 5) * 0.05

        card = {
            "id": f"card-{entity['id']}",
            "difficulty": 4.5 + (i % 3) * 0.5,
            "stability_days": 4.0 + (i % 4) * 1.5,
            "state": "review",
            "due_utc": due_past,
            "last_review_utc": last_review,
            "source_verified": True,
            "target_retention": 0.9,
        }

        scenario_input = {
            "case_id": cid,
            "task_type": "historical_explanation",
            "fact_prerequisite_mastered": True,
            "content": entity,
            "learner": learner,
            "now_utc": now_utc,
            "review_card": card,
            "scheduler_weight": weight,
            "seed": 20261108 + case_idx,
        }

        cases.append({
            "case_id": cid,
            "paper_id": "LN-03",
            "cohort": "INDEPENDENT_HOLDOUT",
            "fault_id": "nominal",
            "materializer_version": "3.0",
            "input": scenario_input,
            "input_hash": canonical_hash(scenario_input),
            "oracle": {
                "basis": "PEDAGOGICAL_SPEC_DUAL_MODE",
                "expected_decision": "schedule_eligible",
                "expected_generative": True,
                "expected_review_burden": 2.0,
                "reason": "Due, fact prerequisite mastered, and source verified",
            },
        })
        case_idx += 1

    # 2. missing_fact_base: 24 cases
    for i in range(24):
        cid = f"LN-03-HO-{case_idx:05d}"
        entity = HERITAGE_ENTITIES[i % len(HERITAGE_ENTITIES)]
        learner = dict(LEARNER_PROFILES[i % len(LEARNER_PROFILES)])
        learner["synthetic"] = True
        weight = 1.0 + (i % 5) * 0.05

        card = {
            "id": f"card-{entity['id']}",
            "difficulty": 5.0 + (i % 3) * 0.5,
            "stability_days": 3.0 + (i % 4) * 1.0,
            "state": "review",
            "due_utc": due_past,
            "last_review_utc": last_review,
            "source_verified": True,
            "target_retention": 0.9,
        }

        scenario_input = {
            "case_id": cid,
            "task_type": "historical_explanation",
            "fact_prerequisite_mastered": False,  # Missing prerequisite fact!
            "content": entity,
            "learner": learner,
            "now_utc": now_utc,
            "review_card": card,
            "scheduler_weight": weight,
            "seed": 20261108 + case_idx,
        }

        cases.append({
            "case_id": cid,
            "paper_id": "LN-03",
            "cohort": "INDEPENDENT_HOLDOUT",
            "fault_id": "missing_fact_base",
            "materializer_version": "3.0",
            "input": scenario_input,
            "input_hash": canonical_hash(scenario_input),
            "oracle": {
                "basis": "PEDAGOGICAL_SPEC_DUAL_MODE",
                "expected_decision": "assign_fact_retrieval",
                "expected_generative": False,
                "expected_review_burden": 1.0,
                "reason": "Generative explanation blocked due to unmastered fact prerequisite; routed to retrieval",
            },
        })
        case_idx += 1

    # 3. not_due_for_review: 24 cases
    for i in range(24):
        cid = f"LN-03-HO-{case_idx:05d}"
        entity = HERITAGE_ENTITIES[i % len(HERITAGE_ENTITIES)]
        learner = dict(LEARNER_PROFILES[i % len(LEARNER_PROFILES)])
        learner["synthetic"] = True
        weight = 1.0 + (i % 5) * 0.05
        future_days = 5 + (i % 15)
        due_str = f"2026-11-{13 + (i % 15):02d}T12:00:00Z"

        card = {
            "id": f"card-{entity['id']}",
            "difficulty": 5.0,
            "stability_days": float(future_days),
            "state": "review",
            "due_utc": due_str,  # In the future!
            "last_review_utc": last_review,
            "source_verified": True,
            "target_retention": 0.9,
        }

        scenario_input = {
            "case_id": cid,
            "task_type": "historical_explanation",
            "fact_prerequisite_mastered": True,
            "content": entity,
            "learner": learner,
            "now_utc": now_utc,
            "review_card": card,
            "scheduler_weight": weight,
            "seed": 20261108 + case_idx,
        }

        cases.append({
            "case_id": cid,
            "paper_id": "LN-03",
            "cohort": "INDEPENDENT_HOLDOUT",
            "fault_id": "not_due_for_review",
            "materializer_version": "3.0",
            "input": scenario_input,
            "input_hash": canonical_hash(scenario_input),
            "oracle": {
                "basis": "PEDAGOGICAL_SPEC_DUAL_MODE",
                "expected_decision": "postpone",
                "expected_generative": False,
                "expected_review_burden": 0.0,
                "reason": "Card not yet due according to spaced repetition interval",
            },
        })
        case_idx += 1

    # 4. non_finite_stability_weight: 24 cases
    for i in range(24):
        cid = f"LN-03-HO-{case_idx:05d}"
        entity = HERITAGE_ENTITIES[i % len(HERITAGE_ENTITIES)]
        learner = dict(LEARNER_PROFILES[i % len(LEARNER_PROFILES)])
        learner["synthetic"] = True
        bad_weight = NON_FINITE_WEIGHTS[i % len(NON_FINITE_WEIGHTS)]

        card = {
            "id": f"card-{entity['id']}",
            "difficulty": 5.0,
            "stability_days": 5.0,
            "state": "review",
            "due_utc": due_past,
            "last_review_utc": last_review,
            "source_verified": True,
            "target_retention": 0.9,
        }

        scenario_input = {
            "case_id": cid,
            "task_type": "historical_explanation",
            "fact_prerequisite_mastered": True,
            "content": entity,
            "learner": learner,
            "now_utc": now_utc,
            "review_card": card,
            "scheduler_weight": bad_weight,  # Non-finite!
            "seed": 20261108 + case_idx,
        }

        cases.append({
            "case_id": cid,
            "paper_id": "LN-03",
            "cohort": "INDEPENDENT_HOLDOUT",
            "fault_id": "non_finite_stability_weight",
            "materializer_version": "3.0",
            "input": scenario_input,
            "input_hash": canonical_hash(scenario_input),
            "oracle": {
                "basis": "PEDAGOGICAL_SPEC_DUAL_MODE",
                "expected_decision": "reject_invalid_scheduler",
                "expected_generative": False,
                "expected_review_burden": 0.0,
                "reason": "Scheduler stability weight non-finite or malformed",
            },
        })
        case_idx += 1

    # 5. unverified_source_claim: 24 cases
    for i in range(24):
        cid = f"LN-03-HO-{case_idx:05d}"
        entity = HERITAGE_ENTITIES[i % len(HERITAGE_ENTITIES)]
        learner = dict(LEARNER_PROFILES[i % len(LEARNER_PROFILES)])
        learner["synthetic"] = True
        weight = 1.0 + (i % 5) * 0.05

        card = {
            "id": f"card-{entity['id']}",
            "difficulty": 5.0 + (i % 3) * 0.5,
            "stability_days": 4.0 + (i % 4) * 1.5,
            "state": "review",
            "due_utc": due_past,
            "last_review_utc": last_review,
            "source_verified": False,  # Unverified source!
            "target_retention": 0.9,
        }

        scenario_input = {
            "case_id": cid,
            "task_type": "historical_explanation",
            "fact_prerequisite_mastered": True,
            "content": entity,
            "learner": learner,
            "now_utc": now_utc,
            "review_card": card,
            "scheduler_weight": weight,
            "seed": 20261108 + case_idx,
        }

        cases.append({
            "case_id": cid,
            "paper_id": "LN-03",
            "cohort": "INDEPENDENT_HOLDOUT",
            "fault_id": "unverified_source_claim",
            "materializer_version": "3.0",
            "input": scenario_input,
            "input_hash": canonical_hash(scenario_input),
            "oracle": {
                "basis": "PEDAGOGICAL_SPEC_DUAL_MODE",
                "expected_decision": "block_explanation",
                "expected_generative": False,
                "expected_review_burden": 0.0,
                "reason": "Generative explanation blocked due to unverified or absent historical source",
            },
        })
        case_idx += 1

    return cases


def main():
    cases = generate_cases()
    out_path = Path(__file__).resolve().parents[2] / "research" / "fixtures" / "holdout" / "LN-03_holdout.jsonl"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", encoding="utf-8") as f:
        for c in cases:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")

    print(f"Generated {len(cases)} holdout cases at: {out_path}")


if __name__ == "__main__":
    main()
