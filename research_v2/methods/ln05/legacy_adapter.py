"""LN-05 read-only adapter over the legacy research engine.

Wraps ``research.integrations.ln05.run_policy`` (which delegates to
``research.gamification.mastery_reward_policy``) with:
- deep-copy isolation: the legacy callable never sees our feature dict identity;
- total legacy->V2 label translation (unknown labels raise ``DecisionError``);
- no writes to legacy modules, database, network or ``research_artifacts/``.

If the legacy import fails the adapter reports ``BLOCKED`` via
``LegacyLn05Adapter.available`` instead of fabricating predictions.
"""
from __future__ import annotations

import copy
from typing import Any, Mapping

from research_v2.contracts.types import StudyInput, StudyPrediction
from research_v2.methods.ln05.labels import DecisionError, to_v2_decision


def _load_legacy():
    try:
        from research.integrations.ln05 import run_policy
    except Exception as exc:  # pragma: no cover - depends on legacy tree
        raise ImportError(f"BLOCKED: legacy LN-05 adapter unavailable: {exc}") from exc
    return run_policy


class LegacyLn05Adapter:
    """Stateless read-only bridge to the legacy mastery reward policy."""

    method_id = "legacy_adapter"
    method_version = "1.0.0"

    def __init__(self) -> None:
        self._run_policy = None

    @property
    def available(self) -> bool:
        try:
            _load_legacy()
        except ImportError:
            return False
        return True

    def _policy(self):
        if self._run_policy is None:
            self._run_policy = _load_legacy()
        return self._run_policy

    def run(self, features: Mapping[str, Any], *, mode: str, config: Mapping[str, Any] | None = None) -> dict[str, Any]:
        result = self._policy()(copy.deepcopy(dict(features)), mode=mode, config=dict(config or {}))
        if "decision" not in result:
            raise DecisionError(f"legacy adapter returned no decision: {result!r}")
        result["decision"] = to_v2_decision(str(result["decision"]))
        return result

    def predict_one(self, inp: StudyInput, *, mode: str = "intervention", config: Mapping[str, Any] | None = None) -> StudyPrediction:
        result = self.run(inp.features, mode=mode, config=config)
        return StudyPrediction(
            study_id=inp.study_id,
            case_id=inp.case_id,
            decision=str(result["decision"]),
            score=result.get("score"),
            reason_codes=tuple(str(rc) for rc in result.get("reason_codes", ())),
            evidence_ids=tuple(str(ev) for ev in result.get("evidence_ids", ())),
        )


def run_legacy_policy(
    features: Mapping[str, Any],
    *,
    mode: str = "intervention",
    config: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Convenience wrapper returning the translated legacy result dict."""
    return LegacyLn05Adapter().run(features, mode=mode, config=config)
