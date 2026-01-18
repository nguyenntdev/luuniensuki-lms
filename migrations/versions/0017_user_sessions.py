"""Add user sessions table for real-time session tracking.

Revision ID: 0017_user_sessions
Revises: 0016_audit_logs
Create Date: 2025-01-17
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0017_user_sessions"
down_revision = "0016_audit_logs"
branch_labels = None
depends_on = None


def _table_exists(table_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return table_name in inspector.get_table_names()


def _index_exists(table_name: str, index_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    if not _table_exists(table_name):
        return False
    return index_name in {idx["name"] for idx in inspector.get_indexes(table_name)}


def upgrade() -> None:
    # Create user_sessions table
    if not _table_exists("user_sessions"):
        op.create_table(
            "user_sessions",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column(
                "user_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                nullable=True,
            ),
            sa.Column(
                "session_id", postgresql.UUID(as_uuid=True), nullable=False, unique=True
            ),
            sa.Column(
                "started_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.Column(
                "last_active_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("device_type", sa.String(length=20), nullable=False),
            sa.Column("platform", sa.String(length=20), nullable=False),
            sa.Column("app_version", sa.String(length=20), nullable=True),
            sa.Column(
                "is_active",
                sa.Boolean,
                nullable=False,
                server_default=sa.text("true"),
            ),
        )

    # Create indexes
    if not _index_exists("user_sessions", "idx_user_sessions_user_id"):
        op.create_index(
            "idx_user_sessions_user_id", "user_sessions", ["user_id"]
        )

    if not _index_exists("user_sessions", "idx_user_sessions_session_id"):
        op.create_index(
            "idx_user_sessions_session_id", "user_sessions", ["session_id"]
        )

    if not _index_exists("user_sessions", "idx_user_sessions_is_active"):
        op.create_index(
            "idx_user_sessions_is_active", "user_sessions", ["is_active"]
        )

    if not _index_exists("user_sessions", "idx_user_sessions_last_active"):
        op.create_index(
            "idx_user_sessions_last_active", "user_sessions", ["last_active_at"]
        )

    if not _index_exists("user_sessions", "idx_user_sessions_started_at"):
        op.create_index(
            "idx_user_sessions_started_at", "user_sessions", ["started_at"]
        )


def downgrade() -> None:
    # Drop indexes
    if _index_exists("user_sessions", "idx_user_sessions_started_at"):
        op.drop_index("idx_user_sessions_started_at", table_name="user_sessions")

    if _index_exists("user_sessions", "idx_user_sessions_last_active"):
        op.drop_index("idx_user_sessions_last_active", table_name="user_sessions")

    if _index_exists("user_sessions", "idx_user_sessions_is_active"):
        op.drop_index("idx_user_sessions_is_active", table_name="user_sessions")

    if _index_exists("user_sessions", "idx_user_sessions_session_id"):
        op.drop_index("idx_user_sessions_session_id", table_name="user_sessions")

    if _index_exists("user_sessions", "idx_user_sessions_user_id"):
        op.drop_index("idx_user_sessions_user_id", table_name="user_sessions")

    # Drop table
    if _table_exists("user_sessions"):
        op.drop_table("user_sessions")

