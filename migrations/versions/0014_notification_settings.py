"""Add user notification settings and push permission tracking

Revision ID: 0014
Revises: 0013
Create Date: 2025-01-17

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision = '0014'
down_revision = '0013_review_workflow'
branch_label = None
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


def upgrade() -> None:
    # Add push_permission_prompted to users table
    _add_column_if_missing(
        'users',
        sa.Column(
            'push_permission_prompted',
            sa.Boolean(),
            nullable=False,
            server_default=sa.text('false')
        )
    )

    if not _table_exists('user_notification_settings'):
        # Create user_notification_settings table
        op.create_table(
            'user_notification_settings',
            sa.Column('id', UUID(as_uuid=True), primary_key=True),
            sa.Column('user_id', UUID(as_uuid=True), nullable=False),
            sa.Column('push_enabled', sa.Boolean(), nullable=False, server_default=sa.text('false')),
            sa.Column('push_token', sa.Text(), nullable=True),
            sa.Column('push_platform', sa.String(20), nullable=True),
            sa.Column('email_enabled', sa.Boolean(), nullable=False, server_default=sa.text('true')),
            sa.Column('streak_reminders', sa.Boolean(), nullable=False, server_default=sa.text('true')),
            sa.Column('daily_mission_reminders', sa.Boolean(), nullable=False, server_default=sa.text('true')),
            sa.Column('weekly_digest', sa.Boolean(), nullable=False, server_default=sa.text('true')),
            sa.Column('marketing_enabled', sa.Boolean(), nullable=False, server_default=sa.text('false')),
            sa.Column('quiet_hours_start', sa.Integer(), nullable=True),
            sa.Column('quiet_hours_end', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.UniqueConstraint('user_id', name='uq_notification_settings_user')
        )

    # Create index on user_id
    if not _index_exists('user_notification_settings', 'idx_notification_settings_user'):
        op.create_index(
            'idx_notification_settings_user',
            'user_notification_settings',
            ['user_id']
        )


def downgrade() -> None:
    # Drop notification settings table and index
    op.drop_index('idx_notification_settings_user', table_name='user_notification_settings')
    op.drop_table('user_notification_settings')
    
    # Remove push_permission_prompted column from users
    op.drop_column('users', 'push_permission_prompted')

