"""Add analytics event taxonomy and business conversion ingest fields

Revision ID: 0088_analytics_taxonomy_ingest
Revises: 0087_rbpc_startup_evidence_room
Create Date: 2026-11-07 10:15:00.000000

V5-T111 / W11-A01: Analytics event taxonomy & ingest.
Consent-aware telemetry events with idempotency keys, server-trusted business
conversion events (view, explore, inquiry_start, inquiry_submit, inquiry_confirm),
and zero student PII in payloads.
Negative abuse invariant: Demo/synthetic traffic is never counted as real customer conversion funnel.

Strictly additive:
- Adds idempotency_key column and index to analytics_events
- Adds consent_status column to analytics_events
- Adds is_server_verified column and index to analytics_events
- Adds is_demo column and index to analytics_events
- Adds is_synthetic column and index to analytics_events
- Alters user_id column to nullable for anonymous visitor telemetry
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "0088_analytics_taxonomy_ingest"
down_revision: Union[str, Sequence[str], None] = "0087_rbpc_startup_evidence_room"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_exists(table_name: str, column_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return column_name in {col["name"] for col in inspector.get_columns(table_name)}


def _index_exists(table_name: str, index_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return index_name in {idx["name"] for idx in inspector.get_indexes(table_name)}


def upgrade() -> None:
    # 1. Make user_id nullable for anonymous / unauthenticated visitor telemetry
    op.alter_column(
        "analytics_events",
        "user_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=True,
    )

    # 2. Add idempotency_key
    if not _column_exists("analytics_events", "idempotency_key"):
        op.add_column(
            "analytics_events",
            sa.Column("idempotency_key", sa.String(length=128), nullable=True),
        )

    # 3. Add consent_status
    if not _column_exists("analytics_events", "consent_status"):
        op.add_column(
            "analytics_events",
            sa.Column(
                "consent_status",
                sa.String(length=50),
                nullable=True,
                server_default="consented",
            ),
        )

    # 4. Add is_server_verified
    if not _column_exists("analytics_events", "is_server_verified"):
        op.add_column(
            "analytics_events",
            sa.Column(
                "is_server_verified",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("false"),
            ),
        )

    # 5. Add is_demo
    if not _column_exists("analytics_events", "is_demo"):
        op.add_column(
            "analytics_events",
            sa.Column(
                "is_demo",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("false"),
            ),
        )

    # 6. Add is_synthetic
    if not _column_exists("analytics_events", "is_synthetic"):
        op.add_column(
            "analytics_events",
            sa.Column(
                "is_synthetic",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("false"),
            ),
        )

    # 7. Create indexes
    if not _index_exists("analytics_events", "idx_analytics_idempotency"):
        op.create_index(
            "idx_analytics_idempotency",
            "analytics_events",
            ["idempotency_key"],
        )

    if not _index_exists("analytics_events", "idx_analytics_server_verified"):
        op.create_index(
            "idx_analytics_server_verified",
            "analytics_events",
            ["is_server_verified"],
        )

    if not _index_exists("analytics_events", "idx_analytics_is_demo"):
        op.create_index(
            "idx_analytics_is_demo",
            "analytics_events",
            ["is_demo"],
        )

    if not _index_exists("analytics_events", "idx_analytics_is_synthetic"):
        op.create_index(
            "idx_analytics_is_synthetic",
            "analytics_events",
            ["is_synthetic"],
        )


def downgrade() -> None:
    if _index_exists("analytics_events", "idx_analytics_is_synthetic"):
        op.drop_index("idx_analytics_is_synthetic", table_name="analytics_events")

    if _index_exists("analytics_events", "idx_analytics_is_demo"):
        op.drop_index("idx_analytics_is_demo", table_name="analytics_events")

    if _index_exists("analytics_events", "idx_analytics_server_verified"):
        op.drop_index("idx_analytics_server_verified", table_name="analytics_events")

    if _index_exists("analytics_events", "idx_analytics_idempotency"):
        op.drop_index("idx_analytics_idempotency", table_name="analytics_events")

    if _column_exists("analytics_events", "is_synthetic"):
        op.drop_column("analytics_events", "is_synthetic")

    if _column_exists("analytics_events", "is_demo"):
        op.drop_column("analytics_events", "is_demo")

    if _column_exists("analytics_events", "is_server_verified"):
        op.drop_column("analytics_events", "is_server_verified")

    if _column_exists("analytics_events", "consent_status"):
        op.drop_column("analytics_events", "consent_status")

    if _column_exists("analytics_events", "idempotency_key"):
        op.drop_column("analytics_events", "idempotency_key")
