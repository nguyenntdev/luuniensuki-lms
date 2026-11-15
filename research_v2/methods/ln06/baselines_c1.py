"""Runner alias: LN-06 C1 strong classical baseline (A* travel-only path).

Matrix method id ``baselines_c1`` resolves to ``predict_batch`` here; the
independent implementation lives in ``baselines.py``.
"""
from __future__ import annotations

from .baselines import c1_predict_one as predict_one
from .baselines import c1_solve, predict_batch_c1

STUDY_ID = "LN-06"
METHOD_ID = "baselines_c1"


def predict_batch(inputs: list, config: dict | None = None) -> list:
    return predict_batch_c1(inputs, config)
