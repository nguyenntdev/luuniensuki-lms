"""Runner alias: LN-04 B0 naive direct-answer baseline."""
from __future__ import annotations

from .baselines import B0_METHOD_ID, B0_METHOD_VERSION, predict_batch_b0, predict_one_b0

METHOD_ID = B0_METHOD_ID
METHOD_VERSION = B0_METHOD_VERSION

predict_batch = predict_batch_b0
predict_one = predict_one_b0

__all__ = ["METHOD_ID", "METHOD_VERSION", "predict_batch", "predict_one"]
