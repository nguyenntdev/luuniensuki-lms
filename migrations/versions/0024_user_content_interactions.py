"""Add user content interactions for recommendations

Revision ID: 0024
Revises: 0023
Create Date: 2025-01-19 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0024'
down_revision = '0023_hearts_system'
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
    # Create interaction_type enum type
    if not _enum_exists("interaction_type"):
        op.execute(
            """
            CREATE TYPE interaction_type AS ENUM (
                'view',
                'complete',
                'like',
                'save'
            );
            """
        )

    interaction_type_enum = postgresql.ENUM(
        'view',
        'complete',
        'like',
        'save',
        name='interaction_type',
        create_type=False,
    )

    # Create user_content_interactions table
    if not _table_exists('user_content_interactions'):
        op.create_table(
            'user_content_interactions',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('content_type', sa.String(50), nullable=False),
            sa.Column('content_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('interaction_type', interaction_type_enum, nullable=False),
            sa.Column('duration_seconds', sa.Integer(), nullable=True),
            sa.Column('metadata', postgresql.JSONB(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        )

    # Create indexes for efficient querying
    if not _index_exists('user_content_interactions', 'idx_user_content_interactions_user'):
        op.create_index('idx_user_content_interactions_user', 'user_content_interactions', ['user_id'])
    if not _index_exists('user_content_interactions', 'idx_user_content_interactions_content'):
        op.create_index('idx_user_content_interactions_content', 'user_content_interactions', ['content_type', 'content_id'])
    if not _index_exists('user_content_interactions', 'idx_user_content_interactions_type'):
        op.create_index('idx_user_content_interactions_type', 'user_content_interactions', ['interaction_type'])
    if not _index_exists('user_content_interactions', 'idx_user_content_interactions_created'):
        op.create_index('idx_user_content_interactions_created', 'user_content_interactions', ['created_at'])
    if not _index_exists('user_content_interactions', 'idx_user_content_interactions_user_type'):
        op.create_index('idx_user_content_interactions_user_type', 'user_content_interactions', ['user_id', 'content_type'])


def downgrade() -> None:
    # Drop indexes
    if _index_exists('user_content_interactions', 'idx_user_content_interactions_user_type'):
        op.drop_index('idx_user_content_interactions_user_type', 'user_content_interactions')
    if _index_exists('user_content_interactions', 'idx_user_content_interactions_created'):
        op.drop_index('idx_user_content_interactions_created', 'user_content_interactions')
    if _index_exists('user_content_interactions', 'idx_user_content_interactions_type'):
        op.drop_index('idx_user_content_interactions_type', 'user_content_interactions')
    if _index_exists('user_content_interactions', 'idx_user_content_interactions_content'):
        op.drop_index('idx_user_content_interactions_content', 'user_content_interactions')
    if _index_exists('user_content_interactions', 'idx_user_content_interactions_user'):
        op.drop_index('idx_user_content_interactions_user', 'user_content_interactions')

    # Drop table
    if _table_exists('user_content_interactions'):
        op.drop_table('user_content_interactions')

    # Drop enum type
    if _enum_exists("interaction_type"):
        op.execute('DROP TYPE interaction_type;')
