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
                           -> ``deduplicate_events`` (INV-LN-05-02). The ledger
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
predictions; the replay ledger is keyed by content hash, never by wall clock.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from research_v2.contracts.canonical_hash import sha256_input
from research_v2.contracts.types import StudyInput, StudyPrediction
from research_v2.methods.ln05.labels import ReplayLedgerEntry, validate_v2_decision

METHOD_ID = "proposed"
METHOD_VERSION = "2.0.0"

DEFAULT_COMPETENCY_KEYS = ("S1", "S2", "S3", "S4")
DEFAULT_BADGE_POLICY_VERSION = 2
#: Freshness horizon: an event stamped under a policy version newer than the
#: badge definition is also stale (badge definitions must be re-issued first).
DEFAULT_SERVER_ACTOR = "server"


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
    """Atomic idempotency ledger over cryptographic dedup keys.

    A dedup key is the canonical SHA-256 of the submission identity tuple
    (learner profile, badge, verified evidence, ordered event identity). It is
    *content derived*, so a clock-skewed redelivery with a fresh timestamp but
    the same submission content maps to the same key and is rejected as a
    replay. ``consume`` is check-and-set in one step; only one caller per key
    can obtain ``True``.
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
    ) -> str:
        return sha256_input(
            {
                "learner": learner.get("profile_id"),
                "badge": dict(badge),
                "evidence": dict(skill_evidence),
                "events": [dict(ev) for ev in reward_events],
            }
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
