# -*- coding: utf-8 -*-
"""Pydantic request/response schemas for Research Factory P11 Releases (V5-T079 / W07-A09)."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ReleasePreflightIn(BaseModel):
    story_ids: list[UUID] = Field(..., min_length=1, description="List of HistoryStory UUIDs to validate.")
    claim_ids: Optional[list[UUID]] = Field(default=None, description="Optional extra claims to validate.")
    scope: str = Field(default="cuu_dinh_162_motifs", description="Target content scope identifier.")
    allow_unreviewed: bool = Field(default=False, description="Flag for emergency/preview validation.")


class ReleasePreflightReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    can_publish: bool
    scope: str
    manifest_sha256: str
    stories_count: int
    claims_count: int
    sources_count: int
    assets_count: int
    checks: dict[str, bool]
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ReleaseCreateIn(BaseModel):
    release_code: str = Field(..., min_length=3, max_length=64, description="Unique human-readable release identifier.")
    story_ids: list[UUID] = Field(..., min_length=1, description="List of HistoryStory UUIDs to atomically publish.")
    scope: str = Field(default="cuu_dinh_162_motifs", description="Content scope.")
    previous_release_id: Optional[UUID] = Field(default=None, description="Explicit previous release pointer.")
    allow_unreviewed: bool = Field(default=False, description="Whether to bypass draft checks (strictly for tests/preview).")
    simulate_failure_at_story_idx: Optional[int] = Field(
        default=None, description="Negative abuse test flag to simulate mid-release crash and verify rollback."
    )


class ReleaseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    release_code: str
    scope: str
    status: str
    manifest_sha256: str
    signed_revision: str
    signer_identity: str
    signer_role: str
    previous_release_id: Optional[UUID] = None
    published_at: Optional[datetime] = None
    invalidated_at: Optional[datetime] = None
    rolled_back_at: Optional[datetime] = None
    cache_purge_status: str
    purged_at: Optional[datetime] = None
    stories_count: int = 0
    created_at: datetime


class ReleaseDetailOut(ReleaseOut):
    snapshot_payload: dict[str, Any] = Field(default_factory=dict)


class ReleaseInvalidateIn(BaseModel):
    trigger_type: str = Field(
        default="RIGHTS_EXPIRATION",
        pattern="^(RIGHTS_EXPIRATION|SCHOLARLY_RETRACTION|CORRECTION_TRIAGE|LINK_404|MALFORMED_CLAIM|MANUAL)$",
        description="Reason trigger for invalidation.",
    )
    rationale: str = Field(..., min_length=5, description="Audited explanation of the retraction.")
    story_id: Optional[UUID] = None
    claim_id: Optional[UUID] = None
    source_id: Optional[UUID] = None
    entity_slug: Optional[str] = None


class InvalidationResultOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    release_id: UUID
    trigger_type: str
    rationale: str
    invalidated_story_ids: list[UUID] = Field(default_factory=list)
    invalidated_claim_ids: list[UUID] = Field(default_factory=list)
    revoked_source_ids: list[UUID] = Field(default_factory=list)
    purged_cache_keys: list[str] = Field(default_factory=list)
    timestamp: datetime


class ReleaseRollbackIn(BaseModel):
    rollback_reason: str = Field(..., min_length=5, description="Audited reason for rolling back this publication release.")
    restore_release_id: Optional[UUID] = Field(default=None, description="Optional specific previous release to restore.")


class RollbackResultOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    rolled_back_release_id: UUID
    release_code: str
    rollback_reason: str
    restored_release_id: Optional[UUID] = None
    reverted_stories_count: int
    purged_cache_keys: list[str] = Field(default_factory=list)
    timestamp: datetime


class ReleaseAuditOut(BaseModel):
    release_id: UUID
    release_code: str
    corrections: list[dict[str, Any]] = Field(default_factory=list)
    cache_purges: list[dict[str, Any]] = Field(default_factory=list)
