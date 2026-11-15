"""Runner alias: C1 Rasch 1-PL scalar-ability baseline (MATCHED_CLASSICAL)."""
from .core import MethodContractError
from .baselines import (
    C1_PROVENANCE,
    C1_STATUS,
    METHOD_VERSION_C1,
    predict_c1_batch,
    predict_one_c1,
)


def predict_batch(inputs, config=None):
    if not isinstance(inputs, list):
        raise MethodContractError("predict_batch expects a list of StudyInput")
    return predict_c1_batch(inputs, config)


__all__ = [
    "MethodContractError",
    "C1_PROVENANCE",
    "C1_STATUS",
    "METHOD_VERSION_C1",
    "predict_c1_batch",
    "predict_batch",
    "predict_one_c1",
]
