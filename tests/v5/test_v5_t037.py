# -*- coding: utf-8 -*-
"""V5-T037 (Wave W03, Slot A07): Student Learning Progression Test Suite.

Audits and verifies:
1. Four-stage discrete progression state machine:
   hidden -> discovered -> learned -> mastered.
2. Server-acknowledged validation:
   - Hotspot / 3D click -> discovered (+25 XP).
   - Verified lesson completion -> learned (+50 XP, total 75 XP).
   - Quiz evaluation >= 80% -> mastered (+75 XP, total 150 XP).
3. Anti-replay gamification:
   - Duplicate discovery calls award 0 XP.
   - Duplicate lesson completions award 0 XP.
   - Duplicate quiz submissions on mastered relics award 0 XP.
   - Idempotency key deduplication returns cached result without double-awarding.
4. Negative abuse protections:
   - Simply clicking a 3D hotspot or client event CANNOT grant mastery XP or mastered status.
   - Client-claimed status parameters are strictly ignored.
   - Submitting a quiz with score < 80% (e.g. 50%) NEVER grants mastered status or mastery XP.
   - Guest users are forbidden from accessing non-demo motifs (HTTP 403).
   - Negative time spent is rejected (HTTP 400).
   - Non-existent motifs return 404.
5. Rate limiting:
   - In-memory sliding-window rate limiter rejects rapid burst requests with HTTP 429.
6. Summary & individual motif progression endpoints:
   - GET /api/v1/progress/summary
   - GET /api/v1/progress/motifs/{motif_id}
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
import pytest
from sqlalchemy import select

from backend.domain.helpers import (
    DISCOVERY_XP,
    LESSON_XP,
    MASTERED_XP,
    QUIZ_PASS_PERCENT,
)
from backend.models import (
    Motif,
    MotifCategory,
    QuestionType,
    QuizAttempt,
    QuizQuestion,
    UnlockStatus,
    Urn,
    User,
    UserProgress,
    UserRole,
)
from backend.security import hash_password
from backend.services.progress_service import rate_limiter, clear_idempotency_cache


# --------------------------------------------------------------------------- #
# Helpers & Seeders
# --------------------------------------------------------------------------- #

def _create_user(
    db_session,
    email: str,
    role: UserRole = UserRole.learner,
    display_name: str | None = None,
) -> User:
    user = User(
        email=email,
        password_hash=hash_password("Password123!"),
        display_name=display_name or f"Student {email.split('@')[0]}",
        username=f"stu_{uuid.uuid4().hex[:8]}",
        role=role,
        total_xp=0,
        current_streak=0,
        longest_streak=0,
        is_profile_public=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _login_user(client, email: str, password: str = "Password123!") -> dict:
    res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    return res.json()


def _seed_urn_and_motif(
    db_session,
    name: str = "Mặt trời (Nhật)",
    mesh_name: str = "relief_cao_nhat",
    is_demo: bool = False,
) -> tuple[Urn, Motif]:
    urn = Urn(
        slug=f"urn-{uuid.uuid4().hex[:6]}",
        name=f"Cao Đỉnh {uuid.uuid4().hex[:4]}",
        model_url="https://example.com/urn.glb",
        display_order=1,
        is_demo=is_demo,
    )
    db_session.add(urn)
    db_session.flush()

    motif = Motif(
        name=name,
        name_en="The Sun",
        mesh_name=f"{mesh_name}_{uuid.uuid4().hex[:6]}",
        urn_id=urn.id,
        category=MotifCategory.thien_van,
        pos_x=0.0,
        pos_y=1.0,
        pos_z=0.0,
        bounding_radius=1.0,
        is_active=True,
        is_demo=is_demo,
    )
    db_session.add(motif)
    db_session.commit()
    db_session.refresh(urn)
    db_session.refresh(motif)
    return urn, motif


def _seed_quiz_questions(db_session, motif_id: uuid.UUID) -> list[QuizQuestion]:
    """Seed 2 questions: answers are 'A' and 'B'."""
    q1 = QuizQuestion(
        motif_id=motif_id,
        question_text="Hình tượng Mặt trời trên Cao Đỉnh biểu trưng cho điều gì?",
        question_type=QuestionType.multiple_choice,
        options=["Vương quyền tối cao", "Nông nghiệp", "Biển cả", "Gió mùa"],
        correct_answer="Vương quyền tối cao",
        difficulty=1,
        is_published=True,
        is_active=True,
    )
    q2 = QuizQuestion(
        motif_id=motif_id,
        question_text="Cao Đỉnh được đúc vào năm nào dưới triều Minh Mạng?",
        question_type=QuestionType.multiple_choice,
        options=["1835", "1802", "1841", "1885"],
        correct_answer="1835",
        difficulty=1,
        is_published=True,
        is_active=True,
    )
    db_session.add_all([q1, q2])
    db_session.commit()
    db_session.refresh(q1)
    db_session.refresh(q2)
    return [q1, q2]


# --------------------------------------------------------------------------- #
# Tests
# --------------------------------------------------------------------------- #

def test_progression_state_machine_happy_path(client, db_session):
    """Verifies complete 4-step discrete lifecycle:
    hidden -> discovered (+25 XP) -> learned (+50 XP) -> mastered (+75 XP).
    """
    clear_idempotency_cache()
    student = _create_user(db_session, "prog_student_happy@example.com")
    _login_user(client, student.email)
    rate_limiter.reset(student.id)

    _, motif = _seed_urn_and_motif(db_session)
    questions = _seed_quiz_questions(db_session, motif.id)

    # 0. Initial state: No progress row (hidden)
    res_init = client.get(f"/api/v1/progress/motifs/{motif.id}")
    assert res_init.status_code == 200
    assert res_init.json()["status"] == "hidden"
    assert res_init.json()["xp_earned"] == 0

    # 1. Action 1: Discover (3D hotspot / relic discovery)
    res_disc = client.post(
        "/api/v1/progress/action",
        json={"action": "discover", "motif_id": str(motif.id)},
    )
    assert res_disc.status_code == 200
    disc_data = res_disc.json()
    assert disc_data["success"] is True
    assert disc_data["previous_status"] == "hidden"
    assert disc_data["new_status"] == "discovered"
    assert disc_data["status_changed"] is True
    assert disc_data["xp_awarded"] == DISCOVERY_XP  # 25
    assert disc_data["total_xp"] == DISCOVERY_XP

    # Check DB state
    p_row = db_session.execute(
        select(UserProgress).where(UserProgress.user_id == student.id, UserProgress.motif_id == motif.id)
    ).scalar_one()
    assert p_row.status == UnlockStatus.discovered
    assert p_row.discovered_at is not None
    assert p_row.xp_earned == DISCOVERY_XP

    # 2. Action 2: Complete Lesson
    res_lesson = client.post(
        "/api/v1/progress/action",
        json={"action": "complete_lesson", "motif_id": str(motif.id), "time_spent_seconds": 120},
    )
    assert res_lesson.status_code == 200
    lesson_data = res_lesson.json()
    assert lesson_data["success"] is True
    assert lesson_data["previous_status"] == "discovered"
    assert lesson_data["new_status"] == "learned"
    assert lesson_data["status_changed"] is True
    assert lesson_data["xp_awarded"] == LESSON_XP  # 50
    assert lesson_data["total_xp"] == DISCOVERY_XP + LESSON_XP  # 75

    db_session.refresh(p_row)
    assert p_row.status == UnlockStatus.learned
    assert p_row.learned_at is not None
    assert p_row.lesson_viewed_at is not None
    assert p_row.xp_earned == 75

    # 3. Action 3: Submit Quiz (100% correct >= 80% pass threshold)
    answers = {
        str(questions[0].id): "Vương quyền tối cao",
        str(questions[1].id): "1835",
    }
    res_quiz = client.post(
        "/api/v1/progress/action",
        json={
            "action": "submit_quiz",
            "motif_id": str(motif.id),
            "answers": answers,
            "time_spent_seconds": 45,
        },
    )
    assert res_quiz.status_code == 200
    quiz_data = res_quiz.json()
    assert quiz_data["success"] is True
    assert quiz_data["previous_status"] == "learned"
    assert quiz_data["new_status"] == "mastered"
    assert quiz_data["status_changed"] is True
    assert quiz_data["quiz_score"] == 100
    assert quiz_data["quiz_passed"] is True
    assert quiz_data["xp_awarded"] == MASTERED_XP  # 75
    assert quiz_data["total_xp"] == DISCOVERY_XP + LESSON_XP + MASTERED_XP  # 150

    db_session.refresh(p_row)
    assert p_row.status == UnlockStatus.mastered
    assert p_row.mastered_at is not None
    assert p_row.xp_earned == 150
    assert p_row.quiz_best_score == 100
    assert p_row.quiz_attempts == 1

    # Check persistent QuizAttempt record
    attempts = db_session.execute(
        select(QuizAttempt).where(QuizAttempt.user_id == student.id, QuizAttempt.motif_id == motif.id)
    ).scalars().all()
    assert len(attempts) == 1
    assert attempts[0].percentage == 100


def test_anti_replay_gamification(client, db_session):
    """Verifies that duplicate calls and idempotency keys do NOT grant duplicate XP."""
    clear_idempotency_cache()
    student = _create_user(db_session, "prog_anti_replay@example.com")
    _login_user(client, student.email)
    rate_limiter.reset(student.id)

    _, motif = _seed_urn_and_motif(db_session)
    questions = _seed_quiz_questions(db_session, motif.id)

    # 1. Discover once -> 25 XP
    res1 = client.post("/api/v1/progress/discover", json={"action": "discover", "motif_id": str(motif.id)})
    assert res1.json()["xp_awarded"] == 25
    assert res1.json()["total_xp"] == 25

    # 2. Replay discover -> 0 XP awarded, total XP unchanged
    res1_replay = client.post("/api/v1/progress/discover", json={"action": "discover", "motif_id": str(motif.id)})
    assert res1_replay.json()["xp_awarded"] == 0
    assert res1_replay.json()["status_changed"] is False
    assert res1_replay.json()["already_unlocked"] is True
    assert res1_replay.json()["total_xp"] == 25

    # 3. Complete lesson once -> 50 XP
    res2 = client.post("/api/v1/progress/complete-lesson", json={"action": "complete_lesson", "motif_id": str(motif.id)})
    assert res2.json()["xp_awarded"] == 50
    assert res2.json()["total_xp"] == 75

    # 4. Replay complete lesson -> 0 XP awarded
    res2_replay = client.post("/api/v1/progress/complete-lesson", json={"action": "complete_lesson", "motif_id": str(motif.id)})
    assert res2_replay.json()["xp_awarded"] == 0
    assert res2_replay.json()["status_changed"] is False
    assert res2_replay.json()["already_learned"] is True
    assert res2_replay.json()["total_xp"] == 75

    # 5. Submit perfect quiz once -> 75 XP
    answers = {
        str(questions[0].id): "Vương quyền tối cao",
        str(questions[1].id): "1835",
    }
    res3 = client.post(
        "/api/v1/progress/submit-quiz",
        json={"action": "submit_quiz", "motif_id": str(motif.id), "answers": answers},
    )
    assert res3.json()["xp_awarded"] == 75
    assert res3.json()["total_xp"] == 150

    # 6. Replay perfect quiz -> 0 XP awarded (Already mastered)
    res3_replay = client.post(
        "/api/v1/progress/submit-quiz",
        json={"action": "submit_quiz", "motif_id": str(motif.id), "answers": answers},
    )
    assert res3_replay.json()["xp_awarded"] == 0
    assert res3_replay.json()["already_mastered"] is True
    assert res3_replay.json()["total_xp"] == 150

    # 7. Idempotency Key Replay Test
    rate_limiter.reset(student.id)
    _, motif2 = _seed_urn_and_motif(db_session, name="Hoa sen (Liên hoa)", mesh_name="relief_lien_hoa")
    idem_key = f"idem-{uuid.uuid4().hex}"

    first_call = client.post(
        "/api/v1/progress/action",
        json={"action": "discover", "motif_id": str(motif2.id), "idempotency_key": idem_key},
    )
    assert first_call.status_code == 200
    assert first_call.json()["xp_awarded"] == 25

    second_call = client.post(
        "/api/v1/progress/action",
        json={"action": "discover", "motif_id": str(motif2.id), "idempotency_key": idem_key},
    )
    assert second_call.status_code == 200
    # Exact cached response returned
    assert second_call.json() == first_call.json()


def test_negative_abuse_hotspot_cannot_grant_mastery(client, db_session):
    """Negative abuse check:
    Simply clicking a 3D hotspot or client-side event without completing lesson/quiz
    CANNOT grant mastery XP or mastered status.
    Client-claimed status is discarded.
    """
    clear_idempotency_cache()
    student = _create_user(db_session, "prog_negative_abuse@example.com")
    _login_user(client, student.email)
    rate_limiter.reset(student.id)

    _, motif = _seed_urn_and_motif(db_session, name="Cây lúa (Ngô)", mesh_name="relief_lua")

    # Malicious payload: client claims "mastered" directly from hotspot click
    res = client.post(
        "/api/v1/progress/action",
        json={
            "action": "discover",
            "motif_id": str(motif.id),
            "client_claimed_status": "mastered",  # Malicious attempt to forge mastery
        },
    )
    assert res.status_code == 200
    data = res.json()

    # Invariants enforced:
    assert data["new_status"] == "discovered"
    assert data["new_status"] != "mastered"
    assert data["xp_awarded"] == DISCOVERY_XP  # 25, NOT 150!
    assert data["total_xp"] == DISCOVERY_XP

    p_row = db_session.execute(
        select(UserProgress).where(UserProgress.user_id == student.id, UserProgress.motif_id == motif.id)
    ).scalar_one()
    assert p_row.status == UnlockStatus.discovered
    assert p_row.mastered_at is None
    assert p_row.learned_at is None


def test_negative_abuse_failing_quiz_cannot_grant_mastery(client, db_session):
    """Negative abuse check:
    Submitting a quiz with score < 80% (e.g. 50%) NEVER grants mastered status or mastery XP.
    """
    clear_idempotency_cache()
    student = _create_user(db_session, "prog_quiz_fail@example.com")
    _login_user(client, student.email)
    rate_limiter.reset(student.id)

    _, motif = _seed_urn_and_motif(db_session)
    questions = _seed_quiz_questions(db_session, motif.id)

    # First discover and learn properly
    client.post("/api/v1/progress/discover", json={"action": "discover", "motif_id": str(motif.id)})
    client.post("/api/v1/progress/complete-lesson", json={"action": "complete_lesson", "motif_id": str(motif.id)})

    # Submit quiz with 1 wrong answer out of 2 (50% < 80%)
    wrong_answers = {
        str(questions[0].id): "Vương quyền tối cao",  # correct
        str(questions[1].id): "1802",                # WRONG (correct is 1835)
    }
    res = client.post(
        "/api/v1/progress/submit-quiz",
        json={"action": "submit_quiz", "motif_id": str(motif.id), "answers": wrong_answers},
    )
    assert res.status_code == 200
    data = res.json()

    assert data["quiz_score"] == 50
    assert data["quiz_passed"] is False
    assert data["status_changed"] is False
    assert data["new_status"] == "learned"
    assert data["new_status"] != "mastered"
    assert data["xp_awarded"] == 0
    assert data["total_xp"] == 75  # unchanged from learned stage

    p_row = db_session.execute(
        select(UserProgress).where(UserProgress.user_id == student.id, UserProgress.motif_id == motif.id)
    ).scalar_one()
    assert p_row.status == UnlockStatus.learned
    assert p_row.mastered_at is None
    assert p_row.quiz_best_score == 50
    assert p_row.quiz_attempts == 1


def test_guest_and_validation_guardrails(client, db_session):
    """Verifies guest role restrictions, negative time spent validation, and invalid action rejection."""
    clear_idempotency_cache()
    # 1. Guest user trying to progress non-demo motif
    guest = _create_user(db_session, "prog_guest@example.com", role=UserRole.guest)
    _login_user(client, guest.email)
    rate_limiter.reset(guest.id)

    _, non_demo_motif = _seed_urn_and_motif(db_session, is_demo=False)
    res_guest_non_demo = client.post(
        "/api/v1/progress/discover",
        json={"action": "discover", "motif_id": str(non_demo_motif.id)},
    )
    assert res_guest_non_demo.status_code == 403
    assert res_guest_non_demo.json()["error"]["code"] == "FORBIDDEN_GUEST_ACCESS"

    # Guest user CAN progress demo motif
    _, demo_motif = _seed_urn_and_motif(db_session, is_demo=True)
    res_guest_demo = client.post(
        "/api/v1/progress/discover",
        json={"action": "discover", "motif_id": str(demo_motif.id)},
    )
    assert res_guest_demo.status_code == 200
    assert res_guest_demo.json()["new_status"] == "discovered"

    # 2. Student user validation guardrails
    student = _create_user(db_session, "prog_guardrails@example.com")
    _login_user(client, student.email)
    rate_limiter.reset(student.id)

    # Negative time spent
    res_neg_time = client.post(
        "/api/v1/progress/complete-lesson",
        json={"action": "complete_lesson", "motif_id": str(demo_motif.id), "time_spent_seconds": -50},
    )
    assert res_neg_time.status_code == 400
    assert res_neg_time.json()["error"]["code"] == "INVALID_TIME_SPENT"

    # Non-existent motif
    fake_id = str(uuid.uuid4())
    res_404 = client.post(
        "/api/v1/progress/discover",
        json={"action": "discover", "motif_id": fake_id},
    )
    assert res_404.status_code == 404
    assert res_404.json()["error"]["code"] == "MOTIF_NOT_FOUND"

    # Unsupported progression action
    res_bad_action = client.post(
        "/api/v1/progress/action",
        json={"action": "teleport_to_mastery", "motif_id": str(demo_motif.id)},
    )
    assert res_bad_action.status_code in (400, 422)


def test_rate_limiting_enforcement(client, db_session):
    """Verifies that exceeding the sliding-window rate limit triggers HTTP 429."""
    clear_idempotency_cache()
    student = _create_user(db_session, "prog_rate_limit@example.com")
    _login_user(client, student.email)
    rate_limiter.reset(student.id)

    _, motif = _seed_urn_and_motif(db_session)

    # The rate limiter allows 30 requests per window
    for _ in range(30):
        res = client.post("/api/v1/progress/discover", json={"action": "discover", "motif_id": str(motif.id)})
        assert res.status_code == 200

    # 31st request triggers HTTP 429
    res_blocked = client.post("/api/v1/progress/discover", json={"action": "discover", "motif_id": str(motif.id)})
    assert res_blocked.status_code == 429
    assert res_blocked.json()["error"]["code"] == "RATE_LIMIT_EXCEEDED"
    assert "Retry-After" in res_blocked.headers

    # Reset cleans up
    rate_limiter.reset(student.id)
    res_ok = client.post("/api/v1/progress/discover", json={"action": "discover", "motif_id": str(motif.id)})
    assert res_ok.status_code == 200


def test_progression_summary_and_stats(client, db_session):
    """Verifies student progression summary aggregates across relics and calculate stats."""
    clear_idempotency_cache()
    student = _create_user(db_session, "prog_summary_test@example.com")
    _login_user(client, student.email)
    rate_limiter.reset(student.id)

    _, m1 = _seed_urn_and_motif(db_session, name="Hoa sen 1")
    q1 = _seed_quiz_questions(db_session, m1.id)
    _, m2 = _seed_urn_and_motif(db_session, name="Hoa cúc 2")

    # Motif 1 -> progress to Mastered
    client.post("/api/v1/progress/discover", json={"action": "discover", "motif_id": str(m1.id)})
    client.post("/api/v1/progress/complete-lesson", json={"action": "complete_lesson", "motif_id": str(m1.id)})
    client.post(
        "/api/v1/progress/submit-quiz",
        json={
            "action": "submit_quiz",
            "motif_id": str(m1.id),
            "answers": {str(q1[0].id): "Vương quyền tối cao", str(q1[1].id): "1835"},
        },
    )

    # Motif 2 -> progress to Discovered only
    client.post("/api/v1/progress/discover", json={"action": "discover", "motif_id": str(m2.id)})

    # Fetch summary
    res = client.get("/api/v1/progress/summary")
    assert res.status_code == 200
    data = res.json()

    assert data["user_id"] == str(student.id)
    assert data["mastered_count"] >= 1
    assert data["discovered_count"] >= 1
    assert data["rules"]["discovery_xp"] == 25
    assert data["rules"]["lesson_xp"] == 50
    assert data["rules"]["mastery_xp"] == 75
    assert data["rules"]["quiz_pass_threshold"] == 80
    assert data["completion_percentage"] > 0
    assert data["mastery_percentage"] > 0


def test_negative_abuse_lesson_cannot_grant_mastery(client, db_session):
    """Negative abuse check:
    Completing a lesson CANNOT grant mastery XP or mastered status.
    Max status is 'learned' and max XP is 75 (DISCOVERY_XP + LESSON_XP).
    """
    clear_idempotency_cache()
    student = _create_user(db_session, "prog_lesson_abuse@example.com")
    _login_user(client, student.email)
    rate_limiter.reset(student.id)

    _, motif = _seed_urn_and_motif(db_session, name="Cây ngô (Bắp)")

    # Call complete-lesson from hidden state
    res = client.post(
        "/api/v1/progress/complete-lesson",
        json={"action": "complete_lesson", "motif_id": str(motif.id)},
    )
    assert res.status_code == 200
    data = res.json()

    assert data["new_status"] == "learned"
    assert data["new_status"] != "mastered"
    assert data["xp_awarded"] == DISCOVERY_XP + LESSON_XP  # 75
    assert data["total_xp"] == 75

    p_row = db_session.execute(
        select(UserProgress).where(UserProgress.user_id == student.id, UserProgress.motif_id == motif.id)
    ).scalar_one()
    assert p_row.status == UnlockStatus.learned
    assert p_row.mastered_at is None
    assert p_row.learned_at is not None


def test_negative_abuse_unanswered_quiz(client, db_session):
    """Submitting empty answers to a quiz results in 0% score, no mastery, and 0 XP."""
    clear_idempotency_cache()
    student = _create_user(db_session, "prog_empty_quiz@example.com")
    _login_user(client, student.email)
    rate_limiter.reset(student.id)

    _, motif = _seed_urn_and_motif(db_session)
    _seed_quiz_questions(db_session, motif.id)

    client.post("/api/v1/progress/discover", json={"action": "discover", "motif_id": str(motif.id)})

    res = client.post(
        "/api/v1/progress/submit-quiz",
        json={"action": "submit_quiz", "motif_id": str(motif.id), "answers": {}},
    )
    assert res.status_code == 200
    data = res.json()

    assert data["quiz_score"] == 0
    assert data["quiz_passed"] is False
    assert data["new_status"] == "discovered"
    assert data["xp_awarded"] == 0
    assert data["total_xp"] == 25


def test_cross_student_progression_isolation(client, db_session):
    """Verifies multi-student data isolation:
    Student A mastering a motif does not leak or affect Student B's progress.
    """
    clear_idempotency_cache()
    student_a = _create_user(db_session, "student_a_isolation@example.com")
    student_b = _create_user(db_session, "student_b_isolation@example.com")

    _, motif = _seed_urn_and_motif(db_session, name="Voi (Tượng)")
    questions = _seed_quiz_questions(db_session, motif.id)

    # Student A logs in and completes all stages to Mastered
    _login_user(client, student_a.email)
    rate_limiter.reset(student_a.id)

    client.post("/api/v1/progress/discover", json={"action": "discover", "motif_id": str(motif.id)})
    client.post("/api/v1/progress/complete-lesson", json={"action": "complete_lesson", "motif_id": str(motif.id)})
    client.post(
        "/api/v1/progress/submit-quiz",
        json={
            "action": "submit_quiz",
            "motif_id": str(motif.id),
            "answers": {str(questions[0].id): "Vương quyền tối cao", str(questions[1].id): "1835"},
        },
    )

    res_a = client.get(f"/api/v1/progress/motifs/{motif.id}")
    assert res_a.json()["status"] == "mastered"
    assert res_a.json()["xp_earned"] == 150

    # Student B logs in: Student B must see 'hidden' with 0 XP for the same motif!
    _login_user(client, student_b.email)
    rate_limiter.reset(student_b.id)

    res_b = client.get(f"/api/v1/progress/motifs/{motif.id}")
    assert res_b.json()["status"] == "hidden"
    assert res_b.json()["xp_earned"] == 0
    assert res_b.json()["mastered_at"] is None

