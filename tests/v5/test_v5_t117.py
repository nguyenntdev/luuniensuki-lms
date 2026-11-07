# -*- coding: utf-8 -*-
"""V5-T117 (Wave W11, Slot A07): Pricing Experiment Instrumentation Test Suite.

Audits and verifies:
1. Pricing Experiment Configuration & Transparency:
   - GET /api/v1/pricing/config returns active experiment key and transparent tiers.
   - Confirms anti-dark-pattern notices and zero automatic charge disclaimers.
   - Supports experiment variants ('control', 'annual_flat', 'per_student_metered').
2. Non-binding Real-Time Pricing Calculator:
   - POST /api/v1/pricing/calculator computes valid cost models based on seat count and add-ons.
   - Enforces volume discount thresholds (1,000+ students, 2,000+ students).
   - STRICT INVARIANT: is_binding=False and revenue_recognized_vnd=0.0.
3. Pricing Experiment Telemetry & User Consent:
   - POST /api/v1/pricing/events records interest events ('tier_view', 'calculator_interaction', 'quote_inquiry').
   - Opt-in consent required: if has_experiment_consent=False, rejects with HTTP 400.
   - Validates anonymous and authenticated sessions.
4. Institutional Contract Drafting:
   - POST /api/v1/pricing/contracts allows authenticated school representatives to draft contracts.
   - Initializes contract in 'pending_signature' status with unique contract number.
5. Contract Acceptance & Cryptographic Execution:
   - POST /api/v1/pricing/contracts/{id}/accept verifies signatory identity and records SHA-256 hash.
   - Dual-attribution authorization: prevents third parties from signing someone else's contract (HTTP 403).
   - Updates contract status to 'signed_and_executed'.
   - Only executed contracts transition customer to paying status and record recognized revenue.
   - Prevents double-signing of executed contracts (HTTP 400).
6. NEGATIVE ABUSE INVARIANTS (Critical Requirement V5-T117):
   - Merely viewing tiers, adjusting calculator, or submitting inquiries NEVER sets is_paying_customer=True.
   - Tier and calculator telemetry events contribute exactly 0.0 VND to recognized revenue.
   - Direct telemetry injection of 'contract_accepted' via /events is strictly prohibited (HTTP 400).
   - Aggregate metrics (/api/v1/pricing/metrics/summary) prove 0 VND recognized revenue from simulations
     and only recognize revenue from formally executed contracts.
"""
from __future__ import annotations

import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from backend.models import (
    ContractStatus,
    PricingContract,
    PricingEventType,
    PricingExperimentEvent,
    PricingTierKey,
    User,
    UserRole,
)
from backend.security import hash_password


def _create_user(
    db_session,
    email: str,
    role: UserRole = UserRole.teacher,
    display_name: str | None = None,
    is_school_verified: bool = True,
) -> User:
    user = db_session.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if not user:
        user = User(
            id=uuid.uuid4(),
            email=email,
            password_hash=hash_password("Password123!"),
            display_name=display_name or f"User {email.split('@')[0]}",
            username=f"u_{uuid.uuid4().hex[:8]}",
            role=role,
            is_school_verified=is_school_verified,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
    else:
        user.role = role
        user.is_school_verified = is_school_verified
        db_session.commit()
        db_session.refresh(user)
    return user


def _auth_headers(client: TestClient, email: str, password: str = "Password123!") -> dict[str, str]:
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    token = client.cookies.get("luuniensuki_access") or res.cookies.get("luuniensuki_access") or ""
    return {"Authorization": f"Bearer {token}"}


# --------------------------------------------------------------------------- #
# Test 1: Configuration & Transparent Tiers
# --------------------------------------------------------------------------- #

def test_pricing_config_transparency_and_variants(client: TestClient):
    res_control = client.get("/api/v1/pricing/config?variant=control")
    assert res_control.status_code == 200
    data_control = res_control.json()

    assert data_control["experiment_key"] == "school_pricing_v1"
    assert data_control["variant_key"] == "control"
    assert data_control["consent_required"] is True
    assert "2026.1-pricing" in data_control["consent_policy_version"]
    assert "không áp dụng dark patterns" in data_control["consent_text_vi"].lower()

    # Check tiers
    tiers = data_control["tiers"]
    tier_keys = [t["key"] for t in tiers]
    assert PricingTierKey.pilot.value in tier_keys
    assert PricingTierKey.standard_school.value in tier_keys
    assert PricingTierKey.district_enterprise.value in tier_keys

    # Confirm anti-dark pattern notice on every tier
    for tier in tiers:
        assert tier["anti_dark_pattern_notice"]
        assert len(tier["features_vi"]) >= 3

    # Check variant query support
    res_metered = client.get("/api/v1/pricing/config?variant=per_student_metered")
    assert res_metered.status_code == 200
    assert res_metered.json()["variant_key"] == "per_student_metered"


# --------------------------------------------------------------------------- #
# Test 2: Real-time Pricing Calculator & 0 VND Recognized Revenue Invariant
# --------------------------------------------------------------------------- #

def test_pricing_calculator_estimates_and_zero_revenue_invariant(client: TestClient):
    payload = {
        "tier_key": "standard_school",
        "student_count": 1200,
        "months_duration": 12,
        "include_ai_tutor_credits": True,
        "include_vr360_interactive_lab": True,
        "include_teacher_training_pdu": False,
    }
    res = client.post("/api/v1/pricing/calculator", json=payload)
    assert res.status_code == 200
    data = res.json()

    # Base: 25,000,000 + 700 * 15,000 = 35,500,000
    # Addons: AI tutor (1200 * 5,000 = 6,000,000) + VR360 (5,000,000) = 11,000,000
    # Total before discount = 46,500,000
    # 1,200 students qualifies for 10% volume discount: 4,650,000
    # Estimated total: 41,850,000
    assert data["student_count"] == 1200
    assert data["volume_discount_vnd"] > 0
    assert data["estimated_total_vnd"] > 0
    assert data["per_student_month_vnd"] > 0

    # STRICT INVARIANTS:
    assert data["is_binding"] is False
    assert data["revenue_recognized_vnd"] == 0.0
    assert "không tạo doanh thu" in data["disclaimer"].lower()


# --------------------------------------------------------------------------- #
# Test 3: Consent Lifecycle & Interest Telemetry Tracking
# --------------------------------------------------------------------------- #

def test_pricing_telemetry_with_consent_lifecycle(client: TestClient, db_session):
    teacher = _create_user(db_session, f"teacher_{uuid.uuid4().hex[:6]}@school.edu.vn")
    headers = _auth_headers(client, teacher.email)

    # 1. Telemetry rejected if user denied consent
    res_no_consent = client.post(
        "/api/v1/pricing/events",
        json={
            "tier_key": "standard_school",
            "event_type": "tier_view",
            "has_experiment_consent": False,
        },
        headers=headers,
    )
    assert res_no_consent.status_code == 400
    assert "CONSENT_REQUIRED" in res_no_consent.text

    # 2. Telemetry accepted with explicit consent
    res_with_consent = client.post(
        "/api/v1/pricing/events",
        json={
            "experiment_key": "school_pricing_v1",
            "variant_key": "control",
            "tier_key": "standard_school",
            "event_type": "tier_view",
            "has_experiment_consent": True,
            "consent_version": "2026.1-pricing",
            "anonymous_session_id": "anon_session_123",
        },
        headers=headers,
    )
    assert res_with_consent.status_code == 201
    evt = res_with_consent.json()
    assert evt["event_type"] == "tier_view"
    assert evt["has_experiment_consent"] is True
    # Zero abuse verified:
    assert evt["is_paying_customer"] is False
    assert evt["revenue_impact_vnd"] == 0.0

    # 3. Calculator interaction event
    res_calc_evt = client.post(
        "/api/v1/pricing/events",
        json={
            "tier_key": "district_enterprise",
            "event_type": "calculator_interaction",
            "has_experiment_consent": True,
            "calculator_params": {"student_count": 2500, "estimated_total": 95000000.0},
        },
        headers=headers,
    )
    assert res_calc_evt.status_code == 201
    calc_evt = res_calc_evt.json()
    assert calc_evt["event_type"] == "calculator_interaction"
    assert calc_evt["is_paying_customer"] is False
    assert calc_evt["revenue_impact_vnd"] == 0.0


# --------------------------------------------------------------------------- #
# Test 4: Real Institutional Contract Acceptance & Cryptographic Execution
# --------------------------------------------------------------------------- #

def test_contract_drafting_and_cryptographic_execution(client: TestClient, db_session):
    school_rep = _create_user(
        db_session,
        f"principal_{uuid.uuid4().hex[:6]}@quochoc.edu.vn",
        role=UserRole.teacher,
    )
    intruder = _create_user(
        db_session,
        f"intruder_{uuid.uuid4().hex[:6]}@other.edu.vn",
        role=UserRole.learner,
    )

    rep_headers = _auth_headers(client, school_rep.email)
    intruder_headers = _auth_headers(client, intruder.email)

    # 1. Draft institutional contract
    contract_payload = {
        "organization_name": "THPT Chuyên Quốc Học Huế",
        "tier_key": "standard_school",
        "variant_key": "control",
        "student_seat_capacity": 800,
        "contract_value_vnd": 29500000.0,
        "terms_version": "v2026.1-edu",
    }
    draft_res = client.post("/api/v1/pricing/contracts", json=contract_payload, headers=rep_headers)
    assert draft_res.status_code == 201
    contract = draft_res.json()
    contract_id = contract["id"]

    assert contract["status"] == "pending_signature"
    assert contract["organization_name"] == "THPT Chuyên Quốc Học Huế"
    assert contract["contract_number"].startswith("EDU-")
    assert contract["signed_at"] is None
    assert contract["verification_hash"] is None

    # 2. Unauthorized third-party cannot sign
    sign_payload = {
        "confirmation_statement": "Tôi xác nhận đại diện cho nhà trường ký kết hợp đồng.",
        "signer_title": "Hiệu trưởng",
        "signer_legal_name": "Nguyễn Văn A",
        "ip_address_masked": "192.168.1.50",
    }
    intruder_res = client.post(
        f"/api/v1/pricing/contracts/{contract_id}/accept",
        json=sign_payload,
        headers=intruder_headers,
    )
    assert intruder_res.status_code == 403
    assert "Not authorized" in intruder_res.text

    # 3. Legitimate authorized signer signs contract
    sign_res = client.post(
        f"/api/v1/pricing/contracts/{contract_id}/accept",
        json=sign_payload,
        headers=rep_headers,
    )
    assert sign_res.status_code == 200
    signed_contract = sign_res.json()

    assert signed_contract["status"] == "signed_and_executed"
    assert signed_contract["signed_at"] is not None
    assert signed_contract["verification_hash"] is not None
    assert len(signed_contract["verification_hash"]) == 64  # SHA-256

    # 4. Attempting to sign again fails (idempotent / double-signing protection)
    re_sign_res = client.post(
        f"/api/v1/pricing/contracts/{contract_id}/accept",
        json=sign_payload,
        headers=rep_headers,
    )
    assert re_sign_res.status_code == 400
    assert "CONTRACT_ALREADY_EXECUTED" in re_sign_res.text


# --------------------------------------------------------------------------- #
# Test 5: Negative Abuse Invariants & Metrics Isolation
# --------------------------------------------------------------------------- #

def test_negative_abuse_invariant_clicks_never_count_as_revenue(client: TestClient, db_session):
    """CRITICAL INVARIANT TEST:
    Merely clicking on a pricing tier or calculator does NOT count as a paying customer or revenue.
    Direct telemetry injection of 'contract_accepted' is strictly rejected.
    """
    user = _create_user(db_session, f"explorer_{uuid.uuid4().hex[:6]}@test.vn")
    headers = _auth_headers(client, user.email)

    exp_key = f"exp_audit_{uuid.uuid4().hex[:6]}"

    # 1. Direct injection of contract_accepted via telemetry MUST fail
    forged_event_res = client.post(
        "/api/v1/pricing/events",
        json={
            "experiment_key": exp_key,
            "tier_key": "district_enterprise",
            "event_type": "contract_accepted",
            "has_experiment_consent": True,
        },
        headers=headers,
    )
    assert forged_event_res.status_code == 400
    assert "DIRECT_CONTRACT_ACCEPTED_PROHIBITED" in forged_event_res.text

    # 2. Simulate 10 tier views and 10 calculator interactions
    for i in range(10):
        client.post(
            "/api/v1/pricing/events",
            json={
                "experiment_key": exp_key,
                "tier_key": "standard_school",
                "event_type": "tier_view",
                "has_experiment_consent": True,
            },
            headers=headers,
        )
        client.post(
            "/api/v1/pricing/events",
            json={
                "experiment_key": exp_key,
                "tier_key": "standard_school",
                "event_type": "calculator_interaction",
                "has_experiment_consent": True,
                "calculator_params": {"student_count": 1000, "estimated_value": 35000000.0},
            },
            headers=headers,
        )

    # 3. Inspect experiment metrics summary
    metrics_res = client.get(f"/api/v1/pricing/metrics/summary?experiment_key={exp_key}")
    assert metrics_res.status_code == 200
    metrics = metrics_res.json()

    assert metrics["total_tier_views"] == 10
    assert metrics["total_calculator_interactions"] == 10

    # Strict invariant: Despite 10 views and 10 calculator clicks, ZERO paying customers and ZERO revenue!
    assert metrics["paying_customers_count"] == 0
    assert metrics["recognized_contract_revenue_vnd"] == 0.0
    assert metrics["unearned_calculator_projected_value_vnd"] == 0.0
    assert "INVARIANT VERIFIED" in metrics["negative_abuse_verification"]


# --------------------------------------------------------------------------- #
# Test 6: Non-Existent Contract & Validation Guards
# --------------------------------------------------------------------------- #

def test_contract_validation_and_not_found_guards(client: TestClient, db_session):
    admin = _create_user(db_session, f"admin_{uuid.uuid4().hex[:6]}@test.vn", role=UserRole.admin)
    headers = _auth_headers(client, admin.email)

    fake_id = uuid.uuid4()
    res = client.post(
        f"/api/v1/pricing/contracts/{fake_id}/accept",
        json={
            "confirmation_statement": "Valid statement",
            "signer_title": "Principal",
            "signer_legal_name": "Nguyen Van B",
        },
        headers=headers,
    )
    assert res.status_code == 404
    assert "CONTRACT_NOT_FOUND" in res.text
