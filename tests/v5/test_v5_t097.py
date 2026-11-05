# -*- coding: utf-8 -*-
"""V5-T097 (Wave W09, Slot A07): Adaptive Evidence Practice in FSRS and Quests Test Suite.

Verifies:
1. Spaced Repetition (FSRS) scheduling applied to scored primary source evaluation tasks:
   - Due evidence task retrieval and dynamic card provisioning.
   - DSR (Difficulty-Stability-Retrievability) formula state transitions.
2. Algorithmic transparency:
   - Detailed mathematical breakdown in evaluation responses (prior/new stability, difficulty, retrievability).
   - Global model transparency endpoint exposing 21-parameter vector and forgetting curve formulas.
3. User opt-out controls:
   - Toggling adaptive FSRS on/off via settings.
   - When opted out, reviews bypass adaptive drift and use fixed linear scheduling.
   - Optimal retention customization (0.70 to 0.97).
4. Gamification XP kept strictly distinct from memory stability:
   - Standard XP earned does not inflate memory half-life stability.
   - Active XP boosters or client-claimed XP have zero effect on stability equations.
5. Negative abuse defense - rapid clicking / dwell time violation:
   - Evaluation submissions with dwell time < 2.0s are flagged as RAPID_CLICK_DWELL_VIOLATION.
   - Mastery badges are strictly withheld and denied.
   - Memory recall stability is not inflated.
6. Negative abuse defense - brute-force burst guessing:
   - Rapid burst attempts (< 3.0s apart) are flagged as BRUTE_FORCE_BURST_ATTEMPTS.
   - Recall stability is penalized/reset rather than inflated.
7. Server-authoritative quest integration:
   - Quests requiring adaptive evidence practice strictly count genuine, non-abusive evaluations.
   - Abusive rapid clicking attempts yield 0 quest progress and block reward claiming with HTTP 400.
   - Valid completion advances quest to 100% and unlocks atomic rewards.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
import pytest
from sqlalchemy import select

from backend.models import (
    AdaptiveEvidenceCard,
    AdaptiveEvidenceLog,
    ContentRating,
    Motif,
    MotifCategory,
    Quest,
    QuestObjective,
    QuestProgress,
    QuestReward,
    QuestStep,
    Urn,
    User,
    UserFsrsParams,
    UserRole,
    HistoricalClaim,
    HistoricalSource,
)
from backend.security import hash_password


def _create_user(db_session, email: str, role: UserRole = UserRole.learner) -> User:
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


def _auth_headers(client, email: str) -> dict[str, str]:
    res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Password123!"},
    )
    assert res.status_code == 200, res.text
    token = res.headers.get("X-Access-Token") or client.cookies.get("luuniensuki_access")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def evidence_seed(db_session):
    """Seed authentic primary historical source and claim for evaluation."""
    source = HistoricalSource(
        id=uuid.uuid4(),
        source_type="primary_chronicle",
        title="Đại Nam Thực Lục Chính Biên - Quyển CLXVIII",
        author_text="Quốc Sử Quán Triều Nguyễn",
        publisher="Nội Các Huế",
        publication_year=1835,
        citation_text="ĐNTL, Chính biên, Đệ nhị kỷ, Quyển CLXVIII, tờ 12a",
        excerpt="Minh Mạng năm thứ 16 (1835), mùa đông tháng 12, đúc chín đỉnh lớn đặt trước sân Thế Miếu. Trên mỗi đỉnh khắc các hình tượng danh sơn đại xuyên của đất nước...",
        verification_status="metadata_verified",
        content_scope="NINE_URNS",
        checksum="sha256:abc123canonicalevidencechecksum456789",
    )
    db_session.add(source)
    db_session.commit()
    return source


def test_fsrs_due_evidence_tasks_retrieval_and_provisioning(client, db_session, evidence_seed):
    """Verifies learners receive due primary source evaluation items with authentic provenance."""
    source = evidence_seed
    user = _create_user(db_session, f"learner_due_{uuid.uuid4().hex[:6]}@example.com")
    headers = _auth_headers(client, user.email)

    res = client.get("/api/v1/fsrs/evidence/due", headers=headers)
    assert res.status_code == 200, res.text
    data = res.json()
    assert "tasks" in data
    assert data["total_due"] >= 1

    first_task = data["tasks"][0]
    assert first_task["source_id"] == str(source.id)
    assert "Đại Nam Thực Lục" in first_task["source_title"]
    assert first_task["citation_text"] is not None
    assert first_task["excerpt"] is not None
    assert first_task["fsrs_state"] == "new"
    assert first_task["fsrs_difficulty"] == 5.0
    assert first_task["retrievability"] == 1.0
    assert first_task["is_mastered"] is False


def test_fsrs_scored_evaluation_adaptive_scheduling_and_transparency(
    client, db_session, evidence_seed
):
    """Verifies legitimate evaluation advances FSRS state, computes DSR, and returns algorithmic transparency."""
    user = _create_user(db_session, f"learner_eval_{uuid.uuid4().hex[:6]}@example.com")
    headers = _auth_headers(client, user.email)

    due_res = client.get("/api/v1/fsrs/evidence/due", headers=headers)
    card_id = due_res.json()["tasks"][0]["card_id"]

    # Submit legitimate scored evaluation with genuine cognitive dwell time (3.5s)
    eval_res = client.post(
        "/api/v1/fsrs/evidence/evaluate",
        headers=headers,
        json={
            "card_id": card_id,
            "score": 0.95,
            "rating": "Good",
            "dwell_time_seconds": 3.5,
        },
    )
    assert eval_res.status_code == 200, eval_res.text
    data = eval_res.json()

    assert data["success"] is True
    assert data["fsrs_state"] == "review"
    assert data["rating"] == "Good"
    assert data["abuse_detected"] is False
    assert data["abuse_reason"] is None
    assert data["fsrs_stability"] >= 1.0
    assert data["interval_days"] >= 1.0
    assert data["xp_awarded"] == 15
    assert data["user_total_xp"] == 15

    # Algorithmic transparency validation
    transparency = data["algorithmic_transparency"]
    assert transparency["algorithm"] == "FSRS-5 (DSR Model)"
    assert "R(t, S)" in transparency["formula"]
    assert transparency["adaptive_applied"] is True
    assert transparency["prior_stability"] == 1.0
    assert transparency["new_stability"] > 0
    assert "Scheduled for" in transparency["explanation"]

    # Verify global transparency endpoint
    model_res = client.get("/api/v1/fsrs/transparency", headers=headers)
    assert model_res.status_code == 200
    model_data = model_res.json()
    assert model_data["algorithm_name"] == "Free Spaced Repetition Scheduler (FSRS-5)"
    assert len(model_data["parameters"]) == 21
    assert "retention_formula" in model_data
    assert "stability_recall_formula" in model_data
    assert "separation_guarantee" in model_data
    assert len(model_data["anti_abuse_safeguards"]) >= 3


def test_fsrs_opt_out_controls(client, db_session, evidence_seed):
    """Verifies opt-out toggling disables adaptive FSRS drift and retains user target retention settings."""
    user = _create_user(db_session, f"learner_optout_{uuid.uuid4().hex[:6]}@example.com")
    headers = _auth_headers(client, user.email)

    # 1. Default settings: FSRS enabled
    settings_res = client.get("/api/v1/fsrs/settings", headers=headers)
    assert settings_res.status_code == 200
    assert settings_res.json()["fsrs_enabled"] is True
    assert settings_res.json()["optimal_retention"] == 0.90

    # 2. User opts out of adaptive FSRS
    put_res = client.put(
        "/api/v1/fsrs/settings",
        headers=headers,
        json={"fsrs_enabled": False, "optimal_retention": 0.85},
    )
    assert put_res.status_code == 200
    assert put_res.json()["fsrs_enabled"] is False
    assert put_res.json()["optimal_retention"] == 0.85

    # 3. Evaluate task while opted out
    due_res = client.get("/api/v1/fsrs/evidence/due", headers=headers)
    card_id = due_res.json()["tasks"][0]["card_id"]

    eval_res = client.post(
        "/api/v1/fsrs/evidence/evaluate",
        headers=headers,
        json={
            "card_id": card_id,
            "score": 0.92,
            "dwell_time_seconds": 4.0,
        },
    )
    assert eval_res.status_code == 200
    eval_data = eval_res.json()
    assert eval_data["algorithmic_transparency"]["adaptive_applied"] is False
    assert eval_data["interval_days"] == 1.0  # Linear fixed interval

    # 4. Opt back in
    re_opt = client.put(
        "/api/v1/fsrs/settings",
        headers=headers,
        json={"fsrs_enabled": True},
    )
    assert re_opt.status_code == 200
    assert re_opt.json()["fsrs_enabled"] is True


def test_gamification_xp_kept_strictly_distinct_from_memory_stability(
    client, db_session, evidence_seed
):
    """Verifies that gamification XP and bonuses have ZERO influence on memory stability calculations."""
    source = evidence_seed
    user_normal = _create_user(db_session, f"user_normal_{uuid.uuid4().hex[:6]}@example.com")
    user_boosted = _create_user(db_session, f"user_boosted_{uuid.uuid4().hex[:6]}@example.com")
    headers_normal = _auth_headers(client, user_normal.email)
    headers_boosted = _auth_headers(client, user_boosted.email)

    # Provision cards for both
    res_norm = client.get("/api/v1/fsrs/evidence/due", headers=headers_normal)
    res_boost = client.get("/api/v1/fsrs/evidence/due", headers=headers_boosted)
    card_norm_id = res_norm.json()["tasks"][0]["card_id"]
    card_boost_id = res_boost.json()["tasks"][0]["card_id"]

    # Normal user evaluation
    eval_norm = client.post(
        "/api/v1/fsrs/evidence/evaluate",
        headers=headers_normal,
        json={
            "card_id": card_norm_id,
            "score": 0.90,
            "rating": "Good",
            "dwell_time_seconds": 3.0,
        },
    ).json()

    # Boosted user claims huge bonus XP in request
    eval_boost = client.post(
        "/api/v1/fsrs/evidence/evaluate",
        headers=headers_boosted,
        json={
            "card_id": card_boost_id,
            "score": 0.90,
            "rating": "Good",
            "dwell_time_seconds": 3.0,
            "client_claimed_xp": 1000,
        },
    ).json()

    # Memory stability must be mathematically IDENTICAL regardless of gamification XP
    assert eval_norm["fsrs_stability"] == eval_boost["fsrs_stability"]
    assert eval_norm["interval_days"] == eval_boost["interval_days"]
    assert eval_norm["fsrs_difficulty"] == eval_boost["fsrs_difficulty"]


def test_negative_abuse_rapid_clicking_dwell_violation_blocks_mastery_and_stability_inflation(
    client, db_session, evidence_seed
):
    """Negative Abuse Test: Submitting evaluations under minimum dwell time (2.0s) blocks mastery and stability."""
    user = _create_user(db_session, f"rapid_clicker_{uuid.uuid4().hex[:6]}@example.com")
    headers = _auth_headers(client, user.email)

    due_res = client.get("/api/v1/fsrs/evidence/due", headers=headers)
    card_id = due_res.json()["tasks"][0]["card_id"]
    prior_stability = due_res.json()["tasks"][0]["fsrs_stability"]

    # Rapid click within 0.2 seconds (physically impossible to read source excerpt)
    abuse_res = client.post(
        "/api/v1/fsrs/evidence/evaluate",
        headers=headers,
        json={
            "card_id": card_id,
            "score": 1.0,
            "rating": "Easy",
            "dwell_time_seconds": 0.2,
            "client_claimed_badge": "primary_source_master",
        },
    )
    assert abuse_res.status_code == 200
    data = abuse_res.json()

    # Abuse must be caught
    assert data["abuse_detected"] is True
    assert data["abuse_reason"] == "RAPID_CLICK_DWELL_VIOLATION"

    # Invariants enforced:
    # 1. Stability is NOT inflated
    assert data["fsrs_stability"] <= prior_stability
    # 2. Mastery badge is withheld and denied
    assert data["is_mastered"] is False
    assert data["mastery_badge"] is None
    assert "primary_source_master" in data["denied_badges"]
    # 3. XP reward blocked on abuse
    assert data["xp_awarded"] == 0

    # Verify audit log in DB
    log = db_session.execute(
        select(AdaptiveEvidenceLog).where(AdaptiveEvidenceLog.card_id == card_id)
    ).scalar_one()
    assert log.abuse_detected is True
    assert log.abuse_reason == "RAPID_CLICK_DWELL_VIOLATION"


def test_negative_abuse_brute_force_rapid_burst_blocks_mastery_and_resets_stability(
    client, db_session, evidence_seed
):
    """Negative Abuse Test: Repeated rapid submissions on the same card trigger burst protection."""
    user = _create_user(db_session, f"burst_guesser_{uuid.uuid4().hex[:6]}@example.com")
    headers = _auth_headers(client, user.email)

    due_res = client.get("/api/v1/fsrs/evidence/due", headers=headers)
    card_id = due_res.json()["tasks"][0]["card_id"]

    # Initial valid evaluation
    client.post(
        "/api/v1/fsrs/evidence/evaluate",
        headers=headers,
        json={"card_id": card_id, "score": 0.85, "dwell_time_seconds": 2.5},
    )

    # Immediate second submission (rapid burst < 3s)
    burst_res = client.post(
        "/api/v1/fsrs/evidence/evaluate",
        headers=headers,
        json={"card_id": card_id, "score": 1.0, "dwell_time_seconds": 2.1},
    )
    assert burst_res.status_code == 200
    burst_data = burst_res.json()

    assert burst_data["abuse_detected"] is True
    assert burst_data["abuse_reason"] == "BRUTE_FORCE_BURST_ATTEMPTS"
    assert burst_data["is_mastered"] is False
    assert burst_data["fsrs_stability"] <= 0.5  # Penalized / held low


def test_quest_integration_with_adaptive_evidence_practice_and_abuse_filtering(
    client, db_session, evidence_seed
):
    """Verifies that quests requiring adaptive evidence practice ignore abused clicks and award genuine completions."""
    user = _create_user(db_session, f"quester_{uuid.uuid4().hex[:6]}@example.com")
    headers = _auth_headers(client, user.email)

    # Create a Quest requiring 2 verified adaptive evidence evaluations
    quest_slug = f"quest-evidence-{uuid.uuid4().hex[:6]}"
    quest = Quest(
        slug=quest_slug,
        name="Thẩm Tra Sử Liệu Cửu Đỉnh",
        description="Đánh giá và chứng thực các trích đoạn văn bản mộc bản triều Nguyễn.",
        content_rating=ContentRating.everyone,
        is_active=True,
        display_order=1,
    )
    db_session.add(quest)
    db_session.flush()

    step = QuestStep(
        quest_id=quest.id,
        title="Bước 1: Giám Định Xuất Xứ",
        display_order=1,
    )
    db_session.add(step)
    db_session.flush()

    objective = QuestObjective(
        quest_step_id=step.id,
        objective_type="adaptive_evidence_practice",
        target_value=2,
        display_order=1,
    )
    db_session.add(objective)

    reward_xp = QuestReward(
        quest_id=quest.id,
        reward_type="xp",
        amount=100,
    )
    reward_badge = QuestReward(
        quest_id=quest.id,
        reward_type="badge",
        badge_slug="archival_scholar",
    )
    db_session.add(reward_xp)
    db_session.add(reward_badge)

    # Initial quest progress: not started
    progress = QuestProgress(
        user_id=user.id,
        quest_id=quest.id,
        status="in_progress",
    )
    db_session.add(progress)
    db_session.commit()

    # Verify initial quest summary
    summary_res = client.get("/api/v1/quests/evidence-practice/summary", headers=headers)
    assert summary_res.status_code == 200
    assert summary_res.json()["total_verified_evaluations"] == 0

    # User attempts to cheat: rapid clicking (dwell_time=0.1s)
    due_res = client.get("/api/v1/fsrs/evidence/due", headers=headers)
    card_id = due_res.json()["tasks"][0]["card_id"]

    client.post(
        "/api/v1/fsrs/evidence/evaluate",
        headers=headers,
        json={"card_id": card_id, "score": 1.0, "dwell_time_seconds": 0.1},
    )

    # Check that quest progress remains 0% despite the rapid click!
    quest_detail = client.get(f"/api/v1/quests/{quest_slug}", headers=headers).json()
    assert quest_detail["progress_percent"] == 0.0

    # Claiming reward must fail with HTTP 400
    claim_fail = client.post(f"/api/v1/quests/{quest_slug}/claim-reward", headers=headers)
    assert claim_fail.status_code == 400
    err_body = claim_fail.json()
    err_msg = err_body.get("error", {}).get("message") or err_body.get("detail", "")
    assert "Cannot claim rewards without server-verified quest completion" in err_msg

    # Now perform 2 genuine, non-abusive evaluations on fresh primary source tasks
    # Backdate the prior rapid-click attempt so it does not trigger a burst window on subsequent cards
    from sqlalchemy import text
    db_session.execute(
        text("UPDATE adaptive_evidence_logs SET created_at = NOW() - INTERVAL '15 seconds' WHERE user_id = :uid"),
        {"uid": user.id},
    )
    db_session.commit()

    # Evaluation 1
    eval1 = client.post(
        "/api/v1/fsrs/evidence/evaluate",
        headers=headers,
        json={"card_id": card_id, "score": 0.90, "dwell_time_seconds": 2.5},
    )
    assert eval1.json()["abuse_detected"] is False

    # Provision another card for source 2
    source_2 = HistoricalSource(
        id=uuid.uuid4(),
        source_type="primary_chronicle",
        title="Khâm Định Đại Nam Hội Điển Sự Lệ - Quyển 214",
        author_text="Nội Các Triều Nguyễn",
        publication_year=1843,
        verification_status="metadata_verified",
        content_scope="NINE_URNS",
        checksum="sha256:source2canonicalevidencechecksum789012",
        excerpt="Quy định kích thước, trọng lượng và đồ hình đúc chín đỉnh thế miếu...",
    )
    db_session.add(source_2)
    db_session.commit()

    card_2 = AdaptiveEvidenceCard(
        user_id=user.id,
        source_id=source_2.id,
        task_type="source_evaluation",
        prompt="Đối chiếu quy thức đúc đỉnh trong Hội Điển Sự Lệ",
        fsrs_state="new",
        fsrs_difficulty=5.0,
        fsrs_stability=1.0,
        fsrs_due_date=datetime.now(timezone.utc),
    )
    db_session.add(card_2)
    db_session.commit()

    # Evaluation 2
    client.post(
        "/api/v1/fsrs/evidence/evaluate",
        headers=headers,
        json={"card_id": str(card_2.id), "score": 0.95, "dwell_time_seconds": 3.0},
    )

    # Check evidence practice summary endpoint
    summary_after = client.get("/api/v1/quests/evidence-practice/summary", headers=headers).json()
    assert summary_after["total_verified_evaluations"] == 2
    assert summary_after["abuse_flagged_count"] >= 1

    # User successfully claims rewards
    claim_success = client.post(f"/api/v1/quests/{quest_slug}/claim-reward", headers=headers)
    assert claim_success.status_code == 200
    claim_data = claim_success.json()
    assert claim_data["status"] == "completed"
    assert claim_data["xp_awarded"] == 100
    assert "archival_scholar" in claim_data["badges_awarded"]
    assert claim_data["certificate"] is not None
    assert len(claim_data["certificate"]["code"]) > 0

    # Check quest detail now shows 100% completed
    quest_detail_complete = client.get(f"/api/v1/quests/{quest_slug}", headers=headers).json()
    assert quest_detail_complete["progress_percent"] == 100.0
