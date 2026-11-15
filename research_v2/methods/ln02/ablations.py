"""LN-02 mechanism-isolating ablations of the proposed policy.

Each ablation disables exactly one mechanism of the proposed stack and keeps
everything else fixed, so any metric movement is attributable to the removed
component (spec section 15.C):

- **a1 ``no_prerequisites``**: the non-compensatory prerequisite gate is
  removed; eligibility is decided from the aggregate score alone (after the
  shared structural and validity gates). Sensitive metric: prerequisite
  safety / false-recommendation rate on high-aggregate cases with an unmet
  necessary skill.

- **a2 ``no_abstention``**: calibrated abstention is disabled; unobserved
  required dimensions are imputed as 0.0 (missing treated as zero mastery),
  which silently forces remediation instead of an honest abstention.
  Sensitive metric: abstention coverage on unobserved-dimension cases.

- **a3 ``single_latent_skill``**: the S1-S4 mastery vector is collapsed into
  one scalar latent skill (mean mastery) compared against the mean
  prerequisite threshold; per-dimension conjunction is lost. Sensitive
  metric: false-eligible rate when one required dimension is far below its
  threshold while others compensate.
"""
from __future__ import annotations

from typing import Any, Mapping

from research_v2.contracts.types import StudyInput, StudyPrediction

from .core import (
    METHOD_VERSION_CORE,
    RC_ABLATION_COLLAPSED,
    RC_ABLATION_NO_ABSTENTION,
    RC_ABLATION_NO_PREREQS,
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
    is_valid_score,
    observed_mastery_values,
    task_evidence_ids,
    validate_scores,
)

METHOD_VERSION_A1 = f"{METHOD_VERSION_CORE}+ablation-a1-no-prerequisites"
METHOD_VERSION_A2 = f"{METHOD_VERSION_CORE}+ablation-a2-no-abstention"
METHOD_VERSION_A3 = f"{METHOD_VERSION_CORE}+ablation-a3-single-latent-skill"

ABLATION_IDS: dict[str, str] = {
    "a1": "no_prerequisites",
    "a2": "no_abstention",
    "a3": "single_latent_skill",
}

RC_UNOBSERVED = "UNOBSERVED_DIMENSION"


def _gates(
    inp: StudyInput, features: Mapping[str, Any], method_version: str
) -> StudyPrediction | None:
    """Structural + validity gates retained by every ablation variant."""
    if has_cycle(features):
        return build_prediction(
            inp,
            decision="reject_cycle",
            reason_codes=(RC_CYCLE,),
            evidence_ids=task_evidence_ids(features),
            method_version=method_version,
        )
    if not validate_scores(features):
        return build_prediction(
            inp,
            decision="reject_invalid_score",
            reason_codes=(RC_INVALID_SCORE,),
            evidence_ids=task_evidence_ids(features),
            method_version=method_version,
        )
    return None


def _imputed_mastery(
    mastery: Mapping[str, Any], prerequisites: Mapping[str, Any]
) -> dict[str, float]:
    """Vector with every unobserved *required* dimension imputed to 0.0."""
    imputed: dict[str, float] = {}
    for dim in prerequisites:
        value = mastery.get(dim)
        number = float(value) if is_valid_score(value) else 0.0
        imputed[dim] = number
    return imputed


# --------------------------------------------------------------------------- #
# a1: remove the prerequisite gate (aggregate score only)
# --------------------------------------------------------------------------- #
def predict_one_a1(inp: StudyInput, config: Mapping[str, Any] | None = None) -> StudyPrediction:
    cfg: Mapping[str, Any] = config or {}
    features = _features(inp)
    blocked = _gates(inp, features, METHOD_VERSION_A1)
    if blocked is not None:
        return blocked

    threshold = _validate_config_number(cfg, "aggregate_score_threshold", 0.5)
    mastery = _mastery_map(features)
    prerequisites = _prerequisites(features)
    score_observed = features.get("score_observed")
    score_value = float(score_observed) if is_valid_score(score_observed) else 0.0
    eligible = score_value >= threshold
    # Diagnostic only: would the removed gate have blocked this learner?
    unmet = [
        dim
        for dim, t in prerequisites.items()
        if is_valid_score(mastery.get(dim)) and float(mastery[dim]) < float(t)
    ]
    return build_prediction(
        inp,
        decision="recommend_eligible" if eligible else "remediate_first",
        reason_codes=(RC_ELIGIBLE if eligible else RC_PREREQ_NOT_MET, RC_ABLATION_NO_PREREQS)
        + (tuple(f"UNMET_PREREQUISITE:{d}" for d in sorted(unmet)) if eligible else ()),
        score=score_value,
        evidence_ids=task_evidence_ids(features),
        method_version=METHOD_VERSION_A1,
    )


# --------------------------------------------------------------------------- #
# a2: disable calibrated abstention (impute unobserved required dims as 0)
# --------------------------------------------------------------------------- #
def predict_one_a2(inp: StudyInput, config: Mapping[str, Any] | None = None) -> StudyPrediction:
    features = _features(inp)
    blocked = _gates(inp, features, METHOD_VERSION_A2)
    if blocked is not None:
        return blocked

    mastery = _mastery_map(features)
    prerequisites = _prerequisites(features)
    unobserved = [dim for dim in prerequisites if not is_valid_score(mastery.get(dim))]
    if unobserved:
        # Mechanism removed: missing is silently treated as zero mastery.
        imputed = _imputed_mastery(mastery, prerequisites)
        unmet = [dim for dim, t in prerequisites.items() if imputed[dim] < float(t)]
        return build_prediction(
            inp,
            decision="remediate_first" if unmet else "recommend_eligible",
            reason_codes=(RC_ABLATION_NO_ABSTENTION,)
            + tuple(f"{RC_UNOBSERVED}:{d}" for d in sorted(unobserved)),
            score=competency_coverage(mastery),
            evidence_ids=task_evidence_ids(features),
            method_version=METHOD_VERSION_A2,
        )
    unmet = [dim for dim, t in prerequisites.items() if float(mastery[dim]) < float(t)]
    return build_prediction(
        inp,
        decision="remediate_first" if unmet else "recommend_eligible",
        reason_codes=(RC_ABLATION_NO_ABSTENTION if not unmet else RC_PREREQ_NOT_MET,),
        score=competency_coverage(mastery),
        evidence_ids=task_evidence_ids(features),
        method_version=METHOD_VERSION_A2,
    )


# --------------------------------------------------------------------------- #
# a3: collapse mastery to a single latent scalar skill
# --------------------------------------------------------------------------- #
def predict_one_a3(inp: StudyInput, config: Mapping[str, Any] | None = None) -> StudyPrediction:
    features = _features(inp)
    blocked = _gates(inp, features, METHOD_VERSION_A3)
    if blocked is not None:
        return blocked

    mastery = _mastery_map(features)
    prerequisites = _prerequisites(features)
    # A scalar gate over the required dimensions needs their observations;
    # with a required dimension unobserved the collapsed model cannot form
    # its latent input and the classical fallback is the honest abstain.
    unobserved = [
        dim
        for dim in prerequisites
        if not is_valid_score(mastery.get(dim))
    ]
    if unobserved:
        return build_prediction(
            inp,
            decision="abstain_insufficient_data",
            reason_codes=(RC_INSUFFICIENT_DATA, RC_ABLATION_COLLAPSED)
            + tuple(f"{RC_UNOBSERVED}:{d}" for d in sorted(unobserved)),
            score=competency_coverage(mastery),
            evidence_ids=task_evidence_ids(features),
            method_version=METHOD_VERSION_A3,
        )
    observed = observed_mastery_values(mastery)
    if not observed:  # pragma: no cover - unobserved check above covers this
        return build_prediction(
            inp,
            decision="abstain_insufficient_data",
            reason_codes=(RC_INSUFFICIENT_DATA, RC_ABLATION_COLLAPSED),
            score=0.0,
            evidence_ids=task_evidence_ids(features),
            method_version=METHOD_VERSION_A3,
        )
    required = [float(t) for t in prerequisites.values() if is_valid_score(t)]
    latent_skill = sum(observed) / len(observed)
    mean_threshold = sum(required) / len(required) if required else 0.5
    eligible = latent_skill >= mean_threshold
    return build_prediction(
        inp,
        decision="recommend_eligible" if eligible else "remediate_first",
        reason_codes=(RC_ABLATION_COLLAPSED,),
        score=round(latent_skill, 6),
        evidence_ids=task_evidence_ids(features),
        method_version=METHOD_VERSION_A3,
    )


# --------------------------------------------------------------------------- #
# Batch entrypoints
# --------------------------------------------------------------------------- #
def _batch(
    predict_one,
    inputs: list[StudyInput],
    config: Mapping[str, Any] | None,
) -> list[StudyPrediction]:
    cfg: Mapping[str, Any] = config or {}
    variant = cfg.get("variant")
    if variant is not None and variant not in ABLATION_IDS.values():
        raise MethodContractError(
            f"unknown ablation variant {variant!r}; expected one of {sorted(ABLATION_IDS.values())}"
        )
    return [predict_one(inp, cfg) for inp in inputs]


def predict_a1_batch(inputs: list[StudyInput], config: Mapping[str, Any] | None = None) -> list[StudyPrediction]:
    return _batch(predict_one_a1, inputs, config)


def predict_a2_batch(inputs: list[StudyInput], config: Mapping[str, Any] | None = None) -> list[StudyPrediction]:
    return _batch(predict_one_a2, inputs, config)


def predict_a3_batch(inputs: list[StudyInput], config: Mapping[str, Any] | None = None) -> list[StudyPrediction]:
    return _batch(predict_one_a3, inputs, config)


def predict_batch(
    inputs: list[StudyInput], config: Mapping[str, Any] | None = None
) -> list[StudyPrediction]:
    """Default batch dispatches on ``config["variant"]`` (default a1)."""
    cfg: Mapping[str, Any] = config or {}
    variant = cfg.get("variant", "no_prerequisites")
    if variant == "no_prerequisites":
        return predict_a1_batch(inputs, cfg)
    if variant == "no_abstention":
        return predict_a2_batch(inputs, cfg)
    if variant == "single_latent_skill":
        return predict_a3_batch(inputs, cfg)
    raise MethodContractError(
        f"unknown ablation variant {variant!r}; expected one of {sorted(ABLATION_IDS.values())}"
    )


__all__ = [
    "ABLATION_IDS",
    "METHOD_VERSION_A1",
    "METHOD_VERSION_A2",
    "METHOD_VERSION_A3",
    "predict_a1_batch",
    "predict_a2_batch",
    "predict_a3_batch",
    "predict_batch",
    "predict_one_a1",
    "predict_one_a2",
    "predict_one_a3",
]
