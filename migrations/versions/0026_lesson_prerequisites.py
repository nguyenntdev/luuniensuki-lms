"""add lesson prerequisites and sequence fields

Revision ID: 0026_lesson_prerequisites
Revises: 0025_adaptive_quiz
Create Date: 2025-01-20 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0026_lesson_prerequisites'
down_revision: Union[str, None] = '0025_adaptive_quiz'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(table_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return table_name in inspector.get_table_names()


def _column_exists(table_name: str, column_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    if table_name not in inspector.get_table_names():
        return False
    return column_name in {c['name'] for c in inspector.get_columns(table_name)}


def _add_column_if_missing(table_name: str, column: sa.Column) -> None:
    if not _column_exists(table_name, column.name):
        op.add_column(table_name, column)


def _index_exists(table_name: str, index_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    if table_name not in inspector.get_table_names():
        return False
    return index_name in {i['name'] for i in inspector.get_indexes(table_name)}


def upgrade() -> None:
    # Add difficulty_level and estimated_time_minutes to lesson_content
    _add_column_if_missing(
        'lesson_content',
        sa.Column('difficulty_level', sa.Integer(), nullable=True)
    )
    _add_column_if_missing(
        'lesson_content',
        sa.Column('estimated_time_minutes', sa.Integer(), nullable=True)
    )

    if not _table_exists('lesson_prerequisites'):
        # Create lesson_prerequisites table
        op.create_table(
            'lesson_prerequisites',
            sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('lesson_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('prerequisite_lesson_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('is_strict', sa.Boolean(), server_default=sa.text('true'), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(['lesson_id'], ['lesson_content.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['prerequisite_lesson_id'], ['lesson_content.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('lesson_id', 'prerequisite_lesson_id', name='uq_lesson_prereq_lesson_prereq')
        )
    if not _index_exists('lesson_prerequisites', 'idx_lesson_prereq_lesson'):
        op.create_index('idx_lesson_prereq_lesson', 'lesson_prerequisites', ['lesson_id'])
    if not _index_exists('lesson_prerequisites', 'idx_lesson_prereq_prerequisite'):
        op.create_index('idx_lesson_prereq_prerequisite', 'lesson_prerequisites', ['prerequisite_lesson_id'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_lesson_prereq_prerequisite', table_name='lesson_prerequisites')
    op.drop_index('idx_lesson_prereq_lesson', table_name='lesson_prerequisites')
    
    # Drop lesson_prerequisites table
    op.drop_table('lesson_prerequisites')
    
    # Drop columns from lesson_content
    op.drop_column('lesson_content', 'estimated_time_minutes')
    op.drop_column('lesson_content', 'difficulty_level')

