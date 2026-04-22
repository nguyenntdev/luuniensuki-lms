"""Add audit_logs table.

Revision ID: 0016_audit_logs
Revises: 0015_embedding_jobs
Create Date: 2025-01-16
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0016_audit_logs"
down_revision = "0015_embedding_jobs"
branch_labels = None
depends_on = None


def _table_exists(table_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return table_name in inspector.get_table_names()


def _index_exists(table_name: str, index_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return index_name in {idx["name"] for idx in inspector.get_indexes(table_name)}


def upgrade() -> None:
    # Create audit_logs table
    if not _table_exists("audit_logs"):
        op.create_table(
            "audit_logs",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("action", sa.String(length=50), nullable=False),
            sa.Column("resource_type", sa.String(length=50), nullable=False),
            sa.Column("resource_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("old_value", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column("new_value", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column("ip_address", sa.String(length=45), nullable=True),
            sa.Column("user_agent", sa.Text(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(
                ["user_id"],
                ["users.id"],
                name="fk_audit_logs_user_id",
                ondelete="SET NULL",
            ),
        )

    # Create indexes
    if not _index_exists("audit_logs", "idx_audit_logs_user"):
        op.create_index("idx_audit_logs_user", "audit_logs", ["user_id"])

    if not _index_exists("audit_logs", "idx_audit_logs_action"):
        op.create_index("idx_audit_logs_action", "audit_logs", ["action"])

    if not _index_exists("audit_logs", "idx_audit_logs_resource_type"):
        op.create_index("idx_audit_logs_resource_type", "audit_logs", ["resource_type"])

    if not _index_exists("audit_logs", "idx_audit_logs_created_at"):
        op.create_index("idx_audit_logs_created_at", "audit_logs", ["created_at"])

    if not _index_exists("audit_logs", "idx_audit_logs_resource"):
        op.create_index(
            "idx_audit_logs_resource", "audit_logs", ["resource_type", "resource_id"]
        )


def downgrade() -> None:
    # Drop indexes
    if _index_exists("audit_logs", "idx_audit_logs_resource"):
        op.drop_index("idx_audit_logs_resource", table_name="audit_logs")

    if _index_exists("audit_logs", "idx_audit_logs_created_at"):
        op.drop_index("idx_audit_logs_created_at", table_name="audit_logs")

    if _index_exists("audit_logs", "idx_audit_logs_resource_type"):
        op.drop_index("idx_audit_logs_resource_type", table_name="audit_logs")

    if _index_exists("audit_logs", "idx_audit_logs_action"):
        op.drop_index("idx_audit_logs_action", table_name="audit_logs")

    if _index_exists("audit_logs", "idx_audit_logs_user"):
        op.drop_index("idx_audit_logs_user", table_name="audit_logs")

    # Drop table
    if _table_exists("audit_logs"):
        op.drop_table("audit_logs")

