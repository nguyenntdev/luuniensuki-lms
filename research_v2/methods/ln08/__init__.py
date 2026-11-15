"""LN-08 — Evidence-Calibrated Diagnostic Feedback for Historical Reasoning.

Method package for the Research V2 study LN-08. The proposed policy performs
evidence-calibrated diagnostic classification of historical answers: strict
precedence of source-linkage verification, negation/contradiction parsing
(keyword-complete-but-reversed answers are contradictions, never supported),
partial-reasoning detection, synonym-equivalence recognition, then canonical
keyword support, with calibrated abstention for unrecognised forms.
"""
from research_v2.methods.ln08.labels import (
    NATIVE_DECISIONS,
    NATIVE_TO_CONTRACT,
    Decision,
    LabelError,
    to_contract_decision,
)

__all__ = [
    "NATIVE_DECISIONS",
    "NATIVE_TO_CONTRACT",
    "Decision",
    "LabelError",
    "to_contract_decision",
]
