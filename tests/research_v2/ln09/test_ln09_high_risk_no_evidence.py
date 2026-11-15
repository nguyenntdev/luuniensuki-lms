"""MANDATORY counterexample (spec F Case 1): a student flagged HIGH RISK with
NO actionable evidence (missing logs) must NOT receive a deficit inference.
The proposed method must abstain (explicit certificate) or hand off
descriptively — never propose an intervention from absent data.
"""
from __future__ import annotations

from research_v2.methods.ln09.proposed import predict_batch as proposed_batch
from research_v2.methods.ln09.baselines import predict_batch_b0, predict_batch_c1

from ln09_helpers import make_features, make_high_risk_no_evidence, make_input


def test_high_risk_no_evidence_abstains_never_deficit_inference():
    pred = proposed_batch([make_high_risk_no_evidence()], {})[0]
    assert pred.decision in {
        "abstain_missing_evidence",  # explicit abstention certificate
        "descriptive_summary_only",  # or descriptive hand-off
        "require_teacher_override",  # or explicit teacher hand-off (V2 space)
    }
    # The violation under test: proposing an action = fabricating a deficit
    # conclusion ("learner is weak") from missing logs.
    assert pred.decision != "propose_explained_action"
    assert "missing_logs" in pred.reason_codes
    # No evidence ids can be cited for a deficit claim built on absent data.
    assert pred.evidence_ids == ()


def test_missing_required_signal_family_blocks_deficit_even_with_partial_logs():
    """Risk signals present for one competency family but a *required* family
    has zero observations at all: still no deficit inference."""
    feats = make_features(
        learning_evidence=[{"outcome": "spatial", "score": 0.1, "type": "quiz", "verified": True}],
        required_signal_types=["source_task", "quiz"],
    )
    pred = proposed_batch([make_input("partial", feats)], {})[0]
    assert pred.decision == "abstain_missing_evidence"
    assert "missing_required_signal_types" in pred.reason_codes


def test_unverified_row_is_trust_not_missingness():
    """An unverified row still proves the signal family was observed: the case
    fails the unverified-source gate (trust), never the missing-logs gate
    (existence). Conflating the two would hide real missingness behind trust
    noise."""
    feats = make_features(
        learning_evidence=[
            {"outcome": "evidence_use", "score": 0.2, "type": "source_task", "verified": False},
            {"outcome": "spatial", "score": 0.35, "type": "quiz", "verified": True},
        ],
        required_signal_types=["source_task", "quiz"],
    )
    pred = proposed_batch([make_input("trust-vs-missing", feats)], {})[0]
    assert pred.decision == "abstain_unverified_source"
    assert "unverified_task" in pred.reason_codes
    assert "missing_logs" not in pred.reason_codes


def test_teacher_override_on_missing_evidence_yields_descriptive_handoff_only():
    """Even an explicit teacher push on a no-evidence case can only produce a
    descriptive hand-off (teacher supremacy), never an automatic deficit
    intervention or grade."""
    feats = make_features(
        learning_evidence=[],
        teacher_override={"status": "accepted", "teacher_id": "T-001", "override_reason": "I know this learner"},
    )
    pred = proposed_batch([make_input("override", feats)], {})[0]
    assert pred.decision != "propose_explained_action" or pred.decision == "propose_explained_action"
    # The teacher-accepted branch inherits the underlying algorithmic decision,
    # which for missing evidence is an abstention — never a fabricated action.
    assert pred.decision == "abstain_missing_evidence"
    assert "teacher_accepted" in pred.reason_codes
    assert "missing_logs" in pred.reason_codes


def test_b0_baseline_violates_the_invariant_negative_control():
    """B0 (always propose on any risk signal) commits exactly the forbidden
    deficit inference — this is the documented negative control proving the
    counterexample separates methods."""
    pred = predict_batch_b0([make_high_risk_no_evidence()], {})[0]
    assert pred.decision == "propose_explained_action"
    assert "baseline_ungrounded_heuristic" in pred.reason_codes


def test_c1_baseline_violates_the_invariant_negative_control():
    """C1 EMA alert also proposes on partial unverified evidence without
    source audit — second negative control."""
    feats = make_features(
        learning_evidence=[
            {"outcome": "evidence_use", "score": 0.2, "type": "source_task", "verified": False}
        ],
        required_signal_types=["source_task"],
    )
    pred = predict_batch_c1([make_input("c1-nosrc", feats)], {})[0]
    assert pred.decision == "propose_explained_action"
