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
import backend.imperial_models  # noqa: F401
import backend.imperial_v51_models  # noqa: F401
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
                "ALTER TABLE IF EXISTS historical_sources ADD COLUMN IF NOT EXISTS checksum TEXT;"
                "ALTER TABLE IF EXISTS historical_sources ADD COLUMN IF NOT EXISTS excerpt TEXT;"
                "ALTER TABLE IF EXISTS historical_assets ADD COLUMN IF NOT EXISTS offline_licensing_allowed BOOLEAN DEFAULT TRUE;"
                "ALTER TABLE IF EXISTS historical_assets ADD COLUMN IF NOT EXISTS cache_control_policy VARCHAR(255) DEFAULT 'public, max-age=31536000, immutable';"
                "ALTER TABLE IF EXISTS historical_assets ADD COLUMN IF NOT EXISTS is_private BOOLEAN NOT NULL DEFAULT FALSE;"
                "ALTER TABLE IF EXISTS historical_assets ADD COLUMN IF NOT EXISTS revoked_at TIMESTAMPTZ;"
                "ALTER TABLE IF EXISTS historical_assets ADD COLUMN IF NOT EXISTS revocation_reason TEXT;"
                "ALTER TABLE IF EXISTS historical_assets ADD COLUMN IF NOT EXISTS media_cms_item_id UUID;"
                "ALTER TABLE IF EXISTS users ADD COLUMN IF NOT EXISTS guardian_consent BOOLEAN DEFAULT FALSE;"
                "ALTER TABLE IF EXISTS users ADD COLUMN IF NOT EXISTS guardian_email VARCHAR(255);"
                "ALTER TABLE IF EXISTS ai_conversations ADD COLUMN IF NOT EXISTS retention_due_at TIMESTAMPTZ;"
                "ALTER TABLE IF EXISTS ai_conversations ADD COLUMN IF NOT EXISTS is_minor BOOLEAN DEFAULT FALSE;"
                "ALTER TABLE IF EXISTS ai_conversations ADD COLUMN IF NOT EXISTS guardian_consent_granted BOOLEAN DEFAULT FALSE;"
                "ALTER TABLE IF EXISTS ai_messages ADD COLUMN IF NOT EXISTS training_allowed BOOLEAN DEFAULT FALSE;"
                "ALTER TABLE IF EXISTS ai_messages ADD COLUMN IF NOT EXISTS pii_redacted BOOLEAN DEFAULT FALSE;"
                "ALTER TABLE IF EXISTS ai_jobs ADD COLUMN IF NOT EXISTS is_minor BOOLEAN DEFAULT FALSE;"
                "ALTER TABLE IF EXISTS ai_jobs ADD COLUMN IF NOT EXISTS training_allowed BOOLEAN DEFAULT FALSE;"
                "ALTER TABLE IF EXISTS ai_jobs ADD COLUMN IF NOT EXISTS pii_redacted BOOLEAN DEFAULT FALSE;"
            )
        )
        conn.commit()
    Base.metadata.create_all(eng)
    return eng
