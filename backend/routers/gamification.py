# -*- coding: utf-8 -*-
"""Gamification & progression: streak, XP, badges, milestones, hearts, missions, leaderboard, recommendations, review & learning path (backend-modularization router extraction).

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
    _apply_quest_rewards,
    _build_quest_rewards,
    _build_rules_recommendations,
    _compute_quest_progress_data,
    _ensure_daily_missions_for_user,
    _ensure_weekly_quests_for_user,
    _extract_next_objective,
    _format_learning_path_response,
    _generate_llm_recommendations,
    _get_rag_settings,
    _load_daily_goal_settings,
    _normalize_recommendation_items,
    _quest_prerequisite_completed,
    _resolve_daily_goal_level,
    _store_recommendation,
    get_allowed_content_ratings,
)

logger = logging.getLogger("luuniensuki.api")

# ``get_dashboard_summary`` reuses the content router's ``list_urns`` query
# function exactly as the monolith did (direct call, not via HTTP). Importing it
# here keeps that behavior; the import is one-way (``content`` never imports this
# module) so no cycle is introduced.
from .content import list_urns  # noqa: E402

router = APIRouter()


@router.get("/api/v1/quests", response_model=list[QuestListItemOut])
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


@router.get("/api/v1/quests/{quest_slug}", response_model=QuestDetailOut)
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


@router.post("/api/v1/quests/{quest_slug}/start", response_model=QuestDetailOut)
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


@router.get("/api/v1/users/me/quest-summary", response_model=Optional[QuestSummaryOut])
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


@router.get("/api/v1/users/me/streak", response_model=StreakResponse)
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


@router.get("/api/v1/dashboard/summary", response_model=DashboardSummaryOut)
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


@router.post("/api/v1/users/me/streak/freeze", response_model=StreakResponse)
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


@router.post("/api/v1/streak/freeze", response_model=StreakFreezeResponse)
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


@router.get("/api/v1/users/me/xp-boost", response_model=schemas.XpBoostStatusOut)
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


@router.post(
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


@router.get("/api/v1/users/me/badges", response_model=list[UserBadgeOut])
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


@router.get("/api/v1/milestones", response_model=schemas.MilestoneListOut)
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


@router.get(
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


@router.post(
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


@router.get("/api/v1/leaderboard", response_model=schemas.EnhancedLeaderboardOut)
def get_leaderboard(
    scope: str = Query("global", regex="^(global|friends|class)$"),
    limit: int = Query(50, ge=1, le=200),
    order_by: str = Query("xp", regex="^(xp|streak)$"),
    classroom_id: Optional[UUID] = Query(
        None, description="Required when scope=class"
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.EnhancedLeaderboardOut:
    """
    Get leaderboard with optional scope filtering.

    Scopes:
    - global: All users (default)
    - friends: Only mutual follows
    - class: Classroom leaderboard (requires classroom_id)

    Order by:
    - xp: Total experience points (default)
    - streak: Current streak
    """
    from .services import leaderboard as leaderboard_service

    if scope == "class":
        from .services import student_progress as progress_service

        if classroom_id is None:
            raise HTTPException(
                status_code=422, detail="classroom_id is required when scope=class"
            )

        classroom = db.get(Classroom, classroom_id)
        if classroom is None:
            raise HTTPException(status_code=404, detail="Classroom not found")

        if current_user.role not in ADMIN_ROLES:
            if current_user.role == UserRole.teacher:
                if classroom.teacher_id != current_user.id:
                    raise HTTPException(
                        status_code=403, detail="Not authorized to view this classroom"
                    )
            else:
                membership = db.execute(
                    select(ClassMember.id).where(
                        ClassMember.class_id == classroom_id,
                        ClassMember.user_id == current_user.id,
                    )
                ).scalar_one_or_none()
                if membership is None:
                    raise HTTPException(
                        status_code=403, detail="Not enrolled in this classroom"
                    )

        total_users = (
            db.execute(
                select(func.count(ClassMember.id)).where(
                    ClassMember.class_id == classroom_id,
                    ClassMember.role == "learner",
                )
            ).scalar_one()
            or 0
        )

        full_entries = progress_service.get_class_leaderboard(
            db=db,
            classroom_id=classroom_id,
            limit=max(total_users, limit),
            order_by=order_by,
        )
        user_rank = next(
            (
                int(entry["rank"])
                for entry in full_entries
                if entry["student_id"] == current_user.id
            ),
            None,
        )
        class_entries = full_entries[:limit]

        avatar_map = {}
        user_ids = [entry["student_id"] for entry in class_entries]
        if user_ids:
            avatar_rows = db.execute(
                select(User.id, User.avatar_url).where(User.id.in_(user_ids))
            ).all()
            avatar_map = {user_id: avatar_url for user_id, avatar_url in avatar_rows}

        entries = [
            {
                "rank": int(entry["rank"]),
                "user_id": entry["student_id"],
                "display_name": entry["display_name"],
                "avatar_url": avatar_map.get(entry["student_id"]),
                "total_xp": int(entry["total_xp"]),
                "current_streak": int(entry.get("current_streak", 0)),
            }
            for entry in class_entries
        ]
    elif scope == "friends":
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


@router.get("/api/v1/leaderboard/friends", response_model=schemas.EnhancedLeaderboardOut)
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


@router.get("/api/v1/leaderboard/settings", response_model=schemas.LeaderboardSettingsOut)
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


@router.put("/api/v1/leaderboard/settings", response_model=schemas.LeaderboardSettingsOut)
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


@router.get("/api/v1/skills", response_model=schemas.UserSkillsOut)
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


@router.post("/api/v1/skills/recalculate", response_model=schemas.UserSkillsOut)
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


@router.get("/api/v1/users/me/recommendations", response_model=RecommendationOut)
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


@router.post("/api/v1/users/me/recommendations/refresh", response_model=RecommendationOut)
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


@router.get("/api/v1/recommendations", response_model=schemas.RecommendationsOut)
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


@router.get(
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


@router.post(
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


@router.post(
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


@router.get("/api/v1/ranks", response_model=list[RankListItemOut])
def list_ranks(
    current_user: User = Depends(get_current_user),
) -> list[RankListItemOut]:
    """List all XP ranks."""
    return [
        RankListItemOut(level=r["level"], name=r["name"], xp=r["xp"]) for r in XP_RANKS
    ]


@router.get("/api/v1/badges", response_model=list[BadgeListItemOut])
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


@router.get("/api/v1/daily-goal/settings", response_model=DailyGoalSettingsOut)
def get_daily_goal_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DailyGoalSettingsOut:
    """Get daily-goal settings for current user."""
    return _load_daily_goal_settings(db, current_user)


@router.put("/api/v1/daily-goal/settings", response_model=DailyGoalSettingsOut)
def update_daily_goal_settings(
    payload: DailyGoalSettingsUpdateIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DailyGoalSettingsOut:
    """Update daily-goal settings for current user."""
    goal_level = _resolve_daily_goal_level(payload)
    xp_target = DAILY_GOAL_LEVELS[goal_level]
    now = datetime.now(timezone.utc)

    from .services.analytics import create_event_record

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


@router.get("/api/v1/daily-missions", response_model=DailyMissionsResponse)
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


@router.post(
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


@router.get("/api/v1/daily-missions/history", response_model=DailyMissionHistoryResponse)
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


@router.get("/api/v1/streak", response_model=StreakStatusOut)
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


@router.post("/api/v1/streak/claim-daily", response_model=ClaimDailyStreakOut)
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


@router.post("/api/v1/streak/use-freeze", response_model=UseStreakFreezeOut)
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


@router.get("/api/v1/hearts", response_model=schemas.HeartsStatusOut)
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


@router.post("/api/v1/hearts/use", response_model=schemas.UseHeartOut)
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


@router.post("/api/v1/hearts/refill", response_model=schemas.RefillHeartsOut)
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


@router.post(
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


@router.get("/api/v1/hearts/transactions", response_model=schemas.HeartTransactionListOut)
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


@router.get("/api/v1/weekly-quests", response_model=schemas.WeeklyQuestsResponse)
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


@router.post(
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


@router.get(
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


@router.get("/api/v1/review/due", response_model=schemas.DueCardsOut)
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


@router.post("/api/v1/review/{card_id}", response_model=schemas.SpacedRepetitionCardOut)
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


@router.get("/api/v1/learning-path/today", response_model=schemas.LearningPathOut)
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


@router.post("/api/v1/learning-path/generate", response_model=schemas.LearningPathOut)
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


@router.post(
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


@router.get("/api/v1/learning-path/history", response_model=schemas.LearningPathHistoryOut)
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


@router.get("/api/v1/learning-path/stats", response_model=schemas.LearningPathStatsOut)
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


@router.get("/api/v1/review/stats", response_model=schemas.ReviewStatsOut)
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


@router.post("/api/v1/review/cards", response_model=schemas.SpacedRepetitionCardOut)
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
