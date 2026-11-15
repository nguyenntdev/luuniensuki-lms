"""Add persistent logs for live API rate limiting

Revision ID: 0041
Revises: 0040
Create Date: 2026-04-22

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "0041"
down_revision: Union[str, None] = "0040"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(table_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return table_name in inspector.get_table_names()


def _index_exists(table_name: str, index_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    if table_name not in inspector.get_table_names():
        return False
    return index_name in {i["name"] for i in inspector.get_indexes(table_name)}


def upgrade() -> None:
    if not _table_exists("live_rate_limit_logs"):
        op.create_table(
            "live_rate_limit_logs",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("bucket", sa.String(length=64), nullable=False),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("live_session_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["live_session_id"], ["live_sessions.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
    if not _index_exists("live_rate_limit_logs", "idx_live_rate_limit_logs_bucket"):
        op.create_index("idx_live_rate_limit_logs_bucket", "live_rate_limit_logs", ["bucket"])
    if not _index_exists("live_rate_limit_logs", "idx_live_rate_limit_logs_user"):
        op.create_index("idx_live_rate_limit_logs_user", "live_rate_limit_logs", ["user_id"])
    if not _index_exists("live_rate_limit_logs", "idx_live_rate_limit_logs_session"):
        op.create_index("idx_live_rate_limit_logs_session", "live_rate_limit_logs", ["live_session_id"])
    if not _index_exists("live_rate_limit_logs", "idx_live_rate_limit_logs_created_at"):
        op.create_index("idx_live_rate_limit_logs_created_at", "live_rate_limit_logs", ["created_at"])
    if not _index_exists("live_rate_limit_logs", "idx_live_rate_limit_logs_bucket_user_created_at"):
        op.create_index(
            "idx_live_rate_limit_logs_bucket_user_created_at",
            "live_rate_limit_logs",
            ["bucket", "user_id", "created_at"],
        )


def downgrade() -> None:
    op.drop_index(
        "idx_live_rate_limit_logs_bucket_user_created_at",
        table_name="live_rate_limit_logs",
    )
    op.drop_index("idx_live_rate_limit_logs_created_at", table_name="live_rate_limit_logs")
    op.drop_index("idx_live_rate_limit_logs_session", table_name="live_rate_limit_logs")
    op.drop_index("idx_live_rate_limit_logs_user", table_name="live_rate_limit_logs")
    op.drop_index("idx_live_rate_limit_logs_bucket", table_name="live_rate_limit_logs")
    op.drop_table("live_rate_limit_logs")
