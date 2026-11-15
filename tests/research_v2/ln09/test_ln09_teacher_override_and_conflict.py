"""Conflict visibility (INV-LN-09-05) and teacher override supremacy
(INV-LN-09-03): contradictory signals are surfaced explicitly, never silently
resolved; an explicit teacher decision is honored above any recommendation.
"""
from __future__ import annotations

from research_v2.methods.ln09.proposed import predict_batch as proposed_batch

from ln09_helpers import make_features, make_input


def test_conflicting_signals_yield_explicit_conflict_abstention():
    feats = make_features(signals_conflict=True)
    pred = proposed_batch([make_input("conflict", feats)], {})[0]
    assert pred.decision == "abstain_conflict"
    assert "conflicting_signals" in pred.reason_codes
    # Conflict must be visible, not hidden behind a nominal action.
    assert pred.decision != "propose_explained_action"


def test_teacher_rejection_downgrades_to_descriptive_summary():
    feats = make_features(
        teacher_override={
            "status": "rejected",
            "teacher_id": "T-002",
            "override_reason": "Học sinh đang được hỗ trợ riêng",
        }
    )
    pred = proposed_batch([make_input("reject", feats)], {})[0]
    assert pred.decision == "descriptive_summary_only"
    assert "teacher_rejected" in pred.reason_codes


def test_teacher_modification_uses_teacher_owned_action_not_algorithms():
    feats = make_features(
        teacher_override={
            "status": "modified",
            "teacher_id": "T-003",
            "override_reason": "Đổi sang hoạt động thực địa",
            "modified_action": {"action_type": "field_visit_activity", "curriculum_anchor_id": "GDDP12-TEACHER-CUSTOM"},
        }
    )
    pred = proposed_batch([make_input("modify", feats)], {})[0]
    assert pred.decision == "propose_explained_action"
    assert "teacher_modified" in pred.reason_codes
    assert "nominal" in pred.reason_codes


def test_teacher_acceptance_confirms_but_stays_advisory():
    feats = make_features(
        teacher_override={"status": "accepted", "teacher_id": "T-004", "override_reason": "Đồng ý"}
    )
    pred = proposed_batch([make_input("accept", feats)], {})[0]
    assert pred.decision == "propose_explained_action"
    assert "teacher_accepted" in pred.reason_codes
    assert "nominal" in pred.reason_codes


def test_override_absence_never_blocks_default_path():
    feats = make_features()
    assert "teacher_override" not in feats
    pred = proposed_batch([make_input("no-override", feats)], {})[0]
    assert pred.decision == "propose_explained_action"


def test_conflict_plus_teacher_rejection_surfaces_both_reasons():
    """Teacher rejection on a conflicting case yields the descriptive hand-off
    with the teacher reason; the algorithmic conflict never silently vanishes
    into an action."""
    feats = make_features(
        signals_conflict=True,
        teacher_override={"status": "rejected", "teacher_id": "T-005", "override_reason": "sẽ trực tiếp trao đổi"},
    )
    pred = proposed_batch([make_input("conflict-reject", feats)], {})[0]
    assert pred.decision == "descriptive_summary_only"
    assert "teacher_rejected" in pred.reason_codes
