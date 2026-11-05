# -*- coding: utf-8 -*-
"""P04 Citation and Locator Deterministic Verifier (V5-T076 / AIR-020).

Validates source passage locators, page numbers, quotations, and claim-source
bindings. Deterministically rejects:
- Mismatched or out-of-bounds page numbers (negative abuse EV-001/002).
- Uncorroborated claims without verified source bindings or quotations.
- Incompatible support types attempting factual verification.
"""
from __future__ import annotations

import re
import uuid
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import UUID

from pydantic import BaseModel, Field

from ...history_models import (
    HistoricalClaim,
    HistoricalClaimSource,
    HistoricalSource,
    HistoricalSupportType,
    HistoricalVerificationStatus,
)


class ResearchFactoryCitationError(Exception):
    """Base exception for citation and locator verification failures."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class MismatchedPageCitationError(ResearchFactoryCitationError):
    """Raised when a citation references a page outside source boundaries or mismatching content."""
    pass


class UncorroboratedClaimCitationError(ResearchFactoryCitationError):
    """Raised when a factual claim lacks valid, verified citation evidence."""
    pass


class InvalidLocatorFormatError(ResearchFactoryCitationError):
    """Raised when a locator string or structure is malformed."""
    pass


class CitationValidationResult(BaseModel):
    is_valid: bool
    source_id: str
    locator_type: str
    page_start: Optional[int] = None
    page_end: Optional[int] = None
    volume: Optional[str] = None
    normalized_locator: str
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)


def parse_page_range(raw_pages: Optional[str]) -> Tuple[Optional[int], Optional[int]]:
    """Parses page strings like '45', '45-48', 'pp. 102-105', 'tờ 14a-14b' into start/end integers."""
    if not raw_pages:
        return None, None

    cleaned = str(raw_pages).strip().lower()
    # Remove common prefixes
    cleaned = re.sub(r'^(trang|tr\.|pp\.|p\.|tờ)\s*', '', cleaned)

    # Match simple range e.g. "45-48" or single "45"
    match_range = re.search(r'(\d+)\s*[-–—]\s*(\d+)', cleaned)
    if match_range:
        return int(match_range.group(1)), int(match_range.group(2))

    match_single = re.search(r'(\d+)', cleaned)
    if match_single:
        val = int(match_single.group(1))
        return val, val

    return None, None


def validate_citation_locator(
    source: HistoricalSource | Dict[str, Any],
    locator: Dict[str, Any],
    claim_type: str = "factual",
) -> CitationValidationResult:
    """Validates citation locator against the source's recorded metadata bounds.
    
    Negative abuse enforcement:
    - If source defines a page limit (e.g. 320 pages), page_start or page_end > limit raises MismatchedPageCitationError.
    - If page_start <= 0 or page_start > page_end raises MismatchedPageCitationError.
    - If factual claim has empty quotation and empty locator, raises UncorroboratedClaimCitationError.
    """
    source_id = str(getattr(source, "id", None) or source.get("id", "unknown"))
    source_title = getattr(source, "title", None) or (source.get("title") if isinstance(source, dict) else "Unknown Source")
    source_pages_raw = getattr(source, "pages", None) or (source.get("pages") if isinstance(source, dict) else None)
    total_pages_bound: Optional[int] = None

    if source_pages_raw:
        _, max_p = parse_page_range(source_pages_raw)
        total_pages_bound = max_p

    locator_type = locator.get("locator_type") or "page"
    page_start_val = locator.get("page_start")
    page_end_val = locator.get("page_end")
    volume = locator.get("volume")
    raw_locator_str = locator.get("locator") or locator.get("locator_index") or ""
    quotation_excerpt = locator.get("quotation_excerpt") or locator.get("quote_transcription") or ""

    p_start, p_end = None, None
    if page_start_val is not None:
        try:
            p_start = int(page_start_val)
        except (ValueError, TypeError):
            p_start, _ = parse_page_range(str(page_start_val))
    if page_end_val is not None:
        try:
            p_end = int(page_end_val)
        except (ValueError, TypeError):
            _, p_end = parse_page_range(str(page_end_val))

    if p_start is None and raw_locator_str:
        p_start, p_end = parse_page_range(raw_locator_str)

    # Validate numerical boundaries
    if p_start is not None:
        if p_start <= 0:
            raise MismatchedPageCitationError(
                f"Page start must be positive, got {p_start} for source '{source_title}' (id={source_id})",
                {"source_id": source_id, "page_start": p_start},
            )
        if p_end is not None and p_end < p_start:
            raise MismatchedPageCitationError(
                f"Page end ({p_end}) cannot be less than page start ({p_start}) for source '{source_title}'",
                {"source_id": source_id, "page_start": p_start, "page_end": p_end},
            )
        if total_pages_bound is not None and p_start > total_pages_bound:
            raise MismatchedPageCitationError(
                f"Mismatched citation page: page {p_start} exceeds known edition boundary ({total_pages_bound} pages) for '{source_title}'",
                {"source_id": source_id, "page_start": p_start, "source_pages_bound": total_pages_bound},
            )
        if total_pages_bound is not None and p_end is not None and p_end > total_pages_bound:
            raise MismatchedPageCitationError(
                f"Mismatched citation page: page {p_end} exceeds known edition boundary ({total_pages_bound} pages) for '{source_title}'",
                {"source_id": source_id, "page_end": p_end, "source_pages_bound": total_pages_bound},
            )

    # Check quotation excerpt and uncorroborated citations for factual claims
    if claim_type in ("factual", "chronology", "geographic", "attribution"):
        if not raw_locator_str and p_start is None and not locator.get("folio") and not locator.get("inscription_location"):
            raise UncorroboratedClaimCitationError(
                f"Uncorroborated factual claim: missing specific locator for source '{source_title}'",
                {"source_id": source_id, "claim_type": claim_type},
            )
        if not quotation_excerpt or len(str(quotation_excerpt).strip()) < 3:
            raise UncorroboratedClaimCitationError(
                f"Uncorroborated factual claim: missing quote excerpt for source '{source_title}'",
                {"source_id": source_id, "locator": locator},
            )

    normalized = ""
    if volume:
        normalized += f"Tập {volume}, "
    if p_start is not None and p_end is not None and p_start != p_end:
        normalized += f"tr. {p_start}-{p_end}"
    elif p_start is not None:
        normalized += f"tr. {p_start}"
    elif raw_locator_str:
        normalized += str(raw_locator_str).strip()
    else:
        normalized = "Toàn văn sử liệu"

    return CitationValidationResult(
        is_valid=True,
        source_id=source_id,
        locator_type=locator_type,
        page_start=p_start,
        page_end=p_end,
        volume=str(volume) if volume else None,
        normalized_locator=normalized,
    )


def verify_claim_corroboration_policy(
    claim: HistoricalClaim | Dict[str, Any],
    bindings: List[HistoricalClaimSource | Dict[str, Any]],
    sources_by_id: Dict[str, HistoricalSource | Dict[str, Any]],
) -> Dict[str, Any]:
    """Verifies that a claim has corroborated citations meeting historical policy standards."""
    claim_id = str(getattr(claim, "id", None) or claim.get("id", "unknown"))
    claim_type = getattr(claim, "claim_type", None) or claim.get("claim_type", "factual")
    statement_vi = getattr(claim, "statement_vi", None) or claim.get("statement_vi", "")

    if not bindings:
        raise UncorroboratedClaimCitationError(
            f"Claim '{claim_id}' ({statement_vi[:40]}...) has 0 source bindings.",
            {"claim_id": claim_id, "claim_type": claim_type},
        )

    valid_supporting_witnesses = 0
    contradicting_witnesses = 0

    for b in bindings:
        s_id = str(getattr(b, "source_id", None) or b.get("source_id", ""))
        src = sources_by_id.get(s_id)
        if not src:
            raise UncorroboratedClaimCitationError(
                f"Claim '{claim_id}' references non-existent source '{s_id}'",
                {"claim_id": claim_id, "source_id": s_id},
            )

        if isinstance(b, dict):
            supp_type = b.get("support_type", "supports")
            loc_data = {
                "locator_type": b.get("locator_type"),
                "page_start": b.get("page_start"),
                "page_end": b.get("page_end"),
                "locator": b.get("locator_index") or b.get("locator"),
                "quotation_excerpt": b.get("quotation_excerpt") or b.get("quote_transcription"),
                "volume": b.get("volume"),
                "folio": b.get("folio"),
                "inscription_location": b.get("inscription_location"),
            }
        else:
            supp_type = getattr(b, "support_type", "supports")
            loc_data = {
                "locator_type": getattr(b, "locator_type", None),
                "page_start": getattr(b, "page_start", None),
                "page_end": getattr(b, "page_end", None),
                "locator": getattr(b, "locator_index", None) or getattr(b, "locator", None),
                "quotation_excerpt": getattr(b, "quotation_excerpt", None) or getattr(b, "quote_transcription", None),
                "volume": getattr(b, "volume", None),
                "folio": getattr(b, "folio", None),
                "inscription_location": getattr(b, "inscription_location", None),
            }

        if supp_type == "contradicts":
            contradicting_witnesses += 1
            continue


        # Validate locator bounds
        validate_citation_locator(src, loc_data, claim_type=claim_type)

        if supp_type in ("supports", "primary_evidence_for"):
            valid_supporting_witnesses += 1

    if valid_supporting_witnesses == 0 and claim_type in ("factual", "chronology", "geographic"):
        raise UncorroboratedClaimCitationError(
            f"Claim '{claim_id}' has no verified 'supports' or 'primary_evidence_for' source binding.",
            {"claim_id": claim_id, "bindings_count": len(bindings)},
        )

    return {
        "claim_id": claim_id,
        "is_corroborated": valid_supporting_witnesses > 0,
        "supporting_witness_count": valid_supporting_witnesses,
        "contradicting_witness_count": contradicting_witnesses,
        "has_contradictions": contradicting_witnesses > 0,
    }
