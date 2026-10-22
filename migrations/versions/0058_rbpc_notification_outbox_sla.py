"""add rbpc_notification_outbox table and sla_due_at column

Revision ID: 0058_rbpc_notification_outbox_sla
Revises: 0057_merge_all_heads
Create Date: 2026-10-21 12:00:00.000000

V5-T019: Real notification outbox queue and partner SLA tracking.
Strictly additive: creates rbpc_notification_outbox table, adds sla_due_at column
to rbpc_inquiries, and creates associated indexes.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0058_rbpc_notification_outbox_sla"
down_revision: Union[str, Sequence[str], None] = "0057_merge_all_heads"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add sla_due_at column to rbpc_inquiries
    op.add_column(
        "rbpc_inquiries",
        sa.Column("sla_due_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "idx_rbpc_inquiries_sla",
        "rbpc_inquiries",
        ["sla_due_at"],
    )

    # 2. Create rbpc_notification_outbox table
    op.create_table(
        "rbpc_notification_outbox",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "inquiry_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("rbpc_inquiries.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("event_type", sa.Text(), nullable=False, server_default="inquiry_created"),
        sa.Column("channel", sa.Text(), nullable=False, server_default="email"),
        sa.Column("recipient", sa.Text(), nullable=False),
        sa.Column("recipient_masked", sa.Text(), nullable=True),
        sa.Column("template_code", sa.Text(), nullable=True),
        sa.Column("subject", sa.Text(), nullable=True),
        sa.Column("payload_clean", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("status", sa.Text(), nullable=False, server_default="queued"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        "idx_rbpc_notif_outbox_inquiry",
        "rbpc_notification_outbox",
        ["inquiry_id"],
    )
    op.create_index(
        "idx_rbpc_notif_outbox_status",
        "rbpc_notification_outbox",
        ["status"],
    )
    op.create_index(
        "idx_rbpc_notif_outbox_created",
        "rbpc_notification_outbox",
        ["created_at"],
    )
    op.create_index(
        "idx_rbpc_notif_outbox_retry",
        "rbpc_notification_outbox",
        ["status", "next_retry_at"],
    )


def downgrade() -> None:
    pass
