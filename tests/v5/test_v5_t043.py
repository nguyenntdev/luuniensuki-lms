# -*- coding: utf-8 -*-
"""V5-T043 (Wave W04, Slot A03): Admin Map Access Control Test Suite.

Audits and verifies:
1. Server-side RBAC on administrative map endpoints:
   - Unauthenticated requests receive HTTP 401 Unauthorized across all admin endpoints.
   - Non-privileged accounts (learner, guest) receive HTTP 403 Forbidden on raw API:
     * GET /api/v1/imperial/admin/maps
     * GET /api/v1/imperial/admin/maps/{map_id}/annotations
     * POST /api/v1/imperial/admin/maps/{map_id}/annotations
     * PATCH /api/v1/imperial/admin/annotations/{id}
     * DELETE /api/v1/imperial/admin/annotations/{id}
     * POST /api/v1/imperial/admin/maps/{map_id}/publish
     * GET /api/v1/imperial/admin/annotations/{id}/audit
   - Teacher (STAFF_ROLES) has permission to curate and manage annotations, but is rejected
     with HTTP 403 Forbidden on map publication (strictly reserved for ADMIN_ROLES).
2. Editor Ownership enforcement:
   - The original editor/author who created an annotation can update and archive their own marker.
   - Another editor/teacher cannot modify or archive an annotation created by someone else
     (HTTP 403 Forbidden: IMPERIAL_ANNOTATION_FORBIDDEN).
   - System administrators (ADMIN_ROLES) retain override authority to update or archive any marker.
3. Row-version optimistic concurrency control:
   - Modifications require passing current row_version.
   - Out-of-date row_version returns HTTP 409 Conflict (IMPERIAL_CONCURRENCY_CONFLICT).
   - If-Match HTTP header is validated against current row_version.
4. CSRF and Bearer token defense-in-depth:
   - Cookie-authenticated mutating requests (POST, PATCH, DELETE) lacking custom anti-CSRF headers
     (e.g. X-Requested-With) are rejected with HTTP 403 Forbidden.
   - Cross-site browser requests (Sec-Fetch-Site: cross-site) with ambient cookies are rejected with HTTP 403.
   - Cookie-authenticated requests with X-Requested-With: XMLHttpRequest succeed.
   - Direct API Bearer token requests (Authorization: Bearer <token>) succeed without requiring CSRF headers.
5. Tamper-evident Audit Logging:
   - All marker operations (create, update, archive) generate immutable ImperialAnnotationAudit rows.
   - Full audit trail is inspectable via GET /api/v1/imperial/admin/annotations/{id}/audit.
"""
from __future__ import annotations

import os
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select

from backend.imperial_models import (
    CONTENT_SCOPE_IMPERIAL,
    ImperialAnnotationAudit,
    ImperialMapAnnotation,
    ImperialMapAsset,
    ImperialSite,
    ImperialZone,
)
from backend.models import User, UserRole
from backend.security import hash_password

REPO_ROOT = Path(__file__).resolve().parents[2]


# --------------------------------------------------------------------------- #
# Helpers & Fixtures
# --------------------------------------------------------------------------- #
@pytest.fixture(autouse=True)
def _reset_auth_rate_limit():
    """Reset auth rate limit state before each test."""
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


def _login(client, email: str, password: str = "Password123!") -> str:
    """Switch active session on client and return access token."""
    client.cookies.clear()
    res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    token = client.cookies.get("luuniensuki_access") or res.cookies.get("luuniensuki_access") or ""
    return token


def _seed_map_and_site(db_session, creator: User) -> tuple[ImperialMapAsset, ImperialSite]:
    """Seed test zone, site, and map asset."""
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


# --------------------------------------------------------------------------- #
# 1. Unauthenticated Request Rejection Tests
# --------------------------------------------------------------------------- #
def test_unauthenticated_requests_receive_401(client, db_session):
    """Anonymous client without auth headers or cookies must receive HTTP 401."""
    client.cookies.clear()
    admin_user = _create_user(db_session, f"admin_{uuid4().hex[:6]}@example.com", role=UserRole.admin)
    map_asset, site = _seed_map_and_site(db_session, admin_user)
    fake_id = uuid4()

    # 1. List maps
    r1 = client.get("/api/v1/imperial/admin/maps")
    assert r1.status_code == 401

    # 2. Get map annotations
    r2 = client.get(f"/api/v1/imperial/admin/maps/{map_asset.id}/annotations")
    assert r2.status_code == 401

    # 3. Create annotation
    r3 = client.post(
        f"/api/v1/imperial/admin/maps/{map_asset.id}/annotations",
        json={"site_id": str(site.id), "u": 0.5, "v": 0.5},
    )
    assert r3.status_code == 401

    # 4. Update annotation
    r4 = client.patch(
        f"/api/v1/imperial/admin/annotations/{fake_id}",
        json={"u": 0.6, "v": 0.6, "row_version": 1},
    )
    assert r4.status_code == 401

    # 5. Delete annotation
    r5 = client.delete(f"/api/v1/imperial/admin/annotations/{fake_id}")
    assert r5.status_code == 401

    # 6. Publish map
    r6 = client.post(f"/api/v1/imperial/admin/maps/{map_asset.id}/publish")
    assert r6.status_code == 401

    # 7. Audit log
    r7 = client.get(f"/api/v1/imperial/admin/annotations/{fake_id}/audit")
    assert r7.status_code == 401


# --------------------------------------------------------------------------- #
# 2. Negative Abuse Tests: Non-Privileged Roles
# --------------------------------------------------------------------------- #
def test_negative_abuse_learner_and_guest_receive_403(client, db_session):
    """Users with learner or guest roles must receive HTTP 403 on all admin endpoints."""
    admin_user = _create_user(db_session, f"admin_{uuid4().hex[:6]}@example.com", role=UserRole.admin)
    learner = _create_user(db_session, f"learner_{uuid4().hex[:6]}@example.com", role=UserRole.learner)
    guest = _create_user(db_session, f"guest_{uuid4().hex[:6]}@example.com", role=UserRole.guest)
    map_asset, site = _seed_map_and_site(db_session, admin_user)
    fake_id = uuid4()

    csrf_headers = {"X-Requested-With": "XMLHttpRequest"}

    # Test Learner
    _login(client, learner.email)

    assert client.get("/api/v1/imperial/admin/maps").status_code == 403
    assert client.get(f"/api/v1/imperial/admin/maps/{map_asset.id}/annotations").status_code == 403
    assert client.post(
        f"/api/v1/imperial/admin/maps/{map_asset.id}/annotations",
        json={"site_id": str(site.id), "u": 0.5, "v": 0.5},
        headers=csrf_headers,
    ).status_code == 403
    assert client.patch(
        f"/api/v1/imperial/admin/annotations/{fake_id}",
        json={"u": 0.6, "v": 0.6, "row_version": 1},
        headers=csrf_headers,
    ).status_code == 403
    assert client.delete(f"/api/v1/imperial/admin/annotations/{fake_id}", headers=csrf_headers).status_code == 403
    assert client.post(f"/api/v1/imperial/admin/maps/{map_asset.id}/publish", headers=csrf_headers).status_code == 403
    assert client.get(f"/api/v1/imperial/admin/annotations/{fake_id}/audit").status_code == 403

    # Test Guest
    _login(client, guest.email)

    assert client.get("/api/v1/imperial/admin/maps").status_code == 403
    assert client.post(
        f"/api/v1/imperial/admin/maps/{map_asset.id}/annotations",
        json={"site_id": str(site.id), "u": 0.5, "v": 0.5},
        headers=csrf_headers,
    ).status_code == 403


def test_teacher_role_boundary_cannot_publish_map(client, db_session):
    """Teachers have staff access for curation, but cannot execute map publication."""
    teacher = _create_user(db_session, f"teacher_{uuid4().hex[:6]}@example.com", role=UserRole.teacher)
    map_asset, site = _seed_map_and_site(db_session, teacher)

    _login(client, teacher.email)
    csrf_headers = {"X-Requested-With": "XMLHttpRequest"}

    # Teacher CAN view admin maps
    res_list = client.get("/api/v1/imperial/admin/maps")
    assert res_list.status_code == 200

    # Teacher CAN create annotation
    res_create = client.post(
        f"/api/v1/imperial/admin/maps/{map_asset.id}/annotations",
        json={
            "site_id": str(site.id),
            "u": 0.45,
            "v": 0.55,
            "label": "Ghim giáo viên",
        },
        headers=csrf_headers,
    )
    assert res_create.status_code == 201

    # Teacher CANNOT publish map (strictly requires ADMIN_ROLES)
    res_publish = client.post(
        f"/api/v1/imperial/admin/maps/{map_asset.id}/publish",
        headers=csrf_headers,
    )
    assert res_publish.status_code == 403


# --------------------------------------------------------------------------- #
# 3. Editor Ownership Enforcement Tests
# --------------------------------------------------------------------------- #
def test_editor_ownership_lifecycle_and_cross_editor_denial(client, db_session):
    """An editor owns their annotation; other non-admin staff are denied mutation."""
    teacher1 = _create_user(db_session, f"t1_{uuid4().hex[:6]}@example.com", role=UserRole.teacher)
    teacher2 = _create_user(db_session, f"t2_{uuid4().hex[:6]}@example.com", role=UserRole.teacher)
    admin = _create_user(db_session, f"adm_{uuid4().hex[:6]}@example.com", role=UserRole.admin)
    map_asset, site = _seed_map_and_site(db_session, admin)

    csrf_headers = {"X-Requested-With": "XMLHttpRequest"}

    # 1. Teacher 1 creates annotation
    _login(client, teacher1.email)
    res_create = client.post(
        f"/api/v1/imperial/admin/maps/{map_asset.id}/annotations",
        json={
            "site_id": str(site.id),
            "u": 0.35,
            "v": 0.65,
            "label": "Ghim của Teacher 1",
            "position_confidence": "verified",
        },
        headers=csrf_headers,
    )
    assert res_create.status_code == 201
    anno_data = res_create.json()
    anno_id = anno_data["id"]
    assert anno_data["created_by"] == str(teacher1.id)
    assert anno_data["row_version"] == 1

    # 2. Teacher 1 successfully updates their own annotation
    res_update_t1 = client.patch(
        f"/api/v1/imperial/admin/annotations/{anno_id}",
        json={"u": 0.36, "v": 0.66, "row_version": 1},
        headers=csrf_headers,
    )
    assert res_update_t1.status_code == 200
    assert res_update_t1.json()["row_version"] == 2

    # 3. Teacher 2 attempts to update Teacher 1's annotation -> 403 Forbidden
    _login(client, teacher2.email)
    res_update_t2 = client.patch(
        f"/api/v1/imperial/admin/annotations/{anno_id}",
        json={"u": 0.40, "v": 0.70, "row_version": 2},
        headers=csrf_headers,
    )
    assert res_update_t2.status_code == 403
    err_t2 = res_update_t2.json().get("error", {})
    assert err_t2.get("code") == "IMPERIAL_ANNOTATION_FORBIDDEN"

    # 4. Teacher 2 attempts to archive/delete Teacher 1's annotation -> 403 Forbidden
    res_del_t2 = client.delete(
        f"/api/v1/imperial/admin/annotations/{anno_id}",
        headers=csrf_headers,
    )
    assert res_del_t2.status_code == 403
    assert res_del_t2.json().get("error", {}).get("code") == "IMPERIAL_ANNOTATION_FORBIDDEN"

    # 5. Admin override: Admin CAN update Teacher 1's annotation
    _login(client, admin.email)
    res_update_admin = client.patch(
        f"/api/v1/imperial/admin/annotations/{anno_id}",
        json={"u": 0.38, "v": 0.68, "label": "Admin đã hiệu đính", "row_version": 2},
        headers=csrf_headers,
    )
    assert res_update_admin.status_code == 200
    assert res_update_admin.json()["label"] == "Admin đã hiệu đính"
    assert res_update_admin.json()["row_version"] == 3

    # 6. Admin override: Admin CAN archive Teacher 1's annotation
    res_del_admin = client.delete(
        f"/api/v1/imperial/admin/annotations/{anno_id}",
        headers=csrf_headers,
    )
    assert res_del_admin.status_code == 200
    assert res_del_admin.json()["ok"] is True


# --------------------------------------------------------------------------- #
# 4. Row Version Optimistic Concurrency Control Tests
# --------------------------------------------------------------------------- #
def test_optimistic_concurrency_and_if_match_validation(client, db_session):
    """Verify 409 Conflict rejection on stale row_version or mismatched If-Match."""
    teacher = _create_user(db_session, f"t_occ_{uuid4().hex[:6]}@example.com", role=UserRole.teacher)
    map_asset, site = _seed_map_and_site(db_session, teacher)
    csrf_headers = {"X-Requested-With": "XMLHttpRequest"}

    _login(client, teacher.email)
    res_create = client.post(
        f"/api/v1/imperial/admin/maps/{map_asset.id}/annotations",
        json={"site_id": str(site.id), "u": 0.5, "v": 0.5},
        headers=csrf_headers,
    )
    assert res_create.status_code == 201
    anno_id = res_create.json()["id"]
    assert res_create.json()["row_version"] == 1

    # First valid update: row_version 1 -> 2
    res_v1 = client.patch(
        f"/api/v1/imperial/admin/annotations/{anno_id}",
        json={"u": 0.51, "v": 0.51, "row_version": 1},
        headers=csrf_headers,
    )
    assert res_v1.status_code == 200
    assert res_v1.json()["row_version"] == 2

    # Stale update with row_version 1 must fail with 409 Conflict
    res_stale = client.patch(
        f"/api/v1/imperial/admin/annotations/{anno_id}",
        json={"u": 0.52, "v": 0.52, "row_version": 1},
        headers=csrf_headers,
    )
    assert res_stale.status_code == 409
    assert res_stale.json()["error"]["code"] == "IMPERIAL_CONCURRENCY_CONFLICT"
    assert res_stale.json()["error"]["details"]["current_row_version"] == 2

    # Valid update with If-Match header matching row_version 2
    res_if_match = client.patch(
        f"/api/v1/imperial/admin/annotations/{anno_id}",
        json={"u": 0.53, "v": 0.53, "row_version": 2},
        headers={**csrf_headers, "If-Match": '"row-version-2"'},
    )
    assert res_if_match.status_code == 200
    assert res_if_match.json()["row_version"] == 3

    # Mismatched If-Match header must fail with 409 Conflict
    res_mismatch = client.patch(
        f"/api/v1/imperial/admin/annotations/{anno_id}",
        json={"u": 0.54, "v": 0.54, "row_version": 3},
        headers={**csrf_headers, "If-Match": '"row-version-99"'},
    )
    assert res_mismatch.status_code == 409
    assert res_mismatch.json()["error"]["code"] == "IMPERIAL_CONCURRENCY_CONFLICT"


# --------------------------------------------------------------------------- #
# 5. CSRF and Bearer Token Protection Tests
# --------------------------------------------------------------------------- #
def test_csrf_cookie_protection_and_bearer_exemption(client, db_session):
    """Mutating cookie requests without anti-CSRF headers fail; Bearer token succeeds."""
    teacher = _create_user(db_session, f"t_csrf_{uuid4().hex[:6]}@example.com", role=UserRole.teacher)
    map_asset, site = _seed_map_and_site(db_session, teacher)

    token = _login(client, teacher.email)
    payload = {"site_id": str(site.id), "u": 0.44, "v": 0.55}

    # 1. Cookie session without X-Requested-With / anti-CSRF header -> 403 Forbidden
    res_no_csrf = client.post(
        f"/api/v1/imperial/admin/maps/{map_asset.id}/annotations",
        json=payload,
    )
    assert res_no_csrf.status_code == 403
    assert "CSRF validation failed" in res_no_csrf.text

    # 2. Cookie session with Sec-Fetch-Site: cross-site -> 403 Forbidden
    res_cross_site = client.post(
        f"/api/v1/imperial/admin/maps/{map_asset.id}/annotations",
        json=payload,
        headers={"Sec-Fetch-Site": "cross-site", "X-Requested-With": "XMLHttpRequest"},
    )
    assert res_cross_site.status_code == 403
    assert "cross-site cookie mutation rejected" in res_cross_site.text

    # 3. Cookie session WITH X-Requested-With: XMLHttpRequest -> 201 Created
    res_with_csrf = client.post(
        f"/api/v1/imperial/admin/maps/{map_asset.id}/annotations",
        json=payload,
        headers={"X-Requested-With": "XMLHttpRequest"},
    )
    assert res_with_csrf.status_code == 201
    anno_id = res_with_csrf.json()["id"]

    # 4. Bearer token request (cookies purged) -> Succeeds without X-Requested-With
    client.cookies.clear()
    res_bearer = client.patch(
        f"/api/v1/imperial/admin/annotations/{anno_id}",
        json={"u": 0.46, "v": 0.56, "row_version": 1},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_bearer.status_code == 200
    assert res_bearer.json()["row_version"] == 2


# --------------------------------------------------------------------------- #
# 6. Audit Logging Verification Tests
# --------------------------------------------------------------------------- #
def test_annotation_audit_logging_integrity(client, db_session):
    """Verify append-only ImperialAnnotationAudit records for create, update, and archive."""
    teacher = _create_user(db_session, f"t_audit_{uuid4().hex[:6]}@example.com", role=UserRole.teacher)
    map_asset, site = _seed_map_and_site(db_session, teacher)
    csrf_headers = {"X-Requested-With": "XMLHttpRequest"}

    _login(client, teacher.email)

    # 1. Create marker
    res_create = client.post(
        f"/api/v1/imperial/admin/maps/{map_asset.id}/annotations",
        json={
            "site_id": str(site.id),
            "u": 0.25,
            "v": 0.75,
            "label": "Ghim kiểm toán",
            "marker_style": "monument",
        },
        headers=csrf_headers,
    )
    assert res_create.status_code == 201
    anno_id = res_create.json()["id"]

    # 2. Update marker
    res_update = client.patch(
        f"/api/v1/imperial/admin/annotations/{anno_id}",
        json={"u": 0.26, "v": 0.76, "row_version": 1},
        headers=csrf_headers,
    )
    assert res_update.status_code == 200

    # 3. Archive marker
    res_archive = client.delete(
        f"/api/v1/imperial/admin/annotations/{anno_id}",
        headers=csrf_headers,
    )
    assert res_archive.status_code == 200

    # 4. Query audit trail
    res_audit = client.get(f"/api/v1/imperial/admin/annotations/{anno_id}/audit")
    assert res_audit.status_code == 200
    audits = res_audit.json()
    assert len(audits) == 3

    # Ordered chronologically
    actions = [a["action"] for a in audits]
    assert actions == ["create", "update", "archive"]

    # Attribution
    assert all(a["actor_id"] == str(teacher.id) for a in audits)

    # State transitions diff recorded
    assert audits[0]["before_json"] is None
    assert audits[0]["after_json"]["u"] == 0.25
    assert audits[1]["before_json"]["u"] == 0.25
    assert audits[1]["after_json"]["u"] == 0.26
    assert audits[2]["after_json"]["review_status"] == "archived"
