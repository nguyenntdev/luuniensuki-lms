"""Add AI conversation and message models

Revision ID: 0028_ai_conversations
Revises: 0027_quiz_hints
Create Date: 2025-01-20 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0028_ai_conversations'
down_revision: Union[str, None] = '0027_quiz_hints'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create ai_conversations table
    op.create_table(
        'ai_conversations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('context_type', sa.String(length=50), nullable=True),
        sa.Column('context_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('message_count', sa.Integer(), server_default=sa.text('0'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for ai_conversations
    op.create_index('idx_ai_conversation_user', 'ai_conversations', ['user_id'])
    op.create_index('idx_ai_conversation_context', 'ai_conversations', ['context_type', 'context_id'])
    op.create_index('idx_ai_conversation_active', 'ai_conversations', ['is_active'])
    op.create_index('idx_ai_conversation_created', 'ai_conversations', ['created_at'])
    
    # Create ai_messages table
    op.create_table(
        'ai_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('tokens_used', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['conversation_id'], ['ai_conversations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for ai_messages
    op.create_index('idx_ai_message_conversation', 'ai_messages', ['conversation_id'])
    op.create_index('idx_ai_message_role', 'ai_messages', ['role'])
    op.create_index('idx_ai_message_created', 'ai_messages', ['created_at'])


def downgrade() -> None:
    # Drop indexes for ai_messages
    op.drop_index('idx_ai_message_created', table_name='ai_messages')
    op.drop_index('idx_ai_message_role', table_name='ai_messages')
    op.drop_index('idx_ai_message_conversation', table_name='ai_messages')
    
    # Drop ai_messages table
    op.drop_table('ai_messages')
    
    # Drop indexes for ai_conversations
    op.drop_index('idx_ai_conversation_created', table_name='ai_conversations')
    op.drop_index('idx_ai_conversation_active', table_name='ai_conversations')
    op.drop_index('idx_ai_conversation_context', table_name='ai_conversations')
    op.drop_index('idx_ai_conversation_user', table_name='ai_conversations')
    
    # Drop ai_conversations table
    op.drop_table('ai_conversations')

