"""add email scheduling system

Revision ID: 0032_email_scheduling
Revises: 0031_social_features
Create Date: 2024-01-17 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0032_email_scheduling'
down_revision = '0031_social_features'
branch_labels = None
depends_on = None


def upgrade():
    # Create email_status enum
    op.execute("CREATE TYPE email_status AS ENUM ('pending', 'sent', 'failed', 'cancelled')")
    
    # Create email_templates table
    op.create_table(
        'email_templates',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('key', sa.String(100), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('subject_template', sa.String(500), nullable=False),
        sa.Column('body_html', sa.Text(), nullable=False),
        sa.Column('body_text', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key', name='uq_email_templates_key')
    )
    
    # Create indexes for email_templates
    op.create_index('idx_email_templates_key', 'email_templates', ['key'])
    op.create_index('idx_email_templates_active', 'email_templates', ['is_active'])
    
    # Create scheduled_emails table
    op.create_table(
        'scheduled_emails',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('template_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('scheduled_for', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.Enum('pending', 'sent', 'failed', 'cancelled', name='email_status', native_enum=True),
                  server_default=sa.text("'pending'"), nullable=False),
        sa.Column('context_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['template_id'], ['email_templates.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for scheduled_emails
    op.create_index('idx_scheduled_emails_user', 'scheduled_emails', ['user_id'])
    op.create_index('idx_scheduled_emails_template', 'scheduled_emails', ['template_id'])
    op.create_index('idx_scheduled_emails_status', 'scheduled_emails', ['status'])
    op.create_index('idx_scheduled_emails_scheduled_for', 'scheduled_emails', ['scheduled_for'])
    op.create_index('idx_scheduled_emails_sent_at', 'scheduled_emails', ['sent_at'])
    op.create_index('idx_scheduled_emails_user_template', 'scheduled_emails', ['user_id', 'template_id'])


def downgrade():
    # Drop indexes for scheduled_emails
    op.drop_index('idx_scheduled_emails_user_template', table_name='scheduled_emails')
    op.drop_index('idx_scheduled_emails_sent_at', table_name='scheduled_emails')
    op.drop_index('idx_scheduled_emails_scheduled_for', table_name='scheduled_emails')
    op.drop_index('idx_scheduled_emails_status', table_name='scheduled_emails')
    op.drop_index('idx_scheduled_emails_template', table_name='scheduled_emails')
    op.drop_index('idx_scheduled_emails_user', table_name='scheduled_emails')
    
    # Drop scheduled_emails table
    op.drop_table('scheduled_emails')
    
    # Drop indexes for email_templates
    op.drop_index('idx_email_templates_active', table_name='email_templates')
    op.drop_index('idx_email_templates_key', table_name='email_templates')
    
    # Drop email_templates table
    op.drop_table('email_templates')
    
    # Drop email_status enum
    op.execute("DROP TYPE email_status")

