"""Add research survey batches, item audits, and paper truth audits tables

Revision ID: 0090_research_results_truth_gate
Revises: 0089_rbpc_partner_discovery_loi_vault
Create Date: 2026-11-07 14:00:00.000000

V5-T128 / W12-A08: Research results truth gate.
Synchronize self-report n=1,502 survey methodology description with exact data provenance;
do not invent measured learning gains.
Strictly reproducible paper figure numbers from anonymized survey data and real benchmark runs.

Strictly additive:
- Creates research_survey_batches table with indexes and constraints
- Creates research_survey_item_audits table with indexes and constraints
- Creates research_paper_truth_audits table with indexes and constraints
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0090_research_results_truth_gate"
down_revision: Union[str, Sequence[str], None] = "0089_rbpc_partner_discovery_loi_vault"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        -- 1. Create research_survey_batches table
        CREATE TABLE IF NOT EXISTS research_survey_batches (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            batch_code VARCHAR(64) NOT NULL UNIQUE,
            study_title VARCHAR(255) NOT NULL,
            form_version VARCHAR(64) NOT NULL,
            total_respondents INTEGER NOT NULL,
            school_count INTEGER NOT NULL,
            collection_start DATE,
            collection_end DATE,
            dataset_sha256 VARCHAR(64) NOT NULL,
            ethics_protocol_code VARCHAR(64),
            anonymization_standard VARCHAR(64) NOT NULL DEFAULT 'Decree_13_2023_ND_CP',
            is_verified BOOLEAN NOT NULL DEFAULT true,
            provenance_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );

        CREATE INDEX IF NOT EXISTS idx_research_survey_batch_code
            ON research_survey_batches(batch_code);

        -- 2. Create research_survey_item_audits table
        CREATE TABLE IF NOT EXISTS research_survey_item_audits (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            batch_id UUID NOT NULL REFERENCES research_survey_batches(id) ON DELETE CASCADE,
            item_id VARCHAR(64) NOT NULL,
            table_number VARCHAR(32) NOT NULL,
            original_question_vi TEXT NOT NULL,
            question_text_en TEXT NOT NULL,
            response_type VARCHAR(32) NOT NULL,
            allowed_max_choices INTEGER NOT NULL DEFAULT 1,
            valid_respondents INTEGER NOT NULL,
            missing_count INTEGER NOT NULL DEFAULT 0,
            positive_count INTEGER NOT NULL,
            positive_percentage DOUBLE PRECISION NOT NULL,
            analysis_group VARCHAR(64) NOT NULL,
            is_subjective_self_report BOOLEAN NOT NULL DEFAULT true,
            epistemic_limitation TEXT NOT NULL,
            discrepancy_log JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_research_survey_batch_item UNIQUE(batch_id, item_id)
        );

        CREATE INDEX IF NOT EXISTS idx_research_survey_item_id
            ON research_survey_item_audits(item_id);

        CREATE INDEX IF NOT EXISTS idx_research_survey_item_batch
            ON research_survey_item_audits(batch_id);

        -- 3. Create research_paper_truth_audits table
        CREATE TABLE IF NOT EXISTS research_paper_truth_audits (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            paper_code VARCHAR(64) NOT NULL,
            manuscript_sha256 VARCHAR(64) NOT NULL,
            audit_status VARCHAR(32) NOT NULL,
            claims_checked INTEGER NOT NULL,
            claims_passed INTEGER NOT NULL,
            figures_checked INTEGER NOT NULL,
            figures_passed INTEGER NOT NULL,
            anomaly_a_verified BOOLEAN NOT NULL DEFAULT false,
            anomaly_b_verified BOOLEAN NOT NULL DEFAULT false,
            perf_benchmarks_verified BOOLEAN NOT NULL DEFAULT false,
            audit_details JSONB NOT NULL DEFAULT '{}'::jsonb,
            audited_by VARCHAR(64) NOT NULL,
            audited_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );

        CREATE INDEX IF NOT EXISTS idx_research_paper_truth_audit_paper
            ON research_paper_truth_audits(paper_code);

        CREATE INDEX IF NOT EXISTS idx_research_paper_truth_audit_status
            ON research_paper_truth_audits(audit_status);
        """
    )


def downgrade() -> None:
    pass
