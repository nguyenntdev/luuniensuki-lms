"""Add Research Factory publication releases, correction events, and cache purge tables

Revision ID: 0071_research_publication_releases
Revises: 0070_research_factory_core
Create Date: 2026-11-05 21:00:00.000000

V5-T079 / W07-A09: P11 publish, invalidate and revert schema.
Strictly additive:
- Creates research_publication_releases table
- Creates research_correction_events table
- Creates research_cache_purge_events table
- Creates indexes and unique constraints
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID


# revision identifiers, used by Alembic.
revision: str = "0071_research_publication_releases"
down_revision: Union[str, Sequence[str], None] = "0070_research_factory_core"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS research_publication_releases (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            release_code VARCHAR(64) NOT NULL UNIQUE,
            run_id UUID REFERENCES research_runs(id) ON DELETE SET NULL,
            scope VARCHAR(100) NOT NULL DEFAULT 'cuu_dinh_162_motifs',
            status VARCHAR(50) NOT NULL DEFAULT 'PREPARED',
            manifest_sha256 VARCHAR(64) NOT NULL,
            signed_revision VARCHAR(128) NOT NULL,
            signer_identity VARCHAR(255) NOT NULL,
            signer_role VARCHAR(64) NOT NULL DEFAULT 'admin',
            snapshot_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
            previous_release_id UUID REFERENCES research_publication_releases(id) ON DELETE SET NULL,
            published_at TIMESTAMPTZ,
            invalidated_at TIMESTAMPTZ,
            invalidation_reason TEXT,
            rolled_back_at TIMESTAMPTZ,
            rollback_reason TEXT,
            cache_purge_status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
            purged_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE INDEX IF NOT EXISTS idx_research_pub_release_code ON research_publication_releases(release_code);
        CREATE INDEX IF NOT EXISTS idx_research_pub_release_status ON research_publication_releases(status);
        CREATE INDEX IF NOT EXISTS idx_research_pub_release_run ON research_publication_releases(run_id);
        CREATE INDEX IF NOT EXISTS idx_research_pub_release_manifest ON research_publication_releases(manifest_sha256);

        CREATE TABLE IF NOT EXISTS research_correction_events (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            release_id UUID NOT NULL REFERENCES research_publication_releases(id) ON DELETE CASCADE,
            trigger_type VARCHAR(64) NOT NULL,
            source_id UUID REFERENCES historical_sources(id) ON DELETE SET NULL,
            claim_id UUID REFERENCES historical_claims(id) ON DELETE SET NULL,
            story_id UUID REFERENCES history_stories(id) ON DELETE SET NULL,
            entity_slug VARCHAR(255),
            rationale TEXT NOT NULL,
            actor_identity VARCHAR(255) NOT NULL,
            cache_purged BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE INDEX IF NOT EXISTS idx_research_correction_release ON research_correction_events(release_id);
        CREATE INDEX IF NOT EXISTS idx_research_correction_trigger ON research_correction_events(trigger_type);

        CREATE TABLE IF NOT EXISTS research_cache_purge_events (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            release_id UUID NOT NULL REFERENCES research_publication_releases(id) ON DELETE CASCADE,
            cache_key VARCHAR(512) NOT NULL,
            resource_type VARCHAR(64) NOT NULL,
            resource_id VARCHAR(255) NOT NULL,
            purge_status VARCHAR(32) NOT NULL DEFAULT 'PURGED',
            purged_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE INDEX IF NOT EXISTS idx_research_cache_purge_release ON research_cache_purge_events(release_id);
        CREATE INDEX IF NOT EXISTS idx_research_cache_purge_key ON research_cache_purge_events(cache_key);
        """
    )


def downgrade() -> None:
    pass
