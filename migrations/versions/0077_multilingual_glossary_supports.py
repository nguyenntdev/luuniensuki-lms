"""Add historical_glossary_terms table for multilingual pedagogical glossary and epigraphy

Revision ID: 0077_multilingual_glossary_supports
Revises: 0076_school_pilot_measurement_ethics
Create Date: 2026-11-06 03:00:00.000000

V5-T098 / W09-A08: Multilingual learning supports.
Strictly additive:
- Creates historical_glossary_terms table
- Creates category, review_status, source_id, and origin indexes
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "0077_multilingual_glossary_supports"
down_revision: Union[str, Sequence[str], None] = "0076_school_pilot_measurement_ethics"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS historical_glossary_terms (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            term_key VARCHAR(128) NOT NULL UNIQUE,
            term_vi TEXT NOT NULL,
            term_en TEXT NOT NULL,
            term_han_nom TEXT,
            reading_quoc_ngu TEXT,
            category VARCHAR(64) NOT NULL DEFAULT 'general',
            definition_vi TEXT NOT NULL,
            definition_en TEXT NOT NULL,
            contextual_usage_vi TEXT,
            contextual_usage_en TEXT,
            source_id UUID REFERENCES historical_sources(id) ON DELETE SET NULL,
            citation_locator TEXT,
            bilingual_citation JSONB NOT NULL DEFAULT '{}'::jsonb,
            review_status VARCHAR(64) NOT NULL DEFAULT 'provisional',
            origin VARCHAR(64) NOT NULL DEFAULT 'ai_generated',
            is_machine_translated BOOLEAN NOT NULL DEFAULT FALSE,
            is_uncertain BOOLEAN NOT NULL DEFAULT FALSE,
            uncertainty_label TEXT,
            epigrapher_signoff TEXT,
            translation_provenance JSONB NOT NULL DEFAULT '{}'::jsonb,
            related_entity_slugs JSONB NOT NULL DEFAULT '[]'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE INDEX IF NOT EXISTS idx_hist_glossary_category ON historical_glossary_terms(category);
        CREATE INDEX IF NOT EXISTS idx_hist_glossary_review_status ON historical_glossary_terms(review_status);
        CREATE INDEX IF NOT EXISTS idx_hist_glossary_source_id ON historical_glossary_terms(source_id);
        CREATE INDEX IF NOT EXISTS idx_hist_glossary_origin ON historical_glossary_terms(origin);
        """
    )


def downgrade() -> None:
    # Additive migrations keep downgrade safe / non-destructive
    pass
