"""Startup configuration validation tests (Workstream 1).

These tests exercise the production fail-closed startup validator defined in
``backend.config.Settings`` (the deployed runtime package — see
``tests/backend/conftest.py`` which imports ``backend.main``). They cover:

* Correctness Property 9 (Idempotent secret validation): in production, startup
  completes iff all required secrets are non-sentinel/non-empty; otherwise it
  halts before any component initializes.
* Correctness Property 3 (CORS allowlist startup refusal): a wildcard CORS
  origin combined with credentials is refused at startup in production.

Requirements: 1.1, 3.1, 28.1, 28.2.

By construction these assertions FAIL on the unfixed code (no validator / no
sentinel handling) and PASS once ``Settings._validate_production_security`` is
present (Req 27 — fail-on-unfixed / pass-on-fixed).

The tests are hermetic: each constructs ``Settings`` with explicit keyword
arguments and ``_env_file=None`` so no live ``.env`` is read, and the relevant
environment variables are cleared via ``monkeypatch`` so ambient configuration
cannot leak into the assertions.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from backend.config import SENTINELS, Settings  # noqa: E402


# Environment variables that could otherwise leak into the hermetic Settings
# construction below. pydantic-settings gives init kwargs precedence over env
# vars, but clearing these keeps the tests robust regardless of the host env.
_RELEVANT_ENV_VARS = (
    "ENVIRONMENT",
    "JWT_SECRET_KEY",
    "CORS_ORIGINS",
    "CORS_ALLOW_CREDENTIALS",
)

# A realistic, non-sentinel secret used for the "valid secrets" cases. Defined
# as a module constant so tests can assert it never appears in error messages.
STRONG_SECRET = "s3cr3t-Kx9f2Lq8Wz-not-a-sentinel-0123456789abcdef"


def _make_settings(monkeypatch: pytest.MonkeyPatch, **overrides) -> Settings:
    """Build a hermetic ``Settings`` instance.

    Clears the security-relevant env vars and disables ``.env`` loading so the
    only inputs are the explicit ``overrides``.
    """
    for var in _RELEVANT_ENV_VARS:
        monkeypatch.delenv(var, raising=False)
    return Settings(_env_file=None, **overrides)


@pytest.mark.parametrize("sentinel", sorted(SENTINELS))
def test_production_sentinel_jwt_secret_raises(
    monkeypatch: pytest.MonkeyPatch, sentinel: str
) -> None:
    """Production startup with a sentinel/empty JWT secret must halt.

    Covers both sentinel values ("" and "CHANGE_ME_IN_PRODUCTION"). The raised
    error must name the offending key but never echo the secret value.

    Validates Correctness Property 9. Requirements: 1.1, 28.1.
    """
    with pytest.raises(RuntimeError) as exc_info:
        _make_settings(
            monkeypatch,
            environment="production",
            jwt_secret_key=sentinel,
            # Keep CORS valid so the JWT failure is isolated.
            cors_origins="https://app.example.com",
            cors_allow_credentials=True,
        )

    message = str(exc_info.value)
    assert "JWT_SECRET_KEY" in message
    # The error must never leak the secret value itself. The empty-string
    # sentinel is unrepresentable in a message, so only guard the non-empty one.
    if sentinel:
        assert sentinel not in message


def test_production_valid_secrets_start_cleanly(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A strong secret plus an explicit, non-wildcard allowlist must start.

    Validates Correctness Property 9 (the "iff" success direction).
    Requirements: 1.1, 3.1, 28.2.
    """
    settings = _make_settings(
        monkeypatch,
        environment="production",
        jwt_secret_key=STRONG_SECRET,
        cors_origins="https://app.example.com,https://admin.example.com",
        cors_allow_credentials=True,
    )

    assert settings.is_production is True
    assert settings.jwt_secret_key not in SENTINELS
    assert "*" not in settings.cors_origins_list


def test_production_wildcard_with_credentials_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Wildcard CORS origin + credentials must be refused at startup.

    Validates Correctness Property 3 (CORS allowlist startup refusal).
    Requirements: 3.1, 28.1.
    """
    with pytest.raises(RuntimeError) as exc_info:
        _make_settings(
            monkeypatch,
            environment="production",
            # Strong secret so the failure is isolated to the CORS rule.
            jwt_secret_key=STRONG_SECRET,
            cors_origins="*",
            cors_allow_credentials=True,
        )

    assert "CORS_ORIGINS" in str(exc_info.value)


def test_development_permits_sentinel_secrets(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Development is permissive: sentinel/empty secrets must NOT raise.

    The validator only fails closed in production, so a development
    configuration with an empty secret and wildcard+credentials CORS must
    construct successfully. Requirements: 28.2.
    """
    settings = _make_settings(
        monkeypatch,
        environment="development",
        jwt_secret_key="",
        cors_origins="*",
        cors_allow_credentials=True,
    )

    assert settings.is_production is False
    assert settings.jwt_secret_key in SENTINELS
