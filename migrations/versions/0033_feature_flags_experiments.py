"""add feature flags and experiments

Revision ID: 0033_feature_flags_experiments
Revises: 0032_push_notifications
Create Date: 2025-01-20 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0033_feature_flags_experiments'
down_revision: Union[str, None] = '0033'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(table_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return table_name in inspector.get_table_names()


def _index_exists(table_name: str, index_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    if table_name not in inspector.get_table_names():
        return False
    return index_name in {idx["name"] for idx in inspector.get_indexes(table_name)}


def _enum_exists(enum_name: str) -> bool:
    bind = op.get_bind()
    result = bind.execute(
        sa.text("SELECT 1 FROM pg_type WHERE typname = :name"),
        {"name": enum_name},
    ).first()
    return result is not None


def upgrade() -> None:
    # Create flag_type enum
    flag_type_enum = postgresql.ENUM(
        'boolean',
        'percentage',
        'user_list',
        name='flag_type',
        create_type=True
    )
    if not _enum_exists('flag_type'):
        flag_type_enum.create(op.get_bind())

    # Create feature_flags table
    if not _table_exists('feature_flags'):
        op.create_table(
            'feature_flags',
            sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('key', sa.String(100), nullable=False),
            sa.Column('name', sa.String(255), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('flag_type', flag_type_enum, server_default=sa.text("'boolean'"), nullable=False),
            sa.Column('is_enabled', sa.Boolean(), server_default=sa.text('false'), nullable=False),
            sa.Column('percentage', sa.Integer(), server_default=sa.text('0'), nullable=False),
            sa.Column('allowed_user_ids', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('key'),
            sa.CheckConstraint('percentage >= 0 AND percentage <= 100', name='check_percentage_range')
        )
        op.create_index('idx_feature_flags_key', 'feature_flags', ['key'])
        op.create_index('idx_feature_flags_enabled', 'feature_flags', ['is_enabled'])

    # Create experiments table
    if not _table_exists('experiments'):
        op.create_table(
            'experiments',
            sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('key', sa.String(100), nullable=False),
            sa.Column('name', sa.String(255), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('variants', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
            sa.Column('is_active', sa.Boolean(), server_default=sa.text('false'), nullable=False),
            sa.Column('start_date', sa.DateTime(timezone=True), nullable=True),
            sa.Column('end_date', sa.DateTime(timezone=True), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('key')
        )
        op.create_index('idx_experiments_key', 'experiments', ['key'])
        op.create_index('idx_experiments_active', 'experiments', ['is_active'])

    # Create user_experiment_assignments table
    if not _table_exists('user_experiment_assignments'):
        op.create_table(
            'user_experiment_assignments',
            sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('experiment_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('variant_key', sa.String(100), nullable=False),
            sa.Column('assigned_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['experiment_id'], ['experiments.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('user_id', 'experiment_id', name='uq_user_experiment_assignment')
        )
        op.create_index('idx_user_experiment_assignments_user', 'user_experiment_assignments', ['user_id'])
        op.create_index('idx_user_experiment_assignments_experiment', 'user_experiment_assignments', ['experiment_id'])


def downgrade() -> None:
    # Drop tables
    if _table_exists('user_experiment_assignments'):
        if _index_exists('user_experiment_assignments', 'idx_user_experiment_assignments_experiment'):
            op.drop_index('idx_user_experiment_assignments_experiment', table_name='user_experiment_assignments')
        if _index_exists('user_experiment_assignments', 'idx_user_experiment_assignments_user'):
            op.drop_index('idx_user_experiment_assignments_user', table_name='user_experiment_assignments')
        op.drop_table('user_experiment_assignments')

    if _table_exists('experiments'):
        if _index_exists('experiments', 'idx_experiments_active'):
            op.drop_index('idx_experiments_active', table_name='experiments')
        if _index_exists('experiments', 'idx_experiments_key'):
            op.drop_index('idx_experiments_key', table_name='experiments')
        op.drop_table('experiments')

    if _table_exists('feature_flags'):
        if _index_exists('feature_flags', 'idx_feature_flags_enabled'):
            op.drop_index('idx_feature_flags_enabled', table_name='feature_flags')
        if _index_exists('feature_flags', 'idx_feature_flags_key'):
            op.drop_index('idx_feature_flags_key', table_name='feature_flags')
        op.drop_table('feature_flags')

    # Drop enum
    flag_type_enum = postgresql.ENUM(
        'boolean',
        'percentage',
        'user_list',
        name='flag_type'
    )
    if _enum_exists('flag_type'):
        flag_type_enum.drop(op.get_bind())
