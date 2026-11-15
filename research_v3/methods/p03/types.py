"""P03 typed inputs/outputs and typed failures (METHOD.md sections 1-2).

Pure dataclasses; no oracle access, no gold labels in inputs.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

PROVENANCE_STATUSES = frozenset({"verified", "unverified", "quarantined"})
ACTIONS = frozenset(
    {
        "hint",
        "socratic_question",
        "request_source",
        "abstain_insufficient_evidence",
        "reject_injection",
        "answer_with_evidence",
    }
)
# ABSTAIN is explicitly distinct from a negative prediction; NOT_APPLICABLE is
# distinct from both (used when a case cannot be scored at all).
NOT_APPLICABLE = "NOT_APPLICABLE"
ABSTAIN = "abstain_insufficient_evidence"


class MalformedSourceError(ValueError):
    """A retrieved source record violates the schema; fail-closed, never coerced."""


@dataclass(frozen=True)
class SourceRecord:
    """One retrieved evidence record. Text is an UNTRUSTED channel."""

    source_id: str
    text: str
    provenance_status: str
    retrieval_confidence: float = 0.0

    def __post_init__(self) -> None:
        if not self.source_id:
            raise MalformedSourceError("source_id must be non-empty")
        if not isinstance(self.text, str):
            raise MalformedSourceError(
                f"source {self.source_id}: text must be str, got {type(self.text).__name__}"
            )
        if self.provenance_status not in PROVENANCE_STATUSES:
            raise MalformedSourceError(
                f"source {self.source_id}: provenance_status must be one of "
                f"{sorted(PROVENANCE_STATUSES)}, got {self.provenance_status!r}"
            )
        if not (0.0 <= float(self.retrieval_confidence) <= 1.0):
            raise MalformedSourceError(
                f"source {self.source_id}: retrieval_confidence must be in [0,1]"
            )

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "SourceRecord":
        if not isinstance(raw, Mapping):
            raise MalformedSourceError(f"source record must be a mapping, got {type(raw).__name__}")
        missing = {"source_id", "text", "provenance_status"} - set(raw)
        if missing:
            raise MalformedSourceError(f"source record missing required keys {sorted(missing)}")
        return cls(
            source_id=str(raw["source_id"]),
            text=str(raw["text"]),
            provenance_status=str(raw["provenance_status"]),
            retrieval_confidence=float(raw.get("retrieval_confidence", 0.0)),
        )


@dataclass(frozen=True)
class TutorDecisionInput:
    """Typed policy input. Contains NO gold labels by construction."""

    case_id: str
    learner_turn: str
    sources: tuple[SourceRecord, ...]
    stage: str  # observation | evidence | reasoning
    wants_answer: bool = False
    stage_score: float = 0.0  # curriculum-provided 0..1, not gold-derived

    def __post_init__(self) -> None:
        if not self.case_id:
            raise MalformedSourceError("case_id must be non-empty")
        if self.stage not in {"observation", "evidence", "reasoning"}:
            raise MalformedSourceError(
                f"stage must be observation|evidence|reasoning, got {self.stage!r}"
            )
        if not (0.0 <= float(self.stage_score) <= 1.0):
            raise MalformedSourceError("stage_score must be in [0,1]")


@dataclass(frozen=True)
class TutorDecision:
    """Typed policy output with explicit reason codes and cite-only provenance."""

    case_id: str
    action: str
    reason_codes: tuple[str, ...]
    evidence_ids: tuple[str, ...] = ()
    p_answer: float | None = None
    abstained: bool = False
    refused: bool = False
    meta: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.action not in ACTIONS:
            raise MalformedSourceError(f"unknown action {self.action!r}")
        if self.action == ABSTAIN and not self.abstained:
            raise MalformedSourceError("abstain action must set abstained=True")
        if self.action == "reject_injection" and not self.refused:
            raise MalformedSourceError("reject_injection must set refused=True")
        # Note: an answer action MAY carry empty evidence_ids; baselines C0/C1
        # are ungrounded by construction and the grounding/false-citation
        # metrics penalize them. The PROPOSED policy enforces citation at its
        # own gates (G2/G4/G5 always attach verified ids when answering).


def verified_source_ids(sources: Sequence[SourceRecord]) -> tuple[str, ...]:
    return tuple(s.source_id for s in sources if s.provenance_status == "verified")
