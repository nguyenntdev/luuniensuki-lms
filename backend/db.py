# -*- coding: utf-8 -*-
"""Database engine, session factory, and the ``get_db`` request dependency.

Extracted from ``backend.main`` (backend-modularization task 2.1) so that both
``backend.main`` and ``backend.deps`` can import these primitives without a
circular import (neither imports ``backend.main``).

STRICTLY behavior-preserving: the engine/session construction and ``get_db``
generator are moved verbatim. ``backend.main`` re-exports ``engine``,
``SessionLocal``, and ``get_db`` so existing references (and
``tests/backend/conftest.py``'s ``main.app.dependency_overrides[main.get_db]``)
continue to resolve to the same objects.
"""
from __future__ import annotations

from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from .config import settings


engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
