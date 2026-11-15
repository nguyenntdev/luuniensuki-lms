"""LN-03 mechanism-isolating ablations of the proposed dual-mode policy.

Each ablation disables exactly one mechanism of ``proposed.decide`` while
holding input features, budget and metric target fixed:

- ``ablations_a1``: no verified-source gate (a1_no_source_gate)
- ``ablations_a2``: no fact-stability gate (a2_no_fact_stability)
- ``ablations_a3``: no due-date scheduling (a3_no_due_scheduling)

Ablation flags are explicit config, not separate decision functions; the
mechanism under test is the only difference from the proposed method.
"""
from __future__ import annotations

from typing import Any, Iterable, Mapping

from research_v2.contracts.types import StudyInput, StudyPrediction

from . import proposed
from .errors import PolicyConfigError
from .labels import STUDY_ID

ABLATION_FLAGS: Mapping[str, str] = {
    "ablations_a1": "source_gate_enabled",
    "ablations_a2": "fact_stability_enabled",
    "ablations_a3": "due_scheduling_enabled",
}

ABLATION_LABELS: Mapping[str, str] = {
    "ablations_a1": "a1_no_source_gate",
    "ablations_a2": "a2_no_fact_stability",
    "ablations_a3": "a3_no_due_scheduling",
}


def ablation_config(method_id: str, overrides: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Build config for one ablation: exactly one proposed flag disabled."""
    flag = ABLATION_FLAGS.get(method_id)
    if flag is None:
        raise PolicyConfigError(f"{STUDY_ID}: unknown ablation method_id {method_id!r}")
    cfg: dict[str, Any] = {flag: False}
    for key, value in (overrides or {}).items():
        if key in proposed.DEFAULT_CONFIG and key != flag:
            cfg[key] = value
    return cfg


def make_predict_batch(method_id: str):
    """Return an ABI-compatible ``predict_batch`` bound to one ablation."""

    def predict_batch(
        inputs: Iterable[StudyInput], config: Mapping[str, Any] | None = None
    ) -> list[StudyPrediction]:
        cfg = ablation_config(method_id, config or {})
        preds = proposed.predict_batch(inputs, cfg)
        return [
            StudyPrediction(
                study_id=p.study_id,
                case_id=p.case_id,
                decision=p.decision,
                score=p.score,
                reason_codes=tuple(p.reason_codes) + (ABLATION_LABELS[method_id],),
                evidence_ids=p.evidence_ids,
            )
            for p in preds
        ]

    predict_batch.__name__ = f"predict_batch[{method_id}]"
    predict_batch.__qualname__ = predict_batch.__name__
    predict_batch.__doc__ = f"LN-03 ablation {ABLATION_LABELS[method_id]}: {ABLATION_FLAGS[method_id]}=False."
    return predict_batch


predict_batch_a1 = make_predict_batch("ablations_a1")
predict_batch_a2 = make_predict_batch("ablations_a2")
predict_batch_a3 = make_predict_batch("ablations_a3")
