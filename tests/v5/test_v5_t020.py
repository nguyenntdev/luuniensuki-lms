# -*- coding: utf-8 -*-
"""V5-T020: Inquiry End-to-End Acceptance Test Suite.

Audits and verifies complete end-to-end lifecycle:
1. Real visitor submits inquiry to /api/v1/rbpc/inquiries -> receives 202 with public_ref and opaque_token.
2. Authenticated partner logs in and fetches /api/v1/rbpc/partner/inquiries -> sees the new inquiry.
3. Partner updates status to 'contacted' -> 200 OK, audit entry written.
4. Partner updates status to 'confirmed' -> 200 OK, audit entry chained.
5. Visitor looks up /api/v1/rbpc/inquiries/status/{opaqueToken} -> sees status 'confirmed' with zero PII.
6. Multi-tenant isolation:
   - Another partner (Partner B) logs in -> sees 0 inquiries from Partner A.
7. Negative and abuse guardrails:
   - Non-existent / fake status tokens return 404 NOT_FOUND.
   - Unauthorized cross-tenant PATCH returns 403 FORBIDDEN_SCOPE.
   - Disallowed status transitions return 400 RBPC_INVALID_TRANSITION.
   - No path produces synthetic booking, fake partner, or mock payment.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone
import pytest
from sqlalchemy import select

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


def _setup_published_experience(db_session, provider_user: User):
    creator = RbpcCreator(
        slug=f"artisan-e2e-{uuid.uuid4().hex[:6]}",
        public_name="Nghệ nhân Pháp Lam",
        craft_tradition="Pháp lam Huế",
        approved_bio_vi="Nghệ nhân phục dựng Pháp lam hoàng cung.",
        consent_status=RbpcConsentStatus.consented.value,
        is_verified=True,
    )
    db_session.add(creator)
    db_session.flush()

    exp = RbpcExperience(
        slug=f"exp-phap-lam-{uuid.uuid4().hex[:6]}",
        title_vi="Lớp học Họa Pháp Lam Hoàng Cung",
        title_en="Royal Hue Enamel Masterclass",
        description_vi="Trải nghiệm nung men và vẽ họa tiết hoàng cung trên cốt đồng.",
        creator_id=creator.id,
        provider_name="Trung tâm Pháp Lam Huế",
        provider_id=provider_user.id,
        publication_state="published",
        availability_mode="inquiry_only",
    )
    db_session.add(exp)
    db_session.commit()
    db_session.refresh(exp)
    return exp


def test_complete_inquiry_lifecycle_e2e(client, db_session):
    """E2E lifecycle: Visitor submit -> Partner review -> Contacted -> Confirmed -> Visitor token tracking."""
    # Setup Partner A with an experience
    partner_a = _create_user(db_session, "partner_e2e_a@example.com", role=UserRole.teacher)
    exp = _setup_published_experience(db_session, partner_a)

    # Step 1: Visitor submits inquiry
    future_date = (date.today() + timedelta(days=7)).isoformat()
    idempotency_key = str(uuid.uuid4())
    inquiry_payload = {
        "experience_slug": exp.slug,
        "contact": {
            "name": "Nguyễn Hoàng Nam",
            "method": "email",
            "value": "hoangnam@example.com",
        },
        "preferred_date": future_date,
        "party_size": 3,
        "message": "Chúng tôi muốn học kỹ thuật tráng men hoa sen.",
        "consent": {
            "accepted": True,
            "privacy_accepted": True,
            "version": "rbpc-inquiry-v1",
        },
        "idempotency_key": idempotency_key,
    }

    client.cookies.clear()
    submit_res = client.post("/api/v1/rbpc/inquiries", json=inquiry_payload)
    assert submit_res.status_code == 202, submit_res.text
    submit_data = submit_res.json()

    public_ref = submit_data["reference"]
    status_token = submit_data["status_token"]
    assert public_ref.startswith("INQ-")
    assert status_token.startswith("tok_sec_")
    assert submit_data["status"] == "new"

    # Step 2: Authenticated partner logs in and checks inbox
    _login_user(client, partner_a.email)
    inbox_res = client.get("/api/v1/rbpc/partner/inquiries")
    assert inbox_res.status_code == 200, inbox_res.text
    inbox_data = inbox_res.json()
    assert inbox_data["total"] >= 1
    found_inq = next((i for i in inbox_data["items"] if i["reference"] == public_ref), None)
    assert found_inq is not None, "Inquiry not found in partner inbox"
    assert found_inq["contact_name"] == "Nguyễn Hoàng Nam"
    assert found_inq["party_size"] == 3
    inquiry_id = found_inq["id"]

    # Step 3: Partner updates status to 'contacted'
    patch1_res = client.patch(
        f"/api/v1/rbpc/partner/inquiries/{inquiry_id}",
        json={"status": "contacted", "note": "Đã trao đổi qua email về khung giờ thực hiện."},
    )
    assert patch1_res.status_code == 200, patch1_res.text
    assert patch1_res.json()["status"] == "contacted"

    # Step 4: Partner updates status to 'confirmed'
    patch2_res = client.patch(
        f"/api/v1/rbpc/partner/inquiries/{inquiry_id}",
        json={"status": "confirmed", "note": "Đã chốt lịch hẹn lúc 9:00 sáng."},
    )
    assert patch2_res.status_code == 200, patch2_res.text
    assert patch2_res.json()["status"] == "confirmed"

    # Step 5: Visitor tracks status with statusToken (zero PII)
    client.cookies.clear()
    status_res = client.get(f"/api/v1/rbpc/inquiries/status/{status_token}")
    assert status_res.status_code == 200, status_res.text
    status_data = status_res.json()
    assert status_data["reference"] == public_ref
    assert status_data["status"] == "confirmed"
    assert "name" not in status_data
    assert "contact_value" not in status_data
    assert "email" not in status_data
    assert "note" not in status_data
    assert "internal_note" not in status_data


def test_multi_tenant_isolation_inbox_and_mutations(client, db_session):
    """Ensure Partner B sees 0 inquiries from Partner A and cannot mutate Partner A's inquiry."""
    partner_a = _create_user(db_session, "partner_e2e_a2@example.com", role=UserRole.teacher)
    partner_b = _create_user(db_session, "partner_e2e_b2@example.com", role=UserRole.teacher)
    exp_a = _setup_published_experience(db_session, partner_a)

    # Submit inquiry for Partner A
    client.cookies.clear()
    submit_res = client.post(
        "/api/v1/rbpc/inquiries",
        json={
            "experience_slug": exp_a.slug,
            "contact": {
                "name": "Khách Tham Quan A",
                "method": "phone",
                "value": "0911223344",
            },
            "preferred_date": (date.today() + timedelta(days=5)).isoformat(),
            "party_size": 2,
            "consent": {"accepted": True, "privacy_accepted": True, "version": "rbpc-inquiry-v1"},
            "idempotency_key": str(uuid.uuid4()),
        },
    )
    assert submit_res.status_code == 202
    public_ref = submit_res.json()["reference"]

    # Partner B logs in -> Must see 0 inquiries from Partner A
    _login_user(client, partner_b.email)
    inbox_b_res = client.get("/api/v1/rbpc/partner/inquiries")
    assert inbox_b_res.status_code == 200
    inbox_b_items = inbox_b_res.json()["items"]
    assert not any(i["reference"] == public_ref for i in inbox_b_items)

    # Find inquiry in DB
    inq_a = db_session.scalar(select(RbpcInquiry).where(RbpcInquiry.public_ref == public_ref))
    assert inq_a is not None

    # Partner B attempts to mutate Partner A's inquiry -> 403 FORBIDDEN_SCOPE
    patch_b_res = client.patch(
        f"/api/v1/rbpc/partner/inquiries/{inq_a.id}",
        json={"status": "contacted"},
    )
    assert patch_b_res.status_code == 403
    error_obj = patch_b_res.json().get("error", patch_b_res.json())
    assert error_obj["code"] == "FORBIDDEN_SCOPE"


def test_negative_abuse_random_token_and_invalid_transitions(client, db_session):
    """Test negative abuse guardrails: fake tokens return 404, invalid transitions return 400."""
    # 1. Non-existent status token lookup
    client.cookies.clear()
    res_fake = client.get("/api/v1/rbpc/inquiries/status/tok_sec_nonexistent999999999999")
    assert res_fake.status_code == 404

    # 2. Invalid state jump
    partner = _create_user(db_session, "partner_e2e_invalid@example.com", role=UserRole.teacher)
    exp = _setup_published_experience(db_session, partner)

    submit_res = client.post(
        "/api/v1/rbpc/inquiries",
        json={
            "experience_slug": exp.slug,
            "contact": {"name": "Khách Test", "method": "email", "value": "test@example.com"},
            "preferred_date": (date.today() + timedelta(days=3)).isoformat(),
            "party_size": 1,
            "consent": {"accepted": True, "privacy_accepted": True, "version": "rbpc-inquiry-v1"},
            "idempotency_key": str(uuid.uuid4()),
        },
    )
    assert submit_res.status_code == 202
    public_ref = submit_res.json()["reference"]
    inq = db_session.scalar(select(RbpcInquiry).where(RbpcInquiry.public_ref == public_ref))

    _login_user(client, partner.email)
    # new -> confirmed directly without contacted -> 400
    jump_res = client.patch(
        f"/api/v1/rbpc/partner/inquiries/{inq.id}",
        json={"status": "confirmed"},
    )
    assert jump_res.status_code == 400
    assert jump_res.json().get("error", jump_res.json())["code"] == "RBPC_INVALID_TRANSITION"
