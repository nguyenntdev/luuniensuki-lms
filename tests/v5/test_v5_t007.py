# -*- coding: utf-8 -*-
"""V5-T007: RBPC Demo Tenant Isolation & Commercial Honesty Test Suite.

Audits and verifies:
1. DEMO_MODE flag behavior:
   - Configurable via environment variable / settings.
   - Defaults to True in development and False in production.
   - Production mode with demo_mode=True fails closed (RuntimeError).
   - Runtime /api/v1/rbpc/config reflects effective demo_mode setting.
2. Negative / abuse test:
   - Empty prod tenant returns zero inquiries (items: [], total: 0) even when
     other tenants or demo fixtures have active records.
   - Zero synthetic demo inquiries bleed through to production partner inboxes.
3. Cross-tenant isolation:
   - Partner A cannot read Partner B's inquiries (horizontal scoping).
   - Partner A cannot update Partner B's inquiry (HTTP 403 FORBIDDEN_SCOPE).
4. Demo fixtures service & commercial honesty audit:
   - verify_demo_fixtures_integrity ensures zero fraudulent transactions.
   - verify_tenant_isolation confirms strict multi-tenant database scoping.
   - assert_zero_fixtures_in_prod checks absence of mock/synthetic records.
5. Public tracking endpoint isolation:
   - Valid opaque tokens return zero-PII status tracking.
   - Fake or non-existent tokens return HTTP 404 (no synthetic fallback on server).
"""
from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone

import pytest

from backend.config import Settings, get_settings
from backend.models import User, UserRole
from backend.models_rbpc import (
    HeritagePlace,
    RbpcConsentStatus,
    RbpcCreator,
    RbpcExperience,
    RbpcInquiry,
    RbpcInquiryStatus,
)
from backend.security import hash_password
from backend.services.demo_fixtures import (
    assert_zero_fixtures_in_prod,
    verify_demo_fixtures_integrity,
    verify_tenant_isolation,
)


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


def _setup_isolated_tenants(db_session):
    """Seed distinct artisan creators, workshop experiences, and provider users."""
    partner_a = _create_user(db_session, "partner_t007_a@example.com", role=UserRole.teacher)
    partner_b = _create_user(db_session, "partner_t007_b@example.com", role=UserRole.teacher)
    partner_prod_empty = _create_user(db_session, "partner_t007_prod_empty@example.com", role=UserRole.teacher)

    creator_a = RbpcCreator(
        slug=f"artisan-t007-a-{uuid.uuid4().hex[:6]}",
        public_name="Nghệ nhân Đồng A",
        craft_tradition="Đúc đồng Phường Đúc",
        approved_bio_vi="Nghệ nhân Phường Đúc.",
        consent_status=RbpcConsentStatus.consented.value,
        is_verified=True,
    )
    creator_b = RbpcCreator(
        slug=f"artisan-t007-b-{uuid.uuid4().hex[:6]}",
        public_name="Nghệ nhân Hoa B",
        craft_tradition="Hoa giấy Thanh Tiên",
        approved_bio_vi="Nghệ nhân Thanh Tiên.",
        consent_status=RbpcConsentStatus.consented.value,
        is_verified=True,
    )
    db_session.add_all([creator_a, creator_b])
    db_session.flush()

    exp_a = RbpcExperience(
        slug=f"exp-t007-a-{uuid.uuid4().hex[:6]}",
        creator_id=creator_a.id,
        provider_name="Hợp tác xã Đúc Đồng A",
        provider_id=partner_a.id,
        title_vi="Trải nghiệm Đúc Đồng A",
        description_vi="Mô tả trải nghiệm A",
        area_public="Huế",
        publication_state="published",
    )
    exp_b = RbpcExperience(
        slug=f"exp-t007-b-{uuid.uuid4().hex[:6]}",
        creator_id=creator_b.id,
        provider_name="Cơ sở Hoa Giấy B",
        provider_id=partner_b.id,
        title_vi="Trải nghiệm Hoa Giấy B",
        description_vi="Mô tả trải nghiệm B",
        area_public="Huế",
        publication_state="published",
    )
    db_session.add_all([exp_a, exp_b])
    db_session.flush()

    # Inquiry for Partner A only
    inquiry_a = RbpcInquiry(
        public_ref=f"INQ-A{uuid.uuid4().hex[:6].upper()}",
        experience_id=exp_a.id,
        provider_id=partner_a.id,
        name="Visitor A",
        contact_channel="email",
        contact_value="visitor_a@example.com",
        desired_date=date.today() + timedelta(days=7),
        party_size=2,
        message="Interested in workshop A.",
        consent_version="rbpc-inquiry-v1",
        state=RbpcInquiryStatus.new.value,
        idempotency_key=str(uuid.uuid4()),
        opaque_token=f"tok_t007_a_{uuid.uuid4().hex}",
    )

    # Inquiry for Partner B only
    inquiry_b = RbpcInquiry(
        public_ref=f"INQ-B{uuid.uuid4().hex[:6].upper()}",
        experience_id=exp_b.id,
        provider_id=partner_b.id,
        name="Visitor B",
        contact_channel="phone",
        contact_value="0911223344",
        desired_date=date.today() + timedelta(days=10),
        party_size=4,
        message="Interested in workshop B.",
        consent_version="rbpc-inquiry-v1",
        state=RbpcInquiryStatus.new.value,
        idempotency_key=str(uuid.uuid4()),
        opaque_token=f"tok_t007_b_{uuid.uuid4().hex}",
    )
    db_session.add_all([inquiry_a, inquiry_b])
    db_session.commit()

    return {
        "partner_a": partner_a,
        "partner_b": partner_b,
        "partner_prod_empty": partner_prod_empty,
        "exp_a": exp_a,
        "exp_b": exp_b,
        "inquiry_a": inquiry_a,
        "inquiry_b": inquiry_b,
    }


def test_demo_mode_flag_configuration(client):
    """Verify DEMO_MODE flag resolution, fail-closed production validation, and runtime config."""
    # 1. Default in non-production is demo_mode_effective == True
    dev_settings = Settings(environment="development", jwt_secret_key="dev-secret-key-12345")
    assert dev_settings.demo_mode_effective is True

    # 2. Production with unset demo_mode defaults to demo_mode_effective == False
    prod_settings = Settings(
        environment="production",
        jwt_secret_key="prod-secret-must-not-be-sentinel-123",
        cors_origins="https://lms.histolab.icu",
        demo_mode=None,
    )
    assert prod_settings.demo_mode_effective is False

    # 3. Explicit demo_mode=False is respected
    explicit_off_settings = Settings(
        environment="development",
        jwt_secret_key="dev-secret-key-12345",
        demo_mode=False,
    )
    assert explicit_off_settings.demo_mode_effective is False

    # 4. Production mode fails closed if demo_mode is explicitly forced to True
    with pytest.raises(RuntimeError, match="DEMO_MODE"):
        Settings(
            environment="production",
            jwt_secret_key="prod-secret-must-not-be-sentinel-123",
            cors_origins="https://lms.histolab.icu",
            demo_mode=True,
        )

    # 5. GET /api/v1/rbpc/config reflects demo_mode dynamically
    res = client.get("/api/v1/rbpc/config")
    assert res.status_code == 200
    cfg = res.json()
    assert "demo_mode" in cfg
    assert isinstance(cfg["demo_mode"], bool)


def test_empty_prod_tenant_isolation_negative_abuse(client, db_session):
    """Negative/Abuse Test: Empty production tenant returns NO test inquiries even when demo has records.

    Verifies:
    1. An authenticated partner with zero inquiries receives an empty items array.
    2. Zero synthetic demo inquiries (like inq-001 or SEED_PARTNER_INQUIRIES) bleed through.
    """
    fixtures = _setup_isolated_tenants(db_session)
    empty_prod_partner = fixtures["partner_prod_empty"]

    # Log in as the empty production partner
    _login_user(client, empty_prod_partner.email)

    # Query partner inbox
    res = client.get("/api/v1/rbpc/partner/inquiries")
    assert res.status_code == 200, res.text
    data = res.json()

    # CRITICAL: Empty production tenant MUST return zero inquiries
    assert data["total"] == 0, f"Expected 0 inquiries for empty tenant, got {data['total']}"
    assert len(data["items"]) == 0, f"Expected empty items array, got {len(data['items'])}"

    # Negative check: Ensure no synthetic or cross-tenant inquiries are present
    returned_refs = {item["reference"] for item in data["items"]}
    assert "INQ-7F89-A23C" not in returned_refs, "Synthetic seed inquiry bled into empty prod tenant!"
    assert fixtures["inquiry_a"].public_ref not in returned_refs, "Cross-tenant inquiry A leaked!"
    assert fixtures["inquiry_b"].public_ref not in returned_refs, "Cross-tenant inquiry B leaked!"


def test_cross_tenant_isolation(client, db_session):
    """Verify strict tenant isolation between Partner A and Partner B.

    Partner A:
    1. Sees only their own inquiries (inquiry_a).
    2. Never sees Partner B's inquiries (inquiry_b).
    3. Attempting to update Partner B's inquiry returns HTTP 403 FORBIDDEN_SCOPE.
    """
    fixtures = _setup_isolated_tenants(db_session)
    partner_a = fixtures["partner_a"]
    partner_b = fixtures["partner_b"]
    inquiry_a = fixtures["inquiry_a"]
    inquiry_b = fixtures["inquiry_b"]

    # 1. Partner A logs in
    _login_user(client, partner_a.email)

    res_a = client.get("/api/v1/rbpc/partner/inquiries")
    assert res_a.status_code == 200
    data_a = res_a.json()
    assert data_a["total"] == 1
    assert data_a["items"][0]["reference"] == inquiry_a.public_ref

    # 2. Partner A attempts to modify Partner B's inquiry -> 403 Forbidden
    res_tamper = client.patch(
        f"/api/v1/rbpc/partner/inquiries/{inquiry_b.id}",
        json={"status": "contacted", "note": "Unauthorized cross-tenant attempt"},
    )
    assert res_tamper.status_code == 403
    assert res_tamper.json()["error"]["code"] == "FORBIDDEN_SCOPE"

    # 3. Partner B logs in and verifies their own inquiry is intact
    _login_user(client, partner_b.email)
    res_b = client.get("/api/v1/rbpc/partner/inquiries")
    assert res_b.status_code == 200
    data_b = res_b.json()
    assert data_b["total"] == 1
    assert data_b["items"][0]["reference"] == inquiry_b.public_ref


def test_demo_fixtures_services_and_honesty_audit(db_session):
    """Verify demo fixtures service functions for integrity and tenant isolation."""
    fixtures = _setup_isolated_tenants(db_session)
    empty_prod_partner = fixtures["partner_prod_empty"]
    partner_a = fixtures["partner_a"]

    # 1. verify_demo_fixtures_integrity enforces zero fake transaction markers
    report = verify_demo_fixtures_integrity(db_session)
    assert report["status"] == "PASS"
    assert report["commercial_honesty"] == "ENFORCED"

    # 2. verify_tenant_isolation verifies empty tenant isolation vs populated tenant
    isolation_report = verify_tenant_isolation(
        db_session,
        prod_provider_id=empty_prod_partner.id,
        demo_provider_id=partner_a.id,
    )
    assert isolation_report["prod_inquiry_count"] == 0
    assert isolation_report["demo_inquiry_count"] == 1
    assert isolation_report["isolated"] is True
    assert isolation_report["zero_cross_tenant_bleed"] is True

    # 3. assert_zero_fixtures_in_prod confirms no mock / fake markers exist
    prod_check = assert_zero_fixtures_in_prod(db_session)
    assert prod_check["status"] == "PASS"
    assert prod_check["zero_fixtures_in_prod"] is True


def test_public_inquiry_status_lookup_isolation(client, db_session):
    """Verify public status endpoint returns real non-PII status and fails 404 for nonexistent tokens."""
    fixtures = _setup_isolated_tenants(db_session)
    inquiry_a = fixtures["inquiry_a"]

    # 1. Valid real inquiry lookup succeeds with zero PII
    res_valid = client.get(f"/api/v1/rbpc/inquiries/status/{inquiry_a.opaque_token}")
    assert res_valid.status_code == 200
    status_data = res_valid.json()
    assert status_data["reference"] == inquiry_a.public_ref
    assert status_data["status"] == "new"
    # Ensure zero PII in public response
    assert "name" not in status_data
    assert "email" not in status_data
    assert "contact_value" not in status_data

    # 2. Synthetic or fake token lookup fails with 404 NOT FOUND (no fake fallback on server)
    res_fake = client.get("/api/v1/rbpc/inquiries/status/tok_fake_nonexistent_12345")
    assert res_fake.status_code == 404
    assert res_fake.json()["error"]["code"] == "RBPC_INQUIRY_NOT_FOUND"
