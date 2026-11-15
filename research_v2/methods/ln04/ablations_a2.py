"""Runner alias: LN-04 ablation A2 (no source gate)."""
from __future__ import annotations

from .ablations import A2_METHOD_ID, ABLATION_VERSION, predict_batch_a2, predict_one_a2

METHOD_ID = A2_METHOD_ID
METHOD_VERSION = ABLATION_VERSION

predict_batch = predict_batch_a2
predict_one = predict_one_a2

__all__ = ["METHOD_ID", "METHOD_VERSION", "predict_batch", "predict_one"]
