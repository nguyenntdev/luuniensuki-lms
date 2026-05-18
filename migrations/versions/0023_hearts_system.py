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
    return index_name in {idx["name"] for idx in inspector.get_indexes(table_name)}


def upgrade() -> None:
    # Create heart_transaction_reason enum if missing
    if not _enum_exists('heart_transaction_reason'):
        op.execute(
            """
            CREATE TYPE heart_transaction_reason AS ENUM (
                'quiz_wrong',
                'heart_purchase',
                'daily_refill',
                'streak_freeze_used',
                'reward',
                'admin_grant',
                'ad_watch',
                'practice_complete'
            );
            """
        )

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
        create_type=False,
    )

    # Create user_hearts table
    if not _table_exists('user_hearts'):
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
    if not _index_exists('user_hearts', 'idx_user_hearts_user'):
        op.create_index('idx_user_hearts_user', 'user_hearts', ['user_id'])
    if not _index_exists('user_hearts', 'idx_user_hearts_refill'):
        op.create_index('idx_user_hearts_refill', 'user_hearts', ['hearts_refill_at'])

    # Create heart_transactions table
    if not _table_exists('heart_transactions'):
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
    if not _index_exists('heart_transactions', 'idx_heart_transactions_user'):
        op.create_index('idx_heart_transactions_user', 'heart_transactions', ['user_id'])
    if not _index_exists('heart_transactions', 'idx_heart_transactions_reason'):
        op.create_index('idx_heart_transactions_reason', 'heart_transactions', ['reason'])
    if not _index_exists('heart_transactions', 'idx_heart_transactions_created'):
        op.create_index('idx_heart_transactions_created', 'heart_transactions', ['created_at'])


def downgrade() -> None:
    # Drop tables
    if _index_exists('heart_transactions', 'idx_heart_transactions_created'):
        op.drop_index('idx_heart_transactions_created', table_name='heart_transactions')
    if _index_exists('heart_transactions', 'idx_heart_transactions_reason'):
        op.drop_index('idx_heart_transactions_reason', table_name='heart_transactions')
    if _index_exists('heart_transactions', 'idx_heart_transactions_user'):
        op.drop_index('idx_heart_transactions_user', table_name='heart_transactions')
    if _table_exists('heart_transactions'):
        op.drop_table('heart_transactions')

    if _index_exists('user_hearts', 'idx_user_hearts_refill'):
        op.drop_index('idx_user_hearts_refill', table_name='user_hearts')
    if _index_exists('user_hearts', 'idx_user_hearts_user'):
        op.drop_index('idx_user_hearts_user', table_name='user_hearts')
    if _table_exists('user_hearts'):
        op.drop_table('user_hearts')

    if _enum_exists('heart_transaction_reason'):
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
