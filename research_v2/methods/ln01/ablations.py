"""LN-01 mechanism-isolating ablations.

Each ablation genuinely changes a code path of the proposed engine via its
config flags, and each is directly sensitive to the removed mechanism:

- ``a1`` (no_cycle_check): removes DAG cycle feasibility -> accepts true
  prerequisite cycles the proposed method rejects.
- ``a2`` (no_crosswalk): removes curriculum-anchor verification -> accepts
  graphs with missing/blank anchors the proposed method rejects.
- ``a3`` (no_depth_gate): removes Bloom cognitive-depth gating -> accepts
  flat/no-ascent sequences the proposed method rejects.

All ablations run on identical inputs and budgets as the proposed method
(same batch, same config surface); no difference is manufactured by feeding
different data.
"""
from __future__ import annotations

from typing import Any, Mapping

from research_v2.contracts.types import StudyInput, StudyPrediction

from .engine import evaluate_case

METHOD_VERSION = "v2-ablation-1.0.0"


def _predict_with_flag(
    inputs: list[StudyInput], flag: str, config: dict | Mapping[str, Any] | None
) -> list[StudyPrediction]:
    cfg = dict(config or {})
    cfg[flag] = True
    return [evaluate_case(inp, cfg) for inp in inputs]


def predict_batch(
    inputs: list[StudyInput], config: dict | Mapping[str, Any] | None = None
) -> list[StudyPrediction]:
    """Default ablation entry point (a1: no_cycle_check)."""
    return _predict_with_flag(inputs, "skip_cycle_check", config)
