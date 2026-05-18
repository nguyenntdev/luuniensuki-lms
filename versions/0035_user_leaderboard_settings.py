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


def upgrade() -> None:
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
    op.create_index('idx_user_leaderboard_settings_user', 'user_leaderboard_settings', ['user_id'])


def downgrade() -> None:
    # Drop index
    op.drop_index('idx_user_leaderboard_settings_user', table_name='user_leaderboard_settings')
    
    # Drop table
    op.drop_table('user_leaderboard_settings')

