"""Ownership/authorization tests: unauthorized actor -> deny, never apply."""
from __future__ import annotations

import pytest

from tests.research_v2.ln10.ln10_helpers import (
    make_features,
    make_input,
    unauthorized_actor_features,
)
from research_v2.methods.ln10.ablations import a3_solve
from research_v2.methods.ln10.baselines import c1_decide
from research_v2.methods.ln10.dataset import DatasetError, parse_case
from research_v2.methods.ln10.proposed import predict_batch, solve_case


def test_unauthorized_student_without_ownership_denied():
    inp = make_input(unauthorized_actor_features(), case_id="unauthorized")
    pred = predict_batch([inp], {"seed": 11})[0]
    assert pred.decision == "deny_transition"
    assert "unauthorized_actor" in pred.reason_codes
    assert pred.score == 0.0


def test_missing_owns_project_flag_is_typed_schema_failure():
    """A missing ownership boolean is an invalid row: typed failure, no guess."""
    features = make_features()
    features["actor"] = {"role": "student"}  # no owns_project flag
    with pytest.raises(DatasetError, match="owns_project"):
        parse_case("no-owns-flag", features)


def test_staff_role_is_authorized_without_ownership():
    features = make_features(actor={"owns_project": False, "role": "teacher"})
    case = parse_case("staff-mentor", features)
    result = solve_case(case)
    assert result["decision"] == "allow_authorized_transition"


def test_a3_ablation_loses_ownership_gate():
    """Removing the ownership check lets the unauthorized actor through."""
    case = parse_case("unauthorized-a3", unauthorized_actor_features())
    result = a3_solve(case)
    assert result["decision"] == "allow_authorized_transition"
    assert "ownership_check_disabled" in result["reason_codes"]


def test_c1_baseline_keeps_classical_acl():
    case = parse_case("unauthorized-c1", unauthorized_actor_features())
    result = c1_decide(case)
    assert result["decision"] == "deny_transition"


def test_malformed_actor_raises_typed_failure():
    features = make_features(actor="not-a-mapping")
    with pytest.raises(DatasetError):
        parse_case("bad-actor", features)


def test_batch_invalid_row_rejects_whole_batch_with_location():
    from research_v2.contracts.types import StudyInput

    good = make_input(make_features(), case_id="good-1")
    bad = StudyInput(
        "LN-10", "bad-2", "test", "g", make_features(actor={"role": 123, "owns_project": True})
    )
    with pytest.raises(DatasetError, match="bad-2"):
        predict_batch([good, bad], {"seed": 11})
