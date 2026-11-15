"""Threat-model tests: spoofed provenance, missing competency, stale policy."""
from __future__ import annotations

import pytest

from research_v2.contracts.types import StudyInput
from research_v2.methods.ln05 import predict_batch as predict_proposed
from tests.research_v2.ln05.conftest import load_gold, load_rows, make_inputs, run_config


def test_spoofed_client_xp_never_earns_a_grant():
    """INV-LN-05-01: client-supplied XP is not evidence of competency."""
    golds = load_gold()
    rows = [r for r in load_rows() if golds[r["case_id"]] == "reject_forged_event"]
    assert rows, "dataset must contain forged-event threat cases"
    preds = predict_proposed(make_inputs(rows), run_config())
    assert all(p.decision == "reject_forged_event" for p in preds)
    assert all(not p.decision == "grant_if_eligible" for p in preds)
    assert all("untrusted_actor" in p.reason_codes for p in preds)


def test_missing_competency_is_denied_not_granted():
    """INV-LN-05-03: participation without mastery proof earns nothing."""
    golds = load_gold()
    rows = [r for r in load_rows() if golds[r["case_id"]] == "deny_mastery_badge"]
    assert rows
    preds = predict_proposed(make_inputs(rows), run_config())
    assert all(p.decision == "deny_mastery_badge" for p in preds)
    assert all("missing_competency_evidence" in p.reason_codes for p in preds)


def test_uncorroborated_competency_is_denied():
    """Multi-dimension proof: evidence contradicting the learner profile denies."""
    rows = load_rows()
    base = next(r for r in rows if any(e.get("actor") == "server" for e in r["input"]["reward_events"]))
    features = dict(base["input"])
    # Skill evidence above threshold but contradicting the learner profile.
    req = features["badge"]["requires_competency"]
    skill = dict(features["skill_evidence"])
    skill[req] = 0.99
    profile = dict(features["learner"]["competencies"])
    profile[req] = 0.4
    features["skill_evidence"] = skill
    features["learner"] = {**features["learner"], "competencies": profile}
    preds = predict_proposed(
        [StudyInput("LN-05", "LN-05-CORR-1", "test", "grp-corr", features)], run_config()
    )
    assert preds[0].decision == "deny_mastery_badge"
    assert "uncorroborated_competency" in preds[0].reason_codes


def test_stale_policy_version_requires_revalidation():
    """INV-LN-05-04: policy change invalidates previously awarded badges."""
    golds = load_gold()
    rows = [r for r in load_rows() if golds[r["case_id"]] == "revalidate_badge"]
    assert rows
    preds = predict_proposed(make_inputs(rows), run_config())
    assert all(p.decision == "revalidate_badge" for p in preds)
    assert all("stale_policy_version" in p.reason_codes for p in preds)


def test_stale_gate_precedes_provenance_and_competency_gates():
    """Severity ordering: a stale submission is never mislabelled as forged."""
    rows = load_rows()
    base = next(r for r in rows if any(e.get("actor") == "client" for e in r["input"]["reward_events"]))
    features = dict(base["input"])
    features["event_policy_version"] = 1
    preds = predict_proposed(
        [StudyInput("LN-05", "LN-05-ORDER-1", "test", "grp-order", features)], run_config()
    )
    assert preds[0].decision == "revalidate_badge"


def test_malformed_input_raises_typed_failure_not_silent_default():
    from research_v2.methods.ln05.proposed import PolicyInputError

    rows = load_rows()
    features = dict(rows[0]["input"])
    features.pop("badge")
    with pytest.raises(PolicyInputError):
        predict_proposed(
            [StudyInput("LN-05", "LN-05-BAD-1", "test", "grp-bad", features)], run_config()
        )


def test_all_eligible_population_is_granted():
    """Utility side of the frontier: legitimate learners are not all denied."""
    golds = load_gold()
    rows = [r for r in load_rows() if golds[r["case_id"]] == "grant_if_eligible"]
    preds = predict_proposed(make_inputs(rows), run_config())
    assert all(p.decision == "grant_if_eligible" for p in preds), "over-blocking policy"
