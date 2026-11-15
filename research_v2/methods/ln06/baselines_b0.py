"""Runner alias: LN-06 B0 baseline (naive reverse-order walk, C0 SANITY_ONLY).

Matrix method id ``baselines_b0`` resolves to ``predict_batch`` here; the
independent implementation lives in ``baselines.py``.
"""
from __future__ import annotations

from .baselines import b0_predict_one as predict_one
from .baselines import b0_solve, predict_batch_b0

STUDY_ID = "LN-06"
METHOD_ID = "baselines_b0"


def predict_batch(inputs: list, config: dict | None = None) -> list:
    return predict_batch_b0(inputs, config)
