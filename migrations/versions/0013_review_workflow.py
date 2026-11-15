"""Add review workflow states.

Revision ID: 0013_review_workflow
Revises: 0012_daily_missions
Create Date: 2025-01-17
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0013_review_workflow"
down_revision = "0012_daily_missions"
branch_labels = None
depends_on = None


def _enum_exists(enum_name: str) -> bool:
    bind = op.get_bind()
    return bind.execute(
        sa.text("SELECT 1 FROM pg_type WHERE typname = :name"),
        {"name": enum_name},
    ).first() is not None


def _table_exists(table_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return table_name in inspector.get_table_names()


def _column_exists(table_name: str, column_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    if table_name not in inspector.get_table_names():
        return False
    return column_name in {c["name"] for c in inspector.get_columns(table_name)}


def _add_column_if_missing(table_name: str, column: sa.Column) -> None:
    if not _column_exists(table_name, column.name):
        op.add_column(table_name, column)


def _constraint_exists(table_name: str, constraint_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    if table_name not in inspector.get_table_names():
        return False
    fks = {fk["name"] for fk in inspector.get_foreign_keys(table_name)}
    uqs = {uq["name"] for uq in inspector.get_unique_constraints(table_name)}
    cks = {ck["name"] for ck in inspector.get_check_constraints(table_name)}
    return constraint_name in (fks | uqs | cks)


def upgrade() -> None:
    if not _table_exists("lesson_content") or not _table_exists("quiz_questions"):
        return

    # Create content_status enum type
    if not _enum_exists("content_status"):
        op.execute(
            """
            CREATE TYPE content_status AS ENUM ('draft', 'review', 'published', 'archived');
            """
        )

    # Add review workflow fields to lesson_content
    _add_column_if_missing(
        "lesson_content",
        sa.Column(
            "status",
            postgresql.ENUM(
                "draft", "review", "published", "archived",
                name="content_status",
                create_type=False
            ),
            nullable=False,
            server_default="draft",
        ),
    )
    _add_column_if_missing(
        "lesson_content",
        sa.Column(
            "submitted_for_review_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    _add_column_if_missing(
        "lesson_content",
        sa.Column(
            "reviewed_by_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )
    _add_column_if_missing(
        "lesson_content",
        sa.Column(
            "reviewed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    _add_column_if_missing(
        "lesson_content",
        sa.Column(
            "review_notes",
            sa.Text(),
            nullable=True,
        ),
    )
    if not _constraint_exists("lesson_content", "fk_lesson_content_reviewed_by"):
        op.create_foreign_key(
            "fk_lesson_content_reviewed_by",
            "lesson_content",
            "users",
            ["reviewed_by_id"],
            ["id"],
            ondelete="SET NULL",
        )

    # Add review workflow fields to quiz_questions
    _add_column_if_missing(
        "quiz_questions",
        sa.Column(
            "status",
            postgresql.ENUM(
                "draft", "review", "published", "archived",
                name="content_status",
                create_type=False
            ),
            nullable=False,
            server_default="draft",
        ),
    )
    _add_column_if_missing(
        "quiz_questions",
        sa.Column(
            "submitted_for_review_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    _add_column_if_missing(
        "quiz_questions",
        sa.Column(
            "reviewed_by_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )
    _add_column_if_missing(
        "quiz_questions",
        sa.Column(
            "reviewed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    _add_column_if_missing(
        "quiz_questions",
        sa.Column(
            "review_notes",
            sa.Text(),
            nullable=True,
        ),
    )
    _add_column_if_missing(
        "quiz_questions",
        sa.Column(
            "created_by_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )
    if not _constraint_exists("quiz_questions", "fk_quiz_questions_reviewed_by"):
        op.create_foreign_key(
            "fk_quiz_questions_reviewed_by",
            "quiz_questions",
            "users",
            ["reviewed_by_id"],
            ["id"],
            ondelete="SET NULL",
        )
    if not _constraint_exists("quiz_questions", "fk_quiz_questions_created_by"):
        op.create_foreign_key(
            "fk_quiz_questions_created_by",
            "quiz_questions",
            "users",
            ["created_by_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    # Drop quiz_questions foreign keys and columns
    op.drop_constraint(
        "fk_quiz_questions_created_by", "quiz_questions", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_quiz_questions_reviewed_by", "quiz_questions", type_="foreignkey"
    )
    op.drop_column("quiz_questions", "created_by_id")
    op.drop_column("quiz_questions", "review_notes")
    op.drop_column("quiz_questions", "reviewed_at")
    op.drop_column("quiz_questions", "reviewed_by_id")
    op.drop_column("quiz_questions", "submitted_for_review_at")
    op.drop_column("quiz_questions", "status")

    # Drop lesson_content foreign keys and columns
    op.drop_constraint(
        "fk_lesson_content_reviewed_by", "lesson_content", type_="foreignkey"
    )
    op.drop_column("lesson_content", "review_notes")
    op.drop_column("lesson_content", "reviewed_at")
    op.drop_column("lesson_content", "reviewed_by_id")
    op.drop_column("lesson_content", "submitted_for_review_at")
    op.drop_column("lesson_content", "status")

    # Drop content_status enum type
    if _enum_exists("content_status"):
        op.execute("DROP TYPE content_status;")
