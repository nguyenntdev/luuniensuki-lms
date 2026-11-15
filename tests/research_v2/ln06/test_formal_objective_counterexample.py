"""Mandatory counterexample: A/B same outcome at 40 min each, budget 50.

The scientifically correct outcome: feasible with exactly ONE stop at cost 40
(alternative providers are mutually exclusive). The legacy all-providers
behaviour sums both to 80 and rejects - asserted here as the regression that
the proposed policy fixes.
"""
from __future__ import annotations

from tests.research_v2.ln06.conftest import AB_CASE, AB_STOPS, make_case, policy_solve


def test_proposed_chooses_exactly_one_provider():
    case = make_case(**AB_CASE, case_id="ab-mandatory")
    result = policy_solve("proposed", case)
    assert result["decision"] == "find_valid_route"
    assert result["total_cost"] == 40  # 40 <= 50, never 80
    assert len(result["route"]) == 1
    assert result["route"][0] in ("A", "B")


def test_deterministic_tie_break_by_stop_id():
    case = make_case(**AB_CASE, case_id="ab-tiebreak")
    result = policy_solve("proposed", case)
    assert result["route"] == ("A",)  # lexicographic tie-break


def test_budget_50_with_third_dependent_stop_still_feasible():
    stops = AB_STOPS + [
        {"id": "C", "cost": 10, "provides": ["U"], "requires": ["T"], "type": "dep"}
    ]
    case = make_case(stops=stops, available=["A", "B", "C"], targets=["T", "U"], budget=50,
                     case_id="ab-dep")
    result = policy_solve("proposed", case)
    assert result["decision"] == "find_valid_route"
    assert result["total_cost"] == 50  # 40 (one provider) + 10 (dependent)
    assert result["dwell_cost"] == 50

def test_budget_39_rejects_as_cost_exceeded_not_false_infeasible():
    # Minimum subset cost is 40 (one provider); budget 39 is the boundary.
    case = make_case(**{**AB_CASE, "budget": 39}, case_id="ab-budget39")
    result = policy_solve("proposed", case)
    assert result["decision"] == "cost_exceeded"
    assert result["total_cost"] == 40  # the chosen minimal subset, not 80


def test_a3_reproduces_the_legacy_all_providers_regression():
    """A3 (all-providers bug) must reproduce the false infeasibility the fix removes."""
    case = make_case(**AB_CASE, case_id="ab-a3")
    result = policy_solve("ablations_a3", case)
    # Legacy behaviour: both providers summed to 80 > 50 -> not find_valid_route.
    assert result["decision"] != "find_valid_route"
    assert result["dwell_cost"] == 80  # the bug: A and B summed
    # ...while the proposed policy accepts the same case:
    assert policy_solve("proposed", case)["decision"] == "find_valid_route"
