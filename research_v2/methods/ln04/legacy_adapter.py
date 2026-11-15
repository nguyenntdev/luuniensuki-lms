"""Adapter from the legacy LN-04 engine to the research_v2 contract.

The legacy engine (``backend/domain/scaffolding_policy.py`` via
``research/integrations/ln04.py``) emits legacy decision labels. This adapter
translates them deterministically onto the frozen contract label space using
``labels.map_legacy_decision`` and validates each output decision. It is an
inference-sealed reader of legacy behavior only: no oracle, gold or fault
material passes through.
"""
from __future__ import annotations

from typing import Any, Mapping

from research_v2.contracts.label_space import LabelSpaceError
from research_v2.contracts.types import ContractError, StudyInput, StudyPrediction

from .labels import STUDY_ID, map_legacy_decision

ADAPTER_VERSION = "ln04-legacy-adapter-v1.0.0"

#: Legacy engine decision field(s), in priority order.
_LEGACY_DECISION_KEYS = ("decision", "scaffolding_decision", "policy_decision")


def _extract_legacy_decision(result: Mapping[str, Any]) -> str:
    for key in _LEGACY_DECISION_KEYS:
        value = result.get(key)
        if isinstance(value, str) and value:
            return value
        if hasattr(value, "value") and isinstance(getattr(value, "value"), str):
            return str(value.value)
    raise ContractError("legacy engine result carries no decision field")


def adapt_result(case_id: str, result: Mapping[str, Any]) -> StudyPrediction:
    legacy = _extract_legacy_decision(result)
    decision = map_legacy_decision(legacy)
    reason_codes = tuple(str(r) for r in (result.get("reason_codes") or ()))
    return StudyPrediction(
        study_id=STUDY_ID,
        case_id=case_id,
        decision=decision,
        score=None,
        reason_codes=("legacy_engine",) + reason_codes,
        evidence_ids=tuple(
            str(s) for s in ((result.get("details") or {}).get("cited_source_ids") or ())
        ),
    )


def predict_one(inp: StudyInput, config: Mapping[str, Any] | None = None) -> StudyPrediction:
    """Run the legacy engine on masked contract features and map the result.

    Import is deferred so environments without the legacy research package can
    still import the rest of the LN-04 method package.
    """
    try:
        from research.integrations.ln04 import run_policy
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise ContractError(
            "legacy LN-04 engine unavailable; legacy_adapter requires research.integrations.ln04"
        ) from exc

    from research_v2.contracts.input_masking import mask_case_input

    try:
        scenario = mask_case_input({"input": dict(inp.features)})
    except ContractError as exc:
        raise ContractError(f"case {inp.case_id!r}: {exc}") from exc
    result = run_policy(scenario, mode="intervention", config=dict(config or {}))
    return adapt_result(inp.case_id, result)


def predict_batch(
    inputs: list[StudyInput], config: Mapping[str, Any] | None = None
) -> list[StudyPrediction]:
    return [predict_one(inp, config) for inp in inputs]


__all__ = [
    "ADAPTER_VERSION",
    "adapt_result",
    "predict_batch",
    "predict_one",
    "LabelSpaceError",
]
