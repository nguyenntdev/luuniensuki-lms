"""
Email Scheduler Service.

This module provides functions to:
1. Schedule daily digest and weekly summary emails
2. Generate digest content (streak status, missions, recommendations)
3. Render email templates with dynamic content
4. Send test emails
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from uuid import UUID

from jinja2 import Template
from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from backend.models import (
    DailyMission,
    EmailStatus,
    EmailTemplate,
    Recommendation,
    ScheduledEmail,
    User,
    UserDailyMission,
    UserProgress,
    UserWeeklyQuest,
    WeeklyQuest,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Template Rendering
# =============================================================================

def render_email_template(
    template: EmailTemplate,
    context: dict[str, Any]
) -> tuple[str, str, Optional[str]]:
    """
    Render an email template with given context data.
    
    Args:
        template: EmailTemplate instance
        context: Dictionary of template variables
        
    Returns:
        Tuple of (subject, body_html, body_text)
    """
    try:
        # Render subject
        subject_tmpl = Template(template.subject_template)
        subject = subject_tmpl.render(**context)
        
        # Render HTML body
        body_html_tmpl = Template(template.body_html)
        body_html = body_html_tmpl.render(**context)
        
        # Render text body if available
        body_text = None
        if template.body_text:
            body_text_tmpl = Template(template.body_text)
            body_text = body_text_tmpl.render(**context)
        
        return subject, body_html, body_text
    
    except Exception as e:
        logger.error(f"Error rendering email template {template.key}: {e}")
        raise ValueError(f"Failed to render template: {e}")


# =============================================================================
# Digest Content Generation
# =============================================================================

def generate_daily_digest_context(
    session: Session,
    user: User,
    date: Optional[datetime] = None
) -> dict[str, Any]:
    """
    Generate context data for daily digest email.
    
    Args:
        session: Database session
        user: User instance
        date: Optional date for digest (defaults to today)
        
    Returns:
        Dictionary with digest context data
    """
    if date is None:
        date = datetime.now(timezone.utc)
    
    # Get user's daily missions
    missions_query = (
        select(DailyMission, UserDailyMission)
        .outerjoin(
            UserDailyMission,
            and_(
                UserDailyMission.mission_id == DailyMission.id,
                UserDailyMission.user_id == user.id,
                func.date(UserDailyMission.completed_at) == date.date()
            )
        )
        .where(DailyMission.is_active == True)
    )
    
    missions = session.execute(missions_query).all()
    missions_completed = sum(1 for _, user_mission in missions if user_mission and user_mission.completed)
    missions_total = len(missions)
    
    # Get recommendations
    recommendations = session.execute(
        select(Recommendation)
        .where(Recommendation.user_id == user.id)
        .order_by(Recommendation.score.desc())
        .limit(3)
    ).scalars().all()

    # Get recent progress
    recent_progress = session.execute(
        select(UserProgress)
        .where(UserProgress.user_id == user.id)
        .order_by(UserProgress.discovered_at.desc())
        .limit(5)
    ).scalars().all()

    context = {
        "user_name": user.display_name or user.email.split("@")[0],
        "user_email": user.email,
        "streak_count": user.current_streak,
        "longest_streak": user.longest_streak,
        "total_xp": user.total_xp,
        "missions_completed": missions_completed,
        "missions_total": missions_total,
        "missions_pending": missions_total - missions_completed,
        "recommendations": [
            {
                "content_type": rec.content_type,
                "content_id": str(rec.content_id),
                "reason": rec.reason,
                "score": rec.score
            }
            for rec in recommendations
        ],
        "recent_progress": [
            {
                "motif_name": prog.motif.name if prog.motif else "Unknown",
                "status": prog.status.value,
                "discovered_at": prog.discovered_at
            }
            for prog in recent_progress
        ],
        "date": date.strftime("%Y-%m-%d"),
    }

    return context


def generate_weekly_summary_context(
    session: Session,
    user: User,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> dict[str, Any]:
    """
    Generate context data for weekly summary email.

    Args:
        session: Database session
        user: User instance
        start_date: Optional week start date
        end_date: Optional week end date

    Returns:
        Dictionary with weekly summary context data
    """
    if end_date is None:
        end_date = datetime.now(timezone.utc)

    if start_date is None:
        start_date = end_date - timedelta(days=7)

    # Get weekly quest progress
    weekly_quests_query = (
        select(WeeklyQuest, UserWeeklyQuest)
        .outerjoin(
            UserWeeklyQuest,
            and_(
                UserWeeklyQuest.quest_id == WeeklyQuest.id,
                UserWeeklyQuest.user_id == user.id
            )
        )
        .where(WeeklyQuest.is_active == True)
    )

    weekly_quests = session.execute(weekly_quests_query).all()
    quests_completed = sum(1 for _, user_quest in weekly_quests if user_quest and user_quest.completed)
    quests_total = len(weekly_quests)

    # Get progress for the week
    week_progress = session.execute(
        select(UserProgress)
        .where(
            and_(
                UserProgress.user_id == user.id,
                UserProgress.discovered_at >= start_date,
                UserProgress.discovered_at < end_date
            )
        )
    ).scalars().all()

    motifs_discovered = len(week_progress)
    motifs_learned = sum(1 for p in week_progress if p.learned_at is not None)
    motifs_mastered = sum(1 for p in week_progress if p.mastered_at is not None)

    context = {
        "user_name": user.display_name or user.email.split("@")[0],
        "user_email": user.email,
        "week_start": start_date.strftime("%Y-%m-%d"),
        "week_end": end_date.strftime("%Y-%m-%d"),
        "streak_count": user.current_streak,
        "longest_streak": user.longest_streak,
        "total_xp": user.total_xp,
        "quests_completed": quests_completed,
        "quests_total": quests_total,
        "motifs_discovered": motifs_discovered,
        "motifs_learned": motifs_learned,
        "motifs_mastered": motifs_mastered,
    }

    return context


# =============================================================================
# Email Scheduling
# =============================================================================

def schedule_email(
    session: Session,
    user_id: UUID,
    template_id: UUID,
    scheduled_for: datetime,
    context_data: Optional[dict[str, Any]] = None
) -> ScheduledEmail:
    """
    Schedule an email to be sent to a user.

    Args:
        session: Database session
        user_id: User ID
        template_id: Email template ID
        scheduled_for: When to send the email
        context_data: Template context variables

    Returns:
        Created ScheduledEmail instance
    """
    scheduled_email = ScheduledEmail(
        user_id=user_id,
        template_id=template_id,
        scheduled_for=scheduled_for,
        status=EmailStatus.pending,
        context_data=context_data or {}
    )

    session.add(scheduled_email)
    session.commit()
    session.refresh(scheduled_email)

    logger.info(f"Scheduled email {scheduled_email.id} for user {user_id} at {scheduled_for}")

    return scheduled_email


def schedule_daily_digest(
    session: Session,
    user_id: UUID,
    send_time: Optional[datetime] = None
) -> Optional[ScheduledEmail]:
    """
    Schedule a daily digest email for a user.

    Args:
        session: Database session
        user_id: User ID
        send_time: Optional send time (defaults to tomorrow 8 AM user's timezone)

    Returns:
        Created ScheduledEmail instance or None if template not found
    """
    # Get daily digest template
    template = session.execute(
        select(EmailTemplate)
        .where(
            and_(
                EmailTemplate.key == "daily_digest",
                EmailTemplate.is_active == True
            )
        )
    ).scalar_one_or_none()

    if not template:
        logger.warning("Daily digest template not found or inactive")
        return None

    # Get user
    user = session.get(User, user_id)
    if not user:
        logger.warning(f"User {user_id} not found")
        return None

    # Default send time: tomorrow at 8 AM UTC
    if send_time is None:
        now = datetime.now(timezone.utc)
        send_time = (now + timedelta(days=1)).replace(hour=8, minute=0, second=0, microsecond=0)

    # Generate context
    context = generate_daily_digest_context(session, user)

    # Schedule the email
    return schedule_email(session, user_id, template.id, send_time, context)


def schedule_weekly_summary(
    session: Session,
    user_id: UUID,
    send_time: Optional[datetime] = None
) -> Optional[ScheduledEmail]:
    """
    Schedule a weekly summary email for a user.

    Args:
        session: Database session
        user_id: User ID
        send_time: Optional send time (defaults to next Monday 9 AM)

    Returns:
        Created ScheduledEmail instance or None if template not found
    """
    # Get weekly summary template
    template = session.execute(
        select(EmailTemplate)
        .where(
            and_(
                EmailTemplate.key == "weekly_summary",
                EmailTemplate.is_active == True
            )
        )
    ).scalar_one_or_none()

    if not template:
        logger.warning("Weekly summary template not found or inactive")
        return None

    # Get user
    user = session.get(User, user_id)
    if not user:
        logger.warning(f"User {user_id} not found")
        return None

    # Default send time: next Monday at 9 AM UTC
    if send_time is None:
        now = datetime.now(timezone.utc)
        days_until_monday = (7 - now.weekday()) % 7
        if days_until_monday == 0:
            days_until_monday = 7
        send_time = (now + timedelta(days=days_until_monday)).replace(
            hour=9, minute=0, second=0, microsecond=0
        )

    # Generate context
    context = generate_weekly_summary_context(session, user)

    # Schedule the email
    return schedule_email(session, user_id, template.id, send_time, context)


# =============================================================================
# Email Status Management
# =============================================================================

def mark_email_sent(
    session: Session,
    email_id: UUID,
    sent_at: Optional[datetime] = None
) -> ScheduledEmail:
    """
    Mark a scheduled email as sent.

    Args:
        session: Database session
        email_id: Scheduled email ID
        sent_at: Optional send timestamp (defaults to now)

    Returns:
        Updated ScheduledEmail instance
    """
    email = session.get(ScheduledEmail, email_id)
    if not email:
        raise ValueError(f"Scheduled email {email_id} not found")

    email.status = EmailStatus.sent
    email.sent_at = sent_at or datetime.now(timezone.utc)
    email.error_message = None

    session.commit()
    session.refresh(email)

    logger.info(f"Marked email {email_id} as sent")

    return email


def mark_email_failed(
    session: Session,
    email_id: UUID,
    error_message: str
) -> ScheduledEmail:
    """
    Mark a scheduled email as failed.

    Args:
        session: Database session
        email_id: Scheduled email ID
        error_message: Error message describing the failure

    Returns:
        Updated ScheduledEmail instance
    """
    email = session.get(ScheduledEmail, email_id)
    if not email:
        raise ValueError(f"Scheduled email {email_id} not found")

    email.status = EmailStatus.failed
    email.error_message = error_message

    session.commit()
    session.refresh(email)

    logger.error(f"Marked email {email_id} as failed: {error_message}")

    return email


def cancel_scheduled_email(
    session: Session,
    email_id: UUID
) -> ScheduledEmail:
    """
    Cancel a scheduled email.

    Args:
        session: Database session
        email_id: Scheduled email ID

    Returns:
        Updated ScheduledEmail instance
    """
    email = session.get(ScheduledEmail, email_id)
    if not email:
        raise ValueError(f"Scheduled email {email_id} not found")

    if email.status != EmailStatus.pending:
        raise ValueError(f"Can only cancel pending emails, email is {email.status}")

    email.status = EmailStatus.cancelled

    session.commit()
    session.refresh(email)

    logger.info(f"Cancelled scheduled email {email_id}")

    return email


# =============================================================================
# Batch Operations
# =============================================================================

def schedule_daily_digests_for_all_users(
    session: Session,
    send_time: Optional[datetime] = None
) -> list[ScheduledEmail]:
    """
    Schedule daily digest emails for all active users.

    Args:
        session: Database session
        send_time: Optional send time

    Returns:
        List of created ScheduledEmail instances
    """
    users = session.execute(
        select(User)
        .where(User.role != "guest")
    ).scalars().all()

    scheduled_emails = []
    for user in users:
        try:
            email = schedule_daily_digest(session, user.id, send_time)
            if email:
                scheduled_emails.append(email)
        except Exception as e:
            logger.error(f"Failed to schedule daily digest for user {user.id}: {e}")

    logger.info(f"Scheduled {len(scheduled_emails)} daily digest emails")

    return scheduled_emails


def schedule_weekly_summaries_for_all_users(
    session: Session,
    send_time: Optional[datetime] = None
) -> list[ScheduledEmail]:
    """
    Schedule weekly summary emails for all active users.

    Args:
        session: Database session
        send_time: Optional send time

    Returns:
        List of created ScheduledEmail instances
    """
    users = session.execute(
        select(User)
        .where(User.role != "guest")
    ).scalars().all()

    scheduled_emails = []
    for user in users:
        try:
            email = schedule_weekly_summary(session, user.id, send_time)
            if email:
                scheduled_emails.append(email)
        except Exception as e:
            logger.error(f"Failed to schedule weekly summary for user {user.id}: {e}")

    logger.info(f"Scheduled {len(scheduled_emails)} weekly summary emails")

    return scheduled_emails

