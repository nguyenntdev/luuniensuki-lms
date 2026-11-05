# -*- coding: utf-8 -*-
"""V5-T078 (Wave W07, Slot A08): Human Editorial Review Queue & Governance Test Suite.

Audits and verifies:
1. Structured Editorial Review Queue:
   - GET /api/v1/admin/editorial/queue returns pending claims, entities, and sources.
   - Accurate attribution of author, AI draft indicators, source eligibility, rights status.
   - Summary counters across pending_review, internal_review, disputed, needs_source, needs_rights, ai_draft, verified.
2. Author / Reviewer Separation (Four-Eyes Principle):
   - Authors CANNOT verify or publish their own submissions (HTTP 403 HISTORY_SELF_APPROVAL_FORBIDDEN).
   - Independent peer human reviewers can verify and publish.
3. Negative Abuse Guardrails (Anti-AI Self-Approval & Non-Editorial Protection):
   - Automated AI agents cannot approve or publish their own drafts through API (HTTP 403 HISTORY_AI_APPROVAL_FORBIDDEN).
   - Automated AI agents cannot approve any drafts through API.
   - Non-editorial users (learners, guests, unauthenticated) are blocked (401/403).
4. Dispute Resolution Ledger:
   - Flagging disputes updates status and records in historical_content_audit_log.
   - GET /api/v1/admin/editorial/disputes lists active and resolved disputes.
   - POST /api/v1/admin/editorial/disputes/resolve adjudicates disputes with human accountability and notes.
5. Rights Sign-off (P09-A05 Legal/Permissions):
   - POST /api/v1/admin/editorial/rights-signoff records legal sign-off and license metadata.
   - Publication gate strictly blocks claims linked to restricted or revoked rights sources.
6. End-to-End Persistence:
   - Complete P09–P10 human review lifecycle persists through DB sessions and reloads.
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
def _login(client: TestClient, email: str, password: str = "Password123!"):
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, res.text


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


def _make_ai_agent(client: TestClient, db_session, email: str = "ai_agent@example.com", display_name: str = "AI Research Bot") -> User:
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


def _seed_entity(db_session, slug: str = "cao-dinh-urn", name_vi: str = "Cao Đỉnh") -> HistoricalEntity:
    entity = HistoricalEntity(
        id=uuid.uuid4(),
        entity_type="urn",
        slug=slug,
        name_vi=name_vi,
        publication_status="draft",
        content_version=1,
    )
    db_session.add(entity)
    db_session.flush()
    return entity


def _seed_source(
    db_session,
    title: str = "Đại Nam Thực Lục",
    rights_status: str = "cleared",
    license_str: str = "CC BY 4.0 / Educational Fair Use",
) -> HistoricalSource:
    source = HistoricalSource(
        id=uuid.uuid4(),
        source_type="royal_record",
        title=title,
        publication_year=1848,
        rights_status=rights_status,
        license=license_str,
        verification_status="metadata_verified",
    )
    db_session.add(source)
    db_session.flush()
    return source


# --------------------------------------------------------------------------- #
# Tests
# --------------------------------------------------------------------------- #
def test_editorial_queue_retrieval_and_filtering(client: TestClient, db_session):
    """Verifies that GET /api/v1/admin/editorial/queue lists pending items with accurate summary metrics."""
    admin = _make_admin(client, db_session, "admin_queue@example.com")
    entity = _seed_entity(db_session, slug="queue-urn", name_vi="Hàng Đợi Đỉnh")
    source = _seed_source(db_session, title="Khâm Định Đại Nam Hội Điển Sự Lệ")

    # 1. Human draft claim
    claim_human = gov.create_claim(
        db_session,
        data={
            "entity_id": entity.id,
            "claim_type": "factual",
            "statement_vi": "Đỉnh được đúc bằng đồng đỏ pha thiếc vào năm Minh Mạng thứ 17.",
            "verification_status": "draft",
            "origin": "editorial",
        },
        actor_id=admin.id,
    )
    gov.attach_source_to_claim(
        db_session, claim=claim_human, source=source, data={"support_type": "supports"}, actor_id=admin.id
    )

    # 2. AI draft claim awaiting human review
    claim_ai = gov.create_claim(
        db_session,
        data={
            "entity_id": entity.id,
            "claim_type": "factual",
            "statement_vi": "Họa tiết trên đỉnh miêu tả dãy núi Hồng Lĩnh hùng vĩ.",
            "verification_status": "internal_review",
            "origin": "ai_generated",
        },
        actor_id=None,
    )

    # 3. Disputed claim
    claim_disputed = gov.create_claim(
        db_session,
        data={
            "entity_id": entity.id,
            "claim_type": "factual",
            "statement_vi": "Trọng lượng đỉnh ước tính khoảng 3 tấn kim loại.",
            "verification_status": "disputed",
            "confidence": "disputed",
            "origin": "editorial",
        },
        actor_id=admin.id,
    )

    db_session.commit()

    # Query queue as admin
    res = client.get("/api/v1/admin/editorial/queue")
    assert res.status_code == 200, res.text
    body = res.json()
    assert "items" in body
    assert "summary" in body

    summary = body["summary"]
    assert summary["pending_review_count"] >= 2
    assert summary["internal_review_count"] >= 1
    assert summary["disputed_count"] >= 1
    assert summary["ai_draft_count"] >= 1

    # Verify AI draft item identification
    ai_items = [it for it in body["items"] if it["id"] == str(claim_ai.id)]
    assert len(ai_items) == 1
    assert ai_items[0]["is_ai_draft"] is True
    assert ai_items[0]["status"] == "internal_review"

    # Test status filter: only disputed
    res_disp = client.get("/api/v1/admin/editorial/queue", params={"status": "disputed"})
    assert res_disp.status_code == 200
    disp_items = res_disp.json()["items"]
    assert all(it["status"] == "disputed" for it in disp_items)


def test_four_eyes_author_reviewer_separation_enforced(client: TestClient, db_session):
    """Negative & positive test: Author CANNOT approve/verify their own submission (4-eyes rule); peer reviewer CAN."""
    author = _make_teacher(client, db_session, "author_teacher@example.com", "Author Teacher")
    entity = _seed_entity(db_session, slug="four-eyes-urn", name_vi="Tứ Nhãn Đỉnh")
    source = _seed_source(db_session)
    db_session.commit()

    # Author creates a claim draft and attaches source
    claim_res = client.post(
        "/api/v1/admin/history/claims",
        json={
            "entity_id": str(entity.id),
            "claim_type": "factual",
            "statement_vi": "Bản ghi này do Giáo viên A biên soạn và đưa vào quy trình thẩm định.",
            "verification_status": "draft",
            "origin": "editorial",
        },
    )
    assert claim_res.status_code == 200, claim_res.text
    claim_id = claim_res.json()["id"]

    client.post(
        f"/api/v1/admin/history/claims/{claim_id}/sources",
        json={"source_id": str(source.id), "support_type": "supports"},
    )

    # Author moves draft -> internal_review
    rev_res = client.post(
        "/api/v1/admin/editorial/review",
        json={
            "item_type": "claim",
            "item_id": claim_id,
            "action": "submit_for_review",
            "notes": "Hoàn tất bản thảo, gửi hội đồng bình duyệt.",
        },
    )
    assert rev_res.status_code == 200, rev_res.text
    assert rev_res.json()["new_status"] == "internal_review"

    # NEGATIVE ABUSE TEST: Author attempts to verify their own submission
    # Must fail with 403 HISTORY_SELF_APPROVAL_FORBIDDEN (Four-Eyes Principle)
    self_verify_res = client.post(
        "/api/v1/admin/editorial/review",
        json={
            "item_type": "claim",
            "item_id": claim_id,
            "action": "verify",
            "notes": "Tác giả tự duyệt công trình của chính mình.",
        },
    )
    assert self_verify_res.status_code == 403, self_verify_res.text
    err_body = self_verify_res.json()["error"]
    assert err_body["code"] == "HISTORY_SELF_APPROVAL_FORBIDDEN"
    assert "four-eyes" in err_body["message"].lower() or "author cannot" in err_body["message"].lower()

    # NEGATIVE ABUSE TEST: Author attempts to transition claim directly via transition endpoint with 4-eyes check
    self_trans_res = client.post(
        f"/api/v1/admin/history/claims/{claim_id}/transition",
        params={"target": "verified", "reason": "Tự duyệt", "require_four_eyes": True},
    )
    assert self_trans_res.status_code == 403, self_trans_res.text
    assert self_trans_res.json()["error"]["code"] == "HISTORY_SELF_APPROVAL_FORBIDDEN"

    # POSITIVE FLOW: Independent peer reviewer logs in and verifies
    reviewer = _make_admin(client, db_session, "peer_reviewer@example.com", "Peer Reviewer")
    peer_verify_res = client.post(
        "/api/v1/admin/editorial/review",
        json={
            "item_type": "claim",
            "item_id": claim_id,
            "action": "verify",
            "notes": "Đã đối chiếu với Đại Nam Thực Lục tập 3, tư liệu chính xác.",
        },
    )
    assert peer_verify_res.status_code == 200, peer_verify_res.text
    assert peer_verify_res.json()["new_status"] == "verified"
    assert peer_verify_res.json()["reviewer_id"] == str(reviewer.id)

    # Verify claim in DB has author != verifier
    claim_db = db_session.get(HistoricalClaim, uuid.UUID(claim_id))
    assert claim_db.verification_status == "verified"
    assert claim_db.created_by == author.id
    assert claim_db.verified_by == reviewer.id
    assert claim_db.created_by != claim_db.verified_by


def test_negative_abuse_ai_agent_cannot_approve_own_draft_or_any_draft(client: TestClient, db_session):
    """Negative abuse test: Automated AI bot accounts CANNOT approve or publish their own or any drafts."""
    human_author = _make_teacher(client, db_session, "human_teacher@example.com")
    ai_bot = _make_ai_agent(client, db_session, "ai_bot_approver@example.com")
    entity = _seed_entity(db_session, slug="ai-abuse-urn", name_vi="Kháng AI Đỉnh")
    source = _seed_source(db_session)
    db_session.commit()

    # 1. Draft created by AI
    ai_draft = gov.create_claim(
        db_session,
        data={
            "entity_id": entity.id,
            "claim_type": "factual",
            "statement_vi": "Khẳng định do mô hình AI tự sinh từ tài liệu scan OCR.",
            "verification_status": "internal_review",
            "origin": "ai_generated",
        },
        actor_id=ai_bot.id,
    )
    gov.attach_source_to_claim(
        db_session, claim=ai_draft, source=source, data={"support_type": "supports"}, actor_id=None
    )

    # 2. Draft created by human
    human_draft = gov.create_claim(
        db_session,
        data={
            "entity_id": entity.id,
            "claim_type": "factual",
            "statement_vi": "Khẳng định do con người nghiên cứu.",
            "verification_status": "internal_review",
            "origin": "editorial",
        },
        actor_id=human_author.id,
    )
    gov.attach_source_to_claim(
        db_session, claim=human_draft, source=source, data={"support_type": "supports"}, actor_id=None
    )
    db_session.commit()

    # Log in as AI bot
    client.post(
        "/api/v1/auth/login",
        json={"email": "ai_bot_approver@example.com", "password": "Password123!"},
    )

    # Attempt A: AI bot tries to approve its OWN draft via review endpoint
    ai_self_res = client.post(
        "/api/v1/admin/editorial/review",
        json={
            "item_type": "claim",
            "item_id": str(ai_draft.id),
            "action": "verify",
            "notes": "AI tự duyệt khẳng định của chính mình.",
        },
    )
    assert ai_self_res.status_code == 403, ai_self_res.text
    assert ai_self_res.json()["error"]["code"] == "HISTORY_AI_APPROVAL_FORBIDDEN"
    assert "AI agent" in ai_self_res.json()["error"]["message"]

    # Attempt B: AI bot tries to approve human draft via review endpoint
    ai_human_res = client.post(
        "/api/v1/admin/editorial/review",
        json={
            "item_type": "claim",
            "item_id": str(human_draft.id),
            "action": "verify",
            "notes": "AI duyệt khẳng định của con người.",
        },
    )
    assert ai_human_res.status_code == 403, ai_human_res.text
    assert ai_human_res.json()["error"]["code"] == "HISTORY_AI_APPROVAL_FORBIDDEN"

    # Attempt C: AI bot tries transition endpoint
    ai_trans_res = client.post(
        f"/api/v1/admin/history/claims/{ai_draft.id}/transition",
        params={"target": "verified", "reason": "AI transition"},
    )
    assert ai_trans_res.status_code == 403, ai_trans_res.text
    assert ai_trans_res.json()["error"]["code"] == "HISTORY_AI_APPROVAL_FORBIDDEN"


def test_non_editorial_roles_strictly_forbidden(client: TestClient, db_session):
    """Negative abuse test: Learner, guest, and unauthenticated users receive 401/403."""
    entity = _seed_entity(db_session, slug="rbac-urn", name_vi="RBAC Đỉnh")
    claim = gov.create_claim(
        db_session,
        data={
            "entity_id": entity.id,
            "claim_type": "factual",
            "statement_vi": "Kiểm tra quyền hạn truy cập.",
            "verification_status": "draft",
            "origin": "editorial",
        },
    )
    db_session.commit()

    # 1. Unauthenticated request
    unauth_client = TestClient(client.app)
    unauth_queue = unauth_client.get("/api/v1/admin/editorial/queue")
    assert unauth_queue.status_code == 401

    unauth_review = unauth_client.post(
        "/api/v1/admin/editorial/review",
        json={"item_type": "claim", "item_id": str(claim.id), "action": "verify", "notes": "No auth"},
    )
    assert unauth_review.status_code == 401

    # 2. Learner request
    _make_learner(client, db_session, "student_user@example.com")
    learner_queue = client.get("/api/v1/admin/editorial/queue")
    assert learner_queue.status_code == 403

    learner_review = client.post(
        "/api/v1/admin/editorial/review",
        json={"item_type": "claim", "item_id": str(claim.id), "action": "verify", "notes": "Learner attempt"},
    )
    assert learner_review.status_code == 403

    # 3. Guest request
    _make_guest(client, db_session, "guest_user@example.com")
    guest_queue = client.get("/api/v1/admin/editorial/queue")
    assert guest_queue.status_code == 403


def test_dispute_resolution_ledger_workflow(client: TestClient, db_session):
    """Verifies dispute flagging, ledger indexing, and human adjudication workflow."""
    editor_a = _make_teacher(client, db_session, "editor_a@example.com", "Editor A")
    entity = _seed_entity(db_session, slug="dispute-ledger-urn", name_vi="Tranh Chấp Đỉnh")
    source = _seed_source(db_session)

    claim = gov.create_claim(
        db_session,
        data={
            "entity_id": entity.id,
            "claim_type": "factual",
            "statement_vi": "Năm đúc đỉnh có dị bản ghi là 1836 thay vì 1835.",
            "verification_status": "internal_review",
            "origin": "editorial",
        },
        actor_id=editor_a.id,
    )
    gov.attach_source_to_claim(
        db_session, claim=claim, source=source, data={"support_type": "supports"}, actor_id=editor_a.id
    )
    db_session.commit()

    # Step 1: Flag dispute
    flag_res = client.post(
        "/api/v1/admin/editorial/review",
        json={
            "item_type": "claim",
            "item_id": str(claim.id),
            "action": "flag_dispute",
            "notes": "Phát hiện mâu thuẫn giữa Châu bản triều Nguyễn và bia ký.",
        },
    )
    assert flag_res.status_code == 200, flag_res.text
    assert flag_res.json()["new_status"] == "disputed"

    # Step 2: Query dispute ledger
    disp_list_res = client.get("/api/v1/admin/editorial/disputes")
    assert disp_list_res.status_code == 200
    disp_body = disp_list_res.json()
    assert disp_body["active_count"] >= 1
    matched = [d for d in disp_body["items"] if d["resource_id"] == str(claim.id)]
    assert len(matched) >= 1
    assert "Châu bản" in matched[0]["dispute_reason"]

    # Step 3: Human adjudicator resolves dispute
    adjudicator = _make_admin(client, db_session, "adjudicator@example.com", "Chief Editor")
    resolve_res = client.post(
        "/api/v1/admin/editorial/disputes/resolve",
        json={
            "item_type": "claim",
            "item_id": str(claim.id),
            "resolution": "resolved",
            "resolution_notes": "Đã khảo sát bia ký gốc tại Đại Nội; thống nhất ghi nhận 1835 theo văn bản sắc phong.",
            "cited_source_id": str(source.id),
        },
    )
    assert resolve_res.status_code == 200, resolve_res.text
    res_data = resolve_res.json()
    assert res_data["success"] is True
    assert res_data["resolution"] == "resolved"
    assert res_data["status"] == "draft"

    # Verify claim status in DB is unblocked
    db_session.expire_all()
    claim_db = db_session.get(HistoricalClaim, claim.id)
    assert claim_db.verification_status == "draft"
    assert claim_db.confidence != "disputed"


def test_rights_signoff_workflow_and_publication_gate(client: TestClient, db_session):
    """Verifies rights clearance sign-off and publication blocking for restricted rights sources."""
    admin = _make_admin(client, db_session, "rights_admin@example.com")
    entity = _seed_entity(db_session, slug="rights-urn", name_vi="Bản Quyền Đỉnh")

    # Source 1: Restricted rights
    restricted_source = _seed_source(
        db_session, title="Tư liệu hạn chế lưu hành nội bộ", rights_status="restricted"
    )

    # Source 2: Cleared rights
    cleared_source = _seed_source(
        db_session, title="Tư liệu công khai Đại Nội", rights_status="unreviewed"
    )

    claim = gov.create_claim(
        db_session,
        data={
            "entity_id": entity.id,
            "claim_type": "factual",
            "statement_vi": "Khẳng định liên kết với nguồn tư liệu có bản quyền nghiêm ngặt.",
            "verification_status": "draft",
            "origin": "editorial",
        },
        actor_id=admin.id,
    )
    db_session.commit()

    # Step 1: Sign off rights for Source 2 via endpoint
    signoff_res = client.post(
        "/api/v1/admin/editorial/rights-signoff",
        json={
            "resource_type": "source",
            "resource_id": str(cleared_source.id),
            "rights_status": "cleared",
            "rights_owner": "Trung tâm Bảo tồn Di tích Cố đô Huế (HMCC)",
            "license": "CC BY 4.0 / Educational Fair Use",
            "legal_basis": "Quyết định lưu trữ di sản số 42/QĐ-HMCC",
            "notes": "Đã hoàn thành rà soát pháp lý P09-A05.",
        },
    )
    assert signoff_res.status_code == 200, signoff_res.text
    assert signoff_res.json()["rights_status"] == "cleared"

    # Step 2: Attach restricted source to claim, verify claim, and attempt publication
    gov.attach_source_to_claim(
        db_session, claim=claim, source=restricted_source, data={"support_type": "supports"}, actor_id=admin.id
    )
    teacher = _make_teacher(client, db_session, "peer_teacher@example.com")
    gov.transition_claim_status(
        db_session, claim=claim, target="internal_review", actor_id=teacher.id, reason="Ready"
    )
    gov.transition_claim_status(
        db_session, claim=claim, target="verified", actor_id=teacher.id, reason="Verified"
    )
    db_session.commit()

    # Attempt to publish claim bound to restricted source
    # Must fail with 422 rejected by publication rights gate
    _make_admin(client, db_session, "rights_admin@example.com")
    pub_res = client.post(
        f"/api/v1/admin/history/claims/{claim.id}/transition",
        params={"target": "published", "reason": "Thử xuất bản tài liệu bị hạn chế quyền"},
    )
    assert pub_res.status_code == 422, pub_res.text
    assert "restricted/revoked rights" in pub_res.json()["error"]["message"]


def test_editorial_lifecycle_e2e_persistence(client: TestClient, db_session):
    """End-to-end P09–P10 test: Draft -> Submit Review -> Peer Verification -> Rights Sign-off -> Publication."""
    author = _make_teacher(client, db_session, "author_e2e@example.com", "E2E Author")
    reviewer = _make_teacher(client, db_session, "reviewer_e2e@example.com", "E2E Reviewer")
    publisher = _make_admin(client, db_session, "publisher_e2e@example.com", "E2E Publisher")

    entity = _seed_entity(db_session, slug="e2e-urn", name_vi="Cửu Đỉnh Toàn Thư")
    source = _seed_source(db_session, title="Khâm Định Đại Nam Hội Điển Sự Lệ Tập 15", rights_status="cleared")
    db_session.commit()

    # 1. Author creates draft
    _login(client, "author_e2e@example.com")
    claim_res = client.post(
        "/api/v1/admin/history/claims",
        json={
            "entity_id": str(entity.id),
            "claim_type": "factual",
            "statement_vi": "Cửu Đỉnh được công nhận là Bảo vật Quốc gia của Việt Nam.",
            "verification_status": "draft",
            "origin": "editorial",
        },
    )
    assert claim_res.status_code == 200
    claim_id = claim_res.json()["id"]

    # 2. Author attaches source
    bind_res = client.post(
        f"/api/v1/admin/history/claims/{claim_id}/sources",
        json={"source_id": str(source.id), "support_type": "supports", "page_start": "112"},
    )
    assert bind_res.status_code == 200

    # 3. Author submits for peer review
    sub_res = client.post(
        "/api/v1/admin/editorial/review",
        json={
            "item_type": "claim",
            "item_id": claim_id,
            "action": "submit_for_review",
            "notes": "Hoàn tất bản thảo, gửi hội đồng.",
        },
    )
    assert sub_res.status_code == 200
    assert sub_res.json()["new_status"] == "internal_review"

    # 4. Reviewer reviews and verifies (distinct from author)
    _login(client, "reviewer_e2e@example.com")
    ver_res = client.post(
        "/api/v1/admin/editorial/review",
        json={
            "item_type": "claim",
            "item_id": claim_id,
            "action": "verify",
            "notes": "Đã đối chiếu với quyết định công nhận Bảo vật Quốc gia năm 2012.",
        },
    )
    assert ver_res.status_code == 200
    assert ver_res.json()["new_status"] == "verified"

    # 5. Publisher publishes to public atlas
    _login(client, "publisher_e2e@example.com")
    pub_res = client.post(
        "/api/v1/admin/editorial/review",
        json={
            "item_type": "claim",
            "item_id": claim_id,
            "action": "publish",
            "notes": "Phê duyệt xuất bản toàn văn trên bản đồ số di sản.",
        },
    )
    assert pub_res.status_code == 200
    assert pub_res.json()["new_status"] == "published"

    # 6. Database verification across a clean reload
    db_session.expire_all()
    claim_final = db_session.get(HistoricalClaim, uuid.UUID(claim_id))
    assert claim_final.verification_status == "published"
    assert claim_final.created_by == author.id
    assert claim_final.verified_by == reviewer.id
    assert claim_final.is_published is True

    # Check audit trail has all 5 distinct lifecycle actions
    audit_entries = list(
        db_session.scalars(
            select(HistoricalContentAuditLog)
            .where(HistoricalContentAuditLog.resource_id == uuid.UUID(claim_id))
            .order_by(HistoricalContentAuditLog.id.asc())
        )
    )
    action_sequence = [a.action for a in audit_entries]
    assert "create" in action_sequence
    assert "attach_source" in action_sequence
    assert "submit_for_review" in action_sequence
    assert "verify" in action_sequence
    assert "publish" in action_sequence
