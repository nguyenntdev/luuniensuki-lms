"""Add lesson_cache table for offline caching.

Revision ID: 0018_lesson_cache
Revises: 0017_user_sessions
Create Date: 2025-01-18
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0018_lesson_cache"
down_revision = "0017_user_sessions"
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
    # Create lesson_cache table
    if not _table_exists("lesson_cache"):
        op.create_table(
            "lesson_cache",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column(
                "user_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column(
                "lesson_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("lesson_content.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column(
                "cached_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.Column(
                "cache_version",
                sa.Integer,
                nullable=False,
                server_default=sa.text("1"),
            ),
            sa.Column(
                "file_size_bytes",
                sa.Integer,
                nullable=False,
                server_default=sa.text("0"),
            ),
            sa.Column(
                "is_valid",
                sa.Boolean,
                nullable=False,
                server_default=sa.text("true"),
            ),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        )

    # Create unique constraint
    if not _constraint_exists("lesson_cache", "uq_lesson_cache_user_lesson"):
        op.create_unique_constraint(
            "uq_lesson_cache_user_lesson",
            "lesson_cache",
            ["user_id", "lesson_id"],
        )

    # Create indexes
    if not _index_exists("lesson_cache", "idx_lesson_cache_user"):
        op.create_index("idx_lesson_cache_user", "lesson_cache", ["user_id"])

    if not _index_exists("lesson_cache", "idx_lesson_cache_lesson"):
        op.create_index("idx_lesson_cache_lesson", "lesson_cache", ["lesson_id"])

    if not _index_exists("lesson_cache", "idx_lesson_cache_cached_at"):
        op.create_index("idx_lesson_cache_cached_at", "lesson_cache", ["cached_at"])


def downgrade() -> None:
    # Drop indexes
    if _index_exists("lesson_cache", "idx_lesson_cache_cached_at"):
        op.drop_index("idx_lesson_cache_cached_at", table_name="lesson_cache")

    if _index_exists("lesson_cache", "idx_lesson_cache_lesson"):
        op.drop_index("idx_lesson_cache_lesson", table_name="lesson_cache")

    if _index_exists("lesson_cache", "idx_lesson_cache_user"):
        op.drop_index("idx_lesson_cache_user", table_name="lesson_cache")

    # Drop unique constraint
    if _constraint_exists("lesson_cache", "uq_lesson_cache_user_lesson"):
        op.drop_constraint(
            "uq_lesson_cache_user_lesson", "lesson_cache", type_="unique"
        )

    # Drop table
    if _table_exists("lesson_cache"):
        op.drop_table("lesson_cache")

