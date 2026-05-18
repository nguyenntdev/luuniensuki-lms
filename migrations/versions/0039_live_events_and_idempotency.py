"""Add live_events table and idempotency key for live sessions

Revision ID: 0039
Revises: 0038
Create Date: 2026-04-17

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "0039"
down_revision: Union[str, None] = "0038"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "live_sessions",
        sa.Column("idempotency_key", sa.String(length=128), nullable=True),
    )
    op.create_unique_constraint(
        "uq_live_sessions_idempotency_key",
        "live_sessions",
        ["idempotency_key"],
    )
    op.create_index(
        "idx_live_sessions_idempotency_key",
        "live_sessions",
        ["idempotency_key"],
    )

    op.create_table(
        "live_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("live_session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(length=80), nullable=False),
        sa.Column(
            "event_source",
            sa.String(length=40),
            server_default=sa.text("'app'"),
            nullable=False,
        ),
        sa.Column("participant_identity", sa.String(length=191), nullable=True),
        sa.Column("participant_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "payload",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["live_session_id"],
            ["live_sessions.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["participant_user_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_live_events_session", "live_events", ["live_session_id"])
    op.create_index("idx_live_events_type", "live_events", ["event_type"])
    op.create_index("idx_live_events_created_at", "live_events", ["created_at"])
    op.create_index(
        "idx_live_events_session_created_at",
        "live_events",
        ["live_session_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("idx_live_events_session_created_at", table_name="live_events")
    op.drop_index("idx_live_events_created_at", table_name="live_events")
    op.drop_index("idx_live_events_type", table_name="live_events")
    op.drop_index("idx_live_events_session", table_name="live_events")
    op.drop_table("live_events")

    op.drop_index("idx_live_sessions_idempotency_key", table_name="live_sessions")
    op.drop_constraint(
        "uq_live_sessions_idempotency_key",
        "live_sessions",
        type_="unique",
    )
    op.drop_column("live_sessions", "idempotency_key")
