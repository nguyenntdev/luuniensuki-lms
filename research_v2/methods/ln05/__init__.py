"""LN-05 — Evidence-Gated Mastery Credentials and Anti-Replay Gamification.

Study modules:
- ``proposed``        I1 evidence-gated policy (server provenance, event-uniqueness
                      dedup, multi-dimension competency proof, policy freshness,
                      anti-replay ledger; idempotent across duplicate inputs).
- ``baselines``       B0 sanity baseline (award on event count) and C1 strong
                      classical baseline (timestamp-windowed streak, no
                      provenance/competency proof).
- ``ablations``       A1 xp-only, A2 no anti-replay, A3 no provenance check.
- ``legacy_adapter``  Read-only adapter over ``research.integrations.ln05``.
- ``metrics``         Study metrics: replay containment, duplicate-grant count,
                      and accuracy over the frozen V2 label space.
"""
from research_v2.methods.ln05.legacy_adapter import LegacyLn05Adapter, run_legacy_policy
from research_v2.methods.ln05.labels import DecisionError, to_v2_decision
from research_v2.methods.ln05.proposed import METHOD_ID, METHOD_VERSION, predict_batch

__all__ = [
    "METHOD_ID",
    "METHOD_VERSION",
    "DecisionError",
    "LegacyLn05Adapter",
    "run_legacy_policy",
    "to_v2_decision",
    "predict_batch",
]
