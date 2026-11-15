"""P08 — Evidence-grounded mastery gamification: active-adversary reward
integrity (SOFTWARE SECURITY EVALUATION; no human-outcome claims).

Scope and provenance:
- Reuses the anti-replay idempotency invariant CONCEPT from V2 LN-05
  (research_v2/methods/ln05/), which is a single-batch policy-correctness
  result under honest delivery.
- P08's contribution is the boundary LN-05 never claimed: an ACTIVE adversary
  who controls the delivery channel. The defender adds mechanisms LN-05 lacks:
  HMAC-SHA256 server attestation, persistent cross-session idempotency, and
  velocity control.

Boundary contract (binding):
- Every verdict is about software behavior, never about human motivation,
  engagement, trust, or learning.
- Typed failures; no silent defaults; determinism under a fixed seed.
"""
from __future__ import annotations

from .defender import PolicyConfig, RewardIntegrityDefender
from .types import (
    AwardDecision,
    AwardVerdict,
    Delivery,
    PolicyInputError,
    ReasonCode,
    RewardEvent,
    Session,
    Submission,
    LearnerProfile,
)

__all__ = [
    "AwardDecision",
    "AwardVerdict",
    "Delivery",
    "PolicyConfig",
    "PolicyInputError",
    "ReasonCode",
    "RewardEvent",
    "RewardIntegrityDefender",
    "Session",
    "Submission",
    "LearnerProfile",
]
