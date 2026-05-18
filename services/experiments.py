"""
Experiment Service for Luuniensuki LMS.

This module provides utilities for A/B testing experiments.
For feature flags, use backend.services.feature_flags instead.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models import (
    Experiment,
    UserExperimentAssignment,
)


def get_experiment_variant_for_user(
    db: Session,
    experiment_key: str,
    user_id: UUID,
) -> Optional[str]:
    """
    Get the experiment variant assigned to a user.
    
    If user has no assignment yet, assign them deterministically based on variant weights.

    Args:
        db: Database session
        experiment_key: Experiment key
        user_id: User ID

    Returns:
        Variant key or None if experiment not found/inactive
    """
    # Get experiment
    experiment = db.execute(
        select(Experiment).where(Experiment.key == experiment_key)
    ).scalar_one_or_none()

    if not experiment or not experiment.is_active:
        return None

    # Check if user already has an assignment
    existing_assignment = db.execute(
        select(UserExperimentAssignment).where(
            UserExperimentAssignment.user_id == user_id,
            UserExperimentAssignment.experiment_id == experiment.id,
        )
    ).scalar_one_or_none()

    if existing_assignment:
        return existing_assignment.variant_key

    # Assign variant based on weights
    variant_key = _assign_variant_by_weight(user_id, experiment_key, experiment.variants)
    
    # Create assignment record
    assignment = UserExperimentAssignment(
        user_id=user_id,
        experiment_id=experiment.id,
        variant_key=variant_key,
        assigned_at=datetime.now(timezone.utc),
    )
    db.add(assignment)
    db.flush()

    return variant_key


def _assign_variant_by_weight(
    user_id: UUID,
    experiment_key: str,
    variants: list[dict[str, Any]],
) -> str:
    """
    Assign a variant deterministically based on weights.
    
    Args:
        user_id: User ID
        experiment_key: Experiment key
        variants: List of variant dicts with 'key' and 'weight' fields
        
    Returns:
        Variant key
    """
    # Calculate total weight
    total_weight = sum(v.get("weight", 0) for v in variants)
    
    if total_weight == 0:
        # If no weights, use first variant
        return variants[0]["key"]
    
    # Generate deterministic hash
    hash_input = f"{user_id}:{experiment_key}"
    hash_value = hashlib.md5(hash_input.encode()).hexdigest()
    user_value = int(hash_value[:8], 16) % total_weight

    # Select variant based on cumulative weights
    cumulative_weight = 0
    for variant in variants:
        cumulative_weight += variant.get("weight", 0)
        if user_value < cumulative_weight:
            return variant["key"]

    # Fallback to first variant
    return variants[0]["key"]


def get_all_experiments_for_user(
    db: Session,
    user_id: UUID,
) -> dict[str, str]:
    """
    Get all active experiments and assigned variants for a user.

    Args:
        db: Database session
        user_id: User ID

    Returns:
        Dict mapping experiment keys to variant keys
    """
    experiments = db.execute(
        select(Experiment).where(Experiment.is_active == True)  # noqa: E712
    ).scalars().all()

    result = {}
    for experiment in experiments:
        variant = get_experiment_variant_for_user(db, experiment.key, user_id)
        if variant:
            result[experiment.key] = variant

    return result


def create_experiment(
    db: Session,
    key: str,
    name: str,
    variants: list[dict[str, Any]],
    description: Optional[str] = None,
    target_audience: Optional[dict[str, Any]] = None,
    is_active: bool = False,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    created_by_id: Optional[UUID] = None,
) -> Experiment:
    """
    Create a new experiment.

    Args:
        db: Database session
        key: Unique experiment key
        name: Display name
        variants: List of variant dicts with 'key', 'name', 'weight'
        description: Optional description
        target_audience: Optional targeting rules
        is_active: Whether experiment is active
        start_date: Optional start date
        end_date: Optional end date
        created_by_id: User ID of creator

    Returns:
        Created Experiment
    """
    experiment = Experiment(
        key=key,
        name=name,
        description=description,
        variants=variants,
        target_audience=target_audience,
        is_active=is_active,
        start_date=start_date,
        end_date=end_date,
        created_by_id=created_by_id,
    )
    db.add(experiment)
    db.flush()
    return experiment


def update_experiment(
    db: Session,
    experiment_id: UUID,
    name: Optional[str] = None,
    description: Optional[str] = None,
    variants: Optional[list[dict[str, Any]]] = None,
    target_audience: Optional[dict[str, Any]] = None,
    is_active: Optional[bool] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> Optional[Experiment]:
    """
    Update an existing experiment.

    Args:
        db: Database session
        experiment_id: Experiment ID
        name: Display name
        description: Description
        variants: List of variants
        target_audience: Targeting rules
        is_active: Whether experiment is active
        start_date: Start date
        end_date: End date

    Returns:
        Updated Experiment or None if not found
    """
    experiment = db.execute(
        select(Experiment).where(Experiment.id == experiment_id)
    ).scalar_one_or_none()

    if not experiment:
        return None

    if name is not None:
        experiment.name = name
    if description is not None:
        experiment.description = description
    if variants is not None:
        experiment.variants = variants
    if target_audience is not None:
        experiment.target_audience = target_audience
    if is_active is not None:
        experiment.is_active = is_active
    if start_date is not None:
        experiment.start_date = start_date
    if end_date is not None:
        experiment.end_date = end_date

    db.flush()
    return experiment


