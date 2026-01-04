from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
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


class Base(DeclarativeBase):
    pass


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
    multiple_choice = "multiple_choice"
    true_false = "true_false"
    image_select = "image_select"
    mesh_location = "mesh_location"


class BadgeCategory(str, Enum):
    quest = "quest"
    achievement = "achievement"
    collection = "collection"
    special = "special"


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
    quiz_attempts: Mapped[list[QuizAttempt]] = relationship(
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
    content_flags: Mapped[list["ContentFlag"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    starting_urn: Mapped[Optional["Urn"]] = relationship(
        "Urn",
        foreign_keys=[starting_urn_id],
    )


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
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
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
    explanation: Mapped[Optional[str]] = mapped_column(Text)

    is_published: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    motif: Mapped[Motif] = relationship(back_populates="quiz_questions")
    urn: Mapped[Optional[Urn]] = relationship(
        back_populates="exam_questions", foreign_keys=[urn_id]
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
    xp_bonus: Mapped[int] = mapped_column(
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
    earned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    user: Mapped[User] = relationship(back_populates="user_badges")
    badge: Mapped[Badge] = relationship(back_populates="user_badges")


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
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    teacher: Mapped["User"] = relationship(
        back_populates="classes", foreign_keys=[teacher_id]
    )
    members: Mapped[list["ClassMember"]] = relationship(
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
