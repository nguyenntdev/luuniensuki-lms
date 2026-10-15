//! Friend streak business logic.
//!
//! NOTE: Production schema does not include a `user_friendships` table — only
//! `friend_requests`. Strict mutual-follow enforcement is therefore deferred:
//! - `list_my_friend_streaks` and `get_friend_streak` simply read the
//!   canonical-pair rows that already exist in `friend_streaks`.
//! - `increment_for_pair` is provided as a helper for any future caller that
//!   wants to advance the counter once the friendship model lands.
//!
//! Spec: `.kiro/specs/streak-repair-economy/`

use axum::http::StatusCode;
use chrono::Utc;
use serde_json::json;
use sqlx::PgPool;
use uuid::Uuid;

use crate::error::AppError;
use crate::models::streak_economy::FriendStreakOut;

/// Canonical pair: smaller UUID first (matches the `canonical_pair` CHECK
/// constraint on `friend_streaks`).
pub fn canonical_pair(a: Uuid, b: Uuid) -> (Uuid, Uuid) {
    if a < b {
        (a, b)
    } else {
        (b, a)
    }
}

/// `GET /api/v1/users/me/friend-streaks` — list all friend streaks for me.
pub async fn list_my_friend_streaks(
    pool: &PgPool,
    user_id: Uuid,
) -> Result<Vec<FriendStreakOut>, AppError> {
    let rows = sqlx::query_as::<_, FriendStreakOut>(
        r#"
        SELECT
            CASE WHEN fs.user_a_id = $1 THEN fs.user_b_id ELSE fs.user_a_id END
                AS friend_user_id,
            u.display_name AS friend_display_name,
            u.avatar_url   AS friend_avatar_url,
            fs.current_count,
            fs.longest_count,
            fs.last_increment_date,
            (fs.last_increment_date = (NOW() AT TIME ZONE 'UTC')::date) AS is_alive
        FROM friend_streaks fs
        JOIN users u
          ON u.id = CASE WHEN fs.user_a_id = $1 THEN fs.user_b_id ELSE fs.user_a_id END
        WHERE fs.user_a_id = $1 OR fs.user_b_id = $1
        ORDER BY fs.current_count DESC, fs.updated_at DESC
        "#,
    )
    .bind(user_id)
    .fetch_all(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    Ok(rows)
}

/// `GET /api/v1/users/:other_id/friend-streak` — fetch the canonical-pair row.
///
/// Returns 404 if no `friend_streaks` row exists for the pair.
pub async fn get_friend_streak(
    pool: &PgPool,
    user_id: Uuid,
    other_id: Uuid,
) -> Result<FriendStreakOut, AppError> {
    if user_id == other_id {
        return Err(AppError::Domain {
            status: StatusCode::BAD_REQUEST,
            code: "INVALID_FRIEND".to_string(),
            message: "Cannot fetch a friend streak with yourself".to_string(),
            details: json!({}),
        });
    }

    let (a, b) = canonical_pair(user_id, other_id);

    let row = sqlx::query_as::<_, FriendStreakOut>(
        r#"
        SELECT
            CASE WHEN fs.user_a_id = $1 THEN fs.user_b_id ELSE fs.user_a_id END
                AS friend_user_id,
            u.display_name AS friend_display_name,
            u.avatar_url   AS friend_avatar_url,
            fs.current_count,
            fs.longest_count,
            fs.last_increment_date,
            (fs.last_increment_date = (NOW() AT TIME ZONE 'UTC')::date) AS is_alive
        FROM friend_streaks fs
        JOIN users u
          ON u.id = CASE WHEN fs.user_a_id = $1 THEN fs.user_b_id ELSE fs.user_a_id END
        WHERE fs.user_a_id = $2 AND fs.user_b_id = $3
        LIMIT 1
        "#,
    )
    .bind(user_id)
    .bind(a)
    .bind(b)
    .fetch_optional(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    row.ok_or_else(|| AppError::Http {
        status: StatusCode::NOT_FOUND,
        message: "No friend streak between these users".to_string(),
    })
}

/// Increment a friend streak for the canonical pair.
///
/// Idempotent per UTC day: a second call within the same date is a no-op.
/// TODO: gate the caller on a future `user_friendships` mutual-follow check.
#[allow(dead_code)]
pub async fn increment_for_pair(pool: &PgPool, user_a: Uuid, user_b: Uuid) -> Result<(), AppError> {
    if user_a == user_b {
        return Ok(());
    }
    let (a, b) = canonical_pair(user_a, user_b);

    sqlx::query(
        r#"
        INSERT INTO friend_streaks
            (user_a_id, user_b_id, current_count, longest_count, last_increment_date, updated_at)
        VALUES ($1, $2, 1, 1, (NOW() AT TIME ZONE 'UTC')::date, NOW())
        ON CONFLICT (user_a_id, user_b_id) DO UPDATE
        SET current_count = CASE
                WHEN friend_streaks.last_increment_date = (NOW() AT TIME ZONE 'UTC')::date
                    THEN friend_streaks.current_count
                WHEN friend_streaks.last_increment_date = (NOW() AT TIME ZONE 'UTC')::date - INTERVAL '1 day'
                    THEN friend_streaks.current_count + 1
                ELSE 1
            END,
            longest_count = GREATEST(friend_streaks.longest_count, CASE
                WHEN friend_streaks.last_increment_date = (NOW() AT TIME ZONE 'UTC')::date
                    THEN friend_streaks.current_count
                WHEN friend_streaks.last_increment_date = (NOW() AT TIME ZONE 'UTC')::date - INTERVAL '1 day'
                    THEN friend_streaks.current_count + 1
                ELSE 1
            END),
            last_increment_date = (NOW() AT TIME ZONE 'UTC')::date,
            updated_at = NOW()
        WHERE friend_streaks.last_increment_date IS DISTINCT FROM (NOW() AT TIME ZONE 'UTC')::date
        "#,
    )
    .bind(a)
    .bind(b)
    .execute(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    tracing::info!(
        feature = "friend_streak_increment",
        user_a = %a,
        user_b = %b,
        "friend streak increment"
    );

    crate::routes::metrics::FRIEND_STREAK_INCREMENT_TOTAL
        .fetch_add(1, std::sync::atomic::Ordering::Relaxed);

    let _ = Utc::now();
    Ok(())
}
