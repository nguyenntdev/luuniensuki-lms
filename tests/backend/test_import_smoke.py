"""Import smoke test for the modularized backend package.

Task 1.3 (backend-modularization). As ``backend/main.py`` is decomposed into a
package, each new module must import cleanly and the application factory must
construct without raising. This test asserts:

* ``backend.app.create_app`` is importable and returns a FastAPI instance.
* Every backend module extracted during the refactor imports without a
  ``ModuleNotFoundError`` (or any ImportError).

As new modules are extracted in later increments (``backend.deps``,
``backend.domain.*``, ``backend.schemas.*``, ``backend.routers.*``), add their
dotted names to ``_EXPECTED_MODULES`` so the smoke test grows with the package.
A module listed here that does not yet exist is reported as a failure, which is
the intended signal that an increment's wiring is incomplete.

Requirements: 1.1, 4.1.

NOTE: This test requires the project runtime (FastAPI/SQLAlchemy/pydantic) to be
installed to import ``backend.main``/``backend.app``. It runs in CI / a developer
environment with dependencies installed.
"""

from __future__ import annotations

import importlib

import pytest
from fastapi import FastAPI


# Modules that must import cleanly. Extend this list as the package grows in
# later tasks (deps.py, domain/, schemas/, routers/...).
_EXPECTED_MODULES = [
    "backend.config",
    "backend.errors",
    "backend.models",
    "backend.security",
    "backend.rbac",
    "backend.app",
    "backend.db",
    "backend.deps",
    "backend.domain",
    "backend.domain.gamification",
    "backend.domain.auth_session",
    "backend.apischemas",
    "backend.apischemas.auth",
    "backend.apischemas.users",
    "backend.apischemas.content",
    "backend.apischemas.quests",
    "backend.apischemas.ai",
    "backend.apischemas.progress",
    "backend.apischemas.admin",
    "backend.routers",
    "backend.routers.auth",
    "backend.routers.users",
    "backend.routers.content",
    "backend.routers.gamification",
    "backend.routers.classrooms",
    "backend.routers.live",
    "backend.routers.admin",
    "backend.routers.ai",
    "backend.routers.social",
    "backend.routers.misc",
    "backend.domain.helpers",
    "backend.main",
]


@pytest.mark.parametrize("module_name", _EXPECTED_MODULES)
def test_module_imports_without_error(module_name: str):
    """Each extracted backend module imports without ModuleNotFoundError (Req 1.1, 4.1)."""
    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError as exc:  # pragma: no cover - failure path
        pytest.fail(f"{module_name} raised ModuleNotFoundError: {exc}")
    except ImportError as exc:  # pragma: no cover - failure path
        pytest.fail(f"{module_name} raised ImportError: {exc}")
    assert module is not None


def test_create_app_constructs_a_fastapi_instance():
    """``create_app()`` builds a FastAPI app without raising (Req 1.1, 4.1)."""
    from backend.app import create_app

    app = create_app()
    assert isinstance(app, FastAPI)


def test_main_exposes_app_instance():
    """``backend.main.app`` is the deployed FastAPI instance built by the factory."""
    import backend.main as main

    assert isinstance(main.app, FastAPI)
