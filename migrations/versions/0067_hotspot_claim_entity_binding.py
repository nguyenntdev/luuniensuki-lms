"""Add 3D hotspot coordinates claim and entity binding columns

Revision ID: 0067_hotspot_claim_entity_binding
Revises: 0066_museum_media_cms
Create Date: 2026-11-05 16:00:00.000000

V5-T044: Hotspot and claim binding.
Strictly additive:
- Adds claim_id (UUID references historical_claims(id) on delete set null)
- Adds entity_id (UUID references historical_entities(id) on delete set null)
- Adds asset_revision (INTEGER nullable default null)
- Creates indexes for claim_id and entity_id lookups
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0067_hotspot_claim_entity_binding"
down_revision: Union[str, Sequence[str], None] = "0066_museum_media_cms"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE imperial_media_hotspots
            ADD COLUMN IF NOT EXISTS claim_id UUID REFERENCES historical_claims(id) ON DELETE SET NULL,
            ADD COLUMN IF NOT EXISTS entity_id UUID REFERENCES historical_entities(id) ON DELETE SET NULL,
            ADD COLUMN IF NOT EXISTS asset_revision INTEGER DEFAULT NULL;
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_imperial_media_hotspots_claim ON imperial_media_hotspots(claim_id);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_imperial_media_hotspots_entity ON imperial_media_hotspots(entity_id);")


def downgrade() -> None:
    pass
