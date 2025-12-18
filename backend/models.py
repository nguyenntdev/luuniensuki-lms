from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from sqlalchemy import Boolean
from sqlalchemy import DateTime
from sqlalchemy import Enum as SAEnum
from sqlalchemy import Float
from sqlalchemy import ForeignKey
from sqlalchemy import Index
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy import UniqueConstraint
from sqlalchemy import func
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship


class Base(DeclarativeBase):
    pass


class UserRole(str, Enum):
    guest = "guest"
    learner = "learner"
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
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    avatar_url: Mapped[Optional[str]] = mapped_column(Text)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    username: Mapped[Optional[str]] = mapped_column(String(50), unique=True, nullable=True)
    is_profile_public: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, name="user_role", native_enum=True),
        nullable=False,
        server_default=text("'learner'"),
    )
    total_xp: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    current_streak: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    longest_streak: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    streak_freezes: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    last_active_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
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


class Urn(Base):
    __tablename__ = "urns"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    name_han: Mapped[Optional[str]] = mapped_column(String(50))
    represents: Mapped[Optional[str]] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text)
    model_url: Mapped[str] = mapped_column(Text, nullable=False)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(Text)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

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


class Motif(Base):
    __tablename__ = "motifs"
    __table_args__ = (
        Index("idx_motifs_urn", "urn_id"),
        Index("idx_motifs_mesh", "mesh_name"),
        Index("idx_motifs_category", "category"),
        Index("idx_motifs_rarity", "rarity"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
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

    is_demo: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))

    display_order: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
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

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
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

    is_ai_generated: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
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

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
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
    lesson_viewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    learned_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    mastered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    quiz_attempts: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    quiz_best_score: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))

    xp_earned: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
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

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
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

    difficulty: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))
    explanation: Mapped[Optional[str]] = mapped_column(Text)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    motif: Mapped[Motif] = relationship(back_populates="quiz_questions")
    urn: Mapped[Optional[Urn]] = relationship(back_populates="exam_questions", foreign_keys=[urn_id])


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"
    __table_args__ = (
        Index("idx_quiz_attempts_user", "user_id"),
        Index("idx_quiz_attempts_motif", "motif_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
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

    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    user: Mapped[User] = relationship(back_populates="quiz_attempts")
    motif: Mapped[Motif] = relationship(back_populates="quiz_attempts")


class UrnExam(Base):
    __tablename__ = "urn_exams"
    __table_args__ = (Index("idx_urn_exams_urn", "urn_id"),)

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    urn_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("urns.id", ondelete="CASCADE"),
        nullable=False,
    )

    questions: Mapped[Any] = mapped_column(JSONB, nullable=False)
    passing_score: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("80"))
    xp_reward: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("100"))

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

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
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

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    user: Mapped[User] = relationship(back_populates="urn_exam_attempts")
    urn_exam: Mapped[UrnExam] = relationship(back_populates="attempts")


class Badge(Base):
    __tablename__ = "badges"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    name_en: Mapped[Optional[str]] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text)
    icon_url: Mapped[str] = mapped_column(Text, nullable=False)

    category: Mapped[BadgeCategory] = mapped_column(
        SAEnum(BadgeCategory, name="badge_category", native_enum=True),
        nullable=False,
    )
    xp_bonus: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    unlock_criteria: Mapped[Any] = mapped_column(JSONB, nullable=False)

    is_secret: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

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

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
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
    earned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    user: Mapped[User] = relationship(back_populates="user_badges")
    badge: Mapped[Badge] = relationship(back_populates="user_badges")
