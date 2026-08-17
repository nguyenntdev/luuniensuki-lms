"""history collections — teacher/editorial historical collections

History-First Phase 11 (docs/specs/HISTORY_FIRST_MASTER_SPEC.md section 47):

Teachers build structured collections from canonical entities/sources/stories/
questions rather than copy-pasting content. A collection references canonical
ids (entities, sources, stories, questions) so it stays connected to the
knowledge graph.

- ``history_collections``: owner + visibility + ordered reference lists.

Additive and reversible.

Revision ID: 0052_history_collections
Revises: 0051_history_stories
Create Date: 2026-08-18
"""
from __future__ import annotations

from alembic import op


revision = "0052_history_collections"
down_revision = "0051_history_stories"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS history_collections (
            id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_id      UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            slug          TEXT NOT NULL,
            title_vi      TEXT NOT NULL,
            title_en      TEXT,
            description_vi TEXT,
            status        TEXT NOT NULL DEFAULT 'draft',
            visibility    TEXT NOT NULL DEFAULT 'private',
            entity_ids    JSONB NOT NULL DEFAULT '[]',
            source_ids    JSONB NOT NULL DEFAULT '[]',
            story_ids     JSONB NOT NULL DEFAULT '[]',
            question_ids  JSONB NOT NULL DEFAULT '[]',
            created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
            published_at  TIMESTAMPTZ
        )
        """
    )
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_history_collections_slug "
        "ON history_collections(slug)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_history_collections_owner "
        "ON history_collections(owner_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_history_collections_visibility "
        "ON history_collections(visibility)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_history_collections_visibility")
    op.execute("DROP INDEX IF EXISTS idx_history_collections_owner")
    op.execute("DROP INDEX IF EXISTS uq_history_collections_slug")
    op.execute("DROP TABLE IF EXISTS history_collections")
