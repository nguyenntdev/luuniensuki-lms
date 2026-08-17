# -*- coding: utf-8 -*-
"""Application factory for the Luuniensuki FastAPI backend.

Extracted from ``backend.main`` (backend-modularization task 1.1) so that app
construction — exception handlers, CORS middleware, the security-headers and
rate-limit HTTP middleware, and the static mounts — lives in one place behind a
``create_app()`` factory.

This extraction is STRICTLY behavior-preserving: the wiring order and logic are
identical to the previous inline construction in ``main.py``. Route
registration still happens in ``backend.main`` against the app instance returned
by ``create_app()``.

Import direction is one-way: ``backend.main`` imports from this module; this
module never imports ``backend.main`` (no circular import).
"""
from __future__ import annotations

import logging
import time
from pathlib import Path

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.cors import CORSMiddleware

from .config import settings
from .errors import (
    AppError,
    app_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)

# Use the same named logger as ``backend.main`` so log output is unchanged.
logger = logging.getLogger("luuniensuki.api")


# Content-Security-Policy applied to all responses (Requirements 25.1, 25.3).
# This service is primarily a JSON API that also serves a static "/assets"
# mount, so a conservative self-only policy is appropriate. Keep this as a
# module-level constant so the policy is easy to review and tune in one place.
CONTENT_SECURITY_POLICY = (
    "default-src 'self'; frame-ancestors 'none'; object-src 'none'"
)

# Avatar upload directory (Req 11.1-11.3). Defined here for the static mount.
# ``backend.main`` keeps its own module-global ``AVATAR_DIR`` with the same
# value, which the avatar upload route reads; both resolve from
# ``settings.avatar_dir`` at import time so behavior is identical to before the
# extraction (the mount captures the directory at construction either way).
AVATAR_DIR = Path(settings.avatar_dir).resolve()

# Static assets directory (backend/assets), unchanged by the extraction since
# this module also lives in the ``backend`` package.
ASSETS_DIR = Path(__file__).parent / "assets"


# In-process fixed-window rate limiter for authentication endpoints
# (Requirements 12.1-12.4). Driven by the existing rate_limit_* settings:
# up to `rate_limit_requests_per_minute + rate_limit_burst` requests are
# allowed per 60-second window, keyed by client IP. Over-limit requests get
# an HTTP 429 with a standard error envelope and a Retry-After header.
#
# NOTE: This state is per-process. With multiple workers each process keeps its
# own counters, so the effective global limit scales with the worker count.
# ``backend.main`` re-exports this exact dict object so existing references
# (and tests that clear ``main._auth_rate_limit_state``) operate on the same
# state the middleware reads.
_AUTH_RATE_LIMIT_WINDOW_SECONDS = 60
# Maps client key -> (window_start_epoch, count).
_auth_rate_limit_state: dict[str, tuple[float, int]] = {}


def _auth_rate_limit_key(request: Request) -> str:
    """Derive the rate-limit key for a request from the client IP.

    Honors the first hop of X-Forwarded-For when present (the original client
    behind a trusted proxy); otherwise falls back to the direct peer address.
    """
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        first_hop = forwarded.split(",")[0].strip()
        if first_hop:
            return first_hop
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


async def add_security_headers(request: Request, call_next):
    """Inject standard security headers on every response (Requirements 25.1, 25.3).

    Adds Content-Security-Policy, Strict-Transport-Security, and
    X-Content-Type-Options uniformly across all routes. HSTS is only meaningful
    over HTTPS but is safe to always send. A header that a specific endpoint has
    already set is preserved and never overwritten.
    """
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault(
        "Strict-Transport-Security", "max-age=31536000; includeSubDomains"
    )
    response.headers.setdefault("Content-Security-Policy", CONTENT_SECURITY_POLICY)
    return response


async def rate_limit_auth_endpoints(request: Request, call_next):
    """Apply a fixed 60s-window rate limit to /api/v1/auth/* (Req 12.1-12.4).

    Non-auth paths pass through untouched. For auth paths, requests beyond
    `rate_limit_requests_per_minute + rate_limit_burst` within the current
    window are rejected with HTTP 429.
    """
    if not request.url.path.startswith("/api/v1/auth/"):
        return await call_next(request)

    limit = settings.rate_limit_requests_per_minute + settings.rate_limit_burst
    key = _auth_rate_limit_key(request)
    now = time.time()

    window_start, count = _auth_rate_limit_state.get(key, (now, 0))
    if now - window_start >= _AUTH_RATE_LIMIT_WINDOW_SECONDS:
        # Window expired; start a fresh one.
        window_start, count = now, 0

    if count >= limit:
        retry_after = max(
            1,
            int(_AUTH_RATE_LIMIT_WINDOW_SECONDS - (now - window_start)),
        )
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error": {
                    "code": "RATE_LIMITED",
                    "message": "Too many requests",
                    "details": {},
                }
            },
            headers={"Retry-After": str(retry_after)},
        )

    _auth_rate_limit_state[key] = (window_start, count + 1)
    return await call_next(request)


def create_app() -> FastAPI:
    """Construct and return the FastAPI application.

    Wiring order is identical to the previous inline construction in
    ``backend.main``: exception handlers, then CORS (with the wildcard +
    credentials defense-in-depth downgrade), then the security-headers
    middleware, then the rate-limit middleware, then the static mounts. Routes
    are registered separately in ``backend.main`` on the returned instance.
    """
    app = FastAPI(title="Luuniensuki API", version="0.1.0")
    app.add_exception_handler(AppError, app_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)

    # Add CORS middleware to allow cross-origin requests from mobile app.
    #
    # Defense-in-depth (Requirements 3.2, 3.3, 3.4): when credentials are
    # requested together with a "*" wildcard origin we disable credentials
    # (keeping the wildcard) and log a warning, because reflecting any origin
    # while allowing credentials is unsafe and not honored by browsers.
    # Otherwise the validated allowlist and credential setting pass through
    # unchanged.
    cors_origins = settings.cors_origins_list
    cors_allow_credentials = settings.cors_allow_credentials
    if cors_allow_credentials and "*" in cors_origins:
        logger.warning(
            "CORS is configured with allow_credentials=True and a wildcard '*' origin; "
            "disabling credentials for CORS because reflecting any origin with "
            "credentials is unsafe and not honored by browsers. Configure an explicit "
            "origin allowlist to enable credentialed cross-origin requests."
        )
        cors_allow_credentials = False

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=cors_allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register HTTP middleware in the same order as the original module so the
    # resulting middleware stack (and execution order) is unchanged.
    app.middleware("http")(add_security_headers)
    app.middleware("http")(rate_limit_auth_endpoints)

    # Mount static files for assets (motif images, avatars, etc.)
    if ASSETS_DIR.exists():
        app.mount("/assets", StaticFiles(directory=str(ASSETS_DIR)), name="assets")
    else:
        logger.warning(f"Assets directory not found: {ASSETS_DIR}")

    # Serve uploaded avatars from the single configured avatar directory so the
    # stored file and the served URL resolve to the same location
    # (Req 11.1-11.3). The directory must exist before StaticFiles is mounted.
    AVATAR_DIR.mkdir(parents=True, exist_ok=True)
    app.mount(
        "/uploads/avatars", StaticFiles(directory=str(AVATAR_DIR)), name="avatars"
    )

    # Register domain routers extracted from ``backend.main`` (task 5).
    # Imported lazily inside the factory so the import graph stays one-way
    # (main -> app -> routers -> shared modules) and never reaches back into
    # ``backend.main``. Routes are registered here; any endpoints not yet
    # extracted continue to attach to this same app instance in ``backend.main``.
    from .routers import auth as auth_router
    from .routers import users as users_router
    from .routers import content as content_router
    from .routers import gamification as gamification_router
    from .routers import classrooms as classrooms_router
    from .routers import live as live_router
    from .routers import admin as admin_router
    from .routers import ai as ai_router
    from .routers import social as social_router
    from .routers import misc as misc_router
    from .routers import history as history_router
    from .routers import history_learning as history_learning_router
    from .routers import history_stories as history_stories_router
    from .routers import history_tutor as history_tutor_router

    app.include_router(auth_router.router)
    app.include_router(users_router.router)
    app.include_router(content_router.router)
    app.include_router(gamification_router.router)
    app.include_router(classrooms_router.router)
    app.include_router(live_router.router)
    app.include_router(admin_router.router)
    app.include_router(ai_router.router)
    app.include_router(social_router.router)
    app.include_router(misc_router.router)
    app.include_router(history_router.router)
    app.include_router(history_learning_router.router)
    app.include_router(history_stories_router.router)
    app.include_router(history_tutor_router.router)

    return app
