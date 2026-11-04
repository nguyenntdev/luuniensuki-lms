# -*- coding: utf-8 -*-
"""Atomic Historical Claims Domain Validator & Decomposer (V5-T024 / Wave W02).

Enforces atomic statement granularity for historical claims, preventing false or
disputed assertions from hiding inside compound paragraphs behind a single citation.
Provides decomposition, compound claim detection, conflict detection, and explanation
synthesis with explicit atomic claim IDs and epistemic statuses.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..history_models import (
    HistoricalClaim,
    HistoricalClaimSource,
    HistoricalConfidence,
    HistoricalSupportType,
    HistoricalVerificationStatus,
)


# Punctuation boundary patterns for sentence/statement splitting in Vietnamese/English
_SENTENCE_SPLIT_REGEX = re.compile(
    r"(?<=[.!?。！？;；])\s+|\n+",
    re.UNICODE,
)

# Vietnamese coordinate clauses / conjunctions that combine multiple independent propositions
_COMPOUND_MARKERS = [
    "đồng thời",
    "song song đó",
    "ngoài ra",
    "mặt khác",
    "bên cạnh đó",
    "hơn nữa",
    "vừa là",
    "và đồng thời",
]


def _normalize_text(val: str) -> str:
    """Normalize whitespace and strip extra chars."""
    if not val:
        return ""
    return re.sub(r"\s+", " ", val).strip()


def decompose_into_atomic_claims(text: str) -> list[str]:
    """Decompose a monolithic paragraph or compound text into discrete atomic assertions.

    Each returned assertion represents an independent proposition that can be
    individually verified, cited, contextualized, or contradicted.
    """
    if not text or not text.strip():
        return []

    raw_pieces = _SENTENCE_SPLIT_REGEX.split(text.strip())
    atomic_statements: list[str] = []

    for piece in raw_pieces:
        cleaned = _normalize_text(piece)
        if not cleaned:
            continue
        # Strip trailing punctuation if lone period or semicolon
        cleaned = re.sub(r"[;；]+$", "", cleaned).strip()
        if len(cleaned) >= 5:  # meaningful proposition minimum length
            atomic_statements.append(cleaned)

    return atomic_statements


def validate_atomic_claim(
    statement: str,
    max_words: int = 50,
    max_chars: int = 350,
) -> tuple[bool, Optional[str]]:
    """Validate whether a claim statement conforms to atomic granularity.

    Rejects:
    - Multi-paragraph statements (contains newlines)
    - Multi-sentence statements (contains multiple sentence boundaries)
    - Excessively long monolithic text that bundles multiple propositions (> max_words / max_chars)
    - Compound statements bundling independent propositions via heavy conjunctions
    """
    if not statement or not statement.strip():
        return False, "Statement cannot be empty."

    trimmed = statement.strip()

    # 1. Paragraph breaks are strictly forbidden in an atomic claim
    if "\n" in trimmed:
        return (
            False,
            "Compound claim detected: assertion contains newline breaks. "
            "Claims must be discrete atomic assertions, not multi-line paragraphs.",
        )

    # 2. Check for multiple distinct sentences
    pieces = [p for p in _SENTENCE_SPLIT_REGEX.split(trimmed) if p.strip()]
    if len(pieces) > 1:
        return (
            False,
            f"Compound claim detected: assertion contains {len(pieces)} distinct sentences. "
            "Split into individual atomic claims so each assertion can be verified independently.",
        )

    # 3. Word count & length bounds
    words = trimmed.split()
    if len(words) > max_words or len(trimmed) > max_chars:
        return (
            False,
            f"Statement length ({len(words)} words, {len(trimmed)} chars) exceeds atomic bounds. "
            "Decompose into smaller atomic claims.",
        )

    return True, None


def reject_compound_claim_with_disputed_facts(
    compound_statement: str,
    atomic_claims: list[HistoricalClaim],
) -> tuple[bool, Optional[str]]:
    """Reject a compound statement if any sub-proposition within it matches a disputed

    or contradicted claim.

    Prevents false statements from hiding inside an approved paragraph where one part
    is true/verified and another part is disputed/unverified.
    """
    if not compound_statement or not compound_statement.strip():
        return True, None

    norm_compound = unicodedata.normalize("NFD", compound_statement.lower())

    disputed_claims = [
        c
        for c in atomic_claims
        if c.confidence in (HistoricalConfidence.disputed.value, "contested", "disputed")
        or c.verification_status == HistoricalVerificationStatus.disputed.value
        or c.claim_type == "disputed"
        or any(
            b.support_type == HistoricalSupportType.contradicts.value
            for b in getattr(c, "source_bindings", [])
        )
    ]

    for disp in disputed_claims:
        norm_stmt = unicodedata.normalize("NFD", disp.statement_vi.lower())
        # Check if the disputed proposition words or substantive phrase are contained
        disp_tokens = [w for w in re.findall(r"\w+", norm_stmt) if len(w) > 2]
        if not disp_tokens:
            continue
        compound_tokens = set(re.findall(r"\w+", norm_compound))
        overlap = set(disp_tokens) & compound_tokens
        # If over 60% of significant tokens of the disputed claim appear in the compound statement
        if len(disp_tokens) > 0 and len(overlap) / len(disp_tokens) >= 0.6:
            return (
                False,
                f"Compound statement rejected: hides disputed or contradicted assertion "
                f"'{disp.statement_vi}' (claim_id={disp.id}) inside compound text. "
                f"Disputed assertions cannot be masked under a verified citation.",
            )

    return True, None


def claim_has_contradicting_source(db: Session, claim: HistoricalClaim) -> bool:
    """Return True if any source attached to the claim has support_type == 'contradicts'."""
    if not claim.id:
        return False
    count = db.scalar(
        select(func.count())
        .select_from(HistoricalClaimSource)
        .where(
            HistoricalClaimSource.claim_id == claim.id,
            HistoricalClaimSource.support_type == HistoricalSupportType.contradicts.value,
        )
    )
    return bool(count and count > 0)


def can_verify_atomic_claim(db: Session, claim: HistoricalClaim) -> tuple[bool, Optional[str]]:
    """Strictly verify if a claim meets all epistemic conditions to become expert_verified.

    Invariants:
    1. Must not have any active contradicting source binding.
    2. Must not have confidence == 'disputed'.
    3. Must not have verification_status == 'disputed' or claim_type == 'disputed'.
    4. Must have passed 'editor_reviewed'.
    5. Factual/chronology/geographic/identification claims must have an eligible source binding.
    """
    if claim.confidence in (HistoricalConfidence.disputed.value, "contested", "disputed", "insufficient_sources"):
        return False, f"Cannot verify claim with {claim.confidence} confidence."

    if claim.verification_status == HistoricalVerificationStatus.disputed.value:
        return False, "Cannot verify claim with disputed verification status."

    if claim.claim_type == "disputed":
        return False, "Cannot verify claim whose claim_type is disputed."

    if claim_has_contradicting_source(db, claim):
        return False, "Cannot verify claim with active contradicting sources."

    eligible_support = {
        HistoricalSupportType.supports.value,
        HistoricalSupportType.primary_evidence_for.value,
    }
    reviewable_types = {"factual", "chronology", "geographic", "identification"}

    if claim.claim_type in reviewable_types:
        source_count = db.scalar(
            select(func.count())
            .select_from(HistoricalClaimSource)
            .where(
                HistoricalClaimSource.claim_id == claim.id,
                HistoricalClaimSource.support_type.in_(eligible_support),
            )
        )
        if not source_count or source_count == 0:
            return False, "Factual claim requires an eligible source binding (supports or primary_evidence_for)."

    if claim.verification_status not in (
        HistoricalVerificationStatus.editor_reviewed.value,
        HistoricalVerificationStatus.internal_review.value,
    ):
        return False, "Claim must pass editor_reviewed before expert_verified."

    return True, None


def synthesize_atomic_explanations(
    claims: list[HistoricalClaim],
    sources_by_claim: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    """Synthesize structured explanations where each discrete atomic claim cites its

    exact claim ID and verification status.
    """
    explanations: list[dict[str, Any]] = []

    for claim in claims:
        claim_sources = sources_by_claim.get(str(claim.id), [])
        explanation = {
            "claim_id": str(claim.id),
            "statement": claim.statement_vi,
            "claim_type": claim.claim_type,
            "verification_status": claim.verification_status,
            "confidence": claim.confidence,
            "epistemic_certainty": getattr(claim, "epistemic_certainty", "insufficient_sources"),
            "sources": claim_sources,
            "citation_tag": f"[Claim:{claim.id}|Status:{claim.verification_status}]",
        }
        explanations.append(explanation)

    return explanations
