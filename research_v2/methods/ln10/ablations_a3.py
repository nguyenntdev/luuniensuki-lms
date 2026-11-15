"""Runner alias: LN-10 ablation A3 (ownership check disabled).

Matrix method id ``ablations_a3`` resolves to ``predict_batch`` here.
"""
from __future__ import annotations

from .ablations import a3_solve, predict_batch_a3

STUDY_ID = "LN-10"
METHOD_ID = "ablations_a3"


def predict_batch(inputs: list, config: dict | None = None) -> list:
    return predict_batch_a3(inputs, config)
