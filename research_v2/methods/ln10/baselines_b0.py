"""Runner alias: LN-10 B0 baseline (unchecked linear checklist, C0 SANITY_ONLY).

Matrix method id ``baselines_b0`` resolves to ``predict_batch`` here; the
independent implementation lives in ``baselines.py``.
"""
from __future__ import annotations

from .baselines import b0_decide, predict_batch_b0

STUDY_ID = "LN-10"
METHOD_ID = "baselines_b0"


def predict_batch(inputs: list, config: dict | None = None) -> list:
    return predict_batch_b0(inputs, config)
