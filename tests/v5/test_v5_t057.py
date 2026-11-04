# -*- coding: utf-8 -*-
"""V5-T057: Mobile Lesson Quiz Sync and Server-Authoritative Assessment Test Suite.

Wave W05, Slot A07 (Priority: P1, Classification: PRODUCTION_COMPLETION).
Verifies:
1. Mobile Lesson Quiz Sync Endpoints:
   - GET /api/v1/history/practice/sync:
     - Fetches published, content-validated quiz questions from real DB records.
     - Content validation gate: blocks unreviewed or invalid draft questions.
     - Never leaks correct_answer or answer_contract to the client (security leak prevention).
   - GET /api/v1/history/lessons/{lesson_id}/quiz-sync:
     - Syncs questions specific to a historical lesson / motif.
2. Server-Authoritative Practice Grading & Assessment Tasks:
   - POST /api/v1/history/practice/submit:
     - Server derives score, percentage, and passed mark (>= 80% threshold).
     - Positive completion: awards 75 mastery XP and verified badges in database.
     - Awards first-mastered, perfect-score (100%), and speed-demon (<= 30s) badges.
     - Persists QuizAttempt and advances UserProgress to mastered.
3. Negative Abuse Guardrails:
   - Scores below 80% (failing quiz):
     - passed = False, xp_awarded = 0, awarded_badges = [].
     - Client cannot earn graded completion badges locally or by client-side claims.
     - Forged client_claimed_badges are strictly routed to denied_badges and rejected.
   - Direct unverified badge verification endpoint:
     - POST /api/v1/history/practice/verify-badge rejects unearned badge with HTTP 400
       UNVERIFIED_COMPLETION: "Student cannot earn graded completion badges locally without verified server response."
     - Validates legitimate badges only after passing server evaluation.
4. Anti-Replay & Idempotency:
   - Duplicate quiz submissions on already mastered relics award 0 XP and 0 duplicate badges.
5. Mobile Codebase Verification:
   - Verifies mobile practice_provider.dart eliminated MockQuizData.mockQuestions.
   - Verifies ApiConstants defines real practice sync, submit, and verify-badge endpoints.
"""
from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from backend.domain.helpers import (
    BADGE_FIRST_MASTERED,
    BADGE_PERFECT_SCORE,
    BADGE_SPEED_DEMON,
    DISCOVERY_XP,
    LESSON_XP,
    MASTERED_XP,
)
from backend.seed import DEFAULT_BADGES
from backend.models import (
    Badge,
    ContentStatus,
    LessonContent,
    Motif,
    MotifCategory,
    QuestionType,
    QuizAttempt,
    QuizQuestion,
    UnlockStatus,
    Urn,
    User,
    UserBadge,
    UserProgress,
    UserRole,
)
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
    """Create a verified test user."""
    user = User(
        email=email,
        password_hash=hash_password("Password123!"),
        display_name=display_name or f"User {email.split('@')[0]}",
        username=f"usr_{uuid.uuid4().hex[:8]}",
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


def _login(client: TestClient, email: str, password: str = "Password123!") -> dict:
    """Authenticate user and return session cookie."""
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    return res.json()


def _seed_badges(db_session) -> None:
    """Seed system default badges if not already present."""
    for b in DEFAULT_BADGES:
        existing = db_session.execute(
            select(Badge).where(Badge.slug == b["slug"])
        ).scalar_one_or_none()
        if not existing:
            badge = Badge(
                slug=b["slug"],
                name=b["name"],
                name_en=b.get("name_en"),
                description=b.get("description"),
                icon_url=b["icon_url"],
                category=b["category"],
                xp_bonus=b.get("xp_bonus", 0),
                unlock_criteria=b.get("unlock_criteria", {}),
                is_secret=b.get("is_secret", False),
                is_active=True,
            )
            db_session.add(badge)
    db_session.commit()


def _seed_motif_and_lesson(
    db_session,
    name: str = "Họa tiết Phượng Hoàng",
    category: MotifCategory = MotifCategory.linh_thu,
) -> tuple[Motif, LessonContent]:
    """Seed urn, motif, and associated lesson content."""
    urn = Urn(
        slug=f"urn-{uuid.uuid4().hex[:6]}",
        name=f"Đỉnh Test {uuid.uuid4().hex[:4]}",
        model_url="https://example.com/urn.glb",
        display_order=1,
        is_demo=False,
    )
    db_session.add(urn)
    db_session.flush()

    motif = Motif(
        name=name,
        name_en="Phoenix Relief",
        mesh_name=f"relief_{uuid.uuid4().hex[:6]}",
        urn_id=urn.id,
        category=category,
        pos_x=0.0,
        pos_y=1.0,
        pos_z=0.0,
        bounding_radius=1.0,
        is_active=True,
        is_demo=False,
    )
    db_session.add(motif)
    db_session.flush()

    lesson = LessonContent(
        motif_id=motif.id,
        description="Nội dung lịch sử chi tiết về họa tiết thời Nguyễn...",
        historical_context="Bối cảnh lịch sử triều Nguyễn thế kỷ XIX...",
        symbolism="Ý nghĩa văn hóa biểu trưng...",
        is_published=True,
    )
    db_session.add(lesson)
    db_session.commit()
    db_session.refresh(motif)
    db_session.refresh(lesson)
    return motif, lesson


def _seed_user_progress(
    db_session,
    user_id: uuid.UUID,
    motif_id: uuid.UUID,
    status: UnlockStatus = UnlockStatus.learned,
) -> UserProgress:
    """Seed initial user progression prior to quiz assessment."""
    progress = UserProgress(
        user_id=user_id,
        motif_id=motif_id,
        status=status,
        discovered_at=datetime.now(timezone.utc),
        lesson_viewed_at=datetime.now(timezone.utc),
        learned_at=datetime.now(timezone.utc),
        xp_earned=DISCOVERY_XP + LESSON_XP,  # 75
        quiz_attempts=0,
        quiz_best_score=0,
    )
    db_session.add(progress)
    db_session.commit()
    db_session.refresh(progress)
    return progress


def _seed_quiz_questions(
    db_session,
    motif_id: uuid.UUID,
    include_invalid: bool = False,
) -> list[QuizQuestion]:
    """Seed valid published quiz questions and optionally invalid draft ones."""
    q1 = QuizQuestion(
        motif_id=motif_id,
        question_text="Họa tiết Phượng hoàng tượng trưng cho điều gì trong văn hóa cung đình?",
        question_type=QuestionType.multiple_choice,
        options=["Sự cao quý và thanh nhã", "Sức mạnh chiến binh", "Nông nghiệp trù phú", "Biển cả bao la"],
        correct_answer="Sự cao quý và thanh nhã",
        explanation="Phượng hoàng biểu trưng cho hoàng hậu và sự thanh cao, đức hạnh.",
        difficulty=1,
        is_published=True,
        is_active=True,
        content_validation_status="valid",
    )
    q2 = QuizQuestion(
        motif_id=motif_id,
        question_text="Phượng hoàng trên Cửu Đỉnh được đúc bằng chất liệu gì?",
        question_type=QuestionType.multiple_choice,
        options=["Đồng thau", "Vàng ròng", "Bạc", "Đá cẩm thạch"],
        correct_answer="Đồng thau",
        explanation="Cửu Đỉnh triều Nguyễn được đúc hoàn toàn bằng hợp kim đồng thau.",
        difficulty=2,
        is_published=True,
        is_active=True,
        content_validation_status="valid",
    )
    questions = [q1, q2]

    if include_invalid:
        q_blocked = QuizQuestion(
            motif_id=motif_id,
            question_text="Câu hỏi chưa kiểm định nguồn lịch sử (bị chặn)?",
            question_type=QuestionType.multiple_choice,
            options=["A", "B"],
            correct_answer="A",
            is_published=True,
            is_active=True,
            content_validation_status="blocked_for_authoritative_learning",
        )
        q_draft = QuizQuestion(
            motif_id=motif_id,
            question_text="Câu hỏi nháp chưa xuất bản?",
            question_type=QuestionType.multiple_choice,
            options=["A", "B"],
            correct_answer="A",
            is_published=False,
            is_active=True,
            content_validation_status="valid",
        )
        questions.extend([q_blocked, q_draft])

    db_session.add_all(questions)
    db_session.commit()
    for q in questions:
        db_session.refresh(q)
    return questions


# --------------------------------------------------------------------------- #
# Test 1: Mobile Practice Sync Endpoints & Answer Key Protection
# --------------------------------------------------------------------------- #

def test_practice_sync_real_questions_parity(client: TestClient, db_session):
    """Verifies GET /api/v1/history/practice/sync returns published questions with security protections."""
    motif, _ = _seed_motif_and_lesson(db_session, "Kỳ Lân Hoàng Gia", MotifCategory.linh_thu)
    questions = _seed_quiz_questions(db_session, motif.id, include_invalid=True)

    res = client.get(
        "/api/v1/history/practice/sync",
        params={"motif_id": str(motif.id), "limit": 10},
    )
    assert res.status_code == 200, f"Sync failed: {res.text}"
    data = res.json()

    assert "session_id" in data
    assert "items" in data
    assert data["assessment_mode"] == "quick_review"

    # Must only return the 2 valid published questions; draft and blocked are excluded
    returned_ids = [item["id"] for item in data["items"]]
    assert str(questions[0].id) in returned_ids
    assert str(questions[1].id) in returned_ids
    assert str(questions[2].id) not in returned_ids  # blocked question
    assert str(questions[3].id) not in returned_ids  # draft question
    assert len(data["items"]) == 2

    # CRITICAL SECURITY INVARIANT:
    # Client sync payload must NEVER leak correct_answer or answer_contract
    for item in data["items"]:
        assert "correct_answer" not in item
        assert "answer_contract" not in item
        assert item["question_text"] is not None
        assert isinstance(item["options"], list)
        assert len(item["options"]) == 4
        assert item["content_validation_status"] == "valid"
        assert item["is_verified_content"] is True


def test_lesson_quiz_sync_endpoint(client: TestClient, db_session):
    """Verifies GET /api/v1/history/lessons/{lesson_id}/quiz-sync retrieves lesson-scoped questions."""
    motif, lesson = _seed_motif_and_lesson(db_session, "Cây Tùng", MotifCategory.thao_moc)
    questions = _seed_quiz_questions(db_session, motif.id)

    res = client.get(f"/api/v1/history/lessons/{lesson.id}/quiz-sync")
    assert res.status_code == 200, f"Lesson quiz sync failed: {res.text}"
    data = res.json()

    assert data["assessment_mode"] == "lesson_quiz"
    assert data["total_questions"] == 2
    item_ids = [item["id"] for item in data["items"]]
    assert str(questions[0].id) in item_ids
    assert str(questions[1].id) in item_ids


# --------------------------------------------------------------------------- #
# Test 2: Server-Authoritative Graded Assessment & Verified Completion Badges
# --------------------------------------------------------------------------- #

def test_server_authoritative_grading_positive_completion_badges(client: TestClient, db_session):
    """Verifies positive server-authoritative quiz completion and badge awards."""
    _seed_badges(db_session)
    student = _create_user(db_session, "sync_student_pass@example.com")
    _login(client, student.email)

    motif, lesson = _seed_motif_and_lesson(db_session, "Rồng Vàng", MotifCategory.linh_thu)
    _seed_user_progress(db_session, student.id, motif.id, UnlockStatus.learned)
    student.total_xp = DISCOVERY_XP + LESSON_XP
    db_session.commit()
    questions = _seed_quiz_questions(db_session, motif.id)

    # Prepare 100% correct answers
    answers = {
        str(questions[0].id): "Sự cao quý và thanh nhã",
        str(questions[1].id): "Đồng thau",
    }

    # Student submits work in 25 seconds (qualifies for speed-demon)
    res = client.post(
        "/api/v1/history/practice/submit",
        json={
            "motif_id": str(motif.id),
            "lesson_id": str(lesson.id),
            "answers": answers,
            "time_taken_seconds": 25,
            "client_claimed_badges": ["first-mastered", "perfect-score"],
            "client_claimed_score": 100,
        },
    )
    assert res.status_code == 200, f"Submit failed: {res.text}"
    data = res.json()

    assert data["success"] is True
    assert data["score"] == 2
    assert data["max_score"] == 2
    assert data["percentage"] == 100
    assert data["passed"] is True
    assert data["server_verified"] is True
    assert data["new_status"] == "mastered"
    assert data["xp_awarded"] == MASTERED_XP  # 75

    # Check awarded badges in response
    awarded_slugs = [b["slug"] for b in data["awarded_badges"]]
    assert BADGE_FIRST_MASTERED in awarded_slugs
    assert BADGE_PERFECT_SCORE in awarded_slugs
    assert BADGE_SPEED_DEMON in awarded_slugs
    assert data["denied_badges"] == []

    # Check database persistence: user_badges table must contain rows for student
    user_badges = db_session.execute(
        select(UserBadge).join(Badge).where(UserBadge.user_id == student.id)
    ).scalars().all()
    user_badge_slugs = [ub.badge.slug for ub in user_badges]
    assert BADGE_FIRST_MASTERED in user_badge_slugs
    assert BADGE_PERFECT_SCORE in user_badge_slugs
    assert BADGE_SPEED_DEMON in user_badge_slugs

    # Check QuizAttempt persistent record
    attempt = db_session.execute(
        select(QuizAttempt).where(QuizAttempt.user_id == student.id, QuizAttempt.motif_id == motif.id)
    ).scalar_one_or_none()
    assert attempt is not None
    assert attempt.percentage == 100
    assert attempt.time_taken_seconds == 25

    # Check UserProgress is mastered
    progress = db_session.execute(
        select(UserProgress).where(UserProgress.user_id == student.id, UserProgress.motif_id == motif.id)
    ).scalar_one_or_none()
    assert progress is not None
    assert progress.status == UnlockStatus.mastered


# --------------------------------------------------------------------------- #
# Test 3: Negative Abuse — Failing Quiz Cannot Earn Badges or Mastery
# --------------------------------------------------------------------------- #

def test_negative_abuse_failed_quiz_cannot_earn_completion_badges(client: TestClient, db_session):
    """Verifies student scoring < 80% CANNOT earn completion badges locally or by client-side claims."""
    _seed_badges(db_session)
    student = _create_user(db_session, "sync_student_fail@example.com")
    _login(client, student.email)

    motif, lesson = _seed_motif_and_lesson(db_session, "Hoa Sen", MotifCategory.thao_moc)
    questions = _seed_quiz_questions(db_session, motif.id)

    # 1 correct, 1 incorrect answer (50% < 80% pass threshold)
    answers = {
        str(questions[0].id): "Sự cao quý và thanh nhã",  # Correct
        str(questions[1].id): "Vàng ròng",               # Incorrect
    }

    # Student attempts negative abuse: sends client_claimed_badges and claimed score 100
    res = client.post(
        "/api/v1/history/practice/submit",
        json={
            "motif_id": str(motif.id),
            "lesson_id": str(lesson.id),
            "answers": answers,
            "time_taken_seconds": 20,
            "client_claimed_badges": ["first-mastered", "perfect-score"],
            "client_claimed_score": 100.0,
        },
    )
    assert res.status_code == 200
    data = res.json()

    # Authoritative server score must be 50%, not 100%
    assert data["score"] == 1
    assert data["max_score"] == 2
    assert data["percentage"] == 50
    assert data["passed"] is False
    assert data["xp_awarded"] == 0
    assert data["awarded_badges"] == []
    # Both client-claimed badges MUST be explicitly denied
    assert "first-mastered" in data["denied_badges"]
    assert "perfect-score" in data["denied_badges"]
    assert data["new_status"] != "mastered"

    # Database verification: user_badges must remain completely EMPTY
    badge_count = db_session.execute(
        select(func.count(UserBadge.id)).where(UserBadge.user_id == student.id)
    ).scalar_one()
    assert badge_count == 0

    # UserProgress must not be mastered
    progress = db_session.execute(
        select(UserProgress).where(UserProgress.user_id == student.id, UserProgress.motif_id == motif.id)
    ).scalar_one_or_none()
    assert progress is not None
    assert progress.status != UnlockStatus.mastered


# --------------------------------------------------------------------------- #
# Test 4: Negative Abuse — Direct Unverified Badge Claim Rejected
# --------------------------------------------------------------------------- #

def test_negative_abuse_direct_unverified_badge_claim_rejected(client: TestClient, db_session):
    """Verifies that POST /api/v1/history/practice/verify-badge rejects unearned badge claims."""
    _seed_badges(db_session)
    student = _create_user(db_session, "sync_student_direct_claim@example.com")
    _login(client, student.email)

    motif, _ = _seed_motif_and_lesson(db_session, "Lân Mẫu", MotifCategory.linh_thu)
    questions = _seed_quiz_questions(db_session, motif.id)

    # 1. Direct unverified claim attempt: student tries to claim 'first-mastered' without passing quiz
    res_fake = client.post(
        "/api/v1/history/practice/verify-badge",
        json={"badge_slug": "first-mastered", "motif_id": str(motif.id)},
    )
    assert res_fake.status_code == 400
    err_body = res_fake.json()
    assert err_body["error"]["code"] == "UNVERIFIED_COMPLETION"
    assert "Student cannot earn graded completion badges locally without verified server response" in err_body["error"]["message"]

    # 2. Legitimate quiz completion
    correct_answers = {
        str(questions[0].id): "Sự cao quý và thanh nhã",
        str(questions[1].id): "Đồng thau",
    }
    res_quiz = client.post(
        "/api/v1/history/practice/submit",
        json={"motif_id": str(motif.id), "answers": correct_answers, "time_taken_seconds": 40},
    )
    assert res_quiz.status_code == 200
    assert res_quiz.json()["passed"] is True

    # 3. Now verify legitimate badge -> succeeds with HTTP 200
    res_verified = client.post(
        "/api/v1/history/practice/verify-badge",
        json={"badge_slug": "first-mastered", "motif_id": str(motif.id)},
    )
    assert res_verified.status_code == 200
    v_data = res_verified.json()
    assert v_data["is_verified"] is True
    assert v_data["badge_slug"] == "first-mastered"
    assert v_data["earned_at"] is not None


# --------------------------------------------------------------------------- #
# Test 5: Anti-Replay & Idempotency Safeguards
# --------------------------------------------------------------------------- #

def test_anti_replay_and_idempotency_protection(client: TestClient, db_session):
    """Verifies duplicate passing quiz submissions do NOT grant repeat XP or duplicate badges."""
    _seed_badges(db_session)
    student = _create_user(db_session, "sync_anti_replay@example.com")
    _login(client, student.email)

    motif, _ = _seed_motif_and_lesson(db_session, "Chim Công", MotifCategory.linh_thu)
    _seed_user_progress(db_session, student.id, motif.id, UnlockStatus.learned)
    student.total_xp = DISCOVERY_XP + LESSON_XP
    db_session.commit()
    questions = _seed_quiz_questions(db_session, motif.id)
    correct_answers = {
        str(questions[0].id): "Sự cao quý và thanh nhã",
        str(questions[1].id): "Đồng thau",
    }

    # First submission -> awards 75 mastery XP
    res1 = client.post(
        "/api/v1/history/practice/submit",
        json={"motif_id": str(motif.id), "answers": correct_answers},
    )
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["xp_awarded"] == MASTERED_XP
    assert len(data1["awarded_badges"]) >= 1

    # Second submission (replay) -> 0 XP awarded, 0 new badges
    res2 = client.post(
        "/api/v1/history/practice/submit",
        json={"motif_id": str(motif.id), "answers": correct_answers},
    )
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["xp_awarded"] == 0
    assert data2["passed"] is True
    assert data2["new_status"] == "mastered"

    # UserBadge rows must not be duplicated
    badge_rows = db_session.execute(
        select(UserBadge).where(UserBadge.user_id == student.id)
    ).scalars().all()
    badge_slugs = [b.badge_id for b in badge_rows]
    assert len(badge_slugs) == len(set(badge_slugs))


# --------------------------------------------------------------------------- #
# Test 6: Mobile Codebase Static Invariants Verification
# --------------------------------------------------------------------------- #

def test_mobile_practice_provider_clean_parity():
    """Verifies mobile practice provider has eliminated mock data in real flow and uses real API constants."""
    root_dir = Path("/home/clue/Documents/luuniensuki-lms")
    practice_provider_path = root_dir / "mobile/lib/features/practice/presentation/providers/practice_provider.dart"
    api_constants_path = root_dir / "mobile/lib/core/constants/api_constants.dart"

    assert practice_provider_path.exists(), f"Missing file: {practice_provider_path}"
    assert api_constants_path.exists(), f"Missing file: {api_constants_path}"

    provider_code = practice_provider_path.read_text(encoding="utf-8")
    constants_code = api_constants_path.read_text(encoding="utf-8")

    # Invariant 1: MockQuizData.mockQuestions eliminated from practice_provider.dart
    assert "MockQuizData.mockQuestions" not in provider_code, (
        "practice_provider.dart must not call MockQuizData.mockQuestions in real flows."
    )

    # Invariant 2: Backend sync & submit methods wired
    assert "syncQuestionsFromBackend" in provider_code
    assert "submitSessionToServer" in provider_code
    assert "isServerVerified" in provider_code
    assert "verifiedBadges" in provider_code
    assert "deniedBadges" in provider_code

    # Invariant 3: ApiConstants defines real practice sync and submit routes
    assert "practiceSync" in constants_code
    assert "practiceSubmit" in constants_code
    assert "practiceVerifyBadge" in constants_code
    assert "$apiPath/history/practice/sync" in constants_code
    assert "$apiPath/history/practice/submit" in constants_code
    assert "$apiPath/history/practice/verify-badge" in constants_code
