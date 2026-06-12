"""Endpoint-level (integration) tests for object-level authorization (Req 20).

These drive a real resource-scoped HTTP endpoint with the ``TestClient`` to
verify the ownership contract end to end, complementing the unit tests in
``test_object_authorization.py`` (which exercise ``_ensure_owner_or_404``
directly with stubs).

Target endpoint: ``GET /api/v1/ai/insights/{user_id}`` — the route protected by
the ownership guard (``_ensure_owner_or_404`` / ``require_owner_or_authorized``)
in ``backend/main.py``. The ``{user_id}`` path param is the resource owner id.

Contract under test (Correctness Property 7 — Ownership; Req 20.1):
  - The resource owner accessing their own resource succeeds (2xx).
  - An admin accessing another user's resource succeeds (2xx).
  - A different authenticated, non-owner, non-admin user receives a *generic*
    404 with body message "Not found" — NOT a 403, and the response must not
    disclose whether the resource (the other user) exists (Req 20.2).

Fail-on-unfixed / pass-on-fixed: against unfixed code (no ownership guard) a
non-owner would either receive the resource (2xx, leaking another user's
insights) or a 403 (which discloses existence). The fixed code returns a generic
404. The non-owner test below asserts 404 + "Not found" and explicitly rejects
both 403 and any disclosure of the owner's identity, so it fails on unfixed code
and passes once the guard is in place.

The shared ``client`` fixture carries a single cookie jar, so to act as distinct
authenticated users we capture each user's access cookie at registration and
swap the jar per request via ``_act_as``.
"""

from sqlalchemy import select

import backend.main as main
from backend.models import User, UserRole

ACCESS_COOKIE = main.settings.access_cookie_name


def _register(client, email, display_name):
    """Register a user and return (user_id, access_token_cookie_value)."""
    res = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "password123",
            "display_name": display_name,
        },
    )
    assert res.status_code == 201, res.text
    token = client.cookies.get(ACCESS_COOKIE)
    assert token, "registration did not set an access cookie"
    user_id = res.json()["user"]["id"]
    return user_id, token


def _act_as(client, token):
    """Make subsequent requests authenticate as the user owning ``token``."""
    client.cookies.clear()
    client.cookies.set(ACCESS_COOKIE, token)


def test_owner_can_access_own_resource(client, db_session):
    """Owner success: user A fetches their own insights -> 2xx with data."""
    owner_id, owner_token = _register(client, "owner@example.com", "Owner A")

    _act_as(client, owner_token)
    res = client.get(f"/api/v1/ai/insights/{owner_id}")

    assert res.status_code == 200, res.text
    body = res.json()
    # Expected insights payload shape for the authoritative owner.
    assert "summary" in body
    assert "progress_data" in body
    # Fresh user has no progress, so the server-computed XP is the base 0.
    assert body["progress_data"]["xp"] == 0


def test_non_owner_gets_generic_404(client, db_session):
    """Non-owner: user B requests A's resource -> generic 404, no disclosure."""
    owner_id, _owner_token = _register(client, "owner2@example.com", "Owner A2")
    _non_owner_id, non_owner_token = _register(
        client, "intruder@example.com", "Intruder B"
    )

    # Confirm B is an ordinary, non-admin user (the default registered role).
    intruder = db_session.execute(
        select(User).where(User.email == "intruder@example.com")
    ).scalar_one()
    assert intruder.role not in main.ADMIN_ROLES

    _act_as(client, non_owner_token)
    res = client.get(f"/api/v1/ai/insights/{owner_id}")

    # Generic 404 — not a 403 (which would disclose existence / authz).
    assert res.status_code == 404, res.text
    assert res.status_code != 403
    body = res.json()
    # Message is generic and reveals nothing about the resource owner.
    assert body["error"]["message"] == "Not found"
    serialized = res.text
    assert "Owner A2" not in serialized
    assert "owner2@example.com" not in serialized
    assert str(owner_id) not in serialized


def test_admin_can_access_others_resource(client, db_session):
    """Authorized admin accessing another user's resource succeeds (2xx)."""
    owner_id, _owner_token = _register(client, "owner3@example.com", "Owner A3")
    _admin_id, admin_token = _register(client, "admin@example.com", "Admin")

    # Elevate the second user to admin; role is read from the DB per request,
    # so the previously issued token now authenticates as an admin.
    admin = db_session.execute(
        select(User).where(User.email == "admin@example.com")
    ).scalar_one()
    admin.role = UserRole.admin
    db_session.commit()

    _act_as(client, admin_token)
    res = client.get(f"/api/v1/ai/insights/{owner_id}")

    assert res.status_code == 200, res.text
    assert "summary" in res.json()
