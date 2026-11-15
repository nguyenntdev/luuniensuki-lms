"""Runner alias: LN-04 ablation A1 (no hint budget)."""
from __future__ import annotations

from .ablations import A1_METHOD_ID, ABLATION_VERSION, predict_batch_a1, predict_one_a1

METHOD_ID = A1_METHOD_ID
METHOD_VERSION = ABLATION_VERSION

predict_batch = predict_batch_a1
predict_one = predict_one_a1

__all__ = ["METHOD_ID", "METHOD_VERSION", "predict_batch", "predict_one"]
