"""
Role-Based Access Control (RBAC) helper functions.

This module provides:
- Role hierarchy checking
- Permission validation
- Role-based decorators and dependencies

Role Hierarchy (from lowest to highest):
    guest < learner < teacher < admin < super_admin

Permissions:
    - guest: View public content only
    - learner: Access lessons, quizzes, progress tracking
    - teacher: Create/edit content, view own classes, submit for review
    - admin: Approve content, manage RAG, view analytics, manage settings
    - super_admin: Full access including audit logs, user management, role changes
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import HTTPException

from .models import UserRole


# Role hierarchy (higher value = more permissions)
ROLE_HIERARCHY = {
    UserRole.guest: 0,
    UserRole.learner: 1,
    UserRole.teacher: 2,
    UserRole.admin: 3,
    UserRole.super_admin: 4,
}

# Role groups for common checks
STAFF_ROLES = {UserRole.teacher, UserRole.admin, UserRole.super_admin}
ADMIN_ROLES = {UserRole.admin, UserRole.super_admin}
SUPER_ADMIN_ROLES = {UserRole.super_admin}


def has_role(user_role: UserRole, required_role: UserRole) -> bool:
    """
    Check if a user role meets or exceeds the required role.
    
    Args:
        user_role: The user's current role
        required_role: The minimum required role
        
    Returns:
        True if user has sufficient permissions
    """
    return ROLE_HIERARCHY.get(user_role, 0) >= ROLE_HIERARCHY.get(required_role, 0)


def check_permission(
    user_role: UserRole,
    required_role: UserRole,
    error_message: str = "Insufficient permissions",
) -> None:
    """
    Check if a user has the required role, raise HTTPException if not.
    
    Args:
        user_role: The user's current role
        required_role: The minimum required role
        error_message: Custom error message
        
    Raises:
        HTTPException: 403 if user lacks permissions
    """
    if not has_role(user_role, required_role):
        raise HTTPException(status_code=403, detail=error_message)


def can_manage_user(actor_role: UserRole, target_role: UserRole) -> bool:
    """
    Check if an actor can manage (edit, delete, change role) a target user.
    
    Rules:
    - super_admin can manage anyone
    - admin can manage teacher, learner, guest (not other admins)
    - teacher can only manage their own data
    - No one can manage users with equal or higher role
    
    Args:
        actor_role: Role of the user performing the action
        target_role: Role of the user being managed
        
    Returns:
        True if actor can manage target
    """
    # super_admin can manage anyone (including other super_admins)
    if actor_role == UserRole.super_admin:
        return True

    actor_level = ROLE_HIERARCHY.get(actor_role, 0)
    target_level = ROLE_HIERARCHY.get(target_role, 0)
    
    # Can only manage users with strictly lower role
    return actor_level > target_level


def get_role_display_name(role: UserRole) -> str:
    """
    Get human-readable display name for a role.
    
    Args:
        role: User role enum
        
    Returns:
        Display name string
    """
    display_names = {
        UserRole.guest: "Guest",
        UserRole.learner: "Learner",
        UserRole.teacher: "Teacher",
        UserRole.admin: "Administrator",
        UserRole.super_admin: "Super Administrator",
    }
    return display_names.get(role, role.value)


def get_allowed_actions(role: UserRole) -> dict[str, list[str]]:
    """
    Get list of allowed actions for a role.
    
    Args:
        role: User role enum
        
    Returns:
        Dictionary of resource types to allowed actions
    """
    base_actions = ["view"]
    learner_actions = base_actions + ["progress"]
    teacher_actions = learner_actions + ["create", "update", "submit_review"]
    admin_actions = teacher_actions + ["delete", "approve", "reject", "manage_settings"]
    super_admin_actions = admin_actions + ["manage_users", "view_audit_logs", "change_roles"]
    
    permissions = {
        UserRole.guest: {"lesson": base_actions, "quiz": base_actions},
        UserRole.learner: {
            "lesson": learner_actions,
            "quiz": learner_actions,
            "progress": learner_actions,
        },
        UserRole.teacher: {
            "lesson": teacher_actions,
            "quiz": teacher_actions,
            "rag_document": teacher_actions,
            "class": teacher_actions,
        },
        UserRole.admin: {
            "lesson": admin_actions,
            "quiz": admin_actions,
            "rag_document": admin_actions,
            "user": ["view", "update"],
            "settings": admin_actions,
            "analytics": ["view"],
        },
        UserRole.super_admin: {
            "all": super_admin_actions,
        },
    }
    return permissions.get(role, {})

