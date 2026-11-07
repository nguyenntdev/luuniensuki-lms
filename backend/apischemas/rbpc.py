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


class RbpcSettlementStatus(str, Enum):
    pending_compliance = "pending_compliance"
    approved = "approved"
    settled = "settled"
    refunded = "refunded"
    disputed = "disputed"


class RbpcPayoutStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    disbursed = "disbursed"
    withheld = "withheld"
    cancelled = "cancelled"


class RbpcRevenueStream(str, Enum):
    visitor_commerce = "visitor_commerce"
    school_b2b = "school_b2b"


class RbpcReviewStatus(str, Enum):
    pending_moderation = "pending_moderation"
    published = "published"
    rejected = "rejected"
    disputed = "disputed"
    archived = "archived"


class RbpcDisputeStatus(str, Enum):
    opened = "opened"
    under_review = "under_review"
    resolved_upheld = "resolved_upheld"
    resolved_overturned = "resolved_overturned"
    dismissed = "dismissed"


class RbpcSlotStatus(str, Enum):
    open = "open"
    closed = "closed"
    cancelled = "cancelled"


class RbpcReservationStatus(str, Enum):
    pending = "pending"
    confirmed = "confirmed"
    expired = "expired"
    cancelled = "cancelled"


class RbpcAudioConsentScope(str, Enum):
    full_public = "full_public"
    educational_only = "educational_only"
    preview_only = "preview_only"
    revoked = "revoked"


class RbpcOralHistoryStatus(str, Enum):
    draft = "draft"
    submitted = "submitted"
    consented = "consented"
    revoked = "revoked"
    erased = "erased"



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
    is_verified: bool = Field(
        default=False,
        description="Whether staff/admin has reviewed identity, consent, and rights.",
    )
    verification_notes: Optional[str] = Field(
        default=None,
        description="Verification audit comments.",
    )
    identity_document_ref: Optional[str] = Field(
        default=None,
        description="Encrypted/redacted reference to verified identity document.",
    )
    rights_clearance_notes: Optional[str] = Field(
        default=None,
        description="Rights clearance and portrait usage permissions.",
    )
    verified_at: Optional[datetime] = None
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


class RbpcPartnerOnboardingIn(BaseModel):
    """Self-onboarding registration payload for a partner/artisan."""

    slug: str = Field(..., min_length=3, max_length=100, description="Unique URL slug.")
    public_name: str = Field(..., min_length=2, max_length=200, description="Artisan or workshop name.")
    craft_tradition_vi: str = Field(..., min_length=2, max_length=200, description="Traditional craft name in Vietnamese.")
    craft_tradition_en: Optional[str] = Field(None, max_length=200)
    approved_bio_vi: str = Field(..., min_length=10, max_length=5000, description="Biography or craft history.")
    approved_bio_en: Optional[str] = Field(None, max_length=5000)
    approved_portrait_url: Optional[str] = Field(None, max_length=1000, description="Portrait URL (unverified until staff review).")
    public_region: str = Field(default="Huế", max_length=100)
    years_of_practice: Optional[int] = Field(None, ge=0, le=100)
    generation_lineage: Optional[str] = Field(None, max_length=200)
    heritage_place_slug: Optional[str] = Field(None, max_length=100)
    display_consent_ref: Optional[str] = Field(None, max_length=200, description="Reference to consent agreement.")
    identity_document_ref: Optional[str] = Field(None, max_length=200, description="Identity documentation reference.")
    rights_clearance_notes: Optional[str] = Field(None, max_length=1000, description="Rights and portrait licensing notes.")


class RbpcPartnerProfileUpdateIn(BaseModel):
    """Artisan profile update payload for existing partner."""

    public_name: Optional[str] = Field(None, min_length=2, max_length=200)
    craft_tradition_vi: Optional[str] = Field(None, min_length=2, max_length=200)
    craft_tradition_en: Optional[str] = Field(None, max_length=200)
    approved_bio_vi: Optional[str] = Field(None, min_length=10, max_length=5000)
    approved_bio_en: Optional[str] = Field(None, max_length=5000)
    approved_portrait_url: Optional[str] = Field(None, max_length=1000)
    public_region: Optional[str] = Field(None, max_length=100)
    years_of_practice: Optional[int] = Field(None, ge=0, le=100)
    generation_lineage: Optional[str] = Field(None, max_length=200)
    display_consent_ref: Optional[str] = Field(None, max_length=200)
    identity_document_ref: Optional[str] = Field(None, max_length=200)
    rights_clearance_notes: Optional[str] = Field(None, max_length=1000)


class RbpcPartnerVerificationIn(BaseModel):
    """Staff review & verification payload for artisan profile."""

    is_verified: bool = Field(..., description="Staff decision on identity and consent verification.")
    consent_status: Optional[RbpcConsentStatus] = Field(
        default=RbpcConsentStatus.verified_written_consent,
        description="Verified consent state.",
    )
    verification_notes: Optional[str] = Field(None, max_length=1000, description="Review remarks and verification evidence.")
    rights_clearance_notes: Optional[str] = Field(None, max_length=1000, description="Licensing and media clearance remarks.")


class RbpcPartnerExperienceCreateIn(BaseModel):
    """Partner submission to create a cultural experience listing."""

    slug: str = Field(..., min_length=3, max_length=100)
    title_vi: str = Field(..., min_length=3, max_length=255)
    title_en: Optional[str] = Field(None, max_length=255)
    description_vi: str = Field(..., min_length=10, max_length=5000)
    description_en: Optional[str] = Field(None, max_length=5000)
    area_public: str = Field(default="Huế", max_length=100)
    duration_minutes: Optional[int] = Field(None, ge=15, le=1440)
    pricing_display: Optional[str] = Field(None, max_length=100)
    indicative_price_amount: Optional[float] = Field(None, ge=0)
    currency: str = Field(default="VND", max_length=10)
    max_party_size: Optional[int] = Field(default=10, ge=1, le=50)
    languages_supported: list[str] = Field(default_factory=lambda: ["vi"])
    notice: Optional[str] = Field(None, max_length=500)


class RbpcExperienceModerationIn(BaseModel):
    """Staff moderation payload for experience listing."""

    publication_state: str = Field(..., pattern="^(published|draft|archived|rejected)$")
    rights_checked: bool = Field(default=True, description="Confirm all media and brand rights cleared.")
    moderation_notes: Optional[str] = Field(None, max_length=1000)


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
    rights_checked: bool = Field(
        default=False,
        description="Whether licensing and intellectual rights have been cleared.",
    )
    moderation_notes: Optional[str] = Field(
        default=None,
        description="Staff moderation audit notes.",
    )
    moderated_at: Optional[datetime] = None


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
        pattern="^(vi|en|fr|ja|ko)$",
        description="Desired response locale (vi, en, fr, ja, ko).",
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
    email_opt_in: bool = Field(
        default=True,
        description="Whether visitor opts in to receive status update notifications via email.",
    )
    sms_opt_in: bool = Field(
        default=False,
        description="Whether visitor opts in to receive SMS alerts for urgent confirmations or changes.",
    )
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
    # Customer Notification Center Fields (V5-T103)
    email_opt_in: bool = Field(default=True, description="Email status update preference.")
    sms_opt_in: bool = Field(default=False, description="SMS notification preference.")
    is_overdue: bool = Field(default=False, description="True if partner SLA (24h) is overdue without action.")
    sla_due_at: Optional[datetime] = Field(default=None, description="24h partner SLA deadline.")
    can_escalate: bool = Field(default=False, description="True if customer can escalate late response.")
    escalated_at: Optional[datetime] = Field(default=None, description="Timestamp of partner escalation if triggered.")
    escalation_reason: Optional[str] = Field(default=None, description="Reason recorded for escalation.")
    escalation_count: int = Field(default=0, description="Total number of escalations triggered.")


class RbpcInquiryNotificationPreferenceUpdate(BaseModel):
    """Update opt-in preferences for customer notifications."""

    email_opt_in: Optional[bool] = Field(default=None, description="Opt in or out of email updates.")
    sms_opt_in: Optional[bool] = Field(default=None, description="Opt in or out of SMS updates.")
    frequency: Optional[str] = Field(default="immediate", description="Digest frequency (immediate, daily).")


class RbpcInquiryNotificationPreferenceOut(BaseModel):
    """Result of updating notification preferences."""

    reference: str
    email_opt_in: bool
    sms_opt_in: bool
    unsubscribed: bool
    message: str
    updated_at: datetime


class RbpcInquiryEscalationCreate(BaseModel):
    """Customer request to escalate a late partner response."""

    reason: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Reason customer is escalating (e.g. overdue 24h SLA, urgent travel plan).",
    )


class RbpcInquiryEscalationOut(BaseModel):
    """Result of partner late response escalation."""

    reference: str
    status: RbpcInquiryStatus
    escalated_at: datetime
    escalation_count: int
    sla_overdue_seconds: float
    message: str
    notification_dispatched: bool


class RbpcInquiryWithdrawOut(BaseModel):
    """Visitor response when inquiry consent is withdrawn and contact details redacted."""

    model_config = ConfigDict(from_attributes=True)

    reference: str = Field(..., description="Non-sequential reference code.")
    experience_title: str = Field(
        default="Trải nghiệm văn hóa",
        description="Title of the requested experience.",
    )
    status: RbpcInquiryStatus = Field(
        default=RbpcInquiryStatus.closed,
        description="Current inquiry lifecycle state (closed).",
    )
    status_message: str = Field(
        default="Đồng thuận đã được rút lại. Toàn bộ thông tin liên hệ đã được ẩn danh/xóa bỏ.",
        description="Human-readable explanation of the withdrawal status.",
    )
    privacy_accepted: bool = Field(
        default=False,
        description="Consent acceptance flag (False following withdrawal).",
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
    completed_experiences_count: int = Field(
        default=0,
        description="Total verified completed cultural experiences observed from real closed inquiries.",
    )
    artisan_payout_vnd_settled: float = Field(
        default=0.0,
        description="Total verified actual artisan payouts settled through the financial ledger (VND).",
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


# --------------------------------------------------------------------------- #
# Fee & Revenue Settlement Ledger Schemas (V5-T108)
# --------------------------------------------------------------------------- #
class RbpcSettlementCreate(BaseModel):
    """Create a verified settlement record for an inquiry with contracted take rate."""

    inquiry_id: UUID = Field(..., description="ID of the confirmed inquiry")
    gross_amount_vnd: float = Field(..., ge=0.0, description="Gross transacted amount in VND")
    revenue_stream: Optional[RbpcRevenueStream] = Field(
        default=RbpcRevenueStream.visitor_commerce,
        description="Revenue stream category ('visitor_commerce' or 'school_b2b')",
    )
    take_rate: Optional[float] = Field(
        default=0.1500,
        ge=0.0,
        le=1.0,
        description="Contracted platform take rate (e.g. 0.15 for 15%)",
    )
    vat_rate: Optional[float] = Field(
        default=0.0800,
        ge=0.0,
        le=0.20,
        description="Applicable tax/VAT rate (default 8% for cultural services)",
    )
    transaction_proof_hash: Optional[str] = Field(
        default=None,
        description="Cryptographic or banking reference/hash proof of payment",
    )
    compliance_notes: Optional[str] = Field(
        default=None,
        description="Initial notes or justification for the settlement",
    )


class RbpcSettlementComplianceReview(BaseModel):
    """Compliance approval or rejection of a settlement."""

    approved: bool = Field(..., description="True if approved for payout, False if rejected/held")
    compliance_notes: Optional[str] = Field(default=None, description="Compliance reviewer notes")


class RbpcSettlementRefund(BaseModel):
    """Process a partial or full refund against a settlement."""

    refund_amount_vnd: float = Field(..., gt=0.0, description="Amount to refund in VND")
    reason: str = Field(..., description="Reason for refund")


class RbpcSettlementOut(BaseModel):
    """Detailed settlement ledger record."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    settlement_ref: str
    inquiry_id: UUID
    provider_id: Optional[UUID] = None
    creator_id: Optional[UUID] = None
    gross_amount_vnd: float
    revenue_stream: str = "visitor_commerce"
    take_rate: float
    platform_fee_vnd: float
    tax_vat_vnd: float
    artisan_payout_vnd: float
    refund_amount_vnd: float
    status: RbpcSettlementStatus
    payout_status: RbpcPayoutStatus
    compliance_approved: bool
    compliance_reviewer_id: Optional[UUID] = None
    compliance_reviewed_at: Optional[datetime] = None
    compliance_notes: Optional[str] = None
    transaction_proof_hash: Optional[str] = None
    currency: str = "VND"
    disbursed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class RbpcSettlementListOut(BaseModel):
    """List of settlements."""

    items: list[RbpcSettlementOut]
    total: int


class RbpcLedgerFinancialSummary(BaseModel):
    """Aggregate financial summary from the verified settlement ledger."""

    total_gross_settled_vnd: float = Field(default=0.0, description="Total gross settled transaction volume")
    total_platform_fee_vnd: float = Field(default=0.0, description="Total platform fee earned")
    total_tax_vat_vnd: float = Field(default=0.0, description="Total taxes collected/remitted")
    total_artisan_payout_vnd: float = Field(default=0.0, description="Total net payout allocated to artisans")
    total_refund_vnd: float = Field(default=0.0, description="Total refunded amount")
    approved_settlements_count: int = Field(default=0, description="Number of compliance-approved settlements")
    pending_settlements_count: int = Field(default=0, description="Settlements awaiting compliance")
    contracted_take_rate_avg: float = Field(default=0.15, description="Weighted or average contracted take rate")


# --------------------------------------------------------------------------- #
# Unit Economics Actual Ledger Schemas (V5-T115 / W11-A05)
# --------------------------------------------------------------------------- #
class RbpcCashActuals(BaseModel):
    """Realized cash actuals strictly aggregated from approved/settled transactions."""

    total_settled_gross_vnd: float = Field(default=0.0, description="Gross transacted amount settled in VND")
    total_platform_fee_cash_vnd: float = Field(default=0.0, description="Actual cash platform fees collected")
    total_artisan_payout_vnd: float = Field(default=0.0, description="Cash allocated/disbursed to artisans")
    total_tax_vat_vnd: float = Field(default=0.0, description="Taxes and VAT remitted/collected")
    total_refunds_vnd: float = Field(default=0.0, description="Total cash refunds processed")
    net_cash_revenue_vnd: float = Field(default=0.0, description="Net cash platform revenue after refunds")
    approved_settlements_count: int = Field(default=0, description="Number of compliance-approved settlements")
    settled_settlements_count: int = Field(default=0, description="Number of fully settled/disbursed transactions")
    pending_settlements_count: int = Field(default=0, description="Settlements awaiting compliance review")


class RbpcGmvForecasts(BaseModel):
    """GMV and pipeline forecasts explicitly separated from cash actuals."""

    unsettled_pipeline_inquiries_count: int = Field(default=0, description="Inquiries with zero settled cash")
    pipeline_potential_gmv_forecast_vnd: float = Field(default=0.0, description="Pipeline potential GMV forecast")
    annual_som_target_gmv_vnd: float = Field(default=570000000.0, description="SOM Year 1 Target GMV (570M VND)")
    annual_som_target_revenue_vnd: float = Field(default=57000000.0, description="SOM Year 1 Target Net Revenue (57M VND)")
    forecast_realization_rate: float = Field(default=0.0, description="Ratio of realized gross to SOM target")
    truth_tier: str = Field(default="FORECAST", description="Epistemic truth tier: strictly FORECAST")
    epistemic_notice: str = Field(
        default="Cash actuals require verified settlement records. Inquiries and pipeline forecasts are model estimates and contribute strictly 0 VND cash to recognized revenue.",
        description="Epistemic disclosure regarding forecasts",
    )


class RbpcCostStructureInference(BaseModel):
    """Inferred cost structure covering server hosting, AI tokens, and take rates."""

    inferred_server_cost_vnd: float = Field(default=0.0, description="Commercial server replacement cost")
    server_cost_is_in_kind: bool = Field(default=True, description="True if subsidized by in-kind corporate sponsor")
    server_sponsor: str = Field(default="BNIX (Dedicated Cloud VPS, Value: 1,142,400 VND)", description="Hosting sponsor")
    inferred_ai_token_cost_vnd: float = Field(default=0.0, description="Commercial AI token replacement cost")
    ai_token_cost_is_in_kind: bool = Field(default=True, description="True if subsidized by in-kind AI credits")
    ai_sponsor: str = Field(default="Phổ Tuệ (AI API Credits: $7,610 USD / 201,218,238 VND)", description="AI sponsor")
    effective_take_rate: float = Field(default=0.1000, description="Realized or contracted platform take rate")
    inferred_total_variable_cost_vnd: float = Field(default=0.0, description="Sum of inferred server and AI compute costs")
    net_contribution_margin_sponsored_vnd: float = Field(default=0.0, description="Cash contribution margin under sponsored runway")
    net_contribution_margin_sponsored_pct: float = Field(default=0.0, description="Cash contribution margin percentage")
    net_contribution_margin_commercial_vnd: float = Field(default=0.0, description="Commercial contribution margin deducting replacement costs")
    net_contribution_margin_commercial_pct: float = Field(default=0.0, description="Commercial contribution margin percentage")


class RbpcStreamEconomics(BaseModel):
    """Granular unit economics for an individual revenue stream."""

    stream: str = Field(..., description="Revenue stream key ('visitor_commerce' or 'school_b2b')")
    settled_gross_vnd: float = Field(default=0.0, description="Gross settled transaction volume in VND")
    platform_fee_cash_vnd: float = Field(default=0.0, description="Cash platform fee collected in VND")
    artisan_payout_vnd: float = Field(default=0.0, description="Artisan payout in VND")
    tax_vat_vnd: float = Field(default=0.0, description="Tax and VAT in VND")
    refund_amount_vnd: float = Field(default=0.0, description="Refund amount in VND")
    transactions_count: int = Field(default=0, description="Count of settled transactions")
    average_order_value_vnd: float = Field(default=0.0, description="Average transaction order value")
    effective_take_rate: float = Field(default=0.1000, description="Realized take rate for this stream")
    unsettled_inquiries_count: int = Field(default=0, description="Unsettled pipeline inquiries in this stream")
    pipeline_forecast_gmv_vnd: float = Field(default=0.0, description="Pipeline potential GMV forecast in VND")


class RbpcNegativeAbuseVerification(BaseModel):
    """Auditable proof that unverified inquiries generate zero recognized revenue."""

    unsettled_inquiries_count: int = Field(default=0, description="Count of inquiries with no settled payment")
    unsettled_inquiries_cash_revenue_vnd: float = Field(default=0.0, description="Strictly 0.0 VND cash recognized")
    unsettled_inquiries_realized_gmv_vnd: float = Field(default=0.0, description="Strictly 0.0 VND realized GMV recognized")
    rule: str = Field(
        default="Partner inquiry creates 0 VND revenue without verified payment or settled transaction.",
        description="Negative abuse invariant rule",
    )
    is_compliant: bool = Field(default=True, description="True if invariant holds with zero leakage")


class RbpcUnitEconomicsActualLedger(BaseModel):
    """Complete unit economics actual ledger report."""

    generated_at: datetime = Field(..., description="Timestamp of report generation")
    currency: str = Field(default="VND", description="Accounting currency")
    cash_actuals: RbpcCashActuals
    gmv_forecasts: RbpcGmvForecasts
    cost_inference: RbpcCostStructureInference
    streams: dict[str, RbpcStreamEconomics]
    negative_abuse: RbpcNegativeAbuseVerification


# --------------------------------------------------------------------------- #
# Verified Customer Reviews & Disputes Schemas (V5-T107)
# --------------------------------------------------------------------------- #
class RbpcCustomerReviewCreate(BaseModel):
    """Customer payload to submit a verified review for a completed inquiry."""

    inquiry_token: str = Field(
        ...,
        min_length=16,
        max_length=255,
        description="Opaque status token of the inquiry proving possession and completion.",
    )
    rating: int = Field(
        ...,
        ge=1,
        le=5,
        description="Rating from 1 (lowest) to 5 (highest).",
    )
    title: str = Field(
        ...,
        min_length=3,
        max_length=200,
        description="Short summary or headline of the experience review.",
    )
    comment: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        description="Detailed review of the workshop experience.",
    )
    author_display_name: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Public author alias. If omitted, uses inquiry contact name or anonymous format.",
    )


class RbpcCustomerReviewModeration(BaseModel):
    """Staff/admin action to moderate a review (publish, reject, archive)."""

    status: RbpcReviewStatus = Field(
        ...,
        description="Target review status: published, rejected, archived.",
    )
    notes: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Staff moderation audit reasoning.",
    )


class RbpcReviewDisputeCreate(BaseModel):
    """Partner or visitor filing a dispute against a published or pending review."""

    reason: str = Field(
        ...,
        min_length=10,
        max_length=1000,
        description="Specific reason for contesting the review (e.g. defamation, factually inaccurate, unexperienced).",
    )
    evidence_payload: dict[str, Any] = Field(
        default_factory=dict,
        description="Structured supporting evidence or documentation.",
    )


class RbpcReviewDisputeResolution(BaseModel):
    """Staff/admin resolution of a review dispute."""

    status: RbpcDisputeStatus = Field(
        ...,
        description="Resolution status: resolved_upheld (review overturned), resolved_overturned (dispute rejected, review stays), dismissed.",
    )
    notes: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Formal resolution notes and reasoning.",
    )


class RbpcReviewDisputeOut(BaseModel):
    """Dispute record representation."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    review_id: UUID
    disputant_user_id: Optional[UUID] = None
    reason: str
    evidence_payload: dict[str, Any]
    status: RbpcDisputeStatus
    resolved_by_id: Optional[UUID] = None
    resolution_notes: Optional[str] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class RbpcCustomerReviewOut(BaseModel):
    """Public customer review representation with verified badge and zero PII."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    experience_id: UUID
    experience_slug: Optional[str] = None
    author_display_name: str
    rating: int
    title: str
    comment: str
    verified_completed: bool
    status: RbpcReviewStatus
    created_at: datetime
    updated_at: datetime


class RbpcCustomerReviewAdminOut(BaseModel):
    """Internal moderation view of a review with fraud flags and inquiry linkage."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    inquiry_id: UUID
    experience_id: UUID
    author_user_id: Optional[UUID] = None
    author_display_name: str
    rating: int
    title: str
    comment: str
    verified_completed: bool
    status: RbpcReviewStatus
    fraud_flags: dict[str, Any]
    moderated_by_id: Optional[UUID] = None
    moderated_at: Optional[datetime] = None
    moderation_notes: Optional[str] = None
    disputes: list[RbpcReviewDisputeOut] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class RbpcCustomerReviewListOut(BaseModel):
    """List of customer reviews."""

    items: list[RbpcCustomerReviewOut]
    total: int
    average_rating: float = 0.0


class RbpcCustomerReviewAdminListOut(BaseModel):
    """Moderation list of customer reviews."""

    items: list[RbpcCustomerReviewAdminOut]
    total: int
    pending_count: int = 0


# --------------------------------------------------------------------------- #
# Workshop Availability Inventory & Calendar Schemas (V5-T102)
# --------------------------------------------------------------------------- #
class RbpcWorkshopSlotOut(BaseModel):
    """Workshop calendar time slot with seat capacity metrics."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    experience_id: UUID
    start_time: datetime
    end_time: datetime
    capacity: int = Field(..., ge=1, le=100)
    reserved_seats: int = Field(default=0, ge=0)
    confirmed_seats: int = Field(default=0, ge=0)
    available_seats: int = Field(..., ge=0)
    status: str = Field(default="open")
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class RbpcAvailabilityCalendarOut(BaseModel):
    """Calendar schedule of workshop slots for an experience."""

    experience_slug: str
    experience_title: str
    slots: list[RbpcWorkshopSlotOut]
    total_slots: int


class RbpcSlotCreateIn(BaseModel):
    """Partner payload to open a new workshop slot."""

    experience_slug: str = Field(..., min_length=2, max_length=160)
    start_time: datetime
    end_time: datetime
    capacity: int = Field(default=10, ge=1, le=100)
    notes: Optional[str] = None


class RbpcSeatReserveIn(BaseModel):
    """Visitor payload to temporarily reserve seats in a workshop slot."""

    slot_id: UUID
    seats: int = Field(default=1, ge=1, le=10)
    customer_name: str = Field(..., min_length=2, max_length=120)
    customer_contact: str = Field(..., min_length=5, max_length=120)
    hold_timeout_seconds: int = Field(default=900, ge=60, le=1800)
    idempotency_key: Optional[str] = None
    inquiry_id: Optional[UUID] = None


class RbpcSeatReservationOut(BaseModel):
    """Receipt for a seat reservation or booking hold."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    public_ref: str
    slot_id: UUID
    experience_slug: Optional[str] = None
    seats: int
    status: str
    expires_at: datetime
    remaining_seconds: int
    customer_name: str
    customer_contact: str
    confirmed_at: Optional[datetime] = None
    message: str = "Thao tác thành công."
    created_at: datetime


class RbpcReservationConfirmIn(BaseModel):
    """Partner action to confirm a reserved seat hold."""

    reservation_id: UUID
    partner_note: Optional[str] = None


class RbpcReservationCancelIn(BaseModel):
    """Partner or visitor action to cancel/release a reservation."""

    reservation_id: UUID
    reason: Optional[str] = None


# --------------------------------------------------------------------------- #
# Oral History & Consent Studio Schemas (V5-T109)
# --------------------------------------------------------------------------- #
class RbpcTranscriptCue(BaseModel):
    """Timecoded narration cue segment."""

    time_sec: float = Field(..., ge=0.0, description="Start time cue in seconds.")
    end_time_sec: Optional[float] = Field(default=None, ge=0.0, description="Optional cue end time in seconds.")
    text: str = Field(..., min_length=1, description="Narration text segment.")
    speaker: Optional[str] = Field(default=None, description="Speaker name or attribution.")
    section_title: Optional[str] = Field(default=None, description="Section or thematic title.")


class RbpcAudioTranscriptVersionOut(BaseModel):
    """Audio transcript revision record."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    recording_id: UUID
    version_number: int
    transcript_text_vi: str
    transcript_text_en: Optional[str] = None
    timed_cues: list[RbpcTranscriptCue] = Field(default_factory=list)
    change_summary: Optional[str] = None
    author_id: Optional[UUID] = None
    is_verified_by_artisan: bool = False
    artisan_verified_at: Optional[datetime] = None
    created_at: datetime


class RbpcOralHistoryRecordingOut(BaseModel):
    """Oral history recording public / partner view."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    creator_id: UUID
    recording_code: str
    title_vi: str
    title_en: Optional[str] = None
    audio_url: Optional[str] = None
    audio_sha256: Optional[str] = None
    audio_duration_seconds: int
    mime_type: str
    cultural_context_vi: str
    cultural_context_en: Optional[str] = None
    recording_date: Optional[date] = None
    recording_location: Optional[str] = None
    interviewer_name: Optional[str] = None
    epistemic_certainty: str
    consent_scope: RbpcAudioConsentScope
    status: RbpcOralHistoryStatus
    consent_granted: bool
    consent_agreement_ref: Optional[str] = None
    consent_granted_at: Optional[datetime] = None
    consent_notes: Optional[str] = None
    revoked_at: Optional[datetime] = None
    revocation_reason: Optional[str] = None
    erased_at: Optional[datetime] = None
    current_version_number: int
    created_at: datetime
    updated_at: datetime
    latest_transcript: Optional[RbpcAudioTranscriptVersionOut] = None


class RbpcOralHistoryRecordingListOut(BaseModel):
    """List of oral history recordings."""

    items: list[RbpcOralHistoryRecordingOut]
    total: int


class RbpcOralHistoryCreateIn(BaseModel):
    """Create a new oral history recording draft."""

    creator_id: UUID
    title_vi: str = Field(..., min_length=2, max_length=255)
    title_en: Optional[str] = Field(default=None, max_length=255)
    audio_url: Optional[str] = Field(default=None, max_length=1000)
    audio_sha256: Optional[str] = Field(default=None, max_length=64)
    audio_duration_seconds: int = Field(default=0, ge=0)
    mime_type: str = Field(default="audio/webm")
    cultural_context_vi: str = Field(..., min_length=10)
    cultural_context_en: Optional[str] = None
    recording_date: Optional[date] = None
    recording_location: Optional[str] = None
    interviewer_name: Optional[str] = None
    epistemic_certainty: Optional[str] = "community_tradition"
    initial_transcript_vi: Optional[str] = None
    initial_transcript_en: Optional[str] = None
    initial_cues: list[RbpcTranscriptCue] = Field(default_factory=list)


class RbpcOralHistoryTranscriptUpdateIn(BaseModel):
    """Submit a new version of the transcript with diff/summary."""

    transcript_text_vi: str = Field(..., min_length=5)
    transcript_text_en: Optional[str] = None
    timed_cues: list[RbpcTranscriptCue] = Field(default_factory=list)
    change_summary: Optional[str] = Field(default=None, max_length=500)
    verify_by_artisan: bool = False


class RbpcOralHistoryConsentUpdateIn(BaseModel):
    """Update per-use media consent scope and grant agreement."""

    consent_scope: RbpcAudioConsentScope
    consent_granted: bool
    consent_agreement_ref: Optional[str] = Field(default=None, max_length=255)
    consent_notes: Optional[str] = Field(default=None, max_length=1000)


class RbpcOralHistoryRevokeIn(BaseModel):
    """Revoke consent or request erasure (right-to-erasure / GDPR / Decree 13/2023/ND-CP)."""

    reason: str = Field(..., min_length=5, max_length=1000)
    erase_data: bool = Field(
        default=False,
        description="Whether to scrub media references and text under right-to-erasure.",
    )


# --------------------------------------------------------------------------- #
# Startup Evidence Room & Pitch Review Schemas (V5-T120 / W11-A10)
# --------------------------------------------------------------------------- #
class RbpcEvidencePointerOut(BaseModel):
    """Versioned evidence pointer representation."""

    model_config = ConfigDict(from_attributes=True)

    pointer_id: str
    domain: str
    title: str
    doc_ref: str
    version: str
    status: str
    hash_sha256: str
    metrics_payload: dict[str, Any] = Field(default_factory=dict)
    summary: str
    owner: str
    verified_at: datetime
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class RbpcEvidencePointerListOut(BaseModel):
    """List of evidence room pointers with metadata."""

    items: list[RbpcEvidencePointerOut]
    total: int
    domains_covered: list[str]


class RbpcPitchClaimIn(BaseModel):
    """Input claim to be audited for pitch review."""

    claim_text: str = Field(..., min_length=3, max_length=1000)
    domain: str = Field(default="product")
    evidence_pointer_id: Optional[str] = None
    metric_key: Optional[str] = None
    claimed_value: Optional[Any] = None
    is_quantitative: bool = True
    truth_tier: Optional[str] = Field(default="OBSERVED")


class RbpcPitchReviewIn(BaseModel):
    """Payload to evaluate and audit a pitch deck against evidence room."""

    pitch_deck_title: str = Field(..., min_length=2, max_length=255)
    deck_version: str = Field(default="1.0.0", max_length=50)
    claims: list[RbpcPitchClaimIn] = Field(..., min_length=1)


class RbpcPitchClaimFindingOut(BaseModel):
    """Individual claim audit finding."""

    claim_text: str
    domain: str
    evidence_pointer_id: Optional[str]
    status: str
    is_grounded: bool
    discrepancy_notes: Optional[str] = None
    verified_metric_value: Optional[Any] = None
    claimed_metric_value: Optional[Any] = None


class RbpcPitchReviewOut(BaseModel):
    """Pitch review evaluation audit report."""

    model_config = ConfigDict(from_attributes=True)

    audit_ref: str
    pitch_deck_title: str
    deck_version: str
    total_claims_audited: int
    verified_claims_count: int
    ungrounded_claims_count: int
    pitch_readiness: str
    claims_payload: list[dict[str, Any]] = Field(default_factory=list)
    audit_findings: dict[str, Any] = Field(default_factory=dict)
    reviewed_at: datetime


class RbpcEvidenceRoomExportOut(BaseModel):
    """Evidence room due diligence export."""

    format: str
    content: str
    total_pointers: int
    domains_covered: list[str]




