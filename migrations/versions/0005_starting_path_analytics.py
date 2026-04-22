from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# Timestamp: 2025-12-25 01:10:00
revision = "0005_starting_path_analytics"
down_revision = "0004_urn_exams"
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


def _foreign_key_exists(table_name: str, fk_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return fk_name in {fk["name"] for fk in inspector.get_foreign_keys(table_name)}


def upgrade() -> None:
    if not _column_exists("users", "starting_urn_id"):
        op.add_column(
            "users",
            sa.Column("starting_urn_id", postgresql.UUID(as_uuid=True), nullable=True),
        )
    if not _foreign_key_exists("users", "fk_users_starting_urn_id"):
        op.create_foreign_key(
            "fk_users_starting_urn_id",
            "users",
            "urns",
            ["starting_urn_id"],
            ["id"],
            ondelete="SET NULL",
        )
    if not _index_exists("users", "idx_users_starting_urn"):
        op.create_index("idx_users_starting_urn", "users", ["starting_urn_id"])

    if not _table_exists("analytics_events"):
        op.create_table(
            "analytics_events",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("event_name", sa.String(length=100), nullable=False),
            sa.Column("path", sa.String(length=255), nullable=True),
            sa.Column(
                "payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True
            ),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
    if not _index_exists("analytics_events", "idx_analytics_user"):
        op.create_index("idx_analytics_user", "analytics_events", ["user_id"])
    if not _index_exists("analytics_events", "idx_analytics_event_name"):
        op.create_index("idx_analytics_event_name", "analytics_events", ["event_name"])
    if not _index_exists("analytics_events", "idx_analytics_created_at"):
        op.create_index("idx_analytics_created_at", "analytics_events", ["created_at"])


def downgrade() -> None:
    if _index_exists("analytics_events", "idx_analytics_created_at"):
        op.drop_index("idx_analytics_created_at", table_name="analytics_events")
    if _index_exists("analytics_events", "idx_analytics_event_name"):
        op.drop_index("idx_analytics_event_name", table_name="analytics_events")
    if _index_exists("analytics_events", "idx_analytics_user"):
        op.drop_index("idx_analytics_user", table_name="analytics_events")
    if _table_exists("analytics_events"):
        op.drop_table("analytics_events")

    if _index_exists("users", "idx_users_starting_urn"):
        op.drop_index("idx_users_starting_urn", table_name="users")
    if _foreign_key_exists("users", "fk_users_starting_urn_id"):
        op.drop_constraint("fk_users_starting_urn_id", "users", type_="foreignkey")
    if _column_exists("users", "starting_urn_id"):
        op.drop_column("users", "starting_urn_id")
