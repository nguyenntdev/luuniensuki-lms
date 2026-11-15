"""Runner alias: LN-10 ablation A2 (concurrency/conflict check disabled).

Matrix method id ``ablations_a2`` resolves to ``predict_batch`` here.
"""
from __future__ import annotations

from .ablations import a2_solve, predict_batch_a2

STUDY_ID = "LN-10"
METHOD_ID = "ablations_a2"


def predict_batch(inputs: list, config: dict | None = None) -> list:
    return predict_batch_a2(inputs, config)
