"""Legacy engine adapter for LN-09 (read-only comparability bridge).

Wraps the legacy policy engine ``research/teacher_analytics/intervention_rules.py``
(callable adapter ``research/integrations/ln09.py``) when it is importable,
exposing the same V2 ``predict_batch`` ABI. The legacy engine is treated as a
*comparator*, never as the source of V2 decisions. This adapter is recorded as
``ORIGINAL_CODE_VERIFIED`` for legacy-behavior reproduction only.

Behavior notes:
- sends a **deep copy** of the masked inference-time features (no side effects),
- never routes by ``case_id`` / ``fault_id``,
- never reads oracle or gold material,
- maps the legacy result dictionary onto the frozen ``StudyPrediction`` type;
  legacy decisions map 1:1 into the gold-compatible vocabulary already used by
  the V2 engine, unknown decisions raise a typed ``ContractError``,
- raises a typed ``ContractError`` if the legacy module cannot be imported
  rather than fabricating a silent fallback.

The legacy engine is *not* used by the runner matrix by default; it exists so
reviewers can diff new-method behaviour against the audited incumbent on
identical inputs (golden-case QA, spec 05.C).
"""
from __future__ import annotations

import copy
from typing import Any, Mapping

from research_v2.contracts.types import ContractError, StudyInput, StudyPrediction

from .engine import STUDY_ID, VALID_DECISIONS

METHOD_VERSION = "v2-legacy-adapter-1.0.0"

try:  # pragma: no cover - exercised only when legacy package is present
    from research.teacher_analytics.intervention_rules import (  # type: ignore
        evaluate_intervention_rules,
    )

    _LEGACY_AVAILABLE = True
except Exception:  # pragma: no cover
    evaluate_intervention_rules = None  # type: ignore[assignment]
    _LEGACY_AVAILABLE = False


def predict_batch(
    inputs: list[StudyInput], config: dict | Mapping[str, Any] | None = None
) -> list[StudyPrediction]:
    if not _LEGACY_AVAILABLE:
        raise ContractError(
            "LN-09 legacy adapter: legacy engine "
            "'research.teacher_analytics.intervention_rules' is not importable; "
            "refusing to fabricate a fallback (typed failure, not silent default)."
        )
    cfg = dict(config or {})
    predictions: list[StudyPrediction] = []
    for inp in inputs:
        result = evaluate_intervention_rules(copy.deepcopy(dict(inp.features)), cfg)
        decision = str(result.get("decision", ""))
        if decision not in VALID_DECISIONS:
            raise ContractError(
                f"case {inp.case_id!r}: legacy adapter produced unknown decision {decision!r}"
            )
        predictions.append(
            StudyPrediction(
                study_id=STUDY_ID,
                case_id=inp.case_id,
                decision=decision,
                score=None,
                reason_codes=tuple(f"legacy:{rc}" for rc in result.get("reason_codes", [])),
                evidence_ids=(),
            )
        )
    return predictions
