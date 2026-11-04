"""Add offline licensing, cache control policy, and cache revocation registry

Revision ID: 0064_offline_licensing_cache_headers
Revises: 0063_school_teacher_classroom_model
Create Date: 2026-11-05 12:00:00.000000

V5-T048: Offline licensing and cache headers in Nginx configuration, public/models/,
and backend asset endpoints.
Strictly additive:
- Adds offline_licensing_allowed, cache_control_policy, is_private, revoked_at,
  and revocation_reason to historical_assets table.
- Creates asset_cache_revocations table to track asset invalidation events
  and purge status for stale CDN protection.
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0064_offline_licensing_cache_headers"
down_revision: Union[str, Sequence[str], None] = "0063_school_teacher_classroom_model"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add offline licensing and cache policy columns to historical_assets table
    op.execute(
        """
        ALTER TABLE historical_assets ADD COLUMN IF NOT EXISTS offline_licensing_allowed BOOLEAN DEFAULT TRUE;
        ALTER TABLE historical_assets ADD COLUMN IF NOT EXISTS cache_control_policy VARCHAR(255) DEFAULT 'public, max-age=31536000, immutable';
        ALTER TABLE historical_assets ADD COLUMN IF NOT EXISTS is_private BOOLEAN NOT NULL DEFAULT FALSE;
        ALTER TABLE historical_assets ADD COLUMN IF NOT EXISTS revoked_at TIMESTAMPTZ;
        ALTER TABLE historical_assets ADD COLUMN IF NOT EXISTS revocation_reason TEXT;
        CREATE INDEX IF NOT EXISTS idx_historical_assets_private ON historical_assets (is_private);
        CREATE INDEX IF NOT EXISTS idx_historical_assets_offline ON historical_assets (offline_licensing_allowed);
        """
    )

    # 2. Create asset_cache_revocations table for cache invalidation registry
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS asset_cache_revocations (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            asset_id VARCHAR(255) NOT NULL,
            asset_url VARCHAR(1000),
            revocation_reason TEXT NOT NULL,
            revoked_by VARCHAR(255) NOT NULL DEFAULT 'system',
            revoked_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            cdn_purged BOOLEAN NOT NULL DEFAULT FALSE,
            purge_timestamp TIMESTAMPTZ
        );
        CREATE INDEX IF NOT EXISTS idx_asset_revocations_asset ON asset_cache_revocations (asset_id);
        CREATE INDEX IF NOT EXISTS idx_asset_revocations_revoked_at ON asset_cache_revocations (revoked_at);
        CREATE INDEX IF NOT EXISTS idx_asset_revocations_cdn_purged ON asset_cache_revocations (cdn_purged);
        """
    )


def downgrade() -> None:
    # Strictly additive migrations keep downgrade safe / non-destructive
    pass
