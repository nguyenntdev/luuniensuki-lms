"""
Audit logging service for tracking all system changes and sensitive operations.

This service provides functions for:
- Recording audit events
- Retrieving audit logs with filtering
- Getting user-specific audit trails
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models import AuditLog, User


def log_action(
    db: Session,
    *,
    user_id: Optional[uuid.UUID],
    action: str,
    resource_type: str,
    resource_id: Optional[uuid.UUID] = None,
    old_value: Optional[dict[str, Any]] = None,
    new_value: Optional[dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> AuditLog:
    """
    Record an audit event.
    
    Args:
        db: Database session
        user_id: ID of user performing the action (None for system actions)
        action: Action type (create, update, delete, view, ai_request, login, logout, role_change)
        resource_type: Type of resource (lesson, quiz, rag_document, user, settings, auth, ai_generation)
        resource_id: ID of the affected resource
        old_value: Previous state (for updates/deletes)
        new_value: New state (for creates/updates)
        ip_address: Client IP address
        user_agent: Client user agent string
        
    Returns:
        Created AuditLog instance
    """
    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        old_value=old_value,
        new_value=new_value,
        ip_address=ip_address,
        user_agent=user_agent,
        created_at=datetime.now(timezone.utc),
    )
    db.add(audit_log)
    db.flush()
    return audit_log


def get_audit_logs(
    db: Session,
    *,
    user_id: Optional[uuid.UUID] = None,
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[uuid.UUID] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    page: int = 1,
    page_size: int = 50,
) -> tuple[list[AuditLog], int]:
    """
    Retrieve audit logs with filtering.
    
    Args:
        db: Database session
        user_id: Filter by user ID
        action: Filter by action type
        resource_type: Filter by resource type
        resource_id: Filter by specific resource
        start_date: Filter by start date
        end_date: Filter by end date
        page: Page number (1-indexed)
        page_size: Items per page
        
    Returns:
        Tuple of (logs list, total count)
    """
    query = select(AuditLog)
    
    # Apply filters
    if user_id:
        query = query.where(AuditLog.user_id == user_id)
    if action:
        query = query.where(AuditLog.action == action)
    if resource_type:
        query = query.where(AuditLog.resource_type == resource_type)
    if resource_id:
        query = query.where(AuditLog.resource_id == resource_id)
    if start_date:
        query = query.where(AuditLog.created_at >= start_date)
    if end_date:
        query = query.where(AuditLog.created_at <= end_date)
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = db.execute(count_query).scalar_one()
    
    # Apply pagination and ordering
    query = query.order_by(AuditLog.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    logs = list(db.execute(query).scalars().all())
    
    return logs, total


def get_user_audit_trail(
    db: Session,
    user_id: uuid.UUID,
    page: int = 1,
    page_size: int = 50,
) -> tuple[list[AuditLog], int]:
    """
    Get complete audit trail for a specific user.
    
    Args:
        db: Database session
        user_id: User ID to get trail for
        page: Page number (1-indexed)
        page_size: Items per page
        
    Returns:
        Tuple of (logs list, total count)
    """
    return get_audit_logs(db, user_id=user_id, page=page, page_size=page_size)

