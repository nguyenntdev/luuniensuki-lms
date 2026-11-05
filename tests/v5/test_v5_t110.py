# -*- coding: utf-8 -*-
"""V5-T110: Public impact dashboard sourced from real events Test Suite.

Wave W10, Slot A10:
Public impact dashboard sourced from real events in frontend/src/app/rbpc/ and backend/routers/rbpc.py.
Displays anonymized actual completed experiences and artisan payouts; forecast projections are clearly separated.
Negative abuse invariant:
Empty database displays 0 / no metrics, never fabricated pitch numbers or synthetic counts.

Audits and verifies:
1. Negative abuse test (Empty Database baseline):
   - With zero closed inquiries and zero settlements, completed_experiences_count is 0.
   - artisan_payout_vnd_settled is 0.0 VND.
   - Never outputs fabricated pitch numbers (such as 1,100 completed SOM or fake GMV) into observed metrics.
2. Sourced from real completed events:
   - When an inquiry is in 'new' or 'contacted' or 'confirmed', completed_experiences_count remains 0.
   - When an inquiry transitions to 'closed', completed_experiences_count increments by 1.
3. Sourced from verified settlement artisan payouts:
   - Settlements in 'pending_compliance' do NOT count towards settled artisan payout.
   - Settlements in 'approved' or 'settled' contribute exactly to artisan_payout_vnd_settled.
   - Full refund or unapproved status does not leak fake payout.
4. Clean separation of observed vs forward projections:
   - observed_metrics contains completed_experiences_count, artisan_payout_vnd_settled, and sponsor_support_vnd_verified.
   - projected_metrics contains estimated_monthly_demand and projected_local_value_addition_vnd with clear projection_basis disclaimer.
   - Projections are never conflated with observed facts.
5. Anonymization & zero PII leaks:
   - Public GET /api/v1/rbpc/impact does not require authentication.
   - Contains zero user names, emails, phone numbers, or private notes.
6. Frontend impact dashboard page verification:
   - Verifies frontend/src/app/rbpc/impact/page.tsx exists and is wired to /api/v1/rbpc/impact.
   - Ensures data-testid elements exist for completed-experiences-count, artisan-payout-settled, and projection-basis-disclaimer.
"""
from __future__ import annotations

import os
from pathlib import Path
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


def _setup_test_context(db_session, provider_user: User):
    creator = RbpcCreator(
        slug=f"artisan-impact-{uuid.uuid4().hex[:6]}",
        public_name="Nghệ nhân Đúc Đồng Huế",
        craft_tradition="Đúc đồng thủ công",
        approved_bio_vi="Gia đình truyền thống đúc chuông và khí đồng.",
        consent_status=RbpcConsentStatus.consented.value,
        is_verified=True,
    )
    db_session.add(creator)
    db_session.flush()

    exp = RbpcExperience(
        slug=f"exp-impact-{uuid.uuid4().hex[:6]}",
        title_vi="Workshop Đúc Đồng Phường Đúc",
        title_en="Phuong Duc Bronze Casting Workshop",
        description_vi="Tham gia đúc đồng và tạo tác hoa văn.",
        creator_id=creator.id,
        provider_name="Xưởng Đúc Đồng Phường Đúc",
        provider_id=provider_user.id,
        publication_state="published",
        availability_mode="inquiry_only",
    )
    db_session.add(exp)
    db_session.flush()

    inquiry = RbpcInquiry(
        public_ref=f"INQ-IMP-{uuid.uuid4().hex[:6].upper()}",
        experience_id=exp.id,
        provider_id=provider_user.id,
        name="Du khách Thử Nghiệm",
        contact_channel="email",
        contact_value="tourist@example.com",
        desired_date=date.today(),
        party_size=2,
        message="Tôi muốn tham gia workshop đúc đồng.",
        state=RbpcInquiryStatus.new.value,
        idempotency_key=str(uuid.uuid4()),
        opaque_token=f"tok_imp_{uuid.uuid4().hex}",
    )
    db_session.add(inquiry)
    db_session.commit()
    db_session.refresh(inquiry)
    return creator, exp, inquiry


def test_v5_t110_negative_abuse_empty_database_zero_metrics(client, db_session):
    """Negative abuse invariant:

    When there are no closed inquiries or settled transactions in the DB,
    observed completed experiences is strictly 0 and artisan payout is 0.0.
    Never outputs fabricated pitch numbers.
    """
    res = client.get("/api/v1/rbpc/impact")
    assert res.status_code == 200, res.text
    data = res.json()

    assert "observed_metrics" in data
    assert "projected_metrics" in data

    observed = data["observed_metrics"]
    # Check baseline zero metrics
    assert observed["completed_experiences_count"] == 0, "Empty DB must show 0 completed experiences"
    assert observed["artisan_payout_vnd_settled"] == 0.0, "Empty DB must show 0.0 artisan payout"
    assert observed["sponsor_support_vnd_verified"] == 202360638.0, "Verified sponsor support constant preserved"

    # Confirm projections are quarantined and clearly labeled
    projected = data["projected_metrics"]
    assert "giả định" in projected["projection_basis"], "Projection disclaimer must be present"
    assert projected["projection_basis"] != "", "Disclaimers cannot be empty"


def test_v5_t110_completed_experiences_sourced_from_closed_inquiries_only(client, db_session):
    """Verify completed experiences count strictly tracks closed inquiry state events."""
    provider = _create_user(db_session, f"provider_{uuid.uuid4().hex[:6]}@example.com")
    creator, exp, inquiry = _setup_test_context(db_session, provider)

    # 1. State 'new' -> completed count is 0
    res = client.get("/api/v1/rbpc/impact")
    assert res.json()["observed_metrics"]["completed_experiences_count"] == 0

    # 2. State 'contacted' -> completed count is still 0
    inquiry.state = RbpcInquiryStatus.contacted.value
    db_session.commit()
    res = client.get("/api/v1/rbpc/impact")
    assert res.json()["observed_metrics"]["completed_experiences_count"] == 0

    # 3. State 'confirmed' -> completed count is still 0 (not completed until closed)
    inquiry.state = RbpcInquiryStatus.confirmed.value
    db_session.commit()
    res = client.get("/api/v1/rbpc/impact")
    assert res.json()["observed_metrics"]["completed_experiences_count"] == 0

    # 4. State 'closed' (Completed experience) -> completed count becomes 1
    inquiry.state = RbpcInquiryStatus.closed.value
    db_session.commit()
    res = client.get("/api/v1/rbpc/impact")
    assert res.json()["observed_metrics"]["completed_experiences_count"] == 1


def test_v5_t110_artisan_payout_sourced_from_verified_settlement_ledger(client, db_session):
    """Verify artisan payouts are strictly aggregated from approved/settled ledger records."""
    provider = _create_user(db_session, f"provider_{uuid.uuid4().hex[:6]}@example.com")
    creator, exp, inquiry = _setup_test_context(db_session, provider)
    inquiry.state = RbpcInquiryStatus.closed.value
    db_session.commit()

    # 1. Without settlement -> artisan payout is 0.0
    res = client.get("/api/v1/rbpc/impact")
    assert res.json()["observed_metrics"]["artisan_payout_vnd_settled"] == 0.0

    # 2. Settlement created but pending compliance -> payout is still 0.0
    settlement = RbpcSettlementLedger(
        settlement_ref=f"SET-{uuid.uuid4().hex[:8].upper()}",
        inquiry_id=inquiry.id,
        provider_id=provider.id,
        creator_id=creator.id,
        gross_amount_vnd=1000000.0,
        take_rate=0.1000,
        platform_fee_vnd=100000.0,
        tax_vat_vnd=80000.0,
        artisan_payout_vnd=820000.0,
        status=RbpcSettlementStatus.pending_compliance.value,
        payout_status=RbpcPayoutStatus.pending.value,
        compliance_approved=False,
    )
    db_session.add(settlement)
    db_session.commit()

    res = client.get("/api/v1/rbpc/impact")
    assert res.json()["observed_metrics"]["artisan_payout_vnd_settled"] == 0.0

    # 3. Compliance approved -> payout includes 820,000 VND
    settlement.status = RbpcSettlementStatus.approved.value
    settlement.compliance_approved = True
    settlement.payout_status = RbpcPayoutStatus.approved.value
    db_session.commit()

    res = client.get("/api/v1/rbpc/impact")
    assert res.json()["observed_metrics"]["artisan_payout_vnd_settled"] == 820000.0

    # 4. Disbursed/Settled status -> payout continues to be verified
    settlement.status = RbpcSettlementStatus.settled.value
    settlement.payout_status = RbpcPayoutStatus.disbursed.value
    settlement.disbursed_at = datetime.now(timezone.utc)
    db_session.commit()

    res = client.get("/api/v1/rbpc/impact")
    assert res.json()["observed_metrics"]["artisan_payout_vnd_settled"] == 820000.0

    # 5. Full refund -> status refunded -> excluded from verified payout
    settlement.status = RbpcSettlementStatus.refunded.value
    settlement.payout_status = RbpcPayoutStatus.cancelled.value
    db_session.commit()

    res = client.get("/api/v1/rbpc/impact")
    assert res.json()["observed_metrics"]["artisan_payout_vnd_settled"] == 0.0


def test_v5_t110_zero_pii_in_public_impact_metrics(client, db_session):
    """Ensure impact endpoint returns zero personally identifiable information."""
    provider = _create_user(db_session, f"provider_{uuid.uuid4().hex[:6]}@example.com")
    creator, exp, inquiry = _setup_test_context(db_session, provider)

    res = client.get("/api/v1/rbpc/impact")
    assert res.status_code == 200
    text = res.text

    # No visitor PII leaks
    assert "tourist@example.com" not in text
    assert "Du khách Thử Nghiệm" not in text
    assert inquiry.opaque_token not in text
    assert inquiry.idempotency_key not in text


def test_v5_t110_frontend_impact_page_and_contracts_exist():
    """Verify frontend page and client contracts for the public impact dashboard."""
    repo_root = Path(__file__).resolve().parents[2]
    page_path = repo_root / "frontend" / "src" / "app" / "rbpc" / "impact" / "page.tsx"
    inquiries_lib = repo_root / "frontend" / "src" / "lib" / "rbpc" / "inquiries.ts"
    types_file = repo_root / "frontend" / "src" / "types" / "rbpc.ts"

    assert page_path.exists(), f"Frontend page {page_path} must exist"
    page_content = page_path.read_text(encoding="utf-8")

    # Invariants in page.tsx
    assert "fetchImpactMetricsApi" in page_content
    assert "completed-experiences-count" in page_content
    assert "artisan-payout-settled" in page_content
    assert "sponsor-support-verified" in page_content
    assert "projection-basis-disclaimer" in page_content

    # Inquiries client library
    lib_content = inquiries_lib.read_text(encoding="utf-8")
    assert "fetchImpactMetricsApi" in lib_content
    assert "/api/v1/rbpc/impact" in lib_content

    # Types file
    types_content = types_file.read_text(encoding="utf-8")
    assert "RbpcImpactMetricsOut" in types_content
    assert "completed_experiences_count" in types_content
    assert "artisan_payout_vnd_settled" in types_content
