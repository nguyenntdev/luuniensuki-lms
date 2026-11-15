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


def _table_exists(table_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return table_name in inspector.get_table_names()


def _column_exists(table_name: str, column_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    if table_name not in inspector.get_table_names():
        return False
    return column_name in {c["name"] for c in inspector.get_columns(table_name)}


def _add_column_if_missing(table_name: str, column: sa.Column) -> None:
    if not _column_exists(table_name, column.name):
        op.add_column(table_name, column)


def _index_exists(table_name: str, index_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    if table_name not in inspector.get_table_names():
        return False
    return index_name in {i["name"] for i in inspector.get_indexes(table_name)}


def _constraint_exists(table_name: str, constraint_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    if table_name not in inspector.get_table_names():
        return False
    fks = {fk["name"] for fk in inspector.get_foreign_keys(table_name)}
    uqs = {uq["name"] for uq in inspector.get_unique_constraints(table_name)}
    cks = {ck["name"] for ck in inspector.get_check_constraints(table_name)}
    return constraint_name in (fks | uqs | cks)


def upgrade() -> None:
    _add_column_if_missing(
        "live_sessions",
        sa.Column("idempotency_key", sa.String(length=128), nullable=True),
    )
    if not _constraint_exists("live_sessions", "uq_live_sessions_idempotency_key"):
        op.create_unique_constraint(
            "uq_live_sessions_idempotency_key",
            "live_sessions",
            ["idempotency_key"],
        )
    if not _index_exists("live_sessions", "idx_live_sessions_idempotency_key"):
        op.create_index(
            "idx_live_sessions_idempotency_key",
            "live_sessions",
            ["idempotency_key"],
        )

    if not _table_exists("live_events"):
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
    if not _index_exists("live_events", "idx_live_events_session"):
        op.create_index("idx_live_events_session", "live_events", ["live_session_id"])
    if not _index_exists("live_events", "idx_live_events_type"):
        op.create_index("idx_live_events_type", "live_events", ["event_type"])
    if not _index_exists("live_events", "idx_live_events_created_at"):
        op.create_index("idx_live_events_created_at", "live_events", ["created_at"])
    if not _index_exists("live_events", "idx_live_events_session_created_at"):
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
