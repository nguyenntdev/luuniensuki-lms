"""Unit tests for object-level authorization helper (Requirement 20).

These tests exercise ``_ensure_owner_or_404`` directly with lightweight user
stubs so they do not require a database connection. The helper must permit the
resource owner and admins, and deny everyone else with a generic 404 that does
not disclose whether the resource exists (Req 20.2).
"""

import uuid
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

import backend.main as main
from backend.models import UserRole


def _user(user_id, role):
    return SimpleNamespace(id=user_id, role=role)


def test_owner_is_permitted():
    owner_id = uuid.uuid4()
    # Owner accessing their own resource: no exception.
    main._ensure_owner_or_404(owner_id, _user(owner_id, UserRole.learner))


@pytest.mark.parametrize("role", [UserRole.admin, UserRole.super_admin])
def test_admin_roles_are_permitted(role):
    owner_id = uuid.uuid4()
    actor = _user(uuid.uuid4(), role)
    # Admins may act on resources they do not own: no exception.
    main._ensure_owner_or_404(owner_id, actor)


@pytest.mark.parametrize("role", [UserRole.learner, UserRole.teacher, UserRole.guest])
def test_non_owner_non_admin_gets_generic_404(role):
    owner_id = uuid.uuid4()
    actor = _user(uuid.uuid4(), role)
    with pytest.raises(HTTPException) as exc_info:
        main._ensure_owner_or_404(owner_id, actor)
    # Generic 404 that does not disclose resource existence (Req 20.2).
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Not found"
