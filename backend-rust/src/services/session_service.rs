//! Session and Analytics business logic.
//!
//! Phase 11 (Tasks 12.1–12.2): Sessions, Heartbeat, Analytics Events migration.
//! Fixed to match actual production schema:
//! - Sessions: `user_sessions` table with `session_id`, `device_type`, `platform`,
//!   `app_version`, `is_active`, `last_active_at`
//! - Analytics: `analytics_events` table with `event_name`, `path`, `payload`,
//!   `session_id`, `cohort`, `event_category`, `device_info`

use chrono::Utc;
use sqlx::PgPool;
use uuid::Uuid;

use crate::error::AppError;
use crate::models::session::*;

/// POST /api/v1/sessions/heartbeat — session heartbeat.
/// Creates a new session if session_id is None, otherwise updates last_active_at.
pub async fn heartbeat(
    pool: &PgPool,
    user_id: Uuid,
    req: HeartbeatRequest,
) -> Result<HeartbeatResponse, AppError> {
    let now = Utc::now();

    if let Some(session_id) = req.session_id {
        // Update existing session heartbeat
        sqlx::query(
            "UPDATE user_sessions SET last_active_at = $1 WHERE session_id = $2 AND user_id = $3 AND is_active = true",
        )
        .bind(now)
        .bind(session_id)
        .bind(user_id)
        .execute(pool)
        .await
        .map_err(|e| AppError::Internal(e.into()))?;

        Ok(HeartbeatResponse {
            session_id,
            last_active_at: now,
        })
    } else {
        // Create a new session
        let session_id = Uuid::new_v4();
        let device_type = req.device_type.unwrap_or_else(|| "unknown".to_string());
        let platform = req.platform.unwrap_or_else(|| "unknown".to_string());

        sqlx::query(
            r#"
            INSERT INTO user_sessions (id, user_id, session_id, started_at, last_active_at, device_type, platform, app_version, is_active)
            VALUES ($1, $2, $3, $4, $4, $5, $6, $7, true)
            "#,
        )
        .bind(Uuid::new_v4())
        .bind(user_id)
        .bind(session_id)
        .bind(now)
        .bind(&device_type)
        .bind(&platform)
        .bind(&req.app_version)
        .execute(pool)
        .await
        .map_err(|e| AppError::Internal(e.into()))?;

        Ok(HeartbeatResponse {
            session_id,
            last_active_at: now,
        })
    }
}

/// POST /api/v1/sessions/end — end session.
pub async fn end_session(
    pool: &PgPool,
    user_id: Uuid,
    req: EndSessionRequest,
) -> Result<EndSessionResponse, AppError> {
    let now = Utc::now();

    let result = sqlx::query(
        r#"
        UPDATE user_sessions
        SET ended_at = $1, is_active = false
        WHERE session_id = $2 AND user_id = $3 AND is_active = true
        "#,
    )
    .bind(now)
    .bind(req.session_id)
    .bind(user_id)
    .execute(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    if result.rows_affected() == 0 {
        return Err(AppError::Http {
            status: axum::http::StatusCode::NOT_FOUND,
            message: "Session not found or already ended".to_string(),
        });
    }

    Ok(EndSessionResponse {
        session_id: req.session_id,
        ended_at: now,
    })
}

/// POST /api/v1/analytics/events — ingest analytics events.
pub async fn ingest_events(
    pool: &PgPool,
    user_id: Uuid,
    req: IngestEventsRequest,
) -> Result<IngestEventsResponse, AppError> {
    let now = Utc::now();
    let count = req.events.len() as i32;

    for event in &req.events {
        let ts = event.timestamp.unwrap_or(now);
        sqlx::query(
            r#"
            INSERT INTO analytics_events (id, user_id, event_name, path, payload, session_id, cohort, event_category, device_info, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            "#,
        )
        .bind(Uuid::new_v4())
        .bind(user_id)
        .bind(&event.event_name)
        .bind(&event.path)
        .bind(&event.payload)
        .bind(event.session_id)
        .bind(&event.cohort)
        .bind(&event.event_category)
        .bind(&event.device_info)
        .bind(ts)
        .execute(pool)
        .await
        .map_err(|e| AppError::Internal(e.into()))?;
    }

    Ok(IngestEventsResponse { ingested: count })
}

/// GET /api/v1/admin/analytics/sessions/active — admin: active sessions.
pub async fn get_active_sessions(pool: &PgPool) -> Result<ActiveSessionsResponse, AppError> {
    let rows = sqlx::query_as::<_, ActiveSessionRow>(
        r#"
        SELECT id, session_id, user_id, started_at, last_active_at, device_type, platform
        FROM user_sessions
        WHERE is_active = true
          AND last_active_at > NOW() - INTERVAL '5 minutes'
        ORDER BY last_active_at DESC
        "#,
    )
    .fetch_all(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    let total = rows.len() as i64;
    let sessions = rows
        .into_iter()
        .map(|r| ActiveSessionOut {
            session_id: r.session_id,
            user_id: r.user_id,
            started_at: r.started_at,
            last_active_at: r.last_active_at,
            device_type: r.device_type,
            platform: r.platform,
        })
        .collect();

    Ok(ActiveSessionsResponse { sessions, total })
}

/// GET /api/v1/admin/analytics/sessions/stats — admin: session stats.
pub async fn get_session_stats(pool: &PgPool) -> Result<SessionStatsResponse, AppError> {
    let stats = sqlx::query_as::<_, SessionStatsRow>(
        r#"
        SELECT
            (SELECT COUNT(*) FROM user_sessions WHERE is_active = true AND last_active_at > NOW() - INTERVAL '5 minutes') AS active_sessions,
            (SELECT COUNT(*) FROM user_sessions WHERE started_at::date = CURRENT_DATE) AS total_sessions_today,
            (SELECT AVG(EXTRACT(EPOCH FROM (COALESCE(ended_at, NOW()) - started_at)) / 60.0) FROM user_sessions WHERE started_at::date = CURRENT_DATE) AS avg_session_minutes
        "#,
    )
    .fetch_one(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    Ok(SessionStatsResponse {
        active_sessions: stats.active_sessions,
        total_sessions_today: stats.total_sessions_today,
        avg_session_minutes: stats.avg_session_minutes.unwrap_or(0.0),
    })
}
