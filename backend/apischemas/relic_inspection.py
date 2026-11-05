# -*- coding: utf-8 -*-
"""Pydantic schemas for AR fallback & relic inspection tasks (V5-T045).

Defines the contract for:
- Device capability reporting & mobile performance budget telemetry
- Relic inspection completion requests (WebXR AR or Turntable 2D/3D fallback)
- Equivalent learning verification responses
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class RelicInspectionCompleteRequest(BaseModel):
    """Payload submitted when a student completes an inspection of a heritage relic."""

    target_slug: str = Field(
        ...,
        min_length=1,
        max_length=120,
        description="Slug of the relic, urn, motif, or imperial art detail",
    )
    inspection_mode: str = Field(
        ...,
        pattern="^(webxr_ar|quicklook_ar|turntable_3d|turntable_2d|image_fallback|paper_handout|offline_rubbing)$",
        description="Active inspection mode used by the client",
    )
    camera_permission_granted: bool = Field(
        ...,
        description="Whether camera permission was granted by user (False for denied/unsupported fallback)",
    )
    device_tier: Optional[str] = Field(
        default="desktop",
        pattern="^(low_end_mobile|mid_range_mobile|high_end_mobile|desktop|paper_only|none)$",
        description="Client device capability tier classification",
    )
    time_spent_seconds: int = Field(
        ...,
        ge=0,
        description="Total duration spent actively examining the relic in seconds",
    )
    angles_inspected: list[str] = Field(
        default_factory=list,
        description="List of angles or viewports inspected (e.g. front, left, back, right)",
    )
    hotspots_examined: list[str] = Field(
        default_factory=list,
        description="IDs of visual hotspots or relief details scrutinized",
    )
    idempotency_key: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Client-provided unique key to prevent duplicate awards",
    )


class RelicInspectionCompleteResponse(BaseModel):
    """Server-authoritative response verifying completion of the inspection task."""

    success: bool = True
    task_id: UUID
    target_slug: str
    target_title: str
    inspection_mode: str
    camera_permission_granted: bool
    equivalent_learning_completed: bool = True
    xp_awarded: int
    total_xp: int
    already_completed: bool = False
    feedback: str
    recorded_at: datetime


class RelicInspectionStatusResponse(BaseModel):
    """Status check query for whether a student has completed relic inspection."""

    target_slug: str
    is_completed: bool
    completed_mode: Optional[str] = None
    camera_permission_granted: Optional[bool] = None
    xp_earned: int = 0
    completed_at: Optional[datetime] = None
