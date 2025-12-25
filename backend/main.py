from __future__ import annotations

import logging
import math
import re
import unicodedata
import uuid as uuid_module
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional
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
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import create_engine, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload, sessionmaker
from starlette.exceptions import HTTPException as StarletteHTTPException

from .errors import (
    AppError,
    app_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from .models import (
    AnalyticsEvent,
    Badge,
    BadgeCategory,
    LessonContent,
    Motif,
    MotifCategory,
    QuestionType,
    QuizAttempt,
    QuizQuestion,
    UnlockStatus,
    Urn,
    UrnExam,
    UrnExamAttempt,
    User,
    UserBadge,
    UserProgress,
    UserRole,
)
from .security import create_jwt_token, hash_password, verify_password

DISCOVERY_XP = 25
LESSON_XP = 50
MASTERED_XP = 75
QUIZ_PASS_PERCENT = 80
URN_EXAM_PASS_PERCENT = 80
URN_EXAM_PASS_XP = 300
URN_EXAM_QUESTION_COUNT = 15

USERNAME_REGEX = re.compile(r"^[a-zA-Z0-9_]{3,20}$")

AVATAR_UPLOAD_DIR = Path("/app/uploads/avatars")
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_AVATAR_SIZE = 5 * 1024 * 1024

BADGE_FIRST_DISCOVERY = "first-discovery"
BADGE_FIRST_MASTERED = "first-mastered"
BADGE_STREAK_7 = "streak-7"
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


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://postgres:postgres@db:5432/luuniensuki"
    log_level: str = "info"
    interaction_tolerance_multiplier: float = 1.25
    jwt_secret_key: str = "dev-insecure-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 30
    access_cookie_name: str = "luuniensuki_access"
    refresh_cookie_name: str = "luuniensuki_refresh"
    cookie_domain: Optional[str] = None
    cookie_secure: bool = False
    cookie_samesite: str = "lax"
    cookie_path: str = "/"

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
app.add_exception_handler(AppError, app_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

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
) -> None:
    try:
        session.add(
            AnalyticsEvent(
                user_id=user_id,
                event_name=name,
                payload=payload,
                path=path,
            )
        )
        session.commit()
    except Exception:
        session.rollback()
        logger.warning("Failed to record analytics event", exc_info=True)


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

    session.add(UserBadge(user_id=user.id, badge_id=badge.id))
    bonus = int(badge.xp_bonus or 0)
    if bonus:
        user.total_xp += bonus
    session.flush()
    return bonus


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
        "secure": settings.cookie_secure,
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

    try:
        payload = jwt.decode(
            raw_token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        subject = payload.get("sub")
        token_type = payload.get("type")
        if not subject or token_type != "access":
            raise credentials_exception
        user_id = UUID(subject)
    except (JWTError, ValueError):
        raise credentials_exception

    user = db.get(User, user_id)
    if user is None:
        raise credentials_exception
    return user


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
        extra_claims={"type": "access"},
    )
    refresh_token = create_jwt_token(
        subject=str(user.id),
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        expires_delta=timedelta(days=settings.refresh_token_expire_days),
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
        extra_claims={"type": "access"},
    )
    refresh_token = create_jwt_token(
        subject=str(user.id),
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        expires_delta=timedelta(days=settings.refresh_token_expire_days),
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
        payload = jwt.decode(
            raw_token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        subject = payload.get("sub")
        token_type = payload.get("type")
        if not subject or token_type != "refresh":
            raise credentials_exception
        user_id = UUID(subject)
    except (JWTError, ValueError):
        raise credentials_exception

    user = db.get(User, user_id)
    if user is None:
        raise credentials_exception

    access_token = create_jwt_token(
        subject=str(user.id),
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
        extra_claims={"type": "access"},
    )
    refresh_token = create_jwt_token(
        subject=str(user.id),
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        expires_delta=timedelta(days=settings.refresh_token_expire_days),
        extra_claims={"type": "refresh"},
    )

    _set_auth_cookies(response, access_token=access_token, refresh_token=refresh_token)
    response.headers["Cache-Control"] = "no-store"
    return _build_auth_me_response(user)


@app.post("/api/v1/auth/logout")
def logout(response: Response) -> dict[str, bool]:
    _clear_auth_cookies(response)
    response.headers["Cache-Control"] = "no-store"
    return {"success": True}


class UpdateProfileRequest(BaseModel):
    display_name: Optional[str] = Field(None, min_length=2, max_length=100)
    username: Optional[str] = None
    bio: Optional[str] = Field(None, max_length=500)
    is_profile_public: Optional[bool] = None


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


class AnalyticsEventIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    payload: Optional[dict[str, Any]] = None
    path: Optional[str] = None


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

    db.add_all(
        [
            AnalyticsEvent(
                user_id=current_user.id,
                event_name=event.name,
                payload=event.payload,
                path=event.path,
            )
            for event in payload.events
        ]
    )
    db.commit()
    return AnalyticsEventsOut(success=True, count=len(payload.events))


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


@app.get("/api/v1/urns", response_model=list[UrnListItemOut])
def list_urns(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[UrnListItemOut]:
    motif_counts = (
        select(Motif.urn_id, func.count(Motif.id).label("motif_count"))
        .where(Motif.is_active.is_(True))
        .group_by(Motif.urn_id)
        .subquery()
    )

    rows = db.execute(
        select(Urn, func.coalesce(motif_counts.c.motif_count, 0))
        .outerjoin(motif_counts, motif_counts.c.urn_id == Urn.id)
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
        )
        for urn, motif_count in rows
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
                lesson_intro=(m.lesson.intro_text if m.lesson else None),
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
    is_demo: bool
    display_order: Optional[int] = None
    lesson: Optional[LessonContentOut] = None
    quiz_question_count: int = 0


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

    lesson_out = LessonContentOut.model_validate(motif.lesson) if motif.lesson else None

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
        is_demo=motif.is_demo,
        display_order=motif.display_order,
        lesson=lesson_out,
        quiz_question_count=len([q for q in motif.quiz_questions if q.is_active]),
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
        current_user.total_xp += target_xp
        xp_awarded = target_xp
    else:
        if progress.status in (UnlockStatus.hidden, UnlockStatus.discovered):
            progress.status = UnlockStatus.learned
            progress.learned_at = progress.learned_at or now
            progress.discovered_at = progress.discovered_at or now

        progress.lesson_viewed_at = progress.lesson_viewed_at or now

        if progress.xp_earned < target_xp:
            delta = target_xp - progress.xp_earned
            progress.xp_earned = target_xp
            current_user.total_xp += delta
            xp_awarded = delta

    badge_bonus = 0
    _update_streak(current_user, now)
    if was_locked and int(discovered_before or 0) == 0:
        badge_bonus += _award_badge(
            db, user=current_user, badge_slug=BADGE_FIRST_DISCOVERY
        )
    if current_user.current_streak >= 7:
        badge_bonus += _award_badge(db, user=current_user, badge_slug=BADGE_STREAK_7)

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
            current_user.total_xp += delta
            xp_awarded = max(xp_awarded, delta)
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


class ProgressUnlockResponse(BaseModel):
    user_id: UUID
    motif_id: UUID
    status: str
    discovered_at: Optional[datetime] = None
    xp_awarded: int
    total_xp: int


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
    _update_streak(user, now)
    if was_locked and int(discovered_before or 0) == 0:
        badge_bonus += _award_badge(db, user=user, badge_slug=BADGE_FIRST_DISCOVERY)
    if user.current_streak >= 7:
        badge_bonus += _award_badge(db, user=user, badge_slug=BADGE_STREAK_7)

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
        badge_bonus += _award_badge(db, user=user, badge_slug=BADGE_COLLECTOR_10)
    if discovered >= 50:
        badge_bonus += _award_badge(db, user=user, badge_slug=BADGE_COLLECTOR_50)
    if urns >= 9:
        badge_bonus += _award_badge(db, user=user, badge_slug=BADGE_EXPLORER_ALL_URNS)

    user.last_active_at = now

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        logger.warning(
            "IntegrityError during unlock; retrying fetch/update", exc_info=True
        )
        badge_bonus = 0
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
        _update_streak(user, now)
        if was_locked and int(discovered_before or 0) == 0:
            badge_bonus += _award_badge(db, user=user, badge_slug=BADGE_FIRST_DISCOVERY)
        if user.current_streak >= 7:
            badge_bonus += _award_badge(db, user=user, badge_slug=BADGE_STREAK_7)
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
            badge_bonus += _award_badge(db, user=user, badge_slug=BADGE_COLLECTOR_10)
        if discovered >= 50:
            badge_bonus += _award_badge(db, user=user, badge_slug=BADGE_COLLECTOR_50)
        if urns >= 9:
            badge_bonus += _award_badge(
                db, user=user, badge_slug=BADGE_EXPLORER_ALL_URNS
            )
        user.last_active_at = now
        db.commit()

    return ProgressUnlockResponse(
        user_id=user.id,
        motif_id=motif.id,
        status=progress.status.value,
        discovered_at=progress.discovered_at,
        xp_awarded=xp_awarded + badge_bonus,
        total_xp=user.total_xp,
    )


@app.post("/api/v1/users/me/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        if file.content_type not in ALLOWED_IMAGE_TYPES:
            raise AppError(
                code="INVALID_IMAGE_TYPE",
                message="Unsupported image type",
                status_code=status.HTTP_400_BAD_REQUEST,
                details={"content_type": file.content_type},
            )

        contents = await file.read(MAX_AVATAR_SIZE + 1)
        if len(contents) > MAX_AVATAR_SIZE:
            raise AppError(
                code="AVATAR_TOO_LARGE",
                message="Avatar file too large",
                status_code=status.HTTP_400_BAD_REQUEST,
                details={"max_bytes": MAX_AVATAR_SIZE},
            )

        extension_by_type = {
            "image/jpeg": "jpg",
            "image/png": "png",
            "image/webp": "webp",
        }
        extension = extension_by_type[file.content_type]
        filename = f"{current_user.id}_{uuid_module.uuid4()}.{extension}"

        AVATAR_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        destination = AVATAR_UPLOAD_DIR / filename
        with destination.open("wb") as handle:
            handle.write(contents)

        current_user.avatar_url = f"/assets/avatars/{filename}"
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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(request.current_password, current_user.password_hash):
        raise HTTPException(400, "Current password is incorrect")

    current_user.password_hash = hash_password(request.new_password)
    db.commit()
    return {"message": "Password changed successfully"}


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


class BadgeOut(BaseModel):
    slug: str
    name: str
    description: Optional[str] = None
    icon_url: str
    category: str
    xp_bonus: int


class UserBadgeOut(BaseModel):
    badge: BadgeOut
    earned_at: datetime


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
            ),
            earned_at=ub.earned_at,
        )
        for ub in badges
    ]


class LeaderboardEntryOut(BaseModel):
    rank: int
    user_id: UUID
    display_name: str
    avatar_url: Optional[str] = None
    total_xp: int
    title: str


@app.get("/api/v1/leaderboard", response_model=list[LeaderboardEntryOut])
def get_leaderboard(
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[LeaderboardEntryOut]:
    users = (
        db.execute(
            select(User)
            .where(User.role != UserRole.guest)
            .order_by(User.total_xp.desc(), User.created_at.asc())
            .limit(limit)
        )
        .scalars()
        .all()
    )

    entries: list[LeaderboardEntryOut] = []
    for idx, user in enumerate(users, start=1):
        current_rank, _, _ = _compute_rank(user.total_xp)
        entries.append(
            LeaderboardEntryOut(
                rank=idx,
                user_id=user.id,
                display_name=user.display_name,
                avatar_url=user.avatar_url,
                total_xp=user.total_xp,
                title=str(current_rank["name"]),
            )
        )
    return entries


class QuizQuestionOut(BaseModel):
    id: UUID
    question_type: str
    question_text: str
    options: Optional[list[str]] = None
    target_mesh_name: Optional[str] = None
    difficulty: int


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

    questions = (
        db.execute(
            select(QuizQuestion)
            .where(QuizQuestion.motif_id == motif.id, QuizQuestion.is_active.is_(True))
            .order_by(QuizQuestion.created_at.asc())
        )
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
                options=[str(opt) for opt in q.options]
                if isinstance(q.options, list)
                else None,
                target_mesh_name=q.target_mesh_name,
                difficulty=max(1, int(q.difficulty or 1)),
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

    questions = (
        db.execute(
            select(QuizQuestion)
            .where(QuizQuestion.motif_id == motif.id, QuizQuestion.is_active.is_(True))
            .order_by(QuizQuestion.created_at.asc())
        )
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

    percentage = int(round((score / max_score) * 100)) if max_score > 0 else 0
    passed = percentage >= QUIZ_PASS_PERCENT

    total_xp_before = current_user.total_xp
    now = datetime.now(timezone.utc)

    progress.quiz_attempts += 1
    progress.quiz_best_score = max(progress.quiz_best_score, percentage)

    badge_bonus = 0
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
            current_user.total_xp += delta

        if int(mastered_before or 0) == 0:
            badge_bonus += _award_badge(
                db, user=current_user, badge_slug=BADGE_FIRST_MASTERED
            )

    _update_streak(current_user, now)
    if current_user.current_streak >= 7:
        badge_bonus += _award_badge(db, user=current_user, badge_slug=BADGE_STREAK_7)

    # Check quiz badges
    if percentage == 100:
        badge_bonus += _award_badge(
            db, user=current_user, badge_slug=BADGE_PERFECT_SCORE
        )
    if payload.time_taken_seconds is not None and payload.time_taken_seconds <= 30:
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
    except IntegrityError:
        db.rollback()
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


def _select_urn_exam_questions(db: Session, *, urn: Urn) -> list[QuizQuestion]:
    urn_questions = (
        db.execute(
            select(QuizQuestion)
            .where(QuizQuestion.urn_id == urn.id, QuizQuestion.is_active.is_(True))
            .order_by(QuizQuestion.created_at.asc(), QuizQuestion.id.asc())
        )
        .scalars()
        .all()
    )
    if len(urn_questions) >= URN_EXAM_QUESTION_COUNT:
        return urn_questions[:URN_EXAM_QUESTION_COUNT]

    motif_questions = (
        db.execute(
            select(QuizQuestion)
            .join(Motif, QuizQuestion.motif_id == Motif.id)
            .where(
                Motif.urn_id == urn.id,
                QuizQuestion.is_active.is_(True),
                QuizQuestion.urn_id.is_(None),
            )
            .order_by(QuizQuestion.created_at.asc(), QuizQuestion.id.asc())
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

    questions = _select_urn_exam_questions(db, urn=urn)
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
                options=[str(opt) for opt in q.options]
                if isinstance(q.options, list)
                else None,
                target_mesh_name=q.target_mesh_name,
                difficulty=max(1, int(q.difficulty or 1)),
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


class UrnExamSubmitResponse(BaseModel):
    urn_id: UUID
    score: int
    max_score: int
    percentage: int
    passed: bool
    xp_awarded: int
    total_xp: int
    results: list[UrnExamResultDetail]


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

    questions = _select_urn_exam_questions(db, urn=urn)
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
    )


class UrnExamAttemptOut(BaseModel):
    id: UUID
    urn_id: UUID
    urn_slug: str
    urn_name: str
    score: int
    passed: bool
    created_at: datetime


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
