"""k-anonymity suppression (INV-LN-09-04): cohorts below the threshold (n < 5)
are suppressed to a descriptive-only summary; no learner-level recommendation
is published. Teacher override remains honored above suppression (supremacy).
"""
from __future__ import annotations

import pytest

from research_v2.methods.ln09 import ablations_a3
from research_v2.methods.ln09.proposed import predict_batch as proposed_batch

from ln09_helpers import make_features, make_input


def test_small_cohort_suppressed_to_descriptive_only():
    feats = make_features(cohort_size=4)
    pred = proposed_batch([make_input("small", feats)], {})[0]
    assert pred.decision == "descriptive_summary_only"
    assert "k_anonymity_violation" in pred.reason_codes
    assert pred.evidence_ids == ()


def test_cohort_at_threshold_is_not_suppressed():
    feats = make_features(cohort_size=5)
    pred = proposed_batch([make_input("edge", feats)], {})[0]
    assert pred.decision == "propose_explained_action"


def test_missing_cohort_size_defaults_to_individual_anonymized_profile():
    """Single-learner synthetic scenario with an anonymized profile satisfies
    privacy (mirrors legacy check_k_anonymity None-handling)."""
    feats = make_features()
    del feats["cohort_size"]
    pred = proposed_batch([make_input("nocohort", feats)], {})[0]
    assert pred.decision == "propose_explained_action"


def test_a3_ablation_publishes_recommendation_the_proposed_method_suppresses():
    """Removing the k-anonymity mechanism must change the code path: the
    small-cohort case that proposed suppresses becomes publishable in a3."""
    feats = make_features(cohort_size=3)
    inp = make_input("small-a3", feats)
    proposed = proposed_batch([inp], {})[0]
    ablated = ablations_a3.predict_batch([inp], {})[0]
    assert proposed.decision == "descriptive_summary_only"
    assert ablated.decision == "propose_explained_action"


def test_teacher_override_supremacy_over_k_anonymity_suppression():
    """An explicit teacher decision outranks the privacy suppression: the
    output stays a teacher-owned descriptive hand-off (never an automatic
    learner-level intervention published against the privacy gate)."""
    feats = make_features(
        cohort_size=3,
        teacher_override={"status": "rejected", "teacher_id": "T-007", "override_reason": "not appropriate"},
    )
    pred = proposed_batch([make_input("override-small", feats)], {})[0]
    assert pred.decision == "descriptive_summary_only"
    assert "teacher_rejected" in pred.reason_codes


@pytest.mark.parametrize("bad", [-1, "many", True, 2.5])
def test_invalid_cohort_size_raises_typed_error(bad):
    feats = make_features(cohort_size=bad)
    with pytest.raises(Exception, match="cohort_size"):
        proposed_batch([make_input("bad-cohort", feats)], {})
