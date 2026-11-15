"""Add user_leaderboard_settings table for leaderboard preferences

Revision ID: 0035
Revises: 0034
Create Date: 2025-01-20

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision = '0035'
down_revision = '0034'
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
    if not _table_exists('user_leaderboard_settings'):
        # Create user_leaderboard_settings table
        op.create_table(
            'user_leaderboard_settings',
            sa.Column('id', UUID(as_uuid=True), primary_key=True),
            sa.Column('user_id', UUID(as_uuid=True), nullable=False, unique=True),
            sa.Column('show_on_global', sa.Boolean(), nullable=False, server_default=sa.text('true')),
            sa.Column('show_real_name', sa.Boolean(), nullable=False, server_default=sa.text('false')),
            sa.Column('preferred_leaderboard', sa.String(20), nullable=False, server_default=sa.text("'global'")),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        )

    # Create index
    if not _index_exists('user_leaderboard_settings', 'idx_user_leaderboard_settings_user'):
        op.create_index('idx_user_leaderboard_settings_user', 'user_leaderboard_settings', ['user_id'])


def downgrade() -> None:
    # Drop index
    op.drop_index('idx_user_leaderboard_settings_user', table_name='user_leaderboard_settings')
    
    # Drop table
    op.drop_table('user_leaderboard_settings')

