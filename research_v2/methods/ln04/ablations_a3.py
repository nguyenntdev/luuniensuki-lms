"""Runner alias: LN-04 ablation A3 (no injection filter)."""
from __future__ import annotations

from .ablations import A3_METHOD_ID, ABLATION_VERSION, predict_batch_a3, predict_one_a3

METHOD_ID = A3_METHOD_ID
METHOD_VERSION = ABLATION_VERSION

predict_batch = predict_batch_a3
predict_one = predict_one_a3

__all__ = ["METHOD_ID", "METHOD_VERSION", "predict_batch", "predict_one"]
