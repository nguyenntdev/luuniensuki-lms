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


def upgrade() -> None:
    # Add difficulty_level and estimated_time_minutes to lesson_content
    op.add_column(
        'lesson_content',
        sa.Column('difficulty_level', sa.Integer(), nullable=True)
    )
    op.add_column(
        'lesson_content',
        sa.Column('estimated_time_minutes', sa.Integer(), nullable=True)
    )
    
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
    op.create_index('idx_lesson_prereq_lesson', 'lesson_prerequisites', ['lesson_id'])
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

