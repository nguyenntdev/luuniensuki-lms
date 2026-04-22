"""Update feature_flags table with new fields

Revision ID: 0037
Revises: 0036
Create Date: 2025-01-18

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers, used by Alembic.
revision = '0037'
down_revision = '0036'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Remove the old percentage column and add rollout_percentage
    op.drop_constraint('check_percentage_range', 'feature_flags', type_='check')
    op.alter_column('feature_flags', 'percentage', new_column_name='rollout_percentage')
    op.create_check_constraint(
        'check_rollout_percentage_range', 
        'feature_flags', 
        'rollout_percentage >= 0 AND rollout_percentage <= 100'
    )
    
    # Rename allowed_user_ids to user_whitelist
    op.alter_column('feature_flags', 'allowed_user_ids', new_column_name='user_whitelist')
    
    # Add new columns
    op.add_column('feature_flags', sa.Column('user_blacklist', JSONB, nullable=True))
    op.add_column('feature_flags', sa.Column('rules', JSONB, nullable=True))
    op.add_column('feature_flags', sa.Column('created_by_id', UUID(as_uuid=True), nullable=True))
    
    # Add foreign key constraint for created_by_id
    op.create_foreign_key(
        'fk_feature_flags_created_by_id',
        'feature_flags',
        'users',
        ['created_by_id'],
        ['id'],
        ondelete='SET NULL'
    )
    
    # Create index for created_by_id
    op.create_index('idx_feature_flags_created_by', 'feature_flags', ['created_by_id'])
    
    # Remove flag_type column and metadata column as they're no longer needed
    op.drop_column('feature_flags', 'flag_type')
    op.drop_column('feature_flags', 'metadata')


def downgrade() -> None:
    # Add back flag_type and metadata columns
    op.add_column('feature_flags', sa.Column('flag_type', sa.Enum('boolean', 'percentage', 'user_list', name='flag_type'), 
                                             nullable=False, server_default=sa.text("'boolean'")))
    op.add_column('feature_flags', sa.Column('metadata', JSONB, nullable=True))
    
    # Drop index and foreign key
    op.drop_index('idx_feature_flags_created_by', table_name='feature_flags')
    op.drop_constraint('fk_feature_flags_created_by_id', 'feature_flags', type_='foreignkey')
    
    # Remove new columns
    op.drop_column('feature_flags', 'created_by_id')
    op.drop_column('feature_flags', 'rules')
    op.drop_column('feature_flags', 'user_blacklist')
    
    # Rename user_whitelist back to allowed_user_ids
    op.alter_column('feature_flags', 'user_whitelist', new_column_name='allowed_user_ids')
    
    # Rename rollout_percentage back to percentage
    op.drop_constraint('check_rollout_percentage_range', 'feature_flags', type_='check')
    op.alter_column('feature_flags', 'rollout_percentage', new_column_name='percentage')
    op.create_check_constraint('check_percentage_range', 'feature_flags', 'percentage >= 0 AND percentage <= 100')

