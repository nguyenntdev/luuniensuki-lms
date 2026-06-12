"""Rate-limit integration tests for the deployed FastAPI runtime (Workstream 6).

These tests exercise the in-process fixed-window rate limiter that
``backend.main`` installs as an HTTP middleware over ``/api/v1/auth/*``
(Task 11.2). The ``client``/``db_session`` fixtures come from
``tests/backend/conftest.py`` which imports ``backend.main`` (the deployed
runtime).

Limiter mechanism (read from ``backend/main.py``)
-------------------------------------------------
* Middleware: ``rate_limit_auth_endpoints`` — applies only to paths starting
  with ``/api/v1/auth/``; all other paths pass through untouched.
* Window: a fixed 60s window (``_AUTH_RATE_LIMIT_WINDOW_SECONDS``).
* Limit: ``settings.rate_limit_requests_per_minute + settings.rate_limit_burst``
  (defaults ``60 + 10 = 70``). The limit is **read dynamically on every
  request**, so monkeypatching ``main.settings`` *after* import takes effect —
  we exploit this to shrink the limit to a small number and keep the loop fast.
* Keying: per client IP (first hop of ``X-Forwarded-For`` if present, else
  ``request.client.host``). ``TestClient`` uses a constant client host
  (``"testclient"``), so every request in a test shares one rate-limit key
  automatically; no headers are needed.
* State: a module-level dict ``main._auth_rate_limit_state`` (per-process,
  in-memory). It can leak across tests in the same process, so the autouse
  ``_reset_rate_limit_state`` fixture clears it before and after each test so
  every test starts from a clean count.
* Enablement: the limiter is **always active** (not gated by an enable flag),
  so no setting needs to be toggled to observe a 429.
* Over-limit response: HTTP 429 with a ``{"error": {"code": "RATE_LIMITED",
  ...}}`` envelope and a ``Retry-After`` header.

Requirements: 12.1, 27.1. Validates design.md "Workstream 6" rate limiting.

Fail-on-unfixed / pass-on-fixed (Req 27): on code lacking the auth rate-limit
middleware (Task 11.2), ``/api/v1/auth/login`` only ever returns its normal
status (401 for bad creds) and never 429, so the over-limit assertions FAIL.
Once the middleware is wired, request ``N+1`` returns 429 and the tests PASS.
"""

from __future__ import annotations

import pytest

import backend.main as main


# A deliberately-wrong credential payload. ``AuthLoginRequest`` requires a valid
# email and a 1..72 char password; with no matching user the login endpoint
# returns 401 INVALID_CREDENTIALS (the normal, non-rate-limited response).
_BAD_CREDENTIALS = {
    "email": "rate-limit-nobody@example.com",
    "password": "definitely-wrong-password",
}


@pytest.fixture(autouse=True)
def _reset_rate_limit_state():
    """Reset the in-memory limiter so each test starts from a clean count.

    The limiter keeps per-process state in ``main._auth_rate_limit_state``;
    without resetting it, counts would leak across tests and make assertions
    order-dependent.
    """
    main._auth_rate_limit_state.clear()
    yield
    main._auth_rate_limit_state.clear()


def _set_small_limit(monkeypatch, per_minute: int, burst: int) -> int:
    """Shrink the configured limit and return the effective limit.

    The middleware reads ``settings.rate_limit_requests_per_minute`` and
    ``settings.rate_limit_burst`` on every request, so patching them on the
    deployed ``main.settings`` instance changes the limit dynamically.
    """
    monkeypatch.setattr(main.settings, "rate_limit_requests_per_minute", per_minute)
    monkeypatch.setattr(main.settings, "rate_limit_burst", burst)
    return main.settings.rate_limit_requests_per_minute + main.settings.rate_limit_burst


def test_exceeding_auth_rate_limit_returns_429(client, monkeypatch) -> None:
    """Request ``N+1`` over the configured auth limit returns HTTP 429.

    Drives the loop count from the configured ``rate_limit_*`` settings rather
    than hardcoding: the first ``limit`` requests return their normal status
    (401 for bad creds) and the very next one is rejected with 429.

    Validates design.md Workstream 6 rate limiting. Requirements: 12.1, 27.1.
    """
    limit = _set_small_limit(monkeypatch, per_minute=2, burst=1)  # -> 3

    # The first `limit` requests are allowed through to the handler (401).
    for i in range(limit):
        response = client.post("/api/v1/auth/login", json=_BAD_CREDENTIALS)
        assert response.status_code == 401, (
            f"request {i + 1}/{limit} should be allowed (401), "
            f"got {response.status_code}: {response.text}"
        )

    # Request N+1 exceeds the window limit and is rate-limited.
    over_limit = client.post("/api/v1/auth/login", json=_BAD_CREDENTIALS)
    assert over_limit.status_code == 429, over_limit.text


def test_requests_up_to_limit_are_not_rate_limited(client, monkeypatch) -> None:
    """Exactly ``limit`` requests within the window are never 429.

    Guards the lower boundary: the limiter must not reject requests at or below
    the configured threshold.

    Requirements: 12.1, 27.1.
    """
    limit = _set_small_limit(monkeypatch, per_minute=4, burst=1)  # -> 5

    statuses = [
        client.post("/api/v1/auth/login", json=_BAD_CREDENTIALS).status_code
        for _ in range(limit)
    ]
    assert all(code != 429 for code in statuses), statuses
    # With no matching user every allowed request is a 401.
    assert all(code == 401 for code in statuses), statuses


def test_rate_limited_response_envelope_and_retry_after(client, monkeypatch) -> None:
    """The 429 carries the RATE_LIMITED error envelope and a Retry-After header.

    Requirements: 12.1, 27.1.
    """
    limit = _set_small_limit(monkeypatch, per_minute=1, burst=0)  # -> 1

    first = client.post("/api/v1/auth/login", json=_BAD_CREDENTIALS)
    assert first.status_code == 401, first.text

    blocked = client.post("/api/v1/auth/login", json=_BAD_CREDENTIALS)
    assert blocked.status_code == 429, blocked.text

    body = blocked.json()
    assert body["error"]["code"] == "RATE_LIMITED", body
    retry_after = blocked.headers.get("retry-after")
    assert retry_after is not None
    assert int(retry_after) >= 1


def test_limit_is_driven_by_settings(client, monkeypatch) -> None:
    """Raising the configured limit lets more requests through before 429.

    Confirms the limit is sourced from ``rate_limit_*`` settings (read
    dynamically) rather than a hardcoded constant: with a limit of 2 the third
    request is blocked, demonstrating the threshold tracks the setting.

    Requirements: 12.1, 27.1.
    """
    limit = _set_small_limit(monkeypatch, per_minute=2, burst=0)  # -> 2
    assert limit == 2

    assert client.post("/api/v1/auth/login", json=_BAD_CREDENTIALS).status_code == 401
    assert client.post("/api/v1/auth/login", json=_BAD_CREDENTIALS).status_code == 401
    assert client.post("/api/v1/auth/login", json=_BAD_CREDENTIALS).status_code == 429


def test_non_auth_paths_are_not_rate_limited(client, monkeypatch) -> None:
    """Non-auth paths bypass the limiter even past the auth limit.

    The middleware only guards ``/api/v1/auth/*``; ``/health`` must keep
    returning 200 regardless of how many times it is hit.

    Requirements: 12.1, 27.1.
    """
    _set_small_limit(monkeypatch, per_minute=1, burst=0)  # -> 1

    for _ in range(5):
        response = client.get("/health")
        assert response.status_code == 200, response.text
