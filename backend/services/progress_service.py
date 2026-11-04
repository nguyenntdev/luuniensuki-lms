# -*- coding: utf-8 -*-
"""Student learning progression service.

Handles:
- Discrete 4-stage progression: hidden -> discovered -> learned -> mastered.
- Server-acknowledged actions (hotspot discovery, lesson completion, quiz passed >= 80%).
- Anti-replay gamification (idempotency, zero repeat XP, cumulative XP cap 150).
- Rate limiting per student sliding window.
- Negative abuse protection: Hotspot clicks or client claims CANNOT grant mastery XP.
"""
from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from fastapi import status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..domain.gamification import _apply_xp_boost, _compute_rank, _update_streak
from ..domain.helpers import (
    DISCOVERY_XP,
    LESSON_XP,
    MASTERED_XP,
    QUIZ_PASS_PERCENT,
)
from ..errors import AppError
from ..models import (
    Motif,
    QuizAttempt,
    QuizQuestion,
    UnlockStatus,
    Urn,
    User,
    UserProgress,
)

logger = logging.getLogger("luuniensuki.api")

MAX_PROGRESSION_XP = DISCOVERY_XP + LESSON_XP + MASTERED_XP  # 150
PROGRESSION_RATE_LIMIT_ACTIONS = 30
PROGRESSION_RATE_LIMIT_WINDOW = 60  # seconds


class ProgressionRateLimiter:
    """Sliding-window in-memory rate limiter for progression requests."""

    def __init__(self, max_requests: int = PROGRESSION_RATE_LIMIT_ACTIONS, window_seconds: int = PROGRESSION_RATE_LIMIT_WINDOW):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._user_timestamps: dict[UUID, list[float]] = {}

    def check_rate_limit(self, user_id: UUID) -> None:
        now = time.time()
        timestamps = self._user_timestamps.setdefault(user_id, [])
        # Evict timestamps outside sliding window
        cutoff = now - self.window_seconds
        self._user_timestamps[user_id] = [ts for ts in timestamps if ts > cutoff]
        timestamps = self._user_timestamps[user_id]

        if len(timestamps) >= self.max_requests:
            oldest = timestamps[0]
            retry_after = max(1, int(self.window_seconds - (now - oldest)))
            raise AppError(
                code="RATE_LIMIT_EXCEEDED",
                message="Too many progression requests. Please slow down.",
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                details={"retry_after_seconds": retry_after},
            )

        timestamps.append(now)

    def reset(self, user_id: Optional[UUID] = None) -> None:
        if user_id is not None:
            self._user_timestamps.pop(user_id, None)
        else:
            self._user_timestamps.clear()


# Global rate limiter instance and idempotency cache
rate_limiter = ProgressionRateLimiter()
_idempotency_cache: dict[str, dict[str, Any]] = {}


def clear_idempotency_cache() -> None:
    _idempotency_cache.clear()


def record_discovery(
    db: Session,
    user: User,
    motif_id: UUID,
    time_spent_seconds: int = 0,
) -> dict[str, Any]:
    """Record a 3D hotspot / relic discovery action.
    
    Progression invariant:
    Can ONLY advance hidden -> discovered.
    Can NEVER grant learned or mastered status.
    Awards at most DISCOVERY_XP (25).
    Anti-replay: Returns 0 XP if already discovered/learned/mastered.
    """
    motif = db.get(Motif, motif_id)
    if motif is None or not motif.is_active:
        raise AppError("MOTIF_NOT_FOUND", "Motif not found or inactive", status_code=status.HTTP_404_NOT_FOUND)

    if user.role.value == "guest" and not motif.is_demo:
        raise AppError("FORBIDDEN_GUEST_ACCESS", "Guests can only access demo motifs", status_code=status.HTTP_403_FORBIDDEN)

    now = datetime.now(timezone.utc)
    progress = db.execute(
        select(UserProgress).where(
            UserProgress.user_id == user.id,
            UserProgress.motif_id == motif.id,
        )
    ).scalar_one_or_none()

    previous_status = progress.status.value if progress else "hidden"
    xp_awarded = 0
    status_changed = False
    already_unlocked = False

    if progress is None:
        progress = UserProgress(
            user_id=user.id,
            motif_id=motif.id,
            status=UnlockStatus.discovered,
            discovered_at=now,
            xp_earned=DISCOVERY_XP,
        )
        db.add(progress)
        user.total_xp += DISCOVERY_XP
        xp_awarded = DISCOVERY_XP
        status_changed = True
    else:
        if progress.status == UnlockStatus.hidden:
            progress.status = UnlockStatus.discovered
            progress.discovered_at = progress.discovered_at or now
            delta = max(0, DISCOVERY_XP - progress.xp_earned)
            if delta > 0:
                progress.xp_earned = DISCOVERY_XP
                user.total_xp += delta
                xp_awarded = delta
            status_changed = True
        else:
            # Anti-replay: already discovered, learned, or mastered
            already_unlocked = True
            xp_awarded = 0

    new_status = progress.status.value
    _update_streak(user, now)
    user.last_active_at = now
    db.commit()
    db.refresh(progress)

    return {
        "success": True,
        "motif_id": motif.id,
        "previous_status": previous_status,
        "new_status": new_status,
        "status_changed": status_changed,
        "xp_awarded": xp_awarded,
        "total_xp": user.total_xp,
        "message": "Motif discovered successfully" if status_changed else "Motif was already discovered",
        "already_unlocked": already_unlocked,
        "already_learned": progress.status in (UnlockStatus.learned, UnlockStatus.mastered),
        "already_mastered": progress.status == UnlockStatus.mastered,
        "quiz_score": None,
        "quiz_passed": None,
    }


def record_lesson_completion(
    db: Session,
    user: User,
    motif_id: UUID,
    time_spent_seconds: int = 0,
) -> dict[str, Any]:
    """Record verified lesson completion.
    
    Progression invariant:
    Can ONLY advance hidden/discovered -> learned.
    Can NEVER grant mastered status.
    Awards at most LESSON_XP (50), bringing cumulative total to 75.
    Anti-replay: Returns 0 XP if already learned or mastered.
    """
    if time_spent_seconds < 0:
        raise AppError("INVALID_TIME_SPENT", "Time spent cannot be negative", status_code=status.HTTP_400_BAD_REQUEST)

    motif = db.get(Motif, motif_id)
    if motif is None or not motif.is_active:
        raise AppError("MOTIF_NOT_FOUND", "Motif not found or inactive", status_code=status.HTTP_404_NOT_FOUND)

    if user.role.value == "guest" and not motif.is_demo:
        raise AppError("FORBIDDEN_GUEST_ACCESS", "Guests can only access demo motifs", status_code=status.HTTP_403_FORBIDDEN)

    now = datetime.now(timezone.utc)
    target_xp = DISCOVERY_XP + LESSON_XP  # 75

    progress = db.execute(
        select(UserProgress).where(
            UserProgress.user_id == user.id,
            UserProgress.motif_id == motif.id,
        )
    ).scalar_one_or_none()

    previous_status = progress.status.value if progress else "hidden"
    xp_awarded = 0
    status_changed = False
    already_learned = False

    if progress is None:
        progress = UserProgress(
            user_id=user.id,
            motif_id=motif.id,
            status=UnlockStatus.learned,
            discovered_at=now,
            lesson_viewed_at=now,
            learned_at=now,
            xp_earned=target_xp,
        )
        db.add(progress)
        xp_with_boost = _apply_xp_boost(user, target_xp, now)
        user.total_xp += xp_with_boost
        xp_awarded = xp_with_boost
        status_changed = True
    else:
        progress.lesson_viewed_at = progress.lesson_viewed_at or now
        if progress.status in (UnlockStatus.hidden, UnlockStatus.discovered):
            progress.status = UnlockStatus.learned
            progress.discovered_at = progress.discovered_at or now
            progress.learned_at = progress.learned_at or now
            delta = max(0, target_xp - progress.xp_earned)
            if delta > 0:
                progress.xp_earned = target_xp
                delta_with_boost = _apply_xp_boost(user, delta, now)
                user.total_xp += delta_with_boost
                xp_awarded = delta_with_boost
            status_changed = True
        else:
            # Already learned or mastered
            already_learned = True
            xp_awarded = 0

    new_status = progress.status.value
    _update_streak(user, now)
    user.last_active_at = now
    db.commit()
    db.refresh(progress)

    return {
        "success": True,
        "motif_id": motif.id,
        "previous_status": previous_status,
        "new_status": new_status,
        "status_changed": status_changed,
        "xp_awarded": xp_awarded,
        "total_xp": user.total_xp,
        "message": "Lesson completed successfully" if status_changed else "Lesson was already completed",
        "already_unlocked": True,
        "already_learned": already_learned,
        "already_mastered": progress.status == UnlockStatus.mastered,
        "quiz_score": None,
        "quiz_passed": None,
    }


def record_quiz_completion(
    db: Session,
    user: User,
    motif_id: UUID,
    answers: Optional[dict[str, str]] = None,
    time_taken_seconds: Optional[int] = None,
) -> dict[str, Any]:
    """Record server-graded quiz attempt and mastery evaluation.
    
    Progression invariant:
    Advances to 'mastered' ONLY when score >= QUIZ_PASS_PERCENT (80%).
    If score < 80%: Quiz attempt is recorded, status remains learned/discovered,
    mastery XP is NOT awarded.
    Anti-replay: If already mastered, passing again awards 0 XP.
    """
    motif = db.get(Motif, motif_id)
    if motif is None or not motif.is_active:
        raise AppError("MOTIF_NOT_FOUND", "Motif not found or inactive", status_code=status.HTTP_404_NOT_FOUND)

    if user.role.value == "guest" and not motif.is_demo:
        raise AppError("FORBIDDEN_GUEST_ACCESS", "Guests can only access demo motifs", status_code=status.HTTP_403_FORBIDDEN)

    questions = (
        db.execute(
            select(QuizQuestion)
            .where(QuizQuestion.motif_id == motif.id, QuizQuestion.is_active.is_(True))
            .order_by(QuizQuestion.created_at.asc())
        )
        .scalars()
        .all()
    )
    if not questions:
        raise AppError("NO_QUIZ_QUESTIONS", "No quiz questions found for this motif", status_code=status.HTTP_404_NOT_FOUND)

    # Server-side grading of true answers
    score = 0
    max_score = len(questions)
    ans_dict = answers or {}
    for q in questions:
        user_ans = str(ans_dict.get(str(q.id), "")).strip()
        expected = str(q.correct_answer or "").strip()
        if user_ans and user_ans.lower() == expected.lower():
            score += 1

    percentage = int(round((score / max_score) * 100)) if max_score > 0 else 0
    passed = percentage >= QUIZ_PASS_PERCENT

    now = datetime.now(timezone.utc)
    progress = db.execute(
        select(UserProgress).where(
            UserProgress.user_id == user.id,
            UserProgress.motif_id == motif.id,
        )
    ).scalar_one_or_none()

    if progress is None:
        progress = UserProgress(
            user_id=user.id,
            motif_id=motif.id,
            status=UnlockStatus.discovered,
            discovered_at=now,
            xp_earned=DISCOVERY_XP,
        )
        db.add(progress)
        user.total_xp += DISCOVERY_XP

    previous_status = progress.status.value
    progress.quiz_attempts += 1
    progress.quiz_best_score = max(progress.quiz_best_score, percentage)

    # Record persistent QuizAttempt
    attempt = QuizAttempt(
        user_id=user.id,
        motif_id=motif.id,
        score=score,
        max_score=max_score,
        percentage=percentage,
        answers=[{"question_id": str(q.id), "answer": ans_dict.get(str(q.id), "")} for q in questions],
        time_taken_seconds=time_taken_seconds,
    )
    db.add(attempt)

    target_xp = MAX_PROGRESSION_XP  # 150
    xp_awarded = 0
    status_changed = False
    already_mastered = False

    if passed:
        if progress.status != UnlockStatus.mastered:
            progress.status = UnlockStatus.mastered
            progress.mastered_at = progress.mastered_at or now
            delta = max(0, target_xp - progress.xp_earned)
            if delta > 0:
                progress.xp_earned = target_xp
                delta_with_boost = _apply_xp_boost(user, delta, now)
                user.total_xp += delta_with_boost
                xp_awarded = delta_with_boost
            status_changed = True
        else:
            already_mastered = True
            xp_awarded = 0
    else:
        # NEGATIVE ABUSE GUARD:
        # Score below 80% NEVER grants mastery or mastery XP!
        # Status remains untouched.
        xp_awarded = 0
        status_changed = False

    new_status = progress.status.value
    _update_streak(user, now)
    user.last_active_at = now
    db.commit()
    db.refresh(progress)

    return {
        "success": True,
        "motif_id": motif.id,
        "previous_status": previous_status,
        "new_status": new_status,
        "status_changed": status_changed,
        "xp_awarded": xp_awarded,
        "total_xp": user.total_xp,
        "message": "Quiz passed! Motif mastered." if passed and status_changed else (
            "Quiz completed but pass mark (>=80%) not reached" if not passed else "Quiz passed (already mastered)"
        ),
        "already_unlocked": True,
        "already_learned": progress.status in (UnlockStatus.learned, UnlockStatus.mastered),
        "already_mastered": already_mastered or (progress.status == UnlockStatus.mastered and not status_changed),
        "quiz_score": percentage,
        "quiz_passed": passed,
    }


def process_progression_action(
    db: Session,
    user: User,
    action: str,
    motif_id: UUID,
    time_spent_seconds: int = 0,
    answers: Optional[dict[str, str]] = None,
    idempotency_key: Optional[str] = None,
    client_claimed_status: Optional[str] = None,
) -> dict[str, Any]:
    """Unified entry point with rate limiting, anti-replay, and anti-abuse validation."""
    rate_limiter.check_rate_limit(user.id)

    # Anti-replay via idempotency cache
    if idempotency_key:
        cache_key = f"{user.id}:{idempotency_key}"
        if cache_key in _idempotency_cache:
            logger.info("Returning cached idempotent progression response for user %s key %s", user.id, idempotency_key)
            return _idempotency_cache[cache_key]

    # Negative abuse guard: Client-sent claims of status or unearned states are discarded.
    if client_claimed_status and client_claimed_status not in ("hidden", "discovered", "learned", "mastered"):
        raise AppError("INVALID_STATUS_CLAIM", "Invalid progression status claim", status_code=status.HTTP_400_BAD_REQUEST)

    if action == "discover":
        result = record_discovery(db, user, motif_id, time_spent_seconds)
    elif action == "complete_lesson":
        result = record_lesson_completion(db, user, motif_id, time_spent_seconds)
    elif action == "submit_quiz":
        result = record_quiz_completion(db, user, motif_id, answers, time_spent_seconds)
    else:
        raise AppError("INVALID_PROGRESSION_ACTION", f"Unsupported progression action: {action}", status_code=status.HTTP_400_BAD_REQUEST)

    if idempotency_key:
        cache_key = f"{user.id}:{idempotency_key}"
        _idempotency_cache[cache_key] = result

    return result


def get_student_progression_summary(db: Session, user: User) -> dict[str, Any]:
    """Retrieve complete progression overview for a student."""
    motifs = (
        db.execute(
            select(Motif, Urn)
            .outerjoin(Urn, Motif.urn_id == Urn.id)
            .where(Motif.is_active.is_(True))
            .order_by(Motif.created_at.asc())
        )
        .all()
    )
    total_motifs = len(motifs)

    progress_entries = (
        db.execute(
            select(UserProgress).where(UserProgress.user_id == user.id)
        )
        .scalars()
        .all()
    )
    progress_map = {p.motif_id: p for p in progress_entries}

    hidden_count = 0
    discovered_count = 0
    learned_count = 0
    mastered_count = 0
    motif_items = []

    for motif, urn in motifs:
        p = progress_map.get(motif.id)
        current_status = p.status.value if p else "hidden"
        if current_status == "hidden":
            hidden_count += 1
        elif current_status == "discovered":
            discovered_count += 1
        elif current_status == "learned":
            learned_count += 1
        elif current_status == "mastered":
            mastered_count += 1

        motif_title = getattr(motif, "name", None) or getattr(motif, "title", "Hoa văn")
        motif_items.append({
            "motif_id": motif.id,
            "motif_title": motif_title,
            "urn_id": urn.id if urn else None,
            "urn_slug": urn.slug if urn else None,
            "status": current_status,
            "discovered_at": p.discovered_at if p else None,
            "lesson_viewed_at": p.lesson_viewed_at if p else None,
            "learned_at": p.learned_at if p else None,
            "mastered_at": p.mastered_at if p else None,
            "quiz_attempts": p.quiz_attempts if p else 0,
            "quiz_best_score": p.quiz_best_score if p else 0,
            "xp_earned": p.xp_earned if p else 0,
            "is_demo": bool(motif.is_demo),
            "can_view_lesson": current_status in ("discovered", "learned", "mastered"),
            "can_take_quiz": current_status in ("discovered", "learned", "mastered"),
            "is_mastered": current_status == "mastered",
        })

    active_count = discovered_count + learned_count + mastered_count
    completion_pct = round((active_count / total_motifs * 100), 1) if total_motifs > 0 else 0.0
    mastery_pct = round((mastered_count / total_motifs * 100), 1) if total_motifs > 0 else 0.0
    rank_info, _, _ = _compute_rank(user.total_xp)

    return {
        "user_id": user.id,
        "display_name": user.display_name or user.username,
        "total_xp": user.total_xp,
        "current_streak": user.current_streak,
        "rank": rank_info["name"],
        "total_motifs": total_motifs,
        "hidden_count": hidden_count,
        "discovered_count": discovered_count,
        "learned_count": learned_count,
        "mastered_count": mastered_count,
        "completion_percentage": completion_pct,
        "mastery_percentage": mastery_pct,
        "motifs": motif_items,
        "rules": {
            "discovery_xp": DISCOVERY_XP,
            "lesson_xp": LESSON_XP,
            "mastery_xp": MASTERED_XP,
            "max_possible_xp_per_motif": MAX_PROGRESSION_XP,
            "quiz_pass_threshold": QUIZ_PASS_PERCENT,
        },
    }


def get_motif_progression_detail(db: Session, user: User, motif_id: UUID) -> dict[str, Any]:
    """Retrieve detailed progression for a single motif."""
    motif = db.get(Motif, motif_id)
    if motif is None or not motif.is_active:
        raise AppError("MOTIF_NOT_FOUND", "Motif not found or inactive", status_code=status.HTTP_404_NOT_FOUND)

    p = db.execute(
        select(UserProgress).where(
            UserProgress.user_id == user.id,
            UserProgress.motif_id == motif.id,
        )
    ).scalar_one_or_none()

    current_status = p.status.value if p else "hidden"
    motif_title = getattr(motif, "name", None) or getattr(motif, "title", "Hoa văn")
    return {
        "motif_id": motif.id,
        "motif_title": motif_title,
        "urn_id": motif.urn_id,
        "urn_slug": None,
        "status": current_status,
        "discovered_at": p.discovered_at if p else None,
        "lesson_viewed_at": p.lesson_viewed_at if p else None,
        "learned_at": p.learned_at if p else None,
        "mastered_at": p.mastered_at if p else None,
        "quiz_attempts": p.quiz_attempts if p else 0,
        "quiz_best_score": p.quiz_best_score if p else 0,
        "xp_earned": p.xp_earned if p else 0,
        "is_demo": bool(motif.is_demo),
        "can_view_lesson": current_status in ("discovered", "learned", "mastered"),
        "can_take_quiz": current_status in ("discovered", "learned", "mastered"),
        "is_mastered": current_status == "mastered",
    }
