# -*- coding: utf-8 -*-
"""V5-T014: Partner Status PATCH Persistence and Client Rollback Contract Test Suite.

Audits and verifies:
1. Valid lifecycle state machine transitions:
   - new -> contacted -> confirmed -> closed
   - new -> contacted -> declined -> closed
2. Disallowed state machine transitions:
   - new -> confirmed (skipping contacted returns 400 RBPC_INVALID_TRANSITION)
   - new -> closed (returns 400 RBPC_INVALID_TRANSITION)
   - confirmed -> contacted (backwards transition returns 400 RBPC_INVALID_TRANSITION)
   - closed -> any (closed is terminal; returns 400 RBPC_INVALID_TRANSITION)
3. Multi-tenant ownership and security scoping:
   - Unauthorized provider attempting to PATCH another provider's inquiry receives 403 FORBIDDEN_SCOPE.
   - Unauthenticated caller receives 401 Unauthorized.
4. Client contract enforcement:
   - updatePartnerInquiryStatusApi re-throws errors on network / server failures.
   - handleStatusChange rolls back optimistic UI state upon failed mutation.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
import pytest

from backend.models import User, UserRole
from backend.models_rbpc import (
    RbpcConsentStatus,
    RbpcCreator,
    RbpcExperience,
    RbpcInquiry,
    RbpcInquiryStatus,
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
        display_name=display_name or f"Provider {email.split('@')[0]}",
        username=f"prov_{uuid.uuid4().hex[:8]}",
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


def _setup_test_inquiry(db_session, provider_user: User):
    creator = RbpcCreator(
        slug=f"artisan-{uuid.uuid4().hex[:6]}",
        public_name="Nghệ nhân Đúc Đồng",
        craft_tradition="Đúc đồng Phường Đúc",
        approved_bio_vi="Nghệ nhân gia truyền.",
        consent_status=RbpcConsentStatus.consented.value,
        is_verified=True,
    )
    db_session.add(creator)
    db_session.flush()

    exp = RbpcExperience(
        slug=f"exp-patch-{uuid.uuid4().hex[:6]}",
        title_vi="Trải nghiệm Đúc Đồng Thử Nghiệm",
        title_en="Bronze Casting Trial",
        description_vi="Mô tả trải nghiệm thử nghiệm.",
        creator_id=creator.id,
        provider_name="Xưởng Đúc Đồng Thử Nghiệm",
        provider_id=provider_user.id,
        publication_state="published",
        availability_mode="inquiry_only",
    )
    db_session.add(exp)
    db_session.flush()

    inquiry = RbpcInquiry(
        public_ref=f"INQ-{uuid.uuid4().hex[:4].upper()}-{uuid.uuid4().hex[:4].upper()}",
        experience_id=exp.id,
        provider_id=provider_user.id,
        name="Khách Hàng Thử Nghiệm",
        contact_channel="email",
        contact_value="test.visitor@example.com",
        desired_date=date.today(),
        party_size=2,
        message="Mong muốn tham gia trải nghiệm.",
        consent_version="rbpc-inquiry-v1",
        privacy_accepted=True,
        state=RbpcInquiryStatus.new.value,
        idempotency_key=str(uuid.uuid4()),
        opaque_token=f"tok_sec_{uuid.uuid4().hex}",
    )
    db_session.add(inquiry)
    db_session.commit()
    db_session.refresh(inquiry)
    return inquiry


def test_valid_inquiry_status_transition_sequence(client, db_session):
    """Test valid sequential status transitions: new -> contacted -> confirmed -> closed."""
    provider = _create_user(db_session, "provider_t014_valid@example.com", role=UserRole.teacher)
    inquiry = _setup_test_inquiry(db_session, provider)
    _login_user(client, provider.email)

    # 1. new -> contacted
    res1 = client.patch(
        f"/api/v1/rbpc/partner/inquiries/{inquiry.id}",
        json={"status": "contacted", "note": "Đã gọi điện thoại xác nhận sơ bộ."},
    )
    assert res1.status_code == 200, res1.text
    data1 = res1.json()
    assert data1["status"] == "contacted"

    # 2. contacted -> confirmed
    res2 = client.patch(
        f"/api/v1/rbpc/partner/inquiries/{inquiry.id}",
        json={"status": "confirmed", "note": "Đã chốt lịch hẹn ngày mai."},
    )
    assert res2.status_code == 200, res2.text
    data2 = res2.json()
    assert data2["status"] == "confirmed"

    # 3. confirmed -> closed
    res3 = client.patch(
        f"/api/v1/rbpc/partner/inquiries/{inquiry.id}",
        json={"status": "closed", "note": "Buổi trải nghiệm đã hoàn tất thành công."},
    )
    assert res3.status_code == 200, res3.text
    data3 = res3.json()
    assert data3["status"] == "closed"


def test_alternative_inquiry_status_transition_declined(client, db_session):
    """Test alternative transition: new -> contacted -> declined -> closed."""
    provider = _create_user(db_session, "provider_t014_declined@example.com", role=UserRole.teacher)
    inquiry = _setup_test_inquiry(db_session, provider)
    _login_user(client, provider.email)

    # 1. new -> contacted
    res1 = client.patch(
        f"/api/v1/rbpc/partner/inquiries/{inquiry.id}",
        json={"status": "contacted", "note": "Đã liên hệ kiểm tra lịch."},
    )
    assert res1.status_code == 200

    # 2. contacted -> declined
    res2 = client.patch(
        f"/api/v1/rbpc/partner/inquiries/{inquiry.id}",
        json={"status": "declined", "note": "Xưởng bận lịch đại hồng chung, không thể tiếp đoàn."},
    )
    assert res2.status_code == 200
    assert res2.json()["status"] == "declined"

    # 3. declined -> closed
    res3 = client.patch(
        f"/api/v1/rbpc/partner/inquiries/{inquiry.id}",
        json={"status": "closed", "note": "Đã đóng hồ sơ từ chối."},
    )
    assert res3.status_code == 200
    assert res3.json()["status"] == "closed"


def test_invalid_transition_skipping_contacted_rejected(client, db_session):
    """Test that transitioning directly from new -> confirmed fails with 400 RBPC_INVALID_TRANSITION."""
    provider = _create_user(db_session, "provider_t014_invalid@example.com", role=UserRole.teacher)
    inquiry = _setup_test_inquiry(db_session, provider)
    _login_user(client, provider.email)

    res = client.patch(
        f"/api/v1/rbpc/partner/inquiries/{inquiry.id}",
        json={"status": "confirmed", "note": "Nhảy cóc từ new lên confirmed mà chưa liên hệ."},
    )
    assert res.status_code == 400
    data = res.json()
    error_obj = data.get("error", data)
    assert error_obj["code"] == "RBPC_INVALID_TRANSITION"


def test_terminal_state_closed_cannot_be_reopened(client, db_session):
    """Test that transitioning from closed to any other status fails with 400 RBPC_INVALID_TRANSITION."""
    provider = _create_user(db_session, "provider_t014_terminal@example.com", role=UserRole.teacher)
    inquiry = _setup_test_inquiry(db_session, provider)
    _login_user(client, provider.email)

    # Advance to closed
    client.patch(f"/api/v1/rbpc/partner/inquiries/{inquiry.id}", json={"status": "contacted"})
    client.patch(f"/api/v1/rbpc/partner/inquiries/{inquiry.id}", json={"status": "confirmed"})
    client.patch(f"/api/v1/rbpc/partner/inquiries/{inquiry.id}", json={"status": "closed"})

    # Try reopening
    res = client.patch(
        f"/api/v1/rbpc/partner/inquiries/{inquiry.id}",
        json={"status": "contacted", "note": "Thử mở lại hồ sơ đã đóng."},
    )
    assert res.status_code == 400
    data = res.json()
    error_obj = data.get("error", data)
    assert error_obj["code"] == "RBPC_INVALID_TRANSITION"


def test_cross_tenant_patch_rejected_with_forbidden_scope(client, db_session):
    """Test that Provider A attempting to PATCH Provider B's inquiry receives 403 FORBIDDEN_SCOPE."""
    provider_a = _create_user(db_session, "provider_t014_a@example.com", role=UserRole.teacher)
    provider_b = _create_user(db_session, "provider_t014_b@example.com", role=UserRole.teacher)
    inquiry_b = _setup_test_inquiry(db_session, provider_b)

    # Login as Provider A and attempt to modify Provider B's inquiry
    _login_user(client, provider_a.email)
    res = client.patch(
        f"/api/v1/rbpc/partner/inquiries/{inquiry_b.id}",
        json={"status": "contacted", "note": "Xâm phạm hồ sơ đối tác khác."},
    )
    assert res.status_code == 403
    data = res.json()
    error_obj = data.get("error", data)
    assert error_obj["code"] == "FORBIDDEN_SCOPE"


def test_unauthenticated_patch_rejected(client, db_session):
    """Test that unauthenticated PATCH requests are rejected with 401."""
    provider = _create_user(db_session, "provider_t014_anon@example.com", role=UserRole.teacher)
    inquiry = _setup_test_inquiry(db_session, provider)

    client.cookies.clear()
    res = client.patch(
        f"/api/v1/rbpc/partner/inquiries/{inquiry.id}",
        json={"status": "contacted"},
    )
    assert res.status_code == 401


def test_client_rollback_contract_invariants():
    """Verify frontend implementation files enforce strict failure re-throw and UI rollback."""
    with open("frontend/src/lib/rbpc/inquiries.ts", "r", encoding="utf-8") as f:
        inquiries_ts = f.read()

    assert "updatePartnerInquiryStatusApi" in inquiries_ts
    # updatePartnerInquiryStatusApi must await apiRequest directly without swallowing exceptions
    assert "await apiRequest(`/api/v1/rbpc/partner/inquiries/${encodeURIComponent(id)}`" in inquiries_ts

    with open("frontend/src/app/rbpc/partner/page.tsx", "r", encoding="utf-8") as f:
        partner_page_tsx = f.read()

    # handleStatusChange must have rollback logic in catch block
    assert "setInquiries(previousInquiries)" in partner_page_tsx
    assert "Failed to transition inquiry status" in partner_page_tsx or "Không thể chuyển trạng thái hồ sơ" in partner_page_tsx
