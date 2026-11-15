"""Runner alias: LN-08 ablation A3 (source-link verification disabled).

Matrix method id ``ablations_a3`` resolves to ``predict_batch`` here.
"""
from __future__ import annotations

from .ablations import a3_predict_one as predict_one
from .ablations import a3_solve, predict_batch_a3

STUDY_ID = "LN-08"
METHOD_ID = "ablations_a3"


def predict_batch(inputs: list, config: dict | None = None) -> list:
    return predict_batch_a3(inputs, config)
