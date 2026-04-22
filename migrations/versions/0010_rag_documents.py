from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# Timestamp: 2025-01-15 18:00:00
revision = "0010_rag_documents"
down_revision = "0009_ai_recommendations"
branch_labels = None
depends_on = None


def _table_exists(table_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return table_name in inspector.get_table_names()


def _index_exists(table_name: str, index_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return index_name in {idx["name"] for idx in inspector.get_indexes(table_name)}


def upgrade() -> None:
    if not _table_exists("rag_documents"):
        op.create_table(
            "rag_documents",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("title", sa.String(length=255), nullable=False),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column(
                "source_type",
                sa.String(length=30),
                server_default=sa.text("'manual'"),
                nullable=False,
            ),
            sa.Column("source_path", sa.String(length=255), nullable=True),
            sa.Column(
                "is_active",
                sa.Boolean(),
                server_default=sa.text("true"),
                nullable=False,
            ),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.PrimaryKeyConstraint("id"),
        )
    if not _index_exists("rag_documents", "idx_rag_documents_active"):
        op.create_index(
            "idx_rag_documents_active", "rag_documents", ["is_active"]
        )
    if not _index_exists("rag_documents", "idx_rag_documents_updated"):
        op.create_index(
            "idx_rag_documents_updated", "rag_documents", ["updated_at"]
        )

    if not _table_exists("rag_settings"):
        op.create_table(
            "rag_settings",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("system_instruction", sa.Text(), nullable=True),
            sa.Column("prompt_prefix", sa.Text(), nullable=True),
            sa.Column("model_override", sa.String(length=100), nullable=True),
            sa.Column("temperature", sa.Float(), nullable=True),
            sa.Column(
                "max_documents",
                sa.Integer(),
                server_default=sa.text("6"),
                nullable=False,
            ),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.PrimaryKeyConstraint("id"),
        )


def downgrade() -> None:
    if _index_exists("rag_documents", "idx_rag_documents_updated"):
        op.drop_index("idx_rag_documents_updated", table_name="rag_documents")
    if _index_exists("rag_documents", "idx_rag_documents_active"):
        op.drop_index("idx_rag_documents_active", table_name="rag_documents")
    if _table_exists("rag_documents"):
        op.drop_table("rag_documents")

    if _table_exists("rag_settings"):
        op.drop_table("rag_settings")
