# -*- coding: utf-8 -*-
"""Pytest fixtures for V5 baseline test suite.

Configures isolated test database for V5-T006 to avoid concurrency conflicts
with other parallel W00 development agents.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Database URL resolution: honor existing DATABASE_URL, fallback to DATABASE_URL_T006 or luuniensuki_test
if "DATABASE_URL" not in os.environ:
    os.environ["DATABASE_URL"] = os.environ.get(
        "DATABASE_URL_T006",
        "postgresql+psycopg://postgres:postgres@localhost:5432/luuniensuki_t006",
    )

import pytest
from sqlalchemy import create_engine, text
from backend.base_model import Base
import backend.history_models  # noqa: F401
import backend.models_rbpc  # noqa: F401
import backend.models  # noqa: F401
import backend.main as main  # noqa: F401

pytest_plugins = ["tests.backend.conftest"]


@pytest.fixture(scope="session")
def engine():
    db_url = os.environ["DATABASE_URL"]
    eng = create_engine(db_url, pool_pre_ping=True)
    with eng.connect() as conn:
        conn.execute(
            text(
                "CREATE EXTENSION IF NOT EXISTS pgcrypto; "
                "CREATE EXTENSION IF NOT EXISTS unaccent; "
                "CREATE EXTENSION IF NOT EXISTS pg_trgm; "
                "ALTER TABLE IF EXISTS rbpc_inquiries ADD COLUMN IF NOT EXISTS sla_due_at TIMESTAMPTZ;"
            )
        )
        conn.commit()
    Base.metadata.create_all(eng)
    return eng
