"""add history_lesson_assignments and history_assignment_submissions tables

Revision ID: 0060_history_lesson_assignments
Revises: 0059_historical_sources_registry
Create Date: 2026-11-04 00:00:00.000000

V5-T033: Assignment and source-locked lessons.
Strictly additive: creates history_lesson_assignments and history_assignment_submissions tables.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0060_history_lesson_assignments"
down_revision: Union[str, Sequence[str], None] = "0059_historical_sources_registry"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
    CREATE TABLE IF NOT EXISTS history_lesson_assignments (
        id UUID PRIMARY KEY,
        classroom_id UUID NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
        lesson_id UUID NOT NULL REFERENCES lesson_content(id) ON DELETE CASCADE,
        assigned_by_id UUID REFERENCES users(id) ON DELETE SET NULL,
        title TEXT NOT NULL,
        instructions TEXT,
        status TEXT NOT NULL DEFAULT 'draft',
        due_at TIMESTAMPTZ,
        points INTEGER NOT NULL DEFAULT 100,
        pinned_version INTEGER NOT NULL DEFAULT 1,
        pinned_lesson_snapshot JSONB NOT NULL DEFAULT '{}'::jsonb,
        rubric JSONB NOT NULL DEFAULT '{}'::jsonb,
        pinned_source_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
        pinned_sources_snapshot JSONB NOT NULL DEFAULT '[]'::jsonb,
        pinned_claim_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        published_at TIMESTAMPTZ
    );
    CREATE INDEX IF NOT EXISTS idx_hist_assignments_class ON history_lesson_assignments(classroom_id);
    CREATE INDEX IF NOT EXISTS idx_hist_assignments_lesson ON history_lesson_assignments(lesson_id);
    CREATE INDEX IF NOT EXISTS idx_hist_assignments_teacher ON history_lesson_assignments(assigned_by_id);
    CREATE INDEX IF NOT EXISTS idx_hist_assignments_status ON history_lesson_assignments(status);

    CREATE TABLE IF NOT EXISTS history_assignment_submissions (
        id UUID PRIMARY KEY,
        assignment_id UUID NOT NULL REFERENCES history_lesson_assignments(id) ON DELETE CASCADE,
        student_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        status TEXT NOT NULL DEFAULT 'submitted',
        submission_content JSONB NOT NULL DEFAULT '{}'::jsonb,
        assessment_basis_snapshot JSONB NOT NULL DEFAULT '{}'::jsonb,
        idempotency_key TEXT,
        score DOUBLE PRECISION,
        rubric_evaluation JSONB,
        teacher_feedback TEXT,
        submitted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        graded_at TIMESTAMPTZ,
        graded_by_id UUID REFERENCES users(id) ON DELETE SET NULL,
        CONSTRAINT uq_hist_assignment_student UNIQUE (assignment_id, student_id)
    );
    ALTER TABLE history_assignment_submissions ADD COLUMN IF NOT EXISTS idempotency_key TEXT;
    CREATE INDEX IF NOT EXISTS idx_hist_submissions_assignment ON history_assignment_submissions(assignment_id);
    CREATE INDEX IF NOT EXISTS idx_hist_submissions_student ON history_assignment_submissions(student_id);
    CREATE INDEX IF NOT EXISTS idx_hist_submissions_status ON history_assignment_submissions(status);
    CREATE INDEX IF NOT EXISTS idx_hist_submissions_idempotency ON history_assignment_submissions(idempotency_key);
    """)


def downgrade() -> None:
    # Additive migrations keep downgrade safe / non-destructive
    pass
