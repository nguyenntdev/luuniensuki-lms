"""LN-03 decision labels and typed errors.

Native decisions follow the legacy dual-mode policy engine
(``research/spaced_learning/dual_mode_policy.py``), which the T3 gold oracle
(``PEDAGOGICAL_SPEC_DUAL_MODE`` basis) was generated from:

- ``schedule_eligible``      : due, stable fact base, verified source -> schedule review
- ``assign_fact_retrieval``  : generative task requested before stable fact recall
- ``postpone``               : review not yet due
- ``reject_invalid_scheduler``: non-finite scheduler parameters
- ``block_explanation``      : generative task without verified source

The frozen contract space (``research_v2.contracts.label_space.LN03_DECISIONS``)
declares ``remediate_first``/``reject_missing_fact``/``reject_absent_source``
instead of the legacy engine labels. Native labels are validated against the
native space strictly (unknown labels raise :class:`LabelSpaceError`); the
contract mapping is diagnostic-only and never silently rewrites a decision.
"""
from __future__ import annotations

from enum import Enum

from research_v2.contracts.label_space import (
    LN03_DECISIONS as CONTRACT_DECISIONS,
    LabelSpaceError,
)

STUDY_ID = "LN-03"

#: Native decision labels produced by the LN-03 policies (oracle label space).
class Decision(str, Enum):
    SCHEDULE_ELIGIBLE = "schedule_eligible"
    ASSIGN_FACT_RETRIEVAL = "assign_fact_retrieval"
    POSTPONE = "postpone"
    REJECT_INVALID_SCHEDULER = "reject_invalid_scheduler"
    BLOCK_EXPLANATION = "block_explanation"


NATIVE_DECISIONS: frozenset[str] = frozenset(d.value for d in Decision)

#: Diagnostic mapping native -> contract space (NOT applied automatically).
NATIVE_TO_CONTRACT: dict[str, str] = {
    "schedule_eligible": "schedule_eligible",
    "postpone": "postpone",
    "assign_fact_retrieval": "remediate_first",
    "reject_invalid_scheduler": "reject_missing_fact",
    "block_explanation": "reject_absent_source",
}

#: Contract decisions with no native engine equivalent.
CONTRACT_ONLY_DECISIONS: frozenset[str] = CONTRACT_DECISIONS - set(NATIVE_TO_CONTRACT.values())

#: Reason codes emitted by the legacy rule engine (rule IDs preserved).
REASON_NONFINITE_WEIGHT = "nonfinite_weight"
REASON_NOT_DUE = "not_due"
REASON_MISSING_FACT_BASE = "missing_fact_base"
REASON_ABSENT_SOURCE = "absent_source"
REASON_RULE_ORDER = "RULE-LN-03"

RULE_WEIGHT = "RULE-LN-03-04"
RULE_DUE = "RULE-LN-03-03"
RULE_FACT = "RULE-LN-03-02"
RULE_SOURCE = "RULE-LN-03-05"
RULE_SCHEDULE = "RULE-LN-03-01"


class InvalidLabelError(ValueError):
    """Raised when a policy would emit a decision outside the native space."""


def validate_native_decision(decision: str) -> str:
    """Validate against the native engine space; typed failure on unknown."""
    if decision not in NATIVE_DECISIONS:
        raise InvalidLabelError(
            f"{STUDY_ID}: decision {decision!r} not in native label space {sorted(NATIVE_DECISIONS)}"
        )
    return decision


def validate_contract_decision(decision: str) -> str:
    """Validate against the frozen V2 contract space (diagnostic use)."""
    if decision not in CONTRACT_DECISIONS:
        raise LabelSpaceError(
            f"{STUDY_ID}: decision {decision!r} not in contract label space {sorted(CONTRACT_DECISIONS)}"
        )
    return decision


def native_decision(value: str | Decision) -> str:
    """Coerce an enum or string to a validated native decision string."""
    d = value.value if isinstance(value, Decision) else str(value)
    return validate_native_decision(d)
