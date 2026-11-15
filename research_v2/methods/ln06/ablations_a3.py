"""Runner alias: LN-06 ablation A3 (legacy all-providers bug, kept as ablation).

Matrix method id ``ablations_a3`` resolves to ``predict_batch`` here. This is
the documented regression of the observed legacy engine: alternative providers
of the same outcome are summed instead of chosen, producing false
infeasibility on the mandatory A/B case.
"""
from __future__ import annotations

from .ablations import a3_predict_one as predict_one
from .ablations import a3_solve, predict_batch_a3

STUDY_ID = "LN-06"
METHOD_ID = "ablations_a3"


def predict_batch(inputs: list, config: dict | None = None) -> list:
    return predict_batch_a3(inputs, config)
