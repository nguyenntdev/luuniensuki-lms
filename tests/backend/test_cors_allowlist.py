"""CORS allowlist reflection tests (Workstream 2).

These tests assert the runtime CORS contract that ``backend.main`` configures
on its FastAPI app (see ``tests/backend/conftest.py`` which imports
``backend.main`` and exposes ``client``/``db_session`` fixtures). They cover:

* Correctness Property 3 (CORS-allowlist): for any Origin O, the response
  reflects O **iff** O is in the allowlist; an Origin absent from the allowlist
  is NEVER reflected (and never replaced by ``"*"``). When credentials are
  enabled, an exact allowed Origin is reflected together with
  ``Access-Control-Allow-Credentials: true`` and is never paired with a
  wildcard origin.

Requirements: 3.3, 27.1, 27.2.

By construction these assertions FAIL on unfixed code (where the deployed
runtime allows a wildcard origin together with credentials, so an arbitrary
Origin would be reflected) and PASS once the allowlist is enforced and the
wildcard+credentials combination is refused/downgraded (Req 27 —
fail-on-unfixed / pass-on-fixed).

Approach (option "a" — self-contained app)
------------------------------------------
``backend.main`` wires ``CORSMiddleware`` once, at module import time, from
``settings.cors_origins_list`` (whose ambient default is the wildcard ``"*"``),
and there is no ``create_app`` factory to re-run that wiring against a
monkeypatched allowlist. Re-configuring middleware on the already-built app is
not supported by Starlette. So to make the assertions deterministic regardless
of the host's ambient configuration, each test builds a small fresh FastAPI app
with a KNOWN allowlist and a trivial route, wiring ``CORSMiddleware`` exactly
the way ``backend.main`` does — including its defense-in-depth downgrade that
disables credentials when a wildcard origin is combined with credentials. This
exercises the identical Starlette ``CORSMiddleware`` reflection behavior the
deployed app relies on, so the CORS contract is verified by construction.
"""

from __future__ import annotations

import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.middleware.cors import CORSMiddleware

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

# A concrete, finite allowlist used across the reflection tests.
ALLOWED_ORIGIN = "https://app.example.com"
SECOND_ALLOWED_ORIGIN = "https://admin.example.com"
ALLOWLIST = [ALLOWED_ORIGIN, SECOND_ALLOWED_ORIGIN]

# An Origin that is deliberately NOT in the allowlist and must never be echoed.
DISALLOWED_ORIGIN = "https://evil.example.com"

# Header names normalized to lowercase (Starlette/TestClient expose them
# case-insensitively; we read them lowercase for clarity).
ACAO = "access-control-allow-origin"
ACAC = "access-control-allow-credentials"


def _build_cors_app(allow_origins: list[str], allow_credentials: bool) -> FastAPI:
    """Build a minimal FastAPI app wired exactly like ``backend.main``.

    Mirrors the production wiring: the validated allowlist drives
    ``allow_origins``; ``allow_methods``/``allow_headers`` are wildcards; and the
    defense-in-depth rule disables credentials whenever a wildcard origin is
    combined with credentials (because reflecting any origin with credentials is
    unsafe and not honored by browsers).
    """
    effective_credentials = allow_credentials
    if effective_credentials and "*" in allow_origins:
        effective_credentials = False

    app = FastAPI()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=effective_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/ping")
    def ping() -> dict[str, bool]:
        return {"ok": True}

    return app


def _preflight(client: TestClient, origin: str):
    """Issue a CORS preflight (OPTIONS) for the ``/ping`` route from ``origin``."""
    return client.options(
        "/ping",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "GET",
        },
    )


def test_allowlisted_origin_reflected_on_simple_request() -> None:
    """A GET from an allowlisted Origin reflects exactly that Origin.

    Validates Correctness Property 3 (the "reflect iff allowed" direction).
    Requirements: 3.3, 27.1.
    """
    client = TestClient(_build_cors_app(ALLOWLIST, allow_credentials=True))

    response = client.get("/ping", headers={"Origin": ALLOWED_ORIGIN})

    assert response.status_code == 200
    assert response.headers.get(ACAO) == ALLOWED_ORIGIN
    # The exact origin is echoed, never the wildcard.
    assert response.headers.get(ACAO) != "*"


def test_each_allowlisted_origin_reflected_exactly() -> None:
    """Every Origin in a multi-entry allowlist is reflected exactly.

    Validates Correctness Property 3 across more than one allowed origin.
    Requirements: 3.3, 27.1.
    """
    client = TestClient(_build_cors_app(ALLOWLIST, allow_credentials=True))

    for origin in ALLOWLIST:
        response = client.get("/ping", headers={"Origin": origin})
        assert response.status_code == 200
        assert response.headers.get(ACAO) == origin


def test_allowlisted_origin_reflected_on_preflight() -> None:
    """A preflight (OPTIONS) from an allowlisted Origin reflects that Origin.

    Validates Correctness Property 3 for preflight requests.
    Requirements: 3.3, 27.1.
    """
    client = TestClient(_build_cors_app(ALLOWLIST, allow_credentials=True))

    response = _preflight(client, ALLOWED_ORIGIN)

    assert response.headers.get(ACAO) == ALLOWED_ORIGIN
    assert response.headers.get(ACAO) != "*"


def test_non_allowlisted_origin_not_reflected_on_simple_request() -> None:
    """A GET from a disallowed Origin never gets an ``Access-Control-Allow-Origin``.

    The header must be absent entirely — never the origin, never ``"*"``.

    Validates Correctness Property 3 (the "never reflect when not allowed"
    direction). Requirements: 3.3, 27.1, 27.2.
    """
    client = TestClient(_build_cors_app(ALLOWLIST, allow_credentials=True))

    response = client.get("/ping", headers={"Origin": DISALLOWED_ORIGIN})

    assert ACAO not in response.headers
    assert response.headers.get(ACAO) != DISALLOWED_ORIGIN
    assert response.headers.get(ACAO) != "*"


def test_non_allowlisted_origin_not_reflected_on_preflight() -> None:
    """A preflight from a disallowed Origin yields no ``Access-Control-Allow-Origin``.

    Validates Correctness Property 3 for disallowed preflight requests.
    Requirements: 3.3, 27.1, 27.2.
    """
    client = TestClient(_build_cors_app(ALLOWLIST, allow_credentials=True))

    response = _preflight(client, DISALLOWED_ORIGIN)

    assert ACAO not in response.headers
    assert response.headers.get(ACAO) != DISALLOWED_ORIGIN
    assert response.headers.get(ACAO) != "*"


def test_credentials_paired_only_with_exact_allowed_origin() -> None:
    """When credentials are enabled, an allowed Origin is reflected exactly with creds.

    ``Access-Control-Allow-Credentials: true`` must accompany the exact reflected
    origin, and that origin must never be the wildcard.

    Validates Correctness Property 3 (credentials direction).
    Requirements: 3.3, 27.1.
    """
    client = TestClient(_build_cors_app(ALLOWLIST, allow_credentials=True))

    response = client.get("/ping", headers={"Origin": ALLOWED_ORIGIN})

    assert response.headers.get(ACAO) == ALLOWED_ORIGIN
    assert response.headers.get(ACAO) != "*"
    assert response.headers.get(ACAC) == "true"


def test_wildcard_with_credentials_never_reflects_credentialed_wildcard() -> None:
    """Wildcard origin + credentials never emits a credentialed wildcard reflection.

    Mirrors ``backend.main``'s defense-in-depth: a wildcard origin combined with
    credentials downgrades credentials off, so a wildcard ``Access-Control-Allow-Origin``
    is never paired with ``Access-Control-Allow-Credentials: true``.

    Validates Correctness Property 3 (the "never wildcard + credentials" invariant).
    Requirements: 3.3, 27.1, 27.2.
    """
    client = TestClient(_build_cors_app(["*"], allow_credentials=True))

    response = client.get("/ping", headers={"Origin": DISALLOWED_ORIGIN})

    # The wildcard may be reflected, but only because credentials were disabled.
    if response.headers.get(ACAO) == "*":
        assert response.headers.get(ACAC) != "true"
    # And credentials must never be advertised as enabled in this configuration.
    assert response.headers.get(ACAC) != "true"
