"""Runner alias: B0 naive aggregate-score baseline (C0, SANITY_ONLY)."""
from .core import MethodContractError
from .baselines import (
    B0_STATUS,
    METHOD_VERSION_B0,
    predict_b0_batch,
    predict_one_b0,
)


def predict_batch(inputs, config=None):
    if not isinstance(inputs, list):
        raise MethodContractError("predict_batch expects a list of StudyInput")
    return predict_b0_batch(inputs, config)


__all__ = [
    "MethodContractError",
    "B0_STATUS",
    "METHOD_VERSION_B0",
    "predict_b0_batch",
    "predict_batch",
    "predict_one_b0",
]
