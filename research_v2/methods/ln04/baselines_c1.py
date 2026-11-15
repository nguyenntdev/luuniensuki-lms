"""Runner alias: LN-04 C1 SIMULATED generic-LLM proxy baseline.

Scientific labeling: this is a rule-based heuristic proxy that simulates the
failure modes of an unconstrained generic LLM tutor. It is NOT a real LLM and
its outputs must never be reported as real-LLM evaluation. All reason codes are
prefixed with ``simulated``.
"""
from __future__ import annotations

from .baselines import C1_METHOD_ID, C1_METHOD_VERSION, C1_SIMULATED, predict_batch_c1, predict_one_c1

METHOD_ID = C1_METHOD_ID
METHOD_VERSION = C1_METHOD_VERSION
SIMULATED = C1_SIMULATED

predict_batch = predict_batch_c1
predict_one = predict_one_c1

__all__ = ["METHOD_ID", "METHOD_VERSION", "SIMULATED", "predict_batch", "predict_one"]
