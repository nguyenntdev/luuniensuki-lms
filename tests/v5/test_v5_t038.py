# -*- coding: utf-8 -*-
"""V5-T038 (Wave W03, Slot A08): Peer / group historical inquiry.

Audits and verifies:
1. Historical inquiry activity creation & classroom association:
   - Classroom teachers / staff can create inquiry activities with guiding questions and suggested sources.
   - Non-teachers cannot create activities for another teacher's class.
2. Group formation with enrolled peers:
   - Students enrolled in the classroom can form inquiry groups.
   - Creator is assigned leader role, peers assigned contributor role.
   - Non-enrolled students cannot be added to class-scoped groups.
3. Collaborative source evidence synthesis & member attribution:
   - Group members collaboratively assemble primary source citations (HistoricalSource & HistoricalClaim).
   - Each evidence item tracks contributor attribution (contributed_by_user_id, name, timestamp).
   - Hypothesis and synthesis argument updates maintain optimistic concurrency (versioning).
4. Epistemic rigor validation:
   - Rejects claiming 'su_lieu_xac_thuc' without backing primary source citations (422).
   - Rejects fake or nonexistent source IDs (404).
5. Strict negative abuse guardrails:
   - Group member from another group CANNOT alter another group's collaborative submission (403).
   - Group member from another group CANNOT add evidence to another group (403).
   - Group member from another group CANNOT remove evidence from another group (403).
   - Group member from another group CANNOT submit another group's inquiry (403).
6. Privacy isolation:
   - Peer group drafts in 'private_group' mode are strictly hidden from peers of other groups (403).
   - Classroom teacher and group members retain full access.
7. Teacher moderation & feedback workflow:
   - Students cannot self-moderate or grade submissions (403).
   - Classroom teacher can review, provide feedback, assign rubric scores, and approve or request revisions.
   - Revision request unlocks the submission for subsequent student revisions and re-submission.
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
    """Seed primary source and claim for inquiry tests."""
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
    db_session.add_all([source1, source2])
    db_session.flush()

    entity = HistoricalEntity(
        entity_type="urn",
        slug=f"cao-dinh-{uuid.uuid4().hex[:6]}",
        name_vi="Cao Đỉnh",
        publication_status="published",
    )
    db_session.add(entity)
    db_session.flush()

    claim = HistoricalClaim(
        entity_id=entity.id,
        claim_key=f"claim_{uuid.uuid4().hex[:8]}",
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
    db_session.refresh(claim)
    return source1, source2, claim


def _setup_classroom_env(db_session):
    """Create a classroom with a teacher, two groups of students, and one outsider."""
    teacher = _create_user(db_session, f"teacher_{uuid.uuid4().hex[:6]}@school.edu.vn", role=UserRole.teacher, display_name="Thầy Giáo Sử")
    other_teacher = _create_user(db_session, f"teacher_other_{uuid.uuid4().hex[:6]}@school.edu.vn", role=UserRole.teacher, display_name="Cô Giáo Khác")
    student_a1 = _create_user(db_session, f"student_a1_{uuid.uuid4().hex[:6]}@school.edu.vn", display_name="Học sinh A1 (Nhóm Alpha)")
    student_a2 = _create_user(db_session, f"student_a2_{uuid.uuid4().hex[:6]}@school.edu.vn", display_name="Học sinh A2 (Nhóm Alpha)")
    student_b1 = _create_user(db_session, f"student_b1_{uuid.uuid4().hex[:6]}@school.edu.vn", display_name="Học sinh B1 (Nhóm Beta)")
    outsider = _create_user(db_session, f"outsider_{uuid.uuid4().hex[:6]}@other.edu.vn", display_name="Học sinh Ngoài Lớp")

    classroom = Classroom(
        name="Lớp Sử 11A1 — Chuyên đề Cửu Đỉnh",
        teacher_id=teacher.id,
        class_code=f"CD{uuid.uuid4().hex[:4].upper()}",
        is_archived=False,
    )
    db_session.add(classroom)
    db_session.commit()
    db_session.refresh(classroom)

    # Enroll students in classroom
    for user in [student_a1, student_a2, student_b1]:
        cm = ClassMember(class_id=classroom.id, user_id=user.id, role="learner")
        db_session.add(cm)
    db_session.commit()

    return {
        "teacher": teacher,
        "other_teacher": other_teacher,
        "student_a1": student_a1,
        "student_a2": student_a2,
        "student_b1": student_b1,
        "outsider": outsider,
        "classroom": classroom,
    }


# =========================================================================== #
# Test 1: Historical Inquiry Activity Creation & Scoping
# =========================================================================== #
def test_inquiry_activity_creation_and_listing(client, db_session):
    env = _setup_classroom_env(db_session)
    source1, _, claim = _seed_sources_and_claims(db_session)

    # 1. Other teacher attempting to create activity for env['classroom'] receives 403
    _login_user(client, env["other_teacher"].email)
    res_forbidden = client.post(
        "/api/v1/history/inquiry/activities",
        json={
            "classroom_id": str(env["classroom"].id),
            "title": "Khảo cứu niên đại đúc Cao Đỉnh trái phép",
            "description": "Nghiên cứu văn bản Đại Nam Thực Lục",
        },
    )
    assert res_forbidden.status_code == 403
    assert res_forbidden.json()["error"]["code"] == "FORBIDDEN_SCOPE"

    # 2. Legitimate teacher creates inquiry activity
    _login_user(client, env["teacher"].email)
    res_ok = client.post(
        "/api/v1/history/inquiry/activities",
        json={
            "classroom_id": str(env["classroom"].id),
            "title": "Khảo cứu niên đại và biểu tượng rồng trên Cao Đỉnh",
            "description": "Dựa vào Đại Nam Thực Lục Chính Biên để phân tích bối cảnh và kỹ thuật đúc đồng Cửu Đỉnh.",
            "guiding_questions": [
                "Niên đại khởi công và hoàn thành Cao Đỉnh được ghi chép thế nào?",
                "Hình tượng rồng mây trên Cao Đỉnh mang ý nghĩa vương quyền gì?",
            ],
            "suggested_source_ids": [str(source1.id)],
            "suggested_claim_ids": [str(claim.id)],
            "rubric_criteria": {
                "source_evidence": 30,
                "critical_analysis": 30,
                "epistemic_rigor": 20,
                "collaboration": 20,
            },
        },
    )
    assert res_ok.status_code == 201
    activity_data = res_ok.json()
    assert activity_data["title"] == "Khảo cứu niên đại và biểu tượng rồng trên Cao Đỉnh"
    assert len(activity_data["guiding_questions"]) == 2
    assert str(source1.id) in [str(s) for s in activity_data["suggested_source_ids"]]

    # 3. List activities
    res_list = client.get(f"/api/v1/history/inquiry/activities?classroom_id={env['classroom'].id}")
    assert res_list.status_code == 200
    items = res_list.json()
    assert any(a["id"] == activity_data["id"] for a in items)


# =========================================================================== #
# Test 2: Group Formation & Membership Controls
# =========================================================================== #
def test_group_formation_with_enrolled_peers(client, db_session):
    env = _setup_classroom_env(db_session)
    source1, _, claim = _seed_sources_and_claims(db_session)

    _login_user(client, env["teacher"].email)
    res_act = client.post(
        "/api/v1/history/inquiry/activities",
        json={
            "classroom_id": str(env["classroom"].id),
            "title": "Chuyên đề khảo sát Thực Lục",
            "description": "Nghiên cứu nhóm tương tác",
            "suggested_source_ids": [str(source1.id)],
        },
    )
    activity_id = res_act.json()["id"]

    # Student A1 forms Group Alpha with student A2
    _login_user(client, env["student_a1"].email)
    res_grp = client.post(
        f"/api/v1/history/inquiry/activities/{activity_id}/groups",
        json={
            "name": "Nhóm Alpha — Nghiên Cứu Cao Đỉnh",
            "member_ids": [str(env["student_a2"].id)],
        },
    )
    assert res_grp.status_code == 201
    grp_data = res_grp.json()
    assert grp_data["name"] == "Nhóm Alpha — Nghiên Cứu Cao Đỉnh"
    members = grp_data["members"]
    assert len(members) == 2
    roles = {m["user_id"]: m["role"] for m in members}
    assert roles[str(env["student_a1"].id)] == "leader"
    assert roles[str(env["student_a2"].id)] == "contributor"

    # Outsider student cannot create group in this classroom
    _login_user(client, env["outsider"].email)
    res_outsider = client.post(
        f"/api/v1/history/inquiry/activities/{activity_id}/groups",
        json={"name": "Nhóm Kẻ Đột Nhập"},
    )
    assert res_outsider.status_code == 403
    assert res_outsider.json()["error"]["code"] == "FORBIDDEN_SCOPE"


# =========================================================================== #
# Test 3: Collaborative Source Evidence Synthesis & Contributor Attribution
# =========================================================================== #
def test_collaborative_source_evidence_synthesis(client, db_session):
    env = _setup_classroom_env(db_session)
    source1, source2, claim = _seed_sources_and_claims(db_session)

    # Teacher creates activity
    _login_user(client, env["teacher"].email)
    res_act = client.post(
        "/api/v1/history/inquiry/activities",
        json={
            "classroom_id": str(env["classroom"].id),
            "title": "Đối chiếu sử liệu Cửu Đỉnh",
            "description": "Phân tích nguồn tư liệu",
        },
    )
    activity_id = res_act.json()["id"]

    # Student A1 creates Group Alpha with student A2
    _login_user(client, env["student_a1"].email)
    res_grp = client.post(
        f"/api/v1/history/inquiry/activities/{activity_id}/groups",
        json={"name": "Nhóm Alpha", "member_ids": [str(env["student_a2"].id)]},
    )
    group_id = res_grp.json()["id"]

    # Student A1 contributes first primary source evidence citation
    res_ev1 = client.post(
        f"/api/v1/history/inquiry/groups/{group_id}/evidence",
        json={
            "source_id": str(source1.id),
            "locator": "Đệ nhị kỷ, quyển 154, tờ 12a",
            "excerpt": "Tháng 10 năm Ất Mùi, đúc chín đỉnh... khắc rồng mây tại Cao Đỉnh.",
            "claim_id": str(claim.id),
            "support_type": "supports",
            "interpretation_note": "Tư liệu thực lục khẳng định thời điểm đúc Cao Đỉnh và vị trí quẻ Càn tượng trưng cho vua Gia Long.",
        },
    )
    assert res_ev1.status_code == 201
    ev1 = res_ev1.json()
    assert ev1["source_title"] == "Đại Nam Thực Lục Chính Biên"
    assert ev1["contributed_by_user_id"] == str(env["student_a1"].id)
    assert "Học sinh A1" in ev1["contributed_by_name"]

    # Student A2 contributes second evidence citation
    _login_user(client, env["student_a2"].email)
    res_ev2 = client.post(
        f"/api/v1/history/inquiry/groups/{group_id}/evidence",
        json={
            "source_id": str(source2.id),
            "locator": "Quyển 214, mục Đúc tượng vạc",
            "excerpt": "Quy định kích thước, trọng lượng đồng và thợ đúc xưởng Bác Tế.",
            "support_type": "contextualizes",
            "interpretation_note": "Khâm Định Đại Nam Hội Điển Sự Lệ cung cấp định mức vật liệu đồng và thiếc cho thợ đúc.",
        },
    )
    assert res_ev2.status_code == 201
    ev2 = res_ev2.json()
    assert ev2["contributed_by_user_id"] == str(env["student_a2"].id)
    assert "Học sinh A2" in ev2["contributed_by_name"]

    # Student A1 synthesizes the collaborative hypothesis and argument
    _login_user(client, env["student_a1"].email)
    res_update = client.put(
        f"/api/v1/history/inquiry/groups/{group_id}/submission",
        json={
            "hypothesis": "Cao Đỉnh giữ vị trí trung tâm trong hệ thống Cửu Đỉnh vì mang biểu tượng của vua sáng lập triều đại (Thế Tổ Cao Hoàng đế).",
            "synthesis_argument": "Tổng hợp từ Thực Lục quyển 154 và Hội Điển quyển 214 cho thấy Cao Đỉnh được ưu tiên chế tác lớn nhất, hoàn thành trước tiên và chạm khắc rồng mây độc quyền.",
            "epistemic_rating": "su_lieu_xac_thuc",
            "privacy_mode": "private_group",
        },
    )
    assert res_update.status_code == 200
    sub_data = res_update.json()
    assert len(sub_data["evidence_items"]) == 2
    assert sub_data["epistemic_rating"] == "su_lieu_xac_thuc"
    assert sub_data["version"] >= 3  # Initial + ev1 + ev2 + update


# =========================================================================== #
# Test 4: Negative Abuse — Epistemic Rigor & Fake Source Protection
# =========================================================================== #
def test_negative_abuse_epistemic_rigor_enforced(client, db_session):
    env = _setup_classroom_env(db_session)

    _login_user(client, env["teacher"].email)
    res_act = client.post(
        "/api/v1/history/inquiry/activities",
        json={"classroom_id": str(env["classroom"].id), "title": "Hoạt động thử nghiệm", "description": "Kiểm tra kiểm duyệt"},
    )
    activity_id = res_act.json()["id"]

    _login_user(client, env["student_a1"].email)
    res_grp = client.post(
        f"/api/v1/history/inquiry/activities/{activity_id}/groups",
        json={"name": "Nhóm Gian Lận Không Dẫn Chứng"},
    )
    group_id = res_grp.json()["id"]

    # Attempting to declare 'su_lieu_xac_thuc' (verified fact) with ZERO evidence items MUST fail
    res_fail = client.put(
        f"/api/v1/history/inquiry/groups/{group_id}/submission",
        json={
            "hypothesis": "Tự nhận định không cần bằng chứng",
            "synthesis_argument": "Không có bằng chứng nào",
            "epistemic_rating": "su_lieu_xac_thuc",
        },
    )
    assert res_fail.status_code == 422
    assert res_fail.json()["error"]["code"] == "INSUFFICIENT_EVIDENCE"

    # Attempting to add a fake / non-existent source_id MUST fail with 404
    fake_source_id = str(uuid.uuid4())
    res_fake_source = client.post(
        f"/api/v1/history/inquiry/groups/{group_id}/evidence",
        json={
            "source_id": fake_source_id,
            "locator": "Tờ bịa đặt",
            "excerpt": "Trích dẫn giả",
            "interpretation_note": "Ghi chú phân tích",
        },
    )
    assert res_fake_source.status_code == 404
    assert res_fake_source.json()["error"]["code"] == "SOURCE_NOT_FOUND"


# =========================================================================== #
# Test 5: STRICT NEGATIVE ABUSE — Cross-Group Alteration Blocked
# =========================================================================== #
def test_negative_abuse_cross_group_alteration_forbidden(client, db_session):
    """MANDATORY TICKET INVARIANT:
    Group member cannot alter another group's collaborative inquiry submission.
    """
    env = _setup_classroom_env(db_session)
    source1, _, _ = _seed_sources_and_claims(db_session)

    _login_user(client, env["teacher"].email)
    res_act = client.post(
        "/api/v1/history/inquiry/activities",
        json={"classroom_id": str(env["classroom"].id), "title": "Hoạt động nhóm đôi", "description": "Đề tài nhóm"},
    )
    activity_id = res_act.json()["id"]

    # Student A1 creates Group Alpha
    _login_user(client, env["student_a1"].email)
    res_alpha = client.post(
        f"/api/v1/history/inquiry/activities/{activity_id}/groups",
        json={"name": "Nhóm Alpha"},
    )
    group_alpha_id = res_alpha.json()["id"]

    # Add initial evidence to Group Alpha
    res_ev = client.post(
        f"/api/v1/history/inquiry/groups/{group_alpha_id}/evidence",
        json={
            "source_id": str(source1.id),
            "locator": "Quyển 154",
            "excerpt": "Trích dẫn ban đầu của nhóm Alpha",
            "interpretation_note": "Phân tích của nhóm Alpha",
        },
    )
    assert res_ev.status_code == 201
    evidence_id = res_ev.json()["id"]

    # Student B1 creates Group Beta
    _login_user(client, env["student_b1"].email)
    res_beta = client.post(
        f"/api/v1/history/inquiry/activities/{activity_id}/groups",
        json={"name": "Nhóm Beta"},
    )
    assert res_beta.status_code == 201

    # NEGATIVE ATTACK 1: Student B1 tries to alter Group Alpha's collaborative text
    res_attack_update = client.put(
        f"/api/v1/history/inquiry/groups/{group_alpha_id}/submission",
        json={
            "hypothesis": "HACKED: Giả thuyết bị sửa bởi Nhóm Beta",
            "synthesis_argument": "HACKED: Luận điểm bị sửa trộm",
        },
    )
    assert res_attack_update.status_code == 403
    assert res_attack_update.json()["error"]["code"] == "FORBIDDEN_SCOPE"

    # NEGATIVE ATTACK 2: Student B1 tries to inject evidence into Group Alpha
    res_attack_evidence = client.post(
        f"/api/v1/history/inquiry/groups/{group_alpha_id}/evidence",
        json={
            "source_id": str(source1.id),
            "locator": "HACKED",
            "excerpt": "HACKED evidence injection",
            "interpretation_note": "Injected by rival group",
        },
    )
    assert res_attack_evidence.status_code == 403
    assert res_attack_evidence.json()["error"]["code"] == "FORBIDDEN_SCOPE"

    # NEGATIVE ATTACK 3: Student B1 tries to delete evidence from Group Alpha
    res_attack_delete = client.delete(
        f"/api/v1/history/inquiry/groups/{group_alpha_id}/evidence/{evidence_id}"
    )
    assert res_attack_delete.status_code == 403
    assert res_attack_delete.json()["error"]["code"] == "FORBIDDEN_SCOPE"

    # NEGATIVE ATTACK 4: Student B1 tries to submit Group Alpha's inquiry prematurely
    res_attack_submit = client.post(
        f"/api/v1/history/inquiry/groups/{group_alpha_id}/submit"
    )
    assert res_attack_submit.status_code == 403
    assert res_attack_submit.json()["error"]["code"] == "FORBIDDEN_SCOPE"


# =========================================================================== #
# Test 6: Privacy Isolation Between Peer Groups
# =========================================================================== #
def test_privacy_isolation_between_peer_groups(client, db_session):
    env = _setup_classroom_env(db_session)
    source1, _, _ = _seed_sources_and_claims(db_session)

    _login_user(client, env["teacher"].email)
    res_act = client.post(
        "/api/v1/history/inquiry/activities",
        json={"classroom_id": str(env["classroom"].id), "title": "Bảo mật nhóm", "description": "Kiểm tra quyền riêng tư"},
    )
    activity_id = res_act.json()["id"]

    # Student A1 creates Group Alpha (draft, private_group)
    _login_user(client, env["student_a1"].email)
    res_alpha = client.post(
        f"/api/v1/history/inquiry/activities/{activity_id}/groups",
        json={"name": "Nhóm Alpha Bảo Mật"},
    )
    group_alpha_id = res_alpha.json()["id"]

    # Student B1 from Group Beta tries to read Group Alpha's draft submission
    _login_user(client, env["student_b1"].email)
    res_peek = client.get(f"/api/v1/history/inquiry/groups/{group_alpha_id}/submission")
    assert res_peek.status_code == 403
    assert res_peek.json()["error"]["code"] == "FORBIDDEN_SCOPE"

    # Legitimate member Student A1 can read their submission
    _login_user(client, env["student_a1"].email)
    res_member = client.get(f"/api/v1/history/inquiry/groups/{group_alpha_id}/submission")
    assert res_member.status_code == 200
    assert res_member.json()["status"] == "draft"

    # Teacher of the class can also read the submission
    _login_user(client, env["teacher"].email)
    res_teacher = client.get(f"/api/v1/history/inquiry/groups/{group_alpha_id}/submission")
    assert res_teacher.status_code == 200


# =========================================================================== #
# Test 7: Submission Locking & Teacher Moderation Lifecycle
# =========================================================================== #
def test_teacher_moderation_and_revision_cycle(client, db_session):
    env = _setup_classroom_env(db_session)
    source1, source2, claim = _seed_sources_and_claims(db_session)

    # Teacher creates activity
    _login_user(client, env["teacher"].email)
    res_act = client.post(
        "/api/v1/history/inquiry/activities",
        json={"classroom_id": str(env["classroom"].id), "title": "Vòng đời nộp bài", "description": "Kiểm tra nộp và chấm điểm"},
    )
    activity_id = res_act.json()["id"]

    # Student A1 creates group, contributes evidence and fills hypothesis
    _login_user(client, env["student_a1"].email)
    res_grp = client.post(
        f"/api/v1/history/inquiry/activities/{activity_id}/groups",
        json={"name": "Nhóm Nghiên Cứu Alpha"},
    )
    group_id = res_grp.json()["id"]

    client.post(
        f"/api/v1/history/inquiry/groups/{group_id}/evidence",
        json={
            "source_id": str(source1.id),
            "locator": "Tờ 12a",
            "excerpt": "Đúc chín đỉnh",
            "claim_id": str(claim.id),
            "interpretation_note": "Ghi chú sơ khởi",
        },
    )

    client.put(
        f"/api/v1/history/inquiry/groups/{group_id}/submission",
        json={
            "hypothesis": "Cao Đỉnh là đỉnh lớn nhất",
            "synthesis_argument": "Dựa vào Thực Lục",
            "epistemic_rating": "su_lieu_xac_thuc",
        },
    )

    # Student submits inquiry
    res_submit = client.post(f"/api/v1/history/inquiry/groups/{group_id}/submit")
    assert res_submit.status_code == 200
    sub_data = res_submit.json()
    assert sub_data["status"] == "submitted"
    submission_id = sub_data["id"]

    # NEGATIVE ABUSE: Editing while 'submitted' is locked
    res_locked_edit = client.put(
        f"/api/v1/history/inquiry/groups/{group_id}/submission",
        json={"hypothesis": "Thay đổi sau khi nộp"},
    )
    assert res_locked_edit.status_code == 400
    assert res_locked_edit.json()["error"]["code"] == "SUBMISSION_LOCKED"

    # NEGATIVE ABUSE: Student cannot self-moderate or grade
    res_student_mod = client.post(
        f"/api/v1/history/inquiry/submissions/{submission_id}/moderate",
        json={
            "status": "approved",
            "teacher_feedback": "Tự chấm điểm 100",
            "score": 100.0,
        },
    )
    assert res_student_mod.status_code == 403
    assert res_student_mod.json()["error"]["code"] == "FORBIDDEN_SCOPE"

    # Teacher reviews and requests revision
    _login_user(client, env["teacher"].email)
    res_request_rev = client.post(
        f"/api/v1/history/inquiry/submissions/{submission_id}/moderate",
        json={
            "status": "revision_requested",
            "teacher_feedback": "Cần bổ sung trích dẫn từ Khâm Định Đại Nam Hội Điển Sự Lệ để làm rõ tỷ lệ đồng và thiếc.",
            "score": 75.0,
            "rubric_evaluation": {"source_evidence": 20, "critical_analysis": 25, "epistemic_rigor": 15, "collaboration": 15},
        },
    )
    assert res_request_rev.status_code == 200
    mod_out = res_request_rev.json()
    assert mod_out["status"] == "revision_requested"
    assert mod_out["score"] == 75.0
    assert "Khâm Định Đại Nam Hội Điển Sự Lệ" in mod_out["teacher_feedback"]

    # Revision request unlocks editing for students
    _login_user(client, env["student_a1"].email)
    res_add_rev_evidence = client.post(
        f"/api/v1/history/inquiry/groups/{group_id}/evidence",
        json={
            "source_id": str(source2.id),
            "locator": "Quyển 214",
            "excerpt": "Tỷ lệ đồng đỏ và chì kẽm trong hợp kim đúc Đỉnh.",
            "interpretation_note": "Bổ sung theo yêu cầu của Thầy Giáo Sử.",
        },
    )
    assert res_add_rev_evidence.status_code == 201

    # Re-submit after revision
    res_resubmit = client.post(f"/api/v1/history/inquiry/groups/{group_id}/submit")
    assert res_resubmit.status_code == 200
    assert res_resubmit.json()["status"] == "submitted"

    # Teacher approves final submission with excellent score
    _login_user(client, env["teacher"].email)
    res_final_approve = client.post(
        f"/api/v1/history/inquiry/submissions/{submission_id}/moderate",
        json={
            "status": "approved",
            "teacher_feedback": "Bài tổng hợp xuất sắc, đối chiếu nguồn tư liệu hoàn hảo.",
            "score": 98.0,
            "rubric_evaluation": {"source_evidence": 30, "critical_analysis": 30, "epistemic_rigor": 20, "collaboration": 18},
        },
    )
    assert res_final_approve.status_code == 200
    assert res_final_approve.json()["status"] == "approved"
    assert res_final_approve.json()["score"] == 98.0


# =========================================================================== #
# Test 8: Member Addition & Evidence Deletion Workflow
# =========================================================================== #
def test_member_addition_and_evidence_deletion(client, db_session):
    env = _setup_classroom_env(db_session)
    source1, _, _ = _seed_sources_and_claims(db_session)

    _login_user(client, env["teacher"].email)
    res_act = client.post(
        "/api/v1/history/inquiry/activities",
        json={"classroom_id": str(env["classroom"].id), "title": "Hoạt động bổ sung thành viên", "description": "Kiểm tra thêm xóa"},
    )
    activity_id = res_act.json()["id"]

    # Student A1 creates group alone
    _login_user(client, env["student_a1"].email)
    res_grp = client.post(
        f"/api/v1/history/inquiry/activities/{activity_id}/groups",
        json={"name": "Nhóm Đơn Thân"},
    )
    group_id = res_grp.json()["id"]

    # Add student A2 as contributor
    res_add_mem = client.post(
        f"/api/v1/history/inquiry/groups/{group_id}/members",
        json={"user_id": str(env["student_a2"].id), "role": "contributor"},
    )
    assert res_add_mem.status_code == 201
    assert res_add_mem.json()["user_id"] == str(env["student_a2"].id)

    # Add evidence
    res_ev = client.post(
        f"/api/v1/history/inquiry/groups/{group_id}/evidence",
        json={
            "source_id": str(source1.id),
            "locator": "Tờ 15b",
            "excerpt": "Bằng chứng tạm",
            "interpretation_note": "Ghi chú sẽ xóa",
        },
    )
    assert res_ev.status_code == 201
    evidence_id = res_ev.json()["id"]

    # Delete evidence
    res_del = client.delete(f"/api/v1/history/inquiry/groups/{group_id}/evidence/{evidence_id}")
    assert res_del.status_code == 200
    assert len(res_del.json()["evidence_items"]) == 0


# =========================================================================== #
# Test 9: Class-Visible Published Synthesis Read-Only for Class Peers
# =========================================================================== #
def test_class_visible_submission_read_only_for_peers(client, db_session):
    env = _setup_classroom_env(db_session)
    source1, _, claim = _seed_sources_and_claims(db_session)

    _login_user(client, env["teacher"].email)
    res_act = client.post(
        "/api/v1/history/inquiry/activities",
        json={"classroom_id": str(env["classroom"].id), "title": "Công bố kết quả lớp", "description": "Chia sẻ với cả lớp"},
    )
    activity_id = res_act.json()["id"]

    # Student A1 creates group and sets privacy_mode to class_visible
    _login_user(client, env["student_a1"].email)
    res_grp = client.post(
        f"/api/v1/history/inquiry/activities/{activity_id}/groups",
        json={"name": "Nhóm Tiên Phong"},
    )
    group_id = res_grp.json()["id"]

    client.post(
        f"/api/v1/history/inquiry/groups/{group_id}/evidence",
        json={
            "source_id": str(source1.id),
            "locator": "Tờ 12",
            "excerpt": "Trích yếu",
            "claim_id": str(claim.id),
            "interpretation_note": "Ghi chú công khai",
        },
    )

    client.put(
        f"/api/v1/history/inquiry/groups/{group_id}/submission",
        json={
            "hypothesis": "Giả thuyết công khai",
            "synthesis_argument": "Luận điểm hoàn thiện",
            "epistemic_rating": "su_lieu_xac_thuc",
            "privacy_mode": "class_visible",
        },
    )

    # Submit inquiry
    res_sub = client.post(f"/api/v1/history/inquiry/groups/{group_id}/submit")
    submission_id = res_sub.json()["id"]

    # Teacher approves
    _login_user(client, env["teacher"].email)
    client.post(
        f"/api/v1/history/inquiry/submissions/{submission_id}/moderate",
        json={"status": "approved", "teacher_feedback": "Đồng ý công khai cho cả lớp học hỏi.", "score": 96.0},
    )

    # Peer student B1 can now READ the approved submission
    _login_user(client, env["student_b1"].email)
    res_peer_read = client.get(f"/api/v1/history/inquiry/groups/{group_id}/submission")
    assert res_peer_read.status_code == 200
    assert res_peer_read.json()["hypothesis"] == "Giả thuyết công khai"

    # BUT peer student B1 still CANNOT alter the submission!
    res_peer_edit = client.put(
        f"/api/v1/history/inquiry/groups/{group_id}/submission",
        json={"hypothesis": "Thay đổi của người ngoài"},
    )
    assert res_peer_edit.status_code == 403
    assert res_peer_edit.json()["error"]["code"] == "FORBIDDEN_SCOPE"

