"""LN-03 method-local typed errors (never silently default)."""
from __future__ import annotations


class ScenarioError(ValueError):
    """Malformed scenario input: fail closed instead of guessing a fallback."""


class PolicyConfigError(ValueError):
    """Invalid policy configuration (thresholds, budgets, ablation flags)."""
