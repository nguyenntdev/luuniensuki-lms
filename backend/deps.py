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

from .config import settings
from .db import get_db
from .models import User, UserRole
from .rbac import ADMIN_ROLES, STAFF_ROLES


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


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
        kwargs["options"] = {"require": ["exp", "iss", "aud"]}
    else:
        kwargs["options"] = {"require": ["exp"]}
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
