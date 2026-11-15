"""P08 attack suite: deterministic generators for six attack vectors.

Every generator is a pure function of (seed, index, base submission). Attack
metadata is carried in ``evaluator_meta`` and is structurally invisible to the
defender (see types.strip_evaluator_meta).

Vectors (frozen in pre_registration.yaml):
  AV1_replay_identical           exact re-delivery of a captured valid submission
  AV2_replay_mutated_timestamp   re-delivery with shifted timestamps
  AV3_replay_rotated_event_id    re-delivery with rotated event/delivery/request ids
  AV4_forged_server_actor        attacker-controlled channel stamps actor='server'
  AV5_stale_policy               deliveries under a superseded policy version
  AV6_cross_device_replay        re-delivery from a new device/session
"""
from __future__ import annotations

import hashlib
import hmac as hmac_mod
from typing import Iterator

from .attestation import AttestationKey
from .types import Delivery, LearnerProfile, RewardEvent, Submission

ATTACK_VECTOR_IDS: tuple[str, ...] = (
    "AV1_replay_identical",
    "AV2_replay_mutated_timestamp",
    "AV3_replay_rotated_event_id",
    "AV4_forged_server_actor",
    "AV5_stale_policy",
    "AV6_cross_device_replay",
)


def deterministic_nonce(seed: str, index: int) -> str:
    """Stable pseudo-random hex derived from (seed, index); no RNG state."""
    digest = hashlib.sha256(f"{seed}:{index}".encode("utf-8")).hexdigest()
    return digest[:16]


class AttackFactory:
    """Builds adversarial deliveries from one captured honest submission."""

    def __init__(
        self,
        captured: Delivery,
        *,
        attacker_key: AttestationKey | None = None,
        stale_policy_version: int = 7,
    ) -> None:
        self._captured = captured
        self._attacker_key = attacker_key  # None => attacker cannot attest
        self._stale_policy_version = stale_policy_version

    # -- helpers ------------------------------------------------------------

    def _clone_submission(self) -> Submission:
        return self._captured.submission

    def _re_sign(self, submission: Submission, policy_version: int, nonce: str) -> str:
        """Sign with the ATTACKER key if the attacker has one (AV4 threat)."""
        if self._attacker_key is None:
            # attacker without the server key can only guess/fabricate
            return deterministic_nonce("forged-hmac", hash(nonce) % (2**32))
        return hmac_mod.new(
            self._attacker_key.key_bytes,
            AttestationKey.canonical_attestation_payload(submission, policy_version),
            hashlib.sha256,
        ).hexdigest()

    # -- vector generators ---------------------------------------------------

    def deliveries(self, vector_id: str, count: int, *, seed: str) -> Iterator[Delivery]:
        if vector_id not in ATTACK_VECTOR_IDS:
            raise ValueError(f"unknown attack vector: {vector_id!r}")
        gen = getattr(self, f"_gen_{vector_id}")
        return gen(count, seed)

    def _gen_AV1_replay_identical(self, count: int, seed: str) -> Iterator[Delivery]:
        """Exact byte-identical re-delivery of the captured delivery."""
        cap = self._captured
        for i in range(count):
            yield Delivery(
                submission=self._clone_submission(),
                event_id=cap.event_id,
                session_id=cap.session_id,
                device_id=cap.device_id,
                client_timestamp=cap.client_timestamp,
                policy_version=cap.policy_version,
                hmac_hex=cap.hmac_hex,
                evaluator_meta={"attack_vector": "AV1_replay_identical", "attack_index": i},
            )

    def _gen_AV2_replay_mutated_timestamp(self, count: int, seed: str) -> Iterator[Delivery]:
        cap = self._captured
        for i in range(count):
            yield Delivery(
                submission=self._clone_submission(),
                event_id=cap.event_id,
                session_id=cap.session_id,
                device_id=cap.device_id,
                client_timestamp=f"2099-01-01T00:{i // 60:02d}:{i % 60:02d}Z",
                policy_version=cap.policy_version,
                hmac_hex=cap.hmac_hex,  # timestamp is delivery variance, not signed
                evaluator_meta={"attack_vector": "AV2_replay_mutated_timestamp", "attack_index": i},
            )

    def _gen_AV3_replay_rotated_event_id(self, count: int, seed: str) -> Iterator[Delivery]:
        cap = self._captured
        for i in range(count):
            yield Delivery(
                submission=self._clone_submission(),
                event_id=f"evt-{deterministic_nonce(seed, i)}",  # rotated id
                session_id=cap.session_id,
                device_id=cap.device_id,
                client_timestamp=cap.client_timestamp,
                policy_version=cap.policy_version,
                hmac_hex=cap.hmac_hex,
                evaluator_meta={"attack_vector": "AV3_replay_rotated_event_id", "attack_index": i},
            )

    def _gen_AV4_forged_server_actor(self, count: int, seed: str) -> Iterator[Delivery]:
        """Attacker controls the channel: stamps actor='server' and forges
        maximal evidence. Whether this succeeds depends ONLY on whether the
        attacker can produce a valid HMAC under the server key."""
        cap = self._captured
        for i in range(count):
            forged_events = tuple(
                RewardEvent(kind=ev.kind, task_id=ev.task_id, competency=ev.competency,
                            level=1.0, actor="server")
                for ev in cap.submission.events
            )
            forged_submission = Submission(
                learner=LearnerProfile(
                    learner_id=cap.submission.learner.learner_id,
                    competencies={
                        cap.submission.requires_competency: 1.0,
                        **{k: 1.0 for k in cap.submission.skill_evidence},
                    },
                ),
                badge_id=cap.submission.badge_id,
                requires_competency=cap.submission.requires_competency,
                min_level=cap.submission.min_level,
                skill_evidence={cap.submission.requires_competency: 1.0},
                verified_task=True,
                events=forged_events,
            )
            # attacker attempts attestation with whatever key it holds
            hmac_hex = self._re_sign(forged_submission, cap.policy_version, f"av4-{i}")
            yield Delivery(
                submission=forged_submission,
                event_id=f"evt-{deterministic_nonce(seed + 'av4', i)}",
                session_id=cap.session_id,
                device_id=cap.device_id,
                client_timestamp=cap.client_timestamp,
                policy_version=cap.policy_version,
                hmac_hex=hmac_hex,
                evaluator_meta={"attack_vector": "AV4_forged_server_actor", "attack_index": i},
            )

    def _gen_AV5_stale_policy(self, count: int, seed: str) -> Iterator[Delivery]:
        cap = self._captured
        for i in range(count):
            # stale-policy deliveries keep the captured (server-valid) HMAC but
            # claim the superseded policy version; the payload is therefore
            # re-signed for the stale version by the ATTACKER only if it can.
            hmac_hex = cap.hmac_hex
            yield Delivery(
                submission=self._clone_submission(),
                event_id=f"evt-{deterministic_nonce(seed + 'av5', i)}",
                session_id=cap.session_id,
                device_id=cap.device_id,
                client_timestamp=cap.client_timestamp,
                policy_version=self._stale_policy_version,
                hmac_hex=hmac_hex,
                evaluator_meta={"attack_vector": "AV5_stale_policy", "attack_index": i},
            )

    def _gen_AV6_cross_device_replay(self, count: int, seed: str) -> Iterator[Delivery]:
        cap = self._captured
        for i in range(count):
            yield Delivery(
                submission=self._clone_submission(),
                event_id=f"evt-{deterministic_nonce(seed + 'av6', i)}",
                session_id=f"sess-{deterministic_nonce(seed + 'av6s', i)}",  # new session
                device_id=f"dev-{deterministic_nonce(seed + 'av6d', i)}",    # new device
                client_timestamp=f"2099-02-01T{i // 3600:02d}:{(i // 60) % 60:02d}:{i % 60:02d}Z",
                policy_version=cap.policy_version,
                hmac_hex=cap.hmac_hex,  # replaying the captured attestation
                evaluator_meta={"attack_vector": "AV6_cross_device_replay", "attack_index": i},
            )
