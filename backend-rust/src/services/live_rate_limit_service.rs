//! Live rate-limit buckets (Task 13).
//!
//! DB-backed, cross-process rate limiter for live endpoints. Ports
//! `check_and_record` from `backend/services/live_rate_limits.py` over the
//! reused `live_rate_limit_logs` table.
//!
//! Uses sqlx runtime queries (`query`, `query_scalar`) — NOT the compile-time
//! `query!` macro — matching the other service modules in this crate.
//!
//! `live_rate_limit_logs` columns (migration `0041_live_rate_limit_logs.py`):
//!   id UUID PK, bucket VARCHAR(64) NOT NULL, user_id UUID NOT NULL,
//!   live_session_id UUID NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT now()
//!
//! ## Ported limit/window values
//!
//! The Python `check_and_record` takes `max_requests`/`window_seconds` as
//! arguments; the concrete values live at the call sites in `backend/main.py`.
//! Both the `token` and `join` buckets call the limiter with `ai_path=False`,
//! which resolves (via `backend/config.py`) to:
//!   * `live_rate_limit_requests_per_minute = 120`
//!   * `live_rate_limit_window_seconds      = 60`
//! so both buckets are 120 requests / 60s. The AI buckets (45/min) are not
//! ported here — Task 13 only covers `token` and `join`.
//!
//! Validates: Requirements 12.5

use axum::http::StatusCode;
use chrono::{Duration, Utc};
use serde_json::json;
use sqlx::PgPool;
use uuid::Uuid;

use crate::error::AppError;

/// Requests allowed per window for the live `token`/`join` buckets.
/// Mirrors `settings.live_rate_limit_requests_per_minute` (backend/config.py).
const LIVE_RATE_LIMIT_REQUESTS_PER_MINUTE: i64 = 120;

/// Rolling window length in seconds.
/// Mirrors `settings.live_rate_limit_window_seconds` (backend/config.py).
const LIVE_RATE_LIMIT_WINDOW_SECONDS: i64 = 60;

/// Opportunistic cleanup horizon. Rows older than this are deleted on each
/// call to keep the table small without a separate job — mirrors the Python
/// `now - timedelta(hours=6)` cleanup in `check_and_record`.
const CLEANUP_AGE_HOURS: i64 = 6;

/// Rate-limit buckets ported from the Python live stack.
///
/// Each variant maps to the `bucket` string stored in `live_rate_limit_logs`
/// and carries its own per-window limit. Today both buckets share the same
/// limit/window, but they are modeled per-bucket so they can diverge without
/// touching call sites.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum RateBucket {
    /// Issuing a live access token (`POST /live/.../token`).
    Token,
    /// Joining a live session (`POST /live/.../join`).
    Join,
}

impl RateBucket {
    /// Stable string key persisted in the `bucket` column and returned in the
    /// `RATE_LIMITED` error details. Matches the Python `bucket="token"` /
    /// `bucket="join"` call sites in `backend/main.py`.
    pub fn as_str(&self) -> &'static str {
        match self {
            RateBucket::Token => "token",
            RateBucket::Join => "join",
        }
    }

    /// Maximum number of requests permitted within [`Self::window_seconds`].
    pub fn max_requests(&self) -> i64 {
        match self {
            // Both buckets use `ai_path=False` in Python => 120/min.
            RateBucket::Token | RateBucket::Join => LIVE_RATE_LIMIT_REQUESTS_PER_MINUTE,
        }
    }

    /// Rolling window length in seconds for this bucket.
    pub fn window_seconds(&self) -> i64 {
        match self {
            RateBucket::Token | RateBucket::Join => LIVE_RATE_LIMIT_WINDOW_SECONDS,
        }
    }
}

/// Count recent requests for `(user_id, bucket, window)` and either record the
/// current request or reject it as rate-limited.
///
/// Mirrors `backend/services/live_rate_limits.py::check_and_record`:
///   1. Opportunistically delete log rows older than 6 hours.
///   2. Count rows in the bucket for this user with `created_at >= window_start`
///      (additionally scoped to `session_id` when one is supplied).
///   3. If `count >= max_requests`, return `RATE_LIMITED` (HTTP 429).
///   4. Otherwise insert a fresh log row and return `Ok(())`.
///
/// The Python code clamps both the limit and window up to a minimum of `1`; we
/// replicate that with `.max(1)` so a misconfigured zero can never disable the
/// limiter or produce a non-positive window.
///
/// Validates: Requirements 12.5
pub async fn check_and_record(
    pool: &PgPool,
    user_id: Uuid,
    session_id: Option<Uuid>,
    bucket: RateBucket,
) -> Result<(), AppError> {
    let now = Utc::now();
    let window_seconds = bucket.window_seconds().max(1);
    let max_requests = bucket.max_requests().max(1);
    let window_start = now - Duration::seconds(window_seconds);
    let cleanup_cutoff = now - Duration::hours(CLEANUP_AGE_HOURS);

    // 1. Opportunistic cleanup keeps the table small without a separate job.
    sqlx::query("DELETE FROM live_rate_limit_logs WHERE created_at < $1")
        .bind(cleanup_cutoff)
        .execute(pool)
        .await
        .map_err(|e| AppError::Internal(e.into()))?;

    // 2. Count requests inside the rolling window. The `live_session_id`
    //    filter is only applied when a session id is supplied (the
    //    `$4::uuid IS NULL` short-circuit mirrors the optional WHERE in Python).
    let count: i64 = sqlx::query_scalar::<_, i64>(
        r#"
        SELECT COUNT(id)
        FROM live_rate_limit_logs
        WHERE bucket = $1
          AND user_id = $2
          AND created_at >= $3
          AND ($4::uuid IS NULL OR live_session_id = $4)
        "#,
    )
    .bind(bucket.as_str())
    .bind(user_id)
    .bind(window_start)
    .bind(session_id)
    .fetch_one(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    // 3. Reject when the window is already full (Python uses `>=`).
    if count >= max_requests {
        return Err(AppError::Domain {
            status: StatusCode::TOO_MANY_REQUESTS,
            code: "RATE_LIMITED".to_string(),
            message: "Rate limit exceeded".to_string(),
            details: json!({ "bucket": bucket.as_str() }),
        });
    }

    // 4. Record this request. `id` is generated here; `created_at` uses the DB
    //    clock via `now()` to stay consistent with the count query's source.
    sqlx::query(
        r#"
        INSERT INTO live_rate_limit_logs (id, bucket, user_id, live_session_id, created_at)
        VALUES ($1, $2, $3, $4, now())
        "#,
    )
    .bind(Uuid::new_v4())
    .bind(bucket.as_str())
    .bind(user_id)
    .bind(session_id)
    .execute(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn bucket_as_str_matches_python_keys() {
        // Mirrors `bucket="token"` / `bucket="join"` in backend/main.py.
        assert_eq!(RateBucket::Token.as_str(), "token");
        assert_eq!(RateBucket::Join.as_str(), "join");
    }

    #[test]
    fn bucket_limits_match_ported_values() {
        // backend/config.py: live_rate_limit_requests_per_minute = 120 (both
        // token and join use ai_path=False).
        assert_eq!(RateBucket::Token.max_requests(), 120);
        assert_eq!(RateBucket::Join.max_requests(), 120);
    }

    #[test]
    fn bucket_windows_match_ported_values() {
        // backend/config.py: live_rate_limit_window_seconds = 60.
        assert_eq!(RateBucket::Token.window_seconds(), 60);
        assert_eq!(RateBucket::Join.window_seconds(), 60);
    }

    #[test]
    fn constants_match_python_defaults() {
        assert_eq!(LIVE_RATE_LIMIT_REQUESTS_PER_MINUTE, 120);
        assert_eq!(LIVE_RATE_LIMIT_WINDOW_SECONDS, 60);
        assert_eq!(CLEANUP_AGE_HOURS, 6);
    }
}
