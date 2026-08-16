# -*- coding: utf-8 -*-
"""Authentication endpoints (backend-modularization task 5.1).

These routes were moved verbatim from ``backend.main``; only the decorator was
changed from ``@app.<method>`` to ``@router.<method>``. The router is registered
via ``app.include_router(router)`` in ``backend.app.create_app()``. Behavior,
paths, request/response models and status codes are unchanged.

Shared auth/session helpers (cookie handling, refresh-token revocation, the
``/me`` response builder) live in ``backend.domain.auth_session`` so both this
router and the remaining ``backend.main`` endpoints can use them without a
circular import.
"""
from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..apischemas.auth import (
    AuthLoginRequest,
    AuthMeResponse,
    AuthRegisterRequest,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
)
from ..config import settings
from ..deps import get_current_user, get_db
from ..domain.auth_session import (
    _build_auth_me_response,
    _clear_auth_cookies,
    _decode_refresh_token_best_effort,
    _is_refresh_revoked,
    _revoke_refresh_jti,
    _set_auth_cookies,
)
from ..errors import AppError
from ..models import PasswordResetToken, User
from ..security import create_jwt_token, hash_password, verify_password

router = APIRouter()


@router.post(
    "/api/v1/auth/register",
    response_model=AuthMeResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    payload: AuthRegisterRequest,
    response: Response,
    db: Session = Depends(get_db),
) -> AuthMeResponse:
    existing = db.execute(
        select(User).where(User.email == str(payload.email))
    ).scalar_one_or_none()
    if existing is not None:
        raise AppError(
            code="EMAIL_ALREADY_REGISTERED",
            message="Email already registered",
            status_code=status.HTTP_409_CONFLICT,
        )

    user = User(
        email=str(payload.email),
        password_hash="",
        display_name=payload.display_name,
    )
    try:
        user.password_hash = hash_password(payload.password)
    except ValueError:
        raise AppError(
            code="PASSWORD_TOO_LONG",
            message="Password too long",
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise AppError(
            code="EMAIL_ALREADY_REGISTERED",
            message="Email already registered",
            status_code=status.HTTP_409_CONFLICT,
        )

    db.refresh(user)

    access_token = create_jwt_token(
        subject=str(user.id),
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
        issuer=settings.jwt_issuer,
        audience=settings.jwt_audience,
        extra_claims={"type": "access"},
    )
    refresh_token = create_jwt_token(
        subject=str(user.id),
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        expires_delta=timedelta(days=settings.refresh_token_expire_days),
        issuer=settings.jwt_issuer,
        audience=settings.jwt_audience,
        extra_claims={"type": "refresh"},
    )

    _set_auth_cookies(response, access_token=access_token, refresh_token=refresh_token)
    response.headers["Cache-Control"] = "no-store"
    return _build_auth_me_response(user)


@router.post("/api/v1/auth/login", response_model=AuthMeResponse)
def login(
    payload: AuthLoginRequest, response: Response, db: Session = Depends(get_db)
) -> AuthMeResponse:
    user = db.execute(
        select(User).where(User.email == str(payload.email))
    ).scalar_one_or_none()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise AppError(
            code="INVALID_CREDENTIALS",
            message="Invalid email or password",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    access_token = create_jwt_token(
        subject=str(user.id),
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
        issuer=settings.jwt_issuer,
        audience=settings.jwt_audience,
        extra_claims={"type": "access"},
    )
    refresh_token = create_jwt_token(
        subject=str(user.id),
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        expires_delta=timedelta(days=settings.refresh_token_expire_days),
        issuer=settings.jwt_issuer,
        audience=settings.jwt_audience,
        extra_claims={"type": "refresh"},
    )

    _set_auth_cookies(response, access_token=access_token, refresh_token=refresh_token)
    response.headers["Cache-Control"] = "no-store"
    return _build_auth_me_response(user)


@router.get("/api/v1/auth/me", response_model=AuthMeResponse)
def me(current_user: User = Depends(get_current_user)) -> AuthMeResponse:
    return _build_auth_me_response(current_user)


@router.post("/api/v1/auth/refresh", response_model=AuthMeResponse)
def refresh_session(
    request: Request, response: Response, db: Session = Depends(get_db)
) -> AuthMeResponse:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    raw_token = request.cookies.get(settings.refresh_cookie_name)
    if not raw_token:
        raise credentials_exception

    try:
        payload = jwt.decode(
            raw_token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            # Issued tokens carry aud/iss; without disabling verification here
            # python-jose's default verify_aud/verify_iss rejects every token
            # ("Invalid audience"), matching the access-token path (Req 26.4).
            # exp is required via require_exp below.
            options={"require_exp": True, "verify_aud": False, "verify_iss": False},
        )
        subject = payload.get("sub")
        token_type = payload.get("type")
        if not subject or token_type != "refresh":
            raise credentials_exception
        user_id = UUID(subject)
    except (JWTError, ValueError):
        raise credentials_exception

    user = db.get(User, user_id)
    if user is None:
        raise credentials_exception

    # Reject refresh tokens whose `jti` has been revoked (logout / password
    # change). Done after decoding and before issuing new tokens (Req 17.2).
    if _is_refresh_revoked(db, payload.get("jti")):
        raise credentials_exception

    # Rotate: revoke the presented refresh token so the old `jti` cannot be
    # replayed once a new refresh token is issued below (best-effort).
    _revoke_refresh_jti(db, payload)

    access_token = create_jwt_token(
        subject=str(user.id),
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
        issuer=settings.jwt_issuer,
        audience=settings.jwt_audience,
        extra_claims={"type": "access"},
    )
    refresh_token = create_jwt_token(
        subject=str(user.id),
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        expires_delta=timedelta(days=settings.refresh_token_expire_days),
        issuer=settings.jwt_issuer,
        audience=settings.jwt_audience,
        extra_claims={"type": "refresh"},
    )

    _set_auth_cookies(response, access_token=access_token, refresh_token=refresh_token)
    response.headers["Cache-Control"] = "no-store"
    return _build_auth_me_response(user)


@router.post("/api/v1/auth/logout")
def logout(
    request: Request, response: Response, db: Session = Depends(get_db)
) -> dict[str, bool]:
    # Best-effort revoke the presented refresh token so it cannot be replayed
    # after logout (Req 17.2). Decode tolerantly — a failure must never break
    # logout, which still clears the cookies below.
    raw_token = request.cookies.get(settings.refresh_cookie_name)
    if raw_token:
        payload = _decode_refresh_token_best_effort(raw_token)
        if payload is not None:
            _revoke_refresh_jti(db, payload)
    _clear_auth_cookies(response)
    response.headers["Cache-Control"] = "no-store"
    return {"success": True}


@router.post("/api/v1/auth/forgot-password", response_model=ForgotPasswordResponse)
def forgot_password(
    payload: ForgotPasswordRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> ForgotPasswordResponse:
    """Request a password reset token for an account.

    The response is intentionally generic to avoid account enumeration.
    """
    now = datetime.now(timezone.utc)
    email = str(payload.email)
    user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()

    reset_token_value: Optional[str] = None
    if user is not None:
        # Invalidate any still-active reset tokens for this user.
        existing_tokens = (
            db.execute(
                select(PasswordResetToken).where(
                    PasswordResetToken.user_id == user.id,
                    PasswordResetToken.used_at.is_(None),
                    PasswordResetToken.expires_at > now,
                )
            )
            .scalars()
            .all()
        )
        for token in existing_tokens:
            token.used_at = now

        reset_token_value = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(reset_token_value.encode("utf-8")).hexdigest()
        expires_at = now + timedelta(
            minutes=settings.password_reset_token_expire_minutes
        )

        db.add(
            PasswordResetToken(
                user_id=user.id,
                token_hash=token_hash,
                expires_at=expires_at,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
            )
        )
        db.commit()

    response = ForgotPasswordResponse(
        message="If an account exists for this email, a password reset instruction has been generated.",
    )
    if settings.password_reset_return_token and reset_token_value is not None:
        response.reset_token = reset_token_value
    return response


@router.post("/api/v1/auth/reset-password", response_model=ResetPasswordResponse)
def reset_password(
    payload: ResetPasswordRequest,
    db: Session = Depends(get_db),
) -> ResetPasswordResponse:
    """Reset password using a valid reset token."""
    now = datetime.now(timezone.utc)
    token_hash = hashlib.sha256(payload.token.encode("utf-8")).hexdigest()

    reset_token = (
        db.execute(
            select(PasswordResetToken)
            .where(
                PasswordResetToken.token_hash == token_hash,
                PasswordResetToken.used_at.is_(None),
                PasswordResetToken.expires_at > now,
            )
            .order_by(PasswordResetToken.created_at.desc())
        )
        .scalars()
        .first()
    )
    if reset_token is None:
        raise AppError(
            code="INVALID_OR_EXPIRED_RESET_TOKEN",
            message="Invalid or expired password reset token",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    user = db.get(User, reset_token.user_id)
    if user is None:
        raise AppError(
            code="USER_NOT_FOUND",
            message="User not found",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    try:
        user.password_hash = hash_password(payload.new_password)
    except ValueError:
        raise AppError(
            code="PASSWORD_TOO_LONG",
            message="Password too long",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    reset_token.used_at = now
    db.commit()
    return ResetPasswordResponse(message="Password has been reset successfully.")
