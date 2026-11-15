"""Add crash reporting for mobile and web clients.

Revision ID: 0014_crash_reports
Revises: 0013_review_workflow
Create Date: 2025-01-17
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0014_crash_reports"
down_revision = "0013_review_workflow"
branch_labels = None
depends_on = None


def _table_exists(table_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return table_name in inspector.get_table_names()


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
    if not _table_exists("crash_reports"):
        # Create crash_reports table
        op.create_table(
            "crash_reports",
            sa.Column(
                "id",
                postgresql.UUID(as_uuid=True),
                primary_key=True,
            ),
            sa.Column(
                "user_id",
                postgresql.UUID(as_uuid=True),
                nullable=True,
            ),
            sa.Column(
                "session_id",
                postgresql.UUID(as_uuid=True),
                nullable=True,
            ),
            sa.Column(
                "error_type",
                sa.String(length=20),
                nullable=False,
            ),
            sa.Column(
                "error_message",
                sa.Text(),
                nullable=False,
            ),
            sa.Column(
                "stack_trace",
                sa.Text(),
                nullable=True,
            ),
            sa.Column(
                "platform",
                sa.String(length=20),
                nullable=False,
            ),
            sa.Column(
                "app_version",
                sa.String(length=20),
                nullable=False,
            ),
            sa.Column(
                "device_model",
                sa.String(length=100),
                nullable=True,
            ),
            sa.Column(
                "os_version",
                sa.String(length=50),
                nullable=True,
            ),
            sa.Column(
                "additional_data",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=True,
            ),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.Column(
                "is_resolved",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("false"),
            ),
            sa.Column(
                "resolved_by_id",
                postgresql.UUID(as_uuid=True),
                nullable=True,
            ),
            sa.Column(
                "resolved_at",
                sa.DateTime(timezone=True),
                nullable=True,
            ),
        )

        # Add foreign key constraints
        op.create_foreign_key(
            "fk_crash_reports_user",
            "crash_reports",
            "users",
            ["user_id"],
            ["id"],
            ondelete="CASCADE",
        )
        op.create_foreign_key(
            "fk_crash_reports_resolved_by",
            "crash_reports",
            "users",
            ["resolved_by_id"],
            ["id"],
            ondelete="SET NULL",
        )

    # Create indices for better query performance
    if not _index_exists("crash_reports", "idx_crash_reports_user_id"):
        op.create_index("idx_crash_reports_user_id", "crash_reports", ["user_id"])
    if not _index_exists("crash_reports", "idx_crash_reports_session_id"):
        op.create_index("idx_crash_reports_session_id", "crash_reports", ["session_id"])
    if not _index_exists("crash_reports", "idx_crash_reports_error_type"):
        op.create_index("idx_crash_reports_error_type", "crash_reports", ["error_type"])
    if not _index_exists("crash_reports", "idx_crash_reports_platform"):
        op.create_index("idx_crash_reports_platform", "crash_reports", ["platform"])
    if not _index_exists("crash_reports", "idx_crash_reports_created_at"):
        op.create_index("idx_crash_reports_created_at", "crash_reports", ["created_at"])
    if not _index_exists("crash_reports", "idx_crash_reports_is_resolved"):
        op.create_index("idx_crash_reports_is_resolved", "crash_reports", ["is_resolved"])


def downgrade() -> None:
    # Drop indices
    op.drop_index("idx_crash_reports_is_resolved", table_name="crash_reports")
    op.drop_index("idx_crash_reports_created_at", table_name="crash_reports")
    op.drop_index("idx_crash_reports_platform", table_name="crash_reports")
    op.drop_index("idx_crash_reports_error_type", table_name="crash_reports")
    op.drop_index("idx_crash_reports_session_id", table_name="crash_reports")
    op.drop_index("idx_crash_reports_user_id", table_name="crash_reports")

    # Drop foreign keys
    op.drop_constraint("fk_crash_reports_resolved_by", "crash_reports", type_="foreignkey")
    op.drop_constraint("fk_crash_reports_user", "crash_reports", type_="foreignkey")

    # Drop table
    op.drop_table("crash_reports")

