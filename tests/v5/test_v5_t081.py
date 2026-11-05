# -*- coding: utf-8 -*-
"""V5-T081: Fail-start Unsafe Production Cookies Test Suite.

Wave W08, Slot A01 (Priority: P0, Classification: PRODUCTION_COMPLETION).
Verifies that:
1. Production settings validation fails closed with RuntimeError when COOKIE_SECURE=false.
2. Production settings validation fails closed with RuntimeError on insecure SameSite settings.
3. Production startup (create_app) enforces fail-closed checks for insecure cookies.
4. Production valid configuration enforces secure=True, httponly=True, samesite in {lax, strict}.
5. Domain auth_session helpers (_cookie_params, _set_auth_cookies, _clear_auth_cookies)
   strictly emit secure cookies in production and refuse insecure emission.
6. Development mode remains permissive for local HTTP testing.
"""
from __future__ import annotations

import pytest
from fastapi import Response

from backend.app import create_app
from backend.config import Settings
from backend.domain.auth_session import (
    _clear_auth_cookies,
    _cookie_params,
    _set_auth_cookies,
)

_STRONG_SECRET = "s3cr3t-Kx9f2Lq8Wz-production-strong-key-0123456789"
_VALID_CORS = "https://app.histolab.icu,https://lms.histolab.icu"

_ENV_VARS_TO_CLEAR = (
    "ENVIRONMENT",
    "JWT_SECRET_KEY",
    "CORS_ORIGINS",
    "CORS_ALLOW_CREDENTIALS",
    "PASSWORD_RESET_RETURN_TOKEN",
    "DEMO_MODE",
    "COOKIE_SECURE",
    "COOKIE_SAMESITE",
    "COOKIE_DOMAIN",
    "COOKIE_PATH",
)


def _make_production_settings(monkeypatch: pytest.MonkeyPatch, **overrides) -> Settings:
    for var in _ENV_VARS_TO_CLEAR:
        monkeypatch.delenv(var, raising=False)
    kwargs = {
        "environment": "production",
        "jwt_secret_key": _STRONG_SECRET,
        "cors_origins": _VALID_CORS,
        "cors_allow_credentials": True,
    }
    kwargs.update(overrides)
    return Settings(_env_file=None, **kwargs)


# ==============================================================================
# 1. Production Settings Validation Fail-Closed
# ==============================================================================


@pytest.mark.parametrize("insecure_value", [False, "false", "False", "0", "off", "no"])
def test_production_cookie_secure_false_rejected(monkeypatch: pytest.MonkeyPatch, insecure_value) -> None:
    """Explicitly disabling secure cookies in production MUST raise RuntimeError."""
    for var in _ENV_VARS_TO_CLEAR:
        monkeypatch.delenv(var, raising=False)

    with pytest.raises(RuntimeError) as exc_info:
        Settings(
            _env_file=None,
            environment="production",
            jwt_secret_key=_STRONG_SECRET,
            cors_origins=_VALID_CORS,
            cors_allow_credentials=True,
            cookie_secure=insecure_value,
        )

    msg = str(exc_info.value)
    assert "Insecure production configuration" in msg
    assert "COOKIE_SECURE" in msg


def test_production_cookie_secure_env_var_false_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    """Setting COOKIE_SECURE=false via environment variables fails closed on startup."""
    for var in _ENV_VARS_TO_CLEAR:
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("COOKIE_SECURE", "false")
    monkeypatch.setenv("JWT_SECRET_KEY", _STRONG_SECRET)
    monkeypatch.setenv("CORS_ORIGINS", _VALID_CORS)

    with pytest.raises(RuntimeError) as exc_info:
        Settings(_env_file=None)

    msg = str(exc_info.value)
    assert "Insecure production configuration" in msg
    assert "COOKIE_SECURE" in msg


@pytest.mark.parametrize("insecure_samesite", ["none", "None", "NONE", "invalid", ""])
def test_production_cookie_samesite_insecure_rejected(monkeypatch: pytest.MonkeyPatch, insecure_samesite) -> None:
    """Insecure or non-standard SameSite values in production MUST raise RuntimeError."""
    with pytest.raises(RuntimeError) as exc_info:
        _make_production_settings(monkeypatch, cookie_samesite=insecure_samesite)

    msg = str(exc_info.value)
    assert "Insecure production configuration" in msg
    assert "COOKIE_SAMESITE" in msg


# ==============================================================================
# 2. Positive Valid Production Configuration Enforcing Secure Cookies
# ==============================================================================


def test_production_default_cookies_are_secure(monkeypatch: pytest.MonkeyPatch) -> None:
    """In production without explicit COOKIE_SECURE, secure cookies default to True."""
    cfg = _make_production_settings(monkeypatch)
    assert cfg.is_production is True
    assert cfg.cookie_secure_effective is True
    assert cfg.cookie_samesite.lower() in {"lax", "strict"}


def test_production_explicit_secure_true_succeeds(monkeypatch: pytest.MonkeyPatch) -> None:
    """Explicit COOKIE_SECURE=True in production constructs successfully."""
    cfg = _make_production_settings(monkeypatch, cookie_secure=True, cookie_samesite="lax")
    assert cfg.is_production is True
    assert cfg.cookie_secure is True
    assert cfg.cookie_secure_effective is True

    cfg_strict = _make_production_settings(monkeypatch, cookie_secure=True, cookie_samesite="strict")
    assert cfg_strict.cookie_samesite == "strict"
    assert cfg_strict.cookie_secure_effective is True


# ==============================================================================
# 3. Application Startup Enforcement (create_app)
# ==============================================================================


def test_create_app_fails_start_on_insecure_cookie_secure(monkeypatch: pytest.MonkeyPatch) -> None:
    """create_app() must refuse to start in production if cookie_secure is False."""
    from backend import app as app_module

    monkeypatch.setattr(app_module.settings, "environment", "production")
    monkeypatch.setattr(app_module.settings, "jwt_secret_key", "SuperSecureProductionSecretKey1234567890!")
    monkeypatch.setattr(app_module.settings, "cookie_secure", False)

    with pytest.raises(RuntimeError) as exc_info:
        create_app()

    assert "COOKIE_SECURE" in str(exc_info.value)


def test_create_app_fails_start_on_insecure_cookie_samesite(monkeypatch: pytest.MonkeyPatch) -> None:
    """create_app() must refuse to start in production if cookie_samesite is invalid/none."""
    from backend import app as app_module

    monkeypatch.setattr(app_module.settings, "environment", "production")
    monkeypatch.setattr(app_module.settings, "jwt_secret_key", "SuperSecureProductionSecretKey1234567890!")
    monkeypatch.setattr(app_module.settings, "cookie_secure", True)
    monkeypatch.setattr(app_module.settings, "cookie_samesite", "none")

    with pytest.raises(RuntimeError) as exc_info:
        create_app()

    assert "COOKIE_SAMESITE" in str(exc_info.value)


# ==============================================================================
# 4. Domain Auth Session Cookie Emission Adheres Strictly to Secure Flags
# ==============================================================================


def test_domain_cookie_params_in_production(monkeypatch: pytest.MonkeyPatch) -> None:
    """_cookie_params() in production yields secure=True and samesite in {lax, strict}."""
    from backend.domain import auth_session

    monkeypatch.setattr(auth_session.settings, "environment", "production")
    monkeypatch.setattr(auth_session.settings, "cookie_secure", True)
    monkeypatch.setattr(auth_session.settings, "cookie_samesite", "lax")

    params = _cookie_params()
    assert params["secure"] is True
    assert params["samesite"] == "lax"
    assert params["path"] == "/"


def test_domain_cookie_params_rejects_insecure_in_production(monkeypatch: pytest.MonkeyPatch) -> None:
    """_cookie_params() raises RuntimeError if invoked in production with insecure flags."""
    from backend.domain import auth_session

    monkeypatch.setattr(auth_session.settings, "environment", "production")
    monkeypatch.setattr(auth_session.settings, "cookie_secure", False)

    with pytest.raises(RuntimeError) as exc_info:
        _cookie_params()
    assert "Insecure auth cookies cannot be used in production" in str(exc_info.value)

    monkeypatch.setattr(auth_session.settings, "cookie_secure", True)
    monkeypatch.setattr(auth_session.settings, "cookie_samesite", "none")

    with pytest.raises(RuntimeError) as exc_info:
        _cookie_params()
    assert "Insecure cookie samesite in production" in str(exc_info.value)


def test_domain_set_auth_cookies_emits_secure_and_httponly(monkeypatch: pytest.MonkeyPatch) -> None:
    """_set_auth_cookies() emits cookies with Secure, HttpOnly, SameSite in production."""
    from backend.domain import auth_session

    monkeypatch.setattr(auth_session.settings, "environment", "production")
    monkeypatch.setattr(auth_session.settings, "cookie_secure", True)
    monkeypatch.setattr(auth_session.settings, "cookie_samesite", "lax")

    response = Response()
    _set_auth_cookies(response, access_token="mock_access_jwt", refresh_token="mock_refresh_jwt")

    set_cookie_headers = response.headers.getlist("set-cookie")
    assert len(set_cookie_headers) == 2

    access_name = auth_session.settings.access_cookie_name
    refresh_name = auth_session.settings.refresh_cookie_name

    access_header = next((h for h in set_cookie_headers if h.startswith(f"{access_name}=")), None)
    refresh_header = next((h for h in set_cookie_headers if h.startswith(f"{refresh_name}=")), None)

    assert access_header is not None, "Access cookie header missing"
    assert refresh_header is not None, "Refresh cookie header missing"

    for header in [access_header, refresh_header]:
        header_lower = header.lower()
        assert "secure" in header_lower
        assert "httponly" in header_lower
        assert "samesite=lax" in header_lower
        assert "path=/" in header_lower


def test_domain_clear_auth_cookies_emits_secure_and_httponly(monkeypatch: pytest.MonkeyPatch) -> None:
    """_clear_auth_cookies() emits expired cookies with Secure and HttpOnly in production."""
    from backend.domain import auth_session

    monkeypatch.setattr(auth_session.settings, "environment", "production")
    monkeypatch.setattr(auth_session.settings, "cookie_secure", True)
    monkeypatch.setattr(auth_session.settings, "cookie_samesite", "lax")

    response = Response()
    _clear_auth_cookies(response)

    set_cookie_headers = response.headers.getlist("set-cookie")
    assert len(set_cookie_headers) == 2

    for header in set_cookie_headers:
        header_lower = header.lower()
        assert "secure" in header_lower
        assert "httponly" in header_lower
        assert "samesite=lax" in header_lower
        assert "max-age=0" in header_lower


def test_domain_set_auth_cookies_fails_closed_on_forced_insecure(monkeypatch: pytest.MonkeyPatch) -> None:
    """_set_auth_cookies() raises RuntimeError if insecure cookies are attempted in production."""
    from backend.domain import auth_session

    monkeypatch.setattr(auth_session.settings, "environment", "production")
    # Even if _cookie_params were monkeypatched to return insecure parameters:
    monkeypatch.setattr(
        auth_session,
        "_cookie_params",
        lambda: {"secure": False, "samesite": "lax", "path": "/"},
    )

    response = Response()
    with pytest.raises(RuntimeError) as exc_info:
        _set_auth_cookies(response, access_token="tok1", refresh_token="tok2")

    assert "Attempted to set insecure auth cookies in production" in str(exc_info.value)


# ==============================================================================
# 5. Permissive Behavior in Development
# ==============================================================================


def test_development_mode_allows_insecure_cookies_for_local_http(monkeypatch: pytest.MonkeyPatch) -> None:
    """Development mode permits cookie_secure=False for local HTTP testing."""
    for var in _ENV_VARS_TO_CLEAR:
        monkeypatch.delenv(var, raising=False)

    dev_cfg = Settings(_env_file=None, environment="development", cookie_secure=False)
    assert dev_cfg.is_production is False
    assert dev_cfg.cookie_secure_effective is False

    from backend.domain import auth_session

    monkeypatch.setattr(auth_session.settings, "environment", "development")
    monkeypatch.setattr(auth_session.settings, "cookie_secure", False)
    monkeypatch.setattr(auth_session.settings, "cookie_samesite", "lax")

    response = Response()
    _set_auth_cookies(response, access_token="dev_access", refresh_token="dev_refresh")

    set_cookie_headers = response.headers.getlist("set-cookie")
    assert len(set_cookie_headers) == 2
    for header in set_cookie_headers:
        # In development with cookie_secure=False, 'Secure' should not be present
        assert "secure" not in header.lower()
        # HttpOnly and SameSite should still be set for safety
        assert "httponly" in header.lower()
