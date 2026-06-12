"""OpenAPI snapshot test — behavior-preservation oracle for backend modularization.

Task 1.2 (backend-modularization). The decomposition of ``backend/main.py`` into a
package must NOT change the public HTTP contract. This test serializes the live
OpenAPI schema of the deployed app (``backend.main.app``) and compares it against a
committed fixture, so any accidental change to a path, method, parameter, request
body, response model, or status code during a refactor increment is caught.

Requirements: 2.1, 2.3.

Workflow:
* First run (no fixture yet): the schema is written to the fixture and the test is
  skipped with an explanatory message. Commit the generated fixture; it becomes the
  pre-refactor contract oracle.
* Subsequent runs: the current schema must equal the fixture byte-for-byte (after a
  canonical, sorted-key JSON serialization). A mismatch fails the test and prints a
  unified diff of the first differing lines.
* Intentional, reviewed contract changes: delete/regenerate the fixture deliberately
  (e.g. ``REGENERATE_OPENAPI_SNAPSHOT=1 pytest ...``) — never as a silent side effect
  of a refactor.

NOTE: This test requires the FastAPI/SQLAlchemy/pydantic runtime to import
``backend.main``. It is intended to run in CI / a developer environment with the
project dependencies installed; it cannot execute in a bare environment without
those packages.
"""

from __future__ import annotations

import difflib
import json
import os
from pathlib import Path

import pytest

import backend.main as main


FIXTURE_DIR = Path(__file__).parent / "fixtures"
FIXTURE_PATH = FIXTURE_DIR / "openapi_snapshot.json"

# Set this env var to deliberately (re)generate the fixture after a reviewed,
# intentional contract change.
_REGEN_ENV = "REGENERATE_OPENAPI_SNAPSHOT"


def _canonical(schema: dict) -> str:
    """Serialize the schema deterministically (sorted keys, stable separators)."""
    return json.dumps(schema, sort_keys=True, indent=2, ensure_ascii=False) + "\n"


def _current_schema() -> dict:
    """Return the live OpenAPI schema for the deployed app."""
    return main.app.openapi()


def test_openapi_schema_matches_snapshot():
    """The live OpenAPI schema must equal the committed snapshot (Req 2.1, 2.3)."""
    current = _canonical(_current_schema())

    if os.environ.get(_REGEN_ENV) == "1" or not FIXTURE_PATH.exists():
        FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
        FIXTURE_PATH.write_text(current, encoding="utf-8")
        pytest.skip(
            f"OpenAPI snapshot written to {FIXTURE_PATH}. Commit this fixture; it "
            "is the behavior-preservation oracle for subsequent refactor increments."
        )

    expected = FIXTURE_PATH.read_text(encoding="utf-8")
    if current != expected:
        diff = "\n".join(
            difflib.unified_diff(
                expected.splitlines(),
                current.splitlines(),
                fromfile="openapi_snapshot.json (committed)",
                tofile="current schema",
                lineterm="",
                n=2,
            )
        )
        # Cap the diff so a large drift does not flood the report.
        capped = "\n".join(diff.splitlines()[:200])
        pytest.fail(
            "OpenAPI schema drifted from the committed snapshot. If this change is "
            "intentional and reviewed, regenerate the fixture with "
            f"{_REGEN_ENV}=1. First differing lines:\n{capped}"
        )
