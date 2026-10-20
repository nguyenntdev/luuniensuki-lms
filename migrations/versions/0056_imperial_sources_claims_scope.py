"""add content_scope to historical_sources, historical_claims, and historical_entities

STTTNNĐ (Lưu Niên — Đại Nội Huế) Phase V5.1 Historical Corpus Expansion:
Adds content_scope to:
- historical_sources
- historical_claims
- historical_entities

All operations are additive and strictly safe.

Revision ID: 0056_imperial_sources_claims_scope
Revises: 0055_imperial_v51_extensions
Create Date: 2026-10-16
"""
from __future__ import annotations

from alembic import op


revision = "0056_imperial_sources_claims_scope"
down_revision = "0055_imperial_v51_extensions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE historical_sources
        ADD COLUMN IF NOT EXISTS content_scope TEXT DEFAULT 'STTT_IMPERIAL_CITY';
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_historical_sources_scope ON historical_sources(content_scope);")

    op.execute(
        """
        ALTER TABLE historical_claims
        ADD COLUMN IF NOT EXISTS content_scope TEXT DEFAULT 'STTT_IMPERIAL_CITY';
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_historical_claims_scope ON historical_claims(content_scope);")

    op.execute(
        """
        ALTER TABLE historical_entities
        ADD COLUMN IF NOT EXISTS content_scope TEXT DEFAULT 'STTT_IMPERIAL_CITY';
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_historical_entities_scope ON historical_entities(content_scope);")


def downgrade() -> None:
    pass
