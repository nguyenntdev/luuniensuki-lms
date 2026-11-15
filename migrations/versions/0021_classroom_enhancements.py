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


def _column_exists(table_name: str, column_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    if table_name not in inspector.get_table_names():
        return False
    return column_name in {c['name'] for c in inspector.get_columns(table_name)}


def _add_column_if_missing(table_name: str, column: sa.Column) -> None:
    if not _column_exists(table_name, column.name):
        op.add_column(table_name, column)


def _index_exists(table_name: str, index_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    if table_name not in inspector.get_table_names():
        return False
    return index_name in {i['name'] for i in inspector.get_indexes(table_name)}


def _constraint_exists(table_name: str, constraint_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    if table_name not in inspector.get_table_names():
        return False
    fks = {fk['name'] for fk in inspector.get_foreign_keys(table_name)}
    uqs = {uq['name'] for uq in inspector.get_unique_constraints(table_name)}
    cks = {ck['name'] for ck in inspector.get_check_constraints(table_name)}
    return constraint_name in (fks | uqs | cks)


def upgrade() -> None:
    """Add new fields to classrooms table."""

    fresh_column = not _column_exists('classes', 'class_code')

    # Add new columns
    _add_column_if_missing('classes', sa.Column('class_code', sa.String(length=8), nullable=True))
    _add_column_if_missing('classes', sa.Column('max_students', sa.Integer(), nullable=True))
    _add_column_if_missing('classes', sa.Column('is_archived', sa.Boolean(), server_default=sa.text('false'), nullable=False))
    _add_column_if_missing('classes', sa.Column('settings', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    _add_column_if_missing('classes', sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False))

    if fresh_column:
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
    if not _constraint_exists('classes', 'uq_classes_class_code'):
        op.create_unique_constraint('uq_classes_class_code', 'classes', ['class_code'])
    if not _index_exists('classes', 'idx_classes_class_code'):
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
