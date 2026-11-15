"""Ablation divergence: each ablation must genuinely change the decision path
versus the proposed method on a case exercising exactly the removed mechanism,
and must NOT differ on nominal cases."""
from __future__ import annotations

from research_v2.methods.ln09 import ablations, ablations_a2, ablations_a3
from research_v2.methods.ln09.proposed import predict_batch as proposed_batch

from ln09_helpers import make_features, make_input

MISSING_EV = make_features(learning_evidence=[], required_signal_types=["source_task", "quiz"])
STALE_EV = make_features(observation_age_days=45)
UNVERIFIED_EV = make_features(
    learning_evidence=[
        {"outcome": "evidence_use", "score": 0.2, "type": "source_task", "verified": False},
        {"outcome": "spatial", "score": 0.35, "type": "quiz", "verified": True},
    ],
    # Mirror the frozen dataset's unverified-source family: all required
    # signal families have a verified representative, so the ONLY fault is
    # the unverified source task (no missing-family confound).
    required_signal_types=["quiz", "quiz"],
)
SMALL_COHORT = make_features(cohort_size=3)


def test_a1_loses_explicit_abstention_certificate_on_missing_evidence():
    """Without the descriptive/abstention fallback mechanism, a1 degrades the
    missing-logs certificate: proposed abstains explicitly with
    missing_logs reasons; a1 emits a bare descriptive summary."""
    inp = make_input("a1-missing", MISSING_EV)
    proposed = proposed_batch([inp], {})[0]
    ablated = ablations.predict_batch([inp], {})[0]
    assert proposed.decision == "abstain_missing_evidence"
    assert "missing_logs" in proposed.reason_codes
    assert ablated.decision == "descriptive_summary_only"
    assert "descriptive_only_no_action" in ablated.reason_codes
    assert ablated.decision != proposed.decision


def test_a2_accepts_stale_case_proposed_requests_refresh():
    inp = make_input("a2-stale", STALE_EV)
    proposed = proposed_batch([inp], {})[0]
    ablated = ablations_a2.predict_batch([inp], {})[0]
    assert proposed.decision == "request_refresh"
    assert "stale_mastery" in proposed.reason_codes
    assert ablated.decision == "propose_explained_action"


def test_a2_accepts_unverified_source_case_proposed_abstains():
    inp = make_input("a2-unverified", UNVERIFIED_EV)
    proposed = proposed_batch([inp], {})[0]
    ablated = ablations_a2.predict_batch([inp], {})[0]
    assert proposed.decision == "abstain_unverified_source"
    assert "unverified_task" in proposed.reason_codes
    assert ablated.decision == "propose_explained_action"


def test_a3_publishes_small_cohort_proposed_suppresses():
    inp = make_input("a3-small", SMALL_COHORT)
    proposed = proposed_batch([inp], {})[0]
    ablated = ablations_a3.predict_batch([inp], {})[0]
    assert proposed.decision == "descriptive_summary_only"
    assert "k_anonymity_violation" in proposed.reason_codes
    assert ablated.decision == "propose_explained_action"


def test_ablations_never_differ_on_nominal_case():
    """Ablations must not manufacture differences on nominal inputs."""
    nominal = make_input("nom", make_features())
    for fn in (
        ablations.predict_batch,
        ablations_a2.predict_batch,
        ablations_a3.predict_batch,
    ):
        assert fn([nominal], {})[0].decision == "propose_explained_action"


def test_always_accept_and_always_reject_controls_never_both_perfect():
    """Golden-case QA: B0 (always accept) fails every abstention family; the
    proposed method separates positive from negative cases on both sides."""
    from research_v2.methods.ln09.baselines import predict_batch_b0

    good = proposed_batch([make_input("good")], {})[0]
    bad = proposed_batch([make_input("bad", MISSING_EV)], {})[0]
    assert good.decision == "propose_explained_action"
    assert bad.decision != "propose_explained_action"
    # B0 proposes on both: it cannot separate.
    b0_good = predict_batch_b0([make_input("b0-good")], {})[0]
    b0_bad = predict_batch_b0([make_input("b0-bad", MISSING_EV)], {})[0]
    assert b0_good.decision == b0_bad.decision == "propose_explained_action"
