"""Add created_by_id and target_audience to experiments

Revision ID: 0036
Revises: 0035
Create Date: 2025-01-20

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0036'
down_revision = '0035'
branch_labels = None
depends_on = None


def upgrade():
    # Add created_by_id column to experiments table
    op.add_column('experiments', sa.Column('created_by_id', postgresql.UUID(as_uuid=True), nullable=True))
    
    # Add target_audience column to experiments table
    op.add_column('experiments', sa.Column('target_audience', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    
    # Create foreign key constraint for created_by_id
    op.create_foreign_key(
        'fk_experiments_created_by_id_users',
        'experiments', 
        'users',
        ['created_by_id'], 
        ['id'],
        ondelete='SET NULL'
    )
    
    # Create index on created_by_id for better query performance
    op.create_index('idx_experiments_created_by', 'experiments', ['created_by_id'])


def downgrade():
    # Remove index
    op.drop_index('idx_experiments_created_by', table_name='experiments')
    
    # Remove foreign key constraint
    op.drop_constraint('fk_experiments_created_by_id_users', 'experiments', type_='foreignkey')
    
    # Remove columns
    op.drop_column('experiments', 'target_audience')
    op.drop_column('experiments', 'created_by_id')

