"""LN-04 — Source-Grounded Socratic Tutoring and Instruction Boundary Enforcement.

Method package for Research V2 study ``LN-04``. All methods implement the frozen
``predict_batch`` ABI over ``research_v2.contracts.types`` and emit decisions in
the contract label space declared in ``research_v2.contracts.label_space``.

Scientific labeling: every method here is a deterministic heuristic policy.
``baselines_c1`` is a rule-based SIMULATED generic-LLM proxy (reason codes
prefixed ``simulated``). No module in this package performs real-LLM inference,
and no result may be reported as real-LLM evaluation.
"""
from __future__ import annotations

from .labels import (
    CONTRACT_DECISIONS,
    LEGACY_DECISIONS,
    LEGACY_TO_CONTRACT,
    STUDY_ID,
    map_legacy_decision,
    validate_contract_decision,
)

__all__ = [
    "STUDY_ID",
    "CONTRACT_DECISIONS",
    "LEGACY_DECISIONS",
    "LEGACY_TO_CONTRACT",
    "map_legacy_decision",
    "validate_contract_decision",
]
