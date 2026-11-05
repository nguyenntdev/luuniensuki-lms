"""Add heritage passport stamps table for verified site check-in and QR provenance

Revision ID: 0074_heritage_passport_stamps
Revises: 0073_evidence_board_comparative_links
Create Date: 2026-11-06 01:00:00.000000

V5-T092 / W09-A02: Verified heritage passport stamps schema.
Strictly additive:
- Creates heritage_passport_stamps table
- Creates indexes on user_id, site_slug, is_verified
- Creates unique constraint on (user_id, site_slug)
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers, used by Alembic.
revision: str = "0074_heritage_passport_stamps"
down_revision: Union[str, Sequence[str], None] = "0073_evidence_board_comparative_links"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS heritage_passport_stamps (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            site_slug VARCHAR(100) NOT NULL,
            site_name VARCHAR(255) NOT NULL,
            zone_slug VARCHAR(100) NOT NULL,
            verification_method VARCHAR(50) NOT NULL DEFAULT 'qr_code',
            qr_nonce VARCHAR(100),
            provenance_hash VARCHAR(64) NOT NULL,
            authority VARCHAR(100) NOT NULL DEFAULT 'HMCC_HUE_HERITAGE',
            stamped_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            checkin_count INTEGER NOT NULL DEFAULT 1,
            last_visited_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            is_verified BOOLEAN NOT NULL DEFAULT true,
            latitude FLOAT,
            longitude FLOAT,
            device_metadata JSONB,
            CONSTRAINT uq_heritage_passport_user_site UNIQUE (user_id, site_slug)
        );
        CREATE INDEX IF NOT EXISTS idx_heritage_passport_user
            ON heritage_passport_stamps(user_id);
        CREATE INDEX IF NOT EXISTS idx_heritage_passport_site
            ON heritage_passport_stamps(site_slug);
        CREATE INDEX IF NOT EXISTS idx_heritage_passport_verified
            ON heritage_passport_stamps(is_verified);
        """
    )


def downgrade() -> None:
    pass
