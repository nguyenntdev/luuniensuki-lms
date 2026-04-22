"""add quiz hints with RAG support

Revision ID: 0027_quiz_hints
Revises: 0026_lesson_prerequisites
Create Date: 2025-01-20 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0027_quiz_hints'
down_revision: Union[str, None] = '0026_lesson_prerequisites'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create HintType enum
    op.execute("CREATE TYPE hint_type AS ENUM ('explain', 'clue', 'elimination')")
    
    # Add quiz_hint to HeartTransactionReason enum
    op.execute("ALTER TYPE heart_transaction_reason ADD VALUE 'quiz_hint'")
    
    # Create quiz_hint_requests table
    op.create_table(
        'quiz_hint_requests',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('question_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('hint_type', sa.String(length=20), nullable=False),
        sa.Column('hint_text', sa.Text(), nullable=False),
        sa.Column('heart_cost', sa.Integer(), server_default=sa.text('0'), nullable=False),
        sa.Column('rag_sources', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['question_id'], ['quiz_questions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('idx_quiz_hints_user', 'quiz_hint_requests', ['user_id'])
    op.create_index('idx_quiz_hints_question', 'quiz_hint_requests', ['question_id'])
    op.create_index('idx_quiz_hints_created', 'quiz_hint_requests', ['created_at'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_quiz_hints_created', table_name='quiz_hint_requests')
    op.drop_index('idx_quiz_hints_question', table_name='quiz_hint_requests')
    op.drop_index('idx_quiz_hints_user', table_name='quiz_hint_requests')
    
    # Drop quiz_hint_requests table
    op.drop_table('quiz_hint_requests')
    
    # Note: Cannot remove enum value from heart_transaction_reason without recreating the enum
    # Note: Cannot drop hint_type enum if it's still in use
    # For a clean downgrade, you would need to recreate the enums without these values

