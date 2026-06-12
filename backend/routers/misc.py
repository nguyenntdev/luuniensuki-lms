# -*- coding: utf-8 -*-
"""Miscellaneous: health, version check, analytics ingest, abuse reports, content flags & user-facing feature flags/experiments (backend-modularization router extraction).

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
    _compare_versions,
    _get_experiment_or_404,
)

logger = logging.getLogger("luuniensuki.api")

router = APIRouter()


@router.post("/api/v1/analytics/events", response_model=AnalyticsEventsOut)
def ingest_analytics_events(
    payload: AnalyticsEventsIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AnalyticsEventsOut:
    if not payload.events:
        return AnalyticsEventsOut(success=True, count=0)

    # Import analytics service for event validation
    from .services.analytics import create_event_record

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


@router.post("/api/v1/content/flags", response_model=ContentFlagOut, status_code=201)
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


@router.get("/health", response_model=HealthResponse)
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


@router.get("/api/v1/app/version/check", response_model=schemas.AppVersionCheckOut)
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


@router.post(
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


@router.get("/api/v1/reports/abuse/mine", response_model=list[schemas.AbuseReportOut])
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


@router.get("/api/v1/features", response_model=schemas.UserFeaturesOut)
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


@router.get("/api/v1/features/{key}", response_model=schemas.FeatureCheckOut)
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


@router.get("/api/v1/experiments", response_model=schemas.UserExperimentsOut)
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


@router.post(
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


@router.post(
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

    _get_experiment_or_404(db, experiment_id)

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
