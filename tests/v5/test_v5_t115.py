# -*- coding: utf-8 -*-
"""V5-T115: Unit Economics Actual Ledger Test Suite.

Wave W11, Slot A05:
Goal: Unit economics actual ledger in docs/rbpc/FINANCIAL_ASSUMPTIONS.md and backend/routers/.
Cash actuals separated from GMV forecasts, cost structure inference (server, AI tokens, take rate),
school B2B separated from visitor commerce.
Negative abuse invariant: Partner inquiry creates 0 VND revenue without verified payment or settled transaction.

Audits and verifies:
1. Negative abuse test:
   - Creating or confirming inquiries produces EXACTLY 0 VND cash revenue and 0 VND realized GMV.
   - Unsettled inquiries are counted under pipeline forecasts with truth_tier="FORECAST".
   - Negative abuse verification payload confirms compliance.
2. Verified cash actuals from settled transactions:
   - Settlements in 'pending_compliance' status do NOT contribute to realized cash revenue.
   - Once approved by compliance reviewer, settlement contributes accurately to cash actuals
     (gross, platform fee, taxes, artisan payout).
3. Cost structure inference:
   - Server hosting: BNIX in-kind sponsorship, commercial replacement rate 95,200 VND/month.
   - AI token inference: Phổ Tuệ in-kind credits, commercial replacement rate 270 VND/inquiry.
   - Dual margin calculation: Sponsored runway cash margin (100%) vs Commercial shadow margin.
4. Revenue stream separation (visitor_commerce vs school_b2b):
   - Supports creating settlements with explicit revenue_stream classification.
   - Granular breakdown accurately segments visitor commerce from institutional school B2B.
   - Stream filtering via query parameter ?stream=school_b2b scopes results cleanly.
5. Multi-tenant security scoping:
   - Providers only see their own cash actuals and inquiries.
   - Admin/staff see global aggregate actuals.
   - Guest users are rejected with HTTP 403 FORBIDDEN.
6. Documentation parity:
   - Confirms docs/rbpc/FINANCIAL_ASSUMPTIONS.md contains Section 8 with full accounting firewalls.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
import pytest
from sqlalchemy import select

from backend.models import User, UserRole
from backend.models_rbpc import (
    RbpcConsentStatus,
    RbpcCreator,
    RbpcExperience,
    RbpcInquiry,
    RbpcInquiryStatus,
    RbpcPayoutStatus,
    RbpcRevenueStream,
    RbpcSettlementLedger,
    RbpcSettlementStatus,
)
from backend.security import hash_password


def _create_user(
    db_session,
    email: str,
    role: UserRole = UserRole.teacher,
    display_name: str | None = None,
) -> User:
    user = User(
        email=email,
        password_hash=hash_password("Password123!"),
        display_name=display_name or f"User {email.split('@')[0]}",
        username=f"usr_{uuid.uuid4().hex[:8]}",
        role=role,
        is_profile_public=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _login_user(client, email: str, password: str = "Password123!") -> dict:
    res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    return res.json()


def _setup_test_context(db_session, provider_user: User):
    creator = RbpcCreator(
        slug=f"artisan-ue-{uuid.uuid4().hex[:6]}",
        public_name="Nghệ nhân Đúc Đồng Huế",
        craft_tradition="Đúc đồng thủ công Cửu Đỉnh",
        approved_bio_vi="Gia đình 4 đời nghệ nhân đúc đồng Phường Đúc.",
        consent_status=RbpcConsentStatus.consented.value,
        is_verified=True,
    )
    db_session.add(creator)
    db_session.flush()

    exp = RbpcExperience(
        slug=f"exp-ue-{uuid.uuid4().hex[:6]}",
        title_vi="Trải nghiệm Đúc Đồng Phường Đúc",
        title_en="Phuong Duc Bronze Casting Experience",
        description_vi="Đúc và chạm khắc phù điêu đồng cổ.",
        creator_id=creator.id,
        provider_name="Xưởng Nghệ Nhân Huỳnh",
        provider_id=provider_user.id,
        indicative_price_amount=650000.0,
        currency="VND",
        duration_minutes=180,
        availability_mode="inquiry_only",
        publication_state="published",
    )
    db_session.add(exp)
    db_session.commit()
    db_session.refresh(creator)
    db_session.refresh(exp)
    return creator, exp


def _create_inquiry(
    db_session,
    exp: RbpcExperience,
    provider: User,
    state: str = "new",
    name: str = "Khách Hàng",
    party_size: int = 1,
) -> RbpcInquiry:
    inquiry = RbpcInquiry(
        public_ref=f"INQ-UE-{uuid.uuid4().hex[:6].upper()}",
        experience_id=exp.id,
        provider_id=provider.id,
        name=name,
        contact_channel="email",
        contact_value=f"{uuid.uuid4().hex[:6]}@example.com",
        desired_date=date.today(),
        party_size=party_size,
        message="Trải nghiệm đúc đồng di sản.",
        state=state,
        idempotency_key=f"idem_{uuid.uuid4().hex}",
        opaque_token=f"tok_{uuid.uuid4().hex}",
        retention_due_at=datetime.now(timezone.utc),
    )
    db_session.add(inquiry)
    db_session.commit()
    db_session.refresh(inquiry)
    return inquiry


def test_negative_abuse_partner_inquiry_produces_zero_revenue_without_settlement(client, db_session):
    """Negative Abuse Invariant (V5-T115):
    Merely submitting, contacting, or confirming an inquiry creates 0 VND revenue
    and 0 VND realized GMV in the unit economics actual ledger.
    """
    provider = _create_user(db_session, f"provider_abuse_{uuid.uuid4().hex[:6]}@example.com", UserRole.teacher)
    creator, exp = _setup_test_context(db_session, provider)

    # Create 3 inquiries in various lifecycle states: new, contacted, confirmed
    _create_inquiry(db_session, exp, provider, state="new", name="Nguyễn Văn A", party_size=2)
    _create_inquiry(db_session, exp, provider, state="contacted", name="Trần Thị B", party_size=4)
    _create_inquiry(db_session, exp, provider, state="confirmed", name="Lê Văn C", party_size=3)

    # Query unit economics actual ledger as provider
    _login_user(client, provider.email)
    res = client.get("/api/v1/rbpc/ledger/unit-economics")
    assert res.status_code == 200, res.text
    data = res.json()

    # Cash actuals MUST be strictly 0.0 VND
    cash = data["cash_actuals"]
    assert cash["total_settled_gross_vnd"] == 0.0
    assert cash["total_platform_fee_cash_vnd"] == 0.0
    assert cash["net_cash_revenue_vnd"] == 0.0
    assert cash["total_artisan_payout_vnd"] == 0.0
    assert cash["approved_settlements_count"] == 0
    assert cash["settled_settlements_count"] == 0

    # Negative abuse audit block verification
    abuse = data["negative_abuse"]
    assert abuse["unsettled_inquiries_count"] == 3
    assert abuse["unsettled_inquiries_cash_revenue_vnd"] == 0.0
    assert abuse["unsettled_inquiries_realized_gmv_vnd"] == 0.0
    assert abuse["is_compliant"] is True
    assert "0 VND revenue without verified payment" in abuse["rule"]

    # Forecasts block confirms pipeline intent is labeled FORECAST
    forecast = data["gmv_forecasts"]
    assert forecast["truth_tier"] == "FORECAST"
    assert forecast["unsettled_pipeline_inquiries_count"] == 3
    # Potential forecast: (2 + 4 + 3) * 650,000 = 9 * 650,000 = 5,850,000 VND
    assert forecast["pipeline_potential_gmv_forecast_vnd"] == 5850000.0


def test_verified_settlement_produces_cash_actuals_after_compliance(client, db_session):
    """Verified Settlement Lifecycle & Cash Actuals:
    1. Unapproved settlement in 'pending_compliance' status does not contribute to cash actuals.
    2. Once approved by compliance reviewer, settlement accurately registers cash actuals.
    """
    admin = _create_user(db_session, f"admin_ue_{uuid.uuid4().hex[:6]}@example.com", UserRole.admin)
    provider = _create_user(db_session, f"prov_settle_{uuid.uuid4().hex[:6]}@example.com", UserRole.teacher)
    creator, exp = _setup_test_context(db_session, provider)

    inquiry = _create_inquiry(db_session, exp, provider, state="confirmed", name="Hoàng Thị D", party_size=2)

    # Step 1: Provider records settlement for 1,300,000 VND (2 pax * 650k) with 10% take rate
    _login_user(client, provider.email)
    create_res = client.post(
        "/api/v1/rbpc/partner/settlements",
        json={
            "inquiry_id": str(inquiry.id),
            "gross_amount_vnd": 1300000.0,
            "take_rate": 0.1000,
            "vat_rate": 0.0800,
            "revenue_stream": "visitor_commerce",
            "transaction_proof_hash": "tx_proof_bank_transfer_001",
            "compliance_notes": "Completed weekend casting workshop with 2 guests",
        },
    )
    assert create_res.status_code == 201, create_res.text
    settlement_data = create_res.json()
    settlement_id = settlement_data["id"]
    assert settlement_data["status"] == "pending_compliance"

    # Before compliance approval: Cash actuals should still be 0.0 VND!
    ledger_res = client.get("/api/v1/rbpc/ledger/unit-economics")
    assert ledger_res.status_code == 200
    pre_approval_cash = ledger_res.json()["cash_actuals"]
    assert pre_approval_cash["total_settled_gross_vnd"] == 0.0
    assert pre_approval_cash["total_platform_fee_cash_vnd"] == 0.0
    assert pre_approval_cash["pending_settlements_count"] == 1

    # Step 2: Admin reviews and approves compliance
    _login_user(client, admin.email)
    review_res = client.post(
        f"/api/v1/rbpc/editor/settlements/{settlement_id}/compliance",
        json={"approved": True, "compliance_notes": "Verified attendee signed attendance sheet"},
    )
    assert review_res.status_code == 200, review_res.text
    assert review_res.json()["status"] == "approved"

    # Step 3: Now check unit economics actual ledger as provider
    _login_user(client, provider.email)
    ledger_res2 = client.get("/api/v1/rbpc/ledger/unit-economics")
    assert ledger_res2.status_code == 200
    data = ledger_res2.json()

    cash = data["cash_actuals"]
    assert cash["total_settled_gross_vnd"] == 1300000.0
    assert cash["total_platform_fee_cash_vnd"] == 130000.0  # 10% of 1.3M
    assert cash["total_tax_vat_vnd"] == 104000.0            # 8% of 1.3M
    assert cash["total_artisan_payout_vnd"] == 1066000.0    # 1.3M - 130k - 104k
    assert cash["net_cash_revenue_vnd"] == 130000.0
    assert cash["approved_settlements_count"] == 1
    assert cash["pending_settlements_count"] == 0


def test_cost_structure_inference_server_and_ai_tokens(client, db_session):
    """Cost Structure Inference (V5-T115):
    Verifies that the ledger infers server hosting costs (BNIX subsidy) and
    AI token costs (Phổ Tuệ subsidy), providing dual contribution margins.
    """
    admin = _create_user(db_session, f"admin_cost_{uuid.uuid4().hex[:6]}@example.com", UserRole.admin)
    provider = _create_user(db_session, f"prov_cost_{uuid.uuid4().hex[:6]}@example.com", UserRole.teacher)
    creator, exp = _setup_test_context(db_session, provider)

    inquiry = _create_inquiry(db_session, exp, provider, state="confirmed", name="Phạm Minh E", party_size=1)

    # Record and approve settlement: 650,000 VND gross, 10% fee = 65,000 VND
    settlement = RbpcSettlementLedger(
        settlement_ref=f"STL-TST-{uuid.uuid4().hex[:6].upper()}",
        inquiry_id=inquiry.id,
        provider_id=provider.id,
        creator_id=creator.id,
        gross_amount_vnd=650000.0,
        revenue_stream="visitor_commerce",
        take_rate=0.1000,
        platform_fee_vnd=65000.0,
        tax_vat_vnd=52000.0,
        artisan_payout_vnd=533000.0,
        refund_amount_vnd=0.0,
        status="approved",
        payout_status="approved",
        compliance_approved=True,
    )
    db_session.add(settlement)
    db_session.commit()

    _login_user(client, provider.email)
    res = client.get("/api/v1/rbpc/ledger/unit-economics")
    assert res.status_code == 200, res.text
    data = res.json()

    cost = data["cost_inference"]
    assert cost["server_cost_is_in_kind"] is True
    assert "BNIX" in cost["server_sponsor"]
    assert cost["inferred_server_cost_vnd"] == 95200.0

    assert cost["ai_token_cost_is_in_kind"] is True
    assert "Phổ Tuệ" in cost["ai_sponsor"]
    # 1 inquiry * 270 VND = 270 VND
    assert cost["inferred_ai_token_cost_vnd"] == 270.0

    assert cost["effective_take_rate"] == 0.1000
    assert cost["inferred_total_variable_cost_vnd"] == 95470.0  # 95,200 + 270

    # Sponsored Runway Contribution Margin: 100% cash retention (65,000 VND)
    assert cost["net_contribution_margin_sponsored_vnd"] == 65000.0
    assert cost["net_contribution_margin_sponsored_pct"] == 100.0

    # Commercial Shadow Contribution Margin: 65,000 - 95,470 = -30,470 VND
    assert cost["net_contribution_margin_commercial_vnd"] == -30470.0


def test_stream_separation_visitor_commerce_vs_school_b2b(client, db_session):
    """Revenue Stream Separation (V5-T115):
    Verifies that visitor cultural commerce and school B2B educational contracts
    are tracked in separate streams with distinct economics and filtering.
    """
    admin = _create_user(db_session, f"admin_stream_{uuid.uuid4().hex[:6]}@example.com", UserRole.admin)
    provider = _create_user(db_session, f"prov_stream_{uuid.uuid4().hex[:6]}@example.com", UserRole.teacher)
    creator, exp = _setup_test_context(db_session, provider)

    inq_visitor = _create_inquiry(db_session, exp, provider, state="confirmed", name="Khách Du Lịch", party_size=1)
    inq_school = _create_inquiry(db_session, exp, provider, state="confirmed", name="Trường THPT Quốc Học Huế", party_size=20)

    # Visitor commerce settlement: 650,000 VND, 10% fee = 65,000 VND
    stl_visitor = RbpcSettlementLedger(
        settlement_ref=f"STL-VIS-{uuid.uuid4().hex[:6].upper()}",
        inquiry_id=inq_visitor.id,
        provider_id=provider.id,
        creator_id=creator.id,
        gross_amount_vnd=650000.0,
        revenue_stream="visitor_commerce",
        take_rate=0.1000,
        platform_fee_vnd=65000.0,
        tax_vat_vnd=52000.0,
        artisan_payout_vnd=533000.0,
        status="settled",
        payout_status="disbursed",
        compliance_approved=True,
    )

    # School B2B settlement: 5,000,000 VND institutional cohort, 15% fee = 750,000 VND
    stl_school = RbpcSettlementLedger(
        settlement_ref=f"STL-SCH-{uuid.uuid4().hex[:6].upper()}",
        inquiry_id=inq_school.id,
        provider_id=provider.id,
        creator_id=creator.id,
        gross_amount_vnd=5000000.0,
        revenue_stream="school_b2b",
        take_rate=0.1500,
        platform_fee_vnd=750000.0,
        tax_vat_vnd=400000.0,
        artisan_payout_vnd=3850000.0,
        status="settled",
        payout_status="disbursed",
        compliance_approved=True,
    )
    db_session.add_all([stl_visitor, stl_school])
    db_session.commit()

    _login_user(client, provider.email)

    # 1. Query full unit economics report without stream filter
    res = client.get("/api/v1/rbpc/ledger/unit-economics")
    assert res.status_code == 200, res.text
    streams = res.json()["streams"]

    v_stream = streams["visitor_commerce"]
    assert v_stream["settled_gross_vnd"] == 650000.0
    assert v_stream["platform_fee_cash_vnd"] == 65000.0
    assert v_stream["transactions_count"] == 1
    assert v_stream["effective_take_rate"] == 0.1000

    s_stream = streams["school_b2b"]
    assert s_stream["settled_gross_vnd"] == 5000000.0
    assert s_stream["platform_fee_cash_vnd"] == 750000.0
    assert s_stream["transactions_count"] == 1
    assert s_stream["effective_take_rate"] == 0.1500

    # 2. Query with specific stream filter: ?stream=school_b2b
    filter_res = client.get("/api/v1/rbpc/ledger/unit-economics?stream=school_b2b")
    assert filter_res.status_code == 200
    filter_data = filter_res.json()
    assert filter_data["cash_actuals"]["total_settled_gross_vnd"] == 5000000.0
    assert filter_data["cash_actuals"]["total_platform_fee_cash_vnd"] == 750000.0


def test_multi_tenant_isolation_and_guest_forbidden(client, db_session):
    """Multi-Tenant Isolation & Role Authorization:
    1. Provider A cannot see Provider B's cash actuals.
    2. Admin/Staff sees combined aggregate.
    3. Guest user receives HTTP 403 FORBIDDEN.
    """
    admin = _create_user(db_session, f"admin_iso_{uuid.uuid4().hex[:6]}@example.com", UserRole.admin)
    prov_a = _create_user(db_session, f"prov_a_{uuid.uuid4().hex[:6]}@example.com", UserRole.teacher)
    prov_b = _create_user(db_session, f"prov_b_{uuid.uuid4().hex[:6]}@example.com", UserRole.teacher)
    guest = _create_user(db_session, f"guest_iso_{uuid.uuid4().hex[:6]}@example.com", UserRole.guest)

    _, exp_a = _setup_test_context(db_session, prov_a)
    _, exp_b = _setup_test_context(db_session, prov_b)

    inq_a = _create_inquiry(db_session, exp_a, prov_a, state="confirmed", name="Khách của A", party_size=1)
    inq_b = _create_inquiry(db_session, exp_b, prov_b, state="confirmed", name="Khách của B", party_size=1)

    # Settlement for A: 1,000,000 VND
    stl_a = RbpcSettlementLedger(
        settlement_ref=f"STL-A-{uuid.uuid4().hex[:6].upper()}",
        inquiry_id=inq_a.id,
        provider_id=prov_a.id,
        gross_amount_vnd=1000000.0,
        take_rate=0.1000,
        platform_fee_vnd=100000.0,
        artisan_payout_vnd=820000.0,
        tax_vat_vnd=80000.0,
        status="settled",
        payout_status="disbursed",
        compliance_approved=True,
    )
    # Settlement for B: 2,000,000 VND
    stl_b = RbpcSettlementLedger(
        settlement_ref=f"STL-B-{uuid.uuid4().hex[:6].upper()}",
        inquiry_id=inq_b.id,
        provider_id=prov_b.id,
        gross_amount_vnd=2000000.0,
        take_rate=0.1000,
        platform_fee_vnd=200000.0,
        artisan_payout_vnd=1640000.0,
        tax_vat_vnd=160000.0,
        status="settled",
        payout_status="disbursed",
        compliance_approved=True,
    )
    db_session.add_all([stl_a, stl_b])
    db_session.commit()

    # Provider A checks ledger: only sees 1,000,000 VND
    _login_user(client, prov_a.email)
    res_a = client.get("/api/v1/rbpc/ledger/unit-economics")
    assert res_a.status_code == 200
    assert res_a.json()["cash_actuals"]["total_settled_gross_vnd"] == 1000000.0

    # Provider B checks ledger: only sees 2,000,000 VND
    _login_user(client, prov_b.email)
    res_b = client.get("/api/v1/rbpc/ledger/unit-economics")
    assert res_b.status_code == 200
    assert res_b.json()["cash_actuals"]["total_settled_gross_vnd"] == 2000000.0

    # Admin checks ledger: sees aggregate sum of 3,000,000 VND
    _login_user(client, admin.email)
    res_admin = client.get("/api/v1/rbpc/ledger/unit-economics")
    assert res_admin.status_code == 200
    assert res_admin.json()["cash_actuals"]["total_settled_gross_vnd"] == 3000000.0

    # Guest user check: HTTP 403 Forbidden
    _login_user(client, guest.email)
    res_guest = client.get("/api/v1/rbpc/ledger/unit-economics")
    assert res_guest.status_code == 403


def test_documentation_parity_financial_assumptions():
    """Documentation Parity Check:
    Verifies that docs/rbpc/FINANCIAL_ASSUMPTIONS.md contains Section 8 with
    explicit cash actuals, cost inferences, and stream separation definitions.
    """
    from pathlib import Path
    doc_path = Path("docs/rbpc/FINANCIAL_ASSUMPTIONS.md")
    assert doc_path.exists(), "docs/rbpc/FINANCIAL_ASSUMPTIONS.md not found"

    content = doc_path.read_text(encoding="utf-8")
    assert "## 8. Unit Economics Actual Ledger" in content
    assert "V5-T115" in content
    assert "visitor_commerce" in content
    assert "school_b2b" in content
    assert "BNIX" in content
    assert "Phổ Tuệ" in content
    assert "Negative Abuse Invariant" in content
    assert "0 VND revenue without verified payment" in content
