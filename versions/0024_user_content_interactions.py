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


def upgrade() -> None:
    # Create interaction_type enum type
    op.execute("""
        CREATE TYPE interaction_type AS ENUM (
            'view',
            'complete',
            'like',
            'save'
        );
    """)

    # Create user_content_interactions table
    op.create_table(
        'user_content_interactions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('content_type', sa.String(50), nullable=False),
        sa.Column('content_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('interaction_type',
                  sa.Enum('view', 'complete', 'like', 'save',
                          name='interaction_type', native_enum=True),
                  nullable=False),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )

    # Create indexes for efficient querying
    op.create_index('idx_user_content_interactions_user', 'user_content_interactions', ['user_id'])
    op.create_index('idx_user_content_interactions_content', 'user_content_interactions', ['content_type', 'content_id'])
    op.create_index('idx_user_content_interactions_type', 'user_content_interactions', ['interaction_type'])
    op.create_index('idx_user_content_interactions_created', 'user_content_interactions', ['created_at'])
    op.create_index('idx_user_content_interactions_user_type', 'user_content_interactions', ['user_id', 'content_type'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_user_content_interactions_user_type', 'user_content_interactions')
    op.drop_index('idx_user_content_interactions_created', 'user_content_interactions')
    op.drop_index('idx_user_content_interactions_type', 'user_content_interactions')
    op.drop_index('idx_user_content_interactions_content', 'user_content_interactions')
    op.drop_index('idx_user_content_interactions_user', 'user_content_interactions')

    # Drop table
    op.drop_table('user_content_interactions')

    # Drop enum type
    op.execute('DROP TYPE interaction_type;')
