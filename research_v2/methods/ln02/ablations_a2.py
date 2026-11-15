"""Runner alias: A2 ablation - disable calibrated abstention (impute 0)."""
from .core import MethodContractError
from .ablations import (
    METHOD_VERSION_A2,
    predict_a2_batch,
    predict_one_a2,
)


def predict_batch(inputs, config=None):
    if not isinstance(inputs, list):
        raise MethodContractError("predict_batch expects a list of StudyInput")
    return predict_a2_batch(inputs, config)


__all__ = [
    "MethodContractError",
    "METHOD_VERSION_A2",
    "predict_a2_batch",
    "predict_batch",
    "predict_one_a2",
]
