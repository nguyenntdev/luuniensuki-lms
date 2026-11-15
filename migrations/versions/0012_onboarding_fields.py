"""Add onboarding fields to users table.

Revision ID: 0012_onboarding_fields
Revises: 0011_rag_embeddings
Create Date: 2025-01-16
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0012_onboarding_fields"
down_revision = "0011_rag_embeddings"
branch_labels = None
depends_on = None


def _add_column_if_missing(table_name: str, column: sa.Column) -> None:
    inspector = sa.inspect(op.get_bind())
    if table_name not in inspector.get_table_names():
        return
    if column.name in {c["name"] for c in inspector.get_columns(table_name)}:
        return
    op.add_column(table_name, column)


def upgrade() -> None:
    _add_column_if_missing(
        "users",
        sa.Column("onboarding_goal", sa.String(length=50), nullable=True),
    )
    _add_column_if_missing(
        "users",
        sa.Column(
            "onboarding_completed",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    _add_column_if_missing(
        "users",
        sa.Column("onboarding_completed_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "onboarding_completed_at")
    op.drop_column("users", "onboarding_completed")
    op.drop_column("users", "onboarding_goal")

