# -*- coding: utf-8 -*-
"""Pydantic v2 schemas for STTT Imperial City offline batch sync (STTT-SPEC-PWA-PRINT-001).

Supports offline-first queued submissions from PWA / Service Worker IndexedDB queue:
- ImperialOfflineSubmissionItem: single queued submission item from client IndexedDB.
- ImperialSyncItemResult: per-item synchronization result with server ID and status.
- ImperialBatchSyncRequest: batch payload with list of submission items.
- ImperialBatchSyncResponse: aggregate counts and per-item results.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ImperialBaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ImperialOfflineSubmissionItem(ImperialBaseSchema):
    """Queued submission item stored in client IndexedDB while offline."""

    id: str = Field(..., description="Client-side queued submission identifier (UUID or local string)")
    activity_id: UUID = Field(..., description="Imperial inquiry activity UUID")
    answer_text: str = Field(..., min_length=1, description="Student's answer text or reflection")
    evidence_refs: list[Any] = Field(
        default_factory=list,
        description="List of primary source or media citations / evidence items",
    )
    client_timestamp: datetime = Field(
        ...,
        description="ISO 8601 timestamp when student recorded the submission offline",
    )
    classroom_id: Optional[UUID] = Field(
        default=None,
        description="Optional classroom identifier if student is participating in an assignment",
    )


class ImperialSyncItemResult(ImperialBaseSchema):
    """Per-item synchronization status report."""

    client_id: str = Field(..., description="Matching client-side queued item ID")
    server_id: Optional[UUID] = Field(
        default=None,
        description="Server UUID of the persisted or acknowledged ImperialSubmission",
    )
    status: str = Field(
        ...,
        description="Item sync status: 'synced' (new), 'acknowledged' (idempotent duplicate), 'updated' (content changed), or 'failed' (invalid)",
    )
    activity_id: Optional[UUID] = Field(
        default=None,
        description="Activity UUID associated with this submission item",
    )
    error: Optional[str] = Field(
        default=None,
        description="Failure details or validation error if status == 'failed'",
    )


class ImperialBatchSyncRequest(ImperialBaseSchema):
    """Batch payload sent when client regains connectivity."""

    items: list[ImperialOfflineSubmissionItem] = Field(
        default_factory=list,
        description="List of offline submissions to synchronize",
    )

    @model_validator(mode="before")
    @classmethod
    def populate_items(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Allow 'submissions' as alias for 'items'
            if "items" not in data and "submissions" in data:
                data["items"] = data["submissions"]
        elif isinstance(data, list):
            # If payload was a bare list of items, wrap it
            data = {"items": data}
        return data


class ImperialBatchSyncResponse(ImperialBaseSchema):
    """Aggregate response returned after batch synchronization."""

    synced_count: int = Field(
        default=0,
        ge=0,
        description="Count of successfully synced, acknowledged, or updated submissions",
    )
    failed_count: int = Field(
        default=0,
        ge=0,
        description="Count of rejected or failed submission items",
    )
    results: list[ImperialSyncItemResult] = Field(
        default_factory=list,
        description="Per-item synchronization results with server IDs and status",
    )
