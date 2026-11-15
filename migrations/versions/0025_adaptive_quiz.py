"""add adaptive quiz and user skill levels

Revision ID: 0025_adaptive_quiz
Revises: 0024_spaced_repetition
Create Date: 2025-01-20 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0025_adaptive_quiz'
down_revision: Union[str, None] = '0024_spaced_repetition'
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
    # Add skill_type column to quiz_questions table
    _add_column_if_missing(
        'quiz_questions',
        sa.Column('skill_type', sa.String(length=50), nullable=True)
    )

    if not _table_exists('user_skill_levels'):
        # Create user_skill_levels table
        op.create_table(
            'user_skill_levels',
            sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('skill_type', sa.String(length=50), nullable=False),
            sa.Column('skill_level', sa.Float(), server_default=sa.text('0.5'), nullable=False),
            sa.Column('total_questions', sa.Integer(), server_default=sa.text('0'), nullable=False),
            sa.Column('correct_answers', sa.Integer(), server_default=sa.text('0'), nullable=False),
            sa.Column('last_updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('user_id', 'skill_type', name='uq_user_skill')
        )
    if not _index_exists('user_skill_levels', 'idx_user_skill_user'):
        op.create_index('idx_user_skill_user', 'user_skill_levels', ['user_id'])
    if not _index_exists('user_skill_levels', 'idx_user_skill_type'):
        op.create_index('idx_user_skill_type', 'user_skill_levels', ['skill_type'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_user_skill_type', table_name='user_skill_levels')
    op.drop_index('idx_user_skill_user', table_name='user_skill_levels')
    
    # Drop user_skill_levels table
    op.drop_table('user_skill_levels')
    
    # Drop skill_type column from quiz_questions
    op.drop_column('quiz_questions', 'skill_type')

