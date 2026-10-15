"""compound indexes for user daily missions and weekly quests

Adds compound indexes:
- `idx_user_daily_missions_user_date` on `user_daily_missions(user_id, mission_date)`
- `idx_user_weekly_quests_user_week` on `user_weekly_quests(user_id, week_start_date)`

These optimize queries filtering progress by user and mission/week date.

All additive and reversible.

Revision ID: 0053_user_mission_quest_compound_indexes
Revises: 0052_history_collections
Create Date: 2026-09-06
"""
from __future__ import annotations

from alembic import op


revision = "0053_user_mission_quest_compound_indexes"
down_revision = "0052_history_collections"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_user_daily_missions_user_date "
        "ON user_daily_missions(user_id, mission_date)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_user_weekly_quests_user_week "
        "ON user_weekly_quests(user_id, week_start_date)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_user_weekly_quests_user_week")
    op.execute("DROP INDEX IF EXISTS idx_user_daily_missions_user_date")
