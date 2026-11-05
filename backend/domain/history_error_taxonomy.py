# -*- coding: utf-8 -*-
"""History Error Taxonomy and Diagnostic Models (LN-08 / Study 08).

Defines the historical misconception and reasoning error taxonomy:
- Logical Negation / Contradiction (phủ định biến câu đúng thành sai)
- Source Mismatch / Citation Fabrication (nguồn không hỗ trợ nhận định)
- Semantic & Synonym Equivalence (diễn đạt khác nhưng cùng mệnh đề)
- Partial / Incomplete Reasoning (thiếu liên kết nhân quả hoặc không gian - nghi lễ)
- Temporal Anachronism & Causal Reversal (lệch niên đại, đảo quan hệ)

Adheres strictly to LN-08 invariants:
- INV-LN-08-01: Keyword matching alone must NEVER grant correctness.
- INV-LN-08-02: Ambiguous / unknown text must abstain without personal competence judgments.
- INV-LN-08-03: No claim of source support without verified locator.
- INV-LN-08-04: Feedback adheres to task boundary and disclosure limit.
- INV-LN-08-05: Synthetic fixtures are isolated from real learner data.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class HistoricalErrorType(str, Enum):
    """Taxonomy of reasoning faults in historical domain assessments."""
    NONE = "none"
    LOGICAL_NEGATION = "logical_negation"
    SOURCE_MISMATCH = "source_mismatch"
    SYNONYM_EQUIVALENCE = "synonym_equivalence"
    PARTIAL_REASONING = "partial_reasoning"
    TEMPORAL_ANACHRONISM = "temporal_anachronism"
    CAUSAL_REVERSAL = "causal_reversal"
    CONTRADICTION = "contradiction"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    UNKNOWN = "unknown"


class DiagnosticDecision(str, Enum):
    """Decision outcomes for historical diagnostic evaluation."""
    FEEDBACK_SUPPORTED = "feedback_supported"
    CLASSIFY_CONTRADICTION = "classify_contradiction"
    CLASSIFY_SOURCE_ERROR = "classify_source_error"
    PRESERVE_SEMANTICS = "preserve_semantics"
    FEEDBACK_INCOMPLETE = "feedback_incomplete"
    ABSTAIN = "abstain"


class DiagnosticCategory(str, Enum):
    """Standardized diagnostic category mapping for metric derivation."""
    CONTRADICTION = "contradiction"
    SOURCE_ERROR = "source_error"
    SUPPORTED_EQUIVALENT = "supported_equivalent"
    INCOMPLETE = "incomplete"
    SUPPORTED = "supported"
    KEYWORD_MATCH = "keyword_match"
    KEYWORD_MISSING = "keyword_missing"
    UNCLASSIFIED = "unclassified"


@dataclass(frozen=True)
class AnswerEvidence:
    """Historical evidence linked with student response."""
    question_id: str
    answer_text: str
    claim_id: Optional[str] = None
    source_id: Optional[str] = None
    verified: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DiagnosticTag:
    """Fine-grained tag on detected error span and rationale."""
    code: str
    error_type: HistoricalErrorType
    confidence: float
    span: str
    evidence: str
    actionable_hint: str


@dataclass(frozen=True)
class FeedbackTemplate:
    """Pedagogical guidance focused on task and process, not personal judgment."""
    error_type: HistoricalErrorType
    action_hint: str
    what_to_verify: str
    disclosure_limit: str = "task_boundary_only"


@dataclass(frozen=True)
class AssessmentDecision:
    """Complete diagnostic assessment output."""
    decision: DiagnosticDecision
    diagnostic_category: DiagnosticCategory
    reason_codes: list[str]
    score: float
    criteria: dict[str, Any]
    diagnostic_tags: list[DiagnosticTag] = field(default_factory=list)
    feedback_message: str = ""
    observables: dict[str, Any] = field(default_factory=dict)
    research_only: bool = True
