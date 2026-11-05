# -*- coding: utf-8 -*-
"""V5-T079 / Wave W07 Slot A09: P11 Publish, Invalidate, and Revert Integration Test Suite.

Validates the complete production contract for P11 Release Management:
1. Two-phase preflight validation blocking unreviewed content, disputed claims, and revoked sources.
2. Atomic publication & snapshot creation with cryptographic HMAC-SHA256 signed revisions.
3. Negative abuse test (CONC-009): Mid-release failure cleanly rolls back the entire transaction,
   ensuring zero half-published stories, no dangling objects, and consistent 404 on public surface.
4. Cryptographic tamper detection: Mismatched digests or forged signatures are deterministically rejected.
5. Invalidation & retraction (P11 Watchers): Rights expiration or scholarly disputes demote published items,
   purge CDN caches, and log immutable ResearchCorrectionEvent records.
6. Atomic rollback (P11-A10): Reverts active release pointer, restores prior approved snapshot,
   and prevents duplicate rollback attempts.
7. Role-based access control (RBAC): Learners and guests are strictly blocked with 403 Forbidden.
8. Cache purge engine: Confirms cache keys for stories, entities, and manifests are registered for CDN purging.
"""
from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from backend.config import settings
from backend.history_models import (
    HistoricalClaim,
    HistoricalClaimType,
    HistoricalConfidence,
    HistoricalEntity,
    HistoricalEntityType,
    HistoricalPublicationStatus,
    HistoricalSource,
    HistoricalSourceType,
    HistoricalSourceVerificationStatus,
    HistoricalVerificationStatus,
    HistoryStory,
)
from backend.main import app
from backend.models import User, UserRole
from backend.research_factory_models import (
    ResearchCachePurgeEvent,
    ResearchCorrectionEvent,
    ResearchPublicationRelease,
)
from backend.security import create_jwt_token, hash_password
from backend.services.research_factory import releases as svc


# --------------------------------------------------------------------------- #
# Fixtures & Helpers
# --------------------------------------------------------------------------- #
def _create_user(
    db_session,
    email: str,
    role: UserRole = UserRole.admin,
) -> User:
    user = User(
        email=email,
        password_hash=hash_password("SecurePassword123!"),
        display_name=f"User {email.split('@')[0]}",
        username=f"u_{uuid.uuid4().hex[:8]}",
        role=role,
        is_profile_public=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _auth_header(user: User) -> dict[str, str]:
    token = create_jwt_token(
        subject=str(user.id),
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        expires_delta=timedelta(hours=2),
        issuer=settings.jwt_issuer,
        audience=settings.jwt_audience,
        extra_claims={"role": user.role.value, "type": "access"},
    )
    return {"Authorization": f"Bearer {token}"}


def _seed_entity(
    db_session,
    slug: str | None = None,
    name_vi: str = "Cao Đỉnh",
) -> HistoricalEntity:
    unique_slug = slug or f"urn_test_{uuid.uuid4().hex[:8]}"
    entity = HistoricalEntity(
        id=uuid.uuid4(),
        entity_type=HistoricalEntityType.urn.value,
        slug=unique_slug,
        name_vi=name_vi,
        publication_status=HistoricalPublicationStatus.published.value,
        content_scope="CUU_DINH",
        summary_vi=f"Mô tả về {name_vi}",
    )
    db_session.add(entity)
    db_session.flush()
    return entity


def _seed_source(
    db_session,
    title: str = "Đại Nam Thực Lục Chính Biên",
    rights_status: str = "public_domain",
    public_display_allowed: bool = True,
) -> HistoricalSource:
    source = HistoricalSource(
        id=uuid.uuid4(),
        title=title,
        source_type=HistoricalSourceType.primary_source.value,
        verification_status=HistoricalSourceVerificationStatus.metadata_verified.value,
        rights_status=rights_status,
        public_display_allowed=public_display_allowed,
    )
    db_session.add(source)
    db_session.flush()
    return source


def _seed_claim(
    db_session,
    statement: str = "Đỉnh Cao được đúc vào năm Bính Thân 1836 triều Minh Mạng.",
    status: str = "source_attached",
    entity_id: uuid.UUID | None = None,
) -> HistoricalClaim:
    if entity_id is None:
        entity = _seed_entity(db_session)
        entity_id = entity.id

    claim = HistoricalClaim(
        id=uuid.uuid4(),
        entity_id=entity_id,
        claim_type=HistoricalClaimType.factual.value,
        statement_vi=statement,
        verification_status=status,
        confidence=HistoricalConfidence.high.value,
        origin="editorial",
    )
    db_session.add(claim)
    db_session.flush()
    return claim


def _seed_story(
    db_session,
    slug: str,
    title_vi: str,
    status: str = "internal_review",
    citations: list[dict] | None = None,
) -> HistoryStory:
    blocks = [
        {
            "type": "text",
            "body": f"Nội dung bài viết lịch sử cho {title_vi}.",
            "citations": citations or [],
        }
    ]
    story = HistoryStory(
        id=uuid.uuid4(),
        slug=slug,
        title_vi=title_vi,
        title_en=f"Story of {title_vi}",
        status=status,
        blocks=blocks,
        featured=False,
    )
    db_session.add(story)
    db_session.flush()
    return story


# --------------------------------------------------------------------------- #
# Test 1: Preflight Validation Gates
# --------------------------------------------------------------------------- #
def test_preflight_validation_gates_and_blockers(db_session):
    """Preflight must block unreviewed draft content, disputed claims, and revoked sources."""
    source_ok = _seed_source(db_session, title="Châu Bản Triều Nguyễn")
    claim_ok = _seed_claim(db_session, statement="Tuyên Đỉnh biểu tượng cho sự tuyên đạt.")
    
    # Valid story
    story_ok = _seed_story(
        db_session,
        slug=f"story_ok_{uuid.uuid4().hex[:6]}",
        title_vi="Tuyên Đỉnh Huy Hoàng",
        status="internal_review",
        citations=[{"claim_id": str(claim_ok.id), "source_id": str(source_ok.id), "locator": "Tập 1, tr. 45"}],
    )
    
    # 1. Clean preflight passes
    report = svc.run_release_preflight(db_session, story_ids=[story_ok.id])
    assert report.can_publish is True
    assert len(report.blockers) == 0
    assert report.stories_count == 1
    assert report.claims_count == 1
    assert report.sources_count == 1
    assert len(report.manifest_sha256) == 64

    # 2. Block draft story
    story_draft = _seed_story(
        db_session,
        slug=f"story_draft_{uuid.uuid4().hex[:6]}",
        title_vi="Bản nháp chưa duyệt",
        status="draft",
    )
    report_draft = svc.run_release_preflight(db_session, story_ids=[story_draft.id])
    assert report_draft.can_publish is False
    assert any("unreviewed 'draft' status" in b for b in report_draft.blockers)

    # 3. Block disputed claim
    claim_disputed = _seed_claim(db_session, statement="Mệnh đề gây tranh cãi.", status="disputed")
    story_disputed = _seed_story(
        db_session,
        slug=f"story_disp_{uuid.uuid4().hex[:6]}",
        title_vi="Câu chuyện tranh cãi",
        status="internal_review",
        citations=[{"claim_id": str(claim_disputed.id), "source_id": str(source_ok.id), "locator": "tr. 10"}],
    )
    report_disp = svc.run_release_preflight(db_session, story_ids=[story_disputed.id])
    assert report_disp.can_publish is False
    assert any("cannot be published" in b for b in report_disp.blockers)

    # 4. Block revoked source
    source_revoked = _seed_source(db_session, title="Nguồn Bị Thu Hồi", rights_status="revoked")
    story_revoked = _seed_story(
        db_session,
        slug=f"story_rev_{uuid.uuid4().hex[:6]}",
        title_vi="Câu chuyện nguồn thu hồi",
        status="internal_review",
        citations=[{"claim_id": str(claim_ok.id), "source_id": str(source_revoked.id), "locator": "tr. 1"}],
    )
    report_rev = svc.run_release_preflight(db_session, story_ids=[story_revoked.id])
    assert report_rev.can_publish is False
    assert any("rights status is 'revoked'" in b for b in report_rev.blockers)


# --------------------------------------------------------------------------- #
# Test 2: Atomic Publication & Cryptographic Revision Signing
# --------------------------------------------------------------------------- #
def test_atomic_publication_and_cryptographic_signed_revision(client: TestClient, db_session):
    """Atomic publication creates frozen snapshot, valid HMAC signature, and purges caches."""
    admin = _create_user(db_session, "admin_publisher@histolab.icu", UserRole.admin)
    source = _seed_source(db_session, title="Khâm Định Đại Nam Hội Điển Sự Lệ")
    claim = _seed_claim(db_session, statement="Minh Mạng năm thứ 17 đúc xong Cửu Đỉnh.")
    
    story1 = _seed_story(
        db_session,
        slug=f"story_cao_{uuid.uuid4().hex[:6]}",
        title_vi="Cao Đỉnh Khải Hoàn",
        status="internal_review",
        citations=[{"claim_id": str(claim.id), "source_id": str(source.id), "locator": "Quyển 4, tr. 12"}],
    )
    story2 = _seed_story(
        db_session,
        slug=f"story_nhan_{uuid.uuid4().hex[:6]}",
        title_vi="Nhân Đỉnh Phúc Lành",
        status="internal_review",
        citations=[{"claim_id": str(claim.id), "source_id": str(source.id), "locator": "Quyển 4, tr. 14"}],
    )
    
    release_code = f"REL-2026-TEST-{uuid.uuid4().hex[:6]}"
    release = svc.publish_release(
        db=db_session,
        story_ids=[story1.id, story2.id],
        release_code=release_code,
        signer=admin,
        scope="cuu_dinh_162_motifs",
    )

    assert release.id is not None
    assert release.release_code == release_code
    assert release.status == "PUBLISHED"
    assert release.signer_identity == admin.email
    assert release.signer_role == "admin"
    assert len(release.manifest_sha256) == 64
    assert len(release.signed_revision) == 64  # HMAC-SHA256 hex string

    # Verify signature validity
    is_valid_sig = svc.verify_revision_signature(
        signed_revision=release.signed_revision,
        manifest_sha256=release.manifest_sha256,
        release_code=release_code,
        signer_identity=admin.email,
    )
    assert is_valid_sig is True

    # Verify story statuses transitioned
    db_session.refresh(story1)
    db_session.refresh(story2)
    assert story1.status == "published"
    assert story1.published_at is not None
    assert story2.status == "published"
    assert story2.published_at is not None

    # Verify frozen snapshot payload
    snapshot = release.snapshot_payload
    assert snapshot["release_code"] == release_code
    assert len(snapshot["stories"]) == 2
    assert set(snapshot["story_slugs"]) == {story1.slug, story2.slug}

    # Verify cache purges registered
    purges = db_session.scalars(
        select(ResearchCachePurgeEvent).where(ResearchCachePurgeEvent.release_id == release.id)
    ).all()
    assert len(purges) >= 4
    purge_keys = [p.cache_key for p in purges]
    assert f"/api/v1/history/stories/{story1.slug}" in purge_keys
    assert f"/api/v1/history/stories/{story2.slug}" in purge_keys
    assert "/api/v1/history/stories" in purge_keys

    # Public endpoint check: Unauthenticated visitor can access published story
    resp = client.get(f"/api/v1/history/stories/{story1.slug}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["slug"] == story1.slug
    assert data["title_vi"] == story1.title_vi


# --------------------------------------------------------------------------- #
# Test 3: Negative Abuse Test (CONC-009) — Mid-Release Failure Rollback
# --------------------------------------------------------------------------- #
def test_negative_abuse_mid_release_failure_clean_rollback_conc009(client: TestClient, db_session):
    """Failure mid-release MUST cleanly roll back; no half-published stories or dangling records."""
    admin = _create_user(db_session, "admin_abort@histolab.icu", UserRole.admin)
    source = _seed_source(db_session, title="Tạp Chí Nghiên Cứu Lịch Sử")
    claim = _seed_claim(db_session, statement="Huyền Đỉnh biểu trưng cho chiều sâu trí tuệ.")

    story1 = _seed_story(
        db_session,
        slug=f"story_huyen_{uuid.uuid4().hex[:6]}",
        title_vi="Huyền Đỉnh Trầm Mặc",
        status="internal_review",
        citations=[{"claim_id": str(claim.id), "source_id": str(source.id), "locator": "tr. 99"}],
    )
    story2 = _seed_story(
        db_session,
        slug=f"story_thuan_{uuid.uuid4().hex[:6]}",
        title_vi="Thuần Đỉnh Tinh Khiết",
        status="internal_review",
        citations=[{"claim_id": str(claim.id), "source_id": str(source.id), "locator": "tr. 101"}],
    )
    db_session.commit()

    story1_id = story1.id
    story2_id = story2.id
    story1_slug = story1.slug
    story2_slug = story2.slug

    release_code = f"REL-ABORT-{uuid.uuid4().hex[:6]}"

    # Simulate catastrophic crash at story index 1 (after story index 0 was updated in memory/session)
    with pytest.raises(svc.ReleaseTransactionAbortedError) as exc_info:
        svc.publish_release(
            db=db_session,
            story_ids=[story1_id, story2_id],
            release_code=release_code,
            signer=admin,
            scope="cuu_dinh_162_motifs",
            simulate_failure_at_story_idx=1,
        )

    assert "Transaction aborted: no stories half-published" in str(exc_info.value)

    # Invariant: Neither story is published!
    # Re-fetch fresh rows from DB using stored UUIDs
    st1_db = db_session.get(HistoryStory, story1_id)
    st2_db = db_session.get(HistoryStory, story2_id)
    assert st1_db.status == "internal_review"
    assert st1_db.published_at is None
    assert st2_db.status == "internal_review"
    assert st2_db.published_at is None

    # Invariant: No release record exists in PUBLISHED state for this aborted code
    rel_db = db_session.scalar(
        select(ResearchPublicationRelease).where(ResearchPublicationRelease.release_code == release_code)
    )
    assert rel_db is None

    # Invariant: Public surface returns 404 for story1 and story2 (zero draft leakage)
    res1 = client.get(f"/api/v1/history/stories/{story1_slug}")
    assert res1.status_code == 404
    res2 = client.get(f"/api/v1/history/stories/{story2_slug}")
    assert res2.status_code == 404


# --------------------------------------------------------------------------- #
# Test 4: Cryptographic Signature Tamper Detection
# --------------------------------------------------------------------------- #
def test_cryptographic_signature_tamper_detection(db_session):
    """Tampering with manifest digest, release code, or signature is detected deterministically."""
    manifest_sha = hashlib.sha256(b'{"sample":"payload"}').hexdigest()
    release_code = "REL-2026-SIGN-001"
    signer = "archivist@histolab.icu"

    valid_signature = svc.sign_revision(manifest_sha, release_code, signer)
    assert svc.verify_revision_signature(valid_signature, manifest_sha, release_code, signer) is True

    # 1. Tampered manifest SHA
    tampered_manifest = manifest_sha[:-1] + ("0" if manifest_sha[-1] != "0" else "1")
    assert svc.verify_revision_signature(valid_signature, tampered_manifest, release_code, signer) is False

    # 2. Tampered release code
    assert svc.verify_revision_signature(valid_signature, manifest_sha, "REL-FORGED-999", signer) is False

    # 3. Tampered signer
    assert svc.verify_revision_signature(valid_signature, manifest_sha, release_code, "attacker@fake.com") is False

    # 4. Forged signature
    forged_signature = "a" * 64
    assert svc.verify_revision_signature(forged_signature, manifest_sha, release_code, signer) is False


# --------------------------------------------------------------------------- #
# Test 5: Invalidation & Retraction Protocol (P11 Watchers)
# --------------------------------------------------------------------------- #
def test_invalidation_and_retraction_protocol(client: TestClient, db_session):
    """Invalidating a story removes it from public view, logs a correction event, and purges caches."""
    admin = _create_user(db_session, "admin_invalidator@histolab.icu", UserRole.admin)
    source = _seed_source(db_session, title="Tư Liệu Hoàng Cung Huế")
    claim = _seed_claim(db_session, statement="Dụ Đỉnh đúc năm 1836.")
    story = _seed_story(
        db_session,
        slug=f"story_du_{uuid.uuid4().hex[:6]}",
        title_vi="Dụ Đỉnh Bình An",
        status="internal_review",
        citations=[{"claim_id": str(claim.id), "source_id": str(source.id), "locator": "tr. 55"}],
    )
    release = svc.publish_release(
        db=db_session,
        story_ids=[story.id],
        release_code=f"REL-INV-{uuid.uuid4().hex[:6]}",
        signer=admin,
    )

    # Confirm published
    assert client.get(f"/api/v1/history/stories/{story.slug}").status_code == 200

    # Invalidate story due to rights expiration
    inv_result = svc.invalidate_release_item(
        db=db_session,
        release_id=release.id,
        trigger_type="RIGHTS_EXPIRATION",
        rationale="Bản quyền số hóa của đối tác bảo tàng đã hết hạn 90 ngày theo hợp đồng.",
        actor=admin,
        story_id=story.id,
    )

    assert inv_result.release_id == release.id
    assert inv_result.trigger_type == "RIGHTS_EXPIRATION"
    assert story.id in inv_result.invalidated_story_ids
    assert len(inv_result.purged_cache_keys) > 0

    # Invariant: Story is archived in DB
    db_session.refresh(story)
    assert story.status == "archived"

    # Invariant: Public request returns 404
    assert client.get(f"/api/v1/history/stories/{story.slug}").status_code == 404

    # Invariant: ResearchCorrectionEvent recorded
    correction = db_session.scalar(
        select(ResearchCorrectionEvent).where(ResearchCorrectionEvent.release_id == release.id)
    )
    assert correction is not None
    assert correction.trigger_type == "RIGHTS_EXPIRATION"
    assert "hết hạn 90 ngày" in correction.rationale
    assert correction.cache_purged is True


# --------------------------------------------------------------------------- #
# Test 6: Atomic Rollback to Prior Approved Release
# --------------------------------------------------------------------------- #
def test_atomic_rollback_to_prior_approved_release(db_session):
    """Rollback restores prior release state, marks flawed release ROLLED_BACK, and rejects replay."""
    admin = _create_user(db_session, "admin_rollback@histolab.icu", UserRole.admin)
    source = _seed_source(db_session, title="Châu Bản Triều Nguyễn Quyển 12")
    claim = _seed_claim(db_session, statement="Nghị Đỉnh đúc năm 1836.")

    story1 = _seed_story(
        db_session,
        slug=f"story_nghi_{uuid.uuid4().hex[:6]}",
        title_vi="Nghị Đỉnh Vững Vàng",
        status="internal_review",
        citations=[{"claim_id": str(claim.id), "source_id": str(source.id), "locator": "tr. 80"}],
    )

    # 1. First approved release: v1.0
    rel1 = svc.publish_release(
        db=db_session,
        story_ids=[story1.id],
        release_code=f"REL-V1-{uuid.uuid4().hex[:6]}",
        signer=admin,
    )
    assert rel1.status == "PUBLISHED"

    # 2. Second release: v2.0 introduces a second story
    story2 = _seed_story(
        db_session,
        slug=f"story_flawed_{uuid.uuid4().hex[:6]}",
        title_vi="Thuần Đỉnh Phiên Bản Lỗi",
        status="internal_review",
        citations=[{"claim_id": str(claim.id), "source_id": str(source.id), "locator": "tr. 85"}],
    )
    rel2 = svc.publish_release(
        db=db_session,
        story_ids=[story1.id, story2.id],
        release_code=f"REL-V2-{uuid.uuid4().hex[:6]}",
        signer=admin,
        previous_release_id=rel1.id,
    )
    assert rel2.status == "PUBLISHED"

    # 3. Roll back v2.0 to restore v1.0
    rollback_res = svc.rollback_publication_release(
        db=db_session,
        release_id=rel2.id,
        rollback_reason="Khẩn cấp gỡ bỏ Thuần Đỉnh do phát hiện nhầm lẫn vị trí quai vạc.",
        actor=admin,
        restore_release_id=rel1.id,
    )

    assert rollback_res.rolled_back_release_id == rel2.id
    assert rollback_res.restored_release_id == rel1.id
    assert rollback_res.reverted_stories_count >= 1

    # Invariant: rel2 status is ROLLED_BACK
    db_session.refresh(rel2)
    assert rel2.status == "ROLLED_BACK"
    assert rel2.rolled_back_at is not None
    assert "nhầm lẫn vị trí" in (rel2.rollback_reason or "")

    # Invariant: rel1 is restored to PUBLISHED
    db_session.refresh(rel1)
    assert rel1.status == "PUBLISHED"

    # Invariant: story2 (not in v1.0) is demoted to internal_review
    db_session.refresh(story2)
    assert story2.status == "internal_review"

    # Invariant: story1 is still published
    db_session.refresh(story1)
    assert story1.status == "published"

    # Negative test: Repeat rollback of already rolled-back release fails!
    with pytest.raises(svc.ReleaseAlreadyRolledBackError):
        svc.rollback_publication_release(
            db=db_session,
            release_id=rel2.id,
            rollback_reason="Cố tình rollback lần 2",
            actor=admin,
        )


# --------------------------------------------------------------------------- #
# Test 7: API Endpoints, Idempotency & RBAC Access Control
# --------------------------------------------------------------------------- #
def test_api_endpoints_idempotency_and_rbac(client: TestClient, db_session):
    """Admin API endpoints enforce RBAC (403 for learners) and conflict handling (409)."""
    admin = _create_user(db_session, "admin_api@histolab.icu", UserRole.admin)
    learner = _create_user(db_session, "learner_api@histolab.icu", UserRole.learner)
    
    source = _seed_source(db_session, title="Đại Nam Nhất Thống Chí")
    claim = _seed_claim(db_session, statement="Tuyên Đỉnh cao 2 mét 31.")
    story = _seed_story(
        db_session,
        slug=f"story_api_{uuid.uuid4().hex[:6]}",
        title_vi="Tuyên Đỉnh Uy Nghi",
        status="internal_review",
        citations=[{"claim_id": str(claim.id), "source_id": str(source.id), "locator": "tr. 22"}],
    )
    db_session.commit()

    admin_headers = _auth_header(admin)
    learner_headers = _auth_header(learner)

    release_code = f"REL-API-{uuid.uuid4().hex[:6]}"
    payload = {
        "release_code": release_code,
        "story_ids": [str(story.id)],
        "scope": "cuu_dinh_162_motifs",
    }

    # 1. Learner cannot publish (403 Forbidden)
    res_learner = client.post(
        "/api/v1/admin/research-factory/releases",
        json=payload,
        headers=learner_headers,
    )
    assert res_learner.status_code == 403
    assert res_learner.json()["error"]["code"] in ("FORBIDDEN", "FORBIDDEN_RELEASE_ACTION", "HTTP_ERROR")

    # 2. Unauthenticated cannot publish (401 Unauthorized)
    res_unauth = client.post("/api/v1/admin/research-factory/releases", json=payload)
    assert res_unauth.status_code == 401

    # 3. Admin preflight endpoint
    pre_resp = client.post(
        "/api/v1/admin/research-factory/releases/preflight",
        json={"story_ids": [str(story.id)]},
        headers=admin_headers,
    )
    assert pre_resp.status_code == 200
    pre_data = pre_resp.json()
    assert pre_data["can_publish"] is True
    assert pre_data["stories_count"] == 1

    # 4. Admin publish success (201 Created)
    pub_resp = client.post(
        "/api/v1/admin/research-factory/releases",
        json=payload,
        headers=admin_headers,
    )
    assert pub_resp.status_code == 201
    pub_data = pub_resp.json()
    release_id = pub_data["id"]
    assert pub_data["release_code"] == release_code
    assert pub_data["status"] == "PUBLISHED"
    assert len(pub_data["manifest_sha256"]) == 64

    # 5. Duplicate release_code rejection (409 Conflict)
    dup_resp = client.post(
        "/api/v1/admin/research-factory/releases",
        json=payload,
        headers=admin_headers,
    )
    assert dup_resp.status_code == 409
    assert dup_resp.json()["error"]["code"] == "RELEASE_CODE_EXISTS"

    # 6. Active release lookup
    active_resp = client.get(
        "/api/v1/admin/research-factory/releases/active?scope=cuu_dinh_162_motifs",
        headers=admin_headers,
    )
    assert active_resp.status_code == 200
    assert active_resp.json()["id"] == release_id

    # 7. Audit trail endpoint
    audit_resp = client.get(
        f"/api/v1/admin/research-factory/releases/{release_id}/audit",
        headers=admin_headers,
    )
    assert audit_resp.status_code == 200
    audit_data = audit_resp.json()
    assert audit_data["release_id"] == release_id
    assert len(audit_data["cache_purges"]) >= 3
