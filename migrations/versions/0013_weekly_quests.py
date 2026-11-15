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


def _table_exists(table_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return table_name in inspector.get_table_names()


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

    if not _table_exists('weekly_quests'):
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
    if not _index_exists('weekly_quests', 'idx_weekly_quests_slug'):
        op.create_index('idx_weekly_quests_slug', 'weekly_quests', ['slug'])
    if not _index_exists('weekly_quests', 'idx_weekly_quests_category'):
        op.create_index('idx_weekly_quests_category', 'weekly_quests', ['category'])
    if not _index_exists('weekly_quests', 'idx_weekly_quests_week_year'):
        op.create_index('idx_weekly_quests_week_year', 'weekly_quests', ['week_number', 'year'])
    if not _index_exists('weekly_quests', 'idx_weekly_quests_active'):
        op.create_index('idx_weekly_quests_active', 'weekly_quests', ['is_active'])
    if not _index_exists('weekly_quests', 'idx_weekly_quests_recurring'):
        op.create_index('idx_weekly_quests_recurring', 'weekly_quests', ['is_recurring'])

    if not _table_exists('user_weekly_quests'):
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
    if not _constraint_exists('user_weekly_quests', 'uq_user_weekly_quest'):
        op.create_unique_constraint(
            'uq_user_weekly_quest',
            'user_weekly_quests',
            ['user_id', 'quest_id', 'week_start_date']
        )

    # Create indexes for user_weekly_quests
    if not _index_exists('user_weekly_quests', 'idx_user_weekly_quests_user'):
        op.create_index('idx_user_weekly_quests_user', 'user_weekly_quests', ['user_id'])
    if not _index_exists('user_weekly_quests', 'idx_user_weekly_quests_quest'):
        op.create_index('idx_user_weekly_quests_quest', 'user_weekly_quests', ['quest_id'])
    if not _index_exists('user_weekly_quests', 'idx_user_weekly_quests_week'):
        op.create_index('idx_user_weekly_quests_week', 'user_weekly_quests', ['week_start_date'])
    if not _index_exists('user_weekly_quests', 'idx_user_weekly_quests_completed'):
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
