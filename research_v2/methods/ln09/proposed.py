"""LN-09 proposed policy: source-auditable teacher decision support.

Pure decision function over masked inference-time features. Enforces
INV-LN-09-01 (no deficit inference from missing logs), source traceability
(INV-LN-09-02), teacher override supremacy (INV-LN-09-03), k-anonymity
suppression (INV-LN-09-04) and explicit conflict visibility (INV-LN-09-05).
No oracle access.
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
    # Proposed configuration: every safeguard active.
    cfg.setdefault("skip_k_anonymity", False)
    cfg.setdefault("skip_source_verification", False)
    cfg.setdefault("skip_freshness_check", False)
    cfg.setdefault("disable_descriptive_fallback", False)
    return [evaluate_case(inp, cfg) for inp in inputs]
