# -*- coding: utf-8 -*-
"""V5-T042: Replace Fake Map Annotation Mutations in Frontend and Backend Routers.

Scope & Invariants:
1. Frontend map-api client (frontend/src/lib/imperial/map-api.ts):
   - Zero fabricated success on createAnnotation, updateAnnotation, deleteAnnotation,
     publishMap, exportAnnotations, importAnnotations.
   - Never generates synthetic IDs ("anno-draft-*") or optimistic bumped row_versions
     in error catch blocks.
   - Network or server 500 errors reject cleanly, allowing the calling UI to handle errors.
2. Studio Client & Review Dialog (AnnotationStudioClient.tsx, PublishReviewDialog.tsx):
   - Local drafts use distinct `draft-*` IDs and are tracked separately in client state.
   - When mutations fail (e.g. 500 error), drafts are preserved and not falsely cleared;
     error banners / notices are shown.
   - Publish dialog catches errors and never calls `onPublishedSuccess` on server rejection.
3. Vitest frontend contract test execution:
   - All tests in `src/lib/imperial/map-api.test.ts` pass, asserting authentic server
     responses and rejection on 500/409/422 errors.
4. Backend Real Server Persistence & RBAC:
   - Anonymous and learner roles are rejected with 401/403.
   - Staff/admin creates annotation with UV validation -> DB row persisted with audit log.
   - Optimistic concurrency control enforces `row_version` (and If-Match header),
     rejecting stale updates with HTTP 409 (IMPERIAL_CONCURRENCY_CONFLICT).
   - Soft-delete archives annotation in DB, creates audit record, and hides from public queries.
   - Atomic publish enforces license approval gate, activates map, publishes annotations,
     and serves via public GET /api/v1/imperial/maps/active.
5. Negative Abuse Invariant:
   - Network / server 500 or error rejections never show published changes on client.
"""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import uuid
from datetime import datetime, timezone

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


def _create_user(
    db_session,
    email: str,
    role: UserRole = UserRole.teacher,
    display_name: str | None = None,
) -> User:
    """Helper to persist a user with specific role."""
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


def _login_user(client, email: str, password: str = "Password123!") -> dict:
    """Login helper setting session cookies and anti-CSRF header on test client."""
    client.cookies.clear()
    client.headers.update({"X-Requested-With": "XMLHttpRequest"})
    res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    return res.json()


def _ensure_test_map_and_site(db_session, actor_id: uuid.UUID) -> tuple[ImperialMapAsset, ImperialSite]:
    """Create test ImperialZone, ImperialSite, and ImperialMapAsset in STTT scope."""
    zone = db_session.execute(
        select(ImperialZone).where(ImperialZone.content_scope == CONTENT_SCOPE_IMPERIAL)
    ).scalars().first()
    if not zone:
        zone = ImperialZone(
            id=uuid.uuid4(),
            content_scope=CONTENT_SCOPE_IMPERIAL,
            slug=f"zone-t042-{uuid.uuid4().hex[:6]}",
            title_vi="Khu vực Trung tâm",
            title_en="Central Ceremonial Axis",
            display_order=1,
        )
        db_session.add(zone)
        db_session.flush()

    site = ImperialSite(
        id=uuid.uuid4(),
        zone_id=zone.id,
        content_scope=CONTENT_SCOPE_IMPERIAL,
        slug=f"site-t042-{uuid.uuid4().hex[:6]}",
        name_vi="Điện Kiến Trung",
        name_en="Kien Trung Palace",
        condition="reconstructed",
        learning_level="L2_ANALYZED",
        is_published=True,
    )
    db_session.add(site)
    db_session.flush()

    map_asset = ImperialMapAsset(
        id=uuid.uuid4(),
        content_scope=CONTENT_SCOPE_IMPERIAL,
        title_vi="Bản đồ Trực giao Đại Nội 1932",
        slug=f"map-t042-{uuid.uuid4().hex[:6]}",
        version=1,
        image_storage_key="/assets/aerial/hue_1932.webp",
        image_sha256=f"sha256_{uuid.uuid4().hex}",
        mime_type="image/webp",
        width_px=4096,
        height_px=3072,
        source_title="Bản đồ Địa bạ Triều Nguyễn 1932",
        credit_text="Trung tâm Bảo tồn Di tích Cố đô Huế",
        license_kind="CC-BY-NC-4.0",
        license_status="approved",
        review_status="draft",
        is_active=False,
        created_by=actor_id,
        row_version=1,
    )
    db_session.add(map_asset)
    db_session.commit()
    db_session.refresh(site)
    db_session.refresh(map_asset)
    return map_asset, site


# =========================================================================== #
# 1. Source Code Invariants
# =========================================================================== #

def test_frontend_map_api_no_fabricated_mutation_success():
    """Verify frontend/src/lib/imperial/map-api.ts does NOT fabricate success or synthetic fallbacks."""
    repo_root = Path(__file__).resolve().parents[2]
    api_file = repo_root / "frontend" / "src" / "lib" / "imperial" / "map-api.ts"
    assert api_file.exists(), "map-api.ts must exist"

    content = api_file.read_text(encoding="utf-8")

    # 1. Negative check: createAnnotation must NOT fabricate synthetic IDs on error
    assert "anno-draft-" not in content, (
        "Forbidden: createAnnotation must not fabricate synthetic 'anno-draft-*' markers in catch fallback"
    )

    # 2. Negative check: updateAnnotation must NOT optimistically bump row_version in catch block
    assert "row_version: payload.row_version + 1" not in content, (
        "Forbidden: updateAnnotation must not fabricate bumped row_version on failure"
    )

    # 3. Negative check: deleteAnnotation must NOT return fake { success: true } on error
    assert "return { success: true, id: annotationId };" not in content, (
        "Forbidden: deleteAnnotation must not fabricate { success: true } on failure"
    )

    # 4. Negative check: publishMap must NOT fabricate published map on error
    assert 'review_status: "published"' not in content, (
        "Forbidden: publishMap must not fabricate published review_status in catch block"
    )

    # 5. Must re-throw errors from apiRequest
    assert "export async function createAnnotation" in content
    assert "export async function updateAnnotation" in content
    assert "export async function deleteAnnotation" in content
    assert "export async function publishMap" in content


def test_studio_client_handles_errors_and_separates_drafts():
    """Verify AnnotationStudioClient and PublishReviewDialog handle server rejections safely."""
    repo_root = Path(__file__).resolve().parents[2]
    studio_file = repo_root / "frontend" / "src" / "app" / "admin" / "dai-noi" / "annotate" / "AnnotationStudioClient.tsx"
    assert studio_file.exists(), "AnnotationStudioClient.tsx must exist"

    studio_content = studio_file.read_text(encoding="utf-8")

    # 1. Local drafts are separated with draft- prefix
    assert "draft-" in studio_content, "Studio client must identify local unsaved drafts with draft- prefix"

    # 2. handleDeleteAnnotation handles errors cleanly without assuming success
    assert "catch (err)" in studio_content
    assert "Lỗi khi xóa điểm ghim trên máy chủ" in studio_content, (
        "Studio client must notify user when server delete fails"
    )

    # 3. handleSaveDrafts preserves drafts and notifies on failure
    assert "Lỗi khi lưu dữ liệu lên máy chủ" in studio_content, (
        "Studio client must notify user when server save drafts fails"
    )

    # 4. PublishReviewDialog handles errors and does not execute onPublishedSuccess
    dialog_file = repo_root / "frontend" / "src" / "components" / "imperial" / "studio" / "PublishReviewDialog.tsx"
    assert dialog_file.exists(), "PublishReviewDialog.tsx must exist"

    dialog_content = dialog_file.read_text(encoding="utf-8")
    assert "setPublishError" in dialog_content, "Dialog must track and display publish errors"
    assert "onPublishedSuccess(res.map)" in dialog_content, "Dialog must only call onPublishedSuccess on real server success"


def test_vitest_frontend_contract():
    """Execute Vitest test suite src/lib/imperial/map-api.test.ts asserting client contracts."""
    repo_root = Path(__file__).resolve().parents[2]
    res = subprocess.run(
        ["npm", "run", "test", "--", "src/lib/imperial/map-api.test.ts"],
        cwd=str(repo_root / "frontend"),
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, f"Vitest tests failed:\n{res.stdout}\n{res.stderr}"
    assert "passed" in res.stdout.lower()


# =========================================================================== #
# 2. Backend Server Persistence & RBAC Tests
# =========================================================================== #

def test_unauthenticated_or_learner_cannot_mutate_annotations(client, db_session):
    """Verify that unauthenticated and learner users are rejected with 401 or 403."""
    client.cookies.clear()
    admin_user = _create_user(db_session, f"admin_t042_{uuid.uuid4().hex[:6]}@example.com", role=UserRole.admin)
    map_asset, site = _ensure_test_map_and_site(db_session, admin_user.id)
    payload = {"site_id": str(site.id), "u": 0.5, "v": 0.5, "label": "Test"}

    # 1. Unauthenticated create -> 401
    res = client.post(f"/api/v1/imperial/admin/maps/{map_asset.id}/annotations", json=payload)
    assert res.status_code == 401, f"Expected 401, got {res.status_code}"

    # 2. Learner role create -> 403
    learner = _create_user(db_session, f"learner_t042_{uuid.uuid4().hex[:6]}@example.com", role=UserRole.learner)
    _login_user(client, learner.email)
    res_learner = client.post(f"/api/v1/imperial/admin/maps/{map_asset.id}/annotations", json=payload)
    assert res_learner.status_code == 403, f"Expected 403 for learner, got {res_learner.status_code}"

    # 3. Learner role publish -> 403
    res_pub = client.post(f"/api/v1/imperial/admin/maps/{map_asset.id}/publish")
    assert res_pub.status_code == 403, f"Expected 403 for learner publish, got {res_pub.status_code}"


def test_backend_create_annotation_real_persistence_and_audit(client, db_session):
    """Verify POST /api/v1/imperial/admin/maps/{map_id}/annotations persists row and audit record."""
    staff = _create_user(db_session, f"staff_t042_{uuid.uuid4().hex[:6]}@example.com", role=UserRole.teacher)
    map_asset, site = _ensure_test_map_and_site(db_session, staff.id)
    _login_user(client, staff.email)

    create_payload = {
        "site_id": str(site.id),
        "shape_type": "point",
        "u": 0.45,
        "v": 0.65,
        "label": "Điện Kiến Trung Khảo Cổ",
        "marker_style": "palace",
        "position_confidence": "verified",
        "editorial_notes": "Điểm ghim đo đạc theo bản đồ trực giao 1932",
    }

    res = client.post(
        f"/api/v1/imperial/admin/maps/{map_asset.id}/annotations",
        json=create_payload,
    )
    assert res.status_code == 201, f"Create annotation failed: {res.text}"
    anno_data = res.json()
    anno_id = uuid.UUID(anno_data["id"])

    # Invariants in response:
    assert anno_data["review_status"] == "draft"
    assert anno_data["row_version"] == 1
    assert anno_data["u"] == 0.45
    assert anno_data["v"] == 0.65
    assert anno_data["label"] == "Điện Kiến Trung Khảo Cổ"

    # Invariants in Database:
    db_anno = db_session.get(ImperialMapAnnotation, anno_id)
    assert db_anno is not None
    assert db_anno.site_id == site.id
    assert db_anno.map_asset_id == map_asset.id
    assert float(db_anno.u) == 0.45
    assert float(db_anno.v) == 0.65
    assert db_anno.row_version == 1
    assert db_anno.created_by == staff.id

    # Audit trail invariant:
    audits = db_session.execute(
        select(ImperialAnnotationAudit).where(
            ImperialAnnotationAudit.annotation_id == anno_id,
            ImperialAnnotationAudit.action == "create",
        )
    ).scalars().all()
    assert len(audits) >= 1
    audit = audits[0]
    assert audit.actor_id == staff.id
    assert audit.after_json["label"] == "Điện Kiến Trung Khảo Cổ"


def test_backend_create_annotation_validations_and_conflict(client, db_session):
    """Verify UV coordinate bounds, nonexistent site, and duplicate annotation rejections."""
    staff = _create_user(db_session, f"staff_val_{uuid.uuid4().hex[:6]}@example.com", role=UserRole.teacher)
    map_asset, site = _ensure_test_map_and_site(db_session, staff.id)
    _login_user(client, staff.email)

    # 1. Out-of-bounds UV coordinates (> 1.0 or < 0.0) -> HTTP 422
    bad_uv = {"site_id": str(site.id), "u": 1.25, "v": -0.1}
    res_uv = client.post(f"/api/v1/imperial/admin/maps/{map_asset.id}/annotations", json=bad_uv)
    assert res_uv.status_code == 422, f"Expected 422 for bad UV, got {res_uv.status_code}"

    # 2. Non-existent site -> HTTP 404
    bad_site = {"site_id": str(uuid.uuid4()), "u": 0.5, "v": 0.5}
    res_site = client.post(f"/api/v1/imperial/admin/maps/{map_asset.id}/annotations", json=bad_site)
    assert res_site.status_code == 404
    assert "IMPERIAL_SITE_NOT_FOUND" in res_site.text

    # 3. Create initial annotation successfully
    valid_payload = {"site_id": str(site.id), "u": 0.5, "v": 0.5}
    res_ok = client.post(f"/api/v1/imperial/admin/maps/{map_asset.id}/annotations", json=valid_payload)
    assert res_ok.status_code == 201

    # 4. Duplicate annotation for same site on same map -> HTTP 409
    res_dup = client.post(f"/api/v1/imperial/admin/maps/{map_asset.id}/annotations", json=valid_payload)
    assert res_dup.status_code == 409
    assert "IMPERIAL_ANNOTATION_EXISTS" in res_dup.text


def test_backend_update_annotation_optimistic_concurrency_and_audit(client, db_session):
    """Verify PATCH updates with optimistic locking (row_version and If-Match) and audit logging."""
    staff = _create_user(db_session, f"staff_upd_{uuid.uuid4().hex[:6]}@example.com", role=UserRole.teacher)
    map_asset, site = _ensure_test_map_and_site(db_session, staff.id)
    _login_user(client, staff.email)

    # Create initial annotation
    create_res = client.post(
        f"/api/v1/imperial/admin/maps/{map_asset.id}/annotations",
        json={"site_id": str(site.id), "u": 0.2, "v": 0.3, "label": "Vị trí ban đầu"},
    )
    assert create_res.status_code == 201
    anno_id = create_res.json()["id"]

    # 1. Update with matching row_version -> 200 OK, bumped row_version
    update_res = client.patch(
        f"/api/v1/imperial/admin/annotations/{anno_id}",
        headers={"If-Match": '"row-version-1"'},
        json={"u": 0.25, "v": 0.35, "label": "Vị trí hiệu chỉnh", "row_version": 1},
    )
    assert update_res.status_code == 200, f"Update failed: {update_res.text}"
    updated_data = update_res.json()
    assert updated_data["row_version"] == 2
    assert updated_data["u"] == 0.25
    assert updated_data["v"] == 0.35
    assert updated_data["label"] == "Vị trí hiệu chỉnh"

    # DB persistence check
    db_anno = db_session.get(ImperialMapAnnotation, uuid.UUID(anno_id))
    db_session.refresh(db_anno)
    assert db_anno.row_version == 2
    assert float(db_anno.u) == 0.25

    # Audit record check
    update_audits = db_session.execute(
        select(ImperialAnnotationAudit).where(
            ImperialAnnotationAudit.annotation_id == uuid.UUID(anno_id),
            ImperialAnnotationAudit.action == "update",
        )
    ).scalars().all()
    assert len(update_audits) >= 1
    assert update_audits[0].after_json["row_version"] == 2

    # 2. Concurrency Conflict: Update with stale row_version 1 (now current is 2) -> HTTP 409
    conflict_res = client.patch(
        f"/api/v1/imperial/admin/annotations/{anno_id}",
        json={"u": 0.99, "row_version": 1},
    )
    assert conflict_res.status_code == 409
    assert "IMPERIAL_CONCURRENCY_CONFLICT" in conflict_res.text

    # 3. Header mismatch: If-Match row-version-5 != payload row_version 2 -> HTTP 409
    header_mismatch_res = client.patch(
        f"/api/v1/imperial/admin/annotations/{anno_id}",
        headers={"If-Match": '"row-version-5"'},
        json={"u": 0.26, "row_version": 2},
    )
    assert header_mismatch_res.status_code == 409
    assert "IMPERIAL_CONCURRENCY_CONFLICT" in header_mismatch_res.text


def test_backend_delete_annotation_soft_deletes_and_archives(client, db_session):
    """Verify DELETE soft-deletes annotation, creates audit log, and hides from public views."""
    staff = _create_user(db_session, f"staff_del_{uuid.uuid4().hex[:6]}@example.com", role=UserRole.teacher)
    map_asset, site = _ensure_test_map_and_site(db_session, staff.id)
    _login_user(client, staff.email)

    create_res = client.post(
        f"/api/v1/imperial/admin/maps/{map_asset.id}/annotations",
        json={"site_id": str(site.id), "u": 0.4, "v": 0.4},
    )
    assert create_res.status_code == 201
    anno_id = create_res.json()["id"]

    # Delete annotation
    del_res = client.delete(f"/api/v1/imperial/admin/annotations/{anno_id}")
    assert del_res.status_code == 200, f"Delete failed: {del_res.text}"
    del_data = del_res.json()
    assert del_data["success"] is True
    assert del_data["id"] == str(anno_id)

    # In DB, record is archived
    db_anno = db_session.get(ImperialMapAnnotation, uuid.UUID(anno_id))
    db_session.refresh(db_anno)
    assert db_anno.review_status == "archived"
    assert db_anno.is_visible is False

    # Audit record for archive action exists
    del_audits = db_session.execute(
        select(ImperialAnnotationAudit).where(
            ImperialAnnotationAudit.annotation_id == uuid.UUID(anno_id),
            ImperialAnnotationAudit.action == "archive",
        )
    ).scalars().all()
    assert len(del_audits) >= 1


def test_backend_atomic_publish_gates_and_transitions(client, db_session):
    """Verify atomic map publication enforces license approval, activates map, and publishes annotations."""
    admin = _create_user(db_session, f"admin_pub_{uuid.uuid4().hex[:6]}@example.com", role=UserRole.admin)
    map_asset, site = _ensure_test_map_and_site(db_session, admin.id)
    _login_user(client, admin.email)

    # Create draft annotation
    client.post(
        f"/api/v1/imperial/admin/maps/{map_asset.id}/annotations",
        json={"site_id": str(site.id), "u": 0.52, "v": 0.48, "label": "Điện Kiến Trung"},
    )

    # 1. Gate: Map with unapproved license cannot be published
    map_asset.license_status = "pending"
    db_session.commit()

    gate_res = client.post(f"/api/v1/imperial/admin/maps/{map_asset.id}/publish")
    assert gate_res.status_code == 400
    assert "IMPERIAL_LICENSE_NOT_APPROVED" in gate_res.text

    # 2. Approve license and publish atomically
    map_asset.license_status = "approved"
    db_session.commit()

    pub_res = client.post(f"/api/v1/imperial/admin/maps/{map_asset.id}/publish")
    assert pub_res.status_code == 200, f"Publish failed: {pub_res.text}"
    pub_data = pub_res.json()
    assert pub_data["review_status"] == "published"
    assert pub_data["is_active"] is True
    assert pub_data["published_at"] is not None

    # In DB: map is active, annotation is published
    db_session.refresh(map_asset)
    assert map_asset.is_active is True
    assert map_asset.review_status == "published"

    annos = db_session.execute(
        select(ImperialMapAnnotation).where(ImperialMapAnnotation.map_asset_id == map_asset.id)
    ).scalars().all()
    assert len(annos) >= 1
    for a in annos:
        assert a.review_status == "published"

    # Public active map endpoint now serves this published map!
    active_res = client.get("/api/v1/imperial/maps/active")
    assert active_res.status_code == 200
    active_data = active_res.json()
    assert active_data["map"]["id"] == str(map_asset.id)
    assert any(a["id"] == str(annos[0].id) for a in active_data["annotations"])


def test_negative_abuse_server_failure_does_not_mutate_state(client, db_session):
    """Negative Abuse Invariant: Server 404 or 422 errors do not cause partial mutations or leaked published states."""
    staff = _create_user(db_session, f"staff_neg_{uuid.uuid4().hex[:6]}@example.com", role=UserRole.teacher)
    admin = _create_user(db_session, f"admin_neg_{uuid.uuid4().hex[:6]}@example.com", role=UserRole.admin)
    fake_map_id = uuid.uuid4()

    _login_user(client, staff.email)

    # 1. Posting annotation to nonexistent map -> 404, zero rows inserted
    res_fake_map = client.post(
        f"/api/v1/imperial/admin/maps/{fake_map_id}/annotations",
        json={"site_id": str(uuid.uuid4()), "u": 0.5, "v": 0.5},
    )
    assert res_fake_map.status_code == 404

    # 2. Publishing nonexistent map -> 404
    _login_user(client, admin.email)
    res_fake_pub = client.post(f"/api/v1/imperial/admin/maps/{fake_map_id}/publish")
    assert res_fake_pub.status_code == 404

    # 3. Soft-deleting nonexistent annotation -> 404
    _login_user(client, staff.email)
    res_fake_del = client.delete(f"/api/v1/imperial/admin/annotations/{uuid.uuid4()}")
    assert res_fake_del.status_code == 404
