"""P08 deterministic fixtures: honest learners, captured submissions, attack
streams, stress strata. Pure functions of the frozen seed (20261115).

No fixture carries gold material into defender inputs; attack vector ids live
only in ``Delivery.evaluator_meta`` (stripped before evaluation).
"""
from __future__ import annotations

from .attestation import AttestationKey
from .attacks import ATTACK_VECTOR_IDS, AttackFactory
from .types import Delivery, LearnerProfile, RewardEvent, Submission

SEED = "20261115"
POLICY_VERSION = 8
STALE_POLICY_VERSION = 7
HONEST_LEARNERS = 100
HONEST_SUBMISSIONS_PER_LEARNER = 10
FARMING_BURST_SIZE = 30
DUPLICATE_STRESS_COUNT = 100


def _honest_submission(learner_idx: int, sub_idx: int) -> Submission:
    """A valid mastery submission; content varies with (learner, sub) so the
    honest control stream has no replay structure at all."""
    learner_id = f"learner-{learner_idx:04d}"
    task_id = f"task-{learner_idx:04d}-{sub_idx:02d}"
    kind = ("discovery", "lesson", "mastered")[sub_idx % 3]
    comp = f"S{1 + (learner_idx + sub_idx) % 4}"
    level = 0.80 + ((learner_idx * 7 + sub_idx * 13) % 20) / 100.0  # 0.80..0.99
    return Submission(
        learner=LearnerProfile(learner_id=learner_id, competencies={comp: level}),
        badge_id=f"badge-{comp}",
        requires_competency=comp,
        min_level=0.75,
        skill_evidence={comp: level},
        verified_task=True,
        events=(RewardEvent(kind=kind, task_id=task_id, competency=comp, level=level),),
    )


def _deliver(
    sub: Submission,
    *,
    server_key: AttestationKey,
    event_id: str,
    session_id: str,
    device_id: str,
    client_timestamp: str,
    policy_version: int = POLICY_VERSION,
) -> Delivery:
    return Delivery(
        submission=sub,
        event_id=event_id,
        session_id=session_id,
        device_id=device_id,
        client_timestamp=client_timestamp,
        policy_version=policy_version,
        hmac_hex=server_key.sign(sub, policy_version),
        evaluator_meta={},
    )


def honest_control_deliveries(server_key: AttestationKey) -> list[Delivery]:
    """HC0: HONEST_LEARNERS x HONEST_SUBMISSIONS_PER_LEARNER distinct valid
    submissions, respecting the published velocity policy (max 5 per learner
    per 60s window): each learner's 10 submissions are spread across two
    sessions, and session arrivals are interleaved across learners so no
    learner exceeds the per-window cap in the global arrival order. Learners
    0..9 resubmit across sessions with DIFFERENT evidence content (honest new
    work, not a replay)."""
    deliveries: list[Delivery] = []
    records: list[tuple[int, int]] = []
    for learner_idx in range(HONEST_LEARNERS):
        for sub_idx in range(HONEST_SUBMISSIONS_PER_LEARNER):
            records.append((learner_idx, sub_idx))
    # interleave: round-robin over learners, keeping per-learner order
    records.sort(key=lambda pair: (pair[1], pair[0]))
    n = 0
    for learner_idx, sub_idx in records:
        sub = _honest_submission(learner_idx, sub_idx)
        # two sessions per learner: subs 0-4 in session A, 5-9 in session B
        session = (f"sess-{learner_idx:04d}-a" if sub_idx < 5
                   else f"sess-{learner_idx:04d}-b")
        deliveries.append(_deliver(
            sub,
            server_key=server_key,
            event_id=f"evt-honest-{n:06d}",
            session_id=session,
            device_id=f"dev-{learner_idx % 7:03d}",
            client_timestamp=f"2026-11-15T10:{n // 60:02d}:{n % 60:02d}Z",
        ))
        n += 1
    return deliveries


def captured_valid_delivery(server_key: AttestationKey) -> Delivery:
    """One server-attested valid submission that the attacker has captured."""
    sub = _honest_submission(0, 0)
    return _deliver(
        sub,
        server_key=server_key,
        event_id="evt-captured-1",
        session_id="sess-orig",
        device_id="dev-orig",
        client_timestamp="2026-11-15T09:00:00Z",
    )


def adversarial_deliveries(server_key: AttestationKey, attacker_key: AttestationKey,
                           per_vector: int) -> dict[str, list[Delivery]]:
    """6 attack vectors x ``per_vector`` deliveries each.

    AV4 gets a weak attacker key (different secret) to model an attacker who
    can run the signing algorithm but does NOT hold the server key; AV1-AV3,
    AV5, AV6 replay the captured server attestation without any new minting.
    """
    captured = captured_valid_delivery(server_key)
    factory = AttackFactory(captured, attacker_key=attacker_key,
                            stale_policy_version=STALE_POLICY_VERSION)
    return {
        vector_id: list(factory.deliveries(vector_id, per_vector, seed=SEED))
        for vector_id in ATTACK_VECTOR_IDS
    }


def duplicate_stress_delivery(server_key: AttestationKey) -> list[Delivery]:
    """SS1: the same valid submission delivered 100x (mixed transport skins)."""
    base = captured_valid_delivery(server_key)
    factory = AttackFactory(base, attacker_key=None)
    return list(factory.deliveries("AV1_replay_identical", DUPLICATE_STRESS_COUNT, seed=SEED))


def farming_burst_deliveries(server_key: AttestationKey) -> list[Delivery]:
    """SS2: 30 DISTINCT valid-evidence submissions in one burst from one
    learner (no replay; the attack is velocity, not duplication)."""
    deliveries: list[Delivery] = []
    for k in range(FARMING_BURST_SIZE):
        level = 0.80 + k * 0.001
        sub = Submission(
            learner=LearnerProfile(learner_id="learner-farmer", competencies={"S1": level}),
            badge_id="badge-S1",
            requires_competency="S1",
            min_level=0.75,
            skill_evidence={"S1": level},
            verified_task=True,
            events=(RewardEvent(kind="mastered", task_id=f"task-farm-{k:02d}",
                                competency="S1", level=level),),
        )
        deliveries.append(_deliver(
            sub,
            server_key=server_key,
            event_id=f"evt-farm-{k:03d}",
            session_id="sess-farmer",
            device_id="dev-farmer",
            client_timestamp=f"2026-11-15T11:00:{k:02d}Z",
        ))
    return deliveries


def stream_id(delivery: Delivery, index: int) -> str:
    meta = delivery.evaluator_meta or {}
    return f"{meta.get('attack_vector', 'HC0_honest_learners')}#{meta.get('attack_index', index)}"
