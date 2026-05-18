from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# Timestamp: 2025-12-29 10:15:00
revision = "0007_quests"
down_revision = "0006_certificates"
branch_labels = None
depends_on = None


def _table_exists(table_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return table_name in inspector.get_table_names()


def _column_exists(table_name: str, column_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return column_name in {col["name"] for col in inspector.get_columns(table_name)}


def _index_exists(table_name: str, index_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return index_name in {idx["name"] for idx in inspector.get_indexes(table_name)}


def _constraint_exists(table_name: str, constraint_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return constraint_name in {c["name"] for c in inspector.get_unique_constraints(table_name)}


def _foreign_key_exists(table_name: str, fk_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return fk_name in {fk["name"] for fk in inspector.get_foreign_keys(table_name)}


def upgrade() -> None:
    if not _table_exists("quests"):
        op.create_table(
            "quests",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("slug", sa.String(length=100), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("category", sa.String(length=50), nullable=True),
            sa.Column(
                "display_order",
                sa.Integer(),
                server_default=sa.text("0"),
                nullable=False,
            ),
            sa.Column(
                "is_active",
                sa.Boolean(),
                server_default=sa.text("true"),
                nullable=False,
            ),
            sa.Column("prerequisite_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("slug", name="uq_quests_slug"),
        )
    if not _foreign_key_exists("quests", "fk_quests_prerequisite_id"):
        op.create_foreign_key(
            "fk_quests_prerequisite_id",
            "quests",
            "quests",
            ["prerequisite_id"],
            ["id"],
            ondelete="SET NULL",
        )

    if not _index_exists("quests", "idx_quests_slug"):
        op.create_index("idx_quests_slug", "quests", ["slug"])
    if not _index_exists("quests", "idx_quests_active"):
        op.create_index("idx_quests_active", "quests", ["is_active"])
    if not _index_exists("quests", "idx_quests_order"):
        op.create_index("idx_quests_order", "quests", ["display_order"])

    if not _table_exists("quest_steps"):
        op.create_table(
            "quest_steps",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("quest_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("title", sa.String(length=255), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column(
                "display_order",
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
            sa.ForeignKeyConstraint(["quest_id"], ["quests.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
    if not _index_exists("quest_steps", "idx_quest_steps_quest"):
        op.create_index("idx_quest_steps_quest", "quest_steps", ["quest_id"])
    if not _index_exists("quest_steps", "idx_quest_steps_order"):
        op.create_index("idx_quest_steps_order", "quest_steps", ["display_order"])

    if not _table_exists("quest_objectives"):
        op.create_table(
            "quest_objectives",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("quest_step_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("objective_type", sa.String(length=50), nullable=False),
            sa.Column(
                "target_value",
                sa.Integer(),
                server_default=sa.text("1"),
                nullable=False,
            ),
            sa.Column("params", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column(
                "display_order",
                sa.Integer(),
                server_default=sa.text("0"),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(
                ["quest_step_id"], ["quest_steps.id"], ondelete="CASCADE"
            ),
            sa.PrimaryKeyConstraint("id"),
        )
    if not _index_exists("quest_objectives", "idx_quest_objectives_step"):
        op.create_index(
            "idx_quest_objectives_step", "quest_objectives", ["quest_step_id"]
        )
    if not _index_exists("quest_objectives", "idx_quest_objectives_type"):
        op.create_index(
            "idx_quest_objectives_type", "quest_objectives", ["objective_type"]
        )

    if not _table_exists("quest_rewards"):
        op.create_table(
            "quest_rewards",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("quest_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("reward_type", sa.String(length=50), nullable=False),
            sa.Column("amount", sa.Integer(), nullable=True),
            sa.Column("badge_slug", sa.String(length=100), nullable=True),
            sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.ForeignKeyConstraint(["quest_id"], ["quests.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
    if not _index_exists("quest_rewards", "idx_quest_rewards_quest"):
        op.create_index("idx_quest_rewards_quest", "quest_rewards", ["quest_id"])
    if not _index_exists("quest_rewards", "idx_quest_rewards_type"):
        op.create_index("idx_quest_rewards_type", "quest_rewards", ["reward_type"])

    if not _table_exists("quest_progress"):
        op.create_table(
            "quest_progress",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("quest_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column(
                "status",
                sa.String(length=20),
                server_default=sa.text("'in_progress'"),
                nullable=False,
            ),
            sa.Column(
                "started_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["quest_id"], ["quests.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("user_id", "quest_id", name="uq_quest_progress_user"),
        )
    if not _index_exists("quest_progress", "idx_quest_progress_user"):
        op.create_index("idx_quest_progress_user", "quest_progress", ["user_id"])
    if not _index_exists("quest_progress", "idx_quest_progress_quest"):
        op.create_index("idx_quest_progress_quest", "quest_progress", ["quest_id"])
    if not _index_exists("quest_progress", "idx_quest_progress_status"):
        op.create_index("idx_quest_progress_status", "quest_progress", ["status"])


def downgrade() -> None:
    if _index_exists("quest_progress", "idx_quest_progress_status"):
        op.drop_index("idx_quest_progress_status", table_name="quest_progress")
    if _index_exists("quest_progress", "idx_quest_progress_quest"):
        op.drop_index("idx_quest_progress_quest", table_name="quest_progress")
    if _index_exists("quest_progress", "idx_quest_progress_user"):
        op.drop_index("idx_quest_progress_user", table_name="quest_progress")
    if _table_exists("quest_progress"):
        op.drop_table("quest_progress")

    if _index_exists("quest_rewards", "idx_quest_rewards_type"):
        op.drop_index("idx_quest_rewards_type", table_name="quest_rewards")
    if _index_exists("quest_rewards", "idx_quest_rewards_quest"):
        op.drop_index("idx_quest_rewards_quest", table_name="quest_rewards")
    if _table_exists("quest_rewards"):
        op.drop_table("quest_rewards")

    if _index_exists("quest_objectives", "idx_quest_objectives_type"):
        op.drop_index("idx_quest_objectives_type", table_name="quest_objectives")
    if _index_exists("quest_objectives", "idx_quest_objectives_step"):
        op.drop_index("idx_quest_objectives_step", table_name="quest_objectives")
    if _table_exists("quest_objectives"):
        op.drop_table("quest_objectives")

    if _index_exists("quest_steps", "idx_quest_steps_order"):
        op.drop_index("idx_quest_steps_order", table_name="quest_steps")
    if _index_exists("quest_steps", "idx_quest_steps_quest"):
        op.drop_index("idx_quest_steps_quest", table_name="quest_steps")
    if _table_exists("quest_steps"):
        op.drop_table("quest_steps")

    if _index_exists("quests", "idx_quests_order"):
        op.drop_index("idx_quests_order", table_name="quests")
    if _index_exists("quests", "idx_quests_active"):
        op.drop_index("idx_quests_active", table_name="quests")
    if _index_exists("quests", "idx_quests_slug"):
        op.drop_index("idx_quests_slug", table_name="quests")
    if _foreign_key_exists("quests", "fk_quests_prerequisite_id"):
        op.drop_constraint("fk_quests_prerequisite_id", "quests", type_="foreignkey")
    if _table_exists("quests"):
        op.drop_table("quests")
