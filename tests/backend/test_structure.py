"""Package-structure assertions for the modularized backend.

Task 6.3 (backend-modularization). These tests encode the structural invariants
from Requirements 3.1, 3.2 and (eventually) 1.3:

* No empty/placeholder ``backend/routes/`` package remains — routing code lives
  in the populated ``backend/routers/`` package instead (Req 3.1, 3.2).
* ``main.py`` is reduced below a line threshold once it becomes a thin entry
  shim (Req 1.3). This assertion is currently PARKED behind ``MAIN_PY_MAX_LINES``
  being ``None`` because the router extraction (tasks 5.2-5.6) and the thin-shim
  reduction (task 6.1) are not yet complete; main.py still hosts the
  not-yet-extracted endpoints. When 6.1 lands, set ``MAIN_PY_MAX_LINES`` to the
  agreed threshold (e.g. 200) to activate the check.
"""

from __future__ import annotations

from pathlib import Path

import pytest

_BACKEND_DIR = Path(__file__).resolve().parents[2] / "backend"

# main.py is now the thin entry shim (task 6.1): it only builds the app via
# ``create_app()`` and re-exports the handful of names the test suite references.
# The threshold keeps it honest with comfortable headroom over its current size.
MAIN_PY_MAX_LINES: int | None = 100


def test_no_empty_routes_package():
    """The legacy empty ``backend/routes/`` package must not exist (Req 3.1, 3.2)."""
    routes_pkg = _BACKEND_DIR / "routes"
    assert not routes_pkg.exists(), (
        f"Empty/placeholder routes package still present at {routes_pkg}; "
        "routing code belongs in backend/routers/."
    )


def test_routers_package_is_populated():
    """Routing code lives in a populated ``backend/routers/`` package (Req 3.2)."""
    routers_pkg = _BACKEND_DIR / "routers"
    assert routers_pkg.is_dir(), "backend/routers/ package is missing."
    router_modules = [
        p for p in routers_pkg.glob("*.py") if p.name != "__init__.py"
    ]
    assert router_modules, "backend/routers/ contains no router modules."


@pytest.mark.skipif(
    MAIN_PY_MAX_LINES is None,
    reason="main.py thin-shim reduction (task 6.1) not yet complete.",
)
def test_main_py_below_line_threshold():
    """Once a thin shim, main.py stays below the agreed line threshold (Req 1.3)."""
    main_py = _BACKEND_DIR / "main.py"
    line_count = sum(1 for _ in main_py.open(encoding="utf-8"))
    assert line_count <= MAIN_PY_MAX_LINES, (
        f"main.py has {line_count} lines, exceeding the {MAIN_PY_MAX_LINES}-line "
        "threshold for the thin entry shim."
    )
