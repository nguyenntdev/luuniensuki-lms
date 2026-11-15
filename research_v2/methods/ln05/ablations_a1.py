"""Runner alias: A1 ablation (xp-only, mastery proof disabled)."""
from research_v2.methods.ln05.ablations import ABLATION_VERSION as METHOD_VERSION
from research_v2.methods.ln05.ablations import A1_METHOD_ID, make_predict_batch

METHOD_ID = A1_METHOD_ID
predict_batch = make_predict_batch(A1_METHOD_ID)

__all__ = ["METHOD_ID", "METHOD_VERSION", "predict_batch"]
