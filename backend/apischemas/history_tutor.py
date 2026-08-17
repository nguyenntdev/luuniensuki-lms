# -*- coding: utf-8 -*-
"""History tutor API schemas (Phase 9).

Request/response contract for the source-grounded history tutor (Spec 38).
"""
from __future__ import annotations

from typing import Literal, Optional

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


class HistoryTutorCitation(BaseModel):
    source_id: str
    claim_ids: list[str]
    locator: str


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