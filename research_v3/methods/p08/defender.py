"""P08 reward-integrity defender (the proposed method).

Defense stack (frozen in pre_registration.yaml):
  D1 HMAC-SHA256 server attestation  — actor='server' events are trusted only
     when the delivery's HMAC verifies under the server key (gates AV4).
  D2 Persistent cross-session idempotency — award identity is content-derived
     (learner, badge, task, evidence, event semantics) with ALL transport
     fields stripped; the ledger persists across sessions/devices for the
     policy epoch (gates AV1/AV2/AV3/AV6; concept reused from LN-05 but
     LN-05's ledger is per-batch, this one is persistent).
  D3 Velocity/burst control — per-learner sliding window caps submissions
     (gates fast-click farming, SS2).
  D4 Server-side evidence re-verification — badge competency requirements are
     checked against the (attested) evidence, not client claims.

Gate order (first triggered gate decides; families never collapse):
  1. policy freshness          -> reject_stale_policy
  2. attestation               -> reject_forged_attestation
  3. velocity control          -> reject_velocity
  4. evidence re-verification  -> reject_invalid_evidence
  5. idempotency (persistent)  -> reject_replay
  6. award                     -> award

Fail-closed: capacity/config failure -> abstain (never award).

Determinism: no RNG, no wall clock; identical (deliveries, config) produce
byte-identical verdict sequences.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from .attestation import AttestationKey
from .types import (
    AwardDecision,
    AwardVerdict,
    Delivery,
    PolicyInputError,
    ReasonCode,
    Submission,
    strip_evaluator_meta,
)


@dataclass(frozen=True)
class VelocityPolicy:
    window_seconds: int = 60
    max_submissions_per_learner: int = 5


@dataclass(frozen=True)
class PolicyConfig:
    policy_version: int
    attestation_key: AttestationKey
    velocity: VelocityPolicy = field(default_factory=VelocityPolicy)
    evidence_threshold_default: float = 0.75
    award_amounts: Mapping[str, int] = field(
        default_factory=lambda: {"discovery": 25, "lesson": 50, "mastered": 75}
    )
    max_xp_per_learner: int = 150
    capacity: int = 10_000_000  # ledger capacity; exceed => abstain


def submission_identity(sub: Submission) -> dict:
    """Normalized award identity: WHAT was earned, not HOW it was delivered.

    Included: learner id, badge id + requirement + threshold, evidence
    content, verified_task, event semantics (kind/task/competency/level).
    Excluded (delivery variance): event_id, session_id, device_id,
    client_timestamp, actor string (attestation decides trust), HMAC.
    """
    return {
        "learner_id": sub.learner.learner_id,
        "badge_id": sub.badge_id,
        "requires_competency": sub.requires_competency,
        "min_level": float(sub.min_level),
        "skill_evidence": {k: sub.skill_evidence[k] for k in sorted(sub.skill_evidence)},
        "verified_task": bool(sub.verified_task),
        "events": sorted(
            (
                {"kind": ev.kind, "task_id": ev.task_id,
                 "competency": ev.competency, "level": float(ev.level)}
                for ev in sub.events
            ),
            key=lambda d: (d["kind"], d["task_id"], d["competency"], d["level"]),
        ),
    }


def identity_key(sub: Submission) -> str:
    import hashlib
    import json
    payload = json.dumps(submission_identity(sub), sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False, allow_nan=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


class _VelocityWindow:
    """Per-learner sliding window over delivery arrival order (deterministic:
    'time' is the delivery index scaled by the window, not a wall clock)."""

    def __init__(self, policy: VelocityPolicy) -> None:
        self._policy = policy
        self._hits: dict[str, list[int]] = {}

    def allow(self, learner_id: str, arrival_index: int) -> bool:
        # Deterministic virtual clock: one second per arrival slot.
        now = arrival_index  # seconds
        hits = [t for t in self._hits.get(learner_id, []) if t > now - self._policy.window_seconds]
        self._hits[learner_id] = hits
        if len(hits) >= self._policy.max_submissions_per_learner:
            return False
        self._hits[learner_id].append(now)
        return True


class RewardIntegrityDefender:
    """The P08 proposed defender. One instance per policy epoch."""

    def __init__(self, config: PolicyConfig) -> None:
        self._config = config
        self._consumed: dict[str, dict] = {}   # identity_key -> award record
        self._learner_xp: dict[str, int] = {}
        self._velocity = _VelocityWindow(config.velocity)
        self._abstained = False

    # -- introspection (evaluator-facing) -----------------------------------

    @property
    def consumed_count(self) -> int:
        return len(self._consumed)

    def xp_total(self, learner_id: str) -> int:
        return self._learner_xp.get(learner_id, 0)

    # -- gates ----------------------------------------------------------------

    def _gate_policy_freshness(self, delivery: Delivery) -> AwardVerdict | None:
        if delivery.policy_version != self._config.policy_version:
            return AwardVerdict(
                delivery_index=-1,
                decision=AwardDecision.REJECT_STALE_POLICY,
                reason_codes=(ReasonCode.STALE_POLICY_VERSION,),
                xp_awarded=0,
            )
        return None

    def _gate_attestation(self, delivery: Delivery) -> AwardVerdict | None:
        key = self._config.attestation_key
        if not key.verify(delivery.submission, delivery.policy_version, delivery.hmac_hex):
            return AwardVerdict(
                delivery_index=-1,
                decision=AwardDecision.REJECT_FORGED_ATTESTATION,
                reason_codes=(ReasonCode.BAD_HMAC,),
                xp_awarded=0,
            )
        # attested payload must itself claim server actor
        if any(ev.actor != "server" for ev in delivery.submission.events):
            return AwardVerdict(
                delivery_index=-1,
                decision=AwardDecision.REJECT_FORGED_ATTESTATION,
                reason_codes=(ReasonCode.UNTRUSTED_ACTOR,),
                xp_awarded=0,
            )
        return None

    def _gate_velocity(self, delivery: Delivery, arrival_index: int) -> AwardVerdict | None:
        if not self._velocity.allow(delivery.submission.learner.learner_id, arrival_index):
            return AwardVerdict(
                delivery_index=-1,
                decision=AwardDecision.REJECT_VELOCITY,
                reason_codes=(ReasonCode.VELOCITY_BURST,),
                xp_awarded=0,
            )
        return None

    def _gate_evidence(self, delivery: Delivery) -> AwardVerdict | None:
        sub = delivery.submission
        req = sub.requires_competency
        level = sub.skill_evidence.get(req)
        if not isinstance(level, (int, float)) or isinstance(level, bool):
            return AwardVerdict(
                delivery_index=-1,
                decision=AwardDecision.REJECT_INVALID_EVIDENCE,
                reason_codes=(ReasonCode.MISSING_COMPETENCY_EVIDENCE,),
                xp_awarded=0,
            )
        threshold = float(sub.min_level) if sub.min_level else self._config.evidence_threshold_default
        reasons = []
        if float(level) < threshold:
            reasons.append(ReasonCode.SCORE_BELOW_THRESHOLD)
        if sub.verified_task is not True:
            reasons.append(ReasonCode.UNVERIFIED_TASK)
        if reasons:
            return AwardVerdict(
                delivery_index=-1,
                decision=AwardDecision.REJECT_INVALID_EVIDENCE,
                reason_codes=tuple(reasons),
                xp_awarded=0,
            )
        return None

    def _gate_idempotency(self, delivery: Delivery, key: str) -> AwardVerdict | None:
        if key in self._consumed:
            record = self._consumed[key]
            session_new = delivery.session_id != record.get("session_id")
            device_new = delivery.device_id != record.get("device_id")
            reasons = [ReasonCode.DUPLICATE_SUBMISSION]
            if session_new or device_new:
                reasons.append(ReasonCode.CROSS_SESSION_REPLAY)
            return AwardVerdict(
                delivery_index=-1,
                decision=AwardDecision.REJECT_REPLAY,
                reason_codes=tuple(reasons),
                xp_awarded=0,
                dedup_key=key,
            )
        return None

    # -- main entry ------------------------------------------------------------

    def evaluate(self, deliveries: list[Delivery]) -> list[AwardVerdict]:
        """One deterministic pass over the delivery stream."""
        verdicts: list[AwardVerdict] = []
        for index, raw in enumerate(deliveries):
            delivery = strip_evaluator_meta(raw)  # oracle hygiene
            try:
                verdict = self._evaluate_one(delivery, index)
            except PolicyInputError:
                verdict = AwardVerdict(
                    delivery_index=index,
                    decision=AwardDecision.ABSTAIN,
                    reason_codes=(ReasonCode.CAPACITY_EXHAUSTED,),
                    xp_awarded=0,
                )
            verdicts.append(AwardVerdict(
                delivery_index=index,
                decision=verdict.decision,
                reason_codes=verdict.reason_codes,
                xp_awarded=verdict.xp_awarded,
                dedup_key=verdict.dedup_key,
            ))
        return verdicts

    def _evaluate_one(self, delivery: Delivery, arrival_index: int) -> AwardVerdict:
        if len(self._consumed) >= self._config.capacity:
            return AwardVerdict(
                delivery_index=arrival_index,
                decision=AwardDecision.ABSTAIN,
                reason_codes=(ReasonCode.CAPACITY_EXHAUSTED,),
                xp_awarded=0,
            )

        gate = self._gate_policy_freshness(delivery)
        if gate is not None:
            return self._finalize(gate, arrival_index)

        gate = self._gate_attestation(delivery)
        if gate is not None:
            return self._finalize(gate, arrival_index)

        gate = self._gate_velocity(delivery, arrival_index)
        if gate is not None:
            return self._finalize(gate, arrival_index)

        gate = self._gate_evidence(delivery)
        if gate is not None:
            return self._finalize(gate, arrival_index)

        key = identity_key(delivery.submission)
        gate = self._gate_idempotency(delivery, key)
        if gate is not None:
            return self._finalize(gate, arrival_index, dedup_key=key)

        # ---- award path ----
        learner_id = delivery.submission.learner.learner_id
        xp_cap = self._config.max_xp_per_learner
        current = self._learner_xp.get(learner_id, 0)
        primary_kind = delivery.submission.events[0].kind
        amount = int(self._config.award_amounts.get(primary_kind, 0))
        amount = min(amount, max(0, xp_cap - current))
        self._learner_xp[learner_id] = current + amount
        self._consumed[key] = {
            "session_id": delivery.session_id,
            "device_id": delivery.device_id,
            "xp": amount,
        }
        return AwardVerdict(
            delivery_index=arrival_index,
            decision=AwardDecision.AWARD,
            reason_codes=(ReasonCode.FIRST_AWARD,),
            xp_awarded=amount,
            dedup_key=key,
        )

    def _finalize(self, verdict: AwardVerdict, arrival_index: int,
                  dedup_key: str | None = None) -> AwardVerdict:
        return AwardVerdict(
            delivery_index=arrival_index,
            decision=verdict.decision,
            reason_codes=verdict.reason_codes,
            xp_awarded=0,
            dedup_key=dedup_key,
        )
