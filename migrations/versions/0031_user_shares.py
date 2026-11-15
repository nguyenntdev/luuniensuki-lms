"""add user shares table

Revision ID: 0031_user_shares
Revises: 0030_student_progress_snapshots
Create Date: 2025-01-20 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0031_user_shares'
down_revision: Union[str, None] = '0030_student_progress_snapshots'
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
    return index_name in {i['name'] for i in inspector.get_indexes(table_name)}


def upgrade() -> None:
    # Create share_type enum
    if not _enum_exists("share_type"):
        share_type_enum = postgresql.ENUM(
            'achievement',
            'badge',
            'streak',
            'level_up',
            'certificate',
            name='share_type',
            create_type=True
        )
        share_type_enum.create(op.get_bind())

    # Create share_visibility enum
    if not _enum_exists("share_visibility"):
        share_visibility_enum = postgresql.ENUM(
            'public',
            'followers',
            'private',
            name='share_visibility',
            create_type=True
        )
        share_visibility_enum.create(op.get_bind())

    if not _table_exists('user_shares'):
        # Create user_shares table
        op.create_table(
            'user_shares',
            sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('share_type', sa.String(length=50), nullable=False),
            sa.Column('content_id', postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column('caption', sa.Text(), nullable=True),
            sa.Column('visibility', sa.String(length=20), server_default=sa.text("'public'"), nullable=False),
            sa.Column('share_url', sa.String(length=255), nullable=True),
            sa.Column('view_count', sa.Integer(), server_default=sa.text('0'), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )

    # Create indexes
    if not _index_exists('user_shares', 'idx_user_shares_user'):
        op.create_index('idx_user_shares_user', 'user_shares', ['user_id'])
    if not _index_exists('user_shares', 'idx_user_shares_type'):
        op.create_index('idx_user_shares_type', 'user_shares', ['share_type'])
    if not _index_exists('user_shares', 'idx_user_shares_visibility'):
        op.create_index('idx_user_shares_visibility', 'user_shares', ['visibility'])
    if not _index_exists('user_shares', 'idx_user_shares_created'):
        op.create_index('idx_user_shares_created', 'user_shares', ['created_at'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_user_shares_created', table_name='user_shares')
    op.drop_index('idx_user_shares_visibility', table_name='user_shares')
    op.drop_index('idx_user_shares_type', table_name='user_shares')
    op.drop_index('idx_user_shares_user', table_name='user_shares')

    # Drop table
    op.drop_table('user_shares')

    # Drop enums
    share_visibility_enum = postgresql.ENUM(
        'public',
        'followers',
        'private',
        name='share_visibility'
    )
    share_visibility_enum.drop(op.get_bind())

    share_type_enum = postgresql.ENUM(
        'achievement',
        'badge',
        'streak',
        'level_up',
        'certificate',
        name='share_type'
    )
    share_type_enum.drop(op.get_bind())

