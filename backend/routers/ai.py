# -*- coding: utf-8 -*-
"""AI assistant: tutor, Q&A, summaries, flashcards, insights, conversations & AI jobs (backend-modularization router extraction).

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
    _apply_ai_settings,
    _build_ai_citations,
    _build_qa_system_prompt,
    _build_qa_user_prompt,
    _build_rules_recommendations,
    _build_tutor_system_prompt,
    _build_tutor_user_prompt,
    _call_deepseek_chat,
    _call_deepseek_chat_stream,
    _collect_ai_sources,
    _extract_citations,
    _fail_ai_job,
    _fallback_answer_from_sources,
    _fallback_explain_text,
    _fallback_flashcards_from_sources,
    _fallback_summary_from_sources,
    _find_seed_entry,
    _finish_ai_job,
    _finish_ai_job_fallback,
    _format_sources_for_prompt,
    _generate_llm_recommendations,
    _generate_quiz_payloads_with_ai,
    _get_rag_settings,
    _lesson_payload_from_seed,
    _normalize_recommendation_items,
    _quiz_payloads_from_seed,
    _resolve_motif,
    _resolve_urn,
    _safe_parse_json,
    _sanitize_quiz_payload,
    _source_snippet,
    _start_ai_job,
    _store_quiz_payloads,
    _store_recommendation,
)

logger = logging.getLogger("luuniensuki.api")

router = APIRouter()


@router.get("/api/v1/users/me/ai-jobs", response_model=list[AIJobOut])
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


@router.post("/api/v1/users/me/ai-jobs/{job_id}/retry", response_model=RecommendationOut)
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


@router.post("/api/v1/ai/tutor", response_model=AIAnswerOut)
def ai_tutor(
    payload: AITutorRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AIAnswerOut:
    from .services.ai_tutor import apply_content_safety_filter

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
    user_prompt = _build_tutor_user_prompt(
        message=payload.message,
        sources_prompt=sources_prompt,
    )
    system_prompt = _build_tutor_system_prompt(level=payload.level)
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
        answer = apply_content_safety_filter(answer, current_user)
        _finish_ai_job(db, job, response=answer)
    except Exception as exc:
        answer = _fallback_answer_from_sources(payload.message, sources)
        answer = apply_content_safety_filter(answer, current_user)
        _finish_ai_job_fallback(db, job, response=answer, error=str(exc))

    cited_indexes = _extract_citations(answer)
    citations = _build_ai_citations(sources, cited_indexes)
    if not citations:
        citations = _build_ai_citations(sources, [])
    return AIAnswerOut(answer=answer, citations=citations, job_id=job.id)


@router.post("/api/v1/ai/tutor/stream")
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

    from .services.ai_tutor import apply_content_safety_filter

    context = payload.context or AIContextIn()
    sources = _collect_ai_sources(
        db,
        urn_slug=context.urn_slug,
        motif_id=context.motif_id,
        limit=6,
        query=payload.message,
    )
    sources_prompt = _format_sources_for_prompt(sources)
    user_prompt = _build_tutor_user_prompt(
        message=payload.message,
        sources_prompt=sources_prompt,
    )
    system_prompt = _build_tutor_system_prompt(level=payload.level)
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
        stream_chunks = bool(getattr(current_user, "age_verified", False))
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
                if stream_chunks:
                    yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"

            safe_answer = apply_content_safety_filter(accumulated_text, current_user)
            if not stream_chunks:
                yield f"data: {json.dumps({'type': 'chunk', 'content': safe_answer})}\n\n"

            # Finalize job and send completion
            _finish_ai_job(db, job, response=safe_answer)

            # Extract and send final citations
            cited_indexes = _extract_citations(safe_answer)
            final_citations = _build_ai_citations(sources, cited_indexes)
            if not final_citations:
                final_citations = _build_ai_citations(sources, [])

            yield f"data: {json.dumps({'type': 'done', 'job_id': str(job.id), 'full_response': safe_answer, 'citations': [c.dict() for c in final_citations]})}\n\n"

        except Exception as exc:
            fallback = _fallback_answer_from_sources(payload.message, sources)
            fallback = apply_content_safety_filter(fallback, current_user)
            _finish_ai_job_fallback(db, job, response=fallback, error=str(exc))
            yield f"data: {json.dumps({'type': 'error', 'error': fallback, 'message': fallback})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@router.post("/api/v1/ai/qa", response_model=AIAnswerOut)
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
    user_prompt = _build_qa_user_prompt(
        question=payload.question,
        sources_prompt=sources_prompt,
    )
    system_prompt = _build_qa_system_prompt()
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


@router.post("/api/v1/ai/qa/stream")
async def ai_qa_stream(
    payload: AIQuestionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Streaming version of AI QA endpoint using SSE."""
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
    user_prompt = _build_qa_user_prompt(
        question=payload.question,
        sources_prompt=sources_prompt,
    )
    system_prompt = _build_qa_system_prompt()
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

    job = _start_ai_job(db, user=current_user, job_type="qa_stream", prompt=user_prompt)

    async def event_generator():
        accumulated_text = ""
        try:
            for chunk in _call_deepseek_chat_stream(
                messages, temperature=temperature, model=model_override
            ):
                accumulated_text += chunk
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"

            _finish_ai_job(db, job, response=accumulated_text)
            cited_indexes = _extract_citations(accumulated_text)
            citations = _build_ai_citations(sources, cited_indexes)
            if not citations:
                citations = _build_ai_citations(sources, [])
            yield f"data: {json.dumps({'type': 'done', 'job_id': str(job.id), 'full_response': accumulated_text, 'citations': [c.dict() for c in citations]})}\n\n"
        except Exception as exc:
            fallback = _fallback_answer_from_sources(payload.question, sources)
            _finish_ai_job_fallback(db, job, response=fallback, error=str(exc))
            yield f"data: {json.dumps({'type': 'error', 'error': fallback, 'message': fallback})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@router.post("/api/v1/ai/summary", response_model=SummaryGenerateOut)
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


@router.post("/api/v1/ai/flashcards", response_model=FlashcardGenerateOut)
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


@router.post("/api/v1/ai/feedback", response_model=FeedbackGenerateOut)
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


@router.post("/api/v1/ai/coach", response_model=CoachGenerateOut)
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


@router.post("/api/v1/ai/explain", response_model=ExplainGenerateOut)
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


@router.get("/api/v1/ai/review-plan", response_model=ReviewPlanOut)
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


@router.get("/api/v1/ai/insights", response_model=schemas.AILearningInsightsResponse)
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


@router.get(
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


@router.post("/api/v1/ai/lessons/generate", response_model=LessonGenerateOut)
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


@router.post("/api/v1/ai/quizzes/generate", response_model=QuizGenerateOut)
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


@router.post("/api/v1/ai/diagnostic", response_model=DiagnosticGenerateOut)
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


@router.get("/api/v1/ai/conversations", response_model=schemas.AIConversationListOut)
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


@router.post(
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


@router.get(
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


@router.post(
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


@router.delete("/api/v1/ai/conversations/{conversation_id}", status_code=204)
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
