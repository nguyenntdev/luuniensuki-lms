# -*- coding: utf-8 -*-
"""Progress / streak / dashboard / daily-mission / badge / peer-feedback models.

Relocated verbatim from ``backend.main`` (backend-modularization task 4.1).
Field sets, validators, defaults and docstrings are preserved exactly.
``backend.main`` imports these by their original bare names.

Cross-domain references: ``DashboardSummaryOut`` aggregates models that live in
other apischemas submodules (``UrnListItemOut`` from ``.content``,
``CollectionStatsOut``/``QuestSummaryOut`` from ``.quests``, ``RecommendationOut``
from ``.ai``). The import direction is one-way (those modules never import this
one), so there is no circular import.

These models are intentionally distinct from any same-named models in
``backend/schemas.py`` (see ``backend/apischemas/__init__.py``).
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from .ai import RecommendationOut
from .content import UrnListItemOut
from .quests import CollectionStatsOut, QuestSummaryOut


class StreakResponse(BaseModel):
    current_streak: int
    longest_streak: int
    streak_freezes: int
    last_active_at: Optional[datetime] = None
    days_since_last_active: Optional[int] = None


class DashboardPathMotifOut(BaseModel):
    id: UUID
    name: str
    name_en: Optional[str] = None
    display_order: Optional[int] = None
    status: str
    category: Optional[str] = None
    thumbnail_url: Optional[str] = None
    silhouette_url: Optional[str] = None


class DashboardSummaryOut(BaseModel):
    urns: list[UrnListItemOut]
    collection_stats: CollectionStatsOut
    streak: StreakResponse
    quest_summary: Optional[QuestSummaryOut] = None
    recommendations: RecommendationOut
    path_motifs: list[DashboardPathMotifOut]


class StreakFreezeResponse(BaseModel):
    success: bool
    message: str
    streak_freezes_remaining: int
    current_streak: int


class BadgeOut(BaseModel):
    slug: str
    name: str
    description: Optional[str] = None
    icon_url: str
    category: str
    xp_bonus: int
    tier: str = "bronze"  # Default tier for badge


class UserBadgeOut(BaseModel):
    badge: BadgeOut
    earned_at: datetime
    current_tier: str = "bronze"  # User's current tier for this badge


class RankListItemOut(BaseModel):
    level: int
    name: str
    xp: int


class BadgeListItemOut(BaseModel):
    id: UUID
    slug: str
    name: str
    name_en: Optional[str] = None
    description: Optional[str] = None
    icon_url: str
    category: str
    xp_bonus: int


class DailyGoalSettingsOut(BaseModel):
    """User daily-goal settings."""

    goal_level: str
    xp_target: int
    updated_at: datetime
    source: str = "default"


class DailyGoalSettingsUpdateIn(BaseModel):
    """Update payload for daily-goal settings."""

    goal_level: Optional[str] = None
    xp_target: Optional[int] = Field(default=None, ge=1, le=500)


class DailyMissionOut(BaseModel):
    """Schema for a daily mission template."""

    id: UUID
    slug: str
    name: str
    description: str
    mission_type: str
    target_count: int
    xp_reward: int
    is_active: bool


class UserDailyMissionOut(BaseModel):
    """Schema for user's daily mission progress."""

    id: UUID
    mission: DailyMissionOut
    mission_date: datetime
    current_count: int
    is_completed: bool
    completed_at: Optional[datetime] = None
    xp_awarded: int
    progress_percentage: int


class DailyMissionsResponse(BaseModel):
    """Response for today's daily missions."""

    missions: list[UserDailyMissionOut]
    total_xp_today: int
    completed_count: int
    total_count: int


class UpdateMissionProgressRequest(BaseModel):
    """Request to update mission progress."""

    increment: int = Field(default=1, ge=0)


class UpdateMissionProgressResponse(BaseModel):
    """Response after updating mission progress."""

    mission: UserDailyMissionOut
    xp_gained: int
    just_completed: bool


class DailyMissionHistoryItem(BaseModel):
    """Schema for a historical daily mission entry."""

    mission_date: datetime
    mission_name: str
    mission_type: str
    target_count: int
    current_count: int
    is_completed: bool
    completed_at: Optional[datetime] = None
    xp_awarded: int


class DailyMissionHistoryResponse(BaseModel):
    """Response for daily mission history."""

    history: list[DailyMissionHistoryItem]
    total_completed: int
    total_xp_earned: int
    current_streak: int


class StreakMilestoneOut(BaseModel):
    """Streak milestone information."""

    day: int
    xp_reward: int
    badge_slug: Optional[str] = None
    freeze_reward: int = 0
    is_completed: bool = False


class StreakStatusOut(BaseModel):
    """Current streak status response."""

    current_streak: int
    longest_streak: int
    streak_freezes: int
    is_maintained_today: bool
    is_at_risk: bool
    next_milestone: Optional[dict] = None
    milestones: list[StreakMilestoneOut]


class ClaimDailyStreakOut(BaseModel):
    """Response for claiming daily streak reward."""

    xp_awarded: int
    current_streak: int
    total_xp: int
    message: str


class UseStreakFreezeOut(BaseModel):
    """Response for using streak freeze."""

    success: bool
    remaining_freezes: int
    message: str


class PeerFeedbackSendIn(BaseModel):
    to_user_id: UUID
    template_key: str = Field(
        ...,
        pattern="^(great_progress|keep_going|impressive_streak|quiz_champion)$",
    )
    share_id: Optional[UUID] = None


class PeerFeedbackOut(BaseModel):
    success: bool
    message: str
    template_key: str
    notification_id: UUID
