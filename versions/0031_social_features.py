"""add social features

Revision ID: 0031_social_features
Revises: 0030_student_progress_snapshots
Create Date: 2024-01-16 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0031_social_features'
down_revision = '0030_student_progress_snapshots'
branch_labels = None
depends_on = None


def upgrade():
    # Create friend_request_status enum
    op.execute("CREATE TYPE friend_request_status AS ENUM ('pending', 'accepted', 'rejected')")
    
    # Create user_follows table
    op.create_table(
        'user_follows',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('follower_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('following_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['follower_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['following_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('follower_id', 'following_id', name='uq_user_follows'),
        sa.CheckConstraint('follower_id != following_id', name='ck_user_follows_no_self_follow')
    )
    
    # Create indexes for user_follows
    op.create_index('idx_user_follows_follower', 'user_follows', ['follower_id'])
    op.create_index('idx_user_follows_following', 'user_follows', ['following_id'])
    op.create_index('idx_user_follows_created', 'user_follows', ['created_at'])
    
    # Create friend_requests table
    op.create_table(
        'friend_requests',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('from_user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('to_user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.Enum('pending', 'accepted', 'rejected', name='friend_request_status', native_enum=True), 
                  server_default=sa.text("'pending'"), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('responded_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['from_user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['to_user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('from_user_id', 'to_user_id', name='uq_friend_requests')
    )
    
    # Create indexes for friend_requests
    op.create_index('idx_friend_requests_from_user', 'friend_requests', ['from_user_id'])
    op.create_index('idx_friend_requests_to_user', 'friend_requests', ['to_user_id'])
    op.create_index('idx_friend_requests_status', 'friend_requests', ['status'])
    op.create_index('idx_friend_requests_created', 'friend_requests', ['created_at'])


def downgrade():
    # Drop indexes for friend_requests
    op.drop_index('idx_friend_requests_created', table_name='friend_requests')
    op.drop_index('idx_friend_requests_status', table_name='friend_requests')
    op.drop_index('idx_friend_requests_to_user', table_name='friend_requests')
    op.drop_index('idx_friend_requests_from_user', table_name='friend_requests')
    
    # Drop friend_requests table
    op.drop_table('friend_requests')
    
    # Drop indexes for user_follows
    op.drop_index('idx_user_follows_created', table_name='user_follows')
    op.drop_index('idx_user_follows_following', table_name='user_follows')
    op.drop_index('idx_user_follows_follower', table_name='user_follows')
    
    # Drop user_follows table
    op.drop_table('user_follows')
    
    # Drop friend_request_status enum
    op.execute("DROP TYPE friend_request_status")

