"""Runner alias: LN-08 ablation A2 (negation parsing disabled).

Matrix method id ``ablations_a2`` resolves to ``predict_batch`` here.
"""
from __future__ import annotations

from .ablations import a2_predict_one as predict_one
from .ablations import a2_solve, predict_batch_a2

STUDY_ID = "LN-08"
METHOD_ID = "ablations_a2"


def predict_batch(inputs: list, config: dict | None = None) -> list:
    return predict_batch_a2(inputs, config)
