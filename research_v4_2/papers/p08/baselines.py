"""P08 Baselines:
C0: Naive Increment (no idempotency, blind awards).
C1: Simple Idempotency Key (standard HTTP header idempotency key check).
C2 / Baseline Champion B*: Optimistic CAS Ledger (version-checked ledger, but lacks normalized content hashing and server attestation verification).
"""
from __future__ import annotations

from typing import Dict, Optional, Set
from .method import AwardDecision, Delivery


class C0NaiveIncrement:
    """C0 Sanity: Awards XP for every incoming delivery without check."""
    def process_delivery(self, delivery: Delivery) -> AwardDecision:
        sub = delivery.submission
        return AwardDecision(
            status="awarded",
            xp_granted=sub.xp_value,
            reasons=("c0_blind_award",),
        )


class C1SimpleIdempotencyKey:
    """C1 Classical: Deduplicates solely on the client-provided idempotency_key string."""
    def __init__(self):
        self.seen_keys: Set[str] = set()

    def process_delivery(self, delivery: Delivery) -> AwardDecision:
        sub = delivery.submission
        if sub.idempotency_key in self.seen_keys:
            return AwardDecision(
                status="reject_replay",
                xp_granted=0,
                reasons=("c1_duplicate_idempotency_key",),
            )
        self.seen_keys.add(sub.idempotency_key)
        return AwardDecision(
            status="awarded",
            xp_granted=sub.xp_value,
            reasons=("c1_key_accepted",),
        )


class C2OptimisticCASLedger:
    """C2 / Baseline Champion B*: Optimistic CAS Versioned Ledger.
    
    Tracks a per-learner version counter and dedupes on idempotency_key.
    However, it lacks:
    1. Server HMAC attestation (trusts client-fabricated actor='server' claims).
    2. Normalized content hashing (fooled when attacker generates a new idempotency_key for the same badge).
    3. Causal epoch chaining across distributed services.
    """
    def __init__(self):
        self.seen_keys: Set[str] = set()
        self.learner_versions: Dict[str, int] = {}

    def process_delivery(self, delivery: Delivery) -> AwardDecision:
        sub = delivery.submission
        lid = sub.learner.learner_id

        # 1. Check raw idempotency key
        if sub.idempotency_key in self.seen_keys:
            return AwardDecision(
                status="reject_replay",
                xp_granted=0,
                reasons=("c2_duplicate_idempotency_key",),
            )

        # 2. CAS version increment
        ver = self.learner_versions.get(lid, 0)
        self.learner_versions[lid] = ver + 1
        self.seen_keys.add(sub.idempotency_key)

        return AwardDecision(
            status="awarded",
            xp_granted=sub.xp_value,
            reasons=("c2_cas_version_committed",),
        )
