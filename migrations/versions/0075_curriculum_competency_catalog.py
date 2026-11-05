"""Add curriculum competency catalog, relic mappings, and teacher flags

Revision ID: 0074_curriculum_competency_catalog
Revises: 0073_evidence_board_comparative_links
Create Date: 2026-11-06 01:00:00.000000

V5-T095 / W09-A05: Curriculum competency catalog for Vietnam 2018 General Education Program.
Strictly additive:
- Creates curriculum_competencies table and indexes
- Creates curriculum_competency_relic_mappings table and indexes
- Creates curriculum_competency_flags table and indexes
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID


# revision identifiers, used by Alembic.
revision: str = "0075_curriculum_competency_catalog"
down_revision: Union[str, Sequence[str], None] = (
    "0074_heritage_passport_stamps",
    "0073_history_lesson_plans",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS curriculum_competencies (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            code TEXT NOT NULL,
            standard_framework TEXT NOT NULL DEFAULT 'VN_GDPT_2018',
            domain TEXT NOT NULL,
            name_vi TEXT NOT NULL,
            name_en TEXT NOT NULL,
            description_vi TEXT NOT NULL,
            description_en TEXT NOT NULL,
            grade_band_descriptors JSONB NOT NULL DEFAULT '{}'::jsonb,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_curriculum_competencies_code UNIQUE (code)
        );

        CREATE INDEX IF NOT EXISTS idx_curriculum_competency_domain
            ON curriculum_competencies(domain);
        CREATE INDEX IF NOT EXISTS idx_curriculum_competency_framework
            ON curriculum_competencies(standard_framework);

        CREATE TABLE IF NOT EXISTS curriculum_competency_relic_mappings (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            competency_id UUID NOT NULL REFERENCES curriculum_competencies(id) ON DELETE CASCADE,
            relic_urn_slug TEXT,
            relic_motif_id TEXT,
            entity_slug TEXT,
            grade_band TEXT NOT NULL DEFAULT 'GRADE_10_12',
            min_grade INTEGER NOT NULL DEFAULT 6,
            max_grade INTEGER NOT NULL DEFAULT 12,
            learning_activity_vi TEXT NOT NULL,
            learning_activity_en TEXT,
            evidence_requirement_vi TEXT NOT NULL,
            evidence_requirement_en TEXT,
            status TEXT NOT NULL DEFAULT 'unreviewed',
            is_reviewed BOOLEAN NOT NULL DEFAULT FALSE,
            review_warning TEXT DEFAULT 'Cảnh báo: Ánh xạ năng lực chưa được thẩm định chuyên môn bởi giáo viên cốt cán',
            flag_count INTEGER NOT NULL DEFAULT 0,
            created_by_id UUID REFERENCES users(id) ON DELETE SET NULL,
            updated_by_id UUID REFERENCES users(id) ON DELETE SET NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE INDEX IF NOT EXISTS idx_comp_mapping_competency
            ON curriculum_competency_relic_mappings(competency_id);
        CREATE INDEX IF NOT EXISTS idx_comp_mapping_relic_urn
            ON curriculum_competency_relic_mappings(relic_urn_slug);
        CREATE INDEX IF NOT EXISTS idx_comp_mapping_relic_motif
            ON curriculum_competency_relic_mappings(relic_motif_id);
        CREATE INDEX IF NOT EXISTS idx_comp_mapping_status
            ON curriculum_competency_relic_mappings(status);
        CREATE INDEX IF NOT EXISTS idx_comp_mapping_grade_band
            ON curriculum_competency_relic_mappings(grade_band);

        CREATE TABLE IF NOT EXISTS curriculum_competency_flags (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            mapping_id UUID NOT NULL REFERENCES curriculum_competency_relic_mappings(id) ON DELETE CASCADE,
            flagged_by_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            reason TEXT NOT NULL,
            commentary TEXT NOT NULL,
            suggested_correction JSONB,
            status TEXT NOT NULL DEFAULT 'pending',
            resolved_by_id UUID REFERENCES users(id) ON DELETE SET NULL,
            resolution_notes TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            resolved_at TIMESTAMPTZ
        );

        CREATE INDEX IF NOT EXISTS idx_comp_flag_mapping
            ON curriculum_competency_flags(mapping_id);
        CREATE INDEX IF NOT EXISTS idx_comp_flag_teacher
            ON curriculum_competency_flags(flagged_by_id);
        CREATE INDEX IF NOT EXISTS idx_comp_flag_status
            ON curriculum_competency_flags(status);
        """
    )


def downgrade() -> None:
    # Additive-only policy forbids destructive drops in production
    pass
