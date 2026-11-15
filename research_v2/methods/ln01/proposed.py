"""LN-01 proposed policy: constraint-aware spiral progression planning.

Implements the V2 correction of the legacy engine: alternative providers of
the same learning outcome are redundancy, not infeasibility. Cycles restricted
to alternative-provider (redundancy) edges are benign because a feasible route
exists by selecting one provider; cycles containing at least one progression
edge are true logical contradictions. See ``engine.py`` module docstring for
the full legacy-divergence rationale.

Pure decision function. No oracle access.
"""
from __future__ import annotations

from typing import Any, Mapping

from research_v2.contracts.types import StudyInput, StudyPrediction

from .engine import evaluate_case

METHOD_VERSION = "v2-proposed-1.0.0"


def predict_batch(
    inputs: list[StudyInput], config: dict | Mapping[str, Any] | None = None
) -> list[StudyPrediction]:
    cfg = dict(config or {})
    cfg.setdefault("skip_cycle_check", False)
    cfg.setdefault("skip_anchor_check", False)
    cfg.setdefault("skip_depth_gate", False)
    return [evaluate_case(inp, cfg) for inp in inputs]
