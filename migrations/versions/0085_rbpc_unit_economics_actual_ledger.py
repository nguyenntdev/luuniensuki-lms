"""Add revenue_stream to rbpc_settlement_ledger

Revision ID: 0085_rbpc_unit_economics_actual_ledger
Revises: 0084_rbpc_oral_history_consent_studio
Create Date: 2026-11-06 09:00:00.000000

V5-T115 / W11-A05: Unit economics actual ledger.
Cash actuals separated from GMV forecasts, cost structure inference (server, AI tokens, take rate),
and school B2B revenue stream separated from visitor cultural commerce.
Negative abuse invariant: Partner inquiry alone creates 0 VND revenue without verified payment or settled transaction.

Strictly additive:
- Adds revenue_stream column to rbpc_settlement_ledger table with check constraint and index
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0085_rbpc_unit_economics_actual_ledger"
down_revision: Union[str, Sequence[str], None] = "0084_rbpc_oral_history_consent_studio"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        -- 1. Add revenue_stream column to rbpc_settlement_ledger
        ALTER TABLE rbpc_settlement_ledger ADD COLUMN IF NOT EXISTS revenue_stream TEXT NOT NULL DEFAULT 'visitor_commerce';

        -- 2. Add check constraint
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = 'ck_rbpc_settlement_revenue_stream'
            ) THEN
                ALTER TABLE rbpc_settlement_ledger ADD CONSTRAINT ck_rbpc_settlement_revenue_stream
                CHECK (revenue_stream IN ('visitor_commerce', 'school_b2b'));
            END IF;
        END $$;

        -- 3. Create index for revenue_stream
        CREATE INDEX IF NOT EXISTS idx_rbpc_settlement_stream ON rbpc_settlement_ledger(revenue_stream);
        """
    )


def downgrade() -> None:
    # Strictly additive migration discipline
    pass
