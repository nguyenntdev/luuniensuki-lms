"""Add AI privacy and child protections columns

Revision ID: 0069_ai_privacy_child_protections
Revises: 0068_ai_observability_budgeting
Create Date: 2026-11-05 19:00:00.000000

V5-T068: AI privacy and child protections.
Strictly additive:
- Adds guardian_consent, guardian_email to users table
- Adds retention_due_at, is_minor, guardian_consent_granted to ai_conversations table
- Adds training_allowed, pii_redacted to ai_messages table
- Adds is_minor, training_allowed, pii_redacted to ai_jobs table
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0069_ai_privacy_child_protections"
down_revision: Union[str, Sequence[str], None] = "0068_ai_observability_budgeting"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE IF EXISTS users
            ADD COLUMN IF NOT EXISTS guardian_consent BOOLEAN NOT NULL DEFAULT FALSE,
            ADD COLUMN IF NOT EXISTS guardian_email VARCHAR(255);

        ALTER TABLE IF EXISTS ai_conversations
            ADD COLUMN IF NOT EXISTS retention_due_at TIMESTAMPTZ,
            ADD COLUMN IF NOT EXISTS is_minor BOOLEAN NOT NULL DEFAULT FALSE,
            ADD COLUMN IF NOT EXISTS guardian_consent_granted BOOLEAN NOT NULL DEFAULT FALSE;

        ALTER TABLE IF EXISTS ai_messages
            ADD COLUMN IF NOT EXISTS training_allowed BOOLEAN NOT NULL DEFAULT FALSE,
            ADD COLUMN IF NOT EXISTS pii_redacted BOOLEAN NOT NULL DEFAULT FALSE;

        ALTER TABLE IF EXISTS ai_jobs
            ADD COLUMN IF NOT EXISTS is_minor BOOLEAN NOT NULL DEFAULT FALSE,
            ADD COLUMN IF NOT EXISTS training_allowed BOOLEAN NOT NULL DEFAULT FALSE,
            ADD COLUMN IF NOT EXISTS pii_redacted BOOLEAN NOT NULL DEFAULT FALSE;

        CREATE INDEX IF NOT EXISTS idx_ai_conversation_retention ON ai_conversations(retention_due_at);
        CREATE INDEX IF NOT EXISTS idx_ai_message_training ON ai_messages(training_allowed);
        """
    )


def downgrade() -> None:
    pass
