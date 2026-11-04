# -*- coding: utf-8 -*-
"""V5-T025 (Wave W02, Slot A05): Human Editorial Workflow & Verification Governance Test Suite.

Audits and verifies:
1. Editorial lifecycle transitions:
   - Strict progression: draft -> internal_review -> verified -> published.
   - Blocked illegal state skips: direct jump from draft to published, draft to verified,
     or internal_review to published without verification is strictly rejected (422 / ValueError).
2. Role-based permissions (admin / staff / teacher):
   - Admin, super_admin, and teacher users have full editorial authority to review,
     verify, and publish.
3. Negative abuse tests:
   - Non-editorial users (learner, guest, unauthenticated) attempting to publish receive
     HTTP 403 Forbidden (API) and PermissionError (service layer).
   - Automated AI agents cannot self-approve or sign off on verification or publication
     (anti-AI self-approval guardrail).
4. Mandatory review note & source preconditions:
   - Advancing to verified or published strictly requires a non-empty review note / reason.
   - Factual claims cannot reach verified or published without an eligible supporting source.
   - Contradicted claims cannot be verified or published.
5. Entity editorial governance:
   - Entity follows the same draft -> internal_review -> verified -> published lifecycle.
   - An entity containing disputed or contradicted claims CANNOT be published.
6. Immutable audit logging:
   - All state transitions append immutable entries to historical_content_audit_log
     with actor attribution, action name, before/after diffs, and review reasons.
"""
from __future__ import annotations

import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from backend.history_models import (
    HistoricalClaim,
    HistoricalClaimSource,
    HistoricalContentAuditLog,
    HistoricalEntity,
    HistoricalSource,
)
from backend.models import User, UserRole
from backend.services import history_governance as gov


# --------------------------------------------------------------------------- #
# Helpers & Seeders
# --------------------------------------------------------------------------- #
def _make_admin(client: TestClient, db_session, email: str = "admin@example.com", display_name: str = "Admin") -> User:
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password123!", "display_name": display_name},
    )
    user = db_session.execute(select(User).where(User.email == email)).scalar_one()
    user.role = UserRole.admin
    db_session.commit()
    client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Password123!"},
    )
    return user


def _make_teacher(client: TestClient, db_session, email: str = "teacher@example.com", display_name: str = "Teacher") -> User:
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password123!", "display_name": display_name},
    )
    user = db_session.execute(select(User).where(User.email == email)).scalar_one()
    user.role = UserRole.teacher
    db_session.commit()
    client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Password123!"},
    )
    return user


def _make_learner(client: TestClient, db_session, email: str = "learner@example.com", display_name: str = "Learner") -> User:
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password123!", "display_name": display_name},
    )
    user = db_session.execute(select(User).where(User.email == email)).scalar_one()
    user.role = UserRole.learner
    db_session.commit()
    client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Password123!"},
    )
    return user


def _make_guest(client: TestClient, db_session, email: str = "guest@example.com", display_name: str = "Guest") -> User:
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password123!", "display_name": display_name},
    )
    user = db_session.execute(select(User).where(User.email == email)).scalar_one()
    user.role = UserRole.guest
    db_session.commit()
    client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Password123!"},
    )
    return user


def _make_ai_agent(client: TestClient, db_session, email: str = "ai_agent@example.com", display_name: str = "AI Teacher Bot") -> User:
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password123!", "display_name": display_name},
    )
    user = db_session.execute(select(User).where(User.email == email)).scalar_one()
    user.role = UserRole.admin
    user.is_ai_agent = True
    db_session.commit()
    client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Password123!"},
    )
    return user


def _seed_entity(db_session, slug: str = "nghi-dinh-urn", name_vi: str = "Nghị Đỉnh") -> HistoricalEntity:
    entity = HistoricalEntity(
        entity_type="urn",
        slug=slug,
        name_vi=name_vi,
        publication_status="draft",
    )
    db_session.add(entity)
    db_session.flush()
    return entity


def _seed_source(
    db_session,
    title: str = "Đại Nam Thực Lục",
    source_type: str = "royal_record",
) -> HistoricalSource:
    source = HistoricalSource(
        source_type=source_type,
        title=title,
        author_text="Quốc Sử Quán Triều Nguyễn",
        publication_year=1848,
        verification_status="metadata_verified",
    )
    db_session.add(source)
    db_session.flush()
    return source


# --------------------------------------------------------------------------- #
# Tests
# --------------------------------------------------------------------------- #
def test_editorial_lifecycle_complete_transition_flow(client: TestClient, db_session):
    """Verifies complete valid progression: draft -> internal_review -> verified -> published."""
    admin = _make_admin(client, db_session, "admin_flow@example.com")
    teacher = _make_teacher(client, db_session, "teacher_flow@example.com")
    entity = _seed_entity(db_session, slug="thuan-dinh-urn", name_vi="Thuận Đỉnh")
    source = _seed_source(db_session, title="Khâm Định Đại Nam Hội Điển Sự Lệ")
    db_session.commit()

    # Step 1: Create claim in draft status
    claim_res = client.post(
        "/api/v1/admin/history/claims",
        json={
            "entity_id": str(entity.id),
            "claim_type": "factual",
            "statement_vi": "Thuận Đỉnh được đặt ở vị trí thứ hai bên tả của Cửu Đỉnh.",
            "confidence": "high",
            "verification_status": "draft",
            "origin": "editorial",
        },
    )
    assert claim_res.status_code == 200, claim_res.text
    claim_id = claim_res.json()["id"]
    assert claim_res.json()["verification_status"] == "draft"

    # Step 2: Attach eligible supporting source
    bind_res = client.post(
        f"/api/v1/admin/history/claims/{claim_id}/sources",
        json={"source_id": str(source.id), "support_type": "supports", "page_start": "42"},
    )
    assert bind_res.status_code == 200, bind_res.text

    # Step 3: Transition draft -> internal_review (by teacher)
    rev_res = client.post(
        f"/api/v1/admin/history/claims/{claim_id}/transition",
        params={"target": "internal_review", "reason": "Draft finalized and ready for peer review."},
    )
    assert rev_res.status_code == 200, rev_res.text
    assert rev_res.json()["verification_status"] == "internal_review"

    claim_db = db_session.get(HistoricalClaim, uuid.UUID(claim_id))
    assert claim_db.verification_status == "internal_review"
    assert claim_db.reviewed_by == teacher.id

    # Step 4: Transition internal_review -> verified (by teacher)
    ver_res = client.post(
        f"/api/v1/admin/history/claims/{claim_id}/transition",
        params={"target": "verified", "reason": "Verified against chronicle volume 12."},
    )
    assert ver_res.status_code == 200, ver_res.text
    assert ver_res.json()["verification_status"] == "verified"

    claim_db = db_session.get(HistoricalClaim, uuid.UUID(claim_id))
    assert claim_db.verification_status == "verified"
    assert claim_db.verified_by == teacher.id

    # Step 5: Transition verified -> published (by admin)
    _make_admin(client, db_session, "admin_flow@example.com")  # re-login as admin
    pub_res = client.post(
        f"/api/v1/admin/history/claims/{claim_id}/transition",
        params={"target": "published", "reason": "Editorial board approval for public atlas."},
    )
    assert pub_res.status_code == 200, pub_res.text
    assert pub_res.json()["verification_status"] == "published"

    claim_db = db_session.get(HistoricalClaim, uuid.UUID(claim_id))
    assert claim_db.verification_status == "published"

    # Step 6: Verify immutable audit log sequence
    audit_logs = list(
        db_session.scalars(
            select(HistoricalContentAuditLog)
            .where(
                HistoricalContentAuditLog.resource_type == "claim",
                HistoricalContentAuditLog.resource_id == uuid.UUID(claim_id),
            )
            .order_by(HistoricalContentAuditLog.id.asc())
        )
    )
    actions = [log.action for log in audit_logs]
    assert "create" in actions
    assert "attach_source" in actions
    assert "submit_for_review" in actions
    assert "verify" in actions
    assert "publish" in actions

    publish_log = next(log for log in audit_logs if log.action == "publish")
    assert publish_log.before_json == {"verification_status": "verified"}
    assert publish_log.after_json == {"verification_status": "published"}
    assert publish_log.reason == "Editorial board approval for public atlas."
    assert publish_log.actor_id == admin.id


def test_editorial_lifecycle_strict_ordering_blocks_skipping_steps(client: TestClient, db_session):
    """Negative abuse test: skipping lifecycle states is strictly rejected with 422."""
    admin = _make_admin(client, db_session, "admin_skip@example.com")
    entity = _seed_entity(db_session, slug="tuyen-dinh-urn", name_vi="Tuyên Đỉnh")
    source = _seed_source(db_session)
    db_session.commit()

    claim = gov.create_claim(
        db_session,
        data={
            "entity_id": entity.id,
            "claim_type": "factual",
            "statement_vi": "Tuyên Đỉnh là chiếc đỉnh thứ hai bên hữu.",
            "verification_status": "draft",
            "origin": "editorial",
        },
        actor_id=admin.id,
    )
    gov.attach_source_to_claim(
        db_session, claim=claim, source=source, data={"support_type": "supports"}, actor_id=admin.id
    )
    db_session.commit()

    # Attempt 1: Direct jump draft -> published (must fail)
    res_pub = client.post(
        f"/api/v1/admin/history/claims/{claim.id}/transition",
        params={"target": "published", "reason": "Trying to skip review"},
    )
    assert res_pub.status_code == 422, res_pub.text
    assert res_pub.json()["error"]["code"] == "HISTORY_CLAIM_INVALID_TRANSITION"
    assert "Invalid editorial transition" in res_pub.json()["error"]["message"]

    # Attempt 2: Direct jump draft -> verified (must fail)
    res_ver = client.post(
        f"/api/v1/admin/history/claims/{claim.id}/transition",
        params={"target": "verified", "reason": "Trying to skip review"},
    )
    assert res_ver.status_code == 422, res_ver.text
    assert res_ver.json()["error"]["code"] == "HISTORY_CLAIM_INVALID_TRANSITION"

    # Step to internal_review
    gov.transition_claim_status(
        db_session, claim=claim, target="internal_review", actor_id=admin.id, reason="Moved to review"
    )
    db_session.commit()

    # Attempt 3: Direct jump internal_review -> published (must fail without verified)
    res_pub2 = client.post(
        f"/api/v1/admin/history/claims/{claim.id}/transition",
        params={"target": "published", "reason": "Trying to publish without verify"},
    )
    assert res_pub2.status_code == 422, res_pub2.text
    assert res_pub2.json()["error"]["code"] == "HISTORY_CLAIM_INVALID_TRANSITION"

    # Service layer direct call must also reject skipping steps
    with pytest.raises(ValueError, match="Invalid editorial transition"):
        gov.transition_claim_status(
            db_session, claim=claim, target="published", actor_id=admin.id, reason="Direct skip"
        )


def test_negative_abuse_unauthorized_user_cannot_publish_receives_403(client: TestClient, db_session):
    """Negative abuse test: User without editorial role attempting to publish receives 403 Forbidden."""
    admin = _make_admin(client, db_session, "admin_role_check@example.com")
    entity = _seed_entity(db_session, slug="huyen-dinh-urn", name_vi="Huyền Đỉnh")
    source = _seed_source(db_session)
    db_session.commit()

    # Create and advance claim to verified by admin
    claim = gov.create_claim(
        db_session,
        data={
            "entity_id": entity.id,
            "claim_type": "factual",
            "statement_vi": "Huyền Đỉnh được đúc bằng đồng nguyên chất.",
            "verification_status": "draft",
            "origin": "editorial",
        },
        actor_id=admin.id,
    )
    gov.attach_source_to_claim(
        db_session, claim=claim, source=source, data={"support_type": "supports"}, actor_id=admin.id
    )
    gov.transition_claim_status(
        db_session, claim=claim, target="internal_review", actor_id=admin.id, reason="Review started"
    )
    gov.transition_claim_status(
        db_session, claim=claim, target="verified", actor_id=admin.id, reason="Verified by board"
    )
    db_session.commit()
    assert claim.verification_status == "verified"

    # Create and log in as learner (non-editorial)
    learner = _make_learner(client, db_session, "hacker_learner@example.com")

    # API Attempt: Learner calls transition to publish
    abuse_res = client.post(
        f"/api/v1/admin/history/claims/{claim.id}/transition",
        params={"target": "published", "reason": "Learner attempting unauthorized publish"},
    )
    assert abuse_res.status_code == 403, abuse_res.text
    assert "Not authorized" in abuse_res.text

    # API Attempt: Learner calls transition to verified
    abuse_ver = client.post(
        f"/api/v1/admin/history/claims/{claim.id}/transition",
        params={"target": "verified", "reason": "Learner attempting unauthorized verify"},
    )
    assert abuse_ver.status_code == 403, abuse_ver.text

    # Service Layer Attempt: Calling transition_claim_status with learner actor_id
    with pytest.raises(PermissionError, match="not authorized to advance claims"):
        gov.transition_claim_status(
            db_session,
            claim=claim,
            target="published",
            actor_id=learner.id,
            reason="Direct service abuse",
        )

    # Service Layer Attempt: Calling transition_entity_status with learner actor_id
    with pytest.raises(PermissionError, match="not authorized to advance entity"):
        gov.transition_entity_status(
            db_session,
            entity=entity,
            target="published",
            actor_id=learner.id,
            reason="Learner entity publish",
        )

    # Verify claim remains verified and was not modified
    db_session.refresh(claim)
    assert claim.verification_status == "verified"


def test_negative_abuse_guest_and_unauthenticated_blocked(client: TestClient, db_session):
    """Negative abuse test: Guest users receive 403 and unauthenticated requests receive 401."""
    admin = _make_admin(client, db_session, "admin_guest_check@example.com")
    entity = _seed_entity(db_session, slug="du-dinh-urn", name_vi="Dụ Đỉnh")
    db_session.commit()

    claim = gov.create_claim(
        db_session,
        data={
            "entity_id": entity.id,
            "claim_type": "factual",
            "statement_vi": "Dụ Đỉnh có hoa văn cây lúa.",
            "verification_status": "verified",
            "origin": "editorial",
        },
        actor_id=admin.id,
    )
    db_session.commit()

    # Log out to test unauthenticated access
    client.post("/api/v1/auth/logout")

    unauth_res = client.post(
        f"/api/v1/admin/history/claims/{claim.id}/transition",
        params={"target": "published", "reason": "Unauthenticated attempt"},
    )
    assert unauth_res.status_code == 401, unauth_res.text

    # Guest user attempt
    _make_guest(client, db_session, "guest_user@example.com")
    guest_res = client.post(
        f"/api/v1/admin/history/claims/{claim.id}/transition",
        params={"target": "published", "reason": "Guest publish attempt"},
    )
    assert guest_res.status_code == 403, guest_res.text


def test_negative_abuse_ai_agent_cannot_self_approve_or_publish(client: TestClient, db_session):
    """Negative abuse test: Automated AI agents cannot self-approve or publish claims or entities."""
    admin = _make_admin(client, db_session, "human_admin@example.com")
    ai_bot = _make_ai_agent(client, db_session, "ai_worker_bot@example.com")
    entity = _seed_entity(db_session, slug="ai-guarded-urn", name_vi="AI Guarded Urn")
    source = _seed_source(db_session)
    db_session.commit()

    claim = gov.create_claim(
        db_session,
        data={
            "entity_id": entity.id,
            "claim_type": "factual",
            "statement_vi": "Khẳng định do AI tạo ra cần kiểm duyệt của con người.",
            "verification_status": "internal_review",
            "origin": "ai_generated",
        },
        actor_id=admin.id,
    )
    gov.attach_source_to_claim(
        db_session, claim=claim, source=source, data={"support_type": "supports"}, actor_id=admin.id
    )
    db_session.commit()

    # AI agent attempts to verify claim
    with pytest.raises(PermissionError, match="Automated AI agent cannot self-approve"):
        gov.transition_claim_status(
            db_session,
            claim=claim,
            target="verified",
            actor_id=ai_bot.id,
            reason="AI self-verifying claim",
        )

    # Move claim to verified by human admin
    gov.transition_claim_status(
        db_session,
        claim=claim,
        target="verified",
        actor_id=admin.id,
        reason="Human admin verified source",
    )
    db_session.commit()

    # AI agent attempts to publish claim
    with pytest.raises(PermissionError, match="Automated AI agent cannot self-approve"):
        gov.transition_claim_status(
            db_session,
            claim=claim,
            target="published",
            actor_id=ai_bot.id,
            reason="AI self-publishing claim",
        )

    # AI agent attempts to publish entity
    with pytest.raises(PermissionError, match="Automated AI agent cannot self-approve"):
        gov.transition_entity_status(
            db_session,
            entity=entity,
            target="published",
            actor_id=ai_bot.id,
            reason="AI self-publishing entity",
        )


def test_negative_abuse_publish_requires_review_note_and_eligible_source(client: TestClient, db_session):
    """Negative abuse test: verifying or publishing without a review note or eligible source fails."""
    admin = _make_admin(client, db_session, "admin_checks@example.com")
    entity = _seed_entity(db_session, slug="nhan-dinh-urn", name_vi="Nhân Đỉnh")
    source = _seed_source(db_session)
    db_session.commit()

    # Factual claim created in internal_review without any source attached
    claim_no_src = gov.create_claim(
        db_session,
        data={
            "entity_id": entity.id,
            "claim_type": "factual",
            "statement_vi": "Nhân Đỉnh được đúc vào năm Bính Thân 1836.",
            "verification_status": "internal_review",
            "origin": "editorial",
        },
        actor_id=admin.id,
    )
    db_session.commit()

    # Attempt to verify factual claim without source -> fails
    res_no_src = client.post(
        f"/api/v1/admin/history/claims/{claim_no_src.id}/transition",
        params={"target": "verified", "reason": "Attempting verify without source"},
    )
    assert res_no_src.status_code == 422, res_no_src.text
    assert "require an eligible source" in res_no_src.json()["error"]["message"]

    # Attach source
    gov.attach_source_to_claim(
        db_session, claim=claim_no_src, source=source, data={"support_type": "supports"}, actor_id=admin.id
    )
    db_session.commit()

    # Attempt to verify without a review note -> fails
    res_no_note = client.post(
        f"/api/v1/admin/history/claims/{claim_no_src.id}/transition",
        params={"target": "verified"},
    )
    assert res_no_note.status_code == 422, res_no_note.text
    assert "requires a review note" in res_no_note.json()["error"]["message"]

    # Verify properly with note
    gov.transition_claim_status(
        db_session, claim=claim_no_src, target="verified", actor_id=admin.id, reason="Properly verified"
    )
    db_session.commit()

    # Attempt to publish without a review note -> fails
    res_pub_no_note = client.post(
        f"/api/v1/admin/history/claims/{claim_no_src.id}/transition",
        params={"target": "published"},
    )
    assert res_pub_no_note.status_code == 422, res_pub_no_note.text
    assert "requires a review note" in res_pub_no_note.json()["error"]["message"]

    # Add a contradicting source -> claim demoted to disputed and publication blocked
    source_contradict = _seed_source(db_session, title="Tài liệu phản biện")
    gov.attach_source_to_claim(
        db_session,
        claim=claim_no_src,
        source=source_contradict,
        data={"support_type": "contradicts"},
        actor_id=admin.id,
    )
    db_session.commit()

    assert claim_no_src.verification_status == "disputed"

    # Attempt to publish contradicted claim -> fails
    res_pub_contra = client.post(
        f"/api/v1/admin/history/claims/{claim_no_src.id}/transition",
        params={"target": "published", "reason": "Attempting to publish disputed fact"},
    )
    assert res_pub_contra.status_code == 422, res_pub_contra.text


def test_teacher_and_admin_editorial_permissions(client: TestClient, db_session):
    """Verifies that teachers, admins, and super_admins have valid editorial authority."""
    teacher = _make_teacher(client, db_session, "teacher_perm@example.com")
    admin = _make_admin(client, db_session, "admin_perm@example.com")
    entity = _seed_entity(db_session, slug="chuong-dinh-urn", name_vi="Chương Đỉnh")
    source = _seed_source(db_session)
    db_session.commit()

    assert gov.is_editorial_user(teacher) is True
    assert gov.is_editorial_user(admin) is True

    claim = gov.create_claim(
        db_session,
        data={
            "entity_id": entity.id,
            "claim_type": "factual",
            "statement_vi": "Chương Đỉnh tương ứng với vua Thiệu Trị.",
            "verification_status": "draft",
            "origin": "editorial",
        },
        actor_id=teacher.id,
    )
    gov.attach_source_to_claim(
        db_session, claim=claim, source=source, data={"support_type": "supports"}, actor_id=teacher.id
    )

    # Teacher transitions to internal_review
    gov.transition_claim_status(
        db_session, claim=claim, target="internal_review", actor_id=teacher.id, reason="Teacher submitted"
    )
    assert claim.verification_status == "internal_review"

    # Teacher transitions to verified
    gov.transition_claim_status(
        db_session, claim=claim, target="verified", actor_id=teacher.id, reason="Teacher verified"
    )
    assert claim.verification_status == "verified"

    # Teacher transitions to published
    gov.transition_claim_status(
        db_session, claim=claim, target="published", actor_id=teacher.id, reason="Teacher published"
    )
    assert claim.verification_status == "published"


def test_rejection_and_demotion_editorial_lifecycle(client: TestClient, db_session):
    """Verifies editorial rejection and demotion lifecycles: reject, dispute, archive, unarchive."""
    admin = _make_admin(client, db_session, "admin_demote@example.com")
    entity = _seed_entity(db_session, slug="demote-test-urn", name_vi="Demote Test Urn")
    source = _seed_source(db_session)
    db_session.commit()

    # 1. Draft -> Internal Review -> Rejected -> Draft
    claim = gov.create_claim(
        db_session,
        data={
            "entity_id": entity.id,
            "claim_type": "factual",
            "statement_vi": "Khẳng định này cần chỉnh sửa lại trước khi duyệt.",
            "verification_status": "draft",
            "origin": "editorial",
        },
        actor_id=admin.id,
    )
    gov.attach_source_to_claim(
        db_session, claim=claim, source=source, data={"support_type": "supports"}, actor_id=admin.id
    )
    gov.transition_claim_status(
        db_session, claim=claim, target="internal_review", actor_id=admin.id, reason="Peer review"
    )
    assert claim.verification_status == "internal_review"

    gov.transition_claim_status(
        db_session, claim=claim, target="rejected", actor_id=admin.id, reason="Requires citation page number"
    )
    assert claim.verification_status == "rejected"

    gov.transition_claim_status(
        db_session, claim=claim, target="draft", actor_id=admin.id, reason="Author revised wording"
    )
    assert claim.verification_status == "draft"

    # 2. Draft -> Internal Review -> Verified -> Disputed
    gov.transition_claim_status(
        db_session, claim=claim, target="internal_review", actor_id=admin.id, reason="Re-review"
    )
    gov.transition_claim_status(
        db_session, claim=claim, target="verified", actor_id=admin.id, reason="Approved"
    )
    assert claim.verification_status == "verified"

    gov.transition_claim_status(
        db_session, claim=claim, target="disputed", actor_id=admin.id, reason="Dispute raised by scholar"
    )
    assert claim.verification_status == "disputed"
    assert claim.confidence == "disputed"

    # 3. Disputed -> Draft -> Internal Review -> Verified -> Published -> Archived -> Draft
    gov.transition_claim_status(
        db_session, claim=claim, target="draft", actor_id=admin.id, reason="Resolving dispute"
    )
    claim.confidence = "high"
    db_session.flush()
    gov.transition_claim_status(
        db_session, claim=claim, target="internal_review", actor_id=admin.id, reason="Re-submitting"
    )
    gov.transition_claim_status(
        db_session, claim=claim, target="verified", actor_id=admin.id, reason="Re-verified"
    )
    gov.transition_claim_status(
        db_session, claim=claim, target="published", actor_id=admin.id, reason="Published"
    )
    assert claim.verification_status == "published"

    gov.transition_claim_status(
        db_session, claim=claim, target="archived", actor_id=admin.id, reason="Archiving outdated claim"
    )
    assert claim.verification_status == "archived"
    assert claim.is_current is False

    gov.transition_claim_status(
        db_session, claim=claim, target="draft", actor_id=admin.id, reason="Unarchiving for update"
    )
    assert claim.verification_status == "draft"
    assert claim.is_current is True


def test_entity_editorial_lifecycle_and_governance(client: TestClient, db_session):
    """Verifies entity editorial lifecycle: draft -> internal_review -> verified -> published."""
    admin = _make_admin(client, db_session, "admin_entity_life@example.com")
    teacher = _make_teacher(client, db_session, "teacher_entity_life@example.com")

    entity = gov.create_entity(
        db_session,
        data={
            "entity_type": "urn",
            "slug": "anh-dinh-urn",
            "name_vi": "Anh Đỉnh",
            "publication_status": "draft",
        },
        actor_id=teacher.id,
    )
    db_session.commit()
    assert entity.publication_status == "draft"
    initial_version = entity.content_version

    # Direct jump draft -> published on entity fails
    with pytest.raises(ValueError, match="Invalid editorial transition"):
        gov.transition_entity_status(
            db_session,
            entity=entity,
            target="published",
            actor_id=admin.id,
            reason="Illegal jump",
        )

    # Valid step 1: draft -> internal_review
    gov.transition_entity_status(
        db_session,
        entity=entity,
        target="internal_review",
        actor_id=teacher.id,
        reason="Entity metadata complete",
    )
    assert entity.publication_status == "internal_review"
    assert entity.content_version == initial_version + 1

    # Attach a disputed claim to test negative abuse: entity containing disputed claim cannot be published
    disputed_claim = gov.create_claim(
        db_session,
        data={
            "entity_id": entity.id,
            "claim_type": "factual",
            "statement_vi": "Khẳng định đang có tranh chấp về kích thước Anh Đỉnh.",
            "verification_status": "disputed",
            "confidence": "disputed",
            "origin": "editorial",
        },
        actor_id=teacher.id,
    )
    db_session.commit()

    # Step to verified
    gov.transition_entity_status(
        db_session,
        entity=entity,
        target="verified",
        actor_id=admin.id,
        reason="Entity facts verified",
    )
    assert entity.publication_status == "verified"

    # Attempt to publish entity with disputed claim -> strictly rejected
    with pytest.raises(ValueError, match="contains disputed claim"):
        gov.transition_entity_status(
            db_session,
            entity=entity,
            target="published",
            actor_id=admin.id,
            reason="Attempting to publish entity with disputed claim",
        )

    # Resolve disputed claim
    disputed_claim.verification_status = "verified"
    disputed_claim.confidence = "high"
    db_session.commit()

    # Now publishing entity succeeds
    gov.transition_entity_status(
        db_session,
        entity=entity,
        target="published",
        actor_id=admin.id,
        reason="All entity claims verified, approved for launch",
    )
    assert entity.publication_status == "published"


def test_immutable_audit_logging_and_query_api(client: TestClient, db_session):
    """Verifies that audit logs capture full provenance and are retrievable via admin API."""
    admin = _make_admin(client, db_session, "admin_audit_test@example.com")
    entity = _seed_entity(db_session, slug="audit-trace-urn", name_vi="Audit Trace Urn")
    source = _seed_source(db_session, title="Biên bản thẩm định 1837")
    db_session.commit()

    claim = gov.create_claim(
        db_session,
        data={
            "entity_id": entity.id,
            "claim_type": "factual",
            "statement_vi": "Khẳng định có truy vết kiểm toán đầy đủ.",
            "verification_status": "draft",
            "origin": "editorial",
        },
        actor_id=admin.id,
    )
    gov.attach_source_to_claim(
        db_session, claim=claim, source=source, data={"support_type": "supports"}, actor_id=admin.id
    )
    gov.transition_claim_status(
        db_session, claim=claim, target="internal_review", actor_id=admin.id, reason="Step 1: to review"
    )
    gov.transition_claim_status(
        db_session, claim=claim, target="verified", actor_id=admin.id, reason="Step 2: verified"
    )
    gov.transition_claim_status(
        db_session, claim=claim, target="published", actor_id=admin.id, reason="Step 3: published"
    )
    db_session.commit()

    # Query audit logs via admin API
    audit_res = client.get(
        "/api/v1/admin/history/audit",
        params={"resource_type": "claim", "resource_id": str(claim.id)},
    )
    assert audit_res.status_code == 200, audit_res.text
    data = audit_res.json()
    items = data["items"]
    assert len(items) >= 5

    actions = [item["action"] for item in items]
    assert "publish" in actions
    assert "verify" in actions
    assert "submit_for_review" in actions
    assert "attach_source" in actions
    assert "create" in actions

    # Verify latest action is publish with full diff
    latest = items[0]
    assert latest["action"] == "publish"
    assert latest["before"] == {"verification_status": "verified"}
    assert latest["after"] == {"verification_status": "published"}
    assert latest["reason"] == "Step 3: published"
    assert latest["actor_id"] == str(admin.id)
