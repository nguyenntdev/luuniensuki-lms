from __future__ import annotations

import json
import logging
import math
import re
import unicodedata
import uuid as uuid_module
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional
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
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator
from sqlalchemy import create_engine, delete, func, or_, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload, sessionmaker
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.cors import CORSMiddleware

from .config import settings
from .errors import (
    AppError,
    app_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from .models import (
    AIJob,
    AnalyticsEvent,
    AssignmentProgress,
    Badge,
    BadgeCategory,
    Certificate,
    ClassMember,
    Classroom,
    ContentFlag,
    ContentProvenance,
    LessonContent,
    Motif,
    MotifCategory,
    Quest,
    QuestAssignment,
    QuestionType,
    QuestObjective,
    QuestProgress,
    QuestReward,
    QuestStep,
    QuizAttempt,
    QuizQuestion,
    Recommendation,
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
CERTIFICATE_ISSUER_NAME = "Lưu Niên Sử Kí"

USERNAME_REGEX = re.compile(r"^[a-zA-Z0-9_]{3,20}$")

AVATAR_UPLOAD_DIR = Path("/app/uploads/avatars")
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_AVATAR_SIZE = 5 * 1024 * 1024

STAFF_ROLES = {UserRole.teacher, UserRole.admin, UserRole.super_admin}
ADMIN_ROLES = {UserRole.admin, UserRole.super_admin}

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

# Add CORS middleware to allow cross-origin requests from mobile app
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

    can_view_drafts = _can_view_drafts(current_user)
    lesson_out = (
        LessonContentOut.model_validate(motif.lesson)
        if motif.lesson and (motif.lesson.is_published or can_view_drafts)
        else None
    )

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
        quiz_question_count=len(
            [
                q
                for q in motif.quiz_questions
                if q.is_active and (q.is_published or can_view_drafts)
            ]
        ),
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


class ClassMemberOut(BaseModel):
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


class ClassSummaryOut(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    teacher_id: UUID
    created_at: datetime
    member_count: int
    assignment_count: int


class ClassDetailOut(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    teacher_id: UUID
    created_at: datetime
    members: list[ClassMemberOut]
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


@app.get("/api/v1/classes", response_model=list[ClassSummaryOut])
def list_classes(
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db),
) -> list[ClassSummaryOut]:
    query = select(Classroom)
    if current_user.role == UserRole.teacher:
        query = query.where(Classroom.teacher_id == current_user.id)

    classes = db.execute(query.order_by(Classroom.created_at.desc())).scalars().all()
    if not classes:
        return []

    class_ids = [c.id for c in classes]
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
        ClassSummaryOut(
            id=classroom.id,
            name=classroom.name,
            description=classroom.description,
            teacher_id=classroom.teacher_id,
            created_at=classroom.created_at,
            member_count=int(member_counts.get(classroom.id, 0)),
            assignment_count=int(assignment_counts.get(classroom.id, 0)),
        )
        for classroom in classes
    ]


@app.post("/api/v1/classes", response_model=ClassSummaryOut, status_code=201)
def create_class(
    payload: ClassCreateRequest,
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db),
) -> ClassSummaryOut:
    teacher_id = current_user.id
    if current_user.role in ADMIN_ROLES and current_user.role != UserRole.teacher:
        teacher_id = current_user.id

    classroom = Classroom(
        name=payload.name,
        description=payload.description,
        teacher_id=teacher_id,
    )
    db.add(classroom)
    db.commit()
    db.refresh(classroom)

    return ClassSummaryOut(
        id=classroom.id,
        name=classroom.name,
        description=classroom.description,
        teacher_id=classroom.teacher_id,
        created_at=classroom.created_at,
        member_count=0,
        assignment_count=0,
    )


@app.get("/api/v1/classes/{class_id}", response_model=ClassDetailOut)
def get_class_detail(
    class_id: UUID,
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db),
) -> ClassDetailOut:
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

    return ClassDetailOut(
        id=classroom.id,
        name=classroom.name,
        description=classroom.description,
        teacher_id=classroom.teacher_id,
        created_at=classroom.created_at,
        members=[
            ClassMemberOut(
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


@app.post("/api/v1/classes/{class_id}/members", response_model=ClassDetailOut)
def add_class_member(
    class_id: UUID,
    payload: ClassMemberAddRequest,
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db),
) -> ClassDetailOut:
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
    "/api/v1/classes/{class_id}/members/{user_id}", response_model=ClassDetailOut
)
def remove_class_member(
    class_id: UUID,
    user_id: UUID,
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db),
) -> ClassDetailOut:
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


@app.post("/api/v1/classes/{class_id}/assignments", response_model=ClassDetailOut)
def assign_quest_to_class(
    class_id: UUID,
    payload: AssignmentCreateRequest,
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db),
) -> ClassDetailOut:
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
    display_order: Optional[int] = None
    status: str


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
                display_order=motif.display_order,
                status=(
                    progress_by_id[motif.id].status.value
                    if motif.id in progress_by_id
                    else UnlockStatus.hidden.value
                ),
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

    for field, value in payload.model_dump(exclude_unset=True).items():
        if field == "is_published" and current_user.role not in ADMIN_ROLES:
            continue
        setattr(lesson, field, value)

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
        created_at=question.created_at,
    )


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
            .where(User.role == UserRole.learner)
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
    options: Optional[list[Any]] = None
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
            current_user.total_xp += delta

        if int(mastered_before or 0) == 0:
            badge_attempts.append(BADGE_FIRST_MASTERED)
            badge_bonus += _award_badge(
                db, user=current_user, badge_slug=BADGE_FIRST_MASTERED
            )

    _update_streak(current_user, now)
    if current_user.current_streak >= 7:
        badge_attempts.append(BADGE_STREAK_7)
        badge_bonus += _award_badge(db, user=current_user, badge_slug=BADGE_STREAK_7)

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


def _call_deepseek(prompt: str) -> str:
    if not settings.deepseek_api_key:
        raise RuntimeError("Deepseek API key not configured")

    url = settings.deepseek_base_url.rstrip("/") + "/v1/chat/completions"
    payload = {
        "model": settings.deepseek_model,
        "messages": [
            {
                "role": "system",
                "content": "You generate concise learning recommendations in JSON.",
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
    }
    data = json.dumps(payload).encode("utf-8")
    request = UrlRequest(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.deepseek_api_key}",
        },
    )

    try:
        with urlopen(request, timeout=settings.deepseek_timeout_seconds) as response:
            body = response.read().decode("utf-8")
    except (HTTPError, URLError) as exc:
        raise RuntimeError(f"Deepseek request failed: {exc}") from exc

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

    content = _call_deepseek(prompt)
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
