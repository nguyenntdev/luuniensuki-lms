# -*- coding: utf-8 -*-
"""Social graph: following, friends, feed & shares (backend-modularization router extraction).

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

logger = logging.getLogger("luuniensuki.api")

router = APIRouter()


@router.get("/api/v1/social/following", response_model=schemas.FollowListOut)
def get_following(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.FollowListOut:
    """Get list of users that the current user is following."""
    from .services import social

    skip = (page - 1) * page_size
    follows, total = social.get_following(
        db, current_user.id, skip=skip, limit=page_size
    )

    return schemas.FollowListOut(
        users=[
            schemas.FollowUserOut(
                id=follow.id,
                user_id=follow.following.id,
                display_name=follow.following.display_name,
                username=follow.following.username,
                avatar_url=follow.following.avatar_url,
                bio=follow.following.bio,
                total_xp=follow.following.total_xp,
                followed_at=follow.created_at,
            )
            for follow in follows
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/api/v1/social/followers", response_model=schemas.FollowListOut)
def get_followers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.FollowListOut:
    """Get list of users following the current user."""
    from .services import social

    skip = (page - 1) * page_size
    follows, total = social.get_followers(
        db, current_user.id, skip=skip, limit=page_size
    )

    return schemas.FollowListOut(
        users=[
            schemas.FollowUserOut(
                id=follow.id,
                user_id=follow.follower.id,
                display_name=follow.follower.display_name,
                username=follow.follower.username,
                avatar_url=follow.follower.avatar_url,
                bio=follow.follower.bio,
                total_xp=follow.follower.total_xp,
                followed_at=follow.created_at,
            )
            for follow in follows
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/api/v1/social/search", response_model=schemas.SocialUserSearchOut)
def search_social_users(
    q: str = Query(..., min_length=1, max_length=255),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.SocialUserSearchOut:
    """Search users by email, display name, or username."""
    from .services import social

    skip = (page - 1) * page_size
    users, total = social.search_users(
        db=db,
        current_user_id=current_user.id,
        query=q,
        skip=skip,
        limit=page_size,
    )

    user_ids = [user.id for user in users]
    if user_ids:
        following_ids = set(
            db.execute(
                select(UserFollow.following_id).where(
                    UserFollow.follower_id == current_user.id,
                    UserFollow.following_id.in_(user_ids),
                )
            )
            .scalars()
            .all()
        )
        follower_ids = set(
            db.execute(
                select(UserFollow.follower_id).where(
                    UserFollow.following_id == current_user.id,
                    UserFollow.follower_id.in_(user_ids),
                )
            )
            .scalars()
            .all()
        )
    else:
        following_ids = set()
        follower_ids = set()

    return schemas.SocialUserSearchOut(
        users=[
            schemas.SocialUserOut(
                id=user.id,
                display_name=user.display_name,
                username=user.username,
                avatar_url=user.avatar_url,
                total_xp=user.total_xp,
                is_following=user.id in following_ids,
                is_friend=(user.id in following_ids and user.id in follower_ids),
            )
            for user in users
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/api/v1/social/follow/{user_id}", status_code=201)
def follow_user(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Follow a user."""
    from .services import social

    # Check if user exists
    target_user = db.get(User, user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        follow = social.follow_user(db, current_user.id, user_id)
        return {"message": "User followed successfully", "follow_id": follow.id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/api/v1/social/follow/{user_id}", status_code=204)
def unfollow_user(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Unfollow a user."""
    from .services import social

    success = social.unfollow_user(db, current_user.id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Not following this user")

    return Response(status_code=204)


@router.get("/api/v1/social/friends", response_model=schemas.FriendListOut)
def get_friends(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.FriendListOut:
    """Get list of friends (mutual follows)."""
    from .services import social

    friends = social.get_friends(db, current_user.id)
    online_status = social.get_online_status_map(db, [friend.id for friend in friends])

    return schemas.FriendListOut(
        friends=[
            schemas.FriendOut(
                id=friend.id,
                user_id=friend.id,
                display_name=friend.display_name,
                username=friend.username,
                avatar_url=friend.avatar_url,
                bio=friend.bio,
                total_xp=friend.total_xp,
                is_online=online_status.get(friend.id, False),
            )
            for friend in friends
        ],
        total=len(friends),
    )


@router.post(
    "/api/v1/social/peer-feedback",
    response_model=PeerFeedbackOut,
    status_code=status.HTTP_201_CREATED,
)
def send_peer_feedback(
    payload: PeerFeedbackSendIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PeerFeedbackOut:
    """Send template-based peer feedback to a friend."""
    from .services import push_notifications, social

    if payload.to_user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot send feedback to yourself")

    target_user = db.get(User, payload.to_user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Controlled flow: only mutual followers (friends) can send feedback.
    is_friend = social.is_following(db, current_user.id, payload.to_user_id) and social.is_following(
        db, payload.to_user_id, current_user.id
    )
    if not is_friend:
        raise HTTPException(status_code=403, detail="You can only send feedback to friends")

    if payload.share_id:
        share_exists = (
            db.query(UserShare.id)
            .filter(
                and_(
                    UserShare.id == payload.share_id,
                    UserShare.user_id == payload.to_user_id,
                )
            )
            .first()
            is not None
        )
        if not share_exists:
            raise HTTPException(status_code=404, detail="Related share not found")

    feedback_templates = {
        "great_progress": "{sender_name} gửi lời khen: Bạn đang tiến bộ rất nhanh!",
        "keep_going": "{sender_name} nhắn bạn: Cố lên, giữ nhịp học đều mỗi ngày nhé!",
        "impressive_streak": "{sender_name} ấn tượng với streak học tập của bạn!",
        "quiz_champion": "{sender_name} khen bạn: Kết quả quiz của bạn rất xuất sắc!",
    }
    body_template = feedback_templates.get(payload.template_key)
    if not body_template:
        raise HTTPException(status_code=400, detail="Invalid feedback template")

    sender_name = current_user.display_name or current_user.email or "Một người bạn"
    title = f"Peer feedback từ {sender_name}"
    body = body_template.format(sender_name=sender_name)

    notification = push_notifications.create_notification(
        db=db,
        user_id=payload.to_user_id,
        title=title,
        body=body,
        notification_type=NotificationType.social,
        data_payload={
            "from_user_id": str(current_user.id),
            "from_display_name": sender_name,
            "template_key": payload.template_key,
            "share_id": str(payload.share_id) if payload.share_id else None,
            "type": "peer_feedback",
        },
    )

    return PeerFeedbackOut(
        success=True,
        message="Peer feedback sent successfully",
        template_key=payload.template_key,
        notification_id=notification.id,
    )


@router.post(
    "/api/v1/social/friend-requests",
    response_model=schemas.FriendRequestOut,
    status_code=201,
)
def send_friend_request(
    request_data: schemas.FriendRequestCreateIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.FriendRequestOut:
    """Send a friend request to another user."""
    from .services import social

    # Check if target user exists
    target_user = db.get(User, request_data.to_user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        friend_request = social.create_friend_request(
            db, current_user.id, request_data.to_user_id
        )

        return schemas.FriendRequestOut(
            id=friend_request.id,
            from_user_id=friend_request.from_user_id,
            from_user_display_name=current_user.display_name,
            from_user_avatar_url=current_user.avatar_url,
            to_user_id=friend_request.to_user_id,
            to_user_display_name=target_user.display_name,
            to_user_avatar_url=target_user.avatar_url,
            status=friend_request.status.value,
            created_at=friend_request.created_at,
            responded_at=friend_request.responded_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/api/v1/social/friend-requests", response_model=schemas.FriendRequestListOut)
def get_friend_requests(
    status: Optional[str] = Query(None, pattern="^(pending|accepted|rejected)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.FriendRequestListOut:
    """Get friend requests received by the current user."""
    from .services import social

    requests = social.get_friend_requests(db, current_user.id, status=status)

    pending_count = sum(
        1 for req in requests if req.status == FriendRequestStatus.pending
    )

    return schemas.FriendRequestListOut(
        requests=[
            schemas.FriendRequestOut(
                id=req.id,
                from_user_id=req.from_user_id,
                from_user_display_name=req.from_user.display_name,
                from_user_avatar_url=req.from_user.avatar_url,
                to_user_id=req.to_user_id,
                to_user_display_name=req.to_user.display_name,
                to_user_avatar_url=req.to_user.avatar_url,
                status=req.status.value,
                created_at=req.created_at,
                responded_at=req.responded_at,
            )
            for req in requests
        ],
        total=len(requests),
        pending_count=pending_count,
    )


@router.post(
    "/api/v1/social/friend-requests/{request_id}/accept",
    response_model=schemas.FriendRequestOut,
)
def accept_friend_request(
    request_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.FriendRequestOut:
    """Accept a friend request."""
    from .services import social

    try:
        friend_request = social.accept_friend_request(db, request_id, current_user.id)

        return schemas.FriendRequestOut(
            id=friend_request.id,
            from_user_id=friend_request.from_user_id,
            from_user_display_name=friend_request.from_user.display_name,
            from_user_avatar_url=friend_request.from_user.avatar_url,
            to_user_id=friend_request.to_user_id,
            to_user_display_name=friend_request.to_user.display_name,
            to_user_avatar_url=friend_request.to_user.avatar_url,
            status=friend_request.status.value,
            created_at=friend_request.created_at,
            responded_at=friend_request.responded_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/api/v1/social/friend-requests/{request_id}/reject",
    response_model=schemas.FriendRequestOut,
)
def reject_friend_request(
    request_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.FriendRequestOut:
    """Reject a friend request."""
    from .services import social

    try:
        friend_request = social.reject_friend_request(db, request_id, current_user.id)

        return schemas.FriendRequestOut(
            id=friend_request.id,
            from_user_id=friend_request.from_user_id,
            from_user_display_name=friend_request.from_user.display_name,
            from_user_avatar_url=friend_request.from_user.avatar_url,
            to_user_id=friend_request.to_user_id,
            to_user_display_name=friend_request.to_user.display_name,
            to_user_avatar_url=friend_request.to_user.avatar_url,
            status=friend_request.status.value,
            created_at=friend_request.created_at,
            responded_at=friend_request.responded_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/api/v1/social/feed", response_model=schemas.ActivityFeedOut)
def get_activity_feed(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.ActivityFeedOut:
    """
    Get activity feed from followed users.

    Returns public shares from other users.
    This filters to shares from users the current user follows.
    """
    from .services import sharing

    shares, total = sharing.get_activity_feed(db, current_user.id, page, page_size)

    # Convert shares to activity items
    activities = []
    for share in shares:
        user = db.query(User).filter(User.id == share.user_id).first()
        if not user:
            continue

        content_data = sharing.get_content_data_for_share(db, share)

        activity = schemas.UserActivityOut(
            id=share.id,
            activity_type="share",
            user_id=user.id,
            user_display_name=user.display_name or user.email,
            user_avatar_url=user.avatar_url,
            content={
                "share_type": share.share_type,
                "caption": share.caption,
                "content_data": content_data,
                "share_url": share.share_url,
                "view_count": share.view_count,
            },
            created_at=share.created_at,
        )
        activities.append(activity)

    return schemas.ActivityFeedOut(
        activities=activities,
        total=total,
        page=page,
        page_size=page_size,
        has_more=(page * page_size) < total,
    )


@router.post(
    "/api/v1/social/share",
    response_model=schemas.ShareOut,
    status_code=status.HTTP_201_CREATED,
)
def create_share(
    share_in: schemas.ShareCreateIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.ShareOut:
    """
    Create a new share.

    Allows users to share their achievements, badges, streaks, level ups, and certificates.
    """
    from .services import sharing

    # Validate content_id exists if provided
    if share_in.content_id:
        if share_in.share_type == "badge":
            badge_exists = (
                db.query(UserBadge)
                .filter(
                    and_(
                        UserBadge.user_id == current_user.id,
                        UserBadge.badge_id == share_in.content_id,
                    )
                )
                .first()
            )
            if not badge_exists:
                raise HTTPException(status_code=404, detail="Badge not found")

        elif share_in.share_type == "certificate":
            cert_exists = (
                db.query(Certificate)
                .filter(
                    and_(
                        Certificate.user_id == current_user.id,
                        Certificate.id == share_in.content_id,
                    )
                )
                .first()
            )
            if not cert_exists:
                raise HTTPException(status_code=404, detail="Certificate not found")

    share = sharing.create_share(
        db,
        current_user.id,
        share_in.share_type,
        share_in.content_id,
        share_in.caption,
        share_in.visibility,
    )

    return schemas.ShareOut(
        id=share.id,
        user_id=share.user_id,
        share_type=share.share_type,
        content_id=share.content_id,
        caption=share.caption,
        visibility=share.visibility,
        share_url=share.share_url,
        view_count=share.view_count,
        created_at=share.created_at,
    )


@router.get("/api/v1/social/shares/mine", response_model=schemas.ShareListOut)
def get_my_shares(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.ShareListOut:
    """
    Get current user's shares.
    """
    from .services import sharing

    shares, total = sharing.get_user_shares(db, current_user.id, page, page_size)

    # Convert to detailed output
    share_details = []
    for share in shares:
        content_data = sharing.get_content_data_for_share(db, share)

        share_detail = schemas.ShareDetailOut(
            id=share.id,
            user_id=current_user.id,
            user_display_name=current_user.display_name or current_user.email,
            user_avatar_url=current_user.avatar_url,
            user_xp=current_user.total_xp,
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


@router.get("/api/v1/social/shares/{share_id}", response_model=schemas.ShareDetailOut)
def get_share_by_id(
    share_id: UUID,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
) -> schemas.ShareDetailOut:
    """
    Get a share by ID (public endpoint with optional auth).

    Visibility rules:
    - Public shares: Anyone can view
    - Followers shares: Only followers can view
    - Private shares: Only the owner can view
    """
    from .services import sharing

    current_user_id = current_user.id if current_user else None
    share = sharing.get_share_by_id(db, share_id, current_user_id)

    if not share:
        raise HTTPException(status_code=404, detail="Share not found or not accessible")

    # Increment view count (don't count owner's views)
    if not current_user or current_user.id != share.user_id:
        sharing.increment_view_count(db, share_id)

    # Get user info
    user = db.query(User).filter(User.id == share.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    content_data = sharing.get_content_data_for_share(db, share)

    return schemas.ShareDetailOut(
        id=share.id,
        user_id=user.id,
        user_display_name=user.display_name or user.email,
        user_avatar_url=user.avatar_url,
        user_xp=user.total_xp,
        share_type=share.share_type,
        content_id=share.content_id,
        content_data=content_data,
        caption=share.caption,
        visibility=share.visibility,
        share_url=share.share_url,
        view_count=share.view_count,
        created_at=share.created_at,
    )


@router.delete("/api/v1/social/shares/{share_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_share(
    share_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Delete a share (user can only delete their own shares).
    """
    from .services import sharing

    success = sharing.delete_share(db, share_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Share not found or not authorized")

    return Response(status_code=204)
