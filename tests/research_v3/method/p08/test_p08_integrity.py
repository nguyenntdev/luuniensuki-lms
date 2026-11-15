"""P08 core integrity tests: idempotency, forgery, staleness, replay.

Scope: SOFTWARE SECURITY only. No test asserts or implies any human outcome
(motivation, engagement, trust, learning). Evaluation class is fixed by
research_v3/experiments/p08/pre_registration.yaml.
"""
from __future__ import annotations

from research_v3.methods.p08.attestation import AttestationKey
from research_v3.methods.p08.fixtures import (
    DUPLICATE_STRESS_COUNT,
    STALE_POLICY_VERSION,
    duplicate_stress_delivery,
)
from research_v3.methods.p08.types import AwardDecision, ReasonCode

from .conftest import make_delivery, make_submission, new_defender


# ---------------------------------------------------------------- idempotency

def test_100x_duplicate_submission_yields_exactly_one_award(server_key, config):
    """Mandatory idempotency proof: the same valid submission delivered 100x
    (identical content, varying transport skins) -> exactly 1 award. Later
    duplicates are rejected (as replay, or as velocity when the duplicate
    burst exceeds the window before the replay gate is reached)."""
    deliveries = duplicate_stress_delivery(server_key)
    assert len(deliveries) == DUPLICATE_STRESS_COUNT == 100
    defender = new_defender(config)
    verdicts = defender.evaluate(deliveries)
    awards = [v for v in verdicts if v.decision == AwardDecision.AWARD]
    assert len(awards) == 1
    rejections = verdicts[1:]
    assert all(v.decision in (AwardDecision.REJECT_REPLAY, AwardDecision.REJECT_VELOCITY)
               for v in rejections)
    assert all(v.decision != AwardDecision.AWARD for v in rejections)
    assert all(v.xp_awarded == 0 for v in rejections)
    assert defender.xp_total(deliveries[0].submission.learner.learner_id) == awards[0].xp_awarded


def test_award_identity_ignores_transport_fields(server_key, config):
    """Same submission under a different session/device/event_id/timestamp is
    still ONE submission identity -> second delivery is a replay."""
    sub = make_submission()
    d1 = make_delivery(sub, server_key, event_id="e1", session_id="s1",
                       device_id="d1", client_timestamp="2026-11-15T09:00:00Z")
    d2 = make_delivery(sub, server_key, event_id="e2", session_id="s2",
                       device_id="d2", client_timestamp="2099-01-01T00:00:00Z")
    verdicts = new_defender(config).evaluate([d1, d2])
    assert verdicts[0].decision == AwardDecision.AWARD
    assert verdicts[1].decision == AwardDecision.REJECT_REPLAY
    assert ReasonCode.CROSS_SESSION_REPLAY in verdicts[1].reason_codes


# ------------------------------------------------------------------- forgery

def test_forged_server_actor_without_server_key_is_rejected(server_key, config, attacker_key):
    """AV4: attacker controls the channel, stamps actor='server', forges
    maximal evidence, signs with its OWN key -> HMAC gate must reject."""
    sub = make_submission(level=1.0)
    forged = make_delivery(sub, server_key, hmac_hex=attacker_key.sign(sub, config.policy_version))
    verdicts = new_defender(config).evaluate([forged])
    assert verdicts[0].decision == AwardDecision.REJECT_FORGED_ATTESTATION
    assert ReasonCode.BAD_HMAC in verdicts[0].reason_codes
    assert verdicts[0].xp_awarded == 0


def test_forged_hmac_garbage_is_rejected(server_key, config):
    sub = make_submission()
    forged = make_delivery(sub, server_key, hmac_hex="00" * 32)
    verdicts = new_defender(config).evaluate([forged])
    assert verdicts[0].decision == AwardDecision.REJECT_FORGED_ATTESTATION


def test_any_single_byte_evidence_mutation_breaks_attestation(server_key, config):
    """Mutation test: the HMAC binds the full semantic payload, so ANY change
    to evidence/level/task/competency under a replayed HMAC is rejected."""
    sub = make_submission(level=0.9)
    hmac_hex = server_key.sign(sub, config.policy_version)
    for mutated in (
        make_submission(level=1.0),                      # level bump
        make_submission(task_id="other-task"),           # task swap
        make_submission(comp="S2"),                      # competency swap
        make_submission(verified=False),                 # unverified claim
    ):
        delivery = make_delivery(mutated, server_key, hmac_hex=hmac_hex)
        verdicts = new_defender(config).evaluate([delivery])
        assert verdicts[0].decision == AwardDecision.REJECT_FORGED_ATTESTATION, (
            "replayed HMAC must not validate a mutated payload"
        )


def test_client_actor_in_attested_payload_is_rejected(server_key, config):
    sub = make_submission()
    delivery = make_delivery(sub, server_key)
    assert delivery.submission.events[0].actor == "server"  # sanity
    # attacker cannot flip actor without breaking the HMAC:
    from research_v3.methods.p08.types import RewardEvent
    tampered = make_submission()
    object.__setattr__(tampered, "events",
                       (RewardEvent(kind=tampered.events[0].kind,
                                    task_id=tampered.events[0].task_id,
                                    competency=tampered.events[0].competency,
                                    level=tampered.events[0].level,
                                    actor="client"),))
    bad = make_delivery(tampered, server_key, hmac_hex=delivery.hmac_hex)
    verdicts = new_defender(config).evaluate([bad])
    assert verdicts[0].decision == AwardDecision.REJECT_FORGED_ATTESTATION


# ------------------------------------------------------------------ staleness

def test_stale_policy_version_is_rejected(server_key, config):
    sub = make_submission()
    stale = make_delivery(sub, server_key, policy_version=STALE_POLICY_VERSION)
    verdicts = new_defender(config).evaluate([stale])
    assert verdicts[0].decision == AwardDecision.REJECT_STALE_POLICY
    assert ReasonCode.STALE_POLICY_VERSION in verdicts[0].reason_codes


# -------------------------------------------------------------------- honesty

def test_honest_first_delivery_awards_once(server_key, config):
    sub = make_submission()
    verdicts = new_defender(config).evaluate([make_delivery(sub, server_key)])
    assert verdicts[0].decision == AwardDecision.AWARD
    assert verdicts[0].xp_awarded > 0
    assert ReasonCode.FIRST_AWARD in verdicts[0].reason_codes


def test_honest_new_evidence_across_sessions_is_not_replayed(server_key, config):
    """A learner who does NEW work in a new session must not be treated as a
    replay: different evidence content -> fresh identity -> award."""
    d1 = make_delivery(make_submission(level=0.9, task_id="task-1"), server_key,
                       session_id="s1")
    d2 = make_delivery(make_submission(level=0.95, task_id="task-2"), server_key,
                       session_id="s2", device_id="d2")
    verdicts = new_defender(config).evaluate([d1, d2])
    assert verdicts[0].decision == AwardDecision.AWARD
    assert verdicts[1].decision == AwardDecision.AWARD


def test_insufficient_evidence_denied_not_awarded(server_key, config):
    sub = make_submission(level=0.5)
    verdicts = new_defender(config).evaluate([make_delivery(sub, server_key)])
    assert verdicts[0].decision == AwardDecision.REJECT_INVALID_EVIDENCE
    assert ReasonCode.SCORE_BELOW_THRESHOLD in verdicts[0].reason_codes


def test_unverified_task_denied(server_key, config):
    sub = make_submission(verified=False)
    verdicts = new_defender(config).evaluate([make_delivery(sub, server_key)])
    assert verdicts[0].decision == AwardDecision.REJECT_INVALID_EVIDENCE
    assert ReasonCode.UNVERIFIED_TASK in verdicts[0].reason_codes
