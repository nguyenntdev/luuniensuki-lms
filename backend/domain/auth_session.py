# -*- coding: utf-8 -*-
"""Auth/session helper functions shared between the auth router and the rest of
the backend (backend-modularization task 5.1).

These helpers were previously defined inline in ``backend.main``. They are
relocated here verbatim (logic, log messages and behavior unchanged) so the
``backend.routers.auth`` router and the endpoints still living in
``backend.main`` (e.g. the demo-live entry and change-password flows) can share
them without a circular import. ``backend.main`` re-imports each name so any
``main.<name>`` reference (and tests) continue to resolve to these objects.

Import direction is one-way: this module imports only from ``backend.config``,
``backend.models``, ``backend.domain.gamification`` and ``backend.apischemas``;
it never imports ``backend.main``/``backend.app``/``backend.routers``.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from fastapi import Response
from jose import JWTError, jwt
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..apischemas.auth import AuthMeResponse, RankOut, UserOut, UserStatsOut
from ..config import settings
from ..models import RevokedRefreshToken, User
from .gamification import _compute_rank

# Use the same named logger as ``backend.main`` so log output is unchanged.
logger = logging.getLogger("luuniensuki.api")


def _cookie_params() -> dict[str, Any]:
    samesite = (settings.cookie_samesite or "lax").lower()
    if samesite not in {"lax", "strict", "none"}:
        samesite = "lax"
    params: dict[str, Any] = {
        "secure": settings.cookie_secure_effective,
        "samesite": samesite,
        "path": settings.cookie_path,
    }
    if settings.cookie_domain:
        params["domain"] = settings.cookie_domain
    return params


def _set_auth_cookies(
    response: Response, *, access_token: str, refresh_token: str
) -> None:
    params = _cookie_params()
    if settings.is_production and not params["secure"]:
        logger.warning(
            "Secure auth cookies are DISABLED in production because "
            "COOKIE_SECURE was explicitly overridden to a non-secure value; "
            "session credentials may be transmitted over plaintext connections."
        )
    access_max_age = int(settings.access_token_expire_minutes) * 60
    refresh_max_age = int(settings.refresh_token_expire_days) * 24 * 60 * 60
    response.set_cookie(
        settings.access_cookie_name,
        access_token,
        max_age=access_max_age,
        httponly=True,
        **params,
    )
    response.set_cookie(
        settings.refresh_cookie_name,
        refresh_token,
        max_age=refresh_max_age,
        httponly=True,
        **params,
    )


def _clear_auth_cookies(response: Response) -> None:
    params = _cookie_params()
    response.delete_cookie(settings.access_cookie_name, **params)
    response.delete_cookie(settings.refresh_cookie_name, **params)


def _decode_refresh_token_best_effort(raw_token: str) -> Optional[dict[str, Any]]:
    """Decode a refresh token tolerantly for revocation bookkeeping (Req 17.2).

    Requires ``exp`` so the revocation row's ``expires_at`` can be derived, but
    tolerates any decode failure by returning ``None`` — revocation is a
    best-effort side effect that must never break logout / password-change.
    Issuer/audience are intentionally not enforced here (and ``aud`` validation
    is disabled) so tokens carrying the new identity claims still decode while
    the issue-then-enforce transition is in progress.
    """
    try:
        return jwt.decode(
            raw_token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            options={"require": ["exp"], "verify_aud": False},
        )
    except (JWTError, ValueError):
        return None


def _revoke_refresh_jti(db: Session, payload: dict[str, Any]) -> None:
    """Persist a refresh token's ``jti`` as revoked (idempotent; Req 17.2).

    No-op when the payload lacks the claims needed to build a revocation row
    (e.g. tokens issued before ``jti`` was added). Uses an
    ``ON CONFLICT DO NOTHING`` insert so repeated revocations of the same
    token (logout after password change, double logout) are harmless.
    """
    jti = payload.get("jti")
    subject = payload.get("sub")
    exp = payload.get("exp")
    if not jti or not subject or exp is None:
        return
    try:
        user_id = UUID(str(subject))
        expires_at = datetime.fromtimestamp(int(exp), tz=timezone.utc)
    except (TypeError, ValueError, OverflowError, OSError):
        return
    try:
        db.execute(
            pg_insert(RevokedRefreshToken)
            .values(jti=str(jti), user_id=user_id, expires_at=expires_at)
            .on_conflict_do_nothing(index_elements=["jti"])
        )
        db.commit()
    except IntegrityError:
        # Already revoked: harmless. Roll back the failed insert.
        db.rollback()
    except Exception:
        # Best-effort: a failed revocation must not break the caller's flow.
        db.rollback()
        logger.warning("Failed to persist refresh-token revocation", exc_info=True)


def _is_refresh_revoked(db: Session, jti: Optional[str]) -> bool:
    """Return ``True`` if the given refresh-token ``jti`` has been revoked."""
    if not jti:
        return False
    return db.get(RevokedRefreshToken, str(jti)) is not None


def _build_auth_me_response(user: User) -> AuthMeResponse:
    current_rank, next_rank, xp_to_next = _compute_rank(user.total_xp)
    return AuthMeResponse(
        user=UserOut(
            id=user.id,
            email=user.email,
            display_name=user.display_name,
            avatar_url=user.avatar_url,
            username=user.username,
            role=user.role.value,
            total_xp=user.total_xp,
            starting_urn_id=user.starting_urn_id,
            is_profile_public=user.is_profile_public,
            ai_personalization_enabled=user.ai_personalization_enabled,
        ),
        stats=UserStatsOut(
            total_xp=user.total_xp,
            rank=RankOut(**current_rank),
            xp_to_next_rank=xp_to_next,
            next_rank=(RankOut(**next_rank) if next_rank else None),
        ),
    )
