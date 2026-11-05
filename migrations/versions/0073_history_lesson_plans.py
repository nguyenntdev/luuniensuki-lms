"""Add history_lesson_plans table for teacher 45-minute lesson wizard

Revision ID: 0073_history_lesson_plans
Revises: 0072_distributed_rate_limiting
Create Date: 2026-11-06 00:00:00.000000

V5-T091 / W09-A01: Teacher 45-minute lesson wizard schema.
Strictly additive:
- Creates history_lesson_plans table
- Creates indexes on teacher_id, status, entity_id, motif_id
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers, used by Alembic.
revision: str = "0073_history_lesson_plans"
down_revision: Union[str, Sequence[str], None] = "0072_distributed_rate_limiting"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS history_lesson_plans (
            id UUID PRIMARY KEY,
            teacher_id UUID REFERENCES users(id) ON DELETE SET NULL,
            title TEXT NOT NULL,
            topic TEXT NOT NULL,
            target_grade TEXT NOT NULL DEFAULT 'Lớp 10 THPT',
            duration_minutes INTEGER NOT NULL DEFAULT 45,
            curriculum_framework TEXT NOT NULL DEFAULT 'CV 5512/BGDĐT',
            status TEXT NOT NULL DEFAULT 'draft',
            content_validation_status TEXT NOT NULL DEFAULT 'valid',
            entity_id UUID REFERENCES historical_entities(id) ON DELETE SET NULL,
            urn_id UUID REFERENCES urns(id) ON DELETE SET NULL,
            motif_id UUID REFERENCES motifs(id) ON DELETE SET NULL,
            lesson_id UUID REFERENCES lesson_content(id) ON DELETE SET NULL,
            media_variant TEXT NOT NULL DEFAULT '2d_rubbing',
            media_config JSONB NOT NULL DEFAULT '{}'::jsonb,
            objectives JSONB NOT NULL DEFAULT '{}'::jsonb,
            source_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
            claim_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
            sources_snapshot JSONB NOT NULL DEFAULT '[]'::jsonb,
            claims_snapshot JSONB NOT NULL DEFAULT '[]'::jsonb,
            inquiry_activities JSONB NOT NULL DEFAULT '[]'::jsonb,
            assessment_rubric JSONB NOT NULL DEFAULT '{}'::jsonb,
            printable_handout JSONB NOT NULL DEFAULT '{}'::jsonb,
            version INTEGER NOT NULL DEFAULT 1,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            published_at TIMESTAMPTZ
        );
        CREATE INDEX IF NOT EXISTS idx_hist_lesson_plans_teacher ON history_lesson_plans(teacher_id);
        CREATE INDEX IF NOT EXISTS idx_hist_lesson_plans_status ON history_lesson_plans(status);
        CREATE INDEX IF NOT EXISTS idx_hist_lesson_plans_entity ON history_lesson_plans(entity_id);
        CREATE INDEX IF NOT EXISTS idx_hist_lesson_plans_motif ON history_lesson_plans(motif_id);
        """
    )


def downgrade() -> None:
    # Additive-only policy forbids destructive drops in production
    pass
