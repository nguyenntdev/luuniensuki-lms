"""Create imperial_relic_inspections table for AR and turntable fallback inspection tasks (V5-T045).

Revision ID: 0065_imperial_relic_inspections
Revises: 0064_offline_licensing_cache_headers
Create Date: 2026-11-05 14:00:00.000000

Purely additive:
- Creates imperial_relic_inspections table with indices and constraints.
- Tracks relic inspections, mode (AR vs turntable 2D/3D), device tier, and anti-replay idempotency.
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0065_imperial_relic_inspections"
down_revision: Union[str, Sequence[str], None] = "0064_offline_licensing_cache_headers"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS imperial_relic_inspections (
            id                         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            content_scope              VARCHAR(50) NOT NULL DEFAULT 'STTT_IMPERIAL_CITY',
            user_id                    UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            target_slug                VARCHAR(120) NOT NULL,
            inspection_mode            VARCHAR(50) NOT NULL DEFAULT 'turntable_2d',
            camera_permission_granted  BOOLEAN NOT NULL DEFAULT FALSE,
            device_tier                VARCHAR(50) NOT NULL DEFAULT 'desktop',
            time_spent_seconds         INTEGER NOT NULL DEFAULT 0,
            angles_inspected           JSONB NOT NULL DEFAULT '[]'::jsonb,
            hotspots_examined          JSONB NOT NULL DEFAULT '[]'::jsonb,
            xp_awarded                 INTEGER NOT NULL DEFAULT 25,
            idempotency_key            VARCHAR(100) UNIQUE,
            created_at                 TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at                 TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT ck_imperial_relic_inspections_scope CHECK (content_scope = 'STTT_IMPERIAL_CITY'),
            CONSTRAINT uq_imperial_relic_user_target UNIQUE (user_id, target_slug)
        );

        CREATE INDEX IF NOT EXISTS idx_relic_inspections_user ON imperial_relic_inspections (user_id);
        CREATE INDEX IF NOT EXISTS idx_relic_inspections_target ON imperial_relic_inspections (target_slug);
        CREATE INDEX IF NOT EXISTS idx_relic_inspections_mode ON imperial_relic_inspections (inspection_mode);
        CREATE INDEX IF NOT EXISTS idx_relic_inspections_idempotency ON imperial_relic_inspections (idempotency_key);
        """
    )


def downgrade() -> None:
    pass
