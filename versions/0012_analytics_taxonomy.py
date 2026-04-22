"""Add analytics event taxonomy fields.

Revision ID: 0012_analytics_taxonomy
Revises: 0011_rag_embeddings
Create Date: 2025-01-16
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0012_analytics_taxonomy"
down_revision = "0011_rag_embeddings"
branch_labels = None
depends_on = None


def _column_exists(table_name: str, column_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return column_name in {col["name"] for col in inspector.get_columns(table_name)}


def _index_exists(table_name: str, index_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return index_name in {idx["name"] for idx in inspector.get_indexes(table_name)}


def upgrade() -> None:
    # Add new columns to analytics_events table
    if not _column_exists("analytics_events", "session_id"):
        op.add_column(
            "analytics_events",
            sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=True),
        )
    
    if not _column_exists("analytics_events", "cohort"):
        op.add_column(
            "analytics_events",
            sa.Column("cohort", sa.String(length=50), nullable=True),
        )
    
    if not _column_exists("analytics_events", "event_category"):
        op.add_column(
            "analytics_events",
            sa.Column("event_category", sa.String(length=50), nullable=True),
        )
    
    if not _column_exists("analytics_events", "device_info"):
        op.add_column(
            "analytics_events",
            sa.Column("device_info", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        )
    
    # Create indexes for new columns
    if not _index_exists("analytics_events", "idx_analytics_session"):
        op.create_index(
            "idx_analytics_session",
            "analytics_events",
            ["session_id"],
        )
    
    if not _index_exists("analytics_events", "idx_analytics_category"):
        op.create_index(
            "idx_analytics_category",
            "analytics_events",
            ["event_category"],
        )
    
    if not _index_exists("analytics_events", "idx_analytics_cohort"):
        op.create_index(
            "idx_analytics_cohort",
            "analytics_events",
            ["cohort"],
        )


def downgrade() -> None:
    # Drop indexes
    if _index_exists("analytics_events", "idx_analytics_cohort"):
        op.drop_index("idx_analytics_cohort", table_name="analytics_events")
    
    if _index_exists("analytics_events", "idx_analytics_category"):
        op.drop_index("idx_analytics_category", table_name="analytics_events")
    
    if _index_exists("analytics_events", "idx_analytics_session"):
        op.drop_index("idx_analytics_session", table_name="analytics_events")
    
    # Drop columns
    if _column_exists("analytics_events", "device_info"):
        op.drop_column("analytics_events", "device_info")
    
    if _column_exists("analytics_events", "event_category"):
        op.drop_column("analytics_events", "event_category")
    
    if _column_exists("analytics_events", "cohort"):
        op.drop_column("analytics_events", "cohort")
    
    if _column_exists("analytics_events", "session_id"):
        op.drop_column("analytics_events", "session_id")

