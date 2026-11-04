# -*- coding: utf-8 -*-
"""History tutor API schemas (Phase 9).

Request/response contract for the source-grounded history tutor (Spec 38).
"""
from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class HistoryTutorAskIn(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    entity_filter: Optional[str] = Field(
        default=None,
        description="Optional entity slug or UUID to pin entity resolution.",
    )
    include_unverified: bool = Field(
        default=False,
        description=(
            "When true, unreviewed/needs_source claims may be retrieved but are "
            "always clearly labelled as unverified (Spec 37.1)."
        ),
    )
    heritage_scope: Optional[str] = Field(
        default="ALL",
        description="Heritage scope filter: CUU_DINH, RBPC_HUE, or ALL.",
    )
    mode: Optional[Literal["direct", "hint_first", "socratic"]] = Field(
        default="direct",
        description="Learning mode: direct (factual answer) or hint_first / socratic (guided progressive inquiry).",
    )
    hint_level: Optional[int] = Field(
        default=1,
        ge=1,
        le=3,
        description="Progression level for hints: 1 (observation prompt), 2 (source consultation clue), 3 (guided synthesis).",
    )
    inspect_provenance: Optional[bool] = Field(
        default=False,
        description="When true, returns cryptographic SHA-256 provenance chain and primary source verification records.",
    )
    reveal_answer: Optional[bool] = Field(
        default=False,
        description="Explicit flag to reveal the direct answer after reviewing hints.",
    )


class HistoryTutorCitation(BaseModel):
    source_id: str
    claim_ids: list[str]
    locator: str
    source_title: Optional[str] = None
    author: Optional[str] = None
    publication_year: Optional[int] = None
    archive_url: Optional[str] = None
    reliability_level: Optional[str] = None
    verification_status: Optional[str] = None
    provenance_hash: Optional[str] = None


class CitationProvenanceRecord(BaseModel):
    source_id: str
    source_title: str
    author: Optional[str] = None
    publication_year: Optional[int] = None
    volume: Optional[str] = None
    chapter: Optional[str] = None
    pages: Optional[str] = None
    locator: str
    archive_url: Optional[str] = None
    rights_status: str
    verification_status: str
    bound_claims: list[dict[str, Any]] = Field(default_factory=list)
    provenance_hash: str
    is_disputed: bool = False
    epistemic_certainty: str = "su_lieu_xac_thuc"
    provenance_verified: bool = True


class HistoryTutorRelatedEntity(BaseModel):
    id: str
    type: str
    label: str


class HistoryTutorSuggestedAction(BaseModel):
    type: str
    entity_id: Optional[str] = None


class HistoryTutorGrounding(BaseModel):
    claims_retrieved: int
    claims_used: int
    sources_used: int


class HistoryTutorAskOut(BaseModel):
    answer_markdown: str
    confidence: Literal["high", "medium", "low"]
    epistemic_summary: str
    citations: list[HistoryTutorCitation] = Field(default_factory=list)
    related_entities: list[HistoryTutorRelatedEntity] = Field(default_factory=list)
    uncertainties: list[str] = Field(default_factory=list)
    suggested_actions: list[HistoryTutorSuggestedAction] = Field(default_factory=list)
    grounding: HistoryTutorGrounding
    mode: Literal["direct", "hint_first", "socratic"] = "direct"
    socratic_hints: list[str] = Field(default_factory=list)
    observation_prompts: list[str] = Field(default_factory=list)
    motif_guidance: Optional[str] = None
    source_investigation_guidance: Optional[str] = None
    revealed_direct_answer: bool = True
    provenance_records: list[CitationProvenanceRecord] = Field(default_factory=list)