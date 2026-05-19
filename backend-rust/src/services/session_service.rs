//! Session and Analytics business logic.
//!
//! Phase 11 (Tasks 12.1–12.2): Sessions, Heartbeat, Analytics Events migration.

use chrono::Utc;
use sqlx::PgPool;
use uuid::Uuid;

use crate::error::AppError;
use crate::models::session::*;

/// POST /api/v1/sessions/heartbeat — session heartbeat.
/// Creates a new session if session_id is None, otherwise updates the heartbeat.
pub async fn heartbeat(
    pool: &PgPool,
    user_id: Uuid,
    req: HeartbeatRequest,
) -> Result<HeartbeatResponse, AppError> {
    let now = Utc::now();

    if let Some(session_id) = req.session_id {
        // Update existing session heartbeat
        sqlx::query(
            "UPDATE user_sessions SET last_heartbeat_at = $1 WHERE id = $2 AND user_id = $3 AND ended_at IS NULL",
        )
        .bind(now)
        .bind(session_id)
        .bind(user_id)
        .execute(pool)
        .await
        .map_err(|e| AppError::Internal(e.into()))?;

        Ok(HeartbeatResponse {
            session_id,
            last_heartbeat_at: now,
        })
    } else {
        // Create a new session
        let session_id = Uuid::new_v4();
        sqlx::query(
            r#"
            INSERT INTO user_sessions (id, user_id, started_at, last_heartbeat_at, device_info)
            VALUES ($1, $2, $3, $4, $5)
            "#,
        )
        .bind(session_id)
        .bind(user_id)
        .bind(now)
        .bind(now)
        .bind(&req.device_info)
        .execute(pool)
        .await
        .map_err(|e| AppError::Internal(e.into()))?;

        Ok(HeartbeatResponse {
            session_id,
            last_heartbeat_at: now,
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

    let row = sqlx::query_as::<_, UserSessionRow>(
        r#"
        UPDATE user_sessions
        SET ended_at = $1,
            duration_seconds = EXTRACT(EPOCH FROM ($1 - started_at))::bigint
        WHERE id = $2 AND user_id = $3 AND ended_at IS NULL
        RETURNING id, user_id, started_at, last_heartbeat_at, ended_at, duration_seconds, device_info
        "#,
    )
    .bind(now)
    .bind(req.session_id)
    .bind(user_id)
    .fetch_optional(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?
    .ok_or_else(|| AppError::Http {
        status: axum::http::StatusCode::NOT_FOUND,
        message: "Session not found or already ended".to_string(),
    })?;

    Ok(EndSessionResponse {
        session_id: row.id,
        ended_at: row.ended_at.unwrap_or(now),
        duration_seconds: row.duration_seconds.unwrap_or(0),
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
            INSERT INTO analytics_events (id, user_id, event_type, event_data, created_at)
            VALUES ($1, $2, $3, $4, $5)
            "#,
        )
        .bind(Uuid::new_v4())
        .bind(user_id)
        .bind(&event.event_type)
        .bind(&event.event_data)
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
        SELECT id, user_id, started_at, last_heartbeat_at, device_info
        FROM user_sessions
        WHERE ended_at IS NULL
          AND last_heartbeat_at > NOW() - INTERVAL '5 minutes'
        ORDER BY last_heartbeat_at DESC
        "#,
    )
    .fetch_all(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    let total = rows.len() as i64;
    let sessions = rows
        .into_iter()
        .map(|r| ActiveSessionOut {
            session_id: r.id,
            user_id: r.user_id,
            started_at: r.started_at,
            last_heartbeat_at: r.last_heartbeat_at,
            device_info: r.device_info,
        })
        .collect();

    Ok(ActiveSessionsResponse { sessions, total })
}

/// GET /api/v1/admin/analytics/sessions/stats — admin: session stats.
pub async fn get_session_stats(pool: &PgPool) -> Result<SessionStatsResponse, AppError> {
    let stats = sqlx::query_as::<_, SessionStatsRow>(
        r#"
        SELECT
            (SELECT COUNT(*) FROM user_sessions WHERE ended_at IS NULL AND last_heartbeat_at > NOW() - INTERVAL '5 minutes') AS active_sessions,
            (SELECT COUNT(*) FROM user_sessions WHERE started_at::date = CURRENT_DATE) AS total_sessions_today,
            (SELECT AVG(duration_seconds) FROM user_sessions WHERE ended_at IS NOT NULL AND duration_seconds IS NOT NULL) AS avg_duration_seconds
        "#,
    )
    .fetch_one(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    Ok(SessionStatsResponse {
        active_sessions: stats.active_sessions,
        total_sessions_today: stats.total_sessions_today,
        avg_duration_seconds: stats.avg_duration_seconds.unwrap_or(0.0),
    })
}
