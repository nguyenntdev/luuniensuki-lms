"""
Pydantic schemas for Luuniensuki LMS API.

This module contains all Pydantic models used for request/response validation.
Extracted from main.py for better organization and maintainability.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

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


class PasswordResetRequestOut(BaseModel):
    success: bool
    message: str
    reset_token: Optional[str] = None


class PasswordResetOut(BaseModel):
    success: bool
    message: str


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


class AgeVerificationIn(BaseModel):
    """Schema for age verification request."""
    birth_year: int = Field(..., ge=1900, le=2100, description="User's birth year")


class AgeVerificationOut(BaseModel):
    """Schema for age verification response."""
    age_verified: bool
    age_verified_at: Optional[datetime] = None
    birth_year: Optional[int] = None
    current_age: Optional[int] = None
    allowed_ratings: list[str] = Field(
        default_factory=list,
        description="Content ratings the user can access"
    )


class ContentRatingInfo(BaseModel):
    """Schema for content rating information."""
    rating: str
    label: str
    description: str
    min_age: Optional[int] = None


class ContentRatingsOut(BaseModel):
    """Schema for all content ratings."""
    ratings: list[ContentRatingInfo]


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


class QuizHintRequestIn(BaseModel):
    """Request schema for requesting a quiz hint."""
    hint_type: str  # explain, clue, elimination


class QuizHintOut(BaseModel):
    """Response schema for a quiz hint."""
    id: UUID
    question_id: UUID
    hint_type: str
    hint_text: str
    heart_cost: int
    created_at: datetime
    rag_sources: Optional[Any] = None


class QuizHintsListOut(BaseModel):
    """Response schema for listing hints."""
    hints: list[QuizHintOut]
    total: int


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
    xp_bonus: int = 0


class UserBadgeOut(BaseModel):
    badge: BadgeOut
    earned_at: datetime


# =============================================================================
# Milestone Schemas
# =============================================================================


class MilestoneOut(BaseModel):
    id: UUID
    user_id: UUID
    milestone_type: str
    achieved_at: datetime
    context_data: Optional[dict[str, Any]] = None
    celebrated: bool
    created_at: datetime


class MilestoneListOut(BaseModel):
    milestones: list[MilestoneOut]


class PendingMilestoneOut(BaseModel):
    id: UUID
    milestone_type: str
    achieved_at: datetime
    context_data: Optional[dict[str, Any]] = None


class PendingMilestonesOut(BaseModel):
    pending_milestones: list[PendingMilestoneOut]


class MilestoneCelebratedOut(BaseModel):
    success: bool
    milestone_id: UUID
    milestone_type: str
    message: str


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


class LeaderboardSettingsOut(BaseSchema):
    """User leaderboard settings output."""
    id: UUID
    user_id: UUID
    show_on_global: bool
    show_real_name: bool
    preferred_leaderboard: str
    created_at: datetime
    updated_at: datetime


class LeaderboardSettingsUpdateIn(BaseModel):
    """Update leaderboard settings input."""
    show_on_global: Optional[bool] = None
    show_real_name: Optional[bool] = None
    preferred_leaderboard: Optional[str] = None


class EnhancedLeaderboardEntryOut(BaseModel):
    """Enhanced leaderboard entry with additional metrics."""
    rank: int
    user_id: UUID
    display_name: str
    avatar_url: Optional[str] = None
    total_xp: int
    current_streak: int
    title: str


class EnhancedLeaderboardOut(BaseModel):
    """Enhanced leaderboard response with scope and user rank."""
    scope: str  # "global", "friends", "class"
    entries: list[EnhancedLeaderboardEntryOut]
    user_rank: Optional[int] = None
    user_entry: Optional[EnhancedLeaderboardEntryOut] = None
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
    name: str = Field(..., min_length=1, max_length=100)
    payload: Optional[dict] = Field(default_factory=dict)
    path: Optional[str] = None
    session_id: Optional[UUID] = None
    cohort: Optional[str] = Field(None, max_length=50)
    device_info: Optional[dict] = None


class AnalyticsEventOut(BaseModel):
    id: UUID
    name: str
    payload: dict
    path: Optional[str] = None
    session_id: Optional[UUID] = None
    cohort: Optional[str] = None
    event_category: Optional[str] = None
    device_info: Optional[dict] = None
    created_at: datetime


# =============================================================================
# Session Tracking Schemas
# =============================================================================


class SessionHeartbeatIn(BaseModel):
    """Request body for session heartbeat."""
    session_id: UUID
    device_type: str = Field(..., pattern="^(mobile|web|tablet)$")
    platform: str = Field(..., pattern="^(ios|android|web)$")
    app_version: Optional[str] = None


class SessionHeartbeatOut(BaseModel):
    """Response for session heartbeat."""
    success: bool
    session_id: UUID
    is_active: bool


class SessionEndIn(BaseModel):
    """Request body to end a session."""
    session_id: UUID


class SessionEndOut(BaseModel):
    """Response for ending a session."""
    success: bool
    session_id: UUID
    duration_seconds: Optional[int] = None


class ActiveSessionsOut(BaseModel):
    """Response for active sessions count."""
    active_sessions: int
    last_5_minutes: int
    last_30_minutes: int
    timestamp: datetime


class SessionStatsOut(BaseModel):
    """Response for session statistics."""
    total_sessions_today: int
    total_sessions_week: int
    total_sessions_month: int
    avg_session_duration_minutes: float
    unique_users_today: int
    unique_users_week: int
    unique_users_month: int
    current_active_sessions: int
    peak_concurrent_today: int
    by_platform: dict[str, int]
    by_device_type: dict[str, int]



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
# Content Versioning Schemas
# =============================================================================


class ContentVersionOut(BaseSchema):
    id: UUID
    content_type: str
    content_id: UUID
    version: int
    data: dict
    editor_id: Optional[UUID] = None
    editor_name: Optional[str] = None
    change_note: Optional[str] = None
    created_at: datetime


class ContentVersionListOut(BaseSchema):
    id: UUID
    version: int
    editor_id: Optional[UUID] = None
    editor_name: Optional[str] = None
    change_note: Optional[str] = None
    created_at: datetime


class RevertContentIn(BaseModel):
    change_note: Optional[str] = None


# =============================================================================
# Review Workflow Schemas
# =============================================================================


class SubmitForReviewIn(BaseModel):
    """Request schema for submitting content for review."""
    pass


class ApproveContentIn(BaseModel):
    """Request schema for approving and publishing content."""
    review_notes: Optional[str] = None


class RejectContentIn(BaseModel):
    """Request schema for rejecting content."""
    review_notes: str = Field(..., min_length=1, description="Required rejection reason")


class PendingReviewItemOut(BaseSchema):
    """Schema for a content item pending review."""
    id: UUID
    content_type: str  # 'lesson' or 'quiz_question'
    title: str  # For lessons: motif name, for quiz: question text preview
    motif_name: Optional[str] = None
    submitted_by_id: Optional[UUID] = None
    submitted_by_name: Optional[str] = None
    submitted_at: Optional[datetime] = None
    version: Optional[int] = None


class PendingReviewListOut(BaseModel):
    """Response schema for pending review list."""
    lessons: list[PendingReviewItemOut] = Field(default_factory=list)
    quiz_questions: list[PendingReviewItemOut] = Field(default_factory=list)
    total_count: int


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


# =============================================================================
# Onboarding Schemas
# =============================================================================


class OnboardingGoalIn(BaseModel):
    """Request schema for setting user's onboarding goal."""

    goal: str = Field(
        ...,
        description="User's learning goal",
        examples=["learn_culture", "pass_exam", "curiosity"],
    )


class OnboardingStatusOut(BaseModel):
    """Response schema for onboarding status."""

    onboarding_completed: bool
    onboarding_goal: Optional[str] = None
    onboarding_completed_at: Optional[datetime] = None


class OnboardingCompleteIn(BaseModel):
    """Request schema for marking onboarding as complete."""

    completed: bool = True


class OnboardingCompleteOut(BaseModel):
    """Response schema for completing onboarding."""

    success: bool
    message: str
    onboarding_completed: bool
    onboarding_completed_at: Optional[datetime] = None


# =============================================================================
# Daily Mission Schemas
# =============================================================================


class DailyMissionOut(BaseSchema):
    """Schema for a daily mission template."""

    id: UUID
    slug: str
    name: str
    description: str
    mission_type: str
    target_count: int
    xp_reward: int
    is_active: bool


class UserDailyMissionOut(BaseSchema):
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


class DailyMissionHistoryItem(BaseSchema):
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


# =============================================================================
# Weekly Quest Schemas
# =============================================================================


class WeeklyQuestOut(BaseSchema):
    """Schema for a weekly quest template."""

    id: UUID
    slug: str
    name: str
    description: str
    category: str
    week_number: Optional[int] = None
    year: Optional[int] = None
    target_count: int
    xp_reward: int
    badge_slug: Optional[str] = None
    is_recurring: bool
    is_active: bool


class UserWeeklyQuestOut(BaseSchema):
    """Schema for user's weekly quest progress."""

    id: UUID
    quest: WeeklyQuestOut
    week_start_date: datetime
    current_count: int
    is_completed: bool
    completed_at: Optional[datetime] = None
    xp_awarded: int
    progress_percentage: int


class WeeklyQuestsResponse(BaseModel):
    """Response for this week's quests."""

    quests: list[UserWeeklyQuestOut]
    week_start_date: datetime
    week_end_date: datetime
    total_xp_this_week: int
    completed_count: int
    total_count: int


class UpdateWeeklyQuestProgressRequest(BaseModel):
    """Request to update weekly quest progress."""

    increment: int = Field(default=1, ge=0)


class UpdateWeeklyQuestProgressResponse(BaseModel):
    """Response after updating weekly quest progress."""

    quest: UserWeeklyQuestOut
    xp_gained: int
    just_completed: bool
    badge_earned: Optional[str] = None


class WeeklyQuestHistoryItem(BaseSchema):
    """Schema for a historical weekly quest entry."""

    week_start_date: datetime
    quest_name: str
    quest_category: str
    target_count: int
    current_count: int
    is_completed: bool
    completed_at: Optional[datetime] = None
    xp_awarded: int


class WeeklyQuestHistoryResponse(BaseModel):
    """Response for weekly quest history."""

    history: list[WeeklyQuestHistoryItem]
    total_completed: int
    total_xp_earned: int


# =============================================================================
# Tag Schemas
# =============================================================================


class TagOut(BaseSchema):
    """Schema for tag output."""

    id: UUID
    slug: str
    name: str
    tag_type: str
    description: Optional[str] = None
    is_active: bool
    created_at: datetime


class TagCreateIn(BaseModel):
    """Schema for creating a tag."""

    slug: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=200)
    tag_type: str = Field(..., pattern="^(topic|difficulty|audience|era|style)$")
    description: Optional[str] = None
    is_active: bool = True


class ContentTagOut(BaseSchema):
    """Schema for content tag output."""

    id: UUID
    tag_id: UUID
    content_type: str
    content_id: UUID
    created_at: datetime
    tag: TagOut


class ContentTagCreateIn(BaseModel):
    """Schema for creating a content tag."""

    tag_slugs: list[str] = Field(..., min_items=1)


class SearchRequest(BaseModel):
    """Schema for search request."""

    q: Optional[str] = Field(None, description="Search query")
    tags: Optional[list[str]] = Field(
        None, description="List of tag slugs to filter by"
    )
    content_types: Optional[list[str]] = Field(
        None,
        description="List of content types to search (lesson, motif, quiz, quest)",
    )
    limit: int = Field(20, ge=1, le=100)


class SearchResultItem(BaseModel):
    """Schema for a single search result."""

    content_type: str
    content_id: UUID
    title: str
    description: Optional[str] = None
    tags: list[TagOut]
    relevance_score: float = 0.0


class SearchResponse(BaseModel):
    """Schema for search response."""

    results: list[SearchResultItem]
    total: int
    query: Optional[str] = None
    applied_tags: list[str] = []


# =============================================================================
# Streak Schemas
# =============================================================================


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


class MilestoneRewardOut(BaseModel):
    """Milestone reward information."""

    day: int
    xp: int
    freezes: int


class AwardedBadgeOut(BaseModel):
    """Awarded badge information."""

    slug: str
    name: str
    xp_bonus: int


class MilestoneRewardsOut(BaseModel):
    """Response for milestone rewards check."""

    milestones: list[MilestoneRewardOut]
    total_xp: int
    total_freezes: int
    badges: list[AwardedBadgeOut]



# =============================================================================
# RAG Document Schemas
# =============================================================================


class RagDocumentOut(BaseSchema):
    """Output schema for RAG document."""

    id: UUID
    title: str
    content: str
    source_type: str
    source_path: Optional[str] = None
    is_active: bool
    embedding_model: Optional[str] = None
    embedding_updated_at: Optional[datetime] = None
    has_embedding: bool = False
    created_at: datetime
    updated_at: datetime


class RagDocumentListOut(BaseModel):
    """Output schema for paginated RAG document list."""

    documents: list[RagDocumentOut]
    total: int
    page: int
    page_size: int
    total_pages: int


class RagDocumentCreateIn(BaseModel):
    """Input schema for creating a RAG document."""

    title: str = Field(..., min_length=1, max_length=255, description="Document title")
    content: str = Field(..., min_length=1, description="Document content")
    is_active: Optional[bool] = Field(
        default=True, description="Whether document is active"
    )


class RagDocumentUpdateIn(BaseModel):
    """Input schema for updating a RAG document."""

    title: Optional[str] = Field(
        default=None, min_length=1, max_length=255, description="Document title"
    )
    content: Optional[str] = Field(
        default=None, min_length=1, description="Document content"
    )
    is_active: Optional[bool] = Field(
        default=None, description="Whether document is active"
    )


# =============================================================================
# RAG Settings Schemas
# =============================================================================


class RagSettingsOut(BaseSchema):
    """Output schema for RAG settings."""

    system_instruction: Optional[str] = None
    prompt_prefix: Optional[str] = None
    model_override: Optional[str] = None
    temperature: Optional[float] = None
    max_documents: int
    embedding_enabled: bool = True
    hybrid_alpha: float = 0.6


class RagSettingsUpdateIn(BaseModel):
    """Input schema for updating RAG settings with validation."""

    system_instruction: Optional[str] = Field(
        default=None, max_length=5000, description="AI system instruction"
    )
    prompt_prefix: Optional[str] = Field(
        default=None, max_length=2000, description="Prefix for user prompts"
    )
    model_override: Optional[str] = Field(
        default=None, max_length=100, description="Override model name"
    )
    temperature: Optional[float] = Field(
        default=None, ge=0.0, le=2.0, description="Model temperature"
    )
    max_documents: Optional[int] = Field(
        default=None, ge=1, le=20, description="Maximum RAG documents to retrieve"
    )
    embedding_enabled: Optional[bool] = Field(
        default=None, description="Enable embedding-based search"
    )
    hybrid_alpha: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Hybrid search alpha (0=keyword, 1=semantic)",
    )


# =============================================================================
# Audit Log Schemas
# =============================================================================


class AuditLogOut(BaseSchema):
    """Output schema for audit log entries."""

    id: UUID
    user_id: Optional[UUID] = None
    user_email: Optional[str] = None  # Denormalized for convenience
    action: str
    resource_type: str
    resource_id: Optional[UUID] = None
    old_value: Optional[dict[str, Any]] = None
    new_value: Optional[dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime


class AuditLogListOut(BaseModel):
    """Output schema for paginated audit log list."""

    logs: list[AuditLogOut]
    total: int
    page: int
    page_size: int
    total_pages: int


# =============================================================================
# Retention Analytics Schemas
# =============================================================================


class RetentionMetricsOut(BaseModel):
    """Overall retention metrics response."""

    d1_retention: float = Field(..., description="Day 1 retention rate (%)")
    d7_retention: float = Field(..., description="Day 7 retention rate (%)")
    d30_retention: float = Field(..., description="Day 30 retention rate (%)")
    total_users: int = Field(..., description="Total users in calculation")
    eligible_users: dict[int, int] = Field(
        ..., description="Number of eligible users for each retention period"
    )
    date_range: dict[str, Optional[str]] = Field(
        ..., description="Date range for the calculation"
    )


class CohortRetentionItemOut(BaseModel):
    """Single cohort retention data."""

    cohort: str = Field(..., description="Cohort identifier (e.g., '2024-W01' or '2024-01')")
    signup_count: int = Field(..., description="Number of users who signed up in this cohort")
    d1_retention: float = Field(..., description="Day 1 retention rate (%)")
    d7_retention: float = Field(..., description="Day 7 retention rate (%)")
    d30_retention: float = Field(..., description="Day 30 retention rate (%)")
    eligible_d1: int = Field(..., description="Users eligible for D1 calculation")
    eligible_d7: int = Field(..., description="Users eligible for D7 calculation")
    eligible_d30: int = Field(..., description="Users eligible for D30 calculation")


class CohortRetentionOut(BaseModel):
    """Cohort-based retention response."""

    cohorts: list[CohortRetentionItemOut] = Field(
        default_factory=list, description="List of cohort retention data"
    )
    period: str = Field(..., description="Cohort grouping period (week or month)")


class RetentionCurveDataPointOut(BaseModel):
    """Single data point in retention curve."""

    day: int = Field(..., description="Day number since signup")
    retention_rate: float = Field(..., description="Retention rate (%) on this day")
    retained_users: int = Field(..., description="Number of retained users")
    eligible_users: int = Field(..., description="Number of eligible users")


class RetentionCurveOut(BaseModel):
    """Retention curve response for visualization."""

    data_points: list[RetentionCurveDataPointOut] = Field(
        default_factory=list, description="Retention data points for each day"
    )
    total_users: int = Field(..., description="Total users in cohort")
    days: int = Field(..., description="Number of days calculated")
    cohort_period: dict[str, str] = Field(
        ..., description="Period for user cohort selection"
    )


# =============================================================================
# Analytics Funnel Schemas
# =============================================================================


class FunnelStageOut(BaseModel):
    """Output schema for a funnel stage."""

    stage: str
    display_name: str
    count: int
    conversion_from_previous: float


class FunnelDataOut(BaseModel):
    """Output schema for funnel data."""

    funnel_type: str
    funnel_name: str
    description: str
    date_range: dict[str, Optional[str]]
    cohort: Optional[str] = None
    total_users: int
    stages: list[FunnelStageOut]
    overall_conversion: float


class FunnelListItemOut(BaseModel):
    """Output schema for available funnel types."""

    funnel_type: str
    name: str
    description: str
    stage_count: int
    stages: list[str]


# =============================================================================
# Offline Lesson Cache Schemas
# =============================================================================


class CacheFileInfo(BaseModel):
    """Information about a file to be cached."""

    url: str
    type: str  # 'content', 'image', 'audio', 'video'
    size_bytes: int = 0


class CacheManifestItemOut(BaseSchema):
    """Output schema for a single cacheable lesson in the manifest."""

    lesson_id: UUID
    motif_id: UUID
    motif_name: str
    title: str
    version: int
    file_urls: list[CacheFileInfo]
    total_size_bytes: int
    priority: int  # 1=high (next lessons), 2=medium, 3=low


class CacheManifestOut(BaseModel):
    """Output schema for the complete cache manifest."""

    lessons: list[CacheManifestItemOut]
    total_size_bytes: int
    recommended_cache_size_bytes: int


class LessonCacheIn(BaseModel):
    """Input schema for marking a lesson as cached."""

    file_size_bytes: int = Field(ge=0)
    cache_version: int = Field(default=1, ge=1)


class LessonCacheOut(BaseSchema):
    """Output schema for cached lesson info."""

    id: UUID
    user_id: UUID
    lesson_id: UUID
    cached_at: datetime
    cache_version: int
    file_size_bytes: int
    is_valid: bool
    expires_at: Optional[datetime] = None


# =============================================================================
# Abuse Report Schemas
# =============================================================================


class AbuseReportCreateIn(BaseModel):
    """Input schema for creating an abuse report."""

    reported_user_id: Optional[UUID] = None
    content_type: str = Field(
        ..., min_length=1, max_length=50,
        description="Type of content being reported (comment, review, profile, message, other)"
    )
    content_id: Optional[UUID] = None
    reason: str = Field(
        ..., min_length=1, max_length=50,
        description="Reason for reporting (harassment, spam, inappropriate, copyright, other)"
    )
    description: str = Field(
        ..., min_length=10, max_length=2000,
        description="Detailed description of the issue"
    )
    evidence_urls: Optional[list[str]] = Field(
        default=None,
        max_length=10,
        description="List of screenshot/evidence URLs (max 10)"
    )


class AbuseReportOut(BaseSchema):
    """Output schema for abuse report."""

    id: UUID
    reporter_id: UUID
    reported_user_id: Optional[UUID] = None
    content_type: str
    content_id: Optional[UUID] = None
    reason: str
    description: str
    evidence_urls: Optional[list[str]] = None
    status: str
    priority: str
    assigned_to_id: Optional[UUID] = None
    resolution_notes: Optional[str] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime


class AbuseReportDetailOut(BaseSchema):
    """Detailed output schema for abuse report with user info."""

    id: UUID
    reporter_id: UUID
    reporter_email: Optional[str] = None
    reporter_display_name: Optional[str] = None
    reported_user_id: Optional[UUID] = None
    reported_user_email: Optional[str] = None
    reported_user_display_name: Optional[str] = None
    content_type: str
    content_id: Optional[UUID] = None
    reason: str
    description: str
    evidence_urls: Optional[list[str]] = None
    status: str
    priority: str
    assigned_to_id: Optional[UUID] = None
    assigned_to_email: Optional[str] = None
    assigned_to_display_name: Optional[str] = None
    resolution_notes: Optional[str] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime


class AbuseReportAssignIn(BaseModel):
    """Input schema for assigning an abuse report."""

    assigned_to_id: UUID = Field(..., description="ID of admin to assign the report to")


class AbuseReportResolveIn(BaseModel):
    """Input schema for resolving an abuse report."""

    status: str = Field(
        ..., description="New status (resolved or dismissed)"
    )
    resolution_notes: str = Field(
        ..., min_length=10, max_length=2000,
        description="Notes about the resolution"
    )

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate status is either resolved or dismissed."""
        if v not in ["resolved", "dismissed"]:
            raise ValueError("Status must be either 'resolved' or 'dismissed'")
        return v


class AbuseReportListOut(BaseModel):
    """Output schema for paginated list of abuse reports."""

    reports: list[AbuseReportDetailOut]
    total: int
    page: int
    page_size: int


# =============================================================================
# App Version Schemas
# =============================================================================


class AppVersionCheckOut(BaseModel):
    """Output schema for app version check endpoint."""

    update_available: bool
    force_update: bool
    latest_version: Optional[str] = None
    current_version: str
    min_required_version: Optional[str] = None
    download_url: Optional[str] = None
    release_notes: Optional[str] = None


class AppVersionOut(BaseSchema):
    """Output schema for app version details."""

    id: UUID
    platform: str
    version: str
    version_code: int
    min_required_version: str
    is_current: bool
    force_update: bool
    release_notes: Optional[str] = None
    download_url: Optional[str] = None
    released_at: datetime
    created_at: datetime


class AppVersionCreateIn(BaseModel):
    """Input schema for creating a new app version."""

    platform: str = Field(..., pattern="^(ios|android)$")
    version: str = Field(..., min_length=1, max_length=20)
    version_code: int = Field(..., ge=1)
    min_required_version: str = Field(..., min_length=1, max_length=20)
    is_current: bool = Field(default=False)
    force_update: bool = Field(default=False)
    release_notes: Optional[str] = None
    download_url: Optional[str] = None
    released_at: Optional[datetime] = None


class AppVersionUpdateIn(BaseModel):
    """Input schema for updating an app version."""

    is_current: Optional[bool] = None
    force_update: Optional[bool] = None
    release_notes: Optional[str] = None
    download_url: Optional[str] = None


# =============================================================================
# Crash Report Schemas
# =============================================================================


class CrashReportCreateIn(BaseModel):
    """Input schema for submitting a crash report."""

    user_id: Optional[UUID] = Field(
        default=None, description="User ID if authenticated, null for anonymous"
    )
    session_id: Optional[UUID] = Field(
        default=None, description="Session ID if available"
    )
    error_type: str = Field(
        ...,
        pattern="^(crash|error|exception|anr)$",
        description="Type of error: crash, error, exception, anr",
    )
    error_message: str = Field(
        ..., min_length=1, max_length=5000, description="Error message"
    )
    stack_trace: Optional[str] = Field(
        default=None, max_length=50000, description="Stack trace if available"
    )
    platform: str = Field(
        ..., pattern="^(ios|android|web)$", description="Platform: ios, android, web"
    )
    app_version: str = Field(..., min_length=1, max_length=20, description="App version")
    device_model: Optional[str] = Field(
        default=None, max_length=100, description="Device model"
    )
    os_version: Optional[str] = Field(
        default=None, max_length=50, description="OS version"
    )
    additional_data: Optional[dict[str, Any]] = Field(
        default=None, description="Additional context data"
    )


class CrashReportOut(BaseSchema):
    """Output schema for crash report."""

    id: UUID
    user_id: Optional[UUID] = None
    session_id: Optional[UUID] = None
    error_type: str
    error_message: str
    stack_trace: Optional[str] = None
    platform: str
    app_version: str
    device_model: Optional[str] = None
    os_version: Optional[str] = None
    additional_data: Optional[dict[str, Any]] = None
    created_at: datetime
    is_resolved: bool
    resolved_by_id: Optional[UUID] = None
    resolved_at: Optional[datetime] = None


class CrashReportDetailOut(BaseSchema):
    """Detailed output schema for crash report with user info."""

    id: UUID
    user_id: Optional[UUID] = None
    user_email: Optional[str] = None
    user_display_name: Optional[str] = None
    session_id: Optional[UUID] = None
    error_type: str
    error_message: str
    stack_trace: Optional[str] = None
    platform: str
    app_version: str
    device_model: Optional[str] = None
    os_version: Optional[str] = None
    additional_data: Optional[dict[str, Any]] = None
    created_at: datetime
    is_resolved: bool
    resolved_by_id: Optional[UUID] = None
    resolved_by_email: Optional[str] = None
    resolved_by_display_name: Optional[str] = None
    resolved_at: Optional[datetime] = None


class CrashReportResolveIn(BaseModel):
    """Input schema for resolving a crash report."""

    # No additional fields needed, just marking as resolved


class CrashReportListOut(BaseModel):
    """Output schema for paginated list of crash reports."""

    reports: list[CrashReportDetailOut]
    total: int
    page: int
    page_size: int


class CrashReportStatsOut(BaseModel):
    """Output schema for crash report statistics."""

    total_reports: int
    unresolved_reports: int
    resolved_reports: int
    reports_by_platform: dict[str, int]
    reports_by_error_type: dict[str, int]
    reports_last_24h: int
    reports_last_7d: int
    reports_last_30d: int
    top_errors: list[dict[str, Any]]  # List of {error_message, count, latest_occurrence}


# =============================================================================
# App Version Schemas
# =============================================================================


class AppVersionCheckOut(BaseModel):
    """Output schema for app version check endpoint."""

    update_available: bool
    force_update: bool
    latest_version: Optional[str] = None
    current_version: str
    min_required_version: Optional[str] = None
    download_url: Optional[str] = None
    release_notes: Optional[str] = None


class AppVersionOut(BaseSchema):
    """Output schema for app version details."""

    id: UUID
    platform: str
    version: str
    version_code: int
    min_required_version: str
    is_current: bool
    force_update: bool
    release_notes: Optional[str] = None
    download_url: Optional[str] = None
    released_at: datetime
    created_at: datetime


class AppVersionCreateIn(BaseModel):
    """Input schema for creating a new app version."""

    platform: str = Field(..., pattern="^(ios|android)$")
    version: str = Field(..., min_length=1, max_length=20)
    version_code: int = Field(..., ge=1)
    min_required_version: str = Field(..., min_length=1, max_length=20)
    is_current: bool = Field(default=False)
    force_update: bool = Field(default=False)
    release_notes: Optional[str] = None
    download_url: Optional[str] = None
    released_at: Optional[datetime] = None


class AppVersionUpdateIn(BaseModel):
    """Input schema for updating an app version."""

    is_current: Optional[bool] = None
    force_update: Optional[bool] = None
    release_notes: Optional[str] = None
    download_url: Optional[str] = None


# =============================================================================
# Notification Settings Schemas
# =============================================================================


class NotificationSettingsOut(BaseSchema):
    """User notification settings output schema."""

    id: UUID
    user_id: UUID
    push_enabled: bool = False
    push_token: Optional[str] = None
    push_platform: Optional[str] = None
    email_enabled: bool = True
    streak_reminders: bool = True
    daily_mission_reminders: bool = True
    weekly_digest: bool = True
    marketing_enabled: bool = False
    quiet_hours_start: Optional[int] = None
    quiet_hours_end: Optional[int] = None
    created_at: datetime
    updated_at: datetime


class NotificationSettingsUpdateIn(BaseModel):
    """Update notification settings request schema."""

    push_enabled: Optional[bool] = None
    email_enabled: Optional[bool] = None
    streak_reminders: Optional[bool] = None
    daily_mission_reminders: Optional[bool] = None
    weekly_digest: Optional[bool] = None
    marketing_enabled: Optional[bool] = None
    quiet_hours_start: Optional[int] = Field(None, ge=0, le=23)
    quiet_hours_end: Optional[int] = Field(None, ge=0, le=23)


class PushTokenRegisterIn(BaseModel):
    """Register push notification token request schema."""

    token: str = Field(..., min_length=1, description="FCM or APNS device token")
    platform: str = Field(..., description="Platform: ios, android, or web")

    @field_validator("platform")
    @classmethod
    def validate_platform(cls, v: str) -> str:
        if v not in ["ios", "android", "web"]:
            raise ValueError("Platform must be one of: ios, android, web")
        return v


class PushTokenRegisterOut(BaseModel):
    """Register push token response schema."""

    success: bool
    message: str


class ShouldPromptPermissionOut(BaseModel):
    """Check if should prompt for push permission response schema."""

    should_prompt: bool
    reason: Optional[str] = None


# =============================================================================
# Push Notification Schemas
# =============================================================================


class PushNotificationOut(BaseSchema):
    """Push notification output schema."""

    id: UUID
    user_id: UUID
    title: str
    body: str
    notification_type: str
    data_payload: Optional[dict[str, Any]] = None
    status: str
    scheduled_for: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime


class SendPushNotificationIn(BaseModel):
    """Send push notification request schema."""

    user_ids: list[UUID] = Field(..., min_length=1, description="List of user IDs to send to")
    title: str = Field(..., min_length=1, max_length=255)
    body: str = Field(..., min_length=1)
    notification_type: str = Field(..., description="Type: streak_reminder, daily_mission, achievement, social, system")
    data_payload: Optional[dict[str, Any]] = Field(None, description="Custom data for the app")
    scheduled_for: Optional[datetime] = Field(None, description="Schedule for later (ISO 8601)")

    @field_validator("notification_type")
    @classmethod
    def validate_notification_type(cls, v: str) -> str:
        valid_types = ["streak_reminder", "daily_mission", "achievement", "social", "system"]
        if v not in valid_types:
            raise ValueError(f"notification_type must be one of: {', '.join(valid_types)}")
        return v


class BroadcastPushNotificationIn(BaseModel):
    """Broadcast push notification request schema."""

    title: str = Field(..., min_length=1, max_length=255)
    body: str = Field(..., min_length=1)
    notification_type: str = Field(..., description="Type: streak_reminder, daily_mission, achievement, social, system")
    data_payload: Optional[dict[str, Any]] = Field(None, description="Custom data for the app")
    user_role: Optional[str] = Field(None, description="Filter by role: guest, learner, teacher, admin")

    @field_validator("notification_type")
    @classmethod
    def validate_notification_type(cls, v: str) -> str:
        valid_types = ["streak_reminder", "daily_mission", "achievement", "social", "system"]
        if v not in valid_types:
            raise ValueError(f"notification_type must be one of: {', '.join(valid_types)}")
        return v

    @field_validator("user_role")
    @classmethod
    def validate_user_role(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        valid_roles = ["guest", "learner", "teacher", "admin", "super_admin"]
        if v not in valid_roles:
            raise ValueError(f"user_role must be one of: {', '.join(valid_roles)}")
        return v


class SendPushNotificationOut(BaseModel):
    """Send push notification response schema."""

    success: bool
    message: str
    notifications_created: int
    notifications_sent: int
    notifications_failed: int


class BroadcastPushNotificationOut(BaseModel):
    """Broadcast push notification response schema."""

    success: bool
    message: str
    total_users: int
    total_created: int
    sent: int
    failed: int


class PushNotificationListOut(BaseModel):
    """List of push notifications with pagination."""

    notifications: list[PushNotificationOut]
    total: int
    limit: int
    offset: int



# =============================================================================
# Guest Preview Schemas
# =============================================================================


class GuestPreviewStartIn(BaseModel):
    """Request schema for starting a guest preview session."""

    session_id: str = Field(..., description="Browser/device session identifier")
    device_info: Optional[dict[str, Any]] = Field(
        None, description="Device/browser metadata for analytics"
    )


class GuestPreviewStartOut(BaseModel):
    """Response schema for starting a guest preview session."""

    preview_id: UUID
    lesson_id: UUID
    lesson_title: str
    lesson_description: str
    motif_name: str
    urn_name: str
    started_at: datetime


class GuestPreviewLessonOut(BaseModel):
    """Response schema for getting the demo lesson for guests."""

    lesson_id: UUID
    motif_id: UUID
    motif_name: str
    motif_description: str
    urn_id: UUID
    urn_name: str
    urn_thumbnail_url: Optional[str] = None
    intro_text: Optional[str] = None
    description: str
    historical_context: Optional[str] = None
    symbolism: Optional[str] = None
    fun_fact: Optional[str] = None
    additional_images: Optional[list[str]] = None


class GuestPreviewCompleteIn(BaseModel):
    """Request schema for marking a preview session as complete."""

    session_id: str = Field(..., description="Browser/device session identifier")


class GuestPreviewCompleteOut(BaseModel):
    """Response schema for marking a preview session as complete."""

    success: bool
    message: str
    completed_at: datetime
    preview_id: UUID


class GuestPreviewConvertIn(BaseModel):
    """Request schema for linking a preview session to a new user account."""

    session_id: str = Field(..., description="Browser/device session identifier")


class GuestPreviewConvertOut(BaseModel):
    """Response schema for linking a preview session to a user account."""

    success: bool
    message: str
    preview_sessions_converted: int


# =============================================================================
# Hearts System Schemas
# =============================================================================


class HeartsStatusOut(BaseSchema):
    """Output schema for current hearts status."""

    current_hearts: int
    max_hearts: int
    last_heart_lost_at: Optional[datetime] = None
    hearts_refill_at: Optional[datetime] = None
    unlimited_until: Optional[datetime] = None
    streak_freezes: int
    is_unlimited: bool = False
    time_until_refill_seconds: Optional[int] = None
    updated_at: datetime


class UseHeartIn(BaseModel):
    """Request schema for using a heart."""

    reason: str = Field(default="quiz_wrong", pattern="^(quiz_wrong|practice)$")
    metadata: Optional[dict[str, Any]] = Field(
        None, description="Additional context (e.g., quiz_id, question_id)"
    )


class UseHeartOut(BaseModel):
    """Response schema for using a heart."""

    success: bool
    current_hearts: int
    hearts_refill_at: Optional[datetime] = None
    message: str


class RefillHeartsIn(BaseModel):
    """Request schema for refilling hearts."""

    method: str = Field(
        ...,
        pattern="^(purchase|ad_watch|reward|admin)$",
        description="Method used to refill hearts"
    )
    amount: Optional[int] = Field(
        None, ge=1, le=5, description="Number of hearts to refill (defaults to max)"
    )
    metadata: Optional[dict[str, Any]] = Field(
        None, description="Additional context (e.g., transaction_id, reward_id)"
    )


class RefillHeartsOut(BaseModel):
    """Response schema for refilling hearts."""

    success: bool
    current_hearts: int
    hearts_added: int
    message: str


class UseStreakFreezeIn(BaseModel):
    """Request schema for using a streak freeze to restore hearts."""

    pass  # No additional fields needed


class UseStreakFreezeForHeartsOut(BaseModel):
    """Response schema for using streak freeze to restore hearts."""

    success: bool
    current_hearts: int
    remaining_freezes: int
    message: str


class HeartTransactionOut(BaseSchema):
    """Output schema for heart transaction history."""

    id: UUID
    amount: int
    reason: str
    balance_after: int
    metadata: Optional[dict[str, Any]] = None
    created_at: datetime


class HeartTransactionListOut(BaseModel):
    """Output schema for paginated heart transaction history."""

    transactions: list[HeartTransactionOut]
    total: int
    page: int
    page_size: int


# =============================================================================
# ADAPTIVE QUIZ SCHEMAS
# =============================================================================


class UserSkillLevelOut(BaseModel):
    """Output schema for user skill level."""

    id: UUID
    user_id: UUID
    skill_type: str
    skill_level: float  # 0.0 to 1.0
    total_questions: int
    correct_answers: int
    accuracy: float  # Computed field
    last_updated_at: datetime
    created_at: datetime

    @model_validator(mode="before")
    @classmethod
    def compute_accuracy(cls, data: Any) -> Any:
        """Compute accuracy percentage."""
        if isinstance(data, dict):
            total = data.get("total_questions", 0)
            correct = data.get("correct_answers", 0)
            data["accuracy"] = (correct / total * 100) if total > 0 else 0.0
        else:
            # Handle SQLAlchemy model
            total = getattr(data, "total_questions", 0)
            correct = getattr(data, "correct_answers", 0)
            accuracy = (correct / total * 100) if total > 0 else 0.0
            # Create dict from model
            data = {
                "id": data.id,
                "user_id": data.user_id,
                "skill_type": data.skill_type,
                "skill_level": data.skill_level,
                "total_questions": total,
                "correct_answers": correct,
                "accuracy": accuracy,
                "last_updated_at": data.last_updated_at,
                "created_at": data.created_at,
            }
        return data


class UserSkillsOut(BaseModel):
    """Output schema for all user skills."""

    skills: list[UserSkillLevelOut]
    overall_level: float  # Average skill level


class AdaptiveQuizOut(BaseModel):
    """Output schema for adaptive quiz."""

    motif_id: Optional[UUID] = None
    skill_type: Optional[str] = None
    recommended_difficulty: float
    questions: list[QuizQuestionOut]


# =============================================================================
# Recommendation Schemas
# =============================================================================


class RecommendationContentOut(BaseModel):
    """Schema for a single recommended content item."""

    content_type: str = Field(..., description="Type of content (lesson, motif, quest)")
    content_id: str = Field(..., description="UUID of the content")
    title: str
    description: Optional[str] = None
    reason: str = Field(..., description="Reason for recommendation")
    score: Optional[float] = Field(None, description="Recommendation score")
    similarity_score: Optional[float] = None
    popularity_score: Optional[int] = None
    recommendation_score: Optional[int] = None
    status: Optional[str] = None
    motif_id: Optional[str] = None
    last_completed: Optional[str] = None


class RecommendationsOut(BaseModel):
    """Output schema for personalized recommendations."""

    continue_learning: Optional[list[RecommendationContentOut]] = Field(
        default_factory=list,
        description="Lessons to continue"
    )
    discover_new: Optional[list[RecommendationContentOut]] = Field(
        default_factory=list,
        description="New content based on interests"
    )
    review_needed: Optional[list[RecommendationContentOut]] = Field(
        default_factory=list,
        description="Content needing review"
    )
    popular: Optional[list[RecommendationContentOut]] = Field(
        default_factory=list,
        description="Trending content"
    )


class SimilarContentOut(BaseModel):
    """Output schema for similar content."""

    similar_content: list[RecommendationContentOut]
    total: int


class RecordInteractionIn(BaseModel):
    """Input schema for recording content interaction."""

    content_type: str = Field(..., pattern="^(lesson|motif|quest)$")
    content_id: UUID
    interaction_type: str = Field(..., pattern="^(view|complete|like|save)$")
    duration_seconds: Optional[int] = Field(None, ge=0)
    metadata: Optional[dict[str, Any]] = None


class RecordInteractionOut(BaseModel):
    """Output schema for recording content interaction."""

    success: bool
    message: str
    interaction_id: str


class RecommendationFeedbackIn(BaseModel):
    """Input schema for recommendation feedback."""

    content_id: UUID
    content_type: str = Field(..., pattern="^(lesson|motif|quest)$")
    feedback_type: str = Field(
        ...,
        pattern="^(helpful|not_helpful|irrelevant|already_seen)$",
        description="Type of feedback"
    )
    metadata: Optional[dict[str, Any]] = None


class RecommendationFeedbackOut(BaseModel):
    """Output schema for recommendation feedback."""

    success: bool
    message: str


# =============================================================================
# Spaced Repetition Review Schemas
# =============================================================================


class ReviewHistoryEntry(BaseModel):
    """Single review history entry."""

    quality: int
    reviewed_at: datetime
    ease_factor: float
    interval_days: int
    repetitions: int


class SpacedRepetitionCardOut(BaseSchema):
    """Output schema for spaced repetition card."""

    id: UUID
    user_id: UUID
    motif_id: UUID
    ease_factor: float
    interval_days: int
    repetitions: int
    next_review_at: datetime
    last_reviewed_at: Optional[datetime] = None
    review_history: list[ReviewHistoryEntry]
    created_at: datetime
    updated_at: datetime

    # Include motif details
    motif: Optional[Any] = None  # Will be populated with MotifOut


class ReviewSubmitIn(BaseModel):
    """Input schema for submitting a review."""

    quality: int = Field(..., ge=0, le=5, description="Quality rating from 0-5")


class ReviewStatsOut(BaseModel):
    """Output schema for user review statistics."""

    total_cards: int
    due_cards: int
    reviewed_today: int
    mastered_cards: int
    learning_cards: int
    total_reviews: int


class AddCardIn(BaseModel):
    """Input schema for adding a card to review deck."""

    motif_id: UUID


class DueCardsOut(BaseModel):
    """Output schema for due cards list."""

    cards: list[SpacedRepetitionCardOut]
    total_due: int


# =============================================================================
# Classroom Schemas
# =============================================================================


class ClassroomCreateIn(BaseModel):
    """Input schema for creating a classroom."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    max_students: Optional[int] = Field(None, ge=1, le=1000)
    settings: Optional[dict[str, Any]] = None


class ClassroomUpdateIn(BaseModel):
    """Input schema for updating a classroom."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    max_students: Optional[int] = Field(None, ge=1, le=1000)
    settings: Optional[dict[str, Any]] = None


class ClassroomJoinIn(BaseModel):
    """Input schema for joining a classroom by code."""

    class_code: str = Field(..., min_length=6, max_length=10, pattern="^[A-Z0-9]+$")


class ClassMemberOut(BaseModel):
    """Output schema for a class member."""

    id: UUID
    user_id: UUID
    display_name: str
    email: str
    role: str
    joined_at: datetime


class ClassroomSummaryOut(BaseModel):
    """Output schema for classroom summary (list view)."""

    id: UUID
    name: str
    description: Optional[str] = None
    teacher_id: UUID
    class_code: str
    max_students: Optional[int] = None
    is_archived: bool
    member_count: int
    assignment_count: int
    created_at: datetime
    updated_at: datetime


class ClassroomDetailOut(BaseModel):
    """Output schema for detailed classroom view."""

    id: UUID
    name: str
    description: Optional[str] = None
    teacher_id: UUID
    teacher_name: str
    class_code: str
    max_students: Optional[int] = None
    is_archived: bool
    settings: Optional[dict[str, Any]] = None
    members: list[ClassMemberOut]
    member_count: int
    assignment_count: int
    created_at: datetime
    updated_at: datetime


class ClassroomJoinOut(BaseModel):
    """Output schema for joining a classroom."""

    classroom: ClassroomDetailOut
    message: str


# =============================================================================
# Student Progress Schemas (P1-TEACH-03)
# =============================================================================


class LessonStatsOut(BaseModel):
    """Lesson/motif completion statistics."""

    total_motifs: int
    discovered: int
    learned: int
    mastered: int


class QuizStatsOut(BaseModel):
    """Quiz performance statistics."""

    total_attempts: int
    passed: int
    average_score: float


class EngagementStatsOut(BaseModel):
    """Student engagement statistics."""

    current_streak: int
    longest_streak: int
    total_xp: int
    time_spent_minutes: int


class StudentProgressOut(BaseModel):
    """Detailed progress for a student in a classroom."""

    student_id: UUID
    classroom_id: UUID
    joined_at: datetime
    overall_completion_percent: float
    lessons: LessonStatsOut
    quizzes: QuizStatsOut
    engagement: EngagementStatsOut


class ClassProgressAveragesOut(BaseModel):
    """Class-wide average metrics."""

    completion_percent: float
    discovered_motifs: float
    learned_motifs: float
    mastered_motifs: float
    quiz_attempts: float
    quizzes_passed: float
    average_quiz_score: float
    current_streak: float
    total_xp: float


class ClassProgressSummaryOut(BaseModel):
    """Class-wide progress summary."""

    classroom_id: UUID
    student_count: int
    averages: ClassProgressAveragesOut


class LeaderboardEntryOut(BaseModel):
    """Single entry in the class leaderboard."""

    rank: int
    student_id: UUID
    display_name: str
    total_xp: int
    current_streak: int
    discovered_motifs: int
    mastered_motifs: int
    quizzes_passed: int


class LeaderboardOut(BaseModel):
    """Class leaderboard response."""

    classroom_id: UUID
    order_by: str
    entries: list[LeaderboardEntryOut]


# =============================================================================
# Quest Assignment Schemas
# =============================================================================


class QuestAssignmentCreateIn(BaseModel):
    """Input schema for creating a quest assignment."""

    quest_id: UUID = Field(..., description="Quest to assign")
    due_at: Optional[datetime] = Field(None, description="Due date for the assignment")
    points_override: Optional[int] = Field(None, ge=0, description="Custom points for this assignment")
    notes: Optional[str] = Field(None, max_length=1000, description="Teacher notes for students")
    student_id: Optional[UUID] = Field(None, description="If specified, assign to individual student only")


class QuestAssignmentUpdateIn(BaseModel):
    """Input schema for updating a quest assignment."""

    due_at: Optional[datetime] = Field(None, description="Due date for the assignment")
    points_override: Optional[int] = Field(None, ge=0, description="Custom points for this assignment")
    notes: Optional[str] = Field(None, max_length=1000, description="Teacher notes for students")


class QuestBriefOut(BaseModel):
    """Brief quest info for assignment listing."""

    id: UUID
    slug: str
    name: str
    description: Optional[str] = None


class AssignmentProgressBriefOut(BaseModel):
    """Brief progress info for a student on an assignment."""

    user_id: UUID
    display_name: str
    status: str
    completed_at: Optional[datetime] = None


class QuestAssignmentOut(BaseModel):
    """Output schema for quest assignment."""

    id: UUID
    class_id: UUID
    quest: QuestBriefOut
    assigned_by_id: Optional[UUID] = None
    assigned_by_name: Optional[str] = None
    due_at: Optional[datetime] = None
    assigned_at: datetime
    points_override: Optional[int] = None
    notes: Optional[str] = None
    total_students: int = 0
    completed_count: int = 0
    in_progress_count: int = 0
    assigned_count: int = 0
    completion_rate: float = 0.0


class QuestAssignmentDetailOut(BaseModel):
    """Detailed output schema for quest assignment with student progress."""

    id: UUID
    class_id: UUID
    quest: QuestBriefOut
    assigned_by_id: Optional[UUID] = None
    assigned_by_name: Optional[str] = None
    due_at: Optional[datetime] = None
    assigned_at: datetime
    points_override: Optional[int] = None
    notes: Optional[str] = None
    student_progress: list[AssignmentProgressBriefOut]
    total_students: int = 0
    completed_count: int = 0
    in_progress_count: int = 0
    assigned_count: int = 0
    completion_rate: float = 0.0


class StudentAssignmentOut(BaseModel):
    """Output schema for student's view of an assignment."""

    assignment_id: UUID
    quest_id: UUID
    quest_name: str
    quest_description: Optional[str] = None
    classroom_id: UUID
    classroom_name: str
    due_at: Optional[datetime] = None
    assigned_at: datetime
    points_override: Optional[int] = None
    notes: Optional[str] = None
    status: str
    completed_at: Optional[datetime] = None
    is_overdue: bool = False


class AssignmentSubmitOut(BaseModel):
    """Output schema for assignment submission."""

    assignment_id: UUID
    status: str
    completed_at: Optional[datetime] = None
    message: str


# =============================================================================
# Learning Path Schemas
# =============================================================================


class LearningPathItemOut(BaseModel):
    """Output schema for a learning path item (lesson/review/quiz)."""

    item_id: UUID = Field(..., description="ID of the lesson/motif")
    motif_id: Optional[UUID] = Field(None, description="Associated motif ID")
    order: int = Field(..., description="Order in the path")
    item_type: str = Field(..., description="Type of item: lesson, review, or quiz")
    reason: Optional[str] = Field(None, description="Reason for recommendation")
    priority: Optional[str] = Field(None, description="Priority: low, medium, high")
    difficulty: Optional[int] = Field(None, description="Difficulty level for quizzes")
    is_completed: bool = Field(default=False, description="Whether item is completed")


class LearningPathOut(BaseModel):
    """Output schema for a complete learning path."""

    id: UUID
    path_date: datetime
    lessons: list[LearningPathItemOut]
    reviews: list[LearningPathItemOut]
    quizzes: list[LearningPathItemOut]
    estimated_time_minutes: int
    is_completed: bool
    completed_at: Optional[datetime] = None
    generated_at: datetime
    progress: dict[str, Any] = Field(
        default_factory=dict,
        description="Progress statistics (completed/total for each type)"
    )


class LearningPathGenerateIn(BaseModel):
    """Input schema for generating a new learning path."""

    force_regenerate: bool = Field(
        default=False,
        description="Force regeneration even if path exists for today"
    )
    target_date: Optional[datetime] = Field(
        None,
        description="Target date for the path (defaults to today)"
    )


class CompletePathItemIn(BaseModel):
    """Input schema for marking a path item as complete."""

    item_type: str = Field(
        ...,
        description="Type of item: lesson, review, or quiz"
    )
    item_id: UUID = Field(
        ...,
        description="ID of the item (lesson_id or motif_id)"
    )

    @field_validator("item_type")
    @classmethod
    def validate_item_type(cls, v: str) -> str:
        """Validate item type."""
        if v not in ["lesson", "review", "quiz"]:
            raise ValueError("item_type must be one of: lesson, review, quiz")
        return v


class CompletePathItemOut(BaseModel):
    """Output schema for path item completion."""

    success: bool
    message: str
    already_completed: bool
    completed_at: datetime
    path_completed: bool = Field(
        default=False,
        description="Whether the entire path is now completed"
    )
    progress: int = Field(..., description="Number of items completed")
    total: int = Field(..., description="Total items in path")


class LearningPathHistoryOut(BaseModel):
    """Output schema for learning path history."""

    paths: list[LearningPathOut]
    total_paths: int
    days_analyzed: int


class LearningPathStatsOut(BaseModel):
    """Output schema for learning path statistics."""

    total_paths_generated: int
    completed_paths: int
    completion_rate: float
    lessons: dict[str, Any] = Field(
        ...,
        description="Lesson statistics (recommended, completed, completion_rate)"
    )
    reviews: dict[str, Any] = Field(
        ...,
        description="Review statistics (recommended, completed, completion_rate)"
    )
    quizzes: dict[str, Any] = Field(
        ...,
        description="Quiz statistics (recommended, completed, completion_rate)"
    )
    days_analyzed: int


# =============================================================================
# Lesson Prerequisite and Sequence Schemas
# =============================================================================


class LessonPrerequisiteOut(BaseModel):
    """Output schema for lesson prerequisites."""
    id: UUID
    lesson_id: UUID
    prerequisite_lesson_id: UUID
    is_strict: bool
    created_at: datetime


class PrerequisiteLessonInfo(BaseModel):
    """Info about a prerequisite lesson."""
    id: UUID
    motif_id: UUID
    motif_name: str
    motif_slug: str
    difficulty_level: Optional[int] = None
    estimated_time_minutes: Optional[int] = None
    is_strict: bool
    is_completed: bool


class LessonPrerequisitesOut(BaseModel):
    """Output schema for getting lesson prerequisites with details."""
    lesson_id: UUID
    prerequisites: list[PrerequisiteLessonInfo]
    all_prerequisites_met: bool


class LessonUnlockStatusOut(BaseModel):
    """Output schema for checking if a lesson is unlocked."""
    lesson_id: UUID
    is_unlocked: bool
    missing_prerequisites: list[PrerequisiteLessonInfo]
    recommended_prerequisites: list[PrerequisiteLessonInfo]


class NextLessonOut(BaseModel):
    """Output schema for getting the next recommended lesson."""
    lesson_id: Optional[UUID] = None
    motif_id: Optional[UUID] = None
    motif_name: Optional[str] = None
    motif_slug: Optional[str] = None
    urn_id: Optional[UUID] = None
    urn_name: Optional[str] = None
    difficulty_level: Optional[int] = None
    estimated_time_minutes: Optional[int] = None
    reason: str  # Why this lesson is recommended
    has_prerequisites: bool
    progress_status: Optional[str] = None


class LessonSequenceItem(BaseModel):
    """A single lesson in the learning sequence."""
    lesson_id: UUID
    motif_id: UUID
    motif_name: Optional[str] = None
    motif_slug: Optional[str] = None
    urn_id: Optional[UUID] = None
    urn_name: Optional[str] = None
    difficulty_level: Optional[int] = None
    estimated_time_minutes: Optional[int] = None
    is_unlocked: bool
    is_completed: bool
    progress_status: Optional[str] = None
    position: int


class LessonSequenceOut(BaseModel):
    """Output schema for the full learning sequence."""
    urn_id: Optional[UUID] = None
    urn_name: Optional[str] = None
    total_lessons: int
    completed_lessons: int
    current_position: int
    sequence: list[LessonSequenceItem]


# =============================================================================
# AI Conversation Schemas
# =============================================================================


class AIMessageOut(BaseModel):
    """Output schema for AI messages."""

    id: UUID
    conversation_id: UUID
    role: str  # "user", "assistant", "system"
    content: str
    tokens_used: Optional[int] = None
    created_at: datetime


class AIConversationSummaryOut(BaseModel):
    """Output schema for conversation list (summary view)."""

    id: UUID
    title: Optional[str] = None
    context_type: Optional[str] = None
    context_id: Optional[UUID] = None
    is_active: bool
    message_count: int
    created_at: datetime
    updated_at: datetime
    # Last message preview
    last_message: Optional[str] = None
    last_message_at: Optional[datetime] = None


class AIConversationDetailOut(BaseModel):
    """Output schema for conversation detail with messages."""

    id: UUID
    title: Optional[str] = None
    context_type: Optional[str] = None
    context_id: Optional[UUID] = None
    is_active: bool
    message_count: int
    created_at: datetime
    updated_at: datetime
    messages: list[AIMessageOut] = Field(default_factory=list)


class AIConversationCreateIn(BaseModel):
    """Input schema for creating a new conversation."""

    title: Optional[str] = Field(None, max_length=255)
    context_type: Optional[str] = Field(None, max_length=50)
    context_id: Optional[UUID] = None
    initial_message: Optional[str] = Field(None, description="Optional first message")


class AIConversationCreateOut(BaseModel):
    """Output schema for newly created conversation."""

    id: UUID
    title: Optional[str] = None
    context_type: Optional[str] = None
    context_id: Optional[UUID] = None
    created_at: datetime
    message: str = "Conversation created successfully"


class AISendMessageIn(BaseModel):
    """Input schema for sending a message in a conversation."""

    message: str = Field(..., min_length=1, max_length=5000)


class AISendMessageOut(BaseModel):
    """Output schema for message response."""

    message: AIMessageOut  # User's message
    response: AIMessageOut  # AI's response
    conversation_id: UUID
    tokens_used: Optional[int] = None


class AIConversationListOut(BaseModel):
    """Output schema for list of conversations."""

    conversations: list[AIConversationSummaryOut]
    total: int
    page: int = 1
    page_size: int = 20
    has_more: bool = False


# =============================================================================
# Social Sharing Schemas
# =============================================================================


class ShareCreateIn(BaseModel):
    """Input schema for creating a share."""

    share_type: str = Field(
        ...,
        pattern="^(achievement|badge|streak|level_up|certificate)$",
        description="Type of content being shared"
    )
    content_id: Optional[UUID] = Field(
        None,
        description="ID of the shared item (badge_id, certificate_id, etc.)"
    )
    caption: Optional[str] = Field(
        None,
        max_length=500,
        description="User's custom message"
    )
    visibility: str = Field(
        default="public",
        pattern="^(public|followers|private)$",
        description="Who can view this share"
    )


class ShareOut(BaseSchema):
    """Output schema for a share."""

    id: UUID
    user_id: UUID
    share_type: str
    content_id: Optional[UUID] = None
    caption: Optional[str] = None
    visibility: str
    share_url: Optional[str] = None
    view_count: int
    created_at: datetime


class ShareDetailOut(BaseSchema):
    """Detailed output schema for a share with user info."""

    id: UUID
    user_id: UUID
    user_display_name: str
    user_avatar_url: Optional[str] = None
    user_xp: int
    share_type: str
    content_id: Optional[UUID] = None
    content_data: Optional[dict[str, Any]] = None  # Badge info, certificate info, etc.
    caption: Optional[str] = None
    visibility: str
    share_url: Optional[str] = None
    view_count: int
    created_at: datetime


class ShareListOut(BaseModel):
    """Output schema for paginated list of shares."""

    shares: list[ShareDetailOut]
    total: int
    page: int
    page_size: int


class UserActivityOut(BaseSchema):
    """Output schema for user activity item in feed."""

    id: UUID
    activity_type: str  # share, achievement, level_up, etc.
    user_id: UUID
    user_display_name: str
    user_avatar_url: Optional[str] = None
    content: dict[str, Any]  # Flexible content based on activity type
    created_at: datetime


class ActivityFeedOut(BaseModel):
    """Output schema for activity feed."""

    activities: list[UserActivityOut]
    total: int
    page: int
    page_size: int
    has_more: bool


# =============================================================================
# Friend & Follow System Schemas
# =============================================================================


class FollowUserOut(BaseSchema):
    """Output schema for a follow relationship."""

    id: UUID
    user_id: UUID
    display_name: str
    username: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    total_xp: int
    followed_at: datetime


class FollowListOut(BaseModel):
    """Output schema for list of follows."""

    users: list[FollowUserOut]
    total: int
    page: int = 1
    page_size: int = 20


class FriendOut(BaseSchema):
    """Output schema for a friend (mutual follow)."""

    id: UUID
    user_id: UUID
    display_name: str
    username: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    total_xp: int
    current_streak: int = 0
    is_online: bool = False


class FriendListOut(BaseModel):
    """Output schema for list of friends."""

    friends: list[FriendOut]
    total: int


class FriendRequestCreateIn(BaseModel):
    """Input schema for creating a friend request."""

    to_user_id: UUID = Field(..., description="User ID to send friend request to")
    message: Optional[str] = Field(None, max_length=500, description="Optional message with request")


class FriendRequestOut(BaseSchema):
    """Output schema for a friend request."""

    id: UUID
    from_user_id: UUID
    from_user_display_name: str
    from_user_avatar_url: Optional[str] = None
    to_user_id: UUID
    to_user_display_name: str
    to_user_avatar_url: Optional[str] = None
    status: str
    created_at: datetime
    responded_at: Optional[datetime] = None


class SocialUserOut(BaseModel):
    """Output schema for social user search results."""

    id: UUID
    display_name: str
    username: Optional[str] = None
    avatar_url: Optional[str] = None
    total_xp: int
    is_following: bool
    is_friend: bool


class SocialUserSearchOut(BaseModel):
    """Output schema for social user search."""

    users: list[SocialUserOut]
    total: int
    page: int = 1
    page_size: int = 20


class FriendRequestListOut(BaseModel):
    """Output schema for list of friend requests."""

    requests: list[FriendRequestOut]
    total: int
    pending_count: int = 0


# =============================================================================
# Email Template & Scheduled Email Schemas
# =============================================================================


class EmailTemplateCreate(BaseModel):
    """Schema for creating an email template."""

    key: str = Field(..., min_length=1, max_length=100, description="Unique template key")
    name: str = Field(..., min_length=1, max_length=200, description="Template name")
    subject_template: str = Field(..., min_length=1, max_length=500, description="Email subject template")
    body_html: str = Field(..., min_length=1, description="HTML email body")
    body_text: Optional[str] = Field(None, description="Plain text email body")
    is_active: bool = Field(True, description="Whether template is active")


class EmailTemplateUpdate(BaseModel):
    """Schema for updating an email template."""

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    subject_template: Optional[str] = Field(None, min_length=1, max_length=500)
    body_html: Optional[str] = Field(None, min_length=1)
    body_text: Optional[str] = None
    is_active: Optional[bool] = None


class EmailTemplateOut(BaseModel):
    """Schema for email template output."""

    id: UUID
    key: str
    name: str
    subject_template: str
    body_html: str
    body_text: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class EmailTemplateListOut(BaseModel):
    """Schema for list of email templates."""

    templates: list[EmailTemplateOut]
    total: int


class ScheduledEmailOut(BaseModel):
    """Schema for scheduled email output."""

    id: UUID
    user_id: UUID
    template_id: UUID
    template_key: Optional[str] = None
    template_name: Optional[str] = None
    scheduled_for: datetime
    status: str
    context_data: Optional[dict[str, Any]] = None
    sent_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime


class ScheduledEmailListOut(BaseModel):
    """Schema for list of scheduled emails."""

    emails: list[ScheduledEmailOut]
    total: int
    status_counts: dict[str, int] = Field(default_factory=dict)


class SendTestEmailIn(BaseModel):
    """Schema for sending a test email."""

    template_id: UUID
    recipient_email: EmailStr
    context_data: Optional[dict[str, Any]] = Field(
        default_factory=dict,
        description="Test data for template variables"
    )


class SendTestEmailOut(BaseModel):
    """Schema for test email send response."""

    success: bool
    message: str
    scheduled_email_id: Optional[UUID] = None


# =============================================================================
# Feature Flags and Experiments Schemas
# =============================================================================


class FeatureFlagOut(BaseSchema):
    """Output schema for feature flag."""

    id: UUID
    key: str
    name: str
    description: Optional[str] = None
    is_enabled: bool
    rollout_percentage: int
    user_whitelist: Optional[list[str]] = None
    user_blacklist: Optional[list[str]] = None
    rules: Optional[dict[str, Any]] = None
    created_by_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime


class FeatureFlagCreateIn(BaseModel):
    """Input schema for creating a feature flag."""

    key: str = Field(..., min_length=1, max_length=100, description="Unique feature key (e.g., 'new_quiz_ui')")
    name: str = Field(..., min_length=1, max_length=255, description="Display name")
    description: Optional[str] = Field(None, description="Feature description")
    is_enabled: bool = Field(default=False, description="Global on/off switch")
    rollout_percentage: int = Field(default=0, ge=0, le=100, description="Percentage of users (0-100)")
    user_whitelist: Optional[list[str]] = Field(None, description="User IDs always enabled")
    user_blacklist: Optional[list[str]] = Field(None, description="User IDs always disabled")
    rules: Optional[dict[str, Any]] = Field(None, description="Targeting rules (role, signup_date, etc.)")


class FeatureFlagUpdateIn(BaseModel):
    """Input schema for updating a feature flag."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    is_enabled: Optional[bool] = None
    rollout_percentage: Optional[int] = Field(None, ge=0, le=100)
    user_whitelist: Optional[list[str]] = None
    user_blacklist: Optional[list[str]] = None
    rules: Optional[dict[str, Any]] = None


class UserFeaturesOut(BaseModel):
    """Output schema for user-specific feature flags."""

    features: dict[str, bool]


class FeatureCheckOut(BaseModel):
    """Output schema for checking a specific feature."""

    key: str
    enabled: bool
    metadata: Optional[dict[str, Any]] = None


class ExperimentVariantOut(BaseModel):
    """Output schema for an experiment variant."""

    key: str
    name: str
    weight: int


class ExperimentOut(BaseSchema):
    """Output schema for experiment."""

    id: UUID
    key: str
    name: str
    description: Optional[str] = None
    variants: list[dict[str, Any]]
    target_audience: Optional[dict[str, Any]] = None
    is_active: bool
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    created_by_id: Optional[UUID] = None
    created_at: datetime


class ExperimentCreateIn(BaseModel):
    """Input schema for creating an experiment."""

    key: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    variants: list[dict[str, Any]] = Field(
        ...,
        description="List of variants with 'key', 'name', and 'weight' fields"
    )
    target_audience: Optional[dict[str, Any]] = Field(
        None,
        description="Optional targeting rules for audience segmentation"
    )
    is_active: bool = Field(default=False)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    @field_validator("variants")
    @classmethod
    def validate_variants(cls, v):
        """Validate that variants have required fields."""
        if not v:
            raise ValueError("At least one variant is required")

        for variant in v:
            if "key" not in variant or "name" not in variant or "weight" not in variant:
                raise ValueError("Each variant must have 'key', 'name', and 'weight' fields")
            if not isinstance(variant["weight"], int) or variant["weight"] < 0:
                raise ValueError("Variant weight must be a non-negative integer")

        return v


class ExperimentUpdateIn(BaseModel):
    """Input schema for updating an experiment."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    variants: Optional[list[dict[str, Any]]] = None
    target_audience: Optional[dict[str, Any]] = None
    is_active: Optional[bool] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    @field_validator("variants")
    @classmethod
    def validate_variants(cls, v):
        """Validate that variants have required fields."""
        if v is None:
            return v

        if not v:
            raise ValueError("At least one variant is required")

        for variant in v:
            if "key" not in variant or "name" not in variant or "weight" not in variant:
                raise ValueError("Each variant must have 'key', 'name', and 'weight' fields")
            if not isinstance(variant["weight"], int) or variant["weight"] < 0:
                raise ValueError("Variant weight must be a non-negative integer")

        return v


class UserExperimentsOut(BaseModel):
    """Output schema for user-specific experiment assignments."""

    experiments: dict[str, str]  # experiment_key -> variant_key


class UserExperimentAssignmentOut(BaseSchema):
    """Output schema for user experiment assignment."""

    id: UUID
    user_id: UUID
    experiment_id: UUID
    variant_key: str
    assigned_at: datetime


# =============================================================================
# Experiment Event Schemas (P1-EXP-02)
# =============================================================================


class ExperimentEventIn(BaseModel):
    """Input schema for tracking an experiment event."""

    event_type: str = Field(..., description="Event type: impression, conversion, click, custom")
    event_name: str = Field(..., description="Specific event name (e.g., 'completed_onboarding')")
    event_value: Optional[float] = Field(None, description="Optional numeric value")
    metadata: Optional[dict[str, Any]] = Field(None, description="Additional event metadata")


class ExperimentEventOut(BaseSchema):
    """Output schema for experiment event."""

    id: UUID
    experiment_id: UUID
    user_id: UUID
    assignment_id: UUID
    event_type: str
    event_name: str
    event_value: Optional[float] = None
    metadata: Optional[dict[str, Any]] = None
    created_at: datetime


class ExperimentEventListOut(BaseModel):
    """Output schema for list of experiment events."""

    events: list[ExperimentEventOut]
    total: int
    page: int = 1
    page_size: int = 100


class VariantResultOut(BaseModel):
    """Output schema for per-variant experiment results."""

    variant_key: str
    impressions: int
    conversions: int
    conversion_rate: float
    p_value: Optional[float] = None
    chi_square: Optional[float] = None
    is_significant: bool = False
    improvement: Optional[float] = None


class ExperimentResultsOut(BaseModel):
    """Output schema for complete experiment results."""

    experiment_key: str
    experiment_name: str
    conversion_event: str
    variants: dict[str, VariantResultOut]
    winner: Optional[str] = None
    is_significant: bool = False
    significance_threshold: float = 0.05


# =============================================================================
# Experiment Metric Schemas (P1-EXP-03)
# =============================================================================


class ExperimentMetricEventIn(BaseModel):
    """Input schema for recording an experiment metric event."""

    metric_name: str = Field(..., description="Metric name (e.g., 'conversion', 'retention', 'engagement')")
    metric_value: float = Field(..., description="Numeric value for the metric")
    metadata: Optional[dict[str, Any]] = Field(None, description="Additional metric metadata")


class ExperimentMetricEventOut(BaseSchema):
    """Output schema for experiment metric event."""

    id: UUID
    experiment_id: UUID
    user_id: UUID
    variant: str
    metric_name: str
    metric_value: float
    metadata: Optional[dict[str, Any]] = None
    created_at: datetime


class VariantMetricSummary(BaseModel):
    """Summary statistics for a metric per variant."""

    count: int = Field(..., description="Number of metric events")
    sum: float = Field(..., description="Sum of metric values")
    avg: float = Field(..., description="Average metric value")
    min: float = Field(..., description="Minimum metric value")
    max: float = Field(..., description="Maximum metric value")
    improvement_pct: Optional[float] = Field(None, description="Improvement percentage vs control")
    is_better: Optional[bool] = Field(None, description="Whether this variant performs better than control")
    has_sufficient_data: Optional[bool] = Field(None, description="Whether sample size is sufficient")


class MetricComparisonOut(BaseModel):
    """Output schema for metric comparison between variants."""

    metric_name: str
    control_variant: Optional[str] = None
    variants: dict[str, VariantMetricSummary]


class ExperimentMetricSummaryOut(BaseModel):
    """Output schema for complete experiment metric summary."""

    experiment_id: UUID
    experiment_key: str
    experiment_name: str
    metrics: list[str] = Field(..., description="List of available metric names")
    metric_data: Optional[dict[str, Any]] = Field(None, description="Optional detailed metric data")
