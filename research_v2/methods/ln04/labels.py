"""LN-04 label ontology mapped onto the frozen research_v2 contract space.

Legacy engine decisions (``backend/domain/scaffolding_policy.py`` /
``research/integrations/ln04.py``) use a richer vocabulary than the frozen
contract space ``research_v2.contracts.label_space.LN04_DECISIONS``. This module
owns the single deterministic mapping. Unknown labels raise ``LabelSpaceError``
rather than being silently coerced.
"""
from __future__ import annotations

from dataclasses import dataclass

from research_v2.contracts.label_space import (
    LN04_DECISIONS,
    LabelSpaceError,
    validate_decision,
)

STUDY_ID = "LN-04"

# Contract space (frozen in research_v2.contracts.label_space):
#   hint | socratic_question | abstain_insufficient_source |
#   reject_injection | direct_answer
CONTRACT_DECISIONS: frozenset[str] = LN04_DECISIONS

# Legacy decisions produced by the observed engine (informational; the mapping
# below is the authoritative transformation).
LEGACY_DECISIONS: frozenset[str] = frozenset(
    {
        "hint_then_fade",
        "restrict_leakage",
        "abstain_source_gap",
        "reject_injection",
        "deterministic_fallback",
        "direct_answer",
    }
)

#: Deterministic mapping from legacy engine labels to contract labels.
LEGACY_TO_CONTRACT: dict[str, str] = {
    "hint_then_fade": "socratic_question",
    "restrict_leakage": "hint",
    "abstain_source_gap": "abstain_insufficient_source",
    "reject_injection": "reject_injection",
    "deterministic_fallback": "abstain_insufficient_source",
    "direct_answer": "direct_answer",
}

VERIFIED_SOURCE_STATUSES: frozenset[str] = frozenset({"verified", "editor_reviewed"})


@dataclass(frozen=True)
class LabelInfo:
    decision: str
    stage: str
    leak_answer: bool
    cites_source: bool


STAGE_BY_DECISION: dict[str, str] = {
    "hint": "scaffold_redirect",
    "socratic_question": "observation_evidence_reasoning",
    "abstain_insufficient_source": "epistemic_gate",
    "reject_injection": "instruction_boundary",
    "direct_answer": "answer_release",
}


def validate_contract_decision(decision: str) -> None:
    """Raise ``LabelSpaceError`` when ``decision`` is outside the LN-04 space."""
    validate_decision(STUDY_ID, decision)


def map_legacy_decision(legacy: str) -> str:
    """Deterministically translate a legacy engine label to a contract label."""
    mapped = LEGACY_TO_CONTRACT.get(str(legacy))
    if mapped is None:
        raise LabelSpaceError(f"LN-04: unknown legacy decision {legacy!r}")
    validate_contract_decision(mapped)
    return mapped


def describe(decision: str) -> LabelInfo:
    """Pedagogical stage / leak / citation metadata for a contract decision."""
    validate_contract_decision(decision)
    return LabelInfo(
        decision=decision,
        stage=STAGE_BY_DECISION[decision],
        leak_answer=decision == "direct_answer",
        cites_source=decision in ("hint", "socratic_question"),
    )
