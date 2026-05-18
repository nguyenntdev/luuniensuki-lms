from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# Timestamp: 2025-12-18 19:30:00
revision = "0004_urn_exams"
down_revision = "0003_add_username"
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


def _foreign_key_exists(table_name: str, fk_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return fk_name in {fk["name"] for fk in inspector.get_foreign_keys(table_name)}


def upgrade() -> None:
    if not _table_exists("urn_exams"):
        op.create_table(
            "urn_exams",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("urn_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column(
                "questions", postgresql.JSONB(astext_type=sa.Text()), nullable=False
            ),
            sa.Column(
                "passing_score",
                sa.Integer(),
                server_default=sa.text("80"),
                nullable=False,
            ),
            sa.Column(
                "xp_reward", sa.Integer(), server_default=sa.text("100"), nullable=False
            ),
            sa.ForeignKeyConstraint(["urn_id"], ["urns.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
    if not _index_exists("urn_exams", "idx_urn_exams_urn"):
        op.create_index("idx_urn_exams_urn", "urn_exams", ["urn_id"])

    if not _table_exists("urn_exam_attempts"):
        op.create_table(
            "urn_exam_attempts",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("urn_exam_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("score", sa.Integer(), nullable=False),
            sa.Column("passed", sa.Boolean(), nullable=False),
            sa.Column("time_taken", sa.Integer(), nullable=False),
            sa.Column(
                "answers", postgresql.JSONB(astext_type=sa.Text()), nullable=False
            ),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(
                ["urn_exam_id"], ["urn_exams.id"], ondelete="CASCADE"
            ),
            sa.PrimaryKeyConstraint("id"),
        )
    if not _index_exists("urn_exam_attempts", "idx_urn_exam_attempts_user"):
        op.create_index("idx_urn_exam_attempts_user", "urn_exam_attempts", ["user_id"])
    if not _index_exists("urn_exam_attempts", "idx_urn_exam_attempts_exam"):
        op.create_index(
            "idx_urn_exam_attempts_exam", "urn_exam_attempts", ["urn_exam_id"]
        )
    if not _index_exists("urn_exam_attempts", "idx_urn_exam_attempts_passed"):
        op.create_index("idx_urn_exam_attempts_passed", "urn_exam_attempts", ["passed"])

    if not _column_exists("quiz_questions", "urn_id"):
        op.add_column(
            "quiz_questions",
            sa.Column("urn_id", postgresql.UUID(as_uuid=True), nullable=True),
        )
    if not _foreign_key_exists("quiz_questions", "fk_quiz_questions_urn_id"):
        op.create_foreign_key(
            "fk_quiz_questions_urn_id",
            "quiz_questions",
            "urns",
            ["urn_id"],
            ["id"],
            ondelete="CASCADE",
        )


def downgrade() -> None:
    if _foreign_key_exists("quiz_questions", "fk_quiz_questions_urn_id"):
        op.drop_constraint(
            "fk_quiz_questions_urn_id", "quiz_questions", type_="foreignkey"
        )
    if _column_exists("quiz_questions", "urn_id"):
        op.drop_column("quiz_questions", "urn_id")

    if _index_exists("urn_exam_attempts", "idx_urn_exam_attempts_passed"):
        op.drop_index("idx_urn_exam_attempts_passed", table_name="urn_exam_attempts")
    if _index_exists("urn_exam_attempts", "idx_urn_exam_attempts_exam"):
        op.drop_index("idx_urn_exam_attempts_exam", table_name="urn_exam_attempts")
    if _index_exists("urn_exam_attempts", "idx_urn_exam_attempts_user"):
        op.drop_index("idx_urn_exam_attempts_user", table_name="urn_exam_attempts")
    if _table_exists("urn_exam_attempts"):
        op.drop_table("urn_exam_attempts")

    if _index_exists("urn_exams", "idx_urn_exams_urn"):
        op.drop_index("idx_urn_exams_urn", table_name="urn_exams")
    if _table_exists("urn_exams"):
        op.drop_table("urn_exams")
