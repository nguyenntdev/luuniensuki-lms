#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate independent 120-case holdout dataset for LN-10.

Evaluates Self-Regulated Learning (SRL) cyclical state machine transitions.
5 fault types × 24 cases = 120 total cases:
1. nominal: Authorized student, matching version, rationale provided, reflection complete.
2. missing_forethought_rationale: Blank/missing pedagogical rationale for revision.
3. unauthorized_actor: Learner does not own the project, or unauthorized peer actor.
4. offline_version_conflict: Mismatched expected_version vs project version (stale cache/concurrent edit).
5. skipped_reflection_gate: Submit action attempted with reflection_completed=False.
"""
import hashlib
import json
import pathlib

HERITAGE_CONTENTS = [
    {"id": "ngo-mon", "label": "Ngọ Môn", "type": "imperial-site"},
    {"id": "dien-thai-hoa", "label": "Điện Thái Hòa", "type": "imperial-palace"},
    {"id": "the-to-mieu", "label": "Thế Tổ Miếu", "type": "imperial-shrine"},
    {"id": "cao-dinh", "label": "Cao Đỉnh (Cửu Đỉnh)", "type": "dynastic-urn"},
    {"id": "nhan-dinh", "label": "Nhân Đỉnh (Cửu Đỉnh)", "type": "dynastic-urn"},
    {"id": "chuong-dinh", "label": "Chương Đỉnh (Cửu Đỉnh)", "type": "dynastic-urn"},
    {"id": "lang-tu-duc", "label": "Lăng Tự Đức (Khiêm Lăng)", "type": "imperial-tomb"},
    {"id": "lang-khai-dinh", "label": "Lăng Khải Định (Ứng Lăng)", "type": "imperial-tomb"},
    {"id": "dan-nam-giao", "label": "Đàn Nam Giao", "type": "altar"},
    {"id": "song-huong", "label": "Sông Hương (Hương Giang)", "type": "natural-heritage"},
    {"id": "chua-thien-mu", "label": "Chùa Thiên Mụ", "type": "religious-site"},
    {"id": "ky-dai", "label": "Kỳ Đài Huế", "type": "fortification"},
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

PROJECT_GOALS = [
    ("evidence_based_conservation_proposal", "heritage_learning_campaign"),
    ("nine_urns_iconography_synthesis", "epigraphic_comparative_catalog"),
    ("nguyen_urban_hydrology_analysis", "monsoon_flood_resilience_plan"),
    ("citadel_defense_spatial_chronology", "citadel_restoration_evidence_board"),
]

RATIONALES = [
    "Khảo sát thực địa và đối chiếu Đại Nam Nhất Thống Chí đòi hỏi tái cấu trúc giả thuyết.",
    "Bổ sung nguồn văn khắc Hán Nôm trên Cao Đỉnh chứng minh biểu tượng chủ quyền biển đảo.",
    "Phân tích ảnh viễn thám và sơ đồ thủy hệ Ngự Hà cho thấy cần mở rộng phạm vi nghiên cứu.",
    "Tư liệu Châu bản triều Nguyễn làm rõ niên đại trùng tu thời Thành Thái.",
    "Đối sánh bản dịch Khâm định Đại Nam hội điển sự lệ với hiện vật Cửu Đỉnh.",
    "Kết quả đo đạc thực địa lăng Khiêm Lăng phát hiện sai số trong phân kỳ quy hoạch cũ.",
]


def generate_holdout_cases():
    cases = []
    fault_types = [
        "nominal",
        "missing_forethought_rationale",
        "unauthorized_actor",
        "offline_version_conflict",
        "skipped_reflection_gate",
    ]

    case_num = 1
    for fault_id in fault_types:
        for i in range(24):
            case_id = f"LN-10-HOLD-{case_num:05d}"
            content = HERITAGE_CONTENTS[i % len(HERITAGE_CONTENTS)]
            prof_id, comps, is_new = LEARNER_PROFILES[i % len(LEARNER_PROFILES)]
            initial_goal, new_goal = PROJECT_GOALS[i % len(PROJECT_GOALS)]
            rationale_text = RATIONALES[i % len(RATIONALES)]
            seed = 20261201 + case_num

            # Base configuration
            base_version = 2 + (i % 5)
            actor = {"owns_project": True, "role": "student"}
            project = {
                "goal": initial_goal,
                "state": "monitoring",
                "version": base_version,
                "type": "heritage_city",
                "reflection_completed": True,
            }
            transition = {
                "action": "revise_plan",
                "expected_version": base_version,
                "new_goal": new_goal,
                "rationale": rationale_text,
            }

            if fault_id == "nominal":
                oracle_decision = "allow_authorized_transition"
                oracle_reason = "Có mục tiêu, xác nhận và lí do"
            elif fault_id == "missing_forethought_rationale":
                transition["rationale"] = ""
                oracle_decision = "request_reflection"
                oracle_reason = "Thiếu lí do điều chỉnh"
            elif fault_id == "unauthorized_actor":
                actor["owns_project"] = False
                oracle_decision = "deny_transition"
                oracle_reason = "Vai trò không được chỉnh sửa"
            elif fault_id == "offline_version_conflict":
                # Stale expected_version from offline client
                transition["expected_version"] = base_version - 1
                oracle_decision = "resolve_revision_conflict"
                oracle_reason = "Hai phiên chỉnh sửa xung đột"
            elif fault_id == "skipped_reflection_gate":
                project["reflection_completed"] = False
                transition["action"] = "submit"
                oracle_decision = "reject_premature_submit"
                oracle_reason = "Nộp trước khi có phản tư cần thiết"
            else:
                raise ValueError(f"Unknown fault: {fault_id}")

            case_input = {
                "case_id": case_id,
                "actor": actor,
                "content": content,
                "learner": {
                    "access": "standard",
                    "competencies": comps,
                    "event_condition": "regular",
                    "is_new": is_new,
                    "profile_id": prof_id,
                    "synthetic": True,
                },
                "project": project,
                "seed": seed,
                "transition": transition,
            }

            input_bytes = json.dumps(case_input, sort_keys=True).encode("utf-8")
            input_hash = hashlib.sha256(input_bytes).hexdigest()

            row = {
                "case_id": case_id,
                "cohort": "INDEPENDENT_HOLDOUT",
                "fault_id": fault_id,
                "canonical_fault": {
                    "nominal": "nominal",
                    "missing_forethought_rationale": "missing_rationale",
                    "unauthorized_actor": "unauthorized_actor",
                    "offline_version_conflict": "offline_conflict",
                    "skipped_reflection_gate": "skipped_reflection",
                }[fault_id],
                "input": case_input,
                "input_hash": input_hash,
                "materializer_version": "2.1-holdout",
                "oracle": {
                    "basis": "ZIMMERMAN_SRL_CYCLICAL_INVARIANT",
                    "expected_decision": oracle_decision,
                    "reason": oracle_reason,
                },
                "paper_id": "LN-10",
                "source_commit": "54da2beb71f3df70e1f00b215ae0fb1a850eb263",
            }
            cases.append(row)
            case_num += 1

    return cases


def main():
    cases = generate_holdout_cases()
    out_path = pathlib.Path("research/fixtures/holdout/LN-10_holdout.jsonl")
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
