"""LN-06 legacy engine adapter (read-only) over ``research/heritage_trails``.

Wraps the observed engine at the pinned source snapshot via
``research.integrations.ln06.run_policy`` in ``intervention`` mode. The legacy
input is deep-copied before dispatch so the adapter cannot mutate the caller's
fixture, and the legacy response is mapped onto the V2 typed prediction ABI.

The legacy engine carries the documented all-providers bug: its diagnostic
``needed_stops`` pass sums every alternative provider of the same outcome, so
the mandatory case (A and B both provide outcome T at 40 min each, budget 50)
is falsely reported infeasible. That behaviour belongs to the legacy surface,
NOT to the V2 proposed policy; it is preserved here verbatim (mode
``intervention``) and is also reproducible through the ``ablations_a3``
runner alias for the regression demonstration.
"""
from __future__ import annotations

import copy
from typing import Any, Mapping

from .dataset import DatasetError
from .labels import build_prediction

STUDY_ID = "LN-06"
METHOD_ID = "legacy_adapter"
METHOD_VERSION = "ln06-legacy-adapter-v1.0"

_LEGACY_POLICY = None
_LEGACY_IMPORT_ERROR: str | None = None


def _legacy_run_policy():
    """Import the read-only legacy callable once; report BLOCKED on failure."""
    global _LEGACY_POLICY, _LEGACY_IMPORT_ERROR
    if _LEGACY_POLICY is not None:
        return _LEGACY_POLICY
    try:
        from research.integrations.ln06 import run_policy as fn
    except Exception as exc:  # pragma: no cover - import environment issue
        _LEGACY_IMPORT_ERROR = f"{type(exc).__name__}: {exc}"
        raise DatasetError(
            "LN-06 legacy adapter BLOCKED: cannot import "
            f"research.integrations.ln06.run_policy ({_LEGACY_IMPORT_ERROR})"
        ) from exc
    _LEGACY_POLICY = fn
    return fn


def legacy_features(stops: list[dict], available_stops: list[str], target_outcomes: list[str],
                    time_budget_minutes: int, checkpoint_claim_verified: bool) -> dict[str, Any]:
    """Build the exact legacy scenario_input shape (pure helper, no side effects)."""
    return {
        "stops": copy.deepcopy(stops),
        "available_stops": list(available_stops),
        "target_outcomes": list(target_outcomes),
        "time_budget_minutes": int(time_budget_minutes),
        "checkpoint_claim_verified": bool(checkpoint_claim_verified),
    }


def run_legacy_intervention(scenario_input: Mapping[str, Any], config: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Dispatch a deep copy of the scenario to the legacy policy (intervention mode)."""
    run_policy = _legacy_run_policy()
    payload = copy.deepcopy(dict(scenario_input))
    return run_policy(payload, mode="intervention", config=dict(config or {}))


def predict_one(inp: Any, config: Mapping[str, Any] | None = None) -> Any:
    from research_v2.contracts.types import StudyInput

    if not isinstance(inp, StudyInput):
        raise DatasetError(f"predict_one expects StudyInput, got {type(inp).__name__}")
    cfg = dict(config or {})
    features = inp.features
    try:
        scenario = legacy_features(
            stops=list(features["stops"]),
            available_stops=list(features["available_stops"]),
            target_outcomes=list(features["target_outcomes"]),
            time_budget_minutes=int(features["time_budget_minutes"]),
            checkpoint_claim_verified=bool(features["checkpoint_claim_verified"]),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise DatasetError(f"case {inp.case_id!r}: legacy scenario shape invalid: {exc}") from exc
    raw = run_legacy_intervention(scenario, cfg)
    decision = raw.get("decision")
    if not isinstance(decision, str):
        raise DatasetError(f"case {inp.case_id!r}: legacy adapter returned no decision")
    return build_prediction(
        case_id=inp.case_id,
        decision=decision,
        reason_codes=tuple(str(r) for r in raw.get("reason_codes", ())),
        evidence_ids=tuple(str(s) for s in raw.get("stop_sequence", ())),
        score=float(raw.get("route_cost", 0.0)),
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
