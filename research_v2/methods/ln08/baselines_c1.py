"""Runner alias: LN-08 C1 strong classical baseline (TF-IDF cosine, no
negation handling).

Matrix method id ``baselines_c1`` resolves to ``predict_batch`` here; the
independent implementation lives in ``baselines.py``.
"""
from __future__ import annotations

from .baselines import c1_decide as c1_solve
from .baselines import c1_predict_one as predict_one
from .baselines import predict_batch_c1

STUDY_ID = "LN-08"
METHOD_ID = "baselines_c1"


def predict_batch(inputs: list, config: dict | None = None) -> list:
    return predict_batch_c1(inputs, config)
