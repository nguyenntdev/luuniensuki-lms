"""Runner alias: LN-06 ablation A1 (budget check disabled).

Matrix method id ``ablations_a1`` resolves to ``predict_batch`` here.
"""
from __future__ import annotations

from .ablations import a1_predict_one as predict_one
from .ablations import a1_solve, predict_batch_a1

STUDY_ID = "LN-06"
METHOD_ID = "ablations_a1"


def predict_batch(inputs: list, config: dict | None = None) -> list:
    return predict_batch_a1(inputs, config)
