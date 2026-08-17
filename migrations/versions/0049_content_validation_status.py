"""content validation status columns

History-First MIG-005: legacy quiz questions whose answers depend on
unverified (AI-generated) claims must be flagged
``blocked_for_authoritative_learning`` so they do not enter authoritative
learner review until their backing claims are source-verified. Adds:

- ``quiz_questions.content_validation_status`` TEXT NOT NULL DEFAULT 'valid'
- ``lesson_content.content_validation_status`` TEXT NOT NULL DEFAULT 'valid'

Both are additive and reversible.

Revision ID: 0049_content_validation_status
Revises: 0048_history_governance
Create Date: 2026-08-17
"""
from __future__ import annotations

from alembic import op


revision = "0049_content_validation_status"
down_revision = "0048_history_governance"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE quiz_questions
            ADD COLUMN IF NOT EXISTS content_validation_status TEXT NOT NULL DEFAULT 'valid'
        """
    )
    op.execute(
        """
        ALTER TABLE lesson_content
            ADD COLUMN IF NOT EXISTS content_validation_status TEXT NOT NULL DEFAULT 'valid'
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_quiz_questions_content_validation "
        "ON quiz_questions(content_validation_status)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_lesson_content_validation "
        "ON lesson_content(content_validation_status)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_lesson_content_validation")
    op.execute("DROP INDEX IF EXISTS idx_quiz_questions_content_validation")
    op.execute("ALTER TABLE lesson_content DROP COLUMN IF EXISTS content_validation_status")
    op.execute("ALTER TABLE quiz_questions DROP COLUMN IF EXISTS content_validation_status")
