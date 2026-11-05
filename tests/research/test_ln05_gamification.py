"""Automated tests for Study LN-05 (Evidence-Based Mastery Gamification).

Verifies invariants:
- INV-LN-05-01: Client-supplied XP cannot grant competency badges.
- INV-LN-05-02: Replaying the same task does not create new independent evidence.
- INV-LN-05-03: Mastery badge requires genuine competency evidence (>= threshold).
- INV-LN-05-04: Outdated event policy version triggers revalidation.
- INV-LN-05-05: Separation of XP from mastery.
"""

import json
from pathlib import Path
import pytest

from research.gamification.mastery_reward_policy import (
    evaluate_mastery_reward_ablation,
    evaluate_mastery_reward_baseline,
    evaluate_mastery_reward_intervention,
)
from research.integrations.ln05 import run_policy


FIXTURE_PATH = (
    Path(__file__).resolve().parents[2]
    / "LUU_NIEN_SPEC_10_STUDIES_MODULAR_FULL_2026"
    / "LUU_NIEN_SPEC_MODULAR_10_STUDIES_2026"
    / "04_FIXTURES"
    / "CONCRETE"
    / "LN-05_concrete.jsonl"
)


def test_nominal_intervention():
    scenario = {
        "badge": {
            "id": "historical_reasoning_mastery",
            "min_level": 0.75,
            "policy_version": 2,
            "requires_competency": "S3",
        },
        "event_policy_version": 2,
        "reward_events": [
            {"actor": "server", "event_id": "EVT-A", "kind": "task_mastery", "xp": 20}
        ],
        "skill_evidence": {"S3": 0.9, "verified_task": True},
    }
    res = evaluate_mastery_reward_intervention(scenario)
    assert res.decision == "grant_if_eligible"
    assert res.badge_awarded is True
    assert "verified_competency_achieved" in res.reason_codes


def test_duplicate_events_intervention():
    scenario = {
        "badge": {
            "id": "historical_reasoning_mastery",
            "min_level": 0.75,
            "policy_version": 2,
            "requires_competency": "S3",
        },
        "event_policy_version": 2,
        "reward_events": [
            {"actor": "server", "event_id": "EVT-A", "kind": "task_mastery", "xp": 20},
            {"actor": "server", "event_id": "EVT-A", "kind": "task_mastery", "xp": 20},
        ],
        "skill_evidence": {"S3": 0.9, "verified_task": True},
    }
    res = evaluate_mastery_reward_intervention(scenario)
    assert res.decision == "deduplicate_events"
    assert res.badge_awarded is False
    assert res.observables.get("replay_prevented") is True


def test_missing_competency_intervention():
    scenario = {
        "badge": {
            "id": "historical_reasoning_mastery",
            "min_level": 0.75,
            "policy_version": 2,
            "requires_competency": "S3",
        },
        "event_policy_version": 2,
        "reward_events": [
            {"actor": "server", "event_id": "EVT-A", "kind": "task_mastery", "xp": 20}
        ],
        "skill_evidence": {"S3": 0.1, "verified_task": True},
    }
    res = evaluate_mastery_reward_intervention(scenario)
    assert res.decision == "deny_mastery_badge"
    assert res.badge_awarded is False


def test_spoofed_xp_intervention():
    scenario = {
        "badge": {
            "id": "historical_reasoning_mastery",
            "min_level": 0.75,
            "policy_version": 2,
            "requires_competency": "S3",
        },
        "event_policy_version": 2,
        "reward_events": [
            {"actor": "client", "event_id": "EVT-A", "kind": "task_mastery", "xp": 10000}
        ],
        "skill_evidence": {"S3": 0.9, "verified_task": True},
    }
    res = evaluate_mastery_reward_intervention(scenario)
    assert res.decision == "reject_forged_event"
    assert res.badge_awarded is False


def test_stale_policy_intervention():
    scenario = {
        "badge": {
            "id": "historical_reasoning_mastery",
            "min_level": 0.75,
            "policy_version": 2,
            "requires_competency": "S3",
        },
        "event_policy_version": 1,
        "reward_events": [
            {"actor": "server", "event_id": "EVT-A", "kind": "task_mastery", "xp": 20}
        ],
        "skill_evidence": {"S3": 0.9, "verified_task": True},
    }
    res = evaluate_mastery_reward_intervention(scenario)
    assert res.decision == "revalidate_badge"
    assert res.badge_awarded is False


def test_baseline_always_awards():
    # In baseline, even spoofed XP or missing competency awards badge based on XP/events
    scenario = {
        "reward_events": [
            {"actor": "client", "event_id": "EVT-A", "kind": "task_mastery", "xp": 10000}
        ],
    }
    res = evaluate_mastery_reward_baseline(scenario)
    assert res.decision == "grant_if_eligible"
    assert res.badge_awarded is True


def test_run_policy_adapter_contract():
    scenario = {
        "badge": {
            "id": "historical_reasoning_mastery",
            "min_level": 0.75,
            "policy_version": 2,
            "requires_competency": "S3",
        },
        "event_policy_version": 2,
        "reward_events": [
            {"actor": "server", "event_id": "EVT-A", "kind": "task_mastery", "xp": 20}
        ],
        "skill_evidence": {"S3": 0.9, "verified_task": True},
    }
    out = run_policy(scenario, mode="intervention", config={})
    assert isinstance(out, dict)
    assert out["decision"] == "grant_if_eligible"
    assert "badge_awarded" in out
    assert out["badge_awarded"] is True
    assert isinstance(out["reason_codes"], list)


def test_concrete_fixture_conformance():
    """Verify that intervention matches 100% of the 720 concrete scenarios."""
    if not FIXTURE_PATH.exists():
        pytest.skip("Concrete fixtures not found")

    with open(FIXTURE_PATH, encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            res = run_policy(row["input"], mode="intervention", config={})
            expected = row["oracle"]["expected_decision"]
            assert res["decision"] == expected, f"Failed on {row['case_id']} ({row['fault_id']}): got {res['decision']} expected {expected}"
            # Observable check for derive_study_metrics
            assert "badge_awarded" in res
