"""Add comparative links, inline feedback, revision cycle and history to inquiry submissions

Revision ID: 0073_evidence_board_comparative_links
Revises: 0072_distributed_rate_limiting
Create Date: 2026-11-06 00:00:00.000000

V5-T093 / W09-A03: Evidence board for collaborative inquiry groups.
Strictly additive:
- Adds comparative_links (JSONB) to historical_inquiry_submissions
- Adds inline_feedback (JSONB) to historical_inquiry_submissions
- Adds revision_cycle (INTEGER) to historical_inquiry_submissions
- Adds revision_history (JSONB) to historical_inquiry_submissions
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "0073_evidence_board_comparative_links"
down_revision: Union[str, Sequence[str], None] = "0072_distributed_rate_limiting"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE historical_inquiry_submissions
            ADD COLUMN IF NOT EXISTS comparative_links JSONB NOT NULL DEFAULT '[]'::jsonb,
            ADD COLUMN IF NOT EXISTS inline_feedback JSONB NOT NULL DEFAULT '[]'::jsonb,
            ADD COLUMN IF NOT EXISTS revision_cycle INTEGER NOT NULL DEFAULT 1,
            ADD COLUMN IF NOT EXISTS revision_history JSONB NOT NULL DEFAULT '[]'::jsonb;
        """
    )


def downgrade() -> None:
    # Additive migrations keep downgrade safe / non-destructive
    pass
