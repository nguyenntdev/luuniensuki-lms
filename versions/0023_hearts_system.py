"""add hearts system

Revision ID: 0023_hearts_system
Revises: 0022_guest_preview
Create Date: 2025-01-16 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0023_hearts_system'
down_revision: Union[str, None] = '0022'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create heart_transaction_reason enum
    heart_transaction_reason_enum = postgresql.ENUM(
        'quiz_wrong',
        'heart_purchase',
        'daily_refill',
        'streak_freeze_used',
        'reward',
        'admin_grant',
        'ad_watch',
        'practice_complete',
        name='heart_transaction_reason',
        create_type=True
    )
    heart_transaction_reason_enum.create(op.get_bind())

    # Create user_hearts table
    op.create_table(
        'user_hearts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('current_hearts', sa.Integer(), server_default=sa.text('5'), nullable=False),
        sa.Column('max_hearts', sa.Integer(), server_default=sa.text('5'), nullable=False),
        sa.Column('last_heart_lost_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('hearts_refill_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('unlimited_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('streak_freezes', sa.Integer(), server_default=sa.text('0'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index('idx_user_hearts_user', 'user_hearts', ['user_id'])
    op.create_index('idx_user_hearts_refill', 'user_hearts', ['hearts_refill_at'])

    # Create heart_transactions table
    op.create_table(
        'heart_transactions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_hearts_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('reason', heart_transaction_reason_enum, nullable=False),
        sa.Column('balance_after', sa.Integer(), nullable=False),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_hearts_id'], ['user_hearts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_heart_transactions_user', 'heart_transactions', ['user_id'])
    op.create_index('idx_heart_transactions_reason', 'heart_transactions', ['reason'])
    op.create_index('idx_heart_transactions_created', 'heart_transactions', ['created_at'])


def downgrade() -> None:
    # Drop tables
    op.drop_index('idx_heart_transactions_created', table_name='heart_transactions')
    op.drop_index('idx_heart_transactions_reason', table_name='heart_transactions')
    op.drop_index('idx_heart_transactions_user', table_name='heart_transactions')
    op.drop_table('heart_transactions')

    op.drop_index('idx_user_hearts_refill', table_name='user_hearts')
    op.drop_index('idx_user_hearts_user', table_name='user_hearts')
    op.drop_table('user_hearts')

    # Drop enum
    heart_transaction_reason_enum = postgresql.ENUM(
        'quiz_wrong',
        'heart_purchase',
        'daily_refill',
        'streak_freeze_used',
        'reward',
        'admin_grant',
        'ad_watch',
        'practice_complete',
        name='heart_transaction_reason'
    )
    heart_transaction_reason_enum.drop(op.get_bind())
