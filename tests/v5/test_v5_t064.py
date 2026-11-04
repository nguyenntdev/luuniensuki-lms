# -*- coding: utf-8 -*-
"""V5-T064 (Wave W06, Slot A04): AI Provider Policy & Multi-Tier Fallback.

Audits and verifies:
1. AI Provider Policy & Configuration:
   - Primary provider ('clara') and fallback provider ('deterministic').
   - Allowed models list, timeouts, retries, rate limits, daily quotas, circuit breaker thresholds.
2. AI Model Discovery & Catalog:
   - Discovery catalog returning model tiers, capabilities, and policy authorization.
   - Enforcement rejecting unauthorized models.
3. Rate Limiter, Daily Quota, and Circuit Breaker Lifecycle:
   - In-memory sliding window rate limiter.
   - Daily token / request quota management and cost ceiling tracking.
   - Circuit breaker states: CLOSED -> OPEN -> HALF_OPEN -> CLOSED recovery.
4. Strict Negative Abuse Guardrails:
   - Provider HTTP 429 does NOT produce generic hallucination; returns labeled typed fallback with retry policy.
   - Provider HTTP 500 does NOT produce generic hallucination; returns labeled typed fallback with retry policy.
   - Provider timeout returns labeled typed fallback with status 408.
   - Tripped circuit breaker fast-fails to safe deterministic fallback without hanging or leaking secrets.
   - Queries with zero verified evidence return evidence gap refusal, never fabricated claims.
5. Cultural Bridge Integration:
   - End-to-end question dispatcher with fallback metadata propagation and retry policy.
"""
from __future__ import annotations

import time
import uuid
from typing import Any
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError

import pytest

from backend.config import settings
from backend.services import rbpc_ai
from backend.services.rbpc_ai import (
    AICircuitBreaker,
    AICircuitBreakerOpenError,
    AIProviderError,
    AIQuotaExceededError,
    AIQuotaManager,
    AIRateLimitError,
    AIRateLimiter,
    AITimeoutError,
    build_ai_retry_policy,
    discover_ai_models,
    is_model_allowed,
)


@pytest.fixture(autouse=True)
def reset_ai_state():
    """Reset singletons before and after each test."""
    rbpc_ai.ai_rate_limiter.reset()
    rbpc_ai.ai_quota_manager.reset()
    rbpc_ai.ai_circuit_breaker.reset()
    yield
    rbpc_ai.ai_rate_limiter.reset()
    rbpc_ai.ai_quota_manager.reset()
    rbpc_ai.ai_circuit_breaker.reset()


def _sample_claim_and_source():
    cid = str(uuid.uuid4())
    sid = str(uuid.uuid4())
    claim = {
        "id": cid,
        "statement_vi": "Cửu Đỉnh đúc năm 1835 dưới thời hoàng đế Minh Mạng.",
        "statement_en": "The Nine Dynastic Urns were cast in 1835 under Emperor Minh Mạng.",
        "verification_status": "expert_verified",
        "editorial_status": "published",
        "content_scope": "RBPC_HUE",
    }
    sources = {
        cid: [
            {
                "source_id": sid,
                "title": "Đại Nam Thực Lục Chính Biên",
                "locator": "Đệ nhị kỷ, quyển 162",
                "support_type": "direct",
            }
        ]
    }
    return claim, sources, cid, sid


def test_ai_provider_configuration_and_policy():
    """Verify backend/config.py defines comprehensive AI provider policy settings."""
    assert settings.ai_provider_primary == "clara"
    assert settings.ai_provider_fallback == "deterministic"
    assert "gemini-3.8-flash-tiered" in settings.ai_allowed_models_list
    assert "deepseek-v4-flash" in settings.ai_allowed_models_list
    assert "deterministic-fallback" in settings.ai_allowed_models_list

    assert settings.ai_provider_timeout_seconds >= 10
    assert settings.ai_rate_limit_per_minute > 0
    assert settings.ai_daily_request_quota >= 1000
    assert settings.ai_circuit_breaker_failure_threshold >= 2
    assert settings.ai_circuit_breaker_recovery_seconds > 0
    assert settings.ai_circuit_breaker_enabled is True
    assert settings.ai_deterministic_fallback_enabled is True


def test_ai_model_discovery_and_catalog():
    """Verify model discovery returns active catalog and respects provider policy."""
    models = discover_ai_models()
    assert len(models) >= 4

    model_ids = {m["model_id"] for m in models}
    assert "gemini-3.8-flash-tiered" in model_ids
    assert "deepseek-v4-flash" in model_ids
    assert "deterministic-fallback" in model_ids

    primary_models = [m for m in models if m["is_primary"]]
    assert len(primary_models) == 1
    assert primary_models[0]["model_id"] == settings.clara_model
    assert primary_models[0]["provider"] == "clara"

    # Test allowed model policy check
    assert is_model_allowed("gemini-3.8-flash-tiered") is True
    assert is_model_allowed("unauthorized-gpt-5-omni") is False

    # Calling chat with unauthorized model must raise ValueError
    with pytest.raises(ValueError, match="prohibited by current provider policy"):
        rbpc_ai.call_clara_gemini_chat(
            messages=[{"role": "user", "content": "hi"}],
            model="unauthorized-gpt-5-omni",
        )


def test_ai_rate_limiter_sliding_window():
    """Verify in-memory sliding window rate limiter throttles burst queries."""
    limiter = AIRateLimiter(limit_per_minute=3)
    assert limiter.limit == 3

    ok1, wait1 = limiter.acquire()
    assert ok1 is True
    assert wait1 is None

    ok2, wait2 = limiter.acquire()
    assert ok2 is True
    assert wait2 is None

    ok3, wait3 = limiter.acquire()
    assert ok3 is True
    assert wait3 is None

    # 4th request must be rejected with retry_after wait time
    ok4, wait4 = limiter.acquire()
    assert ok4 is False
    assert wait4 is not None
    assert 0 < wait4 <= 60

    # Reset allows immediate acquisition
    limiter.reset()
    ok5, wait5 = limiter.acquire()
    assert ok5 is True


def test_ai_quota_manager_and_usage_tracking():
    """Verify AI quota manager tracks tokens and stops queries at budget ceiling."""
    manager = AIQuotaManager(
        token_ceiling=1500,
        daily_request_ceiling=3,
        cost_ceiling_usd=1.0,
    )

    # First check passes
    allowed, reason = manager.check_quota(estimated_tokens=500)
    assert allowed is True
    assert reason is None

    # Record first usage
    manager.record_usage(prompt_tokens=400, completion_tokens=200, cost_usd=0.001)
    usage = manager.get_usage()
    assert usage["daily_tokens"] == 600
    assert usage["daily_requests"] == 1
    assert usage["daily_cost_usd"] == 0.001

    # Record second usage to exceed 1500 token ceiling
    manager.record_usage(prompt_tokens=600, completion_tokens=400, cost_usd=0.002)
    assert usage["daily_tokens"] <= 1600

    # Next check exceeds token ceiling
    allowed2, reason2 = manager.check_quota(estimated_tokens=500)
    assert allowed2 is False
    assert "token ceiling" in reason2.lower()


def test_ai_circuit_breaker_lifecycle():
    """Verify circuit breaker trips to OPEN on failures and recovers in HALF_OPEN."""
    cb = AICircuitBreaker(failure_threshold=2, recovery_seconds=1)
    assert cb.get_status()["state"] == AICircuitBreaker.STATE_CLOSED

    can_run, wait = cb.can_execute()
    assert can_run is True
    assert wait is None

    # Record failure 1 -> still CLOSED
    cb.record_failure(status_code=500)
    assert cb.get_status()["state"] == AICircuitBreaker.STATE_CLOSED
    assert cb.get_status()["failure_count"] == 1

    # Record failure 2 -> trips to OPEN
    cb.record_failure(status_code=500)
    assert cb.get_status()["state"] == AICircuitBreaker.STATE_OPEN

    # In OPEN state, requests are blocked with retry wait
    can_run, wait = cb.can_execute()
    assert can_run is False
    assert wait is not None
    assert 0 < wait <= 2

    # Wait for recovery timeout (1s) to enter HALF_OPEN
    time.sleep(1.05)
    can_run_half, _ = cb.can_execute()
    assert can_run_half is True
    assert cb.get_status()["state"] == AICircuitBreaker.STATE_HALF_OPEN

    # Success in HALF_OPEN resets back to CLOSED
    cb.record_success()
    assert cb.get_status()["state"] == AICircuitBreaker.STATE_CLOSED
    assert cb.get_status()["failure_count"] == 0


def test_negative_abuse_provider_429_returns_labeled_typed_fallback(monkeypatch):
    """Negative Abuse: HTTP 429 must NOT hallucinate; returns labeled typed fallback with retry policy."""
    claim, sources, cid, sid = _sample_claim_and_source()

    # Mock HTTP 429 error
    def fake_call_chat(*args, **kwargs):
        raise AIRateLimitError("Provider rate limit reached", retry_after=45)

    monkeypatch.setattr(rbpc_ai, "call_clara_gemini_chat", fake_call_chat)
    monkeypatch.setenv("CLARA_API_KEY", "test-key-429")

    result = rbpc_ai.ask_cultural_bridge(
        db=None,
        question="Cửu Đỉnh được đúc năm nào?",
        locale="vi",
        claims_override=[claim],
        sources_override=sources,
        use_llm=True,
    )

    # 1. Zero Hallucination check
    assert "Cửu Đỉnh đúc năm 1835" in result["answer_markdown"]
    assert "Minh Mạng" in result["answer_markdown"]
    assert len(result["citations"]) == 1
    assert result["citations"][0]["source_id"] == sid

    # 2. Labeled Typed Fallback check
    assert result["fallback_reason"] == "provider_rate_limited"
    assert result["provider_status_code"] == 429
    assert result["review_status"] == "provider_fallback_429"

    # 3. Retry Policy check
    retry = result["retry_policy"]
    assert retry["retryable"] is True
    assert retry["retry_after_seconds"] == 45
    assert retry["status_code"] == 429
    assert retry["strategy"] == "exponential_backoff"
    assert retry["fallback_engaged"] == "deterministic_evidence_only"

    # 4. Uncertainty note includes rate limit notice
    assert any("429" in u for u in result["uncertainties"])


def test_negative_abuse_provider_500_returns_labeled_typed_fallback(monkeypatch):
    """Negative Abuse: HTTP 500 must NOT hallucinate; returns labeled typed fallback with retry policy."""
    claim, sources, cid, sid = _sample_claim_and_source()

    def fake_call_chat(*args, **kwargs):
        raise AIProviderError("Clara internal server failure", status_code=500, retry_after=30)

    monkeypatch.setattr(rbpc_ai, "call_clara_gemini_chat", fake_call_chat)
    monkeypatch.setenv("CLARA_API_KEY", "test-key-500")

    result = rbpc_ai.ask_cultural_bridge(
        db=None,
        question="Cửu Đỉnh được đúc năm nào?",
        locale="en",
        claims_override=[claim],
        sources_override=sources,
        use_llm=True,
    )

    # 1. Zero Hallucination check
    assert "1835" in result["answer_markdown"]
    assert len(result["citations"]) == 1

    # 2. Labeled Typed Fallback check
    assert result["fallback_reason"] == "provider_error"
    assert result["provider_status_code"] == 500
    assert result["review_status"] == "provider_fallback_500"

    # 3. Retry Policy check
    retry = result["retry_policy"]
    assert retry["retryable"] is True
    assert retry["status_code"] == 500
    assert retry["retry_after_seconds"] == 30
    assert retry["strategy"] == "fixed_delay"


def test_negative_abuse_circuit_breaker_open_fast_fails_to_fallback(monkeypatch):
    """Negative Abuse: Tripped circuit breaker immediately engages safe deterministic fallback."""
    claim, sources, cid, sid = _sample_claim_and_source()

    # Pre-trip the circuit breaker
    rbpc_ai.ai_circuit_breaker._state = AICircuitBreaker.STATE_OPEN
    rbpc_ai.ai_circuit_breaker._last_failure_time = time.time()

    monkeypatch.setenv("CLARA_API_KEY", "test-key")

    result = rbpc_ai.ask_cultural_bridge(
        db=None,
        question="Cửu Đỉnh được đúc năm nào?",
        locale="vi",
        claims_override=[claim],
        sources_override=sources,
        use_llm=True,
    )

    assert result["fallback_reason"] == "provider_circuit_breaker_open"
    assert result["provider_status_code"] == 503
    assert result["review_status"] == "provider_fallback_circuit_breaker"
    assert result["retry_policy"]["retryable"] is True
    assert result["retry_policy"]["status_code"] == 503

    # Preserves authentic claims without hallucination
    assert "Cửu Đỉnh đúc năm 1835" in result["answer_markdown"]


def test_negative_abuse_timeout_returns_labeled_typed_fallback(monkeypatch):
    """Negative Abuse: Network timeout returns labeled typed fallback with status 408."""
    claim, sources, cid, sid = _sample_claim_and_source()

    def fake_call_chat(*args, **kwargs):
        raise AITimeoutError("Clara connection timed out", retry_after=15)

    monkeypatch.setattr(rbpc_ai, "call_clara_gemini_chat", fake_call_chat)
    monkeypatch.setenv("CLARA_API_KEY", "test-key")

    result = rbpc_ai.ask_cultural_bridge(
        db=None,
        question="Cửu Đỉnh được đúc năm nào?",
        locale="vi",
        claims_override=[claim],
        sources_override=sources,
        use_llm=True,
    )

    assert result["fallback_reason"] == "provider_timeout"
    assert result["provider_status_code"] == 408
    assert result["review_status"] == "provider_fallback_timeout"
    assert result["retry_policy"]["status_code"] == 408
    assert result["retry_policy"]["retry_after_seconds"] == 15


def test_answer_cultural_question_e2e_with_provider_rate_limit(monkeypatch):
    """End-to-end answer_cultural_question returns typed retry policy on provider failure."""
    claim, sources, cid, sid = _sample_claim_and_source()

    def fake_call_chat(*args, **kwargs):
        raise AIRateLimitError("Too Many Requests", retry_after=60)

    monkeypatch.setattr(rbpc_ai, "call_clara_gemini_chat", fake_call_chat)
    monkeypatch.setenv("CLARA_API_KEY", "test-key")

    response = rbpc_ai.answer_cultural_question(
        db=None,
        question="Cửu Đỉnh đúc vào năm nào?",
        locale="vi",
        claims_override=[claim],
        sources_override=sources,
        use_llm=True,
    )

    assert response["status"] in ("supported", "fallback_to_curated")
    assert response["review_status"] == "provider_fallback_429"
    assert response["fallback_reason"] == "provider_rate_limited"
    assert response["provider_status_code"] == 429
    assert response["retry_policy"]["retryable"] is True
    assert response["retry_policy"]["retry_after_seconds"] == 60
    assert "Cửu Đỉnh đúc năm 1835" in response["answer"]
    assert len(response["citations"]) == 1
    assert response["citations"][0]["source_id"] == sid


def test_negative_abuse_zero_evidence_returns_evidence_gap_refusal():
    """Negative Abuse: Questions without verified evidence return clear evidence gap refusal, never hallucinations."""
    empty_context = rbpc_ai.RBPCRetrievalContext("", claims=[], sources_by_claim={})

    # Vietnamese evidence gap refusal
    res_vi = rbpc_ai.build_rbpc_deterministic_answer(
        "Bức tranh bí mật nào được giấu trong Ngọ Môn?",
        [],
        empty_context,
        locale="vi",
    )
    assert res_vi["confidence"] == "low"
    assert "khoảng trống bằng chứng" in res_vi["answer_markdown"]
    assert "không phải là câu trả lời phỏng đoán" in res_vi["answer_markdown"]
    assert res_vi["citations"] == []
    assert res_vi["fallback_reason"] == "deterministic_evidence_only"

    # English evidence gap refusal
    res_en = rbpc_ai.build_rbpc_deterministic_answer(
        "What secret gold statue is hidden inside the palace?",
        [],
        empty_context,
        locale="en",
    )
    assert res_en["confidence"] == "low"
    assert "evidence gap" in res_en["answer_markdown"]
    assert "not an invitation to speculate" in res_en["answer_markdown"]
    assert res_en["citations"] == []
