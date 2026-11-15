"""Legacy adapter for LN-01 (optional comparability bridge).

Wraps the legacy engine ``research/spiral/progression_graph.py`` when it is
importable, exposing the same V2 ``predict_batch`` ABI. The legacy engine is
treated as a *comparator*, never as the source of V2 decisions: V2 corrects
two legacy bugs documented in ``engine.py`` (alternative-provider false
infeasibility; blank-anchor coverage). This adapter is therefore recorded as
``ORIGINAL_CODE_VERIFIED`` for legacy-behavior reproduction only.

If the legacy package is unavailable (e.g. pruned environment), the adapter
degrades to the V2 proposed engine and stamps the divergence in reason codes.
"""
from __future__ import annotations

from typing import Any, Mapping

from research_v2.contracts.types import StudyInput, StudyPrediction

from .engine import (
    DECISION_ACCEPT,
    RC_NOMINAL,
    STUDY_ID,
    evaluate_case,
)

METHOD_VERSION = "v2-legacy-adapter-1.0.0"

try:  # pragma: no cover - exercised only when legacy package is present
    from research.spiral.progression_graph import (  # type: ignore
        evaluate_spiral_progression_intervention,
    )

    _LEGACY_AVAILABLE = True
except Exception:  # pragma: no cover
    _LEGACY_AVAILABLE = False


def predict_batch(
    inputs: list[StudyInput], config: dict | Mapping[str, Any] | None = None
) -> list[StudyPrediction]:
    """Bridge legacy engine decisions into StudyPrediction rows.

    When the legacy engine is importable, its raw scenario dict (the masked
    ``inp.features``) is evaluated verbatim so its behavior is faithfully
    observable. Predictions keep the legacy decision string and legacy reason
    codes prefixed with ``legacy:`` for auditability.
    """
    predictions: list[StudyPrediction] = []
    for inp in inputs:
        if _LEGACY_AVAILABLE:
            result = evaluate_spiral_progression_intervention(
                dict(inp.features), dict(config or {})
            )
            predictions.append(
                StudyPrediction(
                    study_id=STUDY_ID,
                    case_id=inp.case_id,
                    decision=str(result.decision),
                    score=None,
                    reason_codes=tuple(f"legacy:{rc}" for rc in result.reason_codes),
                    evidence_ids=(),
                )
            )
        else:
            # Degrade to V2 engine, stamped as a documented divergence.
            pred = evaluate_case(inp, {})
            predictions.append(
                StudyPrediction(
                    study_id=STUDY_ID,
                    case_id=inp.case_id,
                    decision=pred.decision,
                    score=pred.score,
                    reason_codes=("legacy_unavailable_v2_divergence",) + pred.reason_codes,
                    evidence_ids=pred.evidence_ids,
                )
            )
    return predictions


__all__ = ["predict_batch", "DECISION_ACCEPT", "RC_NOMINAL", "METHOD_VERSION"]
