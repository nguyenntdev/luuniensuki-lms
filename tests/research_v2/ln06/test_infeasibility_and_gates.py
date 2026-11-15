"""Infeasibility certification: unreachable outcomes, cycles, closed sources."""
from __future__ import annotations

from tests.research_v2.ln06.conftest import make_case, policy_solve


def test_genuinely_infeasible_when_prerequisite_provider_unavailable():
    stops = [
        {"id": "s1", "cost": 10, "provides": ["o1"], "requires": [], "type": "chain"},
        {"id": "s3", "cost": 10, "provides": ["o3"], "requires": ["o2"], "type": "chain"},
    ]
    # o2 has no provider at all among available stops -> certified infeasible.
    case = make_case(stops=stops, available=["s1", "s3"], targets=["o1", "o2", "o3"],
                     budget=75, case_id="infeasible")
    result = policy_solve("proposed", case)
    assert result["decision"] == "no_feasible_route"
    assert any("unreachable_outcome" in rc for rc in result["reason_codes"])


def test_unreachable_target_outcome():
    stops = [{"id": "s1", "cost": 10, "provides": ["o1"], "requires": [], "type": "x"}]
    case = make_case(stops=stops, available=["s1"], targets=["o1", "never_provided"],
                     budget=75, case_id="unreachable")
    result = policy_solve("proposed", case)
    assert result["decision"] == "no_feasible_route"


def test_prerequisite_cycle_certified():
    stops = [
        {"id": "s1", "cost": 10, "provides": ["o1"], "requires": ["o2"], "type": "cyc"},
        {"id": "s2", "cost": 10, "provides": ["o2"], "requires": ["o1"], "type": "cyc"},
    ]
    case = make_case(stops=stops, available=["s1", "s2"], targets=["o1", "o2"],
                     budget=75, case_id="cycle")
    result = policy_solve("proposed", case)
    assert result["decision"] == "reject_cycle"


def test_self_dependent_outcome_cycle():
    # Only provider of o1 requires o1: an unresolvable deadlock, not a false cycle.
    stops = [{"id": "solo", "cost": 10, "provides": ["o1"], "requires": ["o1"], "type": "cyc"}]
    case = make_case(stops=stops, available=["solo"], targets=["o1"], budget=75, case_id="selfcyc")
    result = policy_solve("proposed", case)
    assert result["decision"] == "reject_cycle"


def test_closed_checkpoint_rejected_before_routing():
    case = make_case(**{
        "stops": [
            {"id": "A", "cost": 40, "provides": ["T"], "requires": [], "type": "x"},
        ],
        "available": ["A"],
        "targets": ["T"],
        "budget": 50,
        "verified": False,
        "case_id": "closed",
    })
    result = policy_solve("proposed", case)
    assert result["decision"] == "reject_checkpoint_source"
    assert result["total_cost"] == 0


def test_asymmetric_travel_with_closed_checkpoint():
    """Case 4 counterexample: asymmetric directed travel AND unverified source."""
    edges = [
        {"from": "m1", "to": "m2", "minutes": 6},
        {"from": "m2", "to": "m1", "minutes": 14},
    ]
    case = make_case(
        stops=[
            {"id": "m1", "cost": 10, "provides": ["o1"], "requires": [], "type": "t"},
            {"id": "m2", "cost": 10, "provides": ["o2"], "requires": [], "type": "t"},
        ],
        available=["m1", "m2"],
        targets=["o1", "o2"],
        budget=60,
        verified=False,
        travel_edges=edges,
        case_id="asym-closed",
    )
    assert policy_solve("proposed", case)["decision"] == "reject_checkpoint_source"
    # Source gate precedes travel reasoning for every method sharing the gate.
    assert policy_solve("baselines_c1", case)["decision"] == "reject_checkpoint_source"
