"""Runner alias: method_id ``ablations_a2`` -> ablation without anchor (crosswalk) check."""
from research_v2.contracts.types import StudyInput, StudyPrediction

from .ablations import _predict_with_flag


def predict_batch(
    inputs: list[StudyInput], config: dict | None = None
) -> list[StudyPrediction]:
    return _predict_with_flag(inputs, "skip_anchor_check", config)
