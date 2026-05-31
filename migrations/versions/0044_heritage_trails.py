"""heritage trails

Adds six tables for the Heritage Trail Mode feature:
- trails
- trail_steps
- trail_checkpoints
- user_trail_progress
- user_trail_checkpoint_responses
- trail_certificates

All additive — no existing tables modified. Reversible via downgrade.

Revision ID: 0044_heritage_trails
Revises: 0043_heritage_time_lapse
Create Date: 2026-05-20
"""
from __future__ import annotations

from alembic import op


revision = "0044_heritage_trails"
down_revision = "0043_heritage_time_lapse"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE trails (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            slug text UNIQUE NOT NULL,
            title_vi text NOT NULL,
            title_en text NOT NULL,
            description_vi text,
            description_en text,
            narrator_intro text,
            narrator_outro text,
            difficulty text NOT NULL DEFAULT 'beginner',
            estimated_minutes integer NOT NULL DEFAULT 30,
            created_by_user_id uuid NOT NULL REFERENCES users(id),
            status text NOT NULL DEFAULT 'draft',
            visibility text NOT NULL DEFAULT 'public',
            classroom_id uuid,
            published_at timestamptz,
            created_at timestamptz NOT NULL DEFAULT NOW(),
            updated_at timestamptz NOT NULL DEFAULT NOW(),
            CONSTRAINT trails_status_check
                CHECK (status IN ('draft','published','pending_review','archived')),
            CONSTRAINT trails_visibility_check
                CHECK (visibility IN ('public','classroom','private'))
        );
        CREATE INDEX idx_trails_status_visibility
            ON trails(status, visibility) WHERE status = 'published';
        CREATE INDEX idx_trails_created_by ON trails(created_by_user_id);
        CREATE INDEX idx_trails_classroom ON trails(classroom_id) WHERE classroom_id IS NOT NULL;
        """
    )

    op.execute(
        """
        CREATE TABLE trail_steps (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            trail_id uuid NOT NULL REFERENCES trails(id) ON DELETE CASCADE,
            motif_id uuid NOT NULL REFERENCES motifs(id),
            position integer NOT NULL,
            created_at timestamptz NOT NULL DEFAULT NOW(),
            UNIQUE (trail_id, position)
        );
        CREATE INDEX idx_trail_steps_trail ON trail_steps(trail_id, position);
        """
    )

    op.execute(
        """
        CREATE TABLE trail_checkpoints (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            trail_id uuid NOT NULL REFERENCES trails(id) ON DELETE CASCADE,
            after_position integer NOT NULL,
            prompt_vi text NOT NULL,
            prompt_en text,
            created_at timestamptz NOT NULL DEFAULT NOW(),
            UNIQUE (trail_id, after_position)
        );
        """
    )

    op.execute(
        """
        CREATE TABLE user_trail_progress (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            trail_id uuid NOT NULL REFERENCES trails(id) ON DELETE CASCADE,
            current_position integer NOT NULL DEFAULT 1,
            pace text DEFAULT 'daily',
            started_at timestamptz NOT NULL DEFAULT NOW(),
            completed_at timestamptz,
            last_activity_at timestamptz NOT NULL DEFAULT NOW(),
            next_reminder_at timestamptz,
            CONSTRAINT pace_check CHECK (pace IN ('daily','2x_week','weekly')),
            UNIQUE (user_id, trail_id)
        );
        CREATE INDEX idx_user_trail_progress_user ON user_trail_progress(user_id);
        CREATE INDEX idx_user_trail_progress_reminder
            ON user_trail_progress(next_reminder_at)
            WHERE completed_at IS NULL AND next_reminder_at IS NOT NULL;
        """
    )

    op.execute(
        """
        CREATE TABLE user_trail_checkpoint_responses (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            checkpoint_id uuid NOT NULL REFERENCES trail_checkpoints(id) ON DELETE CASCADE,
            response_text text NOT NULL,
            created_at timestamptz NOT NULL DEFAULT NOW(),
            UNIQUE (user_id, checkpoint_id)
        );
        """
    )

    op.execute(
        """
        CREATE TABLE trail_certificates (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            trail_id uuid NOT NULL REFERENCES trails(id) ON DELETE CASCADE,
            hash text UNIQUE NOT NULL,
            issued_at timestamptz NOT NULL DEFAULT NOW(),
            pdf_url text,
            notes text,
            UNIQUE (user_id, trail_id)
        );
        CREATE INDEX idx_trail_certificates_hash ON trail_certificates(hash);
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS trail_certificates CASCADE")
    op.execute("DROP TABLE IF EXISTS user_trail_checkpoint_responses CASCADE")
    op.execute("DROP TABLE IF EXISTS user_trail_progress CASCADE")
    op.execute("DROP TABLE IF EXISTS trail_checkpoints CASCADE")
    op.execute("DROP TABLE IF EXISTS trail_steps CASCADE")
    op.execute("DROP TABLE IF EXISTS trails CASCADE")
