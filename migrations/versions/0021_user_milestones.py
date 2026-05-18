"""Add user milestones tracking

Revision ID: 0021
Revises: 0020
Create Date: 2025-01-16 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0021'
down_revision = '0020'
branch_labels = None
depends_on = None


def _enum_exists(enum_name: str) -> bool:
    bind = op.get_bind()
    return bind.execute(
        sa.text("SELECT 1 FROM pg_type WHERE typname = :name"),
        {"name": enum_name},
    ).first() is not None


def _table_exists(table_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return table_name in inspector.get_table_names()


def _index_exists(table_name: str, index_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    if table_name not in inspector.get_table_names():
        return False
    return index_name in {idx["name"] for idx in inspector.get_indexes(table_name)}


def upgrade() -> None:
    # Create milestone_type enum type if missing
    if not _enum_exists("milestone_type"):
        op.execute(
            """
            CREATE TYPE milestone_type AS ENUM (
                'first_motif_discovered',
                'first_quiz_passed',
                'first_lesson_completed',
                'first_badge_earned',
                'first_streak_7',
                'onboarding_completed'
            );
            """
        )

    milestone_enum = postgresql.ENUM(
        'first_motif_discovered',
        'first_quiz_passed',
        'first_lesson_completed',
        'first_badge_earned',
        'first_streak_7',
        'onboarding_completed',
        name='milestone_type',
        create_type=False,
    )

    # Create user_milestones table
    if not _table_exists('user_milestones'):
        op.create_table(
            'user_milestones',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('milestone_type', milestone_enum, nullable=False),
            sa.Column('achieved_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column('context_data', postgresql.JSONB(), nullable=True),
            sa.Column('celebrated', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.UniqueConstraint('user_id', 'milestone_type', name='uq_user_milestones_user_type'),
        )

    # Create indexes
    if not _index_exists('user_milestones', 'idx_user_milestones_user'):
        op.create_index('idx_user_milestones_user', 'user_milestones', ['user_id'])
    if not _index_exists('user_milestones', 'idx_user_milestones_type'):
        op.create_index('idx_user_milestones_type', 'user_milestones', ['milestone_type'])
    if not _index_exists('user_milestones', 'idx_user_milestones_celebrated'):
        op.create_index('idx_user_milestones_celebrated', 'user_milestones', ['celebrated'])


def downgrade() -> None:
    # Drop indexes
    if _index_exists('user_milestones', 'idx_user_milestones_celebrated'):
        op.drop_index('idx_user_milestones_celebrated', 'user_milestones')
    if _index_exists('user_milestones', 'idx_user_milestones_type'):
        op.drop_index('idx_user_milestones_type', 'user_milestones')
    if _index_exists('user_milestones', 'idx_user_milestones_user'):
        op.drop_index('idx_user_milestones_user', 'user_milestones')

    # Drop table
    if _table_exists('user_milestones'):
        op.drop_table('user_milestones')

    # Drop enum type
    if _enum_exists('milestone_type'):
        op.execute('DROP TYPE milestone_type;')
