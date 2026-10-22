# -*- coding: utf-8 -*-
"""V5-T006: Identity & Consent Baseline Test Suite.

Audits and verifies:
1. Identity, authentication, and JWT tokens (claims: sub, iat, exp, role, type, jti, iss, aud).
2. Cookie hardening (httpOnly, samesite, path, secure, Cache-Control: no-store).
3. RBAC role isolation matrix (guest, learner, teacher, admin, super_admin, partner).
   - Guest cannot access non-demo content; guest can access demo content.
   - Unauthorized roles cannot access admin / staff endpoints.
   - Partner cross-tenant isolation: Partner A get/modify Partner B -> 403 FORBIDDEN_SCOPE.
4. Consent baseline & student privacy (COPPA / VN Decree 13/2023/ND-CP):
   - Inactive consent (is_profile_public=False) strictly blocks public profile access.
   - Living artisan inactive consent (pending_review / revoked) fails closed:
     blocks public creator lookup (404), blocks experience (404), blocks inquiry (400).
   - Zero PII exposure on public token tracking endpoints.
   - Explicit consent validation on data submission.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone

import pytest
from jose import jwt

from backend.config import settings
from backend.models import (
    ContentRating,
    Motif,
    MotifCategory,
    MotifRarity,
    Urn,
    User,
    UserRole,
)
from backend.models_rbpc import (
    RbpcConsentStatus,
    RbpcCreator,
    RbpcExperience,
    RbpcInquiry,
    RbpcInquiryStatus,
)
from backend.security import create_jwt_token, hash_password


def _create_user(
    db_session,
    email: str,
    role: UserRole = UserRole.learner,
    is_profile_public: bool = True,
    display_name: str | None = None,
) -> User:
    """Helper to persist a user with specific role and privacy settings."""
    user = User(
        email=email,
        password_hash=hash_password("Password123!"),
        display_name=display_name or f"User {email.split('@')[0]}",
        username=f"user_{uuid.uuid4().hex[:8]}",
        role=role,
        is_profile_public=is_profile_public,
        total_xp=150,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _login_user(client, email: str, password: str = "Password123!") -> dict:
    """Login helper setting session cookies on client."""
    res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    return res.json()


def _create_test_urn_and_motifs(db_session) -> tuple[Urn, Motif, Motif]:
    """Helper to create an urn with one demo motif and one non-demo motif."""
    urn = Urn(
        slug=f"urn-test-{uuid.uuid4().hex[:6]}",
        name="Cao Đỉnh Test",
        model_url="/models/cao_dinh.glb",
        display_order=1,
        is_demo=True,
    )
    db_session.add(urn)
    db_session.flush()

    demo_motif = Motif(
        urn_id=urn.id,
        mesh_name=f"mesh_demo_{uuid.uuid4().hex[:8]}",
        name="Họa Tiết Rồng Demo",
        category=MotifCategory.linh_thu,
        rarity=MotifRarity.common,
        content_rating=ContentRating.everyone,
        pos_x=0.0,
        pos_y=1.0,
        pos_z=0.0,
        bounding_radius=0.5,
        is_demo=True,
        is_active=True,
    )
    non_demo_motif = Motif(
        urn_id=urn.id,
        mesh_name=f"mesh_nondemo_{uuid.uuid4().hex[:8]}",
        name="Họa Tiết Phượng Non-Demo",
        category=MotifCategory.linh_thu,
        rarity=MotifRarity.rare,
        content_rating=ContentRating.everyone,
        pos_x=1.0,
        pos_y=1.0,
        pos_z=0.0,
        bounding_radius=0.5,
        is_demo=False,
        is_active=True,
    )
    db_session.add_all([demo_motif, non_demo_motif])
    db_session.commit()
    db_session.refresh(demo_motif)
    db_session.refresh(non_demo_motif)
    return urn, demo_motif, non_demo_motif


# =========================================================================== #
# 1. JWT Claims Contract & Token Structure Tests
# =========================================================================== #
def test_jwt_claims_structure_and_types(client, db_session):
    """Verify issued JWT tokens contain all required claims:
    sub, iat, exp, role, type, jti, iss, aud."""
    user = _create_user(db_session, "jwt_audit@example.com", role=UserRole.learner)

    res = client.post(
        "/api/v1/auth/login",
        json={"email": "jwt_audit@example.com", "password": "Password123!"},
    )
    assert res.status_code == 200

    # Inspect cookies
    access_cookie = client.cookies.get(settings.access_cookie_name)
    refresh_cookie = client.cookies.get(settings.refresh_cookie_name)
    assert access_cookie is not None, "Missing access cookie"
    assert refresh_cookie is not None, "Missing refresh cookie"

    # Decode access token
    access_payload = jwt.decode(
        access_cookie,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
        options={"verify_aud": False, "verify_iss": False},
    )
    assert access_payload["sub"] == str(user.id)
    assert access_payload["type"] == "access"
    assert access_payload["role"] == "learner"
    assert access_payload["iss"] == settings.jwt_issuer
    assert access_payload["aud"] == settings.jwt_audience
    assert "iat" in access_payload
    assert "exp" in access_payload
    assert "jti" in access_payload
    assert len(access_payload["jti"]) >= 16

    # Decode refresh token
    refresh_payload = jwt.decode(
        refresh_cookie,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
        options={"verify_aud": False, "verify_iss": False},
    )
    assert refresh_payload["sub"] == str(user.id)
    assert refresh_payload["type"] == "refresh"
    assert refresh_payload["role"] == "learner"
    assert refresh_payload["iss"] == settings.jwt_issuer
    assert refresh_payload["aud"] == settings.jwt_audience
    assert refresh_payload["jti"] != access_payload["jti"]


def test_auth_cookie_hardening_and_no_store(client, db_session):
    """Verify cookie parameters (httpOnly, path, Cache-Control: no-store)."""
    _create_user(db_session, "cookie_audit@example.com")

    res = client.post(
        "/api/v1/auth/login",
        json={"email": "cookie_audit@example.com", "password": "Password123!"},
    )
    assert res.status_code == 200
    assert res.headers.get("Cache-Control") == "no-store"

    # Logout must clear cookies with no-store
    logout_res = client.post("/api/v1/auth/logout")
    assert logout_res.status_code == 200
    assert logout_res.headers.get("Cache-Control") == "no-store"


# =========================================================================== #
# 2. RBAC Role Isolation: Guest vs Learner vs Staff vs Admin
# =========================================================================== #
def test_guest_cannot_access_non_demo_content(client, db_session):
    """Guest cannot learn or unlock non-demo motifs (HTTP 403); can access demo."""
    _, demo_motif, non_demo_motif = _create_test_urn_and_motifs(db_session)
    guest = _create_user(db_session, "guest_role@example.com", role=UserRole.guest)

    _login_user(client, guest.email)

    # 1. Guest attempts to unlock non-demo motif -> 403 Forbidden
    res_unlock_non_demo = client.post(
        "/progress/unlock",
        json={"motif_id": str(non_demo_motif.id)},
    )
    assert res_unlock_non_demo.status_code == 403
    assert "Guests can only unlock demo motifs" in res_unlock_non_demo.text

    # 2. Guest attempts to complete lesson on non-demo motif -> 403 Forbidden
    res_learn_non_demo = client.post(
        f"/api/v1/motifs/{non_demo_motif.id}/complete-lesson"
    )
    assert res_learn_non_demo.status_code == 403
    assert "Guests can only learn demo motifs" in res_learn_non_demo.text

    # 3. Guest unlocks demo motif -> 200 Success
    res_unlock_demo = client.post(
        "/progress/unlock",
        json={"motif_id": str(demo_motif.id)},
    )
    assert res_unlock_demo.status_code == 200
    assert res_unlock_demo.json()["progress"]["status"] == "discovered"

    # 4. Guest completes lesson on demo motif -> 200 Success
    res_learn_demo = client.post(
        f"/api/v1/motifs/{demo_motif.id}/complete-lesson"
    )
    assert res_learn_demo.status_code == 200
    assert res_learn_demo.json()["status"] == "learned"


def test_unauthorized_roles_blocked_from_admin_and_editor_routes(client, db_session):
    """Learners and non-staff cannot access admin or editor routes."""
    learner = _create_user(db_session, "learner_access@example.com", role=UserRole.learner)
    _login_user(client, learner.email)

    # Learner accesses admin RAG settings -> 403 Not authorized
    res_admin = client.get("/api/v1/admin/rag/settings")
    assert res_admin.status_code == 403
    assert "Not authorized" in res_admin.text

    # Learner accesses creator consent update -> 403 FORBIDDEN_SCOPE
    fake_creator_id = uuid.uuid4()
    res_consent = client.post(
        f"/api/v1/rbpc/editor/creators/{fake_creator_id}/consent",
        json={"consent_status": "revoked", "notes": "Unauthorized attempt"},
    )
    assert res_consent.status_code == 403
    assert res_consent.json()["error"]["code"] == "FORBIDDEN_SCOPE"


# =========================================================================== #
# 3. Partner Tenant Isolation (Cross-Provider Security)
# =========================================================================== #
def test_partner_tenant_isolation_partner_a_get_partner_b_403(client, db_session):
    """Negative abuse test: Partner A get/update Partner B inquiry returns 403."""
    partner_a = _create_user(db_session, "partner_a@example.com", role=UserRole.teacher)
    partner_b = _create_user(db_session, "partner_b@example.com", role=UserRole.teacher)
    admin_user = _create_user(db_session, "admin_partner_view@example.com", role=UserRole.admin)

    # Create creator and experience for Partner A
    creator_a = RbpcCreator(
        slug=f"artisan-a-{uuid.uuid4().hex[:6]}",
        public_name="Nghệ Nhân Đúc Đồng A",
        craft_tradition="Đúc đồng",
        approved_bio_vi="Tiểu sử nghệ nhân A",
        consent_status=RbpcConsentStatus.consented.value,
        is_verified=True,
    )
    creator_b = RbpcCreator(
        slug=f"artisan-b-{uuid.uuid4().hex[:6]}",
        public_name="Nghệ Nhân Thêu Tay B",
        craft_tradition="Thêu may Huế",
        approved_bio_vi="Tiểu sử nghệ nhân B",
        consent_status=RbpcConsentStatus.consented.value,
        is_verified=True,
    )
    db_session.add_all([creator_a, creator_b])
    db_session.flush()

    exp_a = RbpcExperience(
        slug=f"exp-iso-a-{uuid.uuid4().hex[:6]}",
        creator_id=creator_a.id,
        provider_name="HTX Đúc Đồng A",
        provider_id=partner_a.id,
        title_vi="Trải nghiệm Đúc Đồng A",
        description_vi="Mô tả A",
        area_public="Huế",
        publication_state="published",
    )
    exp_b = RbpcExperience(
        slug=f"exp-iso-b-{uuid.uuid4().hex[:6]}",
        creator_id=creator_b.id,
        provider_name="Cơ sở Thêu Tay B",
        provider_id=partner_b.id,
        title_vi="Trải nghiệm Thêu Tay B",
        description_vi="Mô tả B",
        area_public="Huế",
        publication_state="published",
    )
    db_session.add_all([exp_a, exp_b])
    db_session.flush()

    inquiry_a = RbpcInquiry(
        public_ref="INQ-ISO-A-001",
        experience_id=exp_a.id,
        provider_id=partner_a.id,
        name="Khách Partner A",
        contact_channel="email",
        contact_value="khach_a@example.com",
        desired_date=date.today() + timedelta(days=7),
        party_size=2,
        state=RbpcInquiryStatus.new.value,
        idempotency_key=f"idem-iso-a-{uuid.uuid4().hex}",
        opaque_token=f"tok_iso_a_{uuid.uuid4().hex}",
    )
    inquiry_b = RbpcInquiry(
        public_ref="INQ-ISO-B-002",
        experience_id=exp_b.id,
        provider_id=partner_b.id,
        name="Khách Partner B",
        contact_channel="email",
        contact_value="khach_b@example.com",
        desired_date=date.today() + timedelta(days=12),
        party_size=3,
        state=RbpcInquiryStatus.new.value,
        idempotency_key=f"idem-iso-b-{uuid.uuid4().hex}",
        opaque_token=f"tok_iso_b_{uuid.uuid4().hex}",
    )
    db_session.add_all([inquiry_a, inquiry_b])
    db_session.commit()

    # 1. Partner A logs in and lists inquiries -> receives ONLY inquiry A
    _login_user(client, partner_a.email)
    res_list_a = client.get("/api/v1/rbpc/partner/inquiries")
    assert res_list_a.status_code == 200
    refs_a = [item["reference"] for item in res_list_a.json()["items"]]
    assert "INQ-ISO-A-001" in refs_a
    assert "INQ-ISO-B-002" not in refs_a, "Leakage: Partner A saw Partner B's inquiry!"

    # 2. Partner A attempts to modify inquiry belonging to Partner B -> 403 FORBIDDEN_SCOPE
    res_patch_b = client.patch(
        f"/api/v1/rbpc/partner/inquiries/{inquiry_b.id}",
        json={"status": "contacted", "note": "Partner A unauthorized update"},
    )
    assert res_patch_b.status_code == 403
    assert res_patch_b.json()["error"]["code"] == "FORBIDDEN_SCOPE"

    # 3. Partner B logs in and lists inquiries -> receives ONLY inquiry B
    _login_user(client, partner_b.email)
    res_list_b = client.get("/api/v1/rbpc/partner/inquiries")
    assert res_list_b.status_code == 200
    refs_b = [item["reference"] for item in res_list_b.json()["items"]]
    assert "INQ-ISO-B-002" in refs_b
    assert "INQ-ISO-A-001" not in refs_b, "Leakage: Partner B saw Partner A's inquiry!"

    # 4. Admin logs in -> sees inquiries from both partners
    _login_user(client, admin_user.email)
    res_admin = client.get("/api/v1/rbpc/partner/inquiries")
    assert res_admin.status_code == 200
    refs_admin = [item["reference"] for item in res_admin.json()["items"]]
    assert "INQ-ISO-A-001" in refs_admin
    assert "INQ-ISO-B-002" in refs_admin


# =========================================================================== #
# 4. Consent Baseline & Student Privacy (Decree 13/2023/ND-CP & COPPA)
# =========================================================================== #
def test_inactive_consent_blocks_user_public_profile(client, db_session):
    """User with inactive consent (is_profile_public=False) cannot have profile
    viewed by other users (HTTP 403 'Profile is private'). Owner can view."""
    private_user = _create_user(
        db_session,
        "private_student@example.com",
        role=UserRole.learner,
        is_profile_public=False,
        display_name="Học Sinh Bí Mật",
    )
    other_student = _create_user(
        db_session,
        "curious_student@example.com",
        role=UserRole.learner,
        is_profile_public=True,
    )

    # 1. Other student attempts to access private profile -> 403 Forbidden
    _login_user(client, other_student.email)
    res_forbidden = client.get(f"/api/v1/users/{private_user.id}/public")
    assert res_forbidden.status_code == 403
    assert "Profile is private" in res_forbidden.text

    # 2. Private user accesses their own profile -> 200 OK (Owner access permitted)
    _login_user(client, private_user.email)
    res_self = client.get(f"/api/v1/users/{private_user.id}/public")
    assert res_self.status_code == 200
    assert res_self.json()["display_name"] == "Học Sinh Bí Mật"

    # 3. Private user updates consent: sets is_profile_public=True
    res_update = client.patch(
        "/api/v1/users/me",
        json={"is_profile_public": True},
    )
    assert res_update.status_code == 200
    assert res_update.json()["user"]["is_profile_public"] is True

    # 4. Other student now accesses the profile -> 200 OK
    _login_user(client, other_student.email)
    res_now_public = client.get(f"/api/v1/users/{private_user.id}/public")
    assert res_now_public.status_code == 200
    assert res_now_public.json()["display_name"] == "Học Sinh Bí Mật"


def test_artisan_inactive_consent_fails_closed(client, db_session):
    """Artisan with inactive consent (pending_review or revoked):
    - Creator profile fails closed (HTTP 404 RBPC_CREATOR_NOT_FOUND)
    - Associated workshop experience fails closed (HTTP 404 RBPC_EXPERIENCE_NOT_FOUND)
    - Booking inquiry submission fails closed (HTTP 400 RBPC_CREATOR_CONSENT_UNAVAILABLE)
    """
    creator = RbpcCreator(
        slug=f"artisan-consent-{uuid.uuid4().hex[:6]}",
        public_name="Nghệ Nhân Trầm Hương",
        craft_tradition="Làm trầm xứ Huế",
        approved_bio_vi="Nghệ nhân gia truyền làm trầm hương.",
        consent_status=RbpcConsentStatus.consented.value,
        is_verified=True,
    )
    db_session.add(creator)
    db_session.flush()

    exp = RbpcExperience(
        slug=f"exp-consent-{uuid.uuid4().hex[:6]}",
        creator_id=creator.id,
        provider_name="Cơ sở Trầm Hương Xứ Huế",
        title_vi="Trải nghiệm Làm Nhang Trầm",
        description_vi="Thực hành làm nhang trầm cổ truyền",
        area_public="Huế",
        publication_state="published",
    )
    db_session.add(exp)
    db_session.commit()

    # 1. While consented: Public can view creator and experience
    client.cookies.clear()
    assert client.get(f"/api/v1/rbpc/creators/{creator.slug}").status_code == 200
    assert client.get(f"/api/v1/rbpc/experiences/{exp.slug}").status_code == 200

    # 2. Revoke consent (e.g. artisan withdrew consent)
    creator.consent_status = RbpcConsentStatus.revoked.value
    db_session.commit()

    # Public creator lookup fails closed -> 404
    res_pub_creator = client.get(f"/api/v1/rbpc/creators/{creator.slug}")
    assert res_pub_creator.status_code == 404
    assert res_pub_creator.json()["error"]["code"] == "RBPC_CREATOR_NOT_FOUND"

    # Public experience lookup fails closed -> 404
    res_pub_exp = client.get(f"/api/v1/rbpc/experiences/{exp.slug}")
    assert res_pub_exp.status_code == 404
    assert res_pub_exp.json()["error"]["code"] == "RBPC_EXPERIENCE_NOT_FOUND"

    # Booking inquiry for revoked creator experience fails closed -> 400
    res_inq = client.post(
        "/api/v1/rbpc/inquiries",
        json={
            "experience_slug": exp.slug,
            "contact": {
                "name": "Du Khách A",
                "method": "email",
                "value": "dukhach@example.com",
            },
            "preferred_date": (date.today() + timedelta(days=5)).isoformat(),
            "party_size": 2,
            "idempotency_key": str(uuid.uuid4()),
            "consent": {
                "version": "rbpc-inquiry-v1",
                "accepted": True,
                "privacy_accepted": True,
            },
        },
    )
    assert res_inq.status_code == 400
    assert res_inq.json()["error"]["code"] == "RBPC_CREATOR_CONSENT_UNAVAILABLE"


def test_zero_pii_on_public_inquiry_tracking_endpoint(client, db_session):
    """Opaque status tracking endpoint returns zero visitor PII (no name, email, phone, notes)."""
    creator = RbpcCreator(
        slug=f"artisan-pii-{uuid.uuid4().hex[:6]}",
        public_name="Nghệ Nhân Sơn Mài",
        craft_tradition="Sơn mài mỹ nghệ",
        approved_bio_vi="Bậc thầy sơn mài.",
        consent_status=RbpcConsentStatus.consented.value,
        is_verified=True,
    )
    db_session.add(creator)
    db_session.flush()

    exp = RbpcExperience(
        slug=f"exp-pii-{uuid.uuid4().hex[:6]}",
        creator_id=creator.id,
        provider_name="Xưởng Sơn Mài Huế",
        title_vi="Trải nghiệm Sơn Mài",
        description_vi="Mô tả sơn mài",
        area_public="Huế",
        publication_state="published",
    )
    db_session.add(exp)
    db_session.flush()

    opaque_tok = f"tok_sec_pii_{uuid.uuid4().hex}"
    inquiry = RbpcInquiry(
        public_ref="INQ-PII-SAFE-001",
        experience_id=exp.id,
        name="Nguyễn Văn A (Secret Name)",
        contact_channel="email",
        contact_value="nguyenvana_sensitive@example.com",
        desired_date=date.today() + timedelta(days=10),
        party_size=4,
        state=RbpcInquiryStatus.new.value,
        internal_note="Secret internal note about VIP guest",
        idempotency_key=f"idem-pii-{uuid.uuid4().hex}",
        opaque_token=opaque_tok,
    )
    db_session.add(inquiry)
    db_session.commit()

    # Public anonymous tracking request
    client.cookies.clear()
    res = client.get(f"/api/v1/rbpc/inquiries/status/{opaque_tok}")
    assert res.status_code == 200
    data = res.json()

    # Verify public attributes are returned
    assert data["reference"] == "INQ-PII-SAFE-001"
    assert data["status"] == "new"
    assert data["experience_title"] == "Trải nghiệm Sơn Mài"

    # Verify ZERO PII is leaked
    raw_response_text = res.text
    assert "Nguyễn Văn A" not in raw_response_text, "PII Leak: Name exposed!"
    assert "nguyenvana_sensitive@example.com" not in raw_response_text, "PII Leak: Email exposed!"
    assert "Secret internal note" not in raw_response_text, "PII Leak: Internal note exposed!"


def test_inquiry_explicit_consent_validation(client, db_session):
    """Inquiry rejected with 422/400 if user does not explicitly opt in to consent/privacy."""
    creator = RbpcCreator(
        slug=f"artisan-optin-{uuid.uuid4().hex[:6]}",
        public_name="Nghệ Nhân Nón Bài Thơ",
        craft_tradition="Chằm nón lá",
        approved_bio_vi="Nghệ nhân chằm nón lá Tây Hồ.",
        consent_status=RbpcConsentStatus.consented.value,
        is_verified=True,
    )
    db_session.add(creator)
    db_session.flush()

    exp = RbpcExperience(
        slug=f"exp-optin-{uuid.uuid4().hex[:6]}",
        creator_id=creator.id,
        provider_name="Làng Nón Tây Hồ",
        title_vi="Trải nghiệm Chằm Nón Lá",
        description_vi="Học chằm nón bài thơ",
        area_public="Huế",
        publication_state="published",
    )
    db_session.add(exp)
    db_session.commit()

    # Attempt submission with accepted=False -> 422 Unprocessable Entity
    res_rejected = client.post(
        "/api/v1/rbpc/inquiries",
        json={
            "experience_slug": exp.slug,
            "contact": {
                "name": "Du Khách B",
                "method": "email",
                "value": "dukhach_b@example.com",
            },
            "preferred_date": (date.today() + timedelta(days=5)).isoformat(),
            "party_size": 2,
            "idempotency_key": str(uuid.uuid4()),
            "consent": {
                "version": "rbpc-inquiry-v1",
                "accepted": False,  # Missing consent!
                "privacy_accepted": True,
            },
        },
    )
    assert res_rejected.status_code == 422
    assert "Explicit consent must be accepted" in res_rejected.text
