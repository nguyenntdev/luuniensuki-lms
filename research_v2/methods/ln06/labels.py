"""LN-06 decision labels and typed mapping from native policy outputs.

Label ontology (mirrors ``research_v2.contracts.label_space.LN06_DECISIONS``):

- ``find_valid_route``         : feasible ordered route covering all targets.
- ``reject_cycle``             : prerequisite structure is cyclic (certified).
- ``no_feasible_route``        : some target outcome (or its prerequisite
                                 closure) has no available provider.
- ``cost_exceeded``            : minimum feasible subset cost exceeds budget.
- ``reject_checkpoint_source`` : checkpoint claim provenance unverified.

Abstain/invalid/infeasible labels are distinct by design; nothing collapses
into a generic "reject". Unknown native labels raise :class:`LabelError`.
"""
from __future__ import annotations

from enum import Enum

from research_v2.contracts.label_space import validate_decision
from research_v2.contracts.types import ContractError


class LabelError(ValueError):
    """Raised when a native policy output cannot be mapped to a legal label."""


class Decision(str, Enum):
    FIND_VALID_ROUTE = "find_valid_route"
    REJECT_CYCLE = "reject_cycle"
    NO_FEASIBLE_ROUTE = "no_feasible_route"
    COST_EXCEEDED = "cost_exceeded"
    REJECT_CHECKPOINT_SOURCE = "reject_checkpoint_source"


DECISION_VALUES: frozenset[str] = frozenset(d.value for d in Decision)

# Reason codes emitted by policies, grouped for the error analysis ledger.
REASON_NOMINAL = "nominal"
REASON_PREREQ_CYCLE = "prerequisite_cycle"
REASON_UNREACHABLE_STOP = "unreachable_stop"
REASON_UNREACHABLE_OUTCOME = "unreachable_outcome"
REASON_OVER_BUDGET = "over_budget"
REASON_SOURCE_GAP = "source_gap"
REASON_BASELINE_NAIVE = "baseline_spatial_naive"
REASON_ASTAR_TRAVEL_ONLY = "astar_travel_only"
REASON_ABLATION = "ablation"
REASON_LEGACY_ALL_PROVIDERS = "legacy_all_providers_bug"


def map_decision(native: str) -> str:
    """Map a native policy output to the declared LN-06 label space.

    Raises :class:`LabelError` for unknown labels (never guesses a fallback).
    """
    if not isinstance(native, str) or not native:
        raise LabelError(f"native decision must be a non-empty string, got {native!r}")
    label = native.strip()
    try:
        Decision(label)
    except ValueError as exc:
        raise LabelError(
            f"unknown LN-06 decision {native!r}; legal labels: {sorted(DECISION_VALUES)}"
        ) from exc
    validate_decision("LN-06", label)
    return label


def build_prediction(
    *,
    case_id: str,
    decision: str,
    reason_codes: tuple[str, ...] = (),
    evidence_ids: tuple[str, ...] = (),
    score: float | None = None,
) -> "object":
    """Construct a contract-valid StudyPrediction (import kept local to avoid a cycle)."""
    from research_v2.contracts.types import StudyPrediction

    label = map_decision(decision)
    try:
        return StudyPrediction(
            study_id="LN-06",
            case_id=case_id,
            decision=label,
            score=score,
            reason_codes=tuple(reason_codes),
            evidence_ids=tuple(evidence_ids),
        )
    except ContractError as exc:  # pragma: no cover - defensive
        raise LabelError(f"contract violation building prediction for {case_id!r}: {exc}") from exc
