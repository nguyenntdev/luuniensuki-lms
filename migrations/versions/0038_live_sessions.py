"""Add live session and live participant tables

Revision ID: 0038
Revises: 0037
Create Date: 2026-04-17

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "0038"
down_revision: Union[str, None] = "0037"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "live_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("classroom_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("room_name", sa.String(length=191), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column(
            "status",
            sa.String(length=20),
            server_default=sa.text("'scheduled'"),
            nullable=False,
        ),
        sa.Column(
            "starts_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "session_metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["classroom_id"], ["classes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("room_name", name="uq_live_sessions_room_name"),
    )
    op.create_index("idx_live_sessions_classroom", "live_sessions", ["classroom_id"])
    op.create_index("idx_live_sessions_status", "live_sessions", ["status"])
    op.create_index("idx_live_sessions_starts_at", "live_sessions", ["starts_at"])
    op.create_index("idx_live_sessions_created_at", "live_sessions", ["created_at"])
    op.create_index("idx_live_sessions_room_name", "live_sessions", ["room_name"])

    op.create_table(
        "live_participants",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("live_session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("participant_identity", sa.String(length=191), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column(
            "role",
            sa.String(length=20),
            server_default=sa.text("'learner'"),
            nullable=False,
        ),
        sa.Column(
            "is_ai",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "joined_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("left_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "connection_metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["live_session_id"],
            ["live_sessions.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "live_session_id",
            "participant_identity",
            name="uq_live_participants_session_identity",
        ),
        sa.UniqueConstraint(
            "live_session_id",
            "user_id",
            name="uq_live_participants_session_user",
        ),
    )
    op.create_index(
        "idx_live_participants_session", "live_participants", ["live_session_id"]
    )
    op.create_index("idx_live_participants_user", "live_participants", ["user_id"])
    op.create_index(
        "idx_live_participants_joined_at", "live_participants", ["joined_at"]
    )


def downgrade() -> None:
    op.drop_index("idx_live_participants_joined_at", table_name="live_participants")
    op.drop_index("idx_live_participants_user", table_name="live_participants")
    op.drop_index("idx_live_participants_session", table_name="live_participants")
    op.drop_table("live_participants")

    op.drop_index("idx_live_sessions_room_name", table_name="live_sessions")
    op.drop_index("idx_live_sessions_created_at", table_name="live_sessions")
    op.drop_index("idx_live_sessions_starts_at", table_name="live_sessions")
    op.drop_index("idx_live_sessions_status", table_name="live_sessions")
    op.drop_index("idx_live_sessions_classroom", table_name="live_sessions")
    op.drop_table("live_sessions")
