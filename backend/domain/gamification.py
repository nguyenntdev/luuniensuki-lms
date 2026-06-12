# -*- coding: utf-8 -*-
"""Gamification / progression domain helpers.

Extracted from ``backend.main`` (backend-modularization task 3.1): rank
computation, streak updates, XP-boost application, badge awarding, and
certificate issuance, plus the ``XP_RANKS`` table and ``CERTIFICATE_ISSUER_NAME``
constant they depend on.

STRICTLY behavior-preserving: every function is moved verbatim. Import direction
is one-way — this module imports from ``.db``, ``.models``, and standard
libraries only, never from ``backend.main`` (no circular import). ``backend.main``
re-exports these names so existing call sites and tests referencing
``main.<name>`` (e.g. ``main._apply_xp_boost``) resolve to the same objects.
"""
from __future__ import annotations

import logging
import uuid as uuid_module
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from ..db import SessionLocal  # noqa: F401  (kept for parity / potential reuse)
from ..models import Badge, Certificate, User, UserBadge

logger = logging.getLogger("luuniensuki.api")

CERTIFICATE_ISSUER_NAME = "Lưu Niên Sử Kí"

XP_RANKS = [
    {"level": 1, "name": "Lính Mới", "xp": 0},
    {"level": 2, "name": "Thư Sinh", "xp": 500},
    {"level": 3, "name": "Tú Tài", "xp": 1500},
    {"level": 4, "name": "Cử Nhân", "xp": 3500},
    {"level": 5, "name": "Tiến Sĩ", "xp": 7000},
    {"level": 6, "name": "Thám Hoa", "xp": 12000},
    {"level": 7, "name": "Bảng Nhãn", "xp": 20000},
    {"level": 8, "name": "Trạng Nguyên", "xp": 35000},
    {"level": 9, "name": "Hàn Lâm", "xp": 55000},
    {"level": 10, "name": "Sử Quan", "xp": 80000},
]


def _compute_rank(total_xp: int) -> tuple[dict, Optional[dict], int]:
    current = XP_RANKS[0]
    for r in XP_RANKS:
        if total_xp >= r["xp"]:
            current = r
        else:
            break

    next_rank = None
    for r in XP_RANKS:
        if r["xp"] > current["xp"]:
            next_rank = r
            break

    if next_rank is None:
        return current, None, 0
    return current, next_rank, max(0, next_rank["xp"] - total_xp)


def _update_streak(user: User, now: datetime) -> None:
    if user.last_active_at is None:
        user.current_streak = max(user.current_streak, 1)
        user.longest_streak = max(user.longest_streak, user.current_streak)
        return

    last_date = user.last_active_at.astimezone(timezone.utc).date()
    today = now.astimezone(timezone.utc).date()
    diff_days = (today - last_date).days
    if diff_days <= 0:
        return

    if diff_days == 1:
        user.current_streak += 1
    else:
        user.current_streak = 1

    user.longest_streak = max(user.longest_streak, user.current_streak)


def _apply_xp_boost(user: User, base_xp: int, now: datetime) -> int:
    """
    Apply XP boost multiplier if active and not expired.

    Args:
        user: The user object
        base_xp: The base XP amount to be multiplied
        now: Current datetime

    Returns:
        The final XP amount (base_xp or base_xp * multiplier)
    """
    try:
        if not user.xp_boost_active:
            return base_xp

        if user.xp_boost_expires_at is None:
            # Boost active but no expiration set - deactivate it
            user.xp_boost_active = False
            return base_xp

        # Check if boost has expired
        if now >= user.xp_boost_expires_at:
            user.xp_boost_active = False
            user.xp_boost_expires_at = None
            return base_xp

        # Boost is active - apply multiplier. Coerce a null/unset multiplier to
        # the neutral value so that `None > 1` cannot raise a TypeError.
        multiplier = user.xp_boost_multiplier or 0
        return base_xp * (multiplier if multiplier > 1 else 2)
    except Exception:
        # XP application must never raise (Req 9.4) - fall back to base XP.
        logger.warning(
            "Failed to apply XP boost; falling back to base XP",
            extra={"user_id": str(getattr(user, "id", None))},
        )
        return base_xp


def _award_badge(session: Session, *, user: User, badge_slug: str) -> int:
    badge = session.execute(
        select(Badge).where(Badge.slug == badge_slug, Badge.is_active.is_(True))
    ).scalar_one_or_none()
    if badge is None:
        return 0

    existing = session.execute(
        select(UserBadge).where(
            UserBadge.user_id == user.id, UserBadge.badge_id == badge.id
        )
    ).scalar_one_or_none()
    if existing is not None:
        return 0

    try:
        with session.begin_nested():
            insert_stmt = (
                pg_insert(UserBadge)
                .values(user_id=user.id, badge_id=badge.id)
                .on_conflict_do_nothing(
                    index_elements=["user_id", "badge_id"],
                )
                .returning(UserBadge.id)
            )
            inserted = session.execute(insert_stmt).scalar_one_or_none()
    except Exception:
        logger.warning(
            "Failed to award badge",
            extra={"user_id": str(user.id), "badge_slug": badge_slug},
            exc_info=True,
        )
        return 0
    if inserted is None:
        return 0

    # Track first badge earned milestone
    badges_before = session.execute(
        select(func.count(UserBadge.id)).where(UserBadge.user_id == user.id)
    ).scalar_one()
    if badges_before <= 1:  # First badge (just inserted)
        from backend.services.milestones import check_and_create_first_badge_earned

        check_and_create_first_badge_earned(session, user.id, badge_slug)

    bonus = int(badge.xp_bonus or 0)
    if bonus:
        user.total_xp += bonus
    return bonus


def _issue_certificate(
    session: Session,
    *,
    user_id: UUID,
    reason_type: str,
    reason_id: UUID,
    issuer_name: str = CERTIFICATE_ISSUER_NAME,
) -> Certificate:
    existing = session.execute(
        select(Certificate).where(
            Certificate.user_id == user_id,
            Certificate.reason_type == reason_type,
            Certificate.reason_id == reason_id,
        )
    ).scalar_one_or_none()
    if existing is not None:
        return existing

    code = uuid_module.uuid4().hex
    certificate = Certificate(
        user_id=user_id,
        code=code,
        issuer_name=issuer_name,
        reason_type=reason_type,
        reason_id=reason_id,
        status="issued",
    )
    session.add(certificate)
    session.flush()
    return certificate
