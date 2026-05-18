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


def upgrade() -> None:
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
    op.create_index("idx_live_rate_limit_logs_bucket", "live_rate_limit_logs", ["bucket"])
    op.create_index("idx_live_rate_limit_logs_user", "live_rate_limit_logs", ["user_id"])
    op.create_index("idx_live_rate_limit_logs_session", "live_rate_limit_logs", ["live_session_id"])
    op.create_index("idx_live_rate_limit_logs_created_at", "live_rate_limit_logs", ["created_at"])
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
