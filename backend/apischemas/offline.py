# -*- coding: utf-8 -*-
"""Pydantic schemas for offline write queue idempotency and synchronization.

Ticket: V5-T056 (Wave W05, Slot A06)
Supports offline queues in mobile/lib/core/ and frontend/src/lib/imperial/offline-sync.ts:
- Tracks queued offline actions (inspections, submissions, progression)
- Retry logic and exponential backoff tracking
- Conflict resolution (server state preserved, client draft updated)
- Server ACK with server IDs and status
- Client idempotency keys preventing replay abuse / duplicate XP
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class OfflineBaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class OfflineOperationItem(OfflineBaseSchema):
    """Single queued operation item from mobile or frontend offline queue."""

    operation_id: str = Field(..., description="Unique client-generated operation ID")
    resource: str = Field(
        ...,
        description="Resource or action type: 'inspection', 'submission', 'progression', 'quiz_submit', 'complete_lesson', 'discover'",
    )
    payload: dict[str, Any] = Field(default_factory=dict, description="Action payload data")
    created_at: Optional[datetime] = Field(default=None, description="Timestamp recorded when action was queued offline")
    idempotency_key: Optional[str] = Field(default=None, description="Client idempotency key for deduplication")


class OfflineOperationResult(OfflineBaseSchema):
    """Server-authoritative acknowledgment report for an offline operation."""

    operation_id: str = Field(..., description="Matching client operation ID")
    resource: str = Field(..., description="Handled resource type")
    status: str = Field(
        ...,
        description="Sync status: 'synced' (created), 'acknowledged' (idempotent duplicate), 'updated' (pending submission updated), 'conflict' (graded or state conflict resolved), 'failed' (validation/error)",
    )
    idempotency_key: Optional[str] = Field(default=None, description="Echoed idempotency key")
    xp_awarded: int = Field(default=0, ge=0, description="XP awarded for this action (0 on duplicate retries)")
    server_ack: Optional[dict[str, Any]] = Field(default=None, description="Detailed server response payload")
    conflict_resolution: Optional[str] = Field(default=None, description="Explanation of conflict resolution strategy if applicable")
    error: Optional[str] = Field(default=None, description="Error message if status is 'failed'")


class OfflineSyncRequest(OfflineBaseSchema):
    """Offline sync request accepting either a single operation or a batch."""

    operation_id: Optional[str] = None
    resource: Optional[str] = None
    payload: Optional[dict[str, Any]] = None
    created_at: Optional[datetime] = None
    idempotency_key: Optional[str] = None
    operations: Optional[list[OfflineOperationItem]] = None

    @model_validator(mode="before")
    @classmethod
    def normalize_input(cls, data: Any) -> Any:
        if isinstance(data, list):
            return {"operations": data}
        return data


class OfflineSyncResponse(OfflineBaseSchema):
    """Aggregate response returned after synchronizing offline operations."""

    success: bool = True
    operation_id: Optional[str] = None
    status: Optional[str] = None
    resource: Optional[str] = None
    idempotency_key: Optional[str] = None
    xp_awarded: int = 0
    synced_count: int = 0
    acknowledged_count: int = 0
    conflict_count: int = 0
    failed_count: int = 0
    total_xp_awarded: int = 0
    server_ack: Optional[dict[str, Any]] = None
    conflict_resolution: Optional[str] = None
    error: Optional[str] = None
    results: list[OfflineOperationResult] = Field(default_factory=list)
