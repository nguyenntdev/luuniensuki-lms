# -*- coding: utf-8 -*-
"""Application entry module for the Luuniensuki FastAPI backend.

backend-modularization (task 6.1): ``main.py`` is now a thin entry shim. The
~19k-line monolith that used to live here has been decomposed into:

* ``backend.app``      — the ``create_app()`` factory (middleware, exception
                         handlers, static mounts, router registration).
* ``backend.routers.*``— one ``APIRouter`` per domain (auth, users, content,
                         gamification, classrooms, live, admin, ai, social,
                         misc), registered in ``create_app()``.
* ``backend.deps``     — shared FastAPI dependencies (auth, role guards, etc.).
* ``backend.domain.*`` — pure helpers/constants shared across routers
                         (``gamification``, ``auth_session``, ``helpers``).
* ``backend.apischemas.*`` / ``backend.schemas`` — Pydantic request/response
                         models.

This module only constructs the ASGI ``app`` and re-exports the small set of
names that the test suite and ``tests/backend/conftest.py`` reference as
``backend.main.<name>``. No endpoint, schema, or persistence logic lives here.
"""
from __future__ import annotations

import logging

from .app import create_app, _auth_rate_limit_state  # noqa: F401
from .config import settings  # noqa: F401
from .db import get_db  # noqa: F401
from .deps import _decode_access_token, _ensure_owner_or_404  # noqa: F401
from .domain.gamification import _apply_xp_boost  # noqa: F401
from .domain.helpers import (  # noqa: F401
    ALLOWED_IMAGE_TYPES,
    AVATAR_DIR,
    _detect_image_type,
)
from .rbac import ADMIN_ROLES  # noqa: F401

# Configure root logging from settings on import, exactly as the previous
# monolithic ``main.py`` did, so log levels are unchanged for the ASGI server.
logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))
logger = logging.getLogger("luuniensuki.api")

# The FastAPI application consumed by the ASGI server (e.g. ``uvicorn
# backend.main:app``). Built by the factory in ``backend.app``, which registers
# every domain router via ``include_router``.
app = create_app()
