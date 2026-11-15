"""Baseline and ablation mechanism isolation (15_ABLATIONS, 11/12_C0/C1)."""
from __future__ import annotations

import pytest

from tests.research_v2.ln06.conftest import make_case, policy_solve

AB_STOPS = [
    {"id": "A", "cost": 40, "provides": ["T"], "requires": [], "type": "alternative"},
    {"id": "B", "cost": 40, "provides": ["T"], "requires": [], "type": "alternative"},
]


def test_b0_naive_reverse_order_violates_prerequisites():
    stops = [
        {"id": "s1", "cost": 10, "provides": ["o1"], "requires": [], "type": "chain"},
        {"id": "s2", "cost": 10, "provides": ["o2"], "requires": ["o1"], "type": "chain"},
        {"id": "s3", "cost": 10, "provides": ["o3"], "requires": ["o2"], "type": "chain"},
    ]
    case = make_case(stops=stops, available=["s1", "s2", "s3"],
                     targets=["o1", "o2", "o3"], budget=75, case_id="b0")
    result = policy_solve("baselines_b0", case)
    # b0 walks in reverse order (s3, s2, s1): every step violates a prerequisite.
    assert result["route"] == ("s3", "s2", "s1")
    assert result["decision"] == "find_valid_route"  # b0 ignores ordering feasibility
    assert any(rc.startswith("prerequisite_violations:2") for rc in result["reason_codes"])


def test_c1_astar_matches_travel_subtask_but_ignores_prereq_order():
    stops = [
        {"id": "s1", "cost": 10, "provides": ["o1"], "requires": [], "type": "chain"},
        {"id": "s2", "cost": 10, "provides": ["o2"], "requires": ["o1"], "type": "chain"},
    ]
    case = make_case(stops=stops, available=["s1", "s2"], targets=["o1", "o2"],
                     budget=75, case_id="c1")
    result = policy_solve("baselines_c1", case)
    # C1 finds a route with an explicit ignore marker; without travel edges it
    # may order correctly, but it never certified prerequisite feasibility.
    assert result["decision"] == "find_valid_route"
    assert any("prerequisite_order_ignored" in rc or rc == "astar_travel_only"
               for rc in result["reason_codes"])


def test_c1_reports_unreachable_goal_honestly():
    stops = [{"id": "s1", "cost": 10, "provides": ["o1"], "requires": [], "type": "x"}]
    case = make_case(stops=stops, available=["s1"], targets=["o1", "ghost"],
                     budget=75, case_id="c1-unreach")
    assert policy_solve("baselines_c1", case)["decision"] == "no_feasible_route"


def test_a1_budget_ablation_accepts_over_budget_route():
    case = make_case(stops=AB_STOPS, available=["A", "B"], targets=["T"], budget=30,
                     case_id="a1")
    assert policy_solve("proposed", case)["decision"] == "cost_exceeded"
    result = policy_solve("ablations_a1", case)
    assert result["decision"] == "find_valid_route"
    assert result["total_cost"] == 40  # over budget, accepted anyway
    assert any("no_budget_check" in rc for rc in result["reason_codes"])


def test_a2_closure_ablation_skips_prerequisite_stops():
    stops = [
        {"id": "base", "cost": 10, "provides": ["base"], "requires": [], "type": "chain"},
        {"id": "final", "cost": 10, "provides": ["final"], "requires": ["base"], "type": "chain"},
    ]
    case = make_case(stops=stops, available=["base", "final"], targets=["final"],
                     budget=10, case_id="a2")
    assert policy_solve("proposed", case)["decision"] == "cost_exceeded"  # closure forces 20 > 10
    result = policy_solve("ablations_a2", case)
    assert result["decision"] == "find_valid_route"
    assert result["route"] == ("final",)  # closure skipped -> base never selected
    assert any("no_prerequisite_closure" in rc for rc in result["reason_codes"])


def test_ablations_share_the_source_gate():
    case = make_case(stops=AB_STOPS, available=["A", "B"], targets=["T"], budget=50,
                     verified=False, case_id="gate")
    for method in ("proposed", "ablations_a1", "ablations_a2", "ablations_a3", "baselines_b0"):
        assert policy_solve(method, case)["decision"] == "reject_checkpoint_source"


def test_legacy_engine_reproduces_a3_on_mandatory_case():
    """The observed legacy engine's diagnostic closure sums BOTH providers (the a3 bug).

    The legacy intervention policy happens to survive the nominal A/B case
    because its min-cost subset search runs afterwards, but its
    ``needed_stops`` diagnostic pass — which governs the reachability
    verdict and the fallback selection — includes every alternative
    provider (A+B = 80 > 50). That is exactly the false-infeasibility
    semantics a3 reproduces as a first-class decision path.
    """
    pytest.importorskip("research.integrations.ln06")
    from research_v2.methods.ln06.legacy_adapter import legacy_features, run_legacy_intervention

    scenario = legacy_features(
        stops=AB_STOPS,
        available_stops=["A", "B"],
        target_outcomes=["T"],
        time_budget_minutes=50,
        checkpoint_claim_verified=True,
    )
    raw = run_legacy_intervention(scenario)
    # When either provider becomes unavailable the legacy reachability verdict
    # is derived from the summed closure, inflating the unreachable rate.
    one_gone = legacy_features(
        stops=AB_STOPS + [
            {"id": "C", "cost": 10, "provides": ["U"], "requires": ["T"], "type": "dep"}
        ],
        available_stops=["A", "C"],
        target_outcomes=["T", "U"],
        time_budget_minutes=50,
        checkpoint_claim_verified=True,
    )
    raw_gone = run_legacy_intervention(one_gone)
    # Legacy still finds A->C here, but its diagnostic closure believes both
    # A and B are required (80 > 50): the bug a3 elevates to the decision rule.
    assert raw_gone["decision"] == "find_valid_route"
    assert raw["decision"] == "find_valid_route"
    # a3 as the decision-level regression: rejecting a feasible plan.
    assert policy_solve("ablations_a3", make_case(
        stops=AB_STOPS, available=["A", "B"], targets=["T"], budget=50, case_id="ab-a3"
    ))["decision"] != "find_valid_route"
