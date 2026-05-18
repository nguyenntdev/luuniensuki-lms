from __future__ import annotations

import sqlalchemy as sa

from alembic import op

# Timestamp: 2025-12-18 12:00:00
revision = "0003_add_username"
down_revision = "0002_profile_features"
branch_labels = None
depends_on = None


def _column_exists(table_name: str, column_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return column_name in {col["name"] for col in inspector.get_columns(table_name)}


def _index_exists(table_name: str, index_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return index_name in {idx["name"] for idx in inspector.get_indexes(table_name)}


def _unique_constraint_exists(table_name: str, constraint_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return constraint_name in {
        uc["name"] for uc in inspector.get_unique_constraints(table_name)
    }


def upgrade() -> None:
    if not _column_exists("users", "username"):
        op.add_column("users", sa.Column("username", sa.String(50), nullable=True))
    if not _unique_constraint_exists("users", "uq_users_username"):
        op.create_unique_constraint("uq_users_username", "users", ["username"])
    if not _index_exists("users", "idx_users_username"):
        op.create_index("idx_users_username", "users", ["username"])


def downgrade() -> None:
    if _index_exists("users", "idx_users_username"):
        op.drop_index("idx_users_username", table_name="users")
    if _unique_constraint_exists("users", "uq_users_username"):
        op.drop_constraint("uq_users_username", "users", type_="unique")
    if _column_exists("users", "username"):
        op.drop_column("users", "username")
