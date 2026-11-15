"""Add session transcript, summary, and action tables for live sessions

Revision ID: 0040
Revises: 0039
Create Date: 2026-04-22

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "0040"
down_revision: Union[str, None] = "0039"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(table_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return table_name in inspector.get_table_names()


def _index_exists(table_name: str, index_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    if table_name not in inspector.get_table_names():
        return False
    return index_name in {i["name"] for i in inspector.get_indexes(table_name)}


def upgrade() -> None:
    if not _table_exists("session_transcripts"):
        op.create_table(
            "session_transcripts",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("live_session_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("source_event_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("speaker_type", sa.String(length=20), nullable=False),
            sa.Column("speaker_identity", sa.String(length=191), nullable=True),
            sa.Column("speaker_user_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("content_encrypted", sa.Text(), nullable=False),
            sa.Column("confidence", sa.Float(), nullable=True),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("transcript_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["live_session_id"], ["live_sessions.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["source_event_id"], ["live_events.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["speaker_user_id"], ["users.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "live_session_id",
                "source_event_id",
                name="uq_session_transcripts_source_event",
            ),
        )
    if not _index_exists("session_transcripts", "idx_session_transcripts_session"):
        op.create_index("idx_session_transcripts_session", "session_transcripts", ["live_session_id"])
    if not _index_exists("session_transcripts", "idx_session_transcripts_speaker"):
        op.create_index("idx_session_transcripts_speaker", "session_transcripts", ["speaker_type"])
    if not _index_exists("session_transcripts", "idx_session_transcripts_created_at"):
        op.create_index("idx_session_transcripts_created_at", "session_transcripts", ["created_at"])
    if not _index_exists("session_transcripts", "idx_session_transcripts_session_created_at"):
        op.create_index(
            "idx_session_transcripts_session_created_at",
            "session_transcripts",
            ["live_session_id", "created_at"],
        )
    if not _index_exists("session_transcripts", "idx_session_transcripts_expires_at"):
        op.create_index("idx_session_transcripts_expires_at", "session_transcripts", ["expires_at"])

    if not _table_exists("session_summaries"):
        op.create_table(
            "session_summaries",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("live_session_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("summary_encrypted", sa.Text(), nullable=False),
            sa.Column("highlights", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column("citations", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column("rubric_overview", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column("summary_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column(
                "created_by",
                sa.String(length=40),
                server_default=sa.text("'ai_teacher_pipeline'"),
                nullable=False,
            ),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["live_session_id"], ["live_sessions.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
    if not _index_exists("session_summaries", "idx_session_summaries_session"):
        op.create_index("idx_session_summaries_session", "session_summaries", ["live_session_id"])
    if not _index_exists("session_summaries", "idx_session_summaries_created_at"):
        op.create_index("idx_session_summaries_created_at", "session_summaries", ["created_at"])
    if not _index_exists("session_summaries", "idx_session_summaries_expires_at"):
        op.create_index("idx_session_summaries_expires_at", "session_summaries", ["expires_at"])

    if not _table_exists("session_actions"):
        op.create_table(
            "session_actions",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("live_session_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("action_type", sa.String(length=40), nullable=False),
            sa.Column("actor_identity", sa.String(length=191), nullable=True),
            sa.Column("actor_user_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column(
                "status",
                sa.String(length=20),
                server_default=sa.text("'open'"),
                nullable=False,
            ),
            sa.Column("cost_usd", sa.Numeric(12, 6), nullable=True),
            sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["live_session_id"], ["live_sessions.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
        )
    if not _index_exists("session_actions", "idx_session_actions_session"):
        op.create_index("idx_session_actions_session", "session_actions", ["live_session_id"])
    if not _index_exists("session_actions", "idx_session_actions_type"):
        op.create_index("idx_session_actions_type", "session_actions", ["action_type"])
    if not _index_exists("session_actions", "idx_session_actions_created_at"):
        op.create_index("idx_session_actions_created_at", "session_actions", ["created_at"])
    if not _index_exists("session_actions", "idx_session_actions_expires_at"):
        op.create_index("idx_session_actions_expires_at", "session_actions", ["expires_at"])


def downgrade() -> None:
    op.drop_index("idx_session_actions_expires_at", table_name="session_actions")
    op.drop_index("idx_session_actions_created_at", table_name="session_actions")
    op.drop_index("idx_session_actions_type", table_name="session_actions")
    op.drop_index("idx_session_actions_session", table_name="session_actions")
    op.drop_table("session_actions")

    op.drop_index("idx_session_summaries_expires_at", table_name="session_summaries")
    op.drop_index("idx_session_summaries_created_at", table_name="session_summaries")
    op.drop_index("idx_session_summaries_session", table_name="session_summaries")
    op.drop_table("session_summaries")

    op.drop_index("idx_session_transcripts_expires_at", table_name="session_transcripts")
    op.drop_index("idx_session_transcripts_session_created_at", table_name="session_transcripts")
    op.drop_index("idx_session_transcripts_created_at", table_name="session_transcripts")
    op.drop_index("idx_session_transcripts_speaker", table_name="session_transcripts")
    op.drop_index("idx_session_transcripts_session", table_name="session_transcripts")
    op.drop_table("session_transcripts")
