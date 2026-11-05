# -*- coding: utf-8 -*-
"""Research AI Scaffolding Hint Policy Module (LN-04).

Exposes the Socratic scaffolding, hint budget management, and leakage defense policies.
"""
from __future__ import annotations

from typing import Any, Optional

from backend.domain.scaffolding_policy import (
    POLICY_VERSION,
    ScaffoldingDecision,
    ScaffoldingResult,
    detect_answer_request,
    detect_scaffolding_injection,
    evaluate_scaffolding_policy,
)

__all__ = [
    "POLICY_VERSION",
    "ScaffoldingDecision",
    "ScaffoldingResult",
    "detect_answer_request",
    "detect_scaffolding_injection",
    "evaluate_scaffolding_policy",
]
