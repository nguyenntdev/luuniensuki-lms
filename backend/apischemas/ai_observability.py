# -*- coding: utf-8 -*-
"""Pydantic schemas for AI observability, telemetry, and budgeting (Wave W06 / Slot A09 / V5-T069)."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AIBudgetStatusOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    entity_type: str = Field(description="'user' or 'classroom'")
    entity_id: Optional[str] = Field(None, description="Entity identifier")
    daily_token_limit: int = Field(description="Maximum tokens allowed per 24h window")
    tokens_used_today: int = Field(description="Tokens consumed today")
    tokens_remaining: int = Field(description="Tokens remaining before exhaustion")
    daily_cost_limit_usd: float = Field(description="Maximum cost allowed in USD per 24h window")
    cost_used_today_usd: float = Field(description="Estimated cost consumed today in USD")
    cost_remaining_usd: float = Field(description="Cost remaining before exhaustion in USD")
    is_budget_exhausted: bool = Field(description="True if token or cost ceiling is reached")
    retry_after_seconds: int = Field(description="Seconds until window reset (UTC midnight)")
    reset_at: str = Field(description="ISO-8601 UTC timestamp of window reset")
    policy: str = Field(default="daily_sliding_window_fail_closed")


class AIBudgetCapSetIn(BaseModel):
    entity_type: Literal["user", "classroom"] = Field(
        ..., description="Entity type: 'user' or 'classroom'"
    )
    entity_id: UUID = Field(..., description="Target UUID for user or classroom")
    daily_token_limit: int = Field(
        default=500_000, ge=1_000, le=100_000_000, description="Daily token cap"
    )
    daily_cost_limit_usd: float = Field(
        default=5.0, ge=0.01, le=1000.0, description="Daily cost cap in USD"
    )
    max_tokens_per_request: Optional[int] = Field(
        default=4096, ge=256, le=32768, description="Per-request max tokens limit"
    )


class AIBudgetCapOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    entity_type: str
    entity_id: str
    daily_token_limit: int
    daily_cost_limit_usd: float
    max_tokens_per_request: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class AIObservabilityMetricsOut(BaseModel):
    total_requests: int = Field(description="Total AI operations in window")
    successful_requests: int = Field(description="Successful operations")
    error_requests: int = Field(description="Error or rejected operations")
    fallback_requests: int = Field(description="Operations that degraded to deterministic fallback")
    success_rate: float = Field(description="Fraction of requests that succeeded (0.0 to 1.0)")
    total_tokens: int = Field(description="Sum of prompt + completion tokens")
    prompt_tokens: int = Field(description="Sum of prompt/input tokens")
    completion_tokens: int = Field(description="Sum of completion/output tokens")
    total_cost_usd: float = Field(description="Total estimated spend in USD")
    avg_latency_ms: float = Field(description="Average latency in milliseconds")
    p95_latency_ms: float = Field(description="95th percentile latency in milliseconds")
    total_citations_validated: int = Field(description="Total citation evaluations")
    valid_citations: int = Field(description="Total valid citations verified against sources")
    invalid_citations: int = Field(description="Total dropped or hallucinated citations")
    citation_validity_rate: float = Field(description="Valid citations ratio (0.0 to 1.0)")
    by_operation: dict[str, Any] = Field(default_factory=dict, description="Breakdown by operation")
    by_model: dict[str, Any] = Field(default_factory=dict, description="Breakdown by AI model")
    by_status: dict[str, int] = Field(default_factory=dict, description="Breakdown by status code/outcome")
    zero_pii_confirmed: bool = Field(default=True, description="Strictly verified zero PII in telemetry")
    window_hours: int = Field(default=24, description="Lookback window in hours")
    generated_at: str = Field(description="Report generation timestamp")
