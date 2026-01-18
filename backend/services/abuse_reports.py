"""
Service for handling abuse reports and notifications.

This module provides functionality for:
- Creating and managing abuse reports
- Assigning reports to admin users
- Resolving reports
- Notifying admins about high/critical priority reports
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.models import AbuseReport, User, UserRole


def create_abuse_report(
    db: Session,
    reporter_id: UUID,
    reported_user_id: Optional[UUID],
    content_type: str,
    content_id: Optional[UUID],
    reason: str,
    description: str,
    evidence_urls: Optional[list[str]] = None,
) -> AbuseReport:
    """
    Create a new abuse report.

    Automatically determines priority based on reason and content type.
    Notifies admins if priority is high or critical.

    Args:
        db: Database session
        reporter_id: ID of user filing the report
        reported_user_id: ID of user being reported (optional)
        content_type: Type of content (comment, review, profile, message, other)
        content_id: ID of the specific content
        reason: Reason for report (harassment, spam, inappropriate, copyright, other)
        description: Detailed description from reporter
        evidence_urls: Optional list of evidence URLs

    Returns:
        Created AbuseReport instance
    """
    # Determine priority based on reason
    priority = _determine_priority(reason, content_type)

    report = AbuseReport(
        reporter_id=reporter_id,
        reported_user_id=reported_user_id,
        content_type=content_type,
        content_id=content_id,
        reason=reason,
        description=description,
        evidence_urls=evidence_urls,
        status="pending",
        priority=priority,
        created_at=datetime.now(timezone.utc),
    )

    db.add(report)
    db.flush()

    # Notify admins if high or critical priority
    if priority in ["high", "critical"]:
        _notify_admins_of_report(db, report)

    return report


def _determine_priority(reason: str, content_type: str) -> str:
    """
    Determine priority level based on reason and content type.

    Args:
        reason: Reason for report
        content_type: Type of content

    Returns:
        Priority level (low, medium, high, critical)
    """
    # Critical: harassment or threats
    if reason == "harassment":
        return "critical"

    # High: copyright or inappropriate on profiles
    if reason == "copyright":
        return "high"
    if reason == "inappropriate" and content_type == "profile":
        return "high"

    # Medium: spam or inappropriate on other content
    if reason in ["spam", "inappropriate"]:
        return "medium"

    # Low: other reasons
    return "low"


def _notify_admins_of_report(db: Session, report: AbuseReport) -> None:
    """
    Notify admin users about a new high/critical priority report.

    This is a placeholder for actual notification implementation.
    In production, this would:
    - Send email notifications
    - Send push notifications
    - Create in-app notifications
    - Log to admin dashboard

    Args:
        db: Database session
        report: The abuse report to notify about
    """
    # Get all admin and super_admin users
    admins = (
        db.execute(
            select(User).where(User.role.in_([UserRole.admin, UserRole.super_admin]))
        )
        .scalars()
        .all()
    )

    from . import push_notifications

    title = f"New {report.priority} abuse report"
    body = f"Report {report.id} requires review."
    data = {
        "report_id": str(report.id),
        "priority": report.priority,
        "content_type": report.content_type,
    }

    for admin in admins:
        push_notifications.send_system_notification(
            db=db,
            user_id=admin.id,
            title=title,
            body=body,
            data=data,
        )


def assign_abuse_report(
    db: Session,
    report_id: UUID,
    assigned_to_id: UUID,
) -> AbuseReport:
    """
    Assign an abuse report to an admin user.

    Args:
        db: Database session
        report_id: ID of the report to assign
        assigned_to_id: ID of admin user to assign to

    Returns:
        Updated AbuseReport instance

    Raises:
        ValueError: If report not found or assignee is not an admin
    """
    report = db.execute(
        select(AbuseReport).where(AbuseReport.id == report_id)
    ).scalar_one_or_none()

    if not report:
        raise ValueError("Report not found")

    # Verify assignee is an admin
    assignee = db.execute(
        select(User).where(User.id == assigned_to_id)
    ).scalar_one_or_none()

    if not assignee or assignee.role not in [UserRole.admin, UserRole.super_admin]:
        raise ValueError("Assignee must be an admin user")

    report.assigned_to_id = assigned_to_id
    if report.status == "pending":
        report.status = "reviewing"

    db.flush()
    return report


def resolve_abuse_report(
    db: Session,
    report_id: UUID,
    status: str,
    resolution_notes: str,
) -> AbuseReport:
    """
    Resolve an abuse report.

    Args:
        db: Database session
        report_id: ID of the report to resolve
        status: New status (resolved or dismissed)
        resolution_notes: Notes about the resolution

    Returns:
        Updated AbuseReport instance

    Raises:
        ValueError: If report not found or invalid status
    """
    if status not in ["resolved", "dismissed"]:
        raise ValueError("Status must be 'resolved' or 'dismissed'")

    report = db.execute(
        select(AbuseReport).where(AbuseReport.id == report_id)
    ).scalar_one_or_none()

    if not report:
        raise ValueError("Report not found")

    report.status = status
    report.resolution_notes = resolution_notes
    report.resolved_at = datetime.now(timezone.utc)

    db.flush()
    return report
