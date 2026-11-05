"""Add teacher_support_tickets and teacher_onboarding_profiles tables, plus school verification flags

Revision ID: 0078_teacher_onboarding_support
Revises: 0077_multilingual_glossary_supports
Create Date: 2026-11-06 04:00:00.000000

V5-T099 / W09-A09: Teacher onboarding, support center, and student PII safety.
Strictly additive:
- Creates teacher_support_tickets table with indexes
- Creates teacher_onboarding_profiles table with indexes
- Adds is_school_verified, teacher_onboarding_completed, teacher_onboarding_step to users
- Adds is_verified, verification_status to school_members
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "0078_teacher_onboarding_support"
down_revision: Union[str, Sequence[str], None] = "0077_multilingual_glossary_supports"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        -- 1. Create teacher_support_tickets table
        CREATE TABLE IF NOT EXISTS teacher_support_tickets (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            teacher_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            school_id UUID REFERENCES schools(id) ON DELETE SET NULL,
            ticket_code VARCHAR(32) NOT NULL UNIQUE,
            subject VARCHAR(255) NOT NULL,
            category VARCHAR(50) NOT NULL,
            priority VARCHAR(20) NOT NULL DEFAULT 'normal',
            status VARCHAR(20) NOT NULL DEFAULT 'open',
            message TEXT NOT NULL,
            admin_response TEXT,
            responses JSONB NOT NULL DEFAULT '[]'::jsonb,
            resolved_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE INDEX IF NOT EXISTS idx_teacher_tickets_teacher ON teacher_support_tickets(teacher_id);
        CREATE INDEX IF NOT EXISTS idx_teacher_tickets_status ON teacher_support_tickets(status);
        CREATE INDEX IF NOT EXISTS idx_teacher_tickets_category ON teacher_support_tickets(category);
        CREATE INDEX IF NOT EXISTS idx_teacher_tickets_code ON teacher_support_tickets(ticket_code);

        -- 2. Create teacher_onboarding_profiles table
        CREATE TABLE IF NOT EXISTS teacher_onboarding_profiles (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            teacher_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
            school_id UUID REFERENCES schools(id) ON DELETE SET NULL,
            is_school_verified BOOLEAN NOT NULL DEFAULT TRUE,
            current_step VARCHAR(50) NOT NULL DEFAULT 'welcome',
            completed_steps JSONB NOT NULL DEFAULT '[]'::jsonb,
            is_completed BOOLEAN NOT NULL DEFAULT FALSE,
            tour_dismissed BOOLEAN NOT NULL DEFAULT FALSE,
            completed_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE INDEX IF NOT EXISTS idx_teacher_onboarding_teacher ON teacher_onboarding_profiles(teacher_id);

        -- 3. Add school verification and onboarding columns to users table
        ALTER TABLE users ADD COLUMN IF NOT EXISTS is_school_verified BOOLEAN NOT NULL DEFAULT TRUE;
        ALTER TABLE users ADD COLUMN IF NOT EXISTS teacher_onboarding_completed BOOLEAN NOT NULL DEFAULT FALSE;
        ALTER TABLE users ADD COLUMN IF NOT EXISTS teacher_onboarding_step VARCHAR(50) DEFAULT 'welcome';

        -- 4. Add verification columns to school_members table
        ALTER TABLE school_members ADD COLUMN IF NOT EXISTS is_verified BOOLEAN NOT NULL DEFAULT TRUE;
        ALTER TABLE school_members ADD COLUMN IF NOT EXISTS verification_status VARCHAR(20) NOT NULL DEFAULT 'verified';
        """
    )


def downgrade() -> None:
    pass
