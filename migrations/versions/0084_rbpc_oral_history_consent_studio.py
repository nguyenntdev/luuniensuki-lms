"""Add rbpc_oral_history_recordings and rbpc_audio_transcript_versions tables

Revision ID: 0084_rbpc_oral_history_consent_studio
Revises: 0083_rbpc_verified_reviews_disputes
Create Date: 2026-11-06 08:00:00.000000

V5-T109 / W10-A09: Creator oral history consent studio.
Audio transcript and version tracking, per-use media consent, revocation / right to erasure,
and cultural context preservation.
Negative abuse: Revoked audio is immediately unavailable publicly and CDN/local caches are invalidated.

Strictly additive:
- Creates rbpc_oral_history_recordings table with indexes and constraints
- Creates rbpc_audio_transcript_versions table with indexes and constraints
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "0084_rbpc_oral_history_consent_studio"
down_revision: Union[str, Sequence[str], None] = "0083_rbpc_verified_reviews_disputes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        -- 1. Create rbpc_oral_history_recordings table
        CREATE TABLE IF NOT EXISTS rbpc_oral_history_recordings (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            creator_id UUID NOT NULL REFERENCES rbpc_creators(id) ON DELETE CASCADE,
            recording_code TEXT NOT NULL,
            title_vi TEXT NOT NULL,
            title_en TEXT,
            audio_url TEXT,
            audio_sha256 TEXT,
            audio_duration_seconds INTEGER NOT NULL DEFAULT 0,
            mime_type TEXT NOT NULL DEFAULT 'audio/webm',
            cultural_context_vi TEXT NOT NULL,
            cultural_context_en TEXT,
            recording_date DATE,
            recording_location TEXT,
            interviewer_name TEXT,
            epistemic_certainty TEXT NOT NULL DEFAULT 'community_tradition',
            consent_scope TEXT NOT NULL DEFAULT 'preview_only',
            status TEXT NOT NULL DEFAULT 'draft',
            consent_granted BOOLEAN NOT NULL DEFAULT FALSE,
            consent_agreement_ref TEXT,
            consent_granted_at TIMESTAMPTZ,
            consent_notes TEXT,
            revoked_at TIMESTAMPTZ,
            revocation_reason TEXT,
            revoked_by_id UUID REFERENCES users(id) ON DELETE SET NULL,
            erased_at TIMESTAMPTZ,
            current_version_number INTEGER NOT NULL DEFAULT 1,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_rbpc_oral_history_code UNIQUE (creator_id, recording_code),
            CONSTRAINT ck_rbpc_oral_history_consent_scope CHECK (consent_scope IN ('full_public','educational_only','preview_only','revoked')),
            CONSTRAINT ck_rbpc_oral_history_status CHECK (status IN ('draft','submitted','consented','revoked','erased'))
        );

        -- 2. Indexes for rbpc_oral_history_recordings
        CREATE INDEX IF NOT EXISTS idx_rbpc_oral_history_creator ON rbpc_oral_history_recordings(creator_id);
        CREATE INDEX IF NOT EXISTS idx_rbpc_oral_history_status ON rbpc_oral_history_recordings(status);
        CREATE INDEX IF NOT EXISTS idx_rbpc_oral_history_scope ON rbpc_oral_history_recordings(consent_scope);
        CREATE INDEX IF NOT EXISTS idx_rbpc_oral_history_created ON rbpc_oral_history_recordings(created_at);

        -- 3. Create rbpc_audio_transcript_versions table
        CREATE TABLE IF NOT EXISTS rbpc_audio_transcript_versions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            recording_id UUID NOT NULL REFERENCES rbpc_oral_history_recordings(id) ON DELETE CASCADE,
            version_number INTEGER NOT NULL DEFAULT 1,
            transcript_text_vi TEXT NOT NULL,
            transcript_text_en TEXT,
            timed_cues JSONB NOT NULL DEFAULT '[]'::jsonb,
            change_summary TEXT,
            author_id UUID REFERENCES users(id) ON DELETE SET NULL,
            is_verified_by_artisan BOOLEAN NOT NULL DEFAULT FALSE,
            artisan_verified_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_rbpc_audio_version UNIQUE (recording_id, version_number)
        );

        -- 4. Indexes for rbpc_audio_transcript_versions
        CREATE INDEX IF NOT EXISTS idx_rbpc_audio_ver_rec ON rbpc_audio_transcript_versions(recording_id);
        CREATE INDEX IF NOT EXISTS idx_rbpc_audio_ver_created ON rbpc_audio_transcript_versions(created_at);
        """
    )


def downgrade() -> None:
    # Strictly additive per Requirement 6.2 - no destructive drops
    pass
