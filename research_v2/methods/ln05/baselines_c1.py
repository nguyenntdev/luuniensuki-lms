"""Runner alias: C1 strong classical baseline (timestamp-windowed streak)."""
from research_v2.methods.ln05.baselines import B1_METHOD_ID as METHOD_ID
from research_v2.methods.ln05.baselines import BASELINE_METHOD_VERSION as METHOD_VERSION
from research_v2.methods.ln05.baselines import predict_batch_c1 as predict_batch

__all__ = ["METHOD_ID", "METHOD_VERSION", "predict_batch"]
