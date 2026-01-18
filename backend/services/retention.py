"""
Retention Analytics Service.

This module provides functions to calculate user retention metrics
including D1, D7, D30 retention rates, cohort analysis, and retention curves.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import func, select, and_, distinct
from sqlalchemy.orm import Session

from backend.models import AnalyticsEvent, User


# =============================================================================
# Helper Functions
# =============================================================================

def _get_cohort_from_date(created_at: datetime, period: str = "week") -> str:
    """
    Generate cohort identifier from user registration date.
    
    Args:
        created_at: User registration datetime
        period: 'week' or 'month'
        
    Returns:
        Cohort identifier string (e.g., "2024-W01" or "2024-01")
    """
    if period == "week":
        year, week, _ = created_at.isocalendar()
        return f"{year}-W{week:02d}"
    else:  # month
        return created_at.strftime("%Y-%m")


def _check_user_active_on_day(
    session: Session,
    user_id: UUID,
    target_date: datetime,
    window_hours: int = 12
) -> bool:
    """
    Check if a user had any activity on a specific day (within a time window).
    
    Args:
        session: Database session
        user_id: User ID to check
        target_date: Target date to check activity
        window_hours: Time window in hours around target date
        
    Returns:
        True if user had activity, False otherwise
    """
    start_window = target_date - timedelta(hours=window_hours)
    end_window = target_date + timedelta(hours=window_hours)
    
    event_exists = session.execute(
        select(AnalyticsEvent.id)
        .where(
            and_(
                AnalyticsEvent.user_id == user_id,
                AnalyticsEvent.created_at >= start_window,
                AnalyticsEvent.created_at <= end_window
            )
        )
        .limit(1)
    ).first()
    
    return event_exists is not None


# =============================================================================
# Retention Metrics
# =============================================================================

def calculate_overall_retention(
    session: Session,
    days_ago: Optional[int] = None
) -> dict[str, Any]:
    """
    Calculate overall D1, D7, D30 retention rates.
    
    Args:
        session: Database session
        days_ago: Optional number of days to look back for user cohort
        
    Returns:
        Dictionary with overall retention metrics
    """
    now = datetime.now(timezone.utc)
    
    # Build user query
    user_query = select(User.id, User.created_at)
    
    if days_ago:
        cutoff_date = now - timedelta(days=days_ago)
        user_query = user_query.where(User.created_at >= cutoff_date)
    
    users = session.execute(user_query).all()
    
    if not users:
        return {
            "d1_retention": 0.0,
            "d7_retention": 0.0,
            "d30_retention": 0.0,
            "total_users": 0,
            "date_range": {
                "start": (now - timedelta(days=days_ago)).isoformat() if days_ago else None,
                "end": now.isoformat()
            }
        }
    
    total_users = len(users)
    retention_counts = {1: 0, 7: 0, 30: 0}
    
    # Calculate retention for each day threshold
    for user_id, created_at in users:
        for day in [1, 7, 30]:
            # Only check retention for users who have been around long enough
            if (now - created_at).days >= day:
                target_date = created_at + timedelta(days=day)
                if _check_user_active_on_day(session, user_id, target_date):
                    retention_counts[day] += 1
    
    # Calculate eligible users for each retention period
    eligible_users = {
        day: len([u for u in users if (now - u[1]).days >= day])
        for day in [1, 7, 30]
    }
    
    return {
        "d1_retention": round((retention_counts[1] / eligible_users[1] * 100) if eligible_users[1] > 0 else 0, 2),
        "d7_retention": round((retention_counts[7] / eligible_users[7] * 100) if eligible_users[7] > 0 else 0, 2),
        "d30_retention": round((retention_counts[30] / eligible_users[30] * 100) if eligible_users[30] > 0 else 0, 2),
        "total_users": total_users,
        "eligible_users": eligible_users,
        "date_range": {
            "start": (now - timedelta(days=days_ago)).isoformat() if days_ago else None,
            "end": now.isoformat()
        }
    }


def calculate_cohort_retention(
    session: Session,
    period: str = "week",
    limit: int = 12
) -> dict[str, Any]:
    """
    Calculate retention rates grouped by signup cohort.

    Args:
        session: Database session
        period: 'week' or 'month' for cohort grouping
        limit: Maximum number of cohorts to return

    Returns:
        Dictionary with cohort-based retention data
    """
    now = datetime.now(timezone.utc)

    # Get all users
    users = session.execute(
        select(User.id, User.created_at)
        .order_by(User.created_at.desc())
    ).all()

    if not users:
        return {"cohorts": [], "period": period}

    # Group users by cohort
    cohort_users: dict[str, list[tuple[UUID, datetime]]] = {}
    for user_id, created_at in users:
        cohort = _get_cohort_from_date(created_at, period)
        if cohort not in cohort_users:
            cohort_users[cohort] = []
        cohort_users[cohort].append((user_id, created_at))

    # Calculate retention for each cohort
    cohort_data = []

    for cohort, cohort_user_list in sorted(cohort_users.items(), reverse=True)[:limit]:
        cohort_size = len(cohort_user_list)
        retention_counts = {1: 0, 7: 0, 30: 0}
        eligible_counts = {1: 0, 7: 0, 30: 0}

        for user_id, created_at in cohort_user_list:
            for day in [1, 7, 30]:
                # Check if user has been around long enough
                if (now - created_at).days >= day:
                    eligible_counts[day] += 1
                    target_date = created_at + timedelta(days=day)
                    if _check_user_active_on_day(session, user_id, target_date):
                        retention_counts[day] += 1

        cohort_data.append({
            "cohort": cohort,
            "signup_count": cohort_size,
            "d1_retention": round((retention_counts[1] / eligible_counts[1] * 100) if eligible_counts[1] > 0 else 0, 2),
            "d7_retention": round((retention_counts[7] / eligible_counts[7] * 100) if eligible_counts[7] > 0 else 0, 2),
            "d30_retention": round((retention_counts[30] / eligible_counts[30] * 100) if eligible_counts[30] > 0 else 0, 2),
            "eligible_d1": eligible_counts[1],
            "eligible_d7": eligible_counts[7],
            "eligible_d30": eligible_counts[30]
        })

    return {
        "cohorts": cohort_data,
        "period": period
    }


def calculate_retention_curve(
    session: Session,
    days: int = 30,
    cohort_days_ago: int = 90
) -> dict[str, Any]:
    """
    Calculate retention curve data points for visualization.

    Returns retention rate for each day from day 0 to specified day count.

    Args:
        session: Database session
        days: Number of days to calculate (default 30)
        cohort_days_ago: How far back to include users (default 90)

    Returns:
        Dictionary with retention curve data points
    """
    now = datetime.now(timezone.utc)
    cutoff_date = now - timedelta(days=cohort_days_ago)

    # Get users who signed up within the cohort period
    users = session.execute(
        select(User.id, User.created_at)
        .where(User.created_at >= cutoff_date)
    ).all()

    if not users:
        return {
            "data_points": [],
            "total_users": 0,
            "days": days
        }

    total_users = len(users)
    data_points = []

    # Calculate retention for each day
    for day in range(0, days + 1):
        retained_count = 0
        eligible_count = 0

        for user_id, created_at in users:
            # Check if user has been around long enough
            if (now - created_at).days >= day:
                eligible_count += 1

                if day == 0:
                    # Day 0 is 100% by definition (signup day)
                    retained_count += 1
                else:
                    target_date = created_at + timedelta(days=day)
                    if _check_user_active_on_day(session, user_id, target_date):
                        retained_count += 1

        retention_rate = round((retained_count / eligible_count * 100) if eligible_count > 0 else 0, 2)

        data_points.append({
            "day": day,
            "retention_rate": retention_rate,
            "retained_users": retained_count,
            "eligible_users": eligible_count
        })

    return {
        "data_points": data_points,
        "total_users": total_users,
        "days": days,
        "cohort_period": {
            "start": cutoff_date.isoformat(),
            "end": now.isoformat()
        }
    }

