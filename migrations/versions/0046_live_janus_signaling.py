"""live janus signaling

Adds Janus WebRTC signaling state for the live virtual-classroom migration
(Rust control/signaling plane + self-hosted Janus VideoRoom media plane).

Binds Janus feed/handle ids onto the existing roster (`live_participants`) and
introduces `live_janus_rooms` mapping each `live_sessions` row to its Janus
VideoRoom (numeric id + server-side secret reference, never the secret value).

All additive — no existing columns modified. Reversible via downgrade.

Revision ID: 0046_live_janus_signaling
Revises: 0045_fsrs_spaced_repetition
Create Date: 2026-05-27
"""
from __future__ import annotations

from alembic import op


revision = "0046_live_janus_signaling"
down_revision = "0045_fsrs_spaced_repetition"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # Bind Janus feed/handle ids onto the existing roster
    # ------------------------------------------------------------------
    op.execute(
        """
        ALTER TABLE live_participants
            ADD COLUMN IF NOT EXISTS janus_feed_id   BIGINT,
            ADD COLUMN IF NOT EXISTS janus_handle_id BIGINT;
        """
    )

    # ------------------------------------------------------------------
    # live_janus_rooms: maps a session to its Janus VideoRoom and holds
    # a reference to the server-side room secret (not the secret value).
    # ------------------------------------------------------------------
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS live_janus_rooms (
            id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            live_session_id   UUID NOT NULL REFERENCES live_sessions(id) ON DELETE CASCADE,
            janus_room_id     BIGINT NOT NULL,
            room_secret_ref   VARCHAR(191) NOT NULL,
            pin_ref           VARCHAR(191),
            media_state       VARCHAR(20) NOT NULL DEFAULT 'provisioned',
            created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE (live_session_id),
            UNIQUE (janus_room_id)
        );
        """
    )

    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_live_janus_rooms_session ON live_janus_rooms(live_session_id)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_live_janus_rooms_session")
    op.execute("DROP TABLE IF EXISTS live_janus_rooms")
    op.execute(
        """
        ALTER TABLE live_participants
            DROP COLUMN IF EXISTS janus_handle_id,
            DROP COLUMN IF EXISTS janus_feed_id;
        """
    )
