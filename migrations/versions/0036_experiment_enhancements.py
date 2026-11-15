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


def upgrade():
    # Add created_by_id column to experiments table
    _add_column_if_missing(
        'experiments',
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True), nullable=True)
    )

    # Add target_audience column to experiments table
    _add_column_if_missing(
        'experiments',
        sa.Column('target_audience', postgresql.JSONB(astext_type=sa.Text()), nullable=True)
    )

    # Create foreign key constraint for created_by_id
    if not _constraint_exists('experiments', 'fk_experiments_created_by_id_users'):
        op.create_foreign_key(
            'fk_experiments_created_by_id_users',
            'experiments',
            'users',
            ['created_by_id'],
            ['id'],
            ondelete='SET NULL'
        )

    # Create index on created_by_id for better query performance
    if not _index_exists('experiments', 'idx_experiments_created_by'):
        op.create_index('idx_experiments_created_by', 'experiments', ['created_by_id'])


def downgrade():
    # Remove index
    op.drop_index('idx_experiments_created_by', table_name='experiments')
    
    # Remove foreign key constraint
    op.drop_constraint('fk_experiments_created_by_id_users', 'experiments', type_='foreignkey')
    
    # Remove columns
    op.drop_column('experiments', 'target_audience')
    op.drop_column('experiments', 'created_by_id')

