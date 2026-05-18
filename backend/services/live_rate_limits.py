"""Persistent rate limiting for live endpoints (DB-backed)."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, delete, func, select
from sqlalchemy.orm import Session

from ..models import LiveRateLimitLog


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def check_and_record(
    db: Session,
    *,
    bucket: str,
    user_id: uuid.UUID,
    max_requests: int,
    window_seconds: int,
    live_session_id: uuid.UUID | None = None,
) -> None:
    now = _utcnow()
    window_start = now - timedelta(seconds=max(1, int(window_seconds or 1)))

    # Opportunistic cleanup keeps table small without separate job dependency.
    db.execute(
        delete(LiveRateLimitLog).where(
            LiveRateLimitLog.created_at < (now - timedelta(hours=6))
        )
    )

    query = select(func.count(LiveRateLimitLog.id)).where(
        and_(
            LiveRateLimitLog.bucket == bucket,
            LiveRateLimitLog.user_id == user_id,
            LiveRateLimitLog.created_at >= window_start,
        )
    )
    if live_session_id is not None:
        query = query.where(LiveRateLimitLog.live_session_id == live_session_id)

    count = int(db.execute(query).scalar_one() or 0)
    if count >= max(1, int(max_requests or 1)):
        raise RuntimeError(
            f"Rate limit exceeded for {bucket} ({count}/{max_requests} in {window_seconds}s)"
        )

    db.add(
        LiveRateLimitLog(
            bucket=bucket,
            user_id=user_id,
            live_session_id=live_session_id,
        )
    )
    db.flush()


def cleanup_old_logs(db: Session, *, max_age_hours: int = 6) -> int:
    cutoff = _utcnow() - timedelta(hours=max(1, int(max_age_hours or 1)))
    result = db.execute(
        delete(LiveRateLimitLog).where(LiveRateLimitLog.created_at < cutoff)
    )
    return int(result.rowcount or 0)
