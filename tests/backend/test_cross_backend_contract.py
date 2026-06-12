"""Cross-backend JWT contract tests (Python verifier side).

Task 14.4 (security-hardening-remediation). The Python and Rust backends share
the SAME JWT secret, algorithm (HS256), and claim set
``{sub, iat, exp, role, type, jti, iss, aud}`` (design.md "Workstream 3"). Because
of that shared contract, a token minted by the Rust ``issue_access_token`` is
structurally decodable by the Python verifier ``backend.main._decode_access_token``
and vice versa.

A live cross-process integration test is not possible in this environment (no
running services / no Rust toolchain), so this test validates the property at the
SAME layer as the existing contract tests: it simulates a "Rust-issued" token by
minting a raw HS256 token whose claim shape EXACTLY matches what
``backend-rust/src/auth.rs::issue_access_token`` produces, signs it with the shared
secret, and asserts the Python verifier accepts it (and rejects it when standard
validation fails). The Rust half of this property lives in
``backend-rust/src/auth.rs`` (``cross_backend_python_issued_token_accepted`` and
``cross_backend_peer_token_rejected_when_standard_validation_fails``).

Validates Correctness Property 4 (Cross-backend acceptance): a token issued by one
backend under the consistent contract validates on the other for all
standard-valid tokens, and is rejected whenever standard validation fails.

**Validates: Requirements 8.2, 26.2**

The backend uses ``python-jose`` (``from jose import jwt``), so we build the
peer-issued token with the same library and HS256 algorithm the decode path uses.
``_decode_access_token`` returns the subject ``UUID`` on success and ``None`` on any
failure, so each assertion matches that contract directly. Secrets and the
``configure_jwt`` monkeypatch pattern are kept consistent with
``tests/backend/test_jwt_contract.py``.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest
from jose import jwt

import backend.main as main
from backend.config import settings


ALGORITHM = "HS256"
# Shared secret both backends are configured with for these tests. Reuses the
# same constants/pattern as tests/backend/test_jwt_contract.py.
CORRECT_SECRET = "correct-test-secret-key-for-jwt-contract"
WRONG_SECRET = "a-totally-different-secret-key-not-configured"
ISSUER = "luuniensuki"
AUDIENCE = "luuniensuki-app"


@pytest.fixture
def configure_jwt(monkeypatch):
    """Pin the JWT settings the decode path reads and let each test choose the
    ``JWT_VALIDATE_NEW_CLAIMS`` transition state.

    ``backend.main`` does ``from .config import settings``, so patching the
    shared ``settings`` object here is what the decode path observes. Mirrors
    the fixture in ``tests/backend/test_jwt_contract.py``.
    """

    def _apply(*, validate_new_claims: bool) -> None:
        monkeypatch.setattr(settings, "jwt_secret_key", CORRECT_SECRET)
        monkeypatch.setattr(settings, "jwt_algorithm", ALGORITHM)
        monkeypatch.setattr(settings, "jwt_issuer", ISSUER)
        monkeypatch.setattr(settings, "jwt_audience", AUDIENCE)
        monkeypatch.setattr(settings, "jwt_validate_new_claims", validate_new_claims)

    return _apply


def _rust_issued_access_claims(**overrides) -> dict:
    """Build the EXACT claim set the Rust ``issue_access_token`` emits.

    Rust's ``Claims`` struct serializes ``{sub, iat, exp, role, type, iss, aud,
    jti}`` (see ``backend-rust/src/auth.rs``). ``token_type`` is renamed to
    ``"type"`` via serde, and an access token carries ``type = "access"``. We
    reproduce that shape here so the Python verifier sees a token
    indistinguishable from one a live Rust service would issue.
    """
    now = datetime.now(timezone.utc)
    claims = {
        "sub": str(uuid4()),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=60)).timestamp()),
        "role": "user",
        "type": "access",
        "iss": ISSUER,
        "aud": AUDIENCE,
        "jti": uuid4().hex,
    }
    claims.update(overrides)
    return claims


def _encode(secret: str, claims: dict) -> str:
    return jwt.encode(claims, secret, algorithm=ALGORITHM)


# --- Property 4: Cross-backend acceptance --------------------------------


@pytest.mark.parametrize("validate_new_claims", [False, True])
def test_rust_issued_token_is_accepted_by_python_verifier(
    configure_jwt, validate_new_claims
):
    """A token minted with the Rust issuer's exact claim shape, signed with the
    shared secret, decodes to its subject ``UUID`` in the Python verifier.

    Checked under both ``JWT_VALIDATE_NEW_CLAIMS`` states: with the flag on the
    matching ``iss``/``aud`` are required and validated; with it off they are
    simply accepted. This is the cross-backend acceptance direction of
    Property 4.

    **Validates: Requirements 8.2, 26.2** (Property 4: Cross-backend acceptance)
    """
    configure_jwt(validate_new_claims=validate_new_claims)
    subject = uuid4()
    token = _encode(CORRECT_SECRET, _rust_issued_access_claims(sub=str(subject)))
    result = main._decode_access_token(token)
    assert result == subject
    assert isinstance(result, UUID)


# --- Property 4: rejection when standard validation fails ----------------


@pytest.mark.parametrize("validate_new_claims", [False, True])
def test_rust_issued_token_with_wrong_secret_is_rejected(
    configure_jwt, validate_new_claims
):
    """A peer-issued token whose signature was produced with a different secret
    than the verifier is configured with must be rejected (returns ``None``),
    regardless of the transition state.

    **Validates: Requirements 8.2, 26.2** (Property 4: standard validation fails)
    """
    configure_jwt(validate_new_claims=validate_new_claims)
    token = _encode(WRONG_SECRET, _rust_issued_access_claims())
    assert main._decode_access_token(token) is None


@pytest.mark.parametrize("validate_new_claims", [False, True])
def test_rust_issued_token_with_past_exp_is_rejected(
    configure_jwt, validate_new_claims
):
    """A correctly-signed peer-issued token whose ``exp`` is in the past must be
    rejected, independent of the transition flag.

    **Validates: Requirements 8.2, 26.2** (Property 4: standard validation fails)
    """
    configure_jwt(validate_new_claims=validate_new_claims)
    now = datetime.now(timezone.utc)
    token = _encode(
        CORRECT_SECRET,
        _rust_issued_access_claims(
            iat=int((now - timedelta(hours=2)).timestamp()),
            exp=int((now - timedelta(hours=1)).timestamp()),
        ),
    )
    assert main._decode_access_token(token) is None


def test_rust_issued_token_with_wrong_issuer_is_rejected_when_enforced(configure_jwt):
    """When ``JWT_VALIDATE_NEW_CLAIMS`` is on, a peer-issued token whose ``iss``
    does not match the configured issuer must be rejected.

    The token is otherwise fully valid (correct secret, future ``exp``, correct
    ``aud``), so the issuer mismatch is the sole cause of rejection. This guards
    the enforcement half of the consistent-contract transition.

    **Validates: Requirements 8.2, 26.2** (Property 4: standard validation fails)
    """
    configure_jwt(validate_new_claims=True)
    token = _encode(CORRECT_SECRET, _rust_issued_access_claims(iss="evil-issuer"))
    assert main._decode_access_token(token) is None


def test_rust_issued_token_with_wrong_audience_is_rejected_when_enforced(configure_jwt):
    """When ``JWT_VALIDATE_NEW_CLAIMS`` is on, a peer-issued token whose ``aud``
    does not match the configured audience must be rejected.

    Otherwise fully valid, so the audience mismatch is the sole cause.

    **Validates: Requirements 8.2, 26.2** (Property 4: standard validation fails)
    """
    configure_jwt(validate_new_claims=True)
    token = _encode(CORRECT_SECRET, _rust_issued_access_claims(aud="evil-audience"))
    assert main._decode_access_token(token) is None
