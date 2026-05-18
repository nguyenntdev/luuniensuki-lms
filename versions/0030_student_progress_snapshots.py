"""student_progress_snapshots

Revision ID: 0030_student_progress_snapshots
Revises: 0029_quest_assignment_enhancements
Create Date: 2024-01-16 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '0030_student_progress_snapshots'
down_revision: Union[str, None] = '0029_quest_assignment_enhancements'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create student_progress_snapshots table
    op.create_table(
        'student_progress_snapshots',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('student_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('classroom_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('snapshot_date', sa.Date(), nullable=False),
        sa.Column('lessons_completed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('quizzes_passed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('average_quiz_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('motifs_discovered', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('current_streak', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('xp_earned', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('time_spent_minutes', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['student_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['classroom_id'], ['classes.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('student_id', 'classroom_id', 'snapshot_date', 
                          name='uq_progress_snapshot_student_classroom_date'),
    )
    
    # Create indexes
    op.create_index('idx_progress_snapshots_student', 'student_progress_snapshots', ['student_id'])
    op.create_index('idx_progress_snapshots_classroom', 'student_progress_snapshots', ['classroom_id'])
    op.create_index('idx_progress_snapshots_date', 'student_progress_snapshots', ['snapshot_date'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_progress_snapshots_date', 'student_progress_snapshots')
    op.drop_index('idx_progress_snapshots_classroom', 'student_progress_snapshots')
    op.drop_index('idx_progress_snapshots_student', 'student_progress_snapshots')
    
    # Drop table
    op.drop_table('student_progress_snapshots')

