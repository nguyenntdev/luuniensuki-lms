"""Runner alias: method_id ``ablations_a3`` -> ablation without k-anonymity."""
from research_v2.contracts.types import StudyInput, StudyPrediction

from .ablations import _predict_with_flags


def predict_batch(
    inputs: list[StudyInput], config: dict | None = None
) -> list[StudyPrediction]:
    return _predict_with_flags(inputs, {"skip_k_anonymity": True}, config)
