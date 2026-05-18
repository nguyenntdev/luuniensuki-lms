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


def upgrade() -> None:
    # Create content_status enum type
    op.execute(
        """
        CREATE TYPE content_status AS ENUM ('draft', 'review', 'published', 'archived');
        """
    )

    # Add review workflow fields to lesson_content
    op.add_column(
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
    op.add_column(
        "lesson_content",
        sa.Column(
            "submitted_for_review_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "lesson_content",
        sa.Column(
            "reviewed_by_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )
    op.add_column(
        "lesson_content",
        sa.Column(
            "reviewed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "lesson_content",
        sa.Column(
            "review_notes",
            sa.Text(),
            nullable=True,
        ),
    )
    op.create_foreign_key(
        "fk_lesson_content_reviewed_by",
        "lesson_content",
        "users",
        ["reviewed_by_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # Add review workflow fields to quiz_questions
    op.add_column(
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
    op.add_column(
        "quiz_questions",
        sa.Column(
            "submitted_for_review_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "quiz_questions",
        sa.Column(
            "reviewed_by_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )
    op.add_column(
        "quiz_questions",
        sa.Column(
            "reviewed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "quiz_questions",
        sa.Column(
            "review_notes",
            sa.Text(),
            nullable=True,
        ),
    )
    op.add_column(
        "quiz_questions",
        sa.Column(
            "created_by_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )
    op.create_foreign_key(
        "fk_quiz_questions_reviewed_by",
        "quiz_questions",
        "users",
        ["reviewed_by_id"],
        ["id"],
        ondelete="SET NULL",
    )
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
    op.execute("DROP TYPE content_status;")


