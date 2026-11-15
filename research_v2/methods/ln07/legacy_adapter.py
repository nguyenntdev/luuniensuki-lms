"""LN-07 legacy engine adapter (read-only) over ``research/udl``.

Wraps the observed engine at the pinned source snapshot via
``research.integrations.ln07.run_policy``. The legacy scenario is deep-copied
before dispatch so the adapter cannot mutate the caller's fixture, and the
legacy response is mapped onto the V2 typed prediction ABI.

The legacy engine's decision labels match the T3 gold oracle vocabulary
(``choose_feasible_modality``, ``choose_accessible_fallback``, ...) and pass
through strict validation in ``labels.map_decision``; unknown labels raise
typed errors rather than being coerced.
"""
from __future__ import annotations

import copy
from typing import Any, Mapping

from .dataset import DatasetError
from .labels import build_prediction

STUDY_ID = "LN-07"
METHOD_ID = "legacy_adapter"
METHOD_VERSION = "ln07-legacy-adapter-v1.0"

_LEGACY_POLICY = None
_LEGACY_IMPORT_ERROR: str | None = None


def _legacy_run_policy():
    """Import the read-only legacy callable once; report BLOCKED on failure."""
    global _LEGACY_POLICY, _LEGACY_IMPORT_ERROR
    if _LEGACY_POLICY is not None:
        return _LEGACY_POLICY
    try:
        from research.integrations.ln07 import run_policy as fn
    except Exception as exc:  # pragma: no cover - import environment issue
        _LEGACY_IMPORT_ERROR = f"{type(exc).__name__}: {exc}"
        raise DatasetError(
            "LN-07 legacy adapter BLOCKED: cannot import "
            f"research.integrations.ln07.run_policy ({_LEGACY_IMPORT_ERROR})"
        ) from exc
    _LEGACY_POLICY = fn
    return fn


def run_legacy_intervention(
    scenario_input: Mapping[str, Any], config: Mapping[str, Any] | None = None
) -> dict[str, Any]:
    """Dispatch a deep copy of the scenario to the legacy policy (intervention mode)."""
    run_policy = _legacy_run_policy()
    payload = copy.deepcopy(dict(scenario_input))
    return run_policy(payload, mode="intervention", config=dict(config or {}))


def predict_one(inp: Any, config: Mapping[str, Any] | None = None) -> Any:
    from research_v2.contracts.types import StudyInput

    if not isinstance(inp, StudyInput):
        raise DatasetError(f"predict_one expects StudyInput, got {type(inp).__name__}")
    cfg = dict(config or {})
    raw = run_legacy_intervention(inp.features, cfg)
    decision = raw.get("decision")
    if not isinstance(decision, str) or not decision:
        raise DatasetError(f"case {inp.case_id!r}: legacy adapter returned no decision")
    return build_prediction(
        case_id=inp.case_id,
        decision=decision,
        reason_codes=tuple(str(r) for r in raw.get("reason_codes", ())),
        evidence_ids=(),
        score=1.0 if raw.get("task_feasible") else 0.0,
    )


def predict_batch(inputs: list, config: dict | None = None) -> list:
    cfg = dict(config or {})
    out = []
    for i, inp in enumerate(inputs):
        try:
            out.append(predict_one(inp, cfg))
        except DatasetError:
            raise
        except Exception as exc:
            raise DatasetError(f"input[{i}] case {getattr(inp, 'case_id', '?')!r}: {exc}") from exc
    return out
