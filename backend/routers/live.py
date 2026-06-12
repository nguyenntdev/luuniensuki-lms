# -*- coding: utf-8 -*-
"""Live sessions, AI teacher & LiveKit integration (backend-modularization router extraction).

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
    _assert_demo_live_entry_key,
    _build_live_event_out,
    _build_live_participant_out,
    _build_live_session_out,
    _call_deepseek_chat,
    _call_deepseek_chat_stream,
    _check_live_rate_limit,
    _resolve_demo_live_base_url,
    _resolve_livekit_client_url,
)

logger = logging.getLogger("luuniensuki.api")

router = APIRouter()


@router.get("/api/v1/live/demo-enter", include_in_schema=False)
def demo_live_enter(
    request: Request,
    key: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    if not settings.demo_live_entry_enabled:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Demo live entry is disabled",
        )

    _assert_demo_live_entry_key(key)

    demo_email = str(settings.demo_live_teacher_email or "").strip().lower()
    demo_password = str(settings.demo_live_teacher_password or "")
    if not demo_email or not demo_password:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Demo live credentials are not configured",
        )

    try:
        provision_result = run_provision(
            email=demo_email,
            password=demo_password,
            display_name=str(settings.demo_live_teacher_name or "").strip()
            or "Live Demo Teacher",
            class_name=str(settings.demo_live_class_name or "").strip()
            or "AI Teacher 3D Demo Class",
            session_title=str(settings.demo_live_session_title or "").strip()
            or "AI Teacher 3D Live Session",
            max_students=max(10, int(settings.demo_live_max_students)),
            base_url=_resolve_demo_live_base_url(request),
        )
    except Exception as exc:
        logger.exception("Failed to provision demo live session: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to prepare demo live classroom",
        )

    user = db.execute(select(User).where(User.email == demo_email)).scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Demo live teacher account is unavailable",
        )

    session_id = str(
        ((provision_result.get("live_session") or {}).get("id") or "")
    ).strip()
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Demo live session is unavailable",
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

    response = RedirectResponse(
        url=f"/live/{session_id}",
        status_code=status.HTTP_307_TEMPORARY_REDIRECT,
    )
    _set_auth_cookies(response, access_token=access_token, refresh_token=refresh_token)
    response.headers["Cache-Control"] = "no-store"
    return response


@router.get(
    "/api/v1/classrooms/{classroom_id}/live-sessions",
    response_model=list[schemas.LiveSessionOut],
)
def list_live_sessions(
    classroom_id: UUID,
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[schemas.LiveSessionOut]:
    from .services import live_sessions as live_session_service

    classroom = db.get(Classroom, classroom_id)
    if classroom is None:
        raise HTTPException(status_code=404, detail="Classroom not found")
    if not live_session_service.can_access_classroom(db, current_user, classroom):
        raise HTTPException(status_code=403, detail="Not authorized")

    sessions = live_session_service.list_live_sessions_for_classroom(
        db, classroom_id=classroom_id, limit=limit
    )
    return [_build_live_session_out(db, item) for item in sessions]


@router.post(
    "/api/v1/classrooms/{classroom_id}/live-sessions",
    response_model=schemas.LiveSessionOut,
    status_code=201,
)
def create_live_session(
    classroom_id: UUID,
    payload: schemas.LiveSessionCreateIn,
    idempotency_key_header: str | None = Header(default=None, alias="Idempotency-Key"),
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db),
) -> schemas.LiveSessionOut:
    from .services import live_sessions as live_session_service

    classroom = db.get(Classroom, classroom_id)
    if classroom is None:
        raise HTTPException(status_code=404, detail="Classroom not found")
    if not live_session_service.can_manage_classroom(current_user, classroom):
        raise HTTPException(status_code=403, detail="Not authorized")

    try:
        live_session = live_session_service.create_live_session(
            db,
            classroom=classroom,
            created_by=current_user,
            title=payload.title,
            starts_at=payload.starts_at,
            idempotency_key=payload.idempotency_key or idempotency_key_header,
            session_metadata=payload.session_metadata,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    return _build_live_session_out(db, live_session)


@router.get("/api/v1/live-sessions/{live_session_id}", response_model=schemas.LiveSessionOut)
def get_live_session_detail(
    live_session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.LiveSessionOut:
    from .services import live_sessions as live_session_service

    live_session = live_session_service.get_live_session(db, live_session_id)
    if live_session is None:
        raise HTTPException(status_code=404, detail="Live session not found")

    try:
        live_session_service.ensure_user_can_access_live_session(
            db, user=current_user, live_session=live_session
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    return _build_live_session_out(db, live_session)


@router.post(
    "/api/v1/live-sessions/{live_session_id}/token",
    response_model=schemas.LiveSessionTokenOut,
)
def issue_livekit_access_token(
    live_session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.LiveSessionTokenOut:
    from .services import live_sessions as live_session_service

    live_session = live_session_service.get_live_session(db, live_session_id)
    if live_session is None:
        raise HTTPException(status_code=404, detail="Live session not found")
    _check_live_rate_limit(
        db=db,
        user=current_user,
        bucket="token",
        ai_path=False,
        live_session_id=live_session.id,
    )
    if live_session.status == LiveSessionStatus.ended.value:
        raise HTTPException(status_code=400, detail="Live session has ended")

    try:
        live_session_service.ensure_user_can_join_live_session(
            db, user=current_user, live_session=live_session
        )
        identity = live_session_service.participant_identity_for_user(current_user)
        token, expires_at = live_session_service.issue_livekit_token(
            live_session=live_session,
            identity=identity,
            display_name=current_user.display_name or current_user.email,
            metadata={
                "user_id": str(current_user.id),
                "classroom_id": str(live_session.classroom_id),
                "live_session_id": str(live_session.id),
                "role": current_user.role.value
                if isinstance(current_user.role, UserRole)
                else str(current_user.role),
            },
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    return schemas.LiveSessionTokenOut(
        url=_resolve_livekit_client_url(),
        room_name=live_session.room_name,
        identity=identity,
        token=token,
        expires_at=expires_at,
    )


@router.post(
    "/api/v1/live-sessions/{live_session_id}/join",
    response_model=schemas.LiveSessionJoinOut,
)
def join_live_session_room(
    live_session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.LiveSessionJoinOut:
    from .services import live_sessions as live_session_service

    live_session = live_session_service.get_live_session(db, live_session_id)
    if live_session is None:
        raise HTTPException(status_code=404, detail="Live session not found")
    _check_live_rate_limit(
        db=db,
        user=current_user,
        bucket="join",
        ai_path=False,
        live_session_id=live_session.id,
    )
    if live_session.status == LiveSessionStatus.ended.value:
        raise HTTPException(status_code=400, detail="Live session has ended")

    try:
        live_session_service.ensure_user_can_join_live_session(
            db, user=current_user, live_session=live_session
        )
        identity = live_session_service.participant_identity_for_user(current_user)
        participant = live_session_service.upsert_participant_join(
            db,
            live_session=live_session,
            user=current_user,
            identity=identity,
            display_name=current_user.display_name or current_user.email,
        )
        token, expires_at = live_session_service.issue_livekit_token(
            live_session=live_session,
            identity=identity,
            display_name=current_user.display_name or current_user.email,
            metadata={
                "user_id": str(current_user.id),
                "classroom_id": str(live_session.classroom_id),
                "live_session_id": str(live_session.id),
                "role": participant.role,
            },
        )
        db.refresh(live_session)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    return schemas.LiveSessionJoinOut(
        session=_build_live_session_out(db, live_session),
        participant=_build_live_participant_out(participant),
        livekit=schemas.LiveSessionTokenOut(
            url=_resolve_livekit_client_url(),
            room_name=live_session.room_name,
            identity=identity,
            token=token,
            expires_at=expires_at,
        ),
    )


@router.post("/api/v1/live-sessions/{live_session_id}/leave", status_code=204)
def leave_live_session_room(
    live_session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    from .services import live_sessions as live_session_service

    live_session = live_session_service.get_live_session(db, live_session_id)
    if live_session is None:
        raise HTTPException(status_code=404, detail="Live session not found")

    try:
        live_session_service.ensure_user_can_access_live_session(
            db, user=current_user, live_session=live_session
        )
        identity = live_session_service.participant_identity_for_user(current_user)
        live_session_service.mark_participant_left(
            db,
            live_session=live_session,
            user=current_user,
            identity=identity,
        )
    except PermissionError:
        raise HTTPException(status_code=403, detail="Not authorized")
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    return Response(status_code=204)


@router.get(
    "/api/v1/live-sessions/{live_session_id}/participants",
    response_model=list[schemas.LiveParticipantOut],
)
def list_live_session_participants(
    live_session_id: UUID,
    include_inactive: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[schemas.LiveParticipantOut]:
    from .services import live_sessions as live_session_service

    live_session = live_session_service.get_live_session(db, live_session_id)
    if live_session is None:
        raise HTTPException(status_code=404, detail="Live session not found")

    try:
        live_session_service.ensure_user_can_access_live_session(
            db, user=current_user, live_session=live_session
        )
    except PermissionError:
        raise HTTPException(status_code=403, detail="Not authorized")
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    participants = live_session_service.list_live_participants(
        db,
        live_session_id=live_session.id,
        include_inactive=include_inactive,
    )
    return [_build_live_participant_out(item) for item in participants]


@router.get(
    "/api/v1/live-sessions/{live_session_id}/events",
    response_model=list[schemas.LiveEventOut],
)
def list_live_session_events(
    live_session_id: UUID,
    limit: int = Query(50, ge=1, le=200),
    since: datetime | None = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[schemas.LiveEventOut]:
    from .services import live_sessions as live_session_service

    live_session = live_session_service.get_live_session(db, live_session_id)
    if live_session is None:
        raise HTTPException(status_code=404, detail="Live session not found")

    try:
        live_session_service.ensure_user_can_access_live_session(
            db, user=current_user, live_session=live_session
        )
    except PermissionError:
        raise HTTPException(status_code=403, detail="Not authorized")
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    events = live_session_service.list_live_events(
        db,
        live_session_id=live_session.id,
        limit=limit,
        since=since,
    )
    return [_build_live_event_out(item) for item in events]


@router.post(
    "/api/v1/live-sessions/{live_session_id}/events",
    response_model=schemas.LiveEventOut,
    status_code=201,
)
def create_live_session_event(
    live_session_id: UUID,
    payload: schemas.LiveEventCreateIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.LiveEventOut:
    from .services import live_ai_teacher as live_ai_teacher_service
    from .services import live_sessions as live_session_service

    live_session = live_session_service.get_live_session(db, live_session_id)
    if live_session is None:
        raise HTTPException(status_code=404, detail="Live session not found")

    _check_live_rate_limit(
        db=db,
        user=current_user,
        bucket="events",
        ai_path=payload.event_type.startswith("ai_") or "voice" in payload.event_type,
        live_session_id=live_session.id,
    )

    try:
        live_session_service.ensure_user_can_access_live_session(
            db, user=current_user, live_session=live_session
        )
        payload_dict = payload.payload or {}
        if payload.event_type in {"ai_voice_request", "voice_user_final"}:
            safety = live_ai_teacher_service.evaluate_content_safety(
                str(payload_dict.get("text") or payload_dict.get("message") or "")
            )
            if (
                bool(settings.live_ai_enable_guardrails)
                and bool(settings.live_ai_block_unsafe_content)
                and not safety.get("is_safe", True)
            ):
                raise HTTPException(
                    status_code=400,
                    detail="Voice message blocked by content safety guardrails.",
                )
            payload_dict = {**payload_dict, "safety": safety}

        identity = live_session_service.participant_identity_for_user(current_user)
        event = live_session_service.record_live_event(
            db,
            live_session_id=live_session.id,
            event_type=payload.event_type,
            event_source="app",
            participant_identity=identity,
            participant_user_id=current_user.id,
            payload=payload_dict,
        )
    except PermissionError:
        raise HTTPException(status_code=403, detail="Not authorized")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return _build_live_event_out(event)


@router.patch(
    "/api/v1/live-sessions/{live_session_id}/participants/{participant_id}/role",
    response_model=schemas.LiveParticipantOut,
)
def update_live_session_participant_role(
    live_session_id: UUID,
    participant_id: UUID,
    payload: schemas.LiveParticipantRoleUpdateIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.LiveParticipantOut:
    from .services import live_sessions as live_session_service

    live_session = live_session_service.get_live_session(db, live_session_id)
    if live_session is None:
        raise HTTPException(status_code=404, detail="Live session not found")

    participant = live_session_service.get_live_participant(
        db,
        live_session_id=live_session.id,
        participant_id=participant_id,
    )
    if participant is None:
        raise HTTPException(status_code=404, detail="Participant not found")

    try:
        live_session_service.ensure_user_can_moderate_live_session(
            db,
            user=current_user,
            live_session=live_session,
            allow_cohost=False,
        )
        participant = live_session_service.update_participant_role(
            db,
            live_session=live_session,
            participant=participant,
            role=payload.role,
            acted_by=current_user,
        )
    except PermissionError:
        raise HTTPException(status_code=403, detail="Not authorized")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return _build_live_participant_out(participant)


@router.post(
    "/api/v1/live-sessions/{live_session_id}/host/settings",
    response_model=schemas.LiveSessionOut,
)
def host_update_live_session_settings(
    live_session_id: UUID,
    payload: schemas.LiveHostSettingsIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.LiveSessionOut:
    from .services import live_sessions as live_session_service

    live_session = live_session_service.get_live_session(db, live_session_id)
    if live_session is None:
        raise HTTPException(status_code=404, detail="Live session not found")
    _check_live_rate_limit(
        db=db,
        user=current_user,
        bucket="host-settings",
        ai_path=False,
        live_session_id=live_session.id,
    )

    try:
        live_session_service.ensure_user_can_moderate_live_session(
            db,
            user=current_user,
            live_session=live_session,
            allow_cohost=False,
        )
        live_session = live_session_service.update_live_session_settings(
            db,
            live_session=live_session,
            lock_room=payload.lock_room,
            ai_enabled=payload.ai_enabled,
            grade_level=payload.grade_level,
            ai_cost_ceiling_usd=payload.ai_cost_ceiling_usd,
            acted_by=current_user,
        )
    except PermissionError:
        raise HTTPException(status_code=403, detail="Not authorized")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return _build_live_session_out(db, live_session)


@router.post(
    "/api/v1/live-sessions/{live_session_id}/host/mute-all",
    response_model=schemas.LiveModerationActionOut,
)
def host_mute_all_live_session(
    live_session_id: UUID,
    payload: schemas.LiveMuteAllIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.LiveModerationActionOut:
    from .services import live_sessions as live_session_service

    live_session = live_session_service.get_live_session(db, live_session_id)
    if live_session is None:
        raise HTTPException(status_code=404, detail="Live session not found")

    try:
        live_session_service.ensure_user_can_moderate_live_session(
            db,
            user=current_user,
            live_session=live_session,
            allow_cohost=True,
        )
        processed, failed = live_session_service.mute_all_participants(
            db,
            live_session=live_session,
            include_cohosts=payload.include_cohosts,
            acted_by=current_user,
        )
    except PermissionError:
        raise HTTPException(status_code=403, detail="Not authorized")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    return schemas.LiveModerationActionOut(
        action="mute-all",
        processed=processed,
        failed=failed,
        detail=None if failed == 0 else "Some participants could not be muted",
    )


@router.post(
    "/api/v1/live-sessions/{live_session_id}/host/remove-participant",
    response_model=schemas.LiveModerationActionOut,
)
def host_remove_live_session_participant(
    live_session_id: UUID,
    payload: schemas.LiveParticipantRemoveIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.LiveModerationActionOut:
    from .services import live_sessions as live_session_service

    live_session = live_session_service.get_live_session(db, live_session_id)
    if live_session is None:
        raise HTTPException(status_code=404, detail="Live session not found")

    participant = live_session_service.get_live_participant(
        db,
        live_session_id=live_session.id,
        participant_id=payload.participant_id,
    )
    if participant is None:
        raise HTTPException(status_code=404, detail="Participant not found")

    try:
        live_session_service.ensure_user_can_moderate_live_session(
            db,
            user=current_user,
            live_session=live_session,
            allow_cohost=True,
        )
        _, detail = live_session_service.remove_participant(
            db,
            live_session=live_session,
            participant=participant,
            acted_by=current_user,
        )
    except PermissionError:
        raise HTTPException(status_code=403, detail="Not authorized")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return schemas.LiveModerationActionOut(
        action="remove-participant",
        processed=1,
        failed=1 if detail else 0,
        detail=detail,
    )


@router.post("/api/v1/livekit/webhook")
async def livekit_webhook_receiver(
    request: Request,
    x_livekit_webhook_secret: str | None = Header(
        default=None, alias="X-LiveKit-Webhook-Secret"
    ),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    from .services import live_sessions as live_session_service

    if settings.livekit_webhook_secret and (
        x_livekit_webhook_secret != settings.livekit_webhook_secret
    ):
        raise HTTPException(status_code=401, detail="Invalid webhook secret")

    try:
        payload = await request.json()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Webhook payload must be an object")

    try:
        result = live_session_service.process_livekit_webhook_event(
            db,
            payload=payload,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return {"ok": True, **result}


@router.post(
    "/api/v1/live-sessions/{live_session_id}/ai-teacher/presence",
    response_model=schemas.LiveParticipantOut,
)
def ensure_live_ai_teacher_presence(
    live_session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.LiveParticipantOut:
    from .services import live_sessions as live_session_service

    live_session = live_session_service.get_live_session(db, live_session_id)
    if live_session is None:
        raise HTTPException(status_code=404, detail="Live session not found")
    if live_session.status == LiveSessionStatus.ended.value:
        raise HTTPException(status_code=400, detail="Live session has ended")

    try:
        live_session_service.ensure_user_can_access_live_session(
            db, user=current_user, live_session=live_session
        )
    except PermissionError:
        raise HTTPException(status_code=403, detail="Not authorized")
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    if not live_session_service.is_ai_enabled(live_session):
        raise HTTPException(status_code=423, detail="AI teacher is disabled by host")

    try:
        participant = live_session_service.ensure_ai_teacher_participant(
            db,
            live_session=live_session,
            display_name="AI Teacher",
            event_source="ai_teacher_api",
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return _build_live_participant_out(participant)


@router.post(
    "/api/v1/live-sessions/{live_session_id}/ai-teacher/stt",
    response_model=schemas.LiveAITeacherSTTOut,
)
async def live_ai_teacher_stt(
    live_session_id: UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.LiveAITeacherSTTOut:
    from .services import live_ai_teacher as live_ai_teacher_service
    from .services import live_session_reporting as live_reporting_service
    from .services import live_sessions as live_session_service
    from .services import live_voice as live_voice_service

    live_session = live_session_service.get_live_session(db, live_session_id)
    if live_session is None:
        raise HTTPException(status_code=404, detail="Live session not found")
    _check_live_rate_limit(
        db=db,
        user=current_user,
        bucket="ai-stt",
        ai_path=True,
        live_session_id=live_session.id,
    )
    if live_session.status == LiveSessionStatus.ended.value:
        raise HTTPException(status_code=400, detail="Live session has ended")

    try:
        live_session_service.ensure_user_can_access_live_session(
            db, user=current_user, live_session=live_session
        )
    except PermissionError:
        raise HTTPException(status_code=403, detail="Not authorized")
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    if not live_session_service.is_ai_enabled(live_session):
        raise HTTPException(status_code=423, detail="AI teacher is disabled by host")

    content = await file.read()
    await file.close()
    if not content:
        raise HTTPException(status_code=400, detail="Audio file is empty")
    max_audio_bytes = int(settings.voice_max_audio_bytes or 0)
    if max_audio_bytes > 0 and len(content) > max_audio_bytes:
        raise HTTPException(
            status_code=413,
            detail="Audio file is too large",
        )

    estimated_seconds = max(0.5, len(content) / 32000.0)
    projected_cost = live_reporting_service.estimate_stt_cost_usd(audio_seconds=estimated_seconds)
    try:
        live_reporting_service.ensure_within_cost_ceiling(
            db,
            live_session=live_session,
            projected_additional_cost=projected_cost,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=429, detail=str(exc))

    try:
        transcript, provider, model_used = live_voice_service.transcribe_audio_bytes(
            content=content,
            filename=file.filename or "voice.webm",
            content_type=file.content_type,
            session_id=str(live_session.id),
        )
    except live_voice_service.STTNoSpeechError:
        # No usable speech (silence/noise or a dropped hallucination). Return a
        # clean 422 so the client simply goes back to listening instead of
        # surfacing an error or echoing filler text.
        raise HTTPException(status_code=422, detail="Could not detect speech")
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    transcript = transcript.strip()
    if not transcript:
        raise HTTPException(status_code=422, detail="Could not detect speech")

    safety = live_ai_teacher_service.evaluate_content_safety(transcript)
    if (
        bool(settings.live_ai_enable_guardrails)
        and bool(settings.live_ai_block_unsafe_content)
        and not safety.get("is_safe", True)
    ):
        live_session_service.record_live_event(
            db,
            live_session_id=live_session.id,
            event_type="voice_guardrail_blocked",
            event_source="ai_teacher_api",
            participant_identity=live_session_service.participant_identity_for_user(current_user),
            participant_user_id=current_user.id,
            payload={"categories": safety.get("categories", [])},
        )
        raise HTTPException(status_code=400, detail="Transcript blocked by content safety guardrails.")

    live_reporting_service.record_ai_cost(
        db,
        live_session=live_session,
        component="stt",
        cost_usd=projected_cost,
        metadata={
            "provider": provider,
            "model": model_used,
            "audio_seconds_estimate": round(estimated_seconds, 2),
            "audio_persisted": False,
            "audio_retention_days": int(settings.live_audio_retention_days or 7),
        },
    )
    db.commit()

    return schemas.LiveAITeacherSTTOut(
        transcript=transcript,
        provider=provider,
        model=model_used,
    )


@router.post(
    "/api/v1/live-sessions/{live_session_id}/ai-teacher/tts",
)
def live_ai_teacher_tts(
    live_session_id: UUID,
    payload: schemas.LiveAITeacherTTSIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    from .services import live_session_reporting as live_reporting_service
    from .services import live_sessions as live_session_service
    from .services import live_voice as live_voice_service

    live_session = live_session_service.get_live_session(db, live_session_id)
    if live_session is None:
        raise HTTPException(status_code=404, detail="Live session not found")
    _check_live_rate_limit(
        db=db,
        user=current_user,
        bucket="ai-tts",
        ai_path=True,
        live_session_id=live_session.id,
    )
    if live_session.status == LiveSessionStatus.ended.value:
        raise HTTPException(status_code=400, detail="Live session has ended")

    try:
        live_session_service.ensure_user_can_access_live_session(
            db, user=current_user, live_session=live_session
        )
    except PermissionError:
        raise HTTPException(status_code=403, detail="Not authorized")
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    if not live_session_service.is_ai_enabled(live_session):
        raise HTTPException(status_code=423, detail="AI teacher is disabled by host")

    projected_cost = live_reporting_service.estimate_tts_cost_usd(text=payload.text)
    try:
        live_reporting_service.ensure_within_cost_ceiling(
            db,
            live_session=live_session,
            projected_additional_cost=projected_cost,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=429, detail=str(exc))

    try:
        audio_bytes, content_type, provider, model_used = (
            live_voice_service.synthesize_speech_bytes(
                text=payload.text,
                voice=payload.voice,
                session_id=str(live_session.id),
            )
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    live_reporting_service.record_ai_cost(
        db,
        live_session=live_session,
        component="tts",
        cost_usd=projected_cost,
        metadata={
            "provider": provider,
            "model": model_used,
            "chars": len(str(payload.text or "")),
            "audio_persisted": False,
            "audio_retention_days": int(settings.live_audio_retention_days or 7),
        },
    )
    db.commit()

    headers = {
        "Cache-Control": "no-store",
        "X-AI-Provider": provider,
        "X-AI-Model": model_used,
    }
    return StreamingResponse(
        iter([audio_bytes]),
        media_type=content_type or "audio/mpeg",
        headers=headers,
    )


@router.post(
    "/api/v1/live-sessions/{live_session_id}/ai-teacher/reply",
    response_model=schemas.LiveAITeacherReplyOut,
)
def live_ai_teacher_reply(
    live_session_id: UUID,
    payload: schemas.LiveAITeacherRequestIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.LiveAITeacherReplyOut:
    from .services import live_circuit_breaker as live_circuit_service
    from .services import live_ai_teacher as live_ai_teacher_service
    from .services import live_observability as live_observability_service
    from .services import live_session_reporting as live_reporting_service
    from .services import live_sessions as live_session_service

    live_session = live_session_service.get_live_session(db, live_session_id)
    if live_session is None:
        raise HTTPException(status_code=404, detail="Live session not found")
    _check_live_rate_limit(
        db=db,
        user=current_user,
        bucket="ai-reply",
        ai_path=True,
        live_session_id=live_session.id,
    )
    if live_session.status == LiveSessionStatus.ended.value:
        raise HTTPException(status_code=400, detail="Live session has ended")

    try:
        live_session_service.ensure_user_can_access_live_session(
            db, user=current_user, live_session=live_session
        )
    except PermissionError:
        raise HTTPException(status_code=403, detail="Not authorized")
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    if not live_session_service.is_ai_enabled(live_session):
        raise HTTPException(status_code=423, detail="AI teacher is disabled by host")

    ai_participant = live_session_service.ensure_ai_teacher_participant(
        db,
        live_session=live_session,
        display_name="AI Teacher",
        event_source="ai_teacher_api",
    )
    session_metadata = (
        live_session.session_metadata
        if isinstance(live_session.session_metadata, dict)
        else {}
    )
    persona_grade = live_ai_teacher_service.normalize_grade_level(
        str(
            payload.grade_level
            or session_metadata.get("grade_level")
            or settings.live_default_grade_level
        )
    )
    requested_mode = live_ai_teacher_service.normalize_mode(payload.mode)
    forced_hint_first = False
    mode = requested_mode
    if requested_mode in live_ai_teacher_service.MODERATOR_ONLY_MODES and not live_session_service.can_user_moderate_live_session(
        db,
        user=current_user,
        live_session=live_session,
        allow_cohost=True,
    ):
        mode = "hint-first"
        forced_hint_first = True
    speaker_name = (payload.speaker_name or current_user.display_name or "").strip()[:80]
    history_payload = live_ai_teacher_service.build_history_messages(
        [
            {"role": msg.role, "content": msg.content}
            for msg in (payload.history or [])
        ]
    )
    message_text = payload.message.strip()
    safety = live_ai_teacher_service.evaluate_content_safety(message_text)
    if (
        bool(settings.live_ai_enable_guardrails)
        and bool(settings.live_ai_block_unsafe_content)
        and not safety.get("is_safe", True)
    ):
        guardrail_answer = live_ai_teacher_service.safety_response(
            categories=list(safety.get("categories") or [])
        )
        rubric = live_ai_teacher_service.build_rubric_feedback(
            question=message_text,
            answer=guardrail_answer,
            cluster=live_ai_teacher_service.infer_heritage_cluster(
                message=message_text,
                session_title=live_session.title,
            ),
        )
        live_session_service.record_live_event(
            db,
            live_session_id=live_session.id,
            event_type="ai_guardrail_blocked",
            event_source="ai_teacher_api",
            participant_identity=live_session_service.participant_identity_for_user(
                current_user
            ),
            participant_user_id=current_user.id,
            payload={
                "categories": safety.get("categories", []),
                "message_redacted": message_text[:120],
            },
        )
        live_reporting_service.create_session_action(
            db,
            live_session_id=live_session.id,
            action_type="guardrail_blocked",
            status="blocked",
            actor_identity=live_session_service.participant_identity_for_user(
                current_user
            ),
            actor_user_id=current_user.id,
            payload={"categories": safety.get("categories", [])},
        )
        db.commit()
        return schemas.LiveAITeacherReplyOut(
            mode="hint-first",
            answer=guardrail_answer,
            provider="guardrail",
            model="live-safety-v1",
            used_mock=True,
            forced_hint_first=True,
            references=[],
            citations=[],
            suggested_actions=[],
            rubric=schemas.LiveAITeacherRubricOut(
                understanding_level=str(rubric.get("understanding_level") or "needs_support"),
                knowledge_gaps=[str(item) for item in (rubric.get("knowledge_gaps") or [])],
                next_steps=[str(item) for item in (rubric.get("next_steps") or [])],
            ),
            persona=persona_grade,
            checkpoint=None,
        )

    cluster = live_ai_teacher_service.infer_heritage_cluster(
        message=message_text,
        session_title=live_session.title,
    )
    references = live_ai_teacher_service.collect_reference_sources(
        db,
        query=message_text,
        limit=3,
    )
    references_prompt = live_ai_teacher_service.format_reference_context(references)
    system_prompt = live_ai_teacher_service.build_system_prompt(
        mode=mode,
        session_title=live_session.title,
        learner_message=message_text,
        grade_level=persona_grade,
        speaker_name=speaker_name,
        student_memory=live_ai_teacher_service.summarize_student_memory(db, user_id=current_user.id),
    )
    if references_prompt:
        system_prompt = (
            f"{system_prompt}\n\n"
            "Nguon tham khao noi bo uu tien (chi dung de doi chieu, khong can gan ma [S#]):\n"
            f"{references_prompt}"
        )
    messages = [
        {"role": "system", "content": system_prompt},
        *history_payload,
        {"role": "user", "content": message_text},
    ]
    suggested_actions = live_ai_teacher_service.build_suggested_actions(
        question=message_text,
        mode=mode,
        cluster=cluster,
    )
    checkpoint_prompt: str | None = None
    if live_ai_teacher_service.should_trigger_checkpoint(
        db,
        live_session_id=live_session.id,
        session_started_at=live_session.starts_at,
    ):
        checkpoint_prompt = live_ai_teacher_service.build_checkpoint_prompt(cluster=cluster)
    live_session_service.record_live_event(
        db,
        live_session_id=live_session.id,
        event_type="ai_teacher_user_message",
        event_source="ai_teacher_api",
        participant_identity=live_session_service.participant_identity_for_user(current_user),
        participant_user_id=current_user.id,
        payload={
            "requested_mode": requested_mode,
            "mode": mode,
            "message": message_text,
            "forced_hint_first": forced_hint_first,
            "cluster": cluster,
        },
    )

    prompt_tokens = live_reporting_service.estimate_tokens(system_prompt) + sum(
        live_reporting_service.estimate_tokens(item.get("content", ""))
        for item in messages
    )
    projected_cost = live_reporting_service.estimate_deepseek_cost_usd(
        input_tokens=prompt_tokens,
        output_tokens=240,
    )
    try:
        live_reporting_service.ensure_within_cost_ceiling(
            db,
            live_session=live_session,
            projected_additional_cost=projected_cost,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=429, detail=str(exc))

    provider = "fallback_policy"
    model_name = "heritage-guidance-v1"
    used_mock = True
    llm_started = time.perf_counter()

    if settings.deepseek_api_key:
        try:
            live_circuit_service.assert_provider_available("deepseek")
            answer = _call_deepseek_chat(messages, temperature=0.3)
            live_circuit_service.record_success("deepseek")
            provider = "deepseek"
            model_name = settings.deepseek_model
            used_mock = False
            live_observability_service.record_point(
                session_id=str(live_session.id),
                operation="llm_reply",
                provider="deepseek",
                latency_ms=(time.perf_counter() - llm_started) * 1000.0,
                ok=True,
                tokens_in=prompt_tokens,
                tokens_out=live_reporting_service.estimate_tokens(answer),
            )
        except Exception as exc:
            # Catch broadly (RuntimeError, TimeoutError, network errors, etc.)
            # so a flaky upstream LLM never turns into a 500 for the learner —
            # we degrade to the curated heritage fallback response instead.
            live_circuit_service.record_failure("deepseek", str(exc))
            logger.warning("AI teacher reply fell back to canned response: %s", exc)
            live_observability_service.record_point(
                session_id=str(live_session.id),
                operation="llm_reply",
                provider="deepseek",
                latency_ms=(time.perf_counter() - llm_started) * 1000.0,
                ok=False,
                drop=False,
                tokens_in=prompt_tokens,
                tokens_out=0,
            )
            answer = live_ai_teacher_service.fallback_response(
                mode=mode,
                question=payload.message,
            )
        if checkpoint_prompt:
            answer = (
                f"{answer.strip()}\n\n"
                f"Checkpoint nhanh: {checkpoint_prompt}"
            )
            live_session_service.record_live_event(
                db,
                live_session_id=live_session.id,
                event_type=live_ai_teacher_service.CHECKPOINT_EVENT_TYPE,
                event_source="ai_teacher_api",
                participant_identity=ai_participant.participant_identity,
                participant_user_id=None,
                payload={
                    "mode": mode,
                    "cluster": cluster,
                    "prompt": checkpoint_prompt,
                },
            )
        answer, citation_items = live_ai_teacher_service.apply_citation_tags(
            answer,
            references,
        )
        rubric = live_ai_teacher_service.build_rubric_feedback(
            question=message_text,
            answer=answer,
            cluster=cluster,
        )
        if provider == "deepseek":
            cost_usd = live_reporting_service.estimate_deepseek_cost_usd(
                input_tokens=prompt_tokens,
                output_tokens=live_reporting_service.estimate_tokens(answer),
            )
            live_reporting_service.record_ai_cost(
                db,
                live_session=live_session,
                component="llm",
                cost_usd=cost_usd,
                token_in=prompt_tokens,
                token_out=live_reporting_service.estimate_tokens(answer),
                metadata={
                    "provider": provider,
                    "model": model_name,
                },
            )
        live_reporting_service.create_session_action(
            db,
            live_session_id=live_session.id,
            action_type="rubric_feedback",
            status="done",
            actor_identity=ai_participant.participant_identity,
            payload=rubric,
        )
        live_session_service.record_live_event(
            db,
            live_session_id=live_session.id,
            event_type="ai_teacher_reply",
            event_source="ai_teacher_api",
            participant_identity=ai_participant.participant_identity,
            participant_user_id=None,
            payload={
                "requested_mode": requested_mode,
                "mode": mode,
                "provider": provider,
                "model": model_name,
                "answer": answer,
                "used_mock": used_mock,
                "forced_hint_first": forced_hint_first,
                "cluster": cluster,
                "references": references,
                "citations": citation_items,
                "rubric": rubric,
                "persona": persona_grade,
                "suggested_actions": suggested_actions,
                "checkpoint_prompt": checkpoint_prompt,
            },
        )
        db.commit()
        return schemas.LiveAITeacherReplyOut(
            mode=mode,
            answer=answer,
            provider=provider,
            model=model_name,
            used_mock=used_mock,
            forced_hint_first=forced_hint_first,
            references=[
                schemas.LiveAITeacherReferenceOut(
                    source_type=str(item.get("source_type") or "context"),
                    source_id=item.get("source_id"),
                    title=str(item.get("title") or "Nguon noi bo"),
                    snippet=item.get("snippet"),
                )
                for item in references
            ],
            citations=[
                schemas.LiveAITeacherCitationOut(
                    tag=str(item.get("tag") or ""),
                    title=str(item.get("title") or "Nguon noi bo"),
                    source_type=str(item.get("source_type") or "context"),
                    source_id=(str(item.get("source_id")) if item.get("source_id") else None),
                    snippet=item.get("snippet"),
                )
                for item in citation_items
                if item.get("tag")
            ],
            suggested_actions=[
                schemas.LiveAITeacherActionOut(
                    label=str(item.get("label") or "Hoc tiep"),
                    prompt=str(item.get("prompt") or ""),
                )
                for item in suggested_actions
                if item.get("prompt")
            ],
            rubric=schemas.LiveAITeacherRubricOut(
                understanding_level=str(rubric.get("understanding_level") or "developing"),
                knowledge_gaps=[str(item) for item in (rubric.get("knowledge_gaps") or [])],
                next_steps=[str(item) for item in (rubric.get("next_steps") or [])],
            ),
            persona=persona_grade,
            checkpoint=(
                schemas.LiveAITeacherCheckpointOut(prompt=checkpoint_prompt)
                if checkpoint_prompt
                else None
            ),
        )

    answer = live_ai_teacher_service.fallback_response(
        mode=mode,
        question=payload.message,
    )
    if checkpoint_prompt:
        answer = (
            f"{answer.strip()}\n\n"
            f"Checkpoint nhanh: {checkpoint_prompt}"
        )
        live_session_service.record_live_event(
            db,
            live_session_id=live_session.id,
            event_type=live_ai_teacher_service.CHECKPOINT_EVENT_TYPE,
            event_source="ai_teacher_api",
            participant_identity=ai_participant.participant_identity,
            participant_user_id=None,
            payload={
                "mode": mode,
                "cluster": cluster,
                "prompt": checkpoint_prompt,
            },
        )
    answer, citation_items = live_ai_teacher_service.apply_citation_tags(answer, references)
    rubric = live_ai_teacher_service.build_rubric_feedback(
        question=message_text,
        answer=answer,
        cluster=cluster,
    )
    live_reporting_service.create_session_action(
        db,
        live_session_id=live_session.id,
        action_type="rubric_feedback",
        status="done",
        actor_identity=ai_participant.participant_identity,
        payload=rubric,
    )
    live_session_service.record_live_event(
        db,
        live_session_id=live_session.id,
        event_type="ai_teacher_reply",
        event_source="ai_teacher_api",
        participant_identity=ai_participant.participant_identity,
        participant_user_id=None,
        payload={
            "requested_mode": requested_mode,
            "mode": mode,
            "provider": "fallback_policy",
            "model": "heritage-guidance-v1",
            "answer": answer,
            "used_mock": True,
            "forced_hint_first": forced_hint_first,
            "cluster": cluster,
            "references": references,
            "citations": citation_items,
            "rubric": rubric,
            "persona": persona_grade,
            "suggested_actions": suggested_actions,
            "checkpoint_prompt": checkpoint_prompt,
        },
    )
    db.commit()
    return schemas.LiveAITeacherReplyOut(
        mode=mode,
        answer=answer,
        provider="fallback_policy",
        model="heritage-guidance-v1",
        used_mock=True,
        forced_hint_first=forced_hint_first,
        references=[
            schemas.LiveAITeacherReferenceOut(
                source_type=str(item.get("source_type") or "context"),
                source_id=item.get("source_id"),
                title=str(item.get("title") or "Nguon noi bo"),
                snippet=item.get("snippet"),
            )
            for item in references
        ],
        citations=[
            schemas.LiveAITeacherCitationOut(
                tag=str(item.get("tag") or ""),
                title=str(item.get("title") or "Nguon noi bo"),
                source_type=str(item.get("source_type") or "context"),
                source_id=(str(item.get("source_id")) if item.get("source_id") else None),
                snippet=item.get("snippet"),
            )
            for item in citation_items
            if item.get("tag")
        ],
        suggested_actions=[
            schemas.LiveAITeacherActionOut(
                label=str(item.get("label") or "Hoc tiep"),
                prompt=str(item.get("prompt") or ""),
            )
            for item in suggested_actions
            if item.get("prompt")
        ],
        rubric=schemas.LiveAITeacherRubricOut(
            understanding_level=str(rubric.get("understanding_level") or "developing"),
            knowledge_gaps=[str(item) for item in (rubric.get("knowledge_gaps") or [])],
            next_steps=[str(item) for item in (rubric.get("next_steps") or [])],
        ),
        persona=persona_grade,
        checkpoint=(
            schemas.LiveAITeacherCheckpointOut(prompt=checkpoint_prompt)
            if checkpoint_prompt
            else None
        ),
    )


@router.post("/api/v1/live-sessions/{live_session_id}/ai-teacher/reply/stream")
def live_ai_teacher_reply_stream(
    live_session_id: UUID,
    payload: schemas.LiveAITeacherRequestIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Server-Sent Events variant of /ai-teacher/reply.

    Streams answer tokens as they are produced so the UI can show the reply
    appearing live, then emits a final `done` event with the full structured
    payload (citations/rubric/persona). Falls back to the non-streaming call if
    streaming is unavailable. The client uses the full answer for TTS.
    """
    from .services import live_circuit_breaker as live_circuit_service
    from .services import live_ai_teacher as live_ai_teacher_service
    from .services import live_session_reporting as live_reporting_service
    from .services import live_sessions as live_session_service

    live_session = live_session_service.get_live_session(db, live_session_id)
    if live_session is None:
        raise HTTPException(status_code=404, detail="Live session not found")
    _check_live_rate_limit(
        db=db, user=current_user, bucket="ai-reply", ai_path=True, live_session_id=live_session.id
    )
    if live_session.status == LiveSessionStatus.ended.value:
        raise HTTPException(status_code=400, detail="Live session has ended")
    try:
        live_session_service.ensure_user_can_access_live_session(
            db, user=current_user, live_session=live_session
        )
    except PermissionError:
        raise HTTPException(status_code=403, detail="Not authorized")
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    if not live_session_service.is_ai_enabled(live_session):
        raise HTTPException(status_code=423, detail="AI teacher is disabled by host")

    ai_participant = live_session_service.ensure_ai_teacher_participant(
        db, live_session=live_session, display_name="AI Teacher", event_source="ai_teacher_api"
    )
    session_metadata = (
        live_session.session_metadata if isinstance(live_session.session_metadata, dict) else {}
    )
    persona_grade = live_ai_teacher_service.normalize_grade_level(
        str(payload.grade_level or session_metadata.get("grade_level") or settings.live_default_grade_level)
    )
    requested_mode = live_ai_teacher_service.normalize_mode(payload.mode)
    mode = requested_mode
    forced_hint_first = False
    if requested_mode in live_ai_teacher_service.MODERATOR_ONLY_MODES and not live_session_service.can_user_moderate_live_session(
        db, user=current_user, live_session=live_session, allow_cohost=True
    ):
        mode = "hint-first"
        forced_hint_first = True
    speaker_name = (payload.speaker_name or current_user.display_name or "").strip()[:80]
    message_text = payload.message.strip()
    history_payload = live_ai_teacher_service.build_history_messages(
        [{"role": m.role, "content": m.content} for m in (payload.history or [])]
    )

    safety = live_ai_teacher_service.evaluate_content_safety(message_text)
    blocked = (
        bool(settings.live_ai_enable_guardrails)
        and bool(settings.live_ai_block_unsafe_content)
        and not safety.get("is_safe", True)
    )
    cluster = live_ai_teacher_service.infer_heritage_cluster(
        message=message_text, session_title=live_session.title
    )
    references = [] if blocked else live_ai_teacher_service.collect_reference_sources(
        db, query=message_text, limit=3
    )
    references_prompt = live_ai_teacher_service.format_reference_context(references)
    system_prompt = live_ai_teacher_service.build_system_prompt(
        mode=mode,
        session_title=live_session.title,
        learner_message=message_text,
        grade_level=persona_grade,
        speaker_name=speaker_name,
        student_memory=live_ai_teacher_service.summarize_student_memory(db, user_id=current_user.id),
    )
    if references_prompt:
        system_prompt = (
            f"{system_prompt}\n\nNguon tham khao noi bo uu tien:\n{references_prompt}"
        )
    messages = [
        {"role": "system", "content": system_prompt},
        *history_payload,
        {"role": "user", "content": message_text},
    ]
    # Record the user message turn for the shared transcript.
    live_session_service.record_live_event(
        db,
        live_session_id=live_session.id,
        event_type="ai_teacher_user_message",
        event_source="ai_teacher_api",
        participant_identity=live_session_service.participant_identity_for_user(current_user),
        participant_user_id=current_user.id,
        payload={"requested_mode": requested_mode, "mode": mode, "message": message_text, "cluster": cluster},
    )
    db.commit()

    def _sse(obj: dict) -> str:
        return f"data: {json.dumps(obj, ensure_ascii=False)}\n\n"

    def _generate():
        prompt_tokens = live_reporting_service.estimate_tokens(system_prompt) + sum(
            live_reporting_service.estimate_tokens(m.get("content", "")) for m in messages
        )
        provider = "deepseek"
        model_name = settings.deepseek_model
        answer = ""
        if blocked:
            answer = live_ai_teacher_service.safety_response(
                categories=list(safety.get("categories") or [])
            )
            provider, model_name = "guardrail", "live-safety-v1"
            yield _sse({"delta": answer})
        else:
            try:
                live_circuit_service.assert_provider_available("deepseek")
                for delta in _call_deepseek_chat_stream(messages, temperature=0.3):
                    if not delta:
                        continue
                    answer += delta
                    yield _sse({"delta": delta})
                live_circuit_service.record_success("deepseek")
            except Exception as exc:  # noqa: BLE001 — degrade gracefully
                live_circuit_service.record_failure("deepseek", str(exc))
                logger.warning("AI teacher stream fell back: %s", exc)
                if not answer.strip():
                    try:
                        answer = _call_deepseek_chat(messages, temperature=0.3)
                        yield _sse({"delta": answer})
                    except Exception:  # noqa: BLE001
                        answer = live_ai_teacher_service.fallback_response(mode=mode, question=message_text)
                        provider, model_name = "fallback_policy", "heritage-guidance-v1"
                        yield _sse({"delta": answer})

        answer, citation_items = live_ai_teacher_service.apply_citation_tags(answer, references)
        rubric = live_ai_teacher_service.build_rubric_feedback(
            question=message_text, answer=answer, cluster=cluster
        )
        try:
            if provider == "deepseek":
                live_reporting_service.record_ai_cost(
                    db,
                    live_session=live_session,
                    component="llm",
                    cost_usd=live_reporting_service.estimate_deepseek_cost_usd(
                        input_tokens=prompt_tokens,
                        output_tokens=live_reporting_service.estimate_tokens(answer),
                    ),
                    token_in=prompt_tokens,
                    token_out=live_reporting_service.estimate_tokens(answer),
                    metadata={"provider": provider, "model": model_name},
                )
            live_session_service.record_live_event(
                db,
                live_session_id=live_session.id,
                event_type="ai_teacher_reply",
                event_source="ai_teacher_api",
                participant_identity=ai_participant.participant_identity,
                participant_user_id=None,
                payload={
                    "mode": mode,
                    "provider": provider,
                    "model": model_name,
                    "answer": answer,
                    "cluster": cluster,
                    "references": references,
                    "citations": citation_items,
                    "rubric": rubric,
                    "persona": persona_grade,
                },
            )
            db.commit()
        except Exception as exc:  # noqa: BLE001
            logger.warning("AI teacher stream post-processing failed: %s", exc)
            db.rollback()

        yield _sse({
            "done": True,
            "answer": answer,
            "mode": mode,
            "provider": provider,
            "model": model_name,
            "forced_hint_first": forced_hint_first,
            "persona": persona_grade,
            "citations": [c for c in citation_items if c.get("tag")],
            "rubric": rubric,
        })

    return StreamingResponse(
        _generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post(
    "/api/v1/live-sessions/{live_session_id}/end",
    response_model=schemas.LiveSessionOut,
)
def end_live_session_room(
    live_session_id: UUID,
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db),
) -> schemas.LiveSessionOut:
    from .services import live_sessions as live_session_service

    live_session = live_session_service.get_live_session(db, live_session_id)
    if live_session is None:
        raise HTTPException(status_code=404, detail="Live session not found")

    try:
        live_session_service.ensure_user_can_manage_live_session(
            db, user=current_user, live_session=live_session
        )
        live_session = live_session_service.end_live_session(
            db,
            live_session,
            ended_by_user_id=current_user.id,
        )
    except PermissionError:
        raise HTTPException(status_code=403, detail="Not authorized")
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    return _build_live_session_out(db, live_session)


@router.get(
    "/api/v1/live-sessions/{live_session_id}/dashboard",
    response_model=schemas.SessionDashboardOut,
)
def get_live_session_dashboard(
    live_session_id: UUID,
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db),
) -> schemas.SessionDashboardOut:
    from .services import live_observability as live_observability_service
    from .services import live_session_reporting as live_reporting_service
    from .services import live_sessions as live_session_service

    live_session = live_session_service.get_live_session(db, live_session_id)
    if live_session is None:
        raise HTTPException(status_code=404, detail="Live session not found")

    try:
        live_session_service.ensure_user_can_access_live_session(
            db, user=current_user, live_session=live_session
        )
    except PermissionError:
        raise HTTPException(status_code=403, detail="Not authorized")
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    payload = live_reporting_service.build_dashboard_payload(
        db,
        live_session=live_session,
    )
    payload["observability"] = live_observability_service.snapshot(
        session_id=str(live_session.id)
    )
    db.commit()
    return schemas.SessionDashboardOut.model_validate(payload)


@router.get(
    "/api/v1/live-sessions/{live_session_id}/transcripts/export.json",
    response_model=schemas.SessionTranscriptExportOut,
)
def export_live_session_transcripts_json(
    live_session_id: UUID,
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db),
) -> schemas.SessionTranscriptExportOut:
    from .services import live_session_reporting as live_reporting_service
    from .services import live_sessions as live_session_service

    live_session = live_session_service.get_live_session(db, live_session_id)
    if live_session is None:
        raise HTTPException(status_code=404, detail="Live session not found")
    try:
        live_session_service.ensure_user_can_access_live_session(
            db, user=current_user, live_session=live_session
        )
    except PermissionError:
        raise HTTPException(status_code=403, detail="Not authorized")
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    payload = live_reporting_service.export_transcripts_json(
        db,
        live_session_id=live_session.id,
    )
    db.commit()
    return schemas.SessionTranscriptExportOut.model_validate(payload)


@router.get("/api/v1/live-sessions/{live_session_id}/transcripts/export.csv")
def export_live_session_transcripts_csv(
    live_session_id: UUID,
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db),
) -> Response:
    from .services import live_session_reporting as live_reporting_service
    from .services import live_sessions as live_session_service

    live_session = live_session_service.get_live_session(db, live_session_id)
    if live_session is None:
        raise HTTPException(status_code=404, detail="Live session not found")
    try:
        live_session_service.ensure_user_can_access_live_session(
            db, user=current_user, live_session=live_session
        )
    except PermissionError:
        raise HTTPException(status_code=403, detail="Not authorized")
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    csv_content = live_reporting_service.export_transcripts_csv(
        db,
        live_session_id=live_session.id,
    )
    db.commit()
    headers = {
        "Content-Disposition": f'attachment; filename="live-session-{live_session.id}-transcripts.csv"'
    }
    return Response(content=csv_content, media_type="text/csv", headers=headers)


@router.get(
    "/api/v1/live-sessions/{live_session_id}/observability",
    response_model=schemas.SessionObservabilityOut,
)
def get_live_session_observability(
    live_session_id: UUID,
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db),
) -> schemas.SessionObservabilityOut:
    from .services import live_observability as live_observability_service
    from .services import live_sessions as live_session_service

    live_session = live_session_service.get_live_session(db, live_session_id)
    if live_session is None:
        raise HTTPException(status_code=404, detail="Live session not found")
    try:
        live_session_service.ensure_user_can_access_live_session(
            db, user=current_user, live_session=live_session
        )
    except PermissionError:
        raise HTTPException(status_code=403, detail="Not authorized")
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    return schemas.SessionObservabilityOut.model_validate(
        live_observability_service.snapshot(session_id=str(live_session.id))
    )


@router.post("/api/v1/admin/live-sessions/maintenance/cleanup")
def admin_live_sessions_cleanup(
    max_age_hours: int = Query(24, ge=1, le=168),
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    del current_user
    from .services import live_rate_limits as live_rate_limit_service
    from .services import live_session_reporting as live_reporting_service

    live_reporting_service.cleanup_expired_reporting_data(db)
    rate_limit_deleted = live_rate_limit_service.cleanup_old_logs(
        db,
        max_age_hours=max_age_hours,
    )
    db.commit()
    return {
        "ok": True,
        "rate_limit_logs_deleted": rate_limit_deleted,
        "max_age_hours": max_age_hours,
    }
