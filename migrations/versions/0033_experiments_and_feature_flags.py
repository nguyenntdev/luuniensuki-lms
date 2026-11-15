"""Add experiments, feature flags, and experiment events

Revision ID: 0033
Revises: 0032
Create Date: 2025-01-18

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, ENUM

# revision identifiers, used by Alembic.
revision = '0033'
down_revision = '0032'
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


def _index_exists(table_name: str, index_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    if table_name not in inspector.get_table_names():
        return False
    return index_name in {i['name'] for i in inspector.get_indexes(table_name)}


def upgrade() -> None:
    # Create flag_type enum
    if not _enum_exists("flag_type"):
        op.execute("CREATE TYPE flag_type AS ENUM ('boolean', 'percentage', 'user_list')")

    flag_type_enum = ENUM('boolean', 'percentage', 'user_list', name='flag_type', create_type=False)

    if not _table_exists('feature_flags'):
        # Create feature_flags table
        op.create_table(
            'feature_flags',
            sa.Column('id', UUID(as_uuid=True), primary_key=True),
            sa.Column('key', sa.String(100), nullable=False, unique=True),
            sa.Column('name', sa.String(255), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('flag_type', flag_type_enum,
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
    if not _index_exists('feature_flags', 'idx_feature_flags_key'):
        op.create_index('idx_feature_flags_key', 'feature_flags', ['key'])
    if not _index_exists('feature_flags', 'idx_feature_flags_enabled'):
        op.create_index('idx_feature_flags_enabled', 'feature_flags', ['is_enabled'])

    if not _table_exists('experiments'):
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
    if not _index_exists('experiments', 'idx_experiments_key'):
        op.create_index('idx_experiments_key', 'experiments', ['key'])
    if not _index_exists('experiments', 'idx_experiments_active'):
        op.create_index('idx_experiments_active', 'experiments', ['is_active'])

    if not _table_exists('user_experiment_assignments'):
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
    if not _index_exists('user_experiment_assignments', 'idx_user_experiment_assignments_user'):
        op.create_index('idx_user_experiment_assignments_user', 'user_experiment_assignments', ['user_id'])
    if not _index_exists('user_experiment_assignments', 'idx_user_experiment_assignments_experiment'):
        op.create_index('idx_user_experiment_assignments_experiment', 'user_experiment_assignments', ['experiment_id'])

    if not _table_exists('experiment_events'):
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
    if not _index_exists('experiment_events', 'idx_experiment_events_experiment'):
        op.create_index('idx_experiment_events_experiment', 'experiment_events', ['experiment_id'])
    if not _index_exists('experiment_events', 'idx_experiment_events_user'):
        op.create_index('idx_experiment_events_user', 'experiment_events', ['user_id'])
    if not _index_exists('experiment_events', 'idx_experiment_events_assignment'):
        op.create_index('idx_experiment_events_assignment', 'experiment_events', ['assignment_id'])
    if not _index_exists('experiment_events', 'idx_experiment_events_type'):
        op.create_index('idx_experiment_events_type', 'experiment_events', ['event_type'])
    if not _index_exists('experiment_events', 'idx_experiment_events_created'):
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
    if _enum_exists("flag_type"):
        op.execute('DROP TYPE flag_type')
