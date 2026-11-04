"""add checksum and excerpt to historical_sources

Revision ID: 0059_historical_sources_registry
Revises: 0058_rbpc_notification_outbox_sla
Create Date: 2026-10-22 00:00:00.000000

V5-T023: Bibliographic source registry extensions.
Strictly additive: adds checksum and excerpt columns to historical_sources.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0059_historical_sources_registry"
down_revision: Union[str, Sequence[str], None] = "0058_rbpc_notification_outbox_sla"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE historical_sources ADD COLUMN IF NOT EXISTS checksum TEXT;")
    op.execute("ALTER TABLE historical_sources ADD COLUMN IF NOT EXISTS excerpt TEXT;")


def downgrade() -> None:
    # Additive migrations keep downgrade safe / non-destructive
    pass
