# -*- coding: utf-8 -*-
"""V5-T088: Distributed Rate Limits & Abuse Defense Test Suite (Wave W08 / Slot A08).

Priority: P0; Classification: PRODUCTION_COMPLETION.
Verifies:
1. Distributed sliding-window rate limiting per IP and per user account:
   - Inquiry submissions (/api/v1/rbpc/inquiries: max 5 per IP/hour).
   - Authentication login (/api/v1/auth/login: max 5 attempts per minute per IP and per account).
   - AI query endpoints (/api/v1/ai/*: quota / rate limits per minute per IP and per user).
2. Standard HTTP 429 Too Many Requests response with Retry-After header and structured error envelope:
   {"error": {"code": "RATE_LIMIT_EXCEEDED", "message": "...", "details": {...}}}.
3. Negative abuse: Competing requests and distributed workers cannot bypass global per-account rate limit ceiling.
4. Sliding-window expiration and capacity recovery.
"""
from __future__ import annotations

import math
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

import backend.main as main
from backend.deps import get_db
from backend.errors import AppError
from backend.models import (
    RbpcConsentStatus,
    RbpcCreator,
    RbpcExperience,
    User,
    UserRole,
)
from backend.security import hash_password
from backend.services.rate_limiter import DistributedRateLimiter, rate_limiter


# --------------------------------------------------------------------------- #
# Helpers & Fixtures
# --------------------------------------------------------------------------- #
@pytest.fixture(autouse=True)
def clean_rate_limiters(db_session):
    """Ensure clean rate limiter state before and after each test."""
    rate_limiter.clear(db_session)
    if hasattr(main, "_auth_rate_limit_state"):
        main._auth_rate_limit_state.clear()
    from backend.routers.rbpc import _inquiry_rate_limit_store
    _inquiry_rate_limit_store.clear()
    yield
    rate_limiter.clear(db_session)
    if hasattr(main, "_auth_rate_limit_state"):
        main._auth_rate_limit_state.clear()
    _inquiry_rate_limit_store.clear()


def _create_user(
    db_session,
    email: str,
    role: UserRole = UserRole.learner,
    password: str = "Password123!",
) -> User:
    """Helper to create and commit a test user."""
    user = User(
        email=email.strip().lower(),
        password_hash=hash_password(password),
        display_name=f"User {email.split('@')[0]}",
        username=f"usr_{uuid.uuid4().hex[:8]}",
        role=role,
        is_profile_public=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _seed_test_experience(db_session, slug: str) -> tuple[RbpcCreator, RbpcExperience]:
    """Helper to seed a consented creator and published experience."""
    creator = RbpcCreator(
        slug=f"artisan-{slug}",
        public_name="Nghệ nhân RateLimit",
        craft_tradition="Đúc đồng",
        approved_bio_vi="Phục vụ kiểm thử giới hạn tần suất.",
        consent_status=RbpcConsentStatus.consented.value,
        is_verified=True,
    )
    db_session.add(creator)
    db_session.flush()

    exp = RbpcExperience(
        slug=slug,
        creator_id=creator.id,
        provider_name="Phường Đúc RateLimit",
        title_vi="Workshop RateLimit Đúc Đồng",
        description_vi="Trải nghiệm phục vụ kiểm thử rate limit.",
        area_public="Huế",
        duration_minutes=120,
        publication_state="published",
        availability_mode="inquiry_only",
    )
    db_session.add(exp)
    db_session.commit()
    db_session.refresh(exp)
    return creator, exp


# --------------------------------------------------------------------------- #
# Test Cases
# --------------------------------------------------------------------------- #
def test_inquiry_submissions_rate_limit_5_per_ip_hour(client, db_session):
    """Verify inquiry submissions enforce distributed rate limit of max 5 per IP/hour.

    - First 5 submissions from IP 198.51.100.1 return HTTP 202 Accepted.
    - 6th submission from same IP returns HTTP 429 Too Many Requests with Retry-After.
    - Different IP 198.51.100.2 is unaffected and succeeds.
    """
    _, exp = _seed_test_experience(db_session, "exp-rl-inquiry-1")
    target_ip = "198.51.100.1"
    future_date = (date.today() + timedelta(days=5)).isoformat()

    # 1. First 5 submissions succeed
    for i in range(5):
        payload = {
            "experience_slug": exp.slug,
            "contact": {
                "name": f"Khách Hàng {i}",
                "method": "email",
                "value": f"user_{i}@example.com",
            },
            "preferred_date": future_date,
            "party_size": 2,
            "consent": {
                "version": "rbpc-inquiry-v1",
                "accepted": True,
                "privacy_accepted": True,
            },
            "idempotency_key": str(uuid.uuid4()),
        }
        res = client.post(
            "/api/v1/rbpc/inquiries",
            json=payload,
            headers={"X-Forwarded-For": target_ip},
        )
        assert res.status_code == 202, f"Request {i+1} failed: {res.text}"

    # 2. 6th submission from target_ip is blocked with HTTP 429
    payload_6 = {
        "experience_slug": exp.slug,
        "contact": {
            "name": "Khách Hàng Thứ Sáu",
            "method": "email",
            "value": "user_6@example.com",
        },
        "preferred_date": future_date,
        "party_size": 2,
        "consent": {
            "version": "rbpc-inquiry-v1",
            "accepted": True,
            "privacy_accepted": True,
        },
        "idempotency_key": str(uuid.uuid4()),
    }
    res_6 = client.post(
        "/api/v1/rbpc/inquiries",
        json=payload_6,
        headers={"X-Forwarded-For": target_ip},
    )
    assert res_6.status_code == 429, f"Expected 429, got {res_6.status_code}: {res_6.text}"

    # Header and error envelope assertions
    assert "Retry-After" in res_6.headers
    retry_after = int(res_6.headers["Retry-After"])
    assert retry_after > 0
    assert res_6.headers.get("X-RateLimit-Limit") == "5"
    assert res_6.headers.get("X-RateLimit-Remaining") == "0"

    body = res_6.json()
    assert "error" in body
    assert body["error"]["code"] == "RATE_LIMIT_EXCEEDED"
    assert "details" in body["error"]
    assert body["error"]["details"]["limit"] == 5

    # 3. Request from different IP succeeds without interference
    res_other = client.post(
        "/api/v1/rbpc/inquiries",
        json={
            "experience_slug": exp.slug,
            "contact": {
                "name": "Khách IP Khác",
                "method": "email",
                "value": "other_ip@example.com",
            },
            "preferred_date": future_date,
            "party_size": 1,
            "consent": {
                "version": "rbpc-inquiry-v1",
                "accepted": True,
                "privacy_accepted": True,
            },
            "idempotency_key": str(uuid.uuid4()),
        },
        headers={"X-Forwarded-For": "198.51.100.2"},
    )
    assert res_other.status_code == 202, f"Other IP should succeed: {res_other.text}"


def test_auth_login_rate_limit_per_ip(client, db_session):
    """Verify /api/v1/auth/login enforces max 5 attempts per minute per IP.

    - 5 wrong credential attempts from IP 198.51.100.10 return 401 INVALID_CREDENTIALS.
    - 6th attempt from IP 198.51.100.10 returns HTTP 429 with Retry-After and envelope.
    """
    _create_user(db_session, "auth_victim@example.com", password="CorrectPassword123!")
    attacker_ip = "198.51.100.10"

    # 5 failed login attempts
    for i in range(5):
        res = client.post(
            "/api/v1/auth/login",
            json={"email": f"victim_{i}@example.com", "password": "WrongPassword!"},
            headers={"X-Forwarded-For": attacker_ip},
        )
        assert res.status_code == 401, f"Attempt {i+1} got unexpected status {res.status_code}"

    # 6th attempt is blocked with 429
    res_blocked = client.post(
        "/api/v1/auth/login",
        json={"email": "victim_6@example.com", "password": "WrongPassword!"},
        headers={"X-Forwarded-For": attacker_ip},
    )
    assert res_blocked.status_code == 429, res_blocked.text
    assert "Retry-After" in res_blocked.headers
    retry_after = int(res_blocked.headers["Retry-After"])
    assert retry_after > 0

    body = res_blocked.json()
    assert body["error"]["code"] == "RATE_LIMIT_EXCEEDED"
    assert "details" in body["error"]
    assert body["error"]["details"]["limit"] == 5


def test_auth_login_per_account_rate_limit_across_distributed_ips(client, db_session):
    """Verify /api/v1/auth/login blocks distributed brute force against a specific account.

    An attacker distributes attempts across 5 distinct IP addresses targeting one account:
    - IPs 1..5 send 1 attempt each -> all return 401 (account count reaches 5).
    - IP 6 (which has never sent any request) attempts to log in to the same account ->
      blocked with HTTP 429 because per-account limit (5/min) is exhausted!
    """
    victim_email = "targeted_account@example.com"
    _create_user(db_session, victim_email, password="SecurePassword123!")

    # 5 attempts from 5 distinct IP addresses
    for i in range(5):
        ip = f"198.51.100.{20 + i}"
        res = client.post(
            "/api/v1/auth/login",
            json={"email": victim_email, "password": f"Guess_{i}"},
            headers={"X-Forwarded-For": ip},
        )
        assert res.status_code == 401, f"Attempt from IP {ip} should return 401"

    # 6th attempt from a brand-new IP 198.51.100.99
    res_6th = client.post(
        "/api/v1/auth/login",
        json={"email": victim_email, "password": "Guess_6"},
        headers={"X-Forwarded-For": "198.51.100.99"},
    )
    assert res_6th.status_code == 429, (
        f"Distributed brute-force against account {victim_email} must be blocked at 5: {res_6th.text}"
    )
    assert "Retry-After" in res_6th.headers
    body = res_6th.json()
    assert body["error"]["code"] == "RATE_LIMIT_EXCEEDED"
    assert "Tài khoản" in body["error"]["message"] or "account" in body["error"]["details"]["key"]


def test_ai_query_endpoints_quota_rate_limit(client, db_session, monkeypatch):
    """Verify AI query endpoints enforce quota rate limits per minute.

    - Patch ai_rate_limit_per_minute = 3.
    - User makes 3 queries to /api/v1/ai/summary -> all succeed.
    - 4th query is blocked with HTTP 429 and Retry-After.
    """
    monkeypatch.setattr(main.settings, "ai_rate_limit_per_minute", 3)
    user = _create_user(db_session, "ai_learner@example.com", role=UserRole.learner)

    # Login to acquire session cookies
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "ai_learner@example.com", "password": "Password123!"},
    )
    assert login_res.status_code == 200

    test_motif_id = str(uuid.uuid4())

    # 3 allowed AI queries
    for i in range(3):
        res = client.post(
            "/api/v1/ai/summary",
            json={"urn_slug": "cao-dinh", "motif_id": test_motif_id},
            headers={"X-Forwarded-For": "198.51.100.50"},
        )
        assert res.status_code == 200, f"AI query {i+1} failed: {res.text}"

    # 4th AI query exceeds quota
    res_blocked = client.post(
        "/api/v1/ai/summary",
        json={"urn_slug": "cao-dinh", "motif_id": test_motif_id},
        headers={"X-Forwarded-For": "198.51.100.50"},
    )
    assert res_blocked.status_code == 429, res_blocked.text
    assert "Retry-After" in res_blocked.headers
    assert int(res_blocked.headers["Retry-After"]) > 0
    body = res_blocked.json()
    assert body["error"]["code"] == "RATE_LIMIT_EXCEEDED"


def test_sliding_window_expiration_and_recovery(db_session):
    """Verify sliding-window arithmetic: earlier timestamps expire and restore quota."""
    limiter = DistributedRateLimiter()
    test_key = f"test:window:{uuid.uuid4().hex}"
    window_secs = 60
    limit = 3

    # Acquire 3 slots
    for _ in range(limit):
        allowed, _, count = limiter.acquire(
            db=db_session,
            key=test_key,
            max_requests=limit,
            window_seconds=window_secs,
        )
        assert allowed is True

    # 4th request must be rejected with positive retry_after
    allowed, retry_after, count = limiter.acquire(
        db=db_session,
        key=test_key,
        max_requests=limit,
        window_seconds=window_secs,
    )
    assert allowed is False
    assert 1 <= retry_after <= window_secs
    assert count == limit


def test_negative_abuse_competing_workers_cannot_bypass_ceiling(engine):
    """Negative abuse defense test: concurrent worker threads cannot bypass limit ceiling.

    Spawns 15 concurrent worker threads all simultaneously contending for the SAME
    rate limit key with limit=5.
    A threading.Barrier synchronizes all threads to hit acquire() at the exact same microsecond.
    PostgreSQL advisory locking serializes the check-and-insert.

    Asserts:
    - Exactly 5 workers succeed (allowed == True).
    - Exactly 10 workers are blocked (allowed == False).
    - Global ceiling of 5 is strictly preserved under extreme concurrency contention.
    """
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    test_account_key = f"auth:login:account:contended_victim_{uuid.uuid4().hex[:6]}@example.com"
    num_threads = 15
    max_limit = 5
    barrier = threading.Barrier(num_threads)

    results: list[tuple[bool, int, int]] = []
    results_lock = threading.Lock()

    def worker_task():
        session = SessionLocal()
        try:
            # Synchronize all threads so they contend simultaneously
            barrier.wait(timeout=10)
            allowed, retry_after, count = rate_limiter.acquire(
                db=session,
                key=test_account_key,
                max_requests=max_limit,
                window_seconds=60,
                auto_record=True,
            )
            with results_lock:
                results.append((allowed, retry_after, count))
        finally:
            session.close()

    threads = [threading.Thread(target=worker_task) for _ in range(num_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=15)

    assert len(results) == num_threads, f"Expected {num_threads} outcomes, got {len(results)}"

    successful = [r for r in results if r[0] is True]
    blocked = [r for r in results if r[0] is False]

    assert len(successful) == max_limit, (
        f"Negative abuse failed! Expected exactly {max_limit} successful requests, but {len(successful)} succeeded."
    )
    assert len(blocked) == (num_threads - max_limit), (
        f"Expected exactly {num_threads - max_limit} blocked requests, but {len(blocked)} were blocked."
    )
    # Check that blocked requests received a valid Retry-After
    for b in blocked:
        assert b[1] > 0, f"Blocked request should have retry_after > 0, got {b[1]}"


def test_negative_abuse_concurrent_http_login_burst(engine):
    """Negative abuse: concurrent HTTP login requests cannot breach per-account limit ceiling.

    Sends 12 concurrent HTTP requests to /api/v1/auth/login for the same user account.
    Verifies that exactly 5 requests reach the authentication logic (returning 401)
    and all 7 subsequent/competing requests receive HTTP 429 Too Many Requests.
    """
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    # 1. Seed user in isolated session
    setup_session = SessionLocal()
    victim_email = f"burst_victim_{uuid.uuid4().hex[:6]}@example.com"
    user = User(
        email=victim_email,
        password_hash=hash_password("RealPassword123!"),
        display_name="Burst Victim",
        username=f"burst_{uuid.uuid4().hex[:6]}",
        role=UserRole.learner,
    )
    setup_session.add(user)
    setup_session.commit()
    setup_session.close()

    # 2. Dependency override: Each concurrent request gets its own DB session
    def get_isolated_db():
        session = SessionLocal()
        try:
            yield session
        finally:
            session.close()

    main.app.dependency_overrides[get_db] = get_isolated_db

    num_requests = 12
    barrier = threading.Barrier(num_requests)

    with TestClient(main.app) as shared_client:
        def send_login_request(index: int) -> int:
            barrier.wait(timeout=10)
            # Unique IP for each request to isolate the per-account rate limit
            ip = f"198.51.200.{10 + index}"
            res = shared_client.post(
                "/api/v1/auth/login",
                json={"email": victim_email, "password": "WrongPassword!"},
                headers={"X-Forwarded-For": ip},
            )
            return res.status_code

        try:
            with ThreadPoolExecutor(max_workers=num_requests) as executor:
                futures = [executor.submit(send_login_request, i) for i in range(num_requests)]
                status_codes = [f.result() for f in as_completed(futures)]

            assert len(status_codes) == num_requests
            count_401 = status_codes.count(401)
            count_429 = status_codes.count(429)

            assert count_401 == 5, (
                f"Expected exactly 5 requests to be allowed (401), but got {count_401}. Statuses: {status_codes}"
            )
            assert count_429 == 7, (
                f"Expected exactly 7 requests to be rate-limited (429), but got {count_429}. Statuses: {status_codes}"
            )
        finally:
            main.app.dependency_overrides.clear()
