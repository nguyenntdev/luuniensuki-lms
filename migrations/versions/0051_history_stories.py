"""story engine — block-based history stories table

History-First Phase 10 (docs/specs/HISTORY_FIRST_MASTER_SPEC.md section 30):

- Adds ``history_stories``: a story is an ordered list of typed blocks stored
  in a JSONB column (``blocks``), never one giant HTML field (30.1). Each block
  references entities/sources by UUID so the renderer can deep-link into the
  atlas / urns / map / timeline / sources surfaces.

Fields:
  - slug                 unique public path slug
  - title_vi / title_en  bilingual titles (Vietnamese always required)
  - summary_vi / summary_en  bilingual editorial summaries
  - hero_image_url       optional cover image
  - blocks               JSONB list of typed blocks (30.2)
  - status               workflow state (draft -> published); public surface
                         serves only ``published`` rows
  - publication_status   epistemic verification label (default ``unreviewed``)
  - featured             editorial flag for the stories landing list
  - created_by           FK to users(id)
  - published_at         set when the story is published

All additive and reversible.

Revision ID: 0051_history_stories
Revises: 0050_history_questions
Create Date: 2026-08-18
"""
from __future__ import annotations

from alembic import op

revision = "0051_history_stories"
down_revision = "0050_history_questions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS history_stories (
            id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            slug               TEXT NOT NULL,
            title_vi           TEXT NOT NULL,
            title_en           TEXT,
            summary_vi         TEXT,
            summary_en         TEXT,
            hero_image_url     TEXT,
            blocks             JSONB NOT NULL DEFAULT '[]',
            status             TEXT NOT NULL DEFAULT 'draft',
            publication_status TEXT NOT NULL DEFAULT 'unreviewed',
            featured           BOOLEAN NOT NULL DEFAULT false,
            created_by         UUID REFERENCES users(id),
            created_at         TIMESTAMPTZ DEFAULT now(),
            updated_at         TIMESTAMPTZ DEFAULT now(),
            published_at       TIMESTAMPTZ
        )
        """
    )
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_history_stories_slug "
        "ON history_stories(slug)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_history_stories_status "
        "ON history_stories(status)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_history_stories_featured "
        "ON history_stories(featured)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_history_stories_featured")
    op.execute("DROP INDEX IF EXISTS idx_history_stories_status")
    op.execute("DROP INDEX IF EXISTS uq_history_stories_slug")
    op.execute("DROP TABLE IF EXISTS history_stories")