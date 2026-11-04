"""Add schools, school_members, and classroom school/term/guardian fields

Revision ID: 0063_school_teacher_classroom_model
Revises: 0062_learning_outcome_measurement
Create Date: 2026-11-05 00:00:00.000000

V5-T032: School, teacher and classroom model.
Strictly additive: creates schools and school_members tables, adds school_id and term
to classes, adds guardian fields to class_members, and adds school_id to users.
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0063_school_teacher_classroom_model"
down_revision: Union[str, Sequence[str], None] = "0062_learning_outcome_measurement"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create schools table
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS schools (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR(255) NOT NULL,
            code VARCHAR(50) UNIQUE,
            address TEXT,
            city VARCHAR(100),
            region VARCHAR(100),
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            settings JSONB,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_schools_code ON schools (code);
        CREATE INDEX IF NOT EXISTS idx_schools_name ON schools (name);
        CREATE INDEX IF NOT EXISTS idx_schools_city ON schools (city);
        """
    )

    # 2. Create school_members table
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS school_members (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            role VARCHAR(20) NOT NULL DEFAULT 'teacher',
            joined_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_school_members UNIQUE (school_id, user_id)
        );
        CREATE INDEX IF NOT EXISTS idx_school_members_school ON school_members (school_id);
        CREATE INDEX IF NOT EXISTS idx_school_members_user ON school_members (user_id);
        """
    )

    # 3. Add school_id and term to classes table
    op.execute(
        """
        ALTER TABLE classes ADD COLUMN IF NOT EXISTS school_id UUID REFERENCES schools(id) ON DELETE SET NULL;
        ALTER TABLE classes ADD COLUMN IF NOT EXISTS term VARCHAR(50);
        CREATE INDEX IF NOT EXISTS idx_classes_school ON classes (school_id);
        """
    )

    # 4. Add guardian fields to class_members table
    op.execute(
        """
        ALTER TABLE class_members ADD COLUMN IF NOT EXISTS guardian_user_id UUID REFERENCES users(id) ON DELETE SET NULL;
        ALTER TABLE class_members ADD COLUMN IF NOT EXISTS guardian_email VARCHAR(255);
        ALTER TABLE class_members ADD COLUMN IF NOT EXISTS guardian_consent BOOLEAN NOT NULL DEFAULT FALSE;
        CREATE INDEX IF NOT EXISTS idx_class_members_guardian ON class_members (guardian_user_id);
        """
    )

    # 5. Add school_id to users table
    op.execute(
        """
        ALTER TABLE users ADD COLUMN IF NOT EXISTS school_id UUID REFERENCES schools(id) ON DELETE SET NULL;
        CREATE INDEX IF NOT EXISTS idx_users_school ON users (school_id);
        """
    )


def downgrade() -> None:
    # Strictly additive migrations keep downgrade safe / non-destructive
    pass
