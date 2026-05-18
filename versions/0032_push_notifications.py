"""Add push notifications table

Revision ID: 0032
Revises: 0031
Create Date: 2025-01-18

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers, used by Alembic.
revision = '0032'
down_revision = '0031_social_features'
branch_label = None
depends_on = None


def upgrade() -> None:
    # Create push_notifications table
    op.create_table(
        'push_notifications',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('notification_type', sa.String(50), nullable=False),
        sa.Column('data_payload', JSONB, nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default=sa.text("'pending'")),
        sa.Column('scheduled_for', sa.DateTime(timezone=True), nullable=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )

    # Create indexes
    op.create_index(
        'idx_push_notifications_user',
        'push_notifications',
        ['user_id']
    )
    op.create_index(
        'idx_push_notifications_status',
        'push_notifications',
        ['status']
    )
    op.create_index(
        'idx_push_notifications_scheduled',
        'push_notifications',
        ['scheduled_for']
    )
    op.create_index(
        'idx_push_notifications_user_created',
        'push_notifications',
        ['user_id', 'created_at']
    )
    op.create_index(
        'idx_push_notifications_type',
        'push_notifications',
        ['notification_type']
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_push_notifications_type', table_name='push_notifications')
    op.drop_index('idx_push_notifications_user_created', table_name='push_notifications')
    op.drop_index('idx_push_notifications_scheduled', table_name='push_notifications')
    op.drop_index('idx_push_notifications_status', table_name='push_notifications')
    op.drop_index('idx_push_notifications_user', table_name='push_notifications')
    
    # Drop table
    op.drop_table('push_notifications')

