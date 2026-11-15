"""Legacy engine adapter for LN-02 (read-only bridge to the audited engine).

The legacy production engine lives at ``research/adaptive/prerequisite_policy.py``
with the callable adapter ``research/integrations/ln02.py``. This module wraps
it for research-v2 comparison runs:

- sends a **deep copy** of the masked inference-time features (no side
  effects on shared state),
- never routes by ``case_id`` / ``fault_id``,
- never reads oracle or gold material,
- maps the legacy result dictionary onto the frozen ``StudyPrediction`` type,
- raises a typed ``LegacyEngineBlockedError`` (a ``ContractError``) if the
  legacy module cannot be imported rather than fabricating a fallback.

The legacy engine is *not* used by the runner matrix by default; it exists
so reviewers can diff new-method behaviour against the audited incumbent on
identical inputs (golden-case QA, spec 05.C).
"""
from __future__ import annotations

from typing import Any, Mapping

from research_v2.contracts.types import ContractError, StudyInput, StudyPrediction

from .core import (
    METHOD_VERSION_CORE,
    RC_CYCLE,
    RC_ELIGIBLE,
    RC_INSUFFICIENT_DATA,
    RC_INVALID_SCORE,
    RC_PREREQ_NOT_MET,
    STUDY_ID,
    _features,
    build_prediction,
    task_evidence_ids,
)

METHOD_VERSION_LEGACY = f"{METHOD_VERSION_CORE}+legacy-adapter"

_REASON_TO_CODE: dict[str, str] = {
    "ELIGIBLE_RECOMMENDATION": RC_ELIGIBLE,
    "PREREQUISITE_NOT_MET": RC_PREREQ_NOT_MET,
    "INSUFFICIENT_COMPETENCY_DATA": RC_INSUFFICIENT_DATA,
    "INVALID_SCORE_RANGE": RC_INVALID_SCORE,
    "CYCLE_DETECTED": RC_CYCLE,
}

# Legacy decisions map 1:1 onto the frozen LN-02 label space.
_KNOWN_DECISIONS = frozenset(
    {
        "recommend_eligible",
        "remediate_first",
        "abstain_insufficient_data",
        "reject_cycle",
        "reject_invalid_score",
    }
)


class LegacyEngineBlockedError(ContractError):
    """Raised when the legacy engine is unavailable or returns junk."""


def _load_legacy_evaluate():
    try:
        from research.adaptive.prerequisite_policy import (  # noqa: PLC0415
            evaluate_policy,
        )
    except Exception as exc:  # pragma: no cover - exercised via typed raise
        raise LegacyEngineBlockedError(
            f"legacy LN-02 engine unavailable (import failed): {exc}"
        ) from exc
    return evaluate_policy


def predict_one_legacy(inp: StudyInput, config: Mapping[str, Any] | None = None) -> StudyPrediction:
    """Evaluate the legacy engine on a deep copy of the masked features."""
    features = _features(inp)
    evaluate_policy = _load_legacy_evaluate()
    scenario: dict[str, Any] = dict(features)
    # Deep-copy nested mappings so the legacy engine cannot mutate shared state.
    for key, value in list(scenario.items()):
        if isinstance(value, dict):
            scenario[key] = _deep_copy(value)
    try:
        result = evaluate_policy(scenario, mode="intervention", config=dict(config or {}))
    except Exception as exc:
        raise LegacyEngineBlockedError(
            f"case {inp.case_id!r}: legacy engine raised {type(exc).__name__}: {exc}"
        ) from exc
    if not isinstance(result, Mapping):
        raise LegacyEngineBlockedError(
            f"case {inp.case_id!r}: legacy engine returned {type(result).__name__}, expected mapping"
        )
    decision = result.get("decision")
    if decision not in _KNOWN_DECISIONS:
        raise LegacyEngineBlockedError(
            f"case {inp.case_id!r}: legacy decision {decision!r} outside LN-02 label space"
        )
    raw_reasons = result.get("reason_codes") or []
    reason_codes = tuple(
        _REASON_TO_CODE.get(str(code), str(code)) for code in raw_reasons
    )
    return build_prediction(
        inp,
        decision=str(decision),
        reason_codes=reason_codes,
        score=result.get("competency_coverage"),
        evidence_ids=task_evidence_ids(features),
        method_version=METHOD_VERSION_LEGACY,
    )


def _deep_copy(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _deep_copy(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_deep_copy(v) for v in value]
    if isinstance(value, tuple):
        return tuple(_deep_copy(v) for v in value)
    return value


def predict_batch(
    inputs: list[StudyInput], config: Mapping[str, Any] | None = None
) -> list[StudyPrediction]:
    """Batch entrypoint wrapping the legacy engine (mode: intervention)."""
    return [predict_one_legacy(inp, config or {}) for inp in inputs]


__all__ = [
    "LegacyEngineBlockedError",
    "METHOD_VERSION_LEGACY",
    "predict_batch",
    "predict_one_legacy",
]
