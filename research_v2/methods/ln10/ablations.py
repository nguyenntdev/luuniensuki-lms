"""LN-10 mechanism-isolating ablations.

Each ablation disables exactly one I1 gate and keeps everything else identical
(same inputs, same budget, same native label space), so any decision
divergence is attributable to the removed mechanism (LN-10-15.C):

- ``ablations_a1`` (``ablations_a1`` alias): reflection gate disabled.
  Submissions with skipped reflection and material revisions without
  rationale are applied. Sensitive metric: false acceptance of premature
  submits / unjustified revisions (gold ``reject_premature_submit`` /
  ``request_reflection`` predicted ``allow_authorized_transition``).

- ``ablations_a2`` (``ablations_a2`` alias): concurrency/conflict control
  disabled. Both the explicit two-conflicting-offline-edits detector and the
  compare-and-swap gate are removed; conflicting edits to the same version
  are silently applied. Sensitive metric: false acceptance of conflicting
  transitions (gold ``resolve_revision_conflict`` predicted ``allow_authorized_transition``).

- ``ablations_a3`` (``ablations_a3`` alias): ownership check disabled.
  Unauthorized/forged actors can move any project. Sensitive metric: false
  acceptance of unauthorized transitions (gold ``deny_transition`` predicted
  ``allow_authorized_transition``).

Ablations run the genuinely modified gate chain (flags into the shared
``decide_case`` kernel, mirroring the observed engine's own ablation flags) —
not a relabelled proposed output. Each ablation appends the ``ablation`` and
its ``<removed>_disabled`` reason code so downstream analysis can audit which
code path ran.
"""
from __future__ import annotations

from typing import Any, Iterable, Mapping

from research_v2.contracts.types import StudyInput, StudyPrediction

from .dataset import DatasetError, SRLCase, parse_case
from .labels import REASON_ABLATION, build_prediction
from .proposed import decide_case

ABLATION_VERSION = "ln10-ablations-v1.0"

A1_METHOD_ID = "ablations_a1"
A2_METHOD_ID = "ablations_a2"
A3_METHOD_ID = "ablations_a3"


def _parse(inp: StudyInput) -> SRLCase:
    try:
        return parse_case(inp.case_id, inp.features)
    except DatasetError:
        raise
    except Exception as exc:
        raise DatasetError(f"case {inp.case_id!r}: {exc}") from exc


def _predict(inputs: Iterable[StudyInput], **gate_flags: bool) -> list[StudyPrediction]:
    preds: list[StudyPrediction] = []
    for inp in inputs:
        case = _parse(inp)
        result = decide_case(case, **gate_flags)
        result["reason_codes"] = tuple(result["reason_codes"]) + (REASON_ABLATION,)
        preds.append(
            build_prediction(
                case_id=inp.case_id,
                decision=result["decision"],
                reason_codes=tuple(result["reason_codes"]),
                evidence_ids=tuple(result["evidence_ids"]),
                score=1.0 if result["transition_applied"] else 0.0,
            )
        )
    return preds


def a1_solve(case: SRLCase) -> dict[str, Any]:
    """A1: reflection gate disabled (skipped reflection + missing rationale pass)."""
    result = decide_case(case, enforce_reflection_gate=False, enforce_rationale=False)
    result["reason_codes"] = tuple(result["reason_codes"]) + (REASON_ABLATION, "reflection_gate_disabled")
    return result


def a2_solve(case: SRLCase) -> dict[str, Any]:
    """A2: concurrency/conflict control disabled (conflicting edits applied)."""
    result = decide_case(case, enforce_concurrency=False)
    result["reason_codes"] = tuple(result["reason_codes"]) + (REASON_ABLATION, "concurrency_check_disabled")
    return result


def a3_solve(case: SRLCase) -> dict[str, Any]:
    """A3: ownership check disabled (unauthorized actors may transition)."""
    result = decide_case(case, enforce_ownership=False)
    result["reason_codes"] = tuple(result["reason_codes"]) + (REASON_ABLATION, "ownership_check_disabled")
    return result


def predict_batch_a1(inputs: Iterable[StudyInput], config: Mapping[str, Any] | None = None) -> list[StudyPrediction]:
    del config
    return _predict(inputs, enforce_reflection_gate=False, enforce_rationale=False)


def predict_batch_a2(inputs: Iterable[StudyInput], config: Mapping[str, Any] | None = None) -> list[StudyPrediction]:
    del config
    return _predict(inputs, enforce_concurrency=False)


def predict_batch_a3(inputs: Iterable[StudyInput], config: Mapping[str, Any] | None = None) -> list[StudyPrediction]:
    del config
    return _predict(inputs, enforce_ownership=False)
