from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# Timestamp: 2025-12-18 19:30:00
revision = "0004_urn_exams"
down_revision = "0003_add_username"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "urn_exams",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("urn_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("questions", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("passing_score", sa.Integer(), server_default=sa.text("80"), nullable=False),
        sa.Column("xp_reward", sa.Integer(), server_default=sa.text("100"), nullable=False),
        sa.ForeignKeyConstraint(["urn_id"], ["urns.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_urn_exams_urn", "urn_exams", ["urn_id"])

    op.create_table(
        "urn_exam_attempts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("urn_exam_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("passed", sa.Boolean(), nullable=False),
        sa.Column("time_taken", sa.Integer(), nullable=False),
        sa.Column("answers", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["urn_exam_id"], ["urn_exams.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_urn_exam_attempts_user", "urn_exam_attempts", ["user_id"])
    op.create_index("idx_urn_exam_attempts_exam", "urn_exam_attempts", ["urn_exam_id"])
    op.create_index("idx_urn_exam_attempts_passed", "urn_exam_attempts", ["passed"])

    op.add_column("quiz_questions", sa.Column("urn_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key("fk_quiz_questions_urn_id", "quiz_questions", "urns", ["urn_id"], ["id"], ondelete="CASCADE")


def downgrade() -> None:
    op.drop_constraint("fk_quiz_questions_urn_id", "quiz_questions", type_="foreignkey")
    op.drop_column("quiz_questions", "urn_id")

    op.drop_index("idx_urn_exam_attempts_passed", table_name="urn_exam_attempts")
    op.drop_index("idx_urn_exam_attempts_exam", table_name="urn_exam_attempts")
    op.drop_index("idx_urn_exam_attempts_user", table_name="urn_exam_attempts")
    op.drop_table("urn_exam_attempts")

    op.drop_index("idx_urn_exams_urn", table_name="urn_exams")
    op.drop_table("urn_exams")

