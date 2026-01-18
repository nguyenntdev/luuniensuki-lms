"""Add class_code, max_students, is_archived, settings, and updated_at to classrooms

Revision ID: 0021_classroom_enhancements
Revises: 0020_adaptive_learning
Create Date: 2024-01-10 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import random
import string


# revision identifiers, used by Alembic.
revision = '0021_classroom_enhancements'
down_revision = '0020'
branch_label = None
depends_on = None


def generate_class_code(length: int = 8) -> str:
    """Generate a random class code using uppercase letters and numbers."""
    chars = string.ascii_uppercase + string.digits
    # Exclude similar-looking characters
    chars = chars.replace('0', '').replace('O', '').replace('I', '').replace('1', '')
    return ''.join(random.choice(chars) for _ in range(length))


def upgrade() -> None:
    """Add new fields to classrooms table."""

    # Add new columns
    op.add_column('classes', sa.Column('class_code', sa.String(length=8), nullable=True))
    op.add_column('classes', sa.Column('max_students', sa.Integer(), nullable=True))
    op.add_column('classes', sa.Column('is_archived', sa.Boolean(), server_default=sa.text('false'), nullable=False))
    op.add_column('classes', sa.Column('settings', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('classes', sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False))

    # Generate unique class codes for existing classrooms
    connection = op.get_bind()
    result = connection.execute(sa.text("SELECT id FROM classes"))
    existing_classes = result.fetchall()

    used_codes = set()
    for row in existing_classes:
        class_id = row[0]
        # Generate unique code
        while True:
            code = generate_class_code()
            if code not in used_codes:
                used_codes.add(code)
                break

        connection.execute(
            sa.text("UPDATE classes SET class_code = :code WHERE id = :id"),
            {"code": code, "id": class_id}
        )

    # Make class_code non-nullable after populating
    op.alter_column('classes', 'class_code', nullable=False)

    # Create unique constraint and index
    op.create_unique_constraint('uq_classes_class_code', 'classes', ['class_code'])
    op.create_index('idx_classes_class_code', 'classes', ['class_code'])


def downgrade() -> None:
    """Remove new fields from classrooms table."""

    # Drop constraints and indexes first
    op.drop_index('idx_classes_class_code', table_name='classes')
    op.drop_constraint('uq_classes_class_code', 'classes', type_='unique')

    # Drop columns
    op.drop_column('classes', 'updated_at')
    op.drop_column('classes', 'settings')
    op.drop_column('classes', 'is_archived')
    op.drop_column('classes', 'max_students')
    op.drop_column('classes', 'class_code')
