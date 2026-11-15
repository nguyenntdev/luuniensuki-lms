"""Nominal happy-path behaviour: structured result, coverage, ordering."""
from __future__ import annotations

from tests.research_v2.ln06.conftest import make_case, make_input, policy_solve

CHAIN_STOPS = [
    {"id": "ngo-mon", "cost": 15, "provides": ["spatial_layout"], "requires": [], "type": "gate"},
    {"id": "dien-thai-hoa", "cost": 20, "provides": ["ritual_context"],
     "requires": ["spatial_layout"], "type": "palace"},
    {"id": "the-mieu", "cost": 15, "provides": ["commemoration"],
     "requires": ["ritual_context"], "type": "shrine"},
    {"id": "cuu-dinh", "cost": 20, "provides": ["heritage_interpretation"],
     "requires": ["commemoration"], "type": "urns"},
]


def test_nominal_chain_route_is_structured_and_ordered():
    case = make_case(stops=CHAIN_STOPS, available=["ngo-mon", "dien-thai-hoa", "the-mieu", "cuu-dinh"],
                     targets=["spatial_layout", "ritual_context", "commemoration", "heritage_interpretation"],
                     budget=75, case_id="nominal")
    result = policy_solve("proposed", case)
    assert result["decision"] == "find_valid_route"
    assert result["total_cost"] == 70
    # Topological order with lexicographic readiness.
    assert result["route"] == ("ngo-mon", "dien-thai-hoa", "the-mieu", "cuu-dinh")


def test_prediction_via_contract_abi():
    from research_v2.contracts.label_space import validate_decision
    from research_v2.methods.ln06.proposed import predict_batch

    case = make_case(stops=CHAIN_STOPS, available=[s["id"] for s in CHAIN_STOPS],
                     targets=["spatial_layout", "ritual_context", "commemoration", "heritage_interpretation"],
                     budget=75, case_id="abi")
    preds = predict_batch([make_input(case)], {"seed": 11})
    assert len(preds) == 1
    pred = preds[0]
    assert isinstance(pred, StudyPrediction := __import__(
        "research_v2.contracts.types", fromlist=["StudyPrediction"]).StudyPrediction)
    validate_decision("LN-06", pred.decision)
    assert pred.decision == "find_valid_route"
    assert pred.case_id == "abi"
    assert pred.score == 70.0
    assert pred.evidence_ids == ("ngo-mon", "dien-thai-hoa", "the-mieu", "cuu-dinh")


def test_minimal_subset_skips_unavailable_stops():
    case = make_case(stops=CHAIN_STOPS, available=["ngo-mon", "dien-thai-hoa"],
                     targets=["spatial_layout", "ritual_context"], budget=75, case_id="subset")
    result = policy_solve("proposed", case)
    assert result["decision"] == "find_valid_route"
    assert set(result["route"]) == {"ngo-mon", "dien-thai-hoa"}


def test_travel_edges_are_included_in_budget_check():
    # Complete asymmetric directed travel graph between the three stops.
    edges = [
        {"from": "s1", "to": "s2", "minutes": 7},
        {"from": "s1", "to": "s3", "minutes": 20},
        {"from": "s2", "to": "s1", "minutes": 9},
        {"from": "s2", "to": "s3", "minutes": 5},
        {"from": "s3", "to": "s1", "minutes": 11},
        {"from": "s3", "to": "s2", "minutes": 6},
    ]
    stops = [
        {"id": "s1", "cost": 10, "provides": ["o1"], "requires": [], "type": "t"},
        {"id": "s2", "cost": 10, "provides": ["o2"], "requires": [], "type": "t"},
        {"id": "s3", "cost": 10, "provides": ["o3"], "requires": ["o2"], "type": "t"},
    ]
    case = make_case(stops=stops, available=["s1", "s2", "s3"], targets=["o1", "o2", "o3"],
                     budget=42, travel_edges=edges, case_id="travel")
    result = policy_solve("proposed", case)
    assert result["decision"] == "find_valid_route"
    assert result["dwell_cost"] == 30
    # Best feasible order: s1 -> s2 -> s3 = 7 + 5 = 12 travel (s3 requires o2).
    assert result["route"] == ("s1", "s2", "s3")
    assert result["travel_cost"] == 12
    assert result["total_cost"] == 42
    # Budget check includes travel: cutting to 41 flips the decision.
    tight = make_case(stops=stops, available=["s1", "s2", "s3"], targets=["o1", "o2", "o3"],
                      budget=41, travel_edges=edges, case_id="travel-tight")
    assert policy_solve("proposed", tight)["decision"] == "cost_exceeded"
