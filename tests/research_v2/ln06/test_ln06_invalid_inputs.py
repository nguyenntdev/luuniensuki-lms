"""Malformed inputs raise typed failures with batch location - no silent defaults."""
from __future__ import annotations

import pytest

from research_v2.contracts.types import StudyInput
from research_v2.methods.ln06.dataset import DatasetError, TrailCase
from research_v2.methods.ln06.proposed import predict_batch


def _input(case_id: str, features: dict) -> StudyInput:
    return StudyInput("LN-06", case_id, "test", "g", features)


def test_missing_stops_rejects():
    with pytest.raises(DatasetError, match="stops"):
        TrailCase.from_features(
            {"available_stops": ["a"], "target_outcomes": ["o1"],
             "time_budget_minutes": 10, "checkpoint_claim_verified": True},
            case_id="bad",
        )


def test_unknown_available_stop_rejects():
    with pytest.raises(DatasetError, match="unknown ids"):
        TrailCase.from_features(
            {"stops": [{"id": "a", "cost": 1, "provides": ["o1"], "requires": []}],
             "available_stops": ["a", "ghost"],
             "target_outcomes": ["o1"], "time_budget_minutes": 10,
             "checkpoint_claim_verified": True},
            case_id="bad",
        )


def test_negative_cost_rejects():
    with pytest.raises(DatasetError, match="cost"):
        TrailCase.from_features(
            {"stops": [{"id": "a", "cost": -5, "provides": ["o1"], "requires": []}],
             "available_stops": ["a"], "target_outcomes": ["o1"],
             "time_budget_minutes": 10, "checkpoint_claim_verified": True},
            case_id="bad",
        )


def test_non_boolean_verified_flag_rejects():
    with pytest.raises(DatasetError, match="checkpoint_claim_verified"):
        TrailCase.from_features(
            {"stops": [{"id": "a", "cost": 1, "provides": ["o1"], "requires": []}],
             "available_stops": ["a"], "target_outcomes": ["o1"],
             "time_budget_minutes": 10, "checkpoint_claim_verified": "yes"},
            case_id="bad",
        )


def test_invalid_travel_edge_endpoint_rejects():
    with pytest.raises(DatasetError, match="unknown stop ids"):
        TrailCase.from_features(
            {"stops": [{"id": "a", "cost": 1, "provides": ["o1"], "requires": []}],
             "available_stops": ["a"], "target_outcomes": ["o1"],
             "time_budget_minutes": 10, "checkpoint_claim_verified": True,
             "travel_edges": [{"from": "a", "to": "nowhere", "minutes": 3}]},
            case_id="bad",
        )


def test_duplicate_stop_ids_reject():
    with pytest.raises(DatasetError, match="duplicate"):
        TrailCase.from_features(
            {"stops": [
                {"id": "a", "cost": 1, "provides": ["o1"], "requires": []},
                {"id": "a", "cost": 2, "provides": ["o2"], "requires": []},
            ],
             "available_stops": ["a"], "target_outcomes": ["o1"],
             "time_budget_minutes": 10, "checkpoint_claim_verified": True},
            case_id="bad",
        )


def test_batch_rejection_reports_batch_location():
    good = {"stops": [{"id": "a", "cost": 1, "provides": ["o1"], "requires": []}],
            "available_stops": ["a"], "target_outcomes": ["o1"],
            "time_budget_minutes": 10, "checkpoint_claim_verified": True}
    bad = {"stops": [{"id": "b", "cost": "free", "provides": ["o2"], "requires": []}],
           "available_stops": ["b"], "target_outcomes": ["o2"],
           "time_budget_minutes": 10, "checkpoint_claim_verified": True}
    inputs = [_input("ok-1", good), _input("bad-1", bad)]
    with pytest.raises(DatasetError) as excinfo:
        predict_batch(inputs, {})
    assert "bad-1" in str(excinfo.value)


def test_unknown_native_label_rejected_by_label_space():
    from research_v2.contracts.label_space import LabelSpaceError, validate_decision

    with pytest.raises(LabelSpaceError):
        validate_decision("LN-06", "reject_everything")
    from research_v2.methods.ln06.labels import LabelError, map_decision

    with pytest.raises(LabelError):
        map_decision("sort_of_feasible")
