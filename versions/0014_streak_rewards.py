"""Add streak rewards table for milestone tracking.

Revision ID: 0014_streak_rewards
Revises: 0013_review_workflow
Create Date: 2025-01-20
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "0014_streak_rewards"
down_revision = "0013_review_workflow"
branch_labels = None
depends_on = None


def _table_exists(table_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return table_name in inspector.get_table_names()


def _index_exists(table_name: str, index_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return index_name in {idx["name"] for idx in inspector.get_indexes(table_name)}


def upgrade() -> None:
    # Create streak_rewards table
    if not _table_exists("streak_rewards"):
        op.create_table(
            "streak_rewards",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("streak_day", sa.Integer(), nullable=False),
            sa.Column("reward_type", sa.String(length=50), nullable=False),
            sa.Column("reward_amount", sa.Integer(), nullable=False, server_default=sa.text("0")),
            sa.Column(
                "awarded_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("now()"),
            ),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("now()"),
            ),
            sa.ForeignKeyConstraint(
                ["user_id"],
                ["users.id"],
                name=op.f("fk_streak_rewards_user_id_users"),
                ondelete="CASCADE",
            ),
            sa.PrimaryKeyConstraint("id", name=op.f("pk_streak_rewards")),
            sa.UniqueConstraint(
                "user_id",
                "streak_day",
                name="uq_streak_rewards_user_streak_day",
            ),
        )

        # Create indexes
        if not _index_exists("streak_rewards", "idx_streak_rewards_user"):
            op.create_index(
                "idx_streak_rewards_user",
                "streak_rewards",
                ["user_id"],
            )

        if not _index_exists("streak_rewards", "idx_streak_rewards_streak_day"):
            op.create_index(
                "idx_streak_rewards_streak_day",
                "streak_rewards",
                ["streak_day"],
            )


def downgrade() -> None:
    # Drop indexes
    if _index_exists("streak_rewards", "idx_streak_rewards_streak_day"):
        op.drop_index("idx_streak_rewards_streak_day", table_name="streak_rewards")

    if _index_exists("streak_rewards", "idx_streak_rewards_user"):
        op.drop_index("idx_streak_rewards_user", table_name="streak_rewards")

    # Drop table
    if _table_exists("streak_rewards"):
        op.drop_table("streak_rewards")

