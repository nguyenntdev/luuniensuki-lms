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

import logging
import re
import uuid as uuid_module
from datetime import date, datetime, timedelta, timezone
from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy import func, or_, select
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
    RbpcObservedMetrics,
    RbpcPartnerInquiryListOut,
    RbpcPartnerInquiryOut,
    RbpcPartnerInquiryUpdate,
    RbpcProjectedMetrics,
    RbpcStoryDetailOut,
    RbpcStoryListOut,
    RbpcStoryOut,
    RbpcSupportType,
)
from ..db import get_db
from ..deps import get_current_user, get_current_user_optional
from ..errors import AppError
from ..models import User
from ..models_rbpc import (
    HeritagePlace,
    HeritageSourceEvidence,
    RbpcClaimEvidence,
    RbpcContentAudit,
    RbpcCreator,
    RbpcExperience,
    RbpcInquiry,
    RbpcStory,
)
from ..rbac import ADMIN_ROLES, STAFF_ROLES
from ..services import rbpc_ai
from ..services.rbpc_audit import (
    record_audit_entry,
    record_creator_consent_change,
    record_inquiry_state_transition,
)

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
_inquiry_rate_limit_store: dict[str, list[datetime]] = {}
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


def _check_inquiry_rate_limit(request: Request) -> str:
    """Enforce rate-limiting on inquiry submissions (max 5 requests per IP/hour)."""
    ip = _get_client_ip(request)
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(seconds=INQUIRY_RATE_LIMIT_WINDOW_SECONDS)

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
    return RbpcConfigOut(
        enabled=True,
        ai_enabled=True,
        inquiry_enabled=True,
        supported_locales=["vi", "en"],
        default_locale="vi",
        demo_mode=True,
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

    # Experience (fail-closed: hidden if linked creator consent is not active)
    experience_out = None
    if story.experience and story.experience.publication_state == "published":
        exp_creator = story.experience.creator or story.creator
        if not exp_creator or exp_creator.consent_status in (
            RbpcConsentStatus.consented.value,
            RbpcConsentStatus.verified_written_consent.value,
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

    return _creator_to_out(creator)


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

    return _experience_to_out(exp)


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
    # Guardrail 1: Rate limiting (max 5 requests per IP/hour)
    _check_inquiry_rate_limit(request)

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

    # Guardrail 6: Idempotency check
    existing = db.scalar(
        select(RbpcInquiry).where(RbpcInquiry.idempotency_key == validated_key)
    )
    if existing:
        # Check payload consistency
        if (
            existing.experience_id != exp.id
            or existing.name != sanitized_name
            or existing.contact_value != sanitized_contact_value
            or existing.party_size != payload.party_size
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

    # Non-sequential reference code & high-entropy status bearer token
    hex_ref = uuid_module.uuid4().hex[:8].upper()
    public_ref = f"INQ-{hex_ref[:4]}-{hex_ref[4:]}"
    opaque_token = f"tok_sec_{uuid_module.uuid4().hex}"

    inquiry = RbpcInquiry(
        public_ref=public_ref,
        experience_id=exp.id,
        provider_id=exp.provider_id or exp.creator_id,
        name=sanitized_name,
        contact_channel=payload.contact.method.value,
        contact_value=sanitized_contact_value,
        desired_date=payload.preferred_date,
        party_size=payload.party_size,
        message=sanitized_message,
        consent_version=payload.consent.version,
        privacy_accepted=payload.consent.privacy_accepted,
        state=RbpcInquiryStatus.new.value,
        idempotency_key=validated_key,
        opaque_token=opaque_token,
        retention_due_at=datetime.now(timezone.utc) + timedelta(days=90),
    )
    db.add(inquiry)
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
        },
    )

    db.commit()
    db.refresh(inquiry)

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
    cleaned_token = opaqueToken.strip()
    if not cleaned_token:
        raise AppError("RBPC_INQUIRY_NOT_FOUND", "Inquiry not found for status token.", status.HTTP_404_NOT_FOUND)

    inquiry = db.scalar(
        select(RbpcInquiry)
        .options(selectinload(RbpcInquiry.experience))
        .where(RbpcInquiry.opaque_token == cleaned_token)
    )
    if not inquiry:
        raise AppError("RBPC_INQUIRY_NOT_FOUND", "Inquiry not found for status token.", status.HTTP_404_NOT_FOUND)

    exp_title = inquiry.experience.title_vi if inquiry.experience else "Trải nghiệm văn hóa"
    status_msg = INQUIRY_STATUS_MESSAGES.get(inquiry.state, "Trạng thái đang được cập nhật.")

    return RbpcInquiryStatusOut(
        reference=inquiry.public_ref,
        experience_title=exp_title,
        status=inquiry.state,
        status_message=status_msg,
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

    return RbpcImpactMetricsOut(
        observed_metrics=RbpcObservedMetrics(
            published_stories_count=published_stories_count,
            consented_creators_count=consented_creators_count,
            active_experiences_count=active_experiences_count,
            total_inquiries_received=total_inquiries_received,
            verified_heritage_places_count=verified_heritage_places_count,
            verified_source_citations_count=verified_source_citations_count,
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve incoming visitor inquiries for the authenticated provider.

    Enforces strict server-side scoping: non-staff callers only view inquiries
    belonging to their own provider account.
    """
    is_admin = current_user.role in ADMIN_ROLES

    stmt = select(RbpcInquiry).options(selectinload(RbpcInquiry.experience))
    if not is_admin:
        # Provider scoping: strictly provider ownership (provider_id or linked experience.provider_id)
        stmt = stmt.outerjoin(RbpcInquiry.experience).where(
            or_(
                RbpcInquiry.provider_id == current_user.id,
                RbpcExperience.provider_id == current_user.id,
            )
        )

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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Transition inquiry status (new -> contacted -> confirmed / declined / closed).

    Rejects unauthorized access with 403 FORBIDDEN_SCOPE.
    Enforces valid lifecycle state transitions.
    """
    inquiry = db.get(RbpcInquiry, id)
    if not inquiry:
        raise AppError("RBPC_INQUIRY_NOT_FOUND", f"Inquiry '{id}' not found.", status.HTTP_404_NOT_FOUND)

    is_admin = current_user.role in ADMIN_ROLES
    if not is_admin:
        exp = inquiry.experience
        is_owner = (
            inquiry.provider_id == current_user.id
            or (exp is not None and exp.provider_id == current_user.id)
        )
        if not is_owner:
            raise AppError("FORBIDDEN_SCOPE", "You do not have permission to manage this inquiry.", status.HTTP_403_FORBIDDEN)

    target_state = payload.status.value
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Allow editors to update artisan consent state (consented, pending_review, revoked).

    Enforces editor/staff permissions (STAFF_ROLES) and logs cryptographic audit trail.
    """
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
