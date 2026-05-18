"""quest_assignment_enhancements

Revision ID: 0029_quest_assignment_enhancements
Revises: 0028_ai_conversations
Create Date: 2024-01-15 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0029_quest_assignment_enhancements'
down_revision: Union[str, None] = '0028_ai_conversations'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new columns to quest_assignments table
    op.add_column('quest_assignments', sa.Column('points_override', sa.Integer(), nullable=True))
    op.add_column('quest_assignments', sa.Column('notes', sa.Text(), nullable=True))


def downgrade() -> None:
    # Remove the new columns
    op.drop_column('quest_assignments', 'notes')
    op.drop_column('quest_assignments', 'points_override')

