"""Add content rating and age verification

Revision ID: 0020
Revises: 0019
Create Date: 2025-01-08 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0020'
down_revision = '0019'
branch_labels = None
depends_on = None


def _enum_exists(enum_name: str) -> bool:
    bind = op.get_bind()
    return bind.execute(
        sa.text("SELECT 1 FROM pg_type WHERE typname = :name"),
        {"name": enum_name},
    ).first() is not None


def upgrade() -> None:
    # Create content_rating enum type
    if not _enum_exists("content_rating"):
        op.execute(
            """
            CREATE TYPE content_rating AS ENUM ('everyone', 'teen', 'mature');
            """
        )

    # Add content_rating field to motifs table
    op.add_column('motifs',
        sa.Column('content_rating',
                  postgresql.ENUM('everyone', 'teen', 'mature', name='content_rating', create_type=False),
                  nullable=False,
                  server_default='everyone'))

    # Add content_rating field to lesson_content table
    op.add_column('lesson_content',
        sa.Column('content_rating',
                  postgresql.ENUM('everyone', 'teen', 'mature', name='content_rating', create_type=False),
                  nullable=False,
                  server_default='everyone'))

    # Add content_rating field to quests table
    op.add_column('quests',
        sa.Column('content_rating',
                  postgresql.ENUM('everyone', 'teen', 'mature', name='content_rating', create_type=False),
                  nullable=False,
                  server_default='everyone'))

    # Add age verification fields to users table
    op.add_column('users',
        sa.Column('birth_year', sa.Integer(), nullable=True))

    op.add_column('users',
        sa.Column('age_verified', sa.Boolean(), nullable=False, server_default='false'))

    op.add_column('users',
        sa.Column('age_verified_at', sa.DateTime(timezone=True), nullable=True))

    # Create index on content_rating fields for better query performance
    op.create_index('idx_motifs_content_rating', 'motifs', ['content_rating'])
    op.create_index('idx_lesson_content_rating', 'lesson_content', ['content_rating'])
    op.create_index('idx_quests_content_rating', 'quests', ['content_rating'])

    # Create indexes on age verification fields
    op.create_index('idx_users_age_verified', 'users', ['age_verified'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_users_age_verified', 'users')
    op.drop_index('idx_quests_content_rating', 'quests')
    op.drop_index('idx_lesson_content_rating', 'lesson_content')
    op.drop_index('idx_motifs_content_rating', 'motifs')

    # Remove age verification fields from users table
    op.drop_column('users', 'age_verified_at')
    op.drop_column('users', 'age_verified')
    op.drop_column('users', 'birth_year')

    # Remove content_rating fields from tables
    op.drop_column('quests', 'content_rating')
    op.drop_column('lesson_content', 'content_rating')
    op.drop_column('motifs', 'content_rating')

    # Drop enum type
    if _enum_exists("content_rating"):
        op.execute('DROP TYPE content_rating;')
