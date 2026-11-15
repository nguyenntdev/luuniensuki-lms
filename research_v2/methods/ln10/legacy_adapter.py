"""LN-10 legacy engine adapter (read-first provenance bridge).

Bridges the observed legacy engine (``research/srl/project_state_machine.py``
via ``research/integrations/ln10.py`` ``run_policy``) to the V2 ABI. Used for
provenance comparison only — the V2 proposed method re-implements the SRL
cycle natively and never imports legacy decision code at inference time.

Documented legacy limitation preserved verbatim (not fixed here, belongs to
the legacy surface): the legacy engine's optimistic concurrency check is a
plain compare-and-swap on ``expected_version``; when TWO conflicting offline
edits target the same current version, both pass the CAS and the legacy
engine silently applies whichever arrives first — no
``resolve_revision_conflict`` is emitted and no explicit concurrent-edit set
is inspected. The V2 proposed policy adds the mandatory detector; this
adapter is the reference point demonstrating the gap.

If the legacy import fails the adapter raises a typed ``DatasetError``
(BLOCKED) instead of fabricating predictions.
"""
from __future__ import annotations

import copy
from typing import Any, Iterable, Mapping

from research_v2.contracts.types import StudyInput, StudyPrediction

from .dataset import DatasetError
from .labels import NATIVE_DECISIONS, STUDY_ID, build_prediction

METHOD_ID = "legacy_adapter"
METHOD_VERSION = "ln10-legacy-adapter-v1.0"


def _load_legacy():
    try:
        from research.integrations.ln10 import run_policy
    except Exception as exc:  # pragma: no cover - depends on legacy tree
        raise DatasetError(f"BLOCKED: legacy LN-10 adapter unavailable: {exc}") from exc
    return run_policy


def legacy_decide(
    features: Mapping[str, Any],
    *,
    mode: str = "intervention",
    config: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Call the legacy ``run_policy`` and validate its decision label.

    Returns the raw legacy result dict. The input is deep-copied so the
    legacy callable cannot mutate the caller's fixture. Raises
    ``DatasetError`` when the legacy engine emits an unknown label
    (fail-closed provenance check).
    """
    run_policy = _load_legacy()
    result = run_policy(copy.deepcopy(dict(features)), mode=mode, config=dict(config or {}))
    decision = result.get("decision")
    if decision not in NATIVE_DECISIONS:
        raise DatasetError(
            f"{STUDY_ID}: legacy engine emitted unknown decision {decision!r}"
        )
    return result


def predict_batch_legacy(
    inputs: Iterable[StudyInput], config: Mapping[str, Any] | None = None
) -> list[StudyPrediction]:
    """ABI-compatible adapter around the legacy intervention policy."""
    cfg = dict(config or {})
    mode = str(cfg.get("legacy_mode", "intervention"))
    legacy_cfg = dict(cfg.get("legacy_config", {}))
    preds: list[StudyPrediction] = []
    for inp in inputs:
        if not isinstance(inp, StudyInput):
            raise DatasetError(f"predict_batch_legacy expects StudyInput, got {type(inp).__name__}")
        result = legacy_decide(inp.features, mode=mode, config=legacy_cfg)
        preds.append(
            build_prediction(
                case_id=inp.case_id,
                decision=str(result["decision"]),
                reason_codes=tuple(str(rc) for rc in result.get("reason_codes", ())),
                evidence_ids=(),
                score=1.0 if result.get("transition_applied") else 0.0,
            )
        )
    return preds


#: ABI-standard alias so the adapter can be exercised like any matrix method.
predict_batch = predict_batch_legacy
