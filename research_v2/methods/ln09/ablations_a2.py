"""Runner alias: method_id ``ablations_a2`` -> ablation without freshness/source checks."""
from research_v2.contracts.types import StudyInput, StudyPrediction

from .ablations import _predict_with_flags


def predict_batch(
    inputs: list[StudyInput], config: dict | None = None
) -> list[StudyPrediction]:
    return _predict_with_flags(
        inputs,
        {"skip_freshness_check": True, "skip_source_verification": True},
        config,
    )
