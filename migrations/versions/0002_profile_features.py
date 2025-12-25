from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0002_profile_features"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def _column_exists(table_name: str, column_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return column_name in {col["name"] for col in inspector.get_columns(table_name)}


def upgrade() -> None:
    if not _column_exists("users", "bio"):
        op.add_column("users", sa.Column("bio", sa.Text(), nullable=True))
    if not _column_exists("users", "is_profile_public"):
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
    if _column_exists("users", "is_profile_public"):
        op.drop_column("users", "is_profile_public")
    if _column_exists("users", "bio"):
        op.drop_column("users", "bio")
