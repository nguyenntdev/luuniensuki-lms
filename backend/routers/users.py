# -*- coding: utf-8 -*-
"""User profile, onboarding, notifications, sessions, public profiles, avatar, preview & collection (backend-modularization router extraction).

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
    ALLOWED_IMAGE_TYPES,
    AVATAR_DIR,
    IMAGE_EXTENSION_BY_TYPE,
    MAX_AVATAR_SIZE,
    QUIZ_PASS_PERCENT,
    USERNAME_REGEX,
    _detect_image_type,
    _is_valid_display_name,
    get_allowed_content_ratings,
    get_user_age,
)

logger = logging.getLogger("luuniensuki.api")

router = APIRouter()


@router.patch("/api/v1/users/me", response_model=UpdateProfileResponse)
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


@router.post("/api/v1/users/me/starting-path", response_model=StartingPathResponse)
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


@router.post("/api/v1/onboarding/goals")
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


@router.get("/api/v1/onboarding/status", response_model=OnboardingStatusResponse)
def get_onboarding_status(
    current_user: User = Depends(get_current_user),
) -> OnboardingStatusResponse:
    """Get user's onboarding status."""
    return OnboardingStatusResponse(
        onboarding_completed=current_user.onboarding_completed,
        onboarding_goal=current_user.onboarding_goal,
        onboarding_completed_at=current_user.onboarding_completed_at,
    )


@router.post("/api/v1/onboarding/complete", response_model=OnboardingCompleteResponse)
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


@router.get(
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


@router.put(
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


@router.post(
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


@router.delete(
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


@router.get(
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


@router.post(
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
    from ..services import push_notifications

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


@router.post(
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
    from ..services import push_notifications

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


@router.get(
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


@router.get(
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
    from ..services import push_notifications

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


@router.get("/api/v1/preview/lesson")
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


@router.post("/api/v1/preview/start", response_model=schemas.GuestPreviewStartOut)
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


@router.post("/api/v1/preview/complete", response_model=schemas.GuestPreviewCompleteOut)
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


@router.post("/api/v1/preview/convert", response_model=schemas.GuestPreviewConvertOut)
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


@router.get("/api/v1/users/{user_id}/public", response_model=UserPublicProfile)
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


@router.get("/api/v1/u/{username_or_id}", response_model=UserPublicProfile)
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


@router.post("/api/v1/sessions/heartbeat", response_model=schemas.SessionHeartbeatOut)
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


@router.post("/api/v1/sessions/end", response_model=schemas.SessionEndOut)
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


@router.post("/api/v1/users/me/avatar")
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


@router.post("/api/v1/users/me/change-password")
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


@router.post("/api/v1/users/me/age-verify", response_model=schemas.AgeVerificationOut)
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


@router.get("/api/v1/users/me/collection", response_model=UserCollectionResponse)
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


@router.get("/api/v1/users/{user_id}/activity", response_model=schemas.ShareListOut)
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
    from ..services import sharing

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
