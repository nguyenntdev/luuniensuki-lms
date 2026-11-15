"""P08 HMAC-SHA256 reward attestation (defense D1).

The server signs the canonical semantic payload of a submission under a
server-side key. A delivery claiming server-actor events is trusted only if
its HMAC verifies. An attacker who controls the transport channel can replay
captured attestations but cannot mint attestations for NEW forged submissions.

Key material: generated in-memory by the evaluation harness with a fixed seed
for reproducibility of the *experiment*, never committed to the repository.
"""
from __future__ import annotations

import hashlib
import hmac
from typing import Any, Mapping

from .types import PolicyInputError, Submission


class AttestationKey:
    """Server-side attestation key (key id + secret bytes)."""

    def __init__(self, key_id: str, key_bytes: bytes) -> None:
        if not key_bytes:
            raise PolicyInputError("attestation key must be non-empty")
        self.key_id = key_id
        self.key_bytes = key_bytes

    @classmethod
    def derive_from_seed(cls, key_id: str, seed: str) -> "AttestationKey":
        """Deterministic key for reproducible evaluation runs (research only;
        production keys must come from a KMS, never from a public seed)."""
        key_bytes = hashlib.sha256(f"p08-attestation:{seed}:{key_id}".encode("utf-8")).digest()
        return cls(key_id=key_id, key_bytes=key_bytes)

    @staticmethod
    def canonical_attestation_payload(submission: Submission, policy_version: int) -> bytes:
        """Canonical bytes of the signed semantic payload.

        Signed: learner identity, badge identity + requirement, evidence
        content, verified_task, and full event semantics. NOT signed: every
        transport field (event_id, session_id, device_id, client_timestamp) —
        those are delivery variance and must never affect validity.
        """
        payload: dict[str, Any] = {
            "policy_version": int(policy_version),
            "learner_id": submission.learner.learner_id,
            "competencies": {k: submission.learner.competencies[k]
                             for k in sorted(submission.learner.competencies)},
            "badge_id": submission.badge_id,
            "requires_competency": submission.requires_competency,
            "min_level": float(submission.min_level),
            "skill_evidence": {k: submission.skill_evidence[k]
                               for k in sorted(submission.skill_evidence)},
            "verified_task": bool(submission.verified_task),
            "events": [
                {
                    "kind": ev.kind,
                    "task_id": ev.task_id,
                    "competency": ev.competency,
                    "level": float(ev.level),
                    "actor": ev.actor,
                }
                for ev in submission.events
            ],
        }
        # canonical JSON: sorted keys, compact separators, utf-8
        import json
        return json.dumps(payload, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=False, allow_nan=False).encode("utf-8")

    def sign(self, submission: Submission, policy_version: int) -> str:
        mac = hmac.new(
            self.key_bytes,
            self.canonical_attestation_payload(submission, policy_version),
            hashlib.sha256,
        )
        return mac.hexdigest()

    def verify(self, submission: Submission, policy_version: int, hmac_hex: str) -> bool:
        return hmac.compare_digest(self.sign(submission, policy_version), hmac_hex)
