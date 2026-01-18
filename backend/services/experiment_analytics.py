"""
Experiment Analytics Service for Luuniensuki LMS.

This module provides utilities for tracking experiment events and analyzing results
including conversion rates and statistical significance.
"""

from __future__ import annotations

import math
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from backend.models import (
    Experiment,
    ExperimentEvent,
    ExperimentMetricEvent,
    UserExperimentAssignment,
)


def track_experiment_event(
    db: Session,
    experiment_key: str,
    user_id: UUID,
    event_type: str,
    event_name: str,
    event_value: Optional[float] = None,
    metadata: Optional[dict[str, Any]] = None,
) -> Optional[ExperimentEvent]:
    """
    Track an event for an experiment.

    Args:
        db: Database session
        experiment_key: Experiment key
        user_id: User ID
        event_type: Type of event (impression, conversion, click, custom)
        event_name: Specific event name (e.g., "completed_onboarding")
        event_value: Optional numeric value
        metadata: Optional additional metadata

    Returns:
        Created ExperimentEvent or None if experiment/assignment not found
    """
    # Get experiment
    experiment = db.execute(
        select(Experiment).where(Experiment.key == experiment_key)
    ).scalar_one_or_none()

    if not experiment:
        return None

    # Get user's assignment
    assignment = db.execute(
        select(UserExperimentAssignment).where(
            and_(
                UserExperimentAssignment.user_id == user_id,
                UserExperimentAssignment.experiment_id == experiment.id,
            )
        )
    ).scalar_one_or_none()

    if not assignment:
        return None

    # Create event
    event = ExperimentEvent(
        experiment_id=experiment.id,
        user_id=user_id,
        assignment_id=assignment.id,
        event_type=event_type,
        event_name=event_name,
        event_value=event_value,
        metadata_json=metadata or {},
        created_at=datetime.now(timezone.utc),
    )
    db.add(event)
    db.flush()

    return event


def calculate_conversion_rates(
    db: Session,
    experiment_id: UUID,
    conversion_event_name: str,
) -> dict[str, Any]:
    """
    Calculate conversion rates per variant for an experiment.

    Args:
        db: Database session
        experiment_id: Experiment ID
        conversion_event_name: Event name to count as conversion

    Returns:
        Dict with per-variant metrics: impressions, conversions, conversion_rate
    """
    # Get all assignments for this experiment
    assignments = db.execute(
        select(UserExperimentAssignment).where(
            UserExperimentAssignment.experiment_id == experiment_id
        )
    ).scalars().all()

    # Group assignments by variant
    variant_assignments = defaultdict(list)
    for assignment in assignments:
        variant_assignments[assignment.variant_key].append(assignment)

    results = {}

    for variant_key, assignments_list in variant_assignments.items():
        assignment_ids = [a.id for a in assignments_list]

        # Count total impressions (assignments)
        impressions = len(assignments_list)

        # Count conversions (users who had the conversion event)
        conversion_count = db.execute(
            select(func.count(func.distinct(ExperimentEvent.user_id))).where(
                and_(
                    ExperimentEvent.assignment_id.in_(assignment_ids),
                    ExperimentEvent.event_name == conversion_event_name,
                )
            )
        ).scalar() or 0

        conversion_rate = (conversion_count / impressions * 100) if impressions > 0 else 0.0

        results[variant_key] = {
            "impressions": impressions,
            "conversions": conversion_count,
            "conversion_rate": round(conversion_rate, 2),
        }

    return results


def calculate_chi_square_test(
    control_conversions: int,
    control_total: int,
    variant_conversions: int,
    variant_total: int,
) -> dict[str, float]:
    """
    Calculate chi-square test for statistical significance.

    Args:
        control_conversions: Number of conversions in control group
        control_total: Total number in control group
        variant_conversions: Number of conversions in variant group
        variant_total: Total number in variant group

    Returns:
        Dict with chi_square value and p_value
    """
    # Calculate expected values
    total_conversions = control_conversions + variant_conversions
    total_sample = control_total + variant_total

    if total_sample == 0:
        return {"chi_square": 0.0, "p_value": 1.0}

    expected_control_conversions = (control_total * total_conversions) / total_sample
    expected_control_non_conversions = control_total - expected_control_conversions
    expected_variant_conversions = (variant_total * total_conversions) / total_sample
    expected_variant_non_conversions = variant_total - expected_variant_conversions

    actual_control_non_conversions = control_total - control_conversions
    actual_variant_non_conversions = variant_total - variant_conversions

    # Calculate chi-square statistic
    chi_square = 0.0

    # Avoid division by zero
    if expected_control_conversions > 0:
        chi_square += ((control_conversions - expected_control_conversions) ** 2) / expected_control_conversions

    if expected_control_non_conversions > 0:
        chi_square += ((actual_control_non_conversions - expected_control_non_conversions) ** 2) / expected_control_non_conversions

    if expected_variant_conversions > 0:
        chi_square += ((variant_conversions - expected_variant_conversions) ** 2) / expected_variant_conversions

    if expected_variant_non_conversions > 0:
        chi_square += ((actual_variant_non_conversions - expected_variant_non_conversions) ** 2) / expected_variant_non_conversions

    # Calculate p-value (degrees of freedom = 1 for 2x2 contingency table)
    # Using approximation for chi-square CDF
    p_value = _chi_square_p_value(chi_square, df=1)

    return {
        "chi_square": round(chi_square, 4),
        "p_value": round(p_value, 4),
    }


def _chi_square_p_value(chi_square: float, df: int) -> float:
    """
    Approximate p-value for chi-square test.

    For df=1, uses the complementary error function approximation.

    Args:
        chi_square: Chi-square statistic
        df: Degrees of freedom

    Returns:
        Approximate p-value
    """
    if chi_square <= 0 or df != 1:
        return 1.0

    # For df=1, p-value = erfc(sqrt(chi_square/2))
    # Using approximation: erfc(x) ≈ exp(-x²) for x > 0
    x = math.sqrt(chi_square / 2)

    # More accurate erfc approximation
    # erfc(x) ≈ (1/sqrt(π)) * (e^(-x²)/x) * (1 - 1/(2x²) + 3/(4x⁴))
    if x > 5:
        # For large x, use asymptotic expansion
        return 0.0

    exp_term = math.exp(-x * x)

    # Simple approximation
    p_value = 1.0 - math.erf(x)

    return max(0.0, min(1.0, p_value))


def generate_experiment_report(
    db: Session,
    experiment_id: UUID,
    conversion_event_name: str,
    control_variant_key: str = "control",
    significance_threshold: float = 0.05,
) -> dict[str, Any]:
    """
    Generate a complete experiment report with statistical analysis.

    Args:
        db: Database session
        experiment_id: Experiment ID
        conversion_event_name: Event name to count as conversion
        control_variant_key: Key for the control variant (default: "control")
        significance_threshold: P-value threshold for significance (default: 0.05)

    Returns:
        Dict with experiment report including per-variant stats and winner
    """
    # Get experiment
    experiment = db.execute(
        select(Experiment).where(Experiment.id == experiment_id)
    ).scalar_one_or_none()

    if not experiment:
        return {"error": "Experiment not found"}

    # Calculate conversion rates
    variant_stats = calculate_conversion_rates(db, experiment_id, conversion_event_name)

    if not variant_stats:
        return {
            "experiment_key": experiment.key,
            "experiment_name": experiment.name,
            "variants": {},
            "winner": None,
            "is_significant": False,
            "message": "No data available",
        }

    # Calculate statistical significance against control
    control_stats = variant_stats.get(control_variant_key)

    if not control_stats:
        # If no control variant, just return the stats
        return {
            "experiment_key": experiment.key,
            "experiment_name": experiment.name,
            "variants": variant_stats,
            "winner": None,
            "is_significant": False,
            "message": "No control variant found",
        }

    # Compare each variant against control
    comparisons = {}
    best_variant = None
    best_conversion_rate = control_stats["conversion_rate"]
    is_significant = False

    for variant_key, variant_data in variant_stats.items():
        if variant_key == control_variant_key:
            comparisons[variant_key] = {
                **variant_data,
                "p_value": None,
                "is_significant": False,
                "improvement": 0.0,
            }
            continue

        # Calculate chi-square test
        chi_square_result = calculate_chi_square_test(
            control_conversions=control_stats["conversions"],
            control_total=control_stats["impressions"],
            variant_conversions=variant_data["conversions"],
            variant_total=variant_data["impressions"],
        )

        p_value = chi_square_result["p_value"]
        variant_is_significant = p_value < significance_threshold

        # Calculate improvement over control
        improvement = 0.0
        if control_stats["conversion_rate"] > 0:
            improvement = (
                (variant_data["conversion_rate"] - control_stats["conversion_rate"])
                / control_stats["conversion_rate"]
                * 100
            )

        comparisons[variant_key] = {
            **variant_data,
            "p_value": p_value,
            "chi_square": chi_square_result["chi_square"],
            "is_significant": variant_is_significant,
            "improvement": round(improvement, 2),
        }

        # Track best variant
        if variant_is_significant and variant_data["conversion_rate"] > best_conversion_rate:
            best_variant = variant_key
            best_conversion_rate = variant_data["conversion_rate"]
            is_significant = True

    return {
        "experiment_key": experiment.key,
        "experiment_name": experiment.name,
        "conversion_event": conversion_event_name,
        "variants": comparisons,
        "winner": best_variant,
        "is_significant": is_significant,
        "significance_threshold": significance_threshold,
    }


def get_experiment_events(
    db: Session,
    experiment_id: UUID,
    event_type: Optional[str] = None,
    event_name: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> list[ExperimentEvent]:
    """
    Get events for an experiment with optional filtering.

    Args:
        db: Database session
        experiment_id: Experiment ID
        event_type: Optional event type filter
        event_name: Optional event name filter
        limit: Maximum number of events to return
        offset: Number of events to skip

    Returns:
        List of ExperimentEvent objects
    """
    query = select(ExperimentEvent).where(
        ExperimentEvent.experiment_id == experiment_id
    )

    if event_type:
        query = query.where(ExperimentEvent.event_type == event_type)

    if event_name:
        query = query.where(ExperimentEvent.event_name == event_name)

    query = query.order_by(ExperimentEvent.created_at.desc()).limit(limit).offset(offset)

    events = db.execute(query).scalars().all()
    return list(events)


# =============================================================================
# Metric Event Functions (P1-EXP-03)
# =============================================================================


def record_metric_event(
    db: Session,
    experiment_id: UUID,
    user_id: UUID,
    metric_name: str,
    metric_value: float,
    metadata: Optional[dict[str, Any]] = None,
) -> Optional[ExperimentMetricEvent]:
    """
    Record a metric event for an experiment.

    Args:
        db: Database session
        experiment_id: Experiment ID
        user_id: User ID
        metric_name: Metric name (e.g., "conversion", "retention", "engagement")
        metric_value: Numeric value for the metric
        metadata: Optional additional metadata

    Returns:
        Created ExperimentMetricEvent or None if user is not assigned to experiment
    """
    # Get user's assignment to determine variant
    assignment = db.execute(
        select(UserExperimentAssignment).where(
            and_(
                UserExperimentAssignment.user_id == user_id,
                UserExperimentAssignment.experiment_id == experiment_id,
            )
        )
    ).scalar_one_or_none()

    if not assignment:
        return None

    # Create metric event
    metric_event = ExperimentMetricEvent(
        experiment_id=experiment_id,
        user_id=user_id,
        variant=assignment.variant_key,
        metric_name=metric_name,
        metric_value=metric_value,
        metadata_json=metadata or {},
        created_at=datetime.now(timezone.utc),
    )
    db.add(metric_event)
    db.flush()

    return metric_event


def calculate_metric_summary(
    db: Session,
    experiment_id: UUID,
    metric_name: str,
) -> dict[str, Any]:
    """
    Calculate aggregated metric summary per variant.

    Args:
        db: Database session
        experiment_id: Experiment ID
        metric_name: Metric name to analyze

    Returns:
        Dict with per-variant metric aggregations
    """
    # Query metrics grouped by variant
    metrics_query = (
        select(
            ExperimentMetricEvent.variant,
            func.count(ExperimentMetricEvent.id).label("count"),
            func.sum(ExperimentMetricEvent.metric_value).label("sum"),
            func.avg(ExperimentMetricEvent.metric_value).label("avg"),
            func.min(ExperimentMetricEvent.metric_value).label("min"),
            func.max(ExperimentMetricEvent.metric_value).label("max"),
        )
        .where(
            and_(
                ExperimentMetricEvent.experiment_id == experiment_id,
                ExperimentMetricEvent.metric_name == metric_name,
            )
        )
        .group_by(ExperimentMetricEvent.variant)
    )

    results = db.execute(metrics_query).all()

    variant_metrics = {}
    for row in results:
        variant_metrics[row.variant] = {
            "count": row.count,
            "sum": float(row.sum or 0),
            "avg": float(row.avg or 0),
            "min": float(row.min or 0),
            "max": float(row.max or 0),
        }

    return variant_metrics


def calculate_metric_comparison(
    db: Session,
    experiment_id: UUID,
    metric_name: str,
    control_variant_key: str = "control",
) -> dict[str, Any]:
    """
    Calculate metric comparison between variants with statistical indicators.

    Args:
        db: Database session
        experiment_id: Experiment ID
        metric_name: Metric name to compare
        control_variant_key: Key for the control variant

    Returns:
        Dict with variant comparisons and statistical significance
    """
    # Get metric summary
    variant_metrics = calculate_metric_summary(db, experiment_id, metric_name)

    if not variant_metrics:
        return {
            "metric_name": metric_name,
            "variants": {},
            "comparison": {},
        }

    # Get control metrics
    control_metrics = variant_metrics.get(control_variant_key)

    if not control_metrics:
        # Return raw metrics without comparison
        return {
            "metric_name": metric_name,
            "variants": variant_metrics,
            "comparison": {},
        }

    # Compare each variant to control
    comparison = {}
    for variant_key, metrics in variant_metrics.items():
        if variant_key == control_variant_key:
            comparison[variant_key] = {
                **metrics,
                "improvement_pct": 0.0,
                "is_better": False,
            }
            continue

        # Calculate improvement percentage
        improvement_pct = 0.0
        if control_metrics["avg"] != 0:
            improvement_pct = (
                (metrics["avg"] - control_metrics["avg"]) / control_metrics["avg"] * 100
            )

        # Simple significance check: count must be sufficient
        is_significant = metrics["count"] >= 30 and control_metrics["count"] >= 30

        comparison[variant_key] = {
            **metrics,
            "improvement_pct": round(improvement_pct, 2),
            "is_better": metrics["avg"] > control_metrics["avg"],
            "has_sufficient_data": is_significant,
        }

    return {
        "metric_name": metric_name,
        "control_variant": control_variant_key,
        "variants": comparison,
    }


def get_all_metrics_for_experiment(
    db: Session,
    experiment_id: UUID,
) -> list[str]:
    """
    Get list of all unique metric names for an experiment.

    Args:
        db: Database session
        experiment_id: Experiment ID

    Returns:
        List of unique metric names
    """
    metrics = db.execute(
        select(func.distinct(ExperimentMetricEvent.metric_name))
        .where(ExperimentMetricEvent.experiment_id == experiment_id)
        .order_by(ExperimentMetricEvent.metric_name)
    ).scalars().all()

    return list(metrics)
