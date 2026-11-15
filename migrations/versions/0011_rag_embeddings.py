"""Add embeddings and hybrid settings for RAG.

Revision ID: 0011_rag_embeddings
Revises: 0010_rag_documents
Create Date: 2025-01-15
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0011_rag_embeddings"
down_revision = "0010_rag_documents"
branch_labels = None
depends_on = None


def _column_exists(table_name: str, column_name: str) -> bool:
    """Return True when ``column_name`` already exists on ``table_name``.

    ``0001_initial_schema`` materialises the full SQLAlchemy metadata, so a
    fresh database already has these columns. The migration must therefore be
    idempotent, exactly like ``0010_rag_documents``.
    """
    inspector = sa.inspect(op.get_bind())
    if table_name not in inspector.get_table_names():
        return False
    return column_name in {c["name"] for c in inspector.get_columns(table_name)}


def _add_column_if_missing(table_name: str, column: sa.Column) -> None:
    if not _column_exists(table_name, column.name):
        op.add_column(table_name, column)


def upgrade() -> None:
    _add_column_if_missing(
        "rag_documents",
        sa.Column("embedding", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    _add_column_if_missing(
        "rag_documents",
        sa.Column("embedding_model", sa.String(length=100), nullable=True),
    )
    _add_column_if_missing(
        "rag_documents",
        sa.Column("embedding_updated_at", sa.DateTime(timezone=True), nullable=True),
    )

    _add_column_if_missing(
        "rag_settings",
        sa.Column(
            "embedding_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
    )
    _add_column_if_missing(
        "rag_settings",
        sa.Column(
            "hybrid_alpha",
            sa.Float(),
            nullable=False,
            server_default=sa.text("0.6"),
        ),
    )


def downgrade() -> None:
    for table_name, column_name in (
        ("rag_settings", "hybrid_alpha"),
        ("rag_settings", "embedding_enabled"),
        ("rag_documents", "embedding_updated_at"),
        ("rag_documents", "embedding_model"),
        ("rag_documents", "embedding"),
    ):
        if _column_exists(table_name, column_name):
            op.drop_column(table_name, column_name)
