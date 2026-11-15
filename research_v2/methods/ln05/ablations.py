"""LN-05 mechanism-isolating ablations.

Each ablation disables exactly one I1 gate and keeps everything else
identical (same inputs, same budget, same label space), so any decision
divergence is attributable to the removed mechanism (LN-05-15):

- ``ablations_a1`` xp-only: competency proof gate removed; XP threshold on
  event xp values is the only success signal (mastery threshold disabled).
- ``ablations_a2`` no anti-replay: event-uniqueness and ledger consumption
  disabled; duplicate submissions each earn a fresh grant.
- ``ablations_a3`` no provenance check: server-only actor gate disabled;
  client-forged events are accepted.

Config-driven code paths genuinely differ (verified by counterexample tests):
an ablation is not the proposed function with a cosmetic flag but a distinct
gate chain.
"""
from __future__ import annotations

from typing import Any, Mapping

from research_v2.contracts.types import StudyInput, StudyPrediction
from research_v2.methods.ln05.proposed import (
    DEFAULT_BADGE_POLICY_VERSION,
    PolicyEpoch,
    PolicyInputError,
    ReplayLedger,
    evaluate as _evaluate_full,
)

ABLATION_VERSION = "2.0.0-ablation"

A1_METHOD_ID = "ablations_a1"
A2_METHOD_ID = "ablations_a2"
A3_METHOD_ID = "ablations_a3"


def _evaluate_a1(
    features: Mapping[str, Any],
    config: Mapping[str, Any],
    ledger: ReplayLedger,
    epoch: PolicyEpoch,
) -> tuple[str, tuple[str, ...], Mapping[str, Any]]:
    """A1: xp-only — keep freshness + provenance + dedup, drop mastery proof."""
    try:
        badge = features["badge"]
        skill_evidence = features["skill_evidence"]
        reward_events = features["reward_events"]
    except KeyError as exc:
        raise PolicyInputError(f"missing required LN-05 field: {exc}") from exc

    # Freshness and provenance still enforced (only the competency gate is cut).
    if features.get("event_policy_version") is not None and features["event_policy_version"] != badge.get(
        "policy_version", DEFAULT_BADGE_POLICY_VERSION
    ):
        return "revalidate_badge", ("stale_policy_version",), {"badge_awarded": False}
    for ev in reward_events:
        if ev.get("actor") != config.get("server_actor", "server"):
            return "reject_forged_event", ("untrusted_actor",), {"badge_awarded": False}
    event_ids = [ev.get("event_id") for ev in reward_events if ev.get("event_id") is not None]
    if len(event_ids) != len(set(event_ids)):
        return "deduplicate_events", ("replayed_event_detected",), {"badge_awarded": False}

    # Mastery threshold REPLACED by a raw XP criterion.
    xp_threshold = float(config.get("ablation_xp_threshold", 20))
    total_xp = sum(e.get("xp", 0) for e in reward_events if isinstance(e, Mapping))
    if total_xp < xp_threshold:
        return (
            "deny_mastery_badge",
            ("xp_below_threshold", "mastery_proof_disabled"),
            {"total_xp": total_xp, "threshold": xp_threshold, "badge_awarded": False},
        )
    # Replay ledger still consumed so A1 stays idempotent for duplicates.
    dedup = ledger.dedup_key(
        learner=features.get("learner", {}),
        badge=badge,
        skill_evidence=skill_evidence,
        reward_events=reward_events,
    )
    if not ledger.consume(dedup, case_id=str(features.get("case_id", "")), decision="grant_if_eligible", evidence_sha256="a1"):
        return "deduplicate_events", ("cross_batch_replay_detected",), {"badge_awarded": False, "replay_prevented": True}
    return "grant_if_eligible", ("xp_threshold_reached", "mastery_proof_disabled"), {"total_xp": total_xp, "badge_awarded": True}


def _evaluate_a2(
    features: Mapping[str, Any],
    config: Mapping[str, Any],
    ledger: ReplayLedger,
    epoch: PolicyEpoch,
) -> tuple[str, tuple[str, ...], Mapping[str, Any]]:
    """A2: no anti-replay — full I1 chain except event uniqueness/ledger."""
    config = dict(config)
    config["anti_replay"] = False
    return _evaluate_full(features, config, ledger, epoch)


def _evaluate_a3(
    features: Mapping[str, Any],
    config: Mapping[str, Any],
    ledger: ReplayLedger,
    epoch: PolicyEpoch,
) -> tuple[str, tuple[str, ...], Mapping[str, Any]]:
    """A3: no provenance check — full I1 chain except the server-actor gate."""
    config = dict(config)
    config["check_provenance"] = False
    return _evaluate_full(features, config, ledger, epoch)


_EVALUATORS = {
    A1_METHOD_ID: _evaluate_a1,
    A2_METHOD_ID: _evaluate_a2,
    A3_METHOD_ID: _evaluate_a3,
}


def make_predict_batch(method_id: str):
    """Build a runner-compatible ``predict_batch`` for one ablation id."""

    def predict_batch(inputs: list[StudyInput], config: dict | None = None) -> list[StudyPrediction]:
        config = dict(config or {})
        epoch = PolicyEpoch(
            policy_version=int(config.get("badge_policy_version", DEFAULT_BADGE_POLICY_VERSION)),
            dataset_sha256=str(config.get("dataset_sha256", "")),
        )
        ledger = ReplayLedger()
        evaluator = _EVALUATORS[method_id]
        preds: list[StudyPrediction] = []
        for inp in inputs:
            decision, reasons, observables = evaluator(dict(inp.features), config, ledger, epoch)
            dedup_key = observables.get("dedup_key")
            preds.append(
                StudyPrediction(
                    study_id=inp.study_id,
                    case_id=inp.case_id,
                    decision=decision,
                    score=None,
                    reason_codes=tuple(reasons),
                    evidence_ids=(dedup_key,) if dedup_key else (),
                )
            )
        return preds

    predict_batch.__name__ = f"predict_batch_{method_id}"
    predict_batch.__qualname__ = predict_batch.__name__
    return predict_batch
