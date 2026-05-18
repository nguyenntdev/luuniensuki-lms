from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# Timestamp: 2025-12-29 10:45:00
revision = "0008_teacher_classes"
down_revision = "0007_quests"
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


def _foreign_key_exists(table_name: str, fk_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return fk_name in {fk["name"] for fk in inspector.get_foreign_keys(table_name)}


def upgrade() -> None:
    op.execute("ALTER TYPE user_role ADD VALUE IF NOT EXISTS 'teacher'")

    if not _column_exists("lesson_content", "is_published"):
        op.add_column(
            "lesson_content",
            sa.Column(
                "is_published",
                sa.Boolean(),
                server_default=sa.text("true"),
                nullable=False,
            ),
        )

    if not _column_exists("quiz_questions", "is_published"):
        op.add_column(
            "quiz_questions",
            sa.Column(
                "is_published",
                sa.Boolean(),
                server_default=sa.text("true"),
                nullable=False,
            ),
        )

    if not _table_exists("classes"):
        op.create_table(
            "classes",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("teacher_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(["teacher_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
    if not _index_exists("classes", "idx_classes_teacher"):
        op.create_index("idx_classes_teacher", "classes", ["teacher_id"])
    if not _index_exists("classes", "idx_classes_created_at"):
        op.create_index("idx_classes_created_at", "classes", ["created_at"])

    if not _table_exists("class_members"):
        op.create_table(
            "class_members",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("class_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column(
                "role",
                sa.String(length=20),
                server_default=sa.text("'learner'"),
                nullable=False,
            ),
            sa.Column(
                "joined_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(["class_id"], ["classes.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("class_id", "user_id", name="uq_class_members"),
        )
    if not _index_exists("class_members", "idx_class_members_class"):
        op.create_index("idx_class_members_class", "class_members", ["class_id"])
    if not _index_exists("class_members", "idx_class_members_user"):
        op.create_index("idx_class_members_user", "class_members", ["user_id"])

    if not _table_exists("quest_assignments"):
        op.create_table(
            "quest_assignments",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("class_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("quest_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("assigned_by_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column(
                "assigned_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(["class_id"], ["classes.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["quest_id"], ["quests.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["assigned_by_id"], ["users.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
        )
    if not _index_exists("quest_assignments", "idx_assignments_class"):
        op.create_index("idx_assignments_class", "quest_assignments", ["class_id"])
    if not _index_exists("quest_assignments", "idx_assignments_quest"):
        op.create_index("idx_assignments_quest", "quest_assignments", ["quest_id"])

    if not _table_exists("assignment_progress"):
        op.create_table(
            "assignment_progress",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("assignment_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column(
                "status",
                sa.String(length=20),
                server_default=sa.text("'assigned'"),
                nullable=False,
            ),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(
                ["assignment_id"], ["quest_assignments.id"], ondelete="CASCADE"
            ),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "assignment_id", "user_id", name="uq_assignment_progress"
            ),
        )
    if not _index_exists("assignment_progress", "idx_assignment_progress_assignment"):
        op.create_index(
            "idx_assignment_progress_assignment",
            "assignment_progress",
            ["assignment_id"],
        )
    if not _index_exists("assignment_progress", "idx_assignment_progress_user"):
        op.create_index(
            "idx_assignment_progress_user", "assignment_progress", ["user_id"]
        )


def downgrade() -> None:
    if _index_exists("assignment_progress", "idx_assignment_progress_user"):
        op.drop_index(
            "idx_assignment_progress_user", table_name="assignment_progress"
        )
    if _index_exists("assignment_progress", "idx_assignment_progress_assignment"):
        op.drop_index(
            "idx_assignment_progress_assignment", table_name="assignment_progress"
        )
    if _table_exists("assignment_progress"):
        op.drop_table("assignment_progress")

    if _index_exists("quest_assignments", "idx_assignments_quest"):
        op.drop_index("idx_assignments_quest", table_name="quest_assignments")
    if _index_exists("quest_assignments", "idx_assignments_class"):
        op.drop_index("idx_assignments_class", table_name="quest_assignments")
    if _table_exists("quest_assignments"):
        op.drop_table("quest_assignments")

    if _index_exists("class_members", "idx_class_members_user"):
        op.drop_index("idx_class_members_user", table_name="class_members")
    if _index_exists("class_members", "idx_class_members_class"):
        op.drop_index("idx_class_members_class", table_name="class_members")
    if _table_exists("class_members"):
        op.drop_table("class_members")

    if _index_exists("classes", "idx_classes_created_at"):
        op.drop_index("idx_classes_created_at", table_name="classes")
    if _index_exists("classes", "idx_classes_teacher"):
        op.drop_index("idx_classes_teacher", table_name="classes")
    if _table_exists("classes"):
        op.drop_table("classes")

    if _column_exists("quiz_questions", "is_published"):
        op.drop_column("quiz_questions", "is_published")
    if _column_exists("lesson_content", "is_published"):
        op.drop_column("lesson_content", "is_published")
