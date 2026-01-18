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


def upgrade() -> None:
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
    op.create_index("idx_tags_slug", "tags", ["slug"])
    op.create_index("idx_tags_type", "tags", ["tag_type"])
    op.create_index("idx_tags_active", "tags", ["is_active"])

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
    op.create_foreign_key(
        "fk_content_tags_tag",
        "content_tags",
        "tags",
        ["tag_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_unique_constraint(
        "uq_content_tag",
        "content_tags",
        ["tag_id", "content_type", "content_id"],
    )
    op.create_index("idx_content_tags_tag", "content_tags", ["tag_id"])
    op.create_index("idx_content_tags_content_type", "content_tags", ["content_type"])
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
