"""Add content tagging for recommendation and search.

Revision ID: 0013_content_tagging
Revises: 0012_content_versioning
Create Date: 2025-01-16
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0013_content_tagging"
down_revision = "0012_content_versioning"
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
    if not _table_exists("tags"):
        # Create tags table
        op.create_table(
            "tags",
            sa.Column(
                "id",
                postgresql.UUID(as_uuid=True),
                primary_key=True,
            ),
            sa.Column(
                "slug",
                sa.String(length=100),
                nullable=False,
                unique=True,
            ),
            sa.Column(
                "name",
                sa.String(length=200),
                nullable=False,
            ),
            sa.Column(
                "tag_type",
                sa.String(length=50),
                nullable=False,
            ),
            sa.Column(
                "description",
                sa.Text(),
                nullable=True,
            ),
            sa.Column(
                "is_active",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("true"),
            ),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
        )
    if not _index_exists("tags", "idx_tags_slug"):
        op.create_index("idx_tags_slug", "tags", ["slug"])
    if not _index_exists("tags", "idx_tags_type"):
        op.create_index("idx_tags_type", "tags", ["tag_type"])
    if not _index_exists("tags", "idx_tags_active"):
        op.create_index("idx_tags_active", "tags", ["is_active"])

    if not _table_exists("content_tags"):
        # Create content_tags table
        op.create_table(
            "content_tags",
            sa.Column(
                "id",
                postgresql.UUID(as_uuid=True),
                primary_key=True,
            ),
            sa.Column(
                "tag_id",
                postgresql.UUID(as_uuid=True),
                nullable=False,
            ),
            sa.Column(
                "content_type",
                sa.String(length=50),
                nullable=False,
            ),
            sa.Column(
                "content_id",
                postgresql.UUID(as_uuid=True),
                nullable=False,
            ),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
        )
    if not _constraint_exists("content_tags", "fk_content_tags_tag"):
        op.create_foreign_key(
            "fk_content_tags_tag",
            "content_tags",
            "tags",
            ["tag_id"],
            ["id"],
            ondelete="CASCADE",
        )
    if not _constraint_exists("content_tags", "uq_content_tag"):
        op.create_unique_constraint(
            "uq_content_tag",
            "content_tags",
            ["tag_id", "content_type", "content_id"],
        )
    if not _index_exists("content_tags", "idx_content_tags_tag"):
        op.create_index("idx_content_tags_tag", "content_tags", ["tag_id"])
    if not _index_exists("content_tags", "idx_content_tags_content_type"):
        op.create_index("idx_content_tags_content_type", "content_tags", ["content_type"])
    if not _index_exists("content_tags", "idx_content_tags_content"):
        op.create_index(
            "idx_content_tags_content", "content_tags", ["content_type", "content_id"]
        )


def downgrade() -> None:
    op.drop_index("idx_content_tags_content", table_name="content_tags")
    op.drop_index("idx_content_tags_content_type", table_name="content_tags")
    op.drop_index("idx_content_tags_tag", table_name="content_tags")
    op.drop_constraint("uq_content_tag", "content_tags", type_="unique")
    op.drop_constraint("fk_content_tags_tag", "content_tags", type_="foreignkey")
    op.drop_table("content_tags")

    op.drop_index("idx_tags_active", table_name="tags")
    op.drop_index("idx_tags_type", table_name="tags")
    op.drop_index("idx_tags_slug", table_name="tags")
    op.drop_table("tags")
