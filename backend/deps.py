# -*- coding: utf-8 -*-
"""Shared FastAPI dependencies: auth, current-user, role guards, ownership.

Extracted from ``backend.main`` (backend-modularization task 2.1). These are the
cross-cutting request dependencies used across routers: the OAuth2 bearer
scheme, the access-token decode helpers, ``get_current_user`` /
``get_current_user_optional``, the object-level ownership guard, role guards, and
the ``require_feature`` factory.

STRICTLY behavior-preserving: every function is moved verbatim from ``main.py``.
Import direction is one-way — this module imports from ``.config``, ``.db``,
``.models``, ``.rbac`` only, never from ``backend.main`` (no circular import).
``backend.main`` re-exports all of these names so route signatures and tests
that reference ``main.<name>`` continue to resolve to the same objects.
"""
from __future__ import annotations

from typing import Any, Optional
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

from .config import settings
from .db import get_db

def _jwt_decode_kwargs() -> dict[str, Any]:
    """Build keyword arguments for ``jose.jwt.decode``.

    Implements the issue-then-enforce transition for the ``iss``/``aud``
    identity claims (Req 26.4). When ``settings.jwt_validate_new_claims`` is
    False (the transition default), only ``exp`` is required and no
    issuer/audience is enforced, so tokens are accepted whether or not they
    carry ``iss``/``aud``. When True, both backends are known to issue the
    new claims, so ``iss``/``aud`` become required and are validated against
    the configured issuer/audience (jose raises ``JWTError`` on mismatch).
    """
    kwargs: dict[str, Any] = {"algorithms": [settings.jwt_algorithm]}
    if settings.jwt_validate_new_claims:
        kwargs["issuer"] = settings.jwt_issuer
        kwargs["audience"] = settings.jwt_audience
        # ``exp`` is always required (Properties 2, Req 8.2); when the
        # transition flag is set, ``iss``/``aud`` are also required and
        # verified against the configured values.
        kwargs["options"] = {
            "require_exp": True,
            "require_iss": True,
            "require_aud": True,
        }
    else:
        # python-jose enables verify_aud/verify_iss by default. Tokens issued
        # by this codebase now always carry iss/aud (Req 26.3), so without
        # this override any legacy token (or foreign test token) without
        # iss/aud would fail validation even with validate_new_claims=False.
        kwargs["options"] = {
            "verify_aud": False,
            "verify_iss": False,
        }
    return kwargs


def _decode_access_token(raw_token: str) -> Optional[UUID]:
    """Decode an access token and return its subject ``UUID``.

    Shared by ``get_current_user`` and ``get_current_user_optional`` to avoid
    duplicating the access-token decode (Req 18.3). Requires ``exp`` always;
    iss/aud enforcement is gated by the JWT_VALIDATE_NEW_CLAIMS transition
    flag (Req 26.4). Returns the subject ``UUID`` on success, or ``None`` on
    any failure (``JWTError``, ``ValueError``, missing/blank ``sub``, or a
    token whose ``type`` is not ``"access"``).
    """
    try:
        payload = jwt.decode(
            raw_token,
            settings.jwt_secret_key,
            **_jwt_decode_kwargs(),
        )
        subject = payload.get("sub")
        token_type = payload.get("type")
        if not subject or token_type != "access":
            return None
        return UUID(subject)
    except (JWTError, ValueError):
        return None


from .models import User, UserRole
from .rbac import ADMIN_ROLES, STAFF_ROLES


def verify_csrf(request: Request, require_custom_header: bool = False) -> None:
    """Enforce CSRF and Bearer token defense for state-mutating requests.

    Invariants:
    1. Safe HTTP methods (GET, HEAD, OPTIONS) do not mutate state and are exempt.
    2. Requests with Authorization: Bearer <token> header are immune to ambient cookie CSRF attacks.
    3. Requests authenticated via session cookies (access_cookie_name):
       - If Sec-Fetch-Site is 'cross-site', strictly reject with 403 Forbidden.
       - If Origin header is present and does not match Host or allowed CORS origins, reject with 403 Forbidden.
       - If require_custom_header is True, require custom anti-CSRF header (X-Requested-With, X-CSRF-Token, X-XSRF-Token).
       - If Sec-Fetch-Site is present and untrusted, require custom anti-CSRF header.
    """
    if request.method in ("GET", "HEAD", "OPTIONS"):
        return

    auth_header = request.headers.get("authorization", "")
    if auth_header.strip().startswith("Bearer "):
        return

    cookie_token = request.cookies.get(settings.access_cookie_name)
    if not cookie_token:
        return

    # 1. Check Sec-Fetch-Site (Fetch Metadata)
    sec_fetch_site = request.headers.get("sec-fetch-site")
    if sec_fetch_site == "cross-site":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF validation failed: cross-site cookie mutation rejected",
        )

    # 2. Check Origin header against Host and allowed CORS origins
    origin = request.headers.get("origin")
    if origin:
        origin_clean = origin.rstrip("/")
        allowed_origins = [o.rstrip("/") for o in settings.cors_origins_list]
        host = request.headers.get("host", "")
        origin_host = origin_clean.split("://")[-1].split(":")[0] if "://" in origin_clean else origin_clean
        host_name = host.split(":")[0]
        if (
            origin_clean not in allowed_origins
            and origin_host != host_name
            and origin_clean not in ("http://testserver", "https://testserver")
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF validation failed: cross-origin mutation rejected",
            )

    has_csrf_header = bool(
        request.headers.get("x-requested-with")
        or request.headers.get("x-csrf-token")
        or request.headers.get("x-xsrf-token")
    )

    # 3. Custom anti-CSRF header enforcement
    if require_custom_header:
        if not has_csrf_header:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF validation failed: missing custom anti-CSRF header on cookie mutation",
            )
    elif sec_fetch_site and sec_fetch_site not in ("same-origin", "same-site", "none"):
        if not has_csrf_header:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF validation failed: untrusted fetch site without custom anti-CSRF header",
            )


def get_current_user(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    raw_token = token or request.cookies.get(settings.access_cookie_name)
    if not raw_token:
        raise credentials_exception

    user_id = _decode_access_token(raw_token)
    if user_id is None:
        raise credentials_exception

    user = db.get(User, user_id)
    if user is None:
        raise credentials_exception
    return user


def get_current_user_optional(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """
    Get current user if authenticated, otherwise return None.
    Used for endpoints that are public but can show different data when authenticated.
    """
    raw_token = token or request.cookies.get(settings.access_cookie_name)
    if not raw_token:
        return None

    user_id = _decode_access_token(raw_token)
    if user_id is None:
        return None

    user = db.get(User, user_id)
    return user


def _ensure_owner_or_404(resource_owner_id: UUID, current_user: User) -> None:
    """Object-level authorization guard (Req 20).

    Permit the operation only when the authenticated user owns the referenced
    resource or holds an admin role. For anyone else, raise a generic 404 so the
    response never discloses whether the resource exists (Req 20.2).
    """
    if current_user.id == resource_owner_id or current_user.role in ADMIN_ROLES:
        return
    raise HTTPException(status_code=404, detail="Not found")


def _can_view_drafts(user: User) -> bool:
    return user.role in STAFF_ROLES


def _require_roles(roles: set[UserRole]):
    def _dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized"
            )
        return current_user

    return _dependency


def get_staff_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in STAFF_ROLES:
        raise HTTPException(status_code=403, detail="Not authorized")
    return current_user


def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Not authorized")
    return current_user


# Alias for consistency with other endpoints
require_admin = get_admin_user


def get_super_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Require super_admin role for sensitive operations like audit logs."""
    if current_user.role != UserRole.super_admin:
        raise HTTPException(status_code=403, detail="Super admin access required")
    return current_user


def require_feature(feature_key: str):
    """
    Dependency factory to require a feature flag to be enabled for the current user.

    Usage:
        @app.get("/api/v1/new-feature")
        def new_feature_endpoint(
            current_user: User = Depends(require_feature("new_feature_flag")),
            db: Session = Depends(get_db),
        ):
            ...

    Args:
        feature_key: The feature flag key to check

    Returns:
        A dependency function that checks the feature flag
    """

    def _dependency(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> User:
        from backend.services import feature_flags

        if not feature_flags.is_feature_enabled_for_user(
            db, feature_key, current_user.id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Feature '{feature_key}' is not enabled for this user",
            )
        return current_user

    return _dependency
