from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# Timestamp: 2025-12-29 12:30:00
revision = "0009_ai_recommendations"
down_revision = "0008_teacher_classes"
branch_labels = None
depends_on = None


def _table_exists(table_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return table_name in inspector.get_table_names()


def _column_exists(table_name: str, column_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return column_name in {col["name"] for col in inspector.get_columns(table_name)}


def _index_exists(table_name: str, index_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return index_name in {idx["name"] for idx in inspector.get_indexes(table_name)}


def upgrade() -> None:
    if not _column_exists("users", "ai_personalization_enabled"):
        op.add_column(
            "users",
            sa.Column(
                "ai_personalization_enabled",
                sa.Boolean(),
                server_default=sa.text("true"),
                nullable=False,
            ),
        )

    if not _table_exists("recommendations"):
        op.create_table(
            "recommendations",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("source", sa.String(length=20), nullable=False),
            sa.Column("items", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
    if not _index_exists("recommendations", "idx_recommendations_user"):
        op.create_index("idx_recommendations_user", "recommendations", ["user_id"])
    if not _index_exists("recommendations", "idx_recommendations_created"):
        op.create_index(
            "idx_recommendations_created", "recommendations", ["created_at"]
        )

    if not _table_exists("ai_jobs"):
        op.create_table(
            "ai_jobs",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("job_type", sa.String(length=50), nullable=False),
            sa.Column(
                "status",
                sa.String(length=20),
                server_default=sa.text("'pending'"),
                nullable=False,
            ),
            sa.Column("provider", sa.String(length=50), nullable=True),
            sa.Column("prompt", sa.Text(), nullable=True),
            sa.Column("response", sa.Text(), nullable=True),
            sa.Column("error", sa.Text(), nullable=True),
            sa.Column(
                "retry_count",
                sa.Integer(),
                server_default=sa.text("0"),
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
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
    if not _index_exists("ai_jobs", "idx_ai_jobs_user"):
        op.create_index("idx_ai_jobs_user", "ai_jobs", ["user_id"])
    if not _index_exists("ai_jobs", "idx_ai_jobs_status"):
        op.create_index("idx_ai_jobs_status", "ai_jobs", ["status"])

    if not _table_exists("content_provenance"):
        op.create_table(
            "content_provenance",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("content_type", sa.String(length=50), nullable=False),
            sa.Column("content_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("provider", sa.String(length=50), nullable=True),
            sa.Column("model", sa.String(length=100), nullable=True),
            sa.Column("generated_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column(
                "metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True
            ),
            sa.PrimaryKeyConstraint("id"),
        )
    if not _index_exists("content_provenance", "idx_content_provenance_type"):
        op.create_index(
            "idx_content_provenance_type", "content_provenance", ["content_type"]
        )
    if not _index_exists("content_provenance", "idx_content_provenance_content"):
        op.create_index(
            "idx_content_provenance_content", "content_provenance", ["content_id"]
        )

    if not _table_exists("content_flags"):
        op.create_table(
            "content_flags",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("content_type", sa.String(length=50), nullable=False),
            sa.Column("content_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("reason", sa.String(length=255), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
    if not _index_exists("content_flags", "idx_content_flags_user"):
        op.create_index("idx_content_flags_user", "content_flags", ["user_id"])
    if not _index_exists("content_flags", "idx_content_flags_type"):
        op.create_index("idx_content_flags_type", "content_flags", ["content_type"])


def downgrade() -> None:
    if _index_exists("content_flags", "idx_content_flags_type"):
        op.drop_index("idx_content_flags_type", table_name="content_flags")
    if _index_exists("content_flags", "idx_content_flags_user"):
        op.drop_index("idx_content_flags_user", table_name="content_flags")
    if _table_exists("content_flags"):
        op.drop_table("content_flags")

    if _index_exists("content_provenance", "idx_content_provenance_content"):
        op.drop_index("idx_content_provenance_content", table_name="content_provenance")
    if _index_exists("content_provenance", "idx_content_provenance_type"):
        op.drop_index("idx_content_provenance_type", table_name="content_provenance")
    if _table_exists("content_provenance"):
        op.drop_table("content_provenance")

    if _index_exists("ai_jobs", "idx_ai_jobs_status"):
        op.drop_index("idx_ai_jobs_status", table_name="ai_jobs")
    if _index_exists("ai_jobs", "idx_ai_jobs_user"):
        op.drop_index("idx_ai_jobs_user", table_name="ai_jobs")
    if _table_exists("ai_jobs"):
        op.drop_table("ai_jobs")

    if _index_exists("recommendations", "idx_recommendations_created"):
        op.drop_index("idx_recommendations_created", table_name="recommendations")
    if _index_exists("recommendations", "idx_recommendations_user"):
        op.drop_index("idx_recommendations_user", table_name="recommendations")
    if _table_exists("recommendations"):
        op.drop_table("recommendations")

    if _column_exists("users", "ai_personalization_enabled"):
        op.drop_column("users", "ai_personalization_enabled")
