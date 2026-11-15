"""Due-date scheduling: postpone when not due; determinism and metamorphic checks."""
from __future__ import annotations

import pytest

from research_v2.contracts.types import StudyInput
from research_v2.methods.ln03 import proposed
from research_v2.methods.ln03.ablations_a3 import predict_batch as a3

from ln03_helpers import make_features


def _inp(case_id: str, features: dict) -> StudyInput:
    return StudyInput("LN-03", case_id, "test", "grp-due", features)


def test_not_due_postpones():
    features = make_features(review_card={"due_utc": "2026-11-20T12:00:00Z"})
    pred = proposed.predict_batch([_inp("LN-03-D1", features)])[0]
    assert pred.decision == "postpone"
    assert "not_due" in pred.reason_codes
    assert "RULE-LN-03-03" in pred.reason_codes


def test_due_boundary_schedules():
    # due == now -> due (legacy semantic: due <= now)
    features = make_features(review_card={"due_utc": "2026-11-08T12:00:00Z"})
    pred = proposed.predict_batch([_inp("LN-03-D2", features)])[0]
    assert pred.decision == "schedule_eligible"


def test_retrieval_task_skips_generative_gates():
    features = make_features(
        task_type="fact_retrieval", fact_prerequisite_mastered=False, review_card={"source_verified": False}
    )
    pred = proposed.predict_batch([_inp("LN-03-D3", features)])[0]
    assert pred.decision == "schedule_eligible"  # fact tasks have no generative gates


def test_a3_ablation_schedules_not_due_case():
    features = make_features(review_card={"due_utc": "2026-11-20T12:00:00Z"})
    pred_proposed = proposed.predict_batch([_inp("LN-03-D4", features)])[0]
    pred_a3 = a3([_inp("LN-03-D4", features)])[0]
    assert pred_proposed.decision == "postpone"
    assert pred_a3.decision == "schedule_eligible"  # due scheduling disabled


def test_rule_order_due_before_fact_gate():
    # Not due AND missing fact base: due check wins (legacy rule order 04->03->02->05->01).
    features = make_features(fact_prerequisite_mastered=False, review_card={"due_utc": "2026-11-20T12:00:00Z"})
    pred = proposed.predict_batch([_inp("LN-03-D5", features)])[0]
    assert pred.decision == "postpone"


def test_rule_order_fact_before_source_gate():
    # Missing fact base AND unverified source: fact remediation wins.
    features = make_features(fact_prerequisite_mastered=False, review_card={"source_verified": False})
    pred = proposed.predict_batch([_inp("LN-03-D6", features)])[0]
    assert pred.decision == "assign_fact_retrieval"


def test_invalid_config_flag_fails_closed():
    with pytest.raises(Exception, match="boolean"):
        proposed.predict_batch([_inp("LN-03-D7", make_features())], {"postpone_if_not_due": "yes"})


def test_seed_irrelevant_for_deterministic_policy():
    features = make_features()
    p1 = proposed.predict_batch([_inp("LN-03-D8", features)], {"seed": 11})[0]
    p2 = proposed.predict_batch([_inp("LN-03-D8", features)], {"seed": 37})[0]
    assert p1 == p2
