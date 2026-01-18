"""
Analytics Dashboard Service for KPI Metrics.

This module provides functions to calculate key performance indicators (KPIs)
for the analytics dashboard, including retention metrics, completion rates,
and engagement statistics.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import func, select, and_, distinct
from sqlalchemy.orm import Session

from backend.models import (
    AnalyticsEvent,
    User,
    UserProgress,
    QuizAttempt,
    UnlockStatus,
)


# =============================================================================
# Helper Functions
# =============================================================================

def _get_cohort_from_date(created_at: datetime) -> str:
    """
    Generate cohort identifier from user registration date.
    Format: YYYY-Www (e.g., "2024-W01")
    
    Args:
        created_at: User registration datetime
        
    Returns:
        Cohort identifier string
    """
    # Get ISO week number
    year, week, _ = created_at.isocalendar()
    return f"{year}-W{week:02d}"


def _get_date_range(days_ago: int) -> tuple[datetime, datetime]:
    """
    Get date range from N days ago to now.
    
    Args:
        days_ago: Number of days to look back
        
    Returns:
        Tuple of (start_date, end_date)
    """
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=days_ago)
    return start, now


# =============================================================================
# Retention Metrics
# =============================================================================

def calculate_retention_by_cohort(
    session: Session,
    cohort: Optional[str] = None,
    days: list[int] = [1, 7, 30]
) -> dict[str, Any]:
    """
    Calculate D1, D7, D30 retention rates by cohort.
    
    Retention is defined as users who had at least one event on day N
    after their registration.
    
    Args:
        session: Database session
        cohort: Optional specific cohort to analyze (e.g., "2024-W01")
        days: List of days to calculate retention for
        
    Returns:
        Dictionary with retention metrics per cohort
    """
    # Get all users with their registration dates
    user_query = select(User.id, User.created_at)
    if cohort:
        # Filter by cohort if specified
        user_query = user_query.where(
            func.to_char(User.created_at, 'IYYY-"W"IW') == cohort
        )
    
    users = session.execute(user_query).all()
    
    if not users:
        return {"cohorts": {}, "overall": {}}
    
    # Group users by cohort
    cohort_users: dict[str, list[tuple[UUID, datetime]]] = {}
    for user_id, created_at in users:
        user_cohort = _get_cohort_from_date(created_at)
        if user_cohort not in cohort_users:
            cohort_users[user_cohort] = []
        cohort_users[user_cohort].append((user_id, created_at))
    
    # Calculate retention for each cohort
    cohort_metrics = {}
    
    for cohort_name, cohort_user_list in cohort_users.items():
        cohort_size = len(cohort_user_list)
        retention_data = {"cohort_size": cohort_size}
        
        for day in days:
            retained_count = 0
            
            for user_id, created_at in cohort_user_list:
                # Check if user had activity on day N (±12 hours window)
                target_date = created_at + timedelta(days=day)
                start_window = target_date - timedelta(hours=12)
                end_window = target_date + timedelta(hours=12)
                
                # Check for any event in the window
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
                
                if event_exists:
                    retained_count += 1
            
            retention_rate = (retained_count / cohort_size * 100) if cohort_size > 0 else 0
            retention_data[f"d{day}_retained"] = retained_count
            retention_data[f"d{day}_rate"] = round(retention_rate, 2)
        
        cohort_metrics[cohort_name] = retention_data
    
    # Calculate overall retention across all cohorts
    overall = {"total_users": len(users)}
    for day in days:
        total_retained = sum(m.get(f"d{day}_retained", 0) for m in cohort_metrics.values())
        overall_rate = (total_retained / len(users) * 100) if len(users) > 0 else 0
        overall[f"d{day}_retained"] = total_retained
        overall[f"d{day}_rate"] = round(overall_rate, 2)
    
    return {
        "cohorts": cohort_metrics,
        "overall": overall
    }


# =============================================================================
# Completion Rate Metrics
# =============================================================================

def calculate_completion_rates(
    session: Session,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> dict[str, Any]:
    """
    Calculate lesson and quiz completion rates.

    Args:
        session: Database session
        start_date: Optional start date for the period
        end_date: Optional end date for the period

    Returns:
        Dictionary with completion rate metrics
    """
    if not start_date:
        start_date = datetime.now(timezone.utc) - timedelta(days=30)
    if not end_date:
        end_date = datetime.now(timezone.utc)

    # Lesson completion rate
    # Count motifs with status 'learned' (lesson completed but not quiz)
    lesson_started = session.execute(
        select(func.count(distinct(UserProgress.motif_id)))
        .where(
            and_(
                UserProgress.lesson_viewed_at.isnot(None),
                UserProgress.lesson_viewed_at >= start_date,
                UserProgress.lesson_viewed_at <= end_date
            )
        )
    ).scalar() or 0

    lesson_completed = session.execute(
        select(func.count(distinct(UserProgress.motif_id)))
        .where(
            and_(
                UserProgress.lesson_completed_at.isnot(None),
                UserProgress.lesson_completed_at >= start_date,
                UserProgress.lesson_completed_at <= end_date
            )
        )
    ).scalar() or 0

    lesson_completion_rate = (
        (lesson_completed / lesson_started * 100) if lesson_started > 0 else 0
    )

    # Quiz completion rate
    # Count motifs where quiz was started vs completed
    quiz_started_count = session.execute(
        select(func.count(distinct(QuizAttempt.motif_id)))
        .where(
            and_(
                QuizAttempt.submitted_at >= start_date,
                QuizAttempt.submitted_at <= end_date
            )
        )
    ).scalar() or 0

    quiz_passed_count = session.execute(
        select(func.count(distinct(QuizAttempt.motif_id)))
        .where(
            and_(
                QuizAttempt.passed.is_(True),
                QuizAttempt.submitted_at >= start_date,
                QuizAttempt.submitted_at <= end_date
            )
        )
    ).scalar() or 0

    quiz_completion_rate = (
        (quiz_passed_count / quiz_started_count * 100) if quiz_started_count > 0 else 0
    )

    # Mastery rate (completed both lesson and quiz)
    mastered_count = session.execute(
        select(func.count(distinct(UserProgress.motif_id)))
        .where(
            and_(
                UserProgress.status == UnlockStatus.mastered,
                UserProgress.mastered_at >= start_date,
                UserProgress.mastered_at <= end_date
            )
        )
    ).scalar() or 0

    return {
        "period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat()
        },
        "lessons": {
            "started": lesson_started,
            "completed": lesson_completed,
            "completion_rate": round(lesson_completion_rate, 2)
        },
        "quizzes": {
            "started": quiz_started_count,
            "passed": quiz_passed_count,
            "pass_rate": round(quiz_completion_rate, 2)
        },
        "mastery": {
            "total_mastered": mastered_count
        }
    }


# =============================================================================
# Engagement Metrics (WAU/MAU)
# =============================================================================

def calculate_engagement_metrics(
    session: Session
) -> dict[str, Any]:
    """
    Calculate Weekly Active Users (WAU) and Monthly Active Users (MAU).

    Active user is defined as a user who had at least one event.

    Args:
        session: Database session

    Returns:
        Dictionary with WAU and MAU metrics
    """
    now = datetime.now(timezone.utc)

    # Weekly Active Users (last 7 days)
    week_start = now - timedelta(days=7)
    wau = session.execute(
        select(func.count(distinct(AnalyticsEvent.user_id)))
        .where(AnalyticsEvent.created_at >= week_start)
    ).scalar() or 0

    # Monthly Active Users (last 30 days)
    month_start = now - timedelta(days=30)
    mau = session.execute(
        select(func.count(distinct(AnalyticsEvent.user_id)))
        .where(AnalyticsEvent.created_at >= month_start)
    ).scalar() or 0

    # Daily Active Users (last 24 hours)
    day_start = now - timedelta(days=1)
    dau = session.execute(
        select(func.count(distinct(AnalyticsEvent.user_id)))
        .where(AnalyticsEvent.created_at >= day_start)
    ).scalar() or 0

    # Stickiness ratio (DAU/MAU)
    stickiness = (dau / mau * 100) if mau > 0 else 0

    return {
        "dau": dau,
        "wau": wau,
        "mau": mau,
        "stickiness_ratio": round(stickiness, 2),
        "calculated_at": now.isoformat()
    }


# =============================================================================
# Event Summary
# =============================================================================

def aggregate_events_by_type(
    session: Session,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    event_category: Optional[str] = None
) -> dict[str, Any]:
    """
    Aggregate analytics events by type and date.

    Args:
        session: Database session
        start_date: Optional start date for the period
        end_date: Optional end date for the period
        event_category: Optional category filter

    Returns:
        Dictionary with event aggregations
    """
    if not start_date:
        start_date = datetime.now(timezone.utc) - timedelta(days=30)
    if not end_date:
        end_date = datetime.now(timezone.utc)

    # Build base query
    query = select(
        AnalyticsEvent.event_name,
        AnalyticsEvent.event_category,
        func.count(AnalyticsEvent.id).label('count'),
        func.count(distinct(AnalyticsEvent.user_id)).label('unique_users')
    ).where(
        and_(
            AnalyticsEvent.created_at >= start_date,
            AnalyticsEvent.created_at <= end_date
        )
    )

    if event_category:
        query = query.where(AnalyticsEvent.event_category == event_category)

    query = query.group_by(
        AnalyticsEvent.event_name,
        AnalyticsEvent.event_category
    ).order_by(func.count(AnalyticsEvent.id).desc())

    results = session.execute(query).all()

    # Organize by category
    by_category: dict[str, list[dict[str, Any]]] = {}
    total_events = 0
    total_unique_users = set()

    for event_name, category, count, unique_users in results:
        if category not in by_category:
            by_category[category or "uncategorized"] = []

        by_category[category or "uncategorized"].append({
            "event_name": event_name,
            "count": count,
            "unique_users": unique_users
        })
        total_events += count

    # Get unique users across all events in period
    total_unique_users_count = session.execute(
        select(func.count(distinct(AnalyticsEvent.user_id)))
        .where(
            and_(
                AnalyticsEvent.created_at >= start_date,
                AnalyticsEvent.created_at <= end_date
            )
        )
    ).scalar() or 0

    return {
        "period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat()
        },
        "summary": {
            "total_events": total_events,
            "unique_users": total_unique_users_count,
            "categories": len(by_category)
        },
        "by_category": by_category
    }


# =============================================================================
# Overall KPIs
# =============================================================================

def get_overall_kpis(
    session: Session
) -> dict[str, Any]:
    """
    Get overall platform KPIs.

    Args:
        session: Database session

    Returns:
        Dictionary with overall KPIs
    """
    now = datetime.now(timezone.utc)

    # User metrics
    total_users = session.execute(
        select(func.count(User.id))
    ).scalar() or 0

    # Active users (last 30 days)
    month_start = now - timedelta(days=30)
    active_users = session.execute(
        select(func.count(distinct(AnalyticsEvent.user_id)))
        .where(AnalyticsEvent.created_at >= month_start)
    ).scalar() or 0

    # Content engagement
    total_lessons_completed = session.execute(
        select(func.count(UserProgress.id))
        .where(UserProgress.lesson_completed_at.isnot(None))
    ).scalar() or 0

    total_quizzes_passed = session.execute(
        select(func.count(QuizAttempt.id))
        .where(QuizAttempt.passed.is_(True))
    ).scalar() or 0

    total_motifs_mastered = session.execute(
        select(func.count(UserProgress.id))
        .where(UserProgress.status == UnlockStatus.mastered)
    ).scalar() or 0

    # Engagement metrics
    engagement = calculate_engagement_metrics(session)

    return {
        "users": {
            "total": total_users,
            "active_30d": active_users,
            "activity_rate": round((active_users / total_users * 100) if total_users > 0 else 0, 2)
        },
        "content": {
            "lessons_completed": total_lessons_completed,
            "quizzes_passed": total_quizzes_passed,
            "motifs_mastered": total_motifs_mastered
        },
        "engagement": engagement,
        "calculated_at": now.isoformat()
    }


