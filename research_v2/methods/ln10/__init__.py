"""LN-10 — Process-Verifiable Self-Regulated Learning with Reflection Gates.

Method package for the Research V2 study LN-10. The proposed policy is a
Zimmerman cyclical SRL state machine with mandatory reflection gates,
ownership checks, optimistic concurrency (compare-and-swap) and an explicit
two-conflicting-offline-edits detector: concurrent conflicting edits to the
same version are rejected/postponed into a visible conflict-resolution state,
never silently applied.
"""
from research_v2.methods.ln10.labels import (
    CONTRACT_DECISIONS,
    NATIVE_DECISIONS,
    NATIVE_TO_CONTRACT,
    Decision,
    LabelError,
    to_contract_decision,
)

__all__ = [
    "CONTRACT_DECISIONS",
    "NATIVE_DECISIONS",
    "NATIVE_TO_CONTRACT",
    "Decision",
    "LabelError",
    "to_contract_decision",
]
