"""
Pydantic schemas for Luuniensuki LMS API.

This module contains all Pydantic models used for request/response validation.
Extracted from main.py for better organization and maintainability.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

# =============================================================================
# Base Schemas
# =============================================================================


class BaseSchema(BaseModel):
    """Base schema with common configuration."""

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# Auth Schemas
# =============================================================================


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    display_name: Optional[str] = None


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenIn(BaseModel):
    refresh_token: str


class PasswordChangeIn(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)


class PasswordResetRequestIn(BaseModel):
    email: EmailStr


class PasswordResetIn(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)


# =============================================================================
# User Schemas
# =============================================================================


class RankOut(BaseModel):
    title: str
    min_xp: int
    max_xp: Optional[int] = None


class UserOut(BaseModel):
    id: UUID
    email: str
    display_name: Optional[str] = None
    username: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    total_xp: int
    role: str
    starting_urn_id: Optional[UUID] = None
    is_profile_public: bool = False
    ai_personalization_enabled: bool = True
    rank: RankOut
    current_streak: int = 0
    longest_streak: int = 0


class UserProfileUpdateIn(BaseModel):
    display_name: Optional[str] = None
    username: Optional[str] = None
    bio: Optional[str] = None
    is_profile_public: Optional[bool] = None
    ai_personalization_enabled: Optional[bool] = None


class StartingUrnIn(BaseModel):
    urn_id: UUID


class UserPublicStatsOut(BaseModel):
    discovered_count: int
    learned_count: int
    mastered_count: int
    badge_count: int


class PublicBadgeOut(BaseModel):
    slug: str
    name: str
    icon_url: Optional[str] = None


class PublicMotifOut(BaseModel):
    id: UUID
    name: str
    thumbnail_url: Optional[str] = None
    status: str


class UserPublicProfile(BaseModel):
    id: UUID
    username: str
    display_name: str
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    total_xp: int
    rank: RankOut
    badges: list[PublicBadgeOut]
    certificates: list[Any] = Field(default_factory=list)
    stats: UserPublicStatsOut
    motifs: list[PublicMotifOut] = Field(default_factory=list)


# =============================================================================
# Urn Schemas
# =============================================================================


class UrnOut(BaseModel):
    id: UUID
    slug: str
    name: str
    description: Optional[str] = None
    model_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    display_order: int = 0


class UrnDetailOut(UrnOut):
    motif_count: int = 0
    discovered_count: int = 0
    learned_count: int = 0
    mastered_count: int = 0


# =============================================================================
# Motif Schemas
# =============================================================================


class MotifPositionOut(BaseModel):
    x: float
    y: float
    z: float
    bounding_radius: float


class LessonContentOut(BaseModel):
    intro_text: Optional[str] = None
    description: Optional[str] = None
    historical_context: Optional[str] = None
    symbolism: Optional[str] = None
    fun_fact: Optional[str] = None
    audio_narration_url: Optional[str] = None
    video_url: Optional[str] = None
    additional_images: list[str] = Field(default_factory=list)


class MotifOut(BaseModel):
    id: UUID
    slug: str
    name: str
    description: Optional[str] = None
    category: str
    rarity: str
    thumbnail_url: Optional[str] = None
    image_url: Optional[str] = None
    position: Optional[MotifPositionOut] = None
    urn_id: UUID
    urn_slug: str
    urn_name: str


class MotifDetailOut(MotifOut):
    lesson: Optional[LessonContentOut] = None
    status: str = "hidden"
    xp_earned: int = 0


class MotifListOut(BaseModel):
    id: UUID
    slug: str
    name: str
    category: str
    rarity: str
    thumbnail_url: Optional[str] = None
    status: str = "hidden"
    urn_id: UUID
    urn_slug: str


# =============================================================================
# Progress Schemas
# =============================================================================


class UnlockIn(BaseModel):
    motif_id: UUID


class UnlockOut(BaseModel):
    motif_id: UUID
    status: str
    xp_awarded: int
    total_xp: int
    badges_awarded: list[str] = Field(default_factory=list)


class LessonCompleteIn(BaseModel):
    motif_id: UUID


class LessonCompleteOut(BaseModel):
    motif_id: UUID
    status: str
    xp_awarded: int
    total_xp: int
    badges_awarded: list[str] = Field(default_factory=list)


class ProgressOut(BaseModel):
    motif_id: UUID
    status: str
    discovered_at: Optional[datetime] = None
    learned_at: Optional[datetime] = None
    mastered_at: Optional[datetime] = None


# =============================================================================
# Quiz Schemas
# =============================================================================


class QuizOptionOut(BaseModel):
    id: str
    text: str
    image_url: Optional[str] = None


class QuizQuestionOut(BaseModel):
    id: UUID
    question_text: str
    question_type: str
    options: list[QuizOptionOut]
    target_mesh_name: Optional[str] = None
    explanation: Optional[str] = None


class QuizOut(BaseModel):
    motif_id: UUID
    questions: list[QuizQuestionOut]
    time_limit_seconds: Optional[int] = None


class QuizAnswerIn(BaseModel):
    question_id: UUID
    selected_option_id: str


class QuizSubmitIn(BaseModel):
    motif_id: UUID
    answers: list[QuizAnswerIn]
    time_taken_seconds: Optional[int] = None


class QuizResultOut(BaseModel):
    motif_id: UUID
    score: int
    max_score: int
    percentage: int
    passed: bool
    xp_awarded: int
    total_xp: int
    badges_awarded: list[str] = Field(default_factory=list)
    results: list[dict] = Field(default_factory=list)


# =============================================================================
# Urn Exam Schemas
# =============================================================================


class UrnExamQuestionOut(BaseModel):
    id: UUID
    question_text: str
    question_type: str
    options: list[QuizOptionOut]
    motif_name: str
    motif_id: UUID


class UrnExamOut(BaseModel):
    urn_id: UUID
    urn_name: str
    questions: list[UrnExamQuestionOut]
    time_limit_seconds: int = 1800  # 30 minutes default


class UrnExamSubmitIn(BaseModel):
    urn_id: UUID
    answers: list[QuizAnswerIn]
    time_taken_seconds: Optional[int] = None


class UrnExamResultDetail(BaseModel):
    question_id: UUID
    selected_option_id: str
    correct_option_id: str
    is_correct: bool
    explanation: Optional[str] = None


class CertificateSummaryOut(BaseModel):
    code: str
    issuer_name: str
    issued_at: datetime


class UrnExamSubmitResponse(BaseModel):
    urn_id: UUID
    score: int
    max_score: int
    percentage: int
    passed: bool
    xp_awarded: int
    total_xp: int
    results: list[UrnExamResultDetail]
    certificate: Optional[CertificateSummaryOut] = None


class UrnExamAttemptResultOut(BaseModel):
    attempt_id: UUID
    urn_id: UUID
    started_at: datetime
    completed_at: Optional[datetime] = None
    score: int
    max_score: int
    percentage: int
    passed: bool
    results: list[UrnExamResultDetail]
    certificate: Optional[CertificateSummaryOut] = None


# =============================================================================
# Badge Schemas
# =============================================================================


class BadgeOut(BaseModel):
    id: UUID
    slug: str
    name: str
    description: Optional[str] = None
    icon_url: Optional[str] = None
    category: str
    xp_reward: int = 0


class UserBadgeOut(BaseModel):
    badge: BadgeOut
    earned_at: datetime


# =============================================================================
# Certificate Schemas
# =============================================================================


class CertificateOut(BaseModel):
    id: UUID
    code: str
    issuer_name: str
    status: str
    issued_at: datetime
    reason_type: str
    reason_id: UUID


class CertificateVerifyOut(BaseModel):
    code: str
    issuer_name: str
    status: str
    issued_at: datetime
    user_id: UUID
    display_name: str
    reason_type: str
    reason_id: UUID


# =============================================================================
# Quest Schemas
# =============================================================================


class QuestObjectiveOut(BaseModel):
    id: UUID
    description: str
    target_type: str
    target_count: int
    current_count: int = 0
    completed: bool = False


class QuestStepOut(BaseModel):
    id: UUID
    title: str
    description: Optional[str] = None
    order: int
    xp_reward: int = 0
    completed: bool = False
    objectives: list[QuestObjectiveOut] = Field(default_factory=list)


class QuestCertificateOut(BaseModel):
    code: str
    issued_at: datetime
    issuer_name: str


class QuestListOut(BaseModel):
    id: UUID
    slug: str
    name: str
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    difficulty: str
    estimated_time_minutes: int = 0
    xp_reward: int = 0
    status: str = "locked"  # locked, available, in_progress, completed
    progress_percent: int = 0


class QuestDetailOut(BaseModel):
    id: UUID
    slug: str
    name: str
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    difficulty: str
    estimated_time_minutes: int = 0
    xp_reward: int = 0
    status: str
    progress_percent: int = 0
    steps: list[QuestStepOut]
    certificate: Optional[QuestCertificateOut] = None


class QuestStartIn(BaseModel):
    quest_id: UUID


class QuestCompleteStepIn(BaseModel):
    quest_id: UUID
    step_id: UUID


# =============================================================================
# Leaderboard Schemas
# =============================================================================


class LeaderboardEntryOut(BaseModel):
    rank: int
    user_id: UUID
    display_name: str
    avatar_url: Optional[str] = None
    total_xp: int
    title: str


class LeaderboardOut(BaseModel):
    entries: list[LeaderboardEntryOut]
    user_rank: Optional[int] = None
    total_users: int


# =============================================================================
# Streak Schemas
# =============================================================================


class StreakOut(BaseModel):
    current_streak: int
    longest_streak: int
    last_activity_date: Optional[str] = None
    streak_frozen: bool = False


# =============================================================================
# Collection Schemas
# =============================================================================


class CollectionStatsOut(BaseModel):
    total: int
    discovered: int
    learned: int
    mastered: int


class CollectionMotifOut(BaseModel):
    id: UUID
    slug: str
    name: str
    category: str
    rarity: str
    thumbnail_url: Optional[str] = None
    status: str
    urn_id: UUID
    urn_slug: str
    urn_name: str
    discovered_at: Optional[datetime] = None
    learned_at: Optional[datetime] = None
    mastered_at: Optional[datetime] = None


class CollectionOut(BaseModel):
    stats: CollectionStatsOut
    motifs: list[CollectionMotifOut]


# =============================================================================
# Dashboard Schemas
# =============================================================================


class DashboardUrnOut(BaseModel):
    id: UUID
    slug: str
    name: str
    thumbnail_url: Optional[str] = None
    motif_count: int
    discovered_count: int
    learned_count: int
    mastered_count: int
    progress_percent: int


class DashboardQuestSummaryOut(BaseModel):
    active_count: int
    completed_count: int
    available_count: int


class RecommendationItemOut(BaseModel):
    type: str  # "next_up", "remediation", "recommendation"
    motif_id: UUID
    motif_name: str
    urn_slug: str
    action: str
    reason: Optional[str] = None


class DashboardSummaryOut(BaseModel):
    urns: list[DashboardUrnOut]
    collection_stats: CollectionStatsOut
    streak: StreakOut
    quest_summary: DashboardQuestSummaryOut
    recommendations: Optional[list[RecommendationItemOut]] = None
    path_motifs: list[CollectionMotifOut] = Field(default_factory=list)


# =============================================================================
# Analytics Schemas
# =============================================================================


class AnalyticsEventIn(BaseModel):
    name: str
    payload: dict = Field(default_factory=dict)
    path: Optional[str] = None


class AnalyticsEventOut(BaseModel):
    id: UUID
    name: str
    payload: dict
    created_at: datetime


# =============================================================================
# Admin Schemas
# =============================================================================


class AdminUserOut(BaseModel):
    id: UUID
    email: str
    display_name: Optional[str] = None
    role: str
    total_xp: int
    is_active: bool = True
    created_at: datetime


class AdminUserUpdateIn(BaseModel):
    role: Optional[str] = None
    is_active: Optional[bool] = None


class AdminStatsOut(BaseModel):
    total_users: int
    total_urns: int
    total_motifs: int
    total_quests: int
    total_progress_entries: int
    total_quiz_attempts: int
    total_certificates: int


# =============================================================================
# Recommendation Schemas
# =============================================================================


class RefreshRecommendationsIn(BaseModel):
    use_llm: bool = False


class RecommendationsOut(BaseModel):
    next_up: list[RecommendationItemOut] = Field(default_factory=list)
    remediation: list[RecommendationItemOut] = Field(default_factory=list)
    recommendations: list[RecommendationItemOut] = Field(default_factory=list)
    generated_at: datetime
    source: str = "rules"  # "rules" or "llm"


# =============================================================================
# Error Schemas
# =============================================================================


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[dict] = None


class ErrorResponse(BaseModel):
    error: ErrorDetail
