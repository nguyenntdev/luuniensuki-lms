# -*- coding: utf-8 -*-
"""V5-T108: Fee/revenue ledger with actual confirmation Test Suite.

Wave W10, Slot A08:
Contracted take rate, actual recorded amounts, refunds, taxes, and artisan payouts after compliance approval.
Negative abuse invariant: Merely changing inquiry status to 'confirmed' produces zero revenue in financial ledger without verified settlement.

Audits and verifies:
1. Negative abuse test:
   - Setting inquiry status to 'confirmed' alone produces 0 revenue in the financial ledger.
   - An inquiry in 'new' or 'contacted' status rejected from creating a settlement (400 RBPC_INQUIRY_NOT_CONFIRMED).
2. Verified settlement creation:
   - Creating a settlement for a confirmed inquiry correctly calculates:
     * Platform fee based on contracted take_rate (e.g. 15% -> 0.1500)
     * Tax/VAT based on applicable tax rate (e.g. 8% -> 0.0800)
     * Net artisan payout = gross - platform_fee - tax_vat
   - Default status is 'pending_compliance' and payout_status is 'pending'.
3. Compliance approval & artisan payout workflow:
   - Non-staff user attempting compliance review receives 403 FORBIDDEN_SCOPE.
   - Editor/admin approves compliance -> status transitions to 'approved', payout_status to 'approved'.
   - Attempting payout disbursement without compliance approval is rejected (400 RBPC_PAYOUT_NOT_APPROVED).
   - Staff disburses payout -> status transitions to 'settled', payout_status to 'disbursed', recording timestamp.
4. Refund workflow & arithmetic:
   - Partial refund recalculates fees and deductions accurately.
   - Excess refund rejected (400 RBPC_REFUND_EXCEEDS_GROSS).
   - Full refund transitions status to 'refunded' and payout_status to 'cancelled'.
5. Multi-tenant security scoping:
   - Non-staff provider only sees own settlements; cannot access other provider's settlements (403 FORBIDDEN_SCOPE).
6. Ledger summary endpoint (/api/v1/rbpc/ledger/summary):
   - Correctly aggregates settled and approved gross, fees, taxes, payouts, and refunds.
   - Confirms zero fake revenue before explicit settlement.
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
        slug=f"artisan-ledger-{uuid.uuid4().hex[:6]}",
        public_name="Nghệ nhân Đúc Đồng Ý Yên",
        craft_tradition="Đúc đồng thủ công",
        approved_bio_vi="Gia đình 4 đời nghệ nhân đúc đồng.",
        consent_status=RbpcConsentStatus.consented.value,
        is_verified=True,
    )
    db_session.add(creator)
    db_session.flush()

    exp = RbpcExperience(
        slug=f"exp-ledger-{uuid.uuid4().hex[:6]}",
        title_vi="Trải nghiệm Đúc Đồng Lễ Hội",
        title_en="Bronze Casting Festival Experience",
        description_vi="Tham gia đúc chuông và hoa văn đồng cổ.",
        creator_id=creator.id,
        provider_name="Xưởng Nghệ Nhân Huỳnh",
        provider_id=provider_user.id,
        publication_state="published",
        availability_mode="inquiry_only",
    )
    db_session.add(exp)
    db_session.flush()

    inquiry = RbpcInquiry(
        public_ref=f"INQ-LEDGER-{uuid.uuid4().hex[:4].upper()}",
        experience_id=exp.id,
        provider_id=provider_user.id,
        name="Đoàn Du Khách Tràng An",
        contact_channel="email",
        contact_value="trangan.group@example.com",
        desired_date=date.today(),
        party_size=4,
        message="Muốn tìm hiểu quy trình đúc đỉnh đồng.",
        state=RbpcInquiryStatus.new.value,
        idempotency_key=f"idem-ledger-{uuid.uuid4().hex}",
        opaque_token=f"tok-ledger-{uuid.uuid4().hex}",
        privacy_accepted=True,
    )
    db_session.add(inquiry)
    db_session.commit()
    db_session.refresh(inquiry)
    return creator, exp, inquiry


def test_negative_abuse_confirmed_status_alone_produces_zero_revenue(client, db_session):
    """Negative Abuse Invariant: Transitioning inquiry to 'confirmed' alone produces 0 VND revenue."""
    provider = _create_user(db_session, "provider_abuse@example.com", role=UserRole.teacher)
    creator, exp, inquiry = _setup_test_context(db_session, provider)

    _login_user(client, provider.email)

    # 1. Advance inquiry to 'contacted' then 'confirmed'
    res1 = client.patch(
        f"/api/v1/rbpc/partner/inquiries/{inquiry.id}",
        json={"status": "contacted", "note": "Đã gọi điện thoại"},
    )
    assert res1.status_code == 200

    res2 = client.patch(
        f"/api/v1/rbpc/partner/inquiries/{inquiry.id}",
        json={"status": "confirmed", "note": "Đã xác nhận thời gian"},
    )
    assert res2.status_code == 200
    assert res2.json()["status"] == "confirmed"

    # 2. Query financial ledger summary: MUST BE ZERO
    summary_res = client.get("/api/v1/rbpc/ledger/summary")
    assert summary_res.status_code == 200
    summary = summary_res.json()
    assert summary["total_gross_settled_vnd"] == 0.0
    assert summary["total_platform_fee_vnd"] == 0.0
    assert summary["total_artisan_payout_vnd"] == 0.0
    assert summary["approved_settlements_count"] == 0

    # 3. Verify no records exist in DB table rbpc_settlement_ledger
    settlements = list(db_session.scalars(select(RbpcSettlementLedger).where(RbpcSettlementLedger.inquiry_id == inquiry.id)))
    assert len(settlements) == 0


def test_unconfirmed_inquiry_cannot_create_settlement(client, db_session):
    """An inquiry in 'new' or 'contacted' cannot be settled."""
    provider = _create_user(db_session, "provider_unconf@example.com", role=UserRole.teacher)
    creator, exp, inquiry = _setup_test_context(db_session, provider)

    _login_user(client, provider.email)

    # Attempt settlement on 'new' inquiry
    res = client.post(
        "/api/v1/rbpc/partner/settlements",
        json={
            "inquiry_id": str(inquiry.id),
            "gross_amount_vnd": 2500000.0,
            "take_rate": 0.15,
        },
    )
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "RBPC_INQUIRY_NOT_CONFIRMED"


def test_verified_settlement_creation_and_contracted_take_rate(client, db_session):
    """Settlement records contracted take rate, platform fee, taxes, and artisan payout."""
    provider = _create_user(db_session, "provider_settle@example.com", role=UserRole.teacher)
    creator, exp, inquiry = _setup_test_context(db_session, provider)

    _login_user(client, provider.email)

    # Transition inquiry to confirmed
    client.patch(f"/api/v1/rbpc/partner/inquiries/{inquiry.id}", json={"status": "contacted"})
    client.patch(f"/api/v1/rbpc/partner/inquiries/{inquiry.id}", json={"status": "confirmed"})

    gross = 5000000.0  # 5,000,000 VND
    take_rate = 0.15   # 15%
    vat_rate = 0.08    # 8%

    # Create settlement
    create_res = client.post(
        "/api/v1/rbpc/partner/settlements",
        json={
            "inquiry_id": str(inquiry.id),
            "gross_amount_vnd": gross,
            "take_rate": take_rate,
            "vat_rate": vat_rate,
            "transaction_proof_hash": "sha256-vietqr-transfer-sample-12345",
            "compliance_notes": "Thanh toán cọc 100% qua chuyển khoản ngân hàng",
        },
    )
    assert create_res.status_code == 201
    settlement = create_res.json()

    assert settlement["gross_amount_vnd"] == 5000000.0
    assert settlement["take_rate"] == 0.15
    assert settlement["platform_fee_vnd"] == 750000.0  # 5,000,000 * 0.15
    assert settlement["tax_vat_vnd"] == 400000.0       # 5,000,000 * 0.08
    assert settlement["artisan_payout_vnd"] == 3850000.0  # 5,000,000 - 750,000 - 400,000
    assert settlement["status"] == "pending_compliance"
    assert settlement["payout_status"] == "pending"
    assert settlement["compliance_approved"] is False


def test_compliance_approval_and_artisan_payout_lifecycle(client, db_session):
    """Artisan payout requires explicit compliance approval before disbursement."""
    provider = _create_user(db_session, "provider_payout@example.com", role=UserRole.teacher)
    staff = _create_user(db_session, "staff_compliance@example.com", role=UserRole.admin)
    creator, exp, inquiry = _setup_test_context(db_session, provider)

    _login_user(client, provider.email)
    client.patch(f"/api/v1/rbpc/partner/inquiries/{inquiry.id}", json={"status": "contacted"})
    client.patch(f"/api/v1/rbpc/partner/inquiries/{inquiry.id}", json={"status": "confirmed"})

    settle_res = client.post(
        "/api/v1/rbpc/partner/settlements",
        json={
            "inquiry_id": str(inquiry.id),
            "gross_amount_vnd": 3000000.0,
            "take_rate": 0.12,
            "vat_rate": 0.08,
        },
    )
    settlement_id = settle_res.json()["id"]

    # 1. Provider attempts compliance approval -> 403 Forbidden
    non_staff_review = client.post(
        f"/api/v1/rbpc/editor/settlements/{settlement_id}/compliance",
        json={"approved": True, "compliance_notes": "Attempting self-approval"},
    )
    assert non_staff_review.status_code == 403

    # 2. Staff attempts disbursement BEFORE approval -> 400 Payout not approved
    _login_user(client, staff.email)
    disburse_early = client.post(f"/api/v1/rbpc/editor/settlements/{settlement_id}/disburse")
    assert disburse_early.status_code == 400
    assert disburse_early.json()["error"]["code"] == "RBPC_PAYOUT_NOT_APPROVED"

    # 3. Staff approves compliance
    compliance_ok = client.post(
        f"/api/v1/rbpc/editor/settlements/{settlement_id}/compliance",
        json={"approved": True, "compliance_notes": "Đã kiểm tra chứng từ ngân hàng hợp lệ."},
    )
    assert compliance_ok.status_code == 200
    reviewed_data = compliance_ok.json()
    assert reviewed_data["compliance_approved"] is True
    assert reviewed_data["status"] == "approved"
    assert reviewed_data["payout_status"] == "approved"

    # 4. Now disbursement succeeds
    disburse_ok = client.post(f"/api/v1/rbpc/editor/settlements/{settlement_id}/disburse")
    assert disburse_ok.status_code == 200
    disbursed_data = disburse_ok.json()
    assert disbursed_data["status"] == "settled"
    assert disbursed_data["payout_status"] == "disbursed"
    assert disbursed_data["disbursed_at"] is not None


def test_refund_workflow_and_arithmetic(client, db_session):
    """Refund deducts gross, recalculates fees and artisan allocation, and respects bounds."""
    provider = _create_user(db_session, "provider_refund@example.com", role=UserRole.teacher)
    staff = _create_user(db_session, "staff_refund@example.com", role=UserRole.admin)
    creator, exp, inquiry = _setup_test_context(db_session, provider)

    _login_user(client, provider.email)
    client.patch(f"/api/v1/rbpc/partner/inquiries/{inquiry.id}", json={"status": "contacted"})
    client.patch(f"/api/v1/rbpc/partner/inquiries/{inquiry.id}", json={"status": "confirmed"})

    settle_res = client.post(
        "/api/v1/rbpc/partner/settlements",
        json={
            "inquiry_id": str(inquiry.id),
            "gross_amount_vnd": 4000000.0,
            "take_rate": 0.15,
            "vat_rate": 0.08,
        },
    )
    settlement_id = settle_res.json()["id"]

    # 1. Excessive refund rejected
    excess_res = client.post(
        f"/api/v1/rbpc/partner/settlements/{settlement_id}/refund",
        json={"refund_amount_vnd": 5000000.0, "reason": "Too much refund requested"},
    )
    assert excess_res.status_code == 400
    assert excess_res.json()["error"]["code"] == "RBPC_REFUND_EXCEEDS_GROSS"

    # 2. Partial refund of 1,000,000 VND
    partial_res = client.post(
        f"/api/v1/rbpc/partner/settlements/{settlement_id}/refund",
        json={"refund_amount_vnd": 1000000.0, "reason": "1 người trong đoàn hủy chuyến"},
    )
    assert partial_res.status_code == 200
    part_data = partial_res.json()
    assert part_data["refund_amount_vnd"] == 1000000.0
    # Remaining effective gross = 3,000,000
    # Platform fee = 3,000,000 * 0.15 = 450,000
    assert part_data["platform_fee_vnd"] == 450000.0

    # 3. Full refund of remaining 3,000,000 VND
    full_res = client.post(
        f"/api/v1/rbpc/partner/settlements/{settlement_id}/refund",
        json={"refund_amount_vnd": 3000000.0, "reason": "Hủy toàn bộ đoàn do thời tiết bão"},
    )
    assert full_res.status_code == 200
    full_data = full_res.json()
    assert full_data["refund_amount_vnd"] == 4000000.0
    assert full_data["status"] == "refunded"
    assert full_data["payout_status"] == "cancelled"


def test_multi_tenant_isolation_on_settlements(client, db_session):
    """Providers cannot view or modify each other's settlements."""
    prov_a = _create_user(db_session, "provider_a@example.com", role=UserRole.teacher)
    prov_b = _create_user(db_session, "provider_b@example.com", role=UserRole.teacher)

    creator_a, exp_a, inq_a = _setup_test_context(db_session, prov_a)

    _login_user(client, prov_a.email)
    client.patch(f"/api/v1/rbpc/partner/inquiries/{inq_a.id}", json={"status": "contacted"})
    client.patch(f"/api/v1/rbpc/partner/inquiries/{inq_a.id}", json={"status": "confirmed"})

    settle_a = client.post(
        "/api/v1/rbpc/partner/settlements",
        json={"inquiry_id": str(inq_a.id), "gross_amount_vnd": 1000000.0},
    ).json()

    # Provider B attempts to view Provider A's settlement
    _login_user(client, prov_b.email)
    res_b = client.get(f"/api/v1/rbpc/partner/settlements/{settle_a['id']}")
    assert res_b.status_code == 403
    assert res_b.json()["error"]["code"] == "FORBIDDEN_SCOPE"

    # Provider B lists settlements: should not include Provider A's settlement
    list_b = client.get("/api/v1/rbpc/partner/settlements").json()
    ids_b = [item["id"] for item in list_b["items"]]
    assert settle_a["id"] not in ids_b
