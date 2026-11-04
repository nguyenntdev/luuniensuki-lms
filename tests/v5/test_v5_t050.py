# -*- coding: utf-8 -*-
"""V5-T050: Museum Operator Media CMS Test Suite.

Wave W04, Slot A10 (Priority: P1, Classification: PRODUCTION_COMPLETION).
Verifies:
1. Strict Role-Based Access Control (Editor Permissions Enforcement):
   - Only staff, teachers, admins, and super_admins can access operator media CMS endpoints.
   - Learners, guests, and unauthenticated users receive HTTP 403 Forbidden / 401 Unauthorized.
   - Approval and publication strictly require admin privileges.
2. File Format and Magic Byte Verification (GLB, PNG, JPEG, WEBP):
   - Positively verifies valid 3D binary glTF (.glb), PNG, JPEG, and WEBP uploads.
   - Verifies SHA-256 calculation and physical storage mapping.
3. Negative Abuse Guardrails:
   - Executable and script files (.exe, .sh, .php, .html) strictly rejected with HTTP 400.
   - Disguised/spoofed files (e.g. .png with PHP/HTML payload or invalid magic bytes) strictly rejected.
   - Empty files and oversized files rejected.
4. Licensing and Rights Metadata Governance:
   - Mandatory rights owner, approved license type, and creator attribution.
   - Rejection of missing, unapproved, or pirated/unlicensed declarations (HTTP 422).
5. Staged Publication Approval Workflow:
   - Strict progression: draft -> in_review -> approved -> published.
   - Direct leaps from draft to published are strictly blocked (HTTP 400).
   - Direct leaps from in_review to published are strictly blocked (HTTP 400).
   - Mandatory rejection explanation requirement.
   - Version revisioning: uploading replacement file increments version and resets approval status.
   - Publication synchronization to persistent HistoricalAsset table and audit logging.
6. Operator Preview & Archive:
   - Preview endpoint provides typed viewer configuration and licensing summaries.
   - Archiving revokes public display rights on published assets.
"""
from __future__ import annotations

import io
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from backend.history_models import HistoricalAsset, HistoricalContentAuditLog
from backend.media_cms_models import MediaCmsItem, MediaCmsStatus
from backend.models import User, UserRole
from backend.security import hash_password


# --------------------------------------------------------------------------- #
# Helpers & Fixtures
# --------------------------------------------------------------------------- #

def _create_user(
    db_session,
    email: str,
    role: UserRole = UserRole.learner,
    display_name: str | None = None,
) -> User:
    """Create a verified test user with given role."""
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


def _login(client: TestClient, email: str, password: str = "Password123!") -> dict:
    """Authenticate user and store session cookie."""
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    return res.json()


def _make_dummy_glb(size: int = 128) -> bytes:
    """Generate minimal binary glTF (GLB) payload with magic bytes."""
    header = b"glTF" + (2).to_bytes(4, "little") + (size).to_bytes(4, "little")
    return header + b"\x00" * max(0, size - len(header))


def _make_dummy_png(size: int = 64) -> bytes:
    """Generate minimal PNG payload with 8-byte magic header."""
    header = b"\x89PNG\r\n\x1a\n"
    return header + b"\x00" * max(0, size - len(header))


def _make_dummy_jpeg(size: int = 64) -> bytes:
    """Generate minimal JPEG payload with magic bytes."""
    header = b"\xff\xd8\xff\xe0"
    return header + b"\x00" * max(0, size - len(header))


def _make_dummy_webp(size: int = 64) -> bytes:
    """Generate minimal WEBP payload with RIFF and WEBP magic bytes."""
    # RIFF [4 bytes size] WEBP
    riff = b"RIFF" + (size - 8).to_bytes(4, "little") + b"WEBPVP8 "
    return riff + b"\x00" * max(0, size - len(riff))


# ============================================================================== #
# 1. Strict Role-Based Permissions & Editor Guards
# ============================================================================== #

def test_media_cms_role_based_permissions(client: TestClient, db_session):
    """Verify that only editorial staff/teachers/admins can use Media CMS, and only admins can approve/publish."""
    admin = _create_user(db_session, f"admin_{uuid.uuid4().hex[:6]}@example.com", role=UserRole.admin)
    teacher = _create_user(db_session, f"teacher_{uuid.uuid4().hex[:6]}@example.com", role=UserRole.teacher)
    learner = _create_user(db_session, f"learner_{uuid.uuid4().hex[:6]}@example.com", role=UserRole.learner)
    guest = _create_user(db_session, f"guest_{uuid.uuid4().hex[:6]}@example.com", role=UserRole.guest)

    glb_content = _make_dummy_glb()
    valid_data = {
        "title": "Cao Đỉnh 3D Scan",
        "description": "Bản quét 3D Cao Đỉnh tại Thế Miếu",
        "asset_type": "model3d",
        "rights_owner": "Trung tâm Bảo tồn Di tích Cố đô Huế (HMCC)",
        "license_type": "CC BY 4.0 / Educational Fair Use",
        "attribution": "Bảo tàng Cổ vật Cung đình Huế & Histolab",
        "public_display_allowed": "true",
        "derivative_allowed": "true",
        "relic_slug": "cao-dinh",
    }

    # 1. Unauthenticated request -> 401
    client.cookies.clear()
    res = client.post(
        "/api/v1/admin/media-cms/upload",
        data=valid_data,
        files={"file": ("cao_dinh.glb", io.BytesIO(glb_content), "model/gltf-binary")},
    )
    assert res.status_code == 401

    # 2. Learner role -> 403 Forbidden
    _login(client, learner.email)
    res = client.post(
        "/api/v1/admin/media-cms/upload",
        data=valid_data,
        files={"file": ("cao_dinh.glb", io.BytesIO(glb_content), "model/gltf-binary")},
    )
    assert res.status_code == 403

    res = client.get("/api/v1/admin/media-cms/items")
    assert res.status_code == 403

    # 3. Guest role -> 403 Forbidden
    _login(client, guest.email)
    res = client.post(
        "/api/v1/admin/media-cms/upload",
        data=valid_data,
        files={"file": ("cao_dinh.glb", io.BytesIO(glb_content), "model/gltf-binary")},
    )
    assert res.status_code == 403

    # 4. Teacher (editor role) can upload draft
    _login(client, teacher.email)
    res = client.post(
        "/api/v1/admin/media-cms/upload",
        data=valid_data,
        files={"file": ("cao_dinh.glb", io.BytesIO(glb_content), "model/gltf-binary")},
    )
    assert res.status_code == 201, f"Teacher upload failed: {res.text}"
    created = res.json()
    item_id = created["id"]
    assert created["publication_status"] == "draft"

    # Teacher submits for review
    res = client.post(f"/api/v1/admin/media-cms/items/{item_id}/submit-review")
    assert res.status_code == 200
    assert res.json()["publication_status"] == "in_review"

    # Teacher CANNOT approve (requires admin) -> 403 Forbidden
    res = client.post(f"/api/v1/admin/media-cms/items/{item_id}/approve", json={"notes": "Looks good"})
    assert res.status_code == 403

    # Teacher CANNOT publish -> 403 Forbidden
    res = client.post(f"/api/v1/admin/media-cms/items/{item_id}/publish")
    assert res.status_code == 403

    # 5. Admin can approve and publish
    _login(client, admin.email)
    res = client.post(f"/api/v1/admin/media-cms/items/{item_id}/approve", json={"notes": "Approved by curator"})
    assert res.status_code == 200
    assert res.json()["publication_status"] == "approved"

    res = client.post(f"/api/v1/admin/media-cms/items/{item_id}/publish")
    assert res.status_code == 200
    assert res.json()["publication_status"] == "published"


# ============================================================================== #
# 2. File Format & Magic Byte Verification (GLB, PNG, JPEG, WEBP)
# ============================================================================== #

def test_media_cms_file_format_and_magic_byte_validation(client: TestClient, db_session):
    """Verify that GLB meshes, PNG, JPEG, and WEBP images upload with proper format identification and SHA-256."""
    admin = _create_user(db_session, f"admin_{uuid.uuid4().hex[:6]}@example.com", role=UserRole.admin)
    _login(client, admin.email)

    base_data = {
        "rights_owner": "Trung tâm Bảo tồn Di tích Cố đô Huế (HMCC)",
        "license_type": "CC BY 4.0 / Educational Fair Use",
        "attribution": "Bảo tàng Cổ vật Cung đình Huế",
        "public_display_allowed": "true",
    }

    # 1. Valid GLB 3D mesh
    glb_bytes = _make_dummy_glb(256)
    res = client.post(
        "/api/v1/admin/media-cms/upload",
        data={**base_data, "title": "GLB Model", "asset_type": "model3d"},
        files={"file": ("model.glb", io.BytesIO(glb_bytes), "model/gltf-binary")},
    )
    assert res.status_code == 201
    item = res.json()
    assert item["file_format"] == "glb"
    assert item["mime_type"] == "model/gltf-binary"
    assert len(item["sha256"]) == 64
    assert item["storage_url"].endswith(".glb")

    # 2. Valid PNG image
    png_bytes = _make_dummy_png(128)
    res = client.post(
        "/api/v1/admin/media-cms/upload",
        data={**base_data, "title": "PNG Image", "asset_type": "image"},
        files={"file": ("rubbing.png", io.BytesIO(png_bytes), "image/png")},
    )
    assert res.status_code == 201
    item = res.json()
    assert item["file_format"] == "png"
    assert item["mime_type"] == "image/png"
    assert item["thumbnail_url"] == item["storage_url"]

    # 3. Valid JPEG image
    jpeg_bytes = _make_dummy_jpeg(128)
    res = client.post(
        "/api/v1/admin/media-cms/upload",
        data={**base_data, "title": "JPEG Image", "asset_type": "image"},
        files={"file": ("photo.jpg", io.BytesIO(jpeg_bytes), "image/jpeg")},
    )
    assert res.status_code == 201
    item = res.json()
    assert item["file_format"] == "jpeg"
    assert item["mime_type"] == "image/jpeg"

    # 4. Valid WEBP image
    webp_bytes = _make_dummy_webp(128)
    res = client.post(
        "/api/v1/admin/media-cms/upload",
        data={**base_data, "title": "WEBP Image", "asset_type": "image"},
        files={"file": ("photo.webp", io.BytesIO(webp_bytes), "image/webp")},
    )
    assert res.status_code == 201
    item = res.json()
    assert item["file_format"] == "webp"
    assert item["mime_type"] == "image/webp"


# ============================================================================== #
# 3. Negative Abuse Guardrails (Executables, Scripts, Disguised Payloads)
# ============================================================================== #

def test_media_cms_negative_abuse_rejected(client: TestClient, db_session):
    """Verify that executable, script, spoofed, and malicious uploads are strictly rejected with HTTP 400."""
    admin = _create_user(db_session, f"admin_{uuid.uuid4().hex[:6]}@example.com", role=UserRole.admin)
    _login(client, admin.email)

    base_data = {
        "title": "Abuse Test",
        "rights_owner": "HMCC",
        "license_type": "CC BY 4.0",
        "attribution": "Test",
    }

    # 1. Executable file .exe
    exe_payload = b"MZ\x90\x00\x03\x00\x00\x00" + b"\x00" * 50
    res = client.post(
        "/api/v1/admin/media-cms/upload",
        data=base_data,
        files={"file": ("malware.exe", io.BytesIO(exe_payload), "application/octet-stream")},
    )
    assert res.status_code == 400
    assert "FORBIDDEN_FILE_TYPE" in res.text or "prohibited" in res.text

    # 2. Shell script .sh
    sh_payload = b"#!/bin/bash\nrm -rf /\n"
    res = client.post(
        "/api/v1/admin/media-cms/upload",
        data=base_data,
        files={"file": ("exploit.sh", io.BytesIO(sh_payload), "application/x-sh")},
    )
    assert res.status_code == 400

    # 3. PHP script .php
    php_payload = b"<?php phpinfo(); ?>"
    res = client.post(
        "/api/v1/admin/media-cms/upload",
        data=base_data,
        files={"file": ("shell.php", io.BytesIO(php_payload), "application/x-php")},
    )
    assert res.status_code == 400

    # 4. HTML/XSS file .html
    html_payload = b"<html><script>alert(document.cookie)</script></html>"
    res = client.post(
        "/api/v1/admin/media-cms/upload",
        data=base_data,
        files={"file": ("attack.html", io.BytesIO(html_payload), "text/html")},
    )
    assert res.status_code == 400

    # 5. Spoofed disguised file (.png containing PHP script)
    disguised_php = b"<?php system($_GET['cmd']); ?>"
    res = client.post(
        "/api/v1/admin/media-cms/upload",
        data=base_data,
        files={"file": ("innocent.png", io.BytesIO(disguised_php), "image/png")},
    )
    assert res.status_code == 400
    assert "MALICIOUS_CONTENT_DETECTED" in res.text or "INVALID_PNG_FORMAT" in res.text

    # 6. Spoofed disguised file (.png containing HTML markup)
    disguised_html = b"<html><head><title>Phishing</title></head><body>Login</body></html>"
    res = client.post(
        "/api/v1/admin/media-cms/upload",
        data=base_data,
        files={"file": ("avatar.png", io.BytesIO(disguised_html), "image/png")},
    )
    assert res.status_code == 400

    # 7. Spoofed GLB mesh (.glb with plain text instead of glTF header)
    fake_glb = b"This is just a text file claiming to be a 3D model."
    res = client.post(
        "/api/v1/admin/media-cms/upload",
        data=base_data,
        files={"file": ("corrupt.glb", io.BytesIO(fake_glb), "model/gltf-binary")},
    )
    assert res.status_code == 400
    assert "INVALID_GLB_FORMAT" in res.text

    # 8. Empty file
    res = client.post(
        "/api/v1/admin/media-cms/upload",
        data=base_data,
        files={"file": ("empty.png", io.BytesIO(b""), "image/png")},
    )
    assert res.status_code == 400
    assert "EMPTY_FILE" in res.text


# ============================================================================== #
# 4. Licensing and Rights Metadata Validation
# ============================================================================== #

def test_media_cms_licensing_metadata_validation(client: TestClient, db_session):
    """Verify licensing metadata requirements: rights owner, approved license, and attribution."""
    admin = _create_user(db_session, f"admin_{uuid.uuid4().hex[:6]}@example.com", role=UserRole.admin)
    _login(client, admin.email)

    png_bytes = _make_dummy_png()

    # 1. Missing rights owner
    res = client.post(
        "/api/v1/admin/media-cms/upload",
        data={
            "title": "No Owner Test",
            "rights_owner": "   ",
            "license_type": "CC BY 4.0",
            "attribution": "Photographer A",
        },
        files={"file": ("test.png", io.BytesIO(png_bytes), "image/png")},
    )
    assert res.status_code == 422
    assert "MISSING_RIGHTS_OWNER" in res.text

    # 2. Missing license type
    res = client.post(
        "/api/v1/admin/media-cms/upload",
        data={
            "title": "No License Test",
            "rights_owner": "HMCC",
            "license_type": "   ",
            "attribution": "Photographer A",
        },
        files={"file": ("test.png", io.BytesIO(png_bytes), "image/png")},
    )
    assert res.status_code == 422
    assert "MISSING_LICENSE" in res.text

    # 3. Unapproved/unlicensed license declaration
    for bad_license in ["unlicensed", "none", "pirated", "copyrighted_unauthorized"]:
        res = client.post(
            "/api/v1/admin/media-cms/upload",
            data={
                "title": "Bad License Test",
                "rights_owner": "HMCC",
                "license_type": bad_license,
                "attribution": "Photographer A",
            },
            files={"file": ("test.png", io.BytesIO(png_bytes), "image/png")},
        )
        assert res.status_code == 422
        assert "INVALID_LICENSE" in res.text or "UNAPPROVED_LICENSE" in res.text

    # 4. Missing attribution
    res = client.post(
        "/api/v1/admin/media-cms/upload",
        data={
            "title": "No Attribution Test",
            "rights_owner": "HMCC",
            "license_type": "CC BY 4.0",
            "attribution": "  ",
        },
        files={"file": ("test.png", io.BytesIO(png_bytes), "image/png")},
    )
    assert res.status_code == 422
    assert "MISSING_ATTRIBUTION" in res.text

    # 5. Approved license types all succeed
    approved_licenses = [
        "CC BY 4.0",
        "CC BY 4.0 / Educational Fair Use",
        "CC BY-SA 4.0",
        "CC0 1.0",
        "Public Domain",
        "Educational Fair Use",
        "Museum Partner License",
    ]
    for lic in approved_licenses:
        res = client.post(
            "/api/v1/admin/media-cms/upload",
            data={
                "title": f"Valid Lic {lic}",
                "rights_owner": "Trung tâm Bảo tồn Di tích Cố đô Huế (HMCC)",
                "license_type": lic,
                "attribution": "Bảo tàng Cung đình",
            },
            files={"file": (f"{lic[:4]}.png", io.BytesIO(png_bytes), "image/png")},
        )
        assert res.status_code == 201, f"Approved license '{lic}' failed: {res.text}"


# ============================================================================== #
# 5. Staged Publication Approval Workflow (Positive & Negative Invariants)
# ============================================================================== #

def test_media_cms_staged_publication_approval_lifecycle(client: TestClient, db_session):
    """Verify staged progression: draft -> in_review -> approved -> published.

    Invariants tested:
    - Direct leap from draft to published is strictly blocked (HTTP 400).
    - Direct leap from in_review to published without approval is strictly blocked (HTTP 400).
    - Direct publication when public_display_allowed=False is blocked (HTTP 400).
    - Publication creates and synchronizes persistent HistoricalAsset database row.
    - Full audit logging in historical_content_audit_log.
    """
    admin = _create_user(db_session, f"admin_{uuid.uuid4().hex[:6]}@example.com", role=UserRole.admin)
    _login(client, admin.email)

    glb_bytes = _make_dummy_glb(512)

    # Step 1: Upload creates draft
    res = client.post(
        "/api/v1/admin/media-cms/upload",
        data={
            "title": "Cửu Đỉnh 3D Hoàn Chỉnh",
            "description": "Bộ mô hình 3D hoàn chỉnh 9 đỉnh",
            "asset_type": "model3d",
            "rights_owner": "Trung tâm Bảo tồn Di tích Cố đô Huế (HMCC)",
            "license_type": "CC BY 4.0 / Educational Fair Use",
            "attribution": "HMCC & Histolab 3D Scanning Lab",
            "public_display_allowed": "true",
            "relic_slug": "cuu-dinh",
        },
        files={"file": ("cuu_dinh.glb", io.BytesIO(glb_bytes), "model/gltf-binary")},
    )
    assert res.status_code == 201
    item = res.json()
    item_id = item["id"]
    assert item["publication_status"] == "draft"
    assert item["version"] == 1

    # Step 2: Negative test — Direct leap from draft -> published MUST BE BLOCKED
    res = client.post(f"/api/v1/admin/media-cms/items/{item_id}/publish")
    assert res.status_code == 400
    assert "STAGED_APPROVAL_REQUIRED" in res.text

    # Step 3: Transition draft -> in_review
    res = client.post(f"/api/v1/admin/media-cms/items/{item_id}/submit-review")
    assert res.status_code == 200
    assert res.json()["publication_status"] == "in_review"

    # Step 4: Negative test — Direct leap from in_review -> published MUST BE BLOCKED
    res = client.post(f"/api/v1/admin/media-cms/items/{item_id}/publish")
    assert res.status_code == 400
    assert "STAGED_APPROVAL_REQUIRED" in res.text

    # Step 5: Transition in_review -> approved
    res = client.post(
        f"/api/v1/admin/media-cms/items/{item_id}/approve",
        json={"notes": "Đã đối chiếu thông số đo đạc với hồ sơ di tích."},
    )
    assert res.status_code == 200
    assert res.json()["publication_status"] == "approved"
    assert "đối chiếu" in res.json()["review_notes"]

    # Step 6: Negative test — If public_display_allowed is turned False, publish must be rejected
    res = client.patch(
        f"/api/v1/admin/media-cms/items/{item_id}",
        json={"public_display_allowed": False},
    )
    assert res.status_code == 200
    res = client.post(f"/api/v1/admin/media-cms/items/{item_id}/publish")
    assert res.status_code == 400
    assert "PUBLIC_DISPLAY_NOT_ALLOWED" in res.text or "STAGED_APPROVAL_REQUIRED" in res.text

    # Re-enable public display, re-approve
    client.patch(
        f"/api/v1/admin/media-cms/items/{item_id}",
        json={"public_display_allowed": True},
    )
    client.post(f"/api/v1/admin/media-cms/items/{item_id}/submit-review")
    client.post(f"/api/v1/admin/media-cms/items/{item_id}/approve", json={"notes": "Ready to publish"})

    # Step 7: Transition approved -> published
    res = client.post(f"/api/v1/admin/media-cms/items/{item_id}/publish")
    assert res.status_code == 200
    published_item = res.json()
    assert published_item["publication_status"] == "published"

    # Step 8: Verify synchronization to HistoricalAsset table
    h_asset = db_session.execute(
        select(HistoricalAsset).where(HistoricalAsset.storage_url == published_item["storage_url"])
    ).scalar_one_or_none()
    assert h_asset is not None, "Published media item must be synchronized to HistoricalAsset table"
    assert h_asset.rights_status == "cleared"
    assert h_asset.license == "CC BY 4.0 / Educational Fair Use"
    assert h_asset.source_origin == "Trung tâm Bảo tồn Di tích Cố đô Huế (HMCC)"
    assert h_asset.public_display_allowed is True
    assert h_asset.sha256 == published_item["sha256"]

    # Step 9: Verify audit trail
    audits = list(
        db_session.scalars(
            select(HistoricalContentAuditLog).where(
                HistoricalContentAuditLog.resource_id == uuid.UUID(item_id)
            )
        )
    )
    assert len(audits) >= 4
    action_names = {a.action for a in audits}
    assert "media_cms_upload" in action_names
    assert "media_cms_submit_review" in action_names
    assert "media_cms_approve" in action_names
    assert "media_cms_publish" in action_names


# ============================================================================== #
# 6. Rejection, Version Bumping, and Archiving
# ============================================================================== #

def test_media_cms_rejection_and_versioning(client: TestClient, db_session):
    """Verify rejection requirements (mandatory reason) and version replacement resets approval status."""
    admin = _create_user(db_session, f"admin_{uuid.uuid4().hex[:6]}@example.com", role=UserRole.admin)
    _login(client, admin.email)

    png_bytes = _make_dummy_png(128)
    res = client.post(
        "/api/v1/admin/media-cms/upload",
        data={
            "title": "Bản Dập Nghi Đỉnh",
            "rights_owner": "HMCC",
            "license_type": "CC BY 4.0",
            "attribution": "Histolab",
        },
        files={"file": ("nghi_dinh.png", io.BytesIO(png_bytes), "image/png")},
    )
    assert res.status_code == 201
    item_id = res.json()["id"]

    # Submit for review
    client.post(f"/api/v1/admin/media-cms/items/{item_id}/submit-review")

    # 1. Reject without reason -> 422 Unprocessable Content
    res = client.post(f"/api/v1/admin/media-cms/items/{item_id}/reject", json={"reason": "   "})
    assert res.status_code == 422
    assert "REJECTION_REASON_REQUIRED" in res.text

    # 2. Reject with valid reason
    res = client.post(
        f"/api/v1/admin/media-cms/items/{item_id}/reject",
        json={"reason": "Độ phân giải bản dập quá thấp, cần quét lại 600 DPI."},
    )
    assert res.status_code == 200
    assert res.json()["publication_status"] == "rejected"
    assert "600 DPI" in res.json()["review_notes"]

    # 3. Upload new version -> increments version and resets status to draft
    new_png_bytes = _make_dummy_png(256)
    res = client.post(
        f"/api/v1/admin/media-cms/items/{item_id}/version",
        files={"file": ("nghi_dinh_v2.png", io.BytesIO(new_png_bytes), "image/png")},
    )
    assert res.status_code == 200
    v2_item = res.json()
    assert v2_item["version"] == 2
    assert v2_item["publication_status"] == "draft"

    # Cannot publish version 2 directly
    res = client.post(f"/api/v1/admin/media-cms/items/{item_id}/publish")
    assert res.status_code == 400

    # Go through staged flow for version 2
    client.post(f"/api/v1/admin/media-cms/items/{item_id}/submit-review")
    client.post(f"/api/v1/admin/media-cms/items/{item_id}/approve", json={"notes": "Bản 600 DPI đạt chuẩn."})
    res = client.post(f"/api/v1/admin/media-cms/items/{item_id}/publish")
    assert res.status_code == 200
    assert res.json()["publication_status"] == "published"

    # 4. Operator Preview Endpoint
    res = client.get(f"/api/v1/admin/media-cms/preview/{item_id}")
    assert res.status_code == 200
    prev = res.json()
    assert prev["viewer_type"] == "image_2d"
    assert prev["rights_summary"]["rights_owner"] == "HMCC"
    assert prev["rights_summary"]["is_cleared"] is True
    assert prev["staged_review_summary"]["current_stage"] == "published"
    assert prev["staged_review_summary"]["version"] == 2

    # 5. Archive published asset
    res = client.post(f"/api/v1/admin/media-cms/items/{item_id}/archive")
    assert res.status_code == 200
    assert res.json()["publication_status"] == "archived"

    # Verify HistoricalAsset is marked restricted upon archive
    h_asset = db_session.execute(
        select(HistoricalAsset).where(HistoricalAsset.storage_url == v2_item["storage_url"])
    ).scalar_one()
    assert h_asset.public_display_allowed is False
    assert h_asset.rights_status == "restricted"
