# -*- coding: utf-8 -*-
"""Neutral helper module for the modularized backend (backend-modularization).

This module hosts the module-level helper functions and constants that were
previously defined inline in ``backend.main`` and are shared across the
extracted router modules. Relocating them here lets every router import what it
needs without importing ``backend.main`` (which would create an import cycle):
the import direction stays one-way ``main -> app -> routers -> domain.helpers``.

STRICTLY behavior-preserving: every helper body and constant value is moved
verbatim from ``backend.main``. The only adjusted line is ``REPO_ROOT`` whose
``parents`` index is corrected for this module's deeper location so the resolved
filesystem path is identical to before.

Import direction is one-way: this module imports only shared building blocks
(config, db, models, schemas, apischemas, services, domain.*); it never imports
``backend.main``/``backend.app``/``backend.routers``.
"""


import hashlib
import json
import logging
import math
import re
import secrets
import socket
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
    Header,
    HTTPException,
    Query,
    Request,
    Response,
    UploadFile,
    status,
)
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, RedirectResponse, StreamingResponse
from fastapi.security import OAuth2PasswordBearer
from fastapi.staticfiles import StaticFiles
from jose import JWTError, jwt
from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator
from sqlalchemy import and_, case, create_engine, delete, func, or_, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload, sessionmaker
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.cors import CORSMiddleware

from .. import schemas
from ..config import settings
from ..db import engine, SessionLocal, get_db
from ..deps import (
    oauth2_scheme,
    _jwt_decode_kwargs,
    _decode_access_token,
    get_current_user,
    get_current_user_optional,
    _ensure_owner_or_404,
    _can_view_drafts,
    _require_roles,
    get_staff_user,
    get_admin_user,
    require_admin,
    get_super_admin_user,
    require_feature,
)
from .gamification import (
    CERTIFICATE_ISSUER_NAME,
    XP_RANKS,
    _apply_xp_boost,
    _award_badge,
    _compute_rank,
    _issue_certificate,
    _update_streak,
)
from .auth_session import (
    _build_auth_me_response,
    _clear_auth_cookies,
    _cookie_params,
    _decode_refresh_token_best_effort,
    _is_refresh_revoked,
    _revoke_refresh_jti,
    _set_auth_cookies,
)
from ..apischemas.auth import (
    AuthLoginRequest,
    AuthMeResponse,
    AuthRegisterRequest,
    ChangePasswordRequest,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    RankOut,
    ResetPasswordRequest,
    ResetPasswordResponse,
    UserOut,
    UserStatsOut,
)
from ..apischemas.users import (
    OnboardingCompleteResponse,
    OnboardingGoalRequest,
    OnboardingStatusResponse,
    PublicBadgeOut,
    PublicMotifOut,
    StartingPathRequest,
    StartingPathResponse,
    UpdateProfileRequest,
    UpdateProfileResponse,
    UserPublicProfile,
    UserPublicStatsOut,
)
from ..apischemas.content import (
    AnalyticsEventIn,
    AnalyticsEventsIn,
    AnalyticsEventsOut,
    BadgeResponseDto,
    CertificateOut,
    CertificateSummaryOut,
    CertificateVerifyOut,
    ContentTagCreateIn,
    ContentTagOut,
    LessonCompleteResponse,
    LessonContentOut,
    MotifDetailOut,
    MotifOut,
    MotifProgressOut,
    MotifQuizQuestionOut,
    MotifQuizResponse,
    MotifsByUrnResponse,
    ProgressResponseDto,
    ProgressUnlockRequest,
    ProgressUnlockResponse,
    QuizAnswerIn,
    QuizQuestionOut,
    QuizResultDetail,
    QuizSubmitRequest,
    QuizSubmitResponse,
    SearchRequest,
    SearchResponse,
    SearchResultItem,
    TagCreateIn,
    TagOut,
    TapPosition,
    UrnDetailOut,
    UrnDetailResponse,
    UrnExamAttemptOut,
    UrnExamAttemptPayloadOut,
    UrnExamAttemptResultOut,
    UrnExamResponse,
    UrnExamResultDetail,
    UrnExamSnapshotOut,
    UrnExamSubmitRequest,
    UrnExamSubmitResponse,
    UrnListItemOut,
    UrnOut,
    UrnProgressResponse,
    UserProgressDetailOut,
)
from ..apischemas.quests import (
    CollectionItemOut,
    CollectionStatsOut,
    QuestCertificateOut,
    QuestDetailOut,
    QuestListItemOut,
    QuestObjectiveOut,
    QuestPrerequisiteOut,
    QuestProgressOut,
    QuestRewardOut,
    QuestStepOut,
    QuestSummaryObjectiveOut,
    QuestSummaryOut,
    UserCollectionResponse,
)
from ..apischemas.ai import (
    AIAnswerOut,
    AIChatMessage,
    AICitationOut,
    AIContextIn,
    AIJobOut,
    AIQuestionRequest,
    AITutorRequest,
    CoachGenerateIn,
    CoachGenerateOut,
    DiagnosticGenerateIn,
    DiagnosticGenerateOut,
    DiagnosticQuestionOut,
    ExplainGenerateIn,
    ExplainGenerateOut,
    FeedbackGenerateIn,
    FeedbackGenerateOut,
    FlashcardGenerateIn,
    FlashcardGenerateOut,
    FlashcardOut,
    LessonGenerateIn,
    LessonGenerateOut,
    QuizGenerateIn,
    QuizGenerateOut,
    RecommendationAIOut,
    RecommendationItemOut,
    RecommendationOut,
    RecommendationRefreshRequest,
    ReviewPlanItem,
    ReviewPlanOut,
    SeedUrnIn,
    SeedUrnOut,
    SeedUrnResult,
    SummaryGenerateIn,
    SummaryGenerateOut,
)
from ..apischemas.progress import (
    BadgeListItemOut,
    BadgeOut,
    ClaimDailyStreakOut,
    DailyGoalSettingsOut,
    DailyGoalSettingsUpdateIn,
    DailyMissionHistoryItem,
    DailyMissionHistoryResponse,
    DailyMissionOut,
    DailyMissionsResponse,
    DashboardPathMotifOut,
    DashboardSummaryOut,
    PeerFeedbackOut,
    PeerFeedbackSendIn,
    RankListItemOut,
    StreakFreezeResponse,
    StreakMilestoneOut,
    StreakResponse,
    StreakStatusOut,
    UpdateMissionProgressRequest,
    UpdateMissionProgressResponse,
    UseStreakFreezeOut,
    UserBadgeOut,
    UserDailyMissionOut,
)
from ..apischemas.admin import (
    AdminLessonCreateRequest,
    AdminLessonOut,
    AdminLessonUpdateRequest,
    AdminQuizQuestionCreateRequest,
    AdminQuizQuestionOut,
    AdminQuizQuestionUpdateRequest,
    AssignmentCreateRequest,
    AssignmentSummaryOut,
    ClassCreateRequest,
    ClassDetailOut_Legacy,
    ClassMemberAddRequest,
    ClassMemberOut_Legacy,
    ClassSummaryOut_Legacy,
    ContentFlagCreateRequest,
    ContentFlagOut,
    ContentVersionListOut,
    ContentVersionOut,
    EmbeddingJobOut,
    EmbeddingRebuildRequest,
    HealthResponse,
    LeaderboardEntryOut,
    RagEmbeddingRebuildOut,
    RagHealthOut,
    RevertContentIn,
)
from ..errors import (
    AppError,
    app_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from ..models import (
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
    LiveParticipant,
    LiveEvent,
    LiveSession,
    LiveSessionStatus,
    NotificationStatus,
    NotificationType,
    PasswordResetToken,
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
from ..rag_defaults import get_rag_defaults
from ..provision_live_demo import run_provision
from ..rbac import ADMIN_ROLES, STAFF_ROLES
from ..security import create_jwt_token, hash_password, verify_password
from ..services.daily_goal_settings import (
    DAILY_GOAL_DEFAULT_LEVEL,
    DAILY_GOAL_LEVELS,
    get_user_daily_goal_settings,
    resolve_daily_goal_level,
    save_user_daily_goal_settings,
)


# Use the same named logger as ``backend.main`` so log output is unchanged.
logger = logging.getLogger("luuniensuki.api")


DISCOVERY_XP = 25


LESSON_XP = 50


MASTERED_XP = 75


QUIZ_PASS_PERCENT = 80


URN_EXAM_PASS_PERCENT = 80


URN_EXAM_PASS_XP = 300


URN_EXAM_QUESTION_COUNT = 15


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


REPO_ROOT = Path(__file__).resolve().parents[2]


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
        from ..services.analytics import create_event_record

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


def _resolve_demo_live_base_url(request: Request) -> str:
    configured = str(settings.demo_live_base_url or "").strip()
    if configured:
        return configured.rstrip("/")

    origin = str(request.headers.get("origin") or "").strip()
    if origin:
        return origin.rstrip("/")

    return str(request.base_url).rstrip("/")


def _resolve_livekit_client_url() -> str:
    raw = str(settings.livekit_public_url or settings.livekit_url or "").strip()
    if not raw:
        return ""
    normalized = raw.rstrip("/")
    if normalized.endswith("/livekit"):
        return f"{normalized}/"
    return raw


def _assert_demo_live_entry_key(key: str | None) -> None:
    expected = str(settings.demo_live_entry_key or "").strip()
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Demo live entry key is not configured",
        )

    provided = str(key or "").strip()
    if not provided or not secrets.compare_digest(provided, expected):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid demo live entry key",
        )


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


_crash_report_rate_limiter: dict[str, list[datetime]] = {}


_live_rate_limiter: dict[str, list[datetime]] = {}


def _check_window_rate_limit(
    *,
    store: dict[str, list[datetime]],
    key: str,
    max_requests: int,
    window_seconds: int,
    detail: str,
) -> None:
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(seconds=max(1, int(window_seconds or 1)))

    if key in store:
        store[key] = [ts for ts in store[key] if ts > window_start]
    else:
        store[key] = []

    if len(store[key]) >= max(1, int(max_requests or 1)):
        raise HTTPException(status_code=429, detail=detail)

    store[key].append(now)


def _check_live_rate_limit(
    *,
    db: Session,
    user: User,
    bucket: str,
    ai_path: bool = False,
    live_session_id: UUID | None = None,
) -> None:
    from ..services import live_rate_limits as live_rate_limit_service

    max_requests = (
        settings.live_ai_rate_limit_requests_per_minute
        if ai_path
        else settings.live_rate_limit_requests_per_minute
    )
    window_seconds = settings.live_rate_limit_window_seconds

    # Local in-memory limiter acts as a fast-path guard.
    _check_window_rate_limit(
        store=_live_rate_limiter,
        key=f"live:{bucket}:{user.id}",
        max_requests=max_requests,
        window_seconds=window_seconds,
        detail="Rate limit exceeded for live session endpoint.",
    )
    # DB-backed limiter provides cross-process consistency.
    try:
        live_rate_limit_service.check_and_record(
            db,
            bucket=bucket,
            user_id=user.id,
            max_requests=max_requests,
            window_seconds=window_seconds,
            live_session_id=live_session_id,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=429, detail=str(exc))


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


def _ensure_class_access(current_user: User, classroom: Classroom) -> None:
    if current_user.role in ADMIN_ROLES:
        return
    if (
        current_user.role == UserRole.teacher
        and classroom.teacher_id == current_user.id
    ):
        return
    raise HTTPException(status_code=403, detail="Not authorized")


def _build_live_session_out(
    db: Session, live_session: LiveSession
) -> schemas.LiveSessionOut:
    from ..services import live_sessions as live_session_service

    participant_count = live_session_service.count_active_participants(db, live_session.id)
    return schemas.LiveSessionOut(
        id=live_session.id,
        classroom_id=live_session.classroom_id,
        room_name=live_session.room_name,
        title=live_session.title,
        status=live_session.status,
        starts_at=live_session.starts_at,
        ended_at=live_session.ended_at,
        created_by_id=live_session.created_by_id,
        session_metadata=live_session.session_metadata,
        participant_count=participant_count,
        created_at=live_session.created_at,
        updated_at=live_session.updated_at,
    )


def _build_live_participant_out(
    participant: LiveParticipant,
) -> schemas.LiveParticipantOut:
    return schemas.LiveParticipantOut(
        id=participant.id,
        live_session_id=participant.live_session_id,
        user_id=participant.user_id,
        participant_identity=participant.participant_identity,
        display_name=participant.display_name,
        role=participant.role,
        is_ai=participant.is_ai,
        joined_at=participant.joined_at,
        left_at=participant.left_at,
    )


def _build_live_event_out(event: LiveEvent) -> schemas.LiveEventOut:
    return schemas.LiveEventOut(
        id=event.id,
        live_session_id=event.live_session_id,
        event_type=event.event_type,
        event_source=event.event_source,
        participant_identity=event.participant_identity,
        participant_user_id=event.participant_user_id,
        payload=event.payload,
        created_at=event.created_at,
    )


def _normalize_question_type(raw: str) -> QuestionType:
    value = str(raw).strip().lower().replace("-", "_")
    try:
        return QuestionType(value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid question type") from exc


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

    # Try the primary model first, then an optional fallback model. The yescale
    # gateway occasionally returns 503 "temporarily unavailable" for a given
    # model, and some models are far slower than others; falling back keeps the
    # AI teacher responsive instead of surfacing a 500.
    primary_model = model or settings.deepseek_model
    fallback_model = str(getattr(settings, "deepseek_fallback_model", "") or "").strip()
    model_candidates: list[str] = [primary_model]
    if fallback_model and fallback_model != primary_model:
        model_candidates.append(fallback_model)

    last_error: Exception | None = None
    for model_name in model_candidates:
        try:
            return _call_deepseek_chat_once(
                messages,
                temperature=temperature,
                response_format=response_format,
                model=model_name,
            )
        except RuntimeError as exc:
            last_error = exc
            logger.warning(
                "Deepseek model '%s' failed (%s); trying next candidate",
                model_name,
                exc,
            )
            continue

    raise RuntimeError(
        f"Deepseek request failed for all models {model_candidates}: {last_error}"
    )


def _call_deepseek_chat_once(
    messages: Sequence[dict[str, str]],
    *,
    temperature: float = 0.2,
    response_format: Optional[dict[str, Any]] = None,
    model: Optional[str] = None,
) -> str:
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
        except (URLError, TimeoutError, socket.timeout, OSError) as exc:
            # urllib raises a bare TimeoutError (not URLError) on socket read
            # timeouts; catch it here so a slow model degrades gracefully to the
            # fallback model / fallback response instead of a 500.
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
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        # urllib raises a bare TimeoutError (not URLError) on socket read
        # timeouts; treat all transport errors uniformly so callers can fall
        # back to the non-streaming path.
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


def _normalize_tutor_level(level: Optional[str]) -> str:
    normalized = (level or "beginner").strip().lower()
    if normalized in {"beginner", "intermediate", "advanced"}:
        return normalized
    return "beginner"


def _build_tutor_system_prompt(*, level: Optional[str]) -> str:
    learner_level = _normalize_tutor_level(level)
    level_instruction = {
        "beginner": (
            "Giải thích bằng ngôn ngữ đơn giản, từng bước, ưu tiên ví dụ gần gũi."
        ),
        "intermediate": (
            "Giải thích có chiều sâu vừa phải, liên kết kiến thức giữa họa tiết - bối cảnh lịch sử - ý nghĩa biểu tượng."
        ),
        "advanced": (
            "Giải thích chuyên sâu, nêu khác biệt/đối chiếu và chỉ ra giới hạn dữ liệu khi cần."
        ),
    }[learner_level]

    return (
        "Bạn là AI Tutor chuyên về giáo dục di sản Việt Nam cho nền tảng Lưu Niên Sử Kí. "
        "Nhiệm vụ: giúp người học hiểu đúng và hứng thú với Cửu Đỉnh qua ngữ cảnh lịch sử, nghệ thuật và biểu tượng.\n\n"
        "Quy tắc bắt buộc:\n"
        "1) Trả lời bằng tiếng Việt tự nhiên, rõ ràng, ngắn gọn theo từng ý.\n"
        "2) Chỉ dựa trên nguồn được cung cấp; không bịa thông tin ngoài nguồn.\n"
        "3) Khi dùng thông tin nguồn, gắn trích dẫn dạng [S#] ngay sau ý tương ứng.\n"
        "4) Nếu nguồn chưa đủ, nói rõ phần chưa đủ và đề xuất câu hỏi tiếp theo để làm rõ.\n"
        "5) Ưu tiên cách dạy gợi mở (hint-first): đưa định hướng trước, rồi mới chốt ý.\n\n"
        f"Điều chỉnh theo trình độ: {level_instruction}"
    )


def _build_tutor_user_prompt(*, message: str, sources_prompt: str) -> str:
    return (
        "Hãy trả lời câu hỏi theo đúng quy tắc system.\n"
        "Bố cục khuyến nghị:\n"
        "- Ý chính (1-2 câu)\n"
        "- Giải thích ngắn theo từng ý có [S#]\n"
        "- Gợi ý học tiếp (1 câu)\n\n"
        f"Nguồn:\n{sources_prompt}\n\n"
        f"Câu hỏi: {message}\n"
        "Trả lời:"
    )


def _build_qa_system_prompt() -> str:
    return (
        "Bạn là hệ thống hỏi đáp nội dung nội bộ về Cửu Đỉnh và di sản Việt Nam. "
        "Ưu tiên độ chính xác và khả năng kiểm chứng.\n\n"
        "Quy tắc bắt buộc:\n"
        "1) Chỉ trả lời dựa trên nguồn đã cung cấp.\n"
        "2) Mỗi ý quan trọng cần có trích dẫn [S#].\n"
        "3) Nếu nguồn không đủ để kết luận, nói rõ 'chưa đủ dữ liệu từ nguồn hiện có'.\n"
        "4) Trình bày ngắn gọn, trực tiếp, không thêm thông tin suy đoán."
    )


def _build_qa_user_prompt(*, question: str, sources_prompt: str) -> str:
    return (
        "Trả lời câu hỏi dựa trên nguồn dưới đây và tuân thủ quy tắc system.\n\n"
        f"Nguồn:\n{sources_prompt}\n\n"
        f"Câu hỏi: {question}\n"
        "Trả lời:"
    )


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


def _ensure_weekly_quests_for_user(
    db: Session, user_id: UUID, current_time: datetime
) -> list[UserWeeklyQuest]:
    """Ensure user has all active recurring weekly quests assigned for the current week."""
    from ..services.weekly_quests import ensure_weekly_quests_for_user

    return ensure_weekly_quests_for_user(db, user_id, current_time)


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


def _get_experiment_or_404(db: Session, experiment_id: UUID) -> Experiment:
    experiment = db.get(Experiment, experiment_id)
    if experiment is None:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return experiment


def _get_email_template_or_404(db: Session, template_id: UUID) -> EmailTemplate:
    template = db.get(EmailTemplate, template_id)
    if template is None:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


def _to_email_template_out(template: EmailTemplate) -> schemas.EmailTemplateOut:
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


def _to_scheduled_email_out(email: ScheduledEmail) -> schemas.ScheduledEmailOut:
    return schemas.ScheduledEmailOut(
        id=email.id,
        user_id=email.user_id,
        template_id=email.template_id,
        template_key=email.template.key if email.template else None,
        template_name=email.template.name if email.template else None,
        scheduled_for=email.scheduled_for,
        status=email.status.value,
        context_data=email.context_data,
        sent_at=email.sent_at,
        error_message=email.error_message,
        created_at=email.created_at,
    )


def _parse_email_status_filter(status_filter: Optional[str]) -> Optional[EmailStatus]:
    if not status_filter:
        return None
    try:
        return EmailStatus(status_filter)
    except ValueError as exc:
        raise HTTPException(
            status_code=400, detail=f"Invalid status: {status_filter}"
        ) from exc


def _apply_scheduled_email_filters(
    query: Any,
    *,
    status_filter: Optional[EmailStatus] = None,
    user_id: Optional[UUID] = None,
    template_id: Optional[UUID] = None,
) -> Any:
    if status_filter is not None:
        query = query.where(ScheduledEmail.status == status_filter)
    if user_id is not None:
        query = query.where(ScheduledEmail.user_id == user_id)
    if template_id is not None:
        query = query.where(ScheduledEmail.template_id == template_id)
    return query
