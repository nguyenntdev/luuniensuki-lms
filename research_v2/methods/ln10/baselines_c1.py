"""Runner alias: LN-10 C1 strong classical baseline (linear checklist tracker).

Matrix method id ``baselines_c1`` resolves to ``predict_batch`` here; the
independent implementation lives in ``baselines.py``.
"""
from __future__ import annotations

from .baselines import c1_decide, predict_batch_c1

STUDY_ID = "LN-10"
METHOD_ID = "baselines_c1"


def predict_batch(inputs: list, config: dict | None = None) -> list:
    return predict_batch_c1(inputs, config)
