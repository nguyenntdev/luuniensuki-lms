"""peer group historical inquiry tables

Revision ID: 0061_peer_group_historical_inquiry
Revises: 0060_history_lesson_assignments
Create Date: 2026-11-04 00:00:00.000000

V5-T038: Peer / group historical inquiry schema extensions.
Strictly additive: creates inquiry activities, groups, members, and submissions.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0061_peer_group_historical_inquiry"
down_revision: Union[str, Sequence[str], None] = "0060_history_lesson_assignments"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Activities
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS historical_inquiry_activities (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            classroom_id UUID REFERENCES classes(id) ON DELETE CASCADE,
            title VARCHAR(255) NOT NULL,
            description TEXT NOT NULL,
            guiding_questions JSONB NOT NULL DEFAULT '[]'::jsonb,
            suggested_source_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
            suggested_claim_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
            rubric_criteria JSONB DEFAULT '{}'::jsonb,
            created_by_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            due_at TIMESTAMPTZ,
            is_active BOOLEAN NOT NULL DEFAULT true,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE INDEX IF NOT EXISTS idx_inquiry_activities_class ON historical_inquiry_activities(classroom_id);
        CREATE INDEX IF NOT EXISTS idx_inquiry_activities_creator ON historical_inquiry_activities(created_by_id);
        CREATE INDEX IF NOT EXISTS idx_inquiry_activities_active ON historical_inquiry_activities(is_active);
        """
    )

    # 2. Groups
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS historical_inquiry_groups (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            activity_id UUID NOT NULL REFERENCES historical_inquiry_activities(id) ON DELETE CASCADE,
            classroom_id UUID REFERENCES classes(id) ON DELETE CASCADE,
            name VARCHAR(255) NOT NULL,
            created_by_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE INDEX IF NOT EXISTS idx_inquiry_groups_activity ON historical_inquiry_groups(activity_id);
        CREATE INDEX IF NOT EXISTS idx_inquiry_groups_classroom ON historical_inquiry_groups(classroom_id);
        """
    )

    # 3. Members
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS historical_inquiry_group_members (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            group_id UUID NOT NULL REFERENCES historical_inquiry_groups(id) ON DELETE CASCADE,
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            role VARCHAR(50) NOT NULL DEFAULT 'contributor',
            joined_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_inquiry_group_members UNIQUE (group_id, user_id)
        );
        CREATE INDEX IF NOT EXISTS idx_inquiry_group_members_group ON historical_inquiry_group_members(group_id);
        CREATE INDEX IF NOT EXISTS idx_inquiry_group_members_user ON historical_inquiry_group_members(user_id);
        """
    )

    # 4. Submissions
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS historical_inquiry_submissions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            group_id UUID NOT NULL REFERENCES historical_inquiry_groups(id) ON DELETE CASCADE,
            activity_id UUID NOT NULL REFERENCES historical_inquiry_activities(id) ON DELETE CASCADE,
            hypothesis TEXT NOT NULL DEFAULT '',
            synthesis_argument TEXT NOT NULL DEFAULT '',
            epistemic_rating VARCHAR(50) NOT NULL DEFAULT 'dang_khao_cuu',
            evidence_items JSONB NOT NULL DEFAULT '[]'::jsonb,
            status VARCHAR(50) NOT NULL DEFAULT 'draft',
            privacy_mode VARCHAR(50) NOT NULL DEFAULT 'private_group',
            submitted_at TIMESTAMPTZ,
            submitted_by_id UUID REFERENCES users(id) ON DELETE SET NULL,
            moderated_by_id UUID REFERENCES users(id) ON DELETE SET NULL,
            moderated_at TIMESTAMPTZ,
            teacher_feedback TEXT,
            score DOUBLE PRECISION,
            rubric_evaluation JSONB DEFAULT '{}'::jsonb,
            version INTEGER NOT NULL DEFAULT 1,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_inquiry_submissions_group UNIQUE (group_id)
        );
        CREATE INDEX IF NOT EXISTS idx_inquiry_submissions_activity ON historical_inquiry_submissions(activity_id);
        CREATE INDEX IF NOT EXISTS idx_inquiry_submissions_status ON historical_inquiry_submissions(status);
        """
    )


def downgrade() -> None:
    # Additive migrations keep downgrade safe / non-destructive
    pass
