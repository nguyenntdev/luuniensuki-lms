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


def _table_exists(table_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return table_name in inspector.get_table_names()


def _column_exists(table_name: str, column_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    if table_name not in inspector.get_table_names():
        return False
    return column_name in {c["name"] for c in inspector.get_columns(table_name)}


def _add_column_if_missing(table_name: str, column: sa.Column) -> None:
    if not _column_exists(table_name, column.name):
        op.add_column(table_name, column)


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
    if not _table_exists("content_versions"):
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
    if not _constraint_exists("content_versions", "fk_content_versions_editor"):
        op.create_foreign_key(
            "fk_content_versions_editor",
            "content_versions",
            "users",
            ["editor_id"],
            ["id"],
            ondelete="SET NULL",
        )
    if not _index_exists("content_versions", "idx_content_versions_type"):
        op.create_index(
            "idx_content_versions_type",
            "content_versions",
            ["content_type"],
        )
    if not _index_exists("content_versions", "idx_content_versions_content"):
        op.create_index(
            "idx_content_versions_content",
            "content_versions",
            ["content_id"],
        )
    if not _index_exists("content_versions", "idx_content_versions_created"):
        op.create_index(
            "idx_content_versions_created",
            "content_versions",
            ["created_at"],
        )

    # Add versioning fields to lesson_content
    _add_column_if_missing(
        "lesson_content",
        sa.Column(
            "version",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("1"),
        ),
    )
    _add_column_if_missing(
        "lesson_content",
        sa.Column(
            "last_editor_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )
    _add_column_if_missing(
        "lesson_content",
        sa.Column(
            "published_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    _add_column_if_missing(
        "lesson_content",
        sa.Column(
            "publish_note",
            sa.Text(),
            nullable=True,
        ),
    )
    if not _constraint_exists("lesson_content", "fk_lesson_content_last_editor"):
        op.create_foreign_key(
            "fk_lesson_content_last_editor",
            "lesson_content",
            "users",
            ["last_editor_id"],
            ["id"],
            ondelete="SET NULL",
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

