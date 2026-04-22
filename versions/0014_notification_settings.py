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


def upgrade() -> None:
    # Add push_permission_prompted to users table
    op.add_column(
        'users',
        sa.Column(
            'push_permission_prompted',
            sa.Boolean(),
            nullable=False,
            server_default=sa.text('false')
        )
    )

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

