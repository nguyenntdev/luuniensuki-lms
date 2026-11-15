"""Runner alias: A3 ablation - collapse mastery to one latent scalar."""
from .core import MethodContractError
from .ablations import (
    METHOD_VERSION_A3,
    predict_a3_batch,
    predict_one_a3,
)


def predict_batch(inputs, config=None):
    if not isinstance(inputs, list):
        raise MethodContractError("predict_batch expects a list of StudyInput")
    return predict_a3_batch(inputs, config)


__all__ = [
    "MethodContractError",
    "METHOD_VERSION_A3",
    "predict_a3_batch",
    "predict_batch",
    "predict_one_a3",
]
