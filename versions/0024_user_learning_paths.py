"""Add user learning paths table

Revision ID: 0024_user_learning_paths
Revises: 0023_hearts_system
Create Date: 2025-01-16 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0024_user_learning_paths'
down_revision: Union[str, None] = '0023_hearts_system'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create user_learning_paths table
    op.create_table(
        'user_learning_paths',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('path_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('recommended_lessons', postgresql.JSONB(astext_type=sa.Text()), 
                  nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column('recommended_reviews', postgresql.JSONB(astext_type=sa.Text()), 
                  nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column('recommended_quizzes', postgresql.JSONB(astext_type=sa.Text()), 
                  nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column('estimated_time_minutes', sa.Integer(), 
                  nullable=False, server_default=sa.text('0')),
        sa.Column('completed_items', postgresql.JSONB(astext_type=sa.Text()), 
                  nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column('is_completed', sa.Boolean(), 
                  nullable=False, server_default=sa.text('false')),
        sa.Column('generated_at', sa.DateTime(timezone=True), 
                  nullable=False, server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'path_date', name='uq_user_learning_path_user_date')
    )
    
    # Create indexes
    op.create_index('idx_learning_path_user', 'user_learning_paths', ['user_id'])
    op.create_index('idx_learning_path_date', 'user_learning_paths', ['path_date'])
    op.create_index('idx_learning_path_completed', 'user_learning_paths', ['is_completed'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_learning_path_completed', table_name='user_learning_paths')
    op.drop_index('idx_learning_path_date', table_name='user_learning_paths')
    op.drop_index('idx_learning_path_user', table_name='user_learning_paths')
    
    # Drop table
    op.drop_table('user_learning_paths')

