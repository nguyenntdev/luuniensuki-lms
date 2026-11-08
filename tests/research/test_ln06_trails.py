# -*- coding: utf-8 -*-
"""Unit tests for Study LN-06: Cognitive Heritage Trails."""
import json
import os
import sys
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.domain.heritage_checkpoints import (
    HeritageStop,
    LearningCheckpoint,
    RouteObjective,
    RoutePlan,
)
from research.heritage_trails.cognitive_route import (
    evaluate_route_baseline,
    evaluate_route_intervention,
)
from research.integrations.ln06 import run_policy

def _resolve_fixture_path() -> Path:
    candidates = [
        Path(os.environ.get("RESEARCH_FIXTURE_DIR", "")) / "LN-06_concrete.jsonl",
        Path(__file__).resolve().parents[2] / "research" / "fixtures" / "LN-06_concrete.jsonl",
        Path(__file__).resolve().parents[2]
        / "LUU_NIEN_SPEC_10_STUDIES_MODULAR_FULL_2026"
        / "LUU_NIEN_SPEC_MODULAR_10_STUDIES_2026"
        / "04_FIXTURES"
        / "CONCRETE"
        / "LN-06_concrete.jsonl",
    ]
    for c in candidates:
        if c.is_file():
            return c
    return candidates[1]


FIXTURE_PATH = _resolve_fixture_path()


@pytest.fixture
def sample_stops():
    return [
        HeritageStop(
            id="ngo-mon",
            cost=15,
            provides=["spatial_layout"],
            requires=[],
            label="Ngọ Môn",
        ),
        HeritageStop(
            id="dien-thai-hoa",
            cost=15,
            provides=["ritual_context"],
            requires=["spatial_layout"],
            label="Điện Thái Hòa",
        ),
        HeritageStop(
            id="the-mieu",
            cost=15,
            provides=["commemoration"],
            requires=["ritual_context"],
            label="Thế Miếu",
        ),
        HeritageStop(
            id="cuu-dinh",
            cost=15,
            provides=["heritage_interpretation"],
            requires=["commemoration"],
            label="Cửu Đỉnh",
        ),
    ]


def test_nominal_intervention(sample_stops):
    """Test nominal scenario where all checkpoints are valid and feasible."""
    plan = evaluate_route_intervention(
        stops=sample_stops,
        available_stops=["ngo-mon", "dien-thai-hoa", "the-mieu", "cuu-dinh"],
        target_outcomes=["spatial_layout", "ritual_context", "commemoration", "heritage_interpretation"],
        time_budget_minutes=65,
        checkpoint_claim_verified=True,
    )
    assert plan.decision == "find_valid_route"
    assert "nominal" in plan.reason_codes
    assert plan.prerequisite_violation_count == 0
    assert plan.route_cost == 60
    assert plan.stop_sequence == ["ngo-mon", "dien-thai-hoa", "the-mieu", "cuu-dinh"]


def test_unreachable_stop_intervention(sample_stops):
    """Test when an intermediate required stop is not in available_stops."""
    plan = evaluate_route_intervention(
        stops=sample_stops,
        available_stops=["ngo-mon", "dien-thai-hoa", "cuu-dinh"],
        target_outcomes=["spatial_layout", "ritual_context", "commemoration", "heritage_interpretation"],
        time_budget_minutes=65,
        checkpoint_claim_verified=True,
    )
    assert plan.decision == "no_feasible_route"
    assert "unreachable_stop" in plan.reason_codes
    assert plan.unreachable_checkpoint_rate > 0.0


def test_source_gap_intervention(sample_stops):
    """Test rejection when checkpoint source claims are unverified (INV-LN-06-04)."""
    plan = evaluate_route_intervention(
        stops=sample_stops,
        available_stops=["ngo-mon", "dien-thai-hoa", "the-mieu", "cuu-dinh"],
        target_outcomes=["spatial_layout", "ritual_context", "commemoration", "heritage_interpretation"],
        time_budget_minutes=65,
        checkpoint_claim_verified=False,
    )
    assert plan.decision == "reject_checkpoint_source"
    assert "source_gap" in plan.reason_codes


def test_prerequisite_cycle_intervention():
    """Test rejection when stops form a prerequisite cycle (RULE-LN-06-04)."""
    stops_with_cycle = [
        HeritageStop(id="ngo-mon", cost=15, provides=["spatial_layout"], requires=["heritage_interpretation"]),
        HeritageStop(id="dien-thai-hoa", cost=15, provides=["ritual_context"], requires=["spatial_layout"]),
        HeritageStop(id="the-mieu", cost=15, provides=["commemoration"], requires=["ritual_context"]),
        HeritageStop(id="cuu-dinh", cost=15, provides=["heritage_interpretation"], requires=["commemoration"]),
    ]
    plan = evaluate_route_intervention(
        stops=stops_with_cycle,
        available_stops=["ngo-mon", "dien-thai-hoa", "the-mieu", "cuu-dinh"],
        target_outcomes=["spatial_layout", "ritual_context", "commemoration", "heritage_interpretation"],
        time_budget_minutes=65,
        checkpoint_claim_verified=True,
    )
    assert plan.decision == "reject_cycle"
    assert "prerequisite_cycle" in plan.reason_codes


def test_over_budget_intervention(sample_stops):
    """Test cost exceeded decision when budget is insufficient (RULE-LN-06-05)."""
    plan = evaluate_route_intervention(
        stops=sample_stops,
        available_stops=["ngo-mon", "dien-thai-hoa", "the-mieu", "cuu-dinh"],
        target_outcomes=["spatial_layout", "ritual_context", "commemoration", "heritage_interpretation"],
        time_budget_minutes=20,
        checkpoint_claim_verified=True,
    )
    assert plan.decision == "cost_exceeded"
    assert "over_budget" in plan.reason_codes
    assert plan.route_cost == 60


def test_baseline_evaluation(sample_stops):
    """Test baseline naive routing produces prerequisite violations."""
    plan = evaluate_route_baseline(
        stops=sample_stops,
        available_stops=["ngo-mon", "dien-thai-hoa", "the-mieu", "cuu-dinh"],
        target_outcomes=["spatial_layout", "ritual_context", "commemoration", "heritage_interpretation"],
        time_budget_minutes=65,
        checkpoint_claim_verified=True,
    )
    assert plan.decision == "find_valid_route"
    assert plan.prerequisite_violation_count > 0
    assert plan.stop_sequence == ["cuu-dinh", "the-mieu", "dien-thai-hoa", "ngo-mon"]


def test_run_policy_adapter_contract(sample_stops):
    """Verify run_policy adapter matches required observables and types."""
    scenario = {
        "stops": [s.to_dict() for s in sample_stops],
        "available_stops": ["ngo-mon", "dien-thai-hoa", "the-mieu", "cuu-dinh"],
        "target_outcomes": ["spatial_layout", "ritual_context", "commemoration", "heritage_interpretation"],
        "time_budget_minutes": 65,
        "checkpoint_claim_verified": True,
    }
    res = run_policy(scenario, mode="intervention", config={})
    assert isinstance(res, dict)
    assert res["decision"] == "find_valid_route"
    assert isinstance(res["prerequisite_violation_count"], int)
    assert isinstance(res["outcome_coverage"], float)
    assert isinstance(res["route_cost"], int)
    assert isinstance(res["unreachable_checkpoint_rate"], float)
    assert res["policy_version"].startswith("LN-06")


def test_ablation_mode(sample_stops):
    """Test ablation mode toggling prerequisite constraints."""
    stops_with_cycle = [
        HeritageStop(id="ngo-mon", cost=15, provides=["spatial_layout"], requires=["heritage_interpretation"]),
        HeritageStop(id="dien-thai-hoa", cost=15, provides=["ritual_context"], requires=["spatial_layout"]),
        HeritageStop(id="the-mieu", cost=15, provides=["commemoration"], requires=["ritual_context"]),
        HeritageStop(id="cuu-dinh", cost=15, provides=["heritage_interpretation"], requires=["commemoration"]),
    ]
    scenario = {
        "stops": [s.to_dict() for s in stops_with_cycle],
        "available_stops": ["ngo-mon", "dien-thai-hoa", "the-mieu", "cuu-dinh"],
        "target_outcomes": ["spatial_layout", "ritual_context", "commemoration", "heritage_interpretation"],
        "time_budget_minutes": 65,
        "checkpoint_claim_verified": True,
    }
    # Ablation: disable prerequisite check
    res = run_policy(scenario, mode="ablation", config={"enforce_prerequisites": False})
    assert res["decision"] == "find_valid_route"
    assert res["prerequisite_violation_count"] == 1


def test_ablation_variants_aliases(sample_stops):
    """Verify alias configs: shortest_distance_only, ignore_prerequisites, no_theme_filter."""
    stops_with_cycle = [
        HeritageStop(id="ngo-mon", cost=15, provides=["spatial_layout"], requires=["heritage_interpretation"]),
        HeritageStop(id="dien-thai-hoa", cost=15, provides=["ritual_context"], requires=["spatial_layout"]),
        HeritageStop(id="the-mieu", cost=15, provides=["commemoration"], requires=["ritual_context"]),
        HeritageStop(id="cuu-dinh", cost=15, provides=["heritage_interpretation"], requires=["commemoration"]),
    ]
    scenario = {
        "stops": [s.to_dict() for s in stops_with_cycle],
        "available_stops": ["ngo-mon", "dien-thai-hoa", "the-mieu", "cuu-dinh"],
        "target_outcomes": ["spatial_layout", "ritual_context", "commemoration", "heritage_interpretation"],
        "time_budget_minutes": 65,
        "checkpoint_claim_verified": False,
    }
    # A1 alias: shortest_distance_only bypasses prerequisite enforcement
    res_a1_1 = run_policy(scenario, mode="ablation", config={"shortest_distance_only": True, "enforce_sources": False})
    assert res_a1_1["decision"] == "find_valid_route"

    # A1 alias: ignore_prerequisites
    res_a1_2 = run_policy(scenario, mode="ablation", config={"ignore_prerequisites": True, "enforce_sources": False})
    assert res_a1_2["decision"] == "find_valid_route"

    # A3 alias: no_theme_filter / disable_sources
    res_a3 = run_policy(scenario, mode="ablation", config={"no_theme_filter": True})
    # Sources disabled, but cycle is still caught by intervention logic
    assert res_a3["decision"] == "reject_cycle"


def test_edge_cases_and_null_defense(sample_stops):
    """Verify robust handling of empty stops, None fields, and negative budgets."""
    scenario_empty = {
        "stops": [],
        "available_stops": [],
        "target_outcomes": [],
        "time_budget_minutes": None,
        "checkpoint_claim_verified": None,
    }
    res = run_policy(scenario_empty, mode="intervention", config={})
    assert res["decision"] == "find_valid_route"
    assert res["prerequisite_violation_count"] == 0
    assert res["route_cost"] == 0

    # Negative/zero budget with stops needed
    scenario_zero_budget = {
        "stops": [s.to_dict() for s in sample_stops],
        "available_stops": ["ngo-mon"],
        "target_outcomes": ["spatial_layout"],
        "time_budget_minutes": 0,
        "checkpoint_claim_verified": True,
    }
    res = run_policy(scenario_zero_budget, mode="intervention", config={})
    assert res["decision"] == "cost_exceeded"
    assert "over_budget" in res["reason_codes"]


def test_concrete_corpus_conformance():
    """Verify intervention on concrete fixture file matches oracle decisions."""
    assert FIXTURE_PATH.exists(), f"Mandatory fixture missing (fail-closed): {FIXTURE_PATH}"

    count = 0
    with FIXTURE_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            case = json.loads(line)
            res = run_policy(case["input"], mode="intervention", config={})
            assert res["decision"] == case["oracle"]["expected_decision"], (
                f"Mismatch in {case['case_id']}: expected {case['oracle']['expected_decision']}, got {res['decision']}"
            )
            count += 1
    assert count == 720

