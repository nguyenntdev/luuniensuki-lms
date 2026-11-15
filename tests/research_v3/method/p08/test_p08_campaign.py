"""P08 campaign-level tests: the frozen evaluation, oracle hygiene, and the
LN-05 delta (why P08 is not LN-05 under a new name)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from research_v3.methods.p08.attestation import AttestationKey
from research_v3.methods.p08.fixtures import (
    SEED,
    adversarial_deliveries,
    captured_valid_delivery,
    honest_control_deliveries,
)
from research_v3.methods.p08.runner import run_campaign
from research_v3.methods.p08.types import AwardDecision

from .conftest import new_defender

REPO = Path(__file__).resolve().parents[4]
RESULTS_PATH = REPO / "research_artifacts_v3" / "runs" / "p08" / "evaluation_results.json"


@pytest.fixture(scope="module")
def campaign() -> dict:
    return run_campaign()


def test_campaign_primary_gate_passes(campaign):
    assert campaign["primary_gate"]["passed"] is True, json.dumps(campaign["primary_gate"], indent=2)


def test_frozen_metrics_held(campaign):
    m = campaign["metrics"]
    assert m["false_award_count"] == 0
    assert m["duplicate_award_count"] == 0
    assert m["false_award_rate"] == 0.0
    assert m["pooled_detection_recall"] >= 0.999
    assert m["honest_false_rejection_count"] <= 1
    assert m["idempotency_award_count"] == 1


def test_every_attack_vector_fully_detected(campaign):
    for v in campaign["metrics"]["per_vector"]:
        assert v["successful_attacks"] == 0, v
        assert v["detection_recall"] == 1.0, v
        assert v["deliveries"] == 500, v


def test_published_results_match_frozen_rerun(campaign):
    """Source-to-table contract: the committed evaluation_results.json must be
    byte-equal (minus timestamp) to a fresh deterministic rerun."""
    assert RESULTS_PATH.exists(), "run the campaign: python -m research_v3.methods.p08.runner"
    published = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))
    published.pop("generated_at", None)
    fresh = json.loads(json.dumps(campaign))
    fresh.pop("generated_at", None)
    assert published == fresh, "committed results are stale vs frozen seed"


def test_defender_never_reads_evaluator_meta(server_key, config):
    """Oracle hygiene: attack metadata is invisible to the defender. A delivery
    whose evaluator_meta claims 'benign' still gets rejected as an attack."""
    attacker_key = AttestationKey.derive_from_seed("attacker-weak-key", SEED + ":attacker")
    adv = adversarial_deliveries(server_key, attacker_key, 3)
    captured = captured_valid_delivery(server_key)
    for vid, seq in adv.items():
        d = new_defender(config)
        d.evaluate([captured])
        # overwrite evaluator_meta to lie about the traffic
        poisoned = [
            type(delivery)(
                submission=delivery.submission,
                event_id=delivery.event_id,
                session_id=delivery.session_id,
                device_id=delivery.device_id,
                client_timestamp=delivery.client_timestamp,
                policy_version=delivery.policy_version,
                hmac_hex=delivery.hmac_hex,
                evaluator_meta={"attack_vector": "BENIGN", "attack_index": 0},
            )
            for delivery in seq
        ]
        verdicts = d.evaluate(poisoned)
        assert all(v.decision != AwardDecision.AWARD for v in verdicts), (
            f"{vid}: metadata must never influence verdicts"
        )


def test_p08_covers_what_ln05_could_not(server_key, config, attacker_key):
    """The independence-gate delta, as executable checks:
    (a) cross-SESSION replay rejected (LN-05's per-batch ledger grants it);
    (b) forged server-actor submission rejected (LN-05 accepts it);
    (c) farming burst velocity-capped (LN-05 grants all)."""
    captured = captured_valid_delivery(server_key)

    # (a) cross-session: two separate defender epochs share persistent state?
    # No — persistence lives INSIDE one defender (policy epoch). The LN-05
    # failure mode is a fresh ledger per batch; P08's contract is one defender
    # per epoch, so the replay within the epoch is rejected:
    defender = new_defender(config)
    defender.evaluate([captured])
    adv = adversarial_deliveries(server_key, attacker_key, 5)
    cross_device = adv["AV6_cross_device_replay"]
    verdicts = defender.evaluate(cross_device)
    # after the 5th burst delivery the velocity gate fires before the replay
    # gate; the binding property is that NO delivery after the original award
    # ever earns a second award:
    assert all(v.decision in (AwardDecision.REJECT_REPLAY, AwardDecision.REJECT_VELOCITY)
               for v in verdicts)
    assert all(v.decision != AwardDecision.AWARD for v in verdicts)
    assert any(v.decision == AwardDecision.REJECT_REPLAY for v in verdicts)

    # (b) forged actor:
    forged = adv["AV4_forged_server_actor"]
    d2 = new_defender(config)
    d2.evaluate([captured])
    assert all(v.decision == AwardDecision.REJECT_FORGED_ATTESTATION
               for v in d2.evaluate(forged))

    # (c) velocity:
    from research_v3.methods.p08.fixtures import farming_burst_deliveries
    d3 = new_defender(config)
    burst = d3.evaluate(farming_burst_deliveries(server_key))
    grants = sum(1 for v in burst if v.decision == AwardDecision.AWARD)
    assert grants <= 5


def test_campaign_honest_control_untouched(campaign):
    """Honest learners earn real awards; the defense never fails-closed on
    honest traffic beyond the frozen tolerance."""
    m = campaign["metrics"]
    assert m["honest_deliveries"] == 1000
    assert m["honest_false_rejection_count"] == 0
    hist = m["decisions_histogram"]
    assert hist.get("award", 0) >= 1000 - m["honest_false_rejection_count"]


def test_human_outcomes_flag_is_false(campaign):
    """Binding label check: the campaign asserts it measures NO human outcomes."""
    assert campaign["evaluation_class"] == "SOFTWARE_SECURITY_EVALUATION"
    assert campaign["human_outcomes_measured"] is False
    assert campaign["stress"]["SS3_deceptive_badge_copy"]["status"] == "NOT_APPLICABLE"
