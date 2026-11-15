"""LN-02 baselines: B0 naive aggregate threshold and C1 Rasch 1-PL IRT.

Both comparators solve the *same* decision task (eligible / remediate /
abstain / reject labels) from the same legitimate inference-time features
and under the same compute budget. Neither consumes the multi-dimensional
prerequisite DAG as a gating structure - that is the mechanism under test.

- **B0 (SANITY_ONLY)**: recommends whenever the aggregate observed score is
  high, regardless of which competency dimensions are required. It ignores
  the prerequisite graph beyond the shared structural/validity gates. A
  high-aggregate-but-missing-prerequisite learner is wrongly waved through;
  this is the negative control the proposed method must beat.

- **C1 (MATCHED_CLASSICAL, REIMPLEMENTATION)**: Rasch 1-PL item-response
  model *with the prerequisite as a separate single-dimension gate* (the
  classical practice from spec 12.C). Two-stage decision:
  1. a separate gate checks only the task's ``target_competency`` against
     its own required threshold (abstaining if that dimension is unobserved,
     remediating if below it);
  2. scalar ability theta = logit(score_observed) (1-PL sufficient
     statistic) must clear the task's mean difficulty
     b = mean(logit(t_i)) on the same logit scale.
  As a classical *unidimensional* model it deliberately collapses the four
  competency dimensions into one latent trait plus one gate and cannot
  express the full non-compensatory conjunction ("every required dim must
  clear its own threshold") - which is precisely the classical failure mode
  under study. Being DAG-blind is part of the classical scope: a 1-PL model
  never reads ``graph_edges``, so a cyclic prerequisite graph is invisible
  to it; only the shared measurement-validity contract (rejecting invalid
  observed scores, whose MLE is undefined) is retained.
"""
from __future__ import annotations

from typing import Any, Mapping

from research_v2.contracts.types import StudyInput, StudyPrediction

from .core import (
    METHOD_VERSION_CORE,
    RC_BASELINE_GREEDY,
    RC_INSUFFICIENT_DATA,
    RC_INVALID_SCORE,
    RC_PREREQ_NOT_MET,
    RC_RASCH_SCALAR,
    STUDY_ID,
    MethodContractError,
    _features,
    _mastery_map,
    _prerequisites,
    _validate_config_number,
    build_prediction,
    is_valid_score,
    logit,
    task_evidence_ids,
    validate_scores,
)

METHOD_VERSION_B0 = f"{METHOD_VERSION_CORE}+baseline-b0"
METHOD_VERSION_C1 = f"{METHOD_VERSION_CORE}+baseline-c1-rasch1pl"

B0_STATUS = "SANITY_ONLY"
C1_STATUS = "MATCHED_CLASSICAL"
C1_PROVENANCE = "REIMPLEMENTATION"


# --------------------------------------------------------------------------- #
# Shared gate (measurement validity only; B0/C1 are deliberately DAG-blind)
# --------------------------------------------------------------------------- #
def _validity_gate(
    features: Mapping[str, Any],
) -> tuple[str, tuple[str, ...]] | None:
    """Invalid-observed-score gate shared by B0/C1 (no prerequisite DAG read).

    A 1-PL Rasch MLE is undefined for an out-of-range observed score, so the
    measurement-validity contract is retained. Cycle detection is NOT part
    of the classical scalar scope: ``graph_edges`` is never read.
    """
    if not validate_scores(features):
        return "reject_invalid_score", (RC_INVALID_SCORE,)
    return None


# --------------------------------------------------------------------------- #
# B0: naive aggregate-score recommender (negative control)
# --------------------------------------------------------------------------- #
def predict_one_b0(inp: StudyInput, config: Mapping[str, Any] | None = None) -> StudyPrediction:
    cfg: Mapping[str, Any] = config or {}
    features = _features(inp)
    blocked = _validity_gate(features)
    if blocked is not None:
        decision, reason_codes = blocked
        return build_prediction(
            inp,
            decision=decision,
            reason_codes=reason_codes,
            evidence_ids=task_evidence_ids(features),
            method_version=METHOD_VERSION_B0,
        )

    threshold = _validate_config_number(cfg, "aggregate_score_threshold", 0.5)
    if not 0.0 <= threshold <= 1.0:
        raise MethodContractError(
            f"config.aggregate_score_threshold must be in [0, 1], got {threshold!r}"
        )
    score_observed = features.get("score_observed")
    score_value = float(score_observed) if is_valid_score(score_observed) else 0.0
    mastery = _mastery_map(features)
    if score_value >= threshold:
        return build_prediction(
            inp,
            decision="recommend_eligible",
            reason_codes=(RC_BASELINE_GREEDY,),
            score=score_value,
            evidence_ids=task_evidence_ids(features),
            method_version=METHOD_VERSION_B0,
        )
    return build_prediction(
        inp,
        decision="remediate_first",
        reason_codes=(RC_BASELINE_GREEDY,),
        score=score_value,
        evidence_ids=task_evidence_ids(features),
        method_version=METHOD_VERSION_B0,
    )


# --------------------------------------------------------------------------- #
# C1: Rasch 1-PL scalar ability WITHOUT the multi-dimensional prerequisite DAG
# --------------------------------------------------------------------------- #
def predict_one_c1(inp: StudyInput, config: Mapping[str, Any] | None = None) -> StudyPrediction:
    cfg: Mapping[str, Any] = config or {}
    features = _features(inp)
    blocked = _validity_gate(features)
    if blocked is not None:
        decision, reason_codes = blocked
        return build_prediction(
            inp,
            decision=decision,
            reason_codes=reason_codes,
            evidence_ids=task_evidence_ids(features),
            method_version=METHOD_VERSION_C1,
        )

    prerequisites = _prerequisites(features)
    clip = cfg.get("logit_clip", 1e-3)

    # Stage 1: the separate classical gate - only the task's target
    # competency is checked dimensionally; the remaining dimensions are
    # collapsed away by the unidimensional model.
    target_task = features.get("target_task")
    target_dim = (
        target_task.get("target_competency") if isinstance(target_task, Mapping) else None
    )
    if target_dim and target_dim in prerequisites:
        mastery = _mastery_map(features)
        threshold = prerequisites[target_dim]
        gate_value = mastery.get(target_dim)
        if not is_valid_score(gate_value):
            return build_prediction(
                inp,
                decision="abstain_insufficient_data",
                reason_codes=(RC_INSUFFICIENT_DATA, f"UNOBSERVED_DIMENSION:{target_dim}"),
                evidence_ids=task_evidence_ids(features),
                method_version=METHOD_VERSION_C1,
            )
        if float(gate_value) < float(threshold):
            return build_prediction(
                inp,
                decision="remediate_first",
                reason_codes=(RC_PREREQ_NOT_MET, f"UNMET_PREREQUISITE:{target_dim}"),
                evidence_ids=task_evidence_ids(features),
                method_version=METHOD_VERSION_C1,
            )

    # Stage 2: scalar ability from the observed proportion score (1-PL
    # sufficient statistic) against the task's mean logit difficulty.
    score_observed = features.get("score_observed")
    theta = logit(float(score_observed), clip=clip)

    required = [
        float(t)
        for t in prerequisites.values()
        if is_valid_score(t) and 0.0 < float(t) < 1.0
    ]
    difficulty = _mean([logit(t, clip=clip) for t in required])

    margin = theta - difficulty
    decision = "recommend_eligible" if margin >= 0.0 else "remediate_first"
    reason = RC_RASCH_SCALAR if margin >= 0.0 else RC_PREREQ_NOT_MET
    return build_prediction(
        inp,
        decision=decision,
        reason_codes=(reason,),
        score=round(margin, 6),
        evidence_ids=task_evidence_ids(features),
        method_version=METHOD_VERSION_C1,
    )


def _mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


# --------------------------------------------------------------------------- #
# Batch entrypoints
# --------------------------------------------------------------------------- #
def predict_b0_batch(
    inputs: list[StudyInput], config: Mapping[str, Any] | None = None
) -> list[StudyPrediction]:
    return [predict_one_b0(inp, config or {}) for inp in inputs]


def predict_c1_batch(
    inputs: list[StudyInput], config: Mapping[str, Any] | None = None
) -> list[StudyPrediction]:
    return [predict_one_c1(inp, config or {}) for inp in inputs]


def predict_batch(
    inputs: list[StudyInput], config: Mapping[str, Any] | None = None
) -> list[StudyPrediction]:
    """Default batch = B0 sanity baseline (runner method id: ``baselines_b0``)."""
    return predict_b0_batch(inputs, config)


__all__ = [
    "B0_STATUS",
    "C1_PROVENANCE",
    "C1_STATUS",
    "METHOD_VERSION_B0",
    "METHOD_VERSION_C1",
    "predict_b0_batch",
    "predict_batch",
    "predict_c1_batch",
    "predict_one_b0",
    "predict_one_c1",
]
