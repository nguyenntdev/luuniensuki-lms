# -*- coding: utf-8 -*-
"""Content: motifs, urns, lessons, quizzes, exams, certificates, tags & search (backend-modularization router extraction).

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
    BADGE_COLLECTOR_10,
    BADGE_COLLECTOR_50,
    BADGE_EXPLORER_ALL_URNS,
    BADGE_FIRST_DISCOVERY,
    BADGE_FIRST_MASTERED,
    BADGE_PERFECT_SCORE,
    BADGE_QUIZ_MASTER,
    BADGE_SPEED_DEMON,
    BADGE_STREAK_7,
    DISCOVERY_XP,
    LESSON_XP,
    MASTERED_XP,
    QUIZ_PASS_PERCENT,
    URN_EXAM_PASS_PERCENT,
    URN_EXAM_PASS_XP,
    _call_deepseek_chat,
    _collect_ai_sources,
    _count_user_discoveries,
    _ensure_urn_exam_eligibility,
    _record_analytics_event,
    _select_urn_exam_questions,
    get_allowed_content_ratings,
)

logger = logging.getLogger("luuniensuki.api")

router = APIRouter()


@router.get("/motifs/{urn_name}", response_model=MotifsByUrnResponse)
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


@router.get("/api/v1/urns/{urn_slug}/progress", response_model=UrnProgressResponse)
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


@router.get("/api/v1/urns", response_model=list[UrnListItemOut])
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


@router.get("/api/v1/urns/{urn_slug}", response_model=UrnDetailResponse)
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


@router.get("/api/v1/motifs/{motif_id}", response_model=MotifDetailOut)
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


@router.post(
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


@router.get("/api/v1/lessons/cache-manifest", response_model=schemas.CacheManifestOut)
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


@router.post("/api/v1/lessons/{lesson_id}/cache", response_model=schemas.LessonCacheOut)
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


@router.delete("/api/v1/lessons/{lesson_id}/cache", status_code=status.HTTP_204_NO_CONTENT)
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


@router.get("/api/v1/lessons/cached", response_model=list[schemas.LessonCacheOut])
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


@router.get("/api/v1/lessons/next", response_model=schemas.NextLessonOut)
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
    from ..services import lesson_sequence

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


@router.get(
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
    from ..services import lesson_sequence

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


@router.get(
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
    from ..services import lesson_sequence

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


@router.get("/api/v1/lessons/sequence", response_model=schemas.LessonSequenceOut)
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
    from ..services import lesson_sequence

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


@router.post("/progress/unlock", response_model=ProgressUnlockResponse)
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


@router.get("/api/v1/content/ratings", response_model=schemas.ContentRatingsOut)
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


@router.get("/api/v1/motifs/{motif_id}/quiz", response_model=MotifQuizResponse)
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


@router.post("/api/v1/quizzes/submit", response_model=QuizSubmitResponse)
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


@router.get("/api/v1/quiz/adaptive", response_model=schemas.AdaptiveQuizOut)
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
                explanation=q.explanation,
            )
        )

    return schemas.AdaptiveQuizOut(
        motif_id=motif_id,
        skill_type=skill_type,
        recommended_difficulty=recommended_difficulty,
        questions=question_outs,
    )


@router.post(
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


@router.get(
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


@router.get("/api/v1/urns/{urn_slug}/exam", response_model=UrnExamResponse)
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


@router.post("/api/v1/urns/{urn_slug}/exam/submit", response_model=UrnExamSubmitResponse)
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


@router.get("/api/v1/users/me/exam-attempts", response_model=list[UrnExamAttemptOut])
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


@router.get(
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


@router.get("/api/v1/certificates/{code}", response_model=CertificateVerifyOut)
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


@router.get("/api/v1/users/me/certificates", response_model=list[CertificateOut])
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


@router.get("/api/v1/tags", response_model=list[TagOut])
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


@router.get("/api/v1/search", response_model=SearchResponse)
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
