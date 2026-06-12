"""revoked refresh tokens

Adds a `revoked_refresh_tokens` table backing refresh-token revocation. When a
refresh token is revoked, its `jti` is persisted here so the Auth_Service can
reject subsequent attempts to use that refresh token (Requirement 17.2).

Each row is keyed by the token's `jti` and carries `expires_at` so revoked
entries can be pruned once the underlying token would have expired anyway.

All additive — no existing columns modified. Reversible via downgrade.

Revision ID: 0047_revoked_refresh_tokens
Revises: 0046_live_janus_signaling
Create Date: 2026-06-08
"""
from __future__ import annotations

from alembic import op


revision = "0047_revoked_refresh_tokens"
down_revision = "0046_live_janus_signaling"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS revoked_refresh_tokens (
            jti        VARCHAR(64) PRIMARY KEY,
            user_id    UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            revoked_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            expires_at TIMESTAMPTZ NOT NULL
        );
        """
    )

    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_revoked_refresh_tokens_expires_at "
        "ON revoked_refresh_tokens(expires_at)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_revoked_refresh_tokens_expires_at")
    op.execute("DROP TABLE IF EXISTS revoked_refresh_tokens")
