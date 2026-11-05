# -*- coding: utf-8 -*-
"""V5-T093 (Wave W09, Slot A03): Evidence board for collaborative inquiry groups.

Audits and verifies:
1. Collaborative Comparative Source Evidence Board:
   - Group members can view, add, update, and categorize evidence cards on the 4-column board
     (supporting, refuting, synthesis, unresolved).
   - Moving cards across columns updates column and support_type attributes.
2. Comparative Source-to-Source and Source-to-Claim Links:
   - Peer group members can create comparative links between historical sources
     (relation_type: supports, refutes, corroborates, contrasts, qualifies).
3. Teacher Inline Feedback:
   - Classroom teachers / staff can annotate evidence cards with inline pedagogical feedback.
   - Students cannot self-post teacher inline feedback (403 Forbidden).
4. Revision Cycles & Re-submission:
   - Teacher can request revisions on an evidence board, unlocking it for student edits
     and recording cycle history in revision_history.
   - Group members can resubmit revised evidence board, incrementing revision_cycle.
5. Strict Negative Abuse Isolation:
   - Students outside the group CANNOT inject evidence cards into another group's board (403 Forbidden).
   - Students outside the group CANNOT update cards on another group's board (403 Forbidden).
   - Students outside the group CANNOT delete cards from another group's board (403 Forbidden).
   - Students outside the group CANNOT create comparative links on another group's board (403 Forbidden).
   - Students outside the group CANNOT view a private board or its revision history (403 Forbidden).
"""
from __future__ import annotations

import uuid
from typing import Any
import pytest
from sqlalchemy import select

from backend.history_inquiry_models import (
    HistoricalInquiryActivity,
    HistoricalInquiryGroup,
    HistoricalInquiryGroupMember,
    HistoricalInquirySubmission,
    InquiryMemberRole,
    InquiryPrivacyMode,
    InquirySubmissionStatus,
)
from backend.history_models import HistoricalClaim, HistoricalEntity, HistoricalSource
from backend.models import ClassMember, Classroom, User, UserRole
from backend.security import hash_password


def _create_user(
    db_session,
    email: str,
    role: UserRole = UserRole.learner,
    display_name: str | None = None,
) -> User:
    """Helper to persist a user with specific role for tenant/group tests."""
    user = User(
        email=email,
        password_hash=hash_password("Password123!"),
        display_name=display_name or f"User {email.split('@')[0]}",
        username=f"user_{uuid.uuid4().hex[:8]}",
        role=role,
        is_profile_public=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _login_user(client, email: str, password: str = "Password123!"):
    """Login helper setting session cookies on test client."""
    res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"


def _seed_sources_and_claims(db_session):
    """Seed primary sources and claims for inquiry board tests."""
    source1 = HistoricalSource(
        source_type="royal_chronicle",
        title="Đại Nam Thực Lục Chính Biên",
        author_text="Quốc sử quán triều Nguyễn",
        publication_year=1848,
        pages="Đệ nhị kỷ, quyển 154, tờ 12a",
        verification_status="expert_verified",
        license="Public Domain",
        rights_status="public_domain",
        url="https://archives.org.vn/dntl-154",
    )
    source2 = HistoricalSource(
        source_type="court_gazette",
        title="Khâm Định Đại Nam Hội Điển Sự Lệ",
        author_text="Nội các triều Nguyễn",
        publication_year=1851,
        pages="Quyển 214, Công bộ - Đúc tượng vạc",
        verification_status="expert_verified",
        license="Public Domain",
        rights_status="public_domain",
        url="https://archives.org.vn/hoidien-214",
    )
    source3 = HistoricalSource(
        source_type="research_monograph",
        title="Mỹ thuật thời Nguyễn",
        author_text="Nguyễn Bá Lăng",
        publication_year=1974,
        pages="Trang 88-92",
        verification_status="expert_verified",
        license="CC BY-NC",
        rights_status="non_commercial",
    )
    db_session.add_all([source1, source2, source3])
    db_session.flush()

    entity = HistoricalEntity(
        entity_type="urn",
        slug=f"cao-dinh-board-{uuid.uuid4().hex[:6]}",
        name_vi="Cao Đỉnh",
        publication_status="published",
    )
    db_session.add(entity)
    db_session.flush()

    claim = HistoricalClaim(
        entity_id=entity.id,
        claim_key=f"claim_board_{uuid.uuid4().hex[:8]}",
        claim_type="historical_fact",
        statement_vi="Cao Đỉnh được khởi công đúc vào tháng 10 năm Ất Mùi (1835) thời Minh Mạng.",
        origin="editorial",
        verification_status="expert_verified",
        confidence="high",
    )
    db_session.add(claim)
    db_session.commit()
    db_session.refresh(source1)
    db_session.refresh(source2)
    db_session.refresh(source3)
    db_session.refresh(claim)
    return source1, source2, source3, claim


def _setup_board_env(db_session):
    """Create classroom environment with teacher, two distinct groups, and outsider."""
    teacher = _create_user(db_session, f"teacher_board_{uuid.uuid4().hex[:6]}@school.edu.vn", role=UserRole.teacher, display_name="Thầy Phan Sử Học")
    student_a1 = _create_user(db_session, f"student_a1_{uuid.uuid4().hex[:6]}@school.edu.vn", display_name="Nguyễn Văn A (Nhóm 1)")
    student_a2 = _create_user(db_session, f"student_a2_{uuid.uuid4().hex[:6]}@school.edu.vn", display_name="Trần Thị B (Nhóm 1)")
    student_b1 = _create_user(db_session, f"student_b1_{uuid.uuid4().hex[:6]}@school.edu.vn", display_name="Lê Văn C (Nhóm 2)")
    outsider = _create_user(db_session, f"outsider_{uuid.uuid4().hex[:6]}@other.edu.vn", display_name="Học sinh trường ngoài")

    classroom = Classroom(
        name="Lớp 11 Sử — Nghiên Cứu Bảng Bằng Chứng",
        teacher_id=teacher.id,
        class_code=f"EB{uuid.uuid4().hex[:4].upper()}",
        is_archived=False,
    )
    db_session.add(classroom)
    db_session.commit()
    db_session.refresh(classroom)

    for u in [student_a1, student_a2, student_b1]:
        cm = ClassMember(class_id=classroom.id, user_id=u.id, role="learner")
        db_session.add(cm)
    db_session.commit()

    return {
        "teacher": teacher,
        "student_a1": student_a1,
        "student_a2": student_a2,
        "student_b1": student_b1,
        "outsider": outsider,
        "classroom": classroom,
    }


# =========================================================================== #
# Test 1: Collaborative Evidence Board Retrieval & Card Lifecycle
# =========================================================================== #
def test_evidence_board_card_lifecycle(client, db_session):
    env = _setup_board_env(db_session)
    source1, source2, _, claim = _seed_sources_and_claims(db_session)

    # 1. Teacher creates inquiry activity
    _login_user(client, env["teacher"].email)
    res_act = client.post(
        "/api/v1/history/inquiry/activities",
        json={
            "classroom_id": str(env["classroom"].id),
            "title": "Khảo cứu đối chiếu văn bản và hiện vật Cửu Đỉnh",
            "description": "Xây dựng bảng chứng cứ đa nguồn",
        },
    )
    assert res_act.status_code == 201
    activity_id = res_act.json()["id"]

    # 2. Student A1 creates Group 1
    _login_user(client, env["student_a1"].email)
    res_grp = client.post(
        f"/api/v1/history/inquiry/activities/{activity_id}/groups",
        json={"name": "Nhóm 1 — Khảo Luận", "member_ids": [str(env["student_a2"].id)]},
    )
    assert res_grp.status_code == 201
    group_1_id = res_grp.json()["id"]

    # 3. Retrieve board
    res_board = client.get(f"/api/v1/history/inquiry/groups/{group_1_id}/board")
    assert res_board.status_code == 200
    board_data = res_board.json()
    assert board_data["group_name"] == "Nhóm 1 — Khảo Luận"
    assert "supporting" in board_data["columns"]
    assert "refuting" in board_data["columns"]
    assert board_data["revision_cycle"] == 1

    # 4. Student A1 adds a supporting card
    res_card1 = client.post(
        f"/api/v1/history/inquiry/groups/{group_1_id}/board/cards",
        json={
            "source_id": str(source1.id),
            "locator": "Đệ nhị kỷ, quyển 154, tờ 12a",
            "excerpt": "Đúc chín cái đỉnh to đặt trước sân Thế Miếu...",
            "claim_id": str(claim.id),
            "support_type": "supports",
            "board_column": "supporting",
            "interpretation_note": "Khẳng định niên đại khởi công và vị trí đặt đỉnh trang trọng.",
        },
    )
    assert res_card1.status_code == 201
    card1 = res_card1.json()
    assert card1["board_column"] == "supporting"
    assert card1["source_title"] == "Đại Nam Thực Lục Chính Biên"
    assert card1["contributed_by_name"] == env["student_a1"].display_name

    # 5. Peer Student A2 updates card column to 'synthesis'
    _login_user(client, env["student_a2"].email)
    res_update = client.put(
        f"/api/v1/history/inquiry/groups/{group_1_id}/board/cards/{card1['id']}",
        json={
            "board_column": "synthesis",
            "interpretation_note": "Cập nhật suy luận: Sử liệu này làm nền tảng tổng hợp toàn bộ luận điểm.",
        },
    )
    assert res_update.status_code == 200
    updated_card = res_update.json()
    assert updated_card["board_column"] == "synthesis"
    assert "Cập nhật suy luận" in updated_card["interpretation_note"]

    # 6. Delete card verification
    res_del = client.delete(f"/api/v1/history/inquiry/groups/{group_1_id}/board/cards/{card1['id']}")
    assert res_del.status_code == 200

    # Board now has 0 cards
    res_board2 = client.get(f"/api/v1/history/inquiry/groups/{group_1_id}/board")
    assert len(res_board2.json()["cards"]) == 0


# =========================================================================== #
# Test 2: Comparative Source Evidence Links (Supports / Refutes / Corroborates)
# =========================================================================== #
def test_comparative_source_evidence_links(client, db_session):
    env = _setup_board_env(db_session)
    source1, source2, source3, claim = _seed_sources_and_claims(db_session)

    _login_user(client, env["teacher"].email)
    res_act = client.post(
        "/api/v1/history/inquiry/activities",
        json={"classroom_id": str(env["classroom"].id), "title": "So sánh Thực Lục và Hội Điển", "description": "Đối chiếu nguồn sử liệu văn bản"},
    )
    assert res_act.status_code == 201, f"Create activity failed: {res_act.text}"
    activity_id = res_act.json()["id"]

    _login_user(client, env["student_a1"].email)
    res_grp = client.post(
        f"/api/v1/history/inquiry/activities/{activity_id}/groups",
        json={"name": "Nhóm 1", "member_ids": [str(env["student_a2"].id)]},
    )
    group_1_id = res_grp.json()["id"]

    # Add comparative link between source1 and source2
    res_link = client.post(
        f"/api/v1/history/inquiry/groups/{group_1_id}/board/comparisons",
        json={
            "source_id_a": str(source1.id),
            "source_id_b": str(source2.id),
            "relation_type": "corroborates",
            "rationale": "Cả Thực Lục và Hội Điển đều thống nhất về khối lượng đồng và danh sách nghệ nhân Công bộ.",
        },
    )
    assert res_link.status_code == 201
    link_data = res_link.json()
    assert link_data["relation_type"] == "corroborates"
    assert link_data["source_title_a"] == "Đại Nam Thực Lục Chính Biên"
    assert link_data["source_title_b"] == "Khâm Định Đại Nam Hội Điển Sự Lệ"

    # Add comparative link with claim (source vs claim refute/contrast)
    res_link2 = client.post(
        f"/api/v1/history/inquiry/groups/{group_1_id}/board/comparisons",
        json={
            "source_id_a": str(source3.id),
            "claim_id": str(claim.id),
            "relation_type": "contrasts",
            "rationale": "Khảo cứu năm 1974 đưa ra giả thiết khác về hợp kim đúc, đối chiếu với khẳng định chính sử.",
        },
    )
    assert res_link2.status_code == 201
    assert res_link2.json()["relation_type"] == "contrasts"

    # Verify links appear in board payload
    res_board = client.get(f"/api/v1/history/inquiry/groups/{group_1_id}/board")
    assert len(res_board.json()["comparative_links"]) == 2

    # Remove one comparative link
    res_del_link = client.delete(f"/api/v1/history/inquiry/groups/{group_1_id}/board/comparisons/{link_data['id']}")
    assert res_del_link.status_code == 200

    res_board_after = client.get(f"/api/v1/history/inquiry/groups/{group_1_id}/board")
    assert len(res_board_after.json()["comparative_links"]) == 1


# =========================================================================== #
# Test 3: Teacher Inline Feedback Annotations
# =========================================================================== #
def test_teacher_inline_feedback_on_cards(client, db_session):
    env = _setup_board_env(db_session)
    source1, _, _, _ = _seed_sources_and_claims(db_session)

    _login_user(client, env["teacher"].email)
    res_act = client.post(
        "/api/v1/history/inquiry/activities",
        json={"classroom_id": str(env["classroom"].id), "title": "Hoạt động góp ý giáo viên", "description": "Góp ý sư phạm trên thẻ bằng chứng"},
    )
    assert res_act.status_code == 201, f"Create activity failed: {res_act.text}"
    activity_id = res_act.json()["id"]

    _login_user(client, env["student_a1"].email)
    res_grp = client.post(
        f"/api/v1/history/inquiry/activities/{activity_id}/groups",
        json={"name": "Nhóm 1"},
    )
    group_1_id = res_grp.json()["id"]

    # Student adds card
    res_card = client.post(
        f"/api/v1/history/inquiry/groups/{group_1_id}/board/cards",
        json={
            "source_id": str(source1.id),
            "locator": "Tờ 12a",
            "excerpt": "Đúc chín cái đỉnh to...",
            "interpretation_note": "Ý kiến ban đầu của nhóm.",
            "support_type": "supports",
        },
    )
    card_id = res_card.json()["id"]

    # Negative test: Student cannot post teacher inline feedback
    res_student_fb = client.post(
        f"/api/v1/history/inquiry/groups/{group_1_id}/board/feedback",
        json={
            "target_type": "card",
            "target_id": card_id,
            "comment": "Em tự nhận xét thẻ của mình.",
        },
    )
    assert res_student_fb.status_code == 403
    assert res_student_fb.json()["error"]["code"] == "FORBIDDEN_SCOPE"

    # Teacher posts valid pedagogical inline feedback
    _login_user(client, env["teacher"].email)
    res_teacher_fb = client.post(
        f"/api/v1/history/inquiry/groups/{group_1_id}/board/feedback",
        json={
            "target_type": "card",
            "target_id": card_id,
            "comment": "Thầy khen: trích dẫn chuẩn xác. Cần đối chiếu thêm với quy chế Công bộ trong Hội Điển tờ 15.",
        },
    )
    assert res_teacher_fb.status_code == 201
    fb_data = res_teacher_fb.json()
    assert fb_data["teacher_name"] == env["teacher"].display_name
    assert "Thầy khen" in fb_data["comment"]

    # Fetch board and verify card has inline feedback attached
    res_board = client.get(f"/api/v1/history/inquiry/groups/{group_1_id}/board")
    card_in_board = next(c for c in res_board.json()["cards"] if c["id"] == card_id)
    assert len(card_in_board["inline_feedback"]) == 1
    assert card_in_board["inline_feedback"][0]["comment"] == fb_data["comment"]


# =========================================================================== #
# Test 4: Revision Cycles & Re-submission Workflow
# =========================================================================== #
def test_teacher_revision_cycle_and_resubmission(client, db_session):
    env = _setup_board_env(db_session)
    source1, _, _, _ = _seed_sources_and_claims(db_session)

    _login_user(client, env["teacher"].email)
    res_act = client.post(
        "/api/v1/history/inquiry/activities",
        json={"classroom_id": str(env["classroom"].id), "title": "Chu kỳ sửa đổi", "description": "Sửa đổi và nâng cấp bảng bằng chứng"},
    )
    assert res_act.status_code == 201, f"Create activity failed: {res_act.text}"
    activity_id = res_act.json()["id"]

    # 1. Student creates group, adds card, sets hypothesis & synthesis, then submits
    _login_user(client, env["student_a1"].email)
    res_grp = client.post(
        f"/api/v1/history/inquiry/activities/{activity_id}/groups",
        json={"name": "Nhóm 1"},
    )
    group_1_id = res_grp.json()["id"]

    client.post(
        f"/api/v1/history/inquiry/groups/{group_1_id}/board/cards",
        json={
            "source_id": str(source1.id),
            "locator": "Tờ 12a",
            "excerpt": "Đúc chín cái đỉnh to...",
            "interpretation_note": "Minh chứng",
            "support_type": "supports",
        },
    )
    client.put(
        f"/api/v1/history/inquiry/groups/{group_1_id}/submission",
        json={
            "hypothesis": "Cao Đỉnh biểu thị quyền lực tối thượng thời Minh Mạng",
            "synthesis_argument": "Dựa vào Thực Lục để chứng minh niên đại và biểu tượng.",
        },
    )

    # Submit board
    res_sub = client.post(f"/api/v1/history/inquiry/groups/{group_1_id}/submit")
    assert res_sub.status_code == 200
    assert res_sub.json()["status"] == "submitted"

    # While submitted, board is locked for student changes
    res_locked_card = client.post(
        f"/api/v1/history/inquiry/groups/{group_1_id}/board/cards",
        json={
            "source_id": str(source1.id),
            "locator": "Tờ 13b",
            "excerpt": "Thêm sử liệu...",
            "interpretation_note": "Ghi chú",
        },
    )
    assert res_locked_card.status_code == 400
    assert res_locked_card.json()["error"]["code"] == "SUBMISSION_LOCKED"

    # 2. Teacher reviews and requests revision
    _login_user(client, env["teacher"].email)
    res_req_rev = client.post(
        f"/api/v1/history/inquiry/groups/{group_1_id}/board/request-revision",
        json={
            "teacher_feedback": "Nhóm cần bổ sung thêm bằng chứng phản bác giả thuyết dã sử.",
            "score": 75.0,
        },
    )
    assert res_req_rev.status_code == 200
    assert res_req_rev.json()["status"] == "revision_requested"

    # 3. Student can now edit board again
    _login_user(client, env["student_a1"].email)
    res_card2 = client.post(
        f"/api/v1/history/inquiry/groups/{group_1_id}/board/cards",
        json={
            "source_id": str(source1.id),
            "locator": "Tờ 14a",
            "excerpt": "Bổ sung bằng chứng theo yêu cầu thầy giáo...",
            "interpretation_note": "Đã hoàn thành góp ý của giáo viên.",
            "support_type": "supports",
            "board_column": "supporting",
        },
    )
    assert res_card2.status_code == 201

    # 4. Student resubmits board -> Revision cycle increments to 2
    res_resubmit = client.post(
        f"/api/v1/history/inquiry/groups/{group_1_id}/board/resubmit",
        json={"revision_notes": "Nhóm đã bổ sung thêm tư liệu Tờ 14a để giải tỏa thắc mắc."},
    )
    assert res_resubmit.status_code == 200
    resub_data = res_resubmit.json()
    assert resub_data["status"] == "submitted"
    assert resub_data["revision_cycle"] == 2

    # 5. Check revision audit history
    res_rev_hist = client.get(f"/api/v1/history/inquiry/groups/{group_1_id}/board/revisions")
    assert res_rev_hist.status_code == 200
    rev_hist_data = res_rev_hist.json()
    assert rev_hist_data["revision_cycle"] == 2
    assert len(rev_hist_data["history"]) >= 2
    actions = [h["action"] for h in rev_hist_data["history"]]
    assert "revision_requested" in actions
    assert "resubmitted" in actions


# =========================================================================== #
# Test 5: Negative Abuse — Student Outside Group Cannot Alter Evidence Board
# =========================================================================== #
def test_negative_abuse_outside_student_cannot_alter_board(client, db_session):
    env = _setup_board_env(db_session)
    source1, source2, _, _ = _seed_sources_and_claims(db_session)

    # Teacher creates activity
    _login_user(client, env["teacher"].email)
    res_act = client.post(
        "/api/v1/history/inquiry/activities",
        json={"classroom_id": str(env["classroom"].id), "title": "Bảo mật bảng bằng chứng", "description": "Bảo mật và cô lập dữ liệu nhóm"},
    )
    assert res_act.status_code == 201, f"Create activity failed: {res_act.text}"
    activity_id = res_act.json()["id"]

    # Student A1 creates Group 1
    _login_user(client, env["student_a1"].email)
    res_grp1 = client.post(
        f"/api/v1/history/inquiry/activities/{activity_id}/groups",
        json={"name": "Nhóm 1 (Alpha)"},
    )
    group_1_id = res_grp1.json()["id"]

    # Legitimate card added by Student A1
    res_legit_card = client.post(
        f"/api/v1/history/inquiry/groups/{group_1_id}/board/cards",
        json={
            "source_id": str(source1.id),
            "locator": "Tờ 12a",
            "excerpt": "Sử liệu gốc nhóm 1",
            "interpretation_note": "Ghi chú nhóm 1",
            "support_type": "supports",
        },
    )
    card_id = res_legit_card.json()["id"]

    # Student B1 (Nhóm 2) logs in and tries to abuse Group 1's board:
    _login_user(client, env["student_b1"].email)

    # 1. CANNOT inject card into Group 1's board -> 403 Forbidden
    res_inject = client.post(
        f"/api/v1/history/inquiry/groups/{group_1_id}/board/cards",
        json={
            "source_id": str(source2.id),
            "locator": "Tờ 99x",
            "excerpt": "Bằng chứng giả mạo từ nhóm đối thủ",
            "interpretation_note": "Phá hoại bảng của nhóm 1",
            "support_type": "refutes",
        },
    )
    assert res_inject.status_code == 403
    assert res_inject.json()["error"]["code"] == "FORBIDDEN_SCOPE"

    # 2. CANNOT alter/update card on Group 1's board -> 403 Forbidden
    res_alter = client.put(
        f"/api/v1/history/inquiry/groups/{group_1_id}/board/cards/{card_id}",
        json={"interpretation_note": "Đã bị nhóm khác sửa đổi trái phép"},
    )
    assert res_alter.status_code == 403
    assert res_alter.json()["error"]["code"] == "FORBIDDEN_SCOPE"

    # 3. CANNOT delete card on Group 1's board -> 403 Forbidden
    res_del_abuse = client.delete(f"/api/v1/history/inquiry/groups/{group_1_id}/board/cards/{card_id}")
    assert res_del_abuse.status_code == 403
    assert res_del_abuse.json()["error"]["code"] == "FORBIDDEN_SCOPE"

    # 4. CANNOT create comparative link on Group 1's board -> 403 Forbidden
    res_comp_abuse = client.post(
        f"/api/v1/history/inquiry/groups/{group_1_id}/board/comparisons",
        json={
            "source_id_a": str(source1.id),
            "source_id_b": str(source2.id),
            "relation_type": "refutes",
            "rationale": "Trái phép",
        },
    )
    assert res_comp_abuse.status_code == 403
    assert res_comp_abuse.json()["error"]["code"] == "FORBIDDEN_SCOPE"

    # 5. CANNOT view Group 1's private board -> 403 Forbidden
    res_view_abuse = client.get(f"/api/v1/history/inquiry/groups/{group_1_id}/board")
    assert res_view_abuse.status_code == 403
    assert res_view_abuse.json()["error"]["code"] == "FORBIDDEN_SCOPE"

    # 6. CANNOT view Group 1's revision audit history -> 403 Forbidden
    res_rev_abuse = client.get(f"/api/v1/history/inquiry/groups/{group_1_id}/board/revisions")
    assert res_rev_abuse.status_code == 403
    assert res_rev_abuse.json()["error"]["code"] == "FORBIDDEN_SCOPE"

    # 7. Outsider completely outside classroom also rejected with 403
    _login_user(client, env["outsider"].email)
    res_outsider = client.get(f"/api/v1/history/inquiry/groups/{group_1_id}/board")
    assert res_outsider.status_code == 403
    assert res_outsider.json()["error"]["code"] == "FORBIDDEN_SCOPE"
