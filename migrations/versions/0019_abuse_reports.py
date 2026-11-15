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


def _table_exists(table_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return table_name in inspector.get_table_names()


def _index_exists(table_name: str, index_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    if table_name not in inspector.get_table_names():
        return False
    return index_name in {i['name'] for i in inspector.get_indexes(table_name)}


def upgrade() -> None:
    if not _table_exists('abuse_reports'):
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
    if not _index_exists('abuse_reports', 'idx_abuse_reports_reporter'):
        op.create_index('idx_abuse_reports_reporter', 'abuse_reports', ['reporter_id'])
    if not _index_exists('abuse_reports', 'idx_abuse_reports_reported_user'):
        op.create_index('idx_abuse_reports_reported_user', 'abuse_reports', ['reported_user_id'])
    if not _index_exists('abuse_reports', 'idx_abuse_reports_status'):
        op.create_index('idx_abuse_reports_status', 'abuse_reports', ['status'])
    if not _index_exists('abuse_reports', 'idx_abuse_reports_priority'):
        op.create_index('idx_abuse_reports_priority', 'abuse_reports', ['priority'])
    if not _index_exists('abuse_reports', 'idx_abuse_reports_content_type'):
        op.create_index('idx_abuse_reports_content_type', 'abuse_reports', ['content_type'])
    if not _index_exists('abuse_reports', 'idx_abuse_reports_assigned_to'):
        op.create_index('idx_abuse_reports_assigned_to', 'abuse_reports', ['assigned_to_id'])
    if not _index_exists('abuse_reports', 'idx_abuse_reports_created_at'):
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
