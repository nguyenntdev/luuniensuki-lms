"""Add content versioning metadata.

Revision ID: 0012_content_versioning
Revises: 0011_rag_embeddings
Create Date: 2025-01-15
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0012_content_versioning"
down_revision = "0011_rag_embeddings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add versioning fields to lesson_content
    op.add_column(
        "lesson_content",
        sa.Column(
            "version",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("1"),
        ),
    )
    op.add_column(
        "lesson_content",
        sa.Column(
            "last_editor_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )
    op.add_column(
        "lesson_content",
        sa.Column(
            "published_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "lesson_content",
        sa.Column(
            "publish_note",
            sa.Text(),
            nullable=True,
        ),
    )
    op.create_foreign_key(
        "fk_lesson_content_last_editor",
        "lesson_content",
        "users",
        ["last_editor_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # Create content_versions table
    op.create_table(
        "content_versions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
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
            "version",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "data",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "editor_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            "change_note",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_foreign_key(
        "fk_content_versions_editor",
        "content_versions",
        "users",
        ["editor_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "idx_content_versions_type",
        "content_versions",
        ["content_type"],
    )
    op.create_index(
        "idx_content_versions_content",
        "content_versions",
        ["content_id"],
    )
    op.create_index(
        "idx_content_versions_created",
        "content_versions",
        ["created_at"],
    )


def downgrade() -> None:
    op.drop_index("idx_content_versions_created", table_name="content_versions")
    op.drop_index("idx_content_versions_content", table_name="content_versions")
    op.drop_index("idx_content_versions_type", table_name="content_versions")
    op.drop_constraint("fk_content_versions_editor", "content_versions", type_="foreignkey")
    op.drop_table("content_versions")

    op.drop_constraint("fk_lesson_content_last_editor", "lesson_content", type_="foreignkey")
    op.drop_column("lesson_content", "publish_note")
    op.drop_column("lesson_content", "published_at")
    op.drop_column("lesson_content", "last_editor_id")
    op.drop_column("lesson_content", "version")

