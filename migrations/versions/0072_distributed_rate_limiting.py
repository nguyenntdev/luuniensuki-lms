"""Add distributed rate limit entries table for sliding-window request throttling

Revision ID: 0072_distributed_rate_limiting
Revises: 0071_research_publication_releases
Create Date: 2026-11-05 22:00:00.000000

V5-T088 / W08-A08: Distributed sliding-window rate limiting schema.
Strictly additive:
- Creates rate_limit_entries table
- Creates indexes on (key, created_at) and (created_at)
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = "0072_distributed_rate_limiting"
down_revision: Union[str, Sequence[str], None] = "0071_research_publication_releases"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS rate_limit_entries (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            key VARCHAR(255) NOT NULL,
            endpoint VARCHAR(128) NOT NULL DEFAULT '',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE INDEX IF NOT EXISTS idx_rate_limit_entries_key_created_at
            ON rate_limit_entries(key, created_at);
        CREATE INDEX IF NOT EXISTS idx_rate_limit_entries_created_at
            ON rate_limit_entries(created_at);
        """
    )


def downgrade() -> None:
    # Additive-only policy forbids destructive drops in production
    pass
