# -*- coding: utf-8 -*-
from __future__ import annotations

import hashlib
import json
import logging
import math
import re
import secrets
import time
import unicodedata
import uuid as uuid_module
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator, Optional, Sequence
from urllib.error import HTTPError, URLError
from urllib.request import Request as UrlRequest
from urllib.request import urlopen
from uuid import UUID

from fastapi import (
    Depends,
    FastAPI,
    File,
    HTTPException,
    Query,
    Request,
    Response,
    UploadFile,
    status,
)
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.security import OAuth2PasswordBearer
from fastapi.staticfiles import StaticFiles
from jose import JWTError, jwt
from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator
from sqlalchemy import and_, case, create_engine, delete, func, or_, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, selectinload, sessionmaker
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.cors import CORSMiddleware

from . import schemas

# Importing config instantiates Settings via get_settings(), which runs the
# fail-closed @model_validator. This import therefore performs production
# security validation (e.g. rejecting sentinel JWT secrets or wildcard CORS
# with credentials) BEFORE the SQLAlchemy engine and FastAPI app are built
# below. See Requirements 1.1 and 28.2. (get_settings is imported so the
# ordering can be reasserted explicitly right before engine construction.)
from .config import get_settings, settings
from .errors import (
    AppError,
    app_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from .models import (
    AbuseReport,
    AIConversation,
    AIJob,
    AIMessage,
    AnalyticsEvent,
    AppVersion,
    AssignmentProgress,
    Badge,
    BadgeCategory,
    Certificate,
    ClassMember,
    Classroom,
    ContentFlag,
    ContentProvenance,
    ContentRating,
    ContentStatus,
    ContentTag,
    ContentType,
    ContentVersion,
    CrashReport,
    DailyMission,
    EmailStatus,
    EmailTemplate,
    EmbeddingJob,
    ErrorType,
    Experiment,
    ExperimentEvent,
    ExperimentMetricEvent,
    FeatureFlag,
    FlagType,
    FriendRequest,
    FriendRequestStatus,
    GuestPreview,
    HeartTransaction,
    HeartTransactionReason,
    LessonCache,
    LessonContent,
    LessonPrerequisite,
    MilestoneType,
    MissionType,
    Motif,
    MotifCategory,
    NotificationStatus,
    NotificationType,
    PushNotification,
    Quest,
    QuestAssignment,
    QuestCategory,
    QuestionType,
    QuestObjective,
    QuestProgress,
    QuestReward,
    QuestStep,
    QuizAttempt,
    QuizQuestion,
    RagDocument,
    RagSettings,
    Recommendation,
    RevokedRefreshToken,
    ScheduledEmail,
    SkillType,
    SpacedRepetitionCard,
    StreakReward,
    Tag,
    TagType,
    UnlockStatus,
    Urn,
    UrnExam,
    UrnExamAttempt,
    User,
    UserBadge,
    UserDailyMission,
    UserExperimentAssignment,
    UserFollow,
    UserHearts,
    UserLearningPath,
    UserMilestone,
    UserNotificationSettings,
    UserProgress,
    UserRole,
    UserSession,
    UserShare,
    UserSkillLevel,
    UserWeeklyQuest,
    WeeklyQuest,
)
from .rag_defaults import get_rag_defaults
from .rbac import ADMIN_ROLES, STAFF_ROLES
from .security import create_jwt_token, hash_password, verify_password

DISCOVERY_XP = 25
LESSON_XP = 50
MASTERED_XP = 75
QUIZ_PASS_PERCENT = 80
URN_EXAM_PASS_PERCENT = 80
URN_EXAM_PASS_XP = 300
URN_EXAM_QUESTION_COUNT = 15
CERTIFICATE_ISSUER_NAME = "Lưu Niên Sử Kí"

USERNAME_REGEX = re.compile(r"^[a-zA-Z0-9_]{3,20}$")

AVATAR_DIR = Path(settings.avatar_dir).resolve()
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_AVATAR_SIZE = 5 * 1024 * 1024
RAG_ALLOWED_FILE_TYPES = {"text/plain", "text/markdown", "application/json"}

IMAGE_EXTENSION_BY_TYPE = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}


def _detect_image_type(contents: bytes) -> Optional[str]:
    """Determine the true image MIME type from file content.

    Returns one of the ``image/*`` strings in ``IMAGE_EXTENSION_BY_TYPE`` when the
    bytes parse as a supported image, otherwise ``None``. Detection prefers Pillow
    (validating the bytes actually decode) and falls back to a magic-byte sniff when
    Pillow is unavailable.
    """
    if not contents:
        return None

    # Prefer Pillow if it is installed: it actually parses the image.
    try:
        import io as _io

        from PIL import Image as _Image  # type: ignore

        try:
            img = _Image.open(_io.BytesIO(contents))
            img.verify()
            fmt = (img.format or "").upper()
        except Exception:
            return None
        return {
            "JPEG": "image/jpeg",
            "PNG": "image/png",
            "WEBP": "image/webp",
        }.get(fmt)
    except ImportError:
        pass

    # Fallback: magic-byte sniffing.
    if contents.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if contents.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if (
        len(contents) >= 12
        and contents[0:4] == b"RIFF"
        and contents[8:12] == b"WEBP"
    ):
        return "image/webp"
    return None

BADGE_FIRST_DISCOVERY = "first-discovery"
BADGE_FIRST_MASTERED = "first-mastered"
BADGE_STREAK_7 = "streak-7"
BADGE_STREAK_30 = "streak-30-days"
BADGE_STREAK_100 = "streak-100-days"
BADGE_COLLECTOR_10 = "collector-10"
BADGE_COLLECTOR_50 = "collector-50"
BADGE_EXPLORER_ALL_URNS = "explorer-all-urns"
BADGE_QUIZ_MASTER = "quiz-master"
BADGE_SPEED_DEMON = "speed-demon"
BADGE_PERFECT_SCORE = "perfect-score"
BADGE_EARLY_BIRD = "early-bird"

XP_RANKS = [
    {"level": 1, "name": "Lính Mới", "xp": 0},
    {"level": 2, "name": "Thư Sinh", "xp": 500},
    {"level": 3, "name": "Tú Tài", "xp": 1500},
    {"level": 4, "name": "Cử Nhân", "xp": 3500},
    {"level": 5, "name": "Tiến Sĩ", "xp": 7000},
    {"level": 6, "name": "Thám Hoa", "xp": 12000},
    {"level": 7, "name": "Bảng Nhãn", "xp": 20000},
    {"level": 8, "name": "Trạng Nguyên", "xp": 35000},
    {"level": 9, "name": "Hàn Lâm", "xp": 55000},
    {"level": 10, "name": "Sử Quan", "xp": 80000},
]

DAILY_GOAL_LEVELS: dict[str, int] = {
    "CASUAL": 10,
    "REGULAR": 20,
    "SERIOUS": 30,
    "INTENSE": 50,
    "INSANE": 100,
}
DAILY_GOAL_DEFAULT_LEVEL = "REGULAR"

SEED_DATA_FILES = {
    "cao-dinh": "05_Data_CaoDinh.json",
    "nhan-dinh": "06_Data_NhanDinh.json",
    "chuong-dinh": "07_Data_ChuongDinh.json",
    "anh-dinh": "08_Data_AnhDinh.json",
    "nghi-dinh": "09_Data_NghiDinh.json",
    "thuan-dinh": "10_Data_ThuanDinh.json",
    "tuyen-dinh": "11_Data_TuyenDinh.json",
    "du-dinh": "12_Data_DuDinh.json",
    "huyen-dinh": "13_Data_HuyenDinh.json",
}

REPO_ROOT = Path(__file__).resolve().parents[1]
SEED_DATA_DIR = REPO_ROOT / "data"
_SEED_CACHE: dict[str, list[dict[str, Any]]] = {}

CUU_DINH_CONTEXT = (
    "Cửu Đỉnh là chín đỉnh đồng lớn đặt tại Hoàng thành Huế, "
    "được vua Minh Mạng cho đúc giai đoạn 1835-1837. "
    "Mỗi đỉnh mang tên thụy hiệu của các vị vua triều Nguyễn và "
    "khắc họa hàng trăm hình tượng núi sông, cây cỏ, chim thú, "
    "thủy hệ và khí vật tiêu biểu của đất nước. "
    'Cửu Đỉnh vừa là biểu tượng quyền lực quốc gia, vừa là bộ "bách khoa" '
    "về địa lý - văn hóa Việt Nam thế kỷ XIX."
)


logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))
logger = logging.getLogger("luuniensuki.api")


# Re-assert fail-closed configuration validation explicitly and intentionally
# before any infrastructure is constructed. get_settings() is @lru_cache-d, so
# this returns the already-validated instance (or raises a fatal RuntimeError
# if production security checks fail) without re-running side effects. This
# guarantees validation-before-construction ordering (Requirements 1.1, 28.2).
get_settings()

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Content-Security-Policy applied to all responses (Requirements 25.1, 25.3).
# This service is primarily a JSON API that also serves a static "/assets"
# mount, so a conservative self-only policy is appropriate. Keep this as a
# module-level constant so the policy is easy to review and tune in one place.
CONTENT_SECURITY_POLICY = (
    "default-src 'self'; frame-ancestors 'none'; object-src 'none'"
)

app = FastAPI(title="Luuniensuki API", version="0.1.0")
app.add_exception_handler(AppError, app_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

# Add CORS middleware to allow cross-origin requests from mobile app.
#
# Defense-in-depth (Requirements 3.2, 3.3, 3.4): the config-level validator
# (config.py @model_validator) already halts production startup if credentials
# are combined with a wildcard origin. Here we add a second, non-breaking guard
# at the middleware wiring so the browser-incompatible "reflect any origin while
# allowing credentials" behavior can never be configured, even outside
# production. When credentials are requested together with a "*" wildcard, we
# disable credentials (keeping the wildcard) and log a warning; otherwise we
# pass the validated allowlist and credential setting through unchanged.
cors_origins = settings.cors_origins_list
cors_allow_credentials = settings.cors_allow_credentials
if cors_allow_credentials and "*" in cors_origins:
    logger.warning(
        "CORS is configured with allow_credentials=True and a wildcard '*' origin; "
        "disabling credentials for CORS because reflecting any origin with "
        "credentials is unsafe and not honored by browsers. Configure an explicit "
        "origin allowlist to enable credentialed cross-origin requests."
    )
    cors_allow_credentials = False

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Inject standard security headers on every response (Requirements 25.1, 25.3).

    Adds Content-Security-Policy, Strict-Transport-Security, and
    X-Content-Type-Options uniformly across all routes. HSTS is only meaningful
    over HTTPS but is safe to always send. A header that a specific endpoint has
    already set is preserved and never overwritten.
    """
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault(
        "Strict-Transport-Security", "max-age=31536000; includeSubDomains"
    )
    response.headers.setdefault("Content-Security-Policy", CONTENT_SECURITY_POLICY)
    return response

# In-process fixed-window rate limiter for authentication endpoints
# (Requirements 12.1-12.4). Driven by the existing rate_limit_* settings:
# up to `rate_limit_requests_per_minute + rate_limit_burst` requests are
# allowed per 60-second window, keyed by client IP. Over-limit requests get
# an HTTP 429 with a standard error envelope and a Retry-After header.
#
# NOTE: This state is per-process. With multiple workers each process keeps its
# own counters, so the effective global limit scales with the worker count.
# A shared store (e.g. Redis) would be required for a cluster-wide limit.
_AUTH_RATE_LIMIT_WINDOW_SECONDS = 60
# Maps client key -> (window_start_epoch, count).
_auth_rate_limit_state: dict[str, tuple[float, int]] = {}


def _auth_rate_limit_key(request: Request) -> str:
    """Derive the rate-limit key for a request from the client IP.

    Honors the first hop of X-Forwarded-For when present (the original client
    behind a trusted proxy); otherwise falls back to the direct peer address.
    """
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        first_hop = forwarded.split(",")[0].strip()
        if first_hop:
            return first_hop
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


@app.middleware("http")
async def rate_limit_auth_endpoints(request: Request, call_next):
    """Apply a fixed 60s-window rate limit to /api/v1/auth/* (Req 12.1-12.4).

    Non-auth paths pass through untouched. For auth paths, requests beyond
    `rate_limit_requests_per_minute + rate_limit_burst` within the current
    window are rejected with HTTP 429.
    """
    if not request.url.path.startswith("/api/v1/auth/"):
        return await call_next(request)

    limit = settings.rate_limit_requests_per_minute + settings.rate_limit_burst
    key = _auth_rate_limit_key(request)
    now = time.time()

    window_start, count = _auth_rate_limit_state.get(key, (now, 0))
    if now - window_start >= _AUTH_RATE_LIMIT_WINDOW_SECONDS:
        # Window expired; start a fresh one.
        window_start, count = now, 0

    if count >= limit:
        retry_after = max(
            1,
            int(_AUTH_RATE_LIMIT_WINDOW_SECONDS - (now - window_start)),
        )
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error": {
                    "code": "RATE_LIMITED",
                    "message": "Too many requests",
                    "details": {},
                }
            },
            headers={"Retry-After": str(retry_after)},
        )

    _auth_rate_limit_state[key] = (window_start, count + 1)
    return await call_next(request)

# Mount static files for assets (motif images, avatars, etc.)
ASSETS_DIR = Path(__file__).parent / "assets"
if ASSETS_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(ASSETS_DIR)), name="assets")
else:
    logger.warning(f"Assets directory not found: {ASSETS_DIR}")

# Serve uploaded avatars from the single configured avatar directory so the
# stored file and the served URL resolve to the same location (Req 11.1-11.3).
# The directory must exist before StaticFiles is mounted.
AVATAR_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads/avatars", StaticFiles(directory=str(AVATAR_DIR)), name="avatars")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def _compute_rank(total_xp: int) -> tuple[dict, Optional[dict], int]:
    current = XP_RANKS[0]
    for r in XP_RANKS:
        if total_xp >= r["xp"]:
            current = r
        else:
            break

    next_rank = None
    for r in XP_RANKS:
        if r["xp"] > current["xp"]:
            next_rank = r
            break

    if next_rank is None:
        return current, None, 0
    return current, next_rank, max(0, next_rank["xp"] - total_xp)


def _update_streak(user: User, now: datetime) -> None:
    if user.last_active_at is None:
        user.current_streak = max(user.current_streak, 1)
        user.longest_streak = max(user.longest_streak, user.current_streak)
        return

    last_date = user.last_active_at.astimezone(timezone.utc).date()
    today = now.astimezone(timezone.utc).date()
    diff_days = (today - last_date).days
    if diff_days <= 0:
        return

    if diff_days == 1:
        user.current_streak += 1
    else:
        user.current_streak = 1

    user.longest_streak = max(user.longest_streak, user.current_streak)


def _record_analytics_event(
    session: Session,
    *,
    user_id: UUID,
    name: str,
    payload: Optional[dict[str, Any]] = None,
    path: Optional[str] = None,
    session_id: Optional[UUID] = None,
    cohort: Optional[str] = None,
    device_info: Optional[dict[str, Any]] = None,
) -> None:
    try:
        from services.analytics import create_event_record

        event_data = create_event_record(
            user_id=user_id,
            event_name=name,
            payload=payload,
            path=path,
            session_id=session_id,
            cohort=cohort,
            device_info=device_info,
        )
        # Persist the analytics event using a dedicated short-lived session so
        # the request-shared `session` is never committed here. Committing the
        # shared session would prematurely persist any other pending mutations
        # and break the surrounding request's transaction atomicity
        # (Requirements 19.1, 19.2, 19.3).
        with SessionLocal() as analytics_session:
            analytics_session.add(AnalyticsEvent(**event_data))
            analytics_session.commit()
    except Exception:
        logger.warning("Failed to record analytics event", exc_info=True)


def _apply_xp_boost(user: User, base_xp: int, now: datetime) -> int:
    """
    Apply XP boost multiplier if active and not expired.

    Args:
        user: The user object
        base_xp: The base XP amount to be multiplied
        now: Current datetime

    Returns:
        The final XP amount (base_xp or base_xp * multiplier)
    """
    try:
        if not user.xp_boost_active:
            return base_xp

        if user.xp_boost_expires_at is None:
            # Boost active but no expiration set - deactivate it
            user.xp_boost_active = False
            return base_xp

        # Check if boost has expired
        if now >= user.xp_boost_expires_at:
            user.xp_boost_active = False
            user.xp_boost_expires_at = None
            return base_xp

        # Boost is active - apply multiplier. Coerce a null/unset multiplier to
        # the neutral value so that `None > 1` cannot raise a TypeError.
        multiplier = user.xp_boost_multiplier or 0
        return base_xp * (multiplier if multiplier > 1 else 2)
    except Exception:
        # XP application must never raise (Req 9.4) - fall back to base XP.
        logger.warning(
            "Failed to apply XP boost; falling back to base XP",
            extra={"user_id": str(getattr(user, "id", None))},
        )
        return base_xp


def _award_badge(session: Session, *, user: User, badge_slug: str) -> int:
    badge = session.execute(
        select(Badge).where(Badge.slug == badge_slug, Badge.is_active.is_(True))
    ).scalar_one_or_none()
    if badge is None:
        return 0

    existing = session.execute(
        select(UserBadge).where(
            UserBadge.user_id == user.id, UserBadge.badge_id == badge.id
        )
    ).scalar_one_or_none()
    if existing is not None:
        return 0

    try:
        with session.begin_nested():
            insert_stmt = (
                pg_insert(UserBadge)
                .values(user_id=user.id, badge_id=badge.id)
                .on_conflict_do_nothing(
                    index_elements=["user_id", "badge_id"],
                )
                .returning(UserBadge.id)
            )
            inserted = session.execute(insert_stmt).scalar_one_or_none()
    except Exception:
        logger.warning(
            "Failed to award badge",
            extra={"user_id": str(user.id), "badge_slug": badge_slug},
            exc_info=True,
        )
        return 0
    if inserted is None:
        return 0

    # Track first badge earned milestone
    badges_before = session.execute(
        select(func.count(UserBadge.id)).where(UserBadge.user_id == user.id)
    ).scalar_one()
    if badges_before <= 1:  # First badge (just inserted)
        from backend.services.milestones import check_and_create_first_badge_earned

        check_and_create_first_badge_earned(session, user.id, badge_slug)

    bonus = int(badge.xp_bonus or 0)
    if bonus:
        user.total_xp += bonus
    return bonus


def _issue_certificate(
    session: Session,
    *,
    user_id: UUID,
    reason_type: str,
    reason_id: UUID,
    issuer_name: str = CERTIFICATE_ISSUER_NAME,
) -> Certificate:
    existing = session.execute(
        select(Certificate).where(
            Certificate.user_id == user_id,
            Certificate.reason_type == reason_type,
            Certificate.reason_id == reason_id,
        )
    ).scalar_one_or_none()
    if existing is not None:
        return existing

    code = uuid_module.uuid4().hex
    certificate = Certificate(
        user_id=user_id,
        code=code,
        issuer_name=issuer_name,
        reason_type=reason_type,
        reason_id=reason_id,
        status="issued",
    )
    session.add(certificate)
    session.flush()
    return certificate


def _normalize_category(raw: Any) -> Optional[MotifCategory]:
    if raw is None:
        return None
    value = str(raw).strip().lower().replace("-", "_")
    if not value:
        return None
    try:
        return MotifCategory(value)
    except ValueError:
        return None


def _objective_current_value(
    session: Session, *, user: User, objective: QuestObjective
) -> int:
    params = objective.params if isinstance(objective.params, dict) else {}
    objective_type = str(objective.objective_type or "").strip()

    if objective_type == "discover_category":
        category = _normalize_category(params.get("category"))
        if category is None:
            return 0
        return session.execute(
            select(func.count(UserProgress.id))
            .join(Motif, UserProgress.motif_id == Motif.id)
            .where(
                UserProgress.user_id == user.id,
                UserProgress.status != UnlockStatus.hidden,
                Motif.category == category,
            )
        ).scalar_one()

    if objective_type == "master_category":
        category = _normalize_category(params.get("category"))
        if category is None:
            return 0
        return session.execute(
            select(func.count(UserProgress.id))
            .join(Motif, UserProgress.motif_id == Motif.id)
            .where(
                UserProgress.user_id == user.id,
                UserProgress.status == UnlockStatus.mastered,
                Motif.category == category,
            )
        ).scalar_one()

    if objective_type == "quiz_pass_count":
        category = _normalize_category(params.get("category"))
        query = (
            select(func.count(func.distinct(QuizAttempt.motif_id)))
            .select_from(QuizAttempt)
            .join(Motif, QuizAttempt.motif_id == Motif.id)
            .where(
                QuizAttempt.user_id == user.id,
                QuizAttempt.percentage >= QUIZ_PASS_PERCENT,
            )
        )
        if category is not None:
            query = query.where(Motif.category == category)
        return session.execute(query).scalar_one()

    if objective_type == "urn_exam_pass":
        urn_slug = params.get("urn_slug")
        query = (
            select(func.count(func.distinct(UrnExam.urn_id)))
            .select_from(UrnExamAttempt)
            .join(UrnExam, UrnExamAttempt.urn_exam_id == UrnExam.id)
            .where(UrnExamAttempt.user_id == user.id, UrnExamAttempt.passed.is_(True))
        )
        if urn_slug:
            query = query.join(Urn, UrnExam.urn_id == Urn.id).where(
                Urn.slug == urn_slug
            )
        return session.execute(query).scalar_one()

    if objective_type == "discover_motifs":
        motif_ids = params.get("motif_ids")
        if not isinstance(motif_ids, list) or not motif_ids:
            return 0
        return session.execute(
            select(func.count(UserProgress.id)).where(
                UserProgress.user_id == user.id,
                UserProgress.status != UnlockStatus.hidden,
                UserProgress.motif_id.in_(motif_ids),
            )
        ).scalar_one()

    return 0


def _build_objective_progress(
    session: Session,
    *,
    user: User,
    objective: QuestObjective,
    force_complete: bool,
) -> dict[str, Any]:
    target_value = max(1, int(objective.target_value or 1))
    if force_complete:
        current_value = target_value
    else:
        current_value = int(
            _objective_current_value(session, user=user, objective=objective)
        )
    ratio = min(current_value, target_value) / target_value if target_value else 1.0
    return {
        "id": objective.id,
        "objective_type": objective.objective_type,
        "target_value": target_value,
        "current_value": current_value,
        "is_complete": current_value >= target_value,
        "params": objective.params if isinstance(objective.params, dict) else None,
        "ratio": ratio,
    }


def _compute_quest_progress_data(
    session: Session,
    *,
    user: User,
    quest: Quest,
    progress_entry: Optional[QuestProgress],
) -> tuple[list[dict[str, Any]], float]:
    force_complete = progress_entry is not None and progress_entry.status == "completed"
    all_objectives: list[dict[str, Any]] = []
    steps_payload: list[dict[str, Any]] = []

    for step in sorted(quest.steps, key=lambda s: (s.display_order or 0, s.created_at)):
        objectives = [
            _build_objective_progress(
                session, user=user, objective=obj, force_complete=force_complete
            )
            for obj in sorted(
                step.objectives, key=lambda o: (o.display_order or 0, o.id)
            )
        ]
        step_ratio = (
            sum(obj["ratio"] for obj in objectives) / len(objectives)
            if objectives
            else 0.0
        )
        steps_payload.append(
            {
                "id": step.id,
                "title": step.title,
                "description": step.description,
                "display_order": int(step.display_order or 0),
                "objectives": objectives,
                "completion_percent": round(step_ratio * 100, 1),
            }
        )
        all_objectives.extend(objectives)

    quest_ratio = (
        sum(obj["ratio"] for obj in all_objectives) / len(all_objectives)
        if all_objectives
        else 0.0
    )
    return steps_payload, round(quest_ratio * 100, 1)


def _apply_quest_rewards(
    session: Session,
    *,
    user: User,
    quest: Quest,
    progress_entry: QuestProgress,
) -> tuple[int, list[str], Optional[Certificate]]:
    now = datetime.now(timezone.utc)
    xp_awarded = 0
    badges_awarded: list[str] = []

    for reward in quest.rewards:
        reward_type = str(reward.reward_type or "").strip().lower()
        if reward_type == "xp":
            amount = int(reward.amount or 0)
            if amount > 0:
                user.total_xp += amount
                xp_awarded += amount
        elif reward_type == "badge":
            if reward.badge_slug:
                bonus = _award_badge(session, user=user, badge_slug=reward.badge_slug)
                if bonus:
                    xp_awarded += bonus
                badges_awarded.append(reward.badge_slug)
        elif reward_type == "streak_freeze":
            amount = int(reward.amount or 1)
            if amount > 0:
                user.streak_freezes += amount

    progress_entry.status = "completed"
    progress_entry.completed_at = progress_entry.completed_at or now

    certificate = _issue_certificate(
        session,
        user_id=user.id,
        reason_type="quest",
        reason_id=quest.id,
    )

    assignments = (
        session.execute(
            select(QuestAssignment)
            .join(ClassMember, QuestAssignment.class_id == ClassMember.class_id)
            .where(
                QuestAssignment.quest_id == quest.id,
                ClassMember.user_id == user.id,
            )
        )
        .scalars()
        .all()
    )
    for assignment in assignments:
        progress = session.execute(
            select(AssignmentProgress).where(
                AssignmentProgress.assignment_id == assignment.id,
                AssignmentProgress.user_id == user.id,
            )
        ).scalar_one_or_none()
        if progress is None:
            session.add(
                AssignmentProgress(
                    assignment_id=assignment.id,
                    user_id=user.id,
                    status="completed",
                    completed_at=now,
                )
            )
        else:
            progress.status = "completed"
            progress.completed_at = progress.completed_at or now

    return xp_awarded, badges_awarded, certificate


def _count_user_discoveries(session: Session, user_id) -> tuple[int, int]:
    """Returns (total_discovered_motifs, distinct_urns_with_discoveries)"""
    from sqlalchemy import distinct, func

    discovered = session.execute(
        select(func.count(UserProgress.id)).where(
            UserProgress.user_id == user_id, UserProgress.status != UnlockStatus.hidden
        )
    ).scalar_one()
    urns = session.execute(
        select(func.count(distinct(Motif.urn_id)))
        .select_from(UserProgress)
        .join(Motif, UserProgress.motif_id == Motif.id)
        .where(
            UserProgress.user_id == user_id, UserProgress.status != UnlockStatus.hidden
        )
    ).scalar_one()
    return discovered, urns


def _cookie_params() -> dict[str, Any]:
    samesite = (settings.cookie_samesite or "lax").lower()
    if samesite not in {"lax", "strict", "none"}:
        samesite = "lax"
    params: dict[str, Any] = {
        "secure": settings.cookie_secure_effective,
        "samesite": samesite,
        "path": settings.cookie_path,
    }
    if settings.cookie_domain:
        params["domain"] = settings.cookie_domain
    return params


def _set_auth_cookies(
    response: Response, *, access_token: str, refresh_token: str
) -> None:
    params = _cookie_params()
    if settings.is_production and not params["secure"]:
        logger.warning(
            "Secure auth cookies are DISABLED in production because "
            "COOKIE_SECURE was explicitly overridden to a non-secure value; "
            "session credentials may be transmitted over plaintext connections."
        )
    access_max_age = int(settings.access_token_expire_minutes) * 60
    refresh_max_age = int(settings.refresh_token_expire_days) * 24 * 60 * 60
    response.set_cookie(
        settings.access_cookie_name,
        access_token,
        max_age=access_max_age,
        httponly=True,
        **params,
    )
    response.set_cookie(
        settings.refresh_cookie_name,
        refresh_token,
        max_age=refresh_max_age,
        httponly=True,
        **params,
    )


def _clear_auth_cookies(response: Response) -> None:
    params = _cookie_params()
    response.delete_cookie(settings.access_cookie_name, **params)
    response.delete_cookie(settings.refresh_cookie_name, **params)


def _jwt_decode_kwargs() -> dict[str, Any]:
    """Build keyword arguments for ``jose.jwt.decode``.

    Implements the issue-then-enforce transition for the ``iss``/``aud``
    identity claims (Req 26.4). When ``settings.jwt_validate_new_claims`` is
    False (the transition default), only ``exp`` is required and no
    issuer/audience is enforced, so tokens are accepted whether or not they
    carry ``iss``/``aud``. When True, both backends are known to issue the
    new claims, so ``iss``/``aud`` become required and are validated against
    the configured issuer/audience (jose raises ``JWTError`` on mismatch).
    """
    kwargs: dict[str, Any] = {"algorithms": [settings.jwt_algorithm]}
    if settings.jwt_validate_new_claims:
        kwargs["issuer"] = settings.jwt_issuer
        kwargs["audience"] = settings.jwt_audience
        kwargs["options"] = {"require": ["exp", "iss", "aud"]}
    else:
        kwargs["options"] = {"require": ["exp"]}
    return kwargs


def _decode_refresh_token_best_effort(raw_token: str) -> Optional[dict[str, Any]]:
    """Decode a refresh token tolerantly for revocation bookkeeping (Req 17.2).

    Requires ``exp`` so the revocation row's ``expires_at`` can be derived, but
    tolerates any decode failure by returning ``None`` — revocation is a
    best-effort side effect that must never break logout / password-change.
    Issuer/audience are intentionally not enforced here (and ``aud`` validation
    is disabled) so tokens carrying the new identity claims still decode while
    the issue-then-enforce transition (Task 6.4) is in progress.
    """
    try:
        return jwt.decode(
            raw_token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            options={"require": ["exp"], "verify_aud": False},
        )
    except (JWTError, ValueError):
        return None


def _revoke_refresh_jti(db: Session, payload: dict[str, Any]) -> None:
    """Persist a refresh token's ``jti`` as revoked (idempotent; Req 17.2).

    No-op when the payload lacks the claims needed to build a revocation row
    (e.g. tokens issued before ``jti`` was added in Task 6.3). Uses an
    ``ON CONFLICT DO NOTHING`` insert so repeated revocations of the same
    token (logout after password change, double logout) are harmless.
    """
    jti = payload.get("jti")
    subject = payload.get("sub")
    exp = payload.get("exp")
    if not jti or not subject or exp is None:
        return
    try:
        user_id = UUID(str(subject))
        expires_at = datetime.fromtimestamp(int(exp), tz=timezone.utc)
    except (TypeError, ValueError, OverflowError, OSError):
        return
    try:
        db.execute(
            pg_insert(RevokedRefreshToken)
            .values(jti=str(jti), user_id=user_id, expires_at=expires_at)
            .on_conflict_do_nothing(index_elements=["jti"])
        )
        db.commit()
    except SQLAlchemyError:
        # Best-effort: a failed revocation must not break the caller's flow.
        db.rollback()
        logger.warning("Failed to persist refresh-token revocation", exc_info=True)


def _is_refresh_revoked(db: Session, jti: Optional[str]) -> bool:
    """Return ``True`` if the given refresh-token ``jti`` has been revoked."""
    if not jti:
        return False
    return db.get(RevokedRefreshToken, str(jti)) is not None


def _decode_access_token(raw_token: str) -> Optional[UUID]:
    """Decode an access token and return its subject ``UUID``.

    Shared by ``get_current_user`` and ``get_current_user_optional`` to avoid
    duplicating the access-token decode (Req 18.3). Requires ``exp`` always;
    iss/aud enforcement is gated by the JWT_VALIDATE_NEW_CLAIMS transition
    flag (Req 26.4). Returns the subject ``UUID`` on success, or ``None`` on
    any failure (``JWTError``, ``ValueError``, missing/blank ``sub``, or a
    token whose ``type`` is not ``"access"``).
    """
    try:
        payload = jwt.decode(
            raw_token,
            settings.jwt_secret_key,
            **_jwt_decode_kwargs(),
        )
        subject = payload.get("sub")
        token_type = payload.get("type")
        if not subject or token_type != "access":
            return None
        return UUID(subject)
    except (JWTError, ValueError):
        return None


def get_current_user(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    raw_token = token or request.cookies.get(settings.access_cookie_name)
    if not raw_token:
        raise credentials_exception

    user_id = _decode_access_token(raw_token)
    if user_id is None:
        raise credentials_exception

    user = db.get(User, user_id)
    if user is None:
        raise credentials_exception
    return user


def get_current_user_optional(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """
    Get current user if authenticated, otherwise return None.
    Used for endpoints that are public but can show different data when authenticated.
    """
    raw_token = token or request.cookies.get(settings.access_cookie_name)
    if not raw_token:
        return None

    user_id = _decode_access_token(raw_token)
    if user_id is None:
        return None

    return db.get(User, user_id)


def _can_view_drafts(user: User) -> bool:
    return user.role in STAFF_ROLES


def _require_roles(roles: set[UserRole]):
    def _dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized"
            )
        return current_user

    return _dependency


def get_staff_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in STAFF_ROLES:
        raise HTTPException(status_code=403, detail="Not authorized")
    return current_user


def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Not authorized")
    return current_user


def _ensure_owner_or_404(resource_owner_id: UUID, current_user: User) -> None:
    """Object-level authorization guard (Req 20).

    Permit the operation only when the authenticated user owns the referenced
    resource or holds an admin role. For anyone else, raise a generic 404 so the
    response never discloses whether the resource exists (Req 20.2).
    """
    if current_user.id == resource_owner_id or current_user.role in ADMIN_ROLES:
        return
    raise HTTPException(status_code=404, detail="Not found")


# Alias for consistency with other endpoints
require_admin = get_admin_user


def get_super_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Require super_admin role for sensitive operations like audit logs."""
    if current_user.role != UserRole.super_admin:
        raise HTTPException(status_code=403, detail="Super admin access required")
    return current_user


def require_feature(feature_key: str):
    """
    Dependency factory to require a feature flag to be enabled for the current user.

    Usage:
        @app.get("/api/v1/new-feature")
        def new_feature_endpoint(
            current_user: User = Depends(require_feature("new_feature_flag")),
            db: Session = Depends(get_db),
        ):
            ...

    Args:
        feature_key: The feature flag key to check

    Returns:
        A dependency function that checks the feature flag
    """

    def _dependency(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> User:
        from backend.services import feature_flags

        if not feature_flags.is_feature_enabled_for_user(
            db, feature_key, current_user.id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Feature '{feature_key}' is not enabled for this user",
            )
        return current_user

    return _dependency


def get_user_age(user: User) -> Optional[int]:
    """Calculate user's current age from birth year."""
    if user.birth_year is None:
        return None
    current_year = datetime.now(timezone.utc).year
    return current_year - user.birth_year


def get_allowed_content_ratings(user: User) -> list[ContentRating]:
    """
    Determine which content ratings a user can access based on their age verification.

    Rules:
    - If user age not verified or under 13 → only 'everyone' content
    - If user age 13-17 → 'everyone' and 'teen' content
    - If user age 18+ → all content
    """
    if not user.age_verified:
        return [ContentRating.everyone]

    age = get_user_age(user)
    if age is None:
        return [ContentRating.everyone]

    if age < 13:
        return [ContentRating.everyone]
    elif age < 18:
        return [ContentRating.everyone, ContentRating.teen]
    else:
        return [ContentRating.everyone, ContentRating.teen, ContentRating.mature]


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    display_name: str
    avatar_url: Optional[str] = None
    username: Optional[str] = None
    role: str
    total_xp: int
    starting_urn_id: Optional[UUID] = None
    is_profile_public: bool
    ai_personalization_enabled: bool


class RankOut(BaseModel):
    level: int
    name: str
    xp: int


class UserStatsOut(BaseModel):
    total_xp: int
    rank: RankOut
    xp_to_next_rank: int
    next_rank: Optional[RankOut] = None


class AuthMeResponse(BaseModel):
    user: UserOut
    stats: UserStatsOut


def _build_auth_me_response(user: User) -> AuthMeResponse:
    current_rank, next_rank, xp_to_next = _compute_rank(user.total_xp)
    return AuthMeResponse(
        user=UserOut(
            id=user.id,
            email=user.email,
            display_name=user.display_name,
            avatar_url=user.avatar_url,
            username=user.username,
            role=user.role.value,
            total_xp=user.total_xp,
            starting_urn_id=user.starting_urn_id,
            is_profile_public=user.is_profile_public,
            ai_personalization_enabled=user.ai_personalization_enabled,
        ),
        stats=UserStatsOut(
            total_xp=user.total_xp,
            rank=RankOut(**current_rank),
            xp_to_next_rank=xp_to_next,
            next_rank=(RankOut(**next_rank) if next_rank else None),
        ),
    )


class AuthRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    display_name: str = Field(min_length=1, max_length=100)


class AuthLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=72)


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)


@app.post(
    "/api/v1/auth/register",
    response_model=AuthMeResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    payload: AuthRegisterRequest,
    response: Response,
    db: Session = Depends(get_db),
) -> AuthMeResponse:
    existing = db.execute(
        select(User).where(User.email == str(payload.email))
    ).scalar_one_or_none()
    if existing is not None:
        raise AppError(
            code="EMAIL_ALREADY_REGISTERED",
            message="Email already registered",
            status_code=status.HTTP_409_CONFLICT,
        )

    user = User(
        email=str(payload.email),
        password_hash="",
        display_name=payload.display_name,
    )
    try:
        user.password_hash = hash_password(payload.password)
    except ValueError:
        raise AppError(
            code="PASSWORD_TOO_LONG",
            message="Password too long",
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise AppError(
            code="EMAIL_ALREADY_REGISTERED",
            message="Email already registered",
            status_code=status.HTTP_409_CONFLICT,
        )

    db.refresh(user)

    access_token = create_jwt_token(
        subject=str(user.id),
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
        issuer=settings.jwt_issuer,
        audience=settings.jwt_audience,
        extra_claims={"type": "access"},
    )
    refresh_token = create_jwt_token(
        subject=str(user.id),
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        expires_delta=timedelta(days=settings.refresh_token_expire_days),
        issuer=settings.jwt_issuer,
        audience=settings.jwt_audience,
        extra_claims={"type": "refresh"},
    )

    _set_auth_cookies(response, access_token=access_token, refresh_token=refresh_token)
    response.headers["Cache-Control"] = "no-store"
    return _build_auth_me_response(user)


@app.post("/api/v1/auth/login", response_model=AuthMeResponse)
def login(
    payload: AuthLoginRequest, response: Response, db: Session = Depends(get_db)
) -> AuthMeResponse:
    user = db.execute(
        select(User).where(User.email == str(payload.email))
    ).scalar_one_or_none()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise AppError(
            code="INVALID_CREDENTIALS",
            message="Invalid email or password",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    access_token = create_jwt_token(
        subject=str(user.id),
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
        issuer=settings.jwt_issuer,
        audience=settings.jwt_audience,
        extra_claims={"type": "access"},
    )
    refresh_token = create_jwt_token(
        subject=str(user.id),
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        expires_delta=timedelta(days=settings.refresh_token_expire_days),
        issuer=settings.jwt_issuer,
        audience=settings.jwt_audience,
        extra_claims={"type": "refresh"},
    )

    _set_auth_cookies(response, access_token=access_token, refresh_token=refresh_token)
    response.headers["Cache-Control"] = "no-store"
    return _build_auth_me_response(user)


@app.get("/api/v1/auth/me", response_model=AuthMeResponse)
def me(current_user: User = Depends(get_current_user)) -> AuthMeResponse:
    return _build_auth_me_response(current_user)


@app.post("/api/v1/auth/refresh", response_model=AuthMeResponse)
def refresh_session(
    request: Request, response: Response, db: Session = Depends(get_db)
) -> AuthMeResponse:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    raw_token = request.cookies.get(settings.refresh_cookie_name)
    if not raw_token:
        raise credentials_exception

    try:
        # Require `exp` always; iss/aud enforcement is gated by the
        # JWT_VALIDATE_NEW_CLAIMS transition flag (Req 26.4).
        payload = jwt.decode(
            raw_token,
            settings.jwt_secret_key,
            **_jwt_decode_kwargs(),
        )
        subject = payload.get("sub")
        token_type = payload.get("type")
        if not subject or token_type != "refresh":
            raise credentials_exception
        user_id = UUID(subject)
    except (JWTError, ValueError):
        raise credentials_exception

    # Reject refresh tokens whose `jti` has been revoked (logout / password
    # change). Done after decoding and before issuing new tokens (Req 17.2).
    if _is_refresh_revoked(db, payload.get("jti")):
        raise credentials_exception

    user = db.get(User, user_id)
    if user is None:
        raise credentials_exception

    # Rotate: revoke the presented refresh token so the old `jti` cannot be
    # replayed once a new refresh token is issued below (best-effort).
    _revoke_refresh_jti(db, payload)

    access_token = create_jwt_token(
        subject=str(user.id),
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
        issuer=settings.jwt_issuer,
        audience=settings.jwt_audience,
        extra_claims={"type": "access"},
    )
    refresh_token = create_jwt_token(
        subject=str(user.id),
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        expires_delta=timedelta(days=settings.refresh_token_expire_days),
        issuer=settings.jwt_issuer,
        audience=settings.jwt_audience,
        extra_claims={"type": "refresh"},
    )

    _set_auth_cookies(response, access_token=access_token, refresh_token=refresh_token)
    response.headers["Cache-Control"] = "no-store"
    return _build_auth_me_response(user)


@app.post("/api/v1/auth/logout")
def logout(
    request: Request, response: Response, db: Session = Depends(get_db)
) -> dict[str, bool]:
    # Best-effort revoke the presented refresh token so it cannot be replayed
    # after logout (Req 17.2). Decode tolerantly — a failure must never break
    # logout, which still clears the cookies below.
    raw_token = request.cookies.get(settings.refresh_cookie_name)
    if raw_token:
        payload = _decode_refresh_token_best_effort(raw_token)
        if payload is not None:
            _revoke_refresh_jti(db, payload)
    _clear_auth_cookies(response)
    response.headers["Cache-Control"] = "no-store"
    return {"success": True}


class UpdateProfileRequest(BaseModel):
    display_name: Optional[str] = Field(None, min_length=2, max_length=100)
    username: Optional[str] = None
    bio: Optional[str] = Field(None, max_length=500)
    is_profile_public: Optional[bool] = None
    ai_personalization_enabled: Optional[bool] = None


class UpdateProfileResponse(BaseModel):
    user: UserOut
    message: str


class StartingPathRequest(BaseModel):
    urn_id: Optional[UUID] = None
    urn_slug: Optional[str] = None

    @model_validator(mode="after")
    def _validate_reference(self) -> "StartingPathRequest":
        if self.urn_id is None and not self.urn_slug:
            raise ValueError("Either urn_id or urn_slug is required.")
        return self


class StartingPathResponse(BaseModel):
    starting_urn_id: UUID
    starting_urn_slug: str


def _is_valid_display_name(display_name: str) -> bool:
    normalized = unicodedata.normalize("NFC", display_name)
    for character in normalized:
        if character == " ":
            continue
        if "0" <= character <= "9":
            continue
        if unicodedata.category(character).startswith(
            "L"
        ) and "LATIN" in unicodedata.name(character, ""):
            continue
        return False
    return True


@app.patch("/api/v1/users/me", response_model=UpdateProfileResponse)
def update_profile(
    request: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UpdateProfileResponse:
    if request.display_name is not None:
        normalized_display_name = unicodedata.normalize("NFC", request.display_name)
        if not _is_valid_display_name(normalized_display_name):
            raise AppError(
                code="INVALID_DISPLAY_NAME",
                message="Display name must contain only letters, numbers, and spaces",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        current_user.display_name = normalized_display_name

    if request.username is not None:
        if not USERNAME_REGEX.fullmatch(request.username):
            raise AppError(
                code="INVALID_USERNAME",
                message="Username must be 3-20 characters and contain only letters, numbers, and underscores",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        existing_user_id = db.execute(
            select(User.id).where(
                User.username == request.username, User.id != current_user.id
            )
        ).scalar_one_or_none()
        if existing_user_id is not None:
            raise AppError(
                code="USERNAME_TAKEN",
                message="Username already taken",
                status_code=status.HTTP_409_CONFLICT,
            )
        current_user.username = request.username

    if request.bio is not None:
        current_user.bio = request.bio

    if request.is_profile_public is not None:
        current_user.is_profile_public = request.is_profile_public

    if request.ai_personalization_enabled is not None:
        current_user.ai_personalization_enabled = request.ai_personalization_enabled

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        if request.username is not None:
            raise AppError(
                code="USERNAME_TAKEN",
                message="Username already taken",
                status_code=status.HTTP_409_CONFLICT,
            )
        raise
    db.refresh(current_user)

    return UpdateProfileResponse(
        user=UserOut(
            id=current_user.id,
            email=current_user.email,
            display_name=current_user.display_name,
            avatar_url=current_user.avatar_url,
            username=current_user.username,
            role=current_user.role.value,
            total_xp=current_user.total_xp,
            starting_urn_id=current_user.starting_urn_id,
            is_profile_public=current_user.is_profile_public,
            ai_personalization_enabled=current_user.ai_personalization_enabled,
        ),
        message="Profile updated successfully",
    )


@app.post("/api/v1/users/me/starting-path", response_model=StartingPathResponse)
def set_starting_path(
    request: StartingPathRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StartingPathResponse:
    if request.urn_id is not None:
        urn = db.get(Urn, request.urn_id)
    else:
        urn = db.execute(
            select(Urn).where(Urn.slug == request.urn_slug)
        ).scalar_one_or_none()

    if urn is None:
        urn = db.execute(
            select(Urn).where(Urn.slug == request.urn_slug)
        ).scalar_one_or_none()

    if urn is None:
        raise HTTPException(status_code=404, detail="Urn not found")

    current_user.starting_urn_id = urn.id
    db.commit()
    db.refresh(current_user)

    return StartingPathResponse(starting_urn_id=urn.id, starting_urn_slug=urn.slug)


# =============================================================================
# Onboarding Endpoints
# =============================================================================


class OnboardingGoalRequest(BaseModel):
    goal: str = Field(
        ...,
        description="User's learning goal",
        examples=["learn_culture", "pass_exam", "curiosity"],
    )


class OnboardingStatusResponse(BaseModel):
    onboarding_completed: bool
    onboarding_goal: Optional[str] = None
    onboarding_completed_at: Optional[datetime] = None


class OnboardingCompleteResponse(BaseModel):
    success: bool
    message: str
    onboarding_completed: bool
    onboarding_completed_at: Optional[datetime] = None


@app.post("/api/v1/onboarding/goals")
def save_onboarding_goal(
    request: OnboardingGoalRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Save user's selected onboarding goal."""
    # Validate goal value
    valid_goals = ["learn_culture", "pass_exam", "curiosity", "professional", "hobby"]
    if request.goal not in valid_goals:
        raise AppError(
            code="INVALID_GOAL",
            message=f"Invalid goal. Must be one of: {', '.join(valid_goals)}",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    current_user.onboarding_goal = request.goal
    db.commit()
    db.refresh(current_user)

    return {
        "success": True,
        "message": "Onboarding goal saved successfully",
        "goal": current_user.onboarding_goal,
    }


@app.get("/api/v1/onboarding/status", response_model=OnboardingStatusResponse)
def get_onboarding_status(
    current_user: User = Depends(get_current_user),
) -> OnboardingStatusResponse:
    """Get user's onboarding status."""
    return OnboardingStatusResponse(
        onboarding_completed=current_user.onboarding_completed,
        onboarding_goal=current_user.onboarding_goal,
        onboarding_completed_at=current_user.onboarding_completed_at,
    )


@app.post("/api/v1/onboarding/complete", response_model=OnboardingCompleteResponse)
def complete_onboarding(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OnboardingCompleteResponse:
    """Mark user's onboarding as complete."""
    if current_user.onboarding_completed:
        return OnboardingCompleteResponse(
            success=True,
            message="Onboarding already completed",
            onboarding_completed=True,
            onboarding_completed_at=current_user.onboarding_completed_at,
        )

    current_user.onboarding_completed = True
    current_user.onboarding_completed_at = datetime.now(timezone.utc)

    # Track onboarding completion milestone
    from backend.services.milestones import check_and_create_onboarding_completed

    check_and_create_onboarding_completed(db, current_user.id)

    db.commit()
    db.refresh(current_user)

    return OnboardingCompleteResponse(
        success=True,
        message="Onboarding completed successfully",
        onboarding_completed=True,
        onboarding_completed_at=current_user.onboarding_completed_at,
    )


# =============================================================================
# Notification Settings Endpoints
# =============================================================================


@app.get(
    "/api/v1/notifications/settings", response_model=schemas.NotificationSettingsOut
)
def get_notification_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.NotificationSettingsOut:
    """Get user's notification settings."""
    settings = db.execute(
        select(UserNotificationSettings).where(
            UserNotificationSettings.user_id == current_user.id
        )
    ).scalar_one_or_none()

    # Create default settings if they don't exist
    if settings is None:
        settings = UserNotificationSettings(
            id=uuid_module.uuid4(),
            user_id=current_user.id,
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)

    return schemas.NotificationSettingsOut.model_validate(settings)


@app.put(
    "/api/v1/notifications/settings", response_model=schemas.NotificationSettingsOut
)
def update_notification_settings(
    payload: schemas.NotificationSettingsUpdateIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.NotificationSettingsOut:
    """Update user's notification settings."""
    settings = db.execute(
        select(UserNotificationSettings).where(
            UserNotificationSettings.user_id == current_user.id
        )
    ).scalar_one_or_none()

    # Create if doesn't exist
    if settings is None:
        settings = UserNotificationSettings(
            id=uuid_module.uuid4(),
            user_id=current_user.id,
        )
        db.add(settings)

    # Update fields
    if payload.push_enabled is not None:
        settings.push_enabled = payload.push_enabled
    if payload.email_enabled is not None:
        settings.email_enabled = payload.email_enabled
    if payload.streak_reminders is not None:
        settings.streak_reminders = payload.streak_reminders
    if payload.daily_mission_reminders is not None:
        settings.daily_mission_reminders = payload.daily_mission_reminders
    if payload.weekly_digest is not None:
        settings.weekly_digest = payload.weekly_digest
    if payload.marketing_enabled is not None:
        settings.marketing_enabled = payload.marketing_enabled
    if payload.quiet_hours_start is not None:
        settings.quiet_hours_start = payload.quiet_hours_start
    if payload.quiet_hours_end is not None:
        settings.quiet_hours_end = payload.quiet_hours_end

    db.commit()
    db.refresh(settings)

    return schemas.NotificationSettingsOut.model_validate(settings)


@app.post(
    "/api/v1/notifications/register-push", response_model=schemas.PushTokenRegisterOut
)
def register_push_token(
    payload: schemas.PushTokenRegisterIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.PushTokenRegisterOut:
    """Register or update push notification token."""
    settings = db.execute(
        select(UserNotificationSettings).where(
            UserNotificationSettings.user_id == current_user.id
        )
    ).scalar_one_or_none()

    # Create if doesn't exist
    if settings is None:
        settings = UserNotificationSettings(
            id=uuid_module.uuid4(),
            user_id=current_user.id,
        )
        db.add(settings)

    # Update push token and platform
    settings.push_token = payload.token
    settings.push_platform = payload.platform
    settings.push_enabled = True

    # Mark that we've prompted the user for permission
    current_user.push_permission_prompted = True

    db.commit()

    return schemas.PushTokenRegisterOut(
        success=True, message="Push notification token registered successfully"
    )


@app.delete(
    "/api/v1/notifications/unregister-push", response_model=schemas.PushTokenRegisterOut
)
def unregister_push_token(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.PushTokenRegisterOut:
    """Unregister push notification token."""
    settings = db.execute(
        select(UserNotificationSettings).where(
            UserNotificationSettings.user_id == current_user.id
        )
    ).scalar_one_or_none()

    if settings is not None:
        settings.push_token = None
        settings.push_platform = None
        settings.push_enabled = False
        db.commit()

    return schemas.PushTokenRegisterOut(
        success=True, message="Push notification token unregistered successfully"
    )


@app.get(
    "/api/v1/notifications/should-prompt-permission",
    response_model=schemas.ShouldPromptPermissionOut,
)
def should_prompt_permission(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.ShouldPromptPermissionOut:
    """
    Check if we should prompt the user for push notification permission.
    Returns true if:
    - User has not been prompted before (push_permission_prompted is false)
    - User has completed at least 1 lesson
    """
    # Check if already prompted
    if current_user.push_permission_prompted:
        return schemas.ShouldPromptPermissionOut(
            should_prompt=False,
            reason="User has already been prompted for push notifications",
        )

    # Check if user has completed at least one lesson
    completed_lesson_count = db.execute(
        select(func.count(UserProgress.id)).where(
            UserProgress.user_id == current_user.id,
            UserProgress.lesson_viewed_at.isnot(None),
        )
    ).scalar_one()

    if completed_lesson_count == 0:
        return schemas.ShouldPromptPermissionOut(
            should_prompt=False, reason="User has not completed any lessons yet"
        )

    return schemas.ShouldPromptPermissionOut(
        should_prompt=True, reason="User is eligible for push notification prompt"
    )


# =============================================================================
# PUSH NOTIFICATION ENDPOINTS
# =============================================================================


@app.post(
    "/api/v1/admin/push-notifications/send",
    response_model=schemas.SendPushNotificationOut,
)
def admin_send_push_notification(
    payload: schemas.SendPushNotificationIn,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> schemas.SendPushNotificationOut:
    """
    Send push notifications to specific users.

    Admin only endpoint.
    """
    from .services import push_notifications

    # Create notifications for each user
    created_notifications = []
    for user_id in payload.user_ids:
        # Verify user exists
        user = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
        if not user:
            continue

        notification = push_notifications.create_notification(
            db=db,
            user_id=user_id,
            title=payload.title,
            body=payload.body,
            notification_type=NotificationType(payload.notification_type),
            data_payload=payload.data_payload,
            scheduled_for=payload.scheduled_for,
        )
        created_notifications.append(notification)

    # Send notifications immediately if not scheduled
    sent_count = 0
    failed_count = 0

    if not payload.scheduled_for:
        for notification in created_notifications:
            if push_notifications.send_notification(db, notification):
                sent_count += 1
            else:
                failed_count += 1

    return schemas.SendPushNotificationOut(
        success=True,
        message=f"Created {len(created_notifications)} notifications",
        notifications_created=len(created_notifications),
        notifications_sent=sent_count,
        notifications_failed=failed_count,
    )


@app.post(
    "/api/v1/admin/push-notifications/broadcast",
    response_model=schemas.BroadcastPushNotificationOut,
)
def admin_broadcast_push_notification(
    payload: schemas.BroadcastPushNotificationIn,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> schemas.BroadcastPushNotificationOut:
    """
    Broadcast a push notification to all eligible users.

    Admin only endpoint. Can filter by user role.
    """
    from .services import push_notifications

    results = push_notifications.broadcast_notification(
        db=db,
        title=payload.title,
        body=payload.body,
        notification_type=NotificationType(payload.notification_type),
        data_payload=payload.data_payload,
        user_role=payload.user_role,
    )

    return schemas.BroadcastPushNotificationOut(
        success=True,
        message=f"Broadcast to {results['total_users']} users",
        **results,
    )


@app.get(
    "/api/v1/admin/push-notifications", response_model=schemas.PushNotificationListOut
)
def admin_list_push_notifications(
    user_id: Optional[UUID] = Query(None, description="Filter by user ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    notification_type: Optional[str] = Query(None, description="Filter by type"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> schemas.PushNotificationListOut:
    """
    List all push notifications with optional filters.

    Admin only endpoint.
    """
    # Build query
    query = select(PushNotification)

    if user_id:
        query = query.where(PushNotification.user_id == user_id)

    if status:
        query = query.where(PushNotification.status == status)

    if notification_type:
        query = query.where(PushNotification.notification_type == notification_type)

    # Get total count
    total = len(db.execute(query).scalars().all())

    # Get paginated results
    query = (
        query.order_by(PushNotification.created_at.desc()).limit(limit).offset(offset)
    )
    notifications = db.execute(query).scalars().all()

    return schemas.PushNotificationListOut(
        notifications=[
            schemas.PushNotificationOut.model_validate(n) for n in notifications
        ],
        total=total,
        limit=limit,
        offset=offset,
    )


@app.get(
    "/api/v1/notifications/history", response_model=schemas.PushNotificationListOut
)
def get_notification_history(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.PushNotificationListOut:
    """
    Get the current user's notification history.
    """
    from .services import push_notifications

    notifications, total = push_notifications.get_user_notification_history(
        db=db,
        user_id=current_user.id,
        limit=limit,
        offset=offset,
    )

    return schemas.PushNotificationListOut(
        notifications=[
            schemas.PushNotificationOut.model_validate(n) for n in notifications
        ],
        total=total,
        limit=limit,
        offset=offset,
    )


# =============================================================================
# GUEST PREVIEW ENDPOINTS
# =============================================================================


@app.get("/api/v1/preview/lesson")
def get_preview_lesson(
    db: Session = Depends(get_db),
) -> schemas.GuestPreviewLessonOut:
    """Get the demo lesson for guest users (no authentication required).

    Returns the first preview-eligible lesson for guests to experience
    the app before signing up.
    """
    # Find first preview-eligible lesson
    stmt = (
        select(LessonContent)
        .join(Motif)
        .join(Urn)
        .where(LessonContent.preview_eligible == True)
        .where(LessonContent.is_published == True)
        .options(selectinload(LessonContent.motif).selectinload(Motif.urn))
        .order_by(LessonContent.created_at)
        .limit(1)
    )

    lesson = db.execute(stmt).scalar_one_or_none()

    if lesson is None:
        raise AppError(
            code="NO_PREVIEW_AVAILABLE",
            message="No preview lesson available at this time",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    # Parse additional_images if it's a JSON string
    additional_images = None
    if lesson.additional_images:
        if isinstance(lesson.additional_images, str):
            import json

            try:
                additional_images = json.loads(lesson.additional_images)
            except json.JSONDecodeError:
                additional_images = None
        elif isinstance(lesson.additional_images, list):
            additional_images = lesson.additional_images

    return schemas.GuestPreviewLessonOut(
        lesson_id=lesson.id,
        motif_id=lesson.motif.id,
        motif_name=lesson.motif.name,
        motif_description=lesson.motif.description or "",
        urn_id=lesson.motif.urn.id,
        urn_name=lesson.motif.urn.name,
        urn_thumbnail_url=lesson.motif.urn.thumbnail_url,
        intro_text=lesson.intro_text,
        description=lesson.description,
        historical_context=lesson.historical_context,
        symbolism=lesson.symbolism,
        fun_fact=lesson.fun_fact,
        additional_images=additional_images,
    )


@app.post("/api/v1/preview/start", response_model=schemas.GuestPreviewStartOut)
def start_preview_session(
    payload: schemas.GuestPreviewStartIn,
    db: Session = Depends(get_db),
) -> schemas.GuestPreviewStartOut:
    """Start a guest preview session (no authentication required).

    Creates a tracking record for the guest's preview session,
    allowing us to measure engagement and conversion.
    """
    # Find first preview-eligible lesson
    stmt = (
        select(LessonContent)
        .join(Motif)
        .join(Urn)
        .where(LessonContent.preview_eligible == True)
        .where(LessonContent.is_published == True)
        .options(selectinload(LessonContent.motif).selectinload(Motif.urn))
        .order_by(LessonContent.created_at)
        .limit(1)
    )

    lesson = db.execute(stmt).scalar_one_or_none()

    if lesson is None:
        raise AppError(
            code="NO_PREVIEW_AVAILABLE",
            message="No preview lesson available at this time",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    # Create preview session record
    preview = GuestPreview(
        session_id=payload.session_id,
        preview_lesson_id=lesson.id,
        device_info=payload.device_info,
        started_at=datetime.now(timezone.utc),
    )

    db.add(preview)
    db.commit()
    db.refresh(preview)

    return schemas.GuestPreviewStartOut(
        preview_id=preview.id,
        lesson_id=lesson.id,
        lesson_title=lesson.motif.name,
        lesson_description=lesson.description,
        motif_name=lesson.motif.name,
        urn_name=lesson.motif.urn.name,
        started_at=preview.started_at,
    )


@app.post("/api/v1/preview/complete", response_model=schemas.GuestPreviewCompleteOut)
def complete_preview_session(
    payload: schemas.GuestPreviewCompleteIn,
    db: Session = Depends(get_db),
) -> schemas.GuestPreviewCompleteOut:
    """Mark a guest preview session as complete (no authentication required).

    Updates the preview session to track completion, which helps measure
    engagement and content quality.
    """
    # Find the most recent preview session for this session_id that hasn't been completed
    stmt = (
        select(GuestPreview)
        .where(GuestPreview.session_id == payload.session_id)
        .where(GuestPreview.completed_at.is_(None))
        .order_by(GuestPreview.started_at.desc())
        .limit(1)
    )

    preview = db.execute(stmt).scalar_one_or_none()

    if preview is None:
        raise AppError(
            code="PREVIEW_SESSION_NOT_FOUND",
            message="No active preview session found for this session ID",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    # Mark as completed
    preview.completed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(preview)

    return schemas.GuestPreviewCompleteOut(
        success=True,
        message="Preview session marked as complete",
        completed_at=preview.completed_at,
        preview_id=preview.id,
    )


@app.post("/api/v1/preview/convert", response_model=schemas.GuestPreviewConvertOut)
def convert_preview_to_user(
    payload: schemas.GuestPreviewConvertIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.GuestPreviewConvertOut:
    """Link preview session(s) to a newly registered user account.

    After a user signs up, this endpoint connects their previous guest
    preview sessions to their new account for analytics tracking.

    Requires authentication (user must be logged in).
    """
    # Find all preview sessions for this session_id that haven't been converted yet
    stmt = (
        select(GuestPreview)
        .where(GuestPreview.session_id == payload.session_id)
        .where(GuestPreview.converted_to_user_id.is_(None))
    )

    previews = db.execute(stmt).scalars().all()

    if not previews:
        # Not an error - user might not have done a preview
        return schemas.GuestPreviewConvertOut(
            success=True,
            message="No preview sessions to convert",
            preview_sessions_converted=0,
        )

    # Link all matching preview sessions to the current user
    count = 0
    for preview in previews:
        preview.converted_to_user_id = current_user.id
        count += 1

    db.commit()

    return schemas.GuestPreviewConvertOut(
        success=True,
        message=f"Successfully linked {count} preview session(s) to your account",
        preview_sessions_converted=count,
    )


class PublicBadgeOut(BaseModel):
    name: str
    icon: str
    description: Optional[str] = None


class PublicMotifOut(BaseModel):
    id: UUID
    name: str
    category: str
    rarity: str
    status: str
    thumbnail_url: Optional[str] = None
    urn_id: UUID
    urn_name: str
    urn_slug: str


class UserPublicStatsOut(BaseModel):
    discovered_count: int
    learned_count: int
    mastered_count: int
    quizzes_passed: int


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


@app.get("/api/v1/users/{user_id}/public", response_model=UserPublicProfile)
def get_user_public_profile(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserPublicProfile:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.is_profile_public and user.id != current_user.id:
        raise HTTPException(status_code=403, detail="Profile is private")

    current_rank, _, _ = _compute_rank(user.total_xp)

    earned_badges = (
        db.execute(
            select(UserBadge)
            .options(selectinload(UserBadge.badge))
            .where(UserBadge.user_id == user.id)
            .order_by(UserBadge.earned_at.desc())
        )
        .scalars()
        .all()
    )

    discovered_count = db.execute(
        select(func.count(UserProgress.id))
        .select_from(UserProgress)
        .join(Motif, UserProgress.motif_id == Motif.id)
        .where(
            UserProgress.user_id == user.id,
            Motif.is_active.is_(True),
            UserProgress.status == UnlockStatus.discovered,
        )
    ).scalar_one()
    learned_count = db.execute(
        select(func.count(UserProgress.id))
        .select_from(UserProgress)
        .join(Motif, UserProgress.motif_id == Motif.id)
        .where(
            UserProgress.user_id == user.id,
            Motif.is_active.is_(True),
            UserProgress.status == UnlockStatus.learned,
        )
    ).scalar_one()
    mastered_count = db.execute(
        select(func.count(UserProgress.id))
        .select_from(UserProgress)
        .join(Motif, UserProgress.motif_id == Motif.id)
        .where(
            UserProgress.user_id == user.id,
            Motif.is_active.is_(True),
            UserProgress.status == UnlockStatus.mastered,
        )
    ).scalar_one()
    quizzes_passed = db.execute(
        select(func.count(QuizAttempt.id))
        .select_from(QuizAttempt)
        .join(Motif, QuizAttempt.motif_id == Motif.id)
        .where(
            QuizAttempt.user_id == user.id,
            Motif.is_active.is_(True),
            QuizAttempt.percentage >= QUIZ_PASS_PERCENT,
        )
    ).scalar_one()

    unlocked_rows = db.execute(
        select(UserProgress, Motif, Urn)
        .join(Motif, UserProgress.motif_id == Motif.id)
        .join(Urn, Motif.urn_id == Urn.id)
        .where(
            UserProgress.user_id == user.id,
            Motif.is_active.is_(True),
            UserProgress.status != UnlockStatus.hidden,
        )
        .order_by(
            Urn.display_order.nulls_last(), Motif.display_order.nulls_last(), Motif.name
        )
    ).all()

    username = user.username or (user.email or "").split("@", 1)[0] or str(user.id)

    return UserPublicProfile(
        id=user.id,
        username=username,
        display_name=user.display_name,
        avatar_url=user.avatar_url,
        bio=user.bio,
        total_xp=user.total_xp,
        rank=RankOut(**current_rank),
        badges=[
            PublicBadgeOut(
                name=user_badge.badge.name,
                icon=user_badge.badge.icon_url,
                description=user_badge.badge.description,
            )
            for user_badge in earned_badges
            if user_badge.badge is not None
        ],
        certificates=[],
        stats=UserPublicStatsOut(
            discovered_count=int(discovered_count or 0),
            learned_count=int(learned_count or 0),
            mastered_count=int(mastered_count or 0),
            quizzes_passed=int(quizzes_passed or 0),
        ),
        motifs=[
            PublicMotifOut(
                id=motif.id,
                name=motif.name,
                category=motif.category.value,
                rarity=motif.rarity.value,
                status=progress.status.value,
                thumbnail_url=motif.thumbnail_url,
                urn_id=urn.id,
                urn_name=urn.name,
                urn_slug=urn.slug,
            )
            for progress, motif, urn in unlocked_rows
        ],
    )


@app.get("/api/v1/u/{username_or_id}", response_model=UserPublicProfile)
def get_user_public_profile_by_username_or_id(
    username_or_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserPublicProfile:
    try:
        user_id = UUID(username_or_id)
    except ValueError:
        user = db.execute(
            select(User.id).where(User.username == username_or_id)
        ).scalar_one_or_none()
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        user_id = user

    return get_user_public_profile(user_id=user_id, current_user=current_user, db=db)


class UrnOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    slug: str
    name: str
    model_url: str


class AnalyticsEventIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    payload: Optional[dict[str, Any]] = None
    path: Optional[str] = None
    session_id: Optional[UUID] = None
    cohort: Optional[str] = Field(None, max_length=50)
    device_info: Optional[dict[str, Any]] = None


class AnalyticsEventsIn(BaseModel):
    events: list[AnalyticsEventIn]


class AnalyticsEventsOut(BaseModel):
    success: bool
    count: int


@app.post("/api/v1/analytics/events", response_model=AnalyticsEventsOut)
def ingest_analytics_events(
    payload: AnalyticsEventsIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AnalyticsEventsOut:
    if not payload.events:
        return AnalyticsEventsOut(success=True, count=0)

    # Import analytics service for event validation
    from services.analytics import create_event_record

    # Create validated event records
    event_records = []
    for event in payload.events:
        event_data = create_event_record(
            user_id=current_user.id,
            event_name=event.name,
            payload=event.payload,
            path=event.path,
            session_id=event.session_id,
            cohort=event.cohort,
            device_info=event.device_info,
        )
        event_records.append(AnalyticsEvent(**event_data))

    db.add_all(event_records)
    db.commit()
    return AnalyticsEventsOut(success=True, count=len(payload.events))


# =============================================================================
# SESSION TRACKING ENDPOINTS
# =============================================================================


@app.post("/api/v1/sessions/heartbeat", response_model=schemas.SessionHeartbeatOut)
def session_heartbeat(
    payload: schemas.SessionHeartbeatIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.SessionHeartbeatOut:
    """
    Update session activity with heartbeat.
    Called every 30 seconds from client to keep session alive.
    """
    now = datetime.now(timezone.utc)

    # Find existing session or create new one
    existing_session = db.execute(
        select(UserSession).where(
            UserSession.session_id == payload.session_id,
            UserSession.user_id == current_user.id,
        )
    ).scalar_one_or_none()

    if existing_session:
        # Update existing session
        existing_session.last_active_at = now
        existing_session.is_active = True
        existing_session.device_type = payload.device_type
        existing_session.platform = payload.platform
        if payload.app_version:
            existing_session.app_version = payload.app_version
        db.commit()
        db.refresh(existing_session)

        return schemas.SessionHeartbeatOut(
            success=True,
            session_id=existing_session.session_id,
            is_active=existing_session.is_active,
        )
    else:
        # Create new session
        new_session = UserSession(
            session_id=payload.session_id,
            user_id=current_user.id,
            device_type=payload.device_type,
            platform=payload.platform,
            app_version=payload.app_version,
            started_at=now,
            last_active_at=now,
            is_active=True,
        )
        db.add(new_session)
        db.commit()
        db.refresh(new_session)

        return schemas.SessionHeartbeatOut(
            success=True,
            session_id=new_session.session_id,
            is_active=new_session.is_active,
        )


@app.post("/api/v1/sessions/end", response_model=schemas.SessionEndOut)
def end_session(
    payload: schemas.SessionEndIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.SessionEndOut:
    """
    End the current session.
    Called when user logs out or closes app.
    """
    now = datetime.now(timezone.utc)

    # Find the session
    session = db.execute(
        select(UserSession).where(
            UserSession.session_id == payload.session_id,
            UserSession.user_id == current_user.id,
        )
    ).scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Mark session as ended
    session.ended_at = now
    session.is_active = False
    db.commit()

    # Calculate duration
    duration_seconds = None
    if session.started_at:
        duration_seconds = int((now - session.started_at).total_seconds())

    return schemas.SessionEndOut(
        success=True,
        session_id=session.session_id,
        duration_seconds=duration_seconds,
    )


@app.get(
    "/api/v1/admin/analytics/sessions/active", response_model=schemas.ActiveSessionsOut
)
def get_active_sessions(
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> schemas.ActiveSessionsOut:
    """
    Get count of currently active sessions.
    Admin only endpoint.
    """
    now = datetime.now(timezone.utc)
    five_minutes_ago = now - timedelta(minutes=5)
    thirty_minutes_ago = now - timedelta(minutes=30)

    # Active sessions (last 5 minutes)
    active_5min = (
        db.execute(
            select(func.count(UserSession.id)).where(
                UserSession.is_active.is_(True),
                UserSession.last_active_at >= five_minutes_ago,
            )
        ).scalar()
        or 0
    )

    # Sessions active in last 30 minutes
    active_30min = (
        db.execute(
            select(func.count(UserSession.id)).where(
                UserSession.is_active.is_(True),
                UserSession.last_active_at >= thirty_minutes_ago,
            )
        ).scalar()
        or 0
    )

    # Auto-expire old sessions
    db.execute(
        select(UserSession).where(
            UserSession.is_active.is_(True),
            UserSession.last_active_at < thirty_minutes_ago,
        )
    )
    expired_sessions = (
        db.execute(
            select(UserSession).where(
                UserSession.is_active.is_(True),
                UserSession.last_active_at < thirty_minutes_ago,
            )
        )
        .scalars()
        .all()
    )

    for session in expired_sessions:
        session.is_active = False
        session.ended_at = session.last_active_at

    if expired_sessions:
        db.commit()

    return schemas.ActiveSessionsOut(
        active_sessions=active_5min,
        last_5_minutes=active_5min,
        last_30_minutes=active_30min,
        timestamp=now,
    )


@app.get(
    "/api/v1/admin/analytics/sessions/stats", response_model=schemas.SessionStatsOut
)
def get_session_statistics(
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> schemas.SessionStatsOut:
    """
    Get detailed session statistics.
    Admin only endpoint.
    """
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = now - timedelta(days=7)
    month_start = now - timedelta(days=30)

    # Total sessions by period
    total_today = (
        db.execute(
            select(func.count(UserSession.id)).where(
                UserSession.started_at >= today_start
            )
        ).scalar()
        or 0
    )

    total_week = (
        db.execute(
            select(func.count(UserSession.id)).where(
                UserSession.started_at >= week_start
            )
        ).scalar()
        or 0
    )

    total_month = (
        db.execute(
            select(func.count(UserSession.id)).where(
                UserSession.started_at >= month_start
            )
        ).scalar()
        or 0
    )

    # Average session duration (in minutes)
    # Calculate only for ended sessions
    avg_duration_result = db.execute(
        select(
            func.avg(
                func.extract("epoch", UserSession.ended_at - UserSession.started_at)
            )
        ).where(
            UserSession.ended_at.isnot(None),
            UserSession.started_at >= month_start,
        )
    ).scalar()

    avg_duration_minutes = 0.0
    if avg_duration_result:
        avg_duration_minutes = round(float(avg_duration_result) / 60, 2)

    # Unique users by period
    unique_today = (
        db.execute(
            select(func.count(func.distinct(UserSession.user_id))).where(
                UserSession.started_at >= today_start,
                UserSession.user_id.isnot(None),
            )
        ).scalar()
        or 0
    )

    unique_week = (
        db.execute(
            select(func.count(func.distinct(UserSession.user_id))).where(
                UserSession.started_at >= week_start,
                UserSession.user_id.isnot(None),
            )
        ).scalar()
        or 0
    )

    unique_month = (
        db.execute(
            select(func.count(func.distinct(UserSession.user_id))).where(
                UserSession.started_at >= month_start,
                UserSession.user_id.isnot(None),
            )
        ).scalar()
        or 0
    )

    # Current active sessions
    five_minutes_ago = now - timedelta(minutes=5)
    current_active = (
        db.execute(
            select(func.count(UserSession.id)).where(
                UserSession.is_active.is_(True),
                UserSession.last_active_at >= five_minutes_ago,
            )
        ).scalar()
        or 0
    )

    # Peak concurrent today (approximate using 5-minute windows)
    # This is a simplified version - for production you'd want more sophisticated tracking
    peak_concurrent = (
        db.execute(
            select(func.count(UserSession.id)).where(
                UserSession.started_at >= today_start,
                UserSession.is_active.is_(True),
            )
        ).scalar()
        or 0
    )

    # Sessions by platform
    platform_stats = db.execute(
        select(UserSession.platform, func.count(UserSession.id))
        .where(UserSession.started_at >= month_start)
        .group_by(UserSession.platform)
    ).all()

    by_platform = {platform: count for platform, count in platform_stats}

    # Sessions by device type
    device_stats = db.execute(
        select(UserSession.device_type, func.count(UserSession.id))
        .where(UserSession.started_at >= month_start)
        .group_by(UserSession.device_type)
    ).all()

    by_device_type = {device: count for device, count in device_stats}

    return schemas.SessionStatsOut(
        total_sessions_today=total_today,
        total_sessions_week=total_week,
        total_sessions_month=total_month,
        avg_session_duration_minutes=avg_duration_minutes,
        unique_users_today=unique_today,
        unique_users_week=unique_week,
        unique_users_month=unique_month,
        current_active_sessions=current_active,
        peak_concurrent_today=peak_concurrent,
        by_platform=by_platform,
        by_device_type=by_device_type,
    )


# =============================================================================
# CRASH REPORTING ENDPOINTS
# =============================================================================


# Simple in-memory rate limiter for crash reports
_crash_report_rate_limiter: dict[str, list[datetime]] = {}


def _check_crash_report_rate_limit(
    user_key: str, max_reports: int = 10, window_hours: int = 1
) -> None:
    """Check if user has exceeded crash report rate limit."""
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(hours=window_hours)

    # Clean up old entries for this user
    if user_key in _crash_report_rate_limiter:
        _crash_report_rate_limiter[user_key] = [
            ts for ts in _crash_report_rate_limiter[user_key] if ts > window_start
        ]
    else:
        _crash_report_rate_limiter[user_key] = []

    # Check if limit exceeded
    if len(_crash_report_rate_limiter[user_key]) >= max_reports:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Maximum {max_reports} crash reports per {window_hours} hour(s).",
        )

    # Add current timestamp
    _crash_report_rate_limiter[user_key].append(now)


@app.post("/api/v1/crash-reports", response_model=schemas.CrashReportOut)
def submit_crash_report(
    payload: schemas.CrashReportCreateIn,
    request: Request,
    db: Session = Depends(get_db),
) -> schemas.CrashReportOut:
    """
    Submit a crash/error report from mobile or web client.
    Public endpoint with rate limiting (10 reports per hour per user/IP).
    """
    # Determine rate limit key (user_id if provided, otherwise IP address)
    if payload.user_id:
        rate_limit_key = f"user_{payload.user_id}"
    else:
        # Get client IP from request
        client_ip = request.client.host if request.client else "unknown"
        rate_limit_key = f"ip_{client_ip}"

    # Check rate limit
    _check_crash_report_rate_limit(rate_limit_key)

    # Create crash report
    crash_report = CrashReport(
        user_id=payload.user_id,
        session_id=payload.session_id,
        error_type=payload.error_type,
        error_message=payload.error_message,
        stack_trace=payload.stack_trace,
        platform=payload.platform,
        app_version=payload.app_version,
        device_model=payload.device_model,
        os_version=payload.os_version,
        additional_data=payload.additional_data,
    )

    db.add(crash_report)
    db.commit()
    db.refresh(crash_report)

    return schemas.CrashReportOut.model_validate(crash_report)


@app.get("/api/v1/admin/crash-reports", response_model=schemas.CrashReportListOut)
def list_crash_reports(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    platform: Optional[str] = Query(None, pattern="^(ios|android|web)$"),
    error_type: Optional[str] = Query(None, pattern="^(crash|error|exception|anr)$"),
    is_resolved: Optional[bool] = None,
    user_id: Optional[UUID] = None,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> schemas.CrashReportListOut:
    """
    Get paginated list of crash reports with filters.
    Admin only endpoint.
    """
    # Build query
    query = select(CrashReport)

    # Apply filters
    if platform:
        query = query.where(CrashReport.platform == platform)
    if error_type:
        query = query.where(CrashReport.error_type == error_type)
    if is_resolved is not None:
        query = query.where(CrashReport.is_resolved == is_resolved)
    if user_id:
        query = query.where(CrashReport.user_id == user_id)

    # Get total count
    total = db.execute(select(func.count()).select_from(query.subquery())).scalar() or 0

    # Apply pagination and ordering
    query = query.order_by(CrashReport.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    # Execute query with eager loading
    results = (
        db.execute(
            query.options(
                selectinload(CrashReport.user), selectinload(CrashReport.resolved_by)
            )
        )
        .scalars()
        .all()
    )

    # Build detailed output
    detailed_reports = []
    for report in results:
        detailed_reports.append(
            schemas.CrashReportDetailOut(
                id=report.id,
                user_id=report.user_id,
                user_email=report.user.email if report.user else None,
                user_display_name=report.user.display_name if report.user else None,
                session_id=report.session_id,
                error_type=report.error_type,
                error_message=report.error_message,
                stack_trace=report.stack_trace,
                platform=report.platform,
                app_version=report.app_version,
                device_model=report.device_model,
                os_version=report.os_version,
                additional_data=report.additional_data,
                created_at=report.created_at,
                is_resolved=report.is_resolved,
                resolved_by_id=report.resolved_by_id,
                resolved_by_email=report.resolved_by.email
                if report.resolved_by
                else None,
                resolved_by_display_name=report.resolved_by.display_name
                if report.resolved_by
                else None,
                resolved_at=report.resolved_at,
            )
        )

    return schemas.CrashReportListOut(
        reports=detailed_reports,
        total=total,
        page=page,
        page_size=page_size,
    )


@app.get(
    "/api/v1/admin/crash-reports/{report_id}",
    response_model=schemas.CrashReportDetailOut,
)
def get_crash_report(
    report_id: UUID,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> schemas.CrashReportDetailOut:
    """
    Get detailed information about a specific crash report.
    Admin only endpoint.
    """
    report = db.execute(
        select(CrashReport)
        .where(CrashReport.id == report_id)
        .options(selectinload(CrashReport.user), selectinload(CrashReport.resolved_by))
    ).scalar_one_or_none()

    if not report:
        raise HTTPException(status_code=404, detail="Crash report not found")

    return schemas.CrashReportDetailOut(
        id=report.id,
        user_id=report.user_id,
        user_email=report.user.email if report.user else None,
        user_display_name=report.user.display_name if report.user else None,
        session_id=report.session_id,
        error_type=report.error_type,
        error_message=report.error_message,
        stack_trace=report.stack_trace,
        platform=report.platform,
        app_version=report.app_version,
        device_model=report.device_model,
        os_version=report.os_version,
        additional_data=report.additional_data,
        created_at=report.created_at,
        is_resolved=report.is_resolved,
        resolved_by_id=report.resolved_by_id,
        resolved_by_email=report.resolved_by.email if report.resolved_by else None,
        resolved_by_display_name=report.resolved_by.display_name
        if report.resolved_by
        else None,
        resolved_at=report.resolved_at,
    )


@app.post(
    "/api/v1/admin/crash-reports/{report_id}/resolve",
    response_model=schemas.CrashReportDetailOut,
)
def resolve_crash_report(
    report_id: UUID,
    payload: schemas.CrashReportResolveIn,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> schemas.CrashReportDetailOut:
    """
    Mark a crash report as resolved.
    Admin only endpoint.
    """
    report = db.execute(
        select(CrashReport)
        .where(CrashReport.id == report_id)
        .options(selectinload(CrashReport.user), selectinload(CrashReport.resolved_by))
    ).scalar_one_or_none()

    if not report:
        raise HTTPException(status_code=404, detail="Crash report not found")

    if report.is_resolved:
        raise HTTPException(status_code=400, detail="Crash report is already resolved")

    # Mark as resolved
    report.is_resolved = True
    report.resolved_by_id = current_user.id
    report.resolved_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(report)

    return schemas.CrashReportDetailOut(
        id=report.id,
        user_id=report.user_id,
        user_email=report.user.email if report.user else None,
        user_display_name=report.user.display_name if report.user else None,
        session_id=report.session_id,
        error_type=report.error_type,
        error_message=report.error_message,
        stack_trace=report.stack_trace,
        platform=report.platform,
        app_version=report.app_version,
        device_model=report.device_model,
        os_version=report.os_version,
        additional_data=report.additional_data,
        created_at=report.created_at,
        is_resolved=report.is_resolved,
        resolved_by_id=report.resolved_by_id,
        resolved_by_email=report.resolved_by.email if report.resolved_by else None,
        resolved_by_display_name=report.resolved_by.display_name
        if report.resolved_by
        else None,
        resolved_at=report.resolved_at,
    )


@app.get(
    "/api/v1/admin/crash-reports/stats", response_model=schemas.CrashReportStatsOut
)
def get_crash_report_stats(
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> schemas.CrashReportStatsOut:
    """
    Get crash report statistics.
    Admin only endpoint.
    """
    now = datetime.now(timezone.utc)
    last_24h = now - timedelta(hours=24)
    last_7d = now - timedelta(days=7)
    last_30d = now - timedelta(days=30)

    # Total reports
    total_reports = db.execute(select(func.count(CrashReport.id))).scalar() or 0

    # Unresolved reports
    unresolved_reports = (
        db.execute(
            select(func.count(CrashReport.id)).where(CrashReport.is_resolved == False)
        ).scalar()
        or 0
    )

    # Resolved reports
    resolved_reports = (
        db.execute(
            select(func.count(CrashReport.id)).where(CrashReport.is_resolved == True)
        ).scalar()
        or 0
    )

    # Reports by platform
    platform_stats = db.execute(
        select(CrashReport.platform, func.count(CrashReport.id)).group_by(
            CrashReport.platform
        )
    ).all()
    reports_by_platform = {platform: count for platform, count in platform_stats}

    # Reports by error type
    error_type_stats = db.execute(
        select(CrashReport.error_type, func.count(CrashReport.id)).group_by(
            CrashReport.error_type
        )
    ).all()
    reports_by_error_type = {
        error_type: count for error_type, count in error_type_stats
    }

    # Reports in last 24 hours
    reports_last_24h = (
        db.execute(
            select(func.count(CrashReport.id)).where(CrashReport.created_at >= last_24h)
        ).scalar()
        or 0
    )

    # Reports in last 7 days
    reports_last_7d = (
        db.execute(
            select(func.count(CrashReport.id)).where(CrashReport.created_at >= last_7d)
        ).scalar()
        or 0
    )

    # Reports in last 30 days
    reports_last_30d = (
        db.execute(
            select(func.count(CrashReport.id)).where(CrashReport.created_at >= last_30d)
        ).scalar()
        or 0
    )

    # Top errors (most frequent error messages)
    top_errors_raw = db.execute(
        select(
            CrashReport.error_message,
            func.count(CrashReport.id).label("count"),
            func.max(CrashReport.created_at).label("latest_occurrence"),
        )
        .where(CrashReport.created_at >= last_30d)
        .group_by(CrashReport.error_message)
        .order_by(func.count(CrashReport.id).desc())
        .limit(10)
    ).all()

    top_errors = [
        {
            "error_message": error_msg,
            "count": count,
            "latest_occurrence": latest.isoformat() if latest else None,
        }
        for error_msg, count, latest in top_errors_raw
    ]

    return schemas.CrashReportStatsOut(
        total_reports=total_reports,
        unresolved_reports=unresolved_reports,
        resolved_reports=resolved_reports,
        reports_by_platform=reports_by_platform,
        reports_by_error_type=reports_by_error_type,
        reports_last_24h=reports_last_24h,
        reports_last_7d=reports_last_7d,
        reports_last_30d=reports_last_30d,
        top_errors=top_errors,
    )


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


class MotifProgressOut(BaseModel):
    motif_id: UUID
    status: str
    discovered_at: Optional[datetime] = None
    lesson_viewed_at: Optional[datetime] = None
    learned_at: Optional[datetime] = None
    mastered_at: Optional[datetime] = None
    quiz_attempts: int
    quiz_best_score: int
    xp_earned: int


class UrnProgressResponse(BaseModel):
    urn_id: UUID
    urn_slug: str
    motifs: list[MotifProgressOut]


@app.get("/motifs/{urn_name}", response_model=MotifsByUrnResponse)
def get_motifs_by_urn(
    urn_name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MotifsByUrnResponse:
    urn = db.execute(
        select(Urn).where(
            or_(Urn.slug == urn_name, func.lower(Urn.name) == urn_name.lower())
        )
    ).scalar_one_or_none()
    if urn is None:
        raise HTTPException(status_code=404, detail="Urn not found")

    # Get allowed content ratings for the user
    allowed_ratings = get_allowed_content_ratings(current_user)

    motifs = (
        db.execute(
            select(Motif)
            .options(selectinload(Motif.lesson))
            .where(
                Motif.urn_id == urn.id,
                Motif.is_active.is_(True),
                Motif.content_rating.in_(allowed_ratings),
            )
            .order_by(Motif.display_order.nulls_last(), Motif.name)
        )
        .scalars()
        .all()
    )

    can_view_drafts = _can_view_drafts(current_user)

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
                lesson_intro=(
                    m.lesson.intro_text
                    if m.lesson and (m.lesson.is_published or can_view_drafts)
                    else None
                ),
            )
            for m in motifs
        ],
    )


@app.get("/api/v1/urns/{urn_slug}/progress", response_model=UrnProgressResponse)
def get_urn_progress(
    urn_slug: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UrnProgressResponse:
    urn = db.execute(select(Urn).where(Urn.slug == urn_slug)).scalar_one_or_none()
    if urn is None:
        raise HTTPException(status_code=404, detail="Urn not found")

    motif_ids = [
        row[0]
        for row in db.execute(
            select(Motif.id).where(Motif.urn_id == urn.id, Motif.is_active.is_(True))
        ).all()
    ]
    if not motif_ids:
        return UrnProgressResponse(urn_id=urn.id, urn_slug=urn.slug, motifs=[])

    progress_entries = (
        db.execute(
            select(UserProgress).where(
                UserProgress.user_id == current_user.id,
                UserProgress.motif_id.in_(motif_ids),
            )
        )
        .scalars()
        .all()
    )
    progress_by_id = {p.motif_id: p for p in progress_entries}

    return UrnProgressResponse(
        urn_id=urn.id,
        urn_slug=urn.slug,
        motifs=[
            MotifProgressOut(
                motif_id=motif_id,
                status=(
                    progress_by_id[motif_id].status.value
                    if motif_id in progress_by_id
                    else UnlockStatus.hidden.value
                ),
                discovered_at=(
                    progress_by_id[motif_id].discovered_at
                    if motif_id in progress_by_id
                    else None
                ),
                lesson_viewed_at=(
                    progress_by_id[motif_id].lesson_viewed_at
                    if motif_id in progress_by_id
                    else None
                ),
                learned_at=(
                    progress_by_id[motif_id].learned_at
                    if motif_id in progress_by_id
                    else None
                ),
                mastered_at=(
                    progress_by_id[motif_id].mastered_at
                    if motif_id in progress_by_id
                    else None
                ),
                quiz_attempts=(
                    int(progress_by_id[motif_id].quiz_attempts)
                    if motif_id in progress_by_id
                    else 0
                ),
                quiz_best_score=(
                    int(progress_by_id[motif_id].quiz_best_score)
                    if motif_id in progress_by_id
                    else 0
                ),
                xp_earned=(
                    int(progress_by_id[motif_id].xp_earned)
                    if motif_id in progress_by_id
                    else 0
                ),
            )
            for motif_id in motif_ids
        ],
    )


class UrnListItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    slug: str
    name: str
    model_url: str
    thumbnail_url: Optional[str] = None
    display_order: int
    is_demo: bool
    motif_count: int = 0
    discovered_count: int = 0
    learned_count: int = 0
    mastered_count: int = 0


@app.get("/api/v1/urns", response_model=list[UrnListItemOut])
def list_urns(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[UrnListItemOut]:
    # Subquery for total motif counts per urn
    motif_counts = (
        select(Motif.urn_id, func.count(Motif.id).label("motif_count"))
        .where(Motif.is_active.is_(True))
        .group_by(Motif.urn_id)
        .subquery()
    )

    # Subquery for user progress counts per urn
    progress_counts = (
        select(
            Motif.urn_id,
            func.sum(
                case((UserProgress.status == UnlockStatus.discovered, 1), else_=0)
            ).label("discovered_count"),
            func.sum(
                case((UserProgress.status == UnlockStatus.learned, 1), else_=0)
            ).label("learned_count"),
            func.sum(
                case((UserProgress.status == UnlockStatus.mastered, 1), else_=0)
            ).label("mastered_count"),
        )
        .select_from(Motif)
        .join(
            UserProgress,
            and_(
                UserProgress.motif_id == Motif.id,
                UserProgress.user_id == current_user.id,
            ),
            isouter=True,
        )
        .where(Motif.is_active.is_(True))
        .group_by(Motif.urn_id)
        .subquery()
    )

    rows = db.execute(
        select(
            Urn,
            func.coalesce(motif_counts.c.motif_count, 0),
            func.coalesce(progress_counts.c.discovered_count, 0),
            func.coalesce(progress_counts.c.learned_count, 0),
            func.coalesce(progress_counts.c.mastered_count, 0),
        )
        .outerjoin(motif_counts, motif_counts.c.urn_id == Urn.id)
        .outerjoin(progress_counts, progress_counts.c.urn_id == Urn.id)
        .order_by(Urn.display_order, Urn.name)
    ).all()

    return [
        UrnListItemOut(
            id=urn.id,
            slug=urn.slug,
            name=urn.name,
            model_url=urn.model_url,
            thumbnail_url=urn.thumbnail_url,
            display_order=urn.display_order,
            is_demo=urn.is_demo,
            motif_count=int(motif_count or 0),
            discovered_count=int(discovered or 0),
            learned_count=int(learned or 0),
            mastered_count=int(mastered or 0),
        )
        for urn, motif_count, discovered, learned, mastered in rows
    ]


class UrnDetailOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    slug: str
    name: str
    name_han: Optional[str] = None
    represents: Optional[str] = None
    description: Optional[str] = None
    model_url: str
    thumbnail_url: Optional[str] = None
    display_order: int
    is_demo: bool


class UrnDetailResponse(BaseModel):
    urn: UrnDetailOut
    motifs: list[MotifOut]


@app.get("/api/v1/urns/{urn_slug}", response_model=UrnDetailResponse)
def get_urn_detail(
    urn_slug: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UrnDetailResponse:
    urn = db.execute(select(Urn).where(Urn.slug == urn_slug)).scalar_one_or_none()
    if urn is None:
        raise HTTPException(status_code=404, detail="Urn not found")

    motifs = (
        db.execute(
            select(Motif)
            .options(selectinload(Motif.lesson))
            .where(Motif.urn_id == urn.id, Motif.is_active.is_(True))
            .order_by(Motif.display_order.nulls_last(), Motif.name)
        )
        .scalars()
        .all()
    )

    can_view_drafts = _can_view_drafts(current_user)

    return UrnDetailResponse(
        urn=UrnDetailOut.model_validate(urn),
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
                lesson_intro=(
                    m.lesson.intro_text
                    if m.lesson and (m.lesson.is_published or can_view_drafts)
                    else None
                ),
            )
            for m in motifs
        ],
    )


class LessonContentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    intro_text: Optional[str] = None
    description: str
    historical_context: Optional[str] = None
    symbolism: Optional[str] = None
    fun_fact: Optional[str] = None
    is_ai_generated: bool = False
    audio_narration_url: Optional[str] = None
    additional_images: Optional[Any] = None
    video_url: Optional[str] = None


class MotifQuizQuestionOut(BaseModel):
    # Pre-submission payload: the answer key (correct_answer) and per-question
    # explanation are intentionally excluded so the client never receives answers
    # before submitting. Grading is server-authoritative (Requirement 4.2).
    id: UUID
    question_type: str
    question_text: str
    options: Optional[list[Any]] = None
    target_mesh_name: Optional[str] = None
    difficulty: int = 1
    image_url: Optional[str] = None


class UserProgressDetailOut(BaseModel):
    """User progress for a specific motif."""

    id: UUID
    user_id: UUID
    motif_id: UUID
    status: str  # hidden, discovered, learned, mastered
    discovered_at: Optional[datetime] = None
    learned_at: Optional[datetime] = None
    mastered_at: Optional[datetime] = None
    xp_earned: int = 0
    quiz_best_score: Optional[int] = None


class MotifDetailOut(BaseModel):
    id: UUID
    urn: UrnOut
    mesh_name: str
    name: str
    name_en: Optional[str] = None
    category: str
    rarity: str
    thumbnail_url: Optional[str] = None
    silhouette_url: Optional[str] = None
    image_url: Optional[str] = None
    is_demo: bool
    display_order: Optional[int] = None
    lesson: Optional[LessonContentOut] = None
    quiz_question_count: int = 0
    quiz_questions: list[MotifQuizQuestionOut] = Field(default_factory=list)
    progress: Optional[UserProgressDetailOut] = None  # User's progress for this motif


@app.get("/api/v1/motifs/{motif_id}", response_model=MotifDetailOut)
def get_motif_detail(
    motif_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MotifDetailOut:
    motif = db.execute(
        select(Motif)
        .options(
            selectinload(Motif.urn),
            selectinload(Motif.lesson),
            selectinload(Motif.quiz_questions),
        )
        .where(Motif.id == motif_id, Motif.is_active.is_(True))
    ).scalar_one_or_none()
    if motif is None:
        raise HTTPException(status_code=404, detail="Motif not found")

    # Check content rating access
    allowed_ratings = get_allowed_content_ratings(current_user)
    if motif.content_rating not in allowed_ratings:
        raise HTTPException(
            status_code=403,
            detail="You do not have access to this content. Please verify your age.",
        )

    # Query user progress for this motif
    user_progress_out = None
    if current_user:
        progress_row = db.execute(
            select(UserProgress).where(
                UserProgress.user_id == current_user.id,
                UserProgress.motif_id == motif.id,
            )
        ).scalar_one_or_none()

        if progress_row:
            user_progress_out = UserProgressDetailOut(
                id=progress_row.id,
                user_id=progress_row.user_id,
                motif_id=progress_row.motif_id,
                status=progress_row.status.value,
                discovered_at=progress_row.discovered_at,
                learned_at=progress_row.learned_at,
                mastered_at=progress_row.mastered_at,
                xp_earned=progress_row.xp_earned,
                quiz_best_score=progress_row.quiz_best_score,
            )

    can_view_drafts = _can_view_drafts(current_user)
    lesson_out = (
        LessonContentOut.model_validate(motif.lesson)
        if motif.lesson and (motif.lesson.is_published or can_view_drafts)
        else None
    )
    quiz_questions = [
        MotifQuizQuestionOut(
            id=q.id,
            question_type=q.question_type.value,
            question_text=q.question_text,
            options=q.options if isinstance(q.options, list) else None,
            target_mesh_name=q.target_mesh_name,
            difficulty=max(1, int(q.difficulty or 1)),
            image_url=None,
        )
        for q in motif.quiz_questions
        if q.is_active and (q.is_published or can_view_drafts)
    ]

    return MotifDetailOut(
        id=motif.id,
        urn=UrnOut.model_validate(motif.urn),
        mesh_name=motif.mesh_name,
        name=motif.name,
        name_en=motif.name_en,
        category=motif.category.value,
        rarity=motif.rarity.value,
        thumbnail_url=motif.thumbnail_url,
        silhouette_url=motif.silhouette_url,
        image_url=motif.thumbnail_url,
        is_demo=motif.is_demo,
        display_order=motif.display_order,
        lesson=lesson_out,
        quiz_question_count=len(quiz_questions),
        quiz_questions=quiz_questions,
        progress=user_progress_out,
    )


class LessonCompleteResponse(BaseModel):
    user_id: UUID
    motif_id: UUID
    status: str
    lesson_viewed_at: Optional[datetime] = None
    learned_at: Optional[datetime] = None
    xp_awarded: int
    total_xp: int


@app.post(
    "/api/v1/motifs/{motif_id}/complete-lesson", response_model=LessonCompleteResponse
)
def complete_lesson(
    motif_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> LessonCompleteResponse:
    motif = db.get(Motif, motif_id)
    if motif is None or not motif.is_active:
        raise HTTPException(status_code=404, detail="Motif not found")

    if current_user.role.value == "guest" and not motif.is_demo:
        raise HTTPException(status_code=403, detail="Guests can only learn demo motifs")

    if not _can_view_drafts(current_user):
        lesson = db.execute(
            select(LessonContent).where(LessonContent.motif_id == motif.id)
        ).scalar_one_or_none()
        if lesson is not None and not lesson.is_published:
            raise HTTPException(status_code=403, detail="Lesson not published")

    now = datetime.now(timezone.utc)

    progress = db.execute(
        select(UserProgress).where(
            UserProgress.user_id == current_user.id, UserProgress.motif_id == motif.id
        )
    ).scalar_one_or_none()
    discovered_before = db.execute(
        select(func.count(UserProgress.id)).where(
            UserProgress.user_id == current_user.id,
            UserProgress.status != UnlockStatus.hidden,
        )
    ).scalar_one()
    was_locked = progress is None or progress.status == UnlockStatus.hidden

    xp_awarded = 0
    target_xp = DISCOVERY_XP + LESSON_XP

    if progress is None:
        progress = UserProgress(
            user_id=current_user.id,
            motif_id=motif.id,
            status=UnlockStatus.learned,
            discovered_at=now,
            lesson_viewed_at=now,
            learned_at=now,
            xp_earned=target_xp,
        )
        db.add(progress)
        # Apply XP boost if active
        xp_with_boost = _apply_xp_boost(current_user, target_xp, now)
        current_user.total_xp += xp_with_boost
        xp_awarded = xp_with_boost
    else:
        if progress.status in (UnlockStatus.hidden, UnlockStatus.discovered):
            progress.status = UnlockStatus.learned
            progress.learned_at = progress.learned_at or now
            progress.discovered_at = progress.discovered_at or now

        progress.lesson_viewed_at = progress.lesson_viewed_at or now

        if progress.xp_earned < target_xp:
            delta = target_xp - progress.xp_earned
            progress.xp_earned = target_xp
            # Apply XP boost if active
            delta_with_boost = _apply_xp_boost(current_user, delta, now)
            current_user.total_xp += delta_with_boost
            xp_awarded = delta_with_boost

    badge_bonus = 0
    _update_streak(current_user, now)
    if was_locked and int(discovered_before or 0) == 0:
        badge_bonus += _award_badge(
            db, user=current_user, badge_slug=BADGE_FIRST_DISCOVERY
        )

    # Track first lesson completion milestone
    learned_before = db.execute(
        select(func.count(UserProgress.id)).where(
            UserProgress.user_id == current_user.id,
            UserProgress.status.in_([UnlockStatus.learned, UnlockStatus.mastered]),
        )
    ).scalar_one()
    if learned_before == 0 or (
        learned_before == 1 and progress.status == UnlockStatus.learned
    ):
        from backend.services.milestones import check_and_create_first_lesson_completed

        check_and_create_first_lesson_completed(db, current_user.id, motif.id)

    if current_user.current_streak >= 7:
        badge_bonus += _award_badge(db, user=current_user, badge_slug=BADGE_STREAK_7)
        # Track first 7-day streak milestone
        from backend.services.milestones import check_and_create_first_streak_7

        check_and_create_first_streak_7(
            db, current_user.id, current_user.current_streak
        )

    current_user.last_active_at = now

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        logger.warning(
            "IntegrityError during complete-lesson; retrying fetch/update",
            exc_info=True,
        )
        badge_bonus = 0
        discovered_before = db.execute(
            select(func.count(UserProgress.id)).where(
                UserProgress.user_id == current_user.id,
                UserProgress.status != UnlockStatus.hidden,
            )
        ).scalar_one()
        progress = db.execute(
            select(UserProgress).where(
                UserProgress.user_id == current_user.id,
                UserProgress.motif_id == motif.id,
            )
        ).scalar_one()
        was_locked = progress.status == UnlockStatus.hidden
        if progress.status in (UnlockStatus.hidden, UnlockStatus.discovered):
            progress.status = UnlockStatus.learned
            progress.learned_at = progress.learned_at or now
            progress.discovered_at = progress.discovered_at or now
        progress.lesson_viewed_at = progress.lesson_viewed_at or now
        if progress.xp_earned < target_xp:
            delta = target_xp - progress.xp_earned
            progress.xp_earned = target_xp
            # Apply XP boost if active
            delta_with_boost = _apply_xp_boost(current_user, delta, now)
            current_user.total_xp += delta_with_boost
            xp_awarded = max(xp_awarded, delta_with_boost)
        _update_streak(current_user, now)
        if was_locked and int(discovered_before or 0) == 0:
            badge_bonus += _award_badge(
                db, user=current_user, badge_slug=BADGE_FIRST_DISCOVERY
            )
        if current_user.current_streak >= 7:
            badge_bonus += _award_badge(
                db, user=current_user, badge_slug=BADGE_STREAK_7
            )
        current_user.last_active_at = now
        db.commit()

    _record_analytics_event(
        db,
        user_id=current_user.id,
        name="lesson_completed",
        payload={
            "source": "server",
            "motif_id": str(motif.id),
            "urn_id": str(motif.urn_id),
            "status": progress.status.value,
            "xp_awarded": xp_awarded + badge_bonus,
        },
    )

    return LessonCompleteResponse(
        user_id=current_user.id,
        motif_id=motif.id,
        status=progress.status.value,
        lesson_viewed_at=progress.lesson_viewed_at,
        learned_at=progress.learned_at,
        xp_awarded=xp_awarded + badge_bonus,
        total_xp=current_user.total_xp,
    )


# =============================================================================
# Offline Lesson Caching Endpoints
# =============================================================================


@app.get("/api/v1/lessons/cache-manifest", response_model=schemas.CacheManifestOut)
def get_cache_manifest(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.CacheManifestOut:
    """Get a manifest of lessons available for offline caching.

    Returns lessons with metadata about files to cache, estimated sizes,
    and caching priority based on user progress.
    """
    # Get all published lessons with their motifs
    lessons = (
        db.execute(
            select(LessonContent)
            .options(selectinload(LessonContent.motif))
            .where(LessonContent.is_published.is_(True))
            .order_by(LessonContent.updated_at.desc())
        )
        .scalars()
        .all()
    )

    # Get user's progress to determine priority
    user_progress = {
        p.motif_id: p
        for p in db.execute(
            select(UserProgress).where(UserProgress.user_id == current_user.id)
        )
        .scalars()
        .all()
    }

    manifest_items = []
    total_size = 0

    for lesson in lessons:
        if not lesson.motif or not lesson.motif.is_active:
            continue

        # Determine priority based on user progress
        progress = user_progress.get(lesson.motif_id)
        if progress and progress.status in (
            UnlockStatus.discovered,
            UnlockStatus.learned,
        ):
            priority = 1  # High priority - discovered or learned
        elif progress and progress.status == UnlockStatus.mastered:
            priority = 3  # Low priority - already mastered
        else:
            priority = 2  # Medium priority - not yet discovered

        # Build list of files to cache
        file_urls = []
        lesson_size = 0

        # Lesson content (estimate ~5KB per lesson)
        lesson_size += 5000

        # Audio narration
        if lesson.audio_narration_url:
            file_urls.append(
                schemas.CacheFileInfo(
                    url=lesson.audio_narration_url,
                    type="audio",
                    size_bytes=500000,  # Estimate 500KB for audio
                )
            )
            lesson_size += 500000

        # Video
        if lesson.video_url:
            file_urls.append(
                schemas.CacheFileInfo(
                    url=lesson.video_url,
                    type="video",
                    size_bytes=5000000,  # Estimate 5MB for video
                )
            )
            lesson_size += 5000000

        # Additional images
        if lesson.additional_images and isinstance(lesson.additional_images, list):
            for img_url in lesson.additional_images:
                if isinstance(img_url, str):
                    file_urls.append(
                        schemas.CacheFileInfo(
                            url=img_url,
                            type="image",
                            size_bytes=100000,  # Estimate 100KB per image
                        )
                    )
                    lesson_size += 100000

        # Motif images
        if lesson.motif.thumbnail_url:
            file_urls.append(
                schemas.CacheFileInfo(
                    url=lesson.motif.thumbnail_url,
                    type="image",
                    size_bytes=50000,  # Estimate 50KB for thumbnail
                )
            )
            lesson_size += 50000

        if lesson.motif.silhouette_url:
            file_urls.append(
                schemas.CacheFileInfo(
                    url=lesson.motif.silhouette_url,
                    type="image",
                    size_bytes=30000,  # Estimate 30KB for silhouette
                )
            )
            lesson_size += 30000

        manifest_items.append(
            schemas.CacheManifestItemOut(
                lesson_id=lesson.id,
                motif_id=lesson.motif_id,
                motif_name=lesson.motif.name,
                title=lesson.motif.name,
                version=lesson.version,
                file_urls=file_urls,
                total_size_bytes=lesson_size,
                priority=priority,
            )
        )
        total_size += lesson_size

    # Sort by priority (1=high, 2=medium, 3=low)
    manifest_items.sort(key=lambda x: (x.priority, x.motif_name))

    return schemas.CacheManifestOut(
        lessons=manifest_items,
        total_size_bytes=total_size,
        recommended_cache_size_bytes=50 * 1024 * 1024,  # 50MB recommendation
    )


@app.post("/api/v1/lessons/{lesson_id}/cache", response_model=schemas.LessonCacheOut)
def mark_lesson_cached(
    lesson_id: UUID,
    payload: schemas.LessonCacheIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.LessonCacheOut:
    """Mark a lesson as cached by the user."""
    # Verify lesson exists
    lesson = db.get(LessonContent, lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    # Check if already cached
    existing_cache = db.execute(
        select(LessonCache).where(
            LessonCache.user_id == current_user.id,
            LessonCache.lesson_id == lesson_id,
        )
    ).scalar_one_or_none()

    now = datetime.now(timezone.utc)
    expires = now + timedelta(days=30)  # Cache valid for 30 days

    if existing_cache:
        # Update existing cache entry
        existing_cache.cached_at = now
        existing_cache.cache_version = payload.cache_version
        existing_cache.file_size_bytes = payload.file_size_bytes
        existing_cache.is_valid = True
        existing_cache.expires_at = expires
        db.commit()
        db.refresh(existing_cache)
        return schemas.LessonCacheOut.model_validate(existing_cache)

    # Create new cache entry
    cache_entry = LessonCache(
        id=uuid_module.uuid4(),
        user_id=current_user.id,
        lesson_id=lesson_id,
        cached_at=now,
        cache_version=payload.cache_version,
        file_size_bytes=payload.file_size_bytes,
        is_valid=True,
        expires_at=expires,
    )
    db.add(cache_entry)
    db.commit()
    db.refresh(cache_entry)

    return schemas.LessonCacheOut.model_validate(cache_entry)


@app.delete("/api/v1/lessons/{lesson_id}/cache", status_code=status.HTTP_204_NO_CONTENT)
def remove_cached_lesson(
    lesson_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """Remove a lesson from the user's cache."""
    result = db.execute(
        delete(LessonCache).where(
            LessonCache.user_id == current_user.id,
            LessonCache.lesson_id == lesson_id,
        )
    )
    db.commit()

    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Cached lesson not found")


@app.get("/api/v1/lessons/cached", response_model=list[schemas.LessonCacheOut])
def get_cached_lessons(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[schemas.LessonCacheOut]:
    """Get all lessons cached by the user."""
    cached_lessons = (
        db.execute(
            select(LessonCache)
            .where(LessonCache.user_id == current_user.id)
            .order_by(LessonCache.cached_at.desc())
        )
        .scalars()
        .all()
    )

    return [schemas.LessonCacheOut.model_validate(cache) for cache in cached_lessons]


# =============================================================================
# Lesson Prerequisites and Sequence Endpoints
# =============================================================================


@app.get("/api/v1/lessons/next", response_model=schemas.NextLessonOut)
def get_next_lesson(
    urn_id: Optional[UUID] = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.NextLessonOut:
    """
    Get the next recommended lesson for the user.

    This endpoint determines the best next lesson based on:
    - User's current progress
    - Prerequisites and unlock status
    - Difficulty progression
    - Urn context (if provided)

    Args:
        urn_id: Optional urn to filter lessons from
        current_user: Authenticated user
        db: Database session

    Returns:
        Next lesson recommendation or null if no suitable lesson found
    """
    from .services import lesson_sequence

    next_lesson = lesson_sequence.get_next_lesson(db, current_user, urn_id)

    if not next_lesson:
        # Return empty response if no next lesson
        return schemas.NextLessonOut(
            lesson_id=None,
            motif_id=None,
            motif_name=None,
            motif_slug=None,
            urn_id=urn_id,
            urn_name=None,
            difficulty_level=None,
            estimated_time_minutes=None,
            reason="no_lessons_available",
            has_prerequisites=False,
            progress_status=None,
        )

    return schemas.NextLessonOut(**next_lesson)


@app.get(
    "/api/v1/lessons/{lesson_id}/prerequisites",
    response_model=schemas.LessonPrerequisitesOut,
)
def get_lesson_prerequisites(
    lesson_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.LessonPrerequisitesOut:
    """
    Get all prerequisites for a specific lesson.

    Returns the list of prerequisite lessons with their completion status
    and whether all prerequisites have been met.

    Args:
        lesson_id: ID of the lesson
        current_user: Authenticated user
        db: Database session

    Returns:
        Prerequisite information including completion status
    """
    from .services import lesson_sequence

    # Verify lesson exists
    lesson = db.get(LessonContent, lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    prereq_info = lesson_sequence.get_lesson_prerequisites(db, current_user, lesson_id)

    return schemas.LessonPrerequisitesOut(
        lesson_id=prereq_info["lesson_id"],
        prerequisites=[
            schemas.PrerequisiteLessonInfo(**p) for p in prereq_info["prerequisites"]
        ],
        all_prerequisites_met=prereq_info["all_prerequisites_met"],
    )


@app.get(
    "/api/v1/lessons/{lesson_id}/is-unlocked",
    response_model=schemas.LessonUnlockStatusOut,
)
def check_lesson_is_unlocked(
    lesson_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.LessonUnlockStatusOut:
    """
    Check if a lesson is unlocked for the user.

    A lesson is unlocked if all strict prerequisites have been completed.
    Recommended prerequisites don't block access but are shown for guidance.

    Args:
        lesson_id: ID of the lesson
        current_user: Authenticated user
        db: Database session

    Returns:
        Unlock status with missing prerequisites
    """
    from .services import lesson_sequence

    # Verify lesson exists
    lesson = db.get(LessonContent, lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    is_unlocked, missing_strict, missing_recommended = (
        lesson_sequence.check_lesson_unlocked(db, current_user, lesson_id)
    )

    def format_prereq_lesson(
        prereq_lesson: LessonContent,
    ) -> schemas.PrerequisiteLessonInfo:
        return schemas.PrerequisiteLessonInfo(
            id=prereq_lesson.id,
            motif_id=prereq_lesson.motif_id,
            motif_name=prereq_lesson.motif.name,
            motif_slug=prereq_lesson.motif.slug,
            difficulty_level=prereq_lesson.difficulty_level,
            estimated_time_minutes=prereq_lesson.estimated_time_minutes,
            is_strict=True,  # These are from strict list
            is_completed=False,  # By definition, these are missing
        )

    def format_recommended_prereq(
        prereq_lesson: LessonContent,
    ) -> schemas.PrerequisiteLessonInfo:
        return schemas.PrerequisiteLessonInfo(
            id=prereq_lesson.id,
            motif_id=prereq_lesson.motif_id,
            motif_name=prereq_lesson.motif.name,
            motif_slug=prereq_lesson.motif.slug,
            difficulty_level=prereq_lesson.difficulty_level,
            estimated_time_minutes=prereq_lesson.estimated_time_minutes,
            is_strict=False,  # These are recommended only
            is_completed=False,
        )

    return schemas.LessonUnlockStatusOut(
        lesson_id=lesson_id,
        is_unlocked=is_unlocked,
        missing_prerequisites=[format_prereq_lesson(p) for p in missing_strict],
        recommended_prerequisites=[
            format_recommended_prereq(p) for p in missing_recommended
        ],
    )


@app.get("/api/v1/lessons/sequence", response_model=schemas.LessonSequenceOut)
def get_lesson_sequence(
    urn_id: Optional[UUID] = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.LessonSequenceOut:
    """
    Get the full learning sequence for the user.

    Returns an ordered list of all lessons (optionally filtered by urn)
    with their unlock status, completion status, and position in the sequence.

    Args:
        urn_id: Optional urn to filter lessons from
        current_user: Authenticated user
        db: Database session

    Returns:
        Complete learning sequence with progress information
    """
    from .services import lesson_sequence

    sequence_data = lesson_sequence.get_lesson_sequence(db, current_user, urn_id)

    return schemas.LessonSequenceOut(
        urn_id=sequence_data["urn_id"],
        urn_name=sequence_data["urn_name"],
        total_lessons=sequence_data["total_lessons"],
        completed_lessons=sequence_data["completed_lessons"],
        current_position=sequence_data["current_position"],
        sequence=[
            schemas.LessonSequenceItem(**item) for item in sequence_data["sequence"]
        ],
    )


class TapPosition(BaseModel):
    x: float
    y: float
    z: float


class ProgressUnlockRequest(BaseModel):
    motif_id: Optional[UUID] = None
    mesh_name: Optional[str] = None
    tap_position: Optional[TapPosition] = None

    @model_validator(mode="after")
    def _validate_reference(self) -> "ProgressUnlockRequest":
        if self.motif_id is None and not self.mesh_name:
            raise ValueError("Either motif_id or mesh_name is required.")
        return self


class ProgressResponseDto(BaseModel):
    """Progress DTO matching mobile UnlockResponseDto.progress structure."""

    id: UUID
    user_id: UUID
    motif_id: UUID
    status: str
    discovered_at: Optional[datetime] = None
    learned_at: Optional[datetime] = None
    mastered_at: Optional[datetime] = None
    xp_earned: int = 0
    quiz_best_score: Optional[int] = None


class BadgeResponseDto(BaseModel):
    """Badge DTO for new badges earned."""

    id: UUID
    slug: str
    name: str
    description: Optional[str] = None
    icon_url: Optional[str] = None
    xp_bonus: int = 0


class ProgressUnlockResponse(BaseModel):
    """Response matching mobile UnlockResponseDto structure."""

    progress: ProgressResponseDto
    xp_earned: int
    total_xp: int
    new_badges: list[BadgeResponseDto] = []
    streak_updated: bool = False
    current_streak: int = 0


@app.post("/progress/unlock", response_model=ProgressUnlockResponse)
def unlock_progress(
    payload: ProgressUnlockRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProgressUnlockResponse:
    user = current_user

    if payload.motif_id is not None:
        motif = db.get(Motif, payload.motif_id)
    else:
        motif = db.execute(
            select(Motif).where(Motif.mesh_name == payload.mesh_name)
        ).scalar_one_or_none()

    if motif is None:
        raise HTTPException(status_code=404, detail="Motif not found")

    if payload.mesh_name is not None and motif.mesh_name != payload.mesh_name:
        raise HTTPException(status_code=400, detail="mesh_name does not match motif")

    if user.role.value == "guest" and not motif.is_demo:
        raise HTTPException(
            status_code=403, detail="Guests can only unlock demo motifs"
        )

    # Note: tap_position validation removed - user clicks directly on hotspot spheres
    # which are already positioned at the correct motif location
    # Keeping tap_position in API for potential future analytics/logging

    now = datetime.now(timezone.utc)

    progress = db.execute(
        select(UserProgress).where(
            UserProgress.user_id == user.id, UserProgress.motif_id == motif.id
        )
    ).scalar_one_or_none()
    discovered_before = db.execute(
        select(func.count(UserProgress.id)).where(
            UserProgress.user_id == user.id,
            UserProgress.status != UnlockStatus.hidden,
        )
    ).scalar_one()
    was_locked = progress is None or progress.status == UnlockStatus.hidden

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

    badge_bonus = 0
    new_badges: list[Badge] = []
    streak_before = user.current_streak
    _update_streak(user, now)
    streak_updated = user.current_streak != streak_before

    def _try_award_badge(badge_slug: str) -> int:
        """Award badge and track it if newly earned."""
        nonlocal new_badges
        badge = db.execute(
            select(Badge).where(Badge.slug == badge_slug, Badge.is_active.is_(True))
        ).scalar_one_or_none()
        if badge is None:
            return 0
        existing = db.execute(
            select(UserBadge).where(
                UserBadge.user_id == user.id, UserBadge.badge_id == badge.id
            )
        ).scalar_one_or_none()
        if existing is not None:
            return 0
        bonus = _award_badge(db, user=user, badge_slug=badge_slug)
        if bonus > 0 or existing is None:
            # Re-check if badge was just awarded
            newly_awarded = db.execute(
                select(UserBadge).where(
                    UserBadge.user_id == user.id, UserBadge.badge_id == badge.id
                )
            ).scalar_one_or_none()
            if newly_awarded is not None:
                new_badges.append(badge)
        return bonus

    if was_locked and int(discovered_before or 0) == 0:
        badge_bonus += _try_award_badge(BADGE_FIRST_DISCOVERY)
        # Track first motif discovery milestone
        from backend.services.milestones import check_and_create_first_motif_discovered

        check_and_create_first_motif_discovered(db, user.id, motif.id)
    if user.current_streak >= 7:
        badge_bonus += _try_award_badge(BADGE_STREAK_7)
        # Track first 7-day streak milestone
        from backend.services.milestones import check_and_create_first_streak_7

        check_and_create_first_streak_7(db, user.id, user.current_streak)

    # Check collector badges
    discovered, urns = _count_user_discoveries(db, user.id)
    if was_locked and (progress in db.new or progress in db.dirty):
        discovered += 1
        urn_discovered_before = db.execute(
            select(func.count(UserProgress.id))
            .select_from(UserProgress)
            .join(Motif, UserProgress.motif_id == Motif.id)
            .where(
                UserProgress.user_id == user.id,
                UserProgress.status != UnlockStatus.hidden,
                Motif.urn_id == motif.urn_id,
            )
        ).scalar_one()
        if urn_discovered_before == 0:
            urns += 1
    if discovered >= 10:
        badge_bonus += _try_award_badge(BADGE_COLLECTOR_10)
    if discovered >= 50:
        badge_bonus += _try_award_badge(BADGE_COLLECTOR_50)
    if urns >= 9:
        badge_bonus += _try_award_badge(BADGE_EXPLORER_ALL_URNS)

    user.last_active_at = now

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        logger.warning(
            "IntegrityError during unlock; retrying fetch/update", exc_info=True
        )
        badge_bonus = 0
        new_badges = []  # Clear badges on retry
        discovered_before = db.execute(
            select(func.count(UserProgress.id)).where(
                UserProgress.user_id == user.id,
                UserProgress.status != UnlockStatus.hidden,
            )
        ).scalar_one()
        progress = db.execute(
            select(UserProgress).where(
                UserProgress.user_id == user.id, UserProgress.motif_id == motif.id
            )
        ).scalar_one()
        was_locked = progress.status == UnlockStatus.hidden
        if progress.status == UnlockStatus.hidden:
            progress.status = UnlockStatus.discovered
            progress.discovered_at = progress.discovered_at or now
        if progress.xp_earned < DISCOVERY_XP:
            delta = DISCOVERY_XP - progress.xp_earned
            progress.xp_earned = DISCOVERY_XP
            user.total_xp += delta
            xp_awarded = max(xp_awarded, delta)
        streak_before = user.current_streak
        _update_streak(user, now)
        streak_updated = user.current_streak != streak_before
        if was_locked and int(discovered_before or 0) == 0:
            badge_bonus += _try_award_badge(BADGE_FIRST_DISCOVERY)
        if user.current_streak >= 7:
            badge_bonus += _try_award_badge(BADGE_STREAK_7)
        # Check collector badges
        discovered, urns = _count_user_discoveries(db, user.id)
        if was_locked and (progress in db.new or progress in db.dirty):
            discovered += 1
            urn_discovered_before = db.execute(
                select(func.count(UserProgress.id))
                .select_from(UserProgress)
                .join(Motif, UserProgress.motif_id == Motif.id)
                .where(
                    UserProgress.user_id == user.id,
                    UserProgress.status != UnlockStatus.hidden,
                    Motif.urn_id == motif.urn_id,
                )
            ).scalar_one()
            if urn_discovered_before == 0:
                urns += 1
        if discovered >= 10:
            badge_bonus += _try_award_badge(BADGE_COLLECTOR_10)
        if discovered >= 50:
            badge_bonus += _try_award_badge(BADGE_COLLECTOR_50)
        if urns >= 9:
            badge_bonus += _try_award_badge(BADGE_EXPLORER_ALL_URNS)
        user.last_active_at = now
        db.commit()

    # Build the response matching mobile UnlockResponseDto structure
    progress_dto = ProgressResponseDto(
        id=progress.id,
        user_id=user.id,
        motif_id=motif.id,
        status=progress.status.value,
        discovered_at=progress.discovered_at,
        learned_at=progress.learned_at,
        mastered_at=progress.mastered_at,
        xp_earned=progress.xp_earned,
        quiz_best_score=progress.quiz_best_score,
    )

    badge_dtos = [
        BadgeResponseDto(
            id=badge.id,
            slug=badge.slug,
            name=badge.name,
            description=badge.description,
            icon_url=badge.icon_url,
            xp_bonus=badge.xp_bonus or 0,
        )
        for badge in new_badges
    ]

    return ProgressUnlockResponse(
        progress=progress_dto,
        xp_earned=xp_awarded + badge_bonus,
        total_xp=user.total_xp,
        new_badges=badge_dtos,
        streak_updated=streak_updated,
        current_streak=user.current_streak,
    )


@app.post("/api/v1/users/me/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        contents = await file.read(MAX_AVATAR_SIZE + 1)
        if len(contents) > MAX_AVATAR_SIZE:
            raise AppError(
                code="AVATAR_TOO_LARGE",
                message="Avatar file too large",
                status_code=status.HTTP_400_BAD_REQUEST,
                details={"max_bytes": MAX_AVATAR_SIZE},
            )

        # Validate by actual file content (magic bytes), never trusting the
        # client-declared Content-Type. Two distinct checks with distinct codes.
        detected_type = _detect_image_type(contents)

        # 1. Content-format check: the bytes must parse as a supported image.
        if detected_type is None:
            raise AppError(
                code="INVALID_IMAGE_CONTENT",
                message="Uploaded file is not a valid image",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        # 2. Type-authorization check: the content-derived type must be allowed.
        if detected_type not in ALLOWED_IMAGE_TYPES:
            raise AppError(
                code="INVALID_IMAGE_TYPE",
                message="Unsupported image type",
                status_code=status.HTTP_400_BAD_REQUEST,
                details={"content_type": detected_type},
            )

        # 3. Declared-vs-actual mismatch: reject spoofed Content-Type even when
        # both the declared and actual types are individually allowed.
        if file.content_type and file.content_type != detected_type:
            raise AppError(
                code="IMAGE_TYPE_MISMATCH",
                message="Declared content type does not match file content",
                status_code=status.HTTP_400_BAD_REQUEST,
                details={
                    "declared_type": file.content_type,
                    "detected_type": detected_type,
                },
            )

        extension = IMAGE_EXTENSION_BY_TYPE[detected_type]
        filename = f"{current_user.id}_{uuid_module.uuid4()}.{extension}"

        AVATAR_DIR.mkdir(parents=True, exist_ok=True)
        destination = AVATAR_DIR / filename
        with destination.open("wb") as handle:
            handle.write(contents)

        current_user.avatar_url = f"/uploads/avatars/{filename}"
        db.commit()

        return {"avatar_url": current_user.avatar_url}
    finally:
        await file.close()


class CollectionItemOut(BaseModel):
    motif_id: UUID
    mesh_name: str
    name: str
    name_en: Optional[str] = None
    category: str
    rarity: str
    thumbnail_url: Optional[str] = None
    status: str


class QuestProgressOut(BaseModel):
    quest_name: str
    total: int
    discovered: int
    progress_percent: float


class CollectionStatsOut(BaseModel):
    total: int
    discovered: int
    learned: int
    mastered: int
    quest: QuestProgressOut


class UserCollectionResponse(BaseModel):
    items: list[CollectionItemOut]
    stats: CollectionStatsOut


@app.post("/api/v1/users/me/change-password")
def change_password(
    request: ChangePasswordRequest,
    http_request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(request.current_password, current_user.password_hash):
        raise HTTPException(400, "Current password is incorrect")

    current_user.password_hash = hash_password(request.new_password)
    db.commit()

    # After a successful password change, revoke the presented refresh token
    # (if any) so a previously issued session cannot be replayed (Req 17.2).
    raw_token = http_request.cookies.get(settings.refresh_cookie_name)
    if raw_token:
        payload = _decode_refresh_token_best_effort(raw_token)
        if payload is not None:
            _revoke_refresh_jti(db, payload)

    return {"message": "Password changed successfully"}


@app.post("/api/v1/users/me/age-verify", response_model=schemas.AgeVerificationOut)
def verify_user_age(
    request: schemas.AgeVerificationIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.AgeVerificationOut:
    """
    Verify user's age by submitting birth year.

    This enables age-appropriate content filtering.
    """
    # Validate birth year is reasonable
    current_year = datetime.now(timezone.utc).year
    if request.birth_year < 1900 or request.birth_year > current_year:
        raise HTTPException(
            status_code=400,
            detail=f"Birth year must be between 1900 and {current_year}",
        )

    # Update user's age verification info
    current_user.birth_year = request.birth_year
    current_user.age_verified = True
    current_user.age_verified_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(current_user)

    # Calculate current age
    age = get_user_age(current_user)
    allowed_ratings = get_allowed_content_ratings(current_user)

    return schemas.AgeVerificationOut(
        age_verified=current_user.age_verified,
        age_verified_at=current_user.age_verified_at,
        birth_year=current_user.birth_year,
        current_age=age,
        allowed_ratings=[r.value for r in allowed_ratings],
    )


@app.get("/api/v1/content/ratings", response_model=schemas.ContentRatingsOut)
def get_content_ratings() -> schemas.ContentRatingsOut:
    """
    Get content rating definitions.

    Returns information about all available content ratings and their age requirements.
    """
    return schemas.ContentRatingsOut(
        ratings=[
            schemas.ContentRatingInfo(
                rating="everyone",
                label="Everyone",
                description="Suitable for all ages",
                min_age=None,
            ),
            schemas.ContentRatingInfo(
                rating="teen",
                label="Teen",
                description="Suitable for ages 13 and up",
                min_age=13,
            ),
            schemas.ContentRatingInfo(
                rating="mature",
                label="Mature",
                description="Suitable for ages 18 and up",
                min_age=18,
            ),
        ]
    )


@app.get("/api/v1/users/me/collection", response_model=UserCollectionResponse)
def get_my_collection(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> UserCollectionResponse:
    motifs = (
        db.execute(
            select(Motif)
            .where(Motif.is_active.is_(True))
            .order_by(Motif.display_order.nulls_last(), Motif.name)
        )
        .scalars()
        .all()
    )
    progress_entries = (
        db.execute(select(UserProgress).where(UserProgress.user_id == current_user.id))
        .scalars()
        .all()
    )
    progress_by_motif_id = {p.motif_id: p for p in progress_entries}

    discovered = learned = mastered = 0
    quest_total = quest_discovered = 0
    items: list[CollectionItemOut] = []

    for motif in motifs:
        progress = progress_by_motif_id.get(motif.id)
        status_value = progress.status.value if progress else UnlockStatus.hidden.value

        if status_value == UnlockStatus.discovered.value:
            discovered += 1
        elif status_value == UnlockStatus.learned.value:
            learned += 1
        elif status_value == UnlockStatus.mastered.value:
            mastered += 1

        if motif.category == MotifCategory.thao_moc:
            quest_total += 1
            if status_value != UnlockStatus.hidden.value:
                quest_discovered += 1

        items.append(
            CollectionItemOut(
                motif_id=motif.id,
                mesh_name=motif.mesh_name,
                name=motif.name,
                name_en=motif.name_en,
                category=motif.category.value,
                rarity=motif.rarity.value,
                thumbnail_url=motif.thumbnail_url,
                status=status_value,
            )
        )

    total = len(motifs)
    progress_percent = (
        (quest_discovered / quest_total * 100.0) if quest_total > 0 else 0.0
    )

    return UserCollectionResponse(
        items=items,
        stats=CollectionStatsOut(
            total=total,
            discovered=discovered,
            learned=learned,
            mastered=mastered,
            quest=QuestProgressOut(
                quest_name="Ngự Uyển Ký Sự (The Royal Gardens)",
                total=quest_total,
                discovered=quest_discovered,
                progress_percent=progress_percent,
            ),
        ),
    )


class QuestRewardOut(BaseModel):
    reward_type: str
    amount: Optional[int] = None
    badge_slug: Optional[str] = None
    metadata: Optional[Any] = None


class QuestObjectiveOut(BaseModel):
    id: UUID
    objective_type: str
    target_value: int
    current_value: int
    is_complete: bool
    params: Optional[dict[str, Any]] = None


class QuestStepOut(BaseModel):
    id: UUID
    title: str
    description: Optional[str] = None
    display_order: int
    completion_percent: float
    objectives: list[QuestObjectiveOut]


class QuestPrerequisiteOut(BaseModel):
    id: UUID
    slug: str
    name: str


class QuestListItemOut(BaseModel):
    id: UUID
    slug: str
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    display_order: int
    status: str
    progress_percent: float
    is_locked: bool
    lock_reason: Optional[str] = None
    prerequisite: Optional[QuestPrerequisiteOut] = None
    rewards: list[QuestRewardOut]


class QuestCertificateOut(BaseModel):
    code: str
    issued_at: datetime
    issuer_name: str


class QuestDetailOut(QuestListItemOut):
    steps: list[QuestStepOut]
    certificate: Optional[QuestCertificateOut] = None


class QuestSummaryObjectiveOut(BaseModel):
    objective_type: str
    current_value: int
    target_value: int


class QuestSummaryOut(BaseModel):
    quest_id: UUID
    quest_slug: str
    quest_name: str
    status: str
    progress_percent: float
    next_step_title: Optional[str] = None
    next_objective: Optional[QuestSummaryObjectiveOut] = None


def _quest_prerequisite_completed(
    session: Session,
    *,
    user_id: UUID,
    quest: Quest,
    progress_by_quest: dict[UUID, QuestProgress],
) -> bool:
    if not quest.prerequisite_id:
        return True
    prereq_progress = progress_by_quest.get(quest.prerequisite_id)
    if prereq_progress is not None:
        return prereq_progress.status == "completed"
    prereq = session.execute(
        select(QuestProgress).where(
            QuestProgress.user_id == user_id,
            QuestProgress.quest_id == quest.prerequisite_id,
        )
    ).scalar_one_or_none()
    return prereq is not None and prereq.status == "completed"


def _build_quest_rewards(quest: Quest) -> list[QuestRewardOut]:
    return [
        QuestRewardOut(
            reward_type=reward.reward_type,
            amount=int(reward.amount or 0) if reward.amount is not None else None,
            badge_slug=reward.badge_slug,
            metadata=reward.metadata_payload
            if isinstance(reward.metadata_payload, dict)
            else reward.metadata_payload,
        )
        for reward in quest.rewards
    ]


def _extract_next_objective(
    steps: list[dict[str, Any]],
) -> tuple[Optional[str], Optional[QuestSummaryObjectiveOut]]:
    for step in steps:
        for objective in step.get("objectives", []):
            if not objective.get("is_complete"):
                return (
                    step.get("title"),
                    QuestSummaryObjectiveOut(
                        objective_type=str(objective.get("objective_type")),
                        current_value=int(objective.get("current_value") or 0),
                        target_value=int(objective.get("target_value") or 0),
                    ),
                )
    return None, None


@app.get("/api/v1/quests", response_model=list[QuestListItemOut])
def list_quests(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[QuestListItemOut]:
    # Get allowed content ratings for the user
    allowed_ratings = get_allowed_content_ratings(current_user)

    quests = (
        db.execute(
            select(Quest)
            .options(
                selectinload(Quest.steps).selectinload(QuestStep.objectives),
                selectinload(Quest.rewards),
                selectinload(Quest.prerequisite),
            )
            .where(Quest.is_active.is_(True), Quest.content_rating.in_(allowed_ratings))
            .order_by(Quest.display_order.asc(), Quest.created_at.asc())
        )
        .scalars()
        .all()
    )
    if not quests:
        return []

    progress_entries = (
        db.execute(
            select(QuestProgress).where(
                QuestProgress.user_id == current_user.id,
                QuestProgress.quest_id.in_([q.id for q in quests]),
            )
        )
        .scalars()
        .all()
    )
    progress_by_quest = {p.quest_id: p for p in progress_entries}

    items: list[QuestListItemOut] = []
    for quest in quests:
        progress_entry = progress_by_quest.get(quest.id)
        prereq_complete = _quest_prerequisite_completed(
            db,
            user_id=current_user.id,
            quest=quest,
            progress_by_quest=progress_by_quest,
        )
        is_locked = not prereq_complete
        status = "locked" if is_locked else "not_started"
        progress_percent = 0.0

        if not is_locked and progress_entry is not None:
            steps_payload, progress_percent = _compute_quest_progress_data(
                db, user=current_user, quest=quest, progress_entry=progress_entry
            )
            if progress_entry.status != "completed" and progress_percent >= 100.0:
                _apply_quest_rewards(
                    db, user=current_user, quest=quest, progress_entry=progress_entry
                )
                db.commit()
                progress_percent = 100.0
            status = progress_entry.status

        items.append(
            QuestListItemOut(
                id=quest.id,
                slug=quest.slug,
                name=quest.name,
                description=quest.description,
                category=quest.category,
                display_order=int(quest.display_order or 0),
                status=status,
                progress_percent=progress_percent,
                is_locked=is_locked,
                lock_reason=(
                    f"Hoàn thành {quest.prerequisite.name}"
                    if is_locked and quest.prerequisite
                    else None
                ),
                prerequisite=(
                    QuestPrerequisiteOut(
                        id=quest.prerequisite.id,
                        slug=quest.prerequisite.slug,
                        name=quest.prerequisite.name,
                    )
                    if quest.prerequisite
                    else None
                ),
                rewards=_build_quest_rewards(quest),
            )
        )

    return items


@app.get("/api/v1/quests/{quest_slug}", response_model=QuestDetailOut)
def get_quest_detail(
    quest_slug: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> QuestDetailOut:
    quest = db.execute(
        select(Quest)
        .options(
            selectinload(Quest.steps).selectinload(QuestStep.objectives),
            selectinload(Quest.rewards),
            selectinload(Quest.prerequisite),
        )
        .where(Quest.slug == quest_slug, Quest.is_active.is_(True))
    ).scalar_one_or_none()
    if quest is None:
        raise HTTPException(status_code=404, detail="Quest not found")

    # Check content rating access
    allowed_ratings = get_allowed_content_ratings(current_user)
    if quest.content_rating not in allowed_ratings:
        raise HTTPException(
            status_code=403,
            detail="You do not have access to this content. Please verify your age.",
        )

    progress_entry = db.execute(
        select(QuestProgress).where(
            QuestProgress.user_id == current_user.id, QuestProgress.quest_id == quest.id
        )
    ).scalar_one_or_none()

    progress_by_quest = {quest.id: progress_entry} if progress_entry else {}
    prereq_complete = _quest_prerequisite_completed(
        db, user_id=current_user.id, quest=quest, progress_by_quest=progress_by_quest
    )
    is_locked = not prereq_complete
    status = "locked" if is_locked else "not_started"

    steps_payload, progress_percent = _compute_quest_progress_data(
        db, user=current_user, quest=quest, progress_entry=progress_entry
    )
    if progress_entry is not None:
        status = progress_entry.status
        if progress_entry.status != "completed" and progress_percent >= 100.0:
            _apply_quest_rewards(
                db, user=current_user, quest=quest, progress_entry=progress_entry
            )
            db.commit()
            progress_percent = 100.0
            status = "completed"

    certificate = db.execute(
        select(Certificate).where(
            Certificate.user_id == current_user.id,
            Certificate.reason_type == "quest",
            Certificate.reason_id == quest.id,
        )
    ).scalar_one_or_none()

    return QuestDetailOut(
        id=quest.id,
        slug=quest.slug,
        name=quest.name,
        description=quest.description,
        category=quest.category,
        display_order=int(quest.display_order or 0),
        status=status,
        progress_percent=progress_percent,
        is_locked=is_locked,
        lock_reason=(
            f"Hoàn thành {quest.prerequisite.name}"
            if is_locked and quest.prerequisite
            else None
        ),
        prerequisite=(
            QuestPrerequisiteOut(
                id=quest.prerequisite.id,
                slug=quest.prerequisite.slug,
                name=quest.prerequisite.name,
            )
            if quest.prerequisite
            else None
        ),
        rewards=_build_quest_rewards(quest),
        steps=[
            QuestStepOut(
                id=step["id"],
                title=step["title"],
                description=step["description"],
                display_order=step["display_order"],
                completion_percent=step["completion_percent"],
                objectives=[
                    QuestObjectiveOut(
                        id=obj["id"],
                        objective_type=obj["objective_type"],
                        target_value=obj["target_value"],
                        current_value=obj["current_value"],
                        is_complete=obj["is_complete"],
                        params=obj["params"],
                    )
                    for obj in step["objectives"]
                ],
            )
            for step in steps_payload
        ],
        certificate=(
            QuestCertificateOut(
                code=certificate.code,
                issued_at=certificate.issued_at,
                issuer_name=certificate.issuer_name,
            )
            if certificate is not None
            else None
        ),
    )


@app.post("/api/v1/quests/{quest_slug}/start", response_model=QuestDetailOut)
def start_quest(
    quest_slug: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> QuestDetailOut:
    quest = db.execute(
        select(Quest)
        .options(
            selectinload(Quest.steps).selectinload(QuestStep.objectives),
            selectinload(Quest.rewards),
            selectinload(Quest.prerequisite),
        )
        .where(Quest.slug == quest_slug, Quest.is_active.is_(True))
    ).scalar_one_or_none()
    if quest is None:
        raise HTTPException(status_code=404, detail="Quest not found")

    progress_entry = db.execute(
        select(QuestProgress).where(
            QuestProgress.user_id == current_user.id, QuestProgress.quest_id == quest.id
        )
    ).scalar_one_or_none()
    if progress_entry is None:
        prereq_complete = True
        if quest.prerequisite_id:
            prereq_complete = (
                db.execute(
                    select(QuestProgress).where(
                        QuestProgress.user_id == current_user.id,
                        QuestProgress.quest_id == quest.prerequisite_id,
                        QuestProgress.status == "completed",
                    )
                ).scalar_one_or_none()
                is not None
            )
        if not prereq_complete:
            raise HTTPException(status_code=403, detail="Quest is locked")

        progress_entry = QuestProgress(user_id=current_user.id, quest_id=quest.id)
        db.add(progress_entry)
        db.commit()
        db.refresh(progress_entry)

    return get_quest_detail(quest_slug, current_user=current_user, db=db)


@app.get("/api/v1/users/me/quest-summary", response_model=Optional[QuestSummaryOut])
def get_quest_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Optional[QuestSummaryOut]:
    active_progress = db.execute(
        select(QuestProgress)
        .join(Quest, QuestProgress.quest_id == Quest.id)
        .where(
            QuestProgress.user_id == current_user.id,
            QuestProgress.status != "completed",
            Quest.is_active.is_(True),
        )
        .order_by(QuestProgress.started_at.desc())
    ).scalar_one_or_none()

    quest = None
    progress_entry = None
    if active_progress is not None:
        quest = db.execute(
            select(Quest)
            .options(
                selectinload(Quest.steps).selectinload(QuestStep.objectives),
                selectinload(Quest.rewards),
                selectinload(Quest.prerequisite),
            )
            .where(Quest.id == active_progress.quest_id)
        ).scalar_one_or_none()
        progress_entry = active_progress
    else:
        quests = (
            db.execute(
                select(Quest)
                .options(
                    selectinload(Quest.steps).selectinload(QuestStep.objectives),
                    selectinload(Quest.rewards),
                    selectinload(Quest.prerequisite),
                )
                .where(Quest.is_active.is_(True))
                .order_by(Quest.display_order.asc(), Quest.created_at.asc())
            )
            .scalars()
            .all()
        )
        if quests:
            progress_entries = (
                db.execute(
                    select(QuestProgress).where(
                        QuestProgress.user_id == current_user.id,
                        QuestProgress.quest_id.in_([q.id for q in quests]),
                    )
                )
                .scalars()
                .all()
            )
            progress_by_quest = {p.quest_id: p for p in progress_entries}
            for candidate in quests:
                if _quest_prerequisite_completed(
                    db,
                    user_id=current_user.id,
                    quest=candidate,
                    progress_by_quest=progress_by_quest,
                ):
                    quest = candidate
                    break

    if quest is None:
        return None

    steps_payload, progress_percent = _compute_quest_progress_data(
        db, user=current_user, quest=quest, progress_entry=progress_entry
    )
    status = progress_entry.status if progress_entry else "not_started"
    if (
        progress_entry is not None
        and status != "completed"
        and progress_percent >= 100.0
    ):
        _apply_quest_rewards(
            db, user=current_user, quest=quest, progress_entry=progress_entry
        )
        db.commit()
        progress_percent = 100.0
        status = "completed"

    next_step_title, next_objective = _extract_next_objective(steps_payload)

    return QuestSummaryOut(
        quest_id=quest.id,
        quest_slug=quest.slug,
        quest_name=quest.name,
        status=status,
        progress_percent=progress_percent,
        next_step_title=next_step_title,
        next_objective=next_objective,
    )


class ClassCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None


class ClassMemberAddRequest(BaseModel):
    user_id: Optional[UUID] = None
    email: Optional[EmailStr] = None

    @model_validator(mode="after")
    def _validate_identifier(self) -> "ClassMemberAddRequest":
        if not self.user_id and not self.email:
            raise ValueError("Either user_id or email is required.")
        return self


class AssignmentCreateRequest(BaseModel):
    quest_id: UUID
    due_at: Optional[datetime] = None


# Old schemas kept for backward compatibility
class ClassMemberOut_Legacy(BaseModel):
    user_id: UUID
    display_name: str
    email: str
    role: str
    joined_at: datetime


class AssignmentSummaryOut(BaseModel):
    id: UUID
    quest_id: UUID
    quest_slug: str
    quest_name: str
    due_at: Optional[datetime] = None
    assigned_at: datetime
    completion_percent: float


class ClassSummaryOut_Legacy(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    teacher_id: UUID
    created_at: datetime
    member_count: int
    assignment_count: int


class ClassDetailOut_Legacy(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    teacher_id: UUID
    created_at: datetime
    members: list[ClassMemberOut_Legacy]
    assignments: list[AssignmentSummaryOut]


def _ensure_class_access(current_user: User, classroom: Classroom) -> None:
    if current_user.role in ADMIN_ROLES:
        return
    if (
        current_user.role == UserRole.teacher
        and classroom.teacher_id == current_user.id
    ):
        return
    raise HTTPException(status_code=403, detail="Not authorized")


# =============================================================================
# Classroom Management Endpoints (Enhanced for P1-TEACH-01)
# =============================================================================


@app.get("/api/v1/classrooms", response_model=list[schemas.ClassroomSummaryOut])
def list_classrooms(
    include_archived: bool = Query(False, description="Include archived classrooms"),
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db),
) -> list[schemas.ClassroomSummaryOut]:
    """
    List all classrooms for the current teacher.
    Admins can see all classrooms.
    """
    query = select(Classroom)

    if current_user.role == UserRole.teacher:
        query = query.where(Classroom.teacher_id == current_user.id)

    if not include_archived:
        query = query.where(Classroom.is_archived == False)

    classrooms = db.execute(query.order_by(Classroom.created_at.desc())).scalars().all()

    if not classrooms:
        return []

    class_ids = [c.id for c in classrooms]
    member_counts = dict(
        db.execute(
            select(ClassMember.class_id, func.count(ClassMember.id))
            .where(ClassMember.class_id.in_(class_ids))
            .group_by(ClassMember.class_id)
        ).all()
    )
    assignment_counts = dict(
        db.execute(
            select(QuestAssignment.class_id, func.count(QuestAssignment.id))
            .where(QuestAssignment.class_id.in_(class_ids))
            .group_by(QuestAssignment.class_id)
        ).all()
    )

    return [
        schemas.ClassroomSummaryOut(
            id=classroom.id,
            name=classroom.name,
            description=classroom.description,
            teacher_id=classroom.teacher_id,
            class_code=classroom.class_code,
            max_students=classroom.max_students,
            is_archived=classroom.is_archived,
            member_count=int(member_counts.get(classroom.id, 0)),
            assignment_count=int(assignment_counts.get(classroom.id, 0)),
            created_at=classroom.created_at,
            updated_at=classroom.updated_at,
        )
        for classroom in classrooms
    ]


@app.post(
    "/api/v1/classrooms", response_model=schemas.ClassroomSummaryOut, status_code=201
)
def create_classroom(
    payload: schemas.ClassroomCreateIn,
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db),
) -> schemas.ClassroomSummaryOut:
    """
    Create a new classroom.
    Generates a unique class code for students to join.
    """
    from .services import classroom as classroom_service

    classroom = classroom_service.create_classroom(
        db=db,
        teacher=current_user,
        name=payload.name,
        description=payload.description,
        max_students=payload.max_students,
        settings=payload.settings,
    )

    return schemas.ClassroomSummaryOut(
        id=classroom.id,
        name=classroom.name,
        description=classroom.description,
        teacher_id=classroom.teacher_id,
        class_code=classroom.class_code,
        max_students=classroom.max_students,
        is_archived=classroom.is_archived,
        member_count=0,
        assignment_count=0,
        created_at=classroom.created_at,
        updated_at=classroom.updated_at,
    )


@app.get("/api/v1/classrooms/{classroom_id}", response_model=schemas.ClassroomDetailOut)
def get_classroom(
    classroom_id: UUID,
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db),
) -> schemas.ClassroomDetailOut:
    """
    Get detailed classroom information including members and assignments.
    """
    classroom = db.get(Classroom, classroom_id)
    if classroom is None:
        raise HTTPException(status_code=404, detail="Classroom not found")

    _ensure_class_access(current_user, classroom)

    # Get teacher info
    teacher = db.get(User, classroom.teacher_id)
    teacher_name = teacher.display_name if teacher else "Unknown"

    # Get members with user details
    members = (
        db.execute(
            select(ClassMember)
            .options(selectinload(ClassMember.user))
            .where(ClassMember.class_id == classroom.id)
            .order_by(ClassMember.joined_at.asc())
        )
        .scalars()
        .all()
    )

    # Get assignment count
    assignment_count = db.execute(
        select(func.count(QuestAssignment.id)).where(
            QuestAssignment.class_id == classroom.id
        )
    ).scalar_one()

    return schemas.ClassroomDetailOut(
        id=classroom.id,
        name=classroom.name,
        description=classroom.description,
        teacher_id=classroom.teacher_id,
        teacher_name=teacher_name,
        class_code=classroom.class_code,
        max_students=classroom.max_students,
        is_archived=classroom.is_archived,
        settings=classroom.settings,
        members=[
            schemas.ClassMemberOut(
                id=member.id,
                user_id=member.user_id,
                display_name=member.user.display_name,
                email=member.user.email,
                role=member.role,
                joined_at=member.joined_at,
            )
            for member in members
        ],
        member_count=len(members),
        assignment_count=int(assignment_count),
        created_at=classroom.created_at,
        updated_at=classroom.updated_at,
    )


@app.put("/api/v1/classrooms/{classroom_id}", response_model=schemas.ClassroomDetailOut)
def update_classroom(
    classroom_id: UUID,
    payload: schemas.ClassroomUpdateIn,
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db),
) -> schemas.ClassroomDetailOut:
    """
    Update classroom details.
    """
    from .services import classroom as classroom_service

    classroom = db.get(Classroom, classroom_id)
    if classroom is None:
        raise HTTPException(status_code=404, detail="Classroom not found")

    _ensure_class_access(current_user, classroom)

    classroom = classroom_service.update_classroom(
        db=db,
        classroom=classroom,
        name=payload.name,
        description=payload.description,
        max_students=payload.max_students,
        settings=payload.settings,
    )

    return get_classroom(classroom_id, current_user, db)


@app.delete("/api/v1/classrooms/{classroom_id}", status_code=204)
def delete_classroom(
    classroom_id: UUID,
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db),
) -> None:
    """
    Delete a classroom.
    This will also delete all members and assignments.
    """
    classroom = db.get(Classroom, classroom_id)
    if classroom is None:
        raise HTTPException(status_code=404, detail="Classroom not found")

    _ensure_class_access(current_user, classroom)

    db.delete(classroom)
    db.commit()


@app.post(
    "/api/v1/classrooms/{classroom_id}/archive",
    response_model=schemas.ClassroomDetailOut,
)
def archive_classroom(
    classroom_id: UUID,
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db),
) -> schemas.ClassroomDetailOut:
    """
    Archive a classroom.
    Archived classrooms cannot accept new students but existing data is preserved.
    """
    from .services import classroom as classroom_service

    classroom = db.get(Classroom, classroom_id)
    if classroom is None:
        raise HTTPException(status_code=404, detail="Classroom not found")

    _ensure_class_access(current_user, classroom)

    if classroom.is_archived:
        raise HTTPException(status_code=400, detail="Classroom is already archived")

    classroom_service.archive_classroom(db, classroom)

    return get_classroom(classroom_id, current_user, db)


@app.post(
    "/api/v1/classrooms/{classroom_id}/unarchive",
    response_model=schemas.ClassroomDetailOut,
)
def unarchive_classroom(
    classroom_id: UUID,
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db),
) -> schemas.ClassroomDetailOut:
    """
    Unarchive a classroom.
    """
    from .services import classroom as classroom_service

    classroom = db.get(Classroom, classroom_id)
    if classroom is None:
        raise HTTPException(status_code=404, detail="Classroom not found")

    _ensure_class_access(current_user, classroom)

    if not classroom.is_archived:
        raise HTTPException(status_code=400, detail="Classroom is not archived")

    classroom_service.unarchive_classroom(db, classroom)

    return get_classroom(classroom_id, current_user, db)


@app.post("/api/v1/classrooms/join", response_model=schemas.ClassroomJoinOut)
def join_classroom(
    payload: schemas.ClassroomJoinIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.ClassroomJoinOut:
    """
    Join a classroom using a class code.
    Available to learners only.
    """
    from .services import classroom as classroom_service

    if current_user.role != UserRole.learner:
        raise HTTPException(status_code=403, detail="Only learners can join classrooms")

    try:
        classroom, member = classroom_service.join_classroom_by_code(
            db=db,
            user=current_user,
            class_code=payload.class_code,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Get teacher info
    teacher = db.get(User, classroom.teacher_id)
    teacher_name = teacher.display_name if teacher else "Unknown"

    # Get all members
    members = (
        db.execute(
            select(ClassMember)
            .options(selectinload(ClassMember.user))
            .where(ClassMember.class_id == classroom.id)
        )
        .scalars()
        .all()
    )

    # Get assignment count
    assignment_count = db.execute(
        select(func.count(QuestAssignment.id)).where(
            QuestAssignment.class_id == classroom.id
        )
    ).scalar_one()

    classroom_detail = schemas.ClassroomDetailOut(
        id=classroom.id,
        name=classroom.name,
        description=classroom.description,
        teacher_id=classroom.teacher_id,
        teacher_name=teacher_name,
        class_code=classroom.class_code,
        max_students=classroom.max_students,
        is_archived=classroom.is_archived,
        settings=classroom.settings,
        members=[
            schemas.ClassMemberOut(
                id=m.id,
                user_id=m.user_id,
                display_name=m.user.display_name,
                email=m.user.email,
                role=m.role,
                joined_at=m.joined_at,
            )
            for m in members
        ],
        member_count=len(members),
        assignment_count=int(assignment_count),
        created_at=classroom.created_at,
        updated_at=classroom.updated_at,
    )

    return schemas.ClassroomJoinOut(
        classroom=classroom_detail, message=f"Successfully joined {classroom.name}"
    )


@app.delete("/api/v1/classrooms/{classroom_id}/members/{member_id}", status_code=204)
def remove_member(
    classroom_id: UUID,
    member_id: UUID,
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db),
) -> None:
    """
    Remove a member from a classroom.
    """
    from .services import classroom as classroom_service

    classroom = db.get(Classroom, classroom_id)
    if classroom is None:
        raise HTTPException(status_code=404, detail="Classroom not found")

    _ensure_class_access(current_user, classroom)

    try:
        classroom_service.remove_class_member(db, classroom, member_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get(
    "/api/v1/classrooms/enrolled", response_model=list[schemas.ClassroomSummaryOut]
)
def get_enrolled_classrooms(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[schemas.ClassroomSummaryOut]:
    """
    Get all classrooms where the current user is enrolled as a student.
    """
    from .services import classroom as classroom_service

    classrooms = classroom_service.get_enrolled_classrooms(db, current_user)

    if not classrooms:
        return []

    class_ids = [c.id for c in classrooms]
    member_counts = dict(
        db.execute(
            select(ClassMember.class_id, func.count(ClassMember.id))
            .where(ClassMember.class_id.in_(class_ids))
            .group_by(ClassMember.class_id)
        ).all()
    )
    assignment_counts = dict(
        db.execute(
            select(QuestAssignment.class_id, func.count(QuestAssignment.id))
            .where(QuestAssignment.class_id.in_(class_ids))
            .group_by(QuestAssignment.class_id)
        ).all()
    )

    return [
        schemas.ClassroomSummaryOut(
            id=classroom.id,
            name=classroom.name,
            description=classroom.description,
            teacher_id=classroom.teacher_id,
            class_code=classroom.class_code,
            max_students=classroom.max_students,
            is_archived=classroom.is_archived,
            member_count=int(member_counts.get(classroom.id, 0)),
            assignment_count=int(assignment_counts.get(classroom.id, 0)),
            created_at=classroom.created_at,
            updated_at=classroom.updated_at,
        )
        for classroom in classrooms
    ]


# =============================================================================
# Quest Assignment Endpoints (P1-TEACH-02)
# =============================================================================


@app.get(
    "/api/v1/classrooms/{classroom_id}/assignments",
    response_model=list[schemas.QuestAssignmentOut],
)
def list_classroom_assignments(
    classroom_id: UUID,
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db),
) -> list[schemas.QuestAssignmentOut]:
    """
    List all quest assignments for a classroom.
    """
    from backend.services import quest_assignments as assignment_service

    classroom = db.get(Classroom, classroom_id)
    if not classroom:
        raise HTTPException(status_code=404, detail="Classroom not found")

    _ensure_class_access(current_user, classroom)

    assignments = assignment_service.get_classroom_assignments(db, classroom_id)

    # Build response
    result = []
    for assignment in assignments:
        progress_entries = assignment.progress_entries
        total_students = len(progress_entries)
        assigned_count = sum(1 for p in progress_entries if p.status == "assigned")
        in_progress_count = sum(
            1 for p in progress_entries if p.status == "in_progress"
        )
        completed_count = sum(1 for p in progress_entries if p.status == "completed")

        assigned_by_name = None
        if assignment.assigned_by:
            assigned_by_name = (
                assignment.assigned_by.display_name or assignment.assigned_by.email
            )

        result.append(
            schemas.QuestAssignmentOut(
                id=assignment.id,
                class_id=assignment.class_id,
                quest=schemas.QuestBriefOut(
                    id=assignment.quest.id,
                    slug=assignment.quest.slug,
                    name=assignment.quest.name,
                    description=assignment.quest.description,
                ),
                assigned_by_id=assignment.assigned_by_id,
                assigned_by_name=assigned_by_name,
                due_at=assignment.due_at,
                assigned_at=assignment.assigned_at,
                points_override=assignment.points_override,
                notes=assignment.notes,
                total_students=total_students,
                completed_count=completed_count,
                in_progress_count=in_progress_count,
                assigned_count=assigned_count,
                completion_rate=(completed_count / total_students * 100)
                if total_students > 0
                else 0,
            )
        )

    return result


@app.post(
    "/api/v1/classrooms/{classroom_id}/assignments",
    response_model=schemas.QuestAssignmentOut,
    status_code=201,
)
def create_assignment(
    classroom_id: UUID,
    payload: schemas.QuestAssignmentCreateIn,
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db),
) -> schemas.QuestAssignmentOut:
    """
    Create a new quest assignment.
    Can assign to entire classroom or to individual student.
    """
    from backend.services import quest_assignments as assignment_service

    classroom = db.get(Classroom, classroom_id)
    if not classroom:
        raise HTTPException(status_code=404, detail="Classroom not found")

    _ensure_class_access(current_user, classroom)

    try:
        if payload.student_id:
            # Assign to individual student
            assignment = assignment_service.assign_quest_to_student(
                db=db,
                classroom=classroom,
                quest_id=payload.quest_id,
                student_id=payload.student_id,
                teacher=current_user,
                due_at=payload.due_at,
                points_override=payload.points_override,
                notes=payload.notes,
            )
        else:
            # Assign to entire classroom
            assignment = assignment_service.assign_quest_to_classroom(
                db=db,
                classroom=classroom,
                quest_id=payload.quest_id,
                teacher=current_user,
                due_at=payload.due_at,
                points_override=payload.points_override,
                notes=payload.notes,
            )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Build response
    progress_entries = assignment.progress_entries
    total_students = len(progress_entries)
    assigned_count = sum(1 for p in progress_entries if p.status == "assigned")
    in_progress_count = sum(1 for p in progress_entries if p.status == "in_progress")
    completed_count = sum(1 for p in progress_entries if p.status == "completed")

    assigned_by_name = None
    if assignment.assigned_by:
        assigned_by_name = (
            assignment.assigned_by.display_name or assignment.assigned_by.email
        )

    return schemas.QuestAssignmentOut(
        id=assignment.id,
        class_id=assignment.class_id,
        quest=schemas.QuestBriefOut(
            id=assignment.quest.id,
            slug=assignment.quest.slug,
            name=assignment.quest.name,
            description=assignment.quest.description,
        ),
        assigned_by_id=assignment.assigned_by_id,
        assigned_by_name=assigned_by_name,
        due_at=assignment.due_at,
        assigned_at=assignment.assigned_at,
        points_override=assignment.points_override,
        notes=assignment.notes,
        total_students=total_students,
        completed_count=completed_count,
        in_progress_count=in_progress_count,
        assigned_count=assigned_count,
        completion_rate=(completed_count / total_students * 100)
        if total_students > 0
        else 0,
    )


@app.put(
    "/api/v1/classrooms/{classroom_id}/assignments/{assignment_id}",
    response_model=schemas.QuestAssignmentOut,
)
def update_assignment(
    classroom_id: UUID,
    assignment_id: UUID,
    payload: schemas.QuestAssignmentUpdateIn,
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db),
) -> schemas.QuestAssignmentOut:
    """
    Update a quest assignment.
    """
    from backend.services import quest_assignments as assignment_service

    classroom = db.get(Classroom, classroom_id)
    if not classroom:
        raise HTTPException(status_code=404, detail="Classroom not found")

    _ensure_class_access(current_user, classroom)

    try:
        assignment = assignment_service.update_assignment(
            db=db,
            assignment_id=assignment_id,
            due_at=payload.due_at,
            points_override=payload.points_override,
            notes=payload.notes,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    # Build response
    progress_entries = assignment.progress_entries
    total_students = len(progress_entries)
    assigned_count = sum(1 for p in progress_entries if p.status == "assigned")
    in_progress_count = sum(1 for p in progress_entries if p.status == "in_progress")
    completed_count = sum(1 for p in progress_entries if p.status == "completed")

    assigned_by_name = None
    if assignment.assigned_by:
        assigned_by_name = (
            assignment.assigned_by.display_name or assignment.assigned_by.email
        )

    return schemas.QuestAssignmentOut(
        id=assignment.id,
        class_id=assignment.class_id,
        quest=schemas.QuestBriefOut(
            id=assignment.quest.id,
            slug=assignment.quest.slug,
            name=assignment.quest.name,
            description=assignment.quest.description,
        ),
        assigned_by_id=assignment.assigned_by_id,
        assigned_by_name=assigned_by_name,
        due_at=assignment.due_at,
        assigned_at=assignment.assigned_at,
        points_override=assignment.points_override,
        notes=assignment.notes,
        total_students=total_students,
        completed_count=completed_count,
        in_progress_count=in_progress_count,
        assigned_count=assigned_count,
        completion_rate=(completed_count / total_students * 100)
        if total_students > 0
        else 0,
    )


@app.delete(
    "/api/v1/classrooms/{classroom_id}/assignments/{assignment_id}", status_code=204
)
def delete_assignment(
    classroom_id: UUID,
    assignment_id: UUID,
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db),
) -> None:
    """
    Delete a quest assignment.
    """
    from backend.services import quest_assignments as assignment_service

    classroom = db.get(Classroom, classroom_id)
    if not classroom:
        raise HTTPException(status_code=404, detail="Classroom not found")

    _ensure_class_access(current_user, classroom)

    try:
        assignment_service.delete_assignment(db, assignment_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/v1/assignments/mine", response_model=list[schemas.StudentAssignmentOut])
def get_my_assignments(
    classroom_id: Optional[UUID] = Query(None, description="Filter by classroom"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[schemas.StudentAssignmentOut]:
    """
    Get all quest assignments for the current student.
    """
    from datetime import datetime

    from backend.services import quest_assignments as assignment_service

    assignments = assignment_service.get_student_assignments(
        db=db,
        user_id=current_user.id,
        classroom_id=classroom_id,
    )

    result = []
    for assignment in assignments:
        is_overdue = False
        if assignment["due_at"] and assignment["status"] != "completed":
            is_overdue = (
                datetime.now(assignment["due_at"].tzinfo) > assignment["due_at"]
            )

        result.append(
            schemas.StudentAssignmentOut(
                assignment_id=UUID(assignment["assignment_id"]),
                quest_id=UUID(assignment["quest_id"]),
                quest_name=assignment["quest_name"],
                quest_description=assignment["quest_description"],
                classroom_id=UUID(assignment["classroom_id"]),
                classroom_name=assignment["classroom_name"],
                due_at=assignment["due_at"],
                assigned_at=assignment["assigned_at"],
                points_override=assignment["points_override"],
                notes=assignment["notes"],
                status=assignment["status"],
                completed_at=assignment["completed_at"],
                is_overdue=is_overdue,
            )
        )

    return result


@app.post(
    "/api/v1/assignments/{assignment_id}/submit",
    response_model=schemas.AssignmentSubmitOut,
)
def submit_assignment(
    assignment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.AssignmentSubmitOut:
    """
    Submit an assignment as completed.
    The quest must be completed first.
    """
    from backend.services import quest_assignments as assignment_service

    try:
        progress = assignment_service.submit_assignment(
            db=db,
            assignment_id=assignment_id,
            user_id=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    message = (
        "Assignment marked as in progress"
        if progress.status == "in_progress"
        else "Assignment completed!"
    )

    return schemas.AssignmentSubmitOut(
        assignment_id=assignment_id,
        status=progress.status,
        completed_at=progress.completed_at,
        message=message,
    )


# =============================================================================
# Student Progress Endpoints (P1-TEACH-03)
# =============================================================================


@app.get(
    "/api/v1/classrooms/{classroom_id}/students/{student_id}/progress",
    response_model=schemas.StudentProgressOut,
)
def get_student_progress(
    classroom_id: UUID,
    student_id: UUID,
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db),
) -> schemas.StudentProgressOut:
    """
    Get detailed progress for a specific student in a classroom.
    Only accessible to teachers of the classroom and admins.
    """
    from .services import student_progress as progress_service

    classroom = db.get(Classroom, classroom_id)
    if classroom is None:
        raise HTTPException(status_code=404, detail="Classroom not found")

    _ensure_class_access(current_user, classroom)

    try:
        progress = progress_service.get_student_progress(db, student_id, classroom_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return schemas.StudentProgressOut(
        student_id=progress["student_id"],
        classroom_id=progress["classroom_id"],
        joined_at=progress["joined_at"],
        overall_completion_percent=progress["overall_completion_percent"],
        lessons=schemas.LessonStatsOut(**progress["lessons"]),
        quizzes=schemas.QuizStatsOut(**progress["quizzes"]),
        engagement=schemas.EngagementStatsOut(**progress["engagement"]),
    )


@app.get(
    "/api/v1/classrooms/{classroom_id}/progress",
    response_model=schemas.ClassProgressSummaryOut,
)
def get_class_progress_summary(
    classroom_id: UUID,
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db),
) -> schemas.ClassProgressSummaryOut:
    """
    Get class-wide progress summary with average metrics.
    Only accessible to teachers of the classroom and admins.
    """
    from .services import student_progress as progress_service

    classroom = db.get(Classroom, classroom_id)
    if classroom is None:
        raise HTTPException(status_code=404, detail="Classroom not found")

    _ensure_class_access(current_user, classroom)

    summary = progress_service.get_class_progress_summary(db, classroom_id)

    return schemas.ClassProgressSummaryOut(
        classroom_id=summary["classroom_id"],
        student_count=summary["student_count"],
        averages=schemas.ClassProgressAveragesOut(**summary["averages"]),
    )


@app.get(
    "/api/v1/classrooms/{classroom_id}/leaderboard",
    response_model=schemas.LeaderboardOut,
)
def get_class_leaderboard(
    classroom_id: UUID,
    order_by: str = Query("xp", regex="^(xp|streak|motifs|quizzes)$"),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db),
) -> schemas.LeaderboardOut:
    """
    Get class leaderboard sorted by various metrics.

    Order by options:
    - xp: Total XP earned
    - streak: Current streak
    - motifs: Discovered motifs
    - quizzes: Quizzes passed

    Only accessible to teachers of the classroom and admins.
    """
    from .services import student_progress as progress_service

    classroom = db.get(Classroom, classroom_id)
    if classroom is None:
        raise HTTPException(status_code=404, detail="Classroom not found")

    _ensure_class_access(current_user, classroom)

    entries = progress_service.get_class_leaderboard(db, classroom_id, limit, order_by)

    return schemas.LeaderboardOut(
        classroom_id=classroom_id,
        order_by=order_by,
        entries=[schemas.LeaderboardEntryOut(**entry) for entry in entries],
    )


@app.get("/api/v1/classrooms/{classroom_id}/export")
def export_class_progress(
    classroom_id: UUID,
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db),
):
    """
    Export class progress data as CSV.
    Only accessible to teachers of the classroom and admins.
    """
    import csv
    from io import StringIO

    from fastapi.responses import StreamingResponse

    from .services import student_progress as progress_service

    classroom = db.get(Classroom, classroom_id)
    if classroom is None:
        raise HTTPException(status_code=404, detail="Classroom not found")

    _ensure_class_access(current_user, classroom)

    # Get all student members
    members = (
        db.execute(
            select(ClassMember)
            .options(selectinload(ClassMember.user))
            .where(
                and_(
                    ClassMember.class_id == classroom_id,
                    ClassMember.role == "learner",
                )
            )
        )
        .scalars()
        .all()
    )

    # Create CSV
    output = StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow(
        [
            "Student ID",
            "Display Name",
            "Email",
            "Joined At",
            "Completion %",
            "Discovered Motifs",
            "Learned Motifs",
            "Mastered Motifs",
            "Quiz Attempts",
            "Quizzes Passed",
            "Avg Quiz Score",
            "Current Streak",
            "Longest Streak",
            "Total XP",
            "Time Spent (min)",
        ]
    )

    # Write data for each student
    for member in members:
        try:
            progress = progress_service.get_student_progress(
                db, member.user_id, classroom_id
            )

            writer.writerow(
                [
                    str(progress["student_id"]),
                    member.user.display_name,
                    member.user.email,
                    progress["joined_at"].isoformat(),
                    progress["overall_completion_percent"],
                    progress["lessons"]["discovered"],
                    progress["lessons"]["learned"],
                    progress["lessons"]["mastered"],
                    progress["quizzes"]["total_attempts"],
                    progress["quizzes"]["passed"],
                    progress["quizzes"]["average_score"],
                    progress["engagement"]["current_streak"],
                    progress["engagement"]["longest_streak"],
                    progress["engagement"]["total_xp"],
                    progress["engagement"]["time_spent_minutes"],
                ]
            )
        except ValueError:
            # Skip students with errors
            continue

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=classroom_{classroom_id}_progress.csv"
        },
    )


# =============================================================================
# Legacy Classroom Endpoints (Backward Compatibility)
# =============================================================================


@app.get("/api/v1/classes/{class_id}", response_model=ClassDetailOut_Legacy)
def get_class_detail(
    class_id: UUID,
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db),
) -> ClassDetailOut_Legacy:
    classroom = db.get(Classroom, class_id)
    if classroom is None:
        raise HTTPException(status_code=404, detail="Class not found")
    _ensure_class_access(current_user, classroom)

    members = (
        db.execute(
            select(ClassMember)
            .options(selectinload(ClassMember.user))
            .where(ClassMember.class_id == classroom.id)
            .order_by(ClassMember.joined_at.asc())
        )
        .scalars()
        .all()
    )

    assignments = (
        db.execute(
            select(QuestAssignment)
            .options(selectinload(QuestAssignment.quest))
            .where(QuestAssignment.class_id == classroom.id)
            .order_by(QuestAssignment.assigned_at.desc())
        )
        .scalars()
        .all()
    )

    assignment_ids = [a.id for a in assignments]
    progress_counts = {}
    if assignment_ids:
        progress_counts = dict(
            db.execute(
                select(
                    AssignmentProgress.assignment_id,
                    func.count(AssignmentProgress.id).label("completed_count"),
                )
                .where(
                    AssignmentProgress.assignment_id.in_(assignment_ids),
                    AssignmentProgress.status == "completed",
                )
                .group_by(AssignmentProgress.assignment_id)
            ).all()
        )

    member_count = len(members)
    assignment_payload = []
    for assignment in assignments:
        completed_count = int(progress_counts.get(assignment.id, 0))
        completion_percent = (
            (completed_count / member_count * 100.0) if member_count else 0.0
        )
        assignment_payload.append(
            AssignmentSummaryOut(
                id=assignment.id,
                quest_id=assignment.quest_id,
                quest_slug=assignment.quest.slug if assignment.quest else "",
                quest_name=assignment.quest.name if assignment.quest else "",
                due_at=assignment.due_at,
                assigned_at=assignment.assigned_at,
                completion_percent=round(completion_percent, 1),
            )
        )

    return ClassDetailOut_Legacy(
        id=classroom.id,
        name=classroom.name,
        description=classroom.description,
        teacher_id=classroom.teacher_id,
        created_at=classroom.created_at,
        members=[
            ClassMemberOut_Legacy(
                user_id=member.user_id,
                display_name=member.user.display_name,
                email=member.user.email,
                role=member.role,
                joined_at=member.joined_at,
            )
            for member in members
        ],
        assignments=assignment_payload,
    )


@app.post("/api/v1/classes/{class_id}/members", response_model=ClassDetailOut_Legacy)
def add_class_member(
    class_id: UUID,
    payload: ClassMemberAddRequest,
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db),
) -> ClassDetailOut_Legacy:
    classroom = db.get(Classroom, class_id)
    if classroom is None:
        raise HTTPException(status_code=404, detail="Class not found")
    _ensure_class_access(current_user, classroom)

    if payload.user_id:
        user = db.get(User, payload.user_id)
    else:
        user = db.execute(
            select(User).where(User.email == str(payload.email))
        ).scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if user.role != UserRole.learner:
        raise HTTPException(status_code=400, detail="Only learners can join classes")

    existing = db.execute(
        select(ClassMember).where(
            ClassMember.class_id == classroom.id, ClassMember.user_id == user.id
        )
    ).scalar_one_or_none()
    if existing is None:
        db.add(ClassMember(class_id=classroom.id, user_id=user.id, role="learner"))
        db.flush()

        assignments = (
            db.execute(
                select(QuestAssignment).where(QuestAssignment.class_id == classroom.id)
            )
            .scalars()
            .all()
        )
        for assignment in assignments:
            completed = db.execute(
                select(QuestProgress).where(
                    QuestProgress.user_id == user.id,
                    QuestProgress.quest_id == assignment.quest_id,
                    QuestProgress.status == "completed",
                )
            ).scalar_one_or_none()
            db.add(
                AssignmentProgress(
                    assignment_id=assignment.id,
                    user_id=user.id,
                    status="completed" if completed else "assigned",
                    completed_at=completed.completed_at if completed else None,
                )
            )

        db.commit()

    return get_class_detail(class_id, current_user=current_user, db=db)


@app.delete(
    "/api/v1/classes/{class_id}/members/{user_id}", response_model=ClassDetailOut_Legacy
)
def remove_class_member(
    class_id: UUID,
    user_id: UUID,
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db),
) -> ClassDetailOut_Legacy:
    classroom = db.get(Classroom, class_id)
    if classroom is None:
        raise HTTPException(status_code=404, detail="Class not found")
    _ensure_class_access(current_user, classroom)

    member = db.execute(
        select(ClassMember).where(
            ClassMember.class_id == classroom.id, ClassMember.user_id == user_id
        )
    ).scalar_one_or_none()
    if member is None:
        raise HTTPException(status_code=404, detail="Member not found")

    assignment_ids = (
        db.execute(
            select(QuestAssignment.id).where(QuestAssignment.class_id == classroom.id)
        )
        .scalars()
        .all()
    )
    if assignment_ids:
        db.execute(
            delete(AssignmentProgress).where(
                AssignmentProgress.assignment_id.in_(assignment_ids),
                AssignmentProgress.user_id == user_id,
            )
        )

    db.delete(member)
    db.commit()

    return get_class_detail(class_id, current_user=current_user, db=db)


@app.post(
    "/api/v1/classes/{class_id}/assignments", response_model=ClassDetailOut_Legacy
)
def assign_quest_to_class(
    class_id: UUID,
    payload: AssignmentCreateRequest,
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db),
) -> ClassDetailOut_Legacy:
    classroom = db.get(Classroom, class_id)
    if classroom is None:
        raise HTTPException(status_code=404, detail="Class not found")
    _ensure_class_access(current_user, classroom)

    quest = db.get(Quest, payload.quest_id)
    if quest is None or not quest.is_active:
        raise HTTPException(status_code=404, detail="Quest not found")

    assignment = QuestAssignment(
        class_id=classroom.id,
        quest_id=quest.id,
        assigned_by_id=current_user.id,
        due_at=payload.due_at,
    )
    db.add(assignment)
    db.flush()

    members = (
        db.execute(select(ClassMember).where(ClassMember.class_id == classroom.id))
        .scalars()
        .all()
    )
    for member in members:
        completed = db.execute(
            select(QuestProgress).where(
                QuestProgress.user_id == member.user_id,
                QuestProgress.quest_id == quest.id,
                QuestProgress.status == "completed",
            )
        ).scalar_one_or_none()
        db.add(
            AssignmentProgress(
                assignment_id=assignment.id,
                user_id=member.user_id,
                status="completed" if completed else "assigned",
                completed_at=completed.completed_at if completed else None,
            )
        )

    db.commit()

    return get_class_detail(class_id, current_user=current_user, db=db)


class StreakResponse(BaseModel):
    current_streak: int
    longest_streak: int
    streak_freezes: int
    last_active_at: Optional[datetime] = None
    days_since_last_active: Optional[int] = None


@app.get("/api/v1/users/me/streak", response_model=StreakResponse)
def get_my_streak(current_user: User = Depends(get_current_user)) -> StreakResponse:
    now = datetime.now(timezone.utc)
    days = None
    if current_user.last_active_at is not None:
        days = (
            now.date() - current_user.last_active_at.astimezone(timezone.utc).date()
        ).days

    return StreakResponse(
        current_streak=current_user.current_streak,
        longest_streak=current_user.longest_streak,
        streak_freezes=current_user.streak_freezes,
        last_active_at=current_user.last_active_at,
        days_since_last_active=days,
    )


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


@app.get("/api/v1/dashboard/summary", response_model=DashboardSummaryOut)
def get_dashboard_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DashboardSummaryOut:
    urns = list_urns(current_user=current_user, db=db)

    total_motifs = (
        db.execute(
            select(func.count(Motif.id)).where(Motif.is_active.is_(True))
        ).scalar()
        or 0
    )
    status_rows = db.execute(
        select(UserProgress.status, func.count(UserProgress.id))
        .join(Motif, Motif.id == UserProgress.motif_id)
        .where(
            UserProgress.user_id == current_user.id,
            Motif.is_active.is_(True),
        )
        .group_by(UserProgress.status)
    ).all()
    status_counts = {}
    for status_value, count in status_rows:
        key = (
            status_value.value
            if isinstance(status_value, UnlockStatus)
            else str(status_value)
        )
        status_counts[key] = int(count or 0)

    discovered = status_counts.get(UnlockStatus.discovered.value, 0)
    learned = status_counts.get(UnlockStatus.learned.value, 0)
    mastered = status_counts.get(UnlockStatus.mastered.value, 0)

    quest_total = (
        db.execute(
            select(func.count(Motif.id)).where(
                Motif.is_active.is_(True),
                Motif.category == MotifCategory.thao_moc,
            )
        ).scalar()
        or 0
    )
    quest_discovered = (
        db.execute(
            select(func.count(UserProgress.id))
            .join(Motif, Motif.id == UserProgress.motif_id)
            .where(
                UserProgress.user_id == current_user.id,
                Motif.is_active.is_(True),
                Motif.category == MotifCategory.thao_moc,
                UserProgress.status != UnlockStatus.hidden,
            )
        ).scalar()
        or 0
    )
    progress_percent = (
        (quest_discovered / quest_total * 100.0) if quest_total > 0 else 0.0
    )

    collection_stats = CollectionStatsOut(
        total=int(total_motifs),
        discovered=int(discovered),
        learned=int(learned),
        mastered=int(mastered),
        quest=QuestProgressOut(
            quest_name="Ngự Uyển Ký Sự (The Royal Gardens)",
            total=int(quest_total),
            discovered=int(quest_discovered),
            progress_percent=progress_percent,
        ),
    )

    path_motifs: list[DashboardPathMotifOut] = []
    if current_user.starting_urn_id:
        motifs = (
            db.execute(
                select(Motif)
                .where(
                    Motif.urn_id == current_user.starting_urn_id,
                    Motif.is_active.is_(True),
                )
                .order_by(Motif.display_order.nulls_last(), Motif.name)
            )
            .scalars()
            .all()
        )
        motif_ids = [m.id for m in motifs]
        progress_by_id = {}
        if motif_ids:
            progress_entries = (
                db.execute(
                    select(UserProgress).where(
                        UserProgress.user_id == current_user.id,
                        UserProgress.motif_id.in_(motif_ids),
                    )
                )
                .scalars()
                .all()
            )
            progress_by_id = {p.motif_id: p for p in progress_entries}

        path_motifs = [
            DashboardPathMotifOut(
                id=motif.id,
                name=motif.name,
                name_en=motif.name_en,
                display_order=motif.display_order,
                status=(
                    progress_by_id[motif.id].status.value
                    if motif.id in progress_by_id
                    else UnlockStatus.hidden.value
                ),
                category=motif.category.value if motif.category else None,
                thumbnail_url=motif.thumbnail_url,
                silhouette_url=motif.silhouette_url,
            )
            for motif in motifs
        ]

    return DashboardSummaryOut(
        urns=urns,
        collection_stats=collection_stats,
        streak=get_my_streak(current_user=current_user),
        quest_summary=get_quest_summary(current_user=current_user, db=db),
        recommendations=get_my_recommendations(current_user=current_user, db=db),
        path_motifs=path_motifs,
    )


@app.post("/api/v1/users/me/streak/freeze", response_model=StreakResponse)
def use_my_streak_freeze(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StreakResponse:
    if current_user.streak_freezes <= 0:
        raise AppError(
            code="NO_STREAK_FREEZES",
            message="No streak freezes available",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    current_user.streak_freezes -= 1
    db.commit()
    db.refresh(current_user)

    now = datetime.now(timezone.utc)
    days = None
    if current_user.last_active_at is not None:
        days = (
            now.date() - current_user.last_active_at.astimezone(timezone.utc).date()
        ).days

    return StreakResponse(
        current_streak=current_user.current_streak,
        longest_streak=current_user.longest_streak,
        streak_freezes=current_user.streak_freezes,
        last_active_at=current_user.last_active_at,
        days_since_last_active=days,
    )


class StreakFreezeResponse(BaseModel):
    success: bool
    message: str
    streak_freezes_remaining: int
    current_streak: int


@app.post("/api/v1/streak/freeze", response_model=StreakFreezeResponse)
def use_streak_freeze(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StreakFreezeResponse:
    """
    Use a streak freeze to protect streak from breaking.
    - Requires at least 1 streak_freezes available
    - Decrements streak_freezes by 1
    - Preserves current streak even if user missed a day
    """
    if current_user.streak_freezes <= 0:
        raise AppError(
            code="NO_STREAK_FREEZES",
            message="No streak freezes available. You need to earn more freezes.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    # Check if streak is actually at risk (missed yesterday)
    now = datetime.now(timezone.utc)
    if current_user.last_active_at is not None:
        last_date = current_user.last_active_at.astimezone(timezone.utc).date()
        today = now.date()
        diff_days = (today - last_date).days

        if diff_days <= 1:
            raise AppError(
                code="STREAK_NOT_AT_RISK",
                message="Streak is not at risk. No need to use a freeze.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

    # Use the freeze
    current_user.streak_freezes -= 1
    # Update last_active_at to yesterday to preserve streak
    # This ensures the next activity continues the streak
    current_user.last_active_at = now - timedelta(days=1)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise AppError(
            code="STREAK_UPDATE_FAILED",
            message="Failed to use streak freeze",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return StreakFreezeResponse(
        success=True,
        message="Streak freeze used successfully! Your streak is protected.",
        streak_freezes_remaining=current_user.streak_freezes,
        current_streak=current_user.current_streak,
    )


# =============================================================================
# XP Boost Endpoints
# =============================================================================


@app.get("/api/v1/users/me/xp-boost", response_model=schemas.XpBoostStatusOut)
def get_xp_boost_status(
    current_user: User = Depends(get_current_user),
) -> schemas.XpBoostStatusOut:
    """
    Get current XP boost status.

    Returns whether boost is active, multiplier, and time remaining.
    """
    now = datetime.now(timezone.utc)
    is_active = current_user.xp_boost_active

    # Check if expired
    if is_active and current_user.xp_boost_expires_at:
        if now >= current_user.xp_boost_expires_at:
            is_active = False

    remaining_seconds = None
    if is_active and current_user.xp_boost_expires_at:
        remaining_seconds = int(
            (current_user.xp_boost_expires_at - now).total_seconds()
        )
        remaining_seconds = max(0, remaining_seconds)

    return schemas.XpBoostStatusOut(
        is_active=is_active,
        multiplier=current_user.xp_boost_multiplier,
        expires_at=current_user.xp_boost_expires_at if is_active else None,
        remaining_seconds=remaining_seconds,
    )


@app.post(
    "/api/v1/users/me/xp-boost/activate", response_model=schemas.ActivateXpBoostOut
)
def activate_xp_boost(
    request: schemas.ActivateXpBoostIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.ActivateXpBoostOut:
    """
    Activate XP boost for the user.

    Note: This is a simple activation endpoint. In production, you might want to:
    - Require gems/currency to activate
    - Check if user has boost items in inventory
    - Implement cooldown periods
    """
    now = datetime.now(timezone.utc)

    # Check if already active
    if current_user.xp_boost_active and current_user.xp_boost_expires_at:
        if now < current_user.xp_boost_expires_at:
            raise AppError(
                code="BOOST_ALREADY_ACTIVE",
                message="XP boost is already active",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

    # Activate boost
    current_user.xp_boost_active = True
    current_user.xp_boost_expires_at = now + timedelta(minutes=request.duration_minutes)
    current_user.xp_boost_multiplier = 2  # Fixed 2x multiplier

    try:
        db.commit()
        db.refresh(current_user)
    except Exception:
        db.rollback()
        raise AppError(
            code="BOOST_ACTIVATION_FAILED",
            message="Failed to activate XP boost",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    remaining_seconds = int((current_user.xp_boost_expires_at - now).total_seconds())

    return schemas.ActivateXpBoostOut(
        success=True,
        message=f"XP boost activated! Earn 2X XP for {request.duration_minutes} minutes.",
        boost_status=schemas.XpBoostStatusOut(
            is_active=True,
            multiplier=current_user.xp_boost_multiplier,
            expires_at=current_user.xp_boost_expires_at,
            remaining_seconds=remaining_seconds,
        ),
    )


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


@app.get("/api/v1/users/me/badges", response_model=list[UserBadgeOut])
def get_my_badges(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[UserBadgeOut]:
    badges = (
        db.execute(
            select(UserBadge)
            .options(selectinload(UserBadge.badge))
            .where(UserBadge.user_id == current_user.id)
            .order_by(UserBadge.earned_at.desc())
        )
        .scalars()
        .all()
    )

    return [
        UserBadgeOut(
            badge=BadgeOut(
                slug=ub.badge.slug,
                name=ub.badge.name,
                description=ub.badge.description,
                icon_url=ub.badge.icon_url,
                category=ub.badge.category.value,
                xp_bonus=int(ub.badge.xp_bonus or 0),
                tier=ub.current_tier.value if ub.current_tier else "bronze",
            ),
            earned_at=ub.earned_at,
            current_tier=ub.current_tier.value if ub.current_tier else "bronze",
        )
        for ub in badges
    ]


# =============================================================================
# Milestones API
# =============================================================================


@app.get("/api/v1/milestones", response_model=schemas.MilestoneListOut)
def get_user_milestones(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.MilestoneListOut:
    """Get all milestones for the current user."""
    from backend.services.milestones import get_user_milestones

    milestones = get_user_milestones(db, current_user.id)

    return schemas.MilestoneListOut(
        milestones=[
            schemas.MilestoneOut(
                id=m.id,
                user_id=m.user_id,
                milestone_type=m.milestone_type.value,
                achieved_at=m.achieved_at,
                context_data=m.context_data,
                celebrated=m.celebrated,
                created_at=m.created_at,
            )
            for m in milestones
        ]
    )


@app.get(
    "/api/v1/milestones/pending-celebration",
    response_model=schemas.PendingMilestonesOut,
)
def get_pending_milestones(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.PendingMilestonesOut:
    """Get milestones that haven't been celebrated yet."""
    from backend.services.milestones import get_pending_milestones

    milestones = get_pending_milestones(db, current_user.id)

    return schemas.PendingMilestonesOut(
        pending_milestones=[
            schemas.PendingMilestoneOut(
                id=m.id,
                milestone_type=m.milestone_type.value,
                achieved_at=m.achieved_at,
                context_data=m.context_data,
            )
            for m in milestones
        ]
    )


@app.post(
    "/api/v1/milestones/{milestone_id}/celebrate",
    response_model=schemas.MilestoneCelebratedOut,
)
def celebrate_milestone(
    milestone_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.MilestoneCelebratedOut:
    """Mark a milestone as celebrated."""
    from backend.services.milestones import mark_milestone_celebrated

    milestone = mark_milestone_celebrated(db, milestone_id, current_user.id)

    if not milestone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Milestone not found or already celebrated",
        )

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update milestone",
        )

    # Create human-readable message based on milestone type
    milestone_messages = {
        "first_motif_discovered": "Congratulations on discovering your first motif!",
        "first_quiz_passed": "Amazing! You passed your first quiz!",
        "first_lesson_completed": "Great job on completing your first lesson!",
        "first_badge_earned": "You earned your first badge!",
        "first_streak_7": "Incredible! You've maintained a 7-day streak!",
        "onboarding_completed": "Welcome aboard! You've completed onboarding!",
    }

    message = milestone_messages.get(
        milestone.milestone_type.value,
        "Congratulations on this milestone!",
    )

    return schemas.MilestoneCelebratedOut(
        success=True,
        milestone_id=milestone.id,
        milestone_type=milestone.milestone_type.value,
        message=message,
    )


class AdminLessonOut(BaseModel):
    id: UUID
    motif_id: UUID
    intro_text: Optional[str] = None
    description: str
    historical_context: Optional[str] = None
    symbolism: Optional[str] = None
    fun_fact: Optional[str] = None
    audio_narration_url: Optional[str] = None
    additional_images: Optional[Any] = None
    video_url: Optional[str] = None
    is_published: bool
    is_ai_generated: bool
    version: int = 1
    last_editor_id: Optional[UUID] = None
    published_at: Optional[datetime] = None
    publish_note: Optional[str] = None
    # Review workflow fields
    status: str = "draft"
    submitted_for_review_at: Optional[datetime] = None
    reviewed_by_id: Optional[UUID] = None
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class AdminLessonCreateRequest(BaseModel):
    motif_id: UUID
    intro_text: Optional[str] = None
    description: str
    historical_context: Optional[str] = None
    symbolism: Optional[str] = None
    fun_fact: Optional[str] = None
    audio_narration_url: Optional[str] = None
    additional_images: Optional[Any] = None
    video_url: Optional[str] = None
    is_published: Optional[bool] = None
    is_ai_generated: Optional[bool] = None


class AdminLessonUpdateRequest(BaseModel):
    intro_text: Optional[str] = None
    description: Optional[str] = None
    historical_context: Optional[str] = None
    symbolism: Optional[str] = None
    fun_fact: Optional[str] = None
    audio_narration_url: Optional[str] = None
    additional_images: Optional[Any] = None
    video_url: Optional[str] = None
    is_published: Optional[bool] = None
    is_ai_generated: Optional[bool] = None
    publish_note: Optional[str] = None  # Note for publishing this version


class AdminQuizQuestionOut(BaseModel):
    id: UUID
    motif_id: UUID
    urn_id: Optional[UUID] = None
    question_type: str
    question_text: str
    options: Optional[Any] = None
    correct_answer: str
    target_mesh_name: Optional[str] = None
    difficulty: int
    explanation: Optional[str] = None
    is_published: bool
    is_active: bool
    # Review workflow fields
    status: str = "draft"
    submitted_for_review_at: Optional[datetime] = None
    reviewed_by_id: Optional[UUID] = None
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None
    created_by_id: Optional[UUID] = None
    created_at: datetime


class AdminQuizQuestionCreateRequest(BaseModel):
    motif_id: UUID
    urn_id: Optional[UUID] = None
    question_type: str
    question_text: str
    options: Optional[Any] = None
    correct_answer: str
    target_mesh_name: Optional[str] = None
    difficulty: Optional[int] = 1
    explanation: Optional[str] = None
    is_published: Optional[bool] = None
    is_active: Optional[bool] = None


class AdminQuizQuestionUpdateRequest(BaseModel):
    question_type: Optional[str] = None
    question_text: Optional[str] = None
    options: Optional[Any] = None
    correct_answer: Optional[str] = None
    target_mesh_name: Optional[str] = None
    difficulty: Optional[int] = None
    explanation: Optional[str] = None
    is_published: Optional[bool] = None
    is_active: Optional[bool] = None


def _normalize_question_type(raw: str) -> QuestionType:
    value = str(raw).strip().lower().replace("-", "_")
    try:
        return QuestionType(value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid question type") from exc


@app.get("/api/v1/admin/lessons", response_model=list[AdminLessonOut])
def list_admin_lessons(
    motif_id: Optional[UUID] = Query(default=None),
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db),
) -> list[AdminLessonOut]:
    query = select(LessonContent)
    if motif_id:
        query = query.where(LessonContent.motif_id == motif_id)
    lessons = (
        db.execute(query.order_by(LessonContent.updated_at.desc())).scalars().all()
    )
    return [
        AdminLessonOut(
            id=lesson.id,
            motif_id=lesson.motif_id,
            intro_text=lesson.intro_text,
            description=lesson.description,
            historical_context=lesson.historical_context,
            symbolism=lesson.symbolism,
            fun_fact=lesson.fun_fact,
            audio_narration_url=lesson.audio_narration_url,
            additional_images=lesson.additional_images,
            video_url=lesson.video_url,
            is_published=lesson.is_published,
            is_ai_generated=lesson.is_ai_generated,
            version=lesson.version,
            last_editor_id=lesson.last_editor_id,
            published_at=lesson.published_at,
            publish_note=lesson.publish_note,
            status=lesson.status.value if lesson.status else "draft",
            submitted_for_review_at=lesson.submitted_for_review_at,
            reviewed_by_id=lesson.reviewed_by_id,
            reviewed_at=lesson.reviewed_at,
            review_notes=lesson.review_notes,
            created_at=lesson.created_at,
            updated_at=lesson.updated_at,
        )
        for lesson in lessons
    ]


@app.post("/api/v1/admin/lessons", response_model=AdminLessonOut, status_code=201)
def create_admin_lesson(
    payload: AdminLessonCreateRequest,
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db),
) -> AdminLessonOut:
    motif = db.get(Motif, payload.motif_id)
    if motif is None:
        raise HTTPException(status_code=404, detail="Motif not found")

    existing = db.execute(
        select(LessonContent).where(LessonContent.motif_id == payload.motif_id)
    ).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status_code=409, detail="Lesson already exists")

    is_published = payload.is_published
    if current_user.role == UserRole.teacher:
        if is_published:
            raise HTTPException(
                status_code=403, detail="Teachers cannot publish lessons"
            )
        is_published = False
    if is_published is None:
        is_published = current_user.role in ADMIN_ROLES

    lesson = LessonContent(
        motif_id=payload.motif_id,
        intro_text=payload.intro_text,
        description=payload.description,
        historical_context=payload.historical_context,
        symbolism=payload.symbolism,
        fun_fact=payload.fun_fact,
        audio_narration_url=payload.audio_narration_url,
        additional_images=payload.additional_images,
        video_url=payload.video_url,
        is_published=is_published,
        is_ai_generated=bool(payload.is_ai_generated)
        if payload.is_ai_generated is not None
        else False,
        last_editor_id=current_user.id,
        published_at=datetime.now(timezone.utc) if is_published else None,
        status=ContentStatus.published if is_published else ContentStatus.draft,
    )
    db.add(lesson)
    db.commit()
    db.refresh(lesson)

    return AdminLessonOut(
        id=lesson.id,
        motif_id=lesson.motif_id,
        intro_text=lesson.intro_text,
        description=lesson.description,
        historical_context=lesson.historical_context,
        symbolism=lesson.symbolism,
        fun_fact=lesson.fun_fact,
        audio_narration_url=lesson.audio_narration_url,
        additional_images=lesson.additional_images,
        video_url=lesson.video_url,
        is_published=lesson.is_published,
        is_ai_generated=lesson.is_ai_generated,
        version=lesson.version,
        last_editor_id=lesson.last_editor_id,
        published_at=lesson.published_at,
        publish_note=lesson.publish_note,
        status=lesson.status.value if lesson.status else "draft",
        submitted_for_review_at=lesson.submitted_for_review_at,
        reviewed_by_id=lesson.reviewed_by_id,
        reviewed_at=lesson.reviewed_at,
        review_notes=lesson.review_notes,
        created_at=lesson.created_at,
        updated_at=lesson.updated_at,
    )


@app.patch("/api/v1/admin/lessons/{lesson_id}", response_model=AdminLessonOut)
def update_admin_lesson(
    lesson_id: UUID,
    payload: AdminLessonUpdateRequest,
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db),
) -> AdminLessonOut:
    lesson = db.get(LessonContent, lesson_id)
    if lesson is None:
        raise HTTPException(status_code=404, detail="Lesson not found")

    if current_user.role == UserRole.teacher:
        if lesson.is_published:
            raise HTTPException(
                status_code=403, detail="Teachers can only edit draft lessons"
            )
        if payload.is_published:
            raise HTTPException(
                status_code=403, detail="Teachers cannot publish lessons"
            )

    # Create a snapshot before updating
    _create_content_snapshot(
        db,
        "lesson",
        lesson.id,
        lesson.version,
        current_user.id,
        f"Version {lesson.version}",
    )

    # Track if we're publishing
    is_publishing = False
    if payload.is_published and not lesson.is_published:
        is_publishing = True

    for field, value in payload.model_dump(exclude_unset=True).items():
        if field == "is_published" and current_user.role not in ADMIN_ROLES:
            continue
        setattr(lesson, field, value)

    # Update versioning metadata
    lesson.version += 1
    lesson.last_editor_id = current_user.id

    if is_publishing:
        lesson.published_at = datetime.now(timezone.utc)
        # Get publish_note from payload if available (need to add this to schema)
        if hasattr(payload, "publish_note"):
            lesson.publish_note = payload.publish_note

    db.commit()
    db.refresh(lesson)

    return AdminLessonOut(
        id=lesson.id,
        motif_id=lesson.motif_id,
        intro_text=lesson.intro_text,
        description=lesson.description,
        historical_context=lesson.historical_context,
        symbolism=lesson.symbolism,
        fun_fact=lesson.fun_fact,
        audio_narration_url=lesson.audio_narration_url,
        additional_images=lesson.additional_images,
        video_url=lesson.video_url,
        is_published=lesson.is_published,
        is_ai_generated=lesson.is_ai_generated,
        version=lesson.version,
        last_editor_id=lesson.last_editor_id,
        published_at=lesson.published_at,
        publish_note=lesson.publish_note,
        status=lesson.status.value if lesson.status else "draft",
        submitted_for_review_at=lesson.submitted_for_review_at,
        reviewed_by_id=lesson.reviewed_by_id,
        reviewed_at=lesson.reviewed_at,
        review_notes=lesson.review_notes,
        created_at=lesson.created_at,
        updated_at=lesson.updated_at,
    )


@app.get("/api/v1/admin/quiz-questions", response_model=list[AdminQuizQuestionOut])
def list_admin_quiz_questions(
    motif_id: Optional[UUID] = Query(default=None),
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db),
) -> list[AdminQuizQuestionOut]:
    query = select(QuizQuestion)
    if motif_id:
        query = query.where(QuizQuestion.motif_id == motif_id)
    questions = (
        db.execute(query.order_by(QuizQuestion.created_at.desc())).scalars().all()
    )
    return [
        AdminQuizQuestionOut(
            id=q.id,
            motif_id=q.motif_id,
            urn_id=q.urn_id,
            question_type=q.question_type.value,
            question_text=q.question_text,
            options=q.options,
            correct_answer=q.correct_answer,
            target_mesh_name=q.target_mesh_name,
            difficulty=int(q.difficulty or 1),
            explanation=q.explanation,
            is_published=q.is_published,
            is_active=q.is_active,
            status=q.status.value if q.status else "draft",
            submitted_for_review_at=q.submitted_for_review_at,
            reviewed_by_id=q.reviewed_by_id,
            reviewed_at=q.reviewed_at,
            review_notes=q.review_notes,
            created_by_id=q.created_by_id,
            created_at=q.created_at,
        )
        for q in questions
    ]


@app.post(
    "/api/v1/admin/quiz-questions",
    response_model=AdminQuizQuestionOut,
    status_code=201,
)
def create_admin_quiz_question(
    payload: AdminQuizQuestionCreateRequest,
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db),
) -> AdminQuizQuestionOut:
    motif = db.get(Motif, payload.motif_id)
    if motif is None:
        raise HTTPException(status_code=404, detail="Motif not found")

    question_type = _normalize_question_type(payload.question_type)
    is_published = payload.is_published
    if current_user.role == UserRole.teacher:
        if is_published:
            raise HTTPException(
                status_code=403, detail="Teachers cannot publish quiz questions"
            )
        is_published = False
    if is_published is None:
        is_published = current_user.role in ADMIN_ROLES

    question = QuizQuestion(
        motif_id=payload.motif_id,
        urn_id=payload.urn_id,
        question_type=question_type,
        question_text=payload.question_text,
        options=payload.options,
        correct_answer=payload.correct_answer,
        target_mesh_name=payload.target_mesh_name,
        difficulty=int(payload.difficulty or 1),
        explanation=payload.explanation,
        is_published=is_published,
        is_active=True if payload.is_active is None else bool(payload.is_active),
        status=ContentStatus.published if is_published else ContentStatus.draft,
        created_by_id=current_user.id,
    )
    db.add(question)
    db.commit()
    db.refresh(question)

    return AdminQuizQuestionOut(
        id=question.id,
        motif_id=question.motif_id,
        urn_id=question.urn_id,
        question_type=question.question_type.value,
        question_text=question.question_text,
        options=question.options,
        correct_answer=question.correct_answer,
        target_mesh_name=question.target_mesh_name,
        difficulty=int(question.difficulty or 1),
        explanation=question.explanation,
        is_published=question.is_published,
        is_active=question.is_active,
        status=question.status.value if question.status else "draft",
        submitted_for_review_at=question.submitted_for_review_at,
        reviewed_by_id=question.reviewed_by_id,
        reviewed_at=question.reviewed_at,
        review_notes=question.review_notes,
        created_by_id=question.created_by_id,
        created_at=question.created_at,
    )


@app.patch(
    "/api/v1/admin/quiz-questions/{question_id}", response_model=AdminQuizQuestionOut
)
def update_admin_quiz_question(
    question_id: UUID,
    payload: AdminQuizQuestionUpdateRequest,
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db),
) -> AdminQuizQuestionOut:
    question = db.get(QuizQuestion, question_id)
    if question is None:
        raise HTTPException(status_code=404, detail="Question not found")

    if current_user.role == UserRole.teacher:
        if question.is_published:
            raise HTTPException(
                status_code=403,
                detail="Teachers can only edit draft questions",
            )
        if payload.is_published:
            raise HTTPException(
                status_code=403, detail="Teachers cannot publish quiz questions"
            )

    updates = payload.model_dump(exclude_unset=True)
    if "question_type" in updates:
        updates["question_type"] = _normalize_question_type(updates["question_type"])
    if "difficulty" in updates:
        updates["difficulty"] = int(updates["difficulty"] or 1)
    for field, value in updates.items():
        if field == "is_published" and current_user.role not in ADMIN_ROLES:
            continue
        setattr(question, field, value)

    db.commit()
    db.refresh(question)

    return AdminQuizQuestionOut(
        id=question.id,
        motif_id=question.motif_id,
        urn_id=question.urn_id,
        question_type=question.question_type.value,
        question_text=question.question_text,
        options=question.options,
        correct_answer=question.correct_answer,
        target_mesh_name=question.target_mesh_name,
        difficulty=int(question.difficulty or 1),
        explanation=question.explanation,
        is_published=question.is_published,
        is_active=question.is_active,
        status=question.status.value if question.status else "draft",
        submitted_for_review_at=question.submitted_for_review_at,
        reviewed_by_id=question.reviewed_by_id,
        reviewed_at=question.reviewed_at,
        review_notes=question.review_notes,
        created_by_id=question.created_by_id,
        created_at=question.created_at,
    )


class RagEmbeddingRebuildOut(BaseModel):
    total: int
    updated: int
    skipped: int


class RagHealthOut(BaseModel):
    total_documents: int
    active_documents: int
    documents_with_embeddings: int
    documents_without_embeddings: int
    coverage_percent: float
    last_embedding_updated_at: Optional[datetime] = None
    oldest_embedding_at: Optional[datetime] = None
    embedding_model: str
    settings_status: dict[str, Any]
    status: str
    issues: list[str]


class EmbeddingJobOut(BaseModel):
    id: UUID
    status: str
    total_documents: int
    processed_documents: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_by_id: UUID
    created_at: datetime
    progress_percent: float = 0.0


class EmbeddingRebuildRequest(BaseModel):
    force: bool = False


class AIJobOut(BaseModel):
    id: UUID
    user_id: UUID
    user_email: Optional[str] = None
    job_type: str
    status: str
    provider: Optional[str] = None
    prompt: Optional[str] = None
    response: Optional[str] = None
    error: Optional[str] = None
    retry_count: int
    created_at: datetime
    updated_at: datetime


def _rag_document_out(doc: RagDocument) -> schemas.RagDocumentOut:
    return schemas.RagDocumentOut(
        id=doc.id,
        title=doc.title,
        content=doc.content,
        source_type=doc.source_type,
        source_path=doc.source_path,
        is_active=doc.is_active,
        embedding_model=doc.embedding_model,
        embedding_updated_at=doc.embedding_updated_at,
        has_embedding=bool(doc.embedding),
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )


def _embedding_job_out(job: EmbeddingJob) -> EmbeddingJobOut:
    progress_percent = 0.0
    if job.total_documents > 0:
        progress_percent = (job.processed_documents / job.total_documents) * 100.0

    return EmbeddingJobOut(
        id=job.id,
        status=job.status,
        total_documents=job.total_documents,
        processed_documents=job.processed_documents,
        started_at=job.started_at,
        completed_at=job.completed_at,
        error_message=job.error_message,
        created_by_id=job.created_by_id,
        created_at=job.created_at,
        progress_percent=round(progress_percent, 2),
    )


def _embedding_url() -> str:
    base = settings.embedding_base_url.rstrip("/")
    if base.endswith("/v1"):
        return f"{base}/embeddings"
    if base.endswith("/embeddings"):
        return base
    return f"{base}/v1/embeddings"


def _call_embedding(text: str) -> Optional[list[float]]:
    if not settings.embedding_api_key or not text:
        return None

    payload = {"model": settings.embedding_model, "input": text}
    data = json.dumps(payload).encode("utf-8")
    request = UrlRequest(
        _embedding_url(),
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.embedding_api_key}",
        },
    )

    try:
        with urlopen(request, timeout=settings.embedding_timeout_seconds) as response:
            body = response.read().decode("utf-8")
    except HTTPError as exc:
        logger.warning("Embedding request failed: %s", exc)
        return None
    except URLError as exc:
        logger.warning("Embedding request failed: %s", exc)
        return None

    if not body:
        return None

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        logger.warning("Failed to decode embedding response")
        return None

    data_list = payload.get("data") or []
    if not data_list:
        return None
    embedding = data_list[0].get("embedding")
    if not isinstance(embedding, list):
        return None

    result: list[float] = []
    for value in embedding:
        try:
            result.append(float(value))
        except (TypeError, ValueError):
            continue
    return result or None


def _maybe_update_rag_embedding(session: Session, doc: RagDocument) -> bool:
    rag_settings = _get_rag_settings(session)
    if not rag_settings.embedding_enabled:
        return False
    if not settings.embedding_api_key:
        return False
    embedding = _call_embedding(doc.content or doc.title)
    if not embedding:
        return False
    doc.embedding = embedding
    doc.embedding_model = settings.embedding_model
    doc.embedding_updated_at = datetime.now(timezone.utc)
    return True


@app.get("/api/v1/admin/rag/documents", response_model=schemas.RagDocumentListOut)
def list_rag_documents(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> schemas.RagDocumentListOut:
    """List all RAG documents with pagination."""
    # Count total documents
    total = db.execute(select(func.count()).select_from(RagDocument)).scalar_one()

    # Calculate pagination
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    offset = (page - 1) * page_size

    # Get documents for current page
    docs = (
        db.execute(
            select(RagDocument)
            .order_by(RagDocument.updated_at.desc())
            .limit(page_size)
            .offset(offset)
        )
        .scalars()
        .all()
    )

    return schemas.RagDocumentListOut(
        documents=[_rag_document_out(doc) for doc in docs],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@app.get(
    "/api/v1/admin/rag/documents/{document_id}",
    response_model=schemas.RagDocumentOut,
)
def get_rag_document(
    document_id: UUID,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> schemas.RagDocumentOut:
    """Get a single RAG document by ID."""
    doc = db.get(RagDocument, document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return _rag_document_out(doc)


@app.post(
    "/api/v1/admin/rag/documents",
    response_model=schemas.RagDocumentOut,
    status_code=201,
)
def create_rag_document(
    payload: schemas.RagDocumentCreateIn,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> schemas.RagDocumentOut:
    """Create a new RAG document with manual text input."""
    doc = RagDocument(
        title=payload.title,
        content=payload.content,
        source_type="manual",
        is_active=bool(payload.is_active) if payload.is_active is not None else True,
    )
    db.add(doc)
    _maybe_update_rag_embedding(db, doc)
    db.commit()
    db.refresh(doc)
    return _rag_document_out(doc)


@app.post(
    "/api/v1/admin/rag/documents/upload",
    response_model=schemas.RagDocumentOut,
    status_code=201,
)
async def upload_rag_document(
    file: UploadFile = File(...),
    title: Optional[str] = Query(default=None),
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> schemas.RagDocumentOut:
    """Upload a RAG document from a file (.txt, .md, .json)."""
    # Validate file type (fail closed: accept only when positively validated)
    content_type_ok = file.content_type in RAG_ALLOWED_FILE_TYPES
    extension_ok = bool(file.filename) and Path(file.filename).suffix.lower() in {
        ".txt",
        ".md",
        ".json",
    }
    if not (content_type_ok or extension_ok):
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Allowed: .txt, .md, .json",
        )

    # Check file size (5MB limit as per requirements)
    max_bytes = 5 * 1024 * 1024
    contents = await file.read(max_bytes + 1)
    if len(contents) > max_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: 5MB",
        )

    # Decode content (fail closed: reject non-UTF-8 input rather than corrupting it)
    try:
        decoded = contents.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="File must be valid UTF-8 text",
        )

    # Create document
    doc_title = title or Path(file.filename or "RAG Document").stem
    doc = RagDocument(
        title=doc_title,
        content=decoded,
        source_type="file",
        source_path=file.filename,
        is_active=True,
    )
    db.add(doc)
    _maybe_update_rag_embedding(db, doc)
    db.commit()
    db.refresh(doc)
    return _rag_document_out(doc)


@app.put(
    "/api/v1/admin/rag/documents/{document_id}",
    response_model=schemas.RagDocumentOut,
)
def update_rag_document(
    document_id: UUID,
    payload: schemas.RagDocumentUpdateIn,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> schemas.RagDocumentOut:
    """Update a RAG document. Clears embedding when content changes."""
    doc = db.get(RagDocument, document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")

    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(doc, field, value)

    # Clear and rebuild embedding if content or title changed
    if "content" in updates or "title" in updates:
        doc.embedding = None
        doc.embedding_model = None
        doc.embedding_updated_at = None
        _maybe_update_rag_embedding(db, doc)

    db.commit()
    db.refresh(doc)
    return _rag_document_out(doc)


@app.delete("/api/v1/admin/rag/documents/{document_id}", status_code=204)
def delete_rag_document(
    document_id: UUID,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> Response:
    """Delete a RAG document."""
    doc = db.get(RagDocument, document_id)
    if doc is None:
        return Response(status_code=204)
    db.delete(doc)
    db.commit()
    return Response(status_code=204)


@app.post(
    "/api/v1/admin/rag/documents/{document_id}/activate",
    response_model=schemas.RagDocumentOut,
)
def activate_rag_document(
    document_id: UUID,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> schemas.RagDocumentOut:
    """Activate a RAG document."""
    doc = db.get(RagDocument, document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")

    doc.is_active = True
    db.commit()
    db.refresh(doc)
    return _rag_document_out(doc)


@app.post(
    "/api/v1/admin/rag/documents/{document_id}/deactivate",
    response_model=schemas.RagDocumentOut,
)
def deactivate_rag_document(
    document_id: UUID,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> schemas.RagDocumentOut:
    """Deactivate a RAG document."""
    doc = db.get(RagDocument, document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")

    doc.is_active = False
    db.commit()
    db.refresh(doc)
    return _rag_document_out(doc)


@app.get("/api/v1/admin/rag/settings", response_model=schemas.RagSettingsOut)
def get_rag_settings(
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> schemas.RagSettingsOut:
    """Get current RAG settings."""
    settings_row = _get_rag_settings(db)
    return schemas.RagSettingsOut(
        system_instruction=settings_row.system_instruction,
        prompt_prefix=settings_row.prompt_prefix,
        model_override=settings_row.model_override,
        temperature=settings_row.temperature,
        max_documents=int(settings_row.max_documents or 6),
        embedding_enabled=bool(settings_row.embedding_enabled),
        hybrid_alpha=float(settings_row.hybrid_alpha or 0.6),
    )


@app.put("/api/v1/admin/rag/settings", response_model=schemas.RagSettingsOut)
def update_rag_settings(
    payload: schemas.RagSettingsUpdateIn,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> schemas.RagSettingsOut:
    """Update RAG settings with validation."""
    settings_row = _get_rag_settings(db)
    updates = payload.model_dump(exclude_unset=True)
    if "model_override" in updates:
        value = updates.get("model_override")
        updates["model_override"] = value if value else None
    for field, value in updates.items():
        setattr(settings_row, field, value)
    db.commit()
    db.refresh(settings_row)
    return schemas.RagSettingsOut(
        system_instruction=settings_row.system_instruction,
        prompt_prefix=settings_row.prompt_prefix,
        model_override=settings_row.model_override,
        temperature=settings_row.temperature,
        max_documents=int(settings_row.max_documents or 6),
        embedding_enabled=bool(settings_row.embedding_enabled),
        hybrid_alpha=float(settings_row.hybrid_alpha or 0.6),
    )


@app.post("/api/v1/admin/rag/settings/reset", response_model=schemas.RagSettingsOut)
def reset_rag_settings(
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> schemas.RagSettingsOut:
    """Reset RAG settings to default values."""
    settings_row = _get_rag_settings(db)
    defaults = get_rag_defaults()

    # Apply all default values
    for field, value in defaults.items():
        setattr(settings_row, field, value)

    db.commit()
    db.refresh(settings_row)

    return schemas.RagSettingsOut(
        system_instruction=settings_row.system_instruction,
        prompt_prefix=settings_row.prompt_prefix,
        model_override=settings_row.model_override,
        temperature=settings_row.temperature,
        max_documents=int(settings_row.max_documents or 6),
        embedding_enabled=bool(settings_row.embedding_enabled),
        hybrid_alpha=float(settings_row.hybrid_alpha or 0.6),
    )


@app.post(
    "/api/v1/admin/rag/rebuild",
    response_model=EmbeddingJobOut,
    status_code=202,
)
def start_rebuild_embeddings(
    payload: EmbeddingRebuildRequest = EmbeddingRebuildRequest(),
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> EmbeddingJobOut:
    """
    Start a new embedding rebuild job.

    This creates a job and rebuilds all embeddings for active RAG documents.
    Use force=true to rebuild even if embeddings already exist.
    """
    from .services.embeddings import rebuild_all_embeddings

    # Create a new job
    job = EmbeddingJob(
        status="pending",
        total_documents=0,
        processed_documents=0,
        created_by_id=current_user.id,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    try:
        # Run the rebuild process
        rebuild_all_embeddings(db, job, force=payload.force)
        db.refresh(job)
    except Exception as e:
        logger.error("Embedding rebuild job failed: %s", str(e), exc_info=True)
        # Job status is already updated in the service
        db.refresh(job)

    return _embedding_job_out(job)


@app.get(
    "/api/v1/admin/rag/rebuild/status",
    response_model=EmbeddingJobOut,
)
def get_rebuild_status(
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> EmbeddingJobOut:
    """
    Get the status of the most recent embedding rebuild job.
    """
    from .services.embeddings import get_latest_job

    job = get_latest_job(db)
    if job is None:
        raise HTTPException(status_code=404, detail="No rebuild jobs found")

    return _embedding_job_out(job)


@app.get(
    "/api/v1/admin/rag/rebuild/{job_id}",
    response_model=EmbeddingJobOut,
)
def get_rebuild_job(
    job_id: UUID,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> EmbeddingJobOut:
    """
    Get the status of a specific embedding rebuild job.
    """
    from .services.embeddings import get_job_by_id

    job = get_job_by_id(db, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    return _embedding_job_out(job)


# Legacy endpoint - kept for backward compatibility
@app.post(
    "/api/v1/admin/rag/embeddings/rebuild",
    response_model=RagEmbeddingRebuildOut,
    deprecated=True,
)
def rebuild_rag_embeddings(
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> RagEmbeddingRebuildOut:
    """
    Legacy endpoint for rebuilding embeddings.

    Deprecated: Use POST /api/v1/admin/rag/rebuild for progress tracking.
    """
    from .services.embeddings import update_document_embedding

    docs = (
        db.execute(select(RagDocument).order_by(RagDocument.updated_at.desc()))
        .scalars()
        .all()
    )
    total = len(docs)
    updated = 0
    skipped = 0
    for doc in docs:
        try:
            if update_document_embedding(db, doc):
                updated += 1
            else:
                skipped += 1
        except Exception:
            skipped += 1
            logger.warning(
                "Failed to rebuild embedding for RAG document %s",
                doc.id,
                exc_info=True,
            )
    db.commit()
    return RagEmbeddingRebuildOut(total=total, updated=updated, skipped=skipped)


@app.get("/api/v1/admin/rag/health", response_model=RagHealthOut)
def get_rag_health(
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> RagHealthOut:
    """Get comprehensive RAG health status."""
    # Get all documents
    all_docs = db.execute(select(RagDocument)).scalars().all()
    total_documents = len(all_docs)

    # Count active documents
    active_docs = [doc for doc in all_docs if doc.is_active]
    active_documents = len(active_docs)

    # Count documents with/without embeddings
    docs_with_embeddings = [doc for doc in all_docs if doc.embedding is not None]
    documents_with_embeddings = len(docs_with_embeddings)
    documents_without_embeddings = total_documents - documents_with_embeddings

    # Calculate coverage percentage
    coverage_percent = (
        (documents_with_embeddings / total_documents * 100.0)
        if total_documents > 0
        else 0.0
    )

    # Find last and oldest embedding update times
    last_embedding_updated_at: Optional[datetime] = None
    oldest_embedding_at: Optional[datetime] = None

    if docs_with_embeddings:
        embedding_times = [
            doc.embedding_updated_at
            for doc in docs_with_embeddings
            if doc.embedding_updated_at
        ]
        if embedding_times:
            last_embedding_updated_at = max(embedding_times)
            oldest_embedding_at = min(embedding_times)

    # Get current embedding model
    embedding_model = settings.embedding_model

    # Get RAG settings status
    rag_settings = _get_rag_settings(db)
    settings_status = {
        "embedding_enabled": rag_settings.embedding_enabled,
        "max_documents": rag_settings.max_documents,
        "hybrid_alpha": rag_settings.hybrid_alpha,
        "model_override": rag_settings.model_override,
        "temperature": rag_settings.temperature,
    }

    # Determine health status and issues
    issues: list[str] = []

    # Check for embedding API configuration
    if not settings.embedding_api_key:
        issues.append("Embedding API key not configured")

    # Check if embeddings are disabled
    if not rag_settings.embedding_enabled:
        issues.append("Embeddings are disabled in settings")

    # Check for documents without embeddings
    if documents_without_embeddings > 0 and rag_settings.embedding_enabled:
        issues.append(f"{documents_without_embeddings} document(s) missing embeddings")

    # Check for inactive documents
    inactive_count = total_documents - active_documents
    if inactive_count > 0:
        issues.append(f"{inactive_count} inactive document(s)")

    # Check if there are no documents at all
    if total_documents == 0:
        issues.append("No RAG documents available")

    # Determine overall status
    if total_documents == 0 or coverage_percent < 50:
        status = "unhealthy"
    elif coverage_percent < 90 or len(issues) > 0:
        status = "degraded"
    else:
        status = "healthy"

    return RagHealthOut(
        total_documents=total_documents,
        active_documents=active_documents,
        documents_with_embeddings=documents_with_embeddings,
        documents_without_embeddings=documents_without_embeddings,
        coverage_percent=round(coverage_percent, 2),
        last_embedding_updated_at=last_embedding_updated_at,
        oldest_embedding_at=oldest_embedding_at,
        embedding_model=embedding_model,
        settings_status=settings_status,
        status=status,
        issues=issues,
    )


# =============================================================================
# RETENTION ANALYTICS ENDPOINTS
# =============================================================================


@app.get(
    "/api/v1/admin/analytics/retention", response_model=schemas.RetentionMetricsOut
)
def get_retention_metrics(
    days_ago: Optional[int] = Query(
        None, description="Number of days to look back for user cohort (optional)"
    ),
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> schemas.RetentionMetricsOut:
    """
    Get overall retention metrics (D1, D7, D30).

    Calculates retention rates showing what percentage of users return
    after 1, 7, and 30 days from their signup date.

    Admin only.
    """
    from .services.retention import calculate_overall_retention

    result = calculate_overall_retention(db, days_ago=days_ago)
    return schemas.RetentionMetricsOut(**result)


@app.get(
    "/api/v1/admin/analytics/retention/cohorts",
    response_model=schemas.CohortRetentionOut,
)
def get_cohort_retention(
    period: str = Query(
        "week",
        description="Cohort grouping period: 'week' or 'month'",
        regex="^(week|month)$",
    ),
    limit: int = Query(
        12, ge=1, le=52, description="Maximum number of cohorts to return"
    ),
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> schemas.CohortRetentionOut:
    """
    Get retention metrics grouped by signup cohort.

    Returns retention rates for users grouped by their signup week or month.
    Useful for tracking how retention changes over time across different
    user cohorts.

    Admin only.
    """
    from .services.retention import calculate_cohort_retention

    result = calculate_cohort_retention(db, period=period, limit=limit)
    return schemas.CohortRetentionOut(**result)


@app.get(
    "/api/v1/admin/analytics/retention/curve", response_model=schemas.RetentionCurveOut
)
def get_retention_curve(
    days: int = Query(
        30, ge=1, le=90, description="Number of days to calculate retention for"
    ),
    cohort_days_ago: int = Query(
        90, ge=30, le=365, description="How far back to include users in the cohort"
    ),
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> schemas.RetentionCurveOut:
    """
    Get retention curve data for visualization.

    Returns daily retention rates from day 0 to the specified day count.
    Used for plotting retention curves that show how user retention
    decays over time.

    Admin only.
    """
    from .services.retention import calculate_retention_curve

    result = calculate_retention_curve(db, days=days, cohort_days_ago=cohort_days_ago)
    return schemas.RetentionCurveOut(**result)


class LeaderboardEntryOut(BaseModel):
    rank: int
    user_id: UUID
    display_name: str
    avatar_url: Optional[str] = None
    total_xp: int
    title: str


@app.get("/api/v1/leaderboard", response_model=schemas.EnhancedLeaderboardOut)
def get_leaderboard(
    scope: str = Query("global", regex="^(global|friends|class)$"),
    limit: int = Query(50, ge=1, le=200),
    order_by: str = Query("xp", regex="^(xp|streak)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.EnhancedLeaderboardOut:
    """
    Get leaderboard with optional scope filtering.

    Scopes:
    - global: All users (default)
    - friends: Only mutual follows
    - class: Classroom leaderboard (not implemented yet)

    Order by:
    - xp: Total experience points (default)
    - streak: Current streak
    """
    from .services import leaderboard as leaderboard_service

    if scope == "class":
        raise HTTPException(
            status_code=501,
            detail="Classroom leaderboard is not implemented yet",
        )
    if scope == "friends":
        entries, user_rank, total_users = leaderboard_service.get_friends_leaderboard(
            db=db,
            user_id=current_user.id,
            limit=limit,
            order_by=order_by,
        )
    else:  # global
        entries, user_rank, total_users = leaderboard_service.get_global_leaderboard(
            db=db,
            current_user_id=current_user.id,
            limit=limit,
            order_by=order_by,
        )

    # Build response entries with title
    enhanced_entries = []
    user_entry = None
    for entry in entries:
        current_rank, _, _ = _compute_rank(entry["total_xp"])
        enhanced_entry = schemas.EnhancedLeaderboardEntryOut(
            rank=entry["rank"],
            user_id=entry["user_id"],
            display_name=entry["display_name"],
            avatar_url=entry.get("avatar_url"),
            total_xp=entry["total_xp"],
            current_streak=entry.get("current_streak", 0),
            title=str(current_rank["name"]),
        )
        enhanced_entries.append(enhanced_entry)

        if entry["user_id"] == current_user.id:
            user_entry = enhanced_entry

    return schemas.EnhancedLeaderboardOut(
        scope=scope,
        entries=enhanced_entries,
        user_rank=user_rank,
        user_entry=user_entry,
        total_users=total_users,
    )


@app.get("/api/v1/leaderboard/friends", response_model=schemas.EnhancedLeaderboardOut)
def get_friends_leaderboard_endpoint(
    limit: int = Query(50, ge=1, le=200),
    order_by: str = Query("xp", regex="^(xp|streak)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.EnhancedLeaderboardOut:
    """Get leaderboard of user's friends (mutual follows)."""
    from .services import leaderboard as leaderboard_service

    entries, user_rank, total_users = leaderboard_service.get_friends_leaderboard(
        db=db,
        user_id=current_user.id,
        limit=limit,
        order_by=order_by,
    )

    # Build response entries with title
    enhanced_entries = []
    user_entry = None
    for entry in entries:
        current_rank, _, _ = _compute_rank(entry["total_xp"])
        enhanced_entry = schemas.EnhancedLeaderboardEntryOut(
            rank=entry["rank"],
            user_id=entry["user_id"],
            display_name=entry["display_name"],
            avatar_url=entry.get("avatar_url"),
            total_xp=entry["total_xp"],
            current_streak=entry.get("current_streak", 0),
            title=str(current_rank["name"]),
        )
        enhanced_entries.append(enhanced_entry)

        if entry["user_id"] == current_user.id:
            user_entry = enhanced_entry

    return schemas.EnhancedLeaderboardOut(
        scope="friends",
        entries=enhanced_entries,
        user_rank=user_rank,
        user_entry=user_entry,
        total_users=total_users,
    )


@app.get("/api/v1/leaderboard/settings", response_model=schemas.LeaderboardSettingsOut)
def get_leaderboard_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.LeaderboardSettingsOut:
    """Get user's leaderboard settings."""
    from .services import leaderboard as leaderboard_service

    settings = leaderboard_service.get_or_create_leaderboard_settings(
        db, current_user.id
    )
    return schemas.LeaderboardSettingsOut(
        id=settings.id,
        user_id=settings.user_id,
        show_on_global=settings.show_on_global,
        show_real_name=settings.show_real_name,
        preferred_leaderboard=settings.preferred_leaderboard,
        created_at=settings.created_at,
        updated_at=settings.updated_at,
    )


@app.put("/api/v1/leaderboard/settings", response_model=schemas.LeaderboardSettingsOut)
def update_leaderboard_settings(
    payload: schemas.LeaderboardSettingsUpdateIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.LeaderboardSettingsOut:
    """Update user's leaderboard settings."""
    from .services import leaderboard as leaderboard_service

    settings = leaderboard_service.update_leaderboard_settings(
        db=db,
        user_id=current_user.id,
        show_on_global=payload.show_on_global,
        show_real_name=payload.show_real_name,
        preferred_leaderboard=payload.preferred_leaderboard,
    )

    return schemas.LeaderboardSettingsOut(
        id=settings.id,
        user_id=settings.user_id,
        show_on_global=settings.show_on_global,
        show_real_name=settings.show_real_name,
        preferred_leaderboard=settings.preferred_leaderboard,
        created_at=settings.created_at,
        updated_at=settings.updated_at,
    )


class QuizQuestionOut(BaseModel):
    id: UUID
    question_type: str
    question_text: str
    options: Optional[list[Any]] = None
    target_mesh_name: Optional[str] = None
    difficulty: int
    image_url: Optional[str] = None


class MotifQuizResponse(BaseModel):
    motif_id: UUID
    questions: list[QuizQuestionOut]
    attempts: int
    best_score: int
    pass_percent: int


@app.get("/api/v1/motifs/{motif_id}/quiz", response_model=MotifQuizResponse)
def get_motif_quiz(
    motif_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MotifQuizResponse:
    motif = db.get(Motif, motif_id)
    if motif is None or not motif.is_active:
        raise HTTPException(status_code=404, detail="Motif not found")

    progress = db.execute(
        select(UserProgress).where(
            UserProgress.user_id == current_user.id, UserProgress.motif_id == motif.id
        )
    ).scalar_one_or_none()

    if progress is None or progress.status == UnlockStatus.hidden:
        raise HTTPException(status_code=403, detail="Motif is locked")
    if progress.status == UnlockStatus.discovered:
        raise HTTPException(status_code=400, detail="Lesson not completed")

    status_before = progress.status

    can_view_drafts = _can_view_drafts(current_user)

    question_query = select(QuizQuestion).where(
        QuizQuestion.motif_id == motif.id, QuizQuestion.is_active.is_(True)
    )
    if not can_view_drafts:
        question_query = question_query.where(QuizQuestion.is_published.is_(True))

    questions = (
        db.execute(question_query.order_by(QuizQuestion.created_at.asc()))
        .scalars()
        .all()
    )

    return MotifQuizResponse(
        motif_id=motif.id,
        questions=[
            QuizQuestionOut(
                id=q.id,
                question_type=q.question_type.value,
                question_text=q.question_text,
                options=q.options if isinstance(q.options, list) else None,
                target_mesh_name=q.target_mesh_name,
                difficulty=max(1, int(q.difficulty or 1)),
                image_url=None,
            )
            for q in questions
        ],
        attempts=progress.quiz_attempts,
        best_score=progress.quiz_best_score,
        pass_percent=QUIZ_PASS_PERCENT,
    )


class QuizAnswerIn(BaseModel):
    question_id: UUID
    answer: str


class QuizSubmitRequest(BaseModel):
    motif_id: UUID
    answers: list[QuizAnswerIn]
    time_taken_seconds: Optional[int] = Field(default=None, ge=0, le=3600)


class QuizResultDetail(BaseModel):
    question_id: UUID
    correct: bool
    correct_answer: str
    user_answer: Optional[str] = None
    explanation: Optional[str] = None


class QuizSubmitResponse(BaseModel):
    motif_id: UUID
    score: int
    max_score: int
    percentage: int
    passed: bool
    status: str
    attempts: int
    best_score: int
    xp_awarded: int
    total_xp: int
    results: list[QuizResultDetail]


@app.post("/api/v1/quizzes/submit", response_model=QuizSubmitResponse)
def submit_quiz(
    payload: QuizSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> QuizSubmitResponse:
    motif = db.get(Motif, payload.motif_id)
    if motif is None or not motif.is_active:
        raise HTTPException(status_code=404, detail="Motif not found")

    progress = db.execute(
        select(UserProgress).where(
            UserProgress.user_id == current_user.id, UserProgress.motif_id == motif.id
        )
    ).scalar_one_or_none()

    if progress is None or progress.status == UnlockStatus.hidden:
        raise HTTPException(status_code=403, detail="Motif is locked")
    if progress.status == UnlockStatus.discovered:
        raise HTTPException(status_code=400, detail="Lesson not completed")

    status_before = progress.status

    can_view_drafts = _can_view_drafts(current_user)

    question_query = select(QuizQuestion).where(
        QuizQuestion.motif_id == motif.id, QuizQuestion.is_active.is_(True)
    )
    if not can_view_drafts:
        question_query = question_query.where(QuizQuestion.is_published.is_(True))

    questions = (
        db.execute(question_query.order_by(QuizQuestion.created_at.asc()))
        .scalars()
        .all()
    )
    if not questions:
        raise HTTPException(status_code=404, detail="No quiz questions found")

    answer_map: dict[UUID, str] = {}
    for ans in payload.answers:
        if ans.question_id in answer_map:
            raise HTTPException(
                status_code=400, detail="Duplicate answer for a question"
            )
        answer_map[ans.question_id] = ans.answer

    question_ids = {q.id for q in questions}
    if set(answer_map.keys()) != question_ids:
        raise HTTPException(
            status_code=400,
            detail="Answers must include all quiz questions for this motif",
        )

    score = 0
    max_score = len(questions)
    results: list[QuizResultDetail] = []

    for q in questions:
        submitted = (answer_map.get(q.id) or "").strip()
        expected = (q.correct_answer or "").strip()
        is_correct = submitted == expected
        if is_correct:
            score += 1

        results.append(
            QuizResultDetail(
                question_id=q.id,
                correct=is_correct,
                correct_answer=expected,
                user_answer=submitted,
                explanation=(q.explanation or "").strip() or None,
            )
        )

        # Update skill level for adaptive learning if question has skill_type
        if q.skill_type:
            from backend.services.adaptive_quiz import update_skill_level

            try:
                update_skill_level(
                    db,
                    user_id=current_user.id,
                    skill_type=q.skill_type,
                    question_difficulty=q.difficulty,
                    is_correct=is_correct,
                )
            except Exception as e:
                # Log but don't fail the quiz submission
                logger.warning(
                    f"Failed to update skill level: {e}",
                    extra={
                        "user_id": str(current_user.id),
                        "question_id": str(q.id),
                        "skill_type": q.skill_type,
                    },
                )

    percentage = int(round((score / max_score) * 100)) if max_score > 0 else 0
    passed = percentage >= QUIZ_PASS_PERCENT

    total_xp_before = current_user.total_xp
    now = datetime.now(timezone.utc)

    progress.quiz_attempts += 1
    progress.quiz_best_score = max(progress.quiz_best_score, percentage)

    badge_bonus = 0
    badge_attempts: list[str] = []
    if passed:
        mastered_before = db.execute(
            select(func.count(UserProgress.id)).where(
                UserProgress.user_id == current_user.id,
                UserProgress.status == UnlockStatus.mastered,
            )
        ).scalar_one()

        target_xp = DISCOVERY_XP + LESSON_XP + MASTERED_XP
        if progress.status != UnlockStatus.mastered:
            progress.status = UnlockStatus.mastered
            progress.mastered_at = progress.mastered_at or now

        if progress.xp_earned < target_xp:
            delta = target_xp - progress.xp_earned
            progress.xp_earned = target_xp
            # Apply XP boost if active
            delta_with_boost = _apply_xp_boost(current_user, delta, now)
            current_user.total_xp += delta_with_boost

        if int(mastered_before or 0) == 0:
            badge_attempts.append(BADGE_FIRST_MASTERED)
            badge_bonus += _award_badge(
                db, user=current_user, badge_slug=BADGE_FIRST_MASTERED
            )

    # Track first quiz passed milestone
    if passed:
        passed_before = db.execute(
            select(func.count(QuizAttempt.id)).where(
                QuizAttempt.user_id == current_user.id,
                QuizAttempt.percentage >= 70,
            )
        ).scalar_one()
        if passed_before == 0:
            from backend.services.milestones import check_and_create_first_quiz_passed

            check_and_create_first_quiz_passed(
                db, current_user.id, motif.id, score, max_score, percentage
            )

    _update_streak(current_user, now)
    if current_user.current_streak >= 7:
        badge_attempts.append(BADGE_STREAK_7)
        badge_bonus += _award_badge(db, user=current_user, badge_slug=BADGE_STREAK_7)
        # Track first 7-day streak milestone
        from backend.services.milestones import check_and_create_first_streak_7

        check_and_create_first_streak_7(
            db, current_user.id, current_user.current_streak
        )

    # Check quiz badges
    if percentage == 100:
        badge_attempts.append(BADGE_PERFECT_SCORE)
        badge_bonus += _award_badge(
            db, user=current_user, badge_slug=BADGE_PERFECT_SCORE
        )
    if payload.time_taken_seconds is not None and payload.time_taken_seconds <= 30:
        badge_attempts.append(BADGE_SPEED_DEMON)
        badge_bonus += _award_badge(db, user=current_user, badge_slug=BADGE_SPEED_DEMON)

    # Count perfect quizzes for quiz-master
    perfect_count = db.execute(
        select(func.count(QuizAttempt.id)).where(
            QuizAttempt.user_id == current_user.id, QuizAttempt.percentage == 100
        )
    ).scalar_one()
    if percentage == 100:
        perfect_count += 1
    if perfect_count >= 10:
        badge_attempts.append(BADGE_QUIZ_MASTER)
        badge_bonus += _award_badge(db, user=current_user, badge_slug=BADGE_QUIZ_MASTER)
    current_user.last_active_at = now

    db.add(
        QuizAttempt(
            user_id=current_user.id,
            motif_id=motif.id,
            score=score,
            max_score=max_score,
            percentage=percentage,
            answers=[
                {"question_id": str(k), "answer": v} for k, v in answer_map.items()
            ],
            time_taken_seconds=payload.time_taken_seconds,
        )
    )

    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.exception(
            "Failed to submit quiz",
            extra={
                "user_id": str(current_user.id),
                "motif_id": str(motif.id),
                "percentage": percentage,
                "score": score,
                "max_score": max_score,
                "passed": passed,
                "badge_attempts": badge_attempts,
                "badge_bonus": badge_bonus,
                "status_before": status_before.value,
                "status_after": progress.status.value,
                "error": str(exc),
            },
        )
        raise HTTPException(status_code=500, detail="Failed to submit quiz")

    _record_analytics_event(
        db,
        user_id=current_user.id,
        name="quiz_completed",
        payload={
            "source": "server",
            "motif_id": str(motif.id),
            "urn_id": str(motif.urn_id),
            "score": score,
            "max_score": max_score,
            "percentage": percentage,
            "passed": passed,
            "time_taken_seconds": payload.time_taken_seconds,
        },
    )
    if passed and status_before != UnlockStatus.mastered:
        _record_analytics_event(
            db,
            user_id=current_user.id,
            name="motif_mastered",
            payload={
                "source": "server",
                "motif_id": str(motif.id),
                "urn_id": str(motif.urn_id),
                "percentage": percentage,
            },
        )

    return QuizSubmitResponse(
        motif_id=motif.id,
        score=score,
        max_score=max_score,
        percentage=percentage,
        passed=passed,
        status=progress.status.value,
        attempts=progress.quiz_attempts,
        best_score=progress.quiz_best_score,
        xp_awarded=(current_user.total_xp - total_xp_before),
        total_xp=current_user.total_xp,
        results=results,
    )


# =============================================================================
# ADAPTIVE QUIZ ENDPOINTS
# =============================================================================


@app.get("/api/v1/quiz/adaptive", response_model=schemas.AdaptiveQuizOut)
def get_adaptive_quiz(
    motif_id: Optional[UUID] = Query(default=None),
    skill_type: Optional[str] = Query(default=None),
    limit: int = Query(default=10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.AdaptiveQuizOut:
    """
    Get adaptive quiz questions based on user's skill level.

    Query parameters:
    - motif_id: Optional motif ID to filter questions
    - skill_type: Optional skill type (motif_recognition, history_knowledge, cultural_understanding)
    - limit: Number of questions to return (1-50, default 10)
    """
    from backend.services.adaptive_quiz import (
        get_adaptive_questions,
        get_recommended_difficulty,
    )

    # Validate skill type if provided
    if skill_type and skill_type not in [st.value for st in SkillType]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid skill_type. Must be one of: {', '.join([st.value for st in SkillType])}",
        )

    # Get recommended difficulty
    if skill_type:
        recommended_difficulty = get_recommended_difficulty(
            db, current_user.id, skill_type
        )
    else:
        # Get average across all skills
        stmt = select(func.avg(UserSkillLevel.skill_level)).where(
            UserSkillLevel.user_id == current_user.id
        )
        avg_skill = db.execute(stmt).scalar()
        recommended_difficulty = avg_skill if avg_skill is not None else 0.5

    # Get adaptive questions
    questions = get_adaptive_questions(
        db,
        user_id=current_user.id,
        motif_id=motif_id,
        skill_type=skill_type,
        limit=limit,
    )

    if not questions:
        raise HTTPException(
            status_code=404, detail="No questions found matching your skill level"
        )

    # Convert to schema format
    question_outs = []
    for q in questions:
        options = []
        if q.options:
            for opt in q.options:
                options.append(
                    schemas.QuizOptionOut(
                        id=opt.get("id", ""),
                        text=opt.get("text", ""),
                        image_url=opt.get("image_url"),
                    )
                )

        question_outs.append(
            schemas.QuizQuestionOut(
                id=q.id,
                question_text=q.question_text,
                question_type=q.question_type.value,
                options=options,
                target_mesh_name=q.target_mesh_name,
            )
        )

    return schemas.AdaptiveQuizOut(
        motif_id=motif_id,
        skill_type=skill_type,
        recommended_difficulty=recommended_difficulty,
        questions=question_outs,
    )


@app.get("/api/v1/skills", response_model=schemas.UserSkillsOut)
def get_user_skills(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.UserSkillsOut:
    """Get user's skill levels across all skill types."""
    from backend.services.adaptive_quiz import get_user_skill_level

    skills = []
    total_level = 0.0

    for skill_type in SkillType:
        skill = get_user_skill_level(db, current_user.id, skill_type.value)
        skills.append(
            schemas.UserSkillLevelOut(
                id=skill.id,
                user_id=skill.user_id,
                skill_type=skill.skill_type,
                skill_level=skill.skill_level,
                total_questions=skill.total_questions,
                correct_answers=skill.correct_answers,
                accuracy=(skill.correct_answers / skill.total_questions * 100)
                if skill.total_questions > 0
                else 0.0,
                last_updated_at=skill.last_updated_at,
                created_at=skill.created_at,
            )
        )
        total_level += skill.skill_level

    overall_level = total_level / len(SkillType) if len(SkillType) > 0 else 0.5

    return schemas.UserSkillsOut(
        skills=skills,
        overall_level=overall_level,
    )


@app.post("/api/v1/skills/recalculate", response_model=schemas.UserSkillsOut)
def recalculate_user_skills(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.UserSkillsOut:
    """
    Recalculate user's skill levels from quiz history.
    Useful for backfilling or recalibrating skill levels.
    """
    from backend.services.adaptive_quiz import recalculate_user_skills

    # Recalculate all skills
    updated_skills = recalculate_user_skills(db, current_user.id)

    skills = []
    total_level = 0.0

    for skill in updated_skills:
        skills.append(
            schemas.UserSkillLevelOut(
                id=skill.id,
                user_id=skill.user_id,
                skill_type=skill.skill_type,
                skill_level=skill.skill_level,
                total_questions=skill.total_questions,
                correct_answers=skill.correct_answers,
                accuracy=(skill.correct_answers / skill.total_questions * 100)
                if skill.total_questions > 0
                else 0.0,
                last_updated_at=skill.last_updated_at,
                created_at=skill.created_at,
            )
        )
        total_level += skill.skill_level

    overall_level = (
        total_level / len(updated_skills) if len(updated_skills) > 0 else 0.5
    )

    return schemas.UserSkillsOut(
        skills=skills,
        overall_level=overall_level,
    )


# =============================================================================
# QUIZ HINTS ENDPOINTS (P1-AI-02)
# =============================================================================


@app.post(
    "/api/v1/quiz/questions/{question_id}/hint", response_model=schemas.QuizHintOut
)
def request_quiz_hint(
    question_id: UUID,
    payload: schemas.QuizHintRequestIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.QuizHintOut:
    """
    Request a context-aware hint for a quiz question.

    Hint types:
    - explain: Explain the concept without giving answer (0 hearts)
    - clue: Give a subtle clue towards the answer (1 heart)
    - elimination: Eliminate one wrong answer (2 hearts)
    """
    from backend.models import HintType as HintTypeEnum
    from backend.services.quiz_hints import (
        HintType,
        create_hint_request,
    )

    # Validate hint type
    try:
        hint_type = HintTypeEnum(payload.hint_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid hint_type. Must be one of: {', '.join([ht.value for ht in HintTypeEnum])}",
        )

    # Create hint request
    try:
        hint_request = create_hint_request(
            db=db,
            user=current_user,
            question_id=question_id,
            hint_type=hint_type,
            collect_ai_sources_fn=_collect_ai_sources,
            call_deepseek_fn=_call_deepseek_chat,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    return schemas.QuizHintOut(
        id=hint_request.id,
        question_id=hint_request.question_id,
        hint_type=hint_request.hint_type,
        hint_text=hint_request.hint_text,
        heart_cost=hint_request.heart_cost,
        created_at=hint_request.created_at,
        rag_sources=hint_request.rag_sources,
    )


@app.get(
    "/api/v1/quiz/questions/{question_id}/hints",
    response_model=schemas.QuizHintsListOut,
)
def get_question_hints(
    question_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.QuizHintsListOut:
    """
    Get all hints the user has requested for a specific question.
    """
    from backend.services.quiz_hints import get_question_hints as get_hints

    # Verify question exists
    question = db.get(QuizQuestion, question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    # Get hints
    hints = get_hints(db, current_user, question_id)

    return schemas.QuizHintsListOut(
        hints=[
            schemas.QuizHintOut(
                id=hint.id,
                question_id=hint.question_id,
                hint_type=hint.hint_type,
                hint_text=hint.hint_text,
                heart_cost=hint.heart_cost,
                created_at=hint.created_at,
                rag_sources=hint.rag_sources,
            )
            for hint in hints
        ],
        total=len(hints),
    )


# =============================================================================
# URN EXAM ELIGIBILITY
# =============================================================================


def _build_urn_exam_eligibility_detail(
    db: Session, *, user: User, urn: Urn
) -> tuple[list[dict[str, Any]], int]:
    motifs = (
        db.execute(
            select(Motif).where(Motif.urn_id == urn.id, Motif.is_active.is_(True))
        )
        .scalars()
        .all()
    )
    if not motifs:
        return [], 0

    progress_entries = (
        db.execute(
            select(UserProgress).where(
                UserProgress.user_id == user.id,
                UserProgress.motif_id.in_([m.id for m in motifs]),
            )
        )
        .scalars()
        .all()
    )
    progress_by_id = {p.motif_id: p for p in progress_entries}

    missing = []
    for motif in motifs:
        progress = progress_by_id.get(motif.id)
        status = progress.status if progress else UnlockStatus.hidden
        if status != UnlockStatus.mastered:
            missing.append(
                {
                    "id": str(motif.id),
                    "name": motif.name,
                    "mesh_name": motif.mesh_name,
                    "status": status.value,
                }
            )

    return missing, len(motifs)


def _ensure_urn_exam_eligibility(db: Session, *, user: User, urn: Urn) -> None:
    missing, total = _build_urn_exam_eligibility_detail(db, user=user, urn=urn)
    if total > 0 and missing:
        raise HTTPException(
            status_code=403,
            detail={
                "message": "Bạn cần hoàn thành tất cả họa tiết trước khi làm bài kiểm tra.",
                "missing_motifs": missing,
                "total_motifs": total,
                "mastered_motifs": total - len(missing),
            },
        )


def _select_urn_exam_questions(
    db: Session, *, urn: Urn, include_unpublished: bool = False
) -> list[QuizQuestion]:
    urn_query = select(QuizQuestion).where(
        QuizQuestion.urn_id == urn.id, QuizQuestion.is_active.is_(True)
    )
    if not include_unpublished:
        urn_query = urn_query.where(QuizQuestion.is_published.is_(True))

    urn_questions = (
        db.execute(
            urn_query.order_by(QuizQuestion.created_at.asc(), QuizQuestion.id.asc())
        )
        .scalars()
        .all()
    )
    if len(urn_questions) >= URN_EXAM_QUESTION_COUNT:
        return urn_questions[:URN_EXAM_QUESTION_COUNT]

    motif_query = (
        select(QuizQuestion)
        .join(Motif, QuizQuestion.motif_id == Motif.id)
        .where(
            Motif.urn_id == urn.id,
            QuizQuestion.is_active.is_(True),
            QuizQuestion.urn_id.is_(None),
        )
    )
    if not include_unpublished:
        motif_query = motif_query.where(QuizQuestion.is_published.is_(True))

    motif_questions = (
        db.execute(
            motif_query.order_by(QuizQuestion.created_at.asc(), QuizQuestion.id.asc())
        )
        .scalars()
        .all()
    )

    return (urn_questions + motif_questions)[:URN_EXAM_QUESTION_COUNT]


class UrnExamResponse(BaseModel):
    urn_id: UUID
    questions: list[QuizQuestionOut]
    attempts: int
    best_score: int
    pass_percent: int


@app.get("/api/v1/urns/{urn_slug}/exam", response_model=UrnExamResponse)
def get_urn_exam(
    urn_slug: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UrnExamResponse:
    urn = db.execute(select(Urn).where(Urn.slug == urn_slug)).scalar_one_or_none()
    if urn is None:
        raise HTTPException(status_code=404, detail="Urn not found")

    _ensure_urn_exam_eligibility(db, user=current_user, urn=urn)

    questions = _select_urn_exam_questions(
        db, urn=urn, include_unpublished=_can_view_drafts(current_user)
    )
    if not questions:
        raise HTTPException(status_code=404, detail="No exam questions found")

    attempts, best_score = db.execute(
        select(
            func.count(UrnExamAttempt.id).label("attempts"),
            func.coalesce(func.max(UrnExamAttempt.score), 0).label("best_score"),
        )
        .join(UrnExam, UrnExamAttempt.urn_exam_id == UrnExam.id)
        .where(UrnExamAttempt.user_id == current_user.id, UrnExam.urn_id == urn.id)
    ).one()

    return UrnExamResponse(
        urn_id=urn.id,
        questions=[
            QuizQuestionOut(
                id=q.id,
                question_type=q.question_type.value,
                question_text=q.question_text,
                options=q.options if isinstance(q.options, list) else None,
                target_mesh_name=q.target_mesh_name,
                difficulty=max(1, int(q.difficulty or 1)),
                image_url=None,
            )
            for q in questions
        ],
        attempts=int(attempts or 0),
        best_score=int(best_score or 0),
        pass_percent=URN_EXAM_PASS_PERCENT,
    )


class UrnExamSubmitRequest(BaseModel):
    answers: list[QuizAnswerIn]
    time_taken_seconds: Optional[int] = None


class UrnExamResultDetail(BaseModel):
    question_id: UUID
    correct: bool
    correct_answer: str
    user_answer: Optional[str] = None
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


class UrnExamSnapshotOut(BaseModel):
    pass_percent: int
    questions: list[QuizQuestionOut]


class UrnExamAttemptResultOut(BaseModel):
    score: int
    max_score: int
    percentage: int
    passed: bool
    results: list[UrnExamResultDetail]
    certificate: Optional[CertificateSummaryOut] = None


class UrnExamAttemptPayloadOut(BaseModel):
    urn: UrnOut
    exam: UrnExamSnapshotOut
    answers: dict[str, str]
    time_taken_seconds: Optional[int] = None
    submitted_at: datetime
    result: UrnExamAttemptResultOut


@app.post("/api/v1/urns/{urn_slug}/exam/submit", response_model=UrnExamSubmitResponse)
def submit_urn_exam(
    urn_slug: str,
    payload: UrnExamSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UrnExamSubmitResponse:
    urn = db.execute(select(Urn).where(Urn.slug == urn_slug)).scalar_one_or_none()
    if urn is None:
        raise HTTPException(status_code=404, detail="Urn not found")

    _ensure_urn_exam_eligibility(db, user=current_user, urn=urn)

    questions = _select_urn_exam_questions(
        db, urn=urn, include_unpublished=_can_view_drafts(current_user)
    )
    if not questions:
        raise HTTPException(status_code=404, detail="No exam questions found")

    answer_map: dict[UUID, str] = {}
    for ans in payload.answers:
        if ans.question_id in answer_map:
            raise HTTPException(
                status_code=400, detail="Duplicate answer for a question"
            )
        answer_map[ans.question_id] = ans.answer

    question_ids = {q.id for q in questions}
    if set(answer_map.keys()) != question_ids:
        raise HTTPException(
            status_code=400,
            detail="Answers must include all exam questions for this urn",
        )

    score = 0
    max_score = len(questions)
    results: list[UrnExamResultDetail] = []

    for q in questions:
        submitted = (answer_map.get(q.id) or "").strip()
        expected = (q.correct_answer or "").strip()
        is_correct = submitted == expected
        if is_correct:
            score += 1

        results.append(
            UrnExamResultDetail(
                question_id=q.id,
                correct=is_correct,
                correct_answer=expected,
                user_answer=submitted,
                explanation=(q.explanation or "").strip() or None,
            )
        )

    percentage = int(round((score / max_score) * 100)) if max_score > 0 else 0
    passed = percentage >= URN_EXAM_PASS_PERCENT

    total_xp_before = current_user.total_xp
    now = datetime.now(timezone.utc)
    certificate: Optional[Certificate] = None

    if passed:
        # Get urn_exam record
        urn_exam = db.execute(
            select(UrnExam).where(UrnExam.urn_id == urn.id)
        ).scalar_one_or_none()
        if not urn_exam:
            raise HTTPException(status_code=404, detail="Urn exam not found")

        passed_before = db.execute(
            select(func.count(UrnExamAttempt.id))
            .join(UrnExam, UrnExamAttempt.urn_exam_id == UrnExam.id)
            .where(
                UrnExamAttempt.user_id == current_user.id,
                UrnExam.urn_id == urn.id,
                UrnExamAttempt.passed.is_(True),
            )
        ).scalar_one()
        if int(passed_before or 0) == 0:
            current_user.total_xp += URN_EXAM_PASS_XP
        certificate = _issue_certificate(
            db,
            user_id=current_user.id,
            reason_type="urn_exam",
            reason_id=urn.id,
        )

    badge_bonus = 0
    _update_streak(current_user, now)
    if current_user.current_streak >= 7:
        badge_bonus += _award_badge(db, user=current_user, badge_slug=BADGE_STREAK_7)
    current_user.last_active_at = now

    # Get urn_exam record for attempt
    urn_exam = db.execute(
        select(UrnExam).where(UrnExam.urn_id == urn.id)
    ).scalar_one_or_none()
    if not urn_exam:
        raise HTTPException(status_code=404, detail="Urn exam not found")

    db.add(
        UrnExamAttempt(
            user_id=current_user.id,
            urn_exam_id=urn_exam.id,
            score=percentage,
            passed=passed,
            time_taken=payload.time_taken_seconds,
            answers=[
                {"question_id": str(k), "answer": v} for k, v in answer_map.items()
            ],
        )
    )

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to submit exam")

    return UrnExamSubmitResponse(
        urn_id=urn.id,
        score=score,
        max_score=max_score,
        percentage=percentage,
        passed=passed,
        xp_awarded=(current_user.total_xp - total_xp_before),
        total_xp=current_user.total_xp,
        results=results,
        certificate=CertificateSummaryOut(
            code=certificate.code,
            issuer_name=certificate.issuer_name,
            issued_at=certificate.issued_at,
        )
        if certificate
        else None,
    )


class UrnExamAttemptOut(BaseModel):
    id: UUID
    urn_id: UUID
    urn_slug: str
    urn_name: str
    score: int
    passed: bool
    created_at: datetime


class CertificateVerifyOut(BaseModel):
    code: str
    issuer_name: str
    status: str
    issued_at: datetime
    user_id: UUID
    display_name: str
    reason_type: str
    reason_id: UUID


@app.get("/api/v1/users/me/exam-attempts", response_model=list[UrnExamAttemptOut])
def get_my_exam_attempts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[UrnExamAttemptOut]:
    rows = db.execute(
        select(UrnExamAttempt, UrnExam, Urn)
        .join(UrnExam, UrnExamAttempt.urn_exam_id == UrnExam.id)
        .join(Urn, UrnExam.urn_id == Urn.id)
        .where(UrnExamAttempt.user_id == current_user.id)
        .order_by(UrnExamAttempt.created_at.desc())
    ).all()

    return [
        UrnExamAttemptOut(
            id=attempt.id,
            urn_id=urn.id,
            urn_slug=urn.slug,
            urn_name=urn.name,
            score=attempt.score,
            passed=attempt.passed,
            created_at=attempt.created_at,
        )
        for attempt, exam, urn in rows
    ]


@app.get(
    "/api/v1/urns/{urn_slug}/exam/attempts/latest",
    response_model=Optional[UrnExamAttemptPayloadOut],
)
def get_latest_urn_exam_attempt(
    urn_slug: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Optional[UrnExamAttemptPayloadOut]:
    urn = db.execute(select(Urn).where(Urn.slug == urn_slug)).scalar_one_or_none()
    if urn is None:
        raise HTTPException(status_code=404, detail="Urn not found")

    attempt = (
        db.execute(
            select(UrnExamAttempt)
            .join(UrnExam, UrnExamAttempt.urn_exam_id == UrnExam.id)
            .where(UrnExamAttempt.user_id == current_user.id, UrnExam.urn_id == urn.id)
            .order_by(UrnExamAttempt.created_at.desc())
        )
        .scalars()
        .first()
    )
    if attempt is None:
        return None

    answers_map: dict[str, str] = {}
    question_ids: list[str] = []
    if isinstance(attempt.answers, list):
        for entry in attempt.answers:
            if not isinstance(entry, dict):
                continue
            question_id = (
                entry.get("question_id") or entry.get("questionId") or entry.get("id")
            )
            if not question_id:
                continue
            question_id_str = str(question_id)
            if question_id_str in answers_map:
                continue
            answers_map[question_id_str] = str(entry.get("answer") or "")
            question_ids.append(question_id_str)
    elif isinstance(attempt.answers, dict):
        for question_id, answer in attempt.answers.items():
            question_id_str = str(question_id)
            if question_id_str in answers_map:
                continue
            answers_map[question_id_str] = str(answer or "")
            question_ids.append(question_id_str)

    questions: list[QuizQuestion] = []
    if question_ids:
        question_rows = (
            db.execute(select(QuizQuestion).where(QuizQuestion.id.in_(question_ids)))
            .scalars()
            .all()
        )
        question_by_id = {str(q.id): q for q in question_rows}
        questions = [
            question_by_id[qid] for qid in question_ids if qid in question_by_id
        ]

    results: list[UrnExamResultDetail] = []
    score = 0
    for q in questions:
        submitted = (answers_map.get(str(q.id)) or "").strip()
        expected = (q.correct_answer or "").strip()
        is_correct = submitted == expected
        if is_correct:
            score += 1
        results.append(
            UrnExamResultDetail(
                question_id=q.id,
                correct=is_correct,
                correct_answer=expected,
                user_answer=submitted or None,
                explanation=(q.explanation or "").strip() or None,
            )
        )

    max_score = len(questions)
    percentage = int(round((score / max_score) * 100)) if max_score > 0 else 0

    certificate = db.execute(
        select(Certificate).where(
            Certificate.user_id == current_user.id,
            Certificate.reason_type == "urn_exam",
            Certificate.reason_id == urn.id,
        )
    ).scalar_one_or_none()

    return UrnExamAttemptPayloadOut(
        urn=UrnOut.model_validate(urn),
        exam=UrnExamSnapshotOut(
            pass_percent=URN_EXAM_PASS_PERCENT,
            questions=[
                QuizQuestionOut(
                    id=q.id,
                    question_type=q.question_type.value,
                    question_text=q.question_text,
                    options=q.options if isinstance(q.options, list) else None,
                    target_mesh_name=q.target_mesh_name,
                    difficulty=max(1, int(q.difficulty or 1)),
                    image_url=None,
                )
                for q in questions
            ],
        ),
        answers=answers_map,
        time_taken_seconds=attempt.time_taken,
        submitted_at=attempt.created_at,
        result=UrnExamAttemptResultOut(
            score=score,
            max_score=max_score,
            percentage=percentage,
            passed=attempt.passed,
            results=results,
            certificate=(
                CertificateSummaryOut(
                    code=certificate.code,
                    issuer_name=certificate.issuer_name,
                    issued_at=certificate.issued_at,
                )
                if certificate is not None
                else None
            ),
        ),
    )


@app.get("/api/v1/certificates/{code}", response_model=CertificateVerifyOut)
def verify_certificate(
    code: str, db: Session = Depends(get_db)
) -> CertificateVerifyOut:
    row = db.execute(
        select(Certificate, User)
        .join(User, Certificate.user_id == User.id)
        .where(Certificate.code == code)
    ).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Certificate not found")

    certificate, user = row
    return CertificateVerifyOut(
        code=certificate.code,
        issuer_name=certificate.issuer_name,
        status=certificate.status,
        issued_at=certificate.issued_at,
        user_id=user.id,
        display_name=user.display_name,
        reason_type=certificate.reason_type,
        reason_id=certificate.reason_id,
    )


class CertificateOut(BaseModel):
    """Output schema for certificate details."""

    id: UUID
    code: str
    issuer_name: str
    status: str
    issued_at: datetime
    reason_type: str
    reason_id: UUID


@app.get("/api/v1/users/me/certificates", response_model=list[CertificateOut])
def get_my_certificates(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[CertificateOut]:
    """
    Get all certificates for the current user.
    """
    certificates = (
        db.execute(
            select(Certificate)
            .where(Certificate.user_id == current_user.id)
            .order_by(Certificate.issued_at.desc())
        )
        .scalars()
        .all()
    )

    return [
        CertificateOut(
            id=cert.id,
            code=cert.code,
            issuer_name=cert.issuer_name,
            status=cert.status,
            issued_at=cert.issued_at,
            reason_type=cert.reason_type,
            reason_id=cert.reason_id,
        )
        for cert in certificates
    ]


class RecommendationItemOut(BaseModel):
    kind: str
    title: str
    description: Optional[str] = None
    href: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


class RecommendationAIOut(BaseModel):
    provider: Optional[str] = None
    model: Optional[str] = None
    job_id: Optional[UUID] = None
    status: Optional[str] = None


class RecommendationOut(BaseModel):
    id: UUID
    source: str
    created_at: datetime
    items: list[RecommendationItemOut]
    ai: Optional[RecommendationAIOut] = None
    opted_out: bool = False


class RecommendationRefreshRequest(BaseModel):
    use_llm: Optional[bool] = False


class AIJobOut(BaseModel):
    id: UUID
    job_type: str
    status: str
    provider: Optional[str] = None
    retry_count: int
    created_at: datetime
    updated_at: datetime
    error: Optional[str] = None


class AIChatMessage(BaseModel):
    role: str = Field(pattern="^(user|assistant)$")
    content: str = Field(min_length=1)


class AIContextIn(BaseModel):
    urn_id: Optional[UUID] = None
    urn_slug: Optional[str] = None
    motif_id: Optional[UUID] = None
    lesson_id: Optional[UUID] = None
    quiz_question_id: Optional[UUID] = None


class AICitationOut(BaseModel):
    index: int
    source_type: str
    source_id: Optional[str] = None
    title: str
    snippet: Optional[str] = None


class AIAnswerOut(BaseModel):
    answer: str
    citations: list[AICitationOut] = Field(default_factory=list)
    job_id: Optional[UUID] = None


class AITutorRequest(BaseModel):
    message: str = Field(min_length=1)
    history: list[AIChatMessage] = Field(default_factory=list)
    context: Optional[AIContextIn] = None
    level: Optional[str] = None


class AIQuestionRequest(BaseModel):
    question: str = Field(min_length=1)
    context: Optional[AIContextIn] = None
    limit: int = Field(default=6, ge=1, le=12)


class LessonGenerateIn(BaseModel):
    motif_id: Optional[UUID] = None
    motif_mesh_name: Optional[str] = None
    motif_name: Optional[str] = None
    urn_slug: Optional[str] = None
    level: Optional[str] = "beginner"
    language: Optional[str] = "vi"
    force: bool = False
    use_seed: bool = True
    generate_quiz: bool = False
    quiz_count: int = Field(default=4, ge=1, le=20)


class LessonGenerateOut(BaseModel):
    motif_id: UUID
    lesson_id: UUID
    summary: str
    ai_job_id: Optional[UUID] = None
    used_seed: bool = False


class QuizGenerateIn(BaseModel):
    motif_id: Optional[UUID] = None
    motif_mesh_name: Optional[str] = None
    motif_name: Optional[str] = None
    urn_id: Optional[UUID] = None
    urn_slug: Optional[str] = None
    count: int = Field(default=5, ge=1, le=30)
    difficulty: int = Field(default=2, ge=1, le=5)
    replace_existing: bool = False
    use_seed: bool = True


class QuizGenerateOut(BaseModel):
    question_ids: list[UUID]
    ai_job_id: Optional[UUID] = None
    used_seed: bool = False


class SummaryGenerateIn(BaseModel):
    motif_id: Optional[UUID] = None
    urn_slug: Optional[str] = None
    level: Optional[str] = None


class SummaryGenerateOut(BaseModel):
    summary: str
    key_points: list[str] = Field(default_factory=list)
    job_id: Optional[UUID] = None


class FlashcardGenerateIn(BaseModel):
    topic: Optional[str] = None
    motif_id: Optional[UUID] = None
    count: int = Field(default=8, ge=2, le=30)
    level: Optional[str] = None


class FlashcardOut(BaseModel):
    front: str
    back: str


class FlashcardGenerateOut(BaseModel):
    cards: list[FlashcardOut]
    job_id: Optional[UUID] = None


class FeedbackGenerateIn(BaseModel):
    question: str = Field(min_length=1)
    correct_answer: str = Field(min_length=1)
    user_answer: str = Field(min_length=1)
    context: Optional[AIContextIn] = None


class FeedbackGenerateOut(BaseModel):
    is_correct: bool
    explanation: str
    next_step: Optional[str] = None
    job_id: Optional[UUID] = None


class CoachGenerateIn(BaseModel):
    goal: Optional[str] = None
    availability_minutes_per_day: Optional[int] = Field(default=15, ge=5, le=120)
    days_per_week: Optional[int] = Field(default=5, ge=2, le=7)


class CoachGenerateOut(BaseModel):
    message: str
    weekly_plan: list[str] = Field(default_factory=list)
    job_id: Optional[UUID] = None


class ExplainGenerateIn(BaseModel):
    text: str = Field(min_length=1)
    level: str = Field(pattern="^(child|teen|expert)$")


class ExplainGenerateOut(BaseModel):
    explanation: str
    job_id: Optional[UUID] = None


class ReviewPlanItem(BaseModel):
    motif_id: UUID
    motif_name: str
    due_in_days: int
    status: str


class ReviewPlanOut(BaseModel):
    items: list[ReviewPlanItem]


class DiagnosticGenerateIn(BaseModel):
    urn_id: Optional[UUID] = None
    urn_slug: Optional[str] = None
    count: int = Field(default=6, ge=2, le=20)
    level: Optional[str] = None


class DiagnosticQuestionOut(BaseModel):
    question_text: str
    options: list[str]
    correct_answer: str
    explanation: Optional[str] = None


class DiagnosticGenerateOut(BaseModel):
    questions: list[DiagnosticQuestionOut]
    job_id: Optional[UUID] = None


class SeedUrnIn(BaseModel):
    force: bool = False
    generate_quiz: bool = True
    quiz_count: int = Field(default=4, ge=1, le=20)
    use_seed: bool = True


class SeedUrnResult(BaseModel):
    motif_id: UUID
    status: str
    lesson_id: Optional[UUID] = None
    quiz_count: int = 0
    used_seed: bool = False


class SeedUrnOut(BaseModel):
    urn_id: UUID
    urn_slug: str
    total: int
    created: int
    skipped: int
    results: list[SeedUrnResult]


class ContentFlagCreateRequest(BaseModel):
    content_type: str
    content_id: UUID
    reason: str = Field(min_length=3, max_length=255)


class ContentFlagOut(BaseModel):
    id: UUID
    user_id: UUID
    content_type: str
    content_id: UUID
    reason: str
    created_at: datetime


def _normalize_recommendation_items(raw_items: Any) -> list[RecommendationItemOut]:
    if not isinstance(raw_items, list):
        return []
    items: list[RecommendationItemOut] = []
    for item in raw_items:
        if not isinstance(item, dict):
            continue
        items.append(
            RecommendationItemOut(
                kind=str(item.get("kind") or "note"),
                title=str(item.get("title") or "Gợi ý"),
                description=item.get("description"),
                href=item.get("href"),
                metadata=item.get("metadata")
                if isinstance(item.get("metadata"), dict)
                else None,
            )
        )
    return items


def _build_rules_recommendations(
    session: Session, *, user: User
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []

    weak_rows = session.execute(
        select(
            QuizAttempt.motif_id,
            func.max(QuizAttempt.percentage).label("best_score"),
        )
        .where(QuizAttempt.user_id == user.id)
        .group_by(QuizAttempt.motif_id)
        .having(func.max(QuizAttempt.percentage) < QUIZ_PASS_PERCENT)
    ).all()
    if weak_rows:
        motif_ids = [row.motif_id for row in weak_rows]
        motifs = (
            session.execute(select(Motif).where(Motif.id.in_(motif_ids)))
            .scalars()
            .all()
        )
        motif_map = {m.id: m for m in motifs}
        for row in weak_rows[:3]:
            motif = motif_map.get(row.motif_id)
            if motif is None:
                continue
            items.append(
                {
                    "kind": "remediation",
                    "title": f"Ôn tập: {motif.name}",
                    "description": f"Điểm quiz cao nhất {int(row.best_score)}%, thử lại để thành thạo.",
                    "href": f"/motif/{motif.id}/quiz",
                    "metadata": {"motif_id": str(motif.id)},
                }
            )

    progress_rows = session.execute(
        select(UserProgress, Motif)
        .join(Motif, UserProgress.motif_id == Motif.id)
        .where(
            UserProgress.user_id == user.id,
            UserProgress.status.in_([UnlockStatus.learned, UnlockStatus.discovered]),
            Motif.is_active.is_(True),
        )
    ).all()
    progress_list = [
        (progress, motif) for progress, motif in progress_rows if motif is not None
    ]
    status_priority = {UnlockStatus.learned: 0, UnlockStatus.discovered: 1}
    progress_list.sort(
        key=lambda row: (
            status_priority.get(row[0].status, 99),
            row[1].display_order or 0,
        )
    )
    for progress, motif in progress_list[:3]:
        items.append(
            {
                "kind": "motif",
                "title": motif.name,
                "description": "Hoàn thành bài học để mở khóa quiz."
                if progress.status == UnlockStatus.discovered
                else "Hoàn thành quiz để thành thạo.",
                "href": f"/motif/{motif.id}/quiz"
                if progress.status == UnlockStatus.learned
                else f"/motif/{motif.id}",
                "metadata": {
                    "motif_id": str(motif.id),
                    "status": progress.status.value,
                },
            }
        )

    quests = (
        session.execute(
            select(Quest)
            .options(selectinload(Quest.prerequisite))
            .where(Quest.is_active.is_(True))
            .order_by(Quest.display_order.asc(), Quest.created_at.asc())
        )
        .scalars()
        .all()
    )
    if quests:
        progress_entries = (
            session.execute(
                select(QuestProgress).where(
                    QuestProgress.user_id == user.id,
                    QuestProgress.quest_id.in_([q.id for q in quests]),
                )
            )
            .scalars()
            .all()
        )
        progress_by_quest = {p.quest_id: p for p in progress_entries}
        for quest in quests:
            if (
                progress_by_quest.get(quest.id, None)
                and progress_by_quest[quest.id].status == "completed"
            ):
                continue
            if quest.prerequisite_id and (
                progress_by_quest.get(quest.prerequisite_id) is None
                or progress_by_quest[quest.prerequisite_id].status != "completed"
            ):
                continue
            items.append(
                {
                    "kind": "quest",
                    "title": quest.name,
                    "description": quest.description or "Mở khóa hành trình tiếp theo.",
                    "href": f"/quests/{quest.slug}",
                    "metadata": {"quest_id": str(quest.id)},
                }
            )
            break

    if not items:
        items.append(
            {
                "kind": "note",
                "title": "Khám phá thêm họa tiết",
                "description": "Khám phá thêm họa tiết để mở khóa bài học và quest mới.",
                "href": "/explore",
            }
        )

    return items


def _deepseek_chat_url() -> str:
    base = settings.deepseek_base_url.rstrip("/")
    if base.endswith("/v1"):
        return f"{base}/chat/completions"
    return f"{base}/v1/chat/completions"


def _call_deepseek_chat(
    messages: Sequence[dict[str, str]],
    *,
    temperature: float = 0.2,
    response_format: Optional[dict[str, Any]] = None,
    model: Optional[str] = None,
) -> str:
    if not settings.deepseek_api_key:
        raise RuntimeError("Deepseek API key not configured")

    payload: dict[str, Any] = {
        "model": model or settings.deepseek_model,
        "messages": messages,
        "temperature": temperature,
    }
    if response_format is not None:
        payload["response_format"] = response_format

    data = json.dumps(payload).encode("utf-8")
    request = UrlRequest(
        _deepseek_chat_url(),
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.deepseek_api_key}",
        },
    )

    body = None
    max_retries = max(0, int(settings.deepseek_max_retries or 0))
    retryable_codes = {429, 500, 502, 503, 504}

    for attempt in range(max_retries + 1):
        try:
            with urlopen(
                request, timeout=settings.deepseek_timeout_seconds
            ) as response:
                body = response.read().decode("utf-8")
            break
        except HTTPError as exc:
            if attempt < max_retries and exc.code in retryable_codes:
                time.sleep(0.6 * (attempt + 1))
                continue
            raise RuntimeError(f"Deepseek request failed: {exc}") from exc
        except URLError as exc:
            if attempt < max_retries:
                time.sleep(0.6 * (attempt + 1))
                continue
            raise RuntimeError(f"Deepseek request failed: {exc}") from exc

    if body is None:
        raise RuntimeError("Deepseek response was empty")

    try:
        parsed = json.loads(body)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Deepseek response was not valid JSON") from exc

    content = (
        parsed.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
    )
    if not content:
        raise RuntimeError("Deepseek response was empty")
    return content


def _call_deepseek_chat_stream(
    messages: Sequence[dict[str, str]],
    *,
    temperature: float = 0.2,
    model: Optional[str] = None,
):
    """
    Stream responses from DeepSeek API using SSE.
    Yields chunks of text as they arrive.
    """
    if not settings.deepseek_api_key:
        raise RuntimeError("Deepseek API key not configured")

    payload: dict[str, Any] = {
        "model": model or settings.deepseek_model,
        "messages": messages,
        "temperature": temperature,
        "stream": True,
    }

    data = json.dumps(payload).encode("utf-8")
    request = UrlRequest(
        _deepseek_chat_url(),
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.deepseek_api_key}",
        },
    )

    try:
        with urlopen(request, timeout=settings.deepseek_timeout_seconds) as response:
            for line in response:
                line_str = line.decode("utf-8").strip()
                if not line_str or line_str == "data: [DONE]":
                    continue

                if line_str.startswith("data: "):
                    try:
                        chunk_data = json.loads(line_str[6:])
                        content_delta = (
                            chunk_data.get("choices", [{}])[0]
                            .get("delta", {})
                            .get("content", "")
                        )
                        if content_delta:
                            yield content_delta
                    except json.JSONDecodeError:
                        continue
    except (HTTPError, URLError) as exc:
        raise RuntimeError(f"Deepseek streaming request failed: {exc}") from exc


def _strip_accents(value: str) -> str:
    normalized = unicodedata.normalize("NFD", value)
    return "".join(
        char for char in normalized if unicodedata.category(char) != "Mn"
    ).lower()


def _load_seed_data(urn_slug: str) -> list[dict[str, Any]]:
    cached = _SEED_CACHE.get(urn_slug)
    if cached is not None:
        return cached

    filename = SEED_DATA_FILES.get(urn_slug)
    if not filename:
        _SEED_CACHE[urn_slug] = []
        return []

    path = SEED_DATA_DIR / filename
    if not path.exists():
        _SEED_CACHE[urn_slug] = []
        return []

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        _SEED_CACHE[urn_slug] = []
        return []

    items = [item for item in raw if isinstance(item, dict)]
    _SEED_CACHE[urn_slug] = items
    return items


def _find_seed_entry(urn_slug: str, motif_name: str) -> Optional[dict[str, Any]]:
    if not urn_slug or not motif_name:
        return None
    normalized = _strip_accents(motif_name)
    for item in _load_seed_data(urn_slug):
        candidate = item.get("name_vi") or item.get("name_en") or ""
        if _strip_accents(str(candidate)) == normalized:
            return item
    return None


def _slice_json_candidate(content: Optional[str]) -> Optional[str]:
    if not content:
        return None
    start_obj = content.find("{")
    start_arr = content.find("[")
    starts = [idx for idx in (start_obj, start_arr) if idx != -1]
    if not starts:
        return None
    start = min(starts)
    end_obj = content.rfind("}")
    end_arr = content.rfind("]")
    end = max(end_obj, end_arr)
    if end <= start:
        return None
    return content[start : end + 1]


def _extract_json_payload(content: str) -> Optional[str]:
    fence_match = re.search(r"```(?:json)?\\s*([\\s\\S]*?)```", content, re.IGNORECASE)
    if fence_match:
        fenced = fence_match.group(1).strip()
        candidate = _slice_json_candidate(fenced)
        return candidate or fenced
    return _slice_json_candidate(content)


def _safe_parse_json(content: str) -> Optional[Any]:
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        payload = _extract_json_payload(content)
        if not payload:
            return None
        try:
            parsed = json.loads(payload)
        except json.JSONDecodeError:
            return None


def _source_snippet(text: Optional[str], max_len: int = 280) -> Optional[str]:
    if not text:
        return None
    trimmed = " ".join(str(text).split())
    if len(trimmed) <= max_len:
        return trimmed
    return trimmed[: max_len - 1].rstrip() + "…"


def _clip_text(text: Optional[str], max_len: int = 1200) -> str:
    if not text:
        return ""
    trimmed = " ".join(str(text).split())
    if len(trimmed) <= max_len:
        return trimmed
    return trimmed[:max_len].rstrip()


def _get_rag_settings(session: Session) -> RagSettings:
    settings_row = (
        session.execute(select(RagSettings).order_by(RagSettings.created_at.desc()))
        .scalars()
        .first()
    )
    if settings_row:
        return settings_row
    settings_row = RagSettings()
    session.add(settings_row)
    session.commit()
    session.refresh(settings_row)
    return settings_row


def _apply_ai_settings(
    session: Session,
    *,
    system_prompt: str,
    user_prompt: str,
    temperature: float,
) -> tuple[str, str, Optional[str], float]:
    rag_settings = _get_rag_settings(session)
    system_content = system_prompt
    system_instruction = (rag_settings.system_instruction or "").strip()
    if system_instruction:
        system_content = f"{system_instruction}\n\n{system_prompt}"
    prompt_prefix = (rag_settings.prompt_prefix or "").strip()
    if prompt_prefix:
        user_prompt = f"{prompt_prefix}\n\n{user_prompt}"
    model_override = rag_settings.model_override or None
    temp_override = (
        float(rag_settings.temperature)
        if rag_settings.temperature is not None
        else temperature
    )
    return system_content, user_prompt, model_override, temp_override


def _cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    if not vec1 or not vec2 or len(vec1) != len(vec2):
        return 0.0

    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    magnitude1 = math.sqrt(sum(a * a for a in vec1))
    magnitude2 = math.sqrt(sum(b * b for b in vec2))

    if magnitude1 == 0.0 or magnitude2 == 0.0:
        return 0.0

    return dot_product / (magnitude1 * magnitude2)


def _keyword_score(text: str, query: str) -> float:
    """Calculate keyword matching score between text and query."""
    if not text or not query:
        return 0.0

    # Normalize text and query
    text_lower = text.lower()
    query_lower = query.lower()

    # Split into terms
    query_terms = query_lower.split()
    if not query_terms:
        return 0.0

    # Count term matches
    matches = 0
    for term in query_terms:
        if term in text_lower:
            matches += 1

    # Calculate score as ratio of matched terms
    return matches / len(query_terms)


def _score_rag_documents(
    rag_docs: Sequence[RagDocument],
    *,
    query: str,
    query_embedding: Optional[list[float]],
    alpha: float,
) -> list[RagDocument]:
    """
    Score and rank RAG documents using hybrid search.

    Args:
        rag_docs: List of RAG documents to score
        query: Search query text
        query_embedding: Query embedding vector
        alpha: Hybrid search weight (0.0 = pure keyword, 1.0 = pure semantic)

    Returns:
        List of documents sorted by score (highest first)
    """
    if not rag_docs:
        return []

    scored_docs: list[tuple[float, RagDocument]] = []

    for doc in rag_docs:
        # Calculate keyword score
        keyword_score = 0.0
        if query:
            # Score based on title and content
            title_score = _keyword_score(doc.title, query)
            content_score = _keyword_score(doc.content, query)
            # Weight title matches higher
            keyword_score = 0.7 * title_score + 0.3 * content_score

        # Calculate semantic score
        semantic_score = 0.0
        if query_embedding and doc.embedding:
            try:
                # doc.embedding is stored as JSONB, may need to convert
                doc_embedding = doc.embedding
                if isinstance(doc_embedding, list):
                    semantic_score = _cosine_similarity(query_embedding, doc_embedding)
            except (TypeError, ValueError):
                pass

        # Combine scores using alpha
        # alpha=0.0 means pure keyword, alpha=1.0 means pure semantic
        hybrid_score = (1.0 - alpha) * keyword_score + alpha * semantic_score

        scored_docs.append((hybrid_score, doc))

    # Sort by score descending
    scored_docs.sort(key=lambda x: x[0], reverse=True)

    # Return sorted documents
    return [doc for score, doc in scored_docs]


def _collect_ai_sources(
    session: Session,
    *,
    urn_slug: Optional[str] = None,
    motif_id: Optional[UUID] = None,
    limit: int = 6,
    query: Optional[str] = None,
) -> list[dict[str, Any]]:
    sources: list[dict[str, Any]] = []
    rag_settings = _get_rag_settings(session)

    if motif_id:
        motif = session.execute(
            select(Motif)
            .options(selectinload(Motif.lesson), selectinload(Motif.urn))
            .where(Motif.id == motif_id)
        ).scalar_one_or_none()
        if motif:
            motif_summary = None
            if motif.lesson and motif.lesson.description:
                motif_summary = motif.lesson.description
            if not motif_summary:
                motif_summary = (
                    f"Họa tiết {motif.name} thuộc nhóm {motif.category.value}."
                )
            sources.append(
                {
                    "type": "motif",
                    "id": str(motif.id),
                    "title": motif.name,
                    "content": motif_summary,
                }
            )
            if motif.lesson:
                lesson_text = " ".join(
                    chunk
                    for chunk in [
                        motif.lesson.description,
                        motif.lesson.historical_context,
                        motif.lesson.symbolism,
                        motif.lesson.fun_fact,
                    ]
                    if chunk
                )
                if lesson_text:
                    sources.append(
                        {
                            "type": "lesson",
                            "id": str(motif.lesson.id),
                            "title": f"Bài học: {motif.name}",
                            "content": lesson_text,
                        }
                    )
            if motif.urn:
                sources.append(
                    {
                        "type": "urn",
                        "id": str(motif.urn.id),
                        "title": motif.urn.name,
                        "content": motif.urn.description or "",
                    }
                )

    if urn_slug and not motif_id:
        urn = session.execute(
            select(Urn).where(Urn.slug == urn_slug)
        ).scalar_one_or_none()
        if urn:
            sources.append(
                {
                    "type": "urn",
                    "id": str(urn.id),
                    "title": urn.name,
                    "content": urn.description or "",
                }
            )
            motifs = (
                session.execute(
                    select(Motif)
                    .options(selectinload(Motif.lesson))
                    .where(Motif.urn_id == urn.id)
                    .order_by(Motif.display_order.asc())
                    .limit(limit)
                )
                .scalars()
                .all()
            )
            for motif in motifs:
                motif_summary = (
                    motif.lesson.description
                    if motif.lesson and motif.lesson.description
                    else f"Họa tiết {motif.name} thuộc nhóm {motif.category.value}."
                )
                sources.append(
                    {
                        "type": "motif",
                        "id": str(motif.id),
                        "title": motif.name,
                        "content": motif_summary,
                    }
                )
                if motif.lesson and motif.lesson.description:
                    sources.append(
                        {
                            "type": "lesson",
                            "id": str(motif.lesson.id),
                            "title": f"Bài học: {motif.name}",
                            "content": motif.lesson.description,
                        }
                    )

    max_docs = max(1, int(rag_settings.max_documents or 6))
    rag_docs = (
        session.execute(
            select(RagDocument)
            .where(RagDocument.is_active.is_(True))
            .order_by(RagDocument.updated_at.desc(), RagDocument.created_at.desc())
        )
        .scalars()
        .all()
    )

    if query and rag_settings.embedding_enabled and settings.embedding_api_key:
        query_embedding = _call_embedding(query)
        alpha = float(rag_settings.hybrid_alpha or 0.6)
        alpha = min(max(alpha, 0.0), 1.0)
        rag_docs = _score_rag_documents(
            rag_docs,
            query=query,
            query_embedding=query_embedding,
            alpha=alpha,
        )
    rag_docs = rag_docs[:max_docs]
    for doc in rag_docs:
        sources.append(
            {
                "type": "rag",
                "id": str(doc.id),
                "title": doc.title,
                "content": _clip_text(doc.content),
            }
        )

    if not sources:
        sources.append(
            {
                "type": "context",
                "id": "cuu-dinh",
                "title": "Cửu Đỉnh",
                "content": CUU_DINH_CONTEXT,
            }
        )

    return sources[:limit]


def _format_sources_for_prompt(sources: Iterable[dict[str, Any]]) -> str:
    lines: list[str] = []
    for idx, source in enumerate(sources, start=1):
        title = source.get("title") or "Nguồn"
        content = source.get("content") or ""
        lines.append(f"[S{idx}] {title}\n{content}")
    return "\n\n".join(lines)


def _extract_citations(answer: str) -> list[int]:
    citations = []
    for match in re.findall(r"\\[S(\\d+)\\]", answer):
        try:
            citations.append(int(match))
        except ValueError:
            continue
    return list(dict.fromkeys(citations))


def _build_ai_citations(
    sources: Sequence[dict[str, Any]], cited_indexes: Sequence[int]
) -> list[AICitationOut]:
    citations: list[AICitationOut] = []
    for idx, source in enumerate(sources, start=1):
        if cited_indexes and idx not in cited_indexes:
            continue
        citations.append(
            AICitationOut(
                index=idx,
                source_type=str(source.get("type") or "context"),
                source_id=source.get("id"),
                title=str(source.get("title") or "Nguồn"),
                snippet=_source_snippet(source.get("content")),
            )
        )
    return citations


def _fallback_answer_from_sources(
    question: str, sources: Sequence[dict[str, Any]]
) -> str:
    if not sources:
        return (
            "Mình chưa có đủ dữ liệu để trả lời ngay. "
            "Bạn thử lại sau hoặc bổ sung thêm bối cảnh nhé."
        )
    snippet = _source_snippet(sources[0].get("content"), max_len=360) or ""
    if snippet:
        return (
            f"Theo [S1], {snippet}\n\n"
            "Bạn có thể hỏi chi tiết hơn hoặc thử lại để nhận câu trả lời đầy đủ."
        )
    title = sources[0].get("title") or "Nguồn nội bộ"
    return (
        f"Mình đang ưu tiên nội dung từ [S1] {title}. "
        "Bạn thử lại sau để nhận câu trả lời chi tiết hơn nhé."
    )


def _fallback_summary_from_sources(sources: Sequence[dict[str, Any]]) -> str:
    if not sources:
        return "Chưa có dữ liệu để tóm tắt."
    return (
        _source_snippet(sources[0].get("content"), max_len=480)
        or "Chưa có dữ liệu để tóm tắt."
    )


def _fallback_flashcards_from_sources(
    sources: Sequence[dict[str, Any]],
    *,
    count: int,
    topic: Optional[str] = None,
) -> list[FlashcardOut]:
    cards: list[FlashcardOut] = []
    for source in sources:
        if len(cards) >= count:
            break
        title = str(source.get("title") or topic or "Cửu Đỉnh")
        snippet = _source_snippet(source.get("content"), max_len=160) or ""
        if not snippet:
            continue
        cards.append(FlashcardOut(front=title, back=snippet))
    if not cards:
        cards.append(
            FlashcardOut(
                front=topic or "Cửu Đỉnh",
                back="Gợi ý: thử chọn lại họa tiết hoặc thử lại để AI tạo flashcards.",
            )
        )
    return cards


def _fallback_explain_text(text: str) -> str:
    trimmed = " ".join(text.split())
    if not trimmed:
        return "Chưa có nội dung để giải thích."
    if len(trimmed) > 260:
        trimmed = trimmed[:260].rstrip() + "…"
    return f"Tóm tắt nhanh: {trimmed}"


def _start_ai_job(session: Session, *, user: User, job_type: str, prompt: str) -> AIJob:
    job = AIJob(
        user_id=user.id,
        job_type=job_type,
        status="pending",
        provider="deepseek",
        prompt=prompt,
    )
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


def _finish_ai_job(session: Session, job: AIJob, *, response: str) -> None:
    job.status = "succeeded"
    job.response = response
    session.commit()


def _fail_ai_job(session: Session, job: AIJob, *, error: str) -> None:
    job.status = "failed"
    job.error = error
    session.commit()


def _finish_ai_job_fallback(
    session: Session, job: AIJob, *, response: str, error: str
) -> None:
    """Finish an AI job with a fallback response due to an error.

    Marks the job as 'fallback' status with both the fallback response and error details.
    """
    job.status = "fallback"
    job.response = response
    job.error = error
    session.commit()


def _resolve_urn(
    session: Session,
    *,
    urn_id: Optional[UUID] = None,
    urn_slug: Optional[str] = None,
) -> Optional[Urn]:
    if urn_id:
        return session.execute(select(Urn).where(Urn.id == urn_id)).scalar_one_or_none()
    if urn_slug:
        return session.execute(
            select(Urn).where(Urn.slug == urn_slug)
        ).scalar_one_or_none()
    return None


def _resolve_motif(
    session: Session,
    *,
    motif_id: Optional[UUID] = None,
    mesh_name: Optional[str] = None,
    motif_name: Optional[str] = None,
) -> Optional[Motif]:
    if motif_id:
        return session.execute(
            select(Motif)
            .options(selectinload(Motif.lesson), selectinload(Motif.urn))
            .where(Motif.id == motif_id)
        ).scalar_one_or_none()
    if mesh_name:
        return session.execute(
            select(Motif)
            .options(selectinload(Motif.lesson), selectinload(Motif.urn))
            .where(Motif.mesh_name == mesh_name)
        ).scalar_one_or_none()
    if motif_name:
        return session.execute(
            select(Motif)
            .options(selectinload(Motif.lesson), selectinload(Motif.urn))
            .where(func.lower(Motif.name) == motif_name.lower())
        ).scalar_one_or_none()
    return None


def _lesson_payload_from_seed(seed: dict[str, Any]) -> dict[str, Optional[str]]:
    description_short = seed.get("description_short")
    description_educational = seed.get("description_educational") or description_short
    return {
        "intro_text": description_short,
        "description": description_educational or "",
        "historical_context": seed.get("historical_context"),
        "symbolism": seed.get("symbolism"),
        "fun_fact": seed.get("fun_fact"),
    }


def _quiz_payloads_from_seed(seed: dict[str, Any]) -> list[dict[str, Any]]:
    quiz_questions = seed.get("quiz_questions") or []
    payloads: list[dict[str, Any]] = []
    for quiz in quiz_questions:
        if not isinstance(quiz, dict):
            continue
        question_text = quiz.get("question")
        correct_answer = quiz.get("correct_answer")
        if not question_text or not correct_answer:
            continue
        options = quiz.get("options")
        if options is not None and not isinstance(options, list):
            continue
        payloads.append(
            {
                "question_type": quiz.get("type") or "multiple_choice",
                "question_text": question_text,
                "options": options,
                "correct_answer": correct_answer,
                "difficulty": quiz.get("difficulty") or 1,
                "explanation": quiz.get("explanation"),
            }
        )
    return payloads


def _sanitize_quiz_payload(payload: dict[str, Any]) -> Optional[dict[str, Any]]:
    question_text = str(payload.get("question_text") or "").strip()
    correct_answer = str(payload.get("correct_answer") or "").strip()
    question_type = str(payload.get("question_type") or "multiple_choice")
    if not question_text or not correct_answer:
        return None

    if question_type not in {
        QuestionType.multiple_choice.value,
        QuestionType.true_false.value,
        QuestionType.image_select.value,
        QuestionType.mesh_location.value,
    }:
        question_type = QuestionType.multiple_choice.value

    options = payload.get("options")
    if options is not None and not isinstance(options, list):
        options = None
    if isinstance(options, list):
        options = [str(item) for item in options]
        if correct_answer not in options and options:
            options[0] = correct_answer
    return {
        "question_type": question_type,
        "question_text": question_text,
        "options": options,
        "correct_answer": correct_answer,
        "difficulty": max(1, int(payload.get("difficulty") or 1)),
        "explanation": payload.get("explanation"),
        "target_mesh_name": payload.get("target_mesh_name"),
    }


def _generate_quiz_payloads_with_ai(
    session: Session,
    *,
    motif: Optional[Motif],
    urn: Optional[Urn],
    count: int,
    difficulty: int,
    level: Optional[str],
) -> tuple[list[dict[str, Any]], str]:
    topic = motif.name if motif else (urn.name if urn else "Cửu Đỉnh")
    context = CUU_DINH_CONTEXT
    if motif and motif.lesson and motif.lesson.description:
        context = f"{motif.lesson.description}\n\n{CUU_DINH_CONTEXT}"
    prompt = json.dumps(
        {
            "topic": topic,
            "difficulty": difficulty,
            "count": count,
            "level": level or "beginner",
            "context": context,
            "allowed_types": ["multiple_choice", "true_false"],
            "format": {
                "questions": [
                    {
                        "question_type": "multiple_choice|true_false",
                        "question_text": "string",
                        "options": ["string"],
                        "correct_answer": "string",
                        "difficulty": 1,
                        "explanation": "string",
                    }
                ]
            },
        },
        ensure_ascii=False,
    )

    system_prompt = (
        "Bạn tạo câu hỏi kiểm tra kiến thức bằng tiếng Việt, "
        "trả về JSON đúng cấu trúc được yêu cầu."
    )
    system_prompt, user_prompt, model_override, temperature = _apply_ai_settings(
        session,
        system_prompt=system_prompt,
        user_prompt=prompt,
        temperature=0.2,
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    response = _call_deepseek_chat(
        messages, temperature=temperature, model=model_override
    )
    parsed = _safe_parse_json(response)
    questions_raw: list[dict[str, Any]] = []
    if isinstance(parsed, dict):
        questions_raw = parsed.get("questions") or []
    elif isinstance(parsed, list):
        questions_raw = parsed

    payloads: list[dict[str, Any]] = []
    for item in questions_raw:
        if not isinstance(item, dict):
            continue
        sanitized = _sanitize_quiz_payload(item)
        if sanitized:
            payloads.append(sanitized)

    if not payloads:
        raise RuntimeError("AI quiz generation returned empty payloads")
    return payloads[:count], response


def _store_quiz_payloads(
    session: Session,
    *,
    motif: Motif,
    urn: Optional[Urn],
    payloads: Sequence[dict[str, Any]],
) -> list[QuizQuestion]:
    questions: list[QuizQuestion] = []
    for payload in payloads:
        question = QuizQuestion(
            motif_id=motif.id,
            urn_id=urn.id if urn else None,
            question_type=QuestionType(payload["question_type"]),
            question_text=payload["question_text"],
            options=payload.get("options"),
            correct_answer=payload["correct_answer"],
            target_mesh_name=payload.get("target_mesh_name"),
            difficulty=payload.get("difficulty") or 1,
            explanation=payload.get("explanation"),
        )
        session.add(question)
        questions.append(question)
    session.commit()
    return questions


def _generate_llm_recommendations(
    session: Session, *, user: User, rules_items: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], str]:
    prompt = json.dumps(
        {
            "user": {
                "total_xp": user.total_xp,
                "current_streak": user.current_streak,
                "starting_urn_id": str(user.starting_urn_id)
                if user.starting_urn_id
                else None,
            },
            "rules_recommendations": rules_items,
            "response_format": {
                "items": [
                    {
                        "kind": "motif|quest|remediation|note",
                        "title": "string",
                        "description": "string",
                        "href": "/motif/uuid",
                    }
                ]
            },
        },
        ensure_ascii=False,
    )

    system_prompt = "You generate concise learning recommendations in JSON."
    system_prompt, user_prompt, model_override, temperature = _apply_ai_settings(
        session,
        system_prompt=system_prompt,
        user_prompt=prompt,
        temperature=0.2,
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    content = _call_deepseek_chat(
        messages, temperature=temperature, model=model_override
    )
    items: list[dict[str, Any]] = []
    try:
        parsed = json.loads(content)
        if isinstance(parsed, dict):
            parsed_items = parsed.get("items") or parsed.get("recommendations")
        else:
            parsed_items = parsed
        if isinstance(parsed_items, list):
            items = [item for item in parsed_items if isinstance(item, dict)]
    except json.JSONDecodeError:
        items = []

    if not items:
        items = [
            {
                "kind": "ai_summary",
                "title": "Gợi ý từ AI",
                "description": content,
                "href": None,
            }
        ]

    return items, content


def _store_recommendation(
    session: Session, *, user: User, source: str, items: list[dict[str, Any]]
) -> Recommendation:
    recommendation = Recommendation(user_id=user.id, source=source, items=items)
    session.add(recommendation)
    session.flush()
    return recommendation


@app.get("/api/v1/users/me/recommendations", response_model=RecommendationOut)
def get_my_recommendations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RecommendationOut:
    recommendation = db.execute(
        select(Recommendation)
        .where(Recommendation.user_id == current_user.id)
        .order_by(Recommendation.created_at.desc())
    ).scalar_one_or_none()

    if recommendation is None:
        items = _build_rules_recommendations(db, user=current_user)
        recommendation = _store_recommendation(
            db, user=current_user, source="rules", items=items
        )
        db.commit()

    provenance = db.execute(
        select(ContentProvenance).where(
            ContentProvenance.content_type == "recommendation",
            ContentProvenance.content_id == recommendation.id,
        )
    ).scalar_one_or_none()

    return RecommendationOut(
        id=recommendation.id,
        source=recommendation.source,
        created_at=recommendation.created_at,
        items=_normalize_recommendation_items(recommendation.items),
        ai=(
            RecommendationAIOut(
                provider=provenance.provider if provenance else None,
                model=provenance.model if provenance else None,
            )
            if provenance
            else None
        ),
        opted_out=not current_user.ai_personalization_enabled,
    )


@app.post("/api/v1/users/me/recommendations/refresh", response_model=RecommendationOut)
def refresh_recommendations(
    payload: RecommendationRefreshRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RecommendationOut:
    rules_items = _build_rules_recommendations(db, user=current_user)

    if not current_user.ai_personalization_enabled:
        recommendation = _store_recommendation(
            db, user=current_user, source="rules", items=rules_items
        )
        db.commit()
        return RecommendationOut(
            id=recommendation.id,
            source=recommendation.source,
            created_at=recommendation.created_at,
            items=_normalize_recommendation_items(recommendation.items),
            opted_out=True,
        )

    if payload.use_llm:
        job = AIJob(
            user_id=current_user.id,
            job_type="recommendations",
            status="pending",
            provider="deepseek",
        )
        db.add(job)
        db.commit()
        db.refresh(job)

        try:
            llm_items, response_text = _generate_llm_recommendations(
                db, user=current_user, rules_items=rules_items
            )
            job.status = "succeeded"
            job.response = response_text
            db.commit()

            recommendation = _store_recommendation(
                db, user=current_user, source="llm", items=llm_items
            )
            rag_settings = _get_rag_settings(db)
            model_used = rag_settings.model_override or settings.deepseek_model
            provenance = ContentProvenance(
                content_type="recommendation",
                content_id=recommendation.id,
                provider="deepseek",
                model=model_used,
                generated_at=datetime.now(timezone.utc),
                metadata_payload={"job_id": str(job.id)},
            )
            db.add(provenance)
            db.commit()

            return RecommendationOut(
                id=recommendation.id,
                source=recommendation.source,
                created_at=recommendation.created_at,
                items=_normalize_recommendation_items(recommendation.items),
                ai=RecommendationAIOut(
                    provider=provenance.provider,
                    model=provenance.model,
                    job_id=job.id,
                    status=job.status,
                ),
                opted_out=False,
            )
        except Exception as exc:
            job.status = "failed"
            job.error = str(exc)
            db.commit()

    recommendation = _store_recommendation(
        db, user=current_user, source="rules", items=rules_items
    )
    db.commit()
    return RecommendationOut(
        id=recommendation.id,
        source=recommendation.source,
        created_at=recommendation.created_at,
        items=_normalize_recommendation_items(recommendation.items),
        opted_out=False,
    )


@app.get("/api/v1/users/me/ai-jobs", response_model=list[AIJobOut])
def list_ai_jobs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[AIJobOut]:
    jobs = (
        db.execute(
            select(AIJob)
            .where(AIJob.user_id == current_user.id)
            .order_by(AIJob.created_at.desc())
        )
        .scalars()
        .all()
    )
    return [
        AIJobOut(
            id=job.id,
            job_type=job.job_type,
            status=job.status,
            provider=job.provider,
            retry_count=int(job.retry_count or 0),
            created_at=job.created_at,
            updated_at=job.updated_at,
            error=job.error,
        )
        for job in jobs
    ]


@app.post("/api/v1/users/me/ai-jobs/{job_id}/retry", response_model=RecommendationOut)
def retry_ai_job(
    job_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RecommendationOut:
    job = db.execute(
        select(AIJob).where(AIJob.id == job_id, AIJob.user_id == current_user.id)
    ).scalar_one_or_none()
    if job is None:
        raise HTTPException(status_code=404, detail="AI job not found")
    if job.status != "failed":
        raise HTTPException(status_code=400, detail="AI job is not retryable")
    if not current_user.ai_personalization_enabled:
        raise HTTPException(status_code=400, detail="Personalization is disabled")

    job.status = "pending"
    job.retry_count = int(job.retry_count or 0) + 1
    db.commit()

    rules_items = _build_rules_recommendations(db, user=current_user)
    try:
        llm_items, response_text = _generate_llm_recommendations(
            db, user=current_user, rules_items=rules_items
        )
        job.status = "succeeded"
        job.response = response_text
        db.commit()

        recommendation = _store_recommendation(
            db, user=current_user, source="llm", items=llm_items
        )
        provenance = ContentProvenance(
            content_type="recommendation",
            content_id=recommendation.id,
            provider="deepseek",
            model=settings.deepseek_model,
            generated_at=datetime.now(timezone.utc),
            metadata_payload={"job_id": str(job.id)},
        )
        db.add(provenance)
        db.commit()

        return RecommendationOut(
            id=recommendation.id,
            source=recommendation.source,
            created_at=recommendation.created_at,
            items=_normalize_recommendation_items(recommendation.items),
            ai=RecommendationAIOut(
                provider=provenance.provider,
                model=provenance.model,
                job_id=job.id,
                status=job.status,
            ),
            opted_out=False,
        )
    except Exception as exc:
        job.status = "failed"
        job.error = str(exc)
        db.commit()
        raise HTTPException(status_code=502, detail="AI retry failed") from exc


# =============================================================================
# Content-Based Recommendations API
# =============================================================================


@app.get("/api/v1/recommendations", response_model=schemas.RecommendationsOut)
def get_recommendations(
    recommendation_type: Optional[str] = Query(
        None, pattern="^(continue_learning|discover_new|review_needed|popular)$"
    ),
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.RecommendationsOut:
    """
    Get personalized content recommendations.

    Returns different types of recommendations:
    - continue_learning: Lessons to continue
    - discover_new: New content based on interests
    - review_needed: Content needing review
    - popular: Trending content
    """
    from .services.recommendations import get_personalized_recommendations

    recommendations = get_personalized_recommendations(
        db, user=current_user, limit=limit, recommendation_type=recommendation_type
    )

    # Convert to schema format
    result = schemas.RecommendationsOut()

    for rec_type, items in recommendations.items():
        rec_items = [schemas.RecommendationContentOut(**item) for item in items]
        setattr(result, rec_type, rec_items)

    return result


@app.get(
    "/api/v1/recommendations/similar/{content_type}/{content_id}",
    response_model=schemas.SimilarContentOut,
)
def get_similar_content_endpoint(
    content_type: str,
    content_id: UUID,
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.SimilarContentOut:
    """
    Get similar content based on tags and collaborative filtering.

    Args:
        content_type: Type of content (lesson, motif, quest)
        content_id: ID of the content
        limit: Maximum number of recommendations
    """
    from .services.recommendations import get_similar_content

    if content_type not in ["lesson", "motif", "quest"]:
        raise HTTPException(
            status_code=400, detail="content_type must be one of: lesson, motif, quest"
        )

    similar_items = get_similar_content(
        db,
        content_type=content_type,
        content_id=content_id,
        user=current_user,
        limit=limit,
    )

    return schemas.SimilarContentOut(
        similar_content=[
            schemas.RecommendationContentOut(**item) for item in similar_items
        ],
        total=len(similar_items),
    )


@app.post(
    "/api/v1/recommendations/interaction", response_model=schemas.RecordInteractionOut
)
def record_content_interaction(
    payload: schemas.RecordInteractionIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.RecordInteractionOut:
    """
    Record a user content interaction for recommendation engine.

    This helps improve personalized recommendations by tracking:
    - Views: Content user has browsed
    - Completions: Content user has finished
    - Likes: Content user has favorited
    - Saves: Content user has bookmarked
    """
    from .models import InteractionType
    from .services.recommendations import record_interaction

    # Convert string to enum
    interaction_type_enum = InteractionType(payload.interaction_type)

    interaction = record_interaction(
        db=db,
        user=current_user,
        content_type=payload.content_type,
        content_id=payload.content_id,
        interaction_type=interaction_type_enum,
        duration_seconds=payload.duration_seconds,
        metadata=payload.metadata,
    )

    return schemas.RecordInteractionOut(
        success=True,
        message="Interaction recorded successfully",
        interaction_id=str(interaction.id),
    )


@app.post(
    "/api/v1/recommendations/feedback", response_model=schemas.RecommendationFeedbackOut
)
def submit_recommendation_feedback(
    payload: schemas.RecommendationFeedbackIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.RecommendationFeedbackOut:
    """
    Submit feedback on recommendations to improve future suggestions.

    Feedback types:
    - helpful: Recommendation was useful
    - not_helpful: Recommendation was not useful
    - irrelevant: Recommendation was not relevant
    - already_seen: User has already seen this content
    """
    from .models import InteractionType
    from .services.recommendations import record_interaction

    # Store feedback as metadata in interaction
    metadata = payload.metadata or {}
    metadata["feedback_type"] = payload.feedback_type

    # Record as a view interaction with feedback metadata
    record_interaction(
        db=db,
        user=current_user,
        content_type=payload.content_type,
        content_id=payload.content_id,
        interaction_type=InteractionType.view,
        metadata=metadata,
    )

    return schemas.RecommendationFeedbackOut(
        success=True, message="Feedback recorded successfully"
    )


@app.post("/api/v1/ai/tutor", response_model=AIAnswerOut)
def ai_tutor(
    payload: AITutorRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AIAnswerOut:
    if not settings.deepseek_api_key:
        raise HTTPException(status_code=503, detail="AI not configured")

    context = payload.context or AIContextIn()
    sources = _collect_ai_sources(
        db,
        urn_slug=context.urn_slug,
        motif_id=context.motif_id,
        limit=6,
        query=payload.message,
    )
    sources_prompt = _format_sources_for_prompt(sources)
    level = payload.level or "beginner"
    user_prompt = (
        f"Người học ở mức: {level}.\n"
        "Hãy trả lời ngắn gọn, dễ hiểu, có ví dụ thực tế nếu phù hợp.\n"
        "Trích dẫn nguồn bằng [S#] nếu sử dụng thông tin từ nguồn bên dưới.\n\n"
        f"Nguồn:\n{sources_prompt}\n\n"
        f"Câu hỏi: {payload.message}\nTrả lời:"
    )

    system_prompt = (
        "Bạn là trợ giảng lịch sử Việt Nam cho ứng dụng Cửu Đỉnh. "
        "Trả lời bằng tiếng Việt, rõ ràng, súc tích."
    )
    system_prompt, user_prompt, model_override, temperature = _apply_ai_settings(
        db,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0.3,
    )

    messages = [
        {
            "role": "system",
            "content": system_prompt,
        }
    ]
    for msg in payload.history[-6:]:
        messages.append({"role": msg.role, "content": msg.content})
    messages.append({"role": "user", "content": user_prompt})

    job = _start_ai_job(db, user=current_user, job_type="tutor", prompt=user_prompt)
    try:
        answer = _call_deepseek_chat(
            messages, temperature=temperature, model=model_override
        )
        _finish_ai_job(db, job, response=answer)
    except Exception as exc:
        answer = _fallback_answer_from_sources(payload.message, sources)
        _finish_ai_job_fallback(db, job, response=answer, error=str(exc))

    cited_indexes = _extract_citations(answer)
    citations = _build_ai_citations(sources, cited_indexes)
    if not citations:
        citations = _build_ai_citations(sources, [])
    return AIAnswerOut(answer=answer, citations=citations, job_id=job.id)


@app.post("/api/v1/ai/tutor/stream")
async def ai_tutor_stream(
    payload: AITutorRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Streaming version of AI tutor endpoint using Server-Sent Events (SSE).
    Returns text chunks as they arrive from DeepSeek API.
    """
    if not settings.deepseek_api_key:
        raise HTTPException(status_code=503, detail="AI not configured")

    context = payload.context or AIContextIn()
    sources = _collect_ai_sources(
        db,
        urn_slug=context.urn_slug,
        motif_id=context.motif_id,
        limit=6,
        query=payload.message,
    )
    sources_prompt = _format_sources_for_prompt(sources)
    level = payload.level or "beginner"
    user_prompt = (
        f"Người học ở mức: {level}.\n"
        "Hãy trả lời ngắn gọn, dễ hiểu, có ví dụ thực tế nếu phù hợp.\n"
        "Trích dẫn nguồn bằng [S#] nếu sử dụng thông tin từ nguồn bên dưới.\n\n"
        f"Nguồn:\n{sources_prompt}\n\n"
        f"Câu hỏi: {payload.message}\nTrả lời:"
    )

    system_prompt = (
        "Bạn là trợ giảng lịch sử Việt Nam cho ứng dụng Cửu Đỉnh. "
        "Trả lời bằng tiếng Việt, rõ ràng, súc tích."
    )
    system_prompt, user_prompt, model_override, temperature = _apply_ai_settings(
        db,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0.3,
    )

    messages = [
        {
            "role": "system",
            "content": system_prompt,
        }
    ]
    for msg in payload.history[-6:]:
        messages.append({"role": msg.role, "content": msg.content})
    messages.append({"role": "user", "content": user_prompt})

    job = _start_ai_job(
        db, user=current_user, job_type="tutor_stream", prompt=user_prompt
    )

    async def event_generator():
        accumulated_text = ""
        try:
            # Send initial metadata with citations
            cited_indexes = []
            initial_citations = _build_ai_citations(sources, cited_indexes)
            if not initial_citations:
                initial_citations = _build_ai_citations(sources, [])

            yield f"data: {json.dumps({'type': 'citations', 'citations': [c.dict() for c in initial_citations]})}\n\n"

            # Stream AI response chunks
            for chunk in _call_deepseek_chat_stream(
                messages, temperature=temperature, model=model_override
            ):
                accumulated_text += chunk
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"

            # Finalize job and send completion
            _finish_ai_job(db, job, response=accumulated_text)

            # Extract and send final citations
            cited_indexes = _extract_citations(accumulated_text)
            final_citations = _build_ai_citations(sources, cited_indexes)
            if not final_citations:
                final_citations = _build_ai_citations(sources, [])

            yield f"data: {json.dumps({'type': 'done', 'job_id': str(job.id), 'citations': [c.dict() for c in final_citations]})}\n\n"

        except Exception as exc:
            fallback = _fallback_answer_from_sources(payload.message, sources)
            _finish_ai_job_fallback(db, job, response=fallback, error=str(exc))
            yield f"data: {json.dumps({'type': 'error', 'message': fallback})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@app.post("/api/v1/ai/qa", response_model=AIAnswerOut)
def ai_qa(
    payload: AIQuestionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AIAnswerOut:
    if not settings.deepseek_api_key:
        raise HTTPException(status_code=503, detail="AI not configured")

    context = payload.context or AIContextIn()
    sources = _collect_ai_sources(
        db,
        urn_slug=context.urn_slug,
        motif_id=context.motif_id,
        limit=payload.limit,
        query=payload.question,
    )
    sources_prompt = _format_sources_for_prompt(sources)
    user_prompt = (
        "Chỉ trả lời dựa trên nguồn đã cung cấp. "
        "Nếu thiếu dữ kiện, hãy nói rõ cần thêm thông tin.\n"
        "Trích dẫn nguồn bằng [S#].\n\n"
        f"Nguồn:\n{sources_prompt}\n\n"
        f"Câu hỏi: {payload.question}\nTrả lời:"
    )

    system_prompt = (
        "Bạn là hệ thống hỏi đáp nội dung nội bộ về Cửu Đỉnh. "
        "Ưu tiên chính xác và trích dẫn nguồn."
    )
    system_prompt, user_prompt, model_override, temperature = _apply_ai_settings(
        db,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0.2,
    )
    messages = [
        {
            "role": "system",
            "content": system_prompt,
        },
        {"role": "user", "content": user_prompt},
    ]

    job = _start_ai_job(db, user=current_user, job_type="qa", prompt=user_prompt)
    try:
        answer = _call_deepseek_chat(
            messages, temperature=temperature, model=model_override
        )
        _finish_ai_job(db, job, response=answer)
    except Exception as exc:
        answer = _fallback_answer_from_sources(payload.question, sources)
        _finish_ai_job_fallback(db, job, response=answer, error=str(exc))

    cited_indexes = _extract_citations(answer)
    citations = _build_ai_citations(sources, cited_indexes)
    if not citations:
        citations = _build_ai_citations(sources, [])
    return AIAnswerOut(answer=answer, citations=citations, job_id=job.id)


@app.post("/api/v1/ai/summary", response_model=SummaryGenerateOut)
def ai_summary(
    payload: SummaryGenerateIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SummaryGenerateOut:
    sources = _collect_ai_sources(
        db, urn_slug=payload.urn_slug, motif_id=payload.motif_id, limit=6
    )
    sources_prompt = _format_sources_for_prompt(sources)
    if not settings.deepseek_api_key:
        return SummaryGenerateOut(
            summary=sources[0].get("content") or "", key_points=[]
        )

    user_prompt = (
        "Tóm tắt nội dung dưới đây bằng tiếng Việt.\n"
        "Trả về JSON với các khóa: summary, key_points (mảng).\n\n"
        f"Nguồn:\n{sources_prompt}"
    )
    system_prompt = "Bạn tóm tắt bài học lịch sử."
    system_prompt, user_prompt, model_override, temperature = _apply_ai_settings(
        db,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0.2,
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    job = _start_ai_job(db, user=current_user, job_type="summary", prompt=user_prompt)
    try:
        response = _call_deepseek_chat(
            messages, temperature=temperature, model=model_override
        )
        _finish_ai_job(db, job, response=response)
    except Exception as exc:
        summary = _fallback_summary_from_sources(sources)
        _finish_ai_job_fallback(db, job, response=summary, error=str(exc))
        return SummaryGenerateOut(summary=summary, key_points=[], job_id=job.id)

    parsed = _safe_parse_json(response)
    summary = response
    key_points: list[str] = []
    if isinstance(parsed, dict):
        summary = str(parsed.get("summary") or response)
        raw_points = parsed.get("key_points") or []
        if isinstance(raw_points, list):
            key_points = [str(item) for item in raw_points if item]
    return SummaryGenerateOut(summary=summary, key_points=key_points, job_id=job.id)


@app.post("/api/v1/ai/flashcards", response_model=FlashcardGenerateOut)
def ai_flashcards(
    payload: FlashcardGenerateIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FlashcardGenerateOut:
    if not settings.deepseek_api_key:
        raise HTTPException(status_code=503, detail="AI not configured")

    sources = _collect_ai_sources(db, motif_id=payload.motif_id, limit=4)
    topic = payload.topic or (sources[0].get("title") if sources else "Cửu Đỉnh")
    sources_prompt = _format_sources_for_prompt(sources)
    user_prompt = (
        f"Tạo {payload.count} thẻ ghi nhớ ngắn về chủ đề: {topic}.\n"
        "Trả về JSON với khóa cards: [{front, back}].\n\n"
        f"Nguồn:\n{sources_prompt}"
    )
    system_prompt = "Bạn tạo flashcards học tập."
    system_prompt, user_prompt, model_override, temperature = _apply_ai_settings(
        db,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0.3,
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    job = _start_ai_job(
        db, user=current_user, job_type="flashcards", prompt=user_prompt
    )
    try:
        response = _call_deepseek_chat(
            messages, temperature=temperature, model=model_override
        )
        _finish_ai_job(db, job, response=response)
    except Exception as exc:
        cards = _fallback_flashcards_from_sources(
            sources, count=payload.count, topic=topic
        )
        _finish_ai_job_fallback(
            db,
            job,
            response=json.dumps(
                [card.model_dump() for card in cards], ensure_ascii=False
            ),
            error=str(exc),
        )
        return FlashcardGenerateOut(cards=cards, job_id=job.id)

    parsed = _safe_parse_json(response)
    cards: list[FlashcardOut] = []
    if isinstance(parsed, dict):
        raw_cards = parsed.get("cards") or []
    else:
        raw_cards = parsed or []
    if isinstance(raw_cards, list):
        for card in raw_cards:
            if not isinstance(card, dict):
                continue
            front = str(card.get("front") or "").strip()
            back = str(card.get("back") or "").strip()
            if front and back:
                cards.append(FlashcardOut(front=front, back=back))
    if not cards:
        cards = [FlashcardOut(front=topic or "Flashcard", back=response)]
    return FlashcardGenerateOut(cards=cards, job_id=job.id)


@app.post("/api/v1/ai/feedback", response_model=FeedbackGenerateOut)
def ai_feedback(
    payload: FeedbackGenerateIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FeedbackGenerateOut:
    is_correct = payload.user_answer.strip() == payload.correct_answer.strip()
    if not settings.deepseek_api_key:
        return FeedbackGenerateOut(
            is_correct=is_correct,
            explanation="Câu trả lời đã được chấm tự động.",
            next_step=None,
        )

    context = payload.context or AIContextIn()
    sources = _collect_ai_sources(
        db,
        urn_slug=context.urn_slug,
        motif_id=context.motif_id,
        limit=4,
        query=payload.question,
    )
    sources_prompt = _format_sources_for_prompt(sources)
    user_prompt = json.dumps(
        {
            "question": payload.question,
            "correct_answer": payload.correct_answer,
            "user_answer": payload.user_answer,
            "is_correct": is_correct,
            "sources": sources_prompt,
            "format": {"explanation": "string", "next_step": "string"},
        },
        ensure_ascii=False,
    )
    system_prompt = "Bạn là trợ giảng phản hồi câu trả lời. Trả về JSON theo định dạng."
    system_prompt, user_prompt, model_override, temperature = _apply_ai_settings(
        db,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0.2,
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    job = _start_ai_job(db, user=current_user, job_type="feedback", prompt=user_prompt)
    try:
        response = _call_deepseek_chat(
            messages, temperature=temperature, model=model_override
        )
        _finish_ai_job(db, job, response=response)
    except Exception as exc:
        fallback = (
            "Câu trả lời đã được chấm tự động. "
            "Bạn có thể thử lại để nhận phản hồi chi tiết hơn."
        )
        _finish_ai_job_fallback(db, job, response=fallback, error=str(exc))
        return FeedbackGenerateOut(
            is_correct=is_correct,
            explanation=fallback,
            next_step="Ôn lại nội dung liên quan và thử lại câu hỏi.",
            job_id=job.id,
        )

    parsed = _safe_parse_json(response)
    explanation = response
    next_step = None
    if isinstance(parsed, dict):
        explanation = str(parsed.get("explanation") or response)
        next_step_value = parsed.get("next_step")
        if next_step_value:
            next_step = str(next_step_value)
    return FeedbackGenerateOut(
        is_correct=is_correct,
        explanation=explanation,
        next_step=next_step,
        job_id=job.id,
    )


@app.post("/api/v1/ai/coach", response_model=CoachGenerateOut)
def ai_coach(
    payload: CoachGenerateIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CoachGenerateOut:
    if not settings.deepseek_api_key:
        return CoachGenerateOut(
            message="Hãy duy trì thói quen học đều đặn mỗi ngày.",
            weekly_plan=[],
        )

    progress_counts = db.execute(
        select(UserProgress.status, func.count(UserProgress.id))
        .where(UserProgress.user_id == current_user.id)
        .group_by(UserProgress.status)
    ).all()
    counts = {row.status.value: row[1] for row in progress_counts}
    user_prompt = json.dumps(
        {
            "goal": payload.goal,
            "availability_minutes_per_day": payload.availability_minutes_per_day,
            "days_per_week": payload.days_per_week,
            "stats": {
                "total_xp": current_user.total_xp,
                "current_streak": current_user.current_streak,
                "progress": counts,
            },
            "format": {"message": "string", "weekly_plan": ["string"]},
        },
        ensure_ascii=False,
    )
    system_prompt = (
        "Bạn là coach học tập cho nội dung Cửu Đỉnh. Trả về JSON theo định dạng."
    )
    system_prompt, user_prompt, model_override, temperature = _apply_ai_settings(
        db,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0.3,
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    job = _start_ai_job(db, user=current_user, job_type="coach", prompt=user_prompt)
    try:
        response = _call_deepseek_chat(
            messages, temperature=temperature, model=model_override
        )
        _finish_ai_job(db, job, response=response)
    except Exception as exc:
        fallback_message = "Hãy duy trì nhịp học đều đặn mỗi ngày."
        fallback_plan = [
            "Mỗi ngày hoàn thành 1 bài học ngắn.",
            "Làm 5 câu quiz để củng cố kiến thức.",
            "Ôn lại các họa tiết đã học vào cuối tuần.",
        ]
        _finish_ai_job_fallback(
            db,
            job,
            response=json.dumps(
                {"message": fallback_message, "weekly_plan": fallback_plan},
                ensure_ascii=False,
            ),
            error=str(exc),
        )
        return CoachGenerateOut(
            message=fallback_message,
            weekly_plan=fallback_plan,
            job_id=job.id,
        )

    parsed = _safe_parse_json(response)
    message = response
    weekly_plan: list[str] = []
    if isinstance(parsed, dict):
        message = str(parsed.get("message") or response)
        raw_plan = parsed.get("weekly_plan") or []
        if isinstance(raw_plan, list):
            weekly_plan = [str(item) for item in raw_plan if item]
    return CoachGenerateOut(message=message, weekly_plan=weekly_plan, job_id=job.id)


@app.post("/api/v1/ai/explain", response_model=ExplainGenerateOut)
def ai_explain(
    payload: ExplainGenerateIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ExplainGenerateOut:
    if not settings.deepseek_api_key:
        return ExplainGenerateOut(explanation=payload.text)

    user_prompt = json.dumps(
        {
            "text": payload.text,
            "level": payload.level,
            "format": {"explanation": "string"},
        },
        ensure_ascii=False,
    )
    system_prompt = "Bạn diễn giải nội dung theo mức độ người học."
    system_prompt, user_prompt, model_override, temperature = _apply_ai_settings(
        db,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0.3,
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    job = _start_ai_job(db, user=current_user, job_type="explain", prompt=user_prompt)
    try:
        response = _call_deepseek_chat(
            messages, temperature=temperature, model=model_override
        )
        _finish_ai_job(db, job, response=response)
    except Exception as exc:
        explanation = _fallback_explain_text(payload.text)
        _finish_ai_job_fallback(db, job, response=explanation, error=str(exc))
        return ExplainGenerateOut(explanation=explanation, job_id=job.id)

    parsed = _safe_parse_json(response)
    explanation = response
    if isinstance(parsed, dict):
        explanation = str(parsed.get("explanation") or response)
    return ExplainGenerateOut(explanation=explanation, job_id=job.id)


@app.get("/api/v1/ai/review-plan", response_model=ReviewPlanOut)
def ai_review_plan(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ReviewPlanOut:
    now = datetime.now(timezone.utc)
    progress_rows = db.execute(
        select(UserProgress, Motif)
        .join(Motif, Motif.id == UserProgress.motif_id)
        .where(UserProgress.user_id == current_user.id)
    ).all()

    items: list[ReviewPlanItem] = []
    for progress, motif in progress_rows:
        if progress.status == UnlockStatus.hidden:
            continue
        last_attempt = db.execute(
            select(
                func.max(QuizAttempt.created_at), func.max(QuizAttempt.percentage)
            ).where(
                QuizAttempt.user_id == current_user.id,
                QuizAttempt.motif_id == motif.id,
            )
        ).first()
        last_date = last_attempt[0] if last_attempt else None
        score = last_attempt[1] if last_attempt else None

        if last_date is None:
            last_date = (
                progress.mastered_at
                or progress.learned_at
                or progress.lesson_viewed_at
                or progress.discovered_at
                or progress.created_at
            )

        interval_days = 1
        if score is not None:
            if score >= 90:
                interval_days = 14
            elif score >= 80:
                interval_days = 7
            elif score >= 60:
                interval_days = 3
            else:
                interval_days = 1

        due_in_days = 0
        if last_date:
            due_date = last_date + timedelta(days=interval_days)
            due_in_days = max(0, (due_date - now).days)

        items.append(
            ReviewPlanItem(
                motif_id=motif.id,
                motif_name=motif.name,
                due_in_days=due_in_days,
                status=progress.status.value,
            )
        )

    items.sort(key=lambda item: item.due_in_days)
    return ReviewPlanOut(items=items)


@app.get("/api/v1/ai/insights", response_model=schemas.AILearningInsightsResponse)
async def get_learning_insights(
    language: str = Query("vi", description="Language code (vi, en)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.AILearningInsightsResponse:
    """
    Generate AI-powered learning insights for the current user.

    Analyzes the user's learning progress and provides:
    - Natural language summary of their journey
    - Key strengths
    - Areas for improvement
    - Personalized recommendations
    """
    from .services import ai_insights

    try:
        insights = await ai_insights.generate_learning_insights(
            db=db,
            user_id=current_user.id,
            language=language,
            call_deepseek_fn=_call_deepseek_chat if settings.deepseek_api_key else None,
        )

        return schemas.AILearningInsightsResponse(**insights)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating insights: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate insights")


@app.get(
    "/api/v1/ai/insights/{user_id}", response_model=schemas.AILearningInsightsResponse
)
async def get_learning_insights_for_user(
    user_id: UUID,
    language: str = Query("vi", description="Language code (vi, en)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.AILearningInsightsResponse:
    """
    Generate AI-powered learning insights for a specific user.

    This endpoint is restricted to:
    - Teachers viewing their students
    - Admins viewing any user
    - Users viewing their own insights
    """
    from .services import ai_insights

    # Object-level authorization (Req 20.1/20.2): the owner or an admin may
    # always view; a teacher may additionally view their own students. Anyone
    # else receives a generic 404 so the response never discloses whether the
    # user or their insights exist.
    is_teacher_of_student = False
    if current_user.id != user_id and current_user.role not in ADMIN_ROLES:
        from .services import classroom  # noqa: F401

        is_teacher_of_student = (
            db.execute(
                select(ClassMember)
                .join(Classroom, ClassMember.class_id == Classroom.id)
                .where(
                    and_(
                        Classroom.teacher_id == current_user.id,
                        ClassMember.user_id == user_id,
                        ClassMember.role == "learner",
                    )
                )
            ).first()
            is not None
        )

    if not is_teacher_of_student:
        _ensure_owner_or_404(user_id, current_user)

    try:
        insights = await ai_insights.generate_learning_insights(
            db=db,
            user_id=user_id,
            language=language,
            call_deepseek_fn=_call_deepseek_chat if settings.deepseek_api_key else None,
        )

        return schemas.AILearningInsightsResponse(**insights)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating insights for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate insights")


@app.post("/api/v1/ai/lessons/generate", response_model=LessonGenerateOut)
def ai_generate_lesson(
    payload: LessonGenerateIn,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> LessonGenerateOut:
    motif = _resolve_motif(
        db,
        motif_id=payload.motif_id,
        mesh_name=payload.motif_mesh_name,
        motif_name=payload.motif_name,
    )
    if motif is None:
        raise HTTPException(status_code=404, detail="Motif not found")

    if motif.lesson and not payload.force:
        summary = (
            _source_snippet(motif.lesson.description, 160) or motif.lesson.description
        )
        return LessonGenerateOut(
            motif_id=motif.id,
            lesson_id=motif.lesson.id,
            summary=summary,
            used_seed=False,
        )

    urn_slug = payload.urn_slug or (motif.urn.slug if motif.urn else None)
    seed_entry = _find_seed_entry(urn_slug, motif.name) if urn_slug else None
    used_seed = False
    job: Optional[AIJob] = None
    model_used: Optional[str] = None

    lesson_payload: dict[str, Optional[str]] = {}
    if payload.use_seed and seed_entry:
        lesson_payload = _lesson_payload_from_seed(seed_entry)
        used_seed = True
    else:
        if not settings.deepseek_api_key:
            raise HTTPException(status_code=503, detail="AI not configured")
        user_prompt = json.dumps(
            {
                "motif": {
                    "name": motif.name,
                    "category": motif.category.value,
                    "rarity": motif.rarity.value,
                },
                "urn": {
                    "name": motif.urn.name if motif.urn else None,
                    "slug": urn_slug,
                },
                "context": CUU_DINH_CONTEXT,
                "level": payload.level,
                "language": payload.language,
                "format": {
                    "intro_text": "string",
                    "description": "string",
                    "historical_context": "string",
                    "symbolism": "string",
                    "fun_fact": "string",
                },
            },
            ensure_ascii=False,
        )
        system_prompt = (
            "Bạn tạo nội dung bài học lịch sử về Cửu Đỉnh bằng tiếng Việt. "
            "Trả về JSON đúng định dạng."
        )
        system_prompt, user_prompt, model_override, temperature = _apply_ai_settings(
            db,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.3,
        )
        model_used = model_override or settings.deepseek_model
        messages = [
            {
                "role": "system",
                "content": system_prompt,
            },
            {"role": "user", "content": user_prompt},
        ]
        job = _start_ai_job(
            db, user=current_user, job_type="lesson_generate", prompt=user_prompt
        )
        try:
            response = _call_deepseek_chat(
                messages, temperature=temperature, model=model_override
            )
            _finish_ai_job(db, job, response=response)
        except Exception as exc:
            _fail_ai_job(db, job, error=str(exc))
            raise HTTPException(
                status_code=502, detail="AI lesson generation failed"
            ) from exc

        parsed = _safe_parse_json(response)
        if not isinstance(parsed, dict):
            raise HTTPException(status_code=502, detail="AI lesson generation invalid")
        lesson_payload = {
            "intro_text": parsed.get("intro_text"),
            "description": parsed.get("description"),
            "historical_context": parsed.get("historical_context"),
            "symbolism": parsed.get("symbolism"),
            "fun_fact": parsed.get("fun_fact"),
        }

    description = lesson_payload.get("description") or ""
    if not description:
        raise HTTPException(status_code=400, detail="Lesson description missing")

    lesson = motif.lesson or LessonContent(motif_id=motif.id, description=description)
    lesson.intro_text = lesson_payload.get("intro_text")
    lesson.description = description
    lesson.historical_context = lesson_payload.get("historical_context")
    lesson.symbolism = lesson_payload.get("symbolism")
    lesson.fun_fact = lesson_payload.get("fun_fact")
    lesson.is_ai_generated = True
    db.add(lesson)
    db.commit()
    db.refresh(lesson)

    provenance = ContentProvenance(
        content_type="lesson",
        content_id=lesson.id,
        provider="seed" if used_seed else "deepseek",
        model=model_used if not used_seed else None,
        generated_at=datetime.now(timezone.utc) if not used_seed else None,
        metadata_payload={
            "urn_slug": urn_slug,
            "motif_id": str(motif.id),
            "job_id": str(job.id) if job else None,
        },
    )
    db.add(provenance)
    db.commit()

    if payload.generate_quiz:
        quiz_payloads: list[dict[str, Any]] = []
        if used_seed and seed_entry:
            quiz_payloads = [
                sanitized
                for item in _quiz_payloads_from_seed(seed_entry)
                if (sanitized := _sanitize_quiz_payload(item))
            ]
        if not quiz_payloads and settings.deepseek_api_key:
            quiz_payloads, _ = _generate_quiz_payloads_with_ai(
                db,
                motif=motif,
                urn=motif.urn,
                count=payload.quiz_count,
                difficulty=2,
                level=payload.level,
            )
        if quiz_payloads:
            _store_quiz_payloads(db, motif=motif, urn=motif.urn, payloads=quiz_payloads)

    summary = _source_snippet(lesson.description, 160) or lesson.description
    return LessonGenerateOut(
        motif_id=motif.id,
        lesson_id=lesson.id,
        summary=summary,
        ai_job_id=job.id if job else None,
        used_seed=used_seed,
    )


@app.post("/api/v1/ai/quizzes/generate", response_model=QuizGenerateOut)
def ai_generate_quiz(
    payload: QuizGenerateIn,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> QuizGenerateOut:
    motif = _resolve_motif(
        db,
        motif_id=payload.motif_id,
        mesh_name=payload.motif_mesh_name,
        motif_name=payload.motif_name,
    )
    if motif is None:
        raise HTTPException(status_code=404, detail="Motif not found")
    urn = (
        _resolve_urn(db, urn_id=payload.urn_id, urn_slug=payload.urn_slug) or motif.urn
    )

    if payload.replace_existing:
        db.execute(delete(QuizQuestion).where(QuizQuestion.motif_id == motif.id))
        db.commit()

    used_seed = False
    seed_entry = (
        _find_seed_entry(urn.slug if urn else None, motif.name) if urn else None
    )
    quiz_payloads: list[dict[str, Any]] = []
    job: Optional[AIJob] = None

    if payload.use_seed and seed_entry:
        quiz_payloads = [
            sanitized
            for item in _quiz_payloads_from_seed(seed_entry)
            if (sanitized := _sanitize_quiz_payload(item))
        ]
        used_seed = bool(quiz_payloads)

    if not quiz_payloads:
        if not settings.deepseek_api_key:
            raise HTTPException(status_code=503, detail="AI not configured")
        job = _start_ai_job(
            db, user=current_user, job_type="quiz_generate", prompt="generate quiz"
        )
        try:
            quiz_payloads, response = _generate_quiz_payloads_with_ai(
                db,
                motif=motif,
                urn=urn,
                count=payload.count,
                difficulty=payload.difficulty,
                level=None,
            )
            _finish_ai_job(db, job, response=response)
        except Exception as exc:
            _fail_ai_job(db, job, error=str(exc))
            raise HTTPException(
                status_code=502, detail="AI quiz generation failed"
            ) from exc

    model_used = None
    if not used_seed:
        rag_settings = _get_rag_settings(db)
        model_used = rag_settings.model_override or settings.deepseek_model

    questions = _store_quiz_payloads(db, motif=motif, urn=urn, payloads=quiz_payloads)
    for question in questions:
        provenance = ContentProvenance(
            content_type="quiz_question",
            content_id=question.id,
            provider="seed" if used_seed else "deepseek",
            model=model_used if not used_seed else None,
            generated_at=datetime.now(timezone.utc) if not used_seed else None,
            metadata_payload={
                "motif_id": str(motif.id),
                "urn_id": str(urn.id) if urn else None,
                "job_id": str(job.id) if job else None,
            },
        )
        db.add(provenance)
    db.commit()

    return QuizGenerateOut(
        question_ids=[q.id for q in questions],
        ai_job_id=job.id if job else None,
        used_seed=used_seed,
    )


@app.post("/api/v1/ai/diagnostic", response_model=DiagnosticGenerateOut)
def ai_diagnostic(
    payload: DiagnosticGenerateIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DiagnosticGenerateOut:
    if not settings.deepseek_api_key:
        raise HTTPException(status_code=503, detail="AI not configured")

    urn = _resolve_urn(db, urn_id=payload.urn_id, urn_slug=payload.urn_slug)
    job = _start_ai_job(
        db, user=current_user, job_type="diagnostic", prompt="diagnostic quiz"
    )
    try:
        payloads, response = _generate_quiz_payloads_with_ai(
            db,
            motif=None,
            urn=urn,
            count=payload.count,
            difficulty=2,
            level=payload.level,
        )
        _finish_ai_job(db, job, response=response)
    except Exception as exc:
        _fail_ai_job(db, job, error=str(exc))
        raise HTTPException(status_code=502, detail="AI diagnostic failed") from exc

    questions = [
        DiagnosticQuestionOut(
            question_text=item["question_text"],
            options=item.get("options") or [],
            correct_answer=item["correct_answer"],
            explanation=item.get("explanation"),
        )
        for item in payloads
    ]
    return DiagnosticGenerateOut(questions=questions, job_id=job.id)


@app.post("/api/v1/admin/ai/urns/{urn_slug}/seed", response_model=SeedUrnOut)
def ai_seed_urn(
    urn_slug: str,
    payload: SeedUrnIn,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> SeedUrnOut:
    urn = _resolve_urn(db, urn_slug=urn_slug)
    if urn is None:
        raise HTTPException(status_code=404, detail="Urn not found")

    motifs = (
        db.execute(
            select(Motif)
            .options(selectinload(Motif.lesson))
            .where(Motif.urn_id == urn.id)
            .order_by(Motif.display_order.asc())
        )
        .scalars()
        .all()
    )

    results: list[SeedUrnResult] = []
    created = 0
    skipped = 0

    for motif in motifs:
        if motif.lesson and not payload.force:
            skipped += 1
            results.append(
                SeedUrnResult(
                    motif_id=motif.id,
                    status="skipped",
                    lesson_id=motif.lesson.id,
                )
            )
            continue

        seed_entry = (
            _find_seed_entry(urn_slug, motif.name) if payload.use_seed else None
        )
        used_seed = False
        lesson_payload: dict[str, Optional[str]] = {}
        if seed_entry:
            lesson_payload = _lesson_payload_from_seed(seed_entry)
            used_seed = True
        elif not settings.deepseek_api_key:
            skipped += 1
            results.append(SeedUrnResult(motif_id=motif.id, status="skipped"))
            continue
        else:
            prompt = json.dumps(
                {
                    "motif": {"name": motif.name},
                    "urn": {"name": urn.name},
                    "context": CUU_DINH_CONTEXT,
                    "format": {
                        "intro_text": "string",
                        "description": "string",
                        "historical_context": "string",
                        "symbolism": "string",
                        "fun_fact": "string",
                    },
                },
                ensure_ascii=False,
            )
            system_prompt = "Bạn tạo nội dung bài học lịch sử về Cửu Đỉnh."
            system_prompt, user_prompt, model_override, temperature = (
                _apply_ai_settings(
                    db,
                    system_prompt=system_prompt,
                    user_prompt=prompt,
                    temperature=0.3,
                )
            )
            messages = [
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {"role": "user", "content": user_prompt},
            ]
            try:
                response = _call_deepseek_chat(
                    messages, temperature=temperature, model=model_override
                )
            except Exception:
                response = ""
            parsed = _safe_parse_json(response) if response else None
            if isinstance(parsed, dict):
                lesson_payload = {
                    "intro_text": parsed.get("intro_text"),
                    "description": parsed.get("description"),
                    "historical_context": parsed.get("historical_context"),
                    "symbolism": parsed.get("symbolism"),
                    "fun_fact": parsed.get("fun_fact"),
                }

        description = lesson_payload.get("description") or ""
        if not description:
            skipped += 1
            results.append(SeedUrnResult(motif_id=motif.id, status="skipped"))
            continue

        lesson = motif.lesson or LessonContent(
            motif_id=motif.id, description=description
        )
        lesson.intro_text = lesson_payload.get("intro_text")
        lesson.description = description
        lesson.historical_context = lesson_payload.get("historical_context")
        lesson.symbolism = lesson_payload.get("symbolism")
        lesson.fun_fact = lesson_payload.get("fun_fact")
        lesson.is_ai_generated = True
        db.add(lesson)
        db.commit()
        db.refresh(lesson)

        provenance = ContentProvenance(
            content_type="lesson",
            content_id=lesson.id,
            provider="seed" if used_seed else "deepseek",
            model=(
                (_get_rag_settings(db).model_override or settings.deepseek_model)
                if not used_seed
                else None
            ),
            generated_at=datetime.now(timezone.utc) if not used_seed else None,
            metadata_payload={"urn_slug": urn.slug, "motif_id": str(motif.id)},
        )
        db.add(provenance)
        db.commit()

        if payload.generate_quiz:
            quiz_payloads = []
            if seed_entry:
                quiz_payloads = [
                    sanitized
                    for item in _quiz_payloads_from_seed(seed_entry)
                    if (sanitized := _sanitize_quiz_payload(item))
                ]
            if quiz_payloads:
                _store_quiz_payloads(db, motif=motif, urn=urn, payloads=quiz_payloads)

        created += 1
        results.append(
            SeedUrnResult(
                motif_id=motif.id,
                status="created",
                lesson_id=lesson.id,
                quiz_count=len(quiz_payloads) if payload.generate_quiz else 0,
                used_seed=used_seed,
            )
        )

    return SeedUrnOut(
        urn_id=urn.id,
        urn_slug=urn.slug,
        total=len(motifs),
        created=created,
        skipped=skipped,
        results=results,
    )


@app.post("/api/v1/content/flags", response_model=ContentFlagOut, status_code=201)
def create_content_flag(
    payload: ContentFlagCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ContentFlagOut:
    flag = ContentFlag(
        user_id=current_user.id,
        content_type=payload.content_type,
        content_id=payload.content_id,
        reason=payload.reason,
    )
    db.add(flag)
    db.commit()
    db.refresh(flag)
    return ContentFlagOut(
        id=flag.id,
        user_id=flag.user_id,
        content_type=flag.content_type,
        content_id=flag.content_id,
        reason=flag.reason,
        created_at=flag.created_at,
    )


@app.get("/api/v1/admin/content/flags", response_model=list[ContentFlagOut])
def list_content_flags(
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> list[ContentFlagOut]:
    flags = (
        db.execute(select(ContentFlag).order_by(ContentFlag.created_at.desc()))
        .scalars()
        .all()
    )
    return [
        ContentFlagOut(
            id=flag.id,
            user_id=flag.user_id,
            content_type=flag.content_type,
            content_id=flag.content_id,
            reason=flag.reason,
            created_at=flag.created_at,
        )
        for flag in flags
    ]


# ============================================================
# Content Versioning Endpoints
# ============================================================


def _create_content_snapshot(
    db: Session,
    content_type: str,
    content_id: UUID,
    version: int,
    editor_id: UUID,
    change_note: Optional[str] = None,
) -> None:
    """Create a snapshot of content for versioning."""
    # Get the content data based on type
    if content_type == "lesson":
        content = db.get(LessonContent, content_id)
        if content is None:
            return
        data = {
            "intro_text": content.intro_text,
            "description": content.description,
            "historical_context": content.historical_context,
            "symbolism": content.symbolism,
            "fun_fact": content.fun_fact,
            "audio_narration_url": content.audio_narration_url,
            "additional_images": content.additional_images,
            "video_url": content.video_url,
            "is_published": content.is_published,
            "is_ai_generated": content.is_ai_generated,
        }
    else:
        # Future: handle other content types (quiz, etc.)
        return

    snapshot = ContentVersion(
        content_type=content_type,
        content_id=content_id,
        version=version,
        data=data,
        editor_id=editor_id,
        change_note=change_note,
    )
    db.add(snapshot)


class ContentVersionListOut(BaseModel):
    id: UUID
    version: int
    editor_id: Optional[UUID] = None
    editor_name: Optional[str] = None
    change_note: Optional[str] = None
    created_at: datetime


class ContentVersionOut(BaseModel):
    id: UUID
    content_type: str
    content_id: UUID
    version: int
    data: dict
    editor_id: Optional[UUID] = None
    editor_name: Optional[str] = None
    change_note: Optional[str] = None
    created_at: datetime


class RevertContentIn(BaseModel):
    change_note: Optional[str] = None


@app.get(
    "/api/v1/admin/content/{content_type}/{content_id}/versions",
    response_model=list[ContentVersionListOut],
)
def list_content_versions(
    content_type: str,
    content_id: UUID,
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db),
) -> list[ContentVersionListOut]:
    """List all versions of a content item."""
    if content_type not in ["lesson", "quiz"]:
        raise HTTPException(status_code=400, detail="Invalid content type")

    versions = (
        db.execute(
            select(ContentVersion)
            .where(
                ContentVersion.content_type == content_type,
                ContentVersion.content_id == content_id,
            )
            .order_by(ContentVersion.version.desc())
        )
        .scalars()
        .all()
    )

    # Get editor names
    editor_ids = [v.editor_id for v in versions if v.editor_id]
    editors = {}
    if editor_ids:
        users = db.execute(select(User).where(User.id.in_(editor_ids))).scalars().all()
        editors = {u.id: u.display_name for u in users}

    return [
        ContentVersionListOut(
            id=v.id,
            version=v.version,
            editor_id=v.editor_id,
            editor_name=editors.get(v.editor_id) if v.editor_id else None,
            change_note=v.change_note,
            created_at=v.created_at,
        )
        for v in versions
    ]


@app.get(
    "/api/v1/admin/content/{content_type}/{content_id}/versions/{version}",
    response_model=ContentVersionOut,
)
def get_content_version(
    content_type: str,
    content_id: UUID,
    version: int,
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db),
) -> ContentVersionOut:
    """Get a specific version of a content item."""
    if content_type not in ["lesson", "quiz"]:
        raise HTTPException(status_code=400, detail="Invalid content type")

    content_version = db.execute(
        select(ContentVersion).where(
            ContentVersion.content_type == content_type,
            ContentVersion.content_id == content_id,
            ContentVersion.version == version,
        )
    ).scalar_one_or_none()

    if content_version is None:
        raise HTTPException(status_code=404, detail="Version not found")

    editor_name = None
    if content_version.editor_id:
        editor = db.get(User, content_version.editor_id)
        editor_name = editor.display_name if editor else None

    return ContentVersionOut(
        id=content_version.id,
        content_type=content_version.content_type,
        content_id=content_version.content_id,
        version=content_version.version,
        data=content_version.data,
        editor_id=content_version.editor_id,
        editor_name=editor_name,
        change_note=content_version.change_note,
        created_at=content_version.created_at,
    )


# =============================================================================
# Review Workflow Endpoints
# =============================================================================


@app.post(
    "/api/v1/admin/lessons/{lesson_id}/submit-review", response_model=AdminLessonOut
)
def submit_lesson_for_review(
    lesson_id: UUID,
    payload: schemas.SubmitForReviewIn,
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db),
) -> AdminLessonOut:
    """Submit a lesson for review (teachers and admins)."""
    lesson = db.get(LessonContent, lesson_id)
    if lesson is None:
        raise HTTPException(status_code=404, detail="Lesson not found")

    # Check current status
    current_status = lesson.status or ContentStatus.draft
    if current_status != ContentStatus.draft:
        raise HTTPException(
            status_code=400,
            detail=f"Can only submit draft lessons for review. Current status: {current_status.value}",
        )

    # Update status to review
    lesson.status = ContentStatus.review
    lesson.submitted_for_review_at = datetime.utcnow()
    lesson.last_editor_id = current_user.id

    db.commit()
    db.refresh(lesson)

    return AdminLessonOut(
        id=lesson.id,
        motif_id=lesson.motif_id,
        intro_text=lesson.intro_text,
        description=lesson.description,
        historical_context=lesson.historical_context,
        symbolism=lesson.symbolism,
        fun_fact=lesson.fun_fact,
        audio_narration_url=lesson.audio_narration_url,
        additional_images=lesson.additional_images,
        video_url=lesson.video_url,
        is_published=lesson.is_published,
        is_ai_generated=lesson.is_ai_generated,
        version=lesson.version,
        last_editor_id=lesson.last_editor_id,
        published_at=lesson.published_at,
        publish_note=lesson.publish_note,
        status=lesson.status.value if lesson.status else "draft",
        submitted_for_review_at=lesson.submitted_for_review_at,
        reviewed_by_id=lesson.reviewed_by_id,
        reviewed_at=lesson.reviewed_at,
        review_notes=lesson.review_notes,
        created_at=lesson.created_at,
        updated_at=lesson.updated_at,
    )


@app.post("/api/v1/admin/lessons/{lesson_id}/approve", response_model=AdminLessonOut)
def approve_lesson(
    lesson_id: UUID,
    payload: schemas.ApproveContentIn,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> AdminLessonOut:
    """Approve and publish a lesson (admins only)."""
    lesson = db.get(LessonContent, lesson_id)
    if lesson is None:
        raise HTTPException(status_code=404, detail="Lesson not found")

    # Check current status
    current_status = lesson.status or ContentStatus.draft
    if current_status not in (ContentStatus.review, ContentStatus.draft):
        raise HTTPException(
            status_code=400,
            detail=f"Can only approve lessons in review or draft status. Current status: {current_status.value}",
        )

    # Update status to published
    lesson.status = ContentStatus.published
    lesson.is_published = True
    lesson.reviewed_by_id = current_user.id
    lesson.reviewed_at = datetime.utcnow()
    lesson.published_at = datetime.utcnow()
    lesson.review_notes = payload.review_notes

    db.commit()
    db.refresh(lesson)

    return AdminLessonOut(
        id=lesson.id,
        motif_id=lesson.motif_id,
        intro_text=lesson.intro_text,
        description=lesson.description,
        historical_context=lesson.historical_context,
        symbolism=lesson.symbolism,
        fun_fact=lesson.fun_fact,
        audio_narration_url=lesson.audio_narration_url,
        additional_images=lesson.additional_images,
        video_url=lesson.video_url,
        is_published=lesson.is_published,
        is_ai_generated=lesson.is_ai_generated,
        version=lesson.version,
        last_editor_id=lesson.last_editor_id,
        published_at=lesson.published_at,
        publish_note=lesson.publish_note,
        status=lesson.status.value if lesson.status else "draft",
        submitted_for_review_at=lesson.submitted_for_review_at,
        reviewed_by_id=lesson.reviewed_by_id,
        reviewed_at=lesson.reviewed_at,
        review_notes=lesson.review_notes,
        created_at=lesson.created_at,
        updated_at=lesson.updated_at,
    )


@app.post("/api/v1/admin/lessons/{lesson_id}/reject", response_model=AdminLessonOut)
def reject_lesson(
    lesson_id: UUID,
    payload: schemas.RejectContentIn,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> AdminLessonOut:
    """Reject a lesson and send back to draft (admins only)."""
    lesson = db.get(LessonContent, lesson_id)
    if lesson is None:
        raise HTTPException(status_code=404, detail="Lesson not found")

    # Check current status
    current_status = lesson.status or ContentStatus.draft
    if current_status != ContentStatus.review:
        raise HTTPException(
            status_code=400,
            detail=f"Can only reject lessons in review status. Current status: {current_status.value}",
        )

    # Update status back to draft
    lesson.status = ContentStatus.draft
    lesson.reviewed_by_id = current_user.id
    lesson.reviewed_at = datetime.utcnow()
    lesson.review_notes = payload.review_notes

    db.commit()
    db.refresh(lesson)

    return AdminLessonOut(
        id=lesson.id,
        motif_id=lesson.motif_id,
        intro_text=lesson.intro_text,
        description=lesson.description,
        historical_context=lesson.historical_context,
        symbolism=lesson.symbolism,
        fun_fact=lesson.fun_fact,
        audio_narration_url=lesson.audio_narration_url,
        additional_images=lesson.additional_images,
        video_url=lesson.video_url,
        is_published=lesson.is_published,
        is_ai_generated=lesson.is_ai_generated,
        version=lesson.version,
        last_editor_id=lesson.last_editor_id,
        published_at=lesson.published_at,
        publish_note=lesson.publish_note,
        status=lesson.status.value if lesson.status else "draft",
        submitted_for_review_at=lesson.submitted_for_review_at,
        reviewed_by_id=lesson.reviewed_by_id,
        reviewed_at=lesson.reviewed_at,
        review_notes=lesson.review_notes,
        created_at=lesson.created_at,
        updated_at=lesson.updated_at,
    )


@app.post(
    "/api/v1/admin/quiz-questions/{question_id}/submit-review",
    response_model=AdminQuizQuestionOut,
)
def submit_quiz_question_for_review(
    question_id: UUID,
    payload: schemas.SubmitForReviewIn,
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db),
) -> AdminQuizQuestionOut:
    """Submit a quiz question for review (teachers and admins)."""
    question = db.get(QuizQuestion, question_id)
    if question is None:
        raise HTTPException(status_code=404, detail="Quiz question not found")

    # Check current status
    current_status = question.status or ContentStatus.draft
    if current_status != ContentStatus.draft:
        raise HTTPException(
            status_code=400,
            detail=f"Can only submit draft questions for review. Current status: {current_status.value}",
        )

    # Update status to review
    question.status = ContentStatus.review
    question.submitted_for_review_at = datetime.utcnow()

    db.commit()
    db.refresh(question)

    return AdminQuizQuestionOut(
        id=question.id,
        motif_id=question.motif_id,
        urn_id=question.urn_id,
        question_type=question.question_type.value,
        question_text=question.question_text,
        options=question.options,
        correct_answer=question.correct_answer,
        target_mesh_name=question.target_mesh_name,
        difficulty=int(question.difficulty or 1),
        explanation=question.explanation,
        is_published=question.is_published,
        is_active=question.is_active,
        status=question.status.value if question.status else "draft",
        submitted_for_review_at=question.submitted_for_review_at,
        reviewed_by_id=question.reviewed_by_id,
        reviewed_at=question.reviewed_at,
        review_notes=question.review_notes,
        created_by_id=question.created_by_id,
        created_at=question.created_at,
    )


@app.post(
    "/api/v1/admin/quiz-questions/{question_id}/approve",
    response_model=AdminQuizQuestionOut,
)
def approve_quiz_question(
    question_id: UUID,
    payload: schemas.ApproveContentIn,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> AdminQuizQuestionOut:
    """Approve and publish a quiz question (admins only)."""
    question = db.get(QuizQuestion, question_id)
    if question is None:
        raise HTTPException(status_code=404, detail="Quiz question not found")

    # Check current status
    current_status = question.status or ContentStatus.draft
    if current_status not in (ContentStatus.review, ContentStatus.draft):
        raise HTTPException(
            status_code=400,
            detail=f"Can only approve questions in review or draft status. Current status: {current_status.value}",
        )

    # Update status to published
    question.status = ContentStatus.published
    question.is_published = True
    question.reviewed_by_id = current_user.id
    question.reviewed_at = datetime.utcnow()
    question.review_notes = payload.review_notes

    db.commit()
    db.refresh(question)

    return AdminQuizQuestionOut(
        id=question.id,
        motif_id=question.motif_id,
        urn_id=question.urn_id,
        question_type=question.question_type.value,
        question_text=question.question_text,
        options=question.options,
        correct_answer=question.correct_answer,
        target_mesh_name=question.target_mesh_name,
        difficulty=int(question.difficulty or 1),
        explanation=question.explanation,
        is_published=question.is_published,
        is_active=question.is_active,
        status=question.status.value if question.status else "draft",
        submitted_for_review_at=question.submitted_for_review_at,
        reviewed_by_id=question.reviewed_by_id,
        reviewed_at=question.reviewed_at,
        review_notes=question.review_notes,
        created_by_id=question.created_by_id,
        created_at=question.created_at,
    )


@app.post(
    "/api/v1/admin/quiz-questions/{question_id}/reject",
    response_model=AdminQuizQuestionOut,
)
def reject_quiz_question(
    question_id: UUID,
    payload: schemas.RejectContentIn,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> AdminQuizQuestionOut:
    """Reject a quiz question and send back to draft (admins only)."""
    question = db.get(QuizQuestion, question_id)
    if question is None:
        raise HTTPException(status_code=404, detail="Quiz question not found")

    # Check current status
    current_status = question.status or ContentStatus.draft
    if current_status != ContentStatus.review:
        raise HTTPException(
            status_code=400,
            detail=f"Can only reject questions in review status. Current status: {current_status.value}",
        )

    # Update status back to draft
    question.status = ContentStatus.draft
    question.reviewed_by_id = current_user.id
    question.reviewed_at = datetime.utcnow()
    question.review_notes = payload.review_notes

    db.commit()
    db.refresh(question)

    return AdminQuizQuestionOut(
        id=question.id,
        motif_id=question.motif_id,
        urn_id=question.urn_id,
        question_type=question.question_type.value,
        question_text=question.question_text,
        options=question.options,
        correct_answer=question.correct_answer,
        target_mesh_name=question.target_mesh_name,
        difficulty=int(question.difficulty or 1),
        explanation=question.explanation,
        is_published=question.is_published,
        is_active=question.is_active,
        status=question.status.value if question.status else "draft",
        submitted_for_review_at=question.submitted_for_review_at,
        reviewed_by_id=question.reviewed_by_id,
        reviewed_at=question.reviewed_at,
        review_notes=question.review_notes,
        created_by_id=question.created_by_id,
        created_at=question.created_at,
    )


@app.get(
    "/api/v1/admin/content/pending-review", response_model=schemas.PendingReviewListOut
)
def get_pending_review_items(
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db),
) -> schemas.PendingReviewListOut:
    """Get all content items pending review (teachers can see their own, admins see all)."""

    # Get lessons in review status
    lesson_query = (
        select(LessonContent)
        .where(LessonContent.status == ContentStatus.review)
        .options(selectinload(LessonContent.motif))
    )

    lessons = (
        db.execute(lesson_query.order_by(LessonContent.submitted_for_review_at.desc()))
        .scalars()
        .all()
    )

    lesson_items = []
    for lesson in lessons:
        motif_name = lesson.motif.name if lesson.motif else "Unknown Motif"
        # Get submitter name
        submitter_name = None
        if lesson.last_editor_id:
            submitter = db.get(User, lesson.last_editor_id)
            submitter_name = submitter.display_name if submitter else None

        lesson_items.append(
            schemas.PendingReviewItemOut(
                id=lesson.id,
                content_type="lesson",
                title=f"Lesson: {motif_name}",
                motif_name=motif_name,
                submitted_by_id=lesson.last_editor_id,
                submitted_by_name=submitter_name,
                submitted_at=lesson.submitted_for_review_at,
                version=lesson.version,
            )
        )

    # Get quiz questions in review status
    question_query = (
        select(QuizQuestion)
        .where(QuizQuestion.status == ContentStatus.review)
        .options(selectinload(QuizQuestion.motif))
    )

    questions = (
        db.execute(question_query.order_by(QuizQuestion.submitted_for_review_at.desc()))
        .scalars()
        .all()
    )

    question_items = []
    for question in questions:
        motif_name = question.motif.name if question.motif else "Unknown Motif"
        # Get submitter name
        submitter_name = None
        if question.created_by_id:
            submitter = db.get(User, question.created_by_id)
            submitter_name = submitter.display_name if submitter else None

        # Preview of question text (first 60 chars)
        question_preview = (
            question.question_text[:60] + "..."
            if len(question.question_text) > 60
            else question.question_text
        )

        question_items.append(
            schemas.PendingReviewItemOut(
                id=question.id,
                content_type="quiz_question",
                title=question_preview,
                motif_name=motif_name,
                submitted_by_id=question.created_by_id,
                submitted_by_name=submitter_name,
                submitted_at=question.submitted_for_review_at,
                version=None,
            )
        )

    return schemas.PendingReviewListOut(
        lessons=lesson_items,
        quiz_questions=question_items,
        total_count=len(lesson_items) + len(question_items),
    )


@app.post(
    "/api/v1/admin/content/{content_type}/{content_id}/revert/{version}",
    status_code=200,
)
def revert_content_to_version(
    content_type: str,
    content_id: UUID,
    version: int,
    payload: RevertContentIn,
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db),
) -> dict:
    """Revert content to a specific version."""
    if content_type not in ["lesson", "quiz"]:
        raise HTTPException(status_code=400, detail="Invalid content type")

    # Get the version to revert to
    content_version = db.execute(
        select(ContentVersion).where(
            ContentVersion.content_type == content_type,
            ContentVersion.content_id == content_id,
            ContentVersion.version == version,
        )
    ).scalar_one_or_none()

    if content_version is None:
        raise HTTPException(status_code=404, detail="Version not found")

    # Get the current content
    if content_type == "lesson":
        content = db.get(LessonContent, content_id)
        if content is None:
            raise HTTPException(status_code=404, detail="Content not found")

        # Create a snapshot of current state before reverting
        _create_content_snapshot(
            db,
            content_type,
            content_id,
            content.version,
            current_user.id,
            f"Before revert to version {version}",
        )

        # Apply the version data to the content
        for field, value in content_version.data.items():
            if hasattr(content, field):
                setattr(content, field, value)

        # Increment version and update metadata
        content.version += 1
        content.last_editor_id = current_user.id

        # Create a new snapshot for the reverted state
        _create_content_snapshot(
            db,
            content_type,
            content_id,
            content.version,
            current_user.id,
            payload.change_note or f"Reverted to version {version}",
        )

        db.commit()
        db.refresh(content)

        return {
            "message": f"Content reverted to version {version}",
            "new_version": content.version,
        }
    else:
        # Future: handle other content types
        raise HTTPException(status_code=400, detail="Content type not yet supported")


# ============================================================
# Health & Public Endpoints
# ============================================================


class HealthResponse(BaseModel):
    status: str
    database: str
    version: str


@app.get("/health", response_model=HealthResponse)
def health_check(db: Session = Depends(get_db)) -> HealthResponse:
    """Health check endpoint for monitoring."""
    db_status = "ok"
    try:
        db.execute(select(1))
    except Exception:
        db_status = "error"

    return HealthResponse(
        status="ok" if db_status == "ok" else "degraded",
        database=db_status,
        version="0.1.0",
    )


class RankListItemOut(BaseModel):
    level: int
    name: str
    xp: int


@app.get("/api/v1/ranks", response_model=list[RankListItemOut])
def list_ranks(
    current_user: User = Depends(get_current_user),
) -> list[RankListItemOut]:
    """List all XP ranks."""
    return [
        RankListItemOut(level=r["level"], name=r["name"], xp=r["xp"]) for r in XP_RANKS
    ]


class BadgeListItemOut(BaseModel):
    id: UUID
    slug: str
    name: str
    name_en: Optional[str] = None
    description: Optional[str] = None
    icon_url: str
    category: str
    xp_bonus: int


@app.get("/api/v1/badges", response_model=list[BadgeListItemOut])
def list_badges(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[BadgeListItemOut]:
    """List all available badges."""
    badges = (
        db.execute(
            select(Badge).where(Badge.is_active.is_(True), Badge.is_secret.is_(False))
        )
        .scalars()
        .all()
    )
    return [
        BadgeListItemOut(
            id=badge.id,
            slug=badge.slug,
            name=badge.name,
            name_en=badge.name_en,
            description=badge.description,
            icon_url=badge.icon_url,
            category=badge.category.value,
            xp_bonus=int(badge.xp_bonus or 0),
        )
        for badge in badges
    ]


# ============================================================
# Daily Goal Endpoints
# ============================================================


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


def _resolve_daily_goal_level(payload: DailyGoalSettingsUpdateIn) -> str:
    if payload.goal_level:
        normalized = payload.goal_level.strip().upper()
        if normalized in DAILY_GOAL_LEVELS:
            return normalized
        raise HTTPException(
            status_code=422,
            detail=f"Invalid goal_level. Must be one of: {', '.join(DAILY_GOAL_LEVELS.keys())}",
        )

    if payload.xp_target is None:
        raise HTTPException(
            status_code=422,
            detail="Either goal_level or xp_target is required",
        )

    for level, xp in DAILY_GOAL_LEVELS.items():
        if xp == payload.xp_target:
            return level

    allowed_xp = ", ".join(str(xp) for xp in DAILY_GOAL_LEVELS.values())
    raise HTTPException(
        status_code=422,
        detail=f"Invalid xp_target. Must be one of: {allowed_xp}",
    )


def _load_daily_goal_settings(db: Session, user: User) -> DailyGoalSettingsOut:
    latest_event = (
        db.execute(
            select(AnalyticsEvent)
            .where(
                AnalyticsEvent.user_id == user.id,
                AnalyticsEvent.event_name == "daily_goal_settings_updated",
            )
            .order_by(AnalyticsEvent.created_at.desc())
        )
        .scalars()
        .first()
    )

    if latest_event is None:
        default_updated_at = (
            user.updated_at or user.created_at or datetime.now(timezone.utc)
        )
        return DailyGoalSettingsOut(
            goal_level=DAILY_GOAL_DEFAULT_LEVEL,
            xp_target=DAILY_GOAL_LEVELS[DAILY_GOAL_DEFAULT_LEVEL],
            updated_at=default_updated_at,
            source="default",
        )

    payload = latest_event.payload if isinstance(latest_event.payload, dict) else {}
    level = str(payload.get("goal_level") or DAILY_GOAL_DEFAULT_LEVEL).strip().upper()
    if level not in DAILY_GOAL_LEVELS:
        level = DAILY_GOAL_DEFAULT_LEVEL

    return DailyGoalSettingsOut(
        goal_level=level,
        xp_target=DAILY_GOAL_LEVELS[level],
        updated_at=latest_event.created_at,
        source="server",
    )


@app.get("/api/v1/daily-goal/settings", response_model=DailyGoalSettingsOut)
def get_daily_goal_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DailyGoalSettingsOut:
    """Get daily-goal settings for current user."""
    return _load_daily_goal_settings(db, current_user)


@app.put("/api/v1/daily-goal/settings", response_model=DailyGoalSettingsOut)
def update_daily_goal_settings(
    payload: DailyGoalSettingsUpdateIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DailyGoalSettingsOut:
    """Update daily-goal settings for current user."""
    goal_level = _resolve_daily_goal_level(payload)
    xp_target = DAILY_GOAL_LEVELS[goal_level]
    now = datetime.now(timezone.utc)

    from services.analytics import create_event_record

    event_data = create_event_record(
        user_id=current_user.id,
        event_name="daily_goal_settings_updated",
        payload={
            "goal_level": goal_level,
            "xp_target": xp_target,
            "updated_at": now.isoformat(),
        },
        path="/api/v1/daily-goal/settings",
    )

    db.add(AnalyticsEvent(**event_data))
    db.commit()

    return DailyGoalSettingsOut(
        goal_level=goal_level,
        xp_target=xp_target,
        updated_at=now,
        source="server",
    )


# ============================================================
# Daily Mission Endpoints
# ============================================================


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


def _ensure_daily_missions_for_user(
    db: Session, user_id: UUID, mission_date: datetime
) -> list[UserDailyMission]:
    """Ensure user has daily missions assigned for the given date."""
    from datetime import date as date_type

    # Convert mission_date to date (no time)
    if isinstance(mission_date, datetime):
        date_only = mission_date.date()
    else:
        date_only = mission_date

    # Get all active missions
    active_missions = (
        db.execute(
            select(DailyMission)
            .where(DailyMission.is_active.is_(True))
            .order_by(DailyMission.created_at)
        )
        .scalars()
        .all()
    )

    user_missions = []
    for mission in active_missions:
        # Check if user already has this mission for the date
        existing = db.execute(
            select(UserDailyMission).where(
                UserDailyMission.user_id == user_id,
                UserDailyMission.mission_id == mission.id,
                func.date(UserDailyMission.mission_date) == date_only,
            )
        ).scalar_one_or_none()

        if existing is None:
            # Create new user mission
            user_mission = UserDailyMission(
                user_id=user_id,
                mission_id=mission.id,
                mission_date=datetime.combine(date_only, datetime.min.time()),
                current_count=0,
                is_completed=False,
                xp_awarded=0,
            )
            db.add(user_mission)
            user_missions.append(user_mission)
        else:
            user_missions.append(existing)

    if user_missions:
        db.flush()

    return user_missions


@app.get("/api/v1/daily-missions", response_model=DailyMissionsResponse)
def get_daily_missions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DailyMissionsResponse:
    """Get today's daily missions with progress."""
    from datetime import date as date_type

    today = datetime.now(timezone.utc).date()

    # Ensure user has missions for today
    _ensure_daily_missions_for_user(db, current_user.id, datetime.now(timezone.utc))
    db.commit()

    # Fetch user's missions for today
    user_missions = (
        db.execute(
            select(UserDailyMission)
            .options(selectinload(UserDailyMission.mission))
            .where(
                UserDailyMission.user_id == current_user.id,
                func.date(UserDailyMission.mission_date) == today,
            )
            .order_by(UserDailyMission.mission_id)
        )
        .scalars()
        .all()
    )

    missions_out = []
    total_xp = 0
    completed_count = 0

    for um in user_missions:
        progress_pct = min(100, int((um.current_count / um.mission.target_count) * 100))
        missions_out.append(
            UserDailyMissionOut(
                id=um.id,
                mission=DailyMissionOut(
                    id=um.mission.id,
                    slug=um.mission.slug,
                    name=um.mission.name,
                    description=um.mission.description,
                    mission_type=um.mission.mission_type.value,
                    target_count=um.mission.target_count,
                    xp_reward=um.mission.xp_reward,
                    is_active=um.mission.is_active,
                ),
                mission_date=um.mission_date,
                current_count=um.current_count,
                is_completed=um.is_completed,
                completed_at=um.completed_at,
                xp_awarded=um.xp_awarded,
                progress_percentage=progress_pct,
            )
        )
        total_xp += um.xp_awarded
        if um.is_completed:
            completed_count += 1

    return DailyMissionsResponse(
        missions=missions_out,
        total_xp_today=total_xp,
        completed_count=completed_count,
        total_count=len(missions_out),
    )


@app.post(
    "/api/v1/daily-missions/{mission_id}/progress",
    response_model=UpdateMissionProgressResponse,
)
def update_mission_progress(
    mission_id: UUID,
    payload: UpdateMissionProgressRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UpdateMissionProgressResponse:
    """Update progress on a daily mission."""
    from datetime import date as date_type

    today = datetime.now(timezone.utc).date()

    # Find user's mission for today
    user_mission = db.execute(
        select(UserDailyMission)
        .options(selectinload(UserDailyMission.mission))
        .where(
            UserDailyMission.user_id == current_user.id,
            UserDailyMission.mission_id == mission_id,
            func.date(UserDailyMission.mission_date) == today,
        )
    ).scalar_one_or_none()

    if user_mission is None:
        raise HTTPException(status_code=404, detail="Mission not found for today")

    if user_mission.is_completed:
        # Already completed, return current state
        progress_pct = 100
        return UpdateMissionProgressResponse(
            mission=UserDailyMissionOut(
                id=user_mission.id,
                mission=DailyMissionOut(
                    id=user_mission.mission.id,
                    slug=user_mission.mission.slug,
                    name=user_mission.mission.name,
                    description=user_mission.mission.description,
                    mission_type=user_mission.mission.mission_type.value,
                    target_count=user_mission.mission.target_count,
                    xp_reward=user_mission.mission.xp_reward,
                    is_active=user_mission.mission.is_active,
                ),
                mission_date=user_mission.mission_date,
                current_count=user_mission.current_count,
                is_completed=user_mission.is_completed,
                completed_at=user_mission.completed_at,
                xp_awarded=user_mission.xp_awarded,
                progress_percentage=progress_pct,
            ),
            xp_gained=0,
            just_completed=False,
        )

    # Update progress
    user_mission.current_count = min(
        user_mission.current_count + payload.increment,
        user_mission.mission.target_count,
    )

    xp_gained = 0
    just_completed = False

    # Check if mission is now completed
    if (
        user_mission.current_count >= user_mission.mission.target_count
        and not user_mission.is_completed
    ):
        user_mission.is_completed = True
        user_mission.completed_at = datetime.now(timezone.utc)
        user_mission.xp_awarded = user_mission.mission.xp_reward
        xp_gained = user_mission.mission.xp_reward
        just_completed = True

        # Award XP to user
        current_user.total_xp += xp_gained

    db.commit()
    db.refresh(user_mission)

    progress_pct = min(
        100, int((user_mission.current_count / user_mission.mission.target_count) * 100)
    )

    return UpdateMissionProgressResponse(
        mission=UserDailyMissionOut(
            id=user_mission.id,
            mission=DailyMissionOut(
                id=user_mission.mission.id,
                slug=user_mission.mission.slug,
                name=user_mission.mission.name,
                description=user_mission.mission.description,
                mission_type=user_mission.mission.mission_type.value,
                target_count=user_mission.mission.target_count,
                xp_reward=user_mission.mission.xp_reward,
                is_active=user_mission.mission.is_active,
            ),
            mission_date=user_mission.mission_date,
            current_count=user_mission.current_count,
            is_completed=user_mission.is_completed,
            completed_at=user_mission.completed_at,
            xp_awarded=user_mission.xp_awarded,
            progress_percentage=progress_pct,
        ),
        xp_gained=xp_gained,
        just_completed=just_completed,
    )


@app.get("/api/v1/daily-missions/history", response_model=DailyMissionHistoryResponse)
def get_daily_mission_history(
    days: int = Query(default=30, ge=1, le=90),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DailyMissionHistoryResponse:
    """Get past mission history."""
    from datetime import date as date_type
    from datetime import timedelta

    end_date = datetime.now(timezone.utc).date()
    start_date = end_date - timedelta(days=days)

    # Fetch user's missions for the date range
    user_missions = (
        db.execute(
            select(UserDailyMission)
            .options(selectinload(UserDailyMission.mission))
            .where(
                UserDailyMission.user_id == current_user.id,
                func.date(UserDailyMission.mission_date) >= start_date,
                func.date(UserDailyMission.mission_date) <= end_date,
            )
            .order_by(UserDailyMission.mission_date.desc())
        )
        .scalars()
        .all()
    )

    history_items = []
    total_completed = 0
    total_xp = 0

    for um in user_missions:
        history_items.append(
            DailyMissionHistoryItem(
                mission_date=um.mission_date,
                mission_name=um.mission.name,
                mission_type=um.mission.mission_type.value,
                target_count=um.mission.target_count,
                current_count=um.current_count,
                is_completed=um.is_completed,
                completed_at=um.completed_at,
                xp_awarded=um.xp_awarded,
            )
        )
        if um.is_completed:
            total_completed += 1
            total_xp += um.xp_awarded

    # Calculate current mission streak
    streak = 0
    current_date = end_date
    while True:
        day_missions = [
            um
            for um in user_missions
            if isinstance(um.mission_date, datetime)
            and um.mission_date.date() == current_date
        ]
        if not day_missions:
            break

        # Check if all missions for the day are completed
        all_completed = all(um.is_completed for um in day_missions)
        if all_completed:
            streak += 1
            current_date -= timedelta(days=1)
        else:
            break

    return DailyMissionHistoryResponse(
        history=history_items,
        total_completed=total_completed,
        total_xp_earned=total_xp,
        current_streak=streak,
    )


# =============================================================================
# Streak Endpoints
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


@app.get("/api/v1/streak", response_model=StreakStatusOut)
def get_streak_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StreakStatusOut:
    """Get current streak status with milestones."""
    from .services.streak import (
        STREAK_MILESTONES,
        get_next_milestone,
        is_streak_at_risk,
        is_streak_maintained_today,
    )

    now = datetime.now(timezone.utc)

    # Check which milestones are completed
    milestones = []
    for day, rewards in STREAK_MILESTONES.items():
        # Check if milestone is completed
        existing = db.execute(
            select(StreakReward).where(
                StreakReward.user_id == current_user.id, StreakReward.streak_day == day
            )
        ).scalar_one_or_none()

        milestones.append(
            StreakMilestoneOut(
                day=day,
                xp_reward=rewards["xp"],
                badge_slug=rewards.get("badge_slug"),
                freeze_reward=rewards["freeze"],
                is_completed=existing is not None,
            )
        )

    return StreakStatusOut(
        current_streak=current_user.current_streak,
        longest_streak=current_user.longest_streak,
        streak_freezes=current_user.streak_freezes,
        is_maintained_today=is_streak_maintained_today(current_user, now),
        is_at_risk=is_streak_at_risk(current_user, now),
        next_milestone=get_next_milestone(current_user.current_streak),
        milestones=milestones,
    )


@app.post("/api/v1/streak/claim-daily", response_model=ClaimDailyStreakOut)
def claim_daily_streak(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ClaimDailyStreakOut:
    """Claim daily streak reward."""
    from .services.streak import (
        award_daily_streak_reward,
        award_milestone_rewards,
        is_streak_maintained_today,
    )

    now = datetime.now(timezone.utc)

    # Check if streak is maintained today
    if not is_streak_maintained_today(current_user, now):
        raise HTTPException(
            status_code=400,
            detail="You must be active today to claim daily streak reward",
        )

    # Award daily streak XP
    xp_awarded = award_daily_streak_reward(db, current_user, now)

    # Check for milestone rewards
    milestone_rewards = award_milestone_rewards(db, current_user, now)
    total_milestone_xp = milestone_rewards["total_xp"]

    # Refresh user to get updated values
    db.refresh(current_user)

    message = f"Earned {xp_awarded} XP for maintaining your streak!"
    if total_milestone_xp > 0:
        message += f" Plus {total_milestone_xp} XP from milestone rewards!"

    return ClaimDailyStreakOut(
        xp_awarded=xp_awarded + total_milestone_xp,
        current_streak=current_user.current_streak,
        total_xp=current_user.total_xp,
        message=message,
    )


@app.post("/api/v1/streak/use-freeze", response_model=UseStreakFreezeOut)
def use_streak_freeze(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UseStreakFreezeOut:
    """Use a streak freeze to protect the streak."""
    from .services.streak import use_streak_freeze as use_freeze

    now = datetime.now(timezone.utc)

    success = use_freeze(db, current_user, now)

    if not success:
        if current_user.streak_freezes <= 0:
            message = "You don't have any streak freezes available"
        else:
            message = "Streak freeze can only be used when your streak is at risk"

        return UseStreakFreezeOut(
            success=False,
            remaining_freezes=current_user.streak_freezes,
            message=message,
        )

    # Refresh user to get updated values
    db.refresh(current_user)

    return UseStreakFreezeOut(
        success=True,
        remaining_freezes=current_user.streak_freezes,
        message="Streak freeze used successfully! Your streak is protected.",
    )


# =============================================================================
# Hearts System Endpoints
# =============================================================================


@app.get("/api/v1/hearts", response_model=schemas.HeartsStatusOut)
def get_hearts_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.HeartsStatusOut:
    """Get current hearts status for the user."""
    from .services.hearts import (
        auto_refill_hearts,
        calculate_time_until_refill,
        get_or_create_user_hearts,
    )

    now = datetime.now(timezone.utc)
    user_hearts = get_or_create_user_hearts(db, current_user)

    # Auto-refill hearts
    auto_refill_hearts(db, user_hearts, now)
    db.refresh(user_hearts)

    # Calculate time until refill
    time_until_refill = calculate_time_until_refill(user_hearts, now)

    # Check if unlimited
    is_unlimited = (
        user_hearts.unlimited_until is not None and now < user_hearts.unlimited_until
    )

    return schemas.HeartsStatusOut(
        current_hearts=user_hearts.current_hearts,
        max_hearts=user_hearts.max_hearts,
        last_heart_lost_at=user_hearts.last_heart_lost_at,
        hearts_refill_at=user_hearts.hearts_refill_at,
        unlimited_until=user_hearts.unlimited_until,
        streak_freezes=user_hearts.streak_freezes,
        is_unlimited=is_unlimited,
        time_until_refill_seconds=time_until_refill,
        updated_at=user_hearts.updated_at,
    )


@app.post("/api/v1/hearts/use", response_model=schemas.UseHeartOut)
def use_heart_endpoint(
    payload: schemas.UseHeartIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.UseHeartOut:
    """Use a heart (e.g., on wrong quiz answer)."""
    from .services.hearts import use_heart

    now = datetime.now(timezone.utc)

    # Map string reason to enum
    reason_map = {
        "quiz_wrong": HeartTransactionReason.quiz_wrong,
        "practice": HeartTransactionReason.practice_complete,
    }
    reason = reason_map.get(payload.reason, HeartTransactionReason.quiz_wrong)

    success, user_hearts = use_heart(
        db, current_user, now, reason=reason, metadata=payload.metadata
    )

    if not success:
        return schemas.UseHeartOut(
            success=False,
            current_hearts=user_hearts.current_hearts,
            hearts_refill_at=user_hearts.hearts_refill_at,
            message="No hearts available. Wait for refill or purchase more hearts.",
        )

    message = f"Heart used. {user_hearts.current_hearts} hearts remaining."
    if user_hearts.current_hearts == 0:
        message = "Out of hearts! Wait for refill or purchase more."

    return schemas.UseHeartOut(
        success=True,
        current_hearts=user_hearts.current_hearts,
        hearts_refill_at=user_hearts.hearts_refill_at,
        message=message,
    )


@app.post("/api/v1/hearts/refill", response_model=schemas.RefillHeartsOut)
def refill_hearts_endpoint(
    payload: schemas.RefillHeartsIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.RefillHeartsOut:
    """Refill hearts (purchase, ad watch, reward, etc.)."""
    from .services.hearts import refill_hearts

    now = datetime.now(timezone.utc)

    # Map string method to enum reason
    method_reason_map = {
        "purchase": HeartTransactionReason.heart_purchase,
        "ad_watch": HeartTransactionReason.ad_watch,
        "reward": HeartTransactionReason.reward,
        "admin": HeartTransactionReason.admin_grant,
    }
    reason = method_reason_map.get(payload.method, HeartTransactionReason.reward)

    hearts_added, user_hearts = refill_hearts(
        db,
        current_user,
        now,
        amount=payload.amount,
        reason=reason,
        metadata=payload.metadata,
    )

    if hearts_added == 0:
        return schemas.RefillHeartsOut(
            success=False,
            current_hearts=user_hearts.current_hearts,
            hearts_added=0,
            message="Hearts are already full.",
        )

    return schemas.RefillHeartsOut(
        success=True,
        current_hearts=user_hearts.current_hearts,
        hearts_added=hearts_added,
        message=f"Successfully added {hearts_added} hearts!",
    )


@app.post(
    "/api/v1/hearts/use-streak-freeze",
    response_model=schemas.UseStreakFreezeForHeartsOut,
)
def use_streak_freeze_for_hearts_endpoint(
    payload: schemas.UseStreakFreezeIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.UseStreakFreezeForHeartsOut:
    """Use a streak freeze to restore all hearts."""
    from .services.hearts import use_streak_freeze_for_hearts

    now = datetime.now(timezone.utc)

    success, user_hearts = use_streak_freeze_for_hearts(db, current_user, now)

    if not success:
        return schemas.UseStreakFreezeForHeartsOut(
            success=False,
            current_hearts=user_hearts.current_hearts,
            remaining_freezes=current_user.streak_freezes,
            message="No streak freezes available.",
        )

    # Refresh user to get updated streak_freezes
    db.refresh(current_user)

    return schemas.UseStreakFreezeForHeartsOut(
        success=True,
        current_hearts=user_hearts.current_hearts,
        remaining_freezes=current_user.streak_freezes,
        message="Streak freeze used! All hearts restored.",
    )


@app.get("/api/v1/hearts/transactions", response_model=schemas.HeartTransactionListOut)
def get_heart_transactions_endpoint(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.HeartTransactionListOut:
    """Get heart transaction history for the user."""
    from .services.hearts import get_heart_transactions

    transactions, total = get_heart_transactions(db, current_user, page, page_size)

    return schemas.HeartTransactionListOut(
        transactions=[
            schemas.HeartTransactionOut(
                id=t.id,
                amount=t.amount,
                reason=t.reason.value,
                balance_after=t.balance_after,
                metadata=t.metadata_json,
                created_at=t.created_at,
            )
            for t in transactions
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


# =============================================================================
# Weekly Quest Endpoints
# =============================================================================


def _ensure_weekly_quests_for_user(
    db: Session, user_id: UUID, current_time: datetime
) -> list[UserWeeklyQuest]:
    """Ensure user has all active recurring weekly quests assigned for the current week."""
    from .services.weekly_quests import ensure_weekly_quests_for_user

    return ensure_weekly_quests_for_user(db, user_id, current_time)


@app.get("/api/v1/weekly-quests", response_model=schemas.WeeklyQuestsResponse)
def get_weekly_quests(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.WeeklyQuestsResponse:
    """Get this week's quests with progress."""
    from .services.weekly_quests import get_week_end_date, get_week_start_date

    current_time = datetime.now(timezone.utc)
    week_start = get_week_start_date(current_time)
    week_end = get_week_end_date(week_start)

    # Ensure user has quests for this week
    _ensure_weekly_quests_for_user(db, current_user.id, current_time)
    db.commit()

    # Fetch user's quests for this week
    user_quests = (
        db.execute(
            select(UserWeeklyQuest)
            .options(selectinload(UserWeeklyQuest.quest))
            .where(
                UserWeeklyQuest.user_id == current_user.id,
                UserWeeklyQuest.week_start_date == week_start,
            )
            .order_by(UserWeeklyQuest.quest_id)
        )
        .scalars()
        .all()
    )

    quests_out = []
    total_xp = 0
    completed_count = 0

    for uq in user_quests:
        if not uq.quest.is_active:
            continue

        progress_pct = min(100, int((uq.current_count / uq.quest.target_count) * 100))

        quests_out.append(
            schemas.UserWeeklyQuestOut(
                id=uq.id,
                quest=schemas.WeeklyQuestOut(
                    id=uq.quest.id,
                    slug=uq.quest.slug,
                    name=uq.quest.name,
                    description=uq.quest.description,
                    category=uq.quest.category.value,
                    week_number=uq.quest.week_number,
                    year=uq.quest.year,
                    target_count=uq.quest.target_count,
                    xp_reward=uq.quest.xp_reward,
                    badge_slug=uq.quest.badge_slug,
                    is_recurring=uq.quest.is_recurring,
                    is_active=uq.quest.is_active,
                ),
                week_start_date=uq.week_start_date,
                current_count=uq.current_count,
                is_completed=uq.is_completed,
                completed_at=uq.completed_at,
                xp_awarded=uq.xp_awarded,
                progress_percentage=progress_pct,
            )
        )

        if uq.is_completed:
            completed_count += 1
            total_xp += uq.xp_awarded

    return schemas.WeeklyQuestsResponse(
        quests=quests_out,
        week_start_date=week_start,
        week_end_date=week_end,
        total_xp_this_week=total_xp,
        completed_count=completed_count,
        total_count=len(quests_out),
    )


@app.post(
    "/api/v1/weekly-quests/{quest_id}/progress",
    response_model=schemas.UpdateWeeklyQuestProgressResponse,
)
def update_weekly_quest_progress(
    quest_id: UUID,
    payload: schemas.UpdateWeeklyQuestProgressRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.UpdateWeeklyQuestProgressResponse:
    """Update progress on a weekly quest."""
    from .services.weekly_quests import get_week_start_date

    current_time = datetime.now(timezone.utc)
    week_start = get_week_start_date(current_time)

    # Find user's quest for this week
    user_quest = db.execute(
        select(UserWeeklyQuest)
        .options(selectinload(UserWeeklyQuest.quest))
        .where(
            UserWeeklyQuest.user_id == current_user.id,
            UserWeeklyQuest.quest_id == quest_id,
            UserWeeklyQuest.week_start_date == week_start,
        )
    ).scalar_one_or_none()

    if user_quest is None:
        raise HTTPException(status_code=404, detail="Quest not found for this week")

    if user_quest.is_completed:
        # Already completed, return current state
        progress_pct = 100
        return schemas.UpdateWeeklyQuestProgressResponse(
            quest=schemas.UserWeeklyQuestOut(
                id=user_quest.id,
                quest=schemas.WeeklyQuestOut(
                    id=user_quest.quest.id,
                    slug=user_quest.quest.slug,
                    name=user_quest.quest.name,
                    description=user_quest.quest.description,
                    category=user_quest.quest.category.value,
                    week_number=user_quest.quest.week_number,
                    year=user_quest.quest.year,
                    target_count=user_quest.quest.target_count,
                    xp_reward=user_quest.quest.xp_reward,
                    badge_slug=user_quest.quest.badge_slug,
                    is_recurring=user_quest.quest.is_recurring,
                    is_active=user_quest.quest.is_active,
                ),
                week_start_date=user_quest.week_start_date,
                current_count=user_quest.current_count,
                is_completed=user_quest.is_completed,
                completed_at=user_quest.completed_at,
                xp_awarded=user_quest.xp_awarded,
                progress_percentage=progress_pct,
            ),
            xp_gained=0,
            just_completed=False,
        )

    # Update progress
    user_quest.current_count = min(
        user_quest.current_count + payload.increment,
        user_quest.quest.target_count,
    )

    xp_gained = 0
    just_completed = False
    badge_earned = None

    # Check if quest is now completed
    if (
        user_quest.current_count >= user_quest.quest.target_count
        and not user_quest.is_completed
    ):
        user_quest.is_completed = True
        user_quest.completed_at = datetime.now(timezone.utc)
        user_quest.xp_awarded = user_quest.quest.xp_reward
        xp_gained = user_quest.quest.xp_reward
        just_completed = True

        # Award XP to user
        current_user.total_xp += xp_gained

        # Award badge if specified
        if user_quest.quest.badge_slug:
            badge = db.execute(
                select(Badge).where(Badge.slug == user_quest.quest.badge_slug)
            ).scalar_one_or_none()

            if badge:
                # Check if user already has this badge
                existing_user_badge = db.execute(
                    select(UserBadge).where(
                        UserBadge.user_id == current_user.id,
                        UserBadge.badge_id == badge.id,
                    )
                ).scalar_one_or_none()

                if not existing_user_badge:
                    user_badge = UserBadge(
                        user_id=current_user.id,
                        badge_id=badge.id,
                        awarded_at=datetime.now(timezone.utc),
                    )
                    db.add(user_badge)
                    badge_earned = badge.slug

    db.commit()
    db.refresh(user_quest)

    progress_pct = min(
        100, int((user_quest.current_count / user_quest.quest.target_count) * 100)
    )

    return schemas.UpdateWeeklyQuestProgressResponse(
        quest=schemas.UserWeeklyQuestOut(
            id=user_quest.id,
            quest=schemas.WeeklyQuestOut(
                id=user_quest.quest.id,
                slug=user_quest.quest.slug,
                name=user_quest.quest.name,
                description=user_quest.quest.description,
                category=user_quest.quest.category.value,
                week_number=user_quest.quest.week_number,
                year=user_quest.quest.year,
                target_count=user_quest.quest.target_count,
                xp_reward=user_quest.quest.xp_reward,
                badge_slug=user_quest.quest.badge_slug,
                is_recurring=user_quest.quest.is_recurring,
                is_active=user_quest.quest.is_active,
            ),
            week_start_date=user_quest.week_start_date,
            current_count=user_quest.current_count,
            is_completed=user_quest.is_completed,
            completed_at=user_quest.completed_at,
            xp_awarded=user_quest.xp_awarded,
            progress_percentage=progress_pct,
        ),
        xp_gained=xp_gained,
        just_completed=just_completed,
        badge_earned=badge_earned,
    )


@app.get(
    "/api/v1/weekly-quests/history", response_model=schemas.WeeklyQuestHistoryResponse
)
def get_weekly_quest_history(
    weeks: int = Query(default=4, ge=1, le=12),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.WeeklyQuestHistoryResponse:
    """Get past weekly quest history."""
    from .services.weekly_quests import get_week_start_date

    current_time = datetime.now(timezone.utc)
    current_week_start = get_week_start_date(current_time)

    # Calculate the start date for the range
    start_date = current_week_start - timedelta(weeks=weeks)

    # Fetch user's quests for the date range
    user_quests = (
        db.execute(
            select(UserWeeklyQuest)
            .options(selectinload(UserWeeklyQuest.quest))
            .where(
                UserWeeklyQuest.user_id == current_user.id,
                UserWeeklyQuest.week_start_date >= start_date,
                UserWeeklyQuest.week_start_date <= current_week_start,
            )
            .order_by(UserWeeklyQuest.week_start_date.desc())
        )
        .scalars()
        .all()
    )

    history_items = []
    total_completed = 0
    total_xp = 0

    for uq in user_quests:
        history_items.append(
            schemas.WeeklyQuestHistoryItem(
                week_start_date=uq.week_start_date,
                quest_name=uq.quest.name,
                quest_category=uq.quest.category.value,
                target_count=uq.quest.target_count,
                current_count=uq.current_count,
                is_completed=uq.is_completed,
                completed_at=uq.completed_at,
                xp_awarded=uq.xp_awarded,
            )
        )
        if uq.is_completed:
            total_completed += 1
            total_xp += uq.xp_awarded

    return schemas.WeeklyQuestHistoryResponse(
        history=history_items,
        total_completed=total_completed,
        total_xp_earned=total_xp,
    )


# ============================================================
# Tag Schemas
# ============================================================


class TagOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    slug: str
    name: str
    tag_type: str
    description: Optional[str] = None
    is_active: bool
    created_at: datetime


class TagCreateIn(BaseModel):
    slug: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=200)
    tag_type: str = Field(..., pattern="^(topic|difficulty|audience|era|style)$")
    description: Optional[str] = None
    is_active: bool = True


class ContentTagOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tag_id: UUID
    content_type: str
    content_id: UUID
    created_at: datetime
    tag: TagOut


class ContentTagCreateIn(BaseModel):
    tag_slugs: list[str] = Field(..., min_items=1)


class SearchRequest(BaseModel):
    q: Optional[str] = Field(None, description="Search query")
    tags: Optional[list[str]] = Field(
        None, description="List of tag slugs to filter by"
    )
    content_types: Optional[list[str]] = Field(
        None, description="List of content types to search (lesson, motif, quiz, quest)"
    )
    limit: int = Field(20, ge=1, le=100)


class SearchResultItem(BaseModel):
    content_type: str
    content_id: UUID
    title: str
    description: Optional[str] = None
    tags: list[TagOut]
    relevance_score: float = 0.0


class SearchResponse(BaseModel):
    results: list[SearchResultItem]
    total: int
    query: Optional[str] = None
    applied_tags: list[str] = []


# ============================================================
# Tag Endpoints
# ============================================================


@app.get("/api/v1/tags", response_model=list[TagOut])
def list_tags(
    tag_type: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
) -> list[TagOut]:
    """List all active tags, optionally filtered by type."""
    query = select(Tag).where(Tag.is_active == True)
    if tag_type:
        query = query.where(Tag.tag_type == tag_type)
    tags = db.execute(query.order_by(Tag.name)).scalars().all()
    return [
        TagOut(
            id=tag.id,
            slug=tag.slug,
            name=tag.name,
            tag_type=tag.tag_type,
            description=tag.description,
            is_active=tag.is_active,
            created_at=tag.created_at,
        )
        for tag in tags
    ]


@app.post("/api/v1/admin/tags", response_model=TagOut, status_code=201)
def create_tag(
    payload: TagCreateIn,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> TagOut:
    """Create a new tag (admin only)."""
    # Check if slug already exists
    existing = db.execute(
        select(Tag).where(Tag.slug == payload.slug)
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Tag with this slug already exists")

    new_tag = Tag(
        id=uuid_module.uuid4(),
        slug=payload.slug,
        name=payload.name,
        tag_type=payload.tag_type,
        description=payload.description,
        is_active=payload.is_active,
    )
    db.add(new_tag)
    db.commit()
    db.refresh(new_tag)

    return TagOut(
        id=new_tag.id,
        slug=new_tag.slug,
        name=new_tag.name,
        tag_type=new_tag.tag_type,
        description=new_tag.description,
        is_active=new_tag.is_active,
        created_at=new_tag.created_at,
    )


@app.post(
    "/api/v1/admin/content/{content_type}/{content_id}/tags",
    response_model=list[ContentTagOut],
)
def add_content_tags(
    content_type: str,
    content_id: UUID,
    payload: ContentTagCreateIn,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> list[ContentTagOut]:
    """Add tags to content (admin only)."""
    # Validate content type
    valid_types = ["lesson", "motif", "quiz", "quest"]
    if content_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid content type. Must be one of: {', '.join(valid_types)}",
        )

    # Verify content exists
    content_exists = False
    if content_type == "lesson":
        content_exists = db.get(LessonContent, content_id) is not None
    elif content_type == "motif":
        content_exists = db.get(Motif, content_id) is not None
    elif content_type == "quiz":
        content_exists = db.get(QuizQuestion, content_id) is not None
    elif content_type == "quest":
        content_exists = db.get(Quest, content_id) is not None

    if not content_exists:
        raise HTTPException(
            status_code=404, detail=f"{content_type.capitalize()} not found"
        )

    # Get tags by slug
    tags = (
        db.execute(
            select(Tag).where(Tag.slug.in_(payload.tag_slugs), Tag.is_active == True)
        )
        .scalars()
        .all()
    )

    if len(tags) != len(payload.tag_slugs):
        found_slugs = {tag.slug for tag in tags}
        missing_slugs = set(payload.tag_slugs) - found_slugs
        raise HTTPException(
            status_code=404, detail=f"Tags not found: {', '.join(missing_slugs)}"
        )

    # Add content tags (using upsert to avoid duplicates)
    created_tags = []
    for tag in tags:
        # Check if already exists
        existing = db.execute(
            select(ContentTag).where(
                ContentTag.tag_id == tag.id,
                ContentTag.content_type == content_type,
                ContentTag.content_id == content_id,
            )
        ).scalar_one_or_none()

        if not existing:
            content_tag = ContentTag(
                id=uuid_module.uuid4(),
                tag_id=tag.id,
                content_type=content_type,
                content_id=content_id,
            )
            db.add(content_tag)
            created_tags.append(content_tag)

    db.commit()

    # Get all tags for this content
    all_content_tags = (
        db.execute(
            select(ContentTag)
            .options(selectinload(ContentTag.tag))
            .where(
                ContentTag.content_type == content_type,
                ContentTag.content_id == content_id,
            )
        )
        .scalars()
        .all()
    )

    return [
        ContentTagOut(
            id=ct.id,
            tag_id=ct.tag_id,
            content_type=ct.content_type,
            content_id=ct.content_id,
            created_at=ct.created_at,
            tag=TagOut(
                id=ct.tag.id,
                slug=ct.tag.slug,
                name=ct.tag.name,
                tag_type=ct.tag.tag_type,
                description=ct.tag.description,
                is_active=ct.tag.is_active,
                created_at=ct.tag.created_at,
            ),
        )
        for ct in all_content_tags
    ]


@app.delete(
    "/api/v1/admin/content/{content_type}/{content_id}/tags/{tag_slug}", status_code=204
)
def remove_content_tag(
    content_type: str,
    content_id: UUID,
    tag_slug: str,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> Response:
    """Remove a tag from content (admin only)."""
    # Validate content type
    valid_types = ["lesson", "motif", "quiz", "quest"]
    if content_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid content type. Must be one of: {', '.join(valid_types)}",
        )

    # Get tag by slug
    tag = db.execute(select(Tag).where(Tag.slug == tag_slug)).scalar_one_or_none()
    if not tag:
        return Response(status_code=204)

    # Delete content tag
    result = db.execute(
        delete(ContentTag).where(
            ContentTag.tag_id == tag.id,
            ContentTag.content_type == content_type,
            ContentTag.content_id == content_id,
        )
    )
    db.commit()

    return Response(status_code=204)


@app.get("/api/v1/search", response_model=SearchResponse)
def search_content(
    q: Optional[str] = Query(None, description="Search query"),
    tags: Optional[str] = Query(None, description="Comma-separated list of tag slugs"),
    content_types: Optional[str] = Query(
        None, description="Comma-separated list of content types"
    ),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> SearchResponse:
    """Search content by query and/or tags."""
    tag_list = [t.strip() for t in tags.split(",")] if tags else []
    content_type_list = (
        [ct.strip() for ct in content_types.split(",")]
        if content_types
        else ["lesson", "motif", "quiz", "quest"]
    )

    # Validate content types
    valid_types = ["lesson", "motif", "quiz", "quest"]
    for ct in content_type_list:
        if ct not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid content type '{ct}'. Must be one of: {', '.join(valid_types)}",
            )

    results = []

    # Search lessons
    if "lesson" in content_type_list:
        lesson_query = select(LessonContent).options(selectinload(LessonContent.motif))

        # Filter by search query
        if q:
            search_filter = or_(
                LessonContent.intro_text.ilike(f"%{q}%"),
                LessonContent.description.ilike(f"%{q}%"),
                LessonContent.historical_context.ilike(f"%{q}%"),
                LessonContent.symbolism.ilike(f"%{q}%"),
            )
            lesson_query = lesson_query.where(search_filter)

        lessons = db.execute(lesson_query.limit(limit)).scalars().all()

        for lesson in lessons:
            # Get tags for this lesson
            lesson_tags = (
                db.execute(
                    select(ContentTag)
                    .options(selectinload(ContentTag.tag))
                    .where(
                        ContentTag.content_type == "lesson",
                        ContentTag.content_id == lesson.id,
                    )
                )
                .scalars()
                .all()
            )

            # Filter by tags if specified
            if tag_list:
                lesson_tag_slugs = {ct.tag.slug for ct in lesson_tags}
                if not any(tag_slug in lesson_tag_slugs for tag_slug in tag_list):
                    continue

            results.append(
                SearchResultItem(
                    content_type="lesson",
                    content_id=lesson.id,
                    title=lesson.intro_text or "Untitled Lesson",
                    description=lesson.description,
                    tags=[
                        TagOut(
                            id=ct.tag.id,
                            slug=ct.tag.slug,
                            name=ct.tag.name,
                            tag_type=ct.tag.tag_type,
                            description=ct.tag.description,
                            is_active=ct.tag.is_active,
                            created_at=ct.tag.created_at,
                        )
                        for ct in lesson_tags
                    ],
                    relevance_score=1.0,
                )
            )

    # Search motifs
    if "motif" in content_type_list:
        motif_query = select(Motif)

        # Filter by search query
        if q:
            search_filter = or_(
                Motif.name.ilike(f"%{q}%"),
                Motif.description.ilike(f"%{q}%"),
            )
            motif_query = motif_query.where(search_filter)

        motifs = db.execute(motif_query.limit(limit)).scalars().all()

        for motif in motifs:
            # Get tags for this motif
            motif_tags = (
                db.execute(
                    select(ContentTag)
                    .options(selectinload(ContentTag.tag))
                    .where(
                        ContentTag.content_type == "motif",
                        ContentTag.content_id == motif.id,
                    )
                )
                .scalars()
                .all()
            )

            # Filter by tags if specified
            if tag_list:
                motif_tag_slugs = {ct.tag.slug for ct in motif_tags}
                if not any(tag_slug in motif_tag_slugs for tag_slug in tag_list):
                    continue

            results.append(
                SearchResultItem(
                    content_type="motif",
                    content_id=motif.id,
                    title=motif.name,
                    description=motif.description,
                    tags=[
                        TagOut(
                            id=ct.tag.id,
                            slug=ct.tag.slug,
                            name=ct.tag.name,
                            tag_type=ct.tag.tag_type,
                            description=ct.tag.description,
                            is_active=ct.tag.is_active,
                            created_at=ct.tag.created_at,
                        )
                        for ct in motif_tags
                    ],
                    relevance_score=1.0,
                )
            )

    # Limit results
    results = results[:limit]

    return SearchResponse(
        results=results,
        total=len(results),
        query=q,
        applied_tags=tag_list,
    )


# =============================================================================
# Analytics Funnel Endpoints (Admin Only)
# =============================================================================


@app.get(
    "/api/v1/admin/analytics/funnels", response_model=list[schemas.FunnelListItemOut]
)
def list_available_funnels(
    current_user: User = Depends(get_admin_user),
) -> list[schemas.FunnelListItemOut]:
    """
    List all available funnel types.

    Admin only endpoint.
    """
    from services.analytics_funnels import list_available_funnels as get_funnels

    funnels = get_funnels()
    return [schemas.FunnelListItemOut(**funnel) for funnel in funnels]


@app.get(
    "/api/v1/admin/analytics/funnels/{funnel_type}",
    response_model=schemas.FunnelDataOut,
)
def get_funnel_data(
    funnel_type: str,
    start_date: Optional[datetime] = Query(
        None, description="Start date for filtering events"
    ),
    end_date: Optional[datetime] = Query(
        None, description="End date for filtering events"
    ),
    cohort: Optional[str] = Query(
        None, description="Cohort identifier (e.g., '2024-W01')"
    ),
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> schemas.FunnelDataOut:
    """
    Get funnel data with conversion rates.

    Supported funnel types:
    - onboarding: App opened → Onboarding started → Goal selected → First lesson started → First lesson completed
    - lesson: Lesson viewed → Lesson started → 50% progress → Lesson completed
    - quiz: Quiz started → Quiz submitted → Quiz passed

    Admin only endpoint.
    """
    from services.analytics_funnels import calculate_funnel_data

    try:
        funnel_data = calculate_funnel_data(
            session=db,
            funnel_type=funnel_type,
            start_date=start_date,
            end_date=end_date,
            cohort=cohort,
        )
        return schemas.FunnelDataOut(**funnel_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# App Version Management Endpoints
# =============================================================================


def _parse_semver(version_str: str) -> tuple[int, int, int]:
    """Parse semantic version string (major.minor.patch) into tuple of integers."""
    try:
        parts = version_str.strip().split(".")
        if len(parts) != 3:
            raise ValueError("Version must be in format major.minor.patch")
        major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
        return (major, minor, patch)
    except (ValueError, AttributeError) as e:
        raise HTTPException(
            status_code=400, detail=f"Invalid version format: {version_str}"
        ) from e


def _compare_versions(version1: str, version2: str) -> int:
    """
    Compare two semantic version strings.
    Returns: -1 if version1 < version2, 0 if equal, 1 if version1 > version2
    """
    v1 = _parse_semver(version1)
    v2 = _parse_semver(version2)

    if v1 < v2:
        return -1
    elif v1 > v2:
        return 1
    else:
        return 0


@app.get("/api/v1/app/version/check", response_model=schemas.AppVersionCheckOut)
def check_app_version(
    platform: str = Query(..., pattern="^(ios|android)$"),
    current_version: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
) -> schemas.AppVersionCheckOut:
    """
    Check if app update is available or required.

    Public endpoint - no authentication required.

    Query params:
    - platform: "ios" or "android"
    - current_version: Current app version (e.g., "1.2.3")

    Returns:
    - update_available: True if newer version exists
    - force_update: True if user must update (current < min_required_version)
    - latest_version: Latest available version
    - download_url: App store link
    - release_notes: What's new in the latest version
    """
    # Get the current/latest version for this platform
    latest = db.execute(
        select(AppVersion)
        .where(
            AppVersion.platform == platform,
            AppVersion.is_current.is_(True),
        )
        .order_by(AppVersion.released_at.desc())
        .limit(1)
    ).scalar_one_or_none()

    if latest is None:
        # No version info available - allow access
        return schemas.AppVersionCheckOut(
            update_available=False,
            force_update=False,
            current_version=current_version,
        )

    # Compare versions
    try:
        comparison = _compare_versions(current_version, latest.version)
    except HTTPException:
        # If version format is invalid, allow access but warn
        logger.warning(f"Invalid version format received: {current_version}")
        return schemas.AppVersionCheckOut(
            update_available=False,
            force_update=False,
            current_version=current_version,
        )

    update_available = comparison < 0  # current < latest

    # Check if force update is required
    force_update = False
    if latest.min_required_version:
        try:
            min_comparison = _compare_versions(
                current_version, latest.min_required_version
            )
            force_update = min_comparison < 0  # current < min_required
        except HTTPException:
            pass  # Invalid min_required_version format, don't force

    # If the version entry itself has force_update=True, enforce it
    if latest.force_update and update_available:
        force_update = True

    return schemas.AppVersionCheckOut(
        update_available=update_available,
        force_update=force_update,
        latest_version=latest.version,
        current_version=current_version,
        min_required_version=latest.min_required_version,
        download_url=latest.download_url,
        release_notes=latest.release_notes,
    )


@app.get("/api/v1/admin/app/versions", response_model=list[schemas.AppVersionOut])
def list_app_versions(
    platform: Optional[str] = Query(None, pattern="^(ios|android)$"),
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> list[schemas.AppVersionOut]:
    """
    List all app versions.

    Admin only endpoint.

    Query params:
    - platform: Optional filter by platform ("ios" or "android")
    """
    query = select(AppVersion).order_by(
        AppVersion.platform.asc(), AppVersion.released_at.desc()
    )

    if platform:
        query = query.where(AppVersion.platform == platform)

    versions = db.execute(query).scalars().all()

    return [
        schemas.AppVersionOut(
            id=v.id,
            platform=v.platform,
            version=v.version,
            version_code=v.version_code,
            min_required_version=v.min_required_version,
            is_current=v.is_current,
            force_update=v.force_update,
            release_notes=v.release_notes,
            download_url=v.download_url,
            released_at=v.released_at,
            created_at=v.created_at,
        )
        for v in versions
    ]


@app.post(
    "/api/v1/admin/app/versions", response_model=schemas.AppVersionOut, status_code=201
)
def create_app_version(
    payload: schemas.AppVersionCreateIn,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> schemas.AppVersionOut:
    """
    Create a new app version entry.

    Admin only endpoint.

    If is_current=True, will unset is_current for all other versions of the same platform.
    """
    # Validate version format
    _parse_semver(payload.version)
    _parse_semver(payload.min_required_version)

    # Check if version already exists for this platform
    existing = db.execute(
        select(AppVersion).where(
            AppVersion.platform == payload.platform,
            AppVersion.version == payload.version,
        )
    ).scalar_one_or_none()

    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail=f"Version {payload.version} already exists for platform {payload.platform}",
        )

    # If this is marked as current, unset is_current for all other versions of this platform
    if payload.is_current:
        db.execute(select(AppVersion).where(AppVersion.platform == payload.platform))
        for v in db.execute(
            select(AppVersion).where(AppVersion.platform == payload.platform)
        ).scalars():
            v.is_current = False
        db.flush()

    new_version = AppVersion(
        id=uuid_module.uuid4(),
        platform=payload.platform,
        version=payload.version,
        version_code=payload.version_code,
        min_required_version=payload.min_required_version,
        is_current=payload.is_current,
        force_update=payload.force_update,
        release_notes=payload.release_notes,
        download_url=payload.download_url,
        released_at=payload.released_at or datetime.now(timezone.utc),
    )

    db.add(new_version)
    db.commit()
    db.refresh(new_version)

    return schemas.AppVersionOut(
        id=new_version.id,
        platform=new_version.platform,
        version=new_version.version,
        version_code=new_version.version_code,
        min_required_version=new_version.min_required_version,
        is_current=new_version.is_current,
        force_update=new_version.force_update,
        release_notes=new_version.release_notes,
        download_url=new_version.download_url,
        released_at=new_version.released_at,
        created_at=new_version.created_at,
    )


@app.put(
    "/api/v1/admin/app/versions/{version_id}", response_model=schemas.AppVersionOut
)
def update_app_version(
    version_id: UUID,
    payload: schemas.AppVersionUpdateIn,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> schemas.AppVersionOut:
    """
    Update an app version entry.

    Admin only endpoint.

    Allows updating flags like is_current, force_update, release_notes, and download_url.
    """
    version = db.get(AppVersion, version_id)
    if version is None:
        raise HTTPException(status_code=404, detail="App version not found")

    # If setting this as current, unset is_current for all other versions of this platform
    if payload.is_current is True and not version.is_current:
        for v in db.execute(
            select(AppVersion).where(
                AppVersion.platform == version.platform,
                AppVersion.id != version_id,
            )
        ).scalars():
            v.is_current = False
        db.flush()

    # Update fields
    if payload.is_current is not None:
        version.is_current = payload.is_current
    if payload.force_update is not None:
        version.force_update = payload.force_update
    if payload.release_notes is not None:
        version.release_notes = payload.release_notes
    if payload.download_url is not None:
        version.download_url = payload.download_url

    db.commit()
    db.refresh(version)

    return schemas.AppVersionOut(
        id=version.id,
        platform=version.platform,
        version=version.version,
        version_code=version.version_code,
        min_required_version=version.min_required_version,
        is_current=version.is_current,
        force_update=version.force_update,
        release_notes=version.release_notes,
        download_url=version.download_url,
        released_at=version.released_at,
        created_at=version.created_at,
    )


# =============================================================================
# Abuse Report Endpoints
# =============================================================================


@app.post(
    "/api/v1/reports/abuse", response_model=schemas.AbuseReportOut, status_code=201
)
def create_abuse_report(
    payload: schemas.AbuseReportCreateIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.AbuseReportOut:
    """
    Submit an abuse report for user-generated content.

    Any authenticated user can submit a report.
    Reports are automatically prioritized based on reason and content type.
    High and critical priority reports trigger admin notifications.
    """
    from .services.abuse_reports import create_abuse_report as create_report

    report = create_report(
        db=db,
        reporter_id=current_user.id,
        reported_user_id=payload.reported_user_id,
        content_type=payload.content_type,
        content_id=payload.content_id,
        reason=payload.reason,
        description=payload.description,
        evidence_urls=payload.evidence_urls,
    )

    db.commit()
    db.refresh(report)

    return schemas.AbuseReportOut(
        id=report.id,
        reporter_id=report.reporter_id,
        reported_user_id=report.reported_user_id,
        content_type=report.content_type,
        content_id=report.content_id,
        reason=report.reason,
        description=report.description,
        evidence_urls=report.evidence_urls,
        status=report.status,
        priority=report.priority,
        assigned_to_id=report.assigned_to_id,
        resolution_notes=report.resolution_notes,
        resolved_at=report.resolved_at,
        created_at=report.created_at,
    )


@app.get("/api/v1/reports/abuse/mine", response_model=list[schemas.AbuseReportOut])
def get_my_abuse_reports(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
) -> list[schemas.AbuseReportOut]:
    """
    Get abuse reports submitted by the current user.

    Allows users to track the status of their submitted reports.
    """
    query = select(AbuseReport).where(AbuseReport.reporter_id == current_user.id)

    if status_filter:
        query = query.where(AbuseReport.status == status_filter)

    query = query.order_by(AbuseReport.created_at.desc())

    reports = db.execute(query).scalars().all()

    return [
        schemas.AbuseReportOut(
            id=r.id,
            reporter_id=r.reporter_id,
            reported_user_id=r.reported_user_id,
            content_type=r.content_type,
            content_id=r.content_id,
            reason=r.reason,
            description=r.description,
            evidence_urls=r.evidence_urls,
            status=r.status,
            priority=r.priority,
            assigned_to_id=r.assigned_to_id,
            resolution_notes=r.resolution_notes,
            resolved_at=r.resolved_at,
            created_at=r.created_at,
        )
        for r in reports
    ]


@app.get("/api/v1/admin/reports/abuse", response_model=schemas.AbuseReportListOut)
def admin_list_abuse_reports(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
    status: Optional[str] = Query(None, description="Filter by status"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
) -> schemas.AbuseReportListOut:
    """
    List all abuse reports with filtering and pagination.

    Admin only endpoint.
    """
    query = select(AbuseReport).options(
        selectinload(AbuseReport.reporter),
        selectinload(AbuseReport.reported_user),
        selectinload(AbuseReport.assigned_to),
    )

    if status:
        query = query.where(AbuseReport.status == status)
    if priority:
        query = query.where(AbuseReport.priority == priority)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = db.execute(count_query).scalar_one()

    # Apply pagination and ordering
    query = query.order_by(AbuseReport.priority.desc(), AbuseReport.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    reports = db.execute(query).scalars().all()

    return schemas.AbuseReportListOut(
        reports=[
            schemas.AbuseReportDetailOut(
                id=r.id,
                reporter_id=r.reporter_id,
                reporter_email=r.reporter.email if r.reporter else None,
                reporter_display_name=r.reporter.display_name if r.reporter else None,
                reported_user_id=r.reported_user_id,
                reported_user_email=r.reported_user.email if r.reported_user else None,
                reported_user_display_name=r.reported_user.display_name
                if r.reported_user
                else None,
                content_type=r.content_type,
                content_id=r.content_id,
                reason=r.reason,
                description=r.description,
                evidence_urls=r.evidence_urls,
                status=r.status,
                priority=r.priority,
                assigned_to_id=r.assigned_to_id,
                assigned_to_email=r.assigned_to.email if r.assigned_to else None,
                assigned_to_display_name=r.assigned_to.display_name
                if r.assigned_to
                else None,
                resolution_notes=r.resolution_notes,
                resolved_at=r.resolved_at,
                created_at=r.created_at,
            )
            for r in reports
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@app.get(
    "/api/v1/admin/reports/abuse/{report_id}",
    response_model=schemas.AbuseReportDetailOut,
)
def admin_get_abuse_report(
    report_id: UUID,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> schemas.AbuseReportDetailOut:
    """
    Get detailed information about a specific abuse report.

    Admin only endpoint.
    """
    report = db.execute(
        select(AbuseReport)
        .where(AbuseReport.id == report_id)
        .options(
            selectinload(AbuseReport.reporter),
            selectinload(AbuseReport.reported_user),
            selectinload(AbuseReport.assigned_to),
        )
    ).scalar_one_or_none()

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    return schemas.AbuseReportDetailOut(
        id=report.id,
        reporter_id=report.reporter_id,
        reporter_email=report.reporter.email if report.reporter else None,
        reporter_display_name=report.reporter.display_name if report.reporter else None,
        reported_user_id=report.reported_user_id,
        reported_user_email=report.reported_user.email
        if report.reported_user
        else None,
        reported_user_display_name=report.reported_user.display_name
        if report.reported_user
        else None,
        content_type=report.content_type,
        content_id=report.content_id,
        reason=report.reason,
        description=report.description,
        evidence_urls=report.evidence_urls,
        status=report.status,
        priority=report.priority,
        assigned_to_id=report.assigned_to_id,
        assigned_to_email=report.assigned_to.email if report.assigned_to else None,
        assigned_to_display_name=report.assigned_to.display_name
        if report.assigned_to
        else None,
        resolution_notes=report.resolution_notes,
        resolved_at=report.resolved_at,
        created_at=report.created_at,
    )


@app.post(
    "/api/v1/admin/reports/abuse/{report_id}/assign",
    response_model=schemas.AbuseReportDetailOut,
)
def admin_assign_abuse_report(
    report_id: UUID,
    payload: schemas.AbuseReportAssignIn,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> schemas.AbuseReportDetailOut:
    """
    Assign an abuse report to an admin user.

    Admin only endpoint.
    Changes status from 'pending' to 'reviewing' if applicable.
    """
    from .services.abuse_reports import assign_abuse_report

    try:
        report = assign_abuse_report(
            db=db,
            report_id=report_id,
            assigned_to_id=payload.assigned_to_id,
        )
        db.commit()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Reload with relationships
    db.refresh(report)
    report = db.execute(
        select(AbuseReport)
        .where(AbuseReport.id == report_id)
        .options(
            selectinload(AbuseReport.reporter),
            selectinload(AbuseReport.reported_user),
            selectinload(AbuseReport.assigned_to),
        )
    ).scalar_one()

    return schemas.AbuseReportDetailOut(
        id=report.id,
        reporter_id=report.reporter_id,
        reporter_email=report.reporter.email if report.reporter else None,
        reporter_display_name=report.reporter.display_name if report.reporter else None,
        reported_user_id=report.reported_user_id,
        reported_user_email=report.reported_user.email
        if report.reported_user
        else None,
        reported_user_display_name=report.reported_user.display_name
        if report.reported_user
        else None,
        content_type=report.content_type,
        content_id=report.content_id,
        reason=report.reason,
        description=report.description,
        evidence_urls=report.evidence_urls,
        status=report.status,
        priority=report.priority,
        assigned_to_id=report.assigned_to_id,
        assigned_to_email=report.assigned_to.email if report.assigned_to else None,
        assigned_to_display_name=report.assigned_to.display_name
        if report.assigned_to
        else None,
        resolution_notes=report.resolution_notes,
        resolved_at=report.resolved_at,
        created_at=report.created_at,
    )


@app.post(
    "/api/v1/admin/reports/abuse/{report_id}/resolve",
    response_model=schemas.AbuseReportDetailOut,
)
def admin_resolve_abuse_report(
    report_id: UUID,
    payload: schemas.AbuseReportResolveIn,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> schemas.AbuseReportDetailOut:
    """
    Resolve an abuse report.

    Admin only endpoint.
    Sets status to 'resolved' or 'dismissed' with resolution notes.
    """
    from .services.abuse_reports import resolve_abuse_report

    try:
        report = resolve_abuse_report(
            db=db,
            report_id=report_id,
            status=payload.status,
            resolution_notes=payload.resolution_notes,
        )
        db.commit()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Reload with relationships
    db.refresh(report)
    report = db.execute(
        select(AbuseReport)
        .where(AbuseReport.id == report_id)
        .options(
            selectinload(AbuseReport.reporter),
            selectinload(AbuseReport.reported_user),
            selectinload(AbuseReport.assigned_to),
        )
    ).scalar_one()

    return schemas.AbuseReportDetailOut(
        id=report.id,
        reporter_id=report.reporter_id,
        reporter_email=report.reporter.email if report.reporter else None,
        reporter_display_name=report.reporter.display_name if report.reporter else None,
        reported_user_id=report.reported_user_id,
        reported_user_email=report.reported_user.email
        if report.reported_user
        else None,
        reported_user_display_name=report.reported_user.display_name
        if report.reported_user
        else None,
        content_type=report.content_type,
        content_id=report.content_id,
        reason=report.reason,
        description=report.description,
        evidence_urls=report.evidence_urls,
        status=report.status,
        priority=report.priority,
        assigned_to_id=report.assigned_to_id,
        assigned_to_email=report.assigned_to.email if report.assigned_to else None,
        assigned_to_display_name=report.assigned_to.display_name
        if report.assigned_to
        else None,
        resolution_notes=report.resolution_notes,
        resolved_at=report.resolved_at,
        created_at=report.created_at,
    )


# =============================================================================
# Spaced Repetition Review Endpoints
# =============================================================================


@app.get("/api/v1/review/due", response_model=schemas.DueCardsOut)
def get_due_review_cards(
    limit: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.DueCardsOut:
    """
    Get cards due for review.

    Returns cards that are ready to be reviewed based on spaced repetition schedule.
    """
    from .services.spaced_repetition import get_due_cards

    now = datetime.now(timezone.utc)
    cards = get_due_cards(db=db, user_id=current_user.id, limit=limit, now=now)

    # Prepare response with motif details
    card_outputs = []
    for card in cards:
        # Get motif details
        motif_data = None
        if card.motif:
            motif_data = {
                "id": card.motif.id,
                "name": card.motif.name,
                "name_han": card.motif.name_han,
                "thumbnail_url": card.motif.thumbnail_url,
                "category": card.motif.category.value if card.motif.category else None,
            }

        card_outputs.append(
            schemas.SpacedRepetitionCardOut(
                id=card.id,
                user_id=card.user_id,
                motif_id=card.motif_id,
                ease_factor=card.ease_factor,
                interval_days=card.interval_days,
                repetitions=card.repetitions,
                next_review_at=card.next_review_at,
                last_reviewed_at=card.last_reviewed_at,
                review_history=card.review_history or [],
                created_at=card.created_at,
                updated_at=card.updated_at,
                motif=motif_data,
            )
        )

    return schemas.DueCardsOut(
        cards=card_outputs,
        total_due=len(cards),
    )


@app.post("/api/v1/review/{card_id}", response_model=schemas.SpacedRepetitionCardOut)
def submit_review_result(
    card_id: UUID,
    payload: schemas.ReviewSubmitIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.SpacedRepetitionCardOut:
    """
    Submit a review result for a card.

    Quality scale:
    - 0: Complete blackout
    - 1: Incorrect response; correct one recalled
    - 2: Incorrect response; correct one seemed easy to recall
    - 3: Correct response recalled with serious difficulty
    - 4: Correct response after hesitation
    - 5: Perfect response
    """
    from .services.spaced_repetition import process_review

    now = datetime.now(timezone.utc)

    # Verify card belongs to user
    card = db.get(SpacedRepetitionCard, card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    if card.user_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to review this card"
        )

    try:
        card = process_review(
            db=db,
            card_id=card_id,
            quality=payload.quality,
            now=now,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Reload card with motif
    db.refresh(card)
    card = db.execute(
        select(SpacedRepetitionCard)
        .where(SpacedRepetitionCard.id == card_id)
        .options(selectinload(SpacedRepetitionCard.motif))
    ).scalar_one()

    # Prepare motif data
    motif_data = None
    if card.motif:
        motif_data = {
            "id": card.motif.id,
            "name": card.motif.name,
            "name_han": card.motif.name_han,
            "thumbnail_url": card.motif.thumbnail_url,
            "category": card.motif.category.value if card.motif.category else None,
        }

    return schemas.SpacedRepetitionCardOut(
        id=card.id,
        user_id=card.user_id,
        motif_id=card.motif_id,
        ease_factor=card.ease_factor,
        interval_days=card.interval_days,
        repetitions=card.repetitions,
        next_review_at=card.next_review_at,
        last_reviewed_at=card.last_reviewed_at,
        review_history=card.review_history or [],
        created_at=card.created_at,
        updated_at=card.updated_at,
        motif=motif_data,
    )


# =============================================================================
# Learning Path Endpoints
# =============================================================================


def _format_learning_path_response(path: UserLearningPath) -> schemas.LearningPathOut:
    """Format a UserLearningPath model into a response schema."""
    # Parse lessons
    lessons = []
    for lesson_data in path.recommended_lessons:
        lessons.append(
            schemas.LearningPathItemOut(
                item_id=UUID(lesson_data["lesson_id"]),
                motif_id=UUID(lesson_data.get("motif_id"))
                if lesson_data.get("motif_id")
                else None,
                order=lesson_data["order"],
                item_type="lesson",
                reason=lesson_data.get("reason"),
                is_completed=any(
                    c["item_type"] == "lesson"
                    and c["item_id"] == lesson_data["lesson_id"]
                    for c in path.completed_items
                ),
            )
        )

    # Parse reviews
    reviews = []
    for review_data in path.recommended_reviews:
        reviews.append(
            schemas.LearningPathItemOut(
                item_id=UUID(review_data["motif_id"]),
                motif_id=UUID(review_data["motif_id"]),
                order=review_data["order"],
                item_type="review",
                priority=review_data.get("priority"),
                is_completed=any(
                    c["item_type"] == "review"
                    and c["item_id"] == review_data["motif_id"]
                    for c in path.completed_items
                ),
            )
        )

    # Parse quizzes
    quizzes = []
    for quiz_data in path.recommended_quizzes:
        quizzes.append(
            schemas.LearningPathItemOut(
                item_id=UUID(quiz_data["motif_id"]),
                motif_id=UUID(quiz_data["motif_id"]),
                order=quiz_data["order"],
                item_type="quiz",
                difficulty=quiz_data.get("difficulty"),
                is_completed=any(
                    c["item_type"] == "quiz" and c["item_id"] == quiz_data["motif_id"]
                    for c in path.completed_items
                ),
            )
        )

    # Calculate progress
    total_items = len(lessons) + len(reviews) + len(quizzes)
    completed_items = len(path.completed_items)

    progress = {
        "total": total_items,
        "completed": completed_items,
        "percentage": (completed_items / total_items * 100) if total_items > 0 else 0,
        "lessons": {
            "total": len(lessons),
            "completed": sum(1 for l in lessons if l.is_completed),
        },
        "reviews": {
            "total": len(reviews),
            "completed": sum(1 for r in reviews if r.is_completed),
        },
        "quizzes": {
            "total": len(quizzes),
            "completed": sum(1 for q in quizzes if q.is_completed),
        },
    }

    return schemas.LearningPathOut(
        id=path.id,
        path_date=path.path_date,
        lessons=lessons,
        reviews=reviews,
        quizzes=quizzes,
        estimated_time_minutes=path.estimated_time_minutes,
        is_completed=path.is_completed,
        completed_at=path.completed_at,
        generated_at=path.generated_at,
        progress=progress,
    )


@app.get("/api/v1/learning-path/today", response_model=schemas.LearningPathOut)
def get_todays_learning_path(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get today's personalized learning path.

    Automatically generates a new path if one doesn't exist for today.
    """
    from .services import learning_path as lp_service

    now = datetime.now(timezone.utc)
    path = lp_service.get_todays_learning_path(db, current_user, now)

    if not path:
        raise AppError(
            code="PATH_NOT_FOUND",
            message="Could not generate learning path",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return _format_learning_path_response(path)


@app.post("/api/v1/learning-path/generate", response_model=schemas.LearningPathOut)
def generate_learning_path(
    request: schemas.LearningPathGenerateIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Force regenerate a learning path for a specific date.

    If a path already exists for the date, it will be deleted and a new one generated.
    """
    from .services import learning_path as lp_service

    now = datetime.now(timezone.utc)
    target_date = request.target_date if request.target_date else now

    # Normalize to start of day
    target_date = target_date.replace(hour=0, minute=0, second=0, microsecond=0)

    # If force regenerate, delete existing path
    if request.force_regenerate:
        existing_path = db.execute(
            select(UserLearningPath).where(
                and_(
                    UserLearningPath.user_id == current_user.id,
                    UserLearningPath.path_date == target_date,
                )
            )
        ).scalar_one_or_none()

        if existing_path:
            db.delete(existing_path)
            db.commit()

    # Generate new path
    path = lp_service.generate_learning_path(db, current_user, target_date, now)

    return _format_learning_path_response(path)


@app.post(
    "/api/v1/learning-path/complete-item", response_model=schemas.CompletePathItemOut
)
def complete_learning_path_item(
    request: schemas.CompletePathItemIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Mark an item in today's learning path as completed.

    This updates the progress tracking for the learning path.
    """
    from .services import learning_path as lp_service

    now = datetime.now(timezone.utc)

    # Get today's learning path
    path = lp_service.get_todays_learning_path(db, current_user, now)

    if not path:
        raise AppError(
            code="PATH_NOT_FOUND",
            message="No learning path found for today",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    # Complete the item
    result = lp_service.complete_path_item(
        db, path, request.item_type, request.item_id, now
    )

    message = "Item completed successfully"
    if result["already_completed"]:
        message = "Item was already completed"
    elif result["path_completed"]:
        message = "Congratulations! You've completed today's learning path!"

    return schemas.CompletePathItemOut(
        success=True,
        message=message,
        already_completed=result["already_completed"],
        completed_at=datetime.fromisoformat(result["completed_at"]),
        path_completed=result.get("path_completed", False),
        progress=result.get("progress", 0),
        total=result.get("total", 0),
    )


@app.get("/api/v1/learning-path/history", response_model=schemas.LearningPathHistoryOut)
def get_learning_path_history(
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get historical learning paths for the user.

    Returns up to the specified number of days of learning path history.
    """
    from .services import learning_path as lp_service

    paths = lp_service.get_path_history(db, current_user, limit=days)

    formatted_paths = [_format_learning_path_response(p) for p in paths]

    return schemas.LearningPathHistoryOut(
        paths=formatted_paths,
        total_paths=len(formatted_paths),
        days_analyzed=days,
    )


@app.get("/api/v1/learning-path/stats", response_model=schemas.LearningPathStatsOut)
def get_learning_path_stats(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get learning path statistics for the user.

    Returns completion rates and other metrics for the specified time period.
    """
    from .services import learning_path as lp_service

    stats = lp_service.get_path_statistics(db, current_user, days=days)

    return schemas.LearningPathStatsOut(**stats)


@app.get("/api/v1/review/stats", response_model=schemas.ReviewStatsOut)
def get_review_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.ReviewStatsOut:
    """
    Get user's review statistics.

    Returns counts of total cards, due cards, reviewed today, mastered cards, etc.
    """
    from .services.spaced_repetition import get_user_review_stats

    now = datetime.now(timezone.utc)
    stats = get_user_review_stats(db=db, user_id=current_user.id, now=now)

    return schemas.ReviewStatsOut(**stats)


@app.post("/api/v1/review/cards", response_model=schemas.SpacedRepetitionCardOut)
def add_card_to_review_deck(
    payload: schemas.AddCardIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.SpacedRepetitionCardOut:
    """
    Add a motif to the user's review deck.

    Creates a new spaced repetition card for the specified motif.
    If card already exists, returns the existing card.
    """
    from .services.spaced_repetition import add_card_to_deck

    now = datetime.now(timezone.utc)

    try:
        card = add_card_to_deck(
            db=db,
            user_id=current_user.id,
            motif_id=payload.motif_id,
            now=now,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Reload card with motif
    db.refresh(card)
    card = db.execute(
        select(SpacedRepetitionCard)
        .where(SpacedRepetitionCard.id == card.id)
        .options(selectinload(SpacedRepetitionCard.motif))
    ).scalar_one()

    # Prepare motif data
    motif_data = None
    if card.motif:
        motif_data = {
            "id": card.motif.id,
            "name": card.motif.name,
            "name_han": card.motif.name_han,
            "thumbnail_url": card.motif.thumbnail_url,
            "category": card.motif.category.value if card.motif.category else None,
        }

    return schemas.SpacedRepetitionCardOut(
        id=card.id,
        user_id=card.user_id,
        motif_id=card.motif_id,
        ease_factor=card.ease_factor,
        interval_days=card.interval_days,
        repetitions=card.repetitions,
        next_review_at=card.next_review_at,
        last_reviewed_at=card.last_reviewed_at,
        review_history=card.review_history or [],
        created_at=card.created_at,
        updated_at=card.updated_at,
        motif=motif_data,
    )


# =============================================================================
# AI Conversation Endpoints
# =============================================================================


@app.get("/api/v1/ai/conversations", response_model=schemas.AIConversationListOut)
def list_ai_conversations(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    active_only: bool = Query(True, description="Only return active conversations"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.AIConversationListOut:
    """
    Get user's AI conversations with pagination.

    Returns a list of conversation summaries with metadata.
    """
    from .services import ai_tutor

    conversations, total = ai_tutor.get_user_conversations(
        db, current_user, page=page, page_size=page_size, active_only=active_only
    )

    # Format conversations with last message preview
    formatted_conversations = []
    for conv in conversations:
        # Get last message for preview
        last_msg = db.execute(
            select(AIMessage)
            .where(AIMessage.conversation_id == conv.id)
            .order_by(AIMessage.created_at.desc())
            .limit(1)
        ).scalar_one_or_none()

        last_message = None
        last_message_at = None
        if last_msg:
            # Truncate for preview
            last_message = (
                last_msg.content[:100] + "..."
                if len(last_msg.content) > 100
                else last_msg.content
            )
            last_message_at = last_msg.created_at

        formatted_conversations.append(
            schemas.AIConversationSummaryOut(
                id=conv.id,
                title=conv.title,
                context_type=conv.context_type,
                context_id=conv.context_id,
                is_active=conv.is_active,
                message_count=conv.message_count,
                created_at=conv.created_at,
                updated_at=conv.updated_at,
                last_message=last_message,
                last_message_at=last_message_at,
            )
        )

    return schemas.AIConversationListOut(
        conversations=formatted_conversations,
        total=total,
        page=page,
        page_size=page_size,
        has_more=(page * page_size) < total,
    )


@app.post(
    "/api/v1/ai/conversations",
    response_model=schemas.AIConversationCreateOut,
    status_code=201,
)
def create_ai_conversation(
    payload: schemas.AIConversationCreateIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.AIConversationCreateOut:
    """
    Create a new AI conversation.

    Optionally can include an initial message to start the conversation.
    """
    from .services import ai_tutor

    # Create conversation
    conversation = ai_tutor.create_conversation(
        db,
        current_user,
        title=payload.title,
        context_type=payload.context_type,
        context_id=payload.context_id,
    )

    # If initial message provided, send it
    if payload.initial_message:
        try:
            ai_tutor.send_message(
                db,
                conversation,
                current_user,
                payload.initial_message,
                deepseek_chat_func=_call_deepseek_chat,
                collect_sources_func=_collect_ai_sources,
                get_rag_settings_func=_get_rag_settings,
            )
        except Exception as e:
            logger.error(f"Error sending initial message: {e}")
            # Don't fail the conversation creation

    return schemas.AIConversationCreateOut(
        id=conversation.id,
        title=conversation.title,
        context_type=conversation.context_type,
        context_id=conversation.context_id,
        created_at=conversation.created_at,
    )


@app.get(
    "/api/v1/ai/conversations/{conversation_id}",
    response_model=schemas.AIConversationDetailOut,
)
def get_ai_conversation(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.AIConversationDetailOut:
    """
    Get a specific conversation with all messages.
    """
    from .services import ai_tutor

    conversation = ai_tutor.get_conversation(db, conversation_id, current_user)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Format messages
    formatted_messages = [
        schemas.AIMessageOut(
            id=msg.id,
            conversation_id=msg.conversation_id,
            role=msg.role,
            content=msg.content,
            tokens_used=msg.tokens_used,
            created_at=msg.created_at,
        )
        for msg in conversation.messages
    ]

    return schemas.AIConversationDetailOut(
        id=conversation.id,
        title=conversation.title,
        context_type=conversation.context_type,
        context_id=conversation.context_id,
        is_active=conversation.is_active,
        message_count=conversation.message_count,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        messages=formatted_messages,
    )


@app.post(
    "/api/v1/ai/conversations/{conversation_id}/messages",
    response_model=schemas.AISendMessageOut,
)
def send_message_to_conversation(
    conversation_id: UUID,
    payload: schemas.AISendMessageIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.AISendMessageOut:
    """
    Send a message in a conversation and get AI response.

    The AI will respond based on conversation context and RAG sources.
    """
    from .services import ai_tutor

    if not settings.deepseek_api_key:
        raise HTTPException(status_code=503, detail="AI service not configured")

    # Get conversation
    conversation = ai_tutor.get_conversation(db, conversation_id, current_user)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if not conversation.is_active:
        raise HTTPException(status_code=400, detail="Conversation is not active")

    # Send message
    try:
        user_message, ai_response = ai_tutor.send_message(
            db,
            conversation,
            current_user,
            payload.message,
            deepseek_chat_func=_call_deepseek_chat,
            collect_sources_func=_collect_ai_sources,
            get_rag_settings_func=_get_rag_settings,
        )
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        raise HTTPException(status_code=500, detail="Failed to send message")

    # Format response
    return schemas.AISendMessageOut(
        message=schemas.AIMessageOut(
            id=user_message.id,
            conversation_id=user_message.conversation_id,
            role=user_message.role,
            content=user_message.content,
            tokens_used=user_message.tokens_used,
            created_at=user_message.created_at,
        ),
        response=schemas.AIMessageOut(
            id=ai_response.id,
            conversation_id=ai_response.conversation_id,
            role=ai_response.role,
            content=ai_response.content,
            tokens_used=ai_response.tokens_used,
            created_at=ai_response.created_at,
        ),
        conversation_id=conversation.id,
        tokens_used=ai_response.tokens_used,
    )


@app.delete("/api/v1/ai/conversations/{conversation_id}", status_code=204)
def delete_ai_conversation(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Delete a conversation.

    This permanently deletes the conversation and all its messages.
    """
    from .services import ai_tutor

    success = ai_tutor.delete_conversation(db, conversation_id, current_user)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return Response(status_code=204)


# =============================================================================
# Social Features - Friends & Follow System
# =============================================================================


@app.get("/api/v1/social/following", response_model=schemas.FollowListOut)
def get_following(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.FollowListOut:
    """Get list of users that the current user is following."""
    from .services import social

    skip = (page - 1) * page_size
    follows, total = social.get_following(
        db, current_user.id, skip=skip, limit=page_size
    )

    return schemas.FollowListOut(
        users=[
            schemas.FollowUserOut(
                id=follow.id,
                user_id=follow.following.id,
                display_name=follow.following.display_name,
                username=follow.following.username,
                avatar_url=follow.following.avatar_url,
                bio=follow.following.bio,
                total_xp=follow.following.total_xp,
                followed_at=follow.created_at,
            )
            for follow in follows
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@app.get("/api/v1/social/followers", response_model=schemas.FollowListOut)
def get_followers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.FollowListOut:
    """Get list of users following the current user."""
    from .services import social

    skip = (page - 1) * page_size
    follows, total = social.get_followers(
        db, current_user.id, skip=skip, limit=page_size
    )

    return schemas.FollowListOut(
        users=[
            schemas.FollowUserOut(
                id=follow.id,
                user_id=follow.follower.id,
                display_name=follow.follower.display_name,
                username=follow.follower.username,
                avatar_url=follow.follower.avatar_url,
                bio=follow.follower.bio,
                total_xp=follow.follower.total_xp,
                followed_at=follow.created_at,
            )
            for follow in follows
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@app.post("/api/v1/social/follow/{user_id}", status_code=201)
def follow_user(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Follow a user."""
    from .services import social

    # Check if user exists
    target_user = db.get(User, user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        follow = social.follow_user(db, current_user.id, user_id)
        return {"message": "User followed successfully", "follow_id": follow.id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/v1/social/follow/{user_id}", status_code=204)
def unfollow_user(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Unfollow a user."""
    from .services import social

    success = social.unfollow_user(db, current_user.id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Not following this user")

    return Response(status_code=204)


@app.get("/api/v1/social/friends", response_model=schemas.FriendListOut)
def get_friends(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.FriendListOut:
    """Get list of friends (mutual follows)."""
    from .services import social

    friends = social.get_friends(db, current_user.id)
    online_status = social.get_online_status_map(db, [friend.id for friend in friends])

    return schemas.FriendListOut(
        friends=[
            schemas.FriendOut(
                id=friend.id,
                user_id=friend.id,
                display_name=friend.display_name,
                username=friend.username,
                avatar_url=friend.avatar_url,
                bio=friend.bio,
                total_xp=friend.total_xp,
                is_online=online_status.get(friend.id, False),
            )
            for friend in friends
        ],
        total=len(friends),
    )


@app.post(
    "/api/v1/social/friend-requests",
    response_model=schemas.FriendRequestOut,
    status_code=201,
)
def send_friend_request(
    request_data: schemas.FriendRequestCreateIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.FriendRequestOut:
    """Send a friend request to another user."""
    from .services import social

    # Check if target user exists
    target_user = db.get(User, request_data.to_user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        friend_request = social.create_friend_request(
            db, current_user.id, request_data.to_user_id
        )

        return schemas.FriendRequestOut(
            id=friend_request.id,
            from_user_id=friend_request.from_user_id,
            from_user_display_name=current_user.display_name,
            from_user_avatar_url=current_user.avatar_url,
            to_user_id=friend_request.to_user_id,
            to_user_display_name=target_user.display_name,
            to_user_avatar_url=target_user.avatar_url,
            status=friend_request.status.value,
            created_at=friend_request.created_at,
            responded_at=friend_request.responded_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/v1/social/friend-requests", response_model=schemas.FriendRequestListOut)
def get_friend_requests(
    status: Optional[str] = Query(None, pattern="^(pending|accepted|rejected)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.FriendRequestListOut:
    """Get friend requests received by the current user."""
    from .services import social

    requests = social.get_friend_requests(db, current_user.id, status=status)

    pending_count = sum(
        1 for req in requests if req.status == FriendRequestStatus.pending
    )

    return schemas.FriendRequestListOut(
        requests=[
            schemas.FriendRequestOut(
                id=req.id,
                from_user_id=req.from_user_id,
                from_user_display_name=req.from_user.display_name,
                from_user_avatar_url=req.from_user.avatar_url,
                to_user_id=req.to_user_id,
                to_user_display_name=req.to_user.display_name,
                to_user_avatar_url=req.to_user.avatar_url,
                status=req.status.value,
                created_at=req.created_at,
                responded_at=req.responded_at,
            )
            for req in requests
        ],
        total=len(requests),
        pending_count=pending_count,
    )


@app.post(
    "/api/v1/social/friend-requests/{request_id}/accept",
    response_model=schemas.FriendRequestOut,
)
def accept_friend_request(
    request_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.FriendRequestOut:
    """Accept a friend request."""
    from .services import social

    try:
        friend_request = social.accept_friend_request(db, request_id, current_user.id)

        return schemas.FriendRequestOut(
            id=friend_request.id,
            from_user_id=friend_request.from_user_id,
            from_user_display_name=friend_request.from_user.display_name,
            from_user_avatar_url=friend_request.from_user.avatar_url,
            to_user_id=friend_request.to_user_id,
            to_user_display_name=friend_request.to_user.display_name,
            to_user_avatar_url=friend_request.to_user.avatar_url,
            status=friend_request.status.value,
            created_at=friend_request.created_at,
            responded_at=friend_request.responded_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post(
    "/api/v1/social/friend-requests/{request_id}/reject",
    response_model=schemas.FriendRequestOut,
)
def reject_friend_request(
    request_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.FriendRequestOut:
    """Reject a friend request."""
    from .services import social

    try:
        friend_request = social.reject_friend_request(db, request_id, current_user.id)

        return schemas.FriendRequestOut(
            id=friend_request.id,
            from_user_id=friend_request.from_user_id,
            from_user_display_name=friend_request.from_user.display_name,
            from_user_avatar_url=friend_request.from_user.avatar_url,
            to_user_id=friend_request.to_user_id,
            to_user_display_name=friend_request.to_user.display_name,
            to_user_avatar_url=friend_request.to_user.avatar_url,
            status=friend_request.status.value,
            created_at=friend_request.created_at,
            responded_at=friend_request.responded_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# Social Sharing Endpoints
# =============================================================================


@app.get("/api/v1/social/feed", response_model=schemas.ActivityFeedOut)
def get_activity_feed(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.ActivityFeedOut:
    """
    Get activity feed from followed users.

    Returns public shares from other users.
    This filters to shares from users the current user follows.
    """
    from .services import sharing

    shares, total = sharing.get_activity_feed(db, current_user.id, page, page_size)

    # Convert shares to activity items
    activities = []
    for share in shares:
        user = db.query(User).filter(User.id == share.user_id).first()
        if not user:
            continue

        content_data = sharing.get_content_data_for_share(db, share)

        activity = schemas.UserActivityOut(
            id=share.id,
            activity_type="share",
            user_id=user.id,
            user_display_name=user.display_name or user.email,
            user_avatar_url=user.avatar_url,
            content={
                "share_type": share.share_type,
                "caption": share.caption,
                "content_data": content_data,
                "share_url": share.share_url,
                "view_count": share.view_count,
            },
            created_at=share.created_at,
        )
        activities.append(activity)

    return schemas.ActivityFeedOut(
        activities=activities,
        total=total,
        page=page,
        page_size=page_size,
        has_more=(page * page_size) < total,
    )


@app.post(
    "/api/v1/social/share",
    response_model=schemas.ShareOut,
    status_code=status.HTTP_201_CREATED,
)
def create_share(
    share_in: schemas.ShareCreateIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.ShareOut:
    """
    Create a new share.

    Allows users to share their achievements, badges, streaks, level ups, and certificates.
    """
    from .services import sharing

    # Validate content_id exists if provided
    if share_in.content_id:
        if share_in.share_type == "badge":
            badge_exists = (
                db.query(UserBadge)
                .filter(
                    and_(
                        UserBadge.user_id == current_user.id,
                        UserBadge.badge_id == share_in.content_id,
                    )
                )
                .first()
            )
            if not badge_exists:
                raise HTTPException(status_code=404, detail="Badge not found")

        elif share_in.share_type == "certificate":
            cert_exists = (
                db.query(Certificate)
                .filter(
                    and_(
                        Certificate.user_id == current_user.id,
                        Certificate.id == share_in.content_id,
                    )
                )
                .first()
            )
            if not cert_exists:
                raise HTTPException(status_code=404, detail="Certificate not found")

    share = sharing.create_share(
        db,
        current_user.id,
        share_in.share_type,
        share_in.content_id,
        share_in.caption,
        share_in.visibility,
    )

    return schemas.ShareOut(
        id=share.id,
        user_id=share.user_id,
        share_type=share.share_type,
        content_id=share.content_id,
        caption=share.caption,
        visibility=share.visibility,
        share_url=share.share_url,
        view_count=share.view_count,
        created_at=share.created_at,
    )


@app.get("/api/v1/social/shares/mine", response_model=schemas.ShareListOut)
def get_my_shares(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.ShareListOut:
    """
    Get current user's shares.
    """
    from .services import sharing

    shares, total = sharing.get_user_shares(db, current_user.id, page, page_size)

    # Convert to detailed output
    share_details = []
    for share in shares:
        content_data = sharing.get_content_data_for_share(db, share)

        share_detail = schemas.ShareDetailOut(
            id=share.id,
            user_id=current_user.id,
            user_display_name=current_user.display_name or current_user.email,
            user_avatar_url=current_user.avatar_url,
            user_xp=current_user.total_xp,
            share_type=share.share_type,
            content_id=share.content_id,
            content_data=content_data,
            caption=share.caption,
            visibility=share.visibility,
            share_url=share.share_url,
            view_count=share.view_count,
            created_at=share.created_at,
        )
        share_details.append(share_detail)

    return schemas.ShareListOut(
        shares=share_details,
        total=total,
        page=page,
        page_size=page_size,
    )


@app.get("/api/v1/social/shares/{share_id}", response_model=schemas.ShareDetailOut)
def get_share_by_id(
    share_id: UUID,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
) -> schemas.ShareDetailOut:
    """
    Get a share by ID (public endpoint with optional auth).

    Visibility rules:
    - Public shares: Anyone can view
    - Followers shares: Only followers can view
    - Private shares: Only the owner can view
    """
    from .services import sharing

    current_user_id = current_user.id if current_user else None
    share = sharing.get_share_by_id(db, share_id, current_user_id)

    if not share:
        raise HTTPException(status_code=404, detail="Share not found or not accessible")

    # Increment view count (don't count owner's views)
    if not current_user or current_user.id != share.user_id:
        sharing.increment_view_count(db, share_id)

    # Get user info
    user = db.query(User).filter(User.id == share.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    content_data = sharing.get_content_data_for_share(db, share)

    return schemas.ShareDetailOut(
        id=share.id,
        user_id=user.id,
        user_display_name=user.display_name or user.email,
        user_avatar_url=user.avatar_url,
        user_xp=user.total_xp,
        share_type=share.share_type,
        content_id=share.content_id,
        content_data=content_data,
        caption=share.caption,
        visibility=share.visibility,
        share_url=share.share_url,
        view_count=share.view_count,
        created_at=share.created_at,
    )


@app.delete("/api/v1/social/shares/{share_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_share(
    share_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Delete a share (user can only delete their own shares).
    """
    from .services import sharing

    success = sharing.delete_share(db, share_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Share not found or not authorized")

    return Response(status_code=204)


@app.get("/api/v1/users/{user_id}/activity", response_model=schemas.ShareListOut)
def get_user_activity(
    user_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
) -> schemas.ShareListOut:
    """
    Get public activity for a specific user.

    This endpoint shows only public shares.
    """
    from .services import sharing

    # Check if user exists
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    shares, total = sharing.get_public_user_activity(db, user_id, page, page_size)

    # Convert to detailed output
    share_details = []
    for share in shares:
        content_data = sharing.get_content_data_for_share(db, share)

        share_detail = schemas.ShareDetailOut(
            id=share.id,
            user_id=target_user.id,
            user_display_name=target_user.display_name or target_user.email,
            user_avatar_url=target_user.avatar_url,
            user_xp=target_user.total_xp,
            share_type=share.share_type,
            content_id=share.content_id,
            content_data=content_data,
            caption=share.caption,
            visibility=share.visibility,
            share_url=share.share_url,
            view_count=share.view_count,
            created_at=share.created_at,
        )
        share_details.append(share_detail)

    return schemas.ShareListOut(
        shares=share_details,
        total=total,
        page=page,
        page_size=page_size,
    )


# =============================================================================
# Feature Flags and Experiments Endpoints
# =============================================================================


@app.get("/api/v1/features", response_model=schemas.UserFeaturesOut)
def get_user_features(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.UserFeaturesOut:
    """
    Get all feature flags and their status for the current user.

    Returns a mapping of feature keys to their enabled status.
    """
    from backend.services import feature_flags

    features = feature_flags.get_all_features_for_user(db, current_user.id)

    return schemas.UserFeaturesOut(features=features)


@app.get("/api/v1/features/{key}", response_model=schemas.FeatureCheckOut)
def check_feature(
    key: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.FeatureCheckOut:
    """
    Check if a specific feature is enabled for the current user.
    """
    from backend.services import feature_flags

    # Get the feature flag
    flag = db.execute(
        select(FeatureFlag).where(FeatureFlag.key == key)
    ).scalar_one_or_none()

    if not flag:
        raise HTTPException(status_code=404, detail="Feature flag not found")

    enabled = feature_flags.is_feature_enabled_for_user(db, key, current_user.id)

    return schemas.FeatureCheckOut(
        key=key,
        enabled=enabled,
        metadata=flag.rules,
    )


@app.get("/api/v1/experiments", response_model=schemas.UserExperimentsOut)
def get_user_experiments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.UserExperimentsOut:
    """
    Get all active experiments and assigned variants for the current user.

    Returns a mapping of experiment keys to variant keys.
    """
    from backend.services import experiments

    user_experiments = experiments.get_all_experiments_for_user(db, current_user.id)

    return schemas.UserExperimentsOut(experiments=user_experiments)


# =============================================================================
# Admin Endpoints for Feature Flags
# =============================================================================


@app.get("/api/v1/admin/feature-flags", response_model=list[schemas.FeatureFlagOut])
def list_feature_flags(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[schemas.FeatureFlagOut]:
    """
    List all feature flags (admin only).
    """
    flags = db.execute(select(FeatureFlag)).scalars().all()

    return [
        schemas.FeatureFlagOut(
            id=flag.id,
            key=flag.key,
            name=flag.name,
            description=flag.description,
            is_enabled=flag.is_enabled,
            rollout_percentage=flag.rollout_percentage,
            user_whitelist=flag.user_whitelist,
            user_blacklist=flag.user_blacklist,
            rules=flag.rules,
            created_by_id=flag.created_by_id,
            created_at=flag.created_at,
            updated_at=flag.updated_at,
        )
        for flag in flags
    ]


@app.post(
    "/api/v1/admin/feature-flags",
    response_model=schemas.FeatureFlagOut,
    status_code=status.HTTP_201_CREATED,
)
def create_feature_flag(
    payload: schemas.FeatureFlagCreateIn,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> schemas.FeatureFlagOut:
    """
    Create a new feature flag (admin only).
    """
    try:
        flag = FeatureFlag(
            key=payload.key,
            name=payload.name,
            description=payload.description,
            is_enabled=payload.is_enabled,
            rollout_percentage=payload.rollout_percentage,
            user_whitelist=payload.user_whitelist,
            user_blacklist=payload.user_blacklist,
            rules=payload.rules,
            created_by_id=current_user.id,
        )
        db.add(flag)
        db.commit()
        db.refresh(flag)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400, detail="Feature flag with this key already exists"
        )

    return schemas.FeatureFlagOut(
        id=flag.id,
        key=flag.key,
        name=flag.name,
        description=flag.description,
        is_enabled=flag.is_enabled,
        rollout_percentage=flag.rollout_percentage,
        user_whitelist=flag.user_whitelist,
        user_blacklist=flag.user_blacklist,
        rules=flag.rules,
        created_by_id=flag.created_by_id,
        created_at=flag.created_at,
        updated_at=flag.updated_at,
    )


@app.put("/api/v1/admin/feature-flags/{key}", response_model=schemas.FeatureFlagOut)
def update_feature_flag(
    key: str,
    payload: schemas.FeatureFlagUpdateIn,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> schemas.FeatureFlagOut:
    """
    Update a feature flag by key (admin only).
    """
    flag = db.execute(
        select(FeatureFlag).where(FeatureFlag.key == key)
    ).scalar_one_or_none()

    if not flag:
        raise HTTPException(status_code=404, detail="Feature flag not found")

    # Update fields if provided
    if payload.name is not None:
        flag.name = payload.name
    if payload.description is not None:
        flag.description = payload.description
    if payload.is_enabled is not None:
        flag.is_enabled = payload.is_enabled
    if payload.rollout_percentage is not None:
        flag.rollout_percentage = payload.rollout_percentage
    if payload.user_whitelist is not None:
        flag.user_whitelist = payload.user_whitelist
    if payload.user_blacklist is not None:
        flag.user_blacklist = payload.user_blacklist
    if payload.rules is not None:
        flag.rules = payload.rules

    db.commit()
    db.refresh(flag)

    return schemas.FeatureFlagOut(
        id=flag.id,
        key=flag.key,
        name=flag.name,
        description=flag.description,
        is_enabled=flag.is_enabled,
        rollout_percentage=flag.rollout_percentage,
        user_whitelist=flag.user_whitelist,
        user_blacklist=flag.user_blacklist,
        rules=flag.rules,
        created_by_id=flag.created_by_id,
        created_at=flag.created_at,
        updated_at=flag.updated_at,
    )


@app.delete("/api/v1/admin/feature-flags/{key}", status_code=status.HTTP_204_NO_CONTENT)
def delete_feature_flag(
    key: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Delete a feature flag by key (admin only).
    """
    flag = db.execute(
        select(FeatureFlag).where(FeatureFlag.key == key)
    ).scalar_one_or_none()

    if not flag:
        raise HTTPException(status_code=404, detail="Feature flag not found")

    db.delete(flag)
    db.commit()

    return Response(status_code=204)


# =============================================================================
# Admin Endpoints for Experiments
# =============================================================================


@app.get("/api/v1/admin/experiments", response_model=list[schemas.ExperimentOut])
def list_experiments(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[schemas.ExperimentOut]:
    """
    List all experiments (admin only).
    """
    experiments_list = db.execute(select(Experiment)).scalars().all()

    return [
        schemas.ExperimentOut(
            id=exp.id,
            key=exp.key,
            name=exp.name,
            description=exp.description,
            variants=exp.variants,
            is_active=exp.is_active,
            start_date=exp.start_date,
            end_date=exp.end_date,
            created_at=exp.created_at,
        )
        for exp in experiments_list
    ]


@app.post(
    "/api/v1/admin/experiments",
    response_model=schemas.ExperimentOut,
    status_code=status.HTTP_201_CREATED,
)
def create_experiment(
    payload: schemas.ExperimentCreateIn,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> schemas.ExperimentOut:
    """
    Create a new experiment (admin only).
    """
    from backend.services import experiments

    try:
        experiment = experiments.create_experiment(
            db=db,
            key=payload.key,
            name=payload.name,
            variants=payload.variants,
            description=payload.description,
            target_audience=payload.target_audience,
            is_active=payload.is_active,
            start_date=payload.start_date,
            end_date=payload.end_date,
            created_by_id=current_user.id,
        )
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400, detail="Experiment with this key already exists"
        )

    return schemas.ExperimentOut(
        id=experiment.id,
        key=experiment.key,
        name=experiment.name,
        description=experiment.description,
        variants=experiment.variants,
        target_audience=experiment.target_audience,
        is_active=experiment.is_active,
        start_date=experiment.start_date,
        end_date=experiment.end_date,
        created_by_id=experiment.created_by_id,
        created_at=experiment.created_at,
    )


@app.put(
    "/api/v1/admin/experiments/{experiment_id}", response_model=schemas.ExperimentOut
)
def update_experiment(
    experiment_id: UUID,
    payload: schemas.ExperimentUpdateIn,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> schemas.ExperimentOut:
    """
    Update an experiment (admin only).
    """
    from backend.services import experiments

    experiment = experiments.update_experiment(
        db=db,
        experiment_id=experiment_id,
        name=payload.name,
        description=payload.description,
        variants=payload.variants,
        target_audience=payload.target_audience,
        is_active=payload.is_active,
        start_date=payload.start_date,
        end_date=payload.end_date,
    )

    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    db.commit()

    return schemas.ExperimentOut(
        id=experiment.id,
        key=experiment.key,
        name=experiment.name,
        description=experiment.description,
        variants=experiment.variants,
        target_audience=experiment.target_audience,
        is_active=experiment.is_active,
        start_date=experiment.start_date,
        end_date=experiment.end_date,
        created_by_id=experiment.created_by_id,
        created_at=experiment.created_at,
    )


@app.delete(
    "/api/v1/admin/experiments/{experiment_id}", status_code=status.HTTP_204_NO_CONTENT
)
def delete_experiment(
    experiment_id: UUID,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Delete an experiment (admin only).
    """
    experiment = db.get(Experiment, experiment_id)
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    db.delete(experiment)
    db.commit()

    return Response(status_code=204)


@app.get(
    "/api/v1/admin/experiments/{experiment_id}/assignments",
    response_model=list[schemas.UserExperimentAssignmentOut],
)
def get_experiment_assignments(
    experiment_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[schemas.UserExperimentAssignmentOut]:
    """
    Get all user assignments for an experiment (admin only).
    """
    # Verify experiment exists
    experiment = db.get(Experiment, experiment_id)
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    # Get assignments with pagination
    offset = (page - 1) * page_size
    assignments = (
        db.execute(
            select(UserExperimentAssignment)
            .where(UserExperimentAssignment.experiment_id == experiment_id)
            .order_by(UserExperimentAssignment.assigned_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        .scalars()
        .all()
    )

    return [
        schemas.UserExperimentAssignmentOut(
            id=assignment.id,
            user_id=assignment.user_id,
            experiment_id=assignment.experiment_id,
            variant_key=assignment.variant_key,
            assigned_at=assignment.assigned_at,
        )
        for assignment in assignments
    ]


# =============================================================================
# Experiment Events and Analytics Endpoints (P1-EXP-02)
# =============================================================================


@app.post(
    "/api/v1/experiments/{experiment_key}/events",
    response_model=schemas.ExperimentEventOut,
    status_code=status.HTTP_201_CREATED,
)
def track_experiment_event(
    experiment_key: str,
    payload: schemas.ExperimentEventIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.ExperimentEventOut:
    """
    Track an event for an experiment (authenticated users).

    Event types:
    - impression: User saw the variant
    - conversion: User completed the target action
    - click: User clicked on something
    - custom: Custom event
    """
    from backend.services import experiment_analytics

    event = experiment_analytics.track_experiment_event(
        db=db,
        experiment_key=experiment_key,
        user_id=current_user.id,
        event_type=payload.event_type,
        event_name=payload.event_name,
        event_value=payload.event_value,
        metadata=payload.metadata,
    )

    if not event:
        raise HTTPException(
            status_code=404,
            detail="Experiment not found or user not assigned to this experiment",
        )

    db.commit()

    return schemas.ExperimentEventOut(
        id=event.id,
        experiment_id=event.experiment_id,
        user_id=event.user_id,
        assignment_id=event.assignment_id,
        event_type=event.event_type,
        event_name=event.event_name,
        event_value=event.event_value,
        metadata=event.metadata_json,
        created_at=event.created_at,
    )


@app.get(
    "/api/v1/admin/experiments/{experiment_id}/results",
    response_model=schemas.ExperimentResultsOut,
)
def get_experiment_results(
    experiment_id: UUID,
    conversion_event_name: str = Query(
        ..., description="Event name to count as conversion"
    ),
    control_variant_key: str = Query(
        "control", description="Key for the control variant"
    ),
    significance_threshold: float = Query(
        0.05, ge=0.0, le=1.0, description="P-value threshold for significance"
    ),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> schemas.ExperimentResultsOut:
    """
    Get experiment results with statistical analysis (admin only).

    Returns per-variant metrics including:
    - Impressions (assignments)
    - Conversions
    - Conversion rate
    - Statistical significance (p-value)
    - Improvement over control
    - Winning variant (if statistically significant)
    """
    from backend.services import experiment_analytics

    # Verify experiment exists
    experiment = db.get(Experiment, experiment_id)
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    # Generate report
    report = experiment_analytics.generate_experiment_report(
        db=db,
        experiment_id=experiment_id,
        conversion_event_name=conversion_event_name,
        control_variant_key=control_variant_key,
        significance_threshold=significance_threshold,
    )

    if "error" in report:
        raise HTTPException(status_code=400, detail=report["error"])

    # Convert variant stats to schema
    variant_results = {}
    for variant_key, stats in report["variants"].items():
        variant_results[variant_key] = schemas.VariantResultOut(
            variant_key=variant_key,
            impressions=stats["impressions"],
            conversions=stats["conversions"],
            conversion_rate=stats["conversion_rate"],
            p_value=stats.get("p_value"),
            chi_square=stats.get("chi_square"),
            is_significant=stats.get("is_significant", False),
            improvement=stats.get("improvement"),
        )

    return schemas.ExperimentResultsOut(
        experiment_key=report["experiment_key"],
        experiment_name=report["experiment_name"],
        conversion_event=report["conversion_event"],
        variants=variant_results,
        winner=report["winner"],
        is_significant=report["is_significant"],
        significance_threshold=report["significance_threshold"],
    )


@app.get(
    "/api/v1/admin/experiments/{experiment_id}/events",
    response_model=schemas.ExperimentEventListOut,
)
def get_experiment_events(
    experiment_id: UUID,
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    event_name: Optional[str] = Query(None, description="Filter by event name"),
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> schemas.ExperimentEventListOut:
    """
    Get events for an experiment with optional filtering (admin only).
    """
    from backend.models import ExperimentEvent
    from backend.services import experiment_analytics

    # Verify experiment exists
    experiment = db.get(Experiment, experiment_id)
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    # Get total count
    count_query = (
        select(func.count())
        .select_from(ExperimentEvent)
        .where(ExperimentEvent.experiment_id == experiment_id)
    )
    if event_type:
        count_query = count_query.where(ExperimentEvent.event_type == event_type)
    if event_name:
        count_query = count_query.where(ExperimentEvent.event_name == event_name)

    total = db.execute(count_query).scalar() or 0

    # Get events
    offset = (page - 1) * page_size
    events = experiment_analytics.get_experiment_events(
        db=db,
        experiment_id=experiment_id,
        event_type=event_type,
        event_name=event_name,
        limit=page_size,
        offset=offset,
    )

    return schemas.ExperimentEventListOut(
        events=[
            schemas.ExperimentEventOut(
                id=event.id,
                experiment_id=event.experiment_id,
                user_id=event.user_id,
                assignment_id=event.assignment_id,
                event_type=event.event_type,
                event_name=event.event_name,
                event_value=event.event_value,
                metadata=event.metadata_json,
                created_at=event.created_at,
            )
            for event in events
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


# =============================================================================
# Experiment Metric Events Endpoints (P1-EXP-03)
# =============================================================================


@app.post(
    "/api/v1/experiments/{experiment_id}/metrics",
    response_model=schemas.ExperimentMetricEventOut,
    status_code=status.HTTP_201_CREATED,
)
def record_experiment_metric(
    experiment_id: UUID,
    payload: schemas.ExperimentMetricEventIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.ExperimentMetricEventOut:
    """
    Record a metric event for an experiment.

    This endpoint allows authenticated users to track metric values (like conversion,
    retention, engagement scores) for experiments they are assigned to.
    """
    from backend.services import experiment_analytics

    # Verify experiment exists
    experiment = db.get(Experiment, experiment_id)
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    # Record metric event
    metric_event = experiment_analytics.record_metric_event(
        db=db,
        experiment_id=experiment_id,
        user_id=current_user.id,
        metric_name=payload.metric_name,
        metric_value=payload.metric_value,
        metadata=payload.metadata,
    )

    if not metric_event:
        raise HTTPException(
            status_code=400, detail="User is not assigned to this experiment"
        )

    db.commit()

    return schemas.ExperimentMetricEventOut(
        id=metric_event.id,
        experiment_id=metric_event.experiment_id,
        user_id=metric_event.user_id,
        variant=metric_event.variant,
        metric_name=metric_event.metric_name,
        metric_value=metric_event.metric_value,
        metadata=metric_event.metadata_json,
        created_at=metric_event.created_at,
    )


@app.get(
    "/api/v1/admin/experiments/{experiment_id}/metrics",
    response_model=schemas.ExperimentMetricSummaryOut,
)
def get_experiment_metrics_summary(
    experiment_id: UUID,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> schemas.ExperimentMetricSummaryOut:
    """
    Get metric summary for an experiment (admin only).

    Returns a list of all available metrics and basic experiment info.
    """
    from backend.services import experiment_analytics

    # Verify experiment exists
    experiment = db.get(Experiment, experiment_id)
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    # Get all unique metrics for this experiment
    metrics = experiment_analytics.get_all_metrics_for_experiment(
        db=db, experiment_id=experiment_id
    )

    return schemas.ExperimentMetricSummaryOut(
        experiment_id=experiment.id,
        experiment_key=experiment.key,
        experiment_name=experiment.name,
        metrics=metrics,
    )


@app.get(
    "/api/v1/admin/experiments/{experiment_id}/metrics/{metric_name}",
    response_model=schemas.MetricComparisonOut,
)
def get_experiment_metric_comparison(
    experiment_id: UUID,
    metric_name: str,
    control_variant_key: str = Query(
        "control", description="Key for the control variant"
    ),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> schemas.MetricComparisonOut:
    """
    Get detailed metric comparison for a specific metric (admin only).

    Returns aggregated statistics per variant with comparison to control.
    """
    from backend.services import experiment_analytics

    # Verify experiment exists
    experiment = db.get(Experiment, experiment_id)
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    # Get metric comparison
    comparison = experiment_analytics.calculate_metric_comparison(
        db=db,
        experiment_id=experiment_id,
        metric_name=metric_name,
        control_variant_key=control_variant_key,
    )

    # Convert to schema format
    variants_out = {}
    for variant_key, metrics in comparison.get("variants", {}).items():
        variants_out[variant_key] = schemas.VariantMetricSummary(**metrics)

    return schemas.MetricComparisonOut(
        metric_name=comparison["metric_name"],
        control_variant=comparison.get("control_variant"),
        variants=variants_out,
    )


# =============================================================================
# Email Template Management Endpoints (Admin Only)
# =============================================================================


@app.get("/api/v1/admin/email-templates", response_model=schemas.EmailTemplateListOut)
def list_email_templates(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    active_only: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.EmailTemplateListOut:
    """
    List all email templates (admin only).

    Query parameters:
    - page: Page number (default: 1)
    - page_size: Items per page (default: 20, max: 100)
    - active_only: Filter to active templates only
    """
    if current_user.role not in ADMIN_ROLES:
        raise HTTPException(
            status_code=403, detail="Only admins can access email templates"
        )

    # Build query
    query = select(EmailTemplate)

    if active_only:
        query = query.where(EmailTemplate.is_active == True)

    query = query.order_by(EmailTemplate.created_at.desc())

    # Get total count
    count_result = db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar() or 0

    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    templates = db.execute(query).scalars().all()

    return schemas.EmailTemplateListOut(
        templates=[
            schemas.EmailTemplateOut(
                id=t.id,
                key=t.key,
                name=t.name,
                subject_template=t.subject_template,
                body_html=t.body_html,
                body_text=t.body_text,
                is_active=t.is_active,
                created_at=t.created_at,
                updated_at=t.updated_at,
            )
            for t in templates
        ],
        total=total,
    )


@app.post(
    "/api/v1/admin/email-templates",
    response_model=schemas.EmailTemplateOut,
    status_code=201,
)
def create_email_template(
    payload: schemas.EmailTemplateCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.EmailTemplateOut:
    """
    Create a new email template (admin only).
    """
    if current_user.role not in ADMIN_ROLES:
        raise HTTPException(
            status_code=403, detail="Only admins can create email templates"
        )

    # Check if key already exists
    existing = db.execute(
        select(EmailTemplate).where(EmailTemplate.key == payload.key)
    ).scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=400, detail=f"Template with key '{payload.key}' already exists"
        )

    # Create template
    template = EmailTemplate(
        key=payload.key,
        name=payload.name,
        subject_template=payload.subject_template,
        body_html=payload.body_html,
        body_text=payload.body_text,
        is_active=payload.is_active,
    )

    db.add(template)
    db.commit()
    db.refresh(template)

    return schemas.EmailTemplateOut(
        id=template.id,
        key=template.key,
        name=template.name,
        subject_template=template.subject_template,
        body_html=template.body_html,
        body_text=template.body_text,
        is_active=template.is_active,
        created_at=template.created_at,
        updated_at=template.updated_at,
    )


@app.put(
    "/api/v1/admin/email-templates/{template_id}",
    response_model=schemas.EmailTemplateOut,
)
def update_email_template(
    template_id: UUID,
    payload: schemas.EmailTemplateUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.EmailTemplateOut:
    """
    Update an email template (admin only).
    """
    if current_user.role not in ADMIN_ROLES:
        raise HTTPException(
            status_code=403, detail="Only admins can update email templates"
        )

    template = db.get(EmailTemplate, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    # Update fields
    if payload.name is not None:
        template.name = payload.name
    if payload.subject_template is not None:
        template.subject_template = payload.subject_template
    if payload.body_html is not None:
        template.body_html = payload.body_html
    if payload.body_text is not None:
        template.body_text = payload.body_text
    if payload.is_active is not None:
        template.is_active = payload.is_active

    db.commit()
    db.refresh(template)

    return schemas.EmailTemplateOut(
        id=template.id,
        key=template.key,
        name=template.name,
        subject_template=template.subject_template,
        body_html=template.body_html,
        body_text=template.body_text,
        is_active=template.is_active,
        created_at=template.created_at,
        updated_at=template.updated_at,
    )


# =============================================================================
# Scheduled Email Endpoints (Admin Only)
# =============================================================================


@app.get("/api/v1/admin/scheduled-emails", response_model=schemas.ScheduledEmailListOut)
def list_scheduled_emails(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None),
    user_id: Optional[UUID] = Query(None),
    template_id: Optional[UUID] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.ScheduledEmailListOut:
    """
    List scheduled emails (admin only).

    Query parameters:
    - page: Page number
    - page_size: Items per page
    - status_filter: Filter by status (pending, sent, failed, cancelled)
    - user_id: Filter by user ID
    - template_id: Filter by template ID
    """
    if current_user.role not in ADMIN_ROLES:
        raise HTTPException(
            status_code=403, detail="Only admins can access scheduled emails"
        )

    # Build query
    query = select(ScheduledEmail).options(selectinload(ScheduledEmail.template))

    if status_filter:
        try:
            status_enum = EmailStatus(status_filter)
            query = query.where(ScheduledEmail.status == status_enum)
        except ValueError:
            raise HTTPException(
                status_code=400, detail=f"Invalid status: {status_filter}"
            )

    if user_id:
        query = query.where(ScheduledEmail.user_id == user_id)

    if template_id:
        query = query.where(ScheduledEmail.template_id == template_id)

    query = query.order_by(ScheduledEmail.scheduled_for.desc())

    # Get total count
    count_result = db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar() or 0

    # Get status counts
    status_counts_result = db.execute(
        select(ScheduledEmail.status, func.count(ScheduledEmail.id)).group_by(
            ScheduledEmail.status
        )
    ).all()

    status_counts = {str(status.value): count for status, count in status_counts_result}

    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    emails = db.execute(query).scalars().all()

    return schemas.ScheduledEmailListOut(
        emails=[
            schemas.ScheduledEmailOut(
                id=e.id,
                user_id=e.user_id,
                template_id=e.template_id,
                template_key=e.template.key if e.template else None,
                template_name=e.template.name if e.template else None,
                scheduled_for=e.scheduled_for,
                status=e.status.value,
                context_data=e.context_data,
                sent_at=e.sent_at,
                error_message=e.error_message,
                created_at=e.created_at,
            )
            for e in emails
        ],
        total=total,
        status_counts=status_counts,
    )


@app.post(
    "/api/v1/admin/scheduled-emails/send-test", response_model=schemas.SendTestEmailOut
)
def send_test_email(
    payload: schemas.SendTestEmailIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.SendTestEmailOut:
    """
    Send a test email using a template (admin only).

    This creates a scheduled email record for testing purposes.
    In production, you would integrate with an actual email service (e.g., SendGrid, AWS SES).
    """
    if current_user.role not in ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Only admins can send test emails")

    # Get template
    template = db.get(EmailTemplate, payload.template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    # Import email scheduler service
    from .services import email_scheduler

    try:
        # Render template with test context
        subject, body_html, body_text = email_scheduler.render_email_template(
            template, payload.context_data
        )

        # Create a test scheduled email record
        # In production, this would actually send the email
        test_email = ScheduledEmail(
            user_id=current_user.id,  # Send to current admin
            template_id=template.id,
            scheduled_for=datetime.now(timezone.utc),
            status=EmailStatus.pending,
            context_data=payload.context_data,
        )

        db.add(test_email)
        db.commit()
        db.refresh(test_email)

        # Mark as sent immediately for testing
        # In production, this would be done by the email worker
        email_scheduler.mark_email_sent(db, test_email.id)

        return schemas.SendTestEmailOut(
            success=True,
            message=f"Test email rendered successfully. Subject: {subject}",
            scheduled_email_id=test_email.id,
        )

    except Exception as e:
        logger.error(f"Failed to send test email: {e}")
        return schemas.SendTestEmailOut(
            success=False,
            message=f"Failed to render template: {str(e)}",
        )
