"""Transport-security tests for the deployed FastAPI runtime (Workstream 2).

These tests exercise the security headers middleware and the secure-cookie
behavior that ``backend.main`` configures on its FastAPI app. The
``client``/``db_session`` fixtures come from ``tests/backend/conftest.py`` which
imports ``backend.main`` (the deployed runtime).

Coverage:

* Correctness Property 10 (transport security): every response carries
  ``Content-Security-Policy``, ``Strict-Transport-Security``, and
  ``X-Content-Type-Options: nosniff`` — asserted on a 200 response, a 401, and a
  404 so the assertion is robust regardless of route reachability.
* Secure auth cookie in production: when the runtime resolves the secure-cookie
  flag to ``True`` (production + ``cookie_secure=True``), the ``Set-Cookie``
  header for the access cookie carries the ``Secure`` attribute.

Requirements: 6.1, 25.1, 27.1.

Fail-on-unfixed / pass-on-fixed (Req 27): on code lacking the security-headers
middleware (Task 4.3) the header assertions FAIL because the headers are absent;
once the middleware is wired they PASS. On code that does not resolve
``cookie_secure`` to ``True`` in production (Task 4.2), the cookie assertion
FAILS because the ``Set-Cookie`` string omits ``Secure``; once the secure flag
is resolved it PASSES.
"""

from __future__ import annotations

import backend.main as main


# Header names the middleware injects on every response (Requirements 25.1).
CSP = "content-security-policy"
HSTS = "strict-transport-security"
XCTO = "x-content-type-options"


def _assert_security_headers(response) -> None:
    """Assert the three baseline security headers are present and well-formed."""
    assert response.headers.get(XCTO) == "nosniff"

    hsts = response.headers.get(HSTS)
    assert hsts is not None
    assert "max-age=" in hsts

    csp = response.headers.get(CSP)
    assert csp is not None
    assert "default-src 'self'" in csp


def test_security_headers_present_on_200(client) -> None:
    """A successful (200) response carries CSP, HSTS, and X-Content-Type-Options.

    Validates Correctness Property 10. Requirements: 25.1, 27.1.
    """
    response = client.get("/health")
    assert response.status_code == 200, response.text
    _assert_security_headers(response)


def test_security_headers_present_on_401(client) -> None:
    """An unauthenticated (401) response still passes through the middleware.

    Asserting on a 401 makes the contract robust: the headers must be applied
    uniformly across all routes, including rejected requests.

    Validates Correctness Property 10. Requirements: 25.1, 27.1.
    """
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401, response.text
    _assert_security_headers(response)


def test_security_headers_present_on_404(client) -> None:
    """A 404 for an unknown route still carries the security headers.

    Validates Correctness Property 10. Requirements: 25.1, 27.1.
    """
    response = client.get("/this-route-does-not-exist")
    assert response.status_code == 404, response.text
    _assert_security_headers(response)


def _get_access_set_cookie(response) -> str | None:
    """Return the raw ``Set-Cookie`` header for the access cookie, if present.

    TestClient/httpx expose multiple ``Set-Cookie`` headers; we scan all of them
    for the configured access-cookie name and return the matching raw string.
    """
    name = main.settings.access_cookie_name
    for raw in response.headers.get_list("set-cookie"):
        if raw.startswith(f"{name}="):
            return raw
    return None


def test_auth_cookie_is_secure_in_production(client, monkeypatch) -> None:
    """In production the access cookie's ``Set-Cookie`` carries ``Secure``.

    Forces the runtime into production with the secure flag enabled, then
    registers a user (which calls ``_set_auth_cookies``) and asserts the access
    cookie's ``Set-Cookie`` header includes the ``Secure`` attribute. TestClient
    speaks http, but Starlette still emits ``Secure`` in the header string
    regardless of scheme, so asserting on the header is valid.

    Validates the secure-cookie remediation (Task 4.2). Requirements: 6.1, 27.1.
    """
    # Force the deployed settings instance into a production posture with the
    # secure-cookie flag explicitly enabled. ``cookie_secure_effective`` returns
    # the explicit override when set, so this resolves to True. Assigning
    # ``environment``/``cookie_secure`` does not re-run the model validator, so
    # the production secret checks are not triggered here.
    monkeypatch.setattr(main.settings, "environment", "production")
    monkeypatch.setattr(main.settings, "cookie_secure", True)

    assert main.settings.is_production is True
    assert main.settings.cookie_secure_effective is True

    register = client.post(
        "/api/v1/auth/register",
        json={
            "email": "secure-cookie@example.com",
            "password": "password123",
            "display_name": "Secure Cookie",
        },
    )
    assert register.status_code == 201, register.text

    access_cookie = _get_access_set_cookie(register)
    assert access_cookie is not None, "access cookie Set-Cookie header missing"
    # Starlette emits the attribute capitalized as "Secure"; match
    # case-insensitively to be robust against attribute casing.
    assert "secure" in access_cookie.lower(), access_cookie
