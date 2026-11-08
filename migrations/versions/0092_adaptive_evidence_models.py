"""Add adaptive_evidence_cards and adaptive_evidence_logs tables

Revision ID: 0092_adaptive_evidence_models
Revises: 0091_rbpc_pilot_go_no_go_board
Create Date: 2026-11-08 15:30:00.000000

V5-T097 / W09-A07: Adaptive evidence practice using FSRS-5 spaced repetition.
Additive migration aligning SQLAlchemy models with schema.
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "0092_adaptive_evidence_models"
down_revision: Union[str, Sequence[str], None] = "0091_rbpc_pilot_go_no_go_board"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS adaptive_evidence_cards (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            source_id UUID NOT NULL REFERENCES historical_sources(id) ON DELETE CASCADE,
            claim_id UUID REFERENCES historical_claims(id) ON DELETE SET NULL,
            task_type VARCHAR(64) NOT NULL DEFAULT 'source_evaluation',
            prompt TEXT,
            fsrs_state VARCHAR(32) NOT NULL DEFAULT 'new',
            fsrs_difficulty DOUBLE PRECISION NOT NULL DEFAULT 5.0,
            fsrs_stability DOUBLE PRECISION NOT NULL DEFAULT 1.0,
            fsrs_due_date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            fsrs_last_review TIMESTAMPTZ,
            interval_days DOUBLE PRECISION NOT NULL DEFAULT 1.0,
            repetitions INTEGER NOT NULL DEFAULT 0,
            lapses INTEGER NOT NULL DEFAULT 0,
            is_mastered BOOLEAN NOT NULL DEFAULT false,
            mastery_badge_awarded BOOLEAN NOT NULL DEFAULT false,
            review_history JSONB NOT NULL DEFAULT '[]'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );

        CREATE INDEX IF NOT EXISTS idx_aec_user ON adaptive_evidence_cards(user_id);
        CREATE INDEX IF NOT EXISTS idx_aec_source ON adaptive_evidence_cards(source_id);
        CREATE INDEX IF NOT EXISTS idx_aec_due ON adaptive_evidence_cards(fsrs_due_date);
        CREATE INDEX IF NOT EXISTS idx_aec_user_due ON adaptive_evidence_cards(user_id, fsrs_due_date);

        CREATE TABLE IF NOT EXISTS adaptive_evidence_logs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            card_id UUID NOT NULL REFERENCES adaptive_evidence_cards(id) ON DELETE CASCADE,
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            source_id UUID NOT NULL REFERENCES historical_sources(id) ON DELETE CASCADE,
            evaluation_score DOUBLE PRECISION NOT NULL,
            rating VARCHAR(16) NOT NULL,
            dwell_time_seconds DOUBLE PRECISION NOT NULL,
            xp_awarded INTEGER NOT NULL DEFAULT 0,
            stability_before DOUBLE PRECISION NOT NULL,
            stability_after DOUBLE PRECISION NOT NULL,
            difficulty_before DOUBLE PRECISION NOT NULL,
            difficulty_after DOUBLE PRECISION NOT NULL,
            retrievability DOUBLE PRECISION NOT NULL,
            abuse_detected BOOLEAN NOT NULL DEFAULT false,
            abuse_reason VARCHAR(64),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );

        CREATE INDEX IF NOT EXISTS idx_ael_card ON adaptive_evidence_logs(card_id);
        CREATE INDEX IF NOT EXISTS idx_ael_user ON adaptive_evidence_logs(user_id);
        CREATE INDEX IF NOT EXISTS idx_ael_created ON adaptive_evidence_logs(created_at);
        """
    )


def downgrade() -> None:
    pass
