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
from typing import Any, Optional
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


class StudentProgressionRules(BaseModel):
    discovery_xp: int = 25
    lesson_xp: int = 50
    mastery_xp: int = 75
    max_possible_xp_per_motif: int = 150
    quiz_pass_threshold: int = 80


class MotifProgressionItem(BaseModel):
    motif_id: UUID
    motif_title: str
    urn_id: Optional[UUID] = None
    urn_slug: Optional[str] = None
    status: str
    discovered_at: Optional[datetime] = None
    lesson_viewed_at: Optional[datetime] = None
    learned_at: Optional[datetime] = None
    mastered_at: Optional[datetime] = None
    quiz_attempts: int = 0
    quiz_best_score: int = 0
    xp_earned: int = 0
    is_demo: bool = False
    can_view_lesson: bool = True
    can_take_quiz: bool = True
    is_mastered: bool = False


class StudentProgressionSummaryOut(BaseModel):
    user_id: UUID
    display_name: str
    total_xp: int
    current_streak: int
    rank: str
    total_motifs: int
    hidden_count: int
    discovered_count: int
    learned_count: int
    mastered_count: int
    completion_percentage: float
    mastery_percentage: float
    motifs: list[MotifProgressionItem]
    rules: StudentProgressionRules


class ProgressionActionRequest(BaseModel):
    action: str = Field(..., pattern="^(discover|complete_lesson|submit_quiz)$")
    motif_id: UUID
    time_spent_seconds: Optional[int] = 0
    answers: Optional[dict[str, str]] = None
    idempotency_key: Optional[str] = None
    client_claimed_status: Optional[str] = None


class ProgressionActionResponse(BaseModel):
    success: bool
    motif_id: UUID
    previous_status: str
    new_status: str
    status_changed: bool
    xp_awarded: int
    total_xp: int
    message: str
    already_unlocked: bool = False
    already_learned: bool = False
    already_mastered: bool = False
    quiz_score: Optional[int] = None
    quiz_passed: Optional[bool] = None


class PassportCheckInRequest(BaseModel):
    site_slug: str
    verification_method: str = "qr_code"
    qr_payload: Optional[str] = None
    qr_token: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    device_metadata: Optional[dict[str, Any]] = None
    client_claimed_status: Optional[str] = None


class PassportStampDetailOut(BaseModel):
    id: UUID
    site_slug: str
    site_name: str
    zone_slug: str
    verification_method: str
    provenance_hash: str
    authority: str
    stamped_at: datetime
    checkin_count: int
    last_visited_at: datetime
    is_verified: bool
    is_distinct_from_mastery: bool = True


class PassportCheckInResponse(BaseModel):
    success: bool
    stamp_id: UUID
    site_slug: str
    site_name: str
    zone_slug: str
    verification_method: str
    provenance_hash: str
    authority: str
    stamped_at: datetime
    checkin_count: int
    xp_awarded: int
    is_verified: bool
    is_distinct_from_mastery: bool = True
    message: str


class PassportVerificationRequest(BaseModel):
    qr_token: str
    site_slug: Optional[str] = None


class PassportVerificationResponse(BaseModel):
    valid: bool
    site_slug: str
    site_name: str
    zone_slug: str
    authority: str
    issued_at: datetime
    expires_at: Optional[datetime] = None
    nonce: Optional[str] = None
    message: str = "QR code verified successfully."


class VerifiedPassportOut(BaseModel):
    user_id: UUID
    display_name: str
    verified_stamps_count: int
    total_available_seals: int
    verified_completion_percent: float
    assessed_mastery_count: int
    can_export_verified_certificate: bool
    distinct_invariants: dict[str, bool]
    stamps: list[PassportStampDetailOut]


class StudentPassportSummaryOut(BaseModel):
    student_id: UUID
    display_name: str
    email: str
    verified_stamps_count: int
    assessed_mastery_count: int
    last_stamp_at: Optional[datetime] = None
    is_fake_client_claim_detected: bool = False


class ClassroomPassportAnalyticsOut(BaseModel):
    classroom_id: UUID
    student_count: int
    total_verified_stamps: int
    avg_verified_stamps: float
    students: list[StudentPassportSummaryOut]


