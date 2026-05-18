"""
Feature Flags Service for Luuniensuki LMS.

This module provides utilities for feature flag management with support for:
- Deterministic percentage rollouts
- User whitelist/blacklist
- Targeting rules based on user attributes
"""

from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models import FeatureFlag, User, UserRole


def is_feature_enabled_for_user(
    db: Session,
    feature_key: str,
    user_id: UUID,
) -> bool:
    """
    Check if a feature is enabled for a specific user.

    The check follows this priority:
    1. If flag is globally disabled, return False
    2. Check user blacklist - if user is in blacklist, return False
    3. Check user whitelist - if user is in whitelist, return True
    4. Check targeting rules - if user matches rules, return True/False based on rules
    5. Check rollout percentage - deterministic hash-based assignment

    Args:
        db: Database session
        feature_key: Feature flag key
        user_id: User ID

    Returns:
        True if feature is enabled for user, False otherwise
    """
    # Get feature flag
    flag = db.execute(
        select(FeatureFlag).where(FeatureFlag.key == feature_key)
    ).scalar_one_or_none()

    if not flag:
        return False

    # If flag is not enabled globally, return False
    if not flag.is_enabled:
        return False

    # Check blacklist first
    if flag.user_blacklist and isinstance(flag.user_blacklist, list):
        if str(user_id) in flag.user_blacklist:
            return False

    # Check whitelist
    if flag.user_whitelist and isinstance(flag.user_whitelist, list):
        if str(user_id) in flag.user_whitelist:
            return True

    # Check targeting rules
    if flag.rules:
        user = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
        if user and not _check_targeting_rules(user, flag.rules):
            return False

    # Check rollout percentage with deterministic hash
    if flag.rollout_percentage > 0:
        user_hash = _hash_user_for_feature(user_id, feature_key)
        return user_hash < flag.rollout_percentage

    return False


def _check_targeting_rules(user: User, rules: dict[str, Any]) -> bool:
    """
    Check if a user matches the targeting rules.

    Supported rules:
    - roles: List of allowed user roles
    - min_signup_days: Minimum days since signup
    - max_signup_days: Maximum days since signup

    Args:
        user: User object
        rules: Targeting rules dictionary

    Returns:
        True if user matches all rules, False otherwise
    """
    # Check role targeting
    if "roles" in rules and isinstance(rules["roles"], list):
        if user.role.value not in rules["roles"]:
            return False

    # Check signup date targeting
    if "min_signup_days" in rules or "max_signup_days" in rules:
        days_since_signup = (datetime.utcnow() - user.created_at.replace(tzinfo=None)).days

        if "min_signup_days" in rules:
            if days_since_signup < rules["min_signup_days"]:
                return False

        if "max_signup_days" in rules:
            if days_since_signup > rules["max_signup_days"]:
                return False

    return True


def _hash_user_for_feature(user_id: UUID, feature_key: str) -> int:
    """
    Generate a deterministic hash for user+feature combination.

    Returns a number between 0-99 for percentage-based rollout.
    Same user always gets same result for same feature.

    Args:
        user_id: User ID
        feature_key: Feature key

    Returns:
        Integer between 0 and 99
    """
    hash_input = f"{user_id}:{feature_key}"
    hash_value = hashlib.md5(hash_input.encode()).hexdigest()
    return int(hash_value[:8], 16) % 100


def get_all_features_for_user(
    db: Session,
    user_id: UUID,
) -> dict[str, bool]:
    """
    Get all feature flags and their status for a specific user.

    Args:
        db: Database session
        user_id: User ID

    Returns:
        Dict mapping feature keys to their enabled status
    """
    flags = db.execute(select(FeatureFlag)).scalars().all()

    result = {}
    for flag in flags:
        result[flag.key] = is_feature_enabled_for_user(db, flag.key, user_id)

    return result

