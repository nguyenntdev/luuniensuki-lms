from __future__ import annotations

import uuid
from datetime import datetime, date
from enum import Enum
from typing import Any, Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


from .base_model import Base


class UserRole(str, Enum):
    guest = "guest"
    learner = "learner"
    teacher = "teacher"
    admin = "admin"
    super_admin = "super_admin"


class MotifCategory(str, Enum):
    linh_thu = "linh_thu"
    dong_vat = "dong_vat"
    thao_moc = "thao_moc"
    dia_ly = "dia_ly"
    nong_nghiep = "nong_nghiep"
    vo_bi = "vo_bi"
    giao_thuong = "giao_thuong"
    thien_van = "thien_van"
    kien_truc = "kien_truc"


class MotifRarity(str, Enum):
    common = "common"
    uncommon = "uncommon"
    rare = "rare"
    epic = "epic"
    legendary = "legendary"


class UnlockStatus(str, Enum):
    hidden = "hidden"
    discovered = "discovered"
    learned = "learned"
    mastered = "mastered"


class QuestionType(str, Enum):
    # Legacy V1 question types.
    multiple_choice = "multiple_choice"
    true_false = "true_false"
    image_select = "image_select"
    mesh_location = "mesh_location"
    # Historical Learning Engine V2 question types (Spec sections 32-33).
    # The values mirror the ``history_question_types`` registry table created
    # by migration 0050. The Python enum is extended so fresh databases built
    # via ``Base.metadata.create_all`` (tests) include the full enum; the
    # migration keeps the existing Postgres enum untouched for prod safety.
    chronology_order = "chronology_order"
    image_identification = "image_identification"
    map_location = "map_location"
    urn_hotspot = "urn_hotspot"
    evidence_match = "evidence_match"
    entity_match = "entity_match"
    compare_two = "compare_two"
    source_interpretation = "source_interpretation"
    short_response = "short_response"
    multi_select = "multi_select"
    relationship_chain = "relationship_chain"


class MasterySkill(str, Enum):
    """Historical mastery skill dimensions (Spec section 34)."""
    recognition = "recognition"
    factual_recall = "factual_recall"
    chronology = "chronology"
    geography = "geography"
    source_literacy = "source_literacy"
    evidence_reasoning = "evidence_reasoning"
    comparison = "comparison"
    contextualization = "contextualization"


class BadgeCategory(str, Enum):
    quest = "quest"
    achievement = "achievement"
    collection = "collection"
    special = "special"


class BadgeTier(str, Enum):
    bronze = "bronze"
    silver = "silver"
    gold = "gold"
    platinum = "platinum"


class TagType(str, Enum):
    topic = "topic"
    difficulty = "difficulty"
    audience = "audience"
    era = "era"
    style = "style"


class ContentType(str, Enum):
    lesson = "lesson"
    motif = "motif"
    quiz = "quiz"
    quest = "quest"


class ErrorType(str, Enum):
    crash = "crash"
    error = "error"
    exception = "exception"


class NotificationType(str, Enum):
    streak_reminder = "streak_reminder"
    daily_mission = "daily_mission"
    achievement = "achievement"
    social = "social"
    system = "system"


class NotificationStatus(str, Enum):
    pending = "pending"
    sent = "sent"
    delivered = "delivered"
    failed = "failed"
    anr = "anr"


class ContentRating(str, Enum):
    """Age-appropriate content rating system."""
    everyone = "everyone"  # Suitable for all ages
    teen = "teen"  # Ages 13+
    mature = "mature"  # Ages 18+


class ContentStatus(str, Enum):
    draft = "draft"
    review = "review"
    published = "published"
    archived = "archived"


class MilestoneType(str, Enum):
    """Types of user milestones that can be achieved."""
    first_motif_discovered = "first_motif_discovered"
    first_quiz_passed = "first_quiz_passed"
    first_lesson_completed = "first_lesson_completed"
    first_badge_earned = "first_badge_earned"
    first_streak_7 = "first_streak_7"
    onboarding_completed = "onboarding_completed"


class InteractionType(str, Enum):
    """Types of user content interactions."""
    view = "view"
    complete = "complete"
    like = "like"
    save = "save"


class SkillType(str, Enum):
    """Types of skills for adaptive learning."""
    motif_recognition = "motif_recognition"
    history_knowledge = "history_knowledge"
    cultural_understanding = "cultural_understanding"


class HintType(str, Enum):
    """Types of quiz hints available to users."""
    explain = "explain"  # Explain the concept without giving answer (0 hearts)
    clue = "clue"  # Give a subtle clue towards the answer (1 heart)
    elimination = "elimination"  # Eliminate one wrong answer (2 hearts)


class FriendRequestStatus(str, Enum):
    """Status of friend requests."""
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"


class EmailStatus(str, Enum):
    """Status of scheduled emails."""
    pending = "pending"
    sent = "sent"
    failed = "failed"
    cancelled = "cancelled"


class FlagType(str, Enum):
    """Types of feature flags."""
    boolean = "boolean"  # Simple on/off toggle
    percentage = "percentage"  # Gradual rollout to percentage of users
    user_list = "user_list"  # Specific list of allowed users


class LeaderboardScope(str, Enum):
    """Scope/type of leaderboard view."""
    global_ = "global"
    friends = "friends"
    class_ = "class"


class LiveSessionStatus(str, Enum):
    """Status of a live classroom session."""

    scheduled = "scheduled"
    live = "live"
    ended = "ended"


class LiveParticipantRole(str, Enum):
    """Role of a participant in a live session."""

    host = "host"
    cohost = "cohost"
    learner = "learner"
    ai_teacher = "ai_teacher"


class LeagueTier(str, Enum):
    """League tiers for weekly competitive leagues (Duolingo-style)."""
    bronze = "bronze"
    silver = "silver"
    gold = "gold"
    platinum = "platinum"
    diamond = "diamond"
    obsidian = "obsidian"


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        Index("idx_users_email", "email"),
        Index("idx_users_username", "username"),
        Index("idx_users_role", "role"),
        Index("idx_users_starting_urn", "starting_urn_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    avatar_url: Mapped[Optional[str]] = mapped_column(Text)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    username: Mapped[Optional[str]] = mapped_column(
        String(50), unique=True, nullable=True
    )
    starting_urn_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("urns.id", ondelete="SET NULL"),
        nullable=True,
    )
    is_profile_public: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )
    ai_personalization_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, name="user_role", native_enum=True),
        nullable=False,
        server_default=text("'learner'"),
    )
    total_xp: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    current_streak: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    longest_streak: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    streak_freezes: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    onboarding_goal: Mapped[Optional[str]] = mapped_column(String(50))
    onboarding_completed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    onboarding_completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )

    # XP Boost fields
    xp_boost_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    xp_boost_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    xp_boost_multiplier: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("2")
    )

    # Age verification fields
    birth_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    age_verified: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    age_verified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Push notification permission tracking
    push_permission_prompted: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )

    last_active_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    progress_entries: Mapped[list[UserProgress]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    user_badges: Mapped[list[UserBadge]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    milestones: Mapped[list["UserMilestone"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    quiz_attempts: Mapped[list[QuizAttempt]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    skill_levels: Mapped[list["UserSkillLevel"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    urn_exam_attempts: Mapped[list[UrnExamAttempt]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    certificates: Mapped[list["Certificate"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    quest_progress: Mapped[list["QuestProgress"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    classes: Mapped[list["Classroom"]] = relationship(
        back_populates="teacher",
        cascade="all, delete-orphan",
        foreign_keys="Classroom.teacher_id",
    )
    class_memberships: Mapped[list["ClassMember"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    created_live_sessions: Mapped[list["LiveSession"]] = relationship(
        back_populates="created_by",
        foreign_keys="LiveSession.created_by_id",
    )
    live_participations: Mapped[list["LiveParticipant"]] = relationship(
        back_populates="user",
        foreign_keys="LiveParticipant.user_id",
    )
    assignments: Mapped[list["QuestAssignment"]] = relationship(
        back_populates="assigned_by",
        foreign_keys="QuestAssignment.assigned_by_id",
    )
    assignment_progress: Mapped[list["AssignmentProgress"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    recommendations: Mapped[list["Recommendation"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    ai_jobs: Mapped[list["AIJob"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    embedding_jobs: Mapped[list["EmbeddingJob"]] = relationship(
        back_populates="created_by",
        cascade="all, delete-orphan",
    )
    content_flags: Mapped[list["ContentFlag"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    lesson_caches: Mapped[list["LessonCache"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    hearts: Mapped[Optional["UserHearts"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
    )
    starting_urn: Mapped[Optional["Urn"]] = relationship(
        "Urn",
        foreign_keys=[starting_urn_id],
    )
    abuse_reports_filed: Mapped[list["AbuseReport"]] = relationship(
        back_populates="reporter",
        foreign_keys="AbuseReport.reporter_id",
        cascade="all, delete-orphan",
    )
    abuse_reports_received: Mapped[list["AbuseReport"]] = relationship(
        back_populates="reported_user",
        foreign_keys="AbuseReport.reported_user_id",
    )
    abuse_reports_assigned: Mapped[list["AbuseReport"]] = relationship(
        back_populates="assigned_to",
        foreign_keys="AbuseReport.assigned_to_id",
    )
    notification_settings: Mapped[Optional["UserNotificationSettings"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
    )
    ai_conversations: Mapped[list["AIConversation"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    # Social relationships
    following: Mapped[list["UserFollow"]] = relationship(
        back_populates="follower",
        foreign_keys="UserFollow.follower_id",
        cascade="all, delete-orphan",
    )
    followers: Mapped[list["UserFollow"]] = relationship(
        back_populates="following",
        foreign_keys="UserFollow.following_id",
        cascade="all, delete-orphan",
    )
    sent_friend_requests: Mapped[list["FriendRequest"]] = relationship(
        back_populates="from_user",
        foreign_keys="FriendRequest.from_user_id",
        cascade="all, delete-orphan",
    )
    received_friend_requests: Mapped[list["FriendRequest"]] = relationship(
        back_populates="to_user",
        foreign_keys="FriendRequest.to_user_id",
        cascade="all, delete-orphan",
    )
    experiment_assignments: Mapped[list["UserExperimentAssignment"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    created_experiments: Mapped[list["Experiment"]] = relationship(
        back_populates="created_by",
        foreign_keys="Experiment.created_by_id",
        cascade="all, delete-orphan",
    )
    leaderboard_settings: Mapped[Optional["UserLeaderboardSettings"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
    )
    league_entries: Mapped[list["UserLeague"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class UserNotificationSettings(Base):
    """User notification settings and push token management."""
    __tablename__ = "user_notification_settings"
    __table_args__ = (
        Index("idx_notification_settings_user", "user_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    # Push notification settings
    push_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    push_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    push_platform: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True
    )  # ios, android, web

    # Email notification settings
    email_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )

    # Notification preferences
    streak_reminders: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )
    daily_mission_reminders: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )
    weekly_digest: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )
    marketing_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )

    # Quiet hours (0-23, hour in user's timezone)
    quiet_hours_start: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    quiet_hours_end: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    user: Mapped["User"] = relationship("User", back_populates="notification_settings")


class Urn(Base):
    __tablename__ = "urns"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    slug: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    name_han: Mapped[Optional[str]] = mapped_column(String(50))
    represents: Mapped[Optional[str]] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text)
    model_url: Mapped[str] = mapped_column(Text, nullable=False)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(Text)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False)
    is_demo: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    motifs: Mapped[list[Motif]] = relationship(
        back_populates="urn",
        cascade="all, delete-orphan",
    )
    exam_questions: Mapped[list[QuizQuestion]] = relationship(
        back_populates="urn",
        foreign_keys="QuizQuestion.urn_id",
    )
    urn_exams: Mapped[list[UrnExam]] = relationship(
        back_populates="urn",
        cascade="all, delete-orphan",
    )


class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"
    __table_args__ = (
        Index("idx_analytics_user", "user_id"),
        Index("idx_analytics_event_name", "event_name"),
        Index("idx_analytics_created_at", "created_at"),
        Index("idx_analytics_session", "session_id"),
        Index("idx_analytics_category", "event_category"),
        Index("idx_analytics_cohort", "cohort"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    event_name: Mapped[str] = mapped_column(String(100), nullable=False)
    path: Mapped[Optional[str]] = mapped_column(String(255))
    payload: Mapped[Optional[Any]] = mapped_column(JSONB)
    session_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True
    )
    cohort: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    event_category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    device_info: Mapped[Optional[Any]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    user: Mapped["User"] = relationship("User")


class Funnel(Base):
    __tablename__ = "funnels"
    __table_args__ = (
        Index("idx_funnels_user", "user_id"),
        Index("idx_funnels_type", "funnel_type"),
        Index("idx_funnels_stage", "stage"),
        Index("idx_funnels_started_at", "started_at"),
        Index("idx_funnels_completed_at", "completed_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    funnel_type: Mapped[str] = mapped_column(String(50), nullable=False)
    stage: Mapped[str] = mapped_column(String(50), nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    stage_timestamps: Mapped[Optional[Any]] = mapped_column(JSONB, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    metadata_json: Mapped[Optional[Any]] = mapped_column(
        "metadata", JSONB, nullable=True
    )

    user: Mapped["User"] = relationship("User")


class Motif(Base):
    __tablename__ = "motifs"
    __table_args__ = (
        Index("idx_motifs_urn", "urn_id"),
        Index("idx_motifs_mesh", "mesh_name"),
        Index("idx_motifs_category", "category"),
        Index("idx_motifs_rarity", "rarity"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    urn_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("urns.id", ondelete="CASCADE"),
        nullable=False,
    )

    mesh_name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    name_en: Mapped[Optional[str]] = mapped_column(String(255))
    category: Mapped[MotifCategory] = mapped_column(
        SAEnum(MotifCategory, name="motif_category", native_enum=True),
        nullable=False,
    )
    rarity: Mapped[MotifRarity] = mapped_column(
        SAEnum(MotifRarity, name="motif_rarity", native_enum=True),
        nullable=False,
        server_default=text("'common'"),
    )
    content_rating: Mapped[ContentRating] = mapped_column(
        SAEnum(ContentRating, name="content_rating", native_enum=True),
        nullable=False,
        server_default=text("'everyone'"),
    )

    pos_x: Mapped[float] = mapped_column(Float, nullable=False)
    pos_y: Mapped[float] = mapped_column(Float, nullable=False)
    pos_z: Mapped[float] = mapped_column(Float, nullable=False)
    bounding_radius: Mapped[float] = mapped_column(Float, nullable=False)

    cam_pos_x: Mapped[Optional[float]] = mapped_column(Float)
    cam_pos_y: Mapped[Optional[float]] = mapped_column(Float)
    cam_pos_z: Mapped[Optional[float]] = mapped_column(Float)
    cam_look_at_x: Mapped[Optional[float]] = mapped_column(Float)
    cam_look_at_y: Mapped[Optional[float]] = mapped_column(Float)
    cam_look_at_z: Mapped[Optional[float]] = mapped_column(Float)

    thumbnail_url: Mapped[Optional[str]] = mapped_column(Text)
    silhouette_url: Mapped[Optional[str]] = mapped_column(Text)

    is_demo: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )

    display_order: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    urn: Mapped[Urn] = relationship(back_populates="motifs")
    lesson: Mapped[Optional[LessonContent]] = relationship(
        back_populates="motif",
        cascade="all, delete-orphan",
        uselist=False,
    )
    progress_entries: Mapped[list[UserProgress]] = relationship(
        back_populates="motif",
        cascade="all, delete-orphan",
    )
    quiz_questions: Mapped[list[QuizQuestion]] = relationship(
        back_populates="motif",
        cascade="all, delete-orphan",
    )
    quiz_attempts: Mapped[list[QuizAttempt]] = relationship(
        back_populates="motif",
        cascade="all, delete-orphan",
    )


class LessonContent(Base):
    __tablename__ = "lesson_content"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    motif_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("motifs.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    intro_text: Mapped[Optional[str]] = mapped_column(Text)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    historical_context: Mapped[Optional[str]] = mapped_column(Text)
    symbolism: Mapped[Optional[str]] = mapped_column(Text)
    fun_fact: Mapped[Optional[str]] = mapped_column(Text)

    audio_narration_url: Mapped[Optional[str]] = mapped_column(Text)
    additional_images: Mapped[Optional[Any]] = mapped_column(JSONB)
    video_url: Mapped[Optional[str]] = mapped_column(Text)

    is_published: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )
    is_ai_generated: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    preview_eligible: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )  # True if this lesson can be shown to guest users as a preview
    content_validation_status: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default=text("'valid'")
    )  # History-First MIG-005: 'valid' | 'blocked_for_authoritative_learning'
    content_rating: Mapped[ContentRating] = mapped_column(
        SAEnum(ContentRating, name="content_rating", native_enum=True),
        nullable=False,
        server_default=text("'everyone'"),
    )

    # Learning sequence fields
    difficulty_level: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # 1-5, for ordering lessons by difficulty
    estimated_time_minutes: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # Estimated time to complete the lesson

    # Versioning metadata
    version: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("1")
    )
    last_editor_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    published_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    publish_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Review workflow fields
    status: Mapped[ContentStatus] = mapped_column(
        SAEnum(ContentStatus, name="content_status", native_enum=True),
        nullable=False,
        server_default=text("'draft'"),
    )
    submitted_for_review_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    reviewed_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    review_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    motif: Mapped[Motif] = relationship(back_populates="lesson")
    last_editor: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[last_editor_id]
    )
    reviewed_by: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[reviewed_by_id]
    )


class ContentVersion(Base):
    __tablename__ = "content_versions"
    __table_args__ = (
        Index("idx_content_versions_type", "content_type"),
        Index("idx_content_versions_content", "content_id"),
        Index("idx_content_versions_created", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    content_type: Mapped[str] = mapped_column(String(50), nullable=False)
    content_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    data: Mapped[Any] = mapped_column(JSONB, nullable=False)
    editor_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    change_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    editor: Mapped[Optional["User"]] = relationship("User")


class LessonPrerequisite(Base):
    """
    Represents prerequisite relationships between lessons.
    A lesson can have multiple prerequisites that must be completed before it's unlocked.
    """
    __tablename__ = "lesson_prerequisites"
    __table_args__ = (
        UniqueConstraint(
            "lesson_id", "prerequisite_lesson_id",
            name="uq_lesson_prereq_lesson_prereq"
        ),
        Index("idx_lesson_prereq_lesson", "lesson_id"),
        Index("idx_lesson_prereq_prerequisite", "prerequisite_lesson_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    lesson_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("lesson_content.id", ondelete="CASCADE"),
        nullable=False,
    )
    prerequisite_lesson_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("lesson_content.id", ondelete="CASCADE"),
        nullable=False,
    )
    is_strict: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )  # True = must complete, False = recommended only

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    lesson: Mapped["LessonContent"] = relationship(
        "LessonContent",
        foreign_keys=[lesson_id],
        backref="prerequisites"
    )
    prerequisite_lesson: Mapped["LessonContent"] = relationship(
        "LessonContent",
        foreign_keys=[prerequisite_lesson_id],
        backref="unlocks"
    )


class UserProgress(Base):
    __tablename__ = "user_progress"
    __table_args__ = (
        UniqueConstraint("user_id", "motif_id", name="uq_user_progress_user_motif"),
        Index("idx_progress_user", "user_id"),
        Index("idx_progress_motif", "motif_id"),
        Index("idx_progress_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    motif_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("motifs.id", ondelete="CASCADE"),
        nullable=False,
    )

    ease_factor: Mapped[float] = mapped_column(
        Float, nullable=False, server_default=text("2.5")
    )
    interval_days: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    repetitions: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    next_review_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    last_reviewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    review_history: Mapped[list[Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    user: Mapped["User"] = relationship("User")
    motif: Mapped["Motif"] = relationship("Motif")

    status: Mapped[UnlockStatus] = mapped_column(
        SAEnum(UnlockStatus, name="unlock_status", native_enum=True),
        nullable=False,
        server_default=text("'hidden'"),
    )

    discovered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    lesson_viewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )
    learned_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    mastered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    quiz_attempts: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    quiz_best_score: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )

    xp_earned: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    user: Mapped[User] = relationship(back_populates="progress_entries")
    motif: Mapped[Motif] = relationship(back_populates="progress_entries")


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"
    __table_args__ = (Index("idx_quiz_q_motif", "motif_id"),)

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    motif_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("motifs.id", ondelete="CASCADE"),
        nullable=False,
    )
    urn_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("urns.id", ondelete="CASCADE"),
        nullable=True,
    )

    question_type: Mapped[QuestionType] = mapped_column(
        SAEnum(QuestionType, name="question_type", native_enum=True),
        nullable=False,
    )
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    options: Mapped[Optional[Any]] = mapped_column(JSONB)
    correct_answer: Mapped[str] = mapped_column(String(255), nullable=False)
    target_mesh_name: Mapped[Optional[str]] = mapped_column(String(100))

    difficulty: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("1")
    )
    skill_type: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # Maps to SkillType enum for adaptive learning
    explanation: Mapped[Optional[str]] = mapped_column(Text)

    is_published: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )
    content_validation_status: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default=text("'valid'")
    )  # History-First MIG-005: 'valid' | 'blocked_for_authoritative_learning'

    # Historical Learning Engine V2 columns (migration 0050, Spec 32.1):
    # skill_dimensions      — list of mastery skill tags this question trains
    # entity_id             — canonical historical entity the question targets
    # claim_ids             — claim UUIDs the question's answer depends on
    # source_ids            — source UUIDs surfaced to the learner
    # answer_contract       — typed answer rubric per question type (Spec 33)
    skill_dimensions: Mapped[Optional[list[Any]]] = mapped_column(
        JSONB, nullable=True
    )
    entity_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("historical_entities.id", ondelete="SET NULL"),
        nullable=True,
    )
    claim_ids: Mapped[Optional[list[Any]]] = mapped_column(JSONB, nullable=True)
    source_ids: Mapped[Optional[list[Any]]] = mapped_column(JSONB, nullable=True)
    answer_contract: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Review workflow fields
    status: Mapped[ContentStatus] = mapped_column(
        SAEnum(ContentStatus, name="content_status", native_enum=True),
        nullable=False,
        server_default=text("'draft'"),
    )
    submitted_for_review_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    reviewed_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    review_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    motif: Mapped[Motif] = relationship(back_populates="quiz_questions")
    urn: Mapped[Optional[Urn]] = relationship(
        back_populates="exam_questions", foreign_keys=[urn_id]
    )
    reviewed_by: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[reviewed_by_id]
    )
    created_by: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[created_by_id]
    )


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"
    __table_args__ = (
        Index("idx_quiz_attempts_user", "user_id"),
        Index("idx_quiz_attempts_motif", "motif_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    motif_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("motifs.id", ondelete="CASCADE"),
        nullable=False,
    )

    score: Mapped[int] = mapped_column(Integer, nullable=False)
    max_score: Mapped[int] = mapped_column(Integer, nullable=False)
    percentage: Mapped[int] = mapped_column(Integer, nullable=False)

    answers: Mapped[Any] = mapped_column(JSONB, nullable=False)
    time_taken_seconds: Mapped[Optional[int]] = mapped_column(Integer)

    completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    user: Mapped[User] = relationship(back_populates="quiz_attempts")
    motif: Mapped[Motif] = relationship(back_populates="quiz_attempts")


class QuizHintRequest(Base):
    """Stores quiz hint requests with AI-generated hints and RAG sources."""
    __tablename__ = "quiz_hint_requests"
    __table_args__ = (
        Index("idx_quiz_hints_user", "user_id"),
        Index("idx_quiz_hints_question", "question_id"),
        Index("idx_quiz_hints_created", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("quiz_questions.id", ondelete="CASCADE"),
        nullable=False,
    )

    hint_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # explain, clue, elimination
    hint_text: Mapped[str] = mapped_column(Text, nullable=False)
    heart_cost: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )

    # RAG sources used to generate the hint
    rag_sources: Mapped[Optional[Any]] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    question: Mapped["QuizQuestion"] = relationship("QuizQuestion", foreign_keys=[question_id])


class UserSkillLevel(Base):
    """Tracks user's skill level across different skill types for adaptive learning."""
    __tablename__ = "user_skill_levels"
    __table_args__ = (
        UniqueConstraint("user_id", "skill_type", name="uq_user_skill"),
        Index("idx_user_skill_user", "user_id"),
        Index("idx_user_skill_type", "skill_type"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    skill_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )
    skill_level: Mapped[float] = mapped_column(
        Float, nullable=False, server_default=text("0.5")
    )  # 0.0 to 1.0, starts at 0.5
    total_questions: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    correct_answers: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    # Historical Learning Engine V2 (migration 0050): per-dimension weighted
    # breakdown for the mastery dimensions. Holds e.g.
    # {"dimension": "chronology", "attempts": 5, "correct": 4, "last_score": 0.8}.
    skill_dimensions: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    last_updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    user: Mapped[User] = relationship(back_populates="skill_levels")


class UrnExam(Base):
    __tablename__ = "urn_exams"
    __table_args__ = (Index("idx_urn_exams_urn", "urn_id"),)

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    urn_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("urns.id", ondelete="CASCADE"),
        nullable=False,
    )

    questions: Mapped[Any] = mapped_column(JSONB, nullable=False)
    passing_score: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("80")
    )
    xp_reward: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("100")
    )

    urn: Mapped[Urn] = relationship(back_populates="urn_exams")
    attempts: Mapped[list[UrnExamAttempt]] = relationship(
        back_populates="urn_exam",
        cascade="all, delete-orphan",
    )


class UrnExamAttempt(Base):
    __tablename__ = "urn_exam_attempts"
    __table_args__ = (
        Index("idx_urn_exam_attempts_user", "user_id"),
        Index("idx_urn_exam_attempts_exam", "urn_exam_id"),
        Index("idx_urn_exam_attempts_passed", "passed"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    urn_exam_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("urn_exams.id", ondelete="CASCADE"),
        nullable=False,
    )

    score: Mapped[int] = mapped_column(Integer, nullable=False)
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    time_taken: Mapped[Optional[int]] = mapped_column(Integer)
    answers: Mapped[Any] = mapped_column(JSONB, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    user: Mapped[User] = relationship(back_populates="urn_exam_attempts")
    urn_exam: Mapped[UrnExam] = relationship(back_populates="attempts")


class Badge(Base):
    __tablename__ = "badges"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    name_en: Mapped[Optional[str]] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text)
    icon_url: Mapped[str] = mapped_column(Text, nullable=False)

    category: Mapped[BadgeCategory] = mapped_column(
        SAEnum(BadgeCategory, name="badge_category", native_enum=True),
        nullable=False,
    )
    tier: Mapped[BadgeTier] = mapped_column(
        SAEnum(BadgeTier, name="badge_tier", native_enum=True),
        nullable=False,
        server_default=text("'bronze'"),
    )
    xp_bonus: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    tier_xp_bonus: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    unlock_criteria: Mapped[Any] = mapped_column(JSONB, nullable=False)

    is_secret: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    user_badges: Mapped[list[UserBadge]] = relationship(
        back_populates="badge",
        cascade="all, delete-orphan",
    )


class UserBadge(Base):
    __tablename__ = "user_badges"
    __table_args__ = (
        UniqueConstraint("user_id", "badge_id", name="uq_user_badges_user_badge"),
        Index("idx_user_badges_user", "user_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    badge_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("badges.id", ondelete="CASCADE"),
        nullable=False,
    )
    current_tier: Mapped[BadgeTier] = mapped_column(
        SAEnum(BadgeTier, name="badge_tier", native_enum=True),
        nullable=False,
        server_default=text("'bronze'"),
    )
    earned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    user: Mapped[User] = relationship(back_populates="user_badges")
    badge: Mapped[Badge] = relationship(back_populates="user_badges")


class UserMilestone(Base):
    __tablename__ = "user_milestones"
    __table_args__ = (
        UniqueConstraint("user_id", "milestone_type", name="uq_user_milestones_user_type"),
        Index("idx_user_milestones_user", "user_id"),
        Index("idx_user_milestones_type", "milestone_type"),
        Index("idx_user_milestones_celebrated", "celebrated"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    milestone_type: Mapped[MilestoneType] = mapped_column(
        SAEnum(MilestoneType, name="milestone_type", native_enum=True),
        nullable=False,
    )
    achieved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    context_data: Mapped[Optional[Any]] = mapped_column(JSONB, nullable=True)
    celebrated: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="milestones")


class Certificate(Base):
    __tablename__ = "certificates"
    __table_args__ = (
        UniqueConstraint("code", name="uq_certificates_code"),
        UniqueConstraint(
            "user_id", "reason_type", "reason_id", name="uq_certificates_reason"
        ),
        Index("idx_certificates_user", "user_id"),
        Index("idx_certificates_reason", "reason_type", "reason_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    issuer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    reason_type: Mapped[str] = mapped_column(String(50), nullable=False)
    reason_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'issued'")
    )
    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="certificates")


class Quest(Base):
    __tablename__ = "quests"
    __table_args__ = (
        Index("idx_quests_slug", "slug"),
        Index("idx_quests_active", "is_active"),
        Index("idx_quests_order", "display_order"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    category: Mapped[Optional[str]] = mapped_column(String(50))
    display_order: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )
    content_rating: Mapped[ContentRating] = mapped_column(
        SAEnum(ContentRating, name="content_rating", native_enum=True),
        nullable=False,
        server_default=text("'everyone'"),
    )
    prerequisite_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("quests.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    steps: Mapped[list["QuestStep"]] = relationship(
        back_populates="quest",
        cascade="all, delete-orphan",
    )
    rewards: Mapped[list["QuestReward"]] = relationship(
        back_populates="quest",
        cascade="all, delete-orphan",
    )
    progress_entries: Mapped[list["QuestProgress"]] = relationship(
        back_populates="quest",
        cascade="all, delete-orphan",
    )
    prerequisite: Mapped[Optional["Quest"]] = relationship("Quest", remote_side=[id])


class QuestStep(Base):
    __tablename__ = "quest_steps"
    __table_args__ = (
        Index("idx_quest_steps_quest", "quest_id"),
        Index("idx_quest_steps_order", "display_order"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    quest_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("quests.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    display_order: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    quest: Mapped[Quest] = relationship(back_populates="steps")
    objectives: Mapped[list["QuestObjective"]] = relationship(
        back_populates="step",
        cascade="all, delete-orphan",
    )


class QuestObjective(Base):
    __tablename__ = "quest_objectives"
    __table_args__ = (
        Index("idx_quest_objectives_step", "quest_step_id"),
        Index("idx_quest_objectives_type", "objective_type"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    quest_step_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("quest_steps.id", ondelete="CASCADE"),
        nullable=False,
    )
    objective_type: Mapped[str] = mapped_column(String(50), nullable=False)
    target_value: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("1")
    )
    params: Mapped[Optional[Any]] = mapped_column(JSONB)
    display_order: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )

    step: Mapped["QuestStep"] = relationship(back_populates="objectives")


class QuestReward(Base):
    __tablename__ = "quest_rewards"
    __table_args__ = (
        Index("idx_quest_rewards_quest", "quest_id"),
        Index("idx_quest_rewards_type", "reward_type"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    quest_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("quests.id", ondelete="CASCADE"),
        nullable=False,
    )
    reward_type: Mapped[str] = mapped_column(String(50), nullable=False)
    amount: Mapped[Optional[int]] = mapped_column(Integer)
    badge_slug: Mapped[Optional[str]] = mapped_column(String(100))
    metadata_payload: Mapped[Optional[Any]] = mapped_column("metadata", JSONB)

    quest: Mapped["Quest"] = relationship(back_populates="rewards")


class QuestProgress(Base):
    __tablename__ = "quest_progress"
    __table_args__ = (
        UniqueConstraint("user_id", "quest_id", name="uq_quest_progress_user"),
        Index("idx_quest_progress_user", "user_id"),
        Index("idx_quest_progress_quest", "quest_id"),
        Index("idx_quest_progress_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    quest_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("quests.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'in_progress'")
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    user: Mapped["User"] = relationship(back_populates="quest_progress")
    quest: Mapped["Quest"] = relationship(back_populates="progress_entries")


class Classroom(Base):
    __tablename__ = "classes"
    __table_args__ = (
        Index("idx_classes_teacher", "teacher_id"),
        Index("idx_classes_created_at", "created_at"),
        Index("idx_classes_class_code", "class_code"),
        UniqueConstraint("class_code", name="uq_classes_class_code"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    teacher_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    class_code: Mapped[str] = mapped_column(
        String(8), nullable=False, unique=True, index=True
    )
    max_students: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_archived: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    settings: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    teacher: Mapped["User"] = relationship(
        back_populates="classes", foreign_keys=[teacher_id]
    )
    members: Mapped[list["ClassMember"]] = relationship(
        back_populates="classroom",
        cascade="all, delete-orphan",
    )
    live_sessions: Mapped[list["LiveSession"]] = relationship(
        back_populates="classroom",
        cascade="all, delete-orphan",
    )
    assignments: Mapped[list["QuestAssignment"]] = relationship(
        back_populates="classroom",
        cascade="all, delete-orphan",
    )


class ClassMember(Base):
    __tablename__ = "class_members"
    __table_args__ = (
        UniqueConstraint("class_id", "user_id", name="uq_class_members"),
        Index("idx_class_members_class", "class_id"),
        Index("idx_class_members_user", "user_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    class_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("classes.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'learner'")
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    classroom: Mapped["Classroom"] = relationship(back_populates="members")
    user: Mapped["User"] = relationship(back_populates="class_memberships")


class LiveSession(Base):
    __tablename__ = "live_sessions"
    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uq_live_sessions_idempotency_key"),
        Index("idx_live_sessions_classroom", "classroom_id"),
        Index("idx_live_sessions_status", "status"),
        Index("idx_live_sessions_starts_at", "starts_at"),
        Index("idx_live_sessions_created_at", "created_at"),
        Index("idx_live_sessions_room_name", "room_name"),
        Index("idx_live_sessions_idempotency_key", "idempotency_key"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    classroom_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("classes.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    room_name: Mapped[str] = mapped_column(String(191), nullable=False, unique=True)
    idempotency_key: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default=text(f"'{LiveSessionStatus.scheduled.value}'"),
    )
    starts_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    session_metadata: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    classroom: Mapped["Classroom"] = relationship(back_populates="live_sessions")
    created_by: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="created_live_sessions",
        foreign_keys=[created_by_id],
    )
    participants: Mapped[list["LiveParticipant"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
    )
    events: Mapped[list["LiveEvent"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
    )


class LiveParticipant(Base):
    __tablename__ = "live_participants"
    __table_args__ = (
        UniqueConstraint(
            "live_session_id",
            "participant_identity",
            name="uq_live_participants_session_identity",
        ),
        UniqueConstraint(
            "live_session_id",
            "user_id",
            name="uq_live_participants_session_user",
        ),
        Index("idx_live_participants_session", "live_session_id"),
        Index("idx_live_participants_user", "user_id"),
        Index("idx_live_participants_joined_at", "joined_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    live_session_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("live_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    participant_identity: Mapped[str] = mapped_column(String(191), nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default=text(f"'{LiveParticipantRole.learner.value}'"),
    )
    is_ai: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    left_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    connection_metadata: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    session: Mapped["LiveSession"] = relationship(back_populates="participants")
    user: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="live_participations",
        foreign_keys=[user_id],
    )


class LiveEvent(Base):
    __tablename__ = "live_events"
    __table_args__ = (
        Index("idx_live_events_session", "live_session_id"),
        Index("idx_live_events_type", "event_type"),
        Index("idx_live_events_created_at", "created_at"),
        Index(
            "idx_live_events_session_created_at",
            "live_session_id",
            "created_at",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    live_session_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("live_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    event_type: Mapped[str] = mapped_column(String(80), nullable=False)
    event_source: Mapped[str] = mapped_column(
        String(40), nullable=False, server_default=text("'app'")
    )
    participant_identity: Mapped[Optional[str]] = mapped_column(String(191), nullable=True)
    participant_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    payload: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    session: Mapped["LiveSession"] = relationship(back_populates="events")


class SessionTranscript(Base):
    __tablename__ = "session_transcripts"
    __table_args__ = (
        UniqueConstraint(
            "live_session_id",
            "source_event_id",
            name="uq_session_transcripts_source_event",
        ),
        Index("idx_session_transcripts_session", "live_session_id"),
        Index("idx_session_transcripts_speaker", "speaker_type"),
        Index("idx_session_transcripts_created_at", "created_at"),
        Index(
            "idx_session_transcripts_session_created_at",
            "live_session_id",
            "created_at",
        ),
        Index("idx_session_transcripts_expires_at", "expires_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    live_session_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("live_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    source_event_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("live_events.id", ondelete="SET NULL"),
        nullable=True,
    )
    speaker_type: Mapped[str] = mapped_column(String(20), nullable=False)
    speaker_identity: Mapped[Optional[str]] = mapped_column(String(191), nullable=True)
    speaker_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    content_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    transcript_metadata: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    session: Mapped["LiveSession"] = relationship()
    source_event: Mapped[Optional["LiveEvent"]] = relationship()
    speaker_user: Mapped[Optional["User"]] = relationship()


class SessionSummary(Base):
    __tablename__ = "session_summaries"
    __table_args__ = (
        Index("idx_session_summaries_session", "live_session_id"),
        Index("idx_session_summaries_created_at", "created_at"),
        Index("idx_session_summaries_expires_at", "expires_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    live_session_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("live_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    summary_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    highlights: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    citations: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    rubric_overview: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    summary_metadata: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    created_by: Mapped[str] = mapped_column(
        String(40), nullable=False, server_default=text("'ai_teacher_pipeline'")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    session: Mapped["LiveSession"] = relationship()


class SessionAction(Base):
    __tablename__ = "session_actions"
    __table_args__ = (
        Index("idx_session_actions_session", "live_session_id"),
        Index("idx_session_actions_type", "action_type"),
        Index("idx_session_actions_created_at", "created_at"),
        Index("idx_session_actions_expires_at", "expires_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    live_session_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("live_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    action_type: Mapped[str] = mapped_column(String(40), nullable=False)
    actor_identity: Mapped[Optional[str]] = mapped_column(String(191), nullable=True)
    actor_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'open'")
    )
    cost_usd: Mapped[Optional[float]] = mapped_column(Numeric(12, 6), nullable=True)
    payload: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    session: Mapped["LiveSession"] = relationship()
    actor_user: Mapped[Optional["User"]] = relationship()


class LiveRateLimitLog(Base):
    __tablename__ = "live_rate_limit_logs"
    __table_args__ = (
        Index("idx_live_rate_limit_logs_bucket", "bucket"),
        Index("idx_live_rate_limit_logs_user", "user_id"),
        Index("idx_live_rate_limit_logs_session", "live_session_id"),
        Index("idx_live_rate_limit_logs_created_at", "created_at"),
        Index(
            "idx_live_rate_limit_logs_bucket_user_created_at",
            "bucket",
            "user_id",
            "created_at",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    bucket: Mapped[str] = mapped_column(String(64), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    live_session_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("live_sessions.id", ondelete="CASCADE"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    user: Mapped["User"] = relationship()
    session: Mapped[Optional["LiveSession"]] = relationship()


class QuestAssignment(Base):
    __tablename__ = "quest_assignments"
    __table_args__ = (
        Index("idx_assignments_class", "class_id"),
        Index("idx_assignments_quest", "quest_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    class_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("classes.id", ondelete="CASCADE"),
        nullable=False,
    )
    quest_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("quests.id", ondelete="CASCADE"),
        nullable=False,
    )
    assigned_by_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    due_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    points_override: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # Custom points for this assignment
    notes: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # Teacher notes for this assignment

    classroom: Mapped["Classroom"] = relationship(back_populates="assignments")
    quest: Mapped["Quest"] = relationship()
    assigned_by: Mapped["User"] = relationship(
        back_populates="assignments", foreign_keys=[assigned_by_id]
    )
    progress_entries: Mapped[list["AssignmentProgress"]] = relationship(
        back_populates="assignment",
        cascade="all, delete-orphan",
    )


class AssignmentProgress(Base):
    __tablename__ = "assignment_progress"
    __table_args__ = (
        UniqueConstraint("assignment_id", "user_id", name="uq_assignment_progress"),
        Index("idx_assignment_progress_assignment", "assignment_id"),
        Index("idx_assignment_progress_user", "user_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    assignment_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("quest_assignments.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'assigned'")
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    assignment: Mapped["QuestAssignment"] = relationship(
        back_populates="progress_entries"
    )
    user: Mapped["User"] = relationship(back_populates="assignment_progress")


class Recommendation(Base):
    __tablename__ = "recommendations"
    __table_args__ = (
        Index("idx_recommendations_user", "user_id"),
        Index("idx_recommendations_created", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    source: Mapped[str] = mapped_column(String(20), nullable=False)
    items: Mapped[Any] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="recommendations")


class AIJob(Base):
    __tablename__ = "ai_jobs"
    __table_args__ = (
        Index("idx_ai_jobs_user", "user_id"),
        Index("idx_ai_jobs_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    job_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'pending'")
    )
    provider: Mapped[Optional[str]] = mapped_column(String(50))
    prompt: Mapped[Optional[str]] = mapped_column(Text)
    response: Mapped[Optional[str]] = mapped_column(Text)
    error: Mapped[Optional[str]] = mapped_column(Text)
    retry_count: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    user: Mapped["User"] = relationship(back_populates="ai_jobs")


class RagDocument(Base):
    __tablename__ = "rag_documents"
    __table_args__ = (
        Index("idx_rag_documents_active", "is_active"),
        Index("idx_rag_documents_updated", "updated_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[str] = mapped_column(
        String(30), nullable=False, server_default=text("'manual'")
    )
    source_path: Mapped[Optional[str]] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )
    embedding: Mapped[Optional[Any]] = mapped_column(JSONB)
    embedding_model: Mapped[Optional[str]] = mapped_column(String(100))
    embedding_updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class RagSettings(Base):
    __tablename__ = "rag_settings"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    system_instruction: Mapped[Optional[str]] = mapped_column(Text)
    prompt_prefix: Mapped[Optional[str]] = mapped_column(Text)
    model_override: Mapped[Optional[str]] = mapped_column(String(100))
    temperature: Mapped[Optional[float]] = mapped_column(Float)
    max_documents: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("6")
    )
    embedding_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )
    hybrid_alpha: Mapped[float] = mapped_column(
        Float, nullable=False, server_default=text("0.6")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class EmbeddingJob(Base):
    __tablename__ = "embedding_jobs"
    __table_args__ = (
        Index("idx_embedding_jobs_status", "status"),
        Index("idx_embedding_jobs_created_by", "created_by_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'pending'")
    )
    total_documents: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    processed_documents: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    created_by: Mapped["User"] = relationship(back_populates="embedding_jobs")


class ContentProvenance(Base):
    __tablename__ = "content_provenance"
    __table_args__ = (
        Index("idx_content_provenance_type", "content_type"),
        Index("idx_content_provenance_content", "content_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    content_type: Mapped[str] = mapped_column(String(50), nullable=False)
    content_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    provider: Mapped[Optional[str]] = mapped_column(String(50))
    model: Mapped[Optional[str]] = mapped_column(String(100))
    generated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    metadata_payload: Mapped[Optional[Any]] = mapped_column("metadata", JSONB)


class ContentFlag(Base):
    __tablename__ = "content_flags"
    __table_args__ = (
        Index("idx_content_flags_user", "user_id"),
        Index("idx_content_flags_type", "content_type"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    content_type: Mapped[str] = mapped_column(String(50), nullable=False)
    content_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="content_flags")


class MissionType(str, Enum):
    lesson = "lesson"
    quiz = "quiz"
    discovery = "discovery"
    streak = "streak"


class QuestCategory(str, Enum):
    exploration = "exploration"
    mastery = "mastery"
    quiz_champion = "quiz_champion"
    streak_master = "streak_master"


class DailyMission(Base):
    __tablename__ = "daily_missions"
    __table_args__ = (
        Index("idx_daily_missions_slug", "slug"),
        Index("idx_daily_missions_type", "mission_type"),
        Index("idx_daily_missions_active", "is_active"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    mission_type: Mapped[MissionType] = mapped_column(
        SAEnum(MissionType, name="mission_type", native_enum=True),
        nullable=False,
    )
    target_count: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("1")
    )
    xp_reward: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("50")
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    user_missions: Mapped[list["UserDailyMission"]] = relationship(
        back_populates="mission",
        cascade="all, delete-orphan",
    )


class UserDailyMission(Base):
    __tablename__ = "user_daily_missions"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "mission_id", "mission_date", name="uq_user_daily_mission"
        ),
        Index("idx_user_daily_missions_user", "user_id"),
        Index("idx_user_daily_missions_mission", "mission_id"),
        Index("idx_user_daily_missions_date", "mission_date"),
        Index("idx_user_daily_missions_completed", "is_completed"),
        Index("idx_user_daily_missions_user_date", "user_id", "mission_date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    mission_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("daily_missions.id", ondelete="CASCADE"),
        nullable=False,
    )
    mission_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), nullable=False
    )
    current_count: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    is_completed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    xp_awarded: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    user: Mapped["User"] = relationship("User")
    mission: Mapped["DailyMission"] = relationship(back_populates="user_missions")


class Tag(Base):
    __tablename__ = "tags"
    __table_args__ = (
        Index("idx_tags_slug", "slug"),
        Index("idx_tags_type", "tag_type"),
        Index("idx_tags_active", "is_active"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    tag_type: Mapped[str] = mapped_column(
        SAEnum(TagType, native_enum=False, length=50), nullable=False
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    content_tags: Mapped[list["ContentTag"]] = relationship(
        back_populates="tag", cascade="all, delete-orphan"
    )


class ContentTag(Base):
    __tablename__ = "content_tags"
    __table_args__ = (
        UniqueConstraint(
            "tag_id", "content_type", "content_id", name="uq_content_tag"
        ),
        Index("idx_content_tags_tag", "tag_id"),
        Index("idx_content_tags_content_type", "content_type"),
        Index("idx_content_tags_content", "content_type", "content_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tag_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tags.id", ondelete="CASCADE"),
        nullable=False,
    )
    content_type: Mapped[str] = mapped_column(
        SAEnum(ContentType, native_enum=False, length=50), nullable=False
    )
    content_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    tag: Mapped["Tag"] = relationship(back_populates="content_tags")


class StreakReward(Base):
    __tablename__ = "streak_rewards"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "streak_day", name="uq_streak_rewards_user_streak_day"
        ),
        Index("idx_streak_rewards_user", "user_id"),
        Index("idx_streak_rewards_streak_day", "streak_day"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    streak_day: Mapped[int] = mapped_column(Integer, nullable=False)
    reward_type: Mapped[str] = mapped_column(String(50), nullable=False)
    reward_amount: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    awarded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    user: Mapped["User"] = relationship("User")


# =============================================================================
# Weekly Quest Models
# =============================================================================


class WeeklyQuest(Base):
    """Weekly quest template - can be time-specific or recurring."""

    __tablename__ = "weekly_quests"
    __table_args__ = (
        Index("idx_weekly_quests_slug", "slug"),
        Index("idx_weekly_quests_category", "category"),
        Index("idx_weekly_quests_week_year", "week_number", "year"),
        Index("idx_weekly_quests_active", "is_active"),
        Index("idx_weekly_quests_recurring", "is_recurring"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[QuestCategory] = mapped_column(
        SAEnum(QuestCategory, name="quest_category", native_enum=True),
        nullable=False,
    )
    week_number: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # 1-52, null for recurring
    year: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # null for recurring
    target_count: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("1")
    )
    xp_reward: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("100")
    )
    badge_slug: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )  # badge to award on completion
    is_recurring: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )  # auto-assign every week
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    user_quests: Mapped[list["UserWeeklyQuest"]] = relationship(
        back_populates="quest", cascade="all, delete-orphan"
    )


class UserWeeklyQuest(Base):
    """User's progress on a weekly quest."""

    __tablename__ = "user_weekly_quests"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "quest_id", "week_start_date", name="uq_user_weekly_quest"
        ),
        Index("idx_user_weekly_quests_user", "user_id"),
        Index("idx_user_weekly_quests_quest", "quest_id"),
        Index("idx_user_weekly_quests_week", "week_start_date"),
        Index("idx_user_weekly_quests_completed", "is_completed"),
        Index("idx_user_weekly_quests_user_week", "user_id", "week_start_date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    quest_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("weekly_quests.id", ondelete="CASCADE"),
        nullable=False,
    )
    week_start_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), nullable=False
    )  # Monday of the week
    current_count: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    is_completed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    xp_awarded: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    user: Mapped["User"] = relationship("User")
    quest: Mapped["WeeklyQuest"] = relationship(back_populates="user_quests")


class LessonCache(Base):
    """Tracks lessons cached offline by users for the mobile app."""

    __tablename__ = "lesson_cache"
    __table_args__ = (
        UniqueConstraint("user_id", "lesson_id", name="uq_lesson_cache_user_lesson"),
        Index("idx_lesson_cache_user", "user_id"),
        Index("idx_lesson_cache_lesson", "lesson_id"),
        Index("idx_lesson_cache_cached_at", "cached_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    lesson_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("lesson_content.id", ondelete="CASCADE"),
        nullable=False,
    )
    cached_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    cache_version: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("1")
    )
    file_size_bytes: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    is_valid: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    user: Mapped["User"] = relationship("User")
    lesson: Mapped["LessonContent"] = relationship("LessonContent")


class AuditLog(Base):
    """Admin audit log for tracking all system changes and sensitive operations."""

    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("idx_audit_logs_user", "user_id"),
        Index("idx_audit_logs_action", "action"),
        Index("idx_audit_logs_resource_type", "resource_type"),
        Index("idx_audit_logs_created_at", "created_at"),
        Index("idx_audit_logs_resource", "resource_type", "resource_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    action: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # create, update, delete, view, ai_request, login, logout, role_change
    resource_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # lesson, quiz, rag_document, user, settings, auth, ai_generation
    resource_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True
    )
    old_value: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSONB, nullable=True
    )  # Previous state for updates/deletes
    new_value: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSONB, nullable=True
    )  # New state for creates/updates
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    user: Mapped[Optional["User"]] = relationship("User")


class UserSession(Base):
    """User session tracking for real-time analytics."""
    __tablename__ = "user_sessions"
    __table_args__ = (
        Index("idx_user_sessions_user_id", "user_id"),
        Index("idx_user_sessions_session_id", "session_id"),
        Index("idx_user_sessions_is_active", "is_active"),
        Index("idx_user_sessions_last_active", "last_active_at"),
        Index("idx_user_sessions_started_at", "started_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,  # Nullable for anonymous sessions
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), nullable=False, unique=True
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    last_active_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    ended_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    device_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # mobile, web, tablet
    platform: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # ios, android, web
    app_version: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )

    user: Mapped[Optional["User"]] = relationship("User")


class PasswordResetToken(Base):
    """Password reset tokens for account recovery."""
    __tablename__ = "password_reset_tokens"
    __table_args__ = (
        Index("idx_password_reset_tokens_user", "user_id"),
        Index("idx_password_reset_tokens_token", "token_hash"),
        Index("idx_password_reset_tokens_expires", "expires_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    user_agent: Mapped[Optional[str]] = mapped_column(Text)

    user: Mapped["User"] = relationship("User")


class AbuseReport(Base):
    """Abuse reports for user-generated content moderation."""
    __tablename__ = "abuse_reports"
    __table_args__ = (
        Index("idx_abuse_reports_reporter", "reporter_id"),
        Index("idx_abuse_reports_reported_user", "reported_user_id"),
        Index("idx_abuse_reports_status", "status"),
        Index("idx_abuse_reports_priority", "priority"),
        Index("idx_abuse_reports_content_type", "content_type"),
        Index("idx_abuse_reports_assigned_to", "assigned_to_id"),
        Index("idx_abuse_reports_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    reporter_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    reported_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    content_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # comment, review, profile, message, other
    content_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True
    )
    reason: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # harassment, spam, inappropriate, copyright, other
    description: Mapped[str] = mapped_column(
        Text, nullable=False
    )  # User's description of the issue
    evidence_urls: Mapped[Optional[list[str]]] = mapped_column(
        JSONB, nullable=True
    )  # List of screenshot URLs
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'pending'")
    )  # pending, reviewing, resolved, dismissed
    priority: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'low'")
    )  # low, medium, high, critical
    assigned_to_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    reporter: Mapped["User"] = relationship(
        "User", foreign_keys=[reporter_id], back_populates="abuse_reports_filed"
    )
    reported_user: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[reported_user_id], back_populates="abuse_reports_received"
    )
    assigned_to: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[assigned_to_id], back_populates="abuse_reports_assigned"
    )


class CrashReport(Base):
    """Crash/error reporting for mobile and web clients."""

    __tablename__ = "crash_reports"
    __table_args__ = (
        Index("idx_crash_reports_user_id", "user_id"),
        Index("idx_crash_reports_session_id", "session_id"),
        Index("idx_crash_reports_error_type", "error_type"),
        Index("idx_crash_reports_platform", "platform"),
        Index("idx_crash_reports_created_at", "created_at"),
        Index("idx_crash_reports_is_resolved", "is_resolved"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,  # Nullable for anonymous users
    )
    session_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True
    )
    error_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # crash, error, exception, anr
    error_message: Mapped[str] = mapped_column(Text, nullable=False)
    stack_trace: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    platform: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # ios, android, web
    app_version: Mapped[str] = mapped_column(String(20), nullable=False)
    device_model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    os_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    additional_data: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSONB, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    is_resolved: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    resolved_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[user_id])
    resolved_by: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[resolved_by_id]
    )


class AppVersion(Base):
    """Mobile app version tracking and forced update management."""
    __tablename__ = "app_versions"
    __table_args__ = (
        Index("idx_app_versions_platform", "platform"),
        Index("idx_app_versions_is_current", "is_current"),
        Index("idx_app_versions_released_at", "released_at"),
        UniqueConstraint("platform", "version", name="uq_app_version_platform_version"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    platform: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # ios, android
    version: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # e.g., "1.2.3"
    version_code: Mapped[int] = mapped_column(
        Integer, nullable=False
    )  # Build number
    min_required_version: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # Minimum supported version
    is_current: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )  # Latest version flag
    force_update: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )  # If true, users must update
    release_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    download_url: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True
    )  # App store link
    released_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


# =============================================================================
# Hearts System Models
# =============================================================================


class HeartTransactionReason(str, Enum):
    """Reasons for heart transactions."""
    quiz_wrong = "quiz_wrong"
    quiz_hint = "quiz_hint"
    heart_purchase = "heart_purchase"
    daily_refill = "daily_refill"
    streak_freeze_used = "streak_freeze_used"
    reward = "reward"
    admin_grant = "admin_grant"
    ad_watch = "ad_watch"
    practice_complete = "practice_complete"


class UserHearts(Base):
    """User hearts/energy system for gamification."""
    __tablename__ = "user_hearts"
    __table_args__ = (
        Index("idx_user_hearts_user", "user_id"),
        Index("idx_user_hearts_refill", "hearts_refill_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    current_hearts: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("5")
    )
    max_hearts: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("5")
    )
    last_heart_lost_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    hearts_refill_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    unlimited_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    streak_freezes: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="hearts")
    transactions: Mapped[list["HeartTransaction"]] = relationship(
        back_populates="user_hearts",
        cascade="all, delete-orphan",
        order_by="HeartTransaction.created_at.desc()",
    )


class HeartTransaction(Base):
    """Transaction log for heart changes."""
    __tablename__ = "heart_transactions"
    __table_args__ = (
        Index("idx_heart_transactions_user", "user_id"),
        Index("idx_heart_transactions_reason", "reason"),
        Index("idx_heart_transactions_created", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_hearts_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("user_hearts.id", ondelete="CASCADE"),
        nullable=False,
    )
    amount: Mapped[int] = mapped_column(
        Integer, nullable=False
    )  # Positive for gain, negative for loss
    reason: Mapped[HeartTransactionReason] = mapped_column(
        SAEnum(HeartTransactionReason, name="heart_transaction_reason", native_enum=True),
        nullable=False,
    )
    balance_after: Mapped[int] = mapped_column(
        Integer, nullable=False
    )
    metadata_json: Mapped[Optional[Any]] = mapped_column(
        "metadata", JSONB, nullable=True
    )  # Additional context (e.g., quiz_id, question_id)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User")
    user_hearts: Mapped["UserHearts"] = relationship("UserHearts", back_populates="transactions")


class GuestPreview(Base):
    """Track guest users' preview lesson sessions before signup.

    This table enables:
    - Letting guests experience a demo lesson without authentication
    - Tracking preview engagement for analytics
    - Linking preview sessions to user accounts after signup
    - Understanding conversion from preview to registration
    """
    __tablename__ = "guest_previews"
    __table_args__ = (
        Index("idx_guest_previews_session_id", "session_id"),
        Index("idx_guest_previews_started_at", "started_at"),
        Index("idx_guest_previews_converted_user", "converted_to_user_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True
    )  # Browser/device session identifier
    preview_lesson_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("lesson_content.id", ondelete="SET NULL"),
        nullable=True,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    converted_to_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    device_info: Mapped[Optional[Any]] = mapped_column(
        JSONB, nullable=True
    )  # Store device/browser metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    preview_lesson: Mapped[Optional["LessonContent"]] = relationship(
        "LessonContent",
        foreign_keys=[preview_lesson_id],
    )
    converted_to_user: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[converted_to_user_id],
    )


class UserContentInteraction(Base):
    """Track user interactions with content for recommendation algorithms.

    This table enables:
    - Collaborative filtering (users who liked X also liked Y)
    - Content-based filtering (similar content based on tags)
    - Personalized recommendations based on browsing history
    - Understanding user preferences and learning patterns
    """
    __tablename__ = "user_content_interactions"
    __table_args__ = (
        Index("idx_user_content_interactions_user", "user_id"),
        Index("idx_user_content_interactions_content", "content_type", "content_id"),
        Index("idx_user_content_interactions_type", "interaction_type"),
        Index("idx_user_content_interactions_created", "created_at"),
        Index("idx_user_content_interactions_user_type", "user_id", "content_type"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    content_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # lesson, motif, quest
    content_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), nullable=False
    )
    interaction_type: Mapped[InteractionType] = mapped_column(
        SAEnum(InteractionType, name="interaction_type", native_enum=True),
        nullable=False,
    )
    duration_seconds: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # For view interactions
    metadata_json: Mapped[Optional[Any]] = mapped_column(
        "metadata", JSONB, nullable=True
    )  # Additional context
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User")


class SpacedRepetitionCard(Base):
    """Spaced repetition card for motif review using SM-2 algorithm.

    This table manages the spaced repetition scheduler for motif learning:
    - Uses the SuperMemo-2 (SM-2) algorithm
    - Tracks ease factor and interval for each card
    - Maintains review history for analytics
    - Schedules next review based on performance
    """
    __tablename__ = "spaced_repetition_cards"
    __table_args__ = (
        UniqueConstraint("user_id", "motif_id", name="uq_sr_cards_user_motif"),
        Index("idx_sr_cards_user", "user_id"),
        Index("idx_sr_cards_motif", "motif_id"),
        Index("idx_sr_cards_next_review", "next_review_at"),
        Index("idx_sr_cards_user_next_review", "user_id", "next_review_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    motif_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("motifs.id", ondelete="CASCADE"),
        nullable=False,
    )

    ease_factor: Mapped[float] = mapped_column(
        Float, nullable=False, server_default=text("2.5")
    )
    interval_days: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    repetitions: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    next_review_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    last_reviewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    review_history: Mapped[list[Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    user: Mapped["User"] = relationship("User")
    motif: Mapped["Motif"] = relationship("Motif")



class AIConversation(Base):
    """AI Tutor conversation sessions."""
    __tablename__ = "ai_conversations"
    __table_args__ = (
        Index("idx_ai_conversation_user", "user_id"),
        Index("idx_ai_conversation_context", "context_type", "context_id"),
        Index("idx_ai_conversation_active", "is_active"),
        Index("idx_ai_conversation_created", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Conversation metadata
    title: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )  # Auto-generated from first message

    # Context for the conversation (optional)
    context_type: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # e.g., "lesson", "motif", "quest", "general"
    context_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True
    )  # ID of related content

    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )
    message_count: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    messages: Mapped[list["AIMessage"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="AIMessage.created_at",
    )


class AIMessage(Base):
    """Individual messages in AI conversations."""
    __tablename__ = "ai_messages"
    __table_args__ = (
        Index("idx_ai_message_conversation", "conversation_id"),
        Index("idx_ai_message_role", "role"),
        Index("idx_ai_message_created", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("ai_conversations.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Message content
    role: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # "user", "assistant", "system"
    content: Mapped[str] = mapped_column(
        Text, nullable=False
    )

    # Token tracking for cost management
    tokens_used: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    conversation: Mapped["AIConversation"] = relationship(
        "AIConversation", back_populates="messages"
    )


class UserLearningPath(Base):
    """Daily personalized learning path for users."""
    __tablename__ = "user_learning_paths"
    __table_args__ = (
        UniqueConstraint("user_id", "path_date", name="uq_user_learning_path_user_date"),
        Index("idx_learning_path_user", "user_id"),
        Index("idx_learning_path_date", "path_date"),
        Index("idx_learning_path_completed", "is_completed"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    path_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )  # The date this path is for (date part only, time should be 00:00:00)

    # Recommended items (stored as lists of UUIDs with order)
    recommended_lessons: Mapped[Any] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )  # [{"lesson_id": UUID, "order": int, "reason": str}]
    recommended_reviews: Mapped[Any] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )  # [{"motif_id": UUID, "order": int, "priority": str, "due_date": datetime}]
    recommended_quizzes: Mapped[Any] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )  # [{"motif_id": UUID, "order": int, "difficulty": int}]

    # Progress tracking
    estimated_time_minutes: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )  # Estimated time to complete the path
    completed_items: Mapped[Any] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )  # [{"item_type": "lesson|review|quiz", "item_id": UUID, "completed_at": datetime}]
    is_completed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )

    # Timestamps
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])


class UserFollow(Base):
    """Track user following relationships for social features."""
    __tablename__ = "user_follows"
    __table_args__ = (
        UniqueConstraint("follower_id", "following_id", name="uq_user_follows"),
        CheckConstraint("follower_id != following_id", name="ck_user_follows_no_self_follow"),
        Index("idx_user_follows_follower", "follower_id"),
        Index("idx_user_follows_following", "following_id"),
        Index("idx_user_follows_created", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    follower_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    following_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    follower: Mapped["User"] = relationship("User", foreign_keys=[follower_id], back_populates="following")
    following: Mapped["User"] = relationship("User", foreign_keys=[following_id], back_populates="followers")


class FriendRequest(Base):
    """Track friend requests between users."""
    __tablename__ = "friend_requests"
    __table_args__ = (
        UniqueConstraint("from_user_id", "to_user_id", name="uq_friend_requests"),
        Index("idx_friend_requests_from_user", "from_user_id"),
        Index("idx_friend_requests_to_user", "to_user_id"),
        Index("idx_friend_requests_status", "status"),
        Index("idx_friend_requests_created", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    from_user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    to_user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[FriendRequestStatus] = mapped_column(
        SAEnum(FriendRequestStatus, name="friend_request_status", native_enum=True),
        nullable=False,
        server_default=text("'pending'"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    responded_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    from_user: Mapped["User"] = relationship("User", foreign_keys=[from_user_id], back_populates="sent_friend_requests")
    to_user: Mapped["User"] = relationship("User", foreign_keys=[to_user_id], back_populates="received_friend_requests")


class ShareType(str, Enum):
    achievement = "achievement"
    badge = "badge"
    streak = "streak"
    level_up = "level_up"
    certificate = "certificate"


class ShareVisibility(str, Enum):
    public = "public"
    followers = "followers"
    private = "private"


class UserShare(Base):
    """User shares for achievements and progress (social sharing feature)."""
    __tablename__ = "user_shares"
    __table_args__ = (
        Index("idx_user_shares_user", "user_id"),
        Index("idx_user_shares_type", "share_type"),
        Index("idx_user_shares_visibility", "visibility"),
        Index("idx_user_shares_created", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    share_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # achievement, badge, streak, level_up, certificate
    content_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True
    )  # ID of the shared item (badge_id, certificate_id, etc.)
    caption: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # User's custom message
    visibility: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'public'")
    )  # public, followers, private
    share_url: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )  # Generated shareable link
    view_count: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])


class StudentProgressSnapshot(Base):
    """Cached progress snapshots for classroom students."""
    __tablename__ = "student_progress_snapshots"
    __table_args__ = (
        UniqueConstraint(
            "student_id", "classroom_id", "snapshot_date",
            name="uq_progress_snapshot_student_classroom_date"
        ),
        Index("idx_progress_snapshots_student", "student_id"),
        Index("idx_progress_snapshots_classroom", "classroom_id"),
        Index("idx_progress_snapshots_date", "snapshot_date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    classroom_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("classes.id", ondelete="CASCADE"),
        nullable=False,
    )
    snapshot_date: Mapped[date] = mapped_column(
        Date, nullable=False
    )

    # Progress metrics
    lessons_completed: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    quizzes_passed: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    average_quiz_score: Mapped[float] = mapped_column(
        Float, nullable=False, server_default=text("0.0")
    )
    motifs_discovered: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    current_streak: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    xp_earned: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    time_spent_minutes: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    student: Mapped["User"] = relationship("User", foreign_keys=[student_id])
    classroom: Mapped["Classroom"] = relationship("Classroom")


class PushNotification(Base):
    """Push notifications sent to users via FCM/APNs."""
    __tablename__ = "push_notifications"
    __table_args__ = (
        Index("idx_push_notifications_user", "user_id"),
        Index("idx_push_notifications_status", "status"),
        Index("idx_push_notifications_scheduled", "scheduled_for"),
        Index("idx_push_notifications_user_created", "user_id", "created_at"),
        Index("idx_push_notifications_type", "notification_type"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Notification content
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    notification_type: Mapped[NotificationType] = mapped_column(
        SAEnum(NotificationType, native_enum=False, length=50),
        nullable=False,
    )

    # Custom payload for the app
    data_payload: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSONB, nullable=True
    )

    # Notification status tracking
    status: Mapped[NotificationStatus] = mapped_column(
        SAEnum(NotificationStatus, native_enum=False, length=20),
        nullable=False,
        server_default=text("'pending'"),
    )

    # Scheduling and delivery tracking
    scheduled_for: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    delivered_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Error tracking
    error_message: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])


class EmailTemplate(Base):
    """
    Email templates for scheduled notifications.

    Templates support variable substitution using Jinja2-like syntax:
    - {{user_name}} - User's display name
    - {{streak_count}} - Current streak
    - {{missions_completed}} - Daily missions completed
    - etc.
    """
    __tablename__ = "email_templates"
    __table_args__ = (
        Index("idx_email_templates_key", "key"),
        Index("idx_email_templates_active", "is_active"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    key: Mapped[str] = mapped_column(
        String(100), nullable=False, unique=True,
        comment="Unique template identifier (e.g., 'daily_digest', 'weekly_summary')"
    )
    name: Mapped[str] = mapped_column(
        String(200), nullable=False,
        comment="Human-readable template name"
    )
    subject_template: Mapped[str] = mapped_column(
        String(500), nullable=False,
        comment="Email subject with optional placeholders"
    )
    body_html: Mapped[str] = mapped_column(
        Text, nullable=False,
        comment="HTML email body template"
    )
    body_text: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="Plain text email body template (optional)"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true"),
        comment="Whether this template is currently active"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    scheduled_emails: Mapped[list["ScheduledEmail"]] = relationship(
        back_populates="template",
        cascade="all, delete-orphan",
    )


class ScheduledEmail(Base):
    """
    Scheduled email records for digest emails and notifications.

    Tracks individual email sends to users, including scheduling,
    delivery status, and error handling.
    """
    __tablename__ = "scheduled_emails"
    __table_args__ = (
        Index("idx_scheduled_emails_user", "user_id"),
        Index("idx_scheduled_emails_template", "template_id"),
        Index("idx_scheduled_emails_status", "status"),
        Index("idx_scheduled_emails_scheduled_for", "scheduled_for"),
        Index("idx_scheduled_emails_sent_at", "sent_at"),
        Index("idx_scheduled_emails_user_template", "user_id", "template_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    template_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("email_templates.id", ondelete="CASCADE"),
        nullable=False,
    )
    scheduled_for: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        comment="When this email should be sent"
    )
    status: Mapped[EmailStatus] = mapped_column(
        SAEnum(EmailStatus, name="email_status", native_enum=True),
        nullable=False,
        server_default=text("'pending'"),
        comment="Current status of the email"
    )
    context_data: Mapped[Optional[Any]] = mapped_column(
        JSONB, nullable=True,
        comment="Template variables for rendering (e.g., streak_count, missions)"
    )
    sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
        comment="When the email was successfully sent"
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="Error message if send failed"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User")
    template: Mapped["EmailTemplate"] = relationship(
        "EmailTemplate",
        back_populates="scheduled_emails"
    )


class FeatureFlag(Base):
    """Feature flags for A/B testing and gradual rollouts."""
    __tablename__ = "feature_flags"
    __table_args__ = (
        Index("idx_feature_flags_key", "key"),
        Index("idx_feature_flags_enabled", "is_enabled"),
        Index("idx_feature_flags_created_by", "created_by_id"),
        CheckConstraint("rollout_percentage >= 0 AND rollout_percentage <= 100", name="check_rollout_percentage_range"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    key: Mapped[str] = mapped_column(
        String(100), nullable=False, unique=True
    )  # e.g., "new_quiz_ui", "ai_hints"
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )  # Global on/off switch
    rollout_percentage: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )  # 0-100 percentage of users
    user_whitelist: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSONB, nullable=True
    )  # List of user IDs always enabled
    user_blacklist: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSONB, nullable=True
    )  # List of user IDs always disabled
    rules: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSONB, nullable=True
    )  # Targeting rules (role, signup_date, etc.)
    created_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    created_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[created_by_id])


class Experiment(Base):
    """A/B test experiments with variants."""
    __tablename__ = "experiments"
    __table_args__ = (
        Index("idx_experiments_key", "key"),
        Index("idx_experiments_active", "is_active"),
        Index("idx_experiments_created_by", "created_by_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    key: Mapped[str] = mapped_column(
        String(100), nullable=False, unique=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    variants: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False
    )
    target_audience: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSONB, nullable=True
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    start_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    end_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    created_by: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[created_by_id],
    )
    assignments: Mapped[list["UserExperimentAssignment"]] = relationship(
        back_populates="experiment",
        cascade="all, delete-orphan",
    )


class UserExperimentAssignment(Base):
    """Track which variant each user is assigned to in experiments."""
    __tablename__ = "user_experiment_assignments"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "experiment_id",
            name="uq_user_experiment_assignment"
        ),
        Index("idx_user_experiment_assignments_user", "user_id"),
        Index("idx_user_experiment_assignments_experiment", "experiment_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    experiment_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("experiments.id", ondelete="CASCADE"),
        nullable=False,
    )
    variant_key: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # e.g., "control", "variant_a", "variant_b"
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    experiment: Mapped["Experiment"] = relationship("Experiment", back_populates="assignments")
    events: Mapped[list["ExperimentEvent"]] = relationship(
        back_populates="assignment",
        cascade="all, delete-orphan",
    )


class ExperimentEvent(Base):
    """Track events for experiment conversion tracking and analysis."""
    __tablename__ = "experiment_events"
    __table_args__ = (
        Index("idx_experiment_events_experiment", "experiment_id"),
        Index("idx_experiment_events_user", "user_id"),
        Index("idx_experiment_events_assignment", "assignment_id"),
        Index("idx_experiment_events_type", "event_type"),
        Index("idx_experiment_events_created", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    experiment_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("experiments.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    assignment_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("user_experiment_assignments.id", ondelete="CASCADE"),
        nullable=False,
    )
    event_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # impression, conversion, click, custom
    event_name: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # Specific event like "completed_onboarding", "clicked_cta"
    event_value: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )  # Numeric metric value
    metadata_json: Mapped[Optional[dict[str, Any]]] = mapped_column(
        "metadata", JSONB, nullable=True
    )  # Additional event data
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    experiment: Mapped["Experiment"] = relationship("Experiment")
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    assignment: Mapped["UserExperimentAssignment"] = relationship(
        "UserExperimentAssignment", back_populates="events"
    )


class ExperimentMetricEvent(Base):
    """Track metric events for experiments - measures specific metrics per variant."""
    __tablename__ = "experiment_metric_events"
    __table_args__ = (
        Index("idx_experiment_metric_events_experiment", "experiment_id"),
        Index("idx_experiment_metric_events_user", "user_id"),
        Index("idx_experiment_metric_events_variant", "variant"),
        Index("idx_experiment_metric_events_metric_name", "metric_name"),
        Index("idx_experiment_metric_events_created", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    experiment_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("experiments.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    variant: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # Variant key the user is assigned to
    metric_name: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # e.g., "conversion", "retention", "engagement"
    metric_value: Mapped[float] = mapped_column(
        Float, nullable=False
    )  # Numeric value for the metric
    metadata_json: Mapped[Optional[dict[str, Any]]] = mapped_column(
        "metadata", JSONB, nullable=True
    )  # Additional metric metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    experiment: Mapped["Experiment"] = relationship("Experiment")
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])


class UserLeaderboardSettings(Base):
    """User preferences for leaderboard display and privacy.

    This table manages user-specific leaderboard settings:
    - Visibility preferences (show on global leaderboard)
    - Display name preferences (show real name vs username)
    - Default leaderboard view preference
    """
    __tablename__ = "user_leaderboard_settings"
    __table_args__ = (
        Index("idx_user_leaderboard_settings_user", "user_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    show_on_global: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )
    show_real_name: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    preferred_leaderboard: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'global'")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="leaderboard_settings")


class UserLeague(Base):
    """Weekly league participation and rankings for competitive gamification.

    This table manages the Duolingo-style league system:
    - Users compete weekly within their tier based on XP earned
    - Top performers get promoted to higher tiers
    - Bottom performers get demoted to lower tiers
    - Each week creates new league entries for active users
    """
    __tablename__ = "user_leagues"
    __table_args__ = (
        UniqueConstraint("user_id", "week_start", name="uq_user_leagues_user_week"),
        Index("idx_user_leagues_user", "user_id"),
        Index("idx_user_leagues_tier", "tier"),
        Index("idx_user_leagues_week", "week_start", "week_end"),
        Index("idx_user_leagues_tier_week", "tier", "week_start"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    tier: Mapped[LeagueTier] = mapped_column(
        SAEnum(LeagueTier, name="league_tier", native_enum=True),
        nullable=False,
        server_default=text("'bronze'"),
    )
    weekly_xp: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    week_start: Mapped[date] = mapped_column(Date, nullable=False)
    week_end: Mapped[date] = mapped_column(Date, nullable=False)
    rank_in_tier: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    promoted: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    demoted: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="league_entries")


class RevokedRefreshToken(Base):
    """Revoked refresh tokens keyed by JWT id (`jti`) for refresh-token revocation."""
    __tablename__ = "revoked_refresh_tokens"
    __table_args__ = (
        Index("idx_revoked_refresh_tokens_expires_at", "expires_at"),
    )

    jti: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    revoked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    user: Mapped["User"] = relationship("User")


class HistoryQuestionType(Base):
    """Registry of the Historical Learning Engine V2 question types (Spec 32).

    Migration 0050 seeds the 11 V2 keys. The ``quiz_questions.question_type``
    enum remains the Postgres enum; this table is the human-readable registry
    (label_vi/label_en + sort order) used by authoring/admin tooling.
    """
    __tablename__ = "history_question_types"
    __table_args__ = (
        UniqueConstraint("key", name="uq_history_question_types_key"),
        Index("idx_history_question_types_sort", "sort_order"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    key: Mapped[str] = mapped_column(String(50), nullable=False)
    label_vi: Mapped[str] = mapped_column(String(255), nullable=False)
    label_en: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


# --------------------------------------------------------------------------- #
# History-First domain models (Phase 1). Defined in ``backend.history_models``
# to keep this module's size manageable; imported here so ``Base.metadata``
# includes the historical_* tables for conftest create_all and Alembic.
# --------------------------------------------------------------------------- #
from .history_models import (  # noqa: E402,F401
    HistoricalAsset,
    HistoricalClaim,
    HistoricalClaimOrigin,
    HistoricalClaimSource,
    HistoricalClaimType,
    HistoricalConfidence,
    HistoricalContentAuditLog,
    HistoricalEntity,
    HistoricalEntityRelation,
    HistoricalEntityType,
    HistoricalGeoPrecision,
    HistoricalGeography,
    HistoricalMappingStatus,
    HistoricalPublicationStatus,
    HistoricalRelationPredicate,
    HistoricalRiskLevel,
    HistoricalSource,
    HistoricalSourceType,
    HistoricalSourceVerificationStatus,
    HistoricalSupportType,
    HistoricalVerificationStatus,
    HistoryStory,
    HistoryCollection,
)
