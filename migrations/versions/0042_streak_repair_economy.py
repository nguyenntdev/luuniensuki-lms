"""streak repair economy

Adds 6 new tables for the streak repair economy feature:
- streak_repair_events
- streak_protection_events (BRB)
- friend_streaks
- user_streak_history
- user_comeback_bonuses
- streak_insurance_subscriptions

All additive — no existing tables modified.

Revision ID: 0042_streak_repair_economy
Revises: 0041_live_rate_limit_logs
Create Date: 2026-05-19
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0042_streak_repair_economy"
down_revision = "0041"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE streak_repair_events (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            payment_method text NOT NULL CHECK (payment_method IN ('hearts','xp','admin_grant')),
            payment_amount integer NOT NULL DEFAULT 0,
            streak_before_loss integer NOT NULL,
            streak_restored_to integer NOT NULL,
            lost_at timestamptz NOT NULL,
            repaired_at timestamptz NOT NULL DEFAULT NOW(),
            idempotency_key text,
            notes text,
            actor_user_id uuid REFERENCES users(id) ON DELETE SET NULL,
            created_at timestamptz NOT NULL DEFAULT NOW()
        );
        CREATE INDEX idx_streak_repair_user ON streak_repair_events(user_id);
        CREATE INDEX idx_streak_repair_repaired_at ON streak_repair_events(repaired_at DESC);
        CREATE UNIQUE INDEX idx_streak_repair_idempotency
            ON streak_repair_events(user_id, idempotency_key)
            WHERE idempotency_key IS NOT NULL;
        """
    )

    op.execute(
        """
        CREATE TABLE streak_protection_events (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            event_id uuid NOT NULL,
            user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            actor_user_id uuid NOT NULL REFERENCES users(id) ON DELETE SET NULL,
            reason text NOT NULL,
            effective_from timestamptz NOT NULL,
            effective_to timestamptz NOT NULL,
            applied_at timestamptz NOT NULL DEFAULT NOW(),
            created_at timestamptz NOT NULL DEFAULT NOW()
        );
        CREATE INDEX idx_streak_protection_event ON streak_protection_events(event_id);
        CREATE INDEX idx_streak_protection_user ON streak_protection_events(user_id);
        CREATE INDEX idx_streak_protection_actor ON streak_protection_events(actor_user_id);
        """
    )

    op.execute(
        """
        CREATE TABLE friend_streaks (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            user_a_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            user_b_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            current_count integer NOT NULL DEFAULT 0,
            longest_count integer NOT NULL DEFAULT 0,
            last_increment_date date,
            created_at timestamptz NOT NULL DEFAULT NOW(),
            updated_at timestamptz NOT NULL DEFAULT NOW(),
            CONSTRAINT canonical_pair CHECK (user_a_id < user_b_id),
            UNIQUE (user_a_id, user_b_id)
        );
        CREATE INDEX idx_friend_streaks_a ON friend_streaks(user_a_id);
        CREATE INDEX idx_friend_streaks_b ON friend_streaks(user_b_id);
        """
    )

    op.execute(
        """
        CREATE TABLE user_streak_history (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            streak_value integer NOT NULL,
            streak_started_at timestamptz NOT NULL,
            streak_ended_at timestamptz NOT NULL DEFAULT NOW(),
            phoenix_awarded boolean NOT NULL DEFAULT false,
            created_at timestamptz NOT NULL DEFAULT NOW()
        );
        CREATE INDEX idx_streak_history_user ON user_streak_history(user_id);
        CREATE INDEX idx_streak_history_ended_at ON user_streak_history(streak_ended_at DESC);
        """
    )

    op.execute(
        """
        CREATE TABLE user_comeback_bonuses (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            multiplier numeric(4,2) NOT NULL DEFAULT 2.0,
            started_at timestamptz NOT NULL DEFAULT NOW(),
            expires_at timestamptz NOT NULL,
            history_row_id uuid REFERENCES user_streak_history(id) ON DELETE SET NULL,
            created_at timestamptz NOT NULL DEFAULT NOW()
        );
        CREATE INDEX idx_comeback_active ON user_comeback_bonuses(user_id) WHERE expires_at > NOW();
        """
    )

    op.execute(
        """
        CREATE TABLE streak_insurance_subscriptions (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            status text NOT NULL CHECK (status IN ('active','cancelled','expired','pending')),
            started_at timestamptz NOT NULL,
            expires_at timestamptz NOT NULL,
            provider text NOT NULL,
            provider_subscription_id text,
            auto_brb_enabled boolean NOT NULL DEFAULT true,
            granted_by_user_id uuid REFERENCES users(id) ON DELETE SET NULL,
            grant_reason text,
            created_at timestamptz NOT NULL DEFAULT NOW(),
            updated_at timestamptz NOT NULL DEFAULT NOW()
        );
        CREATE UNIQUE INDEX idx_insurance_active ON streak_insurance_subscriptions(user_id)
            WHERE status = 'active';
        """
    )

    op.execute(
        """
        INSERT INTO badges (id, slug, name, name_en, description, icon_url, category, is_active, is_secret, xp_bonus)
        VALUES (
            gen_random_uuid(),
            'phoenix',
            'Phượng Hoàng Tái Sinh',
            'Phoenix Reborn',
            'Quay lại sau khi mất chuỗi 30 ngày trở lên và học 3 ngày liên tiếp',
            '/assets/badges/phoenix.svg',
            'achievement',
            true,
            false,
            100
        )
        ON CONFLICT (slug) DO NOTHING;
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS streak_insurance_subscriptions CASCADE")
    op.execute("DROP TABLE IF EXISTS user_comeback_bonuses CASCADE")
    op.execute("DROP TABLE IF EXISTS user_streak_history CASCADE")
    op.execute("DROP TABLE IF EXISTS friend_streaks CASCADE")
    op.execute("DROP TABLE IF EXISTS streak_protection_events CASCADE")
    op.execute("DROP TABLE IF EXISTS streak_repair_events CASCADE")
    op.execute("DELETE FROM badges WHERE slug = 'phoenix'")
