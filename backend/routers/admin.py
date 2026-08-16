# -*- coding: utf-8 -*-
"""Admin surface: lessons/quiz management, RAG, content versioning/review, feature flags, experiments, email templates, app versions, abuse & crash reports, analytics (backend-modularization router extraction).

Endpoints were moved verbatim from ``backend.main``; only the decorator
prefix changed from ``@app.<method>`` to ``@router.<method>``. The router is
registered via ``app.include_router(router)`` in ``backend.app.create_app()``.
Shared helpers/constants are imported from ``backend.domain.helpers`` so the
import graph stays one-way (routers never import ``backend.main``).
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
from ..domain.gamification import (
    CERTIFICATE_ISSUER_NAME,
    XP_RANKS,
    _apply_xp_boost,
    _award_badge,
    _compute_rank,
    _issue_certificate,
    _update_streak,
)
from ..domain.auth_session import (
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

# Helper functions and constants relocated to backend.domain.helpers
# (backend-modularization). Imported here so existing endpoints in this
# module and tests referencing ``main.<name>`` continue to resolve.
from ..domain.helpers import (  # noqa: F401
    DISCOVERY_XP,
    LESSON_XP,
    MASTERED_XP,
    QUIZ_PASS_PERCENT,
    URN_EXAM_PASS_PERCENT,
    URN_EXAM_PASS_XP,
    URN_EXAM_QUESTION_COUNT,
    USERNAME_REGEX,
    AVATAR_DIR,
    ALLOWED_IMAGE_TYPES,
    MAX_AVATAR_SIZE,
    RAG_ALLOWED_FILE_TYPES,
    IMAGE_EXTENSION_BY_TYPE,
    _detect_image_type,
    BADGE_FIRST_DISCOVERY,
    BADGE_FIRST_MASTERED,
    BADGE_STREAK_7,
    BADGE_STREAK_30,
    BADGE_STREAK_100,
    BADGE_COLLECTOR_10,
    BADGE_COLLECTOR_50,
    BADGE_EXPLORER_ALL_URNS,
    BADGE_QUIZ_MASTER,
    BADGE_SPEED_DEMON,
    BADGE_PERFECT_SCORE,
    BADGE_EARLY_BIRD,
    SEED_DATA_FILES,
    REPO_ROOT,
    SEED_DATA_DIR,
    _SEED_CACHE,
    CUU_DINH_CONTEXT,
    _record_analytics_event,
    _normalize_category,
    _objective_current_value,
    _build_objective_progress,
    _compute_quest_progress_data,
    _apply_quest_rewards,
    _count_user_discoveries,
    _resolve_demo_live_base_url,
    _resolve_livekit_client_url,
    _assert_demo_live_entry_key,
    get_user_age,
    get_allowed_content_ratings,
    _is_valid_display_name,
    _crash_report_rate_limiter,
    _live_rate_limiter,
    _check_window_rate_limit,
    _check_live_rate_limit,
    _check_crash_report_rate_limit,
    _quest_prerequisite_completed,
    _build_quest_rewards,
    _extract_next_objective,
    _ensure_class_access,
    _build_live_session_out,
    _build_live_participant_out,
    _build_live_event_out,
    _normalize_question_type,
    _rag_document_out,
    _embedding_job_out,
    _embedding_url,
    _call_embedding,
    _maybe_update_rag_embedding,
    _build_urn_exam_eligibility_detail,
    _ensure_urn_exam_eligibility,
    _select_urn_exam_questions,
    _normalize_recommendation_items,
    _build_rules_recommendations,
    _deepseek_chat_url,
    _call_deepseek_chat,
    _call_deepseek_chat_once,
    _call_deepseek_chat_stream,
    _strip_accents,
    _load_seed_data,
    _find_seed_entry,
    _slice_json_candidate,
    _extract_json_payload,
    _safe_parse_json,
    _source_snippet,
    _clip_text,
    _get_rag_settings,
    _apply_ai_settings,
    _cosine_similarity,
    _keyword_score,
    _score_rag_documents,
    _collect_ai_sources,
    _format_sources_for_prompt,
    _normalize_tutor_level,
    _build_tutor_system_prompt,
    _build_tutor_user_prompt,
    _build_qa_system_prompt,
    _build_qa_user_prompt,
    _extract_citations,
    _build_ai_citations,
    _fallback_answer_from_sources,
    _fallback_summary_from_sources,
    _fallback_flashcards_from_sources,
    _fallback_explain_text,
    _start_ai_job,
    _finish_ai_job,
    _fail_ai_job,
    _finish_ai_job_fallback,
    _resolve_urn,
    _resolve_motif,
    _lesson_payload_from_seed,
    _quiz_payloads_from_seed,
    _sanitize_quiz_payload,
    _generate_quiz_payloads_with_ai,
    _store_quiz_payloads,
    _generate_llm_recommendations,
    _store_recommendation,
    _create_content_snapshot,
    _resolve_daily_goal_level,
    _load_daily_goal_settings,
    _ensure_daily_missions_for_user,
    _ensure_weekly_quests_for_user,
    _parse_semver,
    _compare_versions,
    _format_learning_path_response,
    _get_experiment_or_404,
    _get_email_template_or_404,
    _to_email_template_out,
    _to_scheduled_email_out,
    _parse_email_status_filter,
    _apply_scheduled_email_filters,
)

from fastapi import APIRouter

from ..domain.helpers import (  # noqa: F401
    CUU_DINH_CONTEXT,
    RAG_ALLOWED_FILE_TYPES,
    _apply_ai_settings,
    _apply_scheduled_email_filters,
    _call_deepseek_chat,
    _check_crash_report_rate_limit,
    _create_content_snapshot,
    _embedding_job_out,
    _find_seed_entry,
    _get_email_template_or_404,
    _get_experiment_or_404,
    _get_rag_settings,
    _lesson_payload_from_seed,
    _maybe_update_rag_embedding,
    _normalize_question_type,
    _parse_email_status_filter,
    _parse_semver,
    _quiz_payloads_from_seed,
    _rag_document_out,
    _resolve_urn,
    _safe_parse_json,
    _sanitize_quiz_payload,
    _store_quiz_payloads,
    _to_email_template_out,
    _to_scheduled_email_out,
)

logger = logging.getLogger("luuniensuki.api")

router = APIRouter()


@router.get(
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


@router.get(
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


@router.post("/api/v1/crash-reports", response_model=schemas.CrashReportOut)
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


@router.get("/api/v1/admin/crash-reports", response_model=schemas.CrashReportListOut)
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


@router.get(
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


@router.post(
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


@router.get(
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


@router.get("/api/v1/admin/lessons", response_model=list[AdminLessonOut])
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


@router.post("/api/v1/admin/lessons", response_model=AdminLessonOut, status_code=201)
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


@router.patch("/api/v1/admin/lessons/{lesson_id}", response_model=AdminLessonOut)
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


@router.get("/api/v1/admin/quiz-questions", response_model=list[AdminQuizQuestionOut])
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


@router.post(
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


@router.patch(
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


@router.get("/api/v1/admin/rag/documents", response_model=schemas.RagDocumentListOut)
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


@router.get(
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


@router.post(
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


@router.post(
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


@router.put(
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


@router.delete("/api/v1/admin/rag/documents/{document_id}", status_code=204)
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


@router.post(
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


@router.post(
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


@router.get("/api/v1/admin/rag/settings", response_model=schemas.RagSettingsOut)
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


@router.put("/api/v1/admin/rag/settings", response_model=schemas.RagSettingsOut)
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


@router.post("/api/v1/admin/rag/settings/reset", response_model=schemas.RagSettingsOut)
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


@router.post(
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
    from ..services.embeddings import rebuild_all_embeddings

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


@router.get(
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
    from ..services.embeddings import get_latest_job

    job = get_latest_job(db)
    if job is None:
        raise HTTPException(status_code=404, detail="No rebuild jobs found")

    return _embedding_job_out(job)


@router.get(
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
    from ..services.embeddings import get_job_by_id

    job = get_job_by_id(db, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    return _embedding_job_out(job)


@router.post(
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
    from ..services.embeddings import update_document_embedding

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


@router.get("/api/v1/admin/rag/health", response_model=RagHealthOut)
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


@router.get(
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
    from ..services.retention import calculate_overall_retention

    result = calculate_overall_retention(db, days_ago=days_ago)
    return schemas.RetentionMetricsOut(**result)


@router.get(
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
    from ..services.retention import calculate_cohort_retention

    result = calculate_cohort_retention(db, period=period, limit=limit)
    return schemas.CohortRetentionOut(**result)


@router.get(
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
    from ..services.retention import calculate_retention_curve

    result = calculate_retention_curve(db, days=days, cohort_days_ago=cohort_days_ago)
    return schemas.RetentionCurveOut(**result)


@router.post("/api/v1/admin/ai/urns/{urn_slug}/seed", response_model=SeedUrnOut)
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


@router.get("/api/v1/admin/content/flags", response_model=list[ContentFlagOut])
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


@router.get(
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


@router.get(
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


@router.post(
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


@router.post("/api/v1/admin/lessons/{lesson_id}/approve", response_model=AdminLessonOut)
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


@router.post("/api/v1/admin/lessons/{lesson_id}/reject", response_model=AdminLessonOut)
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


@router.post(
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


@router.post(
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


@router.post(
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


@router.get(
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


@router.post(
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


@router.post("/api/v1/admin/tags", response_model=TagOut, status_code=201)
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


@router.post(
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


@router.delete(
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


@router.get(
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


@router.get(
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


@router.get("/api/v1/admin/app/versions", response_model=list[schemas.AppVersionOut])
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


@router.post(
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


@router.put(
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


@router.get("/api/v1/admin/reports/abuse", response_model=schemas.AbuseReportListOut)
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


@router.get(
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


@router.post(
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
    from ..services.abuse_reports import assign_abuse_report

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


@router.post(
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
    from ..services.abuse_reports import resolve_abuse_report

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


@router.get("/api/v1/admin/feature-flags", response_model=list[schemas.FeatureFlagOut])
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


@router.post(
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


@router.put("/api/v1/admin/feature-flags/{key}", response_model=schemas.FeatureFlagOut)
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


@router.delete("/api/v1/admin/feature-flags/{key}", status_code=status.HTTP_204_NO_CONTENT)
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


@router.get("/api/v1/admin/experiments", response_model=list[schemas.ExperimentOut])
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


@router.post(
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


@router.put(
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


@router.delete(
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
    experiment = _get_experiment_or_404(db, experiment_id)

    db.delete(experiment)
    db.commit()

    return Response(status_code=204)


@router.get(
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

    _get_experiment_or_404(db, experiment_id)

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


@router.get(
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

    _get_experiment_or_404(db, experiment_id)

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


@router.get(
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

    experiment = _get_experiment_or_404(db, experiment_id)

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


@router.get(
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

    _get_experiment_or_404(db, experiment_id)

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


@router.get("/api/v1/admin/email-templates", response_model=schemas.EmailTemplateListOut)
def list_email_templates(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    active_only: bool = Query(False),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> schemas.EmailTemplateListOut:
    """
    List all email templates (admin only).

    Query parameters:
    - page: Page number (default: 1)
    - page_size: Items per page (default: 20, max: 100)
    - active_only: Filter to active templates only
    """
    query = select(EmailTemplate)

    if active_only:
        query = query.where(EmailTemplate.is_active.is_(True))

    query = query.order_by(EmailTemplate.created_at.desc())

    # Get total count
    count_result = db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar() or 0

    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    templates = db.execute(query).scalars().all()

    return schemas.EmailTemplateListOut(
        templates=[_to_email_template_out(template) for template in templates],
        total=total,
    )


@router.post(
    "/api/v1/admin/email-templates",
    response_model=schemas.EmailTemplateOut,
    status_code=201,
)
def create_email_template(
    payload: schemas.EmailTemplateCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> schemas.EmailTemplateOut:
    """
    Create a new email template (admin only).
    """
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

    return _to_email_template_out(template)


@router.put(
    "/api/v1/admin/email-templates/{template_id}",
    response_model=schemas.EmailTemplateOut,
)
def update_email_template(
    template_id: UUID,
    payload: schemas.EmailTemplateUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> schemas.EmailTemplateOut:
    """
    Update an email template (admin only).
    """
    template = _get_email_template_or_404(db, template_id)

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

    return _to_email_template_out(template)


@router.get("/api/v1/admin/scheduled-emails", response_model=schemas.ScheduledEmailListOut)
def list_scheduled_emails(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None),
    user_id: Optional[UUID] = Query(None),
    template_id: Optional[UUID] = Query(None),
    current_user: User = Depends(require_admin),
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
    status_enum = _parse_email_status_filter(status_filter)
    query = _apply_scheduled_email_filters(
        select(ScheduledEmail).options(selectinload(ScheduledEmail.template)),
        status_filter=status_enum,
        user_id=user_id,
        template_id=template_id,
    ).order_by(ScheduledEmail.scheduled_for.desc())
    total = (
        db.execute(
            _apply_scheduled_email_filters(
                select(func.count(ScheduledEmail.id)),
                status_filter=status_enum,
                user_id=user_id,
                template_id=template_id,
            )
        ).scalar()
        or 0
    )
    status_counts_result = db.execute(
        _apply_scheduled_email_filters(
            select(ScheduledEmail.status, func.count(ScheduledEmail.id)),
            user_id=user_id,
            template_id=template_id,
        ).group_by(ScheduledEmail.status)
    ).all()
    status_counts = {status.value: count for status, count in status_counts_result}

    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    emails = db.execute(query).scalars().all()

    return schemas.ScheduledEmailListOut(
        emails=[_to_scheduled_email_out(email) for email in emails],
        total=total,
        status_counts=status_counts,
    )


@router.post(
    "/api/v1/admin/scheduled-emails/send-test", response_model=schemas.SendTestEmailOut
)
def send_test_email(
    payload: schemas.SendTestEmailIn,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> schemas.SendTestEmailOut:
    """
    Send a test email using a template (admin only).

    This creates a scheduled email record for testing purposes.
    In production, you would integrate with an actual email service (e.g., SendGrid, AWS SES).
    """
    template = _get_email_template_or_404(db, payload.template_id)

    # Import email scheduler service
    from ..services import email_scheduler

    try:
        # Render template with test context
        subject, _, _ = email_scheduler.render_email_template(
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
            message=f"Test email rendered successfully for {payload.recipient_email}. Subject: {subject}",
            scheduled_email_id=test_email.id,
        )

    except Exception as e:
        logger.error(f"Failed to send test email: {e}")
        return schemas.SendTestEmailOut(
            success=False,
            message=f"Failed to render template: {str(e)}",
        )
