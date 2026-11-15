"""Add experiment_metric_events table for tracking experiment metrics

Revision ID: 0034
Revises: 0033
Create Date: 2025-01-18

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers, used by Alembic.
revision = '0034'
down_revision = '0033'
branch_labels = None
depends_on = None


def _table_exists(table_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return table_name in inspector.get_table_names()


def _index_exists(table_name: str, index_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    if table_name not in inspector.get_table_names():
        return False
    return index_name in {i['name'] for i in inspector.get_indexes(table_name)}


def upgrade() -> None:
    if not _table_exists('experiment_metric_events'):
        # Create experiment_metric_events table
        op.create_table(
            'experiment_metric_events',
            sa.Column('id', UUID(as_uuid=True), primary_key=True),
            sa.Column('experiment_id', UUID(as_uuid=True), nullable=False),
            sa.Column('user_id', UUID(as_uuid=True), nullable=False),
            sa.Column('variant', sa.String(100), nullable=False),
            sa.Column('metric_name', sa.String(100), nullable=False),
            sa.Column('metric_value', sa.Float(), nullable=False),
            sa.Column('metadata', JSONB, nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
            sa.ForeignKeyConstraint(['experiment_id'], ['experiments.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        )

    # Create indexes for experiment_metric_events
    if not _index_exists('experiment_metric_events', 'idx_experiment_metric_events_experiment'):
        op.create_index('idx_experiment_metric_events_experiment', 'experiment_metric_events', ['experiment_id'])
    if not _index_exists('experiment_metric_events', 'idx_experiment_metric_events_user'):
        op.create_index('idx_experiment_metric_events_user', 'experiment_metric_events', ['user_id'])
    if not _index_exists('experiment_metric_events', 'idx_experiment_metric_events_variant'):
        op.create_index('idx_experiment_metric_events_variant', 'experiment_metric_events', ['variant'])
    if not _index_exists('experiment_metric_events', 'idx_experiment_metric_events_metric_name'):
        op.create_index('idx_experiment_metric_events_metric_name', 'experiment_metric_events', ['metric_name'])
    if not _index_exists('experiment_metric_events', 'idx_experiment_metric_events_created'):
        op.create_index('idx_experiment_metric_events_created', 'experiment_metric_events', ['created_at'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_experiment_metric_events_created', table_name='experiment_metric_events')
    op.drop_index('idx_experiment_metric_events_metric_name', table_name='experiment_metric_events')
    op.drop_index('idx_experiment_metric_events_variant', table_name='experiment_metric_events')
    op.drop_index('idx_experiment_metric_events_user', table_name='experiment_metric_events')
    op.drop_index('idx_experiment_metric_events_experiment', table_name='experiment_metric_events')
    
    # Drop table
    op.drop_table('experiment_metric_events')

