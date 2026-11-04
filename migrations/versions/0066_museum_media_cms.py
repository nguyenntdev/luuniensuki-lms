"""Add museum operator media CMS items and historical asset linkage

Revision ID: 0066_museum_media_cms
Revises: 0065_imperial_relic_inspections
Create Date: 2026-11-05 15:00:00.000000

V5-T050: Museum operator media CMS.
Strictly additive:
- Creates media_cms_items table for operator media uploads, licensing verification,
  and staged approval workflow.
- Creates indexes on publication_status, relic_slug, historical_entity_id, asset_type, created_at.
- Adds media_cms_item_id column to historical_assets table for persistent bidirectional linkage.
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0066_museum_media_cms"
down_revision: Union[str, Sequence[str], None] = "0065_imperial_relic_inspections"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create media_cms_items table
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS media_cms_items (
            id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            title                 VARCHAR(255) NOT NULL,
            description           TEXT,
            asset_type            VARCHAR(50) NOT NULL DEFAULT 'image',
            file_format           VARCHAR(20) NOT NULL,
            mime_type             VARCHAR(100) NOT NULL,
            storage_url           TEXT NOT NULL,
            thumbnail_url         TEXT,
            file_size_bytes       BIGINT NOT NULL,
            sha256                VARCHAR(64) NOT NULL,
            rights_owner          VARCHAR(255) NOT NULL,
            license_type          VARCHAR(100) NOT NULL,
            attribution           TEXT NOT NULL,
            public_display_allowed BOOLEAN NOT NULL DEFAULT TRUE,
            derivative_allowed    BOOLEAN NOT NULL DEFAULT TRUE,
            historical_entity_id  UUID REFERENCES historical_entities(id) ON DELETE SET NULL,
            relic_slug            VARCHAR(100),
            publication_status    VARCHAR(50) NOT NULL DEFAULT 'draft',
            version               INTEGER NOT NULL DEFAULT 1,
            review_notes          TEXT,
            uploaded_by_id        UUID REFERENCES users(id) ON DELETE SET NULL,
            reviewed_by_id        UUID REFERENCES users(id) ON DELETE SET NULL,
            reviewed_at           TIMESTAMPTZ,
            created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at            TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE INDEX IF NOT EXISTS idx_media_cms_status ON media_cms_items (publication_status);
        CREATE INDEX IF NOT EXISTS idx_media_cms_relic ON media_cms_items (relic_slug);
        CREATE INDEX IF NOT EXISTS idx_media_cms_entity ON media_cms_items (historical_entity_id);
        CREATE INDEX IF NOT EXISTS idx_media_cms_type ON media_cms_items (asset_type);
        CREATE INDEX IF NOT EXISTS idx_media_cms_created ON media_cms_items (created_at DESC);
        ALTER TABLE historical_assets ADD COLUMN IF NOT EXISTS media_cms_item_id UUID REFERENCES media_cms_items(id) ON DELETE SET NULL;
        CREATE INDEX IF NOT EXISTS idx_historical_assets_media_cms ON historical_assets (media_cms_item_id);
        """
    )


def downgrade() -> None:
    # Strictly additive migrations keep downgrade safe / non-destructive
    pass
