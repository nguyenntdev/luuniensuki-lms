from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "0002_profile_features"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("bio", sa.Text(), nullable=True))
    op.add_column(
        "users",
        sa.Column(
            "is_profile_public",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "is_profile_public")
    op.drop_column("users", "bio")

