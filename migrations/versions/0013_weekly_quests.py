"""Add weekly quests

Revision ID: 0013_weekly_quests
Revises: 0012_daily_missions
Create Date: 2025-01-XX XX:XX:XX.XXXXXX

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0013_weekly_quests'
down_revision = '0012_daily_missions'
branch_labels = None
depends_on = None


def _enum_exists(enum_name: str) -> bool:
    bind = op.get_bind()
    return bind.execute(
        sa.text("SELECT 1 FROM pg_type WHERE typname = :name"),
        {"name": enum_name},
    ).first() is not None


def upgrade() -> None:
    # Create quest_category enum
    if not _enum_exists("quest_category"):
        op.execute(
            """
            CREATE TYPE quest_category AS ENUM (
                'exploration',
                'mastery',
                'quiz_champion',
                'streak_master'
            );
            """
        )

    quest_category_enum = postgresql.ENUM(
        'exploration',
        'mastery',
        'quiz_champion',
        'streak_master',
        name='quest_category',
        create_type=False,
    )

    # Create weekly_quests table
    op.create_table(
        'weekly_quests',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('slug', sa.String(100), nullable=False, unique=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('category', quest_category_enum, nullable=False),
        sa.Column('week_number', sa.Integer(), nullable=True),
        sa.Column('year', sa.Integer(), nullable=True),
        sa.Column('target_count', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('xp_reward', sa.Integer(), nullable=False, server_default='100'),
        sa.Column('badge_slug', sa.String(100), nullable=True),
        sa.Column('is_recurring', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Create indexes for weekly_quests
    op.create_index('idx_weekly_quests_slug', 'weekly_quests', ['slug'])
    op.create_index('idx_weekly_quests_category', 'weekly_quests', ['category'])
    op.create_index('idx_weekly_quests_week_year', 'weekly_quests', ['week_number', 'year'])
    op.create_index('idx_weekly_quests_active', 'weekly_quests', ['is_active'])
    op.create_index('idx_weekly_quests_recurring', 'weekly_quests', ['is_recurring'])

    # Create user_weekly_quests table
    op.create_table(
        'user_weekly_quests',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('quest_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('week_start_date', sa.DateTime(timezone=False), nullable=False),
        sa.Column('current_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_completed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('xp_awarded', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['quest_id'], ['weekly_quests.id'], ondelete='CASCADE'),
    )

    # Create unique constraint
    op.create_unique_constraint(
        'uq_user_weekly_quest',
        'user_weekly_quests',
        ['user_id', 'quest_id', 'week_start_date']
    )

    # Create indexes for user_weekly_quests
    op.create_index('idx_user_weekly_quests_user', 'user_weekly_quests', ['user_id'])
    op.create_index('idx_user_weekly_quests_quest', 'user_weekly_quests', ['quest_id'])
    op.create_index('idx_user_weekly_quests_week', 'user_weekly_quests', ['week_start_date'])
    op.create_index('idx_user_weekly_quests_completed', 'user_weekly_quests', ['is_completed'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_user_weekly_quests_completed', 'user_weekly_quests')
    op.drop_index('idx_user_weekly_quests_week', 'user_weekly_quests')
    op.drop_index('idx_user_weekly_quests_quest', 'user_weekly_quests')
    op.drop_index('idx_user_weekly_quests_user', 'user_weekly_quests')

    # Drop unique constraint
    op.drop_constraint('uq_user_weekly_quest', 'user_weekly_quests', type_='unique')

    # Drop user_weekly_quests table
    op.drop_table('user_weekly_quests')

    # Drop indexes for weekly_quests
    op.drop_index('idx_weekly_quests_recurring', 'weekly_quests')
    op.drop_index('idx_weekly_quests_active', 'weekly_quests')
    op.drop_index('idx_weekly_quests_week_year', 'weekly_quests')
    op.drop_index('idx_weekly_quests_category', 'weekly_quests')
    op.drop_index('idx_weekly_quests_slug', 'weekly_quests')

    # Drop weekly_quests table
    op.drop_table('weekly_quests')

    # Drop quest_category enum
    if _enum_exists("quest_category"):
        quest_category_enum = postgresql.ENUM(
            'exploration',
            'mastery',
            'quiz_champion',
            'streak_master',
            name='quest_category'
        )
        quest_category_enum.drop(op.get_bind(), checkfirst=True)
