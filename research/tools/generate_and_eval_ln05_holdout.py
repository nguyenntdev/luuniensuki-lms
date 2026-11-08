#!/usr/bin/env python3
"""Generate independent 120-case holdout dataset for LN-05 and run comprehensive evaluation.

Study LN-05: Evidence-Based Mastery Gamification & Anti-Replay Idempotency.
Pedagogical Invariants:
- INV-LN-05-01: Client-supplied XP is not evidence of competency (actor provenance).
- INV-LN-05-02: Replaying identical event IDs does not create new independent evidence (anti-replay idempotency).
- INV-LN-05-03: Mastery badge requires genuine competency evidence (score >= threshold on verified task).
- INV-LN-05-04: Outdated event policy versions require revalidation.
- INV-LN-05-05: Separation of XP/streaks from competency mastery.
"""

import json
import hashlib
import math
from pathlib import Path
from typing import Any, Dict, List, Tuple

from research.gamification.mastery_reward_policy import (
    evaluate_mastery_reward_baseline,
    evaluate_mastery_reward_intervention,
    evaluate_mastery_reward_ablation,
    PolicyEvaluationResult,
)


def evaluate_mastery_reward_b1(
    scenario_input: Dict[str, Any],
    config: Dict[str, Any] = None,
) -> PolicyEvaluationResult:
    """Stronger baseline B1: Streak counter with basic deduplication.
    
    Checks for duplicate event_ids in reward_events and rejects them.
    However, it awards badges based on streak / event count without verifying
    historical competency evidence (INV-LN-05-03), without checking client vs server
    provenance (INV-LN-05-01), and without checking policy version freshness (INV-LN-05-04).
    """
    reward_events = scenario_input.get("reward_events", [])
    event_ids = [ev.get("event_id") for ev in reward_events if "event_id" in ev]
    
    # Basic deduplication
    if len(event_ids) != len(set(event_ids)):
        return PolicyEvaluationResult(
            decision="deduplicate_events",
            reason_codes=["replayed_event_detected", "basic_dedup_flag"],
            policy_version="1.1-baseline_b1",
            badge_awarded=False,
            observables={"badge_awarded": False, "replay_prevented": True, "mode": "baseline_b1"},
        )
    
    # Blind streak/XP award without evidence verification
    total_xp = sum(e.get("xp", 0) for e in reward_events)
    awarded = len(reward_events) > 0 or total_xp > 0
    decision = "grant_if_eligible" if awarded else "deny_mastery_badge"
    reason_codes = ["baseline_streak_grant"] if awarded else ["insufficient_streak"]
    
    return PolicyEvaluationResult(
        decision=decision,
        reason_codes=reason_codes,
        policy_version="1.1-baseline_b1",
        badge_awarded=awarded,
        observables={"badge_awarded": awarded, "replay_prevented": False, "mode": "baseline_b1"},
    )


# Cửu Đỉnh cultural motifs and metadata
URNS = [
    {"urn_id": "cao_dinh", "name": "Cao Đỉnh", "emperor": "Thế Tổ Cao Hoàng đế (Gia Long)"},
    {"urn_id": "nhan_dinh", "name": "Nhân Đỉnh", "emperor": "Thánh Tổ Nhân Hoàng đế (Minh Mạng)"},
    {"urn_id": "chuong_dinh", "name": "Chương Đỉnh", "emperor": "Hiến Tổ Chương Hoàng đế (Thiệu Trị)"},
    {"urn_id": "anh_dinh", "name": "Anh Đỉnh", "emperor": "Dực Tông Anh Hoàng đế (Tự Đức)"},
    {"urn_id": "nghi_dinh", "name": "Nghị Đỉnh", "emperor": "Cung Tông Nghị Hoàng đế (Dục Đức)"},
    {"urn_id": "thuan_dinh", "name": "Thuần Đỉnh", "emperor": "Cảnh Tông Thuần Hoàng đế (Đồng Khánh)"},
    {"urn_id": "tuyen_dinh", "name": "Tuyên Đỉnh", "emperor": "Hoằng Tông Tuyên Hoàng đế (Khải Định)"},
    {"urn_id": "du_dinh", "name": "Dụ Đỉnh", "emperor": "Dụ Lăng (Kiến Phúc)"},
    {"urn_id": "huyen_dinh", "name": "Huyền Đỉnh", "emperor": "Tuyên Tôn (Hàm Nghi)"},
]

MOTIFS = [
    {"id": "long", "label": "Rồng (Long)", "type": "vũ trụ - thần thú", "urn": "cao_dinh"},
    {"id": "thai_duong", "label": "Mặt trời (Thái dương)", "type": "thiên văn", "urn": "cao_dinh"},
    {"id": "ngo_mon", "label": "Ngọ Môn", "type": "kiến trúc hoàng thành", "urn": "cao_dinh"},
    {"id": "ky_dai", "label": "Kỳ Đài", "type": "kiến trúc kinh kỳ", "urn": "nhan_dinh"},
    {"id": "song_huong", "label": "Sông Hương (Hương giang)", "type": "sông ngòi", "urn": "nhan_dinh"},
    {"id": "nui_ngu_binh", "label": "Núi Ngự Bình (Ngự Bình sơn)", "type": "núi non phong thủy", "urn": "nhan_dinh"},
    {"id": "cay_que", "label": "Cây quế (Quế mộc)", "type": "thực vật quý", "urn": "chuong_dinh"},
    {"id": "ca_voi", "label": "Cá voi (Nhân ngư / Đức Ngư)", "type": "sinh vật biển", "urn": "chuong_dinh"},
    {"id": "song_gianh", "label": "Sông Gianh (Linh giang)", "type": "sông cương vực", "urn": "anh_dinh"},
    {"id": "voi", "label": "Voi (Tượng)", "type": "động vật tượng trưng", "urn": "anh_dinh"},
    {"id": "chim_phuong", "label": "Chim Phượng (Phượng hoàng)", "type": "thần cầm", "urn": "nghi_dinh"},
    {"id": "song_bach_dang", "label": "Sông Bạch Đằng (Bạch Đằng giang)", "type": "thủy đạo lịch sử", "urn": "nghi_dinh"},
    {"id": "cay_mit", "label": "Cây mít (Ba la mật)", "type": "nông sản bản địa", "urn": "thuan_dinh"},
    {"id": "nui_bach_ma", "label": "Núi Bạch Mã (Bạch Mã sơn)", "type": "danh sơn", "urn": "thuan_dinh"},
    {"id": "song_lo", "label": "Sông Lô (Lô giang)", "type": "đại giang phương bắc", "urn": "tuyen_dinh"},
    {"id": "cay_da", "label": "Cây đa (Cổ thụ)", "type": "thực vật văn hóa", "urn": "tuyen_dinh"},
    {"id": "cay_ngo_dong", "label": "Cây ngô đồng (Ngô đồng mộc)", "type": "hoàng mộc", "urn": "du_dinh"},
    {"id": "huou_sao", "label": "Hươu sao (Lộc)", "type": "điềm lành cát tường", "urn": "du_dinh"},
    {"id": "song_cuu_long", "label": "Sông Cửu Long (Cửu Long giang)", "type": "hệ thống sông nam bộ", "urn": "huyen_dinh"},
    {"id": "cay_sen", "label": "Cây sen (Liên hoa)", "type": "quốc hoa tâm linh", "urn": "huyen_dinh"},
    {"id": "trai_vai", "label": "Trái vải (Lệ chi)", "type": "hoa quả tiến vua", "urn": "cao_dinh"},
    {"id": "ga_trong", "label": "Gà trống (Kê)", "type": "ngũ đức cầm", "urn": "nhan_dinh"},
    {"id": "rua_bien", "label": "Rùa biển (Quy)", "type": "tứ linh trường thọ", "urn": "anh_dinh"},
    {"id": "hoa_mai", "label": "Hoa mai (Mai hoa)", "type": "tứ quý", "urn": "nghi_dinh"},
]

COMPETENCY_BADGES = [
    {
        "id": "source_epigraphy_mastery",
        "requires_competency": "S1",
        "min_level": 0.75,
        "policy_version": 2,
        "name_vi": "Làm chủ Minh văn và Văn tự Hán-Nôm Cửu Đỉnh",
    },
    {
        "id": "spatial_iconography_mastery",
        "requires_competency": "S2",
        "min_level": 0.80,
        "policy_version": 2,
        "name_vi": "Làm chủ Không gian và Cương giới Lãnh thổ Cửu Đỉnh",
    },
    {
        "id": "historical_reasoning_mastery",
        "requires_competency": "S3",
        "min_level": 0.75,
        "policy_version": 2,
        "name_vi": "Làm chủ Suy luận Lịch sử và Biểu tượng Quyền lực",
    },
    {
        "id": "epigraphic_critique_mastery",
        "requires_competency": "S4",
        "min_level": 0.75,
        "policy_version": 2,
        "name_vi": "Làm chủ Phê phán Sử liệu và Đối chiếu Khảo cứu",
    },
]


def generate_holdout_cases() -> List[Dict[str, Any]]:
    """Generate 120 balanced holdout test cases (24 per fault type)."""
    cases = []
    fault_types = [
        ("nominal", 24),
        ("duplicate_events_replay", 24),
        ("missing_competency_evidence", 24),
        ("spoofed_client_xp", 24),
        ("stale_policy_version", 24),
    ]

    case_num = 1
    for fault_id, count in fault_types:
        for idx in range(count):
            case_id = f"LN-05-HOLD-{case_num:05d}"
            motif = MOTIFS[idx % len(MOTIFS)]
            badge_spec = COMPETENCY_BADGES[idx % len(COMPETENCY_BADGES)]
            req_comp = badge_spec["requires_competency"]
            min_lvl = badge_spec["min_level"]

            seed = 20261200 + case_num
            access_mode = "low_bandwidth" if idx % 4 == 0 else "standard"
            profile_id = f"HOLD-PROFILE-{(idx % 6) + 1:02d}"

            comp_profile = {"S1": 0.5, "S2": 0.5, "S3": 0.5, "S4": 0.5}
            event_id = f"EVT-HOLD-{case_num:05d}-A"

            if fault_id == "nominal":
                comp_profile[req_comp] = min_lvl + 0.10
                skill_evidence = {req_comp: min_lvl + 0.10, "verified_task": True}
                reward_events = [{"actor": "server", "event_id": event_id, "kind": "task_mastery", "xp": 25}]
                event_policy_version = 2
                expected_decision = "grant_if_eligible"
                expected_badge_awarded = True
                reason_vi = "Minh chứng năng lực hợp lệ từ bài làm có giám sát, xác thực máy chủ đầy đủ."

            elif fault_id == "duplicate_events_replay":
                comp_profile[req_comp] = min_lvl + 0.10
                skill_evidence = {req_comp: min_lvl + 0.10, "verified_task": True}
                reward_events = [
                    {"actor": "server", "event_id": event_id, "kind": "task_mastery", "xp": 25},
                    {"actor": "server", "event_id": event_id, "kind": "task_mastery", "xp": 25},
                ]
                event_policy_version = 2
                expected_decision = "deduplicate_events"
                expected_badge_awarded = False
                reason_vi = "Tái gửi cùng mã sự kiện (replay) không tạo ra chứng cứ năng lực độc lập mới."

            elif fault_id == "missing_competency_evidence":
                if idx % 2 == 0:
                    score = min_lvl - 0.35
                    skill_evidence = {req_comp: max(0.1, score), "verified_task": True}
                else:
                    score = min_lvl + 0.10
                    skill_evidence = {req_comp: score, "verified_task": False}
                comp_profile[req_comp] = skill_evidence[req_comp]
                reward_events = [{"actor": "server", "event_id": event_id, "kind": "task_mastery", "xp": 25}]
                event_policy_version = 2
                expected_decision = "deny_mastery_badge"
                expected_badge_awarded = False
                reason_vi = "Thiếu minh chứng thực chất hoặc điểm đánh giá nhiệm vụ chưa đạt ngưỡng năng lực tối thiểu."

            elif fault_id == "spoofed_client_xp":
                comp_profile[req_comp] = min_lvl + 0.10
                skill_evidence = {req_comp: min_lvl + 0.10, "verified_task": True}
                reward_events = [
                    {"actor": "client", "event_id": event_id, "kind": "task_mastery", "xp": 25000 + idx * 1000}
                ]
                event_policy_version = 2
                expected_decision = "reject_forged_event"
                expected_badge_awarded = False
                reason_vi = "Sự kiện cấp điểm do client tự phát sinh không có chữ ký số máy chủ, từ chối giả mạo."

            elif fault_id == "stale_policy_version":
                comp_profile[req_comp] = min_lvl + 0.10
                skill_evidence = {req_comp: min_lvl + 0.10, "verified_task": True}
                reward_events = [{"actor": "server", "event_id": event_id, "kind": "task_mastery", "xp": 25}]
                event_policy_version = 1
                expected_decision = "revalidate_badge"
                expected_badge_awarded = False
                reason_vi = "Chính sách năng lực đã nâng cấp phiên bản, sự kiện cũ bắt buộc phải tái thẩm định."

            scenario_input = {
                "badge": {
                    "id": badge_spec["id"],
                    "min_level": min_lvl,
                    "policy_version": badge_spec["policy_version"],
                    "requires_competency": req_comp,
                },
                "case_id": case_id,
                "content": {
                    "id": motif["id"],
                    "label": motif["label"],
                    "type": motif["type"],
                    "urn": motif["urn"],
                },
                "event_policy_version": event_policy_version,
                "learner": {
                    "access": access_mode,
                    "competencies": comp_profile,
                    "event_condition": "holdout_validation",
                    "is_new": (idx % 3 == 0),
                    "profile_id": profile_id,
                    "synthetic": True,
                },
                "reward_events": reward_events,
                "seed": seed,
                "skill_evidence": skill_evidence,
            }

            input_bytes = json.dumps(scenario_input, sort_keys=True).encode("utf-8")
            input_hash = hashlib.sha256(input_bytes).hexdigest()

            record = {
                "case_id": case_id,
                "cohort": "INDEPENDENT_HOLDOUT",
                "fault_id": fault_id,
                "input": scenario_input,
                "input_hash": input_hash,
                "materializer_version": "2.0-holdout",
                "oracle": {
                    "basis": "DESIGN_SPEC_EMPIRICAL_HOLDOUT",
                    "expected_decision": expected_decision,
                    "expected_badge_awarded": expected_badge_awarded,
                    "reason": reason_vi,
                },
                "paper_id": "LN-05",
                "source_commit": "independent-holdout-v5",
            }
            cases.append(record)
            case_num += 1

    return cases


def wilson_score_interval(successes: int, total: int, confidence: float = 0.95) -> Tuple[float, float]:
    """Compute 95% Wilson score confidence interval."""
    if total == 0:
        return (0.0, 0.0)
    z = 1.959963984540054
    p_hat = successes / total
    denom = 1 + (z**2) / total
    center = (p_hat + (z**2) / (2 * total)) / denom
    spread = (z / denom) * math.sqrt((p_hat * (1 - p_hat) / total) + (z**2) / (4 * total**2))
    return (max(0.0, center - spread), min(1.0, center + spread))


def mcnemar_test(contingency_table: Tuple[int, int, int, int]) -> Tuple[float, float]:
    """Compute McNemar test statistic with continuity correction and p-value."""
    _, b, c, _ = contingency_table
    if (b + c) == 0:
        return (0.0, 1.0)
    
    diff = abs(b - c)
    if diff == 0:
        chi2 = 0.0
    else:
        chi2 = ((diff - 1.0) ** 2) / (b + c)
    
    p_val = math.erfc(math.sqrt(chi2 / 2.0))
    return (chi2, p_val)


def main():
    cases = generate_holdout_cases()
    assert len(cases) == 120, f"Expected 120 cases, got {len(cases)}"

    # Save holdout fixture
    out_path = Path("research/fixtures/holdout/LN-05_holdout.jsonl")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        for c in cases:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    print(f"Generated {len(cases)} holdout cases to {out_path}")

    # Verify intervention matches oracle 100%
    for c in cases:
        res = evaluate_mastery_reward_intervention(c["input"])
        exp_dec = c["oracle"]["expected_decision"]
        exp_award = c["oracle"]["expected_badge_awarded"]
        assert res.decision == exp_dec and res.badge_awarded == exp_award, (
            f"Intervention mismatch on {c['case_id']}: got ({res.decision}, {res.badge_awarded})"
        )
    print("Intervention policy conforms 100% to all 120 oracle specifications.")

    # Conditions to evaluate
    conditions = [
        ("B0", "XP-only threshold baseline", lambda inp: evaluate_mastery_reward_baseline(inp)),
        ("B1", "Streak counter with basic deduplication", lambda inp: evaluate_mastery_reward_b1(inp)),
        ("I1", "Proof-of-mastery with event deduplication", lambda inp: evaluate_mastery_reward_intervention(inp)),
        ("A1", "Ablation: xp\\_only (bypass proof \\& deduplication)", lambda inp: evaluate_mastery_reward_ablation(inp, {"ablation_type": "xp_only"})),
        ("A2", "Ablation: disable\\_anti\\_replay (bypass event dedup)", lambda inp: evaluate_mastery_reward_ablation(inp, {"ablation_type": "disable_anti_replay"})),
        ("A3", "Ablation: disable\\_provenance (accept client actor)", lambda inp: evaluate_mastery_reward_ablation(inp, {"ablation_type": "disable_provenance"})),
    ]

    negative_faults = ["duplicate_events_replay", "missing_competency_evidence", "spoofed_client_xp", "stale_policy_version"]
    
    # Store artifacts in research_artifacts/holdout/LN-05/
    artifact_dir = Path("research_artifacts/holdout/LN-05")
    artifact_dir.mkdir(parents=True, exist_ok=True)

    results_dict = {}
    traces_dict = {}

    for cond_id, desc, eval_fn in conditions:
        tp = 0
        fp = 0
        tn = 0
        fn = 0
        fault_fp = {f: 0 for f in negative_faults}
        fault_total = {f: 0 for f in negative_faults}
        decisions_list = []
        trace_rows = []

        for c in cases:
            res = eval_fn(c["input"])
            awarded = res.badge_awarded
            is_nominal = (c["fault_id"] == "nominal")
            decisions_list.append(awarded)

            trace_row = {
                "case_id": c["case_id"],
                "fault_id": c["fault_id"],
                "decision": res.decision,
                "badge_awarded": res.badge_awarded,
                "reason_codes": res.reason_codes,
                "expected_decision": c["oracle"]["expected_decision"],
                "expected_badge_awarded": c["oracle"]["expected_badge_awarded"],
                "oracle_match": (res.decision == c["oracle"]["expected_decision"] and res.badge_awarded == c["oracle"]["expected_badge_awarded"]),
                "observables": res.observables,
            }
            trace_rows.append(trace_row)

            if is_nominal:
                if awarded:
                    tp += 1
                else:
                    fn += 1
            else:
                fault = c["fault_id"]
                fault_total[fault] += 1
                if awarded:
                    fp += 1
                    fault_fp[fault] += 1
                else:
                    tn += 1

        total_neg = sum(fault_total.values())
        false_mastery_rate = fp / total_neg if total_neg > 0 else 0.0
        ci_fmr_low, ci_fmr_high = wilson_score_interval(fp, total_neg)
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        ci_prec_low, ci_prec_high = wilson_score_interval(tp, tp + fp)

        results_dict[cond_id] = {
            "condition_id": cond_id,
            "description": desc,
            "tp": tp,
            "fp": fp,
            "tn": tn,
            "fn": fn,
            "total_neg": total_neg,
            "false_mastery_rate": false_mastery_rate,
            "ci_fmr": [ci_fmr_low, ci_fmr_high],
            "precision": precision,
            "ci_prec": [ci_prec_low, ci_prec_high],
            "nominal_preservation": tp / 24,
            "fault_fp": fault_fp,
            "fault_total": fault_total,
            "decisions": decisions_list,
        }
        traces_dict[cond_id] = trace_rows

        # Write trace file
        trace_file = artifact_dir / f"trace_{cond_id}.jsonl"
        with trace_file.open("w", encoding="utf-8") as tf:
            for tr in trace_rows:
                tf.write(json.dumps(tr, ensure_ascii=False) + "\n")

    # McNemar tests vs I1 on fault cases (N = 96)
    neg_indices = [i for i, c in enumerate(cases) if c["fault_id"] != "nominal"]
    i1_decisions = results_dict["I1"]["decisions"]

    paired_summary = {}
    for cond_id, _, _ in conditions:
        if cond_id == "I1":
            paired_summary["I1"] = {"b": 0, "c": 0, "chi2": 0.0, "p_value": "ref"}
            continue
        c_decisions = results_dict[cond_id]["decisions"]
        a = 0
        b = 0
        c_discord = 0
        d = 0
        for idx in neg_indices:
            i1_safe = not i1_decisions[idx]
            c_safe = not c_decisions[idx]
            if i1_safe and c_safe:
                a += 1
            elif i1_safe and not c_safe:
                b += 1
            elif not i1_safe and c_safe:
                c_discord += 1
            else:
                d += 1
        chi2, p_val = mcnemar_test((a, b, c_discord, d))
        results_dict[cond_id]["mcnemar_chi2"] = chi2
        results_dict[cond_id]["mcnemar_p"] = p_val
        paired_summary[cond_id] = {"b": b, "c": c_discord, "chi2": chi2, "p_value": p_val}

    results_dict["I1"]["mcnemar_chi2"] = 0.0
    results_dict["I1"]["mcnemar_p"] = 1.0

    # Save summary.csv
    csv_path = artifact_dir / "summary.csv"
    with csv_path.open("w", encoding="utf-8") as f:
        f.write("condition,description,false_mastery_numerator,eligible_fault_denom,false_mastery_rate,ci_95_low,ci_95_high,badge_precision,prec_ci_low,prec_ci_high,nominal_preservation,p_vs_I1\n")
        for cond_id, desc, _ in conditions:
            r = results_dict[cond_id]
            p_val = results_dict[cond_id]["mcnemar_p"]
            p_str = "ref" if cond_id == "I1" else (f"{p_val:.2e}" if p_val < 0.0001 else f"{p_val:.4f}")
            f.write(
                f"{cond_id},\"{desc}\",{r['fp']},{r['total_neg']},{r['false_mastery_rate']:.4f},"
                f"{r['ci_fmr'][0]:.4f},{r['ci_fmr'][1]:.4f},{r['precision']:.4f},"
                f"{r['ci_prec'][0]:.4f},{r['ci_prec'][1]:.4f},{r['nominal_preservation']:.4f},{p_str}\n"
            )

    # Save results.json
    json_path = artifact_dir / "results.json"
    clean_results = {
        "study": "LN-05",
        "dataset": "research/fixtures/holdout/LN-05_holdout.jsonl",
        "cases_total": 120,
        "nominal_cases": 24,
        "fault_cases": 96,
        "conditions": {
            cond_id: {k: v for k, v in r.items() if k != "decisions"}
            for cond_id, r in results_dict.items()
        },
        "paired_tests_vs_i1": paired_summary,
    }
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(clean_results, f, ensure_ascii=False, indent=2)

    # Generate results_table.tex
    tex_path = artifact_dir / "results_table.tex"
    with tex_path.open("w", encoding="utf-8") as f:
        f.write("% Empirical evaluation table on independent holdout dataset\n")
        f.write("\\begin{table}[htbp]\n")
        f.write("\\centering\n")
        f.write("\\small\n")
        f.write("\\caption{Empirical Evaluation on Independent 120-Case Holdout Dataset (LN-05 Evidence-Based Mastery Gamification)}\n")
        f.write("\\label{tab:ln-05-holdout-benchmark}\n")
        f.write("\\begin{tabular}{llcccccc}\n")
        f.write("\\toprule\n")
        f.write("Condition & Policy Architecture & False / Denom & False Rate & 95\\% CI & Precision & 95\\% CI & McNemar $p$ \\\\\n")
        f.write("\\midrule\n")
        for cond_id, desc, _ in conditions:
            r = results_dict[cond_id]
            fmr_str = f"{r['fp']} / {r['total_neg']}"
            fmr_pct = f"{r['false_mastery_rate']*100:.1f}\\%"
            ci_fmr_str = f"[{r['ci_fmr'][0]*100:.1f}\\%, {r['ci_fmr'][1]*100:.1f}\\%]"
            prec_pct = f"{r['precision']*100:.1f}\\%"
            ci_prec_str = f"[{r['ci_prec'][0]*100:.1f}\\%, {r['ci_prec'][1]*100:.1f}\\%]"
            p_val = r["mcnemar_p"]
            p_str = "\\textit{ref}" if cond_id == "I1" else ("$p < 10^{-15}$" if p_val < 1e-15 else ("$p < 10^{-4}$" if p_val < 0.0001 else f"$p = {p_val:.4f}$"))
            f.write(f"{cond_id} & {desc} & {fmr_str} & {fmr_pct} & {ci_fmr_str} & {prec_pct} & {ci_prec_str} & {p_str} \\\\\n")
        f.write("\\bottomrule\n")
        f.write("\\end{tabular}\n")
        f.write("\\par\\smallskip\n")
        f.write("\\begin{minipage}{0.98\\linewidth}\\footnotesize\n")
        f.write("Evaluation on $N=120$ independent holdout cases (24 nominal cases with genuine competency evidence, 96 fault cases across 4 orthogonal fault archetypes: event replay duplicates, missing/insufficient competency evidence, client-spoofed XP injections, and stale policy version revalidation). False Rate denotes false mastery award rate on eligible fault cases (lower is better; ideal: 0\\%). Precision denotes genuine competency masteries among total badges awarded (higher is better; ideal: 100\\%). Paired McNemar tests evaluate fault blocking discordant pairs against Intervention I1 (df = 1, continuity-corrected).\n")
        f.write("\\end{minipage}\n")
        f.write("\\end{table}\n")

    print(f"Artifacts successfully written to {artifact_dir}:")
    print(f" - {json_path}")
    print(f" - {csv_path}")
    print(f" - {tex_path}")
    print(f" - trace files (trace_B0..trace_A3.jsonl)")


if __name__ == "__main__":
    main()
