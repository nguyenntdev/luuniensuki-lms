"""Add daily missions and user daily mission tracking.

Revision ID: 0012_daily_missions
Revises: 0011_rag_embeddings
Create Date: 2025-01-20
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "0012_daily_missions"
down_revision = "0011_rag_embeddings"
branch_labels = None
depends_on = None


def _table_exists(table_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return table_name in inspector.get_table_names()


def _index_exists(table_name: str, index_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return index_name in {idx["name"] for idx in inspector.get_indexes(table_name)}


def _enum_exists(enum_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    connection = op.get_bind()
    result = connection.execute(
        sa.text(
            "SELECT EXISTS (SELECT 1 FROM pg_type WHERE typname = :enum_name)"
        ),
        {"enum_name": enum_name}
    )
    return result.scalar()


def upgrade() -> None:
    # Create mission_type enum if it doesn't exist
    if not _enum_exists("mission_type"):
        op.execute(
            "CREATE TYPE mission_type AS ENUM ('lesson', 'quiz', 'discovery', 'streak')"
        )

    # Create daily_missions table
    if not _table_exists("daily_missions"):
        op.create_table(
            "daily_missions",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("slug", sa.String(length=100), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("description", sa.Text(), nullable=False),
            sa.Column(
                "mission_type",
                postgresql.ENUM("lesson", "quiz", "discovery", "streak", name="mission_type", create_type=False),
                nullable=False,
            ),
            sa.Column(
                "target_count",
                sa.Integer(),
                server_default=sa.text("1"),
                nullable=False,
            ),
            sa.Column(
                "xp_reward",
                sa.Integer(),
                server_default=sa.text("50"),
                nullable=False,
            ),
            sa.Column(
                "is_active",
                sa.Boolean(),
                server_default=sa.text("true"),
                nullable=False,
            ),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("slug", name="uq_daily_missions_slug"),
        )

    # Create indexes for daily_missions
    if not _index_exists("daily_missions", "idx_daily_missions_slug"):
        op.create_index("idx_daily_missions_slug", "daily_missions", ["slug"])
    if not _index_exists("daily_missions", "idx_daily_missions_type"):
        op.create_index("idx_daily_missions_type", "daily_missions", ["mission_type"])
    if not _index_exists("daily_missions", "idx_daily_missions_active"):
        op.create_index("idx_daily_missions_active", "daily_missions", ["is_active"])

    # Create user_daily_missions table
    if not _table_exists("user_daily_missions"):
        op.create_table(
            "user_daily_missions",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("mission_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("mission_date", sa.DateTime(timezone=False), nullable=False),
            sa.Column(
                "current_count",
                sa.Integer(),
                server_default=sa.text("0"),
                nullable=False,
            ),
            sa.Column(
                "is_completed",
                sa.Boolean(),
                server_default=sa.text("false"),
                nullable=False,
            ),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column(
                "xp_awarded",
                sa.Integer(),
                server_default=sa.text("0"),
                nullable=False,
            ),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["mission_id"], ["daily_missions.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "user_id", "mission_id", "mission_date", name="uq_user_daily_mission"
            ),
        )

    # Create indexes for user_daily_missions
    if not _index_exists("user_daily_missions", "idx_user_daily_missions_user"):
        op.create_index("idx_user_daily_missions_user", "user_daily_missions", ["user_id"])
    if not _index_exists("user_daily_missions", "idx_user_daily_missions_mission"):
        op.create_index("idx_user_daily_missions_mission", "user_daily_missions", ["mission_id"])
    if not _index_exists("user_daily_missions", "idx_user_daily_missions_date"):
        op.create_index("idx_user_daily_missions_date", "user_daily_missions", ["mission_date"])
    if not _index_exists("user_daily_missions", "idx_user_daily_missions_completed"):
        op.create_index("idx_user_daily_missions_completed", "user_daily_missions", ["is_completed"])


def downgrade() -> None:
    # Drop indexes for user_daily_missions
    if _index_exists("user_daily_missions", "idx_user_daily_missions_completed"):
        op.drop_index("idx_user_daily_missions_completed", table_name="user_daily_missions")
    if _index_exists("user_daily_missions", "idx_user_daily_missions_date"):
        op.drop_index("idx_user_daily_missions_date", table_name="user_daily_missions")
    if _index_exists("user_daily_missions", "idx_user_daily_missions_mission"):
        op.drop_index("idx_user_daily_missions_mission", table_name="user_daily_missions")
    if _index_exists("user_daily_missions", "idx_user_daily_missions_user"):
        op.drop_index("idx_user_daily_missions_user", table_name="user_daily_missions")

    # Drop user_daily_missions table
    if _table_exists("user_daily_missions"):
        op.drop_table("user_daily_missions")

    # Drop indexes for daily_missions
    if _index_exists("daily_missions", "idx_daily_missions_active"):
        op.drop_index("idx_daily_missions_active", table_name="daily_missions")
    if _index_exists("daily_missions", "idx_daily_missions_type"):
        op.drop_index("idx_daily_missions_type", table_name="daily_missions")
    if _index_exists("daily_missions", "idx_daily_missions_slug"):
        op.drop_index("idx_daily_missions_slug", table_name="daily_missions")

    # Drop daily_missions table
    if _table_exists("daily_missions"):
        op.drop_table("daily_missions")

    # Drop mission_type enum
    if _enum_exists("mission_type"):
        op.execute("DROP TYPE mission_type")


