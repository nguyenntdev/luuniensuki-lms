"""Runner alias: LN-07 ablation A3 (inscription-affordance check disabled).

Reproduces the naive-equivalence regression on purpose: a raster fallback that
HAS an image but OMITS the inscription the task requires is accepted as
pedagogically complete. Matrix method id ``ablations_a3`` resolves to
``predict_batch`` here.
"""
from __future__ import annotations

from .ablations import a3_solve
from .dataset import DatasetError, from_input
from .labels import build_prediction

STUDY_ID = "LN-07"
METHOD_ID = "ablations_a3"


def predict_one(inp, config: dict | None = None):
    from research_v2.contracts.types import StudyInput

    if not isinstance(inp, StudyInput):
        raise DatasetError(f"predict_one expects StudyInput, got {type(inp).__name__}")
    case = from_input(inp)
    result = a3_solve(case)
    return build_prediction(
        case_id=inp.case_id,
        decision=result["decision"],
        reason_codes=result["reason_codes"],
        evidence_ids=(result["selected_option_id"],) if result["selected_option_id"] else (),
        score=1.0 if result["task_feasible"] else 0.0,
    )


def predict_batch(inputs: list, config: dict | None = None) -> list:
    return [predict_one(i, config) for i in inputs]
