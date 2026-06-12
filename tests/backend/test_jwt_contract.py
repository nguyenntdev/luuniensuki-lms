"""JWT decode-contract tests for the deployed Python backend.

Task 14.2 (security-hardening-remediation). Exercises the real access-token
decode path ``backend.main._decode_access_token`` against hand-crafted tokens
so we control every claim precisely.

Validates Correctness Property 1 (No-forge) and Property 2 (Expiry-required):
- No-forge: a token signed with a key != the configured secret is rejected.
- Expiry-required: a token lacking ``exp`` or with a past ``exp`` is rejected.

**Validates: Requirements 8.2, 26.2**

The backend uses ``python-jose`` (``from jose import jwt``), not PyJWT, so we
build raw tokens with the same library and the same HS256 algorithm the decode
path uses. ``_decode_access_token`` returns the subject ``UUID`` on success and
``None`` on any failure, so each assertion matches that contract directly.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest
from jose import jwt

import backend.main as main
from backend.config import settings


ALGORITHM = "HS256"
CORRECT_SECRET = "correct-test-secret-key-for-jwt-contract"
WRONG_SECRET = "a-totally-different-secret-key-not-configured"
ISSUER = "luuniensuki"
AUDIENCE = "luuniensuki-app"


@pytest.fixture
def configure_jwt(monkeypatch):
    """Pin the JWT settings the decode path reads and let each test choose the
    ``JWT_VALIDATE_NEW_CLAIMS`` transition state.

    ``backend.main`` does ``from .config import settings``, so patching the
    shared ``settings`` object here is what the decode path observes.
    """

    def _apply(*, validate_new_claims: bool) -> None:
        monkeypatch.setattr(settings, "jwt_secret_key", CORRECT_SECRET)
        monkeypatch.setattr(settings, "jwt_algorithm", ALGORITHM)
        monkeypatch.setattr(settings, "jwt_issuer", ISSUER)
        monkeypatch.setattr(settings, "jwt_audience", AUDIENCE)
        monkeypatch.setattr(settings, "jwt_validate_new_claims", validate_new_claims)

    return _apply


def _valid_claims(**overrides) -> dict:
    """Build a complete, currently-valid access-token claim set.

    Individual tests override or delete claims to construct the rejection
    cases. The subject is a fresh UUID string and the token type is
    ``"access"`` so the positive control passes the full decode contract.
    """
    now = datetime.now(timezone.utc)
    claims = {
        "sub": str(uuid4()),
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=60)).timestamp()),
        "iss": ISSUER,
        "aud": AUDIENCE,
        "jti": uuid4().hex,
    }
    claims.update(overrides)
    return claims


def _encode(secret: str, claims: dict) -> str:
    return jwt.encode(claims, secret, algorithm=ALGORITHM)


# --- Property 1: No-forge -------------------------------------------------


@pytest.mark.parametrize("validate_new_claims", [False, True])
def test_token_signed_with_wrong_key_is_rejected(configure_jwt, validate_new_claims):
    """A token whose signature was produced with a different secret than the
    one ``backend.main`` is configured with must be rejected (returns ``None``).

    Claims are otherwise fully valid (correct ``iss``/``aud``, future ``exp``),
    so the signature mismatch is the only reason for rejection under either
    transition state.

    **Validates: Requirements 8.2, 26.2** (Property 1: No-forge)
    """
    configure_jwt(validate_new_claims=validate_new_claims)
    token = _encode(WRONG_SECRET, _valid_claims())
    assert main._decode_access_token(token) is None


# --- Property 2: Expiry-required -----------------------------------------


@pytest.mark.parametrize("validate_new_claims", [False, True])
def test_token_without_exp_is_rejected(configure_jwt, validate_new_claims):
    """A correctly-signed token that omits the ``exp`` claim must be rejected.

    The decode path requires ``exp`` regardless of the
    ``JWT_VALIDATE_NEW_CLAIMS`` flag, so this holds in both states.

    **Validates: Requirements 8.2, 26.2** (Property 2: Expiry-required)
    """
    configure_jwt(validate_new_claims=validate_new_claims)
    claims = _valid_claims()
    del claims["exp"]
    token = _encode(CORRECT_SECRET, claims)
    assert main._decode_access_token(token) is None


@pytest.mark.parametrize("validate_new_claims", [False, True])
def test_token_with_past_exp_is_rejected(configure_jwt, validate_new_claims):
    """A correctly-signed token whose ``exp`` is in the past must be rejected,
    independent of the transition flag.

    **Validates: Requirements 8.2, 26.2** (Property 2: Expiry-required)
    """
    configure_jwt(validate_new_claims=validate_new_claims)
    now = datetime.now(timezone.utc)
    claims = _valid_claims(
        iat=int((now - timedelta(hours=2)).timestamp()),
        exp=int((now - timedelta(hours=1)).timestamp()),
    )
    token = _encode(CORRECT_SECRET, claims)
    assert main._decode_access_token(token) is None


# --- Positive control -----------------------------------------------------


@pytest.mark.parametrize("validate_new_claims", [False, True])
def test_valid_unexpired_token_decodes_successfully(configure_jwt, validate_new_claims):
    """A validly-signed, unexpired token with the correct claims decodes to its
    subject ``UUID``.

    Run under both transition states: with the flag on, the matching
    ``iss``/``aud`` are required and validated; with it off, they are simply
    accepted. This guards against the rejection tests passing for the wrong
    reason.
    """
    configure_jwt(validate_new_claims=validate_new_claims)
    subject = uuid4()
    token = _encode(CORRECT_SECRET, _valid_claims(sub=str(subject)))
    result = main._decode_access_token(token)
    assert result == subject
    assert isinstance(result, UUID)
