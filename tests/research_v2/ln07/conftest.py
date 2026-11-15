"""Pytest bootstrap for the LN-07 test package (standalone importable).

Adds the repo root to sys.path so ``research_v2`` resolves no matter which
directory pytest is invoked from. Test helpers live in ``ln07_helpers.py``
(uniquely named to avoid module-name collisions across study dirs).
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
