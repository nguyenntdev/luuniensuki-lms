# -*- coding: utf-8 -*-
"""V5-T017: Provider membership scope hardening (multi-tenant negative tests and zero parameter trusting).

Audits and verifies:
1. In backend/routers/rbpc.py:
   - In `list_partner_inquiries` and `update_partner_inquiry_status`:
     Caller identity comes SOLELY from `current_user: User = Depends(get_current_user)`.
     Never trusts any client query param (such as `?provider=...`) to grant access to another provider's data.
     Non-admin callers can ONLY view and update inquiries where `inquiry.provider_id == current_user.id`
     or `experience.provider_id == current_user.id`.
   - In `update_partner_inquiry_status`: caller attempting to update another provider's inquiry MUST receive HTTP 403 FORBIDDEN_SCOPE.
2. Multi-tenant negative tests and parameter poisoning resistance:
   - Provider A and Provider B with separate experiences and inquiries.
   - Provider A cannot see Provider B's inquiries via GET `/api/v1/rbpc/partner/inquiries` (returns only A's inquiries).
   - Passing `?provider=<Provider_B_id>` from Provider A does not leak Provider B's inquiries.
   - Provider A attempting to PATCH Provider B's inquiry returns 403 FORBIDDEN_SCOPE.
   - Unauthenticated caller receives 401 Unauthorized.
   - Admin user CAN view and manage cross-tenant inquiries.
"""
from __future__ import annotations

import uuid
from datetime import date, timedelta

import pytest
from fastapi import status

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
    """Helper to persist a user with specific role for tenant tests."""
    user = User(
        email=email,
        password_hash=hash_password("Password123!"),
        display_name=display_name or f"User {email.split('@')[0]}",
        username=f"user_{uuid.uuid4().hex[:8]}",
        role=role,
        is_profile_public=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _login_user(client, email: str, password: str = "Password123!") -> dict:
    """Login helper setting session cookies on test client."""
    res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    return res.json()


def _setup_tenants_and_inquiries(db_session):
    """Seed Provider A and Provider B with distinct experiences and inquiries."""
    partner_a = _create_user(db_session, f"provider_a_{uuid.uuid4().hex[:6]}@example.com", role=UserRole.teacher)
    partner_b = _create_user(db_session, f"provider_b_{uuid.uuid4().hex[:6]}@example.com", role=UserRole.teacher)
    admin_user = _create_user(db_session, f"admin_{uuid.uuid4().hex[:6]}@example.com", role=UserRole.admin)

    creator_a = RbpcCreator(
        slug=f"artisan-v5-a-{uuid.uuid4().hex[:6]}",
        public_name="Nghệ Nhân Đúc Đồng V5 A",
        craft_tradition="Đúc đồng",
        approved_bio_vi="Tiểu sử nghệ nhân A",
        consent_status=RbpcConsentStatus.consented.value,
        is_verified=True,
    )
    creator_b = RbpcCreator(
        slug=f"artisan-v5-b-{uuid.uuid4().hex[:6]}",
        public_name="Nghệ Nhân Thêu V5 B",
        craft_tradition="Thêu tay Huế",
        approved_bio_vi="Tiểu sử nghệ nhân B",
        consent_status=RbpcConsentStatus.consented.value,
        is_verified=True,
    )
    db_session.add_all([creator_a, creator_b])
    db_session.flush()

    exp_a = RbpcExperience(
        slug=f"exp-v5-a-{uuid.uuid4().hex[:6]}",
        creator_id=creator_a.id,
        provider_name="Cơ sở A",
        provider_id=partner_a.id,
        title_vi="Trải nghiệm Đúc Đồng A",
        description_vi="Mô tả trải nghiệm A",
        area_public="Huế",
        publication_state="published",
    )
    exp_b = RbpcExperience(
        slug=f"exp-v5-b-{uuid.uuid4().hex[:6]}",
        creator_id=creator_b.id,
        provider_name="Cơ sở B",
        provider_id=partner_b.id,
        title_vi="Trải nghiệm Thêu B",
        description_vi="Mô tả trải nghiệm B",
        area_public="Huế",
        publication_state="published",
    )
    db_session.add_all([exp_a, exp_b])
    db_session.flush()

    ref_a = f"INQ-A-{uuid.uuid4().hex[:6].upper()}"
    inquiry_a = RbpcInquiry(
        public_ref=ref_a,
        experience_id=exp_a.id,
        provider_id=partner_a.id,
        name="Visitor for A",
        contact_channel="email",
        contact_value="visitor_a@example.com",
        desired_date=date.today() + timedelta(days=5),
        party_size=2,
        message="I want to learn bronze casting.",
        state=RbpcInquiryStatus.new.value,
        idempotency_key=f"idem-a-{uuid.uuid4().hex}",
        opaque_token=f"tok_a_{uuid.uuid4().hex}",
    )

    ref_b = f"INQ-B-{uuid.uuid4().hex[:6].upper()}"
    inquiry_b = RbpcInquiry(
        public_ref=ref_b,
        experience_id=exp_b.id,
        provider_id=partner_b.id,
        name="Visitor for B",
        contact_channel="phone",
        contact_value="0987654321",
        desired_date=date.today() + timedelta(days=7),
        party_size=3,
        message="I want to learn traditional embroidery.",
        state=RbpcInquiryStatus.new.value,
        idempotency_key=f"idem-b-{uuid.uuid4().hex}",
        opaque_token=f"tok_b_{uuid.uuid4().hex}",
    )
    db_session.add_all([inquiry_a, inquiry_b])
    db_session.commit()

    return {
        "partner_a": partner_a,
        "partner_b": partner_b,
        "admin_user": admin_user,
        "exp_a": exp_a,
        "exp_b": exp_b,
        "inquiry_a": inquiry_a,
        "inquiry_b": inquiry_b,
    }


def test_unauthenticated_partner_access_returns_401(client):
    """Verify unauthenticated caller receives 401 Unauthorized on partner endpoints."""
    client.cookies.clear()
    res = client.get("/api/v1/rbpc/partner/inquiries")
    assert res.status_code == status.HTTP_401_UNAUTHORIZED

    dummy_id = uuid.uuid4()
    res_patch = client.patch(
        f"/api/v1/rbpc/partner/inquiries/{dummy_id}",
        json={"status": "contacted", "note": "Unauthenticated update attempt"},
    )
    assert res_patch.status_code == status.HTTP_401_UNAUTHORIZED


def test_provider_a_cannot_see_provider_b_inquiries(client, db_session):
    """Verify Provider A cannot see Provider B's inquiries via GET /api/v1/rbpc/partner/inquiries."""
    data = _setup_tenants_and_inquiries(db_session)
    partner_a = data["partner_a"]
    inquiry_a = data["inquiry_a"]
    inquiry_b = data["inquiry_b"]

    _login_user(client, partner_a.email)
    res = client.get("/api/v1/rbpc/partner/inquiries")
    assert res.status_code == status.HTTP_200_OK

    body = res.json()
    refs = [item["reference"] for item in body.get("items", [])]
    assert inquiry_a.public_ref in refs
    assert inquiry_b.public_ref not in refs, "Multi-tenant leak: Provider A saw Provider B's inquiry"


def test_parameter_tampering_provider_param_does_not_leak(client, db_session):
    """Verify passing ?provider=<Provider_B_id> from Provider A does not leak Provider B's inquiries."""
    data = _setup_tenants_and_inquiries(db_session)
    partner_a = data["partner_a"]
    partner_b = data["partner_b"]
    inquiry_a = data["inquiry_a"]
    inquiry_b = data["inquiry_b"]

    _login_user(client, partner_a.email)

    # Attack: Provider A attempts parameter tampering by injecting Provider B's ID
    res = client.get(f"/api/v1/rbpc/partner/inquiries?provider={partner_b.id}")
    assert res.status_code == status.HTTP_200_OK

    body = res.json()
    refs = [item["reference"] for item in body.get("items", [])]
    # Scoping MUST be enforced strictly from authenticated identity (current_user.id)
    assert inquiry_a.public_ref in refs, "Provider A should still see their own inquiries"
    assert inquiry_b.public_ref not in refs, "Parameter tampering vulnerability: Provider B inquiries leaked via ?provider="


def test_provider_a_patching_provider_b_returns_403_forbidden_scope(client, db_session):
    """Verify Provider A attempting to PATCH Provider B's inquiry returns 403 FORBIDDEN_SCOPE."""
    data = _setup_tenants_and_inquiries(db_session)
    partner_a = data["partner_a"]
    inquiry_b = data["inquiry_b"]

    _login_user(client, partner_a.email)

    res = client.patch(
        f"/api/v1/rbpc/partner/inquiries/{inquiry_b.id}",
        json={"status": "contacted", "note": "Malicious state transition attempt by Provider A"},
    )
    assert res.status_code == status.HTTP_403_FORBIDDEN
    err_body = res.json().get("error", {})
    assert err_body.get("code") == "FORBIDDEN_SCOPE"
    assert "permission" in err_body.get("message", "").lower() or "forbidden" in err_body.get("message", "").lower()


def test_provider_b_can_manage_own_inquiry(client, db_session):
    """Verify Provider B can successfully transition their own inquiry."""
    data = _setup_tenants_and_inquiries(db_session)
    partner_b = data["partner_b"]
    inquiry_b = data["inquiry_b"]

    _login_user(client, partner_b.email)

    res = client.patch(
        f"/api/v1/rbpc/partner/inquiries/{inquiry_b.id}",
        json={"status": "contacted", "note": "Legitimate transition by Provider B"},
    )
    assert res.status_code == status.HTTP_200_OK
    assert res.json().get("status") == "contacted"


def test_admin_can_view_and_manage_cross_tenant_inquiries(client, db_session):
    """Verify admin user CAN view and manage cross-tenant inquiries."""
    data = _setup_tenants_and_inquiries(db_session)
    admin_user = data["admin_user"]
    partner_a = data["partner_a"]
    partner_b = data["partner_b"]
    inquiry_a = data["inquiry_a"]
    inquiry_b = data["inquiry_b"]

    _login_user(client, admin_user.email)

    # 1. Admin views all inquiries across all tenants
    res_all = client.get("/api/v1/rbpc/partner/inquiries")
    assert res_all.status_code == status.HTTP_200_OK
    refs_all = [item["reference"] for item in res_all.json().get("items", [])]
    assert inquiry_a.public_ref in refs_all
    assert inquiry_b.public_ref in refs_all

    # 2. Admin can filter by provider query param
    res_filter_a = client.get(f"/api/v1/rbpc/partner/inquiries?provider={partner_a.id}")
    assert res_filter_a.status_code == status.HTTP_200_OK
    refs_filter_a = [item["reference"] for item in res_filter_a.json().get("items", [])]
    assert inquiry_a.public_ref in refs_filter_a
    assert inquiry_b.public_ref not in refs_filter_a

    # 3. Admin can update inquiries across tenants
    res_admin_patch = client.patch(
        f"/api/v1/rbpc/partner/inquiries/{inquiry_a.id}",
        json={"status": "contacted", "note": "Admin intervention on inquiry A"},
    )
    assert res_admin_patch.status_code == status.HTTP_200_OK
    assert res_admin_patch.json().get("status") == "contacted"
