"""LN-05 decision labels and typed validation.

Research V2 canonical label space (``research_v2.contracts.label_space.LN05_DECISIONS``):
    grant_if_eligible, deny_mastery_badge, reject_replay,
    reject_spoofed_provenance, reject_stale_policy

The legacy engine (``research.gamification.mastery_reward_policy``) emits a
different, overlapping vocabulary. The mapping is bidirectional and total:

==========================  =========================================
V2 label                    Legacy label
==========================  =========================================
grant_if_eligible           grant_if_eligible
deny_mastery_badge          deny_mastery_badge
reject_replay               deduplicate_events
reject_spoofed_provenance   reject_forged_event
reject_stale_policy         revalidate_badge
==========================  =========================================

Per LN-05-04, abstain/defer/reject families stay distinct: a replay rejection
(``reject_replay``) must never collapse into a competency denial
(``deny_mastery_badge``) or a provenance rejection, otherwise the confusion
matrix cannot separate false accepts from false rejects.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from research_v2.contracts.label_space import LN05_DECISIONS, validate_decision


class DecisionError(ValueError):
    """Raised for unknown or out-of-space decision labels."""


#: V2 -> legacy decision vocabulary.
V2_TO_LEGACY: Mapping[str, str] = {
    "grant_if_eligible": "grant_if_eligible",
    "deny_mastery_badge": "deny_mastery_badge",
    "reject_replay": "deduplicate_events",
    "reject_spoofed_provenance": "reject_forged_event",
    "reject_stale_policy": "revalidate_badge",
}

#: Legacy -> V2 decision vocabulary (total over the legacy engine's outputs).
LEGACY_TO_V2: Mapping[str, str] = {v: k for k, v in V2_TO_LEGACY.items()}


def to_v2_decision(label: str) -> str:
    """Translate a legacy decision into the V2 label space.

    Unknown labels raise :class:`DecisionError` instead of silently defaulting.
    """
    mapped = LEGACY_TO_V2.get(label)
    if mapped is None:
        raise DecisionError(f"unknown legacy decision label: {label!r}")
    return mapped


def to_legacy_decision(label: str) -> str:
    """Translate a V2 decision into the legacy engine's vocabulary."""
    mapped = V2_TO_LEGACY.get(label)
    if mapped is None:
        raise DecisionError(f"unknown V2 decision label: {label!r}")
    return mapped


def validate_v2_decision(label: str) -> None:
    """Validate against the frozen V2 label space (raises LabelSpaceError)."""
    validate_decision("LN-05", label)


@dataclass(frozen=True)
class ReplayLedgerEntry:
    """Immutable record of one dedup-key consumption (atomic idempotency)."""

    dedup_key: str
    case_id: str
    decision: str
    evidence_sha256: str
