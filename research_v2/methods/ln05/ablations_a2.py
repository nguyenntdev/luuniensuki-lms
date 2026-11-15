"""Runner alias: A2 ablation (anti-replay disabled)."""
from research_v2.methods.ln05.ablations import ABLATION_VERSION as METHOD_VERSION
from research_v2.methods.ln05.ablations import A2_METHOD_ID, make_predict_batch

METHOD_ID = A2_METHOD_ID
predict_batch = make_predict_batch(A2_METHOD_ID)

__all__ = ["METHOD_ID", "METHOD_VERSION", "predict_batch"]
