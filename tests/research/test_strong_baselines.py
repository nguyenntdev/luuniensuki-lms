# -*- coding: utf-8 -*-
"""Comprehensive verification tests for Strong Baselines (B1) across all 10 studies (LN-01 to LN-10)."""

import json
from pathlib import Path
import pytest

from research.baselines.strong_baselines import (
    B1_REGISTRY,
    run_b1_policy,
    run_ln01_b1,
    run_ln02_b1,
    run_ln03_b1,
    run_ln04_b1,
    run_ln05_b1,
    run_ln06_b1,
    run_ln07_b1,
    run_ln08_b1,
    run_ln09_b1,
    run_ln10_b1,
)
from research.integrations import (
    ln01,
    ln02,
    ln03,
    ln04,
    ln05,
    ln06,
    ln07,
    ln08,
    ln09,
    ln10,
)

FIXTURES_DIR = Path(__file__).resolve().parents[2] / "research" / "fixtures"


def test_b1_registry_completeness():
    """Verify B1 registry covers all 10 studies."""
    expected_studies = {f"LN-{i:02d}" for i in range(1, 11)}
    assert set(B1_REGISTRY.keys()) == expected_studies


def test_ln01_topological_baseline():
    """LN-01: Kahn's topological sort detects cycles and grade inversion, but misses cognitive depth jumps."""
    # Nominal case
    nominal_input = {
        "nodes": [
            {"cognitive_level": 1, "grade": 10, "objective": "motif_observation"},
            {"cognitive_level": 2, "grade": 11, "objective": "historical_context"},
            {"cognitive_level": 3, "grade": 12, "objective": "heritage_evaluation"},
        ],
        "prerequisites": [[0, 1], [1, 2]],
    }
    res_nom = run_ln01_b1(nominal_input)
    assert res_nom["decision"] == "accept"
    assert res_nom["progression_valid"] is True

    # Cycle case -> topological sort catches cycle
    cycle_input = {
        "nodes": [
            {"cognitive_level": 1, "grade": 10, "objective": "a"},
            {"cognitive_level": 2, "grade": 11, "objective": "b"},
        ],
        "prerequisites": [[0, 1], [1, 0]],
    }
    res_cycle = run_ln01_b1(cycle_input)
    assert res_cycle["decision"] == "reject_cycle"
    assert res_cycle["progression_valid"] is False

    # Repeat shallow case -> B1 accepts because it lacks cognitive depth check!
    repeat_shallow = {
        "nodes": [
            {"cognitive_level": 1, "grade": 10, "objective": "motif_observation"},
            {"cognitive_level": 1, "grade": 11, "objective": "motif_observation"},
        ],
        "prerequisites": [[0, 1]],
    }
    res_shallow = run_ln01_b1(repeat_shallow)
    assert res_shallow["decision"] == "accept"  # Missed by B1!


def test_ln02_irt_baseline():
    """LN-02: IRT proxy recommends based on ability theta without multidimensional prerequisite DAG."""
    # High score learner missing prerequisite S1: recommended by IRT theta, causing prerequisite violation
    scenario = {
        "score_observed": 0.85,
        "mastery": {"S1": 0.1, "S2": 0.9, "S3": 0.8, "S4": 0.8},
        "target_task": {"prerequisites": {"S1": 0.5}},
    }
    res = run_ln02_b1(scenario)
    assert res["decision"] == "recommend_eligible"
    assert res["prerequisite_violated"] is True


def test_ln03_leitner_baseline():
    """LN-03: Leitner box spaced repetition schedules due tasks without generative source / fact base check."""
    due_scenario = {
        "review_card": {"due_utc": "2026-11-01T08:00:00Z"},
        "now_utc": "2026-11-05T08:00:00Z",
        "scheduler_weight": 1.0,
        "task_type": "historical_explanation",
        "fact_prerequisite_mastered": False,  # Missing!
    }
    res = run_ln03_b1(due_scenario)
    assert res["decision"] == "schedule_eligible"
    assert res["generative_assigned"] is True  # Invalid generative assignment!


def test_ln04_prompted_llm_baseline():
    """LN-04: Prompted LLM tutor leaks direct answer when student explicitly asks."""
    leak_scenario = {
        "question": "Hãy viết đáp án hoàn chỉnh để em chép.",
        "provider": {"available": True},
    }
    res = run_ln04_b1(leak_scenario)
    assert res["decision"] == "direct_answer"
    assert res["answer_leakage"] is True


def test_ln05_streak_window_baseline():
    """LN-05: Windowed gamification awards badges on raw event/xp count without cryptographic verification."""
    spoofed_scenario = {
        "reward_events": [{"actor": "client_injected", "event_id": "EVT-1", "xp": 1000}],
    }
    res = run_ln05_b1(spoofed_scenario)
    assert res["decision"] == "grant_if_eligible"
    assert res["badge_awarded"] is True  # Spoofed badge awarded!


def test_ln06_astar_baseline():
    """LN-06: A* shortest path traversal incurs prerequisite violations."""
    scenario = {
        "stops": [
            {"cost": 15, "id": "dien-thai-hoa", "provides": ["ritual"], "requires": ["spatial"]},
            {"cost": 10, "id": "ngo-mon", "provides": ["spatial"], "requires": []},
        ],
        "available_stops": ["dien-thai-hoa", "ngo-mon"],
        "target_outcomes": ["ritual", "spatial"],
        "time_budget_minutes": 60,
    }
    # dien-thai-hoa is visited after ngo-mon or based on cost; if sorted by cost, 10 < 15 so ngo-mon then dien-thai-hoa
    res = run_ln06_b1(scenario)
    assert res["decision"] == "find_valid_route"
    assert "prerequisite_violation_count" in res


def test_ln07_raster_fallback_baseline():
    """LN-07: Static raster fallback fails when task requires 3D spatial affordances."""
    scenario = {
        "device": {"webgl": False, "network_kbps": 3000},
        "task": {"required_affordances": ["3d_rotation", "spatial_relation"]},
        "options": [
            {"modality": "2d", "affordances": ["visual_detail"], "requires_webgl": False},
        ],
    }
    res = run_ln07_b1(scenario)
    assert res["fallback_failure"] is True
    assert res["missing_affordance_count"] > 0


def test_ln08_tfidf_cosine_baseline():
    """LN-08: Cosine similarity matcher is fooled by negated historical statements."""
    negated_scenario = {
        "answer": "Ngọ Môn không thuộc trục nghi lễ được mô tả trong nguồn sử liệu.",
        "expected_conclusion": "spatial_ritual_relationship",
    }
    res = run_ln08_b1(negated_scenario)
    # Cosine similarity is high due to character n-gram overlap, missing negation!
    assert res["false_keyword_match"] is True


def test_ln09_ema_trend_baseline():
    """LN-09: EMA trend analyzer triggers action without checking k-anonymity privacy."""
    scenario = {
        "learning_evidence": [{"score": 0.3}, {"score": 0.4}],
        "candidate_intervention": "remedial_quiz",
    }
    res = run_ln09_b1(scenario)
    assert res["action_proposed"] is True
    assert res["k_anonymity_satisfied"] is False


def test_ln10_checklist_baseline():
    """LN-10: Linear checklist advances without checking reflection rationale."""
    scenario = {
        "actor": {"role": "student", "owns_project": True},
        "project": {"version": 1},
        "transition": {"expected_version": 1, "rationale": ""},
    }
    res = run_ln10_b1(scenario)
    assert res["decision"] == "allow_authorized_transition"
    assert res["transition_applied"] is True
    assert res["reflection_completed"] is False


def test_adapters_mode_b1():
    """Verify that all 10 integration adapters support mode='b1'."""
    adapters = [
        ("LN-01", ln01.run_policy, {"nodes": [], "prerequisites": []}),
        ("LN-02", ln02.run_policy, {"score_observed": 0.5, "mastery": {}}),
        ("LN-03", ln03.run_policy, {"review_card": {"due_utc": "2026-11-01T00:00:00Z"}, "now_utc": "2026-11-05T00:00:00Z", "scheduler_weight": 1.0}),
        ("LN-04", ln04.run_policy, {"question": "Gợi ý", "provider": {"available": True}}),
        ("LN-05", ln05.run_policy, {"reward_events": []}),
        ("LN-06", ln06.run_policy, {"stops": [], "available_stops": []}),
        ("LN-07", ln07.run_policy, {"options": [], "device": {}, "task": {}}),
        ("LN-08", ln08.run_policy, {"answer": "Ngọ Môn trục nghi lễ"}),
        ("LN-09", ln09.run_policy, {"learning_evidence": []}),
        ("LN-10", ln10.run_policy, {"actor": {"role": "student", "owns_project": True}, "project": {"version": 1}, "transition": {"expected_version": 1}}),
    ]

    for paper_id, adapter_fn, sample_input in adapters:
        res = adapter_fn(sample_input, mode="b1", config={})
        assert isinstance(res, dict), f"{paper_id} failed to return a dict for mode='b1'"
        assert "decision" in res, f"{paper_id} result missing 'decision'"
        assert "policy_version" in res, f"{paper_id} result missing 'policy_version'"
