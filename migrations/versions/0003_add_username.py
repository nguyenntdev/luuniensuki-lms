from __future__ import annotations

import sqlalchemy as sa
from alembic import op


# Timestamp: 2025-12-18 12:00:00
revision = "0003_add_username"
down_revision = "0002_profile_features"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("username", sa.String(50), nullable=True))
    op.create_unique_constraint("uq_users_username", "users", ["username"])
    op.create_index("idx_users_username", "users", ["username"])


def downgrade() -> None:
    op.drop_index("idx_users_username", table_name="users")
    op.drop_constraint("uq_users_username", "users", type_="unique")
    op.drop_column("users", "username")

