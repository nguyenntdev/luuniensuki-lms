"""Frozen P08 types: submissions, deliveries, verdicts, and the ledger.

Contract invariants:
- No gold labels, oracles, or attack identifiers reach the defender's inputs.
  The defender sees Deliveries only; attack metadata lives in fixtures that
  the evaluator (not the defender) reads.
- Typed failures for structurally invalid inputs (PolicyInputError).
- Verdicts are frozen dataclasses; decisions come from a closed vocabulary.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping

# Closed decision vocabulary. ABSTAIN is reserved for defender-side capacity/
# configuration failures and is distinct from every negative verdict.
class AwardDecision(str, Enum):
    AWARD = "award"
    REJECT_REPLAY = "reject_replay"
    REJECT_FORGED_ATTESTATION = "reject_forged_attestation"
    REJECT_STALE_POLICY = "reject_stale_policy"
    REJECT_VELOCITY = "reject_velocity"
    REJECT_INVALID_EVIDENCE = "reject_invalid_evidence"
    ABSTAIN = "abstain"


class ReasonCode(str, Enum):
    FIRST_AWARD = "first_award"
    DUPLICATE_SUBMISSION = "duplicate_submission"
    CROSS_SESSION_REPLAY = "cross_session_replay"
    BAD_HMAC = "bad_hmac"
    UNTRUSTED_ACTOR = "untrusted_actor"
    STALE_POLICY_VERSION = "stale_policy_version"
    VELOCITY_BURST = "velocity_burst"
    MISSING_COMPETENCY_EVIDENCE = "missing_competency_evidence"
    SCORE_BELOW_THRESHOLD = "score_below_threshold"
    UNVERIFIED_TASK = "unverified_task"
    CAPACITY_EXHAUSTED = "capacity_exhausted"


class PolicyInputError(ValueError):
    """Typed failure for structurally invalid delivery inputs."""


@dataclass(frozen=True)
class LearnerProfile:
    learner_id: str
    competencies: Mapping[str, float]


@dataclass(frozen=True)
class RewardEvent:
    """Semantic content of one reward event as the server would attest it."""

    kind: str            # discovery | lesson | quiz
    task_id: str
    competency: str
    level: float
    actor: str = "server"  # trusted only when the delivery's HMAC verifies

    def semantic_payload(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "task_id": self.task_id,
            "competency": self.competency,
            "level": self.level,
            "actor": self.actor,
        }


@dataclass(frozen=True)
class Submission:
    """A mastery submission: learner, badge target, evidence, events."""

    learner: LearnerProfile
    badge_id: str
    requires_competency: str
    min_level: float
    skill_evidence: Mapping[str, float]
    verified_task: bool
    events: tuple[RewardEvent, ...]


@dataclass(frozen=True)
class Delivery:
    """One transport delivery of a submission to the reward endpoint.

    ``hmac_hex`` is the attestation the *client* presents; the defender only
    accepts ``actor="server"`` events when this verifies under the server key.
    Transport metadata (event_id, session_id, device, timestamps) is delivery
    variance and never part of award identity.
    """

    submission: Submission
    event_id: str
    session_id: str
    device_id: str
    client_timestamp: str
    policy_version: int
    hmac_hex: str
    # evaluator-only provenance; the defender must not read this
    # (enforced by Defender.evaluate copying the delivery without it)
    evaluator_meta: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AwardVerdict:
    delivery_index: int
    decision: AwardDecision
    reason_codes: tuple[ReasonCode, ...]
    xp_awarded: int
    dedup_key: str | None = None


@dataclass
class Session:
    """A learner session; sessions end (device restart, app relaunch)."""

    session_id: str
    device_id: str
    learner_id: str


def strip_evaluator_meta(delivery: Delivery) -> Delivery:
    """Return a copy of ``delivery`` with evaluator-only metadata removed.

    The defender is constructed from this projection so that attack/fixture
    metadata (attack vector id, expected outcome) can never influence the
    verdict — the structural analogue of the LN-05 oracle-leakage contract.
    """
    return Delivery(
        submission=delivery.submission,
        event_id=delivery.event_id,
        session_id=delivery.session_id,
        device_id=delivery.device_id,
        client_timestamp=delivery.client_timestamp,
        policy_version=delivery.policy_version,
        hmac_hex=delivery.hmac_hex,
        evaluator_meta={},
    )


def validate_submission(sub: Submission) -> None:
    if not isinstance(sub.min_level, (int, float)) or isinstance(sub.min_level, bool):
        raise PolicyInputError("min_level must be numeric")
    if not 0.0 <= float(sub.min_level) <= 1.0:
        raise PolicyInputError("min_level must be within [0, 1]")
    if not sub.events:
        raise PolicyInputError("submission must carry at least one reward event")


def deep_freeze_copy(value: Any) -> Any:
    """Defensive copy helper for evaluator bookkeeping."""
    return copy.deepcopy(value)
