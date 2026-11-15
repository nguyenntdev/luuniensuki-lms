"""LN-08 label ontology and typed mapping from native policy outputs.

Native decision vocabulary mirrors the observed legacy engine
(``research/feedback/diagnostic_feedback.py``, oracle basis
``DIAGNOSTIC_FEEDBACK_SPEC``) that generated the T3 gold:

- ``feedback_supported``        : answer asserts the source-backed relation
                                  (canonical keyword OR synonym-equivalent
                                  paraphrase).
- ``classify_contradiction``    : negation reverses the historical relation
                                  even when every keyword is present.
- ``classify_source_error``     : fabricated/untrusted/unverified locator.
- ``preserve_semantics``        : NATIVE label for a synonym-equivalent
                                  supported paraphrase (no exact canonical
                                  keyword); folds into
                                  ``feedback_supported`` in the frozen
                                  contract space.
- ``feedback_incomplete``       : partial/generic reasoning without the
                                  spatial-ritual relation.

The frozen contract space (``research_v2.contracts.label_space.LN08_DECISIONS``)
declares ``abstain_insufficient_data`` where the native engine says ``abstain``
for unrecognised/empty input. Both vocabularies are validated strictly; unknown
labels raise :class:`LabelError` (never guessed into a fallback). The native ->
contract mapping is deterministic and explicit.
"""
from __future__ import annotations

from enum import Enum

from research_v2.contracts.label_space import (
    LN08_DECISIONS as CONTRACT_DECISIONS,
    LabelSpaceError,
    validate_decision,
)
from research_v2.contracts.types import ContractError

STUDY_ID = "LN-08"


class Decision(str, Enum):
    """Native decisions produced by the LN-08 diagnostic pipeline."""

    FEEDBACK_SUPPORTED = "feedback_supported"
    CLASSIFY_CONTRADICTION = "classify_contradiction"
    CLASSIFY_SOURCE_ERROR = "classify_source_error"
    PRESERVE_SEMANTICS = "preserve_semantics"
    FEEDBACK_INCOMPLETE = "feedback_incomplete"
    ABSTAIN = "abstain"


NATIVE_DECISIONS: frozenset[str] = frozenset(d.value for d in Decision)

#: Contract-only decision (calibrated abstention, distinct from every reject).
CONTRACT_ONLY_DECISIONS: frozenset[str] = CONTRACT_DECISIONS - (
    NATIVE_DECISIONS - {"abstain"}
)

#: Deterministic mapping native -> frozen contract label space.
#: The frozen space has no separate supported-paraphrase label: a
#: synonym-equivalent answer asserts the same source-backed proposition, so
#: ``preserve_semantics`` folds into ``feedback_supported`` (the reason codes
#: keep the synonym_equivalence distinction for error analysis).
NATIVE_TO_CONTRACT: dict[str, str] = {
    "feedback_supported": "feedback_supported",
    "classify_contradiction": "classify_contradiction",
    "classify_source_error": "classify_source_error",
    "preserve_semantics": "feedback_supported",
    "feedback_incomplete": "feedback_incomplete",
    "abstain": "abstain_insufficient_data",
}

# Reason codes emitted by the diagnostic pipeline (legacy rule IDs preserved).
REASON_NOMINAL = "nominal"
REASON_NEGATION = "logical_negation"
REASON_SOURCE_MISMATCH = "source_mismatch"
REASON_PARTIAL = "partial_reasoning"
REASON_SYNONYM = "synonym_equivalence"
REASON_KEYWORD_MATCH = "baseline_keyword_match"
REASON_KEYWORD_MISSING = "baseline_keyword_missing"
REASON_EMPTY_ANSWER = "empty_answer"
REASON_ABLATION = "ablation"

RULE_SUPPORTED = "RULE-LN-08-01"
RULE_NEGATION = "RULE-LN-08-02"
RULE_SOURCE = "RULE-LN-08-03"
RULE_SYNONYM = "RULE-LN-08-04"
RULE_PARTIAL = "RULE-LN-08-05"
RULE_INV = "RULE-LN-08-INV"


class LabelError(ValueError):
    """Raised when a native output cannot be mapped to a legal label."""


def validate_native_decision(decision: str) -> str:
    """Validate against the native engine space; typed failure on unknown."""
    if not isinstance(decision, str) or not decision:
        raise LabelError(f"native decision must be a non-empty string, got {decision!r}")
    label = decision.strip()
    if label not in NATIVE_DECISIONS:
        raise LabelError(
            f"{STUDY_ID}: decision {decision!r} not in native label space {sorted(NATIVE_DECISIONS)}"
        )
    return label


def native_decision(value: str | Decision) -> str:
    """Coerce an enum or string to a validated native decision string."""
    d = value.value if isinstance(value, Decision) else str(value)
    return validate_native_decision(d)


def to_contract_decision(decision: str) -> str:
    """Deterministic native -> contract translation; unknown labels raise."""
    native = validate_native_decision(decision)
    mapped = NATIVE_TO_CONTRACT[native]
    try:
        validate_decision(STUDY_ID, mapped)
    except LabelSpaceError as exc:  # pragma: no cover - mapping is static
        raise LabelError(f"{STUDY_ID}: contract mapping invalid: {exc}") from exc
    return mapped


def build_prediction(
    *,
    case_id: str,
    decision: str,
    reason_codes: tuple[str, ...] = (),
    evidence_ids: tuple[str, ...] = (),
    score: float | None = None,
) -> "object":
    """Construct a contract-valid StudyPrediction (local import avoids a cycle)."""
    from research_v2.contracts.types import StudyPrediction

    label = to_contract_decision(decision)
    try:
        return StudyPrediction(
            study_id=STUDY_ID,
            case_id=case_id,
            decision=label,
            score=score,
            reason_codes=tuple(reason_codes),
            evidence_ids=tuple(evidence_ids),
        )
    except ContractError as exc:
        raise LabelError(f"contract violation building prediction for {case_id!r}: {exc}") from exc
