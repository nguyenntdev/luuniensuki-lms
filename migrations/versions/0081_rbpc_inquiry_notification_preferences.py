"""Add notification preferences and partner response escalation columns to rbpc_inquiries

Revision ID: 0082_rbpc_inquiry_notification_preferences
Revises: 0081_rbpc_verified_reviews_disputes
Create Date: 2026-11-06 07:00:00.000000

V5-T103 / W10-A03: Inquiry customer notification center.
Real tracking status updates, email/SMS opt-in preferences, partner late response escalation, and unsubscribe capabilities.
Negative abuse: Network or provider error never shows or sends fake confirmed status.

Strictly additive:
- Adds email_opt_in, sms_opt_in, notification_preferences to rbpc_inquiries
- Adds escalated_at, escalation_reason, escalation_count to rbpc_inquiries
- Creates associated indexes
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "0081_rbpc_inquiry_notification_preferences"
down_revision: Union[str, Sequence[str], None] = "0079_rbpc_fee_revenue_ledger"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        -- Add opt-in and preferences columns to rbpc_inquiries
        ALTER TABLE rbpc_inquiries
            ADD COLUMN IF NOT EXISTS email_opt_in BOOLEAN NOT NULL DEFAULT TRUE,
            ADD COLUMN IF NOT EXISTS sms_opt_in BOOLEAN NOT NULL DEFAULT FALSE,
            ADD COLUMN IF NOT EXISTS notification_preferences JSONB NOT NULL DEFAULT '{}'::jsonb,
            ADD COLUMN IF NOT EXISTS escalated_at TIMESTAMPTZ,
            ADD COLUMN IF NOT EXISTS escalation_reason TEXT,
            ADD COLUMN IF NOT EXISTS escalation_count INTEGER NOT NULL DEFAULT 0;

        CREATE INDEX IF NOT EXISTS idx_rbpc_inquiries_escalated ON rbpc_inquiries(escalated_at) WHERE escalated_at IS NOT NULL;
        CREATE INDEX IF NOT EXISTS idx_rbpc_inquiries_optin ON rbpc_inquiries(email_opt_in, sms_opt_in);
        """
    )


def downgrade() -> None:
    # Downgrade operations are omitted in production forward-only migration policy
    pass
