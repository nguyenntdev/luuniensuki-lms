# -*- coding: utf-8 -*-
"""Pricing experiment instrumentation services (Ticket V5-T117 / W11-A07)."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
from typing import Any, Optional
import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..apischemas.pricing import (
    PricingCalculatorIn,
    PricingCalculatorOut,
    PricingContractCreateIn,
    PricingContractSignAcceptIn,
    PricingExperimentConfigOut,
    PricingExperimentEventCreateIn,
    PricingExperimentMetricsSummaryOut,
    PricingTierInfo,
)
from ..models import (
    ContractStatus,
    PricingContract,
    PricingEventType,
    PricingExperimentEvent,
    PricingTierKey,
    User,
)

TIERS_CONFIG: list[PricingTierInfo] = [
    PricingTierInfo(
        key=PricingTierKey.pilot.value,
        name_vi="Gói Trường Học Thử Nghiệm",
        name_en="School Pilot Tier",
        description_vi="Khởi động 1 học kỳ miễn phí cho 100 học sinh trải nghiệm di sản Cửu Đỉnh.",
        description_en="1 semester pilot trial for 100 students exploring Nine Tripod Cauldrons.",
        base_price_vnd=0.0,
        billing_period="per_semester",
        features_vi=[
            "Tối đa 100 tài khoản học sinh",
            "Toàn quyền truy cập 162 phù điêu và thư viện nguồn sử liệu",
            "Bộ tài liệu in ấn 2D dập nổi đạt chuẩn UDL",
            "Báo cáo tiến độ chuẩn hóa Chương trình GDPT 2018",
        ],
        features_en=[
            "Up to 100 student accounts",
            "Full access to 162 motifs and source registry",
            "UDL-compliant 2D printable rubbings kit",
            "Competency alignment reports for 2018 Curriculum",
        ],
        is_popular=False,
    ),
    PricingTierInfo(
        key=PricingTierKey.standard_school.value,
        name_vi="Gói Trường Chuẩn Hóa",
        name_en="Standard School Tier",
        description_vi="Giải pháp toàn diện cho toàn trường học (500 - 2,000 học sinh) với trợ giảng AI.",
        description_en="Comprehensive solution for schools with source-grounded AI tutor.",
        base_price_vnd=25000000.0,  # 25,000,000 VND / year
        billing_period="per_year",
        features_vi=[
            "Lên đến 1,000 tài khoản học sinh & giáo viên",
            "Tích hợp AI Sử Gia Socratic có trích dẫn nguồn lưu trữ",
            "Sổ điểm số hóa và xuất chứng nhận di sản",
            "Hỗ trợ kỹ thuật giáo viên SLA 24 giờ",
        ],
        features_en=[
            "Up to 1,000 student & teacher accounts",
            "Socratic AI History Tutor with archival citations",
            "Digital gradebook and verifiable passport stamps",
            "24h SLA teacher technical support",
        ],
        is_popular=True,
    ),
    PricingTierInfo(
        key=PricingTierKey.district_enterprise.value,
        name_vi="Gói Cụm Trường & Sở Giáo Dục",
        name_en="District & Enterprise Tier",
        description_vi="Tùy biến cho phòng GD&ĐT / cụm trường học liên cấp với hạ tầng riêng.",
        description_en="Custom deployment for education districts and multi-campus networks.",
        base_price_vnd=75000000.0,  # 75,000,000 VND / year
        billing_period="per_year",
        features_vi=[
            "Không giới hạn số lượng học sinh và giáo viên",
            "Phân tích k-anonymity và so sánh tiến độ liên trường",
            "Tích hợp SSO giáo dục và cổng bảo tàng ảo VR360",
            "Chuyên viên sư phạm đồng hành trực tiếp tại trường",
        ],
        features_en=[
            "Unlimited students and teachers",
            "District-wide k-anonymity learning analytics",
            "Education SSO & VR360 virtual museum portal",
            "Dedicated pedagogical consultant on site",
        ],
        is_popular=False,
    ),
]


def get_pricing_experiment_config(variant_key: str = "control") -> PricingExperimentConfigOut:
    return PricingExperimentConfigOut(
        experiment_key="school_pricing_v1",
        variant_key=variant_key,
        consent_required=True,
        consent_policy_version="2026.1-pricing",
        consent_text_vi=(
            "Chúng tôi cam kết minh bạch 100%: Lựa chọn hoặc tính toán gói giá của bạn giúp cải thiện "
            "sản phẩm và hoàn toàn KHÔNG tự động tính phí, KHÔNG áp dụng dark patterns hay tự gia hạn."
        ),
        consent_text_en=(
            "100% Transparency Commitment: Pricing simulations are used solely for demand study. "
            "No automatic charges, no dark patterns, and no unapproved commitments."
        ),
        tiers=TIERS_CONFIG,
    )


def calculate_pricing_quote(payload: PricingCalculatorIn) -> PricingCalculatorOut:
    """Calculate estimate with non-binding guarantee."""
    # Base tier pricing calculation
    tier_base_annual = {
        PricingTierKey.pilot.value: 0.0,
        PricingTierKey.standard_school.value: 25000000.0,
        PricingTierKey.district_enterprise.value: 75000000.0,
        PricingTierKey.artisan_pro.value: 12000000.0,
    }.get(payload.tier_key, 25000000.0)

    # Scale factor per student above baseline 500
    additional_student_cost = 0.0
    if payload.tier_key != PricingTierKey.pilot.value and payload.student_count > 500:
        extra_students = payload.student_count - 500
        additional_student_cost = extra_students * 15000.0  # 15,000 VND/student/year

    annual_subtotal = tier_base_annual + additional_student_cost
    duration_factor = payload.months_duration / 12.0
    base_subtotal = annual_subtotal * duration_factor

    # Addons calculation
    addons = 0.0
    if payload.include_ai_tutor_credits:
        addons += payload.student_count * 5000.0 * duration_factor
    if payload.include_vr360_interactive_lab:
        addons += 5000000.0 * duration_factor
    if payload.include_teacher_training_pdu:
        addons += 3000000.0

    # Volume discount for scale
    volume_discount = 0.0
    if payload.student_count >= 2000:
        volume_discount = (base_subtotal + addons) * 0.15
    elif payload.student_count >= 1000:
        volume_discount = (base_subtotal + addons) * 0.10

    estimated_total = max(0.0, base_subtotal + addons - volume_discount)
    per_student_month = (
        estimated_total / (payload.student_count * max(1, payload.months_duration))
        if payload.student_count > 0 and payload.months_duration > 0
        else 0.0
    )

    return PricingCalculatorOut(
        tier_key=payload.tier_key,
        student_count=payload.student_count,
        months_duration=payload.months_duration,
        base_subtotal_vnd=round(base_subtotal, 2),
        addons_subtotal_vnd=round(addons, 2),
        volume_discount_vnd=round(volume_discount, 2),
        estimated_total_vnd=round(estimated_total, 2),
        per_student_month_vnd=round(per_student_month, 2),
        is_binding=False,
        revenue_recognized_vnd=0.0,  # STRICT INVARIANT: 0 VND recognized
    )


def record_pricing_event(
    db: Session,
    payload: PricingExperimentEventCreateIn,
    user_id: Optional[uuid.UUID] = None,
) -> PricingExperimentEvent:
    """Record pricing interest event enforcing strict negative-abuse invariant."""
    if not payload.has_experiment_consent:
        raise ValueError("CONSENT_REQUIRED: Recording pricing experiment telemetry requires explicit user consent.")

    if payload.event_type == PricingEventType.contract_accepted.value:
        raise ValueError("DIRECT_CONTRACT_ACCEPTED_PROHIBITED: Contracts must be formally executed via /contracts/{id}/accept.")

    # Negative abuse check: tier_view, calculator_interaction, quote_inquiry, contract_sign_attempt
    # NEVER count as paying customer or revenue.
    is_paying = False
    revenue = 0.0

    event = PricingExperimentEvent(
        user_id=user_id,
        anonymous_session_id=payload.anonymous_session_id,
        experiment_key=payload.experiment_key,
        variant_key=payload.variant_key,
        tier_key=payload.tier_key,
        event_type=payload.event_type,
        has_experiment_consent=payload.has_experiment_consent,
        consent_version=payload.consent_version,
        is_paying_customer=is_paying,
        revenue_impact_vnd=revenue,
        calculator_params=payload.calculator_params,
        client_metadata=payload.client_metadata,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def create_draft_contract(
    db: Session,
    payload: PricingContractCreateIn,
    signer_user: User,
) -> PricingContract:
    """Draft an institutional contract."""
    contract_number = f"EDU-{datetime.now(timezone.utc).year}-{uuid.uuid4().hex[:8].upper()}"
    contract = PricingContract(
        contract_number=contract_number,
        school_id=payload.school_id or getattr(signer_user, "school_id", None),
        organization_name=payload.organization_name,
        signer_user_id=signer_user.id,
        tier_key=payload.tier_key,
        variant_key=payload.variant_key,
        contract_value_vnd=payload.contract_value_vnd,
        student_seat_capacity=payload.student_seat_capacity,
        status=ContractStatus.pending_signature.value,
        terms_version=payload.terms_version,
    )
    db.add(contract)
    db.commit()
    db.refresh(contract)
    return contract


def accept_and_execute_contract(
    db: Session,
    contract_id: uuid.UUID,
    payload: PricingContractSignAcceptIn,
    current_user: User,
) -> PricingContract:
    """Execute real contract acceptance with dual attribution and cryptographic verification."""
    stmt = select(PricingContract).where(PricingContract.id == contract_id)
    contract = db.execute(stmt).scalar_one_or_none()
    if not contract:
        raise ValueError("CONTRACT_NOT_FOUND")

    if contract.status == ContractStatus.signed_and_executed.value:
        raise ValueError("CONTRACT_ALREADY_EXECUTED: Contract has already been signed and executed.")

    if contract.status == ContractStatus.cancelled.value:
        raise ValueError("CONTRACT_CANCELLED: Cannot sign a cancelled contract.")

    if not payload.confirmation_statement or not payload.confirmation_statement.strip():
        raise ValueError("CONFIRMATION_STATEMENT_REQUIRED: Acceptance statement is required.")

    if not payload.signer_legal_name or not payload.signer_legal_name.strip():
        raise ValueError("SIGNER_LEGAL_NAME_REQUIRED: Signer legal name is required.")

    # Authorize signer
    if contract.signer_user_id != current_user.id and current_user.role.value not in ("admin", "staff"):
        raise PermissionError("SIGNER_MISMATCH")

    # Cryptographic hash of acceptance
    now_utc = datetime.now(timezone.utc)
    raw_proof = (
        f"{contract.contract_number}:{current_user.id}:{payload.signer_legal_name}:"
        f"{contract.contract_value_vnd}:{now_utc.isoformat()}"
    )
    v_hash = hashlib.sha256(raw_proof.encode("utf-8")).hexdigest()
    ip_hash = (
        hashlib.sha256(payload.ip_address_masked.encode("utf-8")).hexdigest()
        if payload.ip_address_masked
        else None
    )

    contract.status = ContractStatus.signed_and_executed.value
    contract.signed_at = now_utc
    contract.verification_hash = v_hash
    contract.signature_ip_hash = ip_hash
    contract.metadata_json = {
        "confirmation_statement": payload.confirmation_statement,
        "signer_title": payload.signer_title,
        "signer_legal_name": payload.signer_legal_name,
        "terms_accepted": True,
    }

    # Record verified contract accepted event
    event = PricingExperimentEvent(
        user_id=current_user.id,
        experiment_key="school_pricing_v1",
        variant_key=contract.variant_key,
        tier_key=contract.tier_key,
        event_type=PricingEventType.contract_accepted.value,
        has_experiment_consent=True,
        consent_version=contract.terms_version,
        is_paying_customer=True,  # Legitimate paying customer
        revenue_impact_vnd=contract.contract_value_vnd,
        calculator_params={"contract_number": contract.contract_number},
    )
    db.add(event)
    db.commit()
    db.refresh(contract)
    return contract


def get_pricing_metrics_summary(
    db: Session,
    experiment_key: str = "school_pricing_v1",
) -> PricingExperimentMetricsSummaryOut:
    """Compute aggregate metrics verifying zero abuse from clicks."""
    # Count event types
    events = db.execute(
        select(
            PricingExperimentEvent.event_type,
            func.count(PricingExperimentEvent.id),
        )
        .where(PricingExperimentEvent.experiment_key == experiment_key)
        .group_by(PricingExperimentEvent.event_type)
    ).all()
    event_counts = {row[0]: row[1] for row in events}

    total_tier_views = event_counts.get(PricingEventType.tier_view.value, 0)
    total_calc = event_counts.get(PricingEventType.calculator_interaction.value, 0)
    total_quote = event_counts.get(PricingEventType.quote_inquiry.value, 0)
    total_attempts = event_counts.get(PricingEventType.contract_sign_attempt.value, 0)

    # Real signed contracts
    signed_contracts_stmt = select(
        func.count(PricingContract.id),
        func.coalesce(func.sum(PricingContract.contract_value_vnd), 0.0),
    ).where(PricingContract.status == ContractStatus.signed_and_executed.value)
    contracts_res = db.execute(signed_contracts_stmt).one()
    signed_count = contracts_res[0] or 0
    recognized_rev = float(contracts_res[1] or 0.0)

    # Verified paying customers count
    paying_users_stmt = select(
        func.count(func.distinct(PricingExperimentEvent.user_id))
    ).where(
        PricingExperimentEvent.experiment_key == experiment_key,
        PricingExperimentEvent.is_paying_customer == True,
    )
    paying_count = db.execute(paying_users_stmt).scalar() or 0

    return PricingExperimentMetricsSummaryOut(
        experiment_key=experiment_key,
        total_tier_views=total_tier_views,
        total_calculator_interactions=total_calc,
        total_quote_inquiries=total_quote,
        total_contract_attempts=total_attempts,
        signed_contracts_count=signed_count,
        paying_customers_count=paying_count,
        recognized_contract_revenue_vnd=recognized_rev,
        unearned_calculator_projected_value_vnd=0.0,
    )
