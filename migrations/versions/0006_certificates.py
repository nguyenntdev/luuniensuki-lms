from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# Timestamp: 2025-12-29 09:30:00
revision = "0006_certificates"
down_revision = "0005_starting_path_analytics"
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


def _constraint_exists(table_name: str, constraint_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return constraint_name in {c["name"] for c in inspector.get_unique_constraints(table_name)}


def upgrade() -> None:
    if not _table_exists("certificates"):
        op.create_table(
            "certificates",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("code", sa.String(length=64), nullable=False),
            sa.Column("issuer_name", sa.String(length=255), nullable=False),
            sa.Column("reason_type", sa.String(length=50), nullable=False),
            sa.Column("reason_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column(
                "status",
                sa.String(length=20),
                server_default=sa.text("'issued'"),
                nullable=False,
            ),
            sa.Column(
                "issued_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )

    if not _constraint_exists("certificates", "uq_certificates_code"):
        op.create_unique_constraint(
            "uq_certificates_code", "certificates", ["code"]
        )
    if not _constraint_exists("certificates", "uq_certificates_reason"):
        op.create_unique_constraint(
            "uq_certificates_reason",
            "certificates",
            ["user_id", "reason_type", "reason_id"],
        )

    if not _index_exists("certificates", "idx_certificates_user"):
        op.create_index("idx_certificates_user", "certificates", ["user_id"])
    if not _index_exists("certificates", "idx_certificates_reason"):
        op.create_index(
            "idx_certificates_reason", "certificates", ["reason_type", "reason_id"]
        )


def downgrade() -> None:
    if _index_exists("certificates", "idx_certificates_reason"):
        op.drop_index("idx_certificates_reason", table_name="certificates")
    if _index_exists("certificates", "idx_certificates_user"):
        op.drop_index("idx_certificates_user", table_name="certificates")
    if _constraint_exists("certificates", "uq_certificates_reason"):
        op.drop_constraint(
            "uq_certificates_reason", "certificates", type_="unique"
        )
    if _constraint_exists("certificates", "uq_certificates_code"):
        op.drop_constraint("uq_certificates_code", "certificates", type_="unique")
    if _table_exists("certificates"):
        op.drop_table("certificates")
