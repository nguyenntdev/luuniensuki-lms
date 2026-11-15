"""Runner alias: A1 ablation - remove the prerequisite gate."""
from .core import MethodContractError
from .ablations import (
    METHOD_VERSION_A1,
    predict_a1_batch,
    predict_one_a1,
)


def predict_batch(inputs, config=None):
    if not isinstance(inputs, list):
        raise MethodContractError("predict_batch expects a list of StudyInput")
    return predict_a1_batch(inputs, config)


__all__ = [
    "MethodContractError",
    "METHOD_VERSION_A1",
    "predict_a1_batch",
    "predict_batch",
    "predict_one_a1",
]
