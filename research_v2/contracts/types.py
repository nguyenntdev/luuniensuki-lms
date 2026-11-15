"""Frozen typed interfaces shared by every Research V2 study.

Enforces the scientific boundary: model inputs must never contain gold labels,
oracles, fault identifiers, cohort labels, or future learner activity.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


# Keys that must never appear in an inference-time feature mapping.
FORBIDDEN_INPUT_KEYS: frozenset[str] = frozenset(
    {
        "oracle",
        "expected_decision",
        "expected_category",
        "expected_outcome",
        "gold",
        "gold_label",
        "label",
        "fault_id",
        "canonical_fault",
        "cohort",
        "annotation_provenance",
        "synthetic_annotation_template",
        "external_expert_annotation",
    }
)


class ContractError(ValueError):
    """Raised when a V2 record violates the frozen contract."""


def _check_feature_keys(features: Mapping[str, Any], case_id: str) -> None:
    leaked = sorted(set(features) & FORBIDDEN_INPUT_KEYS)
    if leaked:
        raise ContractError(
            f"case {case_id!r}: forbidden inference-time feature keys leaked into input: {leaked}"
        )
    nested = features.get("input")
    if isinstance(nested, Mapping):
        inner = sorted(set(nested) & FORBIDDEN_INPUT_KEYS)
        if inner:
            raise ContractError(
                f"case {case_id!r}: forbidden keys nested under input: {inner}"
            )


@dataclass(frozen=True)
class StudyInput:
    """One inference-time case. Contains no gold label or oracle material."""

    study_id: str
    case_id: str
    split_id: str
    group_id: str
    features: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.study_id or not self.study_id.startswith("LN-"):
            raise ContractError(f"invalid study_id: {self.study_id!r}")
        if not self.case_id:
            raise ContractError("case_id must be non-empty")
        if not self.split_id:
            raise ContractError(f"case {self.case_id!r}: split_id must be non-empty")
        if not self.group_id:
            raise ContractError(f"case {self.case_id!r}: group_id must be non-empty")
        _check_feature_keys(self.features, self.case_id)

    def to_dict(self) -> dict[str, Any]:
        return {
            "study_id": self.study_id,
            "case_id": self.case_id,
            "split_id": self.split_id,
            "group_id": self.group_id,
            "features": dict(self.features),
        }


@dataclass(frozen=True)
class StudyPrediction:
    """One deterministic policy decision for a case."""

    study_id: str
    case_id: str
    decision: str
    score: float | None = None
    reason_codes: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.decision:
            raise ContractError(f"case {self.case_id!r}: decision must be non-empty")

    def to_dict(self) -> dict[str, Any]:
        return {
            "study_id": self.study_id,
            "case_id": self.case_id,
            "decision": self.decision,
            "score": self.score,
            "reason_codes": list(self.reason_codes),
            "evidence_ids": list(self.evidence_ids),
        }


@dataclass(frozen=True)
class RunManifest:
    """Provenance for one experiment run."""

    study_id: str
    dataset_id: str
    dataset_sha256: str
    method_id: str
    method_version: str
    source_commit: str
    seed: int
    split_id: str
    python_version: str
    packages: Mapping[str, str] = field(default_factory=dict)
    wall_ms: float | None = None
    status: str = "UNKNOWN"
    error_code: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "study_id": self.study_id,
            "dataset_id": self.dataset_id,
            "dataset_sha256": self.dataset_sha256,
            "method_id": self.method_id,
            "method_version": self.method_version,
            "source_commit": self.source_commit,
            "seed": self.seed,
            "split_id": self.split_id,
            "python_version": self.python_version,
            "packages": dict(self.packages),
            "wall_ms": self.wall_ms,
            "status": self.status,
            "error_code": self.error_code,
        }


def prediction_evidence_row(
    *,
    inp: StudyInput,
    pred: StudyPrediction,
    dataset_id: str,
    dataset_sha256: str,
    input_sha256: str,
    method_id: str,
    method_version: str,
    source_commit: str,
    seed: int,
    wall_ms: float | None = None,
    error_code: str | None = None,
) -> dict[str, Any]:
    """Build the mandatory per-case evidence row (never includes gold labels)."""
    return {
        "study_id": inp.study_id,
        "case_id": inp.case_id,
        "dataset_id": dataset_id,
        "dataset_sha256": dataset_sha256,
        "split_id": inp.split_id,
        "group_id": inp.group_id,
        "input_sha256": input_sha256,
        "method_id": method_id,
        "method_version": method_version,
        "source_commit": source_commit,
        "seed": seed,
        "decision": pred.decision,
        "score_or_null": pred.score,
        "reason_codes": list(pred.reason_codes),
        "evidence_ids": list(pred.evidence_ids),
        "wall_ms": wall_ms,
        "error_code_or_null": error_code,
        "oracle_version_in_evaluator_only": "v2-evaluator-1",
    }
