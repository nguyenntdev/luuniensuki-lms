"""add spaced repetition cards

Revision ID: 0024_spaced_repetition
Revises: 0023_hearts_system
Create Date: 2025-01-17 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0024_spaced_repetition'
down_revision: Union[str, None] = '0023_hearts_system'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create spaced_repetition_cards table
    op.create_table(
        'spaced_repetition_cards',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('motif_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('ease_factor', sa.Float(), server_default=sa.text('2.5'), nullable=False),
        sa.Column('interval_days', sa.Integer(), server_default=sa.text('0'), nullable=False),
        sa.Column('repetitions', sa.Integer(), server_default=sa.text('0'), nullable=False),
        sa.Column('next_review_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('last_reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('review_history', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['motif_id'], ['motifs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'motif_id', name='uq_sr_cards_user_motif')
    )
    
    # Create indexes
    op.create_index('idx_sr_cards_user', 'spaced_repetition_cards', ['user_id'])
    op.create_index('idx_sr_cards_motif', 'spaced_repetition_cards', ['motif_id'])
    op.create_index('idx_sr_cards_next_review', 'spaced_repetition_cards', ['next_review_at'])
    op.create_index('idx_sr_cards_user_next_review', 'spaced_repetition_cards', ['user_id', 'next_review_at'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_sr_cards_user_next_review', table_name='spaced_repetition_cards')
    op.drop_index('idx_sr_cards_next_review', table_name='spaced_repetition_cards')
    op.drop_index('idx_sr_cards_motif', table_name='spaced_repetition_cards')
    op.drop_index('idx_sr_cards_user', table_name='spaced_repetition_cards')
    
    # Drop table
    op.drop_table('spaced_repetition_cards')

