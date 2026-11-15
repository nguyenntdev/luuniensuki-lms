"""Runner alias: B0 sanity baseline (award on event count). SANITY_ONLY."""
from research_v2.methods.ln05.baselines import B0_METHOD_ID as METHOD_ID
from research_v2.methods.ln05.baselines import BASELINE_METHOD_VERSION as METHOD_VERSION
from research_v2.methods.ln05.baselines import predict_batch_b0 as predict_batch

__all__ = ["METHOD_ID", "METHOD_VERSION", "predict_batch"]
