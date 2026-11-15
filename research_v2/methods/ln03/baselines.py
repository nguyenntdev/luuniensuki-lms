"""LN-03 baselines (C0 sanity + C1 strong classical) as independent policies.

- ``baselines_b0`` (B0, SANITY_ONLY): always schedule when reachable; ignores
  fact prerequisites, source verification and due dates. Negative control that
  must fail every counterexample gate.
- ``baselines_c1`` (C1, strong classical): Leitner 5-box (classical
  REIMPLEMENTATION) with prerequisite fact demotion but NO source gate —
  the documented failure mode of classical schedulers on this task.

Both implement the identical ABI (``predict_batch(inputs, config)``) with the
same input features, budget and metric target as the proposed method. Neither
shares the proposed decision function (independence requirement).
"""
from __future__ import annotations

from typing import Any, Iterable, Mapping

from research_v2.contracts.types import StudyInput, StudyPrediction

from .errors import PolicyConfigError
from .labels import (
    REASON_MISSING_FACT_BASE,
    REASON_NONFINITE_WEIGHT,
    REASON_NOT_DUE,
    RULE_DUE,
    RULE_FACT,
    RULE_SCHEDULE,
    RULE_WEIGHT,
    STUDY_ID,
)
from .scenario import SchedulingCase, is_valid_finite_number, parse_case

COMPARATOR_STATUS = {
    "baselines_b0": "REIMPLEMENTATION",
    "baselines_c1": "REIMPLEMENTATION",
}


def _empty_case_ok(case: SchedulingCase) -> None:  # pragma: no cover - self-check helper
    if case.case_id == "":
        raise PolicyConfigError("empty case_id")


# ---------------------------------------------------------------- B0: always schedule


def b0_decide(case: SchedulingCase) -> tuple[str, tuple[str, ...], float | None]:
    """B0 sanity control: always schedule, unconditionally.

    Deliberately assigns generative explanation even when the fact base is
    unstable or the source is unverified; ignores due dates and non-finite
    scheduling parameters (documented negative-control behaviour).
    """
    if case.is_generative:
        return (
            "schedule_eligible",
            ("always_schedule_generative", "no_fact_gate", "no_source_gate"),
            1.0,
        )
    return "schedule_eligible", ("always_schedule",), 1.0


def predict_batch_b0(inputs: Iterable[StudyInput], config: Mapping[str, Any] | None = None) -> list[StudyPrediction]:
    del config  # B0 has no tunables
    preds: list[StudyPrediction] = []
    for inp in inputs:
        case = parse_case(inp.case_id, inp.features)
        decision, reasons, score = b0_decide(case)
        preds.append(
            StudyPrediction(
                study_id=STUDY_ID,
                case_id=inp.case_id,
                decision=decision,
                score=score,
                reason_codes=tuple(reasons),
                evidence_ids=(),
            )
        )
    return preds


# ------------------------------------------------------- C1: Leitner 5-box classical

LEITNER_BOXES = 5
LEITNER_DEFAULT_GRADATIONS = (1, 2, 3, 4, 5)  # days per box, classical Leitner


def _leitner_box(case: SchedulingCase) -> int:
    """Map observed repetition history to a Leitner box (1..5), classical style.

    Without a persistent per-card store in this batch ABI the box is derived
    from observed repetitions (Box 1 + one per 2 successful repetitions),
    which is the standard static approximation used for single-shot policies.
    """
    reps = case.repetitions if case.repetitions is not None else 0
    box = 1 + int(reps // 2)
    return max(1, min(LEITNER_BOXES, box))


def c1_decide(case: SchedulingCase, gradations: tuple[int, ...]) -> tuple[str, tuple[str, ...], float | None]:
    """Leitner 5-box policy: prerequisite demotion, no source gate.

    Due items in Box >= 1 schedule; generative tasks without the fact
    prerequisite are demoted to fact retrieval (Box 1). Source verification is
    intentionally ignored — the classical scheduler predates epistemic gates.
    """
    # Non-finite scheduling state handling kept for comparability of failures:
    # classical Leitner ignores scheduler weights entirely.
    _ = case.scheduler_weight_raw

    if case.is_generative and not case.fact_prerequisite_mastered:
        return (
            "assign_fact_retrieval",
            (REASON_MISSING_FACT_BASE, RULE_FACT, "leitner_box_prerequisite_demotion"),
            None,
        )

    box = _leitner_box(case)
    interval_days = gradations[min(box, len(gradations)) - 1]
    return (
        "schedule_eligible",
        (f"leitner_box_{box}", f"interval_days_{interval_days}", RULE_SCHEDULE),
        1.0,
    )


def predict_batch_c1(inputs: Iterable[StudyInput], config: Mapping[str, Any] | None = None) -> list[StudyPrediction]:
    cfg = dict(config or {})
    gradations_raw = cfg.get("leitner_gradations", LEITNER_DEFAULT_GRADATIONS)
    if not isinstance(gradations_raw, (list, tuple)) or len(gradations_raw) != LEITNER_BOXES:
        raise PolicyConfigError(
            f"{STUDY_ID}: leitner_gradations must be a 5-element sequence, got {gradations_raw!r}"
        )
    gradations = []
    for g in gradations_raw:
        if isinstance(g, bool) or not isinstance(g, (int, float)) or g <= 0:
            raise PolicyConfigError(f"{STUDY_ID}: leitner gradations must be positive numbers, got {g!r}")
        gradations.append(g)
    postpone_not_due = cfg.get("postpone_if_not_due", False)

    preds: list[StudyPrediction] = []
    for inp in inputs:
        case = parse_case(inp.case_id, inp.features)
        # Classical Leitner is due-agnostic unless explicitly configured.
        if postpone_not_due and case.due_dt is not None and case.now_dt is not None and case.due_dt > case.now_dt:
            preds.append(
                StudyPrediction(
                    study_id=STUDY_ID,
                    case_id=inp.case_id,
                    decision="postpone",
                    score=None,
                    reason_codes=(REASON_NOT_DUE, RULE_DUE, "leitner_not_due"),
                    evidence_ids=(),
                )
            )
            continue
        decision, reasons, score = c1_decide(case, tuple(gradations))  # type: ignore[arg-type]
        preds.append(
            StudyPrediction(
                study_id=STUDY_ID,
                case_id=inp.case_id,
                decision=decision,
                score=score,
                reason_codes=tuple(reasons),
                evidence_ids=(),
            )
        )
    return preds
