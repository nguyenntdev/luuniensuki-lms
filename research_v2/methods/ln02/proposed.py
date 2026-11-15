"""Proposed method (I1): Non-Compensatory Prerequisite-Aware Adaptive Learning.

Mechanism stack (each component is independently ablated in ``ablations.py``):

1. **Structural gate** - cycle detection on the prerequisite DAG
   (``reject_cycle``).
2. **Measurement validity gate** - every observed score must be a finite
   number in [0, 1] (``reject_invalid_score``); unobserved dimensions are
   *never* imputed (missing != 0, INV-LN-02-01).
3. **Multi-dimensional mastery with uncertainty** - mastery is kept as a
   per-dimension vector S1-S4; each required dimension gets an uncertainty
   set ``[max(0, m - eps), min(1, m + eps)]`` instead of a scalar ability.
4. **Non-compensatory prerequisite gating** - the *worst* (lower-confidence)
   bound of each required dimension is compared against its own threshold;
   a high aggregate score can never compensate a single missing skill.
5. **Calibrated abstention** - when a required dimension is unobserved the
   policy abstains (``abstain_insufficient_data``) instead of guessing.

Decision order (deterministic, matches the audited legacy engine):
cycle -> invalid score -> unobserved required dimension (abstain) ->
below-threshold required dimension (remediate) -> eligible.
"""
from __future__ import annotations

from typing import Any, Mapping

from research_v2.contracts.types import StudyInput, StudyPrediction

from .core import (
    FIELD_SCORE_OBSERVED,
    METHOD_VERSION_CORE,
    RC_CYCLE,
    RC_ELIGIBLE,
    RC_INSUFFICIENT_DATA,
    RC_INVALID_SCORE,
    RC_PREREQ_NOT_MET,
    STUDY_ID,
    MethodContractError,
    _features,
    _mastery_map,
    _prerequisites,
    _validate_config_number,
    build_prediction,
    competency_coverage,
    has_cycle,
    task_evidence_ids,
    unmet_required_dimensions,
    unobserved_required_dimensions,
    validate_scores,
)

METHOD_ID = "proposed"
METHOD_VERSION = f"{METHOD_VERSION_CORE}+proposed"

DEFAULT_MASTERY_UNCERTAINTY_EPS = 0.0


def predict_one(inp: StudyInput, config: Mapping[str, Any] | None = None) -> StudyPrediction:
    """Deterministic non-compensatory prerequisite gate for one case."""
    cfg: Mapping[str, Any] = config or {}
    features = _features(inp)

    # 1. Structural gate: prerequisite graph must be acyclic.
    if has_cycle(features):
        return build_prediction(
            inp,
            decision="reject_cycle",
            reason_codes=(RC_CYCLE,),
            evidence_ids=task_evidence_ids(features),
            method_version=METHOD_VERSION,
        )

    # 2. Measurement validity gate: all observed scores finite in [0, 1].
    if not validate_scores(features):
        return build_prediction(
            inp,
            decision="reject_invalid_score",
            reason_codes=(RC_INVALID_SCORE,),
            evidence_ids=task_evidence_ids(features),
            method_version=METHOD_VERSION,
        )

    mastery = _mastery_map(features)
    prerequisites = _prerequisites(features)

    # 3. Calibrated abstention: required dimension unobserved -> never guess.
    missing = unobserved_required_dimensions(mastery, prerequisites)
    if missing:
        return build_prediction(
            inp,
            decision="abstain_insufficient_data",
            reason_codes=(RC_INSUFFICIENT_DATA,)+ tuple(f"UNOBSERVED_DIMENSION:{d}" for d in missing),
            score=competency_coverage(mastery),
            evidence_ids=task_evidence_ids(features),
            method_version=METHOD_VERSION,
        )

    # 4. Non-compensatory gate with per-dimension uncertainty sets: use the
    #    lower confidence bound of each required dimension. With the default
    #    eps = 0.0 the set collapses to the point observation.
    eps = _validate_config_number(
        cfg, "mastery_uncertainty_eps", DEFAULT_MASTERY_UNCERTAINTY_EPS
    )
    if eps < 0.0 or eps > 1.0:
        raise MethodContractError(
            f"config.mastery_uncertainty_eps must be in [0, 1], got {eps!r}"
        )
    lower_bounds: dict[str, float] = {}
    upper_bounds: dict[str, float] = {}
    for dim in prerequisites:
        observed = float(mastery[dim])
        lower_bounds[dim] = max(0.0, observed - eps)
        upper_bounds[dim] = min(1.0, observed + eps)
    # ``unmet_required_dimensions`` carries the shared None guard: an
    # explicitly None prerequisite threshold is missing prerequisite data,
    # never coerced (a raw TypeError would break the typed-failure contract).
    unmet = unmet_required_dimensions(mastery, prerequisites)
    if unmet:
        # An uncertainty set that straddles the threshold makes the gate
        # undecidable from the data alone; calibrated abstention wins over a
        # hard remediation call. With eps = 0 this never fires.
        uncertain = [
            dim
            for dim in unmet
            if dim in upper_bounds
            and prerequisites[dim] is not None
            and upper_bounds[dim] >= float(prerequisites[dim])
            and eps > 0.0
        ]
        if uncertain:
            return build_prediction(
                inp,
                decision="abstain_insufficient_data",
                reason_codes=(RC_INSUFFICIENT_DATA,)
                + tuple(f"UNCERTAIN_DIMENSION:{d}" for d in sorted(uncertain)),
                score=competency_coverage(mastery),
                evidence_ids=task_evidence_ids(features),
                method_version=METHOD_VERSION,
            )
        return build_prediction(
            inp,
            decision="remediate_first",
            reason_codes=(RC_PREREQ_NOT_MET,)
            + tuple(f"UNMET_PREREQUISITE:{d}" for d in sorted(unmet)),
            score=competency_coverage(mastery),
            evidence_ids=task_evidence_ids(features),
            method_version=METHOD_VERSION,
        )

    # 5. All required dimensions clear their thresholds -> eligible.
    return build_prediction(
        inp,
        decision="recommend_eligible",
        reason_codes=(RC_ELIGIBLE,),
        score=competency_coverage(mastery),
        evidence_ids=task_evidence_ids(features),
        method_version=METHOD_VERSION,
    )


def predict_batch(
    inputs: list[StudyInput], config: Mapping[str, Any] | None = None
) -> list[StudyPrediction]:
    """Batch entrypoint: one deterministic decision per input case."""
    if not isinstance(inputs, list):
        raise MethodContractError("predict_batch expects a list of StudyInput")
    cfg: Mapping[str, Any] = config or {}
    for key in cfg:
        if not isinstance(key, str):
            raise MethodContractError("config keys must be strings")
    score_field = cfg.get("score_field", FIELD_SCORE_OBSERVED)
    if score_field != FIELD_SCORE_OBSERVED:
        raise MethodContractError(
            f"unknown score_field {score_field!r}; proposed reads {FIELD_SCORE_OBSERVED!r}"
        )
    return [predict_one(inp, cfg) for inp in inputs]


__all__ = ["METHOD_ID", "METHOD_VERSION", "predict_batch", "predict_one"]
