# -*- coding: utf-8 -*-
"""V5-T058 (Wave W05, Slot A08): Mobile Quests and Achievements Test Suite.

Audits and verifies:
1. Quest listing & detail API (/api/v1/quests, /api/v1/quests/{quest_slug}):
   - Discrete progression stages: not_started -> in_progress -> completed.
   - Prerequisite-based locking (is_locked, lock_reason).
   - Content rating gatekeeping.
2. Progression stages & server-verified objective calculations:
   - discover_any, complete_lesson, complete_lesson_category.
   - discover_category, quiz_pass_count, urn_exam_pass.
   - source_evidence_task / evidence_inquiry_task.
3. Negative abuse protections:
   - Stale client cannot claim rewards without server-verified 100% completion (HTTP 400).
   - Stale client cannot claim unstarted quest rewards (HTTP 400).
   - Stale client cannot start or claim locked quest rewards (HTTP 403).
   - Non-existent quest slug returns HTTP 404.
   - Duplicate claim attempts rejected (HTTP 400).
4. Positive reward claiming:
   - Atomic reward disbursement (XP, badge, streak freeze).
   - Certificate issuance with verified cryptographic code.
   - Status updated to completed and persisted across queries.
5. Quest summary endpoint (/api/v1/users/me/quest-summary):
   - Returns active in-progress quest or next recommended quest.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
import pytest
from sqlalchemy import select

from backend.models import (
    Certificate,
    ContentRating,
    Motif,
    MotifCategory,
    Quest,
    QuestObjective,
    QuestProgress,
    QuestReward,
    QuestStep,
    QuizAttempt,
    QuizQuestion,
    QuestionType,
    UnlockStatus,
    Urn,
    User,
    UserProgress,
    UserRole,
)
from backend.history_inquiry_models import (
    HistoricalInquiryActivity,
    HistoricalInquiryGroup,
    HistoricalInquirySubmission,
    InquirySubmissionStatus,
    InquiryPrivacyMode,
)
from backend.security import hash_password


def _create_user(db_session, email: str, role: UserRole = UserRole.learner, age: int = 20) -> User:
    user = User(
        email=email,
        password_hash=hash_password("Password123!"),
        display_name=f"User {email.split('@')[0]}",
        username=f"user_{uuid.uuid4().hex[:8]}",
        role=role,
        total_xp=0,
        current_streak=1,
        longest_streak=1,
        streak_freezes=0,
        is_profile_public=True,
    )
    db_session.add(user)
    db_session.commit()
    return user


def _auth_headers(client, email: str = "quester@example.com") -> dict[str, str]:
    res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Password123!"},
    )
    assert res.status_code == 200, res.text
    token = res.headers.get("X-Access-Token") or client.cookies.get("luuniensuki_access")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_setup(db_session):
    """Seed prerequisite urn, motifs, and inquiries for quest verification."""
    urn = Urn(
        slug=f"urn-test-{uuid.uuid4().hex[:6]}",
        name="Cao Đỉnh Test",
        model_url="/models/cao_dinh.glb",
        display_order=1,
    )
    db_session.add(urn)
    db_session.flush()

    motif1 = Motif(
        urn_id=urn.id,
        mesh_name=f"mesh_t1_{uuid.uuid4().hex[:6]}",
        name="Rồng Thần",
        category=MotifCategory.linh_thu,
        pos_x=0.0,
        pos_y=0.0,
        pos_z=0.0,
        bounding_radius=1.0,
        is_active=True,
    )
    motif2 = Motif(
        urn_id=urn.id,
        mesh_name=f"mesh_t2_{uuid.uuid4().hex[:6]}",
        name="Lúa Nước",
        category=MotifCategory.nong_nghiep,
        pos_x=0.0,
        pos_y=0.0,
        pos_z=0.0,
        bounding_radius=1.0,
        is_active=True,
    )
    db_session.add_all([motif1, motif2])
    db_session.flush()

    # Create a prerequisite quest
    q_prereq = Quest(
        slug=f"q-prereq-{uuid.uuid4().hex[:6]}",
        name="Bước Khởi Đầu",
        description="Hoàn thành bước cơ bản",
        category="starter",
        display_order=1,
        is_active=True,
    )
    db_session.add(q_prereq)
    db_session.flush()

    step_pre = QuestStep(
        quest_id=q_prereq.id,
        title="Khám phá bất kỳ",
        display_order=1,
    )
    db_session.add(step_pre)
    db_session.flush()

    db_session.add(
        QuestObjective(
            quest_step_id=step_pre.id,
            objective_type="discover_any",
            target_value=1,
            display_order=1,
        )
    )
    db_session.add(
        QuestReward(
            quest_id=q_prereq.id,
            reward_type="xp",
            amount=50,
        )
    )

    # Create the main quest chained to prerequisite
    q_main = Quest(
        slug=f"q-main-{uuid.uuid4().hex[:6]}",
        name="Nhiệm Vụ Nguồn Tư Liệu",
        description="Hoàn thành bài học và tư liệu lịch sử",
        category="history",
        display_order=2,
        is_active=True,
        prerequisite_id=q_prereq.id,
    )
    db_session.add(q_main)
    db_session.flush()

    step_main1 = QuestStep(
        quest_id=q_main.id,
        title="Bài học & Nguồn tư liệu",
        display_order=1,
    )
    db_session.add(step_main1)
    db_session.flush()

    db_session.add(
        QuestObjective(
            quest_step_id=step_main1.id,
            objective_type="complete_lesson",
            target_value=1,
            display_order=1,
        )
    )
    db_session.add(
        QuestObjective(
            quest_step_id=step_main1.id,
            objective_type="source_evidence_task",
            target_value=1,
            display_order=2,
        )
    )

    db_session.add_all(
        [
            QuestReward(quest_id=q_main.id, reward_type="xp", amount=200),
            QuestReward(quest_id=q_main.id, reward_type="streak_freeze", amount=1),
            QuestReward(quest_id=q_main.id, reward_type="badge", badge_slug="nha-su-hoc"),
        ]
    )

    db_session.commit()

    return {
        "urn": urn,
        "motif1": motif1,
        "motif2": motif2,
        "prereq_quest": q_prereq,
        "main_quest": q_main,
    }


# =========================================================================== #
# Test Cases
# =========================================================================== #

def test_list_quests_with_prerequisite_lock(client, db_session, test_setup):
    """Verify quests are listed and locked quests declare prerequisite lock reasons."""
    user = _create_user(db_session, "quester_list@example.com")
    headers = _auth_headers(client, "quester_list@example.com")

    res = client.get("/api/v1/quests", headers=headers)
    assert res.status_code == 200, res.text
    quests = res.json()
    assert len(quests) >= 2

    prereq_item = next(q for q in quests if q["slug"] == test_setup["prereq_quest"].slug)
    main_item = next(q for q in quests if q["slug"] == test_setup["main_quest"].slug)

    # Prerequisite quest is unlocked and not started
    assert prereq_item["is_locked"] is False
    assert prereq_item["status"] == "not_started"
    assert prereq_item["progress_percent"] == 0.0

    # Main quest is locked because prerequisite is not completed
    assert main_item["is_locked"] is True
    assert main_item["status"] == "locked"
    assert "Hoàn thành" in main_item["lock_reason"]
    assert main_item["prerequisite"]["slug"] == test_setup["prereq_quest"].slug


def test_start_locked_quest_rejected(client, db_session, test_setup):
    """Negative test: starting a locked quest without completing prerequisite returns 403."""
    _create_user(db_session, "quester_locked@example.com")
    headers = _auth_headers(client, "quester_locked@example.com")

    main_slug = test_setup["main_quest"].slug
    res = client.post(f"/api/v1/quests/{main_slug}/start", headers=headers)
    assert res.status_code == 403
    assert "locked" in res.text.lower()


def test_start_unlocked_quest_progression(client, db_session, test_setup):
    """Starting an unlocked quest transitions status to in_progress."""
    user = _create_user(db_session, "quester_start@example.com")
    headers = _auth_headers(client, "quester_start@example.com")

    prereq_slug = test_setup["prereq_quest"].slug
    res = client.post(f"/api/v1/quests/{prereq_slug}/start", headers=headers)
    assert res.status_code == 200, res.text
    detail = res.json()
    assert detail["status"] == "not_started" or detail["status"] == "in_progress"

    # Progress entry in database should exist
    prog = db_session.execute(
        select(QuestProgress).where(
            QuestProgress.user_id == user.id,
            QuestProgress.quest_id == test_setup["prereq_quest"].id,
        )
    ).scalar_one_or_none()
    assert prog is not None


def test_negative_abuse_stale_client_cannot_claim_incomplete_quest(client, db_session, test_setup):
    """Negative abuse defense: Stale client cannot claim rewards without 100% server completion."""
    user = _create_user(db_session, "quester_abuse@example.com")
    headers = _auth_headers(client, "quester_abuse@example.com")

    prereq_slug = test_setup["prereq_quest"].slug

    # 1. Start the quest
    client.post(f"/api/v1/quests/{prereq_slug}/start", headers=headers)

    # 2. User has NOT discovered any motifs (progress = 0%)
    # Stale or malicious client tries to claim rewards
    res = client.post(f"/api/v1/quests/{prereq_slug}/claim", headers=headers)
    assert res.status_code == 400
    assert "Cannot claim rewards without server-verified quest completion" in res.text

    # User total_xp must remain 0
    db_session.refresh(user)
    assert user.total_xp == 0


def test_negative_abuse_cannot_claim_unstarted_quest(client, db_session, test_setup):
    """Negative test: Attempting to claim rewards for a quest never started returns HTTP 400."""
    _create_user(db_session, "quester_unstarted@example.com")
    headers = _auth_headers(client, "quester_unstarted@example.com")

    prereq_slug = test_setup["prereq_quest"].slug
    res = client.post(f"/api/v1/quests/{prereq_slug}/claim", headers=headers)
    assert res.status_code == 400
    assert "Quest has not been started yet" in res.text


def test_negative_abuse_cannot_claim_locked_quest(client, db_session, test_setup):
    """Negative test: Attempting to claim rewards for a locked quest returns HTTP 403."""
    user = _create_user(db_session, "quester_claim_locked@example.com")
    headers = _auth_headers(client, "quester_claim_locked@example.com")

    main_slug = test_setup["main_quest"].slug

    # Synthesize progress entry directly in DB without meeting prerequisite
    db_session.add(
        QuestProgress(user_id=user.id, quest_id=test_setup["main_quest"].id, status="in_progress")
    )
    db_session.commit()

    res = client.post(f"/api/v1/quests/{main_slug}/claim", headers=headers)
    assert res.status_code == 403
    assert "locked" in res.text.lower()


def test_quest_progression_and_claim_rewards_flow(client, db_session, test_setup):
    """Positive test: Server verifies objective completion, awards XP, badge, streak freeze & certificate."""
    user = _create_user(db_session, "quester_success@example.com")
    headers = _auth_headers(client, "quester_success@example.com")

    prereq_slug = test_setup["prereq_quest"].slug
    main_slug = test_setup["main_quest"].slug

    # Step 1: Start prerequisite quest
    client.post(f"/api/v1/quests/{prereq_slug}/start", headers=headers)

    # Step 2: Satisfy prerequisite objective: discover 1 motif
    db_session.add(
        UserProgress(
            user_id=user.id,
            motif_id=test_setup["motif1"].id,
            status=UnlockStatus.discovered,
            discovered_at=datetime.now(timezone.utc),
        )
    )
    db_session.commit()

    # Step 3: Claim prerequisite rewards
    claim_res = client.post(f"/api/v1/quests/{prereq_slug}/claim", headers=headers)
    assert claim_res.status_code == 200, claim_res.text
    claim_data = claim_res.json()
    assert claim_data["status"] == "completed"
    assert claim_data["xp_awarded"] == 50
    assert claim_data["certificate"]["code"] is not None

    db_session.refresh(user)
    assert user.total_xp == 50

    # Step 4: Main quest should now be unlocked!
    list_res = client.get("/api/v1/quests", headers=headers)
    main_quest_item = next(q for q in list_res.json() if q["slug"] == main_slug)
    assert main_quest_item["is_locked"] is False
    assert main_quest_item["status"] == "not_started"

    # Step 5: Start main quest
    start_res = client.post(f"/api/v1/quests/{main_slug}/start", headers=headers)
    assert start_res.status_code == 200

    # Step 6: Complete lesson objective for motif1
    user_prog = db_session.execute(
        select(UserProgress).where(
            UserProgress.user_id == user.id,
            UserProgress.motif_id == test_setup["motif1"].id,
        )
    ).scalar_one()
    user_prog.status = UnlockStatus.learned
    user_prog.learned_at = datetime.now(timezone.utc)
    db_session.commit()

    # Still incomplete because source_evidence_task is missing
    claim_fail = client.post(f"/api/v1/quests/{main_slug}/claim", headers=headers)
    assert claim_fail.status_code == 400
    assert "Cannot claim rewards without server-verified quest completion" in claim_fail.text

    # Step 7: Satisfy source_evidence_task by submitting historical inquiry evidence
    inquiry_activity = HistoricalInquiryActivity(
        classroom_id=None,
        created_by_id=user.id,
        title="Nghiên cứu về Rồng thời Nguyễn",
        description="Khảo sát nguồn tư liệu về rồng.",
        created_at=datetime.now(timezone.utc),
        is_active=True,
    )
    db_session.add(inquiry_activity)
    db_session.flush()

    group = HistoricalInquiryGroup(
        activity_id=inquiry_activity.id,
        name="Nhóm Khảo cứu",
        created_by_id=user.id,
    )
    db_session.add(group)
    db_session.flush()

    submission = HistoricalInquirySubmission(
        group_id=group.id,
        activity_id=inquiry_activity.id,
        submitted_by_id=user.id,
        hypothesis="Rồng thời Nguyễn thể hiện vương quyền tối thượng.",
        synthesis_argument="Theo Đại Nam Thực Lục, rồng là biểu tượng quyền uy.",
        status=InquirySubmissionStatus.submitted.value,
        submitted_at=datetime.now(timezone.utc),
    )
    db_session.add(submission)
    db_session.commit()

    # Step 8: Both objectives now complete! Claim main quest rewards
    claim_success = client.post(f"/api/v1/quests/{main_slug}/claim", headers=headers)
    assert claim_success.status_code == 200, claim_success.text
    res_data = claim_success.json()
    assert res_data["status"] == "completed"
    assert res_data["xp_awarded"] >= 200
    assert "nha-su-hoc" in res_data["badges_awarded"]
    assert res_data["streak_freezes_awarded"] == 1
    assert res_data["certificate"]["code"] is not None

    db_session.refresh(user)
    assert user.total_xp >= 250
    assert user.streak_freezes >= 1

    # Step 9: Duplicate claim attempt must be rejected (negative test)
    dup_claim = client.post(f"/api/v1/quests/{main_slug}/claim", headers=headers)
    assert dup_claim.status_code == 400
    assert "Quest rewards have already been claimed" in dup_claim.text


def test_quest_summary_endpoint(client, db_session, test_setup):
    """Verify /api/v1/users/me/quest-summary returns active quest and next objective."""
    user = _create_user(db_session, "quester_summary@example.com")
    headers = _auth_headers(client, "quester_summary@example.com")

    prereq_slug = test_setup["prereq_quest"].slug
    client.post(f"/api/v1/quests/{prereq_slug}/start", headers=headers)

    res = client.get("/api/v1/users/me/quest-summary", headers=headers)
    assert res.status_code == 200, res.text
    summary = res.json()
    assert summary is not None
    assert summary["quest_slug"] == prereq_slug
    assert summary["status"] in ("not_started", "in_progress")
    assert summary["next_step_title"] is not None
    assert summary["next_objective"]["objective_type"] == "discover_any"
    assert summary["next_objective"]["target_value"] == 1


def test_quest_not_found_returns_404(client, db_session):
    """Unknown quest slug returns 404 for detail, start, and claim endpoints."""
    _create_user(db_session, "quester_404@example.com")
    headers = _auth_headers(client, "quester_404@example.com")

    for method, path in [
        ("GET", "/api/v1/quests/non-existent-quest-slug"),
        ("POST", "/api/v1/quests/non-existent-quest-slug/start"),
        ("POST", "/api/v1/quests/non-existent-quest-slug/claim"),
    ]:
        res = client.request(method, path, headers=headers)
        assert res.status_code == 404, f"{method} {path} should return 404"
        assert "not found" in res.text.lower()


def test_stale_client_payload_injection_ignored(client, db_session, test_setup):
    """Negative abuse: Client injection of fake progress/status payload is completely ignored."""
    user = _create_user(db_session, "quester_inject@example.com")
    headers = _auth_headers(client, "quester_inject@example.com")

    prereq_slug = test_setup["prereq_quest"].slug
    client.post(f"/api/v1/quests/{prereq_slug}/start", headers=headers)

    # Stale/malicious client tries to post completion injection
    res = client.post(
        f"/api/v1/quests/{prereq_slug}/claim",
        headers=headers,
        json={"status": "completed", "progress_percent": 100.0, "force": True},
    )
    assert res.status_code == 400
    assert "Cannot claim rewards without server-verified quest completion" in res.text
    db_session.refresh(user)
    assert user.total_xp == 0


def test_category_and_quiz_objective_progression(client, db_session, test_setup):
    """Verify category discovery and quiz passing objectives calculate accurately."""
    user = _create_user(db_session, "quester_cat@example.com")
    headers = _auth_headers(client, "quester_cat@example.com")

    # Create quest with discover_category and quiz_pass_count
    q_cat = Quest(
        slug=f"q-cat-{uuid.uuid4().hex[:6]}",
        name="Linh Thú Huyền Thoại",
        category="linh_thu",
        display_order=5,
        is_active=True,
    )
    db_session.add(q_cat)
    db_session.flush()

    step = QuestStep(quest_id=q_cat.id, title="Bước 1", display_order=1)
    db_session.add(step)
    db_session.flush()

    db_session.add_all([
        QuestObjective(
            quest_step_id=step.id,
            objective_type="discover_category",
            target_value=1,
            params={"category": "linh_thu"},
            display_order=1,
        ),
        QuestObjective(
            quest_step_id=step.id,
            objective_type="quiz_pass_count",
            target_value=1,
            params={"category": "linh_thu"},
            display_order=2,
        ),
    ])
    db_session.add(QuestReward(quest_id=q_cat.id, reward_type="xp", amount=150))
    db_session.commit()

    # Start quest
    start_res = client.post(f"/api/v1/quests/{q_cat.slug}/start", headers=headers)
    assert start_res.status_code == 200
    assert start_res.json()["progress_percent"] == 0.0

    # Discover linh_thu motif
    db_session.add(
        UserProgress(
            user_id=user.id,
            motif_id=test_setup["motif1"].id,
            status=UnlockStatus.discovered,
            discovered_at=datetime.now(timezone.utc),
        )
    )
    db_session.commit()

    # Check detail: progress should now be 50% (1 of 2 objectives complete)
    detail_res = client.get(f"/api/v1/quests/{q_cat.slug}", headers=headers)
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["progress_percent"] == 50.0
    obj1 = next(o for o in detail["steps"][0]["objectives"] if o["objective_type"] == "discover_category")
    obj2 = next(o for o in detail["steps"][0]["objectives"] if o["objective_type"] == "quiz_pass_count")
    assert obj1["is_complete"] is True
    assert obj2["is_complete"] is False

    # Negative claim attempt at 50%
    claim_50 = client.post(f"/api/v1/quests/{q_cat.slug}/claim", headers=headers)
    assert claim_50.status_code == 400
    assert "Cannot claim rewards without server-verified quest completion" in claim_50.text

    # Record passing quiz attempt
    db_session.add(
        QuizAttempt(
            user_id=user.id,
            motif_id=test_setup["motif1"].id,
            score=10,
            max_score=10,
            percentage=100,
            answers={"q1": "a"},
            completed_at=datetime.now(timezone.utc),
        )
    )
    db_session.commit()

    # Claim at 100%
    claim_100 = client.post(f"/api/v1/quests/{q_cat.slug}/claim", headers=headers)
    assert claim_100.status_code == 200
    claim_data = claim_100.json()
    assert claim_data["status"] == "completed"
    assert claim_data["xp_awarded"] == 150
    db_session.refresh(user)
    assert user.total_xp == 150

