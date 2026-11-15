"""LN-08 legacy engine adapter (read-only provenance bridge).

Bridges the observed legacy engine (``research/feedback/diagnostic_feedback.py``
via ``research/integrations/ln08.py`` ``run_policy`` mode ``intervention``) to
the V2 ABI. Used for provenance comparison only - the V2 proposed method
re-implements the diagnostic chain natively and never imports legacy decision
code at inference time.

The legacy engine emits native labels including ``preserve_semantics`` and
``abstain``; the adapter fail-closes with a typed error when it emits anything
outside the native vocabulary. The native ``abstain`` label is surfaced
unchanged (the contract mapping lives in ``labels.py``, evaluator-side).
"""
from __future__ import annotations

from typing import Any, Iterable, Mapping

from research_v2.contracts.types import StudyInput, StudyPrediction

from .dataset import DatasetError
from .labels import NATIVE_DECISIONS, STUDY_ID, native_decision

STUDY_ID = "LN-08"
METHOD_VERSION = "ln08-legacy-adapter-v1.0"


class LegacyEngineBlockedError(DatasetError):
    """Raised when the legacy engine is unavailable or emits junk."""


def legacy_decide(
    features: Mapping[str, Any], mode: str = "intervention", config: Mapping[str, Any] | None = None
) -> dict[str, Any]:
    """Call the legacy ``run_policy`` and validate its decision label.

    Returns the raw legacy result dict. Raises LegacyEngineBlockedError when
    the legacy engine emits an unknown label (fail-closed provenance check).
    """
    from research.integrations.ln08 import run_policy  # imported lazily; provenance-only

    result = run_policy(dict(features), mode=mode, config=dict(config or {}))
    decision = result.get("decision")
    if decision not in NATIVE_DECISIONS:
        raise LegacyEngineBlockedError(
            f"{STUDY_ID}: legacy engine emitted unknown decision {decision!r}"
        )
    native_decision(decision)
    return result


def predict_batch_legacy(
    inputs: Iterable[StudyInput], config: Mapping[str, Any] | None = None
) -> list[StudyPrediction]:
    """ABI-compatible adapter around the legacy intervention policy."""
    cfg = dict(config or {})
    mode = cfg.get("legacy_mode", "intervention")
    preds: list[StudyPrediction] = []
    for i, inp in enumerate(inputs):
        if not isinstance(inp, StudyInput):
            raise LegacyEngineBlockedError(
                f"input[{i}] expects StudyInput, got {type(inp).__name__}"
            )
        feats = inp.features
        if not isinstance(feats, Mapping):
            raise LegacyEngineBlockedError(
                f"{STUDY_ID} case {inp.case_id!r}: features must be a mapping"
            )
        result = legacy_decide(feats, mode=mode, config=cfg.get("legacy_config", {}))
        decision = result["decision"]
        evidence = feats.get("evidence") or {}
        preds.append(
            StudyPrediction(
                study_id=STUDY_ID,
                case_id=inp.case_id,
                decision=decision,
                score=None,
                reason_codes=tuple(str(rc) for rc in result.get("reason_codes", ())),
                evidence_ids=(
                    str(evidence.get("claim_id", "")),
                    str(evidence.get("source_id", "")),
                ),
            )
        )
    return preds


#: ABI-standard alias so the adapter can be exercised like any matrix method.
predict_batch = predict_batch_legacy
