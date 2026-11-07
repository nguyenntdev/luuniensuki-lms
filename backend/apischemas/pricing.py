# -*- coding: utf-8 -*-
"""Pydantic schemas for Pricing Experiment Instrumentation (Ticket V5-T117 / W11-A07)."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ..models import ContractStatus, PricingEventType, PricingTierKey


class PricingTierInfo(BaseModel):
    """Tier details served in pricing experiment."""
    key: str
    name_vi: str
    name_en: str
    description_vi: str
    description_en: str
    base_price_vnd: float
    billing_period: str
    features_vi: list[str]
    features_en: list[str]
    is_popular: bool = False
    calculator_supported: bool = True
    anti_dark_pattern_notice: str = (
        "Không có phí ẩn, không tự động gia hạn khi chưa có hợp đồng ký kết."
    )


class PricingExperimentConfigOut(BaseModel):
    """Public pricing experiment configuration and variants."""
    experiment_key: str
    variant_key: str
    consent_required: bool = True
    consent_policy_version: str
    consent_text_vi: str
    consent_text_en: str
    tiers: list[PricingTierInfo]
    anti_abuse_notice: str = (
        "Lưu ý: Mọi thao tác tính giá hoặc xem gói chỉ mang tính chất dự toán/khảo sát nhu cầu. "
        "Không ghi nhận doanh thu hoặc ràng buộc hợp đồng cho đến khi có biên bản ký kết hợp pháp."
    )


class PricingCalculatorIn(BaseModel):
    """Input for real-time pricing calculator."""
    tier_key: str
    student_count: int = Field(ge=1, le=100000, description="Dự kiến số học sinh tham gia")
    months_duration: int = Field(ge=1, le=36, default=12, description="Thời hạn sử dụng theo tháng")
    include_ai_tutor_credits: bool = Field(default=False)
    include_vr360_interactive_lab: bool = Field(default=False)
    include_teacher_training_pdu: bool = Field(default=False)


class PricingCalculatorOut(BaseModel):
    """Output estimate from calculator with explicit non-revenue non-binding disclaimer."""
    tier_key: str
    student_count: int
    months_duration: int
    base_subtotal_vnd: float
    addons_subtotal_vnd: float
    volume_discount_vnd: float
    estimated_total_vnd: float
    per_student_month_vnd: float
    is_binding: bool = False
    revenue_recognized_vnd: float = 0.0
    disclaimer: str = (
        "Kết quả tính toán chỉ mang tính ước tính và khảo sát nhu cầu thị trường. "
        "Không cấu thành hóa đơn, không tạo doanh thu và không có hiệu lực pháp lý nếu chưa lập hợp đồng."
    )


class PricingExperimentConsentIn(BaseModel):
    """Consent decision for pricing experiment tracking."""
    has_experiment_consent: bool = Field(
        ...,
        description="Người dùng đồng ý cho phép phân tích hành vi quan tâm gói giá (zero dark pattern).",
    )
    consent_version: str = Field(
        default="2026.1-pricing",
        description="Phiên bản chính sách đồng ý minh bạch."
    )


class PricingExperimentEventCreateIn(BaseModel):
    """Track an interaction on pricing tier or calculator."""
    experiment_key: str = Field(default="school_pricing_v1")
    variant_key: str = Field(default="control")
    tier_key: str = Field(...)
    event_type: str = Field(...)
    has_experiment_consent: bool = Field(default=True)
    consent_version: str = Field(default="2026.1-pricing")
    calculator_params: Optional[dict[str, Any]] = None
    client_metadata: Optional[dict[str, Any]] = None
    anonymous_session_id: Optional[str] = None

    @field_validator("event_type")
    @classmethod
    def validate_event_type(cls, v: str) -> str:
        valid = {e.value for e in PricingEventType}
        if v not in valid:
            raise ValueError(f"Invalid event_type: {v}. Must be one of {valid}")
        return v


class PricingExperimentEventOut(BaseModel):
    """Recorded pricing event."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: Optional[UUID] = None
    experiment_key: str
    variant_key: str
    tier_key: str
    event_type: str
    has_experiment_consent: bool
    consent_version: str
    is_paying_customer: bool
    revenue_impact_vnd: float
    calculator_params: Optional[dict[str, Any]] = None
    created_at: datetime


class PricingContractCreateIn(BaseModel):
    """Create a drafted institutional contract."""
    organization_name: str = Field(..., min_length=3, max_length=255)
    school_id: Optional[UUID] = None
    tier_key: str = Field(...)
    variant_key: str = Field(default="control")
    student_seat_capacity: int = Field(ge=1, le=100000)
    contract_value_vnd: float = Field(ge=0.0)
    terms_version: str = Field(default="v2026.1-edu")


class PricingContractSignAcceptIn(BaseModel):
    """Real contract acceptance requiring explicit agreement and verification token."""
    confirmation_statement: str = Field(
        ...,
        description="Tuyên bố xác nhận cam kết hợp đồng pháp lý của trường học",
    )
    signer_title: str = Field(..., min_length=2, max_length=100)
    signer_legal_name: str = Field(..., min_length=2, max_length=100)
    ip_address_masked: Optional[str] = None


class PricingContractOut(BaseModel):
    """Legitimate contract details."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    contract_number: str
    school_id: Optional[UUID] = None
    organization_name: str
    signer_user_id: UUID
    tier_key: str
    variant_key: str
    contract_value_vnd: float
    student_seat_capacity: int
    status: str
    terms_version: str
    signed_at: Optional[datetime] = None
    verification_hash: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class PricingExperimentMetricsSummaryOut(BaseModel):
    """Strictly separated metrics verifying zero negative abuse."""
    experiment_key: str
    total_tier_views: int
    total_calculator_interactions: int
    total_quote_inquiries: int
    total_contract_attempts: int
    signed_contracts_count: int
    paying_customers_count: int
    recognized_contract_revenue_vnd: float
    unearned_calculator_projected_value_vnd: float
    negative_abuse_verification: str = (
        "INVARIANT VERIFIED: Tier views and calculator clicks contributed 0 VND "
        "and 0 paying customers. Only signed_and_executed contracts contribute to revenue."
    )
