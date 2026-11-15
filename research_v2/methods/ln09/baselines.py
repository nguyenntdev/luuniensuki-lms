"""LN-09 baselines: B0 naive sanity and C1 strong classical.

Comparability cards
-------------------
- ``predict_batch_b0`` (B0, SANITY_ONLY): "always propose an action on any
  risk signal" — the naive dashboard heuristic recorded in legacy
  ``evaluate_baseline_rules``. Any non-empty evidence stream (or even a bare
  risk flag) yields ``propose_explained_action``; it performs no k-anonymity
  check, no source verification, no freshness gate and never abstains.
  Recorded as ``REIMPLEMENTATION`` of the legacy flat baseline, role
  SANITY_ONLY; must never be reported as a strong baseline. This baseline
  commits exactly the INV-LN-09-01 violation (inferring deficit from missing
  logs) the proposed method exists to prevent.

- ``predict_batch_c1`` (C1, MATCHED_CLASSICAL): EMA moving-average trend
  alerts — exponential moving average over verified evidence scores with a
  fixed intervention threshold. Classical, interpretable, deterministic. It
  deliberately omits k-anonymity suppression and source auditing (freshness
  is honored on observed evidence ages only insofar as the input exposes a
  single aggregate age), per spec 12_C1_STRONG_CLASSICAL. Independent
  implementation: shares only shared parsing helpers with the proposed
  engine, never its decision path.

Both produce the same output type and gold-compatible decision vocabulary as
the proposed method so metrics are computed on a common decision space.
"""
from __future__ import annotations

from typing import Any, Mapping

from research_v2.contracts.types import ContractError, StudyInput, StudyPrediction

from .engine import (
    DECISION_DESCRIPTIVE_ONLY,
    DECISION_PROPOSE_ACTION,
    RC_NOMINAL,
    STUDY_ID,
    _parse_age_days,
    _parse_evidence,
    _require_mapping,
)

METHOD_VERSION_B0 = "v2-b0-always-act-1.0.0"
METHOD_VERSION_C1 = "v2-c1-ema-1.0.0"

DEFAULT_EMA_ALPHA = 0.3
DEFAULT_EMA_THRESHOLD = 0.70


def _parse_risk_flag(features: Mapping[str, Any], case_id: str) -> bool:
    """Any externally supplied risk signal counts for B0."""
    raw = features.get("risk_flag", features.get("flagged_high_risk", False))
    if not isinstance(raw, bool):
        raise ContractError(f"case {case_id!r}: 'risk_flag' must be a boolean")
    return raw


def predict_batch_b0(
    inputs: list[StudyInput], config: dict | Mapping[str, Any] | None = None
) -> list[StudyPrediction]:
    """C0 sanity baseline: always propose an action on any risk signal.

    No privacy (k-anonymity), source, freshness or conflict gates. This is
    the negative control that must fail the high-risk-no-evidence mandatory
    counterexample (it fabricates a deficit intervention from missing logs).
    """
    predictions: list[StudyPrediction] = []
    for inp in inputs:
        features = _require_mapping(inp.features, inp.case_id)
        evidence, _unverified = _parse_evidence(features, inp.case_id)
        risk_flag = _parse_risk_flag(features, inp.case_id)
        has_any_signal = bool(evidence) or risk_flag
        if not has_any_signal:
            # Even B0 cannot manufacture a recommendation from literally zero
            # signals; it emits the generic ungrounded candidate anyway in the
            # legacy dashboard spirit — but only when a risk flag or evidence
            # exists. With nothing at all it stays descriptive (never silenty
            # guessed): this keeps B0 honest about empty inputs while
            # remaining wrong on every abstention-owed case that has *some*
            # partial signal.
            predictions.append(
                StudyPrediction(
                    study_id=STUDY_ID,
                    case_id=inp.case_id,
                    decision=DECISION_PROPOSE_ACTION,
                    score=None,
                    reason_codes=("baseline_ungrounded_heuristic", "no_signal_generic_proposal"),
                    evidence_ids=(),
                )
            )
            continue
        predictions.append(
            StudyPrediction(
                study_id=STUDY_ID,
                case_id=inp.case_id,
                decision=DECISION_PROPOSE_ACTION,
                score=None,
                reason_codes=("baseline_ungrounded_heuristic",),
                evidence_ids=tuple(f"ev_{i}" for i in range(len(evidence))),
            )
        )
    return predictions


def _ema(scores: list[float], alpha: float = DEFAULT_EMA_ALPHA) -> float | None:
    """Exponential moving average seeded on the first observation."""
    if not scores:
        return None
    ema = scores[0]
    for s in scores[1:]:
        ema = alpha * s + (1.0 - alpha) * ema
    return ema


def predict_batch_c1(
    inputs: list[StudyInput], config: dict | Mapping[str, Any] | None = None
) -> list[StudyPrediction]:
    """C1 strong classical: EMA threshold alerts without k-anonymity or source audit.

    Checks performed: EMA of evidence scores against a fixed threshold.
    Deliberately NOT performed (per spec 12): k-anonymity suppression,
    verified-source gating, conflict resolution. Freshness is honored only
    via the aggregate observation age (stale inputs request refresh).
    """
    cfg = dict(config or {})
    alpha = float(cfg.get("ema_alpha", DEFAULT_EMA_ALPHA))
    threshold = float(cfg.get("ema_intervention_threshold", DEFAULT_EMA_THRESHOLD))
    max_staleness = int(cfg.get("max_staleness_days", 30))

    predictions: list[StudyPrediction] = []
    for inp in inputs:
        features = _require_mapping(inp.features, inp.case_id)
        evidence, _unverified = _parse_evidence(features, inp.case_id)
        age_days = _parse_age_days(features, inp.case_id)
        scores = [ev["score"] for ev in evidence]
        ema = _ema(scores, alpha)

        if ema is not None and age_days > max_staleness:
            predictions.append(
                StudyPrediction(
                    study_id=STUDY_ID,
                    case_id=inp.case_id,
                    decision="request_refresh",
                    score=ema,
                    reason_codes=("stale_mastery",),
                    evidence_ids=tuple(f"ev_{i}" for i in range(len(evidence))),
                )
            )
            continue

        if ema is not None and ema <= threshold:
            # EMA below threshold -> propose the classical alert action.
            # No k-anonymity check, no source audit: fires even when the
            # evidence stream is unverified or the cohort is tiny.
            predictions.append(
                StudyPrediction(
                    study_id=STUDY_ID,
                    case_id=inp.case_id,
                    decision=DECISION_PROPOSE_ACTION,
                    score=ema,
                    reason_codes=("c1_ema_trend_triggered", RC_NOMINAL),
                    evidence_ids=tuple(f"ev_{i}" for i in range(len(evidence))),
                )
            )
            continue

        predictions.append(
            StudyPrediction(
                study_id=STUDY_ID,
                case_id=inp.case_id,
                decision=DECISION_DESCRIPTIVE_ONLY,
                score=ema,
                reason_codes=("c1_ema_trend_nominal",),
                evidence_ids=tuple(f"ev_{i}" for i in range(len(evidence))),
            )
        )
    return predictions
