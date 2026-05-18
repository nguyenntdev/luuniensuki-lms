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


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("onboarding_goal", sa.String(length=50), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column(
            "onboarding_completed",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.add_column(
        "users",
        sa.Column("onboarding_completed_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "onboarding_completed_at")
    op.drop_column("users", "onboarding_completed")
    op.drop_column("users", "onboarding_goal")

