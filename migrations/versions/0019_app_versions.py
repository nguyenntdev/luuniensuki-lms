"""Add app_versions table for mobile version management.

Revision ID: 0019_app_versions
Revises: 0018_lesson_cache
Create Date: 2025-01-19
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0019_app_versions"
down_revision = "0018_lesson_cache"
branch_labels = None
depends_on = None


def _table_exists(table_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return table_name in inspector.get_table_names()


def _index_exists(table_name: str, index_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    if not _table_exists(table_name):
        return False
    return index_name in {idx["name"] for idx in inspector.get_indexes(table_name)}


def _constraint_exists(table_name: str, constraint_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    if not _table_exists(table_name):
        return False
    unique_constraints = inspector.get_unique_constraints(table_name)
    return constraint_name in {c["name"] for c in unique_constraints}


def upgrade() -> None:
    # Create app_versions table
    if not _table_exists("app_versions"):
        op.create_table(
            "app_versions",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("platform", sa.String(20), nullable=False),
            sa.Column("version", sa.String(20), nullable=False),
            sa.Column("version_code", sa.Integer, nullable=False),
            sa.Column("min_required_version", sa.String(20), nullable=False),
            sa.Column(
                "is_current",
                sa.Boolean,
                nullable=False,
                server_default=sa.text("false"),
            ),
            sa.Column(
                "force_update",
                sa.Boolean,
                nullable=False,
                server_default=sa.text("false"),
            ),
            sa.Column("release_notes", sa.Text, nullable=True),
            sa.Column("download_url", sa.String(500), nullable=True),
            sa.Column(
                "released_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
        )

    # Create unique constraint on platform + version
    if not _constraint_exists("app_versions", "uq_app_version_platform_version"):
        op.create_unique_constraint(
            "uq_app_version_platform_version",
            "app_versions",
            ["platform", "version"],
        )

    # Create indexes
    if not _index_exists("app_versions", "idx_app_versions_platform"):
        op.create_index("idx_app_versions_platform", "app_versions", ["platform"])

    if not _index_exists("app_versions", "idx_app_versions_is_current"):
        op.create_index("idx_app_versions_is_current", "app_versions", ["is_current"])

    if not _index_exists("app_versions", "idx_app_versions_released_at"):
        op.create_index("idx_app_versions_released_at", "app_versions", ["released_at"])


def downgrade() -> None:
    # Drop indexes
    if _index_exists("app_versions", "idx_app_versions_released_at"):
        op.drop_index("idx_app_versions_released_at", table_name="app_versions")

    if _index_exists("app_versions", "idx_app_versions_is_current"):
        op.drop_index("idx_app_versions_is_current", table_name="app_versions")

    if _index_exists("app_versions", "idx_app_versions_platform"):
        op.drop_index("idx_app_versions_platform", table_name="app_versions")

    # Drop unique constraint
    if _constraint_exists("app_versions", "uq_app_version_platform_version"):
        op.drop_constraint(
            "uq_app_version_platform_version", "app_versions", type_="unique"
        )

    # Drop table
    if _table_exists("app_versions"):
        op.drop_table("app_versions")

