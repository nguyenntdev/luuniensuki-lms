# -*- coding: utf-8 -*-
"""FSRS (Free Spaced Repetition Scheduler) Core Algorithm and Adaptive Evidence Service.

Wave W09 / Slot A07 / Ticket V5-T097.

Provides:
1. DSR (Difficulty-Stability-Retrievability) mathematical scheduling engine.
2. Anti-abuse guardrails against rapid clicking, brute-force guessing, and fake mastery.
3. Strict separation of gamification XP from memory stability.
4. Algorithmic transparency and user opt-out controls.
5. Primary source evaluation tasks for historical evidence analysis.
"""
from __future__ import annotations

import math
import uuid
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from ..history_models import HistoricalClaim, HistoricalSource
from ..models import (
    AdaptiveEvidenceCard,
    AdaptiveEvidenceLog,
    User,
    UserFsrsParams,
)

# Default 21 weights for FSRS-5 (matching cohort defaults in migration 0045)
DEFAULT_W: list[float] = [
    0.4072, 1.1829, 3.1262, 15.4722, 7.2102, 0.5316, 1.0651, 0.0589, 1.5747, 0.1070, 1.0070,
    1.9523, 0.1110, 0.3255, 2.2698, 0.2315, 2.9898, 0.5163, 0.6136, 0.0000, 0.0000,
]

# Anti-abuse parameters
MIN_EVALUATION_DWELL_SECONDS: float = 2.0  # Archival reading requires cognitive dwell
RAPID_BURST_WINDOW_SECONDS: float = 3.0    # Submissions under 3s apart flag burst spam
MAX_BURST_ATTEMPTS: int = 3
MASTERY_MIN_REPETITIONS: int = 3
MASTERY_MIN_STABILITY: float = 3.0
MASTERY_MIN_SCORE: float = 0.8
BASE_PRACTICE_XP: int = 15


class FsrsRating(str, Enum):
    Again = "Again"
    Hard = "Hard"
    Good = "Good"
    Easy = "Easy"


class CardState(str, Enum):
    new = "new"
    learning = "learning"
    review = "review"
    relearning = "relearning"


def rating_value(rating: str) -> float:
    normalized = rating.capitalize()
    if normalized == "Again":
        return 1.0
    elif normalized == "Hard":
        return 2.0
    elif normalized == "Good":
        return 3.0
    elif normalized == "Easy":
        return 4.0
    return 3.0


def rating_factor(rating: str) -> float:
    normalized = rating.capitalize()
    if normalized == "Again":
        return 0.0
    elif normalized == "Hard":
        return 0.5
    elif normalized == "Good":
        return 1.0
    elif normalized == "Easy":
        return 1.5
    return 1.0


def map_score_to_rating(score: float, easy_flag: bool = False) -> str:
    """Map continuous score [0.0, 1.0] to discrete FSRS rating."""
    if easy_flag:
        return FsrsRating.Easy.value
    if score >= 0.9:
        return FsrsRating.Good.value
    elif score >= 0.6:
        return FsrsRating.Hard.value
    else:
        return FsrsRating.Again.value


def init_difficulty(rating: str, w: list[float]) -> float:
    r = rating_value(rating)
    d0 = w[4] - math.exp(w[5] * (r - 3.0)) + 1.0
    return max(1.0, min(10.0, d0))


def update_difficulty(d_prev: float, rating: str, w: list[float]) -> float:
    r = rating_value(rating)
    delta_d = -w[6] * (r - 3.0)
    target = d_prev + delta_d * (10.0 - d_prev) / 9.0
    return max(1.0, min(10.0, target))


def retrievability(delta_t_days: float, stability: float) -> float:
    """Compute predicted recall probability R(t, S) using power forgetting curve."""
    if stability <= 0.0 or delta_t_days <= 0.0:
        return 1.0
    return (1.0 + delta_t_days / (9.0 * stability)) ** (-1.0)


def recall_stability(
    d: float, s: float, r: float, rating: str, w: list[float]
) -> float:
    normalized = rating.capitalize()
    hard_penalty = w[15] if normalized == "Hard" else 1.0
    easy_bonus = w[16] if normalized == "Easy" else 1.0
    inc = (
        math.exp(w[8])
        * (11.0 - d)
        * (s ** (-w[9]))
        * (math.exp((1.0 - r) * w[10]) - 1.0)
        * hard_penalty
        * easy_bonus
    )
    return max(0.1, s * (1.0 + max(0.0, inc)))


def forgetting_stability(d: float, s: float, r: float, w: list[float]) -> float:
    v = (
        w[11]
        * (d ** (-w[12]))
        * (((s + 1.0) ** w[13]) - 1.0)
        * math.exp((1.0 - r) * w[14])
    )
    return max(0.1, v)


def next_interval(stability: float, optimal_retention: float) -> float:
    """Calculate next review interval in days matching optimal retention target."""
    if stability <= 0.0:
        return 1.0
    r = max(0.5, min(0.99, optimal_retention))
    interval = 9.0 * stability * ((1.0 / r) - 1.0)
    return max(1.0, min(36500.0, interval))


def schedule_fsrs(
    state: str,
    difficulty: Optional[float],
    stability: Optional[float],
    delta_t_days: float,
    rating: str,
    w: list[float],
    optimal_retention: float,
) -> dict[str, Any]:
    """Execute pure FSRS scheduling update for a review attempt."""
    rating_norm = rating.capitalize()
    optimal_retention = max(0.5, min(0.99, optimal_retention))

    if state == CardState.new.value:
        s0_idx = {
            "Again": 0,
            "Hard": 1,
            "Good": 2,
            "Easy": 3,
        }.get(rating_norm, 2)
        s0 = max(0.1, w[s0_idx])
        d0 = init_difficulty(rating_norm, w)
        next_state = (
            CardState.learning.value if rating_norm == "Again" else CardState.review.value
        )
        return {
            "state": next_state,
            "difficulty": d0,
            "stability": s0,
            "interval_days": next_interval(s0, optimal_retention),
        }

    elif state in (CardState.learning.value, CardState.relearning.value):
        s_prev = max(0.1, stability if stability is not None else 0.5)
        d_prev = max(1.0, min(10.0, difficulty if difficulty is not None else 5.0))
        if rating_norm == "Again":
            s_new = s_prev
            next_state = state
        else:
            s_new = s_prev * (1.0 + 0.5 * rating_factor(rating_norm))
            next_state = CardState.review.value
        d_new = update_difficulty(d_prev, rating_norm, w)
        return {
            "state": next_state,
            "difficulty": d_new,
            "stability": s_new,
            "interval_days": next_interval(s_new, optimal_retention),
        }

    else:  # review state
        s_prev = max(0.1, stability if stability is not None else 1.0)
        d_prev = max(1.0, min(10.0, difficulty if difficulty is not None else 5.0))
        r = retrievability(delta_t_days, s_prev)

        if rating_norm == "Again":
            s_new = forgetting_stability(d_prev, s_prev, r, w)
            next_state = CardState.relearning.value
        else:
            s_new = recall_stability(d_prev, s_prev, r, rating_norm, w)
            next_state = CardState.review.value
        d_new = update_difficulty(d_prev, rating_norm, w)
        return {
            "state": next_state,
            "difficulty": d_new,
            "stability": s_new,
            "interval_days": next_interval(s_new, optimal_retention),
        }


# --------------------------------------------------------------------------- #
# Database Service & Anti-Abuse Logic
# --------------------------------------------------------------------------- #

def get_or_create_user_settings(db: Session, user_id: UUID) -> UserFsrsParams:
    """Retrieve or initialize per-user FSRS settings."""
    settings = db.execute(
        select(UserFsrsParams).where(UserFsrsParams.user_id == user_id)
    ).scalar_one_or_none()

    if settings is None:
        settings = UserFsrsParams(
            user_id=user_id,
            parameters=DEFAULT_W,
            optimal_retention=0.90,
            fsrs_enabled=True,
            review_count_at_last_optimize=0,
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)

    return settings


def update_user_settings(
    db: Session,
    user_id: UUID,
    fsrs_enabled: Optional[bool] = None,
    optimal_retention: Optional[float] = None,
) -> UserFsrsParams:
    """Update user FSRS settings including opt-out controls."""
    settings = get_or_create_user_settings(db, user_id)
    if fsrs_enabled is not None:
        settings.fsrs_enabled = fsrs_enabled
    if optimal_retention is not None:
        settings.optimal_retention = max(0.70, min(0.97, optimal_retention))
    settings.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(settings)
    return settings


def _ensure_seed_sources(db: Session) -> list[HistoricalSource]:
    """Ensure at least one verified historical source exists for practice."""
    sources = db.execute(
        select(HistoricalSource).limit(5)
    ).scalars().all()

    if not sources:
        seed_source = HistoricalSource(
            id=uuid.uuid4(),
            source_type="primary_chronicle",
            title="Đại Nam Thực Lục Chính Biên - Đệ Nhị Kỷ (Kỷ đúc Cửu Đỉnh 1835)",
            author_text="Quốc Sử Quán Triều Nguyễn",
            publisher="Nội Các Huế",
            publication_year=1835,
            citation_text="ĐNTL, Chính biên, Đệ nhị kỷ, Quyển CLXVIII, tờ 12a-15b",
            excerpt="Minh Mạng năm thứ 16, mùa đông tháng 12, đúc xong chín đỉnh lớn đặt trước sân Thế Miếu. Khắc hình sông núi sản vật các xứ trong cõi trời đất...",
            verification_status="metadata_verified",
            content_scope="NINE_URNS",
            checksum="sha256:7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069",
        )
        db.add(seed_source)
        db.commit()
        db.refresh(seed_source)
        sources = [seed_source]

    return sources


def get_due_evidence_tasks(
    db: Session, user: User, limit: int = 10
) -> list[AdaptiveEvidenceCard]:
    """Fetch due primary source evaluation cards, provisioning cards if needed."""
    now = datetime.now(timezone.utc)
    
    # Query due cards
    cards = (
        db.execute(
            select(AdaptiveEvidenceCard)
            .options(
                selectinload(AdaptiveEvidenceCard.source),
                selectinload(AdaptiveEvidenceCard.claim),
            )
            .where(
                AdaptiveEvidenceCard.user_id == user.id,
                AdaptiveEvidenceCard.fsrs_due_date <= now,
            )
            .order_by(AdaptiveEvidenceCard.fsrs_due_date.asc())
            .limit(limit)
        )
        .scalars()
        .all()
    )

    if len(cards) < limit:
        # Provision cards for unassigned sources
        existing_source_ids = db.execute(
            select(AdaptiveEvidenceCard.source_id).where(
                AdaptiveEvidenceCard.user_id == user.id
            )
        ).scalars().all()

        available_sources = (
            db.execute(
                select(HistoricalSource)
                .where(HistoricalSource.id.notin_(existing_source_ids))
                .limit(limit - len(cards))
            )
            .scalars()
            .all()
        )

        if not available_sources and not cards and not existing_source_ids:
            available_sources = _ensure_seed_sources(db)

        for src in available_sources:
            if src.id in existing_source_ids:
                continue
            new_card = AdaptiveEvidenceCard(
                user_id=user.id,
                source_id=src.id,
                task_type="source_evaluation",
                prompt=f"Đánh giá tính xác thực và xuất xứ văn bản của trích đoạn: '{src.title}'",
                fsrs_state=CardState.new.value,
                fsrs_difficulty=5.0,
                fsrs_stability=1.0,
                fsrs_due_date=now,
                interval_days=1.0,
                repetitions=0,
                lapses=0,
                is_mastered=False,
                mastery_badge_awarded=False,
                review_history=[],
            )
            db.add(new_card)

        db.commit()

        # Re-fetch with loaded relationships
        cards = (
            db.execute(
                select(AdaptiveEvidenceCard)
                .options(
                    selectinload(AdaptiveEvidenceCard.source),
                    selectinload(AdaptiveEvidenceCard.claim),
                )
                .where(
                    AdaptiveEvidenceCard.user_id == user.id,
                    AdaptiveEvidenceCard.fsrs_due_date <= now,
                )
                .order_by(AdaptiveEvidenceCard.fsrs_due_date.asc())
                .limit(limit)
            )
            .scalars()
            .all()
        )

    return list(cards)


def evaluate_evidence_task(
    db: Session,
    user: User,
    card_id: UUID,
    score: float,
    dwell_time_seconds: float,
    rating: Optional[str] = None,
    client_claimed_badge: Optional[str] = None,
    client_claimed_xp: Optional[int] = None,
) -> dict[str, Any]:
    """Process a scored primary source evaluation task with anti-abuse enforcement.

    Invariants enforced:
    1. Negative Abuse Prevention:
       - Repeated rapid clicks (< 2.0s dwell time) flagged as RAPID_CLICK_DWELL_VIOLATION.
       - Submissions < 3.0s apart on same card flagged as BRUTE_FORCE_BURST_ATTEMPTS.
       - Abusive attempts NEVER produce mastery badges and NEVER inflate recall stability.
    2. Gamification XP Separation:
       - Earned XP is distinct from FSRS memory stability. XP bonuses or client claims
         have ZERO influence on stability calculations.
    3. Algorithmic Transparency:
       - Returns mathematical breakdown (DSR, formulas, retrievability, interval reason).
    4. Opt-Out Controls:
       - If user opted out (fsrs_enabled=False), adaptive FSRS is bypassed and fixed
         linear scheduling is applied.
    """
    card = db.get(AdaptiveEvidenceCard, card_id)
    if not card or card.user_id != user.id:
        raise ValueError("Practice card not found or unauthorized")

    now = datetime.now(timezone.utc)
    settings = get_or_create_user_settings(db, user.id)

    # Check recent logs for burst guessing
    recent_logs = (
        db.execute(
            select(AdaptiveEvidenceLog)
            .where(
                AdaptiveEvidenceLog.card_id == card_id,
                AdaptiveEvidenceLog.user_id == user.id,
                AdaptiveEvidenceLog.created_at >= now - timedelta(seconds=10),
            )
            .order_by(AdaptiveEvidenceLog.created_at.desc())
        )
        .scalars()
        .all()
    )

    # Abuse Detection
    abuse_detected = False
    abuse_reason: Optional[str] = None

    if dwell_time_seconds < MIN_EVALUATION_DWELL_SECONDS:
        abuse_detected = True
        abuse_reason = "RAPID_CLICK_DWELL_VIOLATION"
    elif len(recent_logs) >= MAX_BURST_ATTEMPTS or (
        recent_logs and (now - recent_logs[0].created_at).total_seconds() < RAPID_BURST_WINDOW_SECONDS
    ):
        abuse_detected = True
        abuse_reason = "BRUTE_FORCE_BURST_ATTEMPTS"

    # Discrete rating mapping
    if not rating:
        rating = map_score_to_rating(score)

    s_prev = card.fsrs_stability or 1.0
    d_prev = card.fsrs_difficulty or 5.0

    delta_t_days = 0.0
    if card.fsrs_last_review is not None:
        delta_t_days = max(
            0.0, (now - card.fsrs_last_review).total_seconds() / 86400.0
        )
    retrievability_val = retrievability(delta_t_days, s_prev)

    denied_badges: list[str] = []
    if client_claimed_badge:
        denied_badges.append(client_claimed_badge)

    xp_awarded = 0
    if not abuse_detected and score >= 0.6:
        # Standard XP awarded for genuine cognitive effort
        xp_awarded = BASE_PRACTICE_XP
        user.total_xp = (user.total_xp or 0) + xp_awarded

    # FSRS scheduling calculation
    if settings.fsrs_enabled and not abuse_detected:
        schedule_res = schedule_fsrs(
            state=card.fsrs_state,
            difficulty=d_prev,
            stability=s_prev,
            delta_t_days=delta_t_days,
            rating=rating,
            w=settings.parameters or DEFAULT_W,
            optimal_retention=settings.optimal_retention or 0.90,
        )
        new_state = schedule_res["state"]
        new_diff = schedule_res["difficulty"]
        new_stab = schedule_res["stability"]
        new_interval = schedule_res["interval_days"]
        adaptive_applied = True
    elif not settings.fsrs_enabled:
        # User opted out: fixed 1-day review, no adaptive drift
        new_state = CardState.review.value
        new_diff = d_prev
        new_stab = 1.0
        new_interval = 1.0
        adaptive_applied = False
    else:
        # Abuse detected: Stability is NOT inflated, interval is capped/reset
        new_state = CardState.relearning.value if score < 0.6 else card.fsrs_state
        new_diff = min(10.0, d_prev + 0.5)
        new_stab = min(s_prev, 0.5)  # Penalized or held stagnant
        new_interval = 1.0
        adaptive_applied = True

    # Mastery Badge Evaluation
    mastery_badge: Optional[str] = None
    is_mastered = False

    if (
        not abuse_detected
        and card.repetitions + 1 >= MASTERY_MIN_REPETITIONS
        and new_stab >= MASTERY_MIN_STABILITY
        and score >= MASTERY_MIN_SCORE
        and new_state == CardState.review.value
    ):
        is_mastered = True
        mastery_badge = "primary_source_master"
        card.is_mastered = True
        card.mastery_badge_awarded = True

    # Persist card state
    card.fsrs_state = new_state
    card.fsrs_difficulty = new_diff
    card.fsrs_stability = new_stab
    card.interval_days = new_interval
    card.fsrs_due_date = now + timedelta(days=new_interval)
    card.fsrs_last_review = now
    card.repetitions = (card.repetitions or 0) + (1 if not abuse_detected else 0)
    if rating == "Again" or abuse_detected:
        card.lapses = (card.lapses or 0) + 1

    history_item = {
        "reviewed_at": now.isoformat(),
        "score": score,
        "rating": rating,
        "dwell_time_seconds": dwell_time_seconds,
        "stability": new_stab,
        "difficulty": new_diff,
        "interval_days": new_interval,
        "abuse_detected": abuse_detected,
        "abuse_reason": abuse_reason,
        "xp_awarded": xp_awarded,
    }
    card.review_history = list(card.review_history or []) + [history_item]
    card.updated_at = now

    # Log to AdaptiveEvidenceLog for auditing and quest progression filtering
    log_entry = AdaptiveEvidenceLog(
        card_id=card.id,
        user_id=user.id,
        source_id=card.source_id,
        evaluation_score=score,
        rating=rating,
        dwell_time_seconds=dwell_time_seconds,
        xp_awarded=xp_awarded,
        stability_before=s_prev,
        stability_after=new_stab,
        difficulty_before=d_prev,
        difficulty_after=new_diff,
        retrievability=retrievability_val,
        abuse_detected=abuse_detected,
        abuse_reason=abuse_reason,
        created_at=now,
    )
    db.add(log_entry)
    db.commit()
    db.refresh(card)
    db.refresh(user)

    explanation = (
        f"Scheduled for {new_interval:.1f} days based on recall score {score:.2f} (Rating: {rating}) "
        f"with estimated retrievability {retrievability_val:.1%}. Prior stability {s_prev:.2f}d updated to {new_stab:.2f}d."
        if not abuse_detected
        else f"Abuse flagged ({abuse_reason}): Recall stability capped at {new_stab:.2f}d and mastery badge withheld."
    )

    transparency = {
        "algorithm": "FSRS-5 (DSR Model)",
        "formula": "R(t, S) = (1 + t / (9 * S)) ^ -1.0; S_new = recall_stability(...) or forgetting_stability(...)",
        "prior_stability": s_prev,
        "new_stability": new_stab,
        "prior_difficulty": d_prev,
        "new_difficulty": new_diff,
        "elapsed_days": delta_t_days,
        "retrievability": retrievability_val,
        "target_retention": settings.optimal_retention,
        "adaptive_applied": adaptive_applied,
        "explanation": explanation,
    }

    return {
        "success": True,
        "card_id": card.id,
        "source_id": card.source_id,
        "score": score,
        "rating": rating,
        "fsrs_state": new_state,
        "fsrs_stability": new_stab,
        "fsrs_difficulty": new_diff,
        "interval_days": new_interval,
        "fsrs_due_date": card.fsrs_due_date,
        "retrievability": retrievability_val,
        "xp_awarded": xp_awarded,
        "user_total_xp": user.total_xp,
        "is_mastered": is_mastered,
        "mastery_badge": mastery_badge,
        "denied_badges": denied_badges,
        "abuse_detected": abuse_detected,
        "abuse_reason": abuse_reason,
        "algorithmic_transparency": transparency,
    }


def get_model_transparency() -> dict[str, Any]:
    """Return static algorithmic transparency specifications and formulas."""
    return {
        "algorithm_name": "Free Spaced Repetition Scheduler (FSRS-5)",
        "parameters": DEFAULT_W,
        "retention_formula": "R(t, S) = (1 + t / (9 * S)) ^ -1.0",
        "stability_recall_formula": "S * (1.0 + exp(w[8]) * (11 - D) * S^(-w[9]) * (exp((1 - R) * w[10]) - 1) * penalty_bonus)",
        "stability_forgetting_formula": "w[11] * D^(-w[12]) * ((S + 1)^w[13] - 1) * exp((1 - R) * w[14])",
        "difficulty_formula": "D_new = D + delta_D * (10 - D) / 9",
        "default_optimal_retention": 0.90,
        "retention_range": [0.70, 0.97],
        "separation_guarantee": (
            "Cognitive memory stability (FSRS) is strictly independent of gamification XP, "
            "level tiers, and streak boosters. Recall half-life reflects cognitive retrieval only."
        ),
        "anti_abuse_safeguards": [
            "Minimum dwell time enforcement (>= 2.0s required to analyze primary source excerpt)",
            "Rapid burst detection (< 3.0s between attempts or > 3 attempts in 10s)",
            "Zero mastery badges on rapid clicks or brute forced guesses",
            "Recall stability is capped or reset on abuse",
        ],
    }
