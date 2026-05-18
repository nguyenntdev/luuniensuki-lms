"""Add abuse_reports table for UGC moderation

Revision ID: 0019
Revises: 0018
Create Date: 2025-01-08 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0019'
down_revision = '0018_lesson_cache'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create abuse_reports table
    op.create_table(
        'abuse_reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('reporter_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('reported_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('content_type', sa.String(length=50), nullable=False),
        sa.Column('content_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('reason', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('evidence_urls', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('priority', sa.String(length=20), nullable=False, server_default='low'),
        sa.Column('assigned_to_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['reporter_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['reported_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['assigned_to_id'], ['users.id'], ondelete='SET NULL'),
    )

    # Create indexes
    op.create_index('idx_abuse_reports_reporter', 'abuse_reports', ['reporter_id'])
    op.create_index('idx_abuse_reports_reported_user', 'abuse_reports', ['reported_user_id'])
    op.create_index('idx_abuse_reports_status', 'abuse_reports', ['status'])
    op.create_index('idx_abuse_reports_priority', 'abuse_reports', ['priority'])
    op.create_index('idx_abuse_reports_content_type', 'abuse_reports', ['content_type'])
    op.create_index('idx_abuse_reports_assigned_to', 'abuse_reports', ['assigned_to_id'])
    op.create_index('idx_abuse_reports_created_at', 'abuse_reports', ['created_at'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_abuse_reports_created_at', table_name='abuse_reports')
    op.drop_index('idx_abuse_reports_assigned_to', table_name='abuse_reports')
    op.drop_index('idx_abuse_reports_content_type', table_name='abuse_reports')
    op.drop_index('idx_abuse_reports_priority', table_name='abuse_reports')
    op.drop_index('idx_abuse_reports_status', table_name='abuse_reports')
    op.drop_index('idx_abuse_reports_reported_user', table_name='abuse_reports')
    op.drop_index('idx_abuse_reports_reporter', table_name='abuse_reports')

    # Drop table
    op.drop_table('abuse_reports')
