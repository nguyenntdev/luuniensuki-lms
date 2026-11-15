"""Make study test helpers importable without package-name collisions.

Each study ships a uniquely-named helper module (``lnXX_helpers.py``), so
adding every study directory to ``sys.path`` is safe and lets tests import
``from lnXX_helpers import ...`` regardless of collection order.
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

for sub in sorted(p for p in HERE.iterdir() if p.is_dir()):
    if sub.name.startswith("__"):
        continue
    s = str(sub)
    if s not in sys.path:
        sys.path.insert(0, s)
