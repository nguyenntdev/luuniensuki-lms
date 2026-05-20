"""fsrs spaced repetition

Adds FSRS (Free Spaced Repetition Scheduler) state to spaced_repetition_cards
and creates supporting tables for per-user parameter tuning and cohort
defaults.

The original spec (`.kiro/specs/fsrs-spaced-repetition/`) targeted a hypothetical
`user_quiz_review_state` table; the actual schema uses `spaced_repetition_cards`
keyed by `(user_id, motif_id)`. This migration adapts to the existing schema.

All additive — no existing columns modified. Reversible via downgrade.

Revision ID: 0045_fsrs_spaced_repetition
Revises: 0044_heritage_trails
Create Date: 2026-05-20
"""
from __future__ import annotations

from alembic import op


revision = "0045_fsrs_spaced_repetition"
down_revision = "0044_heritage_trails"
branch_labels = None
depends_on = None


# Default FSRS parameters from open-spaced-repetition (rs-fsrs / fsrs4anki).
DEFAULT_W = (
    "0.4072,1.1829,3.1262,15.4722,7.2102,0.5316,1.0651,0.0589,1.5747,0.1070,"
    "1.0070,1.9523,0.1110,0.3255,2.2698,0.2315,2.9898,0.5163,0.6136,0.0000,0.0000"
)


def upgrade() -> None:
    # ------------------------------------------------------------------
    # Extend spaced_repetition_cards with FSRS columns
    # ------------------------------------------------------------------
    op.execute(
        """
        ALTER TABLE spaced_repetition_cards
            ADD COLUMN IF NOT EXISTS fsrs_state           text DEFAULT 'new',
            ADD COLUMN IF NOT EXISTS fsrs_difficulty      double precision,
            ADD COLUMN IF NOT EXISTS fsrs_stability       double precision,
            ADD COLUMN IF NOT EXISTS fsrs_due_date        timestamptz,
            ADD COLUMN IF NOT EXISTS fsrs_last_review     timestamptz;
        """
    )

    # Backfill: seed every existing card with sensible FSRS defaults.
    op.execute(
        """
        UPDATE spaced_repetition_cards
        SET fsrs_state      = COALESCE(fsrs_state, 'review'),
            fsrs_difficulty = COALESCE(fsrs_difficulty, 5.0),
            fsrs_stability  = COALESCE(fsrs_stability,
                                       GREATEST(interval_days, 1)::double precision),
            fsrs_due_date   = COALESCE(fsrs_due_date, next_review_at)
        WHERE fsrs_state IS NULL OR fsrs_difficulty IS NULL
           OR fsrs_stability IS NULL OR fsrs_due_date IS NULL;
        """
    )

    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_sr_cards_fsrs_due_date ON spaced_repetition_cards(fsrs_due_date)"
    )

    # ------------------------------------------------------------------
    # user_fsrs_params: per-user weights + retention slider
    # ------------------------------------------------------------------
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS user_fsrs_params (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id uuid NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
            parameters double precision[] NOT NULL DEFAULT '{}',
            optimal_retention double precision NOT NULL DEFAULT 0.9,
            last_optimized_at timestamptz,
            review_count_at_last_optimize integer NOT NULL DEFAULT 0,
            created_at timestamptz NOT NULL DEFAULT NOW(),
            updated_at timestamptz NOT NULL DEFAULT NOW(),
            CONSTRAINT user_fsrs_params_retention_range
                CHECK (optimal_retention BETWEEN 0.70 AND 0.97)
        );
        CREATE INDEX idx_user_fsrs_params_user ON user_fsrs_params(user_id);
        """
    )

    # ------------------------------------------------------------------
    # fsrs_cohort_params: defaults shared by all users
    # ------------------------------------------------------------------
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS fsrs_cohort_params (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            cohort_name text NOT NULL UNIQUE DEFAULT 'default',
            parameters double precision[] NOT NULL,
            optimal_retention double precision NOT NULL DEFAULT 0.9,
            updated_at timestamptz NOT NULL DEFAULT NOW()
        );
        """
    )

    # Seed defaults
    op.execute(
        f"""
        INSERT INTO fsrs_cohort_params (cohort_name, parameters)
        VALUES ('default', ARRAY[{DEFAULT_W}]::double precision[])
        ON CONFLICT (cohort_name) DO NOTHING;
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS user_fsrs_params CASCADE")
    op.execute("DROP TABLE IF EXISTS fsrs_cohort_params CASCADE")
    op.execute("DROP INDEX IF EXISTS idx_sr_cards_fsrs_due_date")
    op.execute(
        """
        ALTER TABLE spaced_repetition_cards
            DROP COLUMN IF EXISTS fsrs_state,
            DROP COLUMN IF EXISTS fsrs_difficulty,
            DROP COLUMN IF EXISTS fsrs_stability,
            DROP COLUMN IF EXISTS fsrs_due_date,
            DROP COLUMN IF EXISTS fsrs_last_review;
        """
    )
