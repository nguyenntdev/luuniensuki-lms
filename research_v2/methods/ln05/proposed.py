"""LN-05 / I1 — Evidence-gated mastery credential policy (proposed method).

Decision procedure (single pass over every gate, in severity order; the first
triggered gate determines the label, so families never collapse):

1. Policy freshness        event_policy_version != badge.policy_version
                           -> ``revalidate_badge`` (INV-LN-05-04).
2. Actor provenance        every reward event must originate from the server
                           actor -> ``reject_forged_event``
                           (INV-LN-05-01: client XP is not evidence).
3. Event uniqueness        repeated ``event_id`` inside the batch, or a
                           ``dedup_key`` already consumed in this policy epoch
                           -> ``deduplicate_events`` (INV-LN-05-02). The key is
                           the SHA-256 of the *normalized submission identity*
                           (learner, credential, task, evidence content, sorted
                           event content); delivery-variant fields (timestamps,
                           event/delivery/request ids, nonces, trace ids) are
                           stripped before hashing, so a clock-skewed or
                           re-tagged redelivery of the same submission maps to
                           the consumed key and is rejected. The ledger
                           consumption is atomic: the first duplicate delivery
                           of an identical submission is the only replay that
                           can observe ``grant_if_eligible``; all later
                           concurrent deliveries observe the replay rejection.
4. Competency mastery      multi-dimension proof: the required competency must
                           be present in skill evidence AND corroborated by the
                           learner's competency profile, the task must be
                           verified, and the evidence level must meet the badge
                           threshold -> otherwise ``deny_mastery_badge``
                           (INV-LN-05-03).
5. Grant                   ``grant_if_eligible`` (RULE-LN-05-01).

Vocabulary note: emitted labels use the dataset/gold vocabulary (the legacy
engine's, shared with ``research_v2/data/ln05/t3_gold.jsonl``); the frozen V2
label space (``reject_replay``, ``reject_spoofed_provenance``,
``reject_stale_policy``) is a documented one-to-one projection via
``research_v2.methods.ln05.labels.to_v2_decision``.

Determinism: identical (features, config, seed) produce byte-identical
predictions; the replay ledger is keyed by the normalized submission identity
(never by wall clock or delivery metadata).
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Any, Mapping

from research_v2.contracts.canonical_hash import canonical_json, sha256_input
from research_v2.contracts.types import StudyInput, StudyPrediction
from research_v2.methods.ln05.labels import ReplayLedgerEntry, validate_v2_decision

METHOD_ID = "proposed"
METHOD_VERSION = "2.1.0"

DEFAULT_COMPETENCY_KEYS = ("S1", "S2", "S3", "S4")
DEFAULT_BADGE_POLICY_VERSION = 2
#: Freshness horizon: an event stamped under a policy version newer than the
#: badge definition is also stale (badge definitions must be re-issued first).
DEFAULT_SERVER_ACTOR = "server"

# --------------------------------------------------------------------------
# Normalized submission identity (INV-LN-05-02 / prereg LN05-CE-3, CE-4).
#
# The replay dedup key must be derived from WHAT was submitted, not HOW it was
# delivered. Delivery-variant fields (clock stamps, transport ids, nonces) are
# excluded; identity-bearing fields and the evidence content are included.
# --------------------------------------------------------------------------

#: Allowlist of identity-bearing fields per feature section. Everything else
#: in a section is dropped before hashing; within reward events the per-event
#: allowlist below applies.
_IDENTITY_FIELDS: tuple[str, ...] = (
    # Learner / profile identity
    "learner_id",
    "profile_id",
    "actor_id",
    "user_id",
    # Credential identity
    "badge_id",
    "credential_id",
    "requires_competency",
    "min_level",
    "policy_version",
    # Task / assessment identity (a retry on a DIFFERENT task is new evidence)
    "task_id",
    "assessment_id",
    "content_id",
    "id",
    "urn",
    "type",
    # Evidence content
    "skill_evidence",
    "competencies",
    "verified_task",
)
#: Per-reward-event allowlist: the semantic content of an event (what was
#: claimed, by whom, for how much). ``event_id`` and any delivery metadata are
#: delivery variants, not submission identity.
_EVENT_IDENTITY_FIELDS: tuple[str, ...] = ("actor", "kind", "xp")

#: Delivery-variant field names excluded from identity. Any key containing
#: "time" (timestamp, server_time, client_time, ...) or ending in a transport
#: id suffix is a redelivery knob, not evidence. ``event_id`` is listed
#: explicitly: rotating it must not mint a fresh dedup key (CE-3).
_DELIVERY_VARIANT_FIELDS: frozenset[str] = frozenset(
    {
        "timestamp",
        "created_at",
        "submitted_at",
        "client_id",
        "request_id",
        "event_id",
        "delivery_id",
        "delivery_attempt",
        "nonce",
        "trace_id",
        "span_id",
        "correlation_id",
        "sequence_no",
        "seq",
        "attempt",
        "received_at",
        "processed_at",
        "idempotency_token",
        "message_id",
        "case_id",
        "seed",
        "session_id",
    }
)
_DELIVERY_VARIANT_SUFFIXES: tuple[str, ...] = ("_id", "_at", "_time", "_ts", "_token")
_DELIVERY_VARIANT_SUBSTRINGS: tuple[str, ...] = ("time", "nonce", "trace")
_IDENTITY_TIME_KEY_RE = re.compile(r"time|_ts$|_at$", re.IGNORECASE)


def _is_delivery_variant(key: str) -> bool:
    """True iff ``key`` names a delivery-variant (redelivery knob) field.

    Delivery variants are excluded from the dedup identity: mutating them is a
    redelivery of the same submission, never new evidence. Identity-bearing
    ``*_id`` fields (learner/profile/task/badge) are exempt via the allowlist.
    """
    if key in _IDENTITY_FIELDS or key in _EVENT_IDENTITY_FIELDS:
        return False
    if key in _DELIVERY_VARIANT_FIELDS:
        return True
    lowered = key.lower()
    if lowered.endswith(_DELIVERY_VARIANT_SUFFIXES):
        return True
    return any(marker in lowered for marker in _DELIVERY_VARIANT_SUBSTRINGS)


def _canonicalize_evidence_content(value: Any) -> Any:
    """Canonical form of evidence/submission content for identity hashing.

    - mappings: delivery-variant keys dropped, remaining keys sorted;
    - strings: NFC-normalized and whitespace-collapsed (a redelivery whose
      text differs only by spacing/NFC form is the same evidence);
    - lists: order-insensitive over items (event deliveries may arrive
      reordered without changing the submission); items canonicalized;
    - scalars: passed through unchanged (numeric equality is exact).
    """
    if isinstance(value, Mapping):
        return {
            key: _canonicalize_evidence_content(v)
            for key, v in sorted(value.items())
            if not _is_delivery_variant(key)
        }
    if isinstance(value, list):
        items = [_canonicalize_evidence_content(v) for v in value]
        return sorted(items, key=lambda item: canonical_json(item))
    if isinstance(value, str):
        return " ".join(unicodedata.normalize("NFC", value).split())
    return value


def _pick_identity_fields(section: Any, keys: tuple[str, ...]) -> dict[str, Any]:
    """Extract only the allowlisted identity fields from a feature section."""
    if not isinstance(section, Mapping):
        return {}
    return {k: _canonicalize_evidence_content(section[k]) for k in keys if k in section}


def _submission_identity(
    features: Mapping[str, Any],
    *,
    learner: Mapping[str, Any],
    badge: Mapping[str, Any],
    skill_evidence: Mapping[str, Any],
    reward_events: list[Mapping[str, Any]],
) -> dict[str, Any]:
    """Normalized submission identity: the payload the dedup key is derived from.

    Included (identity + content):
    - learner/profile identity: ``learner_id`` / ``profile_id`` /
      ``actor_id`` / ``user_id`` plus the competency profile (``competencies``);
    - credential identity: badge id (``id``/``badge_id``/``credential_id``),
      ``requires_competency``, ``min_level``, ``policy_version``;
    - task/assessment identity: the heritage-task section (``content`` /
      ``task`` mapping when present) via ``task_id`` / ``assessment_id`` /
      ``content_id`` / ``id`` / ``urn`` / ``type`` — a retry on a different
      task is genuinely new evidence and must derive a fresh key;
    - evidence content: the full ``skill_evidence`` mapping;
    - event content: per event, the allowlisted semantic fields
      (``actor``/``kind``/``xp``), order-insensitively.

    Excluded (delivery variants — mutating them is a redelivery, not new
    evidence): ``timestamp``/``*_at``/anything containing "time",
    ``event_id``/``*_id`` transport ids (client/request/delivery/trace/...),
    ``nonce``, ``case_id``, ``seed``, ``session_id``.

    Deterministic: identical submissions normalize to byte-identical payloads
    (sorted keys, NFC + whitespace-collapsed strings, order-insensitive event
    lists), so the derived SHA-256 key is stable across machines.
    """
    learner_keys = ("learner_id", "profile_id", "actor_id", "user_id", "competencies")
    badge_keys = ("id", "badge_id", "credential_id", "requires_competency", "min_level", "policy_version")
    task_keys = ("task_id", "assessment_id", "content_id", "id", "urn", "type")
    task_section = None
    for section_name in ("task", "content", "assessment"):
        section = features.get(section_name)
        if isinstance(section, Mapping):
            task_section = section
            break
    if task_section is None:
        task_section = badge.get("content") if isinstance(badge.get("content"), Mapping) else None
    events_payload = [
        _pick_identity_fields(ev, _EVENT_IDENTITY_FIELDS)
        for ev in reward_events
        if isinstance(ev, Mapping)
    ]
    events_payload.sort(key=lambda item: canonical_json(item))
    return {
        "learner": _pick_identity_fields(learner, learner_keys),
        "credential": _pick_identity_fields(badge, badge_keys),
        "task": _pick_identity_fields(task_section, task_keys) if task_section else {},
        "evidence": _canonicalize_evidence_content(skill_evidence),
        "events": events_payload,
    }


class PolicyInputError(ValueError):
    """Typed failure for structurally invalid policy inputs (no silent default)."""


@dataclass(frozen=True)
class PolicyEpoch:
    """Replay-ledger epoch bound to one policy version and dataset snapshot."""

    policy_version: int
    dataset_sha256: str = ""

    @property
    def epoch_key(self) -> str:
        return f"v{self.policy_version}:{self.dataset_sha256}"


class ReplayLedger:
    """Atomic idempotency ledger over normalized-submission-identity keys.

    A dedup key is the canonical SHA-256 of :func:`_submission_identity` —
    learner/credential/task identity plus evidence and event content, with all
    delivery-variant fields (timestamps, event/delivery/request ids, nonces)
    stripped before hashing. It is *content derived over the normalized
    identity*, so a clock-skewed redelivery with a fresh timestamp, or a
    redelivery that rotated its ``event_id``/``nonce``, maps to the same key
    and is rejected as a replay (CE-3); a genuinely new submission (different
    evidence content or task) derives a fresh key and stays eligible (CE-4
    semantics: identical retry is rejected, never re-awarded). ``consume`` is
    check-and-set in one step; only one caller per key can obtain ``True``.
    """

    def __init__(self) -> None:
        self._consumed: dict[str, ReplayLedgerEntry] = {}

    def dedup_key(
        self,
        *,
        learner: Mapping[str, Any],
        badge: Mapping[str, Any],
        skill_evidence: Mapping[str, Any],
        reward_events: list[Mapping[str, Any]],
        features: Mapping[str, Any] | None = None,
    ) -> str:
        """SHA-256 over the normalized submission identity (stable, documented).

        ``features`` (optional) carries the top-level task/assessment section
        (``task``/``content``/``assessment``) when it lives outside the badge;
        when omitted the identity is derived from the named sections alone.
        """
        return sha256_input(
            _submission_identity(
                features if features is not None else {},
                learner=learner,
                badge=badge,
                skill_evidence=skill_evidence,
                reward_events=reward_events,
            )
        )

    def is_consumed(self, dedup_key: str) -> bool:
        return dedup_key in self._consumed

    def consume(self, dedup_key: str, *, case_id: str, decision: str, evidence_sha256: str) -> bool:
        """Atomically claim a dedup key; True iff this caller is first."""
        if dedup_key in self._consumed:
            return False
        self._consumed[dedup_key] = ReplayLedgerEntry(
            dedup_key=dedup_key,
            case_id=case_id,
            decision=decision,
            evidence_sha256=evidence_sha256,
        )
        return True


@dataclass(frozen=True)
class GateResult:
    decision: str
    reason_codes: tuple[str, ...]
    observables: Mapping[str, Any]


def _extract(f: Mapping[str, Any]) -> tuple[Mapping[str, Any], Mapping[str, Any], list[Any], Mapping[str, Any], Mapping[str, Any]]:
    try:
        badge = f["badge"]
        learner = f["learner"]
        skill_evidence = f["skill_evidence"]
        reward_events = f["reward_events"]
        event_policy_version = f["event_policy_version"]
    except KeyError as exc:
        raise PolicyInputError(f"missing required LN-05 field: {exc}") from exc
    if not isinstance(badge, Mapping) or not isinstance(learner, Mapping):
        raise PolicyInputError("badge and learner must be mappings")
    if not isinstance(skill_evidence, Mapping):
        raise PolicyInputError("skill_evidence must be a mapping")
    if not isinstance(reward_events, list):
        raise PolicyInputError("reward_events must be a list")
    return badge, learner, reward_events, skill_evidence, {"event_policy_version": event_policy_version}


def gate_policy_freshness(
    f: Mapping[str, Any],
    config: Mapping[str, Any],
) -> GateResult | None:
    """Gate 1: policy version freshness (INV-LN-05-04)."""
    badge, _learner, _events, _se, extra = _extract(f)
    badge_version = badge.get("policy_version", DEFAULT_BADGE_POLICY_VERSION)
    event_version = extra["event_policy_version"]
    if event_version is not None and event_version != badge_version:
        return GateResult(
            decision="revalidate_badge",
            reason_codes=("stale_policy_version", "revalidation_required"),
            observables={
                "event_policy_version": event_version,
                "badge_policy_version": badge_version,
                "badge_awarded": False,
                "replay_prevented": False,
            },
        )
    return None


def gate_actor_provenance(
    f: Mapping[str, Any],
    config: Mapping[str, Any],
) -> GateResult | None:
    """Gate 2: server-only actor provenance (INV-LN-05-01)."""
    _badge, _learner, events, _se, _extra = _extract(f)
    trusted_actor = config.get("server_actor", DEFAULT_SERVER_ACTOR)
    for ev in events:
        if ev.get("actor") != trusted_actor:
            return GateResult(
                decision="reject_forged_event",
                reason_codes=("untrusted_actor", "client_forged_xp"),
                observables={
                    "forged_actor": ev.get("actor"),
                    "badge_awarded": False,
                    "replay_prevented": False,
                },
            )
    return None


def gate_event_uniqueness(
    f: Mapping[str, Any],
    config: Mapping[str, Any],
    ledger: ReplayLedger,
    epoch: PolicyEpoch,
) -> GateResult | None:
    """Gate 3: within-batch uniqueness + cross-batch anti-replay (INV-LN-05-02)."""
    _badge, learner, events, skill_evidence, _extra = _extract(f)

    event_ids = [ev.get("event_id") for ev in events if ev.get("event_id") is not None]
    if len(event_ids) != len(set(event_ids)):
        return GateResult(
            decision="deduplicate_events",
            reason_codes=("replayed_event_detected", "idempotency_violation"),
            observables={
                "duplicate_count": len(event_ids) - len(set(event_ids)),
                "badge_awarded": False,
                "replay_prevented": True,
            },
        )

    dedup = ledger.dedup_key(
        learner=learner,
        badge=_badge,
        skill_evidence=skill_evidence,
        reward_events=events,
        features=f,
    )
    if ledger.is_consumed(dedup):
        return GateResult(
            decision="deduplicate_events",
            reason_codes=("cross_batch_replay_detected", "idempotency_violation"),
            observables={
                "dedup_key": dedup,
                "badge_awarded": False,
                "replay_prevented": True,
            },
        )
    return None


def gate_competency_mastery(
    f: Mapping[str, Any],
    config: Mapping[str, Any],
) -> GateResult | None:
    """Gate 4: multi-dimension competency mastery proof (INV-LN-05-03)."""
    badge, learner, _events, skill_evidence, _extra = _extract(f)
    req = badge.get("requires_competency")
    if req is None:
        raise PolicyInputError("badge.requires_competency is required")
    min_level = float(badge.get("min_level", 0.75))

    level = skill_evidence.get(req)
    if not isinstance(level, (int, float)) or isinstance(level, bool):
        return GateResult(
            decision="deny_mastery_badge",
            reason_codes=("missing_competency_evidence", "score_below_threshold"),
            observables={
                "competency": req,
                "score": None,
                "threshold": min_level,
                "verified_task": skill_evidence.get("verified_task", False),
                "badge_awarded": False,
                "replay_prevented": False,
            },
        )

    # Corroboration: evidence level must agree with the learner's own
    # competency profile for the same dimension (multi-dimension proof).
    corroborated = True
    profile = learner.get("competencies")
    if isinstance(profile, Mapping) and req in profile:
        corroborated = abs(float(profile[req]) - float(level)) <= 1e-9

    verified_task = skill_evidence.get("verified_task", False) is True
    if not verified_task or not corroborated or float(level) < min_level:
        reasons: list[str] = []
        if not verified_task:
            reasons.append("unverified_task")
        if not corroborated:
            reasons.append("uncorroborated_competency")
        if float(level) < min_level:
            reasons.append("score_below_threshold")
        return GateResult(
            decision="deny_mastery_badge",
            reason_codes=("missing_competency_evidence", *reasons),
            observables={
                "competency": req,
                "score": float(level),
                "threshold": min_level,
                "verified_task": verified_task,
                "corroborated": corroborated,
                "badge_awarded": False,
                "replay_prevented": False,
            },
        )
    return None


def evaluate(
    features: Mapping[str, Any],
    config: Mapping[str, Any],
    ledger: ReplayLedger,
    epoch: PolicyEpoch,
) -> tuple[str, tuple[str, ...], Mapping[str, Any]]:
    """Full gate chain. Returns (decision, reason_codes, observables)."""
    badge, _learner, events, skill_evidence, _extra = _extract(features)

    stale = gate_policy_freshness(features, config)
    if stale is not None:
        return stale.decision, stale.reason_codes, stale.observables

    if config.get("check_provenance", True):
        spoofed = gate_actor_provenance(features, config)
        if spoofed is not None:
            return spoofed.decision, spoofed.reason_codes, spoofed.observables

    if config.get("anti_replay", True):
        replay = gate_event_uniqueness(features, config, ledger, epoch)
        if replay is not None:
            return replay.decision, replay.reason_codes, replay.observables

    denied = gate_competency_mastery(features, config)
    if denied is not None:
        return denied.decision, denied.reason_codes, denied.observables

    # Grant: atomically consume the dedup key. Under concurrency the first
    # delivery wins the grant; every other identical delivery loses the
    # check-and-set race and is a replay.
    dedup = ledger.dedup_key(
        learner=_learner,
        badge=badge,
        skill_evidence=skill_evidence,
        reward_events=events,
        features=features,
    )
    evidence_sha = sha256_input(dict(skill_evidence))
    if config.get("anti_replay", True):
        if not ledger.consume(dedup, case_id=str(features.get("case_id", "")), decision="grant_if_eligible", evidence_sha256=evidence_sha):
            return "deduplicate_events", ("cross_batch_replay_detected", "idempotency_violation"), {
                "dedup_key": dedup,
                "badge_awarded": False,
                "replay_prevented": True,
            }
    return (
        "grant_if_eligible",
        ("verified_competency_achieved", "provenance_validated"),
        {
            "competency": badge.get("requires_competency"),
            "score": float(skill_evidence[badge.get("requires_competency")]),
            "threshold": float(badge.get("min_level", 0.75)),
            "verified_task": True,
            "badge_awarded": True,
            "replay_prevented": False,
            "dedup_key": dedup,
        },
    )


def predict_batch(
    inputs: list[StudyInput],
    config: dict | None = None,
) -> list[StudyPrediction]:
    """ABI: one deterministic decision per input, idempotent under duplicates.

    ``config`` keys: ``seed`` (unused by the deterministic policy but recorded),
    ``dataset_sha256`` (bounds the replay-ledger epoch), ``check_provenance``,
    ``anti_replay``, ``server_actor``.
    """
    config = dict(config or {})
    validate_v2_decision("grant_if_eligible")
    epoch = PolicyEpoch(
        policy_version=int(config.get("badge_policy_version", DEFAULT_BADGE_POLICY_VERSION)),
        dataset_sha256=str(config.get("dataset_sha256", "")),
    )
    ledger = ReplayLedger()
    preds: list[StudyPrediction] = []
    for inp in inputs:
        features = dict(inp.features)
        decision, reasons, observables = evaluate(features, config, ledger, epoch)
        dedup_key = observables.get("dedup_key")
        evidence_ids = [dedup_key] if dedup_key else []
        score = observables.get("score")
        preds.append(
            StudyPrediction(
                study_id=inp.study_id,
                case_id=inp.case_id,
                decision=decision,
                score=float(score) if isinstance(score, (int, float)) else None,
                reason_codes=tuple(reasons),
                evidence_ids=tuple(evidence_ids),
            )
        )
    return preds
