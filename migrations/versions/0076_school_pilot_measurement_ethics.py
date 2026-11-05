"""School pilot measurement and ethics protocol tables

Revision ID: 0076_school_pilot_measurement_ethics
Revises: 0075_curriculum_competency_catalog
Create Date: 2026-11-06 02:00:00.000000

V5-T100 / W09-A10: School pilot measurement & ethics protocol.
Strictly additive:
- Creates history_pilot_guardian_consents table
- Creates history_teacher_workload_logs table
- Creates history_rubric_calibrations table
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "0076_school_pilot_measurement_ethics"
down_revision: Union[str, Sequence[str], None] = "0075_curriculum_competency_catalog"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS history_pilot_guardian_consents (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            ethics_protocol_id UUID NOT NULL REFERENCES history_ethics_protocols(id) ON DELETE CASCADE,
            student_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            guardian_name TEXT NOT NULL,
            guardian_email TEXT NOT NULL,
            guardian_phone TEXT,
            relationship_type TEXT NOT NULL DEFAULT 'parent',
            consent_status TEXT NOT NULL DEFAULT 'pending',
            verification_method TEXT NOT NULL DEFAULT 'school_roster',
            verified_by_id UUID REFERENCES users(id) ON DELETE SET NULL,
            notes TEXT,
            verified_at TIMESTAMPTZ,
            withdrawn_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_pilot_consent_protocol_student UNIQUE (ethics_protocol_id, student_id)
        );
        CREATE INDEX IF NOT EXISTS idx_pilot_consent_protocol ON history_pilot_guardian_consents(ethics_protocol_id);
        CREATE INDEX IF NOT EXISTS idx_pilot_consent_student ON history_pilot_guardian_consents(student_id);
        CREATE INDEX IF NOT EXISTS idx_pilot_consent_status ON history_pilot_guardian_consents(consent_status);

        CREATE TABLE IF NOT EXISTS history_teacher_workload_logs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            teacher_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            school_id UUID REFERENCES schools(id) ON DELETE SET NULL,
            classroom_id UUID REFERENCES classrooms(id) ON DELETE SET NULL,
            ethics_protocol_id UUID REFERENCES history_ethics_protocols(id) ON DELETE SET NULL,
            activity_type TEXT NOT NULL DEFAULT 'rubric_grading',
            minutes_spent FLOAT NOT NULL,
            submissions_evaluated_count INTEGER NOT NULL DEFAULT 0,
            cognitive_load_rating FLOAT NOT NULL DEFAULT 50.0,
            workload_category TEXT NOT NULL DEFAULT 'acceptable',
            notes TEXT,
            logged_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE INDEX IF NOT EXISTS idx_hist_tw_teacher ON history_teacher_workload_logs(teacher_id);
        CREATE INDEX IF NOT EXISTS idx_hist_tw_protocol ON history_teacher_workload_logs(ethics_protocol_id);
        CREATE INDEX IF NOT EXISTS idx_hist_tw_activity ON history_teacher_workload_logs(activity_type);

        CREATE TABLE IF NOT EXISTS history_rubric_calibrations (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            submission_id UUID NOT NULL REFERENCES history_learning_outcome_submissions(id) ON DELETE CASCADE,
            assessor_a_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            assessor_b_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            evaluation_a_id UUID REFERENCES history_learning_outcome_evaluations(id) ON DELETE SET NULL,
            evaluation_b_id UUID REFERENCES history_learning_outcome_evaluations(id) ON DELETE SET NULL,
            score_a FLOAT NOT NULL,
            score_b FLOAT NOT NULL,
            score_difference FLOAT NOT NULL,
            divergence_pct FLOAT NOT NULL,
            inter_rater_agreement FLOAT NOT NULL,
            tolerance_pct FLOAT NOT NULL DEFAULT 0.15,
            status TEXT NOT NULL DEFAULT 'calibrated',
            consensus_score FLOAT,
            criteria_breakdown JSONB NOT NULL DEFAULT '{}'::jsonb,
            calibrated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE INDEX IF NOT EXISTS idx_hist_rc_submission ON history_rubric_calibrations(submission_id);
        CREATE INDEX IF NOT EXISTS idx_hist_rc_status ON history_rubric_calibrations(status);
        """
    )


def downgrade() -> None:
    # Additive migrations keep downgrade safe / non-destructive
    pass
