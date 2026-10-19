# -*- coding: utf-8 -*-
"""LƯU NIÊN — RBPC 2026 Commercial & Cultural Bridge API Schemas (Phase 1).

Request and response models for the commercial MVP slice:
- Discovery stories & approved claims evidence
- AI Cultural Bridge conversational query & citation verification
- Consented creator (artisan) profiles & craft traditions
- Real-world cultural experiences & inquiry-only booking requests
- Partner inbox & state transitions (zero PII leaks on public interfaces)
- Impact metrics with strict observed vs projected data separation

Namespace: /api/v1/rbpc/*
Content Scope: RBPC_HUE
"""
from __future__ import annotations

import re
import uuid as uuid_module
from datetime import date, datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .heritage import HeritageMediaAssetOut


# --------------------------------------------------------------------------- #
# Controlled Vocabularies & State Transitions
# --------------------------------------------------------------------------- #
class RbpcInquiryStatus(str, Enum):
    new = "new"
    contacted = "contacted"
    confirmed = "confirmed"
    declined = "declined"
    closed = "closed"


class RbpcContactMethod(str, Enum):
    email = "email"
    phone = "phone"
    zalo = "zalo"


class RbpcAvailabilityMode(str, Enum):
    inquiry_only = "inquiry_only"
    disabled = "disabled"


class RbpcEpistemicCertainty(str, Enum):
    high = "high"
    medium = "medium"
    contested = "contested"
    insufficient_sources = "insufficient_sources"


class RbpcSupportType(str, Enum):
    direct = "direct"
    contextual = "contextual"
    interpretation = "interpretation"
    unverified = "unverified"


class RbpcConsentStatus(str, Enum):
    consented = "consented"
    verified_written_consent = "verified_written_consent"
    pending_review = "pending_review"
    revoked = "revoked"


# --------------------------------------------------------------------------- #
# Config & Feature Flags
# --------------------------------------------------------------------------- #
class RbpcConfigOut(BaseModel):
    """Platform runtime configuration, feature flags, and consent metadata."""

    model_config = ConfigDict(from_attributes=True)

    enabled: bool = Field(default=True, description="Master feature flag for RBPC module.")
    ai_enabled: bool = Field(default=True, description="Cultural Bridge AI feature availability.")
    inquiry_enabled: bool = Field(
        default=True,
        description="Booking inquiry availability flag.",
    )
    supported_locales: list[str] = Field(
        default_factory=lambda: ["vi", "en"],
        description="Supported ISO 639-1 language codes.",
    )
    default_locale: str = Field(default="vi", description="Fallback default locale.")
    demo_mode: bool = Field(
        default=True,
        description="Demo/competition mode flag (indicates non-commercial student pilot).",
    )
    version: str = Field(default="1.0.0", description="API contract semantic version.")
    privacy_notice_url: str = Field(
        default="/privacy",
        description="URL to the privacy notice covering inquiry processing.",
    )
    terms_url: str = Field(
        default="/terms",
        description="URL to platform terms of use.",
    )
    consent_version: str = Field(
        default="rbpc-inquiry-v1",
        description="Active consent document version required for inquiry submission.",
    )


# --------------------------------------------------------------------------- #
# Creator (Artisan) Profile
# --------------------------------------------------------------------------- #
class RbpcCreatorOut(BaseModel):
    """Consented artisan or master practitioner profile with craft lineage."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    slug: str = Field(..., description="URL-safe identifier.")
    public_name: str = Field(..., description="Public display name or artisan title.")
    craft_tradition_vi: str = Field(
        ...,
        description="Craft tradition name in Vietnamese (e.g. Đúc đồng Phường Đúc, Hoa giấy Thanh Tiên).",
    )
    craft_tradition_en: Optional[str] = Field(
        default=None,
        description="Craft tradition name in English.",
    )
    approved_bio_vi: str = Field(
        ...,
        description="Reviewer- and artisan-approved biography in Vietnamese.",
    )
    approved_bio_en: Optional[str] = Field(
        default=None,
        description="Reviewer- and artisan-approved biography in English.",
    )
    approved_portrait_url: Optional[str] = Field(
        default=None,
        description="Rights-cleared portrait asset URL.",
    )
    public_region: str = Field(
        ...,
        description="Public geographic locality (e.g. Phường Đúc, TP. Huế; Phú Mậu, Phú Vang).",
    )
    consent_status: RbpcConsentStatus = Field(
        default=RbpcConsentStatus.consented,
        description="Verification state of the practitioner's written consent.",
    )
    approved_story_slugs: list[str] = Field(
        default_factory=list,
        description="Slugs of curated stories featuring this practitioner.",
    )
    experience_slugs: list[str] = Field(
        default_factory=list,
        description="Slugs of real-world experiences hosted by this practitioner.",
    )
    years_of_practice: Optional[int] = Field(
        default=None,
        description="Years dedicated to the craft tradition.",
    )
    generation_lineage: Optional[str] = Field(
        default=None,
        description="Family or craft generational lineage (e.g. Đời thứ 4 dòng họ Nguyễn).",
    )
    heritage_place_slug: Optional[str] = Field(
        default=None,
        description="Associated heritage place slug if tied to a specific community monument.",
    )
    created_at: datetime


class RbpcCreatorListOut(BaseModel):
    """List of consented creators."""

    items: list[RbpcCreatorOut]
    total: int


class RbpcCreatorConsentUpdate(BaseModel):
    """Editor request payload to update artisan consent state."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    consent_status: RbpcConsentStatus = Field(
        ...,
        description="Target consent state: consented, pending_review, revoked.",
    )
    notes: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Editorial justification or consent document reference.",
    )

    @model_validator(mode="before")
    @classmethod
    def populate_consent_status(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "consent_status" not in data and "status" in data:
                data = dict(data)
                data["consent_status"] = data["status"]
        return data


# --------------------------------------------------------------------------- #
# Experience (Workshop / Tour Offering)
# --------------------------------------------------------------------------- #
class RbpcExperienceOut(BaseModel):
    """Real-world cultural experience with honest inquiry-only notice."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    slug: str = Field(..., description="URL-safe identifier.")
    creator_slug: str = Field(..., description="Slug of the host practitioner.")
    creator_name: str = Field(..., description="Public name of the practitioner.")
    title_vi: str = Field(..., description="Experience title in Vietnamese.")
    title_en: Optional[str] = Field(default=None, description="Experience title in English.")
    description_vi: str = Field(..., description="Detailed itinerary/description in Vietnamese.")
    description_en: Optional[str] = Field(default=None, description="Detailed description in English.")
    area_public: str = Field(
        ...,
        description="Neighborhood / community location (e.g. Làng Thanh Tiên, Phú Mậu).",
    )
    duration_minutes: Optional[int] = Field(
        default=None,
        description="Approximate duration in minutes.",
    )
    indicative_pricing_display: Optional[str] = Field(
        default=None,
        description="Human-readable indicative price (e.g. Từ 350.000 VNĐ / khách).",
    )
    indicative_price_amount: Optional[float] = Field(
        default=None,
        description="Raw indicative amount in local currency.",
    )
    currency: str = Field(default="VND", description="Currency ISO 4217 code.")
    availability_mode: RbpcAvailabilityMode = Field(
        default=RbpcAvailabilityMode.inquiry_only,
        description="Commercial flow mode: inquiry_only (no simulated instant booking).",
    )
    publication_state: str = Field(default="published")
    cancellation_policy_text_vi: Optional[str] = None
    cancellation_policy_text_en: Optional[str] = None
    max_party_size: Optional[int] = Field(default=10, ge=1, le=50)
    languages_supported: list[str] = Field(default_factory=lambda: ["vi"])
    notice: str = Field(
        default="Yêu cầu trải nghiệm chỉ là bước liên hệ xác nhận, không phải giao dịch thanh toán tức thì.",
        description="Honest transparency disclosure.",
    )


class RbpcExperienceListOut(BaseModel):
    """List of published experiences."""

    items: list[RbpcExperienceOut]
    total: int


# --------------------------------------------------------------------------- #
# Stories & Claim Evidence
# --------------------------------------------------------------------------- #
class RbpcClaimEvidenceOut(BaseModel):
    """Grounded historical or artisanal claim supporting a story."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    statement: str = Field(..., description="Factual or contextual statement.")
    locale: str = Field(default="vi")
    claim_category: str = Field(
        default="historical_fact",
        description="Category: historical_fact, maker_technique, cultural_symbolism, contemporary_practice.",
    )
    source_title: str = Field(..., description="Title of the source backing this claim.")
    source_url: Optional[str] = None
    support_type: RbpcSupportType = RbpcSupportType.direct
    review_status: str = Field(
        default="verified",
        description="Review status: verified, published_human_approved.",
    )
    citation_label: Optional[str] = Field(
        default=None,
        description="Bibliographic short code or footnote reference.",
    )


class RbpcStoryOut(BaseModel):
    """Summary representation of a curated cultural story."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    slug: str
    title_vi: str
    title_en: Optional[str] = None
    intro_vi: str
    intro_en: Optional[str] = None
    primary_asset_url: Optional[str] = None
    category: Optional[str] = None
    status: str = "published"
    published_at: Optional[datetime] = None
    reading_time_minutes: Optional[int] = None
    creator_slug: Optional[str] = None
    experience_slug: Optional[str] = None
    heritage_place_slug: Optional[str] = None
    content_scope: str = "RBPC_HUE"
    created_at: datetime


class RbpcStoryDetailOut(RbpcStoryOut):
    """Deep representation of a curated story including claims, creator, and media."""

    historical_context: Optional[dict[str, Any]] = None
    approved_summary_vi: str = Field(..., description="Curator-approved canonical summary in Vietnamese.")
    approved_summary_en: Optional[str] = Field(
        default=None,
        description="Curator-approved canonical summary in English.",
    )
    evidence_claims: list[RbpcClaimEvidenceOut] = Field(default_factory=list)
    creator: Optional[RbpcCreatorOut] = None
    experience: Optional[RbpcExperienceOut] = None
    media_assets: list[HeritageMediaAssetOut] = Field(default_factory=list)
    version: int = Field(default=1, description="Content version integer.")
    rights_id: Optional[UUID] = None


class RbpcStoryListOut(BaseModel):
    """List of published stories."""

    items: list[RbpcStoryOut]
    total: int
    locale: str = "vi"


# --------------------------------------------------------------------------- #
# AI Cultural Bridge
# --------------------------------------------------------------------------- #
class RbpcCulturalBridgeRequest(BaseModel):
    """Visitor query to the source-grounded Cultural Bridge AI."""

    story_slug: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Slug of the published story scoping the query.",
    )
    question: str = Field(
        ...,
        min_length=2,
        max_length=1000,
        description="User's cultural inquiry question.",
    )
    locale: str = Field(
        default="vi",
        pattern="^(vi|en)$",
        description="Desired response locale (vi or en).",
    )
    context_preferences: Optional[dict[str, Any]] = Field(
        default=None,
        description="Optional visitor preferences (e.g. beginner_friendly, craft_focus).",
    )


class RbpcCulturalBridgeCitation(BaseModel):
    """Strict citation reference mapping back to a verified claim and source."""

    source_id: str = Field(..., description="UUID or approved key of the source.")
    title: str = Field(..., description="Title of the cited source.")
    support: RbpcSupportType = Field(
        default=RbpcSupportType.direct,
        description="Type of evidence support: direct, contextual, interpretation.",
    )
    claim_id: Optional[str] = Field(
        default=None,
        description="UUID of the specific supporting claim in the database.",
    )
    locator: Optional[str] = Field(
        default=None,
        description="Page number, decree section, or interview excerpt locator.",
    )


class RbpcCulturalBridgeResponse(BaseModel):
    """Source-grounded Cultural Bridge response with explicit epistemic certainty."""

    status: str = Field(
        default="supported",
        description="Response status: supported, insufficient_evidence, out_of_scope, fallback_to_curated.",
    )
    locale: str = Field(default="vi")
    answer: str = Field(..., description="Culturally respectful, source-grounded explanation.")
    citations: list[RbpcCulturalBridgeCitation] = Field(
        default_factory=list,
        description="Array of verified citations. Empty citations trigger epistemic uncertainty flag.",
    )
    context_boundary: str = Field(
        ...,
        description="Explicit boundary note separating verified history from contemporary artisan testimony.",
    )
    epistemic_certainty: RbpcEpistemicCertainty = Field(
        default=RbpcEpistemicCertainty.high,
        description="Certainty evaluation: high, medium, contested, insufficient_sources.",
    )
    review_status: str = Field(
        default="published_human_approved_context",
        description="Editorial status of the backing corpus.",
    )
    model_version: str = Field(
        ...,
        description="Private server model and prompt version identifier.",
    )
    uncertainty_note: Optional[str] = Field(
        default=None,
        description="Specific historiographical caveat or note on conflicting traditions.",
    )
    suggested_followups: list[str] = Field(
        default_factory=list,
        description="Suggested follow-up questions relevant to this story.",
    )
    linked_creator_slug: Optional[str] = Field(
        default=None,
        description="Slug of recommended living artisan matching the cultural inquiry.",
    )
    linked_creator_name: Optional[str] = Field(
        default=None,
        description="Public display name of recommended living artisan.",
    )
    linked_experience_slug: Optional[str] = Field(
        default=None,
        description="Slug of recommended workshop experience.",
    )
    linked_experience_title: Optional[str] = Field(
        default=None,
        description="Title of recommended workshop experience.",
    )


# --------------------------------------------------------------------------- #
# Inquiries: Create & Public Status
# --------------------------------------------------------------------------- #
class RbpcContactIn(BaseModel):
    """Visitor contact information."""

    name: str = Field(..., min_length=2, max_length=100, description="Visitor contact name.")
    method: RbpcContactMethod = Field(..., description="Preferred contact channel (email, phone, zalo).")
    value: str = Field(..., min_length=3, max_length=150, description="Email address or phone number.")

    @field_validator("value")
    @classmethod
    def validate_contact_value(cls, v: str, info) -> str:
        v = v.strip()
        method = info.data.get("method")
        if method == RbpcContactMethod.email:
            if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", v):
                raise ValueError("Invalid email format.")
        elif method in (RbpcContactMethod.phone, RbpcContactMethod.zalo):
            digits = re.sub(r"[\s\-\+\(\)]", "", v)
            if not digits.isdigit() or len(digits) < 8 or len(digits) > 15:
                raise ValueError("Invalid phone/zalo format (must be 8-15 digits).")
        return v


class RbpcConsentIn(BaseModel):
    """Explicit visitor opt-in consent for availability inquiry."""

    version: str = Field(..., min_length=1, max_length=50, description="Consent document version.")
    accepted: bool = Field(
        ...,
        description="Explicit consent checkbox. Must be true; requests with false are rejected.",
    )
    privacy_accepted: bool = Field(
        default=True,
        description="Acknowledgement of privacy policy and temporary contact retention.",
    )

    @field_validator("accepted")
    @classmethod
    def validate_accepted(cls, v: bool) -> bool:
        if not v:
            raise ValueError("Explicit consent must be accepted (accepted must be True).")
        return v

    @field_validator("privacy_accepted")
    @classmethod
    def validate_privacy(cls, v: bool) -> bool:
        if not v:
            raise ValueError("Privacy policy must be accepted (privacy_accepted must be True).")
        return v


class RbpcInquiryCreate(BaseModel):
    """Visitor inquiry submission request payload."""

    experience_slug: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Target experience offering slug.",
    )
    contact: RbpcContactIn
    preferred_date: Optional[date] = Field(
        default=None,
        description="Desired workshop/tour date (must be in the future).",
    )
    party_size: int = Field(
        default=1,
        ge=1,
        le=50,
        description="Number of participants (1-50).",
    )
    message: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Optional inquiry notes or dietary/accessibility requests.",
    )
    consent: RbpcConsentIn
    idempotency_key: str = Field(
        ...,
        min_length=16,
        max_length=128,
        description="Client-generated unique UUID or nonce preventing accidental duplicate submissions.",
    )

    @field_validator("consent")
    @classmethod
    def validate_explicit_consent(cls, v: RbpcConsentIn) -> RbpcConsentIn:
        if not v.accepted or not v.privacy_accepted:
            raise ValueError("Explicit consent and privacy policy must be accepted.")
        return v

    @field_validator("preferred_date")
    @classmethod
    def validate_preferred_date(cls, v: Optional[date]) -> Optional[date]:
        if v is not None and v < date.today():
            raise ValueError("Preferred date cannot be in the past.")
        return v

    @field_validator("idempotency_key")
    @classmethod
    def validate_idempotency_key(cls, v: str) -> str:
        if not v or not isinstance(v, str):
            raise ValueError("Idempotency key must be a valid client UUID.")
        cleaned = v.strip()
        raw = cleaned
        if raw.lower().startswith("idem-key-"):
            raw = raw[9:]
        elif raw.lower().startswith("uuid-"):
            raw = raw[5:]
        try:
            uuid_module.UUID(raw)
        except (ValueError, AttributeError, TypeError):
            raise ValueError("Idempotency key must be a valid client UUID.")
        return cleaned


class RbpcInquiryOut(BaseModel):
    """Immediate response upon inquiry submission containing tracking tokens."""

    model_config = ConfigDict(from_attributes=True)

    reference: str = Field(
        ...,
        description="Non-sequential public reference code (e.g. INQ-7F89-A23C).",
    )
    status_token: str = Field(
        ...,
        description="High-entropy secret token for anonymous status checks (stored on client).",
    )
    status: RbpcInquiryStatus = Field(
        default=RbpcInquiryStatus.new,
        description="Initial status: new.",
    )
    message: str = Field(
        default="Yêu cầu đã được ghi nhận. Nhà cung cấp sẽ liên hệ xác nhận lịch trống.",
        description="Honest receipt message.",
    )
    created_at: datetime


class RbpcInquiryStatusOut(BaseModel):
    """Public status inquiry output: ZERO PII returned."""

    model_config = ConfigDict(from_attributes=True)

    reference: str = Field(..., description="Non-sequential reference code.")
    experience_title: str = Field(..., description="Title of the requested experience.")
    status: RbpcInquiryStatus = Field(..., description="Current inquiry lifecycle state.")
    status_message: str = Field(
        ...,
        description="Human-readable explanation of the current status.",
    )
    preferred_date: Optional[date] = None
    party_size: Optional[int] = None
    last_updated_at: datetime


# --------------------------------------------------------------------------- #
# Partner Inbox & Management (Authenticated)
# --------------------------------------------------------------------------- #
class RbpcPartnerInquiryUpdate(BaseModel):
    """Partner action to advance or conclude the inquiry lifecycle."""

    status: RbpcInquiryStatus = Field(
        ...,
        description="Target status: contacted, confirmed, declined, closed.",
    )
    note: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Private internal partner note regarding the conversation.",
    )


class RbpcPartnerInquiryOut(BaseModel):
    """Partner-facing inquiry representation with contact details (provider-scoped)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    reference: str
    experience_slug: str
    experience_title: str
    contact_name: str
    contact_method: RbpcContactMethod
    contact_value: str
    preferred_date: Optional[date] = None
    party_size: int = 1
    message: Optional[str] = None
    status: RbpcInquiryStatus
    created_at: datetime
    updated_at: datetime


class RbpcPartnerInquiryListOut(BaseModel):
    """List of inquiries for an authenticated partner inbox."""

    items: list[RbpcPartnerInquiryOut]
    total: int


# --------------------------------------------------------------------------- #
# Impact Metrics (Strict Observed vs Projected Separation)
# --------------------------------------------------------------------------- #
class RbpcObservedMetrics(BaseModel):
    """Real, verified aggregate statistics observed in the database."""

    published_stories_count: int = Field(
        default=0,
        description="Total human-reviewed, source-grounded stories currently published.",
    )
    consented_creators_count: int = Field(
        default=0,
        description="Total living practitioners with verified written consent.",
    )
    active_experiences_count: int = Field(
        default=0,
        description="Total published experience listings open for inquiries.",
    )
    total_inquiries_received: int = Field(
        default=0,
        description="Total visitor inquiry requests logged.",
    )
    verified_heritage_places_count: int = Field(
        default=0,
        description="Total Huế heritage places catalogued with authoritative source citations.",
    )
    verified_source_citations_count: int = Field(
        default=0,
        description="Total bibliographic claims verified across the knowledge graph.",
    )
    sponsor_support_vnd_verified: float = Field(
        default=202360638.0,
        description="Total verified in-kind sponsorship value (VND) supported by signed documents (BNIX + Phổ Tuệ).",
    )


class RbpcProjectedMetrics(BaseModel):
    """Estimated forward-looking commercial and economic impact hypotheses."""

    estimated_monthly_demand: Optional[int] = Field(
        default=None,
        description="Projected qualified monthly visitor inquiry volume based on pilot conversion rates.",
    )
    projected_local_value_addition_vnd: Optional[float] = Field(
        default=None,
        description="Projected economic value directed to local artisan communities.",
    )
    projection_basis: str = Field(
        default="Các số liệu dự phóng là giả định mô hình kinh doanh phục vụ nghiên cứu và đề án RBPC 2026, không phải doanh thu đã ghi nhận.",
        description="Mandatory disclaimer distinguishing projection from observed financial results.",
    )


class RbpcImpactMetricsOut(BaseModel):
    """Complete impact reporting payload separating observed reality from forward projections."""

    model_config = ConfigDict(from_attributes=True)

    observed_metrics: RbpcObservedMetrics
    projected_metrics: RbpcProjectedMetrics
    scope: str = Field(default="RBPC_HUE")
    generated_at: datetime
