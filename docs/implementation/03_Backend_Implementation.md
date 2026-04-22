# 03_Backend_Implementation.md

Backend Core bootstrap for **Lưu Niên Sử Kí** using **FastAPI + SQLAlchemy + PostgreSQL**.

## Deployment Target (Note)

- Server IP: `160.30.113.189`
- Domain: `lms.histolab.icu`
- Do **not** store credentials in git. Use `.env` / Docker secrets / a vault for passwords and tokens.

---

## 1) Setup Script

### `backend/requirements.txt`

```txt
fastapi>=0.110,<1.0
uvicorn[standard]>=0.29,<1.0

SQLAlchemy>=2.0,<3.0
psycopg[binary]>=3.1,<4.0

pydantic>=2.6,<3.0
pydantic-settings>=2.2,<3.0
python-dotenv>=1.0,<2.0
```

### `docker-compose.yml`

```yaml
services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-luuniensuki}
      POSTGRES_USER: ${POSTGRES_USER:-postgres}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-postgres}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $$POSTGRES_USER -d $$POSTGRES_DB"]
      interval: 5s
      timeout: 5s
      retries: 20
    ports:
      - "${POSTGRES_PORT:-5432}:5432"

  api:
    build:
      context: .
      dockerfile: backend/Dockerfile
    environment:
      DATABASE_URL: postgresql+psycopg://${POSTGRES_USER:-postgres}:${POSTGRES_PASSWORD:-postgres}@db:5432/${POSTGRES_DB:-luuniensuki}
      LOG_LEVEL: ${LOG_LEVEL:-info}
      INTERACTION_TOLERANCE_MULTIPLIER: ${INTERACTION_TOLERANCE_MULTIPLIER:-1.25}
    depends_on:
      db:
        condition: service_healthy
    ports:
      - "${API_PORT:-8000}:8000"
    command: ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
    volumes:
      - .:/app

volumes:
  postgres_data:
```

### `backend/Dockerfile` (used by Compose)

```dockerfile
FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN pip install --no-cache-dir --upgrade pip

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
```

---

## 2) Database Models — `backend/models.py`

Implements Claude’s ERD + the SQL schema details from `docs/architecture/01_Architecture_Spec.md`.

```python
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
        Index("idx_users_role", "role"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    avatar_url: Mapped[Optional[str]] = mapped_column(Text)
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
```

---

## 3) Seeding Script — `backend/seed.py`

Seeds from a file or directory (`--seed-path`, default: `data/`) and optionally scans an image directory
(`--image-path`, default: `ban-duc-noi/`) to populate `Motif.thumbnail_url` with web paths like
`/assets/ban-duc-noi/...`.

- `urns`
- `badges`
- `motifs`
- `lesson_content`
- `quiz_questions`
  - (optional) `motifs.thumbnail_url` (from `/assets/...`)

```python
from __future__ import annotations

import argparse
import difflib
import json
import os
import re
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import quote

from sqlalchemy import create_engine
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker

if __package__ in (None, ""):
    REPO_ROOT = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(REPO_ROOT))

    from backend.models import Badge
    from backend.models import BadgeCategory
    from backend.models import Base
    from backend.models import LessonContent
    from backend.models import Motif
    from backend.models import MotifCategory
    from backend.models import MotifRarity
    from backend.models import QuestionType
    from backend.models import QuizQuestion
    from backend.models import Urn
else:
    from .models import Badge
    from .models import BadgeCategory
    from .models import Base
    from .models import LessonContent
    from .models import Motif
    from .models import MotifCategory
    from .models import MotifRarity
    from .models import QuestionType
    from .models import QuizQuestion
    from .models import Urn


URN_ORDER: dict[str, int] = {
    "cao-dinh": 1,
    "nhan-dinh": 2,
    "chuong-dinh": 3,
    "anh-dinh": 4,
    "nghi-dinh": 5,
    "thuan-dinh": 6,
    "tuyen-dinh": 7,
    "du-dinh": 8,
    "huyen-dinh": 9,
}

# Remote GLB filenames currently available on store.histolab.icu (proxied via Nginx under /assets/models/).
URN_MODEL_FILENAMES: dict[str, str] = {
    "cao-dinh": "CAO-DINH-v1.glb",
    "chuong-dinh": "CHUONG-DINH-v1.glb",
    "huyen-dinh": "HUYEN-DINH-v1.glb",
    "nghi-dinh": "NGHI-DINH-v1.glb",
    "thuan-dinh": "THUAN-DINH-v1.glb",
    "tuyen-dinh": "TUYEN-DINH-v1.glb",
}

# Manual fallbacks for known naming mismatches between seed data and image filenames.
# Keyed by (urn_slug, motif_slug_from_seed) -> motif_slug_from_images
IMAGE_SLUG_ALIASES: dict[tuple[str, str], str] = {
    ("chuong-dinh", "ngu-tinh"): "moc-tinh-hoa-tinh-tho-tinh-kim-tinh-thuy-tinh",
    # ban-duc-noi/NHAN DINH contains "HUƠU GIANG.jpg" but seed uses "Hương Giang".
    ("nhan-dinh", "huong-giang"): "huou-giang",
}

COMPOSITE_NAME_SPLIT_RE = re.compile(r"\s*(?:,|;|\s+[\-–—]\s+)\s*")


DEFAULT_BADGES: list[dict[str, Any]] = [
    {
        "slug": "first-discovery",
        "name": "Khai Môn",
        "name_en": "First Discovery",
        "description": "Mở khóa họa tiết đầu tiên.",
        "icon_url": "/assets/badges/first-discovery.svg",
        "category": BadgeCategory.achievement,
        "xp_bonus": 100,
        "unlock_criteria": {"type": "first_discovery"},
        "is_secret": False,
    },
    {
        "slug": "first-mastered",
        "name": "Bậc Thầy Đầu Tiên",
        "name_en": "First Mastery",
        "description": "Hoàn thành (mastered) họa tiết đầu tiên.",
        "icon_url": "/assets/badges/first-mastered.svg",
        "category": BadgeCategory.achievement,
        "xp_bonus": 200,
        "unlock_criteria": {"type": "first_mastered"},
        "is_secret": False,
    },
    {
        "slug": "streak-7",
        "name": "Thất Nhật Liên Tiếp",
        "name_en": "7-Day Streak",
        "description": "Duy trì streak 7 ngày liên tiếp.",
        "icon_url": "/assets/badges/streak-7.svg",
        "category": BadgeCategory.achievement,
        "xp_bonus": 150,
        "unlock_criteria": {"type": "streak", "days": 7},
        "is_secret": False,
    },
]


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = value.replace("đ", "d")
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def extract_json_array_from_markdown(markdown: str) -> list[dict[str, Any]]:
    match = re.search(r"```json\s*(\[.*?\])\s*```", markdown, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        raise ValueError("No ```json ... ``` array block found in seed markdown file.")
    data = json.loads(match.group(1))
    if not isinstance(data, list):
        raise ValueError("Expected top-level JSON array in seed file.")
    if not all(isinstance(item, dict) for item in data):
        raise ValueError("Expected JSON array of objects in seed file.")
    return data


def process_file(file_path: Path) -> list[dict[str, Any]]:
    suffix = file_path.suffix.lower()
    if suffix == ".json":
        data = json.loads(file_path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError(f"Expected JSON array in {file_path}")
        if not all(isinstance(item, dict) for item in data):
            raise ValueError(f"Expected JSON array of objects in {file_path}")
        return data

    if suffix in {".md", ".markdown"}:
        markdown = file_path.read_text(encoding="utf-8")
        return extract_json_array_from_markdown(markdown)

    raise ValueError(f"Unsupported seed file type: {file_path}")


def parse_display_order(raw_id: Any) -> int | None:
    if not isinstance(raw_id, str) or not raw_id:
        return None
    match = re.search(r"_(\d+)$", raw_id)
    if not match:
        return None
    try:
        return int(match.group(1))
    except ValueError:
        return None


def slug_variants(value: str) -> list[str]:
    variants: list[str] = [slugify(value)]
    parts = [p for p in COMPOSITE_NAME_SPLIT_RE.split(value) if p.strip()]
    if len(parts) > 1:
        part_slugs = [slugify(part) for part in parts]
        variants.append("-".join(sorted(part_slugs)))
    return list(dict.fromkeys(variants))


def resolve_thumbnail_url(image_map: dict[tuple[str, str], str], *, urn_slug: str, name_vi: str) -> str | None:
    target_slug = slugify(name_vi)

    alias = IMAGE_SLUG_ALIASES.get((urn_slug, target_slug))
    if alias:
        url = image_map.get((urn_slug, alias))
        if url:
            return url

    for candidate_slug in slug_variants(name_vi):
        url = image_map.get((urn_slug, candidate_slug))
        if url:
            return url

    candidates = [motif_slug for (u, motif_slug) in image_map.keys() if u == urn_slug]
    matches = difflib.get_close_matches(target_slug, candidates, n=2, cutoff=0.85)
    if not matches:
        return None

    if len(matches) == 1:
        return image_map.get((urn_slug, matches[0]))

    ratio_best = difflib.SequenceMatcher(None, target_slug, matches[0]).ratio()
    ratio_second = difflib.SequenceMatcher(None, target_slug, matches[1]).ratio()
    if ratio_best - ratio_second >= 0.05:
        return image_map.get((urn_slug, matches[0]))

    return None


@dataclass(frozen=True)
class SeedConfig:
    database_url: str
    seed_path: Path
    model_base_url: str


def upsert_urn(session: Session, *, name: str, model_base_url: str) -> Urn:
    slug = slugify(name)
    display_order = URN_ORDER.get(slug, 0)
    is_demo = slug == "cao-dinh"
    model_filename = URN_MODEL_FILENAMES.get(slug, f"{slug}.glb")
    model_url = f"{model_base_url.rstrip('/')}/{model_filename}"

    urn = session.execute(select(Urn).where(Urn.slug == slug)).scalar_one_or_none()
    if urn is None:
        urn = Urn(
            slug=slug,
            name=name,
            model_url=model_url,
            display_order=display_order,
            is_demo=is_demo,
        )
        session.add(urn)
        session.flush()
        return urn

    urn.name = name
    urn.model_url = model_url
    urn.display_order = display_order or urn.display_order
    urn.is_demo = is_demo
    session.flush()
    return urn


def upsert_badge(
    session: Session,
    *,
    slug: str,
    name: str,
    name_en: str | None,
    description: str | None,
    icon_url: str,
    category: BadgeCategory,
    xp_bonus: int,
    unlock_criteria: Any,
    is_secret: bool,
) -> Badge:
    badge = session.execute(select(Badge).where(Badge.slug == slug)).scalar_one_or_none()
    if badge is None:
        badge = Badge(
            slug=slug,
            name=name,
            name_en=name_en,
            description=description,
            icon_url=icon_url,
            category=category,
            xp_bonus=xp_bonus,
            unlock_criteria=unlock_criteria,
            is_secret=is_secret,
            is_active=True,
        )
        session.add(badge)
        session.flush()
        return badge

    badge.name = name
    badge.name_en = name_en
    badge.description = description
    badge.icon_url = icon_url
    badge.category = category
    badge.xp_bonus = xp_bonus
    badge.unlock_criteria = unlock_criteria
    badge.is_secret = is_secret
    badge.is_active = True
    session.flush()
    return badge


def scan_images(image_path: Path) -> dict[tuple[str, str], str]:
    """
    Scans the image directory and returns a mapping of (urn_slug, motif_slug) -> image_url.
    Assumes structure: image_path / Urn_Name / Motif_Name.jpg
    """
    if not image_path.exists():
        print(f"Warning: Image path {image_path} does not exist.")
        return {}

    image_extensions = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
    base_url = f"/assets/{image_path.name}".rstrip("/")

    candidates: dict[tuple[str, str], list[str]] = {}
    files = sorted(p for p in image_path.rglob("*") if p.is_file() and p.suffix.lower() in image_extensions)
    print(f"Scanning images in {image_path}... ({len(files)} files)")

    for img_file in files:
        rel = img_file.relative_to(image_path)
        if len(rel.parts) < 2:
            continue

        urn_dir_name = rel.parts[0]
        urn_slug = slugify(urn_dir_name)
        motif_slug = slugify(img_file.stem)
        key = (urn_slug, motif_slug)
        image_url = f"{base_url}/{quote(rel.as_posix(), safe='/')}"
        candidates.setdefault(key, []).append(image_url)

    image_map: dict[tuple[str, str], str] = {}
    duplicates = 0
    for key, urls in candidates.items():
        image_map[key] = urls[0]
        if len(urls) > 1:
            duplicates += len(urls) - 1
            print(f"Warning: Multiple images match {key}: using {urls[0]} (ignored {len(urls) - 1})")

    print(f"Found {len(image_map)} image mappings ({duplicates} duplicates).")
    return image_map


def upsert_motif(
    session: Session,
    *,
    urn: Urn,
    mesh_name: str,
    name_vi: str,
    name_en: str | None,
    category: MotifCategory,
    rarity: MotifRarity,
    display_order: int | None,
    thumbnail_url: str | None = None,
) -> Motif:
    motif = session.execute(select(Motif).where(Motif.mesh_name == mesh_name)).scalar_one_or_none()
    if motif is None:
        motif = Motif(
            urn_id=urn.id,
            mesh_name=mesh_name,
            name=name_vi,
            name_en=name_en,
            category=category,
            rarity=rarity,
            pos_x=0.0,
            pos_y=0.0,
            pos_z=0.0,
            bounding_radius=1.0,
            is_demo=urn.is_demo,
            display_order=display_order,
            thumbnail_url=thumbnail_url,
        )
        session.add(motif)
        session.flush()
        return motif

    motif.urn_id = urn.id
    motif.name = name_vi
    motif.name_en = name_en
    motif.category = category
    motif.rarity = rarity
    motif.is_demo = urn.is_demo
    motif.display_order = display_order
    if thumbnail_url:
        motif.thumbnail_url = thumbnail_url
    session.flush()
    return motif


def upsert_lesson(session: Session, *, motif: Motif, intro_text: str | None, description: str) -> LessonContent:
    lesson = session.execute(select(LessonContent).where(LessonContent.motif_id == motif.id)).scalar_one_or_none()
    if lesson is None:
        lesson = LessonContent(
            motif_id=motif.id,
            intro_text=intro_text,
            description=description,
        )
        session.add(lesson)
        session.flush()
        return lesson

    lesson.intro_text = intro_text
    lesson.description = description
    session.flush()
    return lesson


def upsert_quiz_question(
    session: Session,
    *,
    motif: Motif,
    question_text: str,
    options: list[str] | None,
    correct_answer: str,
) -> QuizQuestion:
    existing = session.execute(
        select(QuizQuestion).where(
            QuizQuestion.motif_id == motif.id,
            QuizQuestion.question_text == question_text,
        )
    ).scalar_one_or_none()

    if existing is None:
        existing = QuizQuestion(
            motif_id=motif.id,
            question_type=QuestionType.multiple_choice,
            question_text=question_text,
            options=options,
            correct_answer=correct_answer,
            difficulty=1,
            is_active=True,
        )
        session.add(existing)
        session.flush()
        return existing

    existing.options = options
    existing.correct_answer = correct_answer
    existing.is_active = True
    session.flush()
    return existing


def run_seed(config: SeedConfig, image_path: Path | None = None) -> None:
    engine = create_engine(config.database_url, pool_pre_ping=True)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    files_to_process = []
    if config.seed_path.is_file():
        files_to_process.append(config.seed_path)
    elif config.seed_path.is_dir():
        files_to_process.extend(sorted(config.seed_path.glob("*.json")))
        files_to_process.extend(sorted(config.seed_path.glob("*.md")))
    else:
        print(f"Warning: Seed path {config.seed_path} not found.")
        return

    # Load image map
    image_map = {}
    if image_path:
        image_map = scan_images(image_path)

    all_items = []
    for file_path in files_to_process:
        try:
            items = process_file(file_path)
            all_items.extend(items)
            print(f"Loaded {len(items)} items from {file_path}")
        except Exception as e:
            print(f"Error processing {file_path}: {e}")

    with SessionLocal() as session:
        for badge in DEFAULT_BADGES:
            upsert_badge(
                session,
                slug=str(badge["slug"]),
                name=str(badge["name"]),
                name_en=(str(badge["name_en"]) if badge.get("name_en") else None),
                description=(str(badge["description"]) if badge.get("description") else None),
                icon_url=str(badge["icon_url"]),
                category=badge["category"],
                xp_bonus=int(badge.get("xp_bonus") or 0),
                unlock_criteria=badge.get("unlock_criteria") or {},
                is_secret=bool(badge.get("is_secret") or False),
            )

        for idx, item in enumerate(all_items, start=1):
            urn_name = str(item["urn_location"])
            urn = upsert_urn(session, name=urn_name, model_base_url=config.model_base_url)

            mesh_name = str(item["3d_mesh_id"])
            name_vi = str(item["name_vi"])

            # Prefer explicit thumbnail_url from seed; otherwise resolve via scanned images.
            thumbnail_url_raw = item.get("thumbnail_url")
            thumbnail_url = str(thumbnail_url_raw).strip() if isinstance(thumbnail_url_raw, str) else None
            if not thumbnail_url and image_map:
                thumbnail_url = resolve_thumbnail_url(image_map, urn_slug=urn.slug, name_vi=name_vi)
                if not thumbnail_url:
                    print(f"Warning: No thumbnail match for urn={urn.slug!r} motif={name_vi!r}")

            display_order = parse_display_order(item.get("id")) or idx

            motif = upsert_motif(
                session,
                urn=urn,
                mesh_name=mesh_name,
                name_vi=name_vi,
                name_en=item.get("name_en"),
                category=MotifCategory.thao_moc,
                rarity=MotifRarity.common,
                display_order=display_order,
                thumbnail_url=thumbnail_url,
            )

            description_short = item.get("description_short")
            description_educational = item.get("description_educational") or description_short
            if not description_educational:
                print(f"Warning: Missing description for motif mesh_name={mesh_name!r}")
                continue

            upsert_lesson(
                session,
                motif=motif,
                intro_text=description_short,
                description=str(description_educational),
            )

            quiz = item.get("quiz_question")
            if isinstance(quiz, dict):
                question_text = quiz.get("question")
                correct_answer = quiz.get("correct_answer")
                if not question_text or not correct_answer:
                    print(f"Warning: Invalid quiz_question for motif mesh_name={mesh_name!r}")
                    continue
                options = quiz.get("options")
                if options is not None and not isinstance(options, list):
                    print(f"Warning: Invalid quiz_question.options for motif mesh_name={mesh_name!r}")
                    continue
                upsert_quiz_question(
                    session,
                    motif=motif,
                    question_text=str(question_text),
                    options=options,
                    correct_answer=str(correct_answer),
                )

        session.commit()


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed Luuniensuki PostgreSQL database from JSON/Markdown files")
    parser.add_argument(
        "--seed-path",
        default="data",
        help="Path to a file or directory containing seed data (JSON or Markdown)",
    )
    parser.add_argument(
        "--image-path",
        default="ban-duc-noi",
        help="Path to the directory containing embossed images (e.g., ban-duc-noi)",
    )
    args = parser.parse_args()

    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://postgres:postgres@localhost:5432/luuniensuki",
    )
    model_base_url = os.getenv("MODEL_BASE_URL", "/assets/models")

    run_seed(
        SeedConfig(
            database_url=database_url,
            seed_path=Path(args.seed_path),
            model_base_url=model_base_url,
        ),
        image_path=Path(args.image_path) if args.image_path else None
    )


if __name__ == "__main__":
    main()
```

---

## 4) Core APIs — `backend/main.py`

Required endpoints:

- `GET /motifs/{urn_name}`: returns all motifs for the urn (accepts either `slug` like `cao-dinh` or exact `name` like `Cao Đỉnh`).
- `POST /progress/unlock`: validates a user unlock interaction (mesh match + optional tap position distance check) and upserts `user_progress`.

```python
from __future__ import annotations

import logging
import math
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import Depends
from fastapi import FastAPI
from fastapi import HTTPException
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import model_validator
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict
from sqlalchemy import create_engine
from sqlalchemy import func
from sqlalchemy import or_
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import selectinload

from .models import Motif
from .models import UnlockStatus
from .models import Urn
from .models import User
from .models import UserProgress


DISCOVERY_XP = 25


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://postgres:postgres@db:5432/luuniensuki"
    log_level: str = "info"
    interaction_tolerance_multiplier: float = 1.25

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))
logger = logging.getLogger("luuniensuki.api")


engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


app = FastAPI(title="Luuniensuki API", version="0.1.0")


class UrnOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    slug: str
    name: str


class MotifOut(BaseModel):
    id: UUID
    urn_id: UUID
    mesh_name: str
    name: str
    name_en: Optional[str] = None
    category: str
    rarity: str
    pos_x: float
    pos_y: float
    pos_z: float
    bounding_radius: float
    thumbnail_url: Optional[str] = None
    silhouette_url: Optional[str] = None
    is_demo: bool
    display_order: Optional[int] = None
    lesson_intro: Optional[str] = None


class MotifsByUrnResponse(BaseModel):
    urn: UrnOut
    motifs: list[MotifOut]


@app.get("/motifs/{urn_name}", response_model=MotifsByUrnResponse)
def get_motifs_by_urn(urn_name: str, db: Session = Depends(get_db)) -> MotifsByUrnResponse:
    urn = db.execute(
        select(Urn).where(or_(Urn.slug == urn_name, func.lower(Urn.name) == urn_name.lower()))
    ).scalar_one_or_none()
    if urn is None:
        raise HTTPException(status_code=404, detail="Urn not found")

    motifs = db.execute(
        select(Motif)
        .options(selectinload(Motif.lesson))
        .where(Motif.urn_id == urn.id, Motif.is_active.is_(True))
        .order_by(Motif.display_order.nulls_last(), Motif.name)
    ).scalars().all()

    return MotifsByUrnResponse(
        urn=UrnOut.model_validate(urn),
        motifs=[
            MotifOut(
                id=m.id,
                urn_id=m.urn_id,
                mesh_name=m.mesh_name,
                name=m.name,
                name_en=m.name_en,
                category=m.category.value,
                rarity=m.rarity.value,
                pos_x=m.pos_x,
                pos_y=m.pos_y,
                pos_z=m.pos_z,
                bounding_radius=m.bounding_radius,
                thumbnail_url=m.thumbnail_url,
                silhouette_url=m.silhouette_url,
                is_demo=m.is_demo,
                display_order=m.display_order,
                lesson_intro=(m.lesson.intro_text if m.lesson else None),
            )
            for m in motifs
        ],
    )


class TapPosition(BaseModel):
    x: float
    y: float
    z: float


class ProgressUnlockRequest(BaseModel):
    user_id: UUID
    motif_id: Optional[UUID] = None
    mesh_name: Optional[str] = None
    tap_position: Optional[TapPosition] = None

    @model_validator(mode="after")
    def _validate_reference(self) -> "ProgressUnlockRequest":
        if self.motif_id is None and not self.mesh_name:
            raise ValueError("Either motif_id or mesh_name is required.")
        return self


class ProgressUnlockResponse(BaseModel):
    user_id: UUID
    motif_id: UUID
    status: str
    discovered_at: Optional[datetime] = None
    xp_awarded: int
    total_xp: int


@app.post("/progress/unlock", response_model=ProgressUnlockResponse)
def unlock_progress(payload: ProgressUnlockRequest, db: Session = Depends(get_db)) -> ProgressUnlockResponse:
    user = db.get(User, payload.user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if payload.motif_id is not None:
        motif = db.get(Motif, payload.motif_id)
    else:
        motif = db.execute(select(Motif).where(Motif.mesh_name == payload.mesh_name)).scalar_one_or_none()

    if motif is None:
        raise HTTPException(status_code=404, detail="Motif not found")

    if payload.mesh_name is not None and motif.mesh_name != payload.mesh_name:
        raise HTTPException(status_code=400, detail="mesh_name does not match motif")

    if user.role.value == "guest" and not motif.is_demo:
        raise HTTPException(status_code=403, detail="Guests can only unlock demo motifs")

    if payload.tap_position is not None and motif.bounding_radius > 0:
        dx = payload.tap_position.x - motif.pos_x
        dy = payload.tap_position.y - motif.pos_y
        dz = payload.tap_position.z - motif.pos_z
        distance = math.sqrt(dx * dx + dy * dy + dz * dz)
        allowed = motif.bounding_radius * settings.interaction_tolerance_multiplier
        if distance > allowed:
            raise HTTPException(status_code=400, detail="Tap position outside bounding radius")

    now = datetime.now(timezone.utc)

    progress = db.execute(
        select(UserProgress).where(UserProgress.user_id == user.id, UserProgress.motif_id == motif.id)
    ).scalar_one_or_none()

    xp_awarded = 0
    if progress is None:
        progress = UserProgress(
            user_id=user.id,
            motif_id=motif.id,
            status=UnlockStatus.discovered,
            discovered_at=now,
            xp_earned=DISCOVERY_XP,
        )
        db.add(progress)
        user.total_xp += DISCOVERY_XP
        xp_awarded = DISCOVERY_XP
    else:
        if progress.status == UnlockStatus.hidden:
            progress.status = UnlockStatus.discovered
            progress.discovered_at = progress.discovered_at or now

        if progress.xp_earned < DISCOVERY_XP:
            delta = DISCOVERY_XP - progress.xp_earned
            progress.xp_earned = DISCOVERY_XP
            user.total_xp += delta
            xp_awarded = delta

    user.last_active_at = now

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        logger.warning("IntegrityError during unlock; retrying fetch/update", exc_info=True)
        progress = db.execute(
            select(UserProgress).where(UserProgress.user_id == user.id, UserProgress.motif_id == motif.id)
        ).scalar_one()
        if progress.status == UnlockStatus.hidden:
            progress.status = UnlockStatus.discovered
            progress.discovered_at = progress.discovered_at or now
        if progress.xp_earned < DISCOVERY_XP:
            delta = DISCOVERY_XP - progress.xp_earned
            progress.xp_earned = DISCOVERY_XP
            user.total_xp += delta
            xp_awarded = max(xp_awarded, delta)
        user.last_active_at = now
        db.commit()

    return ProgressUnlockResponse(
        user_id=user.id,
        motif_id=motif.id,
        status=progress.status.value,
        discovered_at=progress.discovered_at,
        xp_awarded=xp_awarded,
        total_xp=user.total_xp,
    )
```

---

## Quickstart (Local / Server)

1) Start services:

```bash
docker compose up -d --build
```

2) Seed the DB (from `docs/architecture/02_Content_Seed.md`):

```bash
docker compose run --rm api python -m backend.seed
```

3) Create a user (required for `POST /progress/unlock`):

```bash
docker compose exec db psql -U ${POSTGRES_USER:-postgres} -d ${POSTGRES_DB:-luuniensuki} \
  -c "INSERT INTO users (email, password_hash, display_name) VALUES ('dev@example.com','dev-only','Dev User') RETURNING id;"
```

4) Try the APIs:

```bash
curl -s http://localhost:8000/motifs/cao-dinh | jq .
```

```bash
curl -s -X POST http://localhost:8000/progress/unlock \
  -H 'content-type: application/json' \
  -d '{"user_id":"<UUID_FROM_STEP_3>","mesh_name":"mesh_urn_cao_lotus_v1"}' | jq .
```

---

## Production Notes (Server + Domain)

- DNS: point `lms.histolab.icu` (A record) → `160.30.113.189`.
- Security: do not expose Postgres publicly; remove the `db` ports mapping or bind it to `127.0.0.1`.
- Reverse proxy: put Nginx/Caddy in front of `api:8000` and terminate TLS (Let’s Encrypt).
- Migrations: for production, add Alembic migrations instead of relying on `Base.metadata.create_all`.
