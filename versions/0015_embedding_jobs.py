"""Add EmbeddingJob model for tracking embedding rebuild progress.

Revision ID: 0015_embedding_jobs
Revises: 0014_streak_rewards
Create Date: 2025-01-16
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0015_embedding_jobs"
down_revision = "0014_streak_rewards"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create embedding_jobs table
    op.create_table(
        "embedding_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default=sa.text("'pending'"),
        ),
        sa.Column(
            "total_documents",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "processed_documents",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    
    # Create indexes
    op.create_index(
        "idx_embedding_jobs_status",
        "embedding_jobs",
        ["status"],
    )
    op.create_index(
        "idx_embedding_jobs_created_by",
        "embedding_jobs",
        ["created_by_id"],
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index("idx_embedding_jobs_created_by", table_name="embedding_jobs")
    op.drop_index("idx_embedding_jobs_status", table_name="embedding_jobs")
    
    # Drop table
    op.drop_table("embedding_jobs")

