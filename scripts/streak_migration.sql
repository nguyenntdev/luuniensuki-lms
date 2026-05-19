BEGIN;

CREATE TABLE IF NOT EXISTS streak_repair_events (
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
CREATE INDEX IF NOT EXISTS idx_streak_repair_user ON streak_repair_events(user_id);
CREATE INDEX IF NOT EXISTS idx_streak_repair_repaired_at ON streak_repair_events(repaired_at DESC);
CREATE UNIQUE INDEX IF NOT EXISTS idx_streak_repair_idempotency
    ON streak_repair_events(user_id, idempotency_key)
    WHERE idempotency_key IS NOT NULL;

CREATE TABLE IF NOT EXISTS streak_protection_events (
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
CREATE INDEX IF NOT EXISTS idx_streak_protection_event ON streak_protection_events(event_id);
CREATE INDEX IF NOT EXISTS idx_streak_protection_user ON streak_protection_events(user_id);
CREATE INDEX IF NOT EXISTS idx_streak_protection_actor ON streak_protection_events(actor_user_id);

CREATE TABLE IF NOT EXISTS friend_streaks (
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
CREATE INDEX IF NOT EXISTS idx_friend_streaks_a ON friend_streaks(user_a_id);
CREATE INDEX IF NOT EXISTS idx_friend_streaks_b ON friend_streaks(user_b_id);

CREATE TABLE IF NOT EXISTS user_streak_history (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    streak_value integer NOT NULL,
    streak_started_at timestamptz NOT NULL,
    streak_ended_at timestamptz NOT NULL DEFAULT NOW(),
    phoenix_awarded boolean NOT NULL DEFAULT false,
    created_at timestamptz NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_streak_history_user ON user_streak_history(user_id);
CREATE INDEX IF NOT EXISTS idx_streak_history_ended_at ON user_streak_history(streak_ended_at DESC);

CREATE TABLE IF NOT EXISTS user_comeback_bonuses (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    multiplier numeric(4,2) NOT NULL DEFAULT 2.0,
    started_at timestamptz NOT NULL DEFAULT NOW(),
    expires_at timestamptz NOT NULL,
    history_row_id uuid REFERENCES user_streak_history(id) ON DELETE SET NULL,
    created_at timestamptz NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_comeback_active ON user_comeback_bonuses(user_id, expires_at);

CREATE TABLE IF NOT EXISTS streak_insurance_subscriptions (
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
CREATE UNIQUE INDEX IF NOT EXISTS idx_insurance_active ON streak_insurance_subscriptions(user_id)
    WHERE status = 'active';

INSERT INTO badges (id, slug, name, name_en, description, icon_url, category, is_active, is_secret, xp_bonus, unlock_criteria)
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
    100,
    '{"type":"streak_comeback","min_lost_streak":30,"comeback_days":3}'::jsonb
)
ON CONFLICT (slug) DO NOTHING;

COMMIT;
