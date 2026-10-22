# -*- coding: utf-8 -*-
"""V5-T013: Partner Inbox No Seeding In Production Test Suite.

Scope & Invariants:
1. Empty provider tenant receives empty list `[]` from `/api/v1/rbpc/partner/inquiries` and total=0.
2. Unauthenticated calls to `/api/v1/rbpc/partner/inquiries` and `/api/v1/rbpc/partner/inquiries/{id}`
   are rejected with HTTP 401.
3. Unauthorized cross-tenant mutations to `/api/v1/rbpc/partner/inquiries/{id}` are rejected with HTTP 403
   (FORBIDDEN_SCOPE).
4. Production mode never injects synthetic seed inquiries (e.g. INQ-7F89-A23C, inq-001..inq-005) into
   partner inboxes.
5. Multi-tenant scoping ensures each provider sees strictly their own inquiries, with zero synthetic leakage.
"""
from __future__ import annotations

import uuid
from datetime import date, timedelta

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

SYNTHETIC_SEED_REFS = {
    "INQ-7F89-A23C",
    "INQ-6E21-B44D",
    "INQ-5B10-C89E",
    "INQ-4A02-D11F",
    "INQ-3C98-E52A",
}

SYNTHETIC_SEED_IDS = {
    "inq-001",
    "inq-002",
    "inq-003",
    "inq-004",
    "inq-005",
}


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
    """Login helper setting session cookies on test client."""
    res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    return res.json()


def _setup_test_tenants(db_session):
    """Seed distinct artisan creators, workshop experiences, and provider users."""
    partner_empty = _create_user(
        db_session,
        f"partner_t013_empty_{uuid.uuid4().hex[:6]}@example.com",
        role=UserRole.teacher,
    )
    partner_with_inquiry = _create_user(
        db_session,
        f"partner_t013_active_{uuid.uuid4().hex[:6]}@example.com",
        role=UserRole.teacher,
    )
    partner_other = _create_user(
        db_session,
        f"partner_t013_other_{uuid.uuid4().hex[:6]}@example.com",
        role=UserRole.teacher,
    )

    creator_active = RbpcCreator(
        slug=f"artisan-t013-active-{uuid.uuid4().hex[:6]}",
        public_name="Nghệ nhân T013 Active",
        craft_tradition="Đúc đồng Phường Đúc",
        approved_bio_vi="Nghệ nhân Phường Đúc.",
        consent_status=RbpcConsentStatus.consented.value,
        is_verified=True,
    )
    creator_other = RbpcCreator(
        slug=f"artisan-t013-other-{uuid.uuid4().hex[:6]}",
        public_name="Nghệ nhân T013 Other",
        craft_tradition="Pháp lam Huế",
        approved_bio_vi="Nghệ nhân Pháp lam.",
        consent_status=RbpcConsentStatus.consented.value,
        is_verified=True,
    )
    db_session.add_all([creator_active, creator_other])
    db_session.flush()

    exp_active = RbpcExperience(
        slug=f"exp-t013-active-{uuid.uuid4().hex[:6]}",
        creator_id=creator_active.id,
        provider_name="Xưởng Đúc Đồng Active",
        provider_id=partner_with_inquiry.id,
        title_vi="Trải nghiệm Đúc Đồng Active",
        description_vi="Mô tả trải nghiệm Active",
        area_public="Huế",
        publication_state="published",
    )
    exp_other = RbpcExperience(
        slug=f"exp-t013-other-{uuid.uuid4().hex[:6]}",
        creator_id=creator_other.id,
        provider_name="Trung tâm Pháp lam Other",
        provider_id=partner_other.id,
        title_vi="Trải nghiệm Pháp lam Other",
        description_vi="Mô tả trải nghiệm Other",
        area_public="Huế",
        publication_state="published",
    )
    db_session.add_all([exp_active, exp_other])
    db_session.flush()

    inquiry_active = RbpcInquiry(
        public_ref=f"INQ-ACT-{uuid.uuid4().hex[:4].upper()}",
        experience_id=exp_active.id,
        provider_id=partner_with_inquiry.id,
        name="Visitor Active",
        contact_channel="email",
        contact_value="active_visitor@example.com",
        desired_date=date.today() + timedelta(days=5),
        party_size=2,
        message="Active workshop booking inquiry.",
        consent_version="rbpc-inquiry-v1",
        state=RbpcInquiryStatus.new.value,
        idempotency_key=str(uuid.uuid4()),
        opaque_token=f"tok_t013_active_{uuid.uuid4().hex}",
    )
    inquiry_other = RbpcInquiry(
        public_ref=f"INQ-OTH-{uuid.uuid4().hex[:4].upper()}",
        experience_id=exp_other.id,
        provider_id=partner_other.id,
        name="Visitor Other",
        contact_channel="phone",
        contact_value="0912345678",
        desired_date=date.today() + timedelta(days=10),
        party_size=4,
        message="Other workshop booking inquiry.",
        consent_version="rbpc-inquiry-v1",
        state=RbpcInquiryStatus.new.value,
        idempotency_key=str(uuid.uuid4()),
        opaque_token=f"tok_t013_other_{uuid.uuid4().hex}",
    )
    db_session.add_all([inquiry_active, inquiry_other])
    db_session.commit()

    return {
        "partner_empty": partner_empty,
        "partner_with_inquiry": partner_with_inquiry,
        "partner_other": partner_other,
        "inquiry_active": inquiry_active,
        "inquiry_other": inquiry_other,
    }


def test_unauthenticated_partner_inquiries_rejected(client):
    """Verify that unauthenticated callers cannot access or mutate partner inbox."""
    # 1. GET without credentials -> HTTP 401
    res_get = client.get("/api/v1/rbpc/partner/inquiries")
    assert res_get.status_code == 401, f"Expected 401 for unauthenticated GET, got {res_get.status_code}"

    # 2. PATCH without credentials -> HTTP 401
    random_id = uuid.uuid4()
    res_patch = client.patch(
        f"/api/v1/rbpc/partner/inquiries/{random_id}",
        json={"status": "contacted", "note": "Unauthenticated attempt"},
    )
    assert res_patch.status_code == 401, f"Expected 401 for unauthenticated PATCH, got {res_patch.status_code}"


def test_empty_provider_tenant_receives_empty_list_and_zero_total(client, db_session):
    """Verify that an empty provider tenant receives strictly [] and total=0."""
    tenants = _setup_test_tenants(db_session)
    empty_partner = tenants["partner_empty"]

    # Log in as the empty provider tenant
    _login_user(client, empty_partner.email)

    # Fetch inquiries
    res = client.get("/api/v1/rbpc/partner/inquiries")
    assert res.status_code == 200, res.text
    data = res.json()

    # Invariants for fresh / empty provider:
    assert data["total"] == 0, f"Expected total=0 for empty provider, got {data['total']}"
    assert isinstance(data["items"], list), "Expected items to be a list"
    assert len(data["items"]) == 0, f"Expected 0 items for empty provider, got {len(data['items'])}"
    assert data["items"] == [], "Expected strictly empty list []"


def test_production_mode_never_injects_synthetic_seed_inquiries(client, db_session):
    """Verify that production mode never injects synthetic seed inquiries into any partner inbox."""
    tenants = _setup_test_tenants(db_session)
    empty_partner = tenants["partner_empty"]
    active_partner = tenants["partner_with_inquiry"]
    inquiry_active = tenants["inquiry_active"]

    # 1. Empty partner test
    _login_user(client, empty_partner.email)
    res_empty = client.get("/api/v1/rbpc/partner/inquiries")
    assert res_empty.status_code == 200
    data_empty = res_empty.json()

    returned_refs_empty = {item["reference"] for item in data_empty["items"]}
    returned_ids_empty = {str(item["id"]) for item in data_empty["items"]}

    # Negative check: zero synthetic seed references or IDs
    assert not returned_refs_empty.intersection(SYNTHETIC_SEED_REFS), (
        f"Synthetic seed references bled into empty partner inbox: {returned_refs_empty.intersection(SYNTHETIC_SEED_REFS)}"
    )
    assert not returned_ids_empty.intersection(SYNTHETIC_SEED_IDS), (
        f"Synthetic seed IDs bled into empty partner inbox: {returned_ids_empty.intersection(SYNTHETIC_SEED_IDS)}"
    )

    # 2. Active partner test (has 1 real inquiry)
    _login_user(client, active_partner.email)
    res_active = client.get("/api/v1/rbpc/partner/inquiries")
    assert res_active.status_code == 200
    data_active = res_active.json()

    assert data_active["total"] == 1
    assert len(data_active["items"]) == 1
    assert data_active["items"][0]["reference"] == inquiry_active.public_ref

    returned_refs_active = {item["reference"] for item in data_active["items"]}
    returned_ids_active = {str(item["id"]) for item in data_active["items"]}

    # Negative check: no synthetic seed inquiries
    assert not returned_refs_active.intersection(SYNTHETIC_SEED_REFS)
    assert not returned_ids_active.intersection(SYNTHETIC_SEED_IDS)


def test_unauthorized_cross_tenant_patch_rejected(client, db_session):
    """Verify that an unauthorized partner cannot mutate an inquiry belonging to another provider."""
    tenants = _setup_test_tenants(db_session)
    empty_partner = tenants["partner_empty"]
    active_partner = tenants["partner_with_inquiry"]
    other_partner = tenants["partner_other"]
    inquiry_active = tenants["inquiry_active"]
    inquiry_other = tenants["inquiry_other"]

    # 1. Empty partner attempts to update active partner's inquiry -> 403 Forbidden Scope
    _login_user(client, empty_partner.email)
    res_tamper_1 = client.patch(
        f"/api/v1/rbpc/partner/inquiries/{inquiry_active.id}",
        json={"status": "contacted", "note": "Unauthorized cross-tenant attempt 1"},
    )
    assert res_tamper_1.status_code == 403, f"Expected 403 FORBIDDEN_SCOPE, got {res_tamper_1.status_code}"
    err_1 = res_tamper_1.json().get("error", {})
    assert err_1.get("code") == "FORBIDDEN_SCOPE"

    # 2. Active partner attempts to update other partner's inquiry -> 403 Forbidden Scope
    _login_user(client, active_partner.email)
    res_tamper_2 = client.patch(
        f"/api/v1/rbpc/partner/inquiries/{inquiry_other.id}",
        json={"status": "contacted", "note": "Unauthorized cross-tenant attempt 2"},
    )
    assert res_tamper_2.status_code == 403, f"Expected 403 FORBIDDEN_SCOPE, got {res_tamper_2.status_code}"
    err_2 = res_tamper_2.json().get("error", {})
    assert err_2.get("code") == "FORBIDDEN_SCOPE"

    # 3. Legitimate partner can update their own inquiry
    res_valid = client.patch(
        f"/api/v1/rbpc/partner/inquiries/{inquiry_active.id}",
        json={"status": "contacted", "note": "Legitimate status update by owner"},
    )
    assert res_valid.status_code == 200, res_valid.text
    data_valid = res_valid.json()
    assert data_valid["status"] == "contacted"


def test_provider_inbox_strict_ownership_scoping(client, db_session):
    """Verify horizontal multi-tenant database scoping across all provider accounts."""
    tenants = _setup_test_tenants(db_session)
    partner_empty = tenants["partner_empty"]
    partner_active = tenants["partner_with_inquiry"]
    partner_other = tenants["partner_other"]
    inquiry_active = tenants["inquiry_active"]
    inquiry_other = tenants["inquiry_other"]

    # Partner Active sees only inquiry_active
    _login_user(client, partner_active.email)
    res_a = client.get("/api/v1/rbpc/partner/inquiries")
    assert res_a.status_code == 200
    refs_a = [item["reference"] for item in res_a.json()["items"]]
    assert refs_a == [inquiry_active.public_ref]

    # Partner Other sees only inquiry_other
    _login_user(client, partner_other.email)
    res_o = client.get("/api/v1/rbpc/partner/inquiries")
    assert res_o.status_code == 200
    refs_o = [item["reference"] for item in res_o.json()["items"]]
    assert refs_o == [inquiry_other.public_ref]

    # Empty partner sees nothing
    _login_user(client, partner_empty.email)
    res_e = client.get("/api/v1/rbpc/partner/inquiries")
    assert res_e.status_code == 200
    assert res_e.json()["total"] == 0
    assert res_e.json()["items"] == []
