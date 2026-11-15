"""LN-03 legacy engine adapter (read-first provenance bridge).

Bridges the observed legacy engine (``research/spaced_learning/dual_mode_policy.py``
via ``research/integrations/ln03.py`` ``run_policy``) to the V2 ABI. Used for
provenance comparison only — the V2 proposed method re-implements the rule
chain natively and never imports legacy decision code at inference time.
"""
from __future__ import annotations

from typing import Any, Iterable, Mapping

from research_v2.contracts.types import StudyInput, StudyPrediction

from .errors import ScenarioError
from .labels import NATIVE_DECISIONS, STUDY_ID, validate_native_decision
from .scenario import parse_case


def _features_dict(inp: StudyInput) -> dict[str, Any]:
    feats = inp.features
    if not isinstance(feats, Mapping):
        raise ScenarioError(f"{STUDY_ID} case {inp.case_id!r}: features must be a mapping")
    return dict(feats)


def legacy_decide(features: Mapping[str, Any], mode: str = "intervention", config: Mapping[str, Any] | None = None):
    """Call the legacy ``run_policy`` and validate its decision label.

    Returns the raw legacy result dict. Raises ScenarioError when the legacy
    engine emits an unknown label (fail-closed provenance check).
    """
    from research.integrations.ln03 import run_policy  # imported lazily; provenance-only

    result = run_policy(dict(features), mode=mode, config=dict(config or {}))
    decision = result.get("decision")
    if decision not in NATIVE_DECISIONS:
        raise ScenarioError(f"{STUDY_ID}: legacy engine emitted unknown decision {decision!r}")
    validate_native_decision(decision)
    return result


def predict_batch_legacy(
    inputs: Iterable[StudyInput], config: Mapping[str, Any] | None = None
) -> list[StudyPrediction]:
    """ABI-compatible adapter around the legacy intervention policy."""
    cfg = dict(config or {})
    mode = cfg.get("legacy_mode", "intervention")
    preds: list[StudyPrediction] = []
    for inp in inputs:
        feats = _features_dict(inp)
        result = legacy_decide(feats, mode=mode, config=cfg.get("legacy_config", {}))
        preds.append(
            StudyPrediction(
                study_id=STUDY_ID,
                case_id=inp.case_id,
                decision=result["decision"],
                score=1.0 if result["decision"] == "schedule_eligible" else None,
                reason_codes=tuple(result.get("reason_codes", ())),
                evidence_ids=(),
            )
        )
    return preds


#: ABI-standard alias so the adapter can be exercised like any matrix method.
predict_batch = predict_batch_legacy
