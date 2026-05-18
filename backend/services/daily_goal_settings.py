"""Daily-goal settings domain/service helpers."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import AnalyticsEvent
from .analytics import create_event_record

DAILY_GOAL_LEVELS: dict[str, int] = {
    "CASUAL": 10,
    "REGULAR": 20,
    "SERIOUS": 30,
    "INTENSE": 50,
    "INSANE": 100,
}
DAILY_GOAL_DEFAULT_LEVEL = "REGULAR"


def resolve_daily_goal_level(
    *,
    goal_level: str | None = None,
    xp_target: int | None = None,
) -> str:
    """Resolve normalized goal level from either level key or XP target."""
    if goal_level:
        normalized = goal_level.strip().upper()
        if normalized in DAILY_GOAL_LEVELS:
            return normalized
        raise HTTPException(
            status_code=422,
            detail=f"Invalid goal_level. Must be one of: {', '.join(DAILY_GOAL_LEVELS.keys())}",
        )

    if xp_target is None:
        raise HTTPException(
            status_code=422,
            detail="Either goal_level or xp_target is required",
        )

    for level, xp in DAILY_GOAL_LEVELS.items():
        if xp == xp_target:
            return level

    allowed_xp = ", ".join(str(xp) for xp in DAILY_GOAL_LEVELS.values())
    raise HTTPException(
        status_code=422,
        detail=f"Invalid xp_target. Must be one of: {allowed_xp}",
    )


def get_user_daily_goal_settings(
    db: Session,
    *,
    user_id: UUID,
    fallback_updated_at: datetime,
) -> dict[str, Any]:
    """Get latest daily-goal settings for user from analytics events."""
    latest_event = (
        db.execute(
            select(AnalyticsEvent)
            .where(
                AnalyticsEvent.user_id == user_id,
                AnalyticsEvent.event_name == "daily_goal_settings_updated",
            )
            .order_by(AnalyticsEvent.created_at.desc())
        )
        .scalars()
        .first()
    )

    if latest_event is None:
        return {
            "goal_level": DAILY_GOAL_DEFAULT_LEVEL,
            "xp_target": DAILY_GOAL_LEVELS[DAILY_GOAL_DEFAULT_LEVEL],
            "updated_at": fallback_updated_at,
            "source": "default",
        }

    payload = latest_event.payload if isinstance(latest_event.payload, dict) else {}
    level = str(payload.get("goal_level") or DAILY_GOAL_DEFAULT_LEVEL).strip().upper()
    if level not in DAILY_GOAL_LEVELS:
        level = DAILY_GOAL_DEFAULT_LEVEL

    return {
        "goal_level": level,
        "xp_target": DAILY_GOAL_LEVELS[level],
        "updated_at": latest_event.created_at,
        "source": "server",
    }


def save_user_daily_goal_settings(
    db: Session,
    *,
    user_id: UUID,
    goal_level: str,
) -> dict[str, Any]:
    """Persist daily-goal settings as an analytics event."""
    now = datetime.now(timezone.utc)
    normalized_level = resolve_daily_goal_level(goal_level=goal_level)
    xp_target = DAILY_GOAL_LEVELS[normalized_level]

    event_data = create_event_record(
        user_id=user_id,
        event_name="daily_goal_settings_updated",
        payload={
            "goal_level": normalized_level,
            "xp_target": xp_target,
            "updated_at": now.isoformat(),
        },
        path="/api/v1/daily-goal/settings",
    )

    db.add(AnalyticsEvent(**event_data))
    db.commit()

    return {
        "goal_level": normalized_level,
        "xp_target": xp_target,
        "updated_at": now,
        "source": "server",
    }
