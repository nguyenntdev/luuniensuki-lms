"""Add experiments, feature flags, and experiment events

Revision ID: 0033
Revises: 0032
Create Date: 2025-01-18

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers, used by Alembic.
revision = '0033'
down_revision = '0032'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create flag_type enum
    op.execute("CREATE TYPE flag_type AS ENUM ('boolean', 'percentage', 'user_list')")
    
    # Create feature_flags table
    op.create_table(
        'feature_flags',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('key', sa.String(100), nullable=False, unique=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('flag_type', sa.Enum('boolean', 'percentage', 'user_list', name='flag_type'), 
                  nullable=False, server_default=sa.text("'boolean'")),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('percentage', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('allowed_user_ids', JSONB, nullable=True),
        sa.Column('metadata', JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.CheckConstraint('percentage >= 0 AND percentage <= 100', name='check_percentage_range'),
    )
    
    # Create indexes for feature_flags
    op.create_index('idx_feature_flags_key', 'feature_flags', ['key'])
    op.create_index('idx_feature_flags_enabled', 'feature_flags', ['is_enabled'])
    
    # Create experiments table
    op.create_table(
        'experiments',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('key', sa.String(100), nullable=False, unique=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('variants', JSONB, nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('start_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('end_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    
    # Create indexes for experiments
    op.create_index('idx_experiments_key', 'experiments', ['key'])
    op.create_index('idx_experiments_active', 'experiments', ['is_active'])
    
    # Create user_experiment_assignments table
    op.create_table(
        'user_experiment_assignments',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False),
        sa.Column('experiment_id', UUID(as_uuid=True), nullable=False),
        sa.Column('variant_key', sa.String(100), nullable=False),
        sa.Column('assigned_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['experiment_id'], ['experiments.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('user_id', 'experiment_id', name='uq_user_experiment_assignment'),
    )
    
    # Create indexes for user_experiment_assignments
    op.create_index('idx_user_experiment_assignments_user', 'user_experiment_assignments', ['user_id'])
    op.create_index('idx_user_experiment_assignments_experiment', 'user_experiment_assignments', ['experiment_id'])
    
    # Create experiment_events table
    op.create_table(
        'experiment_events',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('experiment_id', UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False),
        sa.Column('assignment_id', UUID(as_uuid=True), nullable=False),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('event_name', sa.String(100), nullable=False),
        sa.Column('event_value', sa.Float(), nullable=True),
        sa.Column('metadata', JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['experiment_id'], ['experiments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['assignment_id'], ['user_experiment_assignments.id'], ondelete='CASCADE'),
    )
    
    # Create indexes for experiment_events
    op.create_index('idx_experiment_events_experiment', 'experiment_events', ['experiment_id'])
    op.create_index('idx_experiment_events_user', 'experiment_events', ['user_id'])
    op.create_index('idx_experiment_events_assignment', 'experiment_events', ['assignment_id'])
    op.create_index('idx_experiment_events_type', 'experiment_events', ['event_type'])
    op.create_index('idx_experiment_events_created', 'experiment_events', ['created_at'])


def downgrade() -> None:
    # Drop experiment_events table and indexes
    op.drop_index('idx_experiment_events_created', table_name='experiment_events')
    op.drop_index('idx_experiment_events_type', table_name='experiment_events')
    op.drop_index('idx_experiment_events_assignment', table_name='experiment_events')
    op.drop_index('idx_experiment_events_user', table_name='experiment_events')
    op.drop_index('idx_experiment_events_experiment', table_name='experiment_events')
    op.drop_table('experiment_events')
    
    # Drop user_experiment_assignments table and indexes
    op.drop_index('idx_user_experiment_assignments_experiment', table_name='user_experiment_assignments')
    op.drop_index('idx_user_experiment_assignments_user', table_name='user_experiment_assignments')
    op.drop_table('user_experiment_assignments')
    
    # Drop experiments table and indexes
    op.drop_index('idx_experiments_active', table_name='experiments')
    op.drop_index('idx_experiments_key', table_name='experiments')
    op.drop_table('experiments')
    
    # Drop feature_flags table and indexes
    op.drop_index('idx_feature_flags_enabled', table_name='feature_flags')
    op.drop_index('idx_feature_flags_key', table_name='feature_flags')
    op.drop_table('feature_flags')
    
    # Drop flag_type enum
    op.execute('DROP TYPE flag_type')

