"""LN-05 baselines.

- ``baselines_b0`` (C0, SANITY_ONLY): award whenever any reward event exists —
  grants purely on event count / XP activity, trusting client-supplied points.
  Deliberately vulnerable to replay, forgery and missing competency; it exists
  to expose metric gaming, never as a strong comparator.

- ``baselines_c1`` (C1, strong classical): timestamp-windowed server streak
  policy. Grants when server-actor events arrive within one streak window
  (event count >= ``streak_threshold`` inside the window). It uses server-side
  idempotency over the window but performs **no** actor provenance validation
  beyond a raw count, **no** competency/verified-task proof, and **no**
  cross-window replay defence — the classical failure mode LN-05 targets.

Both return the same output family as I1 (award/deny with evidence-chain
reason codes) over the frozen V2 label space, on identical input features and
budget, so comparisons are like-for-like (LN-05-11/12).
"""
from __future__ import annotations

from typing import Any, Mapping

from research_v2.contracts.types import StudyInput, StudyPrediction
from research_v2.methods.ln05.proposed import (
    DEFAULT_BADGE_POLICY_VERSION,
    PolicyInputError,
    ReplayLedger,
    PolicyEpoch,
    evaluate,
)

B0_METHOD_ID = "baselines_b0"
B1_METHOD_ID = "baselines_c1"
BASELINE_METHOD_VERSION = "1.0.0"


def _b0_evaluate(features: Mapping[str, Any], config: Mapping[str, Any]) -> tuple[str, tuple[str, ...], Mapping[str, Any]]:
    try:
        reward_events = features["reward_events"]
    except KeyError as exc:
        raise PolicyInputError(f"missing required LN-05 field: {exc}") from exc
    if not isinstance(reward_events, list):
        raise PolicyInputError("reward_events must be a list")
    total_xp = sum(e.get("xp", 0) for e in reward_events if isinstance(e, Mapping))
    # C0 sanity policy: any activity at all is badge-worthy. Client XP is
    # blindly trusted; duplicates only help (event count is the signal).
    awarded = len(reward_events) > 0 or total_xp > 0
    if awarded:
        return (
            "grant_if_eligible",
            ("baseline_event_count_grant",),
            {"total_xp": total_xp, "event_count": len(reward_events), "badge_awarded": True},
        )
    return (
        "deny_mastery_badge",
        ("baseline_insufficient_activity",),
        {"total_xp": 0, "event_count": 0, "badge_awarded": False},
    )


def predict_batch_b0(inputs: list[StudyInput], config: dict | None = None) -> list[StudyPrediction]:
    """B0 sanity baseline: award on event count."""
    config = dict(config or {})
    return [
        StudyPrediction(
            study_id=inp.study_id,
            case_id=inp.case_id,
            decision=decision,
            score=None,
            reason_codes=tuple(reasons),
            evidence_ids=(),
        )
        for inp in inputs
        for decision, reasons, _obs in [_b0_evaluate(dict(inp.features), config)]
    ]


def _c1_evaluate(
    features: Mapping[str, Any],
    config: Mapping[str, Any],
    ledger: ReplayLedger,
    epoch: PolicyEpoch,
) -> tuple[str, tuple[str, ...], Mapping[str, Any]]:
    try:
        badge = features["badge"]
        learner = features["learner"]
        skill_evidence = features["skill_evidence"]
        reward_events = features["reward_events"]
        event_policy_version = features["event_policy_version"]
    except KeyError as exc:
        raise PolicyInputError(f"missing required LN-05 field: {exc}") from exc

    badge_version = badge.get("policy_version", DEFAULT_BADGE_POLICY_VERSION)
    # C1 keeps only the classical freshness check (timestamp-window analogue:
    # events stamped under an old policy do not extend the current streak).
    if event_policy_version is not None and event_policy_version != badge_version:
        return "revalidate_badge", ("stale_policy_version",), {"badge_awarded": False}

    window = float(config.get("streak_window", 60.0))
    threshold = int(config.get("streak_threshold", 1))
    server_actor = config.get("server_actor", "server")

    streak = 0
    last_ts: float | None = None
    for ev in reward_events:
        ts = ev.get("timestamp")
        # No client timestamp trusted: events without stamps count directly.
        if isinstance(ts, (int, float)) and last_ts is not None and float(ts) - last_ts > window:
            streak = 0
        if ev.get("actor") == server_actor:
            streak += 1
        last_ts = float(ts) if isinstance(ts, (int, float)) else last_ts

    if streak < threshold:
        return (
            "deny_mastery_badge",
            ("streak_below_threshold",),
            {"streak_count": streak, "badge_awarded": False, "replay_prevented": False},
        )

    # Classical idempotency: one grant per window per (learner, badge) tuple,
    # keyed on profile id — no competency proof, no cryptographic event
    # identity, so replaying with a *new* window defeats it.
    dedup = f"{learner.get('profile_id')}:{badge.get('id')}:{badge_version}"
    evidence_sha = f"{skill_evidence.get('verified_task')}:{len(reward_events)}"
    if not ledger.consume(dedup, case_id=str(features.get("case_id", "")), decision="grant_if_eligible", evidence_sha256=evidence_sha):
        return "deduplicate_events", ("streak_window_idempotency",), {"badge_awarded": False, "replay_prevented": True}

    return (
        "grant_if_eligible",
        ("streak_window_reached",),
        {"streak_count": streak, "badge_awarded": True, "replay_prevented": False},
    )


def predict_batch_c1(inputs: list[StudyInput], config: dict | None = None) -> list[StudyPrediction]:
    """C1 strong classical baseline: timestamp-windowed streak, no provenance/proof."""
    config = dict(config or {})
    epoch = PolicyEpoch(
        policy_version=int(config.get("badge_policy_version", DEFAULT_BADGE_POLICY_VERSION)),
        dataset_sha256=str(config.get("dataset_sha256", "")),
    )
    ledger = ReplayLedger()
    preds: list[StudyPrediction] = []
    for inp in inputs:
        decision, reasons, observables = _c1_evaluate(dict(inp.features), config, ledger, epoch)
        preds.append(
            StudyPrediction(
                study_id=inp.study_id,
                case_id=inp.case_id,
                decision=decision,
                score=None,
                reason_codes=tuple(reasons),
                evidence_ids=(),
            )
        )
    return preds


# ---------------------------------------------------------------------------
# Runner-facing aliases: the experiment runner imports
# ``research_v2.methods.ln05.<method_id>.predict_batch``.
# ---------------------------------------------------------------------------


def predict_batch(inputs: list[StudyInput], config: dict | None = None) -> list[StudyPrediction]:
    """Default ABI entry: B0 sanity baseline."""
    return predict_batch_b0(inputs, config)
