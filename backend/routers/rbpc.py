# -*- coding: utf-8 -*-
"""LƯU NIÊN — RBPC 2026 Commercial Slice & Cultural Bridge API Router.

Public and partner endpoints under ``/api/v1/rbpc/*``:
- Configuration and active feature flags.
- Curated cultural stories and verified claim evidence.
- Source-grounded Cultural Bridge AI (strictly constrained to ``RBPC_HUE`` scope).
- Consented artisan creator profiles and living craft traditions.
- Cultural workshop experiences with honest ``inquiry_only`` availability mode.
- Visitor booking inquiries with idempotency, consent validation, and zero-PII status tracking.
- Verified platform impact metrics (202,360,638 VND sponsor support).
- Authenticated partner inbox and scoped inquiry state transitions.

Namespace: /api/v1/rbpc/*
Content Scope: RBPC_HUE
"""
from __future__ import annotations

import hmac
import logging
import re
import uuid as uuid_module
from datetime import date, datetime, timedelta, timezone
from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy import String, Text, cast, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from ..apischemas.heritage import HeritageMediaAssetOut
from ..apischemas.rbpc import (
    RbpcAvailabilityMode,
    RbpcClaimEvidenceOut,
    RbpcConfigOut,
    RbpcConsentStatus,
    RbpcCreatorConsentUpdate,
    RbpcCreatorOut,
    RbpcCulturalBridgeCitation,
    RbpcCulturalBridgeRequest,
    RbpcCulturalBridgeResponse,
    RbpcEpistemicCertainty,
    RbpcExperienceOut,
    RbpcImpactMetricsOut,
    RbpcInquiryCreate,
    RbpcInquiryOut,
    RbpcInquiryStatus,
    RbpcInquiryStatusOut,
    RbpcInquiryNotificationPreferenceUpdate,
    RbpcInquiryNotificationPreferenceOut,
    RbpcInquiryEscalationCreate,
    RbpcInquiryEscalationOut,
    RbpcInquiryWithdrawOut,
    RbpcObservedMetrics,
    RbpcPartnerInquiryListOut,
    RbpcPartnerInquiryOut,
    RbpcPartnerInquiryUpdate,
    RbpcPayoutStatus,
    RbpcProjectedMetrics,
    RbpcCustomerReviewAdminListOut,
    RbpcCustomerReviewAdminOut,
    RbpcCustomerReviewCreate,
    RbpcCustomerReviewListOut,
    RbpcCustomerReviewModeration,
    RbpcCustomerReviewOut,
    RbpcDisputeStatus,
    RbpcReviewDisputeCreate,
    RbpcReviewDisputeOut,
    RbpcReviewDisputeResolution,
    RbpcReviewStatus,
    RbpcSettlementComplianceReview,
    RbpcSettlementCreate,
    RbpcSettlementListOut,
    RbpcSettlementOut,
    RbpcSettlementRefund,
    RbpcSettlementStatus,
    RbpcLedgerFinancialSummary,
    RbpcRevenueStream,
    RbpcUnitEconomicsActualLedger,
    RbpcStoryDetailOut,
    RbpcStoryListOut,
    RbpcStoryOut,
    RbpcSupportType,
    RbpcAvailabilityCalendarOut,
    RbpcReservationCancelIn,
    RbpcReservationConfirmIn,
    RbpcReservationStatus,
    RbpcSeatReservationOut,
    RbpcSeatReserveIn,
    RbpcSlotCreateIn,
    RbpcSlotStatus,
    RbpcWorkshopSlotOut,
    RbpcAudioConsentScope,
    RbpcAudioTranscriptVersionOut,
    RbpcOralHistoryConsentUpdateIn,
    RbpcOralHistoryCreateIn,
    RbpcOralHistoryRecordingListOut,
    RbpcOralHistoryRecordingOut,
    RbpcOralHistoryRevokeIn,
    RbpcOralHistoryStatus,
    RbpcOralHistoryTranscriptUpdateIn,
    RbpcTranscriptCue,
    RbpcPartnerOnboardingIn,
    RbpcPartnerProfileUpdateIn,
    RbpcPartnerVerificationIn,
    RbpcPartnerExperienceCreateIn,
    RbpcExperienceModerationIn,
    RbpcEvidencePointerOut,
    RbpcEvidencePointerListOut,
    RbpcPitchClaimIn,
    RbpcPitchReviewIn,
    RbpcPitchReviewOut,
    RbpcEvidenceRoomExportOut,
)
from ..config import get_settings
from ..db import get_db
from ..deps import get_current_user, get_current_user_optional, verify_csrf
from ..errors import AppError
from ..models import User, UserRole
from ..models_rbpc import (
    HeritagePlace,
    HeritageSourceEvidence,
    RbpcClaimEvidence,
    RbpcContentAudit,
    RbpcCreator,
    RbpcCustomerReview,
    RbpcExperience,
    RbpcInquiry,
    RbpcOralHistoryRecording,
    RbpcAudioTranscriptVersion,
    RbpcReviewDispute,
    RbpcSeatReservation,
    RbpcSettlementLedger,
    RbpcSlotStatus,
    RbpcStory,
    RbpcWorkshopSlot,
    RbpcEvidencePointer,
    RbpcEvidenceDomain,
    RbpcEvidencePointerStatus,
    RbpcPitchClaimStatus,
    RbpcPitchReadiness,
    RbpcPitchReview,
)
from ..rbac import ADMIN_ROLES, STAFF_ROLES
from ..services import rbpc_ai
from ..services.rbpc_audit import (
    ENTITY_CREATOR,
    ENTITY_EXPERIENCE,
    record_audit_entry,
    record_creator_consent_change,
    record_inquiry_state_transition,
)
from ..services.rbpc_notification import (
    check_partner_sla_status,
    compute_sla_deadline,
    dispatch_inquiry_escalation,
    queue_inquiry_notification,
    unsubscribe_inquiry_notifications,
    update_inquiry_notification_preferences,
)
from ..services.rbpc_retention import withdraw_inquiry_consent
from ..services.rbpc_unit_economics import compute_unit_economics_ledger
from ..services.analytics import record_server_conversion_event
from ..services.rbpc_evidence_room import default_evidence_room_service, PitchClaimItem

logger = logging.getLogger("luuniensuki.rbpc")

router = APIRouter(tags=["rbpc"])

# Verified sponsorship constant: signed in-kind documentation from BNIX + Phổ Tuệ
VERIFIED_SPONSOR_VND = 202360638.0

INQUIRY_STATUS_MESSAGES = {
    RbpcInquiryStatus.new.value: "Yêu cầu đã được tiếp nhận và đang chờ nhà cung cấp/nghệ nhân xem xét.",
    RbpcInquiryStatus.contacted.value: "Nhà cung cấp đã nhận thông tin và đang liên hệ với bạn để xác nhận chi tiết.",
    RbpcInquiryStatus.confirmed.value: "Lịch hẹn trải nghiệm đã được nhà cung cấp xác nhận thành công.",
    RbpcInquiryStatus.declined.value: "Rất tiếc nhà cung cấp không thể sắp xếp lịch vào thời gian yêu cầu.",
    RbpcInquiryStatus.closed.value: "Yêu cầu trải nghiệm đã hoàn tất.",
}

# Rate limiter state for inquiry submissions: max 5 requests per IP / hour (3600 seconds)
class _InquiryRateLimitStore(dict):
    def clear(self):
        super().clear()
        try:
            from ..services.rate_limiter import rate_limiter
            rate_limiter.clear_prefix("inquiry:")
        except Exception:
            pass

_inquiry_rate_limit_store: dict[str, list[datetime]] = _InquiryRateLimitStore()
INQUIRY_RATE_LIMIT_PER_HOUR = 5
INQUIRY_RATE_LIMIT_WINDOW_SECONDS = 3600

SLUG_PATTERN = re.compile(r"^[a-zA-Z0-9_\-]{1,120}$")


def _validate_slug(slug: str) -> str:
    """Validate slug format ensuring safe alphanumeric and hyphen/underscore path parameters."""
    cleaned = (slug or "").strip().lower()
    if not cleaned or not SLUG_PATTERN.match(cleaned):
        raise AppError("INVALID_INPUT", f"Malformed slug identifier: '{slug}'.", status.HTTP_400_BAD_REQUEST)
    return cleaned

SPAM_URL_PATTERN = re.compile(r"https?://|www\.", re.IGNORECASE)
SPAM_KEYWORDS = {
    "viagra", "cialis", "casino", "poker", "porn", "xxx", "crypto",
    "bitcoin", "backlink", "seo service", "loans", "buy followers",
    "free spins", "adult dating", "slot online", "telegram:", "whatsapp:",
}
SCRIPT_PATTERN = re.compile(
    r"<script|javascript:|onload=|onerror=|<iframe|<embed|<object|<svg",
    re.IGNORECASE,
)


def _get_client_ip(request: Request) -> str:
    """Extract client IP from first hop of X-Forwarded-For or direct peer host."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        first_hop = forwarded.split(",")[0].strip()
        if first_hop:
            return first_hop
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def _check_inquiry_rate_limit(request: Request, db: Optional[Session] = None) -> str:
    """Enforce rate-limiting on inquiry submissions (max 5 requests per IP/hour)."""
    from ..services.rate_limiter import rate_limiter

    ip = _get_client_ip(request)
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(seconds=INQUIRY_RATE_LIMIT_WINDOW_SECONDS)

    # 1. Enforce distributed rate limit when db session is supplied
    if db is not None:
        if len(_inquiry_rate_limit_store) == 0 or (ip in _inquiry_rate_limit_store and len(_inquiry_rate_limit_store[ip]) == 0):
            rate_limiter.clear_prefix(f"inquiry:ip:{ip}", db=db)
        rate_limiter.check_inquiry_rate_limit(
            db=db,
            request=request,
            limit=INQUIRY_RATE_LIMIT_PER_HOUR,
            window_seconds=INQUIRY_RATE_LIMIT_WINDOW_SECONDS,
        )
        if ip not in _inquiry_rate_limit_store:
            _inquiry_rate_limit_store[ip] = []
        _inquiry_rate_limit_store[ip].append(now)
        return ip

    # 2. In-memory fallback
    if ip in _inquiry_rate_limit_store:
        _inquiry_rate_limit_store[ip] = [
            ts for ts in _inquiry_rate_limit_store[ip] if ts > window_start
        ]
    else:
        _inquiry_rate_limit_store[ip] = []

    if len(_inquiry_rate_limit_store[ip]) >= INQUIRY_RATE_LIMIT_PER_HOUR:
        earliest = min(_inquiry_rate_limit_store[ip])
        elapsed = (now - earliest).total_seconds()
        retry_after = max(1, int(INQUIRY_RATE_LIMIT_WINDOW_SECONDS - elapsed))
        logger.warning("Inquiry rate limit exceeded (5 requests/hour) for IP: %s", ip)
        headers = {
            "X-RateLimit-Limit": str(INQUIRY_RATE_LIMIT_PER_HOUR),
            "X-RateLimit-Remaining": "0",
            "Retry-After": str(retry_after),
        }
        raise AppError(
            "RATE_LIMIT_EXCEEDED",
            "Quá giới hạn gửi yêu cầu trải nghiệm (tối đa 5 yêu cầu/giờ cho mỗi IP).",
            status.HTTP_429_TOO_MANY_REQUESTS,
            details={"ip": ip, "retry_after_seconds": retry_after},
            headers=headers,
        )

    _inquiry_rate_limit_store[ip].append(now)
    return ip


def _sanitize_text(text: Optional[str]) -> Optional[str]:
    """Sanitize text by stripping HTML tags and control characters."""
    if not text:
        return None
    # Strip dangerous HTML/XML tags
    cleaned = re.sub(r"<[^>]*>", "", text)
    # Strip null bytes and non-printable control characters except \n, \r, \t
    cleaned = "".join(ch for ch in cleaned if ch in ("\n", "\r", "\t") or ch >= " ")
    cleaned = cleaned.strip()
    return cleaned if cleaned else None


def _check_anti_spam(name: str, message: Optional[str]) -> None:
    """Check name and message for spam keywords, injection patterns, and excessive links."""
    combined = f"{name} {message or ''}".lower()

    # 1. Script / injection patterns
    if SCRIPT_PATTERN.search(combined):
        raise AppError(
            "RBPC_SPAM_DETECTED",
            "Nội dung chứa mã lệnh hoặc cú pháp script bị cấm.",
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    # 2. Known commercial spam keywords
    for kw in SPAM_KEYWORDS:
        if kw in combined:
            raise AppError(
                "RBPC_SPAM_DETECTED",
                f"Yêu cầu bị từ chối do chứa từ khóa spam nghi vấn: '{kw}'.",
                status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

    # 3. Excessive URLs in inquiry message (max 2 links permitted)
    if message:
        urls = SPAM_URL_PATTERN.findall(message)
        if len(urls) > 2:
            raise AppError(
                "RBPC_SPAM_DETECTED",
                "Nội dung lời nhắn chứa quá nhiều liên kết (vượt giới hạn chống spam).",
                status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

    # 4. Excessive repetitive characters (e.g. 15 identical characters in a row)
    if re.search(r"(.)\1{14,}", combined):
        raise AppError(
            "RBPC_SPAM_DETECTED",
            "Nội dung chứa chuỗi ký tự lặp lại bất thường.",
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        )


def _validate_client_uuid(key: str) -> str:
    """Validate client UUID idempotency key preventing malformed or invalid nonces."""
    if not key or not isinstance(key, str):
        raise AppError(
            "RBPC_INVALID_IDEMPOTENCY_KEY",
            "Mã xác thực idempotency key là bắt buộc.",
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        )
    cleaned = key.strip()
    raw = cleaned
    if raw.lower().startswith("idem-key-"):
        raw = raw[9:]
    elif raw.lower().startswith("uuid-"):
        raw = raw[5:]

    try:
        parsed_uuid = uuid_module.UUID(raw)
        if not parsed_uuid:
            raise ValueError()
    except (ValueError, AttributeError, TypeError):
        raise AppError(
            "RBPC_INVALID_IDEMPOTENCY_KEY",
            "Idempotency key phải là UUID hợp lệ do client tạo.",
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            details={"provided_key": cleaned},
        )
    return cleaned


def _creator_to_out(creator: RbpcCreator) -> RbpcCreatorOut:
    """Transform ORM RbpcCreator into Pydantic RbpcCreatorOut schema."""
    story_slugs = [
        s.slug for s in (creator.stories or [])
        if s.status == "published" and s.content_scope == "RBPC_HUE"
    ]
    experience_slugs = [
        e.slug for e in (creator.experiences or [])
        if e.publication_state == "published"
    ]
    heritage_place_slug = (
        creator.heritage_place.slug
        if creator.heritage_place and creator.heritage_place.content_scope == "RBPC_HUE"
        else None
    )

    return RbpcCreatorOut(
        id=creator.id,
        slug=creator.slug,
        public_name=creator.public_name,
        craft_tradition_vi=creator.craft_tradition,
        craft_tradition_en=creator.craft_tradition_en,
        approved_bio_vi=creator.approved_bio_vi,
        approved_bio_en=creator.approved_bio_en,
        approved_portrait_url=creator.approved_portrait_url,
        public_region=creator.public_region,
        consent_status=creator.consent_status,
        approved_story_slugs=story_slugs,
        experience_slugs=experience_slugs,
        years_of_practice=creator.years_of_practice,
        generation_lineage=creator.generation_lineage,
        heritage_place_slug=heritage_place_slug,
        is_verified=creator.is_verified,
        verification_notes=creator.verification_notes,
        identity_document_ref=creator.identity_document_ref,
        rights_clearance_notes=creator.rights_clearance_notes,
        verified_at=creator.verified_at,
        created_at=creator.created_at,
    )


def _experience_to_out(exp: RbpcExperience) -> RbpcExperienceOut:
    """Transform ORM RbpcExperience into Pydantic RbpcExperienceOut schema."""
    creator_slug = exp.creator.slug if exp.creator else "unknown"
    creator_name = exp.creator.public_name if exp.creator else exp.provider_name

    price_amount = float(exp.indicative_price_amount) if exp.indicative_price_amount is not None else None

    return RbpcExperienceOut(
        id=exp.id,
        slug=exp.slug,
        creator_slug=creator_slug,
        creator_name=creator_name,
        title_vi=exp.title_vi,
        title_en=exp.title_en,
        description_vi=exp.description_vi,
        description_en=exp.description_en,
        area_public=exp.area_public,
        duration_minutes=exp.duration_minutes,
        indicative_pricing_display=exp.pricing_display,
        indicative_price_amount=price_amount,
        currency=exp.currency,
        availability_mode=exp.availability_mode,
        publication_state=exp.publication_state,
        cancellation_policy_text_vi=exp.cancellation_policy_text_vi,
        cancellation_policy_text_en=exp.cancellation_policy_text_en,
        max_party_size=exp.max_party_size,
        languages_supported=exp.languages_supported or ["vi"],
        notice=exp.notice or "Yêu cầu trải nghiệm chỉ là bước liên hệ xác nhận, không phải giao dịch thanh toán tức thì.",
        rights_checked=exp.rights_checked,
        moderation_notes=exp.moderation_notes,
        moderated_at=exp.moderated_at,
    )


def _story_to_out(story: RbpcStory) -> RbpcStoryOut:
    """Transform ORM RbpcStory into summary RbpcStoryOut."""
    creator_slug = story.creator.slug if story.creator else None
    experience_slug = story.experience.slug if story.experience else None
    heritage_place_slug = (
        story.place.slug
        if story.place and story.place.content_scope == "RBPC_HUE"
        else None
    )

    return RbpcStoryOut(
        id=story.id,
        slug=story.slug,
        title_vi=story.title_vi,
        title_en=story.title_en,
        intro_vi=story.intro_vi,
        intro_en=story.intro_en,
        primary_asset_url=story.primary_asset_url,
        category=story.category,
        status=story.status,
        published_at=story.published_at,
        reading_time_minutes=story.reading_time_minutes,
        creator_slug=creator_slug,
        experience_slug=experience_slug,
        heritage_place_slug=heritage_place_slug,
        content_scope=story.content_scope,
        created_at=story.created_at,
    )


# --------------------------------------------------------------------------- #
# Public Endpoints
# --------------------------------------------------------------------------- #
@router.get("/api/v1/rbpc/config", response_model=RbpcConfigOut)
def get_rbpc_config():
    """Retrieve runtime configuration, active feature flags, and consent versions.

    Zero secrets or internal keys are ever exposed.
    """
    from ..services.feature_flags import is_feature_flag_enabled

    app_settings = get_settings()
    inquiry_active = is_feature_flag_enabled("FEATURE_FLAG_RBPC_COMMERCE_ENABLED")
    ai_active = is_feature_flag_enabled("FEATURE_FLAG_AI_TUTOR_ENABLED")

    return RbpcConfigOut(
        enabled=True,
        ai_enabled=ai_active,
        inquiry_enabled=inquiry_active,
        supported_locales=["vi", "en"],
        default_locale="vi",
        demo_mode=app_settings.demo_mode_effective,
        version="1.0.0",
        privacy_notice_url="/privacy",
        terms_url="/terms",
        consent_version="rbpc-inquiry-v1",
    )


@router.get("/api/v1/rbpc/stories", response_model=RbpcStoryListOut)
def list_rbpc_stories(
    locale: str = Query(default="vi", description="Response locale."),
    category: Optional[str] = Query(default=None, description="Story category filter."),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Retrieve published curated cultural stories.

    Draft or archived stories are omitted for public visitors.
    """
    is_staff = current_user is not None and current_user.role in STAFF_ROLES

    stmt = (
        select(RbpcStory)
        .options(
            selectinload(RbpcStory.creator),
            selectinload(RbpcStory.experience),
            selectinload(RbpcStory.place),
        )
        .where(RbpcStory.content_scope == "RBPC_HUE")
    )
    if not is_staff:
        stmt = stmt.where(RbpcStory.status == "published")
    if category:
        stmt = stmt.where(RbpcStory.category == category)

    stmt = stmt.order_by(RbpcStory.published_at.desc().nullslast(), RbpcStory.created_at.desc())
    stories = list(db.scalars(stmt))

    items = [_story_to_out(s) for s in stories]
    return RbpcStoryListOut(items=items, total=len(items), locale=locale)


@router.get("/api/v1/rbpc/stories/{slug}", response_model=RbpcStoryDetailOut)
def get_rbpc_story_detail(
    slug: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Retrieve comprehensive story narrative with verified claims, artisan, and media."""
    valid_slug = _validate_slug(slug)
    is_staff = current_user is not None and current_user.role in STAFF_ROLES

    stmt = (
        select(RbpcStory)
        .options(
            selectinload(RbpcStory.creator).selectinload(RbpcCreator.stories),
            selectinload(RbpcStory.creator).selectinload(RbpcCreator.experiences),
            selectinload(RbpcStory.creator).selectinload(RbpcCreator.heritage_place),
            selectinload(RbpcStory.experience).selectinload(RbpcExperience.creator),
            selectinload(RbpcStory.place).selectinload(HeritagePlace.media_assets),
            selectinload(RbpcStory.claims),
        )
        .where(
            RbpcStory.slug == valid_slug,
            RbpcStory.content_scope == "RBPC_HUE",
        )
    )

    story = db.scalar(stmt)
    if not story:
        raise AppError("RBPC_STORY_NOT_FOUND", f"Story '{slug}' not found.", status.HTTP_404_NOT_FOUND)

    if not is_staff and story.status != "published":
        raise AppError("RBPC_STORY_NOT_FOUND", f"Story '{slug}' not found.", status.HTTP_404_NOT_FOUND)

    base_out = _story_to_out(story)

    # Claims (strictly verified or published_human_approved)
    claims_out = [
        RbpcClaimEvidenceOut(
            id=c.id,
            statement=c.statement,
            locale=c.locale,
            claim_category=c.claim_category,
            source_title=c.source_title,
            source_url=c.source_url,
            support_type=c.support_type,
            review_status=c.review_status,
            citation_label=c.citation_label,
        )
        for c in (story.claims or [])
        if c.review_status in ("verified", "published_human_approved")
    ]

    # Consented creator
    creator_out = None
    if story.creator and story.creator.consent_status in (
        RbpcConsentStatus.consented.value,
        RbpcConsentStatus.verified_written_consent.value,
    ):
        creator_out = _creator_to_out(story.creator)
        if not story.creator.is_verified:
            creator_out.approved_portrait_url = None

    # Experience (fail-closed: hidden if linked creator consent or verification is not active)
    experience_out = None
    if story.experience and story.experience.publication_state == "published":
        exp_creator = story.experience.creator or story.creator
        if not exp_creator or (
            exp_creator.consent_status in (
                RbpcConsentStatus.consented.value,
                RbpcConsentStatus.verified_written_consent.value,
            )
            and exp_creator.is_verified
        ):
            experience_out = _experience_to_out(story.experience)

    # Media assets from associated place (strictly RBPC_HUE and rights-cleared)
    media_assets = []
    if story.place and story.place.media_assets and story.place.content_scope == "RBPC_HUE":
        media_assets = [
            HeritageMediaAssetOut.model_validate(m)
            for m in story.place.media_assets
            if m.content_scope == "RBPC_HUE"
            and m.accuracy_grade != "rejected_accuracy"
            and m.content_status not in ("rejected_accuracy", "blocked", "withdrawn")
        ]

    return RbpcStoryDetailOut(
        **base_out.model_dump(),
        historical_context=story.historical_context_json,
        approved_summary_vi=story.approved_summary_vi or story.intro_vi,
        approved_summary_en=story.approved_summary_en or story.intro_en,
        evidence_claims=claims_out,
        creator=creator_out,
        experience=experience_out,
        media_assets=media_assets,
        version=story.version,
        rights_id=story.rights_id,
    )


@router.get("/api/v1/rbpc/stories/{slug}/recommendations")
def get_story_recommendations_endpoint(
    slug: str,
    locale: str = "vi",
    limit: int = 5,
    db: Session = Depends(get_db),
):
    """Retrieve curator-controlled story recommendations linked to this story.

    Invariants (V5-T105):
    - Rule-based object -> craft workshop linkages with verified historical relationships.
    - Negative abuse: Unverified artisan relationships or commercial claims are strictly hidden.
    - Strictly no implied fake imperial lineage.
    """
    valid_slug = _validate_slug(slug)
    story = db.scalar(
        select(RbpcStory).where(
            RbpcStory.slug == valid_slug,
            RbpcStory.content_scope == "RBPC_HUE",
        )
    )
    if not story:
        raise AppError("RBPC_STORY_NOT_FOUND", f"Story '{slug}' not found.", status.HTTP_404_NOT_FOUND)

    recommendations = rbpc_ai.get_curator_story_recommendations(
        db=db,
        story_slug=valid_slug,
        locale=locale,
        limit=limit,
    )
    return {
        "story_slug": valid_slug,
        "recommendations": recommendations,
        "total": len(recommendations),
        "locale": locale,
    }


@router.post(
    "/api/v1/rbpc/cultural-bridge",
    response_model=RbpcCulturalBridgeResponse,
    status_code=status.HTTP_200_OK,
)
def rbpc_cultural_bridge_ask(
    payload: RbpcCulturalBridgeRequest,
    db: Session = Depends(get_db),
) -> RbpcCulturalBridgeResponse:
    """Ask a source-grounded question to the AI Cultural Bridge.

    Scoped strictly to the selected published story and its verified claims.
    Responses require strict 5-check citation validation. When evidence is
    insufficient or entities unknown, fails closed to canonical text without
    hallucination.
    """
    _validate_slug(payload.story_slug)
    result = rbpc_ai.answer_cultural_question(
        db=db,
        question=payload.question,
        story_slug=payload.story_slug,
        locale=payload.locale,
        context_preferences=payload.context_preferences,
        payload=payload,
    )
    return RbpcCulturalBridgeResponse(**result)


@router.get("/api/v1/rbpc/creators/{slug}", response_model=RbpcCreatorOut)
def get_rbpc_creator(
    slug: str,
    db: Session = Depends(get_db),
):
    """Retrieve living practitioner profile with verified written consent."""
    valid_slug = _validate_slug(slug)
    creator = db.scalar(
        select(RbpcCreator)
        .options(
            selectinload(RbpcCreator.stories),
            selectinload(RbpcCreator.experiences),
            selectinload(RbpcCreator.heritage_place),
        )
        .where(RbpcCreator.slug == valid_slug)
    )
    if not creator:
        raise AppError("RBPC_CREATOR_NOT_FOUND", f"Creator '{slug}' not found.", status.HTTP_404_NOT_FOUND)

    # Consent gate: only consented artisans are published
    if creator.consent_status not in (
        RbpcConsentStatus.consented.value,
        RbpcConsentStatus.verified_written_consent.value,
    ):
        raise AppError("RBPC_CREATOR_NOT_FOUND", f"Creator '{slug}' not found.", status.HTTP_404_NOT_FOUND)

    res = _creator_to_out(creator)
    # Anti-abuse invariant: unverified creator portrait must not be displayed publicly
    if not creator.is_verified:
        res.approved_portrait_url = None
    return res


@router.get("/api/v1/rbpc/experiences/{slug}", response_model=RbpcExperienceOut)
def get_rbpc_experience(
    slug: str,
    db: Session = Depends(get_db),
):
    """Retrieve details of a cultural workshop offering with honest inquiry-only notice."""
    valid_slug = _validate_slug(slug)
    exp = db.scalar(
        select(RbpcExperience)
        .options(selectinload(RbpcExperience.creator))
        .where(
            RbpcExperience.slug == valid_slug,
            RbpcExperience.publication_state == "published",
        )
    )
    if not exp:
        raise AppError("RBPC_EXPERIENCE_NOT_FOUND", f"Experience '{slug}' not found.", status.HTTP_404_NOT_FOUND)

    # Consent gate: if linked to an artisan creator, creator must be actively consented
    if exp.creator and exp.creator.consent_status not in (
        RbpcConsentStatus.consented.value,
        RbpcConsentStatus.verified_written_consent.value,
    ):
        raise AppError("RBPC_EXPERIENCE_NOT_FOUND", f"Experience '{slug}' not found.", status.HTTP_404_NOT_FOUND)

    # Verification gate: if linked creator is unverified or rights not checked, cannot publish to public
    if exp.creator and not exp.creator.is_verified:
        raise AppError("RBPC_EXPERIENCE_NOT_FOUND", f"Experience '{slug}' not found.", status.HTTP_404_NOT_FOUND)

    return _experience_to_out(exp)


def _evaluate_inquiry_idempotency(
    existing: RbpcInquiry,
    exp_id: UUID,
    sanitized_name: str,
    sanitized_contact_value: str,
    party_size: int,
) -> JSONResponse:
    """Validate consistency of an existing inquiry matching idempotency key.

    Returns HTTP 202 with original receipt if payload matches.
    Raises HTTP 409 RBPC_IDEMPOTENCY_CONFLICT if payload differs.
    """
    if (
        existing.experience_id != exp_id
        or existing.name != sanitized_name
        or existing.contact_value != sanitized_contact_value
        or existing.party_size != party_size
    ):
        raise AppError(
            "RBPC_IDEMPOTENCY_CONFLICT",
            "Idempotency key has already been used with differing parameters.",
            status.HTTP_409_CONFLICT,
        )
    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content=RbpcInquiryOut(
            reference=existing.public_ref,
            status_token=existing.opaque_token,
            status=existing.state,
            message="Yêu cầu đã được ghi nhận trước đó. Nhà cung cấp sẽ liên hệ xác nhận lịch trống trong vòng 24 giờ.",
            created_at=existing.created_at,
        ).model_dump(mode="json"),
    )


@router.post("/api/v1/rbpc/inquiries", status_code=status.HTTP_202_ACCEPTED, response_model=RbpcInquiryOut)
def create_rbpc_inquiry(
    payload: RbpcInquiryCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    """Submit a visitor booking/availability inquiry.

    Requires idempotency key, explicit opt-in consent, and future preferred date.
    Zero automated simulated payment: routes to partner review.
    """
    from ..services.feature_flags import assert_kill_switch_active

    assert_kill_switch_active(
        "FEATURE_FLAG_RBPC_COMMERCE_ENABLED",
        feature_name="Đặt lịch & Tiếp nhận yêu cầu Trải nghiệm",
        friendly_message="Hệ thống tiếp nhận yêu cầu đặt lịch trải nghiệm đang tạm ngưng bảo trì. Vui lòng quay lại sau.",
        db=db,
    )

    # Guardrail 1: Rate limiting (max 5 requests per IP/hour)
    _check_inquiry_rate_limit(request, db=db)

    # Guardrail 2: Client UUID idempotency key validation
    validated_key = _validate_client_uuid(payload.idempotency_key)

    # Guardrail 3: Explicit consent and privacy policy validation
    if not payload.consent.accepted or not payload.consent.privacy_accepted:
        raise AppError(
            "RBPC_CONSENT_REQUIRED",
            "Explicit consent and privacy policy must be accepted.",
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    # Guardrail 4: Preferred date must not be in the past
    if payload.preferred_date and payload.preferred_date < date.today():
        raise AppError(
            "RBPC_DATE_PAST",
            "Preferred date cannot be in the past.",
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    # Guardrail 5: Strict input sanitization & anti-spam validation
    _check_anti_spam(payload.contact.name, payload.message)

    sanitized_name = _sanitize_text(payload.contact.name) or ""
    if len(sanitized_name) < 2:
        raise AppError(
            "RBPC_INVALID_INPUT",
            "Tên người liên hệ không hợp lệ hoặc quá ngắn.",
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        )
    sanitized_message = _sanitize_text(payload.message)
    sanitized_contact_value = payload.contact.value.strip()

    # Experience verification
    exp = db.scalar(
        select(RbpcExperience)
        .options(selectinload(RbpcExperience.creator))
        .where(
            RbpcExperience.slug == payload.experience_slug.strip().lower(),
            RbpcExperience.publication_state == "published",
        )
    )
    if not exp:
        raise AppError(
            "RBPC_EXPERIENCE_NOT_FOUND",
            f"Experience '{payload.experience_slug}' not found.",
            status.HTTP_404_NOT_FOUND,
        )

    if exp.availability_mode == "disabled":
        raise AppError(
            "RBPC_INQUIRY_DISABLED",
            "Trải nghiệm này hiện không tiếp nhận yêu cầu đặt chỗ.",
            status.HTTP_400_BAD_REQUEST,
        )

    if exp.creator and exp.creator.consent_status not in ("consented", "verified_written_consent"):
        raise AppError(
            "RBPC_CREATOR_CONSENT_UNAVAILABLE",
            "Nghệ nhân chưa hoàn tất thỏa thuận đồng thuận công khai.",
            status.HTTP_400_BAD_REQUEST,
        )

    exp_id = exp.id

    # Guardrail 6: Idempotency check
    existing = db.scalar(
        select(RbpcInquiry).where(RbpcInquiry.idempotency_key == validated_key)
    )
    if existing:
        return _evaluate_inquiry_idempotency(
            existing=existing,
            exp_id=exp_id,
            sanitized_name=sanitized_name,
            sanitized_contact_value=sanitized_contact_value,
            party_size=payload.party_size,
        )

    # Non-sequential reference code & high-entropy status bearer token
    hex_ref = uuid_module.uuid4().hex[:8].upper()
    public_ref = f"INQ-{hex_ref[:4]}-{hex_ref[4:]}"
    opaque_token = f"tok_sec_{uuid_module.uuid4().hex}"
    now = datetime.now(timezone.utc)
    sla_due_at = compute_sla_deadline(now)

    inquiry = RbpcInquiry(
        public_ref=public_ref,
        experience_id=exp_id,
        provider_id=exp.provider_id or exp.creator_id,
        name=sanitized_name,
        contact_channel=payload.contact.method.value,
        contact_value=sanitized_contact_value,
        desired_date=payload.preferred_date,
        party_size=payload.party_size,
        message=sanitized_message,
        consent_version=payload.consent.version,
        consent_time_utc=now,
        privacy_accepted=payload.consent.privacy_accepted,
        state=RbpcInquiryStatus.new.value,
        idempotency_key=validated_key,
        opaque_token=opaque_token,
        retention_due_at=now + timedelta(days=90),
        sla_due_at=sla_due_at,
        email_opt_in=payload.email_opt_in,
        sms_opt_in=payload.sms_opt_in,
        notification_preferences={"frequency": "immediate"},
    )
    db.add(inquiry)

    try:
        db.flush()

        # Append immutable audit entry with zero PII
        record_audit_entry(
            db,
            entity_type="inquiry",
            entity_id=inquiry.id,
            action="inquiry_created",
            actor_id=None,
            diff_payload={
                "public_ref": inquiry.public_ref,
                "state": inquiry.state,
                "party_size": inquiry.party_size,
                "consent_version": inquiry.consent_version,
                "experience_id": str(inquiry.experience_id),
                "sla_due_at": inquiry.sla_due_at.isoformat() if inquiry.sla_due_at else None,
            },
        )

        # Queue partner notification in outbox with fault-tolerant delivery
        queue_inquiry_notification(db, inquiry, event_type="inquiry_created")

        # Record authoritative server-verified conversion event (zero PII)
        record_server_conversion_event(
            db=db,
            event_name="inquiry_submit",
            payload={
                "inquiry_id": str(inquiry.id),
                "public_ref": inquiry.public_ref,
                "experience_id": str(inquiry.experience_id),
                "party_size": inquiry.party_size,
            },
            idempotency_key=f"srv_inq_sub_{inquiry.id}",
            is_demo=False,
            is_synthetic=False,
        )

        db.commit()
        db.refresh(inquiry)
    except IntegrityError:
        db.rollback()
        # Concurrent race condition: another transaction committed with the same idempotency key
        existing_raced = db.scalar(
            select(RbpcInquiry).where(RbpcInquiry.idempotency_key == validated_key)
        )
        if existing_raced:
            logger.info(
                "Handled concurrent inquiry race condition for idempotency key %s",
                validated_key,
            )
            return _evaluate_inquiry_idempotency(
                existing=existing_raced,
                exp_id=exp_id,
                sanitized_name=sanitized_name,
                sanitized_contact_value=sanitized_contact_value,
                party_size=payload.party_size,
            )
        raise

    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content=RbpcInquiryOut(
            reference=inquiry.public_ref,
            status_token=inquiry.opaque_token,
            status=RbpcInquiryStatus.new,
            message="Yêu cầu đã được ghi nhận. Nhà cung cấp sẽ liên hệ xác nhận lịch trống trong vòng 24 giờ.",
            created_at=inquiry.created_at,
        ).model_dump(mode="json"),
    )


@router.get("/api/v1/rbpc/inquiries/status/{opaqueToken}", response_model=RbpcInquiryStatusOut)
def get_inquiry_status_by_token(
    opaqueToken: str,
    db: Session = Depends(get_db),
):
    """Visitor status lookup via high-entropy secret bearer token.

    ZERO PII Invariant: Email, phone, name, and partner internal notes are
    never disclosed in this response.
    """
    cleaned_token = (opaqueToken or "").strip()
    if not cleaned_token:
        raise AppError("RBPC_INQUIRY_NOT_FOUND", "Inquiry not found for status token.", status.HTTP_404_NOT_FOUND)

    inquiry = db.scalar(
        select(RbpcInquiry)
        .options(selectinload(RbpcInquiry.experience))
        .where(RbpcInquiry.opaque_token == cleaned_token)
    )
    if not inquiry:
        raise AppError("RBPC_INQUIRY_NOT_FOUND", "Inquiry not found for status token.", status.HTTP_404_NOT_FOUND)

    # Constant-time comparison to prevent timing side-channel attacks on bearer token
    if not hmac.compare_digest(inquiry.opaque_token, cleaned_token):
        raise AppError("RBPC_INQUIRY_NOT_FOUND", "Inquiry not found for status token.", status.HTTP_404_NOT_FOUND)

    # TTL / Retention expiration check: Expired inquiries return 404 NOT_FOUND
    now = datetime.now(timezone.utc)
    if inquiry.retention_due_at is not None:
        retention_time = inquiry.retention_due_at
        if retention_time.tzinfo is None:
            retention_time = retention_time.replace(tzinfo=timezone.utc)
        if retention_time <= now:
            raise AppError("RBPC_INQUIRY_NOT_FOUND", "Inquiry not found or token expired.", status.HTTP_404_NOT_FOUND)

    exp_title = inquiry.experience.title_vi if inquiry.experience else "Trải nghiệm văn hóa"
    if not inquiry.privacy_accepted:
        status_msg = "Yêu cầu đã được rút lại và thông tin liên hệ cá nhân đã được xóa theo chính sách bảo mật."
    else:
        status_msg = INQUIRY_STATUS_MESSAGES.get(inquiry.state, "Trạng thái đang được cập nhật.")

    sla_info = check_partner_sla_status(inquiry, as_of=now)
    # Can escalate if inquiry is still open/pending and partner SLA is overdue
    can_escalate = (
        inquiry.state in (RbpcInquiryStatus.new.value, "new")
        and sla_info.is_overdue
        and inquiry.privacy_accepted
    )

    return RbpcInquiryStatusOut(
        reference=inquiry.public_ref,
        experience_title=exp_title,
        status=inquiry.state,
        status_message=status_msg,
        preferred_date=inquiry.desired_date,
        party_size=inquiry.party_size,
        last_updated_at=inquiry.updated_at,
        email_opt_in=inquiry.email_opt_in,
        sms_opt_in=inquiry.sms_opt_in,
        is_overdue=sla_info.is_overdue,
        sla_due_at=inquiry.sla_due_at,
        can_escalate=can_escalate,
        escalated_at=inquiry.escalated_at,
        escalation_reason=inquiry.escalation_reason,
        escalation_count=inquiry.escalation_count,
    )


@router.post(
    "/api/v1/rbpc/inquiries/status/{opaqueToken}/preferences",
    response_model=RbpcInquiryNotificationPreferenceOut,
)
def update_inquiry_preferences_by_token(
    opaqueToken: str,
    payload: RbpcInquiryNotificationPreferenceUpdate,
    db: Session = Depends(get_db),
):
    """Customer Notification Center: Update notification channels (Email / SMS) opt-in preferences."""
    cleaned_token = (opaqueToken or "").strip()
    if not cleaned_token:
        raise AppError("RBPC_INQUIRY_NOT_FOUND", "Inquiry not found for status token.", status.HTTP_404_NOT_FOUND)

    inquiry = db.scalar(
        select(RbpcInquiry)
        .where(RbpcInquiry.opaque_token == cleaned_token)
    )
    if not inquiry or not hmac.compare_digest(inquiry.opaque_token, cleaned_token):
        raise AppError("RBPC_INQUIRY_NOT_FOUND", "Inquiry not found for status token.", status.HTTP_404_NOT_FOUND)

    now = datetime.now(timezone.utc)
    if inquiry.retention_due_at is not None:
        retention_time = inquiry.retention_due_at
        if retention_time.tzinfo is None:
            retention_time = retention_time.replace(tzinfo=timezone.utc)
        if retention_time <= now:
            raise AppError("RBPC_INQUIRY_NOT_FOUND", "Inquiry not found or token expired.", status.HTTP_404_NOT_FOUND)

    if not inquiry.privacy_accepted:
        raise AppError("RBPC_INQUIRY_WITHDRAWN", "Inquiry consent has been withdrawn.", status.HTTP_400_BAD_REQUEST)

    update_inquiry_notification_preferences(
        db,
        inquiry=inquiry,
        email_opt_in=payload.email_opt_in,
        sms_opt_in=payload.sms_opt_in,
        frequency=payload.frequency,
    )
    db.commit()
    db.refresh(inquiry)

    unsubscribed = (not inquiry.email_opt_in and not inquiry.sms_opt_in)
    return RbpcInquiryNotificationPreferenceOut(
        reference=inquiry.public_ref,
        email_opt_in=inquiry.email_opt_in,
        sms_opt_in=inquiry.sms_opt_in,
        unsubscribed=unsubscribed,
        message="Cập nhật tùy chọn thông báo thành công." if not unsubscribed else "Đã hủy đăng ký nhận thông báo cập nhật qua Email và SMS.",
        updated_at=inquiry.updated_at,
    )


@router.post(
    "/api/v1/rbpc/inquiries/status/{opaqueToken}/unsubscribe",
    response_model=RbpcInquiryNotificationPreferenceOut,
)
def unsubscribe_inquiry_by_token(
    opaqueToken: str,
    db: Session = Depends(get_db),
):
    """Customer Notification Center: Unsubscribe from all optional email and SMS notifications."""
    cleaned_token = (opaqueToken or "").strip()
    if not cleaned_token:
        raise AppError("RBPC_INQUIRY_NOT_FOUND", "Inquiry not found for status token.", status.HTTP_404_NOT_FOUND)

    inquiry = db.scalar(
        select(RbpcInquiry)
        .where(RbpcInquiry.opaque_token == cleaned_token)
    )
    if not inquiry or not hmac.compare_digest(inquiry.opaque_token, cleaned_token):
        raise AppError("RBPC_INQUIRY_NOT_FOUND", "Inquiry not found for status token.", status.HTTP_404_NOT_FOUND)

    now = datetime.now(timezone.utc)
    if inquiry.retention_due_at is not None:
        retention_time = inquiry.retention_due_at
        if retention_time.tzinfo is None:
            retention_time = retention_time.replace(tzinfo=timezone.utc)
        if retention_time <= now:
            raise AppError("RBPC_INQUIRY_NOT_FOUND", "Inquiry not found or token expired.", status.HTTP_404_NOT_FOUND)

    unsubscribe_inquiry_notifications(db, inquiry=inquiry)
    db.commit()
    db.refresh(inquiry)

    return RbpcInquiryNotificationPreferenceOut(
        reference=inquiry.public_ref,
        email_opt_in=inquiry.email_opt_in,
        sms_opt_in=inquiry.sms_opt_in,
        unsubscribed=True,
        message="Đã hủy đăng ký tất cả các kênh thông báo tự động (Email/SMS).",
        updated_at=inquiry.updated_at,
    )


@router.post(
    "/api/v1/rbpc/inquiries/status/{opaqueToken}/escalate",
    response_model=RbpcInquiryEscalationOut,
)
def escalate_inquiry_by_token(
    opaqueToken: str,
    payload: Optional[RbpcInquiryEscalationCreate] = None,
    db: Session = Depends(get_db),
):
    """Customer Notification Center: Escalate late partner response when SLA (24h) is overdue.

    Negative abuse invariant (V5-T103):
    Network or provider error never shows or sends fake confirmed status.
    Escalations only apply to inquiries that are overdue and not already resolved/closed.
    """
    cleaned_token = (opaqueToken or "").strip()
    if not cleaned_token:
        raise AppError("RBPC_INQUIRY_NOT_FOUND", "Inquiry not found for status token.", status.HTTP_404_NOT_FOUND)

    inquiry = db.scalar(
        select(RbpcInquiry)
        .options(selectinload(RbpcInquiry.experience))
        .where(RbpcInquiry.opaque_token == cleaned_token)
    )
    if not inquiry or not hmac.compare_digest(inquiry.opaque_token, cleaned_token):
        raise AppError("RBPC_INQUIRY_NOT_FOUND", "Inquiry not found for status token.", status.HTTP_404_NOT_FOUND)

    now = datetime.now(timezone.utc)
    if inquiry.retention_due_at is not None:
        retention_time = inquiry.retention_due_at
        if retention_time.tzinfo is None:
            retention_time = retention_time.replace(tzinfo=timezone.utc)
        if retention_time <= now:
            raise AppError("RBPC_INQUIRY_NOT_FOUND", "Inquiry not found or token expired.", status.HTTP_404_NOT_FOUND)

    if not inquiry.privacy_accepted:
        raise AppError("RBPC_INQUIRY_WITHDRAWN", "Inquiry consent has been withdrawn.", status.HTTP_400_BAD_REQUEST)

    if inquiry.state in ("confirmed", "declined", "closed"):
        raise AppError(
            "RBPC_INQUIRY_ALREADY_RESOLVED",
            f"Hồ sơ đã ở trạng thái {inquiry.state}, không thể thực hiện khiếu nại quá hạn.",
            status.HTTP_400_BAD_REQUEST,
        )

    sla_info = check_partner_sla_status(inquiry, as_of=now)
    if not sla_info.is_overdue:
        raise AppError(
            "RBPC_INQUIRY_SLA_NOT_OVERDUE",
            f"Hồ sơ vẫn đang trong thời hạn phản hồi tiêu chuẩn 24 giờ (còn {sla_info.hours_remaining} giờ).",
            status.HTTP_400_BAD_REQUEST,
            details={"hours_remaining": sla_info.hours_remaining},
        )

    # Cooldown check: max 1 escalation per hour
    if inquiry.escalated_at:
        esc_time = inquiry.escalated_at
        if esc_time.tzinfo is None:
            esc_time = esc_time.replace(tzinfo=timezone.utc)
        if (now - esc_time).total_seconds() < 3600:
            raise AppError(
                "RBPC_ESCALATION_COOLDOWN",
                "Yêu cầu nhắc nhở đã được gửi. Vui lòng chờ ít nhất 1 giờ trước khi gửi nhắc nhở tiếp theo.",
                status.HTTP_429_TOO_MANY_REQUESTS,
                details={"retry_after_seconds": int(3600 - (now - esc_time).total_seconds())},
            )

    reason_str = payload.reason if payload else None
    escalation_res = dispatch_inquiry_escalation(
        db,
        inquiry=inquiry,
        reason=reason_str,
    )
    db.commit()
    db.refresh(inquiry)

    return RbpcInquiryEscalationOut(
        reference=inquiry.public_ref,
        status=inquiry.state,
        escalated_at=escalation_res["escalated_at"],
        escalation_count=escalation_res["escalation_count"],
        sla_overdue_seconds=sla_info.overdue_by_seconds,
        message="Đã gửi thông báo nhắc nhở khẩn cấp đến đối tác quản lý xưởng nghề.",
        notification_dispatched=escalation_res["notification_dispatched"],
    )


@router.post(
    "/api/v1/rbpc/inquiries/status/{opaqueToken}/withdraw",
    response_model=RbpcInquiryWithdrawOut,
)
def withdraw_inquiry_status_consent(
    opaqueToken: str,
    db: Session = Depends(get_db),
):
    """Allow visitor to withdraw consent and redact contact details immediately.

    Vietnam Decree 13/2023/ND-CP Article 11 right of withdrawal / right to erasure:
    - Scrubs name, contact_value, message to remove visitor PII
    - Marks privacy_accepted = False and state = closed
    - Appends immutable cryptographic audit entry to rbpc_content_audit
    """
    inquiry = withdraw_inquiry_consent(db, opaque_token=opaqueToken)
    db.commit()
    db.refresh(inquiry)

    exp_title = inquiry.experience.title_vi if inquiry.experience else "Trải nghiệm văn hóa"
    return RbpcInquiryWithdrawOut(
        reference=inquiry.public_ref,
        experience_title=exp_title,
        status=inquiry.state,
        status_message="Đồng thuận đã được rút lại. Toàn bộ thông tin liên hệ đã được ẩn danh/xóa bỏ.",
        privacy_accepted=inquiry.privacy_accepted,
        preferred_date=inquiry.desired_date,
        party_size=inquiry.party_size,
        last_updated_at=inquiry.updated_at,
    )


@router.get("/api/v1/rbpc/impact", response_model=RbpcImpactMetricsOut)
def get_rbpc_impact_metrics(
    db: Session = Depends(get_db),
):
    """Retrieve aggregate platform metrics.

    Separates real database-observed statistics from forward commercial projections.
    Includes verified 202,360,638 VND sponsor in-kind support.
    """
    published_stories_count = (
        db.scalar(
            select(func.count(RbpcStory.id)).where(
                RbpcStory.status == "published",
                RbpcStory.content_scope == "RBPC_HUE",
            )
        )
        or 0
    )

    consented_creators_count = (
        db.scalar(
            select(func.count(RbpcCreator.id)).where(
                RbpcCreator.consent_status.in_(["consented", "verified_written_consent"])
            )
        )
        or 0
    )

    active_experiences_count = (
        db.scalar(
            select(func.count(RbpcExperience.id)).where(
                RbpcExperience.publication_state == "published",
                RbpcExperience.availability_mode == "inquiry_only",
            )
        )
        or 0
    )

    total_inquiries_received = db.scalar(select(func.count(RbpcInquiry.id))) or 0

    verified_heritage_places_count = (
        db.scalar(
            select(func.count(HeritagePlace.id)).where(
                HeritagePlace.editorial_status == "published",
                HeritagePlace.content_scope == "RBPC_HUE",
            )
        )
        or 0
    )

    verified_source_citations_count = (
        db.scalar(
            select(func.count(HeritageSourceEvidence.id)).where(
                HeritageSourceEvidence.evidence_status == "verified",
                HeritageSourceEvidence.content_scope == "RBPC_HUE",
            )
        )
        or 0
    )

    # Completed experiences: strictly verified completed inquiry requests (state == 'closed')
    completed_experiences_count = (
        db.scalar(
            select(func.count(RbpcInquiry.id)).where(
                RbpcInquiry.state == "closed",
            )
        )
        or 0
    )

    # Actual artisan payouts: strictly aggregated from verified settlements in 'approved' or 'settled' status
    artisan_payout_vnd_settled = float(
        db.scalar(
            select(func.coalesce(func.sum(RbpcSettlementLedger.artisan_payout_vnd), 0.0)).where(
                RbpcSettlementLedger.status.in_(["approved", "settled"]),
            )
        )
        or 0.0
    )

    return RbpcImpactMetricsOut(
        observed_metrics=RbpcObservedMetrics(
            published_stories_count=published_stories_count,
            consented_creators_count=consented_creators_count,
            active_experiences_count=active_experiences_count,
            total_inquiries_received=total_inquiries_received,
            verified_heritage_places_count=verified_heritage_places_count,
            verified_source_citations_count=verified_source_citations_count,
            completed_experiences_count=completed_experiences_count,
            artisan_payout_vnd_settled=artisan_payout_vnd_settled,
            sponsor_support_vnd_verified=VERIFIED_SPONSOR_VND,
        ),
        projected_metrics=RbpcProjectedMetrics(
            estimated_monthly_demand=120,
            projected_local_value_addition_vnd=54000000.0,
            projection_basis="Các số liệu dự phóng là giả định mô hình kinh doanh phục vụ nghiên cứu và đề án RBPC 2026, không phải doanh thu đã ghi nhận.",
        ),
        scope="RBPC_HUE",
        generated_at=datetime.now(timezone.utc),
    )


# --------------------------------------------------------------------------- #
# Partner Endpoints (Authenticated)
# --------------------------------------------------------------------------- #
VALID_INQUIRY_TRANSITIONS: dict[str, set[str]] = {
    RbpcInquiryStatus.new.value: {
        RbpcInquiryStatus.contacted.value,
    },
    RbpcInquiryStatus.contacted.value: {
        RbpcInquiryStatus.confirmed.value,
        RbpcInquiryStatus.declined.value,
        RbpcInquiryStatus.closed.value,
    },
    RbpcInquiryStatus.confirmed.value: {
        RbpcInquiryStatus.closed.value,
    },
    RbpcInquiryStatus.declined.value: {
        RbpcInquiryStatus.closed.value,
    },
    RbpcInquiryStatus.closed.value: set(),
}


@router.get("/api/v1/rbpc/partner/inquiries", response_model=RbpcPartnerInquiryListOut)
def list_partner_inquiries(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve incoming visitor inquiries for the authenticated provider.

    Enforces strict server-side scoping: non-staff callers only view inquiries
    belonging to their own provider account.
    """
    is_admin = current_user.role in ADMIN_ROLES
    if current_user.role == UserRole.guest:
        raise AppError("FORBIDDEN", "Guest users cannot access partner inquiries.", status.HTTP_403_FORBIDDEN)

    stmt = select(RbpcInquiry).options(selectinload(RbpcInquiry.experience))
    if not is_admin:
        # Provider scoping: strictly provider ownership (provider_id or linked experience.provider_id)
        # Any client query param (such as ?provider=...) is strictly ignored for non-admin callers.
        stmt = stmt.outerjoin(RbpcInquiry.experience).where(
            or_(
                RbpcInquiry.provider_id == current_user.id,
                RbpcExperience.provider_id == current_user.id,
            )
        )
    else:
        # Admin callers can view all cross-tenant inquiries or optionally filter by provider
        provider_param = request.query_params.get("provider")
        if provider_param:
            try:
                target_uuid = UUID(provider_param)
                stmt = stmt.outerjoin(RbpcInquiry.experience).where(
                    or_(
                        RbpcInquiry.provider_id == target_uuid,
                        RbpcExperience.provider_id == target_uuid,
                    )
                )
            except ValueError:
                pass

    stmt = stmt.order_by(RbpcInquiry.created_at.desc())
    inquiries = list(db.scalars(stmt))

    items = [
        RbpcPartnerInquiryOut(
            id=inq.id,
            reference=inq.public_ref,
            experience_slug=inq.experience.slug if inq.experience else "unknown",
            experience_title=inq.experience.title_vi if inq.experience else "Trải nghiệm",
            contact_name=inq.name,
            contact_method=inq.contact_channel,
            contact_value=inq.contact_value,
            preferred_date=inq.desired_date,
            party_size=inq.party_size,
            message=inq.message,
            status=inq.state,
            created_at=inq.created_at,
            updated_at=inq.updated_at,
        )
        for inq in inquiries
    ]

    return RbpcPartnerInquiryListOut(items=items, total=len(items))


@router.patch("/api/v1/rbpc/partner/inquiries/{id}", response_model=RbpcPartnerInquiryOut)
def update_partner_inquiry_status(
    id: UUID,
    payload: RbpcPartnerInquiryUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Transition inquiry status (new -> contacted -> confirmed / declined / closed).

    Rejects unauthorized access with 403 FORBIDDEN_SCOPE.
    Enforces valid lifecycle state transitions.
    """
    verify_csrf(request)

    if payload.note is not None:
        if SCRIPT_PATTERN.search(payload.note):
            raise AppError(
                "MALICIOUS_INPUT_DETECTED",
                "Nội dung ghi chú chứa mã lệnh hoặc cú pháp script bị cấm.",
                status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        cleaned_note = _sanitize_text(payload.note) or ""
        payload.note = cleaned_note

    inquiry = db.scalar(
        select(RbpcInquiry)
        .options(selectinload(RbpcInquiry.experience))
        .where(RbpcInquiry.id == id)
    )
    if not inquiry:
        raise AppError("RBPC_INQUIRY_NOT_FOUND", f"Inquiry '{id}' not found.", status.HTTP_404_NOT_FOUND)

    is_admin = current_user.role in ADMIN_ROLES
    if current_user.role == UserRole.guest:
        raise AppError("FORBIDDEN", "Guest users cannot manage partner inquiries.", status.HTTP_403_FORBIDDEN)
    if not is_admin:
        exp = inquiry.experience
        is_owner = (
            inquiry.provider_id == current_user.id
            or (exp is not None and exp.provider_id == current_user.id)
        )
        if not is_owner:
            raise AppError("FORBIDDEN_SCOPE", "You do not have permission to manage this inquiry.", status.HTTP_403_FORBIDDEN)

    target_state = payload.status.value
    # Idempotent replay: if inquiry is already at target_state, return early without error or duplicate audit
    if inquiry.state == target_state:
        if payload.note is not None and payload.note != inquiry.internal_note:
            inquiry.internal_note = payload.note
            inquiry.updated_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(inquiry)
        return RbpcPartnerInquiryOut(
            id=inquiry.id,
            reference=inquiry.public_ref,
            experience_slug=inquiry.experience.slug if inquiry.experience else "unknown",
            experience_title=inquiry.experience.title_vi if inquiry.experience else "Trải nghiệm",
            contact_name=inquiry.name,
            contact_method=inquiry.contact_channel,
            contact_value=inquiry.contact_value,
            preferred_date=inquiry.desired_date,
            party_size=inquiry.party_size,
            message=inquiry.message,
            status=inquiry.state,
            created_at=inquiry.created_at,
            updated_at=inquiry.updated_at,
        )

    allowed_transitions = VALID_INQUIRY_TRANSITIONS.get(inquiry.state, set())
    if target_state not in allowed_transitions:
        raise AppError(
            "RBPC_INVALID_TRANSITION",
            f"Cannot transition inquiry from '{inquiry.state}' to '{target_state}'.",
            status.HTTP_400_BAD_REQUEST,
            details={
                "current_status": inquiry.state,
                "target_status": target_state,
                "allowed_transitions": sorted(allowed_transitions),
            },
        )

    old_state = inquiry.state
    inquiry.state = target_state
    if payload.note is not None:
        inquiry.internal_note = payload.note
    inquiry.updated_at = datetime.now(timezone.utc)

    # Append immutable cryptographic audit entry for state transition
    record_inquiry_state_transition(
        db,
        inquiry=inquiry,
        old_state=old_state,
        new_state=inquiry.state,
        actor_id=current_user.id,
        note=payload.note,
    )

    # Record server-verified business conversion event when confirmed
    if str(inquiry.state).lower() in ("confirmed", "closed"):
        record_server_conversion_event(
            db=db,
            event_name="inquiry_confirm",
            payload={
                "inquiry_id": str(inquiry.id),
                "public_ref": inquiry.public_ref,
                "experience_id": str(inquiry.experience_id),
                "state": inquiry.state,
            },
            idempotency_key=f"srv_inq_conf_{inquiry.id}",
            is_demo=False,
            is_synthetic=False,
        )

    db.commit()
    db.refresh(inquiry)

    return RbpcPartnerInquiryOut(
        id=inquiry.id,
        reference=inquiry.public_ref,
        experience_slug=inquiry.experience.slug if inquiry.experience else "unknown",
        experience_title=inquiry.experience.title_vi if inquiry.experience else "Trải nghiệm",
        contact_name=inquiry.name,
        contact_method=inquiry.contact_channel,
        contact_value=inquiry.contact_value,
        preferred_date=inquiry.desired_date,
        party_size=inquiry.party_size,
        message=inquiry.message,
        status=inquiry.state,
        created_at=inquiry.created_at,
        updated_at=inquiry.updated_at,
    )


# --------------------------------------------------------------------------- #
# Editor Endpoints (Authenticated Staff / Admin)
# --------------------------------------------------------------------------- #
@router.post(
    "/api/v1/rbpc/editor/creators/{id}/consent",
    response_model=RbpcCreatorOut,
)
def update_creator_consent(
    id: UUID,
    payload: RbpcCreatorConsentUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Allow editors to update artisan consent state (consented, pending_review, revoked).

    Enforces editor/staff permissions (STAFF_ROLES) and logs cryptographic audit trail.
    """
    verify_csrf(request)
    if current_user.role not in STAFF_ROLES:
        raise AppError(
            "FORBIDDEN_SCOPE",
            "Chỉ biên tập viên hoặc quản trị viên mới có quyền cập nhật trạng thái đồng thuận nghệ nhân.",
            status.HTTP_403_FORBIDDEN,
        )

    creator = db.scalar(
        select(RbpcCreator)
        .options(
            selectinload(RbpcCreator.stories),
            selectinload(RbpcCreator.experiences),
            selectinload(RbpcCreator.heritage_place),
        )
        .where(RbpcCreator.id == id)
    )
    if not creator:
        raise AppError(
            "RBPC_CREATOR_NOT_FOUND",
            f"Artisan creator with ID '{id}' not found.",
            status.HTTP_404_NOT_FOUND,
        )

    old_status = creator.consent_status
    new_status = payload.consent_status.value

    # Update reviewer and display consent ref if provided
    creator.reviewer_id = current_user.id
    if payload.notes:
        if creator.display_consent_ref:
            creator.display_consent_ref = f"{creator.display_consent_ref}; {payload.notes}"[:120]
        else:
            creator.display_consent_ref = payload.notes[:120]

    # Record append-only cryptographic audit entry and update creator consent_status
    record_creator_consent_change(
        db,
        creator=creator,
        new_status=new_status,
        old_status=old_status,
        actor_id=current_user.id,
        reason=payload.notes,
        proof_ref=creator.display_consent_ref,
    )

    db.commit()
    db.refresh(creator)

    return _creator_to_out(creator)


# --------------------------------------------------------------------------- #
# Fee & Revenue Settlement Ledger Endpoints (V5-T108)
# --------------------------------------------------------------------------- #
@router.post(
    "/api/v1/rbpc/partner/settlements",
    response_model=RbpcSettlementOut,
    status_code=status.HTTP_201_CREATED,
)
def record_settlement_transaction(
    payload: RbpcSettlementCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Record an actual confirmed financial settlement for an inquiry.

    Invariants:
    1. Inquiry MUST exist and MUST be in 'confirmed' or 'closed' status. An inquiry
       in 'new' or 'contacted' status CANNOT produce a settlement record.
    2. Merely changing status to 'confirmed' does NOT create a settlement record
       nor any revenue in the ledger.
    3. Caller must be the assigned provider, experience owner, or staff/admin.
    4. Automatically computes contracted platform fee (take_rate), tax/VAT,
       and net artisan payout:
       - platform_fee = gross_amount * take_rate
       - tax_vat = gross_amount * vat_rate
       - artisan_payout = gross_amount - platform_fee - tax_vat
    5. Initial status is 'pending_compliance' and payout_status is 'pending'.
       Payout disbursement requires compliance approval.
    """
    verify_csrf(request)

    if current_user.role == UserRole.guest:
        raise AppError("FORBIDDEN", "Guest users cannot record settlements.", status.HTTP_403_FORBIDDEN)

    inquiry = db.scalar(
        select(RbpcInquiry)
        .options(selectinload(RbpcInquiry.experience))
        .where(RbpcInquiry.id == payload.inquiry_id)
    )
    if not inquiry:
        raise AppError(
            "RBPC_INQUIRY_NOT_FOUND",
            f"Inquiry with ID '{payload.inquiry_id}' not found.",
            status.HTTP_404_NOT_FOUND,
        )

    # Invariant: Inquiry must be confirmed or closed
    if inquiry.state not in (RbpcInquiryStatus.confirmed.value, RbpcInquiryStatus.closed.value):
        raise AppError(
            "RBPC_INQUIRY_NOT_CONFIRMED",
            f"Cannot settle inquiry in '{inquiry.state}' state. Inquiry must be 'confirmed' or 'closed'.",
            status.HTTP_400_BAD_REQUEST,
            details={"current_status": inquiry.state},
        )

    # Scoping check
    is_admin = current_user.role in ADMIN_ROLES
    exp = inquiry.experience
    is_owner = (
        inquiry.provider_id == current_user.id
        or (exp is not None and exp.provider_id == current_user.id)
    )
    if not is_admin and not is_owner:
        raise AppError(
            "FORBIDDEN_SCOPE",
            "You do not have permission to record settlement for this inquiry.",
            status.HTTP_403_FORBIDDEN,
        )

    # Financial calculations
    gross = round(float(payload.gross_amount_vnd), 2)
    take_rate = float(payload.take_rate if payload.take_rate is not None else 0.1500)
    vat_rate = float(payload.vat_rate if payload.vat_rate is not None else 0.0800)

    platform_fee = round(gross * take_rate, 2)
    tax_vat = round(gross * vat_rate, 2)
    artisan_payout = round(max(0.0, gross - platform_fee - tax_vat), 2)

    creator_id = exp.creator_id if exp else None
    provider_id = inquiry.provider_id or (exp.provider_id if exp else current_user.id)
    settlement_ref = f"STL-{uuid_module.uuid4().hex[:6].upper()}-{datetime.now(timezone.utc).strftime('%y%m%d')}"

    revenue_stream = (
        payload.revenue_stream.value
        if hasattr(payload.revenue_stream, "value")
        else (payload.revenue_stream or RbpcRevenueStream.visitor_commerce.value)
    )

    settlement = RbpcSettlementLedger(
        settlement_ref=settlement_ref,
        inquiry_id=inquiry.id,
        provider_id=provider_id,
        creator_id=creator_id,
        gross_amount_vnd=gross,
        revenue_stream=revenue_stream,
        take_rate=take_rate,
        platform_fee_vnd=platform_fee,
        tax_vat_vnd=tax_vat,
        artisan_payout_vnd=artisan_payout,
        refund_amount_vnd=0.0,
        status=RbpcSettlementStatus.pending_compliance.value,
        payout_status=RbpcPayoutStatus.pending.value,
        compliance_approved=False,
        compliance_notes=payload.compliance_notes,
        transaction_proof_hash=payload.transaction_proof_hash,
        currency="VND",
    )
    db.add(settlement)
    db.flush()

    record_audit_entry(
        db,
        entity_type="rbpc_settlement_ledger",
        entity_id=settlement.id,
        action="settlement_created",
        actor_id=current_user.id,
        diff_payload={
            "settlement_ref": settlement_ref,
            "inquiry_id": str(inquiry.id),
            "gross_amount_vnd": gross,
            "revenue_stream": revenue_stream,
            "platform_fee_vnd": platform_fee,
            "tax_vat_vnd": tax_vat,
            "artisan_payout_vnd": artisan_payout,
            "status": settlement.status,
        },
    )

    db.commit()
    db.refresh(settlement)
    return settlement


@router.get(
    "/api/v1/rbpc/partner/settlements",
    response_model=RbpcSettlementListOut,
)
def list_settlements(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List settlements scoped to the authenticated partner/provider or all if admin/staff."""
    if current_user.role == UserRole.guest:
        raise AppError("FORBIDDEN", "Guest users cannot view settlements.", status.HTTP_403_FORBIDDEN)

    is_admin = current_user.role in ADMIN_ROLES
    stmt = select(RbpcSettlementLedger)
    if not is_admin:
        stmt = stmt.where(RbpcSettlementLedger.provider_id == current_user.id)

    stmt = stmt.order_by(RbpcSettlementLedger.created_at.desc())
    settlements = list(db.scalars(stmt))
    return RbpcSettlementListOut(items=settlements, total=len(settlements))


@router.get(
    "/api/v1/rbpc/partner/settlements/{id}",
    response_model=RbpcSettlementOut,
)
def get_settlement_detail(
    id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get single settlement detail with multi-tenant access control."""
    if current_user.role == UserRole.guest:
        raise AppError("FORBIDDEN", "Guest users cannot view settlements.", status.HTTP_403_FORBIDDEN)

    settlement = db.scalar(select(RbpcSettlementLedger).where(RbpcSettlementLedger.id == id))
    if not settlement:
        raise AppError("RBPC_SETTLEMENT_NOT_FOUND", f"Settlement '{id}' not found.", status.HTTP_404_NOT_FOUND)

    is_admin = current_user.role in ADMIN_ROLES
    if not is_admin and settlement.provider_id != current_user.id:
        raise AppError("FORBIDDEN_SCOPE", "You do not have access to this settlement.", status.HTTP_403_FORBIDDEN)

    return settlement


@router.post(
    "/api/v1/rbpc/editor/settlements/{id}/compliance",
    response_model=RbpcSettlementOut,
)
def review_settlement_compliance(
    id: UUID,
    payload: RbpcSettlementComplianceReview,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Review and approve or hold a settlement for compliance and artisan payout.

    Restricted to ADMIN_ROLES (admin, super_admin).
    When approved: status -> 'approved', payout_status -> 'approved'.
    When held/rejected: status -> 'pending_compliance', payout_status -> 'withheld'.
    """
    verify_csrf(request)
    if current_user.role not in ADMIN_ROLES:
        raise AppError(
            "FORBIDDEN_SCOPE",
            "Chỉ quản trị viên mới có quyền duyệt tuân thủ quyết toán.",
            status.HTTP_403_FORBIDDEN,
        )

    settlement = db.scalar(select(RbpcSettlementLedger).where(RbpcSettlementLedger.id == id))
    if not settlement:
        raise AppError("RBPC_SETTLEMENT_NOT_FOUND", f"Settlement '{id}' not found.", status.HTTP_404_NOT_FOUND)

    if settlement.status in (RbpcSettlementStatus.refunded.value, RbpcSettlementStatus.settled.value):
        if not payload.approved and settlement.status == RbpcSettlementStatus.settled.value:
            pass  # allow revoking/disputing
        else:
            raise AppError(
                "RBPC_SETTLEMENT_FINALIZED",
                f"Cannot alter compliance for settlement in '{settlement.status}' status.",
                status.HTTP_400_BAD_REQUEST,
            )

    settlement.compliance_approved = payload.approved
    settlement.compliance_reviewer_id = current_user.id
    settlement.compliance_reviewed_at = datetime.now(timezone.utc)
    if payload.compliance_notes:
        settlement.compliance_notes = payload.compliance_notes

    if payload.approved:
        settlement.status = RbpcSettlementStatus.approved.value
        settlement.payout_status = RbpcPayoutStatus.approved.value
    else:
        settlement.status = RbpcSettlementStatus.pending_compliance.value
        settlement.payout_status = RbpcPayoutStatus.withheld.value

    settlement.updated_at = datetime.now(timezone.utc)

    record_audit_entry(
        db,
        entity_type="rbpc_settlement_ledger",
        entity_id=settlement.id,
        action="compliance_review",
        actor_id=current_user.id,
        diff_payload={
            "approved": payload.approved,
            "status": settlement.status,
            "payout_status": settlement.payout_status,
            "notes": payload.compliance_notes,
        },
    )

    db.commit()
    db.refresh(settlement)
    return settlement


@router.post(
    "/api/v1/rbpc/editor/settlements/{id}/disburse",
    response_model=RbpcSettlementOut,
)
def disburse_artisan_payout(
    id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark artisan payout as disbursed once banking transfer is complete.

    Requires prior compliance approval. Cannot disburse unapproved settlements.
    Transitions status -> 'settled' and payout_status -> 'disbursed'.
    """
    verify_csrf(request)
    if current_user.role not in ADMIN_ROLES:
        raise AppError(
            "FORBIDDEN_SCOPE",
            "Chỉ quản trị viên mới có quyền giải ngân thanh toán.",
            status.HTTP_403_FORBIDDEN,
        )

    settlement = db.scalar(select(RbpcSettlementLedger).where(RbpcSettlementLedger.id == id))
    if not settlement:
        raise AppError("RBPC_SETTLEMENT_NOT_FOUND", f"Settlement '{id}' not found.", status.HTTP_404_NOT_FOUND)

    if not settlement.compliance_approved or settlement.payout_status != RbpcPayoutStatus.approved.value:
        raise AppError(
            "RBPC_PAYOUT_NOT_APPROVED",
            "Cannot disburse payout without prior compliance approval.",
            status.HTTP_400_BAD_REQUEST,
            details={"compliance_approved": settlement.compliance_approved, "payout_status": settlement.payout_status},
        )

    settlement.payout_status = RbpcPayoutStatus.disbursed.value
    settlement.status = RbpcSettlementStatus.settled.value
    settlement.disbursed_at = datetime.now(timezone.utc)
    settlement.updated_at = datetime.now(timezone.utc)

    record_audit_entry(
        db,
        entity_type="rbpc_settlement_ledger",
        entity_id=settlement.id,
        action="payout_disbursed",
        actor_id=current_user.id,
        diff_payload={
            "disbursed_at": settlement.disbursed_at.isoformat(),
            "status": settlement.status,
            "payout_status": settlement.payout_status,
        },
    )

    db.commit()
    db.refresh(settlement)
    return settlement


@router.post(
    "/api/v1/rbpc/partner/settlements/{id}/refund",
    response_model=RbpcSettlementOut,
)
def process_settlement_refund(
    id: UUID,
    payload: RbpcSettlementRefund,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Process a full or partial refund against a settlement.

    Re-computes platform fee and artisan payout deductions accordingly.
    Marks status -> 'refunded' if fully refunded.
    """
    verify_csrf(request)
    if current_user.role == UserRole.guest:
        raise AppError("FORBIDDEN", "Guest users cannot refund settlements.", status.HTTP_403_FORBIDDEN)

    settlement = db.scalar(select(RbpcSettlementLedger).where(RbpcSettlementLedger.id == id))
    if not settlement:
        raise AppError("RBPC_SETTLEMENT_NOT_FOUND", f"Settlement '{id}' not found.", status.HTTP_404_NOT_FOUND)

    is_admin = current_user.role in STAFF_ROLES
    if not is_admin and settlement.provider_id != current_user.id:
        raise AppError("FORBIDDEN_SCOPE", "You do not have permission to refund this settlement.", status.HTTP_403_FORBIDDEN)

    refund_amt = round(float(payload.refund_amount_vnd), 2)
    max_refundable = round(float(settlement.gross_amount_vnd) - float(settlement.refund_amount_vnd), 2)

    if refund_amt > max_refundable:
        raise AppError(
            "RBPC_REFUND_EXCEEDS_GROSS",
            f"Refund amount ({refund_amt:,.0f} VND) exceeds refundable balance ({max_refundable:,.0f} VND).",
            status.HTTP_400_BAD_REQUEST,
            details={"requested": refund_amt, "max_refundable": max_refundable},
        )

    settlement.refund_amount_vnd = round(float(settlement.refund_amount_vnd) + refund_amt, 2)
    net_effective_gross = max(0.0, float(settlement.gross_amount_vnd) - float(settlement.refund_amount_vnd))
    
    # Recalculate fees on remaining effective gross
    take_rate = float(settlement.take_rate)
    settlement.platform_fee_vnd = round(net_effective_gross * take_rate, 2)
    settlement.artisan_payout_vnd = round(max(0.0, net_effective_gross - float(settlement.platform_fee_vnd) - float(settlement.tax_vat_vnd)), 2)

    if net_effective_gross <= 0.0:
        settlement.status = RbpcSettlementStatus.refunded.value
        settlement.payout_status = RbpcPayoutStatus.cancelled.value

    settlement.updated_at = datetime.now(timezone.utc)

    record_audit_entry(
        db,
        entity_type="rbpc_settlement_ledger",
        entity_id=settlement.id,
        action="settlement_refunded",
        actor_id=current_user.id,
        diff_payload={
            "refund_amount_vnd": refund_amt,
            "total_refunded_vnd": float(settlement.refund_amount_vnd),
            "remaining_gross_vnd": net_effective_gross,
            "reason": payload.reason,
            "status": settlement.status,
        },
    )

    db.commit()
    db.refresh(settlement)
    return settlement


@router.get(
    "/api/v1/rbpc/ledger/summary",
    response_model=RbpcLedgerFinancialSummary,
)
def get_ledger_financial_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Aggregate financial summary from the verified settlement ledger.

    Negative abuse invariant (V5-T108):
    Inquiries in 'confirmed' status alone contribute 0 VND. Only explicit
    records in `rbpc_settlement_ledger` contribute to actual revenue.
    """
    if current_user.role == UserRole.guest:
        raise AppError("FORBIDDEN", "Guest users cannot view financial summaries.", status.HTTP_403_FORBIDDEN)

    is_admin = current_user.role in STAFF_ROLES
    stmt = select(RbpcSettlementLedger)
    if not is_admin:
        stmt = stmt.where(RbpcSettlementLedger.provider_id == current_user.id)

    settlements = list(db.scalars(stmt))

    total_gross = sum(float(s.gross_amount_vnd) for s in settlements if s.status in ("approved", "settled"))
    total_fee = sum(float(s.platform_fee_vnd) for s in settlements if s.status in ("approved", "settled"))
    total_tax = sum(float(s.tax_vat_vnd) for s in settlements if s.status in ("approved", "settled"))
    total_payout = sum(float(s.artisan_payout_vnd) for s in settlements if s.status in ("approved", "settled"))
    total_refund = sum(float(s.refund_amount_vnd) for s in settlements)

    approved_count = sum(1 for s in settlements if s.compliance_approved)
    pending_count = sum(1 for s in settlements if not s.compliance_approved)

    avg_take_rate = (
        sum(float(s.take_rate) for s in settlements) / len(settlements)
        if settlements
        else 0.1500
    )

    return RbpcLedgerFinancialSummary(
        total_gross_settled_vnd=round(total_gross, 2),
        total_platform_fee_vnd=round(total_fee, 2),
        total_tax_vat_vnd=round(total_tax, 2),
        total_artisan_payout_vnd=round(total_payout, 2),
        total_refund_vnd=round(total_refund, 2),
        approved_settlements_count=approved_count,
        pending_settlements_count=pending_count,
        contracted_take_rate_avg=round(avg_take_rate, 4),
    )


@router.get(
    "/api/v1/rbpc/ledger/unit-economics",
    response_model=RbpcUnitEconomicsActualLedger,
)
def get_unit_economics_actual_ledger(
    stream: Optional[str] = Query(None, description="Optional stream filter: 'visitor_commerce' or 'school_b2b'"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Aggregate verified unit economics actual ledger report.

    Features:
    - Cash actuals strictly separated from GMV forecasts (forecasts tagged truth_tier='FORECAST').
    - Cost structure inference: server hosting (BNIX in-kind subsidy vs commercial replacement),
      AI token inference (Phổ Tuệ in-kind credits vs commercial replacement), take rates, and dual margins.
    - Explicit separation of revenue streams: 'visitor_commerce' vs 'school_b2b'.
    - Negative abuse invariant: Partner inquiries in any status create strictly 0 VND revenue
      and 0 VND realized GMV without a verified payment settlement in rbpc_settlement_ledger.
    - Multi-tenant isolation: Admin/staff receive global actuals; partners receive provider-scoped actuals.
    """
    if current_user.role == UserRole.guest:
        raise AppError("FORBIDDEN", "Guest users cannot view financial summaries.", status.HTTP_403_FORBIDDEN)

    is_admin = current_user.role in ADMIN_ROLES
    provider_id = None if is_admin else current_user.id

    ledger = compute_unit_economics_ledger(
        db=db,
        provider_id=provider_id,
        stream_filter=stream,
    )
    return ledger


# --------------------------------------------------------------------------- #
# Verified Customer Reviews & Disputes Endpoints (V5-T107)
# --------------------------------------------------------------------------- #

def _detect_review_fraud(title: str, comment: str, rating: int) -> dict[str, Any]:
    """Run automated anti-fraud heuristics on submitted review text."""
    flags: dict[str, Any] = {}
    content = f"{title} {comment}"

    # Check for external URLs or promotional backlinks
    if SPAM_URL_PATTERN.search(content):
        flags["contains_url"] = True

    # Check for script injection or unsafe markup
    if SCRIPT_PATTERN.search(content):
        flags["contains_script"] = True

    # Check for commercial spam keywords
    lower_content = content.lower()
    matched_spam = [kw for kw in SPAM_KEYWORDS if kw in lower_content]
    if matched_spam:
        flags["spam_keywords"] = matched_spam

    # Check for excessive character repetition (e.g. "aaaaaaa", "!!!!!")
    if re.search(r"(.)\1{6,}", content):
        flags["character_repetition"] = True

    # Check for all uppercase yelling
    letters = [c for c in content if c.isalpha()]
    if len(letters) > 20 and sum(1 for c in letters if c.isupper()) / len(letters) > 0.8:
        flags["excessive_caps"] = True

    flags["flagged"] = bool(flags)
    return flags


@router.post(
    "/api/v1/rbpc/reviews",
    response_model=RbpcCustomerReviewOut,
    status_code=status.HTTP_201_CREATED,
)
def create_customer_review(
    payload: RbpcCustomerReviewCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Submit a verified customer review for a completed inquiry.

    Negative abuse invariant (V5-T107):
    Only customers with verified completed experience inquiries (state == 'closed'
    and completion verified) can submit reviews. Uncompleted, fake, or cancelled
    inquiries cannot post ratings or reviews.
    """
    token_clean = payload.inquiry_token.strip()
    inquiry = db.scalar(
        select(RbpcInquiry)
        .options(selectinload(RbpcInquiry.experience))
        .where(
            or_(
                RbpcInquiry.opaque_token == token_clean,
                RbpcInquiry.public_ref == token_clean,
            )
        )
    )

    if not inquiry:
        raise AppError(
            "RBPC_INQUIRY_NOT_FOUND",
            "Không tìm thấy hồ sơ yêu cầu trải nghiệm tương ứng với mã cung cấp.",
            status.HTTP_404_NOT_FOUND,
        )

    # Invariant: Must be completed ('closed' state)
    if inquiry.state != "closed":
        raise AppError(
            "RBPC_INQUIRY_NOT_COMPLETED",
            f"Chỉ những trải nghiệm đã hoàn tất (trạng thái 'closed') mới có thể đánh giá. Trạng thái hiện tại: '{inquiry.state}'.",
            status.HTTP_400_BAD_REQUEST,
            details={
                "inquiry_ref": inquiry.public_ref,
                "current_state": inquiry.state,
                "required_state": "closed",
            },
        )

    # Invariant: One review per completed inquiry
    existing_review = db.scalar(
        select(RbpcCustomerReview).where(RbpcCustomerReview.inquiry_id == inquiry.id)
    )
    if existing_review:
        raise AppError(
            "RBPC_REVIEW_ALREADY_EXISTS",
            "Hồ sơ trải nghiệm này đã được gửi đánh giá trước đó.",
            status.HTTP_409_CONFLICT,
            details={"review_id": str(existing_review.id)},
        )

    # Anti-fraud heuristic check
    fraud_flags = _detect_review_fraud(payload.title, payload.comment, payload.rating)

    # Resolve author display name safely (Zero unconsented PII leak)
    if payload.author_display_name and payload.author_display_name.strip():
        display_name = payload.author_display_name.strip()[:100]
    elif current_user and current_user.display_name:
        display_name = current_user.display_name[:100]
    else:
        # Default to masked name from inquiry contact (e.g. "Nguyễn ***")
        raw_name = inquiry.name.strip()
        parts = raw_name.split()
        if len(parts) > 1:
            display_name = f"{parts[0]} {'*' * min(len(parts[-1]), 4)}"
        else:
            display_name = f"{raw_name[:2]}***" if len(raw_name) >= 2 else "Khách trải nghiệm"

    # Set initial review status: if fraud flags found, goes to pending_moderation; otherwise published or pending_moderation
    # By default, high quality reviews without fraud flags can be published immediately or held for moderation
    initial_status = (
        RbpcReviewStatus.pending_moderation.value
        if fraud_flags.get("flagged")
        else RbpcReviewStatus.published.value
    )

    review = RbpcCustomerReview(
        inquiry_id=inquiry.id,
        experience_id=inquiry.experience_id,
        author_user_id=current_user.id if current_user else None,
        author_display_name=display_name,
        rating=payload.rating,
        title=payload.title.strip(),
        comment=payload.comment.strip(),
        verified_completed=True,
        status=initial_status,
        fraud_flags=fraud_flags,
    )

    db.add(review)
    db.commit()
    db.refresh(review)

    return RbpcCustomerReviewOut(
        id=review.id,
        experience_id=review.experience_id,
        experience_slug=inquiry.experience.slug if inquiry.experience else None,
        author_display_name=review.author_display_name,
        rating=review.rating,
        title=review.title,
        comment=review.comment,
        verified_completed=review.verified_completed,
        status=RbpcReviewStatus(review.status),
        created_at=review.created_at,
        updated_at=review.updated_at,
    )


@router.get(
    "/api/v1/rbpc/experiences/{slug}/reviews",
    response_model=RbpcCustomerReviewListOut,
)
def list_experience_reviews(
    slug: str,
    db: Session = Depends(get_db),
):
    """Public endpoint to fetch verified published reviews for an experience."""
    clean_slug = _validate_slug(slug)
    exp = db.scalar(select(RbpcExperience).where(RbpcExperience.slug == clean_slug))
    if not exp:
        raise AppError(
            "RBPC_EXPERIENCE_NOT_FOUND",
            f"Experience '{clean_slug}' not found.",
            status.HTTP_404_NOT_FOUND,
        )

    reviews = list(
        db.scalars(
            select(RbpcCustomerReview)
            .where(
                RbpcCustomerReview.experience_id == exp.id,
                RbpcCustomerReview.status == RbpcReviewStatus.published.value,
            )
            .order_by(RbpcCustomerReview.created_at.desc())
        )
    )

    total = len(reviews)
    avg_rating = round(sum(r.rating for r in reviews) / total, 1) if total > 0 else 0.0

    items = [
        RbpcCustomerReviewOut(
            id=r.id,
            experience_id=r.experience_id,
            experience_slug=exp.slug,
            author_display_name=r.author_display_name,
            rating=r.rating,
            title=r.title,
            comment=r.comment,
            verified_completed=r.verified_completed,
            status=RbpcReviewStatus(r.status),
            created_at=r.created_at,
            updated_at=r.updated_at,
        )
        for r in reviews
    ]

    return RbpcCustomerReviewListOut(
        items=items,
        total=total,
        average_rating=avg_rating,
    )


@router.get(
    "/api/v1/rbpc/admin/reviews",
    response_model=RbpcCustomerReviewAdminListOut,
)
def admin_list_reviews(
    review_status: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Staff/admin moderation queue for customer reviews and fraud inspection."""
    if current_user.role not in STAFF_ROLES:
        raise AppError(
            "FORBIDDEN_SCOPE",
            "Chỉ nhân viên hoặc quản trị viên mới có quyền xem danh sách kiểm duyệt đánh giá.",
            status.HTTP_403_FORBIDDEN,
        )

    stmt = select(RbpcCustomerReview).options(
        selectinload(RbpcCustomerReview.disputes)
    ).order_by(RbpcCustomerReview.created_at.desc())

    if review_status:
        stmt = stmt.where(RbpcCustomerReview.status == review_status)

    all_reviews = list(db.scalars(stmt))
    pending_count = sum(1 for r in all_reviews if r.status == RbpcReviewStatus.pending_moderation.value)

    items = [
        RbpcCustomerReviewAdminOut(
            id=r.id,
            inquiry_id=r.inquiry_id,
            experience_id=r.experience_id,
            author_user_id=r.author_user_id,
            author_display_name=r.author_display_name,
            rating=r.rating,
            title=r.title,
            comment=r.comment,
            verified_completed=r.verified_completed,
            status=RbpcReviewStatus(r.status),
            fraud_flags=r.fraud_flags or {},
            moderated_by_id=r.moderated_by_id,
            moderated_at=r.moderated_at,
            moderation_notes=r.moderation_notes,
            disputes=[
                RbpcReviewDisputeOut(
                    id=d.id,
                    review_id=d.review_id,
                    disputant_user_id=d.disputant_user_id,
                    reason=d.reason,
                    evidence_payload=d.evidence_payload or {},
                    status=RbpcDisputeStatus(d.status),
                    resolved_by_id=d.resolved_by_id,
                    resolution_notes=d.resolution_notes,
                    resolved_at=d.resolved_at,
                    created_at=d.created_at,
                    updated_at=d.updated_at,
                )
                for d in (r.disputes or [])
            ],
            created_at=r.created_at,
            updated_at=r.updated_at,
        )
        for r in all_reviews
    ]

    return RbpcCustomerReviewAdminListOut(
        items=items,
        total=len(items),
        pending_count=pending_count,
    )


@router.patch(
    "/api/v1/rbpc/admin/reviews/{id}/moderate",
    response_model=RbpcCustomerReviewAdminOut,
)
def moderate_customer_review(
    id: UUID,
    payload: RbpcCustomerReviewModeration,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Moderate a review: approve/publish, reject, or archive."""
    if current_user.role not in STAFF_ROLES:
        raise AppError(
            "FORBIDDEN_SCOPE",
            "Chỉ nhân viên hoặc quản trị viên mới có quyền kiểm duyệt đánh giá.",
            status.HTTP_403_FORBIDDEN,
        )

    review = db.scalar(
        select(RbpcCustomerReview)
        .options(selectinload(RbpcCustomerReview.disputes))
        .where(RbpcCustomerReview.id == id)
    )
    if not review:
        raise AppError(
            "RBPC_REVIEW_NOT_FOUND",
            f"Review '{id}' not found.",
            status.HTTP_404_NOT_FOUND,
        )

    review.status = payload.status.value
    review.moderated_by_id = current_user.id
    review.moderated_at = datetime.now(timezone.utc)
    if payload.notes:
        review.moderation_notes = payload.notes

    db.commit()
    db.refresh(review)

    return RbpcCustomerReviewAdminOut(
        id=review.id,
        inquiry_id=review.inquiry_id,
        experience_id=review.experience_id,
        author_user_id=review.author_user_id,
        author_display_name=review.author_display_name,
        rating=review.rating,
        title=review.title,
        comment=review.comment,
        verified_completed=review.verified_completed,
        status=RbpcReviewStatus(review.status),
        fraud_flags=review.fraud_flags or {},
        moderated_by_id=review.moderated_by_id,
        moderated_at=review.moderated_at,
        moderation_notes=review.moderation_notes,
        disputes=[
            RbpcReviewDisputeOut(
                id=d.id,
                review_id=d.review_id,
                disputant_user_id=d.disputant_user_id,
                reason=d.reason,
                evidence_payload=d.evidence_payload or {},
                status=RbpcDisputeStatus(d.status),
                resolved_by_id=d.resolved_by_id,
                resolution_notes=d.resolution_notes,
                resolved_at=d.resolved_at,
                created_at=d.created_at,
                updated_at=d.updated_at,
            )
            for d in (review.disputes or [])
        ],
        created_at=review.created_at,
        updated_at=review.updated_at,
    )


@router.post(
    "/api/v1/rbpc/reviews/{id}/dispute",
    response_model=RbpcReviewDisputeOut,
    status_code=status.HTTP_201_CREATED,
)
def file_review_dispute(
    id: UUID,
    payload: RbpcReviewDisputeCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """File a dispute against a review."""
    review = db.scalar(select(RbpcCustomerReview).where(RbpcCustomerReview.id == id))
    if not review:
        raise AppError(
            "RBPC_REVIEW_NOT_FOUND",
            f"Review '{id}' not found.",
            status.HTTP_404_NOT_FOUND,
        )

    dispute = RbpcReviewDispute(
        review_id=review.id,
        disputant_user_id=current_user.id if current_user else None,
        reason=payload.reason.strip(),
        evidence_payload=payload.evidence_payload,
        status=RbpcDisputeStatus.opened.value,
    )

    # Flag the review as disputed in its lifecycle
    review.status = RbpcReviewStatus.disputed.value

    db.add(dispute)
    db.commit()
    db.refresh(dispute)

    return RbpcReviewDisputeOut(
        id=dispute.id,
        review_id=dispute.review_id,
        disputant_user_id=dispute.disputant_user_id,
        reason=dispute.reason,
        evidence_payload=dispute.evidence_payload or {},
        status=RbpcDisputeStatus(dispute.status),
        resolved_by_id=dispute.resolved_by_id,
        resolution_notes=dispute.resolution_notes,
        resolved_at=dispute.resolved_at,
        created_at=dispute.created_at,
        updated_at=dispute.updated_at,
    )


@router.patch(
    "/api/v1/rbpc/admin/disputes/{id}/resolve",
    response_model=RbpcReviewDisputeOut,
)
def resolve_review_dispute(
    id: UUID,
    payload: RbpcReviewDisputeResolution,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Staff/admin resolves a review dispute."""
    if current_user.role not in STAFF_ROLES:
        raise AppError(
            "FORBIDDEN_SCOPE",
            "Chỉ nhân viên hoặc quản trị viên mới có quyền giải quyết tranh chấp đánh giá.",
            status.HTTP_403_FORBIDDEN,
        )

    dispute = db.scalar(
        select(RbpcReviewDispute)
        .options(selectinload(RbpcReviewDispute.review))
        .where(RbpcReviewDispute.id == id)
    )
    if not dispute:
        raise AppError(
            "RBPC_DISPUTE_NOT_FOUND",
            f"Dispute '{id}' not found.",
            status.HTTP_404_NOT_FOUND,
        )

    dispute.status = payload.status.value
    dispute.resolved_by_id = current_user.id
    dispute.resolved_at = datetime.now(timezone.utc)
    if payload.notes:
        dispute.resolution_notes = payload.notes

    # Update associated review based on resolution
    if dispute.review:
        if payload.status == RbpcDisputeStatus.resolved_upheld:
            # Dispute upheld: review is rejected or archived
            dispute.review.status = RbpcReviewStatus.rejected.value
        elif payload.status in (RbpcDisputeStatus.resolved_overturned, RbpcDisputeStatus.dismissed):
            # Dispute overturned or dismissed: review reinstated to published
            dispute.review.status = RbpcReviewStatus.published.value

    db.commit()
    db.refresh(dispute)

    return RbpcReviewDisputeOut(
        id=dispute.id,
        review_id=dispute.review_id,
        disputant_user_id=dispute.disputant_user_id,
        reason=dispute.reason,
        evidence_payload=dispute.evidence_payload or {},
        status=RbpcDisputeStatus(dispute.status),
        resolved_by_id=dispute.resolved_by_id,
        resolution_notes=dispute.resolution_notes,
        resolved_at=dispute.resolved_at,
        created_at=dispute.created_at,
        updated_at=dispute.updated_at,
    )


# --------------------------------------------------------------------------- #
# Workshop Availability Inventory & Calendar Endpoints (V5-T102)
# --------------------------------------------------------------------------- #
def _expire_stale_reservations_for_slot(db: Session, slot: RbpcWorkshopSlot, now: datetime) -> int:
    """Find all pending reservations for this slot past expires_at, mark expired, and release seats."""
    stale_reservations = list(
        db.scalars(
            select(RbpcSeatReservation).where(
                RbpcSeatReservation.slot_id == slot.id,
                RbpcSeatReservation.status == RbpcReservationStatus.pending.value,
                RbpcSeatReservation.expires_at <= now,
            )
        )
    )
    freed_seats = 0
    for r in stale_reservations:
        r.status = RbpcReservationStatus.expired.value
        r.updated_at = now
        freed_seats += r.seats
    if freed_seats > 0:
        slot.reserved_seats = max(0, slot.reserved_seats - freed_seats)
        slot.updated_at = now
        db.flush()
    return freed_seats


def _slot_to_out(slot: RbpcWorkshopSlot) -> RbpcWorkshopSlotOut:
    avail = slot.available_seats
    status_disp = slot.status
    if slot.status == "open" and avail <= 0:
        status_disp = "sold_out"
    return RbpcWorkshopSlotOut(
        id=slot.id,
        experience_id=slot.experience_id,
        start_time=slot.start_time,
        end_time=slot.end_time,
        capacity=slot.capacity,
        reserved_seats=slot.reserved_seats,
        confirmed_seats=slot.confirmed_seats,
        available_seats=avail,
        status=status_disp,
        notes=slot.notes,
        created_at=slot.created_at,
        updated_at=slot.updated_at,
    )


def _reservation_to_out(res: RbpcSeatReservation, msg: str = "Thao tác thành công.") -> RbpcSeatReservationOut:
    now = datetime.now(timezone.utc)
    remaining_secs = max(0, int((res.expires_at - now).total_seconds())) if res.status == "pending" else 0
    exp_slug = None
    if res.slot and res.slot.experience:
        exp_slug = res.slot.experience.slug
    return RbpcSeatReservationOut(
        id=res.id,
        public_ref=res.public_ref,
        slot_id=res.slot_id,
        experience_slug=exp_slug,
        seats=res.seats,
        status=res.status,
        expires_at=res.expires_at,
        remaining_seconds=remaining_secs,
        customer_name=res.customer_name,
        customer_contact=res.customer_contact,
        confirmed_at=res.confirmed_at,
        message=msg,
        created_at=res.created_at,
    )


@router.get(
    "/api/v1/rbpc/experiences/{slug}/availability",
    response_model=RbpcAvailabilityCalendarOut,
)
def get_experience_availability(
    slug: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
):
    """Retrieve workshop slots and real seat availability calendar for an experience.

    Cleans up expired pending reservations, releasing seats back to available capacity.
    """
    valid_slug = _validate_slug(slug)
    exp = db.scalar(
        select(RbpcExperience).where(
            RbpcExperience.slug == valid_slug,
            RbpcExperience.publication_state == "published",
        )
    )
    if not exp:
        raise AppError("RBPC_EXPERIENCE_NOT_FOUND", f"Experience '{slug}' not found.", status.HTTP_404_NOT_FOUND)

    now = datetime.now(timezone.utc)
    stmt = select(RbpcWorkshopSlot).where(RbpcWorkshopSlot.experience_id == exp.id)

    if start_date:
        start_dt = datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc)
        stmt = stmt.where(RbpcWorkshopSlot.start_time >= start_dt)
    if end_date:
        end_dt = datetime.combine(end_date, datetime.max.time(), tzinfo=timezone.utc)
        stmt = stmt.where(RbpcWorkshopSlot.end_time <= end_dt)

    stmt = stmt.order_by(RbpcWorkshopSlot.start_time.asc())
    slots = list(db.scalars(stmt))

    for s in slots:
        _expire_stale_reservations_for_slot(db, s, now)
    db.commit()

    return RbpcAvailabilityCalendarOut(
        experience_slug=exp.slug,
        experience_title=exp.title_vi,
        slots=[_slot_to_out(s) for s in slots],
        total_slots=len(slots),
    )


@router.post(
    "/api/v1/rbpc/availability/reserve",
    status_code=status.HTTP_201_CREATED,
    response_model=RbpcSeatReservationOut,
)
def reserve_workshop_seats(
    payload: RbpcSeatReserveIn,
    request: Request,
    db: Session = Depends(get_db),
):
    """Temporarily hold seat capacity in a workshop slot with a reserve timeout.

    Enforces concurrency race condition safety via row-level pessimistic locking
    (with_for_update) and check constraint (reserved_seats + confirmed_seats <= capacity).
    Two concurrent requests cannot book the last remaining seat twice.
    """
    from ..services.feature_flags import assert_kill_switch_active

    assert_kill_switch_active(
        "FEATURE_FLAG_RBPC_COMMERCE_ENABLED",
        feature_name="Đặt chỗ & Giữ chỗ Trải nghiệm",
        friendly_message="Hệ thống giữ chỗ đang tạm ngưng bảo trì. Vui lòng quay lại sau.",
        db=db,
    )

    # Input sanitization
    sanitized_name = _sanitize_text(payload.customer_name) or ""
    if len(sanitized_name) < 2:
        raise AppError(
            "RBPC_INVALID_INPUT",
            "Tên khách hàng không hợp lệ hoặc quá ngắn.",
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        )
    sanitized_contact = payload.customer_contact.strip()
    if len(sanitized_contact) < 5:
        raise AppError(
            "RBPC_INVALID_INPUT",
            "Thông tin liên hệ không hợp lệ.",
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    # Idempotency check if key provided
    validated_key = None
    if payload.idempotency_key:
        validated_key = _validate_client_uuid(payload.idempotency_key)
        existing = db.scalar(
            select(RbpcSeatReservation)
            .options(selectinload(RbpcSeatReservation.slot).selectinload(RbpcWorkshopSlot.experience))
            .where(RbpcSeatReservation.idempotency_key == validated_key)
        )
        if existing:
            if (
                existing.slot_id != payload.slot_id
                or existing.seats != payload.seats
                or existing.customer_name != sanitized_name
                or existing.customer_contact != sanitized_contact
            ):
                raise AppError(
                    "RBPC_IDEMPOTENCY_CONFLICT",
                    "Idempotency key has already been used with differing parameters.",
                    status.HTTP_409_CONFLICT,
                )
            return _reservation_to_out(existing, "Giữ chỗ đã được tạo trước đó.")

    # Acquire pessimistic row-level lock on the workshop slot
    slot = db.scalar(
        select(RbpcWorkshopSlot)
        .options(selectinload(RbpcWorkshopSlot.experience))
        .where(RbpcWorkshopSlot.id == payload.slot_id)
        .with_for_update()
    )
    if not slot:
        raise AppError("RBPC_SLOT_NOT_FOUND", "Khung giờ trải nghiệm không tồn tại.", status.HTTP_404_NOT_FOUND)

    if slot.status != RbpcSlotStatus.open.value:
        raise AppError(
            "RBPC_SLOT_NOT_OPEN",
            f"Khung giờ này không tiếp nhận đặt chỗ (trạng thái: {slot.status}).",
            status.HTTP_400_BAD_REQUEST,
        )

    now = datetime.now(timezone.utc)
    _expire_stale_reservations_for_slot(db, slot, now)

    available = slot.capacity - slot.confirmed_seats - slot.reserved_seats
    if payload.seats > available:
        raise AppError(
            "INSUFFICIENT_SEAT_CAPACITY",
            f"Không đủ chỗ trống. Chỉ còn {max(0, available)} chỗ khả dụng cho khung giờ này.",
            status.HTTP_409_CONFLICT,
            details={"available_seats": max(0, available), "requested_seats": payload.seats},
        )

    hex_ref = uuid_module.uuid4().hex[:8].upper()
    public_ref = f"RES-{hex_ref[:4]}-{hex_ref[4:]}"
    hold_timeout = payload.hold_timeout_seconds or 900
    expires_at = now + timedelta(seconds=hold_timeout)

    reservation = RbpcSeatReservation(
        slot_id=slot.id,
        inquiry_id=payload.inquiry_id,
        public_ref=public_ref,
        seats=payload.seats,
        status=RbpcReservationStatus.pending.value,
        hold_timeout_seconds=hold_timeout,
        expires_at=expires_at,
        customer_name=sanitized_name,
        customer_contact=sanitized_contact,
        idempotency_key=validated_key,
    )

    slot.reserved_seats += payload.seats
    slot.updated_at = now
    db.add(reservation)

    try:
        db.flush()
        record_audit_entry(
            db,
            entity_type="slot_reservation",
            entity_id=reservation.id,
            action="seat_reserved",
            actor_id=None,
            diff_payload={
                "public_ref": reservation.public_ref,
                "slot_id": str(reservation.slot_id),
                "seats": reservation.seats,
                "expires_at": reservation.expires_at.isoformat(),
            },
        )
        db.commit()
        db.refresh(reservation)
    except IntegrityError:
        db.rollback()
        if validated_key:
            existing_raced = db.scalar(
                select(RbpcSeatReservation)
                .options(selectinload(RbpcSeatReservation.slot).selectinload(RbpcWorkshopSlot.experience))
                .where(RbpcSeatReservation.idempotency_key == validated_key)
            )
            if existing_raced:
                return _reservation_to_out(existing_raced, "Giữ chỗ đã được tạo trước đó.")
        raise AppError(
            "INSUFFICIENT_SEAT_CAPACITY",
            "Không thể hoàn tất giữ chỗ do xung đột số lượng chỗ.",
            status.HTTP_409_CONFLICT,
        )

    return _reservation_to_out(
        reservation,
        "Giữ chỗ thành công. Vui lòng xác nhận trước khi hết thời gian giữ chỗ.",
    )


@router.get(
    "/api/v1/rbpc/availability/reservations/{ref}",
    response_model=RbpcSeatReservationOut,
)
def get_reservation_status(
    ref: str,
    db: Session = Depends(get_db),
):
    """Visitor lookup of reservation status and remaining hold timeout.

    If pending reservation has expired past expires_at, status transitions to expired
    and seats are released back to the slot inventory.
    """
    conditions = [RbpcSeatReservation.public_ref == ref.strip()]
    try:
        parsed_uuid = UUID(ref.strip())
        conditions.append(RbpcSeatReservation.id == parsed_uuid)
    except (ValueError, TypeError):
        pass
    stmt = (
        select(RbpcSeatReservation)
        .options(selectinload(RbpcSeatReservation.slot).selectinload(RbpcWorkshopSlot.experience))
        .where(or_(*conditions))
    )
    reservation = db.scalar(stmt)
    if not reservation:
        raise AppError(
            "RBPC_RESERVATION_NOT_FOUND",
            f"Reservation '{ref}' not found.",
            status.HTTP_404_NOT_FOUND,
        )

    now = datetime.now(timezone.utc)
    if reservation.status == RbpcReservationStatus.pending.value and reservation.expires_at <= now:
        slot = db.scalar(
            select(RbpcWorkshopSlot)
            .where(RbpcWorkshopSlot.id == reservation.slot_id)
            .with_for_update()
        )
        if slot:
            slot.reserved_seats = max(0, slot.reserved_seats - reservation.seats)
            slot.updated_at = now
        reservation.status = RbpcReservationStatus.expired.value
        reservation.updated_at = now
        db.commit()
        db.refresh(reservation)

    return _reservation_to_out(reservation)


@router.post(
    "/api/v1/rbpc/partner/availability/confirm",
    response_model=RbpcSeatReservationOut,
)
def confirm_workshop_reservation(
    payload: RbpcReservationConfirmIn,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Partner confirmation of a reserved workshop seat hold.

    Pessimistic row locking ensures two concurrent requests cannot confirm the last remaining seat twice.
    Rejects expired holds and releases seats. Moves reserved_seats to confirmed_seats upon confirmation.
    """
    verify_csrf(request)

    if current_user.role == UserRole.guest:
        raise AppError("FORBIDDEN", "Guest users cannot manage availability.", status.HTTP_403_FORBIDDEN)

    reservation = db.scalar(
        select(RbpcSeatReservation)
        .options(selectinload(RbpcSeatReservation.slot).selectinload(RbpcWorkshopSlot.experience))
        .where(RbpcSeatReservation.id == payload.reservation_id)
        .with_for_update()
    )
    if not reservation:
        raise AppError(
            "RBPC_RESERVATION_NOT_FOUND",
            f"Reservation '{payload.reservation_id}' not found.",
            status.HTTP_404_NOT_FOUND,
        )

    slot = db.scalar(
        select(RbpcWorkshopSlot)
        .options(selectinload(RbpcWorkshopSlot.experience))
        .where(RbpcWorkshopSlot.id == reservation.slot_id)
        .with_for_update()
    )
    if not slot:
        raise AppError("RBPC_SLOT_NOT_FOUND", "Workshop slot not found.", status.HTTP_404_NOT_FOUND)

    # Multi-tenant access control
    is_admin = current_user.role in ADMIN_ROLES
    if not is_admin:
        exp = slot.experience
        is_owner = (
            exp is not None
            and (exp.provider_id == current_user.id or exp.creator_id == current_user.id)
        )
        if not is_owner:
            raise AppError(
                "FORBIDDEN_SCOPE",
                "You do not have permission to confirm reservations for this experience.",
                status.HTTP_403_FORBIDDEN,
            )

    # Idempotent replay if already confirmed
    if reservation.status == RbpcReservationStatus.confirmed.value:
        return _reservation_to_out(reservation, "Đặt chỗ đã được xác nhận trước đó.")

    now = datetime.now(timezone.utc)
    if reservation.status != RbpcReservationStatus.pending.value:
        raise AppError(
            "INVALID_RESERVATION_STATUS",
            f"Không thể xác nhận đặt chỗ ở trạng thái '{reservation.status}'.",
            status.HTTP_400_BAD_REQUEST,
        )

    # Check expiration timeout
    if reservation.expires_at <= now:
        reservation.status = RbpcReservationStatus.expired.value
        slot.reserved_seats = max(0, slot.reserved_seats - reservation.seats)
        slot.updated_at = now
        db.commit()
        raise AppError(
            "RESERVATION_EXPIRED",
            "Thời gian giữ chỗ đã hết hạn. Vui lòng tạo đặt chỗ mới.",
            status.HTTP_409_CONFLICT,
        )

    # Capacity validation: confirmed_seats + seats <= capacity
    if slot.confirmed_seats + reservation.seats > slot.capacity:
        raise AppError(
            "CAPACITY_EXCEEDED",
            "Vượt quá sức chứa tối đa của khung giờ này.",
            status.HTTP_409_CONFLICT,
        )

    # Transition seat from reserved to confirmed
    slot.reserved_seats = max(0, slot.reserved_seats - reservation.seats)
    slot.confirmed_seats += reservation.seats
    slot.updated_at = now

    reservation.status = RbpcReservationStatus.confirmed.value
    reservation.confirmed_at = now
    reservation.confirmed_by = current_user.id
    reservation.updated_at = now

    # Also synchronize linked inquiry if present
    if reservation.inquiry_id:
        inquiry = db.scalar(select(RbpcInquiry).where(RbpcInquiry.id == reservation.inquiry_id))
        if inquiry and inquiry.state in (RbpcInquiryStatus.new.value, RbpcInquiryStatus.contacted.value):
            inquiry.state = RbpcInquiryStatus.confirmed.value
            inquiry.updated_at = now

    record_audit_entry(
        db,
        entity_type="slot_reservation",
        entity_id=reservation.id,
        action="reservation_confirmed",
        actor_id=current_user.id,
        diff_payload={
            "public_ref": reservation.public_ref,
            "slot_id": str(reservation.slot_id),
            "seats": reservation.seats,
            "status": reservation.status,
            "confirmed_at": reservation.confirmed_at.isoformat(),
        },
    )

    try:
        db.commit()
        db.refresh(reservation)
    except IntegrityError:
        db.rollback()
        raise AppError(
            "CAPACITY_EXCEEDED",
            "Không thể xác nhận đặt chỗ do xung đột sức chứa.",
            status.HTTP_409_CONFLICT,
        )

    return _reservation_to_out(reservation, "Xác nhận đặt chỗ thành công.")


@router.post(
    "/api/v1/rbpc/partner/availability/cancel",
    response_model=RbpcSeatReservationOut,
)
def cancel_workshop_reservation(
    payload: RbpcReservationCancelIn,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cancel a reservation or hold, restoring seat capacity to the available pool."""
    verify_csrf(request)

    if current_user.role == UserRole.guest:
        raise AppError("FORBIDDEN", "Guest users cannot manage availability.", status.HTTP_403_FORBIDDEN)

    reservation = db.scalar(
        select(RbpcSeatReservation)
        .options(selectinload(RbpcSeatReservation.slot).selectinload(RbpcWorkshopSlot.experience))
        .where(RbpcSeatReservation.id == payload.reservation_id)
        .with_for_update()
    )
    if not reservation:
        raise AppError(
            "RBPC_RESERVATION_NOT_FOUND",
            f"Reservation '{payload.reservation_id}' not found.",
            status.HTTP_404_NOT_FOUND,
        )

    slot = db.scalar(
        select(RbpcWorkshopSlot)
        .options(selectinload(RbpcWorkshopSlot.experience))
        .where(RbpcWorkshopSlot.id == reservation.slot_id)
        .with_for_update()
    )
    if not slot:
        raise AppError("RBPC_SLOT_NOT_FOUND", "Workshop slot not found.", status.HTTP_404_NOT_FOUND)

    is_admin = current_user.role in ADMIN_ROLES
    if not is_admin:
        exp = slot.experience
        is_owner = (
            exp is not None
            and (exp.provider_id == current_user.id or exp.creator_id == current_user.id)
        )
        if not is_owner:
            raise AppError(
                "FORBIDDEN_SCOPE",
                "You do not have permission to cancel reservations for this experience.",
                status.HTTP_403_FORBIDDEN,
            )

    if reservation.status == RbpcReservationStatus.cancelled.value:
        return _reservation_to_out(reservation, "Đặt chỗ đã được hủy trước đó.")

    now = datetime.now(timezone.utc)
    if reservation.status == RbpcReservationStatus.confirmed.value:
        slot.confirmed_seats = max(0, slot.confirmed_seats - reservation.seats)
    elif reservation.status == RbpcReservationStatus.pending.value and reservation.expires_at > now:
        slot.reserved_seats = max(0, slot.reserved_seats - reservation.seats)

    slot.updated_at = now
    reservation.status = RbpcReservationStatus.cancelled.value
    reservation.updated_at = now

    record_audit_entry(
        db,
        entity_type="slot_reservation",
        entity_id=reservation.id,
        action="reservation_cancelled",
        actor_id=current_user.id,
        diff_payload={
            "public_ref": reservation.public_ref,
            "slot_id": str(reservation.slot_id),
            "seats": reservation.seats,
            "reason": payload.reason,
        },
    )

    db.commit()
    db.refresh(reservation)

    return _reservation_to_out(reservation, "Hủy đặt chỗ thành công.")


@router.post(
    "/api/v1/rbpc/partner/slots",
    status_code=status.HTTP_201_CREATED,
    response_model=RbpcWorkshopSlotOut,
)
def create_workshop_slot(
    payload: RbpcSlotCreateIn,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Partner endpoint to open a new calendar workshop slot with seat capacity."""
    verify_csrf(request)

    if current_user.role == UserRole.guest:
        raise AppError("FORBIDDEN", "Guest users cannot create workshop slots.", status.HTTP_403_FORBIDDEN)

    exp = db.scalar(
        select(RbpcExperience).where(
            RbpcExperience.slug == payload.experience_slug.strip().lower()
        )
    )
    if not exp:
        raise AppError(
            "RBPC_EXPERIENCE_NOT_FOUND",
            f"Experience '{payload.experience_slug}' not found.",
            status.HTTP_404_NOT_FOUND,
        )

    is_admin = current_user.role in ADMIN_ROLES
    if not is_admin:
        is_owner = (exp.provider_id == current_user.id or exp.creator_id == current_user.id)
        if not is_owner:
            raise AppError(
                "FORBIDDEN_SCOPE",
                "You do not have permission to create slots for this experience.",
                status.HTTP_403_FORBIDDEN,
            )

    if payload.end_time <= payload.start_time:
        raise AppError(
            "INVALID_TIME_RANGE",
            "Thời gian kết thúc phải sau thời gian bắt đầu.",
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    slot = RbpcWorkshopSlot(
        experience_id=exp.id,
        start_time=payload.start_time,
        end_time=payload.end_time,
        capacity=payload.capacity,
        reserved_seats=0,
        confirmed_seats=0,
        status=RbpcSlotStatus.open.value,
        notes=payload.notes,
    )
    db.add(slot)
    db.commit()
    db.refresh(slot)

    return _slot_to_out(slot)


@router.get(
    "/api/v1/rbpc/partner/slots",
    response_model=list[RbpcWorkshopSlotOut],
)
def list_partner_workshop_slots(
    experience_slug: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List workshop slots for experiences owned by the authenticated partner."""
    if current_user.role == UserRole.guest:
        raise AppError("FORBIDDEN", "Guest users cannot view partner slots.", status.HTTP_403_FORBIDDEN)

    stmt = select(RbpcWorkshopSlot).options(selectinload(RbpcWorkshopSlot.experience))

    is_admin = current_user.role in ADMIN_ROLES
    joined_exp = False
    if not is_admin:
        stmt = stmt.join(RbpcWorkshopSlot.experience).where(
            or_(
                RbpcExperience.provider_id == current_user.id,
                RbpcExperience.creator_id == current_user.id,
            )
        )
        joined_exp = True
    if experience_slug:
        if not joined_exp:
            stmt = stmt.join(RbpcWorkshopSlot.experience)
        stmt = stmt.where(
            RbpcExperience.slug == experience_slug.strip().lower()
        )

    slots = list(db.scalars(stmt.order_by(RbpcWorkshopSlot.start_time.asc())))
    now = datetime.now(timezone.utc)
    for s in slots:
        _expire_stale_reservations_for_slot(db, s, now)
    db.commit()

    return [_slot_to_out(s) for s in slots]


# --------------------------------------------------------------------------- #
# Oral History Consent Studio & Living Memory Endpoints (V5-T109)
# --------------------------------------------------------------------------- #
def _oral_history_to_out(rec: RbpcOralHistoryRecording) -> RbpcOralHistoryRecordingOut:
    """Helper to convert RbpcOralHistoryRecording ORM object to Pydantic Out."""
    latest_trans_out = None
    if rec.transcript_versions:
        # sorted by version_number desc
        lv = sorted(rec.transcript_versions, key=lambda v: v.version_number, reverse=True)[0]
        cues = []
        for c in (lv.timed_cues or []):
            if isinstance(c, dict):
                cues.append(
                    RbpcTranscriptCue(
                        time_sec=float(c.get("time_sec", 0.0)),
                        end_time_sec=float(c["end_time_sec"]) if c.get("end_time_sec") is not None else None,
                        text=str(c.get("text", "")),
                        speaker=c.get("speaker"),
                        section_title=c.get("section_title"),
                    )
                )
        latest_trans_out = RbpcAudioTranscriptVersionOut(
            id=lv.id,
            recording_id=lv.recording_id,
            version_number=lv.version_number,
            transcript_text_vi=lv.transcript_text_vi,
            transcript_text_en=lv.transcript_text_en,
            timed_cues=cues,
            change_summary=lv.change_summary,
            author_id=lv.author_id,
            is_verified_by_artisan=lv.is_verified_by_artisan,
            artisan_verified_at=lv.artisan_verified_at,
            created_at=lv.created_at,
        )

    return RbpcOralHistoryRecordingOut(
        id=rec.id,
        creator_id=rec.creator_id,
        recording_code=rec.recording_code,
        title_vi=rec.title_vi,
        title_en=rec.title_en,
        audio_url=rec.audio_url,
        audio_sha256=rec.audio_sha256,
        audio_duration_seconds=rec.audio_duration_seconds,
        mime_type=rec.mime_type,
        cultural_context_vi=rec.cultural_context_vi,
        cultural_context_en=rec.cultural_context_en,
        recording_date=rec.recording_date,
        recording_location=rec.recording_location,
        interviewer_name=rec.interviewer_name,
        epistemic_certainty=rec.epistemic_certainty,
        consent_scope=RbpcAudioConsentScope(rec.consent_scope),
        status=RbpcOralHistoryStatus(rec.status),
        consent_granted=rec.consent_granted,
        consent_agreement_ref=rec.consent_agreement_ref,
        consent_granted_at=rec.consent_granted_at,
        consent_notes=rec.consent_notes,
        revoked_at=rec.revoked_at,
        revocation_reason=rec.revocation_reason,
        erased_at=rec.erased_at,
        current_version_number=rec.current_version_number,
        created_at=rec.created_at,
        updated_at=rec.updated_at,
        latest_transcript=latest_trans_out,
    )


@router.post(
    "/api/v1/rbpc/partner/oral-history",
    response_model=RbpcOralHistoryRecordingOut,
    status_code=status.HTTP_201_CREATED,
)
def create_oral_history_recording(
    payload: RbpcOralHistoryCreateIn,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new oral history recording draft with cultural context and initial transcript."""
    verify_csrf(request)
    if current_user.role == UserRole.guest:
        raise AppError("FORBIDDEN", "Guest users cannot manage oral history recordings.", status.HTTP_403_FORBIDDEN)

    creator = db.get(RbpcCreator, payload.creator_id)
    if not creator:
        raise AppError("RBPC_CREATOR_NOT_FOUND", f"Creator '{payload.creator_id}' not found.", status.HTTP_404_NOT_FOUND)

    # Scoping: staff/admin or associated provider
    is_admin = current_user.role in ADMIN_ROLES
    if not is_admin:
        # Check if creator has experiences owned by user
        has_exp = db.scalar(
            select(func.count(RbpcExperience.id)).where(
                RbpcExperience.creator_id == creator.id,
                RbpcExperience.provider_id == current_user.id,
            )
        )
        if not has_exp and creator.reviewer_id != current_user.id:
            raise AppError("FORBIDDEN_SCOPE", "You do not have access to this creator studio.", status.HTTP_403_FORBIDDEN)

    recording_code = f"OH-{uuid_module.uuid4().hex[:6].upper()}"

    rec = RbpcOralHistoryRecording(
        creator_id=creator.id,
        recording_code=recording_code,
        title_vi=payload.title_vi.strip(),
        title_en=payload.title_en.strip() if payload.title_en else None,
        audio_url=payload.audio_url.strip() if payload.audio_url else f"/assets/rbpc/audio/{recording_code.lower()}.webm",
        audio_sha256=payload.audio_sha256.strip() if payload.audio_sha256 else None,
        audio_duration_seconds=payload.audio_duration_seconds,
        mime_type=payload.mime_type or "audio/webm",
        cultural_context_vi=payload.cultural_context_vi.strip(),
        cultural_context_en=payload.cultural_context_en.strip() if payload.cultural_context_en else None,
        recording_date=payload.recording_date,
        recording_location=payload.recording_location,
        interviewer_name=payload.interviewer_name,
        epistemic_certainty=payload.epistemic_certainty or RbpcEpistemicCertainty.community_tradition.value,
        consent_scope=RbpcAudioConsentScope.preview_only.value,
        status=RbpcOralHistoryStatus.draft.value,
        consent_granted=False,
        current_version_number=1,
    )
    db.add(rec)
    db.flush()

    # Initial transcript version if provided
    initial_text_vi = payload.initial_transcript_vi or payload.cultural_context_vi
    cues_data = [c.model_dump() for c in payload.initial_cues]
    initial_version = RbpcAudioTranscriptVersion(
        recording_id=rec.id,
        version_number=1,
        transcript_text_vi=initial_text_vi.strip(),
        transcript_text_en=payload.initial_transcript_en.strip() if payload.initial_transcript_en else None,
        timed_cues=cues_data,
        change_summary="Initial audio transcript draft",
        author_id=current_user.id,
        is_verified_by_artisan=False,
    )
    db.add(initial_version)
    db.flush()

    record_audit_entry(
        db,
        entity_type="rbpc_oral_history",
        entity_id=rec.id,
        action="oral_history_created",
        actor_id=current_user.id,
        diff_payload={
            "recording_code": rec.recording_code,
            "creator_id": str(creator.id),
            "title_vi": rec.title_vi,
            "status": rec.status,
            "consent_scope": rec.consent_scope,
        },
    )

    db.commit()
    db.refresh(rec)
    return _oral_history_to_out(rec)


@router.get(
    "/api/v1/rbpc/partner/oral-history",
    response_model=RbpcOralHistoryRecordingListOut,
)
def list_partner_oral_history(
    creator_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List oral history recordings for partner studio with role-based scoping."""
    if current_user.role == UserRole.guest:
        raise AppError("FORBIDDEN", "Guest users cannot view oral history recordings.", status.HTTP_403_FORBIDDEN)

    stmt = select(RbpcOralHistoryRecording).options(
        selectinload(RbpcOralHistoryRecording.transcript_versions)
    )

    is_admin = current_user.role in ADMIN_ROLES
    if not is_admin:
        # Scope to creators associated with partner experiences or reviewed by user
        stmt = stmt.join(RbpcCreator, RbpcOralHistoryRecording.creator_id == RbpcCreator.id).outerjoin(
            RbpcExperience, RbpcExperience.creator_id == RbpcCreator.id
        ).where(
            or_(
                RbpcExperience.provider_id == current_user.id,
                RbpcCreator.reviewer_id == current_user.id,
            )
        )

    if creator_id:
        stmt = stmt.where(RbpcOralHistoryRecording.creator_id == creator_id)

    stmt = stmt.distinct().order_by(RbpcOralHistoryRecording.created_at.desc())
    records = list(db.scalars(stmt))
    return RbpcOralHistoryRecordingListOut(
        items=[_oral_history_to_out(r) for r in records],
        total=len(records),
    )


@router.get(
    "/api/v1/rbpc/oral-history/{recording_id}",
    response_model=RbpcOralHistoryRecordingOut,
)
def get_oral_history_public(
    recording_id: UUID,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Public / student access to an oral history recording and its verified transcript.

    Negative abuse invariant (V5-T109):
    If consent is revoked, erased, or not consented:
    - Public access is rejected with HTTP 403 FORBIDDEN (or HTTP 410 GONE).
    - Returns anti-stale cache-control headers (no-store, no-cache).
    """
    rec = db.scalar(
        select(RbpcOralHistoryRecording)
        .options(selectinload(RbpcOralHistoryRecording.transcript_versions))
        .where(RbpcOralHistoryRecording.id == recording_id)
    )
    if not rec:
        raise AppError("ORAL_HISTORY_NOT_FOUND", f"Recording '{recording_id}' not found.", status.HTTP_404_NOT_FOUND)

    # Negative abuse check: Revocation / Erasure Fail-Closed
    from ..services.offline_licensing import (
        REVOKED_ASSET_CACHE,
        is_asset_revoked,
    )

    if rec.status in (RbpcOralHistoryStatus.revoked.value, RbpcOralHistoryStatus.erased.value) or is_asset_revoked(str(rec.id), db):
        revocation_headers = {
            "Cache-Control": REVOKED_ASSET_CACHE,
            "Pragma": "no-cache",
            "Expires": "0",
            "X-Consent-Status": "REVOKED",
            "X-Cache-Invalidation": "PURGE_CDN_IMMEDIATE",
        }
        raise AppError(
            "ORAL_HISTORY_REVOKED",
            "Quyền đồng thuận ghi âm lịch sử truyền khẩu này đã bị thu hồi hoặc xóa bỏ bởi nghệ nhân.",
            status_code=status.HTTP_403_FORBIDDEN,
            details={"cache_headers": revocation_headers, "revoked_at": rec.revoked_at.isoformat() if rec.revoked_at else None},
        )

    # Consent scope check for public non-staff callers
    is_staff = current_user and current_user.role in STAFF_ROLES
    if not is_staff:
        if not rec.consent_granted or rec.status != RbpcOralHistoryStatus.consented.value:
            raise AppError(
                "ORAL_HISTORY_NOT_CONSENTED",
                "Bản ghi chưa hoàn tất thủ tục đồng thuận công bố.",
                status_code=status.HTTP_403_FORBIDDEN,
            )
        if rec.consent_scope == RbpcAudioConsentScope.revoked:
            raise AppError(
                "ORAL_HISTORY_CONSENT_REVOKED",
                "Phạm vi đồng thuận sử dụng âm thanh đã bị thu hồi.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

    return _oral_history_to_out(rec)


@router.post(
    "/api/v1/rbpc/partner/oral-history/{recording_id}/versions",
    response_model=RbpcOralHistoryRecordingOut,
)
def add_transcript_version(
    recording_id: UUID,
    payload: RbpcOralHistoryTranscriptUpdateIn,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add a new versioned transcript with timecode cues to an oral history recording."""
    verify_csrf(request)
    if current_user.role == UserRole.guest:
        raise AppError("FORBIDDEN", "Guest users cannot edit transcripts.", status.HTTP_403_FORBIDDEN)

    rec = db.scalar(
        select(RbpcOralHistoryRecording)
        .options(selectinload(RbpcOralHistoryRecording.transcript_versions))
        .where(RbpcOralHistoryRecording.id == recording_id)
    )
    if not rec:
        raise AppError("ORAL_HISTORY_NOT_FOUND", f"Recording '{recording_id}' not found.", status.HTTP_404_NOT_FOUND)

    if rec.status in (RbpcOralHistoryStatus.revoked.value, RbpcOralHistoryStatus.erased.value):
        raise AppError(
            "ORAL_HISTORY_REVOKED",
            "Cannot add transcript versions to a revoked or erased recording.",
            status.HTTP_400_BAD_REQUEST,
        )

    new_version_num = rec.current_version_number + 1
    cues_data = [c.model_dump() for c in payload.timed_cues]

    ver = RbpcAudioTranscriptVersion(
        recording_id=rec.id,
        version_number=new_version_num,
        transcript_text_vi=payload.transcript_text_vi.strip(),
        transcript_text_en=payload.transcript_text_en.strip() if payload.transcript_text_en else None,
        timed_cues=cues_data,
        change_summary=payload.change_summary or f"Version {new_version_num} revision",
        author_id=current_user.id,
        is_verified_by_artisan=payload.verify_by_artisan,
        artisan_verified_at=datetime.now(timezone.utc) if payload.verify_by_artisan else None,
    )
    db.add(ver)

    rec.current_version_number = new_version_num
    rec.updated_at = datetime.now(timezone.utc)

    record_audit_entry(
        db,
        entity_type="rbpc_oral_history",
        entity_id=rec.id,
        action="transcript_version_added",
        actor_id=current_user.id,
        diff_payload={
            "new_version": new_version_num,
            "change_summary": ver.change_summary,
            "is_verified_by_artisan": ver.is_verified_by_artisan,
        },
    )

    db.commit()
    db.refresh(rec)
    return _oral_history_to_out(rec)


@router.post(
    "/api/v1/rbpc/partner/oral-history/{recording_id}/consent",
    response_model=RbpcOralHistoryRecordingOut,
)
def update_recording_consent(
    recording_id: UUID,
    payload: RbpcOralHistoryConsentUpdateIn,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Grant or update per-use media consent for an oral history recording."""
    verify_csrf(request)
    if current_user.role == UserRole.guest:
        raise AppError("FORBIDDEN", "Guest users cannot update consent.", status.HTTP_403_FORBIDDEN)

    rec = db.scalar(
        select(RbpcOralHistoryRecording)
        .options(selectinload(RbpcOralHistoryRecording.transcript_versions))
        .where(RbpcOralHistoryRecording.id == recording_id)
    )
    if not rec:
        raise AppError("ORAL_HISTORY_NOT_FOUND", f"Recording '{recording_id}' not found.", status.HTTP_404_NOT_FOUND)

    old_status = rec.status
    old_scope = rec.consent_scope

    rec.consent_scope = payload.consent_scope.value
    rec.consent_granted = payload.consent_granted
    if payload.consent_agreement_ref:
        rec.consent_agreement_ref = payload.consent_agreement_ref.strip()
    if payload.consent_notes:
        rec.consent_notes = payload.consent_notes.strip()

    now = datetime.now(timezone.utc)
    if payload.consent_granted and payload.consent_scope != RbpcAudioConsentScope.revoked:
        rec.status = RbpcOralHistoryStatus.consented.value
        rec.consent_granted_at = now
        rec.revoked_at = None
        rec.revocation_reason = None
    else:
        rec.status = RbpcOralHistoryStatus.revoked.value
        rec.revoked_at = now
        rec.revocation_reason = payload.consent_notes or "Consent scope set to revoked"

    rec.updated_at = now

    record_audit_entry(
        db,
        entity_type="rbpc_oral_history",
        entity_id=rec.id,
        action="consent_updated",
        actor_id=current_user.id,
        diff_payload={
            "old_status": old_status,
            "new_status": rec.status,
            "old_scope": old_scope,
            "new_scope": rec.consent_scope,
            "consent_granted": rec.consent_granted,
            "agreement_ref": rec.consent_agreement_ref,
        },
    )

    db.commit()
    db.refresh(rec)
    return _oral_history_to_out(rec)


@router.post(
    "/api/v1/rbpc/partner/oral-history/{recording_id}/revoke",
    response_model=RbpcOralHistoryRecordingOut,
)
def revoke_oral_history_recording(
    recording_id: UUID,
    payload: RbpcOralHistoryRevokeIn,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Revoke consent or request erasure (right-to-erasure / GDPR / Decree 13/2023/ND-CP).

    Negative abuse invariant (V5-T109):
    Immediately invalidates local and persistent CDN caches via AssetCacheRevocation
    and registers an immutable audit entry. Subsequent public calls immediately return 403.
    """
    verify_csrf(request)
    if current_user.role == UserRole.guest:
        raise AppError("FORBIDDEN", "Guest users cannot revoke recordings.", status.HTTP_403_FORBIDDEN)

    rec = db.scalar(
        select(RbpcOralHistoryRecording)
        .options(selectinload(RbpcOralHistoryRecording.transcript_versions))
        .where(RbpcOralHistoryRecording.id == recording_id)
    )
    if not rec:
        raise AppError("ORAL_HISTORY_NOT_FOUND", f"Recording '{recording_id}' not found.", status.HTTP_404_NOT_FOUND)

    now = datetime.now(timezone.utc)
    reason = payload.reason.strip()

    rec.status = RbpcOralHistoryStatus.erased.value if payload.erase_data else RbpcOralHistoryStatus.revoked.value
    rec.consent_scope = RbpcAudioConsentScope.revoked.value
    rec.consent_granted = False
    rec.revoked_at = now
    rec.revocation_reason = reason
    rec.revoked_by_id = current_user.id
    rec.updated_at = now

    if payload.erase_data:
        rec.erased_at = now
        # Redact identifying audio and transcript content under Right-to-Erasure
        rec.audio_url = None
        rec.audio_sha256 = None
        for tv in rec.transcript_versions:
            tv.transcript_text_vi = "[ERASED UNDER RIGHT-TO-ERASURE / DECREE 13/2023/ND-CP]"
            tv.transcript_text_en = "[ERASED UNDER RIGHT-TO-ERASURE / DECREE 13/2023/ND-CP]"
            tv.timed_cues = []

    # Immediate Cache Invalidation Engine (V5-T048 / V5-T109)
    from ..services.offline_licensing import register_asset_revocation

    register_asset_revocation(
        asset_id=str(rec.id),
        reason=f"Oral history consent revoked by creator: {reason}",
        revoked_by=str(current_user.id),
        asset_url=rec.audio_url or f"/assets/rbpc/audio/{rec.recording_code.lower()}.webm",
        db=db,
    )

    record_audit_entry(
        db,
        entity_type="rbpc_oral_history",
        entity_id=rec.id,
        action="erased" if payload.erase_data else "consent_revoked",
        actor_id=current_user.id,
        diff_payload={
            "reason": reason,
            "erased": payload.erase_data,
            "revoked_at": now.isoformat(),
            "cdn_purged": True,
        },
    )

    db.commit()
    db.refresh(rec)
    return _oral_history_to_out(rec)


# --------------------------------------------------------------------------- #
# Partner Self-Onboarding & Verification Endpoints (V5-T101 / W10-A01)
# --------------------------------------------------------------------------- #
@router.post(
    "/api/v1/rbpc/partner/onboarding",
    response_model=RbpcCreatorOut,
    status_code=status.HTTP_201_CREATED,
)
def partner_self_onboard(
    payload: RbpcPartnerOnboardingIn,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Allow an authenticated partner/artisan to register a craft profile.

    Defaults to is_verified=False and consent_status='pending_review' until staff verification.
    """
    verify_csrf(request)
    if current_user.role == UserRole.guest:
        raise AppError("FORBIDDEN", "Guest users cannot onboard as partners.", status.HTTP_403_FORBIDDEN)

    valid_slug = _validate_slug(payload.slug)
    # Check slug uniqueness
    existing = db.scalar(select(RbpcCreator).where(RbpcCreator.slug == valid_slug))
    if existing:
        raise AppError("RBPC_SLUG_CONFLICT", f"Slug '{valid_slug}' is already registered.", status.HTTP_409_CONFLICT)

    # Optional heritage place linking
    place_id = None
    if payload.heritage_place_slug:
        place = db.scalar(
            select(HeritagePlace).where(HeritagePlace.slug == payload.heritage_place_slug.strip().lower())
        )
        if place:
            place_id = place.id

    now = datetime.now(timezone.utc)
    creator = RbpcCreator(
        slug=valid_slug,
        public_name=payload.public_name.strip(),
        craft_tradition=payload.craft_tradition_vi.strip(),
        craft_tradition_en=payload.craft_tradition_en.strip() if payload.craft_tradition_en else None,
        approved_bio_vi=payload.approved_bio_vi.strip(),
        approved_bio_en=payload.approved_bio_en.strip() if payload.approved_bio_en else None,
        approved_portrait_url=payload.approved_portrait_url.strip() if payload.approved_portrait_url else None,
        public_region=payload.public_region.strip() if payload.public_region else "Huế",
        years_of_practice=payload.years_of_practice,
        generation_lineage=payload.generation_lineage.strip() if payload.generation_lineage else None,
        heritage_place_id=place_id,
        display_consent_ref=payload.display_consent_ref.strip() if payload.display_consent_ref else "self_submitted",
        consent_status=RbpcConsentStatus.pending_review.value,
        is_verified=False,
        user_id=current_user.id,
        identity_document_ref=payload.identity_document_ref.strip() if payload.identity_document_ref else None,
        rights_clearance_notes=payload.rights_clearance_notes.strip() if payload.rights_clearance_notes else None,
        created_at=now,
        updated_at=now,
    )
    db.add(creator)
    db.flush()

    record_audit_entry(
        db,
        entity_type=ENTITY_CREATOR,
        entity_id=creator.id,
        action="partner_onboarded",
        actor_id=current_user.id,
        diff_payload={
            "action": "partner_onboarded",
            "slug": creator.slug,
            "public_name": creator.public_name,
            "consent_status": creator.consent_status,
            "is_verified": False,
        },
    )

    db.commit()
    db.refresh(creator)
    return _creator_to_out(creator)


@router.get(
    "/api/v1/rbpc/partner/profile",
    response_model=RbpcCreatorOut,
)
def get_partner_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve the authenticated partner's artisan profile."""
    if current_user.role == UserRole.guest:
        raise AppError("FORBIDDEN", "Guest users do not have a partner profile.", status.HTTP_403_FORBIDDEN)

    creator = db.scalar(
        select(RbpcCreator)
        .options(
            selectinload(RbpcCreator.stories),
            selectinload(RbpcCreator.experiences),
            selectinload(RbpcCreator.heritage_place),
        )
        .where(RbpcCreator.user_id == current_user.id)
    )
    if not creator:
        raise AppError("RBPC_PROFILE_NOT_FOUND", "Partner profile not found for this account.", status.HTTP_404_NOT_FOUND)

    return _creator_to_out(creator)


@router.put(
    "/api/v1/rbpc/partner/profile",
    response_model=RbpcCreatorOut,
)
def update_partner_profile(
    payload: RbpcPartnerProfileUpdateIn,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Allow an artisan partner to edit their profile details.

    Updating core identity fields or portrait URL automatically flags for re-review
    if previous verification was completed.
    """
    verify_csrf(request)
    if current_user.role == UserRole.guest:
        raise AppError("FORBIDDEN", "Guest users cannot update partner profiles.", status.HTTP_403_FORBIDDEN)

    creator = db.scalar(
        select(RbpcCreator)
        .options(
            selectinload(RbpcCreator.stories),
            selectinload(RbpcCreator.experiences),
            selectinload(RbpcCreator.heritage_place),
        )
        .where(RbpcCreator.user_id == current_user.id)
    )
    if not creator:
        raise AppError("RBPC_PROFILE_NOT_FOUND", "Partner profile not found for this account.", status.HTTP_404_NOT_FOUND)

    changes: dict[str, Any] = {}
    if payload.public_name is not None:
        changes["public_name"] = {"old": creator.public_name, "new": payload.public_name.strip()}
        creator.public_name = payload.public_name.strip()
    if payload.craft_tradition_vi is not None:
        changes["craft_tradition"] = {"old": creator.craft_tradition, "new": payload.craft_tradition_vi.strip()}
        creator.craft_tradition = payload.craft_tradition_vi.strip()
    if payload.craft_tradition_en is not None:
        creator.craft_tradition_en = payload.craft_tradition_en.strip()
    if payload.approved_bio_vi is not None:
        changes["approved_bio_vi"] = {"old": creator.approved_bio_vi, "new": payload.approved_bio_vi.strip()}
        creator.approved_bio_vi = payload.approved_bio_vi.strip()
    if payload.approved_bio_en is not None:
        creator.approved_bio_en = payload.approved_bio_en.strip()
    if payload.approved_portrait_url is not None:
        old_portrait = creator.approved_portrait_url
        new_portrait = payload.approved_portrait_url.strip() if payload.approved_portrait_url else None
        if old_portrait != new_portrait:
            changes["approved_portrait_url"] = {"old": old_portrait, "new": new_portrait}
            creator.approved_portrait_url = new_portrait
            # If portrait changed, require staff re-verification for rights check
            creator.is_verified = False
            creator.consent_status = RbpcConsentStatus.pending_review.value
    if payload.public_region is not None:
        creator.public_region = payload.public_region.strip()
    if payload.years_of_practice is not None:
        creator.years_of_practice = payload.years_of_practice
    if payload.generation_lineage is not None:
        creator.generation_lineage = payload.generation_lineage.strip()
    if payload.display_consent_ref is not None:
        creator.display_consent_ref = payload.display_consent_ref.strip()
    if payload.identity_document_ref is not None:
        creator.identity_document_ref = payload.identity_document_ref.strip()
    if payload.rights_clearance_notes is not None:
        creator.rights_clearance_notes = payload.rights_clearance_notes.strip()

    creator.updated_at = datetime.now(timezone.utc)

    record_audit_entry(
        db,
        entity_type=ENTITY_CREATOR,
        entity_id=creator.id,
        action="partner_profile_updated",
        actor_id=current_user.id,
        diff_payload={"action": "partner_profile_updated", "changes": changes},
    )

    db.commit()
    db.refresh(creator)
    return _creator_to_out(creator)


@router.post(
    "/api/v1/rbpc/admin/creators/{id}/verify",
    response_model=RbpcCreatorOut,
)
def staff_verify_creator(
    id: UUID,
    payload: RbpcPartnerVerificationIn,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Staff endpoint to verify partner identity, display consent, and rights.

    Only STAFF_ROLES can approve or reject verification.
    """
    verify_csrf(request)
    if current_user.role not in STAFF_ROLES:
        raise AppError("FORBIDDEN_SCOPE", "Chỉ nhân viên kiểm duyệt mới có quyền xác thực đối tác.", status.HTTP_403_FORBIDDEN)

    creator = db.scalar(
        select(RbpcCreator)
        .options(
            selectinload(RbpcCreator.stories),
            selectinload(RbpcCreator.experiences),
            selectinload(RbpcCreator.heritage_place),
        )
        .where(RbpcCreator.id == id)
    )
    if not creator:
        raise AppError("RBPC_CREATOR_NOT_FOUND", f"Creator '{id}' not found.", status.HTTP_404_NOT_FOUND)

    old_verified = creator.is_verified
    creator.is_verified = payload.is_verified
    creator.reviewer_id = current_user.id
    creator.verified_at = datetime.now(timezone.utc) if payload.is_verified else None
    if payload.verification_notes is not None:
        creator.verification_notes = payload.verification_notes.strip()
    if payload.rights_clearance_notes is not None:
        creator.rights_clearance_notes = payload.rights_clearance_notes.strip()
    if payload.consent_status is not None:
        creator.consent_status = payload.consent_status.value
    creator.updated_at = datetime.now(timezone.utc)

    record_audit_entry(
        db,
        entity_type=ENTITY_CREATOR,
        entity_id=creator.id,
        action="creator_verified" if payload.is_verified else "creator_unverified",
        actor_id=current_user.id,
        diff_payload={
            "action": "creator_verified" if payload.is_verified else "creator_unverified",
            "old_verified": old_verified,
            "new_verified": creator.is_verified,
            "consent_status": creator.consent_status,
            "verification_notes": creator.verification_notes,
            "rights_clearance_notes": creator.rights_clearance_notes,
        },
    )

    db.commit()
    db.refresh(creator)
    return _creator_to_out(creator)


@router.post(
    "/api/v1/rbpc/partner/experiences",
    response_model=RbpcExperienceOut,
    status_code=status.HTTP_201_CREATED,
)
def partner_create_experience(
    payload: RbpcPartnerExperienceCreateIn,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Allow an authenticated partner to submit an experience listing.

    Defaults to publication_state='draft' and rights_checked=False.
    Negative abuse invariant: unverified partner cannot publish without staff verification.
    """
    verify_csrf(request)
    if current_user.role == UserRole.guest:
        raise AppError("FORBIDDEN", "Guest users cannot create experiences.", status.HTTP_403_FORBIDDEN)

    creator = db.scalar(
        select(RbpcCreator)
        .options(selectinload(RbpcCreator.experiences))
        .where(RbpcCreator.user_id == current_user.id)
    )
    if not creator:
        raise AppError(
            "RBPC_PROFILE_REQUIRED",
            "Bạn phải hoàn tất đăng ký hồ sơ nghệ nhân trước khi tạo trải nghiệm.",
            status.HTTP_400_BAD_REQUEST,
        )

    valid_slug = _validate_slug(payload.slug)
    existing_exp = db.scalar(select(RbpcExperience).where(RbpcExperience.slug == valid_slug))
    if existing_exp:
        raise AppError("RBPC_SLUG_CONFLICT", f"Experience slug '{valid_slug}' already exists.", status.HTTP_409_CONFLICT)

    now = datetime.now(timezone.utc)
    # Draft by default awaiting moderation
    exp = RbpcExperience(
        slug=valid_slug,
        creator_id=creator.id,
        provider_name=creator.public_name,
        provider_id=current_user.id,
        title_vi=payload.title_vi.strip(),
        title_en=payload.title_en.strip() if payload.title_en else None,
        description_vi=payload.description_vi.strip(),
        description_en=payload.description_en.strip() if payload.description_en else None,
        area_public=payload.area_public.strip() if payload.area_public else "Huế",
        duration_minutes=payload.duration_minutes,
        pricing_display=payload.pricing_display.strip() if payload.pricing_display else None,
        indicative_price_amount=payload.indicative_price_amount,
        currency=payload.currency.strip() if payload.currency else "VND",
        availability_mode=RbpcAvailabilityMode.inquiry_only.value,
        publication_state="draft",
        rights_checked=False,
        max_party_size=payload.max_party_size or 10,
        languages_supported=payload.languages_supported or ["vi"],
        notice=payload.notice.strip() if payload.notice else None,
        created_at=now,
        updated_at=now,
    )
    db.add(exp)
    db.flush()

    record_audit_entry(
        db,
        entity_type=ENTITY_EXPERIENCE,
        entity_id=exp.id,
        action="experience_created",
        actor_id=current_user.id,
        diff_payload={
            "action": "experience_created",
            "slug": exp.slug,
            "title_vi": exp.title_vi,
            "publication_state": exp.publication_state,
        },
    )

    db.commit()
    db.refresh(exp)
    return _experience_to_out(exp)


@router.patch(
    "/api/v1/rbpc/admin/experiences/{id}/moderate",
    response_model=RbpcExperienceOut,
)
def staff_moderate_experience(
    id: UUID,
    payload: RbpcExperienceModerationIn,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Staff endpoint to review and moderate experience listing and rights clearance.

    Negative abuse invariant: Cannot set publication_state='published' if the host artisan
    creator is not verified (is_verified=False) or rights are not cleared.
    """
    verify_csrf(request)
    if current_user.role not in STAFF_ROLES:
        raise AppError("FORBIDDEN_SCOPE", "Chỉ nhân viên kiểm duyệt mới có quyền phê duyệt trải nghiệm.", status.HTTP_403_FORBIDDEN)

    exp = db.scalar(
        select(RbpcExperience)
        .options(selectinload(RbpcExperience.creator))
        .where(RbpcExperience.id == id)
    )
    if not exp:
        raise AppError("RBPC_EXPERIENCE_NOT_FOUND", f"Experience '{id}' not found.", status.HTTP_404_NOT_FOUND)

    # Negative abuse check: cannot publish if creator is unverified
    if payload.publication_state == "published":
        if not exp.creator or not exp.creator.is_verified:
            raise AppError(
                "RBPC_UNVERIFIED_ARTISAN",
                "Không thể công khai trải nghiệm khi nghệ nhân liên kết chưa được nhân sự xác thực danh tính và đồng thuận.",
                status.HTTP_400_BAD_REQUEST,
            )
        if not payload.rights_checked:
            raise AppError(
                "RBPC_RIGHTS_NOT_CHECKED",
                "Không thể công khai trải nghiệm khi quyền sở hữu trí tuệ và giấy phép chưa được kiểm tra.",
                status.HTTP_400_BAD_REQUEST,
            )

    old_state = exp.publication_state
    exp.publication_state = payload.publication_state
    exp.rights_checked = payload.rights_checked
    exp.moderated_by_id = current_user.id
    exp.moderated_at = datetime.now(timezone.utc)
    if payload.moderation_notes is not None:
        exp.moderation_notes = payload.moderation_notes.strip()
    exp.updated_at = datetime.now(timezone.utc)

    record_audit_entry(
        db,
        entity_type=ENTITY_EXPERIENCE,
        entity_id=exp.id,
        action="experience_moderated",
        actor_id=current_user.id,
        diff_payload={
            "action": "experience_moderated",
            "old_state": old_state,
            "new_state": exp.publication_state,
            "rights_checked": exp.rights_checked,
            "moderation_notes": exp.moderation_notes,
        },
    )

    db.commit()
    db.refresh(exp)
    return _experience_to_out(exp)


# --------------------------------------------------------------------------- #
# Startup Evidence Room & Pitch Review Endpoints (V5-T120 / W11-A10)
# --------------------------------------------------------------------------- #
@router.get(
    "/api/v1/rbpc/evidence-room/pointers",
    response_model=RbpcEvidencePointerListOut,
)
def list_evidence_pointers(
    domain: Optional[str] = Query(None, description="Filter by domain: product, customer, market, finances, impact, legal, team"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status: active_verified, archived, needs_review"),
    db: Session = Depends(get_db),
):
    """Retrieve versioned evidence room pointers with optional domain or status filter."""
    count = db.scalar(select(func.count(RbpcEvidencePointer.id)))
    if count == 0:
        default_evidence_room_service.seed_db(db)

    stmt = select(RbpcEvidencePointer)
    if domain:
        stmt = stmt.where(RbpcEvidencePointer.domain == domain.strip().lower())
    if status_filter:
        stmt = stmt.where(RbpcEvidencePointer.status == status_filter.strip().lower())
    stmt = stmt.order_by(RbpcEvidencePointer.domain, RbpcEvidencePointer.pointer_id)

    rows = db.scalars(stmt).all()
    items = [
        RbpcEvidencePointerOut(
            pointer_id=r.pointer_id,
            domain=r.domain,
            title=r.title,
            doc_ref=r.doc_ref,
            version=r.version,
            status=r.status,
            hash_sha256=r.hash_sha256,
            metrics_payload=r.metrics_payload or {},
            summary=r.summary,
            owner=r.owner,
            verified_at=r.verified_at,
            created_at=r.created_at,
            updated_at=r.updated_at,
        )
        for r in rows
    ]
    return RbpcEvidencePointerListOut(
        items=items,
        total=len(items),
        domains_covered=[d.value for d in RbpcEvidenceDomain],
    )


@router.get(
    "/api/v1/rbpc/evidence-room/pointers/{pointer_id}",
    response_model=RbpcEvidencePointerOut,
)
def get_evidence_pointer(
    pointer_id: str,
    db: Session = Depends(get_db),
):
    """Retrieve a single versioned evidence pointer by pointer_id."""
    pointer = db.scalar(
        select(RbpcEvidencePointer).where(RbpcEvidencePointer.pointer_id == pointer_id.strip())
    )
    if not pointer:
        canon = default_evidence_room_service.get_pointer(pointer_id.strip())
        if not canon:
            raise AppError("POINTER_NOT_FOUND", f"Evidence pointer '{pointer_id}' not found.", status.HTTP_404_NOT_FOUND)
        default_evidence_room_service.seed_db(db)
        pointer = db.scalar(
            select(RbpcEvidencePointer).where(RbpcEvidencePointer.pointer_id == pointer_id.strip())
        )
    return RbpcEvidencePointerOut(
        pointer_id=pointer.pointer_id,
        domain=pointer.domain,
        title=pointer.title,
        doc_ref=pointer.doc_ref,
        version=pointer.version,
        status=pointer.status,
        hash_sha256=pointer.hash_sha256,
        metrics_payload=pointer.metrics_payload or {},
        summary=pointer.summary,
        owner=pointer.owner,
        verified_at=pointer.verified_at,
        created_at=pointer.created_at,
        updated_at=pointer.updated_at,
    )


@router.post(
    "/api/v1/rbpc/pitch-review/evaluate",
    response_model=RbpcPitchReviewOut,
    status_code=status.HTTP_200_OK,
)
def evaluate_pitch_review(
    payload: RbpcPitchReviewIn,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Evaluate and audit a set of pitch deck assertions against the evidence room.

    Negative abuse invariant:
    Every quantitative pitch claim must have an immutable evidence reference and status;
    ungrounded metrics are flagged (UNGROUNDED_FLAGGED) and pitch readiness is FLAGGED_UNREADY.
    """
    count = db.scalar(select(func.count(RbpcEvidencePointer.id)))
    if count == 0:
        default_evidence_room_service.seed_db(db)

    claim_items = [
        PitchClaimItem(
            claim_text=c.claim_text,
            domain=c.domain,
            evidence_pointer_id=c.evidence_pointer_id,
            metric_key=c.metric_key,
            claimed_value=c.claimed_value,
            is_quantitative=c.is_quantitative,
            truth_tier=c.truth_tier or "OBSERVED",
        )
        for c in payload.claims
    ]

    report = default_evidence_room_service.evaluate_pitch_claims(
        deck_title=payload.pitch_deck_title,
        deck_version=payload.deck_version,
        claims=claim_items,
    )

    review_row = default_evidence_room_service.persist_pitch_review(
        db,
        report,
        reviewed_by_id=current_user.id if current_user else None,
    )

    return RbpcPitchReviewOut(
        audit_ref=review_row.audit_ref,
        pitch_deck_title=review_row.pitch_deck_title,
        deck_version=review_row.deck_version,
        total_claims_audited=review_row.total_claims_audited,
        verified_claims_count=review_row.verified_claims_count,
        ungrounded_claims_count=review_row.ungrounded_claims_count,
        pitch_readiness=review_row.pitch_readiness,
        claims_payload=review_row.claims_payload or [],
        audit_findings=review_row.audit_findings or {},
        reviewed_at=review_row.reviewed_at,
    )


@router.get(
    "/api/v1/rbpc/pitch-review/audits/{audit_ref}",
    response_model=RbpcPitchReviewOut,
)
def get_pitch_review_audit(
    audit_ref: str,
    db: Session = Depends(get_db),
):
    """Retrieve an immutable pitch review audit report by audit_ref."""
    review = db.scalar(
        select(RbpcPitchReview).where(RbpcPitchReview.audit_ref == audit_ref.strip())
    )
    if not review:
        raise AppError("AUDIT_NOT_FOUND", f"Pitch review audit '{audit_ref}' not found.", status.HTTP_404_NOT_FOUND)

    return RbpcPitchReviewOut(
        audit_ref=review.audit_ref,
        pitch_deck_title=review.pitch_deck_title,
        deck_version=review.deck_version,
        total_claims_audited=review.total_claims_audited,
        verified_claims_count=review.verified_claims_count,
        ungrounded_claims_count=review.ungrounded_claims_count,
        pitch_readiness=review.pitch_readiness,
        claims_payload=review.claims_payload or [],
        audit_findings=review.audit_findings or {},
        reviewed_at=review.reviewed_at,
    )


@router.get(
    "/api/v1/rbpc/evidence-room/export",
    response_model=RbpcEvidenceRoomExportOut,
)
def export_evidence_room(
    format: str = Query("json", description="Export format: json or markdown"),
):
    """Export evidence room catalog as structured JSON or Markdown table."""
    fmt = format.strip().lower()
    if fmt == "markdown":
        content = default_evidence_room_service.export_evidence_room_markdown()
    else:
        content = default_evidence_room_service.export_evidence_room_json()

    pointers = default_evidence_room_service.get_all_pointers()
    return RbpcEvidenceRoomExportOut(
        format=fmt,
        content=content,
        total_pointers=len(pointers),
        domains_covered=[d.value for d in RbpcEvidenceDomain],
    )





