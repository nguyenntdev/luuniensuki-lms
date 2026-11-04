# -*- coding: utf-8 -*-
"""Classrooms, assignments, student progress & legacy classes (backend-modularization router extraction).

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
from fastapi.responses import JSONResponse, RedirectResponse, Response, StreamingResponse
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
    School,
    SchoolMember,
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
    _ensure_class_access,
    _get_experiment_or_404,
)

logger = logging.getLogger("luuniensuki.api")

router = APIRouter()


@router.get("/api/v1/classrooms", response_model=list[schemas.ClassroomSummaryOut])
def list_classrooms(
    include_archived: bool = Query(False, description="Include archived classrooms"),
    school_id: Optional[UUID] = Query(None, description="Filter by school ID"),
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db),
) -> list[schemas.ClassroomSummaryOut]:
    """
    List all classrooms for the current teacher.
    Admins can see all classrooms.
    """
    query = select(Classroom)

    if current_user.role == UserRole.teacher:
        query = query.where(Classroom.teacher_id == current_user.id)

    if not include_archived:
        query = query.where(Classroom.is_archived == False)

    if school_id:
        query = query.where(Classroom.school_id == school_id)

    classrooms = db.execute(query.order_by(Classroom.created_at.desc())).scalars().all()

    if not classrooms:
        return []

    class_ids = [c.id for c in classrooms]
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
        schemas.ClassroomSummaryOut(
            id=classroom.id,
            name=classroom.name,
            description=classroom.description,
            teacher_id=classroom.teacher_id,
            class_code=classroom.class_code,
            max_students=classroom.max_students,
            is_archived=classroom.is_archived,
            member_count=int(member_counts.get(classroom.id, 0)),
            assignment_count=int(assignment_counts.get(classroom.id, 0)),
            created_at=classroom.created_at,
            updated_at=classroom.updated_at,
            school_id=classroom.school_id,
            term=classroom.term,
        )
        for classroom in classrooms
    ]


@router.post(
    "/api/v1/classrooms", response_model=schemas.ClassroomSummaryOut, status_code=201
)
def create_classroom(
    payload: schemas.ClassroomCreateIn,
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db),
) -> schemas.ClassroomSummaryOut:
    """
    Create a new classroom.
    Generates a unique class code for students to join.
    """
    from ..services import classroom as classroom_service

    try:
        classroom = classroom_service.create_classroom(
            db=db,
            teacher=current_user,
            name=payload.name,
            description=payload.description,
            max_students=payload.max_students,
            settings=payload.settings,
            school_id=payload.school_id,
            term=payload.term,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return schemas.ClassroomSummaryOut(
        id=classroom.id,
        name=classroom.name,
        description=classroom.description,
        teacher_id=classroom.teacher_id,
        class_code=classroom.class_code,
        max_students=classroom.max_students,
        is_archived=classroom.is_archived,
        member_count=0,
        assignment_count=0,
        created_at=classroom.created_at,
        updated_at=classroom.updated_at,
        school_id=classroom.school_id,
        term=classroom.term,
    )


@router.get(
    "/api/v1/classrooms/enrolled", response_model=list[schemas.ClassroomSummaryOut]
)
def get_enrolled_classrooms(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[schemas.ClassroomSummaryOut]:
    """
    Get all classrooms where the current user is enrolled as a student.
    """
    from ..services import classroom as classroom_service

    classrooms = classroom_service.get_enrolled_classrooms(db, current_user)

    if not classrooms:
        return []

    class_ids = [c.id for c in classrooms]
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
        schemas.ClassroomSummaryOut(
            id=classroom.id,
            name=classroom.name,
            description=classroom.description,
            teacher_id=classroom.teacher_id,
            class_code=classroom.class_code,
            max_students=classroom.max_students,
            is_archived=classroom.is_archived,
            member_count=int(member_counts.get(classroom.id, 0)),
            assignment_count=int(assignment_counts.get(classroom.id, 0)),
            created_at=classroom.created_at,
            updated_at=classroom.updated_at,
            school_id=classroom.school_id,
            term=classroom.term,
        )
        for classroom in classrooms
    ]


@router.get("/api/v1/classrooms/{classroom_id}", response_model=schemas.ClassroomDetailOut)
def get_classroom(
    classroom_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.ClassroomDetailOut:
    """
    Get detailed classroom information including members and assignments.
    Only authorized for classroom teacher, admins, or enrolled students.
    """
    classroom = db.get(Classroom, classroom_id)
    if classroom is None:
        raise HTTPException(status_code=404, detail="Classroom not found")

    is_teacher_owner = (current_user.role == UserRole.teacher and classroom.teacher_id == current_user.id)
    is_admin = current_user.role in (UserRole.admin, UserRole.super_admin)
    is_enrolled = False
    if current_user.role == UserRole.learner:
        membership = db.execute(
            select(ClassMember).where(
                and_(ClassMember.class_id == classroom.id, ClassMember.user_id == current_user.id)
            )
        ).scalar_one_or_none()
        is_enrolled = (membership is not None)

    if not (is_teacher_owner or is_admin or is_enrolled):
        raise HTTPException(status_code=403, detail="Not authorized to access this classroom")

    # Get teacher info
    teacher = db.get(User, classroom.teacher_id)
    teacher_name = teacher.display_name if teacher else "Unknown"
    school_name = classroom.school.name if classroom.school else None

    # Get members with user details
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

    # Get assignment count
    assignment_count = db.execute(
        select(func.count(QuestAssignment.id)).where(
            QuestAssignment.class_id == classroom.id
        )
    ).scalar_one()

    can_view_pii = is_teacher_owner or is_admin

    return schemas.ClassroomDetailOut(
        id=classroom.id,
        name=classroom.name,
        description=classroom.description,
        teacher_id=classroom.teacher_id,
        teacher_name=teacher_name,
        class_code=classroom.class_code,
        max_students=classroom.max_students,
        is_archived=classroom.is_archived,
        settings=classroom.settings,
        school_id=classroom.school_id,
        school_name=school_name,
        term=classroom.term,
        members=[
            schemas.ClassMemberOut(
                id=member.id,
                user_id=member.user_id,
                display_name=member.user.display_name if member.user else "Unknown",
                email=member.user.email if (can_view_pii or member.user_id == current_user.id) else "",
                role=member.role,
                joined_at=member.joined_at,
                guardian_email=member.guardian_email if (can_view_pii or member.user_id == current_user.id) else None,
                guardian_consent=member.guardian_consent if (can_view_pii or member.user_id == current_user.id) else None,
            )
            for member in members
        ],
        member_count=len(members),
        assignment_count=int(assignment_count),
        created_at=classroom.created_at,
        updated_at=classroom.updated_at,
    )


@router.put("/api/v1/classrooms/{classroom_id}", response_model=schemas.ClassroomDetailOut)
def update_classroom(
    classroom_id: UUID,
    payload: schemas.ClassroomUpdateIn,
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db),
) -> schemas.ClassroomDetailOut:
    """
    Update classroom details.
    """
    from ..services import classroom as classroom_service

    classroom = db.get(Classroom, classroom_id)
    if classroom is None:
        raise HTTPException(status_code=404, detail="Classroom not found")

    _ensure_class_access(current_user, classroom)

    try:
        classroom = classroom_service.update_classroom(
            db=db,
            classroom=classroom,
            name=payload.name,
            description=payload.description,
            max_students=payload.max_students,
            settings=payload.settings,
            school_id=payload.school_id,
            term=payload.term,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return get_classroom(classroom_id, current_user, db)


@router.delete("/api/v1/classrooms/{classroom_id}", status_code=204)
def delete_classroom(
    classroom_id: UUID,
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db),
) -> None:
    """
    Delete a classroom.
    This will also delete all members and assignments.
    """
    classroom = db.get(Classroom, classroom_id)
    if classroom is None:
        raise HTTPException(status_code=404, detail="Classroom not found")

    _ensure_class_access(current_user, classroom)

    db.delete(classroom)
    db.commit()


@router.post(
    "/api/v1/classrooms/{classroom_id}/archive",
    response_model=schemas.ClassroomDetailOut,
)
def archive_classroom(
    classroom_id: UUID,
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db),
) -> schemas.ClassroomDetailOut:
    """
    Archive a classroom.
    Archived classrooms cannot accept new students but existing data is preserved.
    """
    from ..services import classroom as classroom_service

    classroom = db.get(Classroom, classroom_id)
    if classroom is None:
        raise HTTPException(status_code=404, detail="Classroom not found")

    _ensure_class_access(current_user, classroom)

    if classroom.is_archived:
        raise HTTPException(status_code=400, detail="Classroom is already archived")

    classroom_service.archive_classroom(db, classroom)

    return get_classroom(classroom_id, current_user, db)


@router.post(
    "/api/v1/classrooms/{classroom_id}/unarchive",
    response_model=schemas.ClassroomDetailOut,
)
def unarchive_classroom(
    classroom_id: UUID,
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db),
) -> schemas.ClassroomDetailOut:
    """
    Unarchive a classroom.
    """
    from ..services import classroom as classroom_service

    classroom = db.get(Classroom, classroom_id)
    if classroom is None:
        raise HTTPException(status_code=404, detail="Classroom not found")

    _ensure_class_access(current_user, classroom)

    if not classroom.is_archived:
        raise HTTPException(status_code=400, detail="Classroom is not archived")

    classroom_service.unarchive_classroom(db, classroom)

    return get_classroom(classroom_id, current_user, db)


@router.post("/api/v1/classrooms/join", response_model=schemas.ClassroomJoinOut)
def join_classroom(
    payload: schemas.ClassroomJoinIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.ClassroomJoinOut:
    """
    Join a classroom using a class code.
    Available to learners only.
    """
    from ..services import classroom as classroom_service

    if current_user.role != UserRole.learner:
        raise HTTPException(status_code=403, detail="Only learners can join classrooms")

    try:
        classroom, member = classroom_service.join_classroom_by_code(
            db=db,
            user=current_user,
            class_code=payload.class_code,
            guardian_email=payload.guardian_email,
            guardian_consent=payload.guardian_consent,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    classroom_detail = get_classroom(classroom.id, current_user, db)

    return schemas.ClassroomJoinOut(
        classroom=classroom_detail, message=f"Successfully joined {classroom.name}"
    )


@router.delete("/api/v1/classrooms/{classroom_id}/members/{member_id}", status_code=204)
def remove_member(
    classroom_id: UUID,
    member_id: UUID,
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db),
) -> None:
    """
    Remove a member from a classroom.
    """
    from ..services import classroom as classroom_service

    classroom = db.get(Classroom, classroom_id)
    if classroom is None:
        raise HTTPException(status_code=404, detail="Classroom not found")

    _ensure_class_access(current_user, classroom)

    try:
        classroom_service.remove_class_member(db, classroom, member_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/api/v1/classrooms/{classroom_id}/roster",
    response_model=schemas.ClassroomRosterOut,
)
def get_classroom_roster(
    classroom_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.ClassroomRosterOut:
    """
    Get student roster for a classroom.
    Authorized for classroom teacher, admins, and enrolled learners.
    External students/teachers without authorization receive 403 Forbidden.
    """
    from ..services import classroom as classroom_service

    classroom = db.get(Classroom, classroom_id)
    if classroom is None:
        raise HTTPException(status_code=404, detail="Classroom not found")

    try:
        roster_data = classroom_service.get_classroom_roster(
            db=db,
            classroom=classroom,
            viewer=current_user,
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

    teacher = db.get(User, classroom.teacher_id)
    teacher_name = teacher.display_name if teacher else "Unknown"
    school_name = classroom.school.name if classroom.school else None

    return schemas.ClassroomRosterOut(
        classroom_id=classroom.id,
        classroom_name=classroom.name,
        class_code=classroom.class_code,
        teacher_name=teacher_name,
        term=classroom.term,
        school_id=classroom.school_id,
        school_name=school_name,
        student_count=len(roster_data),
        students=[
            schemas.ClassroomRosterStudentOut(**s)
            for s in roster_data
        ],
    )


# =============================================================================
# School Endpoints
# =============================================================================


@router.post(
    "/api/v1/schools",
    response_model=schemas.SchoolOut,
    status_code=status.HTTP_201_CREATED,
)
def create_school(
    payload: schemas.SchoolCreateIn,
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db),
) -> schemas.SchoolOut:
    """Create a new school (staff/admin only)."""
    from ..services import classroom as classroom_service

    try:
        school = classroom_service.create_school(
            db=db,
            name=payload.name,
            code=payload.code,
            address=payload.address,
            city=payload.city,
            region=payload.region,
            settings=payload.settings,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Associate creator if teacher without a school
    if current_user.role == UserRole.teacher and not current_user.school_id:
        classroom_service.add_school_member(db, school.id, current_user.id, role="teacher")

    return schemas.SchoolOut(
        id=school.id,
        name=school.name,
        code=school.code,
        address=school.address,
        city=school.city,
        region=school.region,
        is_active=school.is_active,
        created_at=school.created_at,
        updated_at=school.updated_at,
        classroom_count=0,
        member_count=1 if current_user.role == UserRole.teacher else 0,
    )


@router.get("/api/v1/schools", response_model=list[schemas.SchoolOut])
def list_schools(
    city: Optional[str] = Query(None, description="Filter by city"),
    is_active: Optional[bool] = Query(True, description="Filter by active status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
) -> list[schemas.SchoolOut]:
    """List schools with optional filters."""
    from ..services import classroom as classroom_service

    schools = classroom_service.list_schools(
        db=db, city=city, is_active=is_active, limit=limit, offset=offset
    )
    if not schools:
        return []

    school_ids = [s.id for s in schools]
    class_counts = dict(
        db.execute(
            select(Classroom.school_id, func.count(Classroom.id))
            .where(Classroom.school_id.in_(school_ids))
            .group_by(Classroom.school_id)
        ).all()
    )
    member_counts = dict(
        db.execute(
            select(SchoolMember.school_id, func.count(SchoolMember.id))
            .where(SchoolMember.school_id.in_(school_ids))
            .group_by(SchoolMember.school_id)
        ).all()
    )

    return [
        schemas.SchoolOut(
            id=s.id,
            name=s.name,
            code=s.code,
            address=s.address,
            city=s.city,
            region=s.region,
            is_active=s.is_active,
            created_at=s.created_at,
            updated_at=s.updated_at,
            classroom_count=int(class_counts.get(s.id, 0)),
            member_count=int(member_counts.get(s.id, 0)),
        )
        for s in schools
    ]


@router.get("/api/v1/schools/{school_id}", response_model=schemas.SchoolOut)
def get_school(
    school_id: UUID,
    current_user: User = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
) -> schemas.SchoolOut:
    """Get school details."""
    from ..services import classroom as classroom_service

    school = classroom_service.get_school(db, school_id)
    if not school:
        raise HTTPException(status_code=404, detail="School not found")

    class_count = db.execute(
        select(func.count(Classroom.id)).where(Classroom.school_id == school.id)
    ).scalar_one()
    member_count = db.execute(
        select(func.count(SchoolMember.id)).where(SchoolMember.school_id == school.id)
    ).scalar_one()

    return schemas.SchoolOut(
        id=school.id,
        name=school.name,
        code=school.code,
        address=school.address,
        city=school.city,
        region=school.region,
        is_active=school.is_active,
        created_at=school.created_at,
        updated_at=school.updated_at,
        classroom_count=int(class_count),
        member_count=int(member_count),
    )


@router.patch("/api/v1/schools/{school_id}", response_model=schemas.SchoolOut)
def update_school(
    school_id: UUID,
    payload: schemas.SchoolUpdateIn,
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db),
) -> schemas.SchoolOut:
    """Update school details (staff/admin only)."""
    from ..services import classroom as classroom_service

    school = classroom_service.get_school(db, school_id)
    if not school:
        raise HTTPException(status_code=404, detail="School not found")

    # If teacher, must be a member of this school or admin
    if current_user.role == UserRole.teacher:
        membership = db.execute(
            select(SchoolMember).where(
                and_(SchoolMember.school_id == school.id, SchoolMember.user_id == current_user.id)
            )
        ).scalar_one_or_none()
        if not membership and current_user.school_id != school.id:
            raise HTTPException(status_code=403, detail="Not authorized to update this school")

    try:
        updated = classroom_service.update_school(
            db=db,
            school=school,
            name=payload.name,
            code=payload.code,
            address=payload.address,
            city=payload.city,
            region=payload.region,
            is_active=payload.is_active,
            settings=payload.settings,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    class_count = db.execute(
        select(func.count(Classroom.id)).where(Classroom.school_id == school.id)
    ).scalar_one()
    member_count = db.execute(
        select(func.count(SchoolMember.id)).where(SchoolMember.school_id == school.id)
    ).scalar_one()

    return schemas.SchoolOut(
        id=updated.id,
        name=updated.name,
        code=updated.code,
        address=updated.address,
        city=updated.city,
        region=updated.region,
        is_active=updated.is_active,
        created_at=updated.created_at,
        updated_at=updated.updated_at,
        classroom_count=int(class_count),
        member_count=int(member_count),
    )


@router.post(
    "/api/v1/schools/{school_id}/members",
    response_model=schemas.SchoolMemberOut,
    status_code=status.HTTP_201_CREATED,
)
def add_school_member(
    school_id: UUID,
    payload: schemas.SchoolMemberAddIn,
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db),
) -> schemas.SchoolMemberOut:
    """Add a teacher or staff member to a school."""
    from ..services import classroom as classroom_service

    try:
        member = classroom_service.add_school_member(
            db=db,
            school_id=school_id,
            user_id=payload.user_id,
            role=payload.role,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    user = db.get(User, payload.user_id)
    return schemas.SchoolMemberOut(
        id=member.id,
        school_id=member.school_id,
        user_id=member.user_id,
        display_name=user.display_name if user else "Unknown",
        email=user.email if user else "",
        role=member.role,
        joined_at=member.joined_at,
    )


@router.get(
    "/api/v1/schools/{school_id}/classrooms",
    response_model=list[schemas.ClassroomSummaryOut],
)
def list_school_classrooms(
    school_id: UUID,
    include_archived: bool = Query(False, description="Include archived classrooms"),
    current_user: User = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
) -> list[schemas.ClassroomSummaryOut]:
    """List classrooms associated with a school."""
    from ..services import classroom as classroom_service

    school = classroom_service.get_school(db, school_id)
    if not school:
        raise HTTPException(status_code=404, detail="School not found")

    classrooms = classroom_service.get_school_classrooms(
        db=db, school_id=school_id, include_archived=include_archived
    )
    if not classrooms:
        return []

    class_ids = [c.id for c in classrooms]
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
        schemas.ClassroomSummaryOut(
            id=c.id,
            name=c.name,
            description=c.description,
            teacher_id=c.teacher_id,
            class_code=c.class_code,
            max_students=c.max_students,
            is_archived=c.is_archived,
            member_count=int(member_counts.get(c.id, 0)),
            assignment_count=int(assignment_counts.get(c.id, 0)),
            created_at=c.created_at,
            updated_at=c.updated_at,
            school_id=c.school_id,
            term=c.term,
        )
        for c in classrooms
    ]


@router.get(
    "/api/v1/classrooms/{classroom_id}/assignments",
    response_model=list[schemas.QuestAssignmentOut],
)
def list_classroom_assignments(
    classroom_id: UUID,
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db),
) -> list[schemas.QuestAssignmentOut]:
    """
    List all quest assignments for a classroom.
    """
    from backend.services import quest_assignments as assignment_service

    classroom = db.get(Classroom, classroom_id)
    if not classroom:
        raise HTTPException(status_code=404, detail="Classroom not found")

    _ensure_class_access(current_user, classroom)

    assignments = assignment_service.get_classroom_assignments(db, classroom_id)

    # Build response
    result = []
    for assignment in assignments:
        progress_entries = assignment.progress_entries
        total_students = len(progress_entries)
        assigned_count = sum(1 for p in progress_entries if p.status == "assigned")
        in_progress_count = sum(
            1 for p in progress_entries if p.status == "in_progress"
        )
        completed_count = sum(1 for p in progress_entries if p.status == "completed")

        assigned_by_name = None
        if assignment.assigned_by:
            assigned_by_name = (
                assignment.assigned_by.display_name or assignment.assigned_by.email
            )

        result.append(
            schemas.QuestAssignmentOut(
                id=assignment.id,
                class_id=assignment.class_id,
                quest=schemas.QuestBriefOut(
                    id=assignment.quest.id,
                    slug=assignment.quest.slug,
                    name=assignment.quest.name,
                    description=assignment.quest.description,
                ),
                assigned_by_id=assignment.assigned_by_id,
                assigned_by_name=assigned_by_name,
                due_at=assignment.due_at,
                assigned_at=assignment.assigned_at,
                points_override=assignment.points_override,
                notes=assignment.notes,
                total_students=total_students,
                completed_count=completed_count,
                in_progress_count=in_progress_count,
                assigned_count=assigned_count,
                completion_rate=(completed_count / total_students * 100)
                if total_students > 0
                else 0,
            )
        )

    return result


@router.post(
    "/api/v1/classrooms/{classroom_id}/assignments",
    response_model=schemas.QuestAssignmentOut,
    status_code=201,
)
def create_assignment(
    classroom_id: UUID,
    payload: schemas.QuestAssignmentCreateIn,
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db),
) -> schemas.QuestAssignmentOut:
    """
    Create a new quest assignment.
    Can assign to entire classroom or to individual student.
    """
    from backend.services import quest_assignments as assignment_service

    classroom = db.get(Classroom, classroom_id)
    if not classroom:
        raise HTTPException(status_code=404, detail="Classroom not found")

    _ensure_class_access(current_user, classroom)

    try:
        if payload.student_id:
            # Assign to individual student
            assignment = assignment_service.assign_quest_to_student(
                db=db,
                classroom=classroom,
                quest_id=payload.quest_id,
                student_id=payload.student_id,
                teacher=current_user,
                due_at=payload.due_at,
                points_override=payload.points_override,
                notes=payload.notes,
            )
        else:
            # Assign to entire classroom
            assignment = assignment_service.assign_quest_to_classroom(
                db=db,
                classroom=classroom,
                quest_id=payload.quest_id,
                teacher=current_user,
                due_at=payload.due_at,
                points_override=payload.points_override,
                notes=payload.notes,
            )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Build response
    progress_entries = assignment.progress_entries
    total_students = len(progress_entries)
    assigned_count = sum(1 for p in progress_entries if p.status == "assigned")
    in_progress_count = sum(1 for p in progress_entries if p.status == "in_progress")
    completed_count = sum(1 for p in progress_entries if p.status == "completed")

    assigned_by_name = None
    if assignment.assigned_by:
        assigned_by_name = (
            assignment.assigned_by.display_name or assignment.assigned_by.email
        )

    return schemas.QuestAssignmentOut(
        id=assignment.id,
        class_id=assignment.class_id,
        quest=schemas.QuestBriefOut(
            id=assignment.quest.id,
            slug=assignment.quest.slug,
            name=assignment.quest.name,
            description=assignment.quest.description,
        ),
        assigned_by_id=assignment.assigned_by_id,
        assigned_by_name=assigned_by_name,
        due_at=assignment.due_at,
        assigned_at=assignment.assigned_at,
        points_override=assignment.points_override,
        notes=assignment.notes,
        total_students=total_students,
        completed_count=completed_count,
        in_progress_count=in_progress_count,
        assigned_count=assigned_count,
        completion_rate=(completed_count / total_students * 100)
        if total_students > 0
        else 0,
    )


@router.put(
    "/api/v1/classrooms/{classroom_id}/assignments/{assignment_id}",
    response_model=schemas.QuestAssignmentOut,
)
def update_assignment(
    classroom_id: UUID,
    assignment_id: UUID,
    payload: schemas.QuestAssignmentUpdateIn,
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db),
) -> schemas.QuestAssignmentOut:
    """
    Update a quest assignment.
    """
    from backend.services import quest_assignments as assignment_service

    classroom = db.get(Classroom, classroom_id)
    if not classroom:
        raise HTTPException(status_code=404, detail="Classroom not found")

    _ensure_class_access(current_user, classroom)

    try:
        assignment = assignment_service.update_assignment(
            db=db,
            assignment_id=assignment_id,
            due_at=payload.due_at,
            points_override=payload.points_override,
            notes=payload.notes,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    # Build response
    progress_entries = assignment.progress_entries
    total_students = len(progress_entries)
    assigned_count = sum(1 for p in progress_entries if p.status == "assigned")
    in_progress_count = sum(1 for p in progress_entries if p.status == "in_progress")
    completed_count = sum(1 for p in progress_entries if p.status == "completed")

    assigned_by_name = None
    if assignment.assigned_by:
        assigned_by_name = (
            assignment.assigned_by.display_name or assignment.assigned_by.email
        )

    return schemas.QuestAssignmentOut(
        id=assignment.id,
        class_id=assignment.class_id,
        quest=schemas.QuestBriefOut(
            id=assignment.quest.id,
            slug=assignment.quest.slug,
            name=assignment.quest.name,
            description=assignment.quest.description,
        ),
        assigned_by_id=assignment.assigned_by_id,
        assigned_by_name=assigned_by_name,
        due_at=assignment.due_at,
        assigned_at=assignment.assigned_at,
        points_override=assignment.points_override,
        notes=assignment.notes,
        total_students=total_students,
        completed_count=completed_count,
        in_progress_count=in_progress_count,
        assigned_count=assigned_count,
        completion_rate=(completed_count / total_students * 100)
        if total_students > 0
        else 0,
    )


@router.delete(
    "/api/v1/classrooms/{classroom_id}/assignments/{assignment_id}", status_code=204
)
def delete_assignment(
    classroom_id: UUID,
    assignment_id: UUID,
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db),
) -> None:
    """
    Delete a quest assignment.
    """
    from backend.services import quest_assignments as assignment_service

    classroom = db.get(Classroom, classroom_id)
    if not classroom:
        raise HTTPException(status_code=404, detail="Classroom not found")

    _ensure_class_access(current_user, classroom)

    try:
        assignment_service.delete_assignment(db, assignment_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/api/v1/assignments/mine", response_model=list[schemas.StudentAssignmentOut])
def get_my_assignments(
    classroom_id: Optional[UUID] = Query(None, description="Filter by classroom"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[schemas.StudentAssignmentOut]:
    """
    Get all quest assignments for the current student.
    """
    from datetime import datetime

    from backend.services import quest_assignments as assignment_service

    assignments = assignment_service.get_student_assignments(
        db=db,
        user_id=current_user.id,
        classroom_id=classroom_id,
    )

    result = []
    for assignment in assignments:
        is_overdue = False
        if assignment["due_at"] and assignment["status"] != "completed":
            is_overdue = (
                datetime.now(assignment["due_at"].tzinfo) > assignment["due_at"]
            )

        result.append(
            schemas.StudentAssignmentOut(
                assignment_id=UUID(assignment["assignment_id"]),
                quest_id=UUID(assignment["quest_id"]),
                quest_name=assignment["quest_name"],
                quest_description=assignment["quest_description"],
                classroom_id=UUID(assignment["classroom_id"]),
                classroom_name=assignment["classroom_name"],
                due_at=assignment["due_at"],
                assigned_at=assignment["assigned_at"],
                points_override=assignment["points_override"],
                notes=assignment["notes"],
                status=assignment["status"],
                completed_at=assignment["completed_at"],
                is_overdue=is_overdue,
            )
        )

    return result


@router.post(
    "/api/v1/assignments/{assignment_id}/submit",
    response_model=schemas.AssignmentSubmitOut,
)
def submit_assignment(
    assignment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.AssignmentSubmitOut:
    """
    Submit an assignment as completed.
    The quest must be completed first.
    """
    from backend.services import quest_assignments as assignment_service

    try:
        progress = assignment_service.submit_assignment(
            db=db,
            assignment_id=assignment_id,
            user_id=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    message = (
        "Assignment marked as in progress"
        if progress.status == "in_progress"
        else "Assignment completed!"
    )

    return schemas.AssignmentSubmitOut(
        assignment_id=assignment_id,
        status=progress.status,
        completed_at=progress.completed_at,
        message=message,
    )


@router.get(
    "/api/v1/classrooms/{classroom_id}/students/{student_id}/progress",
    response_model=schemas.StudentProgressOut,
)
def get_student_progress(
    classroom_id: UUID,
    student_id: UUID,
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db),
) -> schemas.StudentProgressOut:
    """
    Get detailed progress for a specific student in a classroom.
    Only accessible to teachers of the classroom and admins.
    """
    from ..services import student_progress as progress_service

    classroom = db.get(Classroom, classroom_id)
    if classroom is None:
        raise HTTPException(status_code=404, detail="Classroom not found")

    _ensure_class_access(current_user, classroom)

    try:
        progress = progress_service.get_student_progress(db, student_id, classroom_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return schemas.StudentProgressOut(
        student_id=progress["student_id"],
        classroom_id=progress["classroom_id"],
        joined_at=progress["joined_at"],
        overall_completion_percent=progress["overall_completion_percent"],
        lessons=schemas.LessonStatsOut(**progress["lessons"]),
        quizzes=schemas.QuizStatsOut(**progress["quizzes"]),
        engagement=schemas.EngagementStatsOut(**progress["engagement"]),
    )


@router.get(
    "/api/v1/classrooms/{classroom_id}/progress",
    response_model=schemas.ClassProgressSummaryOut,
)
def get_class_progress_summary(
    classroom_id: UUID,
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db),
) -> schemas.ClassProgressSummaryOut:
    """
    Get class-wide progress summary with average metrics.
    Only accessible to teachers of the classroom and admins.
    """
    from ..services import student_progress as progress_service

    classroom = db.get(Classroom, classroom_id)
    if classroom is None:
        raise HTTPException(status_code=404, detail="Classroom not found")

    _ensure_class_access(current_user, classroom)

    summary = progress_service.get_class_progress_summary(db, classroom_id)

    return schemas.ClassProgressSummaryOut(
        classroom_id=summary["classroom_id"],
        student_count=summary["student_count"],
        averages=schemas.ClassProgressAveragesOut(**summary["averages"]),
    )


@router.get(
    "/api/v1/classrooms/{classroom_id}/leaderboard",
    response_model=schemas.LeaderboardOut,
)
def get_class_leaderboard(
    classroom_id: UUID,
    order_by: str = Query("xp", regex="^(xp|streak|motifs|quizzes)$"),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db),
) -> schemas.LeaderboardOut:
    """
    Get class leaderboard sorted by various metrics.

    Order by options:
    - xp: Total XP earned
    - streak: Current streak
    - motifs: Discovered motifs
    - quizzes: Quizzes passed

    Only accessible to teachers of the classroom and admins.
    """
    from ..services import student_progress as progress_service

    classroom = db.get(Classroom, classroom_id)
    if classroom is None:
        raise HTTPException(status_code=404, detail="Classroom not found")

    _ensure_class_access(current_user, classroom)

    entries = progress_service.get_class_leaderboard(db, classroom_id, limit, order_by)

    return schemas.LeaderboardOut(
        classroom_id=classroom_id,
        order_by=order_by,
        entries=[schemas.LeaderboardEntryOut(**entry) for entry in entries],
    )


def _compute_classroom_gradebook(
    db: Session,
    classroom: Classroom,
    status_filter: Optional[str] = None,
    search: Optional[str] = None,
) -> schemas.ClassroomGradebookOut:
    """Compute full gradebook roster, scores, missing/pending metrics for a classroom."""
    from ..services import student_progress as progress_service

    members = (
        db.execute(
            select(ClassMember)
            .options(selectinload(ClassMember.user))
            .where(
                and_(
                    ClassMember.class_id == classroom.id,
                    ClassMember.role == "learner",
                )
            )
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
    progress_map = {}
    if assignment_ids:
        progress_entries = (
            db.execute(
                select(AssignmentProgress).where(
                    AssignmentProgress.assignment_id.in_(assignment_ids)
                )
            )
            .scalars()
            .all()
        )
        for prog in progress_entries:
            progress_map[(prog.user_id, prog.assignment_id)] = prog

    now = datetime.now(timezone.utc)

    roster_entries = []
    total_completed = 0
    total_pending = 0
    total_missing = 0
    sum_quiz_scores = 0.0
    sum_completion_percent = 0.0
    valid_quiz_students = 0

    for member in members:
        user = member.user
        if not user:
            continue

        try:
            progress_data = progress_service.get_student_progress(
                db, member.user_id, classroom.id
            )
            completion_pct = float(progress_data.get("overall_completion_percent", 0.0))
            xp = int(progress_data.get("engagement", {}).get("total_xp", 0))
            quizzes_passed = int(progress_data.get("quizzes", {}).get("passed", 0))
            avg_score = float(progress_data.get("quizzes", {}).get("average_score", 0.0))
        except (ValueError, Exception):
            completion_pct = 0.0
            xp = 0
            quizzes_passed = 0
            avg_score = 0.0

        if avg_score > 0:
            sum_quiz_scores += avg_score
            valid_quiz_students += 1
        sum_completion_percent += completion_pct

        student_assignments = []
        student_completed = 0
        student_pending = 0
        student_missing = 0

        for a in assignments:
            prog = progress_map.get((member.user_id, a.id))
            raw_status = prog.status if prog else "assigned"
            completed_at = prog.completed_at if prog else None

            is_completed = raw_status == "completed"
            is_overdue = False
            if a.due_at is not None:
                due_utc = (
                    a.due_at
                    if a.due_at.tzinfo is not None
                    else a.due_at.replace(tzinfo=timezone.utc)
                )
                is_overdue = due_utc < now

            is_missing = not is_completed and is_overdue
            is_pending = not is_completed and not is_missing

            effective_status = (
                "completed" if is_completed else ("missing" if is_missing else raw_status)
            )

            if is_completed:
                student_completed += 1
            elif is_missing:
                student_missing += 1
            else:
                student_pending += 1

            title = (a.quest.name if a.quest else None) or a.notes or "Nhiệm vụ học tập"
            student_assignments.append(
                schemas.StudentAssignmentProgressOut(
                    assignment_id=a.id,
                    title=title,
                    due_at=a.due_at,
                    status=effective_status,
                    score=float(a.points_override) if a.points_override is not None else None,
                    completed_at=completed_at,
                    is_missing=is_missing,
                    is_pending=is_pending,
                )
            )

        if student_missing > 0:
            student_status = "missing"
            total_missing += 1
        elif student_pending > 0:
            student_status = "pending"
            total_pending += 1
        else:
            student_status = "completed"
            total_completed += 1

        entry = schemas.StudentGradebookEntryOut(
            student_id=member.user_id,
            display_name=user.display_name or user.username or "Học sinh",
            email=user.email,
            role=member.role,
            avatar_url=None,
            joined_at=member.joined_at,
            overall_completion_percent=completion_pct,
            total_xp=xp,
            quizzes_passed=quizzes_passed,
            avg_quiz_score=avg_score,
            assignments=student_assignments,
            completed_count=student_completed,
            pending_count=student_pending,
            missing_count=student_missing,
            status=student_status,
        )

        matches_status = True
        if status_filter:
            sf = status_filter.lower().strip()
            if sf in ("missing", "overdue"):
                matches_status = entry.status == "missing"
            elif sf in ("pending", "submitted", "in_progress"):
                matches_status = entry.status == "pending"
            elif sf in ("completed", "graded"):
                matches_status = entry.status == "completed"
            elif sf == "all":
                matches_status = True

        matches_search = True
        if search and search.strip():
            sq = search.lower().strip()
            matches_search = (
                sq in entry.display_name.lower() or sq in entry.email.lower()
            )

        if matches_status and matches_search:
            roster_entries.append(entry)

    total_count = len(members)
    avg_score_total = (
        round(sum_quiz_scores / valid_quiz_students, 1) if valid_quiz_students > 0 else 0.0
    )
    avg_comp_total = (
        round(sum_completion_percent / total_count, 1) if total_count > 0 else 0.0
    )

    metrics = schemas.GradebookMetricsOut(
        total_students=total_count,
        completed_count=total_completed,
        pending_count=total_pending,
        missing_count=total_missing,
        average_score=avg_score_total,
        average_completion_percent=avg_comp_total,
    )

    return schemas.ClassroomGradebookOut(
        classroom_id=classroom.id,
        classroom_name=classroom.name,
        teacher_id=classroom.teacher_id,
        total_students=len(roster_entries),
        metrics=metrics,
        roster=roster_entries,
    )


@router.get(
    "/api/v1/classrooms/{classroom_id}/gradebook",
    response_model=schemas.ClassroomGradebookOut,
)
def get_classroom_gradebook(
    classroom_id: UUID,
    status_filter: Optional[str] = Query(None, description="Filter by: all, missing, pending, completed"),
    search: Optional[str] = Query(None, description="Search by student display name or email"),
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db),
) -> schemas.ClassroomGradebookOut:
    """
    Get classroom gradebook with real student roster, scores, missing/pending statuses.
    Only accessible to assigned teachers and admins (blocks horizontal privilege escalation with 403).
    """
    classroom = db.get(Classroom, classroom_id)
    if classroom is None:
        raise HTTPException(status_code=404, detail="Classroom not found")

    _ensure_class_access(current_user, classroom)

    return _compute_classroom_gradebook(
        db=db,
        classroom=classroom,
        status_filter=status_filter,
        search=search,
    )


@router.get("/api/v1/classrooms/{classroom_id}/gradebook/export")
def export_classroom_gradebook_csv(
    classroom_id: UUID,
    status_filter: Optional[str] = Query(None, description="Filter by: all, missing, pending, completed"),
    search: Optional[str] = Query(None, description="Search by student display name or email"),
    anonymize: bool = Query(False, description="Anonymize student names and emails with HS-ANON prefix"),
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db),
):
    """
    Export classroom gradebook to CSV with UTF-8 BOM encoding for Excel.
    Only accessible to assigned teachers and admins (blocks horizontal privilege escalation with 403).
    """
    import csv
    from io import StringIO

    classroom = db.get(Classroom, classroom_id)
    if classroom is None:
        raise HTTPException(status_code=404, detail="Classroom not found")

    _ensure_class_access(current_user, classroom)

    gradebook = _compute_classroom_gradebook(
        db=db,
        classroom=classroom,
        status_filter=status_filter,
        search=search,
    )

    output = StringIO()
    # Write UTF-8 BOM for Microsoft Excel compatibility
    output.write("\ufeff")
    writer = csv.writer(output)

    writer.writerow(
        [
            "Mã học sinh",
            "Họ và tên",
            "Email",
            "Lớp học",
            "Tiến độ hoàn thành (%)",
            "Tổng XP",
            "Số bài trắc nghiệm đạt",
            "Điểm TB trắc nghiệm",
            "Bài tập hoàn thành",
            "Bài tập chờ nộp/chấm (Pending)",
            "Bài tập trễ hạn (Missing)",
            "Trạng thái chung",
        ]
    )

    for idx, student in enumerate(gradebook.roster, start=1):
        if anonymize:
            student_code = f"HS-ANON-{idx:03d}"
            name = f"Học sinh {idx:03d}"
            email = f"anon_{idx:03d}@hidden.local"
        else:
            student_code = str(student.student_id)
            name = student.display_name
            email = student.email

        status_vi = (
            "Trễ hạn (Missing)"
            if student.status == "missing"
            else ("Đang chờ (Pending)" if student.status == "pending" else "Hoàn thành (Completed)")
        )

        writer.writerow(
            [
                student_code,
                name,
                email,
                classroom.name,
                f"{student.overall_completion_percent:.1f}%",
                student.total_xp,
                student.quizzes_passed,
                f"{student.avg_quiz_score:.1f}",
                student.completed_count,
                student.pending_count,
                student.missing_count,
                status_vi,
            ]
        )

    output.seek(0)
    return Response(
        content=output.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="classroom_{classroom_id}_gradebook.csv"'
        },
    )


@router.get("/api/v1/classrooms/{classroom_id}/export")
def export_class_progress(
    classroom_id: UUID,
    status_filter: Optional[str] = Query(None, description="Filter by: all, missing, pending, completed"),
    search: Optional[str] = Query(None, description="Search by student name or email"),
    anonymize: bool = Query(False, description="Anonymize student names and emails"),
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db),
):
    """
    Export class progress data as CSV.
    Only accessible to teachers of the classroom and admins.
    """
    import csv
    from io import StringIO

    from fastapi.responses import StreamingResponse

    from ..services import student_progress as progress_service

    classroom = db.get(Classroom, classroom_id)
    if classroom is None:
        raise HTTPException(status_code=404, detail="Classroom not found")

    _ensure_class_access(current_user, classroom)

    # Get all student members
    members = (
        db.execute(
            select(ClassMember)
            .options(selectinload(ClassMember.user))
            .where(
                and_(
                    ClassMember.class_id == classroom_id,
                    ClassMember.role == "learner",
                )
            )
            .order_by(ClassMember.joined_at.asc())
        )
        .scalars()
        .all()
    )

    # Create CSV
    output = StringIO()
    output.write("\ufeff")
    writer = csv.writer(output)

    # Write header
    writer.writerow(
        [
            "Student ID",
            "Display Name",
            "Email",
            "Joined At",
            "Completion %",
            "Discovered Motifs",
            "Learned Motifs",
            "Mastered Motifs",
            "Quiz Attempts",
            "Quizzes Passed",
            "Avg Quiz Score",
            "Current Streak",
            "Longest Streak",
            "Total XP",
            "Time Spent (min)",
        ]
    )

    # Write data for each student
    idx = 1
    for member in members:
        user = member.user
        if not user:
            continue

        if search and search.strip():
            sq = search.lower().strip()
            if sq not in user.display_name.lower() and sq not in user.email.lower():
                continue

        try:
            progress = progress_service.get_student_progress(
                db, member.user_id, classroom_id
            )

            if status_filter:
                sf = status_filter.lower().strip()
                comp_pct = progress.get("overall_completion_percent", 0.0)
                if sf in ("completed", "graded") and comp_pct < 100.0:
                    continue
                elif sf in ("pending", "in_progress") and (comp_pct <= 0.0 or comp_pct >= 100.0):
                    continue
                elif sf in ("missing", "overdue") and comp_pct > 0.0:
                    continue

            s_id = f"HS-ANON-{idx:03d}" if anonymize else str(progress["student_id"])
            s_name = f"Học sinh {idx:03d}" if anonymize else member.user.display_name
            s_email = f"anon_{idx:03d}@hidden.local" if anonymize else member.user.email
            idx += 1

            writer.writerow(
                [
                    s_id,
                    s_name,
                    s_email,
                    progress["joined_at"].isoformat(),
                    progress["overall_completion_percent"],
                    progress["lessons"]["discovered"],
                    progress["lessons"]["learned"],
                    progress["lessons"]["mastered"],
                    progress["quizzes"]["total_attempts"],
                    progress["quizzes"]["passed"],
                    progress["quizzes"]["average_score"],
                    progress["engagement"]["current_streak"],
                    progress["engagement"]["longest_streak"],
                    progress["engagement"]["total_xp"],
                    progress["engagement"]["time_spent_minutes"],
                ]
            )
        except ValueError:
            # Skip students with errors
            continue

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=classroom_{classroom_id}_progress.csv"
        },
    )


@router.get("/api/v1/classes", response_model=list[ClassSummaryOut_Legacy])
def list_classes_legacy(
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db),
) -> list[ClassSummaryOut_Legacy]:
    """List classes (legacy alias for classroom listing)."""
    query = select(Classroom)

    if current_user.role == UserRole.teacher:
        query = query.where(Classroom.teacher_id == current_user.id)

    query = query.where(Classroom.is_archived.is_(False)).order_by(
        Classroom.created_at.desc()
    )
    classrooms = db.execute(query).scalars().all()

    if not classrooms:
        return []

    class_ids = [c.id for c in classrooms]
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
        ClassSummaryOut_Legacy(
            id=classroom.id,
            name=classroom.name,
            description=classroom.description,
            teacher_id=classroom.teacher_id,
            created_at=classroom.created_at,
            member_count=int(member_counts.get(classroom.id, 0)),
            assignment_count=int(assignment_counts.get(classroom.id, 0)),
        )
        for classroom in classrooms
    ]


@router.post("/api/v1/classes", response_model=ClassSummaryOut_Legacy, status_code=201)
def create_class_legacy(
    payload: ClassCreateRequest,
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db),
) -> ClassSummaryOut_Legacy:
    """Create class (legacy alias for classroom creation)."""
    from ..services import classroom as classroom_service

    classroom = classroom_service.create_classroom(
        db=db,
        teacher=current_user,
        name=payload.name,
        description=payload.description,
    )

    return ClassSummaryOut_Legacy(
        id=classroom.id,
        name=classroom.name,
        description=classroom.description,
        teacher_id=classroom.teacher_id,
        created_at=classroom.created_at,
        member_count=0,
        assignment_count=0,
    )


@router.get("/api/v1/classes/{class_id}", response_model=ClassDetailOut_Legacy)
def get_class_detail(
    class_id: UUID,
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db),
) -> ClassDetailOut_Legacy:
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

    return ClassDetailOut_Legacy(
        id=classroom.id,
        name=classroom.name,
        description=classroom.description,
        teacher_id=classroom.teacher_id,
        created_at=classroom.created_at,
        members=[
            ClassMemberOut_Legacy(
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


@router.post("/api/v1/classes/{class_id}/members", response_model=ClassDetailOut_Legacy)
def add_class_member(
    class_id: UUID,
    payload: ClassMemberAddRequest,
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db),
) -> ClassDetailOut_Legacy:
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


@router.delete(
    "/api/v1/classes/{class_id}/members/{user_id}", response_model=ClassDetailOut_Legacy
)
def remove_class_member(
    class_id: UUID,
    user_id: UUID,
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db),
) -> ClassDetailOut_Legacy:
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


@router.post(
    "/api/v1/classes/{class_id}/assignments", response_model=ClassDetailOut_Legacy
)
def assign_quest_to_class(
    class_id: UUID,
    payload: AssignmentCreateRequest,
    current_user: User = Depends(get_staff_user),
    db: Session = Depends(get_db),
) -> ClassDetailOut_Legacy:
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


@router.get(
    "/api/v1/admin/experiments/{experiment_id}/assignments",
    response_model=list[schemas.UserExperimentAssignmentOut],
)
def get_experiment_assignments(
    experiment_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[schemas.UserExperimentAssignmentOut]:
    """
    Get all user assignments for an experiment (admin only).
    """
    _get_experiment_or_404(db, experiment_id)

    # Get assignments with pagination
    offset = (page - 1) * page_size
    assignments = (
        db.execute(
            select(UserExperimentAssignment)
            .where(UserExperimentAssignment.experiment_id == experiment_id)
            .order_by(UserExperimentAssignment.assigned_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        .scalars()
        .all()
    )

    return [
        schemas.UserExperimentAssignmentOut(
            id=assignment.id,
            user_id=assignment.user_id,
            experiment_id=assignment.experiment_id,
            variant_key=assignment.variant_key,
            assigned_at=assignment.assigned_at,
        )
        for assignment in assignments
    ]
