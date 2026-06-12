# -*- coding: utf-8 -*-
"""Validation-error envelope contract tests (Requirements 14.1, 27.1).

These tests pin the behaviour of the ``RequestValidationError`` handler wired
up in ``backend/main.py`` (``backend.errors.validation_exception_handler`` +
``_sanitize_validation_errors``). The handler MUST:

* return ONLY field locations + messages + type for each error,
* never echo the submitted input value (the pydantic ``input``/``ctx`` keys
  are dropped),
* redact fields flagged sensitive (``password`` etc.) by replacing the human
  readable message with a generic ``"invalid value"``,
* wrap everything in the standard envelope
  ``{"error": {"code", "message", "details"}}`` where ``details`` is a dict
  (``AppError.details`` is typed ``Optional[dict]``).

Endpoint exercised: ``POST /api/v1/auth/register`` whose schema
(``AuthRegisterRequest``) is::

    email: EmailStr
    password: str (min_length=8, max_length=72)   # SENSITIVE
    display_name: str (min_length=1, max_length=100)

Invalid body used (see ``INVALID_BODY``):

* ``email`` carries a distinctive NON-sensitive sentinel and is not a valid
  email address -> triggers a 422 on the ``email`` field.
* ``password`` carries a distinctive sensitive sentinel and is longer than the
  72-character maximum -> triggers a 422 on the ``password`` (sensitive) field.

Fail-on-unfixed / pass-on-fixed:

* On UNFIXED code (FastAPI's default validation handler) the 422 body includes
  the raw ``errors`` list whose ``input`` key echoes the submitted password,
  so ``SENSITIVE_SENTINEL`` would appear verbatim in ``response.text`` and the
  no-echo assertions FAIL.
* On FIXED code the ``input``/``ctx`` keys are dropped and the sensitive
  message is replaced with ``"invalid value"``, so neither sentinel appears and
  the assertions PASS.
"""

# A distinctive value placed in the *sensitive* ``password`` field. The handler
# must never surface this anywhere in the response.
SENSITIVE_SENTINEL = "SUPERSECRET_SENTINEL_123"

# A distinctive value placed in a *non-sensitive* field (``email``). The handler
# reports the field location + message but must not echo this raw value.
NONSENSITIVE_SENTINEL = "NONSENSITIVE_SENTINEL_xyz"

# Body that fails validation on two fields at once:
#   - email: invalid address (non-sensitive sentinel embedded)
#   - password: 96 chars > max_length=72 (sensitive sentinel embedded)
INVALID_BODY = {
    "email": f"{NONSENSITIVE_SENTINEL}-not-an-email",
    "password": SENSITIVE_SENTINEL * 4,  # 96 chars, exceeds max_length=72
    "display_name": "Valid Name",
}


def _post_invalid(client):
    resp = client.post("/api/v1/auth/register", json=INVALID_BODY)
    assert resp.status_code == 422, resp.text
    return resp


def test_sensitive_field_value_is_never_echoed(client):
    """The submitted password value must not leak anywhere in the response."""
    resp = _post_invalid(client)

    # Raw response text must not contain the sensitive submitted value.
    assert SENSITIVE_SENTINEL not in resp.text

    # And it must not be hiding inside the structured body either.
    body = resp.json()
    assert SENSITIVE_SENTINEL not in repr(body)


def test_handler_returns_locations_and_messages_without_echoing_input(client):
    """Errors expose loc + msg + type only; raw submitted values are not echoed."""
    resp = _post_invalid(client)
    body = resp.json()

    errors = body["error"]["details"]["errors"]
    assert isinstance(errors, list) and len(errors) >= 2

    # Every error item exposes ONLY field location, message and type.
    for err in errors:
        assert set(err.keys()) == {"loc", "msg", "type"}
        # The submitted-input echo keys must be absent.
        assert "input" not in err
        assert "ctx" not in err
        assert isinstance(err["loc"], list)
        assert isinstance(err["msg"], str)

    # The non-sensitive submitted value is not echoed verbatim, even though its
    # field location ("email") is reported.
    assert NONSENSITIVE_SENTINEL not in resp.text

    by_field = {tuple(err["loc"]): err for err in errors}

    # Email error: located on the email field, with a real (non-redacted) message
    # that does not contain the submitted value.
    email_err = by_field[("body", "email")]
    assert email_err["msg"]  # a human-readable message is present
    assert NONSENSITIVE_SENTINEL not in email_err["msg"]

    # Password error: sensitive field -> message is redacted to a generic value.
    password_err = by_field[("body", "password")]
    assert password_err["msg"] == "invalid value"
    assert SENSITIVE_SENTINEL not in password_err["msg"]


def test_error_envelope_shape(client):
    """Envelope is {"error": {"code", "message", "details"}} with details a dict."""
    resp = _post_invalid(client)
    body = resp.json()

    assert set(body.keys()) == {"error"}
    error = body["error"]
    assert set(error.keys()) == {"code", "message", "details"}

    assert error["code"] == "VALIDATION_ERROR"
    assert error["message"] == "Invalid request parameters"

    # AppError.details is typed Optional[dict]; the validation handler always
    # supplies a dict carrying the sanitized error list.
    assert error["details"] is None or isinstance(error["details"], dict)
    assert isinstance(error["details"], dict)
    assert "errors" in error["details"]
