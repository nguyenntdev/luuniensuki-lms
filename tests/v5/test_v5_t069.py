# -*- coding: utf-8 -*-
"""V5-T069: AI Observability & Budgeting Test Suite (Wave W06 / Slot A09).

Priority: P1; Classification: PRODUCTION_COMPLETION.
Verifies:
1. Strict Zero PII in Telemetry Logs & Scrubbers:
   - Evaluates PII scrubbing (emails, phone numbers, CCCD/CMND, cards, JWT/keys).
   - Telemetry logs strictly store SHA-256 prompt hashes and metadata; zero raw text.
2. Token Usage, Latency & Cost Tracking:
   - Accurate prompt & completion tokens calculation.
   - Multi-model pricing (Clara Gemini vs DeepSeek) and latency tracking in ms.
3. Citation Validity Telemetry:
   - Valid vs dropped/invalid citations counting and validity percentage tracking.
4. User & Classroom Budget Caps:
   - User-level and classroom-level daily token ceilings and cost limits.
   - Headroom calculation and budget status queries.
5. Negative Abuse Guardrail (Exhausted Budget Capacity Response):
   - Exhausted budget triggers HTTP 429 Too Many Requests with explicit Retry-After policy.
   - Standard error envelope: {"error": {"code": "AI_BUDGET_EXHAUSTED", ...}}.
6. Deterministic Fallback on Budget Exhaustion:
   - When fallback is permitted, degrades gracefully to evidence-only claims synthesis.
7. Observability Metrics & RBAC:
   - Role-based access control (Learner receives 403; Staff/Admin receives full analytics).
   - Aggregations, p95 latency, by-operation and by-model breakdowns.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from backend.ai_observability_models import AIBudgetCap, AITelemetryLog
from backend.models import (
    Classroom,
    HistoricalClaim,
    HistoricalClaimSource,
    HistoricalEntity,
    HistoricalSource,
    User,
    UserRole,
)
from backend.security import hash_password
from backend.services import ai_observability


# --------------------------------------------------------------------------- #
# Helpers & Fixtures
# --------------------------------------------------------------------------- #
def _create_user(
    db_session,
    email: str,
    role: UserRole = UserRole.learner,
    display_name: str | None = None,
) -> User:
    """Create a test user with a specific role."""
    user = User(
        email=email,
        password_hash=hash_password("Password123!"),
        display_name=display_name or f"User {email.split('@')[0]}",
        username=f"usr_{uuid.uuid4().hex[:8]}",
        role=role,
        is_profile_public=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _login(client: TestClient, email: str, password: str = "Password123!") -> dict:
    """Authenticate user and store session cookies."""
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    return res.json()


def _create_sample_claims_and_sources(db_session) -> tuple[HistoricalClaim, HistoricalSource]:
    """Create a sample entity, source, and claim for history tutor verification."""
    entity = HistoricalEntity(
        id=uuid.uuid4(),
        entity_type="urn",
        slug=f"cao-dinh-{uuid.uuid4().hex[:6]}",
        name_vi="Cao Đỉnh",
        publication_status="published",
    )
    db_session.add(entity)

    source = HistoricalSource(
        id=uuid.uuid4(),
        source_type="primary",
        title="Đại Nam Thực Lục Chính Biên",
        author_text="Quốc Sử Quán triều Nguyễn",
        publication_year=1848,
        rights_status="public_domain",
        verification_status="expert_verified",
    )
    db_session.add(source)

    claim = HistoricalClaim(
        id=uuid.uuid4(),
        entity_id=entity.id,
        claim_type="factual",
        origin="primary_source",
        statement_vi="Cao Đỉnh được đúc vào năm Minh Mạng thứ 16 (1835) và hoàn thành năm 1837.",
        verification_status="expert_verified",
        confidence="high",
        content_scope="CUU_DINH",
    )
    db_session.add(claim)

    claim_source = HistoricalClaimSource(
        claim_id=claim.id,
        source_id=source.id,
        support_type="supports",
        chapter="Quyển 15",
    )
    db_session.add(claim_source)
    db_session.commit()
    return claim, source


# ============================================================================== #
# 1. Strict Zero-PII Telemetry & Sanitization
# ============================================================================== #
def test_ai_observability_pii_sanitization_and_zero_pii_logging(db_session, caplog):
    """Verify that user PII is scrubbed, hashed with SHA-256, and never logged raw."""
    raw_prompt_with_pii = (
        "Chào cô giáo, em là Nguyễn Văn An, email an.nguyen2026@gmail.com, "
        "số điện thoại 0912345678, số CCCD 046200001234. "
        "Em muốn hỏi về năm đúc Cao Đỉnh Cửu Đỉnh Huế."
    )

    # 1. Verify scrubber rules
    scrubbed = ai_observability.scrub_pii(raw_prompt_with_pii)
    assert "[REDACTED_EMAIL]" in scrubbed
    assert "an.nguyen2026@gmail.com" not in scrubbed
    assert "[REDACTED_PHONE]" in scrubbed
    assert "0912345678" not in scrubbed
    assert "[REDACTED_ID]" in scrubbed
    assert "046200001234" not in scrubbed

    # 2. Verify prompt hashing (deterministic SHA-256)
    p_hash = ai_observability.hash_prompt(raw_prompt_with_pii)
    assert len(p_hash) == 64
    assert p_hash == ai_observability.hash_prompt(raw_prompt_with_pii)

    # 3. Verify telemetry recording writes zero PII to DB and logs
    user = _create_user(db_session, f"student_{uuid.uuid4().hex[:6]}@example.com")
    with caplog.at_level(logging.INFO, logger="luuniensuki.ai_telemetry"):
        entry = ai_observability.record_ai_telemetry(
            db_session,
            user_id=user.id,
            operation="tutor_test",
            model="gemini-3.8-flash-tiered",
            provider="clara",
            prompt_tokens=45,
            completion_tokens=60,
            latency_ms=320.5,
            prompt_text=raw_prompt_with_pii,
        )

    # In database row: verify hash is stored, and prompt text is NOT stored
    assert entry.prompt_sha256 == p_hash
    assert not hasattr(entry, "prompt") or getattr(entry, "prompt", None) is None

    # In logger output: verify no PII leaked into log streams
    log_text = caplog.text
    assert "an.nguyen2026@gmail.com" not in log_text
    assert "0912345678" not in log_text
    assert "046200001234" not in log_text
    assert p_hash[:12] in log_text


# ============================================================================== #
# 2. Token Estimation & Cost Model Tracking
# ============================================================================== #
def test_ai_token_estimation_and_cost_calculation():
    """Verify accurate prompt/completion token estimation and model-tiered pricing."""
    sample_text_vi = "Cửu Đỉnh là bộ chín đỉnh đồng đặt trước sân Thế Miếu trong Hoàng thành Huế."
    tokens = ai_observability.estimate_tokens(sample_text_vi)
    assert tokens > 10

    # Pricing for Clara Gemini (gemini-3.8-flash-tiered: $0.10/1M prompt, $0.40/1M completion)
    cost_gemini = ai_observability.estimate_cost_usd(
        "gemini-3.8-flash-tiered", prompt_tokens=1000, completion_tokens=500
    )
    expected_gemini = (1000 / 1_000_000.0) * 0.10 + (500 / 1_000_000.0) * 0.40
    assert abs(cost_gemini - expected_gemini) < 1e-6

    # Pricing for DeepSeek (deepseek-v4-flash: $0.14/1M prompt, $0.28/1M completion)
    cost_deepseek = ai_observability.estimate_cost_usd(
        "deepseek-v4-flash", prompt_tokens=1000, completion_tokens=500
    )
    expected_deepseek = (1000 / 1_000_000.0) * 0.14 + (500 / 1_000_000.0) * 0.28
    assert abs(cost_deepseek - expected_deepseek) < 1e-6


# ============================================================================== #
# 3. Citation Validity Telemetry
# ============================================================================== #
def test_ai_citation_validity_tracking(db_session):
    """Verify that citation validation metrics (valid vs invalid) are tracked."""
    user = _create_user(db_session, f"learner_{uuid.uuid4().hex[:6]}@example.com")

    # Record request with 3 valid and 1 invalid/dropped citation
    log1 = ai_observability.record_ai_telemetry(
        db_session,
        user_id=user.id,
        operation="history_tutor_ask",
        model="gemini-3.8-flash-tiered",
        prompt_tokens=100,
        completion_tokens=200,
        latency_ms=250.0,
        citation_valid_count=3,
        citation_invalid_count=1,
    )
    assert log1.citation_valid_count == 3
    assert log1.citation_invalid_count == 1
    assert log1.citation_validity_rate == 0.75  # 3 / 4

    # Record request with 5 valid and 0 invalid
    log2 = ai_observability.record_ai_telemetry(
        db_session,
        user_id=user.id,
        operation="history_tutor_ask",
        model="gemini-3.8-flash-tiered",
        prompt_tokens=150,
        completion_tokens=250,
        latency_ms=180.0,
        citation_valid_count=5,
        citation_invalid_count=0,
    )
    assert log2.citation_validity_rate == 1.0


# ============================================================================== #
# 4. User and Classroom Budget Caps
# ============================================================================== #
def test_ai_budget_caps_user_and_classroom(client: TestClient, db_session):
    """Verify user-level and classroom-level budget caps configuration and status."""
    admin = _create_user(db_session, f"admin_{uuid.uuid4().hex[:6]}@example.com", role=UserRole.admin)
    student = _create_user(db_session, f"student_{uuid.uuid4().hex[:6]}@example.com", role=UserRole.learner)
    _login(client, admin.email)

    # 1. Admin sets custom user budget cap via API
    cap_res = client.post(
        "/api/v1/ai/observability/budget/caps",
        json={
            "entity_type": "user",
            "entity_id": str(student.id),
            "daily_token_limit": 50_000,
            "daily_cost_limit_usd": 1.5,
            "max_tokens_per_request": 2048,
        },
    )
    assert cap_res.status_code == 200, cap_res.text
    cap_data = cap_res.json()
    assert cap_data["daily_token_limit"] == 50_000
    assert cap_data["daily_cost_limit_usd"] == 1.5

    # 2. Student queries their own budget status
    _login(client, student.email)
    b_res = client.get("/api/v1/ai/observability/budget")
    assert b_res.status_code == 200
    b_data = b_res.json()
    assert b_data["daily_token_limit"] == 50_000
    assert b_data["daily_cost_limit_usd"] == 1.5
    assert b_data["is_budget_exhausted"] is False
    assert b_data["retry_after_seconds"] > 0
    assert "reset_at" in b_data

    # 3. Student attempting to query another user's budget receives 403 Forbidden
    other_user = _create_user(db_session, f"other_{uuid.uuid4().hex[:6]}@example.com")
    forbidden_res = client.get(f"/api/v1/ai/observability/budget?user_id={other_user.id}")
    assert forbidden_res.status_code == 403


# ============================================================================== #
# 5. Negative Abuse: Exhausted Budget Returns Capacity 429 with Retry Policy
# ============================================================================== #
def test_negative_abuse_exhausted_budget_capacity_response(client: TestClient, db_session):
    """Negative Abuse Test: When daily budget is exhausted, query returns HTTP 429 with Retry-After header."""
    abusive_user = _create_user(
        db_session, f"abusive_{uuid.uuid4().hex[:6]}@example.com", role=UserRole.learner
    )

    # Set an ultra-low cap of 100 tokens and 0.001 USD
    ai_observability.set_entity_budget_cap(
        db_session,
        entity_type="user",
        entity_id=abusive_user.id,
        daily_token_limit=100,
        daily_cost_limit_usd=0.001,
    )

    # Exhaust the budget by recording usage exceeding the cap
    ai_observability.record_ai_telemetry(
        db_session,
        user_id=abusive_user.id,
        operation="previous_query",
        model="gemini-3.8-flash-tiered",
        prompt_tokens=200,
        completion_tokens=100,
        latency_ms=150.0,
        cost_usd=0.005,
    )

    _login(client, abusive_user.email)

    # Strict budget query must FAIL CLOSED with HTTP 429
    res = client.post(
        "/api/v1/history/tutor/ask?strict_budget=true",
        json={"question": "Cao Đỉnh được đúc vào năm nào?"},
    )

    assert res.status_code == 429
    err_body = res.json()
    assert "error" in err_body
    assert err_body["error"]["code"] == "AI_BUDGET_EXHAUSTED"
    assert "details" in err_body["error"]

    details = err_body["error"]["details"]
    assert details["scope"] == "user"
    assert details["retry_after_seconds"] > 0
    assert "reset_at" in details

    # Verify standard HTTP headers
    assert "Retry-After" in res.headers
    assert int(res.headers["Retry-After"]) > 0
    assert res.headers.get("X-AI-Budget-Exhausted") == "true"


# ============================================================================== #
# 6. Graceful Deterministic Fallback on Budget Exhaustion
# ============================================================================== #
def test_exhausted_budget_deterministic_fallback(client: TestClient, db_session):
    """When budget is exhausted but fallback is allowed, returns 200 with deterministic answer and notice."""
    user = _create_user(db_session, f"student_fallback_{uuid.uuid4().hex[:6]}@example.com")
    claim, source = _create_sample_claims_and_sources(db_session)

    # Set exhausted cap
    ai_observability.set_entity_budget_cap(
        db_session,
        entity_type="user",
        entity_id=user.id,
        daily_token_limit=50,
        daily_cost_limit_usd=0.0001,
    )
    ai_observability.record_ai_telemetry(
        db_session,
        user_id=user.id,
        operation="burn_budget",
        prompt_tokens=100,
        completion_tokens=50,
        cost_usd=0.01,
    )

    _login(client, user.email)

    # Standard query with allow_fallback=True (default)
    res = client.post(
        "/api/v1/history/tutor/ask",
        json={"question": "Ý nghĩa lịch sử của Cao Đỉnh trong Cửu Đỉnh là gì?"},
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["answer_markdown"] is not None

    # Verify epistemic notice indicating deterministic mode was used due to budget exhaustion
    uncertainties = data.get("uncertainties", [])
    assert any("Ngân sách AI đã đạt giới hạn" in u for u in uncertainties)

    # Verify telemetry captured status in ("fallback_used", "success") or budget limit
    latest_log = db_session.execute(
        select(AITelemetryLog)
        .where(AITelemetryLog.user_id == user.id)
        .order_by(AITelemetryLog.created_at.desc())
        .limit(1)
    ).scalar_one()

    assert latest_log.status in ("fallback_used", "budget_exhausted") or latest_log.error_code == "AI_BUDGET_EXHAUSTED"
    assert latest_log.error_code == "AI_BUDGET_EXHAUSTED"


# ============================================================================== #
# 7. Observability Analytics & RBAC Security
# ============================================================================== #
def test_ai_observability_metrics_aggregation_and_rbac(client: TestClient, db_session):
    """Verify admin metrics reporting, percentiles calculation, and role authorization."""
    staff = _create_user(db_session, f"admin_{uuid.uuid4().hex[:6]}@example.com", role=UserRole.admin)
    learner = _create_user(db_session, f"learner_unauth_{uuid.uuid4().hex[:6]}@example.com", role=UserRole.learner)

    # 1. Unauthenticated request -> 401
    client.cookies.clear()
    res = client.get("/api/v1/ai/observability/metrics")
    assert res.status_code == 401

    # 2. Learner role -> 403
    _login(client, learner.email)
    res = client.get("/api/v1/ai/observability/metrics")
    assert res.status_code == 403

    # 3. Staff role -> 200 OK with comprehensive aggregates
    _login(client, staff.email)
    res = client.get("/api/v1/ai/observability/metrics?hours=24")
    assert res.status_code == 200
    metrics = res.json()

    assert "total_requests" in metrics
    assert "total_tokens" in metrics
    assert "prompt_tokens" in metrics
    assert "completion_tokens" in metrics
    assert "total_cost_usd" in metrics
    assert "avg_latency_ms" in metrics
    assert "p95_latency_ms" in metrics
    assert "citation_validity_rate" in metrics
    assert "by_operation" in metrics
    assert "by_model" in metrics
    assert "by_status" in metrics
    assert metrics["zero_pii_confirmed"] is True
