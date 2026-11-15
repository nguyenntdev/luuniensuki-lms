"""LN-08 mechanism-isolating ablations.

Each ablation disables exactly one mechanism of the proposed pipeline and
keeps everything else identical (same input schema, same label space, same
native decision chain), so any metric movement is attributable to that
mechanism:

- ``a1`` (``ablations_a1``): keyword-only mode. Source verification, negation
  parsing, partial-reasoning detection and synonym equivalence are all
  disabled; the decision collapses to canonical keyword presence. The
  sensitive metric is false acceptance of negated answers and fabricated
  citations.
- ``a2`` (``ablations_a2``): negation parsing disabled. The pipeline still
  verifies sources but accepts negated answers as supported. The sensitive
  metric is false acceptance of keyword-complete-but-reversed answers.
- ``a3`` (``ablations_a3``): source-link verification disabled. Fabricated,
  untrusted and unverified locators are no longer detected. The sensitive
  metric is false acceptance of citation-switched answers.

Ablations run the genuinely modified code path (flags into ``solve_case``),
not a relabelled proposed output. Every prediction carries the ``ablation``
reason code plus its ``a{N}_...`` label.
"""
from __future__ import annotations

from typing import Any, Mapping

from research_v2.contracts.types import StudyInput, StudyPrediction

from .dataset import DatasetError, DiagnosticCase
from .labels import REASON_ABLATION, STUDY_ID, build_prediction, native_decision
from .proposed import solve_case

STUDY_ID = "LN-08"

ABLATION_FLAGS: dict[str, str] = {
    "ablations_a1": "keyword_only",
    "ablations_a2": "parse_negation",
    "ablations_a3": "check_source",
}

ABLATION_LABELS: dict[str, str] = {
    "ablations_a1": "a1_keyword_only",
    "ablations_a2": "a2_no_negation_parsing",
    "ablations_a3": "a3_no_source_link_check",
}


def ablation_config(method_id: str, overrides: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Build the config for one ablation: exactly one flag disabled."""
    flag = ABLATION_FLAGS.get(method_id)
    if flag is None:
        raise DatasetError(f"{STUDY_ID}: unknown ablation method_id {method_id!r}")
    cfg: dict[str, Any] = dict(overrides or {})
    cfg[flag] = flag == "keyword_only"  # keyword_only=True; the others False
    return cfg


def _ablation_solve(method_id: str, case: DiagnosticCase) -> dict[str, Any]:
    flag = ABLATION_FLAGS[method_id]
    kwargs = {flag: flag == "keyword_only"}
    result = solve_case(case, **kwargs)
    result["decision"] = native_decision(result["decision"])
    result["reason_codes"] = tuple(result["reason_codes"]) + (
        REASON_ABLATION,
        ABLATION_LABELS[method_id],
    )
    return result


def _predict_batch(method_id: str, inputs: list, config: dict | None = None) -> list:
    from research_v2.contracts.types import StudyInput as _StudyInput

    cfg = dict(config or {})
    out = []
    for i, inp in enumerate(inputs):
        if not isinstance(inp, _StudyInput):
            raise DatasetError(f"input[{i}] expects StudyInput, got {type(inp).__name__}")
        case = DiagnosticCase.from_features(inp.features, case_id=inp.case_id)
        try:
            result = _ablation_solve(method_id, case)
        except DatasetError:
            raise
        except Exception as exc:
            raise DatasetError(f"input[{i}] case {inp.case_id!r}: {exc}") from exc
        out.append(
            build_prediction(
                case_id=inp.case_id,
                decision=result["decision"],
                reason_codes=result["reason_codes"],
                evidence_ids=(case.evidence.claim_id, case.evidence.source_id),
                score=result.get("score"),
            )
        )
    return out


def a1_solve(case: DiagnosticCase) -> dict[str, Any]:
    return _ablation_solve("ablations_a1", case)


def a2_solve(case: DiagnosticCase) -> dict[str, Any]:
    return _ablation_solve("ablations_a2", case)


def a3_solve(case: DiagnosticCase) -> dict[str, Any]:
    return _ablation_solve("ablations_a3", case)


def a1_predict_one(inp: Any, config: Mapping[str, Any] | None = None) -> StudyPrediction:
    return _predict_batch("ablations_a1", [inp], config)[0]


def a2_predict_one(inp: Any, config: Mapping[str, Any] | None = None) -> StudyPrediction:
    return _predict_batch("ablations_a2", [inp], config)[0]


def a3_predict_one(inp: Any, config: Mapping[str, Any] | None = None) -> StudyPrediction:
    return _predict_batch("ablations_a3", [inp], config)[0]


def predict_batch_a1(inputs: list, config: dict | None = None) -> list:
    return _predict_batch("ablations_a1", inputs, config)


def predict_batch_a2(inputs: list, config: dict | None = None) -> list:
    return _predict_batch("ablations_a2", inputs, config)


def predict_batch_a3(inputs: list, config: dict | None = None) -> list:
    return _predict_batch("ablations_a3", inputs, config)
