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


def _constraint_exists(table_name: str, constraint_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    if table_name not in inspector.get_table_names():
        return False
    fks = {fk['name'] for fk in inspector.get_foreign_keys(table_name)}
    uqs = {uq['name'] for uq in inspector.get_unique_constraints(table_name)}
    cks = {ck['name'] for ck in inspector.get_check_constraints(table_name)}
    return constraint_name in (fks | uqs | cks)


def upgrade() -> None:
    if not _table_exists('feature_flags'):
        return

    # Legacy pre-freeze shape: rename percentage -> rollout_percentage and
    # swap the matching CHECK constraints. On a fresh database the table is
    # created by 0001 directly in the final shape, so these are no-ops.
    if _column_exists('feature_flags', 'percentage'):
        if _constraint_exists('feature_flags', 'check_percentage_range'):
            op.drop_constraint('check_percentage_range', 'feature_flags', type_='check')
        op.alter_column('feature_flags', 'percentage', new_column_name='rollout_percentage')
    if _column_exists('feature_flags', 'rollout_percentage') and not _constraint_exists(
        'feature_flags', 'check_rollout_percentage_range'
    ):
        op.create_check_constraint(
            'check_rollout_percentage_range',
            'feature_flags',
            'rollout_percentage >= 0 AND rollout_percentage <= 100'
        )

    # Rename allowed_user_ids to user_whitelist
    if _column_exists('feature_flags', 'allowed_user_ids'):
        op.alter_column('feature_flags', 'allowed_user_ids', new_column_name='user_whitelist')

    # Add new columns
    _add_column_if_missing('feature_flags', sa.Column('user_blacklist', JSONB, nullable=True))
    _add_column_if_missing('feature_flags', sa.Column('rules', JSONB, nullable=True))
    _add_column_if_missing('feature_flags', sa.Column('created_by_id', UUID(as_uuid=True), nullable=True))

    # Add foreign key constraint for created_by_id
    if not _constraint_exists('feature_flags', 'fk_feature_flags_created_by_id'):
        op.create_foreign_key(
            'fk_feature_flags_created_by_id',
            'feature_flags',
            'users',
            ['created_by_id'],
            ['id'],
            ondelete='SET NULL'
        )

    # Create index for created_by_id
    if not _index_exists('feature_flags', 'idx_feature_flags_created_by'):
        op.create_index('idx_feature_flags_created_by', 'feature_flags', ['created_by_id'])

    # Remove flag_type column and metadata column as they're no longer needed
    if _column_exists('feature_flags', 'flag_type'):
        op.drop_column('feature_flags', 'flag_type')
    if _column_exists('feature_flags', 'metadata'):
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

