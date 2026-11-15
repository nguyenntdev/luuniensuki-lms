"""Shared typed decision core for Study LN-02 (Prerequisite-Aware Adaptive Learning).

All LN-02 methods (proposed, baselines, ablations) are thin deterministic
policies over the same legitimate inference-time features:

- ``graph_edges``: list of directed prerequisite edges [u, v] (u is a
  prerequisite of v).
- ``mastery`` / ``learner.competencies``: per-dimension mastery observations
  for historical competencies S1-S4 (S1 spatial, S2 temporal, S3 evidence,
  S4 argumentation).
- ``score_observed``: aggregate observed assessment score.
- ``target_task``: task metadata with a ``prerequisites`` mapping
  {dimension: required threshold} and an optional ``target_competency``.

Hard invariants (non-compensatory):
1. A cyclic prerequisite graph is rejected outright (``reject_cycle``).
2. Any invalid score value (non-numeric, NaN/inf, outside [0, 1]) is rejected
   (``reject_invalid_score``). Missing != zero: an unobserved competency is
   never silently imputed (INV-LN-02-01).
3. If a required prerequisite dimension is unobserved, the only honest
   decision is calibrated abstention (``abstain_insufficient_data``).
4. If any *required* dimension is observed but below its prerequisite
   threshold, the learner must remediate first (``remediate_first``) - a high
   aggregate score never compensates for a missing necessary skill.
5. Only when every required dimension clears its threshold is the task
   recommended (``recommend_eligible``).

No oracle, gold label, fault identifier, or future learner activity is read
at inference time. All decisions are pure functions of (features, config).
"""
from __future__ import annotations

import math
from typing import Any, Mapping

from research_v2.contracts.label_space import validate_decision
from research_v2.contracts.types import (
    ContractError,
    StudyInput,
    StudyPrediction,
)

STUDY_ID = "LN-02"

# Historical competency dimensions (Vietnamese General Education 2018 model
# used by the legacy engine). Order matters only for deterministic iteration.
COMPETENCY_DIMENSIONS: tuple[str, ...] = ("S1", "S2", "S3", "S4")

# Feature field names on the masked inference-time input.
FIELD_GRAPH_EDGES = "graph_edges"
FIELD_MASTERY = "mastery"
FIELD_SCORE_OBSERVED = "score_observed"
FIELD_TARGET_TASK = "target_task"
FIELD_LEARNER = "learner"
FIELD_CONTENT = "content"
FIELD_PROFILE_SEED = "seed"

METHOD_VERSION_CORE = "ln02-core-1.0.0"

# Reason codes (mirrors the legacy engine's controlled vocabulary).
RC_ELIGIBLE = "ELIGIBLE_RECOMMENDATION"
RC_PREREQ_NOT_MET = "PREREQUISITE_NOT_MET"
RC_INSUFFICIENT_DATA = "INSUFFICIENT_COMPETENCY_DATA"
RC_INVALID_SCORE = "INVALID_SCORE_RANGE"
RC_CYCLE = "CYCLE_DETECTED"
RC_BASELINE_GREEDY = "BASELINE_GREEDY_SCORE"
RC_RASCH_SCALAR = "RASCH_SCALAR_ABILITY"
RC_ABLATION_NO_PREREQS = "ABLATION_NO_PREREQUISITES"
RC_ABLATION_NO_ABSTENTION = "ABLATION_NO_ABSTENTION"
RC_ABLATION_COLLAPSED = "ABLATION_COLLAPSED_LATENT"

# Public documentation anchor: comparator status per spec section H.
COMPARATOR_STATUS: dict[str, str] = {
    "proposed": "ORIGINAL_CODE_VERIFIED",
    "baselines_b0": "ORIGINAL_CODE_VERIFIED",
    "baselines_c1": "REIMPLEMENTATION",
    "ablations_a1": "ORIGINAL_CODE_VERIFIED",
    "ablations_a2": "ORIGINAL_CODE_VERIFIED",
    "ablations_a3": "ORIGINAL_CODE_VERIFIED",
}


class MethodContractError(ContractError):
    """Typed failure for malformed method inputs (never a silent default)."""


# --------------------------------------------------------------------------- #
# Feature extraction & validation helpers
# --------------------------------------------------------------------------- #
def _features(inp: StudyInput) -> Mapping[str, Any]:
    features = inp.features
    if not isinstance(features, Mapping):
        raise MethodContractError(
            f"case {inp.case_id!r}: features must be a mapping, got {type(features).__name__}"
        )
    return features


def _as_float(value: Any) -> float | None:
    """Return the value as a finite float, or None when unobserved/None.

    Non-numeric junk (strings, bools, lists) returns None here; range/NaN
    policy is applied separately so that callers can distinguish
    "unobserved" from "observed but invalid".
    """
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def coerce_finite_float(value: Any, *, field: str) -> float | None:
    """Typed scalar coercion for decision-path comparisons.

    Returns None when the value is None (unobserved), so callers can apply
    the documented abstain/fallback semantics. Bools are rejected explicitly
    (a boolean is not a measurement); any other non-numeric type raises a
    typed :class:`MethodContractError` instead of a raw ``TypeError``.
    """
    if value is None:
        return None
    if isinstance(value, bool):
        raise MethodContractError(
            f"{field} must be a finite number, got bool {value!r}"
        )
    if isinstance(value, (int, float)):
        return float(value)
    raise MethodContractError(
        f"{field} must be a finite number, got {type(value).__name__} {value!r}"
    )


def is_valid_score(value: Any) -> bool:
    """A score is valid iff it is a finite number within [0.0, 1.0]."""
    number = _as_float(value)
    if number is None:
        return False
    if math.isnan(number) or math.isinf(number):
        return False
    return 0.0 <= number <= 1.0


def _mastery_map(features: Mapping[str, Any]) -> Mapping[str, Any]:
    mastery = features.get(FIELD_MASTERY)
    if mastery is None:
        learner = features.get(FIELD_LEARNER)
        if isinstance(learner, Mapping):
            mastery = learner.get("competencies")
    if mastery is None:
        return {}
    if not isinstance(mastery, Mapping):
        raise MethodContractError(
            "mastery must be a mapping of {dimension: observed mastery}"
        )
    return mastery


def _prerequisites(features: Mapping[str, Any]) -> Mapping[str, Any]:
    target_task = features.get(FIELD_TARGET_TASK)
    if target_task is None:
        return {}
    if not isinstance(target_task, Mapping):
        raise MethodContractError("target_task must be a mapping")
    prerequisites = target_task.get("prerequisites") or {}
    if not isinstance(prerequisites, Mapping):
        raise MethodContractError(
            "target_task.prerequisites must be a mapping {dimension: threshold}"
        )
    return prerequisites


def _edges(features: Mapping[str, Any]) -> list[tuple[str, str]]:
    raw = features.get(FIELD_GRAPH_EDGES) or []
    if not isinstance(raw, (list, tuple)):
        raise MethodContractError("graph_edges must be a list of [prereq, dependent] pairs")
    edges: list[tuple[str, str]] = []
    for item in raw:
        if not isinstance(item, (list, tuple)) or len(item) < 2:
            raise MethodContractError(
                f"graph_edges entries must be [u, v] pairs, got {item!r}"
            )
        edges.append((str(item[0]), str(item[1])))
    return edges


def detect_cycle(edges: list[tuple[str, str]]) -> bool:
    """3-colour DFS cycle detection over the directed prerequisite graph."""
    adjacency: dict[str, list[str]] = {}
    for u, v in edges:
        adjacency.setdefault(u, []).append(v)
        adjacency.setdefault(v, [])

    visiting, visited = 1, 2
    state: dict[str, int] = {}

    def dfs(node: str) -> bool:
        state[node] = visiting
        for nxt in adjacency.get(node, ()):  # pragma: no branch
            nxt_state = state.get(nxt, 0)
            if nxt_state == visiting:
                return True
            if nxt_state == 0 and dfs(nxt):
                return True
        state[node] = visited
        return False

    for node in adjacency:
        if state.get(node, 0) == 0 and dfs(node):
            return True
    return False


def has_cycle(features: Mapping[str, Any]) -> bool:
    return detect_cycle(_edges(features))


def validate_scores(features: Mapping[str, Any]) -> bool:
    """Validate score_observed plus every observed mastery/competency value.

    Unobserved (None / absent) dimensions are fine - abstention handles them.
    Observed-but-invalid values (out of range, NaN, inf, non-numeric junk)
    invalidate the case.
    """
    score_observed = features.get(FIELD_SCORE_OBSERVED)
    if score_observed is not None and not is_valid_score(score_observed):
        return False

    for mastery_map in (_mastery_map(features),):
        for value in mastery_map.values():
            if value is not None and not is_valid_score(value):
                return False

    learner = features.get(FIELD_LEARNER)
    if isinstance(learner, Mapping):
        competencies = learner.get("competencies")
        if isinstance(competencies, Mapping):
            for value in competencies.values():
                if value is not None and not is_valid_score(value):
                    return False

    prerequisites = _prerequisites(features)
    for threshold in prerequisites.values():
        if threshold is not None and not is_valid_score(threshold):
            return False

    return True


def unobserved_required_dimensions(
    mastery: Mapping[str, Any], prerequisites: Mapping[str, Any]
) -> list[str]:
    """Required prerequisite dimensions without an observed mastery value."""
    return [
        dim
        for dim in prerequisites
        if _as_float(mastery.get(dim)) is None
    ]


def unmet_required_dimensions(
    mastery: Mapping[str, Any], prerequisites: Mapping[str, Any]
) -> list[str]:
    """Required prerequisite dimensions observed below their threshold."""
    unmet: list[str] = []
    for dim, threshold in prerequisites.items():
        required = _as_float(threshold)
        if required is None:
            continue
        observed = _as_float(mastery.get(dim))
        if observed is not None and observed < required:
            unmet.append(dim)
    return sorted(unmet)


def competency_coverage(mastery: Mapping[str, Any]) -> float:
    """Fraction of the four competency dimensions with valid observations."""
    if not isinstance(mastery, Mapping):
        return 0.0
    observed = sum(1 for dim in COMPETENCY_DIMENSIONS if is_valid_score(mastery.get(dim)))
    return round(observed / len(COMPETENCY_DIMENSIONS), 4)


def observed_mastery_values(mastery: Mapping[str, Any]) -> list[float]:
    """All observed (valid) mastery values, in deterministic dimension order."""
    values: list[float] = []
    for dim in COMPETENCY_DIMENSIONS:
        number = _as_float(mastery.get(dim))
        if number is not None:
            values.append(number)
    # Preserve any extra non-standard dimensions deterministically.
    for dim in sorted(k for k in mastery if k not in COMPETENCY_DIMENSIONS):
        number = _as_float(mastery.get(dim))
        if number is not None:
            values.append(number)
    return values


# --------------------------------------------------------------------------- #
# Prediction plumbing
# --------------------------------------------------------------------------- #
def build_prediction(
    inp: StudyInput,
    *,
    decision: str,
    reason_codes: tuple[str, ...] | list[str],
    score: float | None = None,
    evidence_ids: tuple[str, ...] | list[str] = (),
    method_version: str = METHOD_VERSION_CORE,
) -> StudyPrediction:
    """Construct a StudyPrediction with the label space enforced.

    Unknown labels raise a typed error (never silently mapped to reject).
    """
    validate_decision(STUDY_ID, decision)
    return StudyPrediction(
        study_id=STUDY_ID,
        case_id=inp.case_id,
        decision=decision,
        score=score,
        reason_codes=tuple(reason_codes),
        evidence_ids=tuple(evidence_ids),
    )


def task_evidence_ids(features: Mapping[str, Any]) -> tuple[str, ...]:
    """Deterministic evidence identifiers for a case (task + content ids)."""
    evidence: list[str] = []
    target_task = features.get(FIELD_TARGET_TASK)
    if isinstance(target_task, Mapping) and target_task.get("id"):
        evidence.append(str(target_task["id"]))
    content = features.get(FIELD_CONTENT)
    if isinstance(content, Mapping) and content.get("id"):
        evidence.append(str(content["id"]))
    return tuple(evidence)


def _config_get(config: Mapping[str, Any] | None, key: str, default: Any) -> Any:
    if not config:
        return default
    value = config.get(key, default)
    return default if value is None else value


def _validate_config_number(config: Mapping[str, Any] | None, key: str, default: float) -> float:
    raw = _config_get(config, key, default)
    number = _as_float(raw)
    if number is None:
        raise MethodContractError(
            f"config.{key} must be a finite number, got {raw!r}"
        )
    if math.isnan(number) or math.isinf(number):
        raise MethodContractError(f"config.{key} must be finite, got {raw!r}")
    return number


def logit(probability: float, *, clip: float = 1e-3) -> float:
    """Numerically stable logit with symmetric clipping (Rasch ability)."""
    p = min(max(probability, clip), 1.0 - clip)
    return math.log(p / (1.0 - p))


def predict_one(features: Mapping[str, Any], case_id: str, config: Mapping[str, Any]) -> StudyPrediction:
    """Default decision core shared via composition (the proposed policy)."""
    from . import proposed as _proposed  # local import to avoid cycles

    shim = StudyInput(
        study_id=STUDY_ID,
        case_id=case_id,
        split_id="test",
        group_id=case_id,
        features=features,
    )
    return _proposed.predict_one(shim, config)


__all__ = [
    "COMPETENCY_DIMENSIONS",
    "COMPARATOR_STATUS",
    "FIELD_CONTENT",
    "FIELD_GRAPH_EDGES",
    "FIELD_LEARNER",
    "FIELD_MASTERY",
    "FIELD_PROFILE_SEED",
    "FIELD_SCORE_OBSERVED",
    "FIELD_TARGET_TASK",
    "METHOD_VERSION_CORE",
    "RC_ABLATION_COLLAPSED",
    "RC_ABLATION_NO_ABSTENTION",
    "RC_ABLATION_NO_PREREQS",
    "RC_BASELINE_GREEDY",
    "RC_CYCLE",
    "RC_ELIGIBLE",
    "RC_INSUFFICIENT_DATA",
    "RC_INVALID_SCORE",
    "RC_PREREQ_NOT_MET",
    "RC_RASCH_SCALAR",
    "STUDY_ID",
    "MethodContractError",
    "build_prediction",
    "coerce_finite_float",
    "competency_coverage",
    "detect_cycle",
    "has_cycle",
    "is_valid_score",
    "logit",
    "observed_mastery_values",
    "predict_one",
    "task_evidence_ids",
    "unmet_required_dimensions",
    "unobserved_required_dimensions",
    "validate_scores",
]
