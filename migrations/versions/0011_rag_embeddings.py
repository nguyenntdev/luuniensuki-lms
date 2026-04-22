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


def upgrade() -> None:
    op.add_column(
        "rag_documents",
        sa.Column("embedding", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "rag_documents",
        sa.Column("embedding_model", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "rag_documents",
        sa.Column("embedding_updated_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.add_column(
        "rag_settings",
        sa.Column(
            "embedding_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
    )
    op.add_column(
        "rag_settings",
        sa.Column(
            "hybrid_alpha",
            sa.Float(),
            nullable=False,
            server_default=sa.text("0.6"),
        ),
    )


def downgrade() -> None:
    op.drop_column("rag_settings", "hybrid_alpha")
    op.drop_column("rag_settings", "embedding_enabled")
    op.drop_column("rag_documents", "embedding_updated_at")
    op.drop_column("rag_documents", "embedding_model")
    op.drop_column("rag_documents", "embedding")
