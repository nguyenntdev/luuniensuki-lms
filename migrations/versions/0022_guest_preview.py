"""Add guest preview functionality

Revision ID: 0022
Revises: 0021
Create Date: 2025-01-16 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0022'
down_revision = '0021'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add preview_eligible column to lesson_content table
    op.add_column(
        'lesson_content',
        sa.Column('preview_eligible', sa.Boolean(), nullable=False, server_default='false')
    )
    
    # Create guest_previews table
    op.create_table(
        'guest_previews',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('session_id', sa.String(255), nullable=False, index=True),
        sa.Column('preview_lesson_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('converted_to_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('device_info', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['preview_lesson_id'], ['lesson_content.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['converted_to_user_id'], ['users.id'], ondelete='SET NULL'),
    )
    
    # Create indexes for guest_previews
    op.create_index('idx_guest_previews_session_id', 'guest_previews', ['session_id'])
    op.create_index('idx_guest_previews_started_at', 'guest_previews', ['started_at'])
    op.create_index('idx_guest_previews_converted_user', 'guest_previews', ['converted_to_user_id'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_guest_previews_converted_user', 'guest_previews')
    op.drop_index('idx_guest_previews_started_at', 'guest_previews')
    op.drop_index('idx_guest_previews_session_id', 'guest_previews')
    
    # Drop guest_previews table
    op.drop_table('guest_previews')
    
    # Remove preview_eligible column from lesson_content
    op.drop_column('lesson_content', 'preview_eligible')

