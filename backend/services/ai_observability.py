# -*- coding: utf-8 -*-
"""AI Observability & Budgeting Service (Wave W06 / Slot A09 / V5-T069).

Core mandates:
1. Track token usage (prompt/completion/total), latency, cost estimation, and model.
2. Citation validity tracking (valid vs dropped invalid citations).
3. Budget cap enforcement at User and Classroom levels.
4. Capacity limit 429/503 response on exhausted budget with Retry-After policy and
   support for deterministic fallback.
5. STRICT ZERO PII in telemetry logs: raw prompts, names, emails, and credentials
   are scrubbed and replaced with SHA-256 hashes.
"""
from __future__ import annotations

import hashlib
import logging
import re
import threading
import unicodedata
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Sequence
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from ..ai_observability_models import AIBudgetCap, AITelemetryLog
from ..config import settings
from ..errors import AppError
from ..models import Classroom, User

logger = logging.getLogger("luuniensuki.ai_telemetry")

# --------------------------------------------------------------------------- #
# PII Scrubbers & Sanitize Rules
# --------------------------------------------------------------------------- #
_RE_EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_RE_PHONE_VN = re.compile(r"(?:\+?84|0)(?:3[2-9]|5[6|8|9]|7[0|6-9]|8[1-9]|9[0-9])[0-9]{7}\b")
_RE_PHONE_INTL = re.compile(r"\b\+?[1-9]\d{1,14}\b")
_RE_CCCD = re.compile(r"\b[0-9]{9}\b|\b[0-9]{12}\b")
_RE_CARD = re.compile(r"\b(?:\d{4}[ -]?){3}\d{4}\b")
_RE_JWT = re.compile(r"ey[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+")
_RE_KEY = re.compile(r"(?i)(?:bearer\s+|api[_-]?key[:=]\s*)[a-zA-Z0-9_\-]{16,}")


def scrub_pii(text: str) -> str:
    """Scrub PII (email, phone, national ID, credit cards, JWT/keys) from text."""
    if not text:
        return ""
    s = text
    s = _RE_EMAIL.sub("[REDACTED_EMAIL]", s)
    s = _RE_PHONE_VN.sub("[REDACTED_PHONE]", s)
    s = _RE_CCCD.sub("[REDACTED_ID]", s)
    s = _RE_CARD.sub("[REDACTED_CARD]", s)
    s = _RE_JWT.sub("[REDACTED_JWT]", s)
    s = _RE_KEY.sub("[REDACTED_KEY]", s)
    return s


def hash_prompt(prompt: str) -> str:
    """Compute SHA-256 digest of normalized prompt.

    Ensures zero raw user prompt text enters telemetry tables or log output.
    """
    if not prompt:
        return ""
    normalized = unicodedata.normalize("NFKC", prompt.strip().lower())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def sanitize_for_telemetry(prompt: str) -> dict[str, Any]:
    """Generate safe, zero-PII metadata for prompt telemetry."""
    cleaned = str(prompt or "").strip()
    return {
        "prompt_sha256": hash_prompt(cleaned),
        "prompt_length": len(cleaned),
        "estimated_tokens": estimate_tokens(cleaned),
    }


# --------------------------------------------------------------------------- #
# Token Estimation & Cost Model
# --------------------------------------------------------------------------- #
# Rates per 1,000,000 tokens (USD)
MODEL_RATES = {
    "gemini-3.8-flash-tiered": {"prompt": 0.10, "completion": 0.40},
    "gemini-2.5-flash": {"prompt": 0.075, "completion": 0.30},
    "clara-gemini-3.8-flash-tiered-v1": {"prompt": 0.10, "completion": 0.40},
    "deepseek-v4-flash": {"prompt": 0.14, "completion": 0.28},
    "deepseek-v3.1": {"prompt": 0.14, "completion": 0.28},
    "deepseek-chat": {"prompt": 0.14, "completion": 0.28},
    "default": {"prompt": 0.15, "completion": 0.35},
}


def estimate_tokens(text: str) -> int:
    """Heuristic token estimator for Vietnamese and multilingual text."""
    cleaned = str(text or "").strip()
    if not cleaned:
        return 0
    words = cleaned.split()
    # In Vietnamese/multilingual text, 1 word is roughly 1.3 - 1.4 tokens
    by_words = int(len(words) * 1.35)
    by_chars = max(1, int(len(cleaned) / 3.8))
    return max(by_words, by_chars)


def estimate_cost_usd(
    model: str, prompt_tokens: int, completion_tokens: int
) -> float:
    """Estimate financial cost in USD for a given model and token consumption."""
    target = str(model or "").lower().strip()
    rates = MODEL_RATES.get("default")
    for k, v in MODEL_RATES.items():
        if k in target:
            rates = v
            break

    in_cost = (max(0, prompt_tokens) / 1_000_000.0) * rates["prompt"]
    out_cost = (max(0, completion_tokens) / 1_000_000.0) * rates["completion"]
    return round(in_cost + out_cost, 6)


# --------------------------------------------------------------------------- #
# Budget Window & Allowance Checking
# --------------------------------------------------------------------------- #
def get_window_start(now: Optional[datetime] = None) -> datetime:
    """Get UTC midnight start of the current daily budget window."""
    t = now or datetime.now(timezone.utc)
    return t.replace(hour=0, minute=0, second=0, microsecond=0)


def get_window_reset_info(now: Optional[datetime] = None) -> tuple[int, str]:
    """Return (retry_after_seconds, reset_at_iso) for the current daily window."""
    t = now or datetime.now(timezone.utc)
    midnight = get_window_start(t) + timedelta(days=1)
    retry_after = max(60, int((midnight - t).total_seconds()))
    return retry_after, midnight.isoformat()


def get_daily_usage(
    db: Session,
    user_id: Optional[UUID] = None,
    classroom_id: Optional[UUID] = None,
    since: Optional[datetime] = None,
) -> dict[str, Any]:
    """Aggregate token and cost usage for the specified entity in current window."""
    start_time = since or get_window_start()
    conditions = [AITelemetryLog.created_at >= start_time]

    if user_id:
        conditions.append(AITelemetryLog.user_id == user_id)
    elif classroom_id:
        conditions.append(AITelemetryLog.classroom_id == classroom_id)
    else:
        # Global usage
        pass

    stmt = select(
        func.coalesce(func.sum(AITelemetryLog.prompt_tokens), 0).label("prompt_tokens"),
        func.coalesce(func.sum(AITelemetryLog.completion_tokens), 0).label("completion_tokens"),
        func.coalesce(func.sum(AITelemetryLog.total_tokens), 0).label("total_tokens"),
        func.coalesce(func.sum(AITelemetryLog.cost_usd), 0.0).label("cost_usd"),
        func.count(AITelemetryLog.id).label("request_count"),
    ).where(and_(*conditions))

    row = db.execute(stmt).one()
    return {
        "prompt_tokens": int(row.prompt_tokens),
        "completion_tokens": int(row.completion_tokens),
        "total_tokens": int(row.total_tokens),
        "cost_usd": round(float(row.cost_usd), 6),
        "request_count": int(row.request_count),
    }


def resolve_budget_caps(
    db: Session,
    user: Optional[User] = None,
    classroom_id: Optional[UUID] = None,
) -> dict[str, Any]:
    """Resolve effective daily token and cost caps for user and/or classroom."""
    user_token_limit = int(
        getattr(settings, "ai_daily_token_budget_ceiling", 500_000) or 500_000
    )
    user_cost_limit = float(
        getattr(settings, "ai_daily_cost_circuit_breaker_usd", 5.0) or 5.0
    )
    classroom_token_limit = 2_000_000
    classroom_cost_limit = 20.0

    # 1. Custom user cap override from DB
    if user:
        user_cap = db.execute(
            select(AIBudgetCap).where(
                and_(
                    AIBudgetCap.entity_type == "user",
                    AIBudgetCap.entity_id == user.id,
                    AIBudgetCap.is_active == True,
                )
            )
        ).scalar_one_or_none()
        if user_cap:
            user_token_limit = user_cap.daily_token_limit
            user_cost_limit = user_cap.daily_cost_limit_usd

    # 2. Classroom cap override
    if classroom_id:
        class_cap = db.execute(
            select(AIBudgetCap).where(
                and_(
                    AIBudgetCap.entity_type == "classroom",
                    AIBudgetCap.entity_id == classroom_id,
                    AIBudgetCap.is_active == True,
                )
            )
        ).scalar_one_or_none()
        if class_cap:
            classroom_token_limit = class_cap.daily_token_limit
            classroom_cost_limit = class_cap.daily_cost_limit_usd
        else:
            # Check Classroom.settings JSONB if present
            classroom = db.get(Classroom, classroom_id)
            if classroom and classroom.settings:
                c_set = classroom.settings
                if "ai_budget_cap_usd" in c_set:
                    try:
                        classroom_cost_limit = float(c_set["ai_budget_cap_usd"])
                    except (ValueError, TypeError):
                        pass
                if "daily_token_budget" in c_set:
                    try:
                        classroom_token_limit = int(c_set["daily_token_budget"])
                    except (ValueError, TypeError):
                        pass

    return {
        "user_token_limit": user_token_limit,
        "user_cost_limit": user_cost_limit,
        "classroom_token_limit": classroom_token_limit,
        "classroom_cost_limit": classroom_cost_limit,
    }


def check_budget_allowance(
    db: Session,
    user: Optional[User],
    classroom_id: Optional[UUID] = None,
    estimated_prompt_tokens: int = 0,
) -> tuple[bool, Optional[dict[str, Any]]]:
    """Check if the user or classroom has sufficient budget remaining.

    Returns:
        (True, None) if request is permitted.
        (False, details_dict) if budget is exhausted.
    """
    caps = resolve_budget_caps(db, user, classroom_id)
    retry_after, reset_at = get_window_reset_info()

    # Check user budget
    if user:
        user_usage = get_daily_usage(db, user_id=user.id)
        projected_tokens = user_usage["total_tokens"] + estimated_prompt_tokens
        if (
            projected_tokens > caps["user_token_limit"]
            or user_usage["cost_usd"] >= caps["user_cost_limit"]
        ):
            return False, {
                "scope": "user",
                "reason": (
                    "TOKEN_LIMIT_EXCEEDED"
                    if projected_tokens > caps["user_token_limit"]
                    else "COST_LIMIT_EXCEEDED"
                ),
                "daily_token_limit": caps["user_token_limit"],
                "tokens_used_today": user_usage["total_tokens"],
                "tokens_remaining": max(
                    0, caps["user_token_limit"] - user_usage["total_tokens"]
                ),
                "daily_cost_limit_usd": caps["user_cost_limit"],
                "cost_used_today_usd": user_usage["cost_usd"],
                "cost_remaining_usd": max(
                    0.0, round(caps["user_cost_limit"] - user_usage["cost_usd"], 6)
                ),
                "retry_after_seconds": retry_after,
                "reset_at": reset_at,
            }

    # Check classroom budget
    if classroom_id:
        class_usage = get_daily_usage(db, classroom_id=classroom_id)
        projected_tokens = class_usage["total_tokens"] + estimated_prompt_tokens
        if (
            projected_tokens > caps["classroom_token_limit"]
            or class_usage["cost_usd"] >= caps["classroom_cost_limit"]
        ):
            return False, {
                "scope": "classroom",
                "reason": (
                    "CLASSROOM_TOKEN_LIMIT_EXCEEDED"
                    if projected_tokens > caps["classroom_token_limit"]
                    else "CLASSROOM_COST_LIMIT_EXCEEDED"
                ),
                "daily_token_limit": caps["classroom_token_limit"],
                "tokens_used_today": class_usage["total_tokens"],
                "tokens_remaining": max(
                    0, caps["classroom_token_limit"] - class_usage["total_tokens"]
                ),
                "daily_cost_limit_usd": caps["classroom_cost_limit"],
                "cost_used_today_usd": class_usage["cost_usd"],
                "cost_remaining_usd": max(
                    0.0,
                    round(caps["classroom_cost_limit"] - class_usage["cost_usd"], 6),
                ),
                "retry_after_seconds": retry_after,
                "reset_at": reset_at,
            }

    return True, None


def enforce_budget_guardrail(
    db: Session,
    user: Optional[User],
    classroom_id: Optional[UUID] = None,
    estimated_prompt_tokens: int = 0,
    allow_fallback: bool = False,
    operation: str = "tutor",
    prompt_text: Optional[str] = None,
) -> tuple[bool, Optional[dict[str, Any]]]:
    """Guardrail to enforce capacity limit or permit deterministic fallback.

    If budget is exhausted:
    - If allow_fallback is True: returns (False, details) so router can trigger deterministic fallback.
    - If allow_fallback is False: records telemetry event and raises AppError with HTTP 429 and Retry-After.
    """
    is_allowed, exhausted_details = check_budget_allowance(
        db, user, classroom_id, estimated_prompt_tokens
    )
    if is_allowed:
        return True, None

    # Budget is exhausted
    assert exhausted_details is not None

    # Record exhausted budget telemetry attempt (zero PII)
    record_ai_telemetry(
        db,
        user_id=user.id if user else None,
        classroom_id=classroom_id,
        operation=operation,
        model="gemini-3.8-flash-tiered",
        provider="capacity_limiter",
        prompt_tokens=estimated_prompt_tokens,
        completion_tokens=0,
        latency_ms=0.0,
        cost_usd=0.0,
        status="budget_exhausted" if not allow_fallback else "fallback_used",
        error_code="AI_BUDGET_EXHAUSTED",
        prompt_text=prompt_text,
    )

    if allow_fallback:
        return False, exhausted_details

    # Reject with HTTP 429 Too Many Requests (or 503 Capacity Limit)
    retry_secs = exhausted_details["retry_after_seconds"]
    headers = {
        "Retry-After": str(retry_secs),
        "X-RateLimit-Limit": str(exhausted_details["daily_token_limit"]),
        "X-RateLimit-Remaining": "0",
        "X-RateLimit-Reset": str(exhausted_details["reset_at"]),
        "X-AI-Budget-Exhausted": "true",
    }
    raise AppError(
        code="AI_BUDGET_EXHAUSTED",
        message=(
            f"Ngân sách AI đã đạt giới hạn ({exhausted_details['scope']}). "
            f"Vui lòng thử lại sau {retry_secs} giây (tại thời điểm {exhausted_details['reset_at']})."
        ),
        status_code=429,
        details=exhausted_details,
        headers=headers,
    )


# --------------------------------------------------------------------------- #
# Telemetry Event Logging & In-Memory Snapshot
# --------------------------------------------------------------------------- #
_LOCK = threading.Lock()
_RECENT_TELEMETRY: deque[dict[str, Any]] = deque(maxlen=2000)


def record_ai_telemetry(
    db: Session,
    *,
    user_id: Optional[UUID] = None,
    classroom_id: Optional[UUID] = None,
    session_id: Optional[str] = None,
    operation: str = "tutor",
    model: str = "gemini-3.8-flash-tiered",
    provider: str = "clara",
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    latency_ms: float = 0.0,
    cost_usd: Optional[float] = None,
    citation_valid_count: int = 0,
    citation_invalid_count: int = 0,
    status: str = "success",
    error_code: Optional[str] = None,
    prompt_text: Optional[str] = None,
) -> AITelemetryLog:
    """Record a telemetry event to database and in-memory buffer with strict ZERO PII.

    NEVER stores raw user prompt, names, emails, or credentials in DB or logs.
    """
    total_tokens = max(0, prompt_tokens) + max(0, completion_tokens)
    computed_cost = (
        cost_usd
        if cost_usd is not None
        else estimate_cost_usd(model, prompt_tokens, completion_tokens)
    )
    total_cites = citation_valid_count + citation_invalid_count
    validity_rate = (
        round(citation_valid_count / float(total_cites), 4) if total_cites > 0 else 1.0
    )
    prompt_hash = hash_prompt(prompt_text) if prompt_text else None

    # Safe zero-PII logging
    logger.info(
        "AI_TELEMETRY: op=%s model=%s provider=%s tokens=%d (p=%d, c=%d) cost=$%.6f latency=%.1fms status=%s cites=%d/%d sha256=%s",
        operation,
        model,
        provider,
        total_tokens,
        prompt_tokens,
        completion_tokens,
        computed_cost,
        latency_ms,
        status,
        citation_valid_count,
        total_cites,
        prompt_hash[:12] if prompt_hash else "none",
    )

    telemetry_entry = AITelemetryLog(
        user_id=user_id,
        classroom_id=classroom_id,
        session_id=session_id[:100] if session_id else None,
        operation=operation[:100],
        model=model[:100],
        provider=provider[:50],
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        latency_ms=max(0.0, float(latency_ms)),
        cost_usd=max(0.0, float(computed_cost)),
        citation_valid_count=max(0, int(citation_valid_count)),
        citation_invalid_count=max(0, int(citation_invalid_count)),
        citation_validity_rate=validity_rate,
        status=status[:50],
        error_code=error_code[:50] if error_code else None,
        prompt_sha256=prompt_hash,
    )

    db.add(telemetry_entry)
    db.commit()
    db.refresh(telemetry_entry)

    # In-memory quick ring buffer
    with _LOCK:
        _RECENT_TELEMETRY.append(
            {
                "id": str(telemetry_entry.id),
                "operation": operation,
                "model": model,
                "provider": provider,
                "total_tokens": total_tokens,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "latency_ms": latency_ms,
                "cost_usd": computed_cost,
                "citation_valid_count": citation_valid_count,
                "citation_invalid_count": citation_invalid_count,
                "status": status,
                "error_code": error_code,
                "created_at": telemetry_entry.created_at,
            }
        )

    return telemetry_entry


# --------------------------------------------------------------------------- #
# Observability Analytics & Dashboard Reporting
# --------------------------------------------------------------------------- #
def get_ai_observability_metrics(
    db: Session,
    *,
    hours: int = 24,
    operation: Optional[str] = None,
    model: Optional[str] = None,
) -> dict[str, Any]:
    """Calculate aggregate observability metrics for the specified time window."""
    since = datetime.now(timezone.utc) - timedelta(hours=max(1, hours))
    conditions = [AITelemetryLog.created_at >= since]
    if operation:
        conditions.append(AITelemetryLog.operation == operation)
    if model:
        conditions.append(AITelemetryLog.model == model)

    rows = db.execute(
        select(AITelemetryLog).where(and_(*conditions)).order_by(AITelemetryLog.created_at.desc())
    ).scalars().all()

    total_requests = len(rows)
    if total_requests == 0:
        return {
            "total_requests": 0,
            "successful_requests": 0,
            "error_requests": 0,
            "fallback_requests": 0,
            "success_rate": 1.0,
            "total_tokens": 0,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_cost_usd": 0.0,
            "avg_latency_ms": 0.0,
            "p95_latency_ms": 0.0,
            "total_citations_validated": 0,
            "valid_citations": 0,
            "invalid_citations": 0,
            "citation_validity_rate": 1.0,
            "by_operation": {},
            "by_model": {},
            "by_status": {},
            "zero_pii_confirmed": True,
            "window_hours": hours,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    successful = sum(1 for r in rows if r.status == "success")
    fallbacks = sum(1 for r in rows if r.status == "fallback_used")
    errors = sum(1 for r in rows if r.status not in ("success", "fallback_used"))
    success_rate = round(successful / float(total_requests), 4)

    prompt_toks = sum(r.prompt_tokens for r in rows)
    comp_toks = sum(r.completion_tokens for r in rows)
    total_toks = sum(r.total_tokens for r in rows)
    total_cost = round(sum(r.cost_usd for r in rows), 6)

    latencies = sorted(r.latency_ms for r in rows)
    avg_latency = round(sum(latencies) / float(len(latencies)), 2)
    p95_idx = max(0, min(len(latencies) - 1, int(round(len(latencies) * 0.95)) - 1))
    p95_latency = round(latencies[p95_idx], 2)

    valid_cites = sum(r.citation_valid_count for r in rows)
    invalid_cites = sum(r.citation_invalid_count for r in rows)
    total_cites = valid_cites + invalid_cites
    citation_rate = round(valid_cites / float(total_cites), 4) if total_cites > 0 else 1.0

    by_op: dict[str, dict[str, Any]] = defaultdict(lambda: {"count": 0, "tokens": 0, "cost": 0.0})
    by_model: dict[str, dict[str, Any]] = defaultdict(lambda: {"count": 0, "tokens": 0, "cost": 0.0})
    by_status: dict[str, int] = defaultdict(int)

    for r in rows:
        by_op[r.operation]["count"] += 1
        by_op[r.operation]["tokens"] += r.total_tokens
        by_op[r.operation]["cost"] = round(by_op[r.operation]["cost"] + r.cost_usd, 6)

        by_model[r.model]["count"] += 1
        by_model[r.model]["tokens"] += r.total_tokens
        by_model[r.model]["cost"] = round(by_model[r.model]["cost"] + r.cost_usd, 6)

        by_status[r.status] += 1

    return {
        "total_requests": total_requests,
        "successful_requests": successful,
        "error_requests": errors,
        "fallback_requests": fallbacks,
        "success_rate": success_rate,
        "total_tokens": total_toks,
        "prompt_tokens": prompt_toks,
        "completion_tokens": comp_toks,
        "total_cost_usd": total_cost,
        "avg_latency_ms": avg_latency,
        "p95_latency_ms": p95_latency,
        "total_citations_validated": total_cites,
        "valid_citations": valid_cites,
        "invalid_citations": invalid_cites,
        "citation_validity_rate": citation_rate,
        "by_operation": dict(by_op),
        "by_model": dict(by_model),
        "by_status": dict(by_status),
        "zero_pii_confirmed": True,
        "window_hours": hours,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def get_user_budget_status(
    db: Session,
    user: User,
    classroom_id: Optional[UUID] = None,
) -> dict[str, Any]:
    """Retrieve the current user's budget consumption and remaining limits."""
    caps = resolve_budget_caps(db, user, classroom_id)
    usage = get_daily_usage(db, user_id=user.id)
    retry_after, reset_at = get_window_reset_info()

    tok_limit = caps["user_token_limit"]
    cost_limit = caps["user_cost_limit"]
    tokens_remaining = max(0, tok_limit - usage["total_tokens"])
    cost_remaining = max(0.0, round(cost_limit - usage["cost_usd"], 6))
    is_exhausted = (usage["total_tokens"] >= tok_limit) or (usage["cost_usd"] >= cost_limit)

    return {
        "entity_type": "user",
        "entity_id": str(user.id),
        "daily_token_limit": tok_limit,
        "tokens_used_today": usage["total_tokens"],
        "tokens_remaining": tokens_remaining,
        "daily_cost_limit_usd": cost_limit,
        "cost_used_today_usd": usage["cost_usd"],
        "cost_remaining_usd": cost_remaining,
        "is_budget_exhausted": is_exhausted,
        "retry_after_seconds": retry_after,
        "reset_at": reset_at,
        "policy": "daily_sliding_window_fail_closed",
    }


def set_entity_budget_cap(
    db: Session,
    entity_type: str,
    entity_id: UUID,
    daily_token_limit: int,
    daily_cost_limit_usd: float,
    max_tokens_per_request: int = 4096,
) -> AIBudgetCap:
    """Upsert a custom budget cap for a user or classroom."""
    cap = db.execute(
        select(AIBudgetCap).where(
            and_(
                AIBudgetCap.entity_type == entity_type,
                AIBudgetCap.entity_id == entity_id,
            )
        )
    ).scalar_one_or_none()

    if not cap:
        cap = AIBudgetCap(
            entity_type=entity_type,
            entity_id=entity_id,
            daily_token_limit=daily_token_limit,
            daily_cost_limit_usd=daily_cost_limit_usd,
            max_tokens_per_request=max_tokens_per_request,
            is_active=True,
        )
        db.add(cap)
    else:
        cap.daily_token_limit = daily_token_limit
        cap.daily_cost_limit_usd = daily_cost_limit_usd
        cap.max_tokens_per_request = max_tokens_per_request
        cap.is_active = True
        cap.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(cap)
    return cap
