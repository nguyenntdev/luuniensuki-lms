# -*- coding: utf-8 -*-
"""P04–P06 Source/Claim Cross-Check Service Facade (V5-T076 / Wave W07 Slot A06).

Integrates:
- P04: Atomic claims and source binding (citations.py).
- P05: Source independence, mirror detection, and contradictions (corroboration.py).
- P06: Evidence dossier construction, scholarly disputes, and date/place resolution.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ...history_models import (
    HistoricalClaim,
    HistoricalClaimSource,
    HistoricalEntity,
    HistoricalSource,
    HistoricalSupportType,
    HistoricalVerificationStatus,
)
from .citations import (
    CitationValidationResult,
    MismatchedPageCitationError,
    ResearchFactoryCitationError,
    UncorroboratedClaimCitationError,
    validate_citation_locator,
    verify_claim_corroboration_policy,
)
from .corroboration import (
    AnachronisticGeographyError,
    ContradictionRecord,
    ContradictionStatus,
    DisputeCategory,
    DisputedClaimCannotAutoVerifyError,
    MirrorDetectionResult,
    NormalizedEdition,
    OverpreciseChronologyError,
    ScholarlyDispute,
    detect_duplicate_or_mirror_sources,
    dispute_ledger,
    normalize_edition,
    resolve_date_chronology,
    resolve_place_geography,
)


class CrossCheckReport(BaseModel):
    report_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    entity_slug: str
    total_claims: int
    total_sources: int
    independent_sources_count: int
    mirror_sources_detected: int
    verified_citations: int
    contradictions_detected: int
    disputes_tracked: int
    is_fully_corroborated: bool
    summary_sha256: str
    warnings: List[str] = Field(default_factory=list)
    contradiction_records: List[ContradictionRecord] = Field(default_factory=list)
    scholarly_disputes: List[ScholarlyDispute] = Field(default_factory=list)


def bind_claim_source_verified(
    db: Session,
    claim_id: UUID,
    source_id: UUID,
    support_type: str,
    locator: Dict[str, Any],
    actor_id: Optional[UUID] = None,
) -> HistoricalClaimSource:
    """Binds a claim to a source with mandatory locator bounds check and anti-abuse validation.
    
    Negative abuse enforcement:
    - Mismatched page -> raises MismatchedPageCitationError.
    - Missing excerpt for factual claim -> raises UncorroboratedClaimCitationError.
    """
    claim = db.get(HistoricalClaim, claim_id)
    if not claim:
        raise ValueError(f"HistoricalClaim '{claim_id}' not found.")

    source = db.get(HistoricalSource, source_id)
    if not source:
        raise ValueError(f"HistoricalSource '{source_id}' not found.")

    # 1. Deterministic citation and locator validation
    val_res = validate_citation_locator(source, locator, claim_type=claim.claim_type)

    # 2. Check if binding already exists
    existing = db.scalars(
        select(HistoricalClaimSource).where(
            HistoricalClaimSource.claim_id == claim_id,
            HistoricalClaimSource.source_id == source_id,
            HistoricalClaimSource.support_type == support_type,
        )
    ).first()

    page_start = str(val_res.page_start) if val_res.page_start is not None else None
    page_end = str(val_res.page_end) if val_res.page_end is not None else None
    quotation = locator.get("quotation_excerpt") or locator.get("quote_transcription") or ""

    if existing:
        existing.locator_type = val_res.locator_type
        existing.page_start = page_start
        existing.page_end = page_end
        existing.quotation_excerpt = quotation
        db.commit()
        db.refresh(existing)
        return existing

    binding = HistoricalClaimSource(
        claim_id=claim_id,
        source_id=source_id,
        support_type=support_type,
        locator_type=val_res.locator_type,
        page_start=page_start,
        page_end=page_end,
        chapter=locator.get("chapter"),
        section=locator.get("section"),
        folio=locator.get("folio"),
        inscription_location=locator.get("inscription_location"),
        quotation_excerpt=quotation,
        created_by=actor_id,
    )
    db.add(binding)

    # If support_type is 'contradicts', demote verified claim to 'disputed'
    if support_type == "contradicts":
        if claim.verification_status in ("expert_verified", "editor_reviewed", "verified", "published"):
            claim.verification_status = "disputed"
            claim.confidence = "disputed"
            claim.review_notes = f"Automatically demoted to disputed upon attachment of contradicting source {source_id}"

    db.commit()
    db.refresh(binding)
    return binding


def cross_check_entity_claims(
    db: Session,
    entity_slug: str,
) -> CrossCheckReport:
    """Executes full P04–P06 cross-check on all claims and sources for an entity."""
    entity = db.scalars(
        select(HistoricalEntity).where(HistoricalEntity.slug == entity_slug)
    ).first()
    if not entity:
        raise ValueError(f"HistoricalEntity '{entity_slug}' not found.")

    claims = db.scalars(
        select(HistoricalClaim).where(HistoricalClaim.entity_id == entity.id)
    ).all()

    # Collect all sources referenced
    claim_ids = [c.id for c in claims]
    bindings: List[HistoricalClaimSource] = []
    if claim_ids:
        bindings = list(db.scalars(
            select(HistoricalClaimSource).where(HistoricalClaimSource.claim_id.in_(claim_ids))
        ).all())

    source_ids = list({b.source_id for b in bindings})
    sources: List[HistoricalSource] = []
    if source_ids:
        sources = list(db.scalars(
            select(HistoricalSource).where(HistoricalSource.id.in_(source_ids))
        ).all())
    sources_by_id = {str(s.id): s for s in sources}

    # 1. P04 / P05: Normalize editions and detect mirror sources
    mirror_res = detect_duplicate_or_mirror_sources(sources)

    # 2. P04: Validate each claim's citations
    verified_citations = 0
    warnings = list(mirror_res.warnings)

    for c in claims:
        c_bindings = [b for b in bindings if b.claim_id == c.id]
        if c.is_approved:
            # Must satisfy corroboration policy
            verify_claim_corroboration_policy(c, c_bindings, sources_by_id)
            verified_citations += len(c_bindings)

    # 3. P05: Detect contradictions across claims
    contradictions: List[ContradictionRecord] = []
    for b in bindings:
        if b.support_type == "contradicts":
            c = next((item for item in claims if item.id == b.claim_id), None)
            s = sources_by_id.get(str(b.source_id))
            if c and s:
                cr = dispute_ledger.register_contradiction(
                    subject_id=entity_slug,
                    conflict_category="source_contradiction",
                    claim_a=c,
                    claim_b={"id": str(uuid.uuid4()), "statement_vi": s.title},
                    source_a=s,
                    status=ContradictionStatus.OPEN,
                )
                contradictions.append(cr)

    # 4. P06: Gather tracked scholarly disputes
    disputes = dispute_ledger.list_disputes_for_subject(entity_slug)

    # Compute deterministic SHA
    summary_dict = {
        "entity_slug": entity_slug,
        "total_claims": len(claims),
        "total_sources": len(sources),
        "independent_sources": mirror_res.independent_origin_count,
        "contradictions": len(contradictions),
        "disputes": len(disputes),
    }
    summary_sha = hashlib.sha256(
        json.dumps(summary_dict, sort_keys=True).encode("utf-8")
    ).hexdigest()

    return CrossCheckReport(
        entity_slug=entity_slug,
        total_claims=len(claims),
        total_sources=len(sources),
        independent_sources_count=mirror_res.independent_origin_count,
        mirror_sources_detected=len(sources) - mirror_res.independent_origin_count,
        verified_citations=verified_citations,
        contradictions_detected=len(contradictions),
        disputes_tracked=len(disputes),
        is_fully_corroborated=len(contradictions) == 0 and len(claims) > 0,
        summary_sha256=summary_sha,
        warnings=warnings,
        contradiction_records=contradictions,
        scholarly_disputes=disputes,
    )
