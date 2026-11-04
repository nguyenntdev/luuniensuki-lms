"""learning outcome measurement scaffold

Revision ID: 0062_learning_outcome_measurement
Revises: 0061_peer_group_historical_inquiry
Create Date: 2026-11-04 00:00:00.000000

V5-T039: Learning outcome measurement scaffold.
Strictly additive: creates ethics protocols, inquiry assessments, submissions,
evaluations, subjective surveys, and causal learning outcome metric tables.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0062_learning_outcome_measurement"
down_revision: Union[str, Sequence[str], None] = "0061_peer_group_historical_inquiry"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Ethics protocols
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS history_ethics_protocols (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            protocol_code TEXT NOT NULL UNIQUE,
            title TEXT NOT NULL,
            irb_institution TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'submitted',
            approved_by TEXT,
            approved_at TIMESTAMPTZ,
            valid_until TIMESTAMPTZ,
            data_retention_days INTEGER NOT NULL DEFAULT 365,
            participant_consent_required BOOLEAN NOT NULL DEFAULT true,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE INDEX IF NOT EXISTS idx_history_ethics_status ON history_ethics_protocols(status);
        """
    )

    # 2. Historical inquiry assessment tasks
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS history_learning_outcome_assessments (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            ethics_protocol_id UUID NOT NULL REFERENCES history_ethics_protocols(id) ON DELETE RESTRICT,
            title TEXT NOT NULL,
            slug TEXT NOT NULL UNIQUE,
            assessment_phase TEXT NOT NULL DEFAULT 'pre_test',
            instrument_type TEXT NOT NULL DEFAULT 'source_inquiry_rubric',
            target_urn_slug TEXT,
            target_motif_slug TEXT,
            prompt_markdown TEXT NOT NULL,
            source_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
            claim_keys JSONB NOT NULL DEFAULT '[]'::jsonb,
            rubric_schema JSONB NOT NULL DEFAULT '{}'::jsonb,
            max_score DOUBLE PRECISION NOT NULL DEFAULT 100.0,
            is_published BOOLEAN NOT NULL DEFAULT true,
            created_by UUID REFERENCES users(id),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE INDEX IF NOT EXISTS idx_hist_lo_assess_phase ON history_learning_outcome_assessments(assessment_phase);
        CREATE INDEX IF NOT EXISTS idx_hist_lo_assess_protocol ON history_learning_outcome_assessments(ethics_protocol_id);
        """
    )

    # 3. Student inquiry submissions
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS history_learning_outcome_submissions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            assessment_id UUID NOT NULL REFERENCES history_learning_outcome_assessments(id) ON DELETE CASCADE,
            student_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            assessment_phase TEXT NOT NULL DEFAULT 'pre_test',
            instrument_type TEXT NOT NULL DEFAULT 'source_inquiry_rubric',
            responses JSONB NOT NULL DEFAULT '{}'::jsonb,
            citations_provided JSONB NOT NULL DEFAULT '[]'::jsonb,
            status TEXT NOT NULL DEFAULT 'submitted',
            submitted_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE INDEX IF NOT EXISTS idx_hist_lo_sub_student_phase ON history_learning_outcome_submissions(student_id, assessment_phase);
        CREATE INDEX IF NOT EXISTS idx_hist_lo_sub_assess ON history_learning_outcome_submissions(assessment_id);
        """
    )

    # 4. Independent assessor rubric evaluations
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS history_learning_outcome_evaluations (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            submission_id UUID NOT NULL REFERENCES history_learning_outcome_submissions(id) ON DELETE CASCADE,
            assessor_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            is_independent BOOLEAN NOT NULL DEFAULT true,
            rubric_scores JSONB NOT NULL DEFAULT '{}'::jsonb,
            total_score DOUBLE PRECISION NOT NULL,
            feedback_markdown TEXT,
            evidence_notes TEXT,
            evaluated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_hist_lo_eval_sub_assessor UNIQUE (submission_id, assessor_id)
        );
        CREATE INDEX IF NOT EXISTS idx_hist_lo_eval_sub ON history_learning_outcome_evaluations(submission_id);
        CREATE INDEX IF NOT EXISTS idx_hist_lo_eval_assessor ON history_learning_outcome_evaluations(assessor_id);
        """
    )

    # 5. Subjective self-report surveys
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS history_subjective_surveys (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            student_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            survey_name TEXT NOT NULL,
            instrument_type TEXT NOT NULL DEFAULT 'self_report_survey',
            is_subjective_self_report BOOLEAN NOT NULL DEFAULT true,
            likert_responses JSONB NOT NULL DEFAULT '{}'::jsonb,
            perceived_learning_score DOUBLE PRECISION,
            satisfaction_score DOUBLE PRECISION,
            feedback_text TEXT,
            submitted_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE INDEX IF NOT EXISTS idx_hist_subj_survey_student ON history_subjective_surveys(student_id);
        """
    )

    # 6. Authoritative causal learning metrics
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS history_causal_learning_metrics (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            student_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            ethics_protocol_id UUID NOT NULL REFERENCES history_ethics_protocols(id) ON DELETE CASCADE,
            pre_submission_id UUID NOT NULL REFERENCES history_learning_outcome_submissions(id),
            post_submission_id UUID NOT NULL REFERENCES history_learning_outcome_submissions(id),
            delayed_submission_id UUID REFERENCES history_learning_outcome_submissions(id),
            pre_score DOUBLE PRECISION NOT NULL,
            post_score DOUBLE PRECISION NOT NULL,
            delayed_score DOUBLE PRECISION,
            normalized_gain DOUBLE PRECISION NOT NULL,
            absolute_gain DOUBLE PRECISION NOT NULL,
            inter_rater_agreement DOUBLE PRECISION,
            competency_gains JSONB NOT NULL DEFAULT '{}'::jsonb,
            instrument_type TEXT NOT NULL DEFAULT 'source_inquiry_rubric',
            is_valid_causal_claim BOOLEAN NOT NULL DEFAULT true,
            computed_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE INDEX IF NOT EXISTS idx_hist_causal_metric_student ON history_causal_learning_metrics(student_id);
        CREATE INDEX IF NOT EXISTS idx_hist_causal_metric_protocol ON history_causal_learning_metrics(ethics_protocol_id);
        """
    )


def downgrade() -> None:
    pass
