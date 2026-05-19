//! Admin push notification business logic.
//!
//! Phase 13 (Tasks 14.1–14.8): Admin migration.

use chrono::Utc;
use sqlx::PgPool;
use uuid::Uuid;

use crate::error::AppError;
use crate::models::admin::*;

/// POST /api/v1/admin/push-notifications/send — send push notification to a user.
pub async fn send_push_notification(
    pool: &PgPool,
    req: SendPushRequest,
) -> Result<PushNotificationResponse, AppError> {
    let id = Uuid::new_v4();
    let now = Utc::now();

    // Count tokens for the target user
    let token_count: (i64,) = sqlx::query_as(
        "SELECT COUNT(*) FROM push_tokens WHERE user_id = $1",
    )
    .bind(req.user_id)
    .fetch_one(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    // Record the notification
    sqlx::query(
        r#"
        INSERT INTO push_notification_log (id, title, body, data, audience, sent_to, created_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        "#,
    )
    .bind(id)
    .bind(&req.title)
    .bind(&req.body)
    .bind(&req.data)
    .bind(format!("user:{}", req.user_id))
    .bind(token_count.0 as i32)
    .bind(now)
    .execute(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    Ok(PushNotificationResponse {
        id,
        sent_to: token_count.0 as i32,
        created_at: now,
    })
}

/// POST /api/v1/admin/push-notifications/broadcast — broadcast push notification.
pub async fn broadcast_push_notification(
    pool: &PgPool,
    req: BroadcastPushRequest,
) -> Result<PushNotificationResponse, AppError> {
    let id = Uuid::new_v4();
    let now = Utc::now();

    // Count all registered push tokens
    let token_count: (i64,) = sqlx::query_as(
        "SELECT COUNT(DISTINCT user_id) FROM push_tokens",
    )
    .fetch_one(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    // Record the broadcast
    sqlx::query(
        r#"
        INSERT INTO push_notification_log (id, title, body, data, audience, sent_to, created_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        "#,
    )
    .bind(id)
    .bind(&req.title)
    .bind(&req.body)
    .bind(&req.data)
    .bind(&req.audience)
    .bind(token_count.0 as i32)
    .bind(now)
    .execute(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    Ok(PushNotificationResponse {
        id,
        sent_to: token_count.0 as i32,
        created_at: now,
    })
}

/// GET /api/v1/admin/push-notifications — list push notifications.
pub async fn list_push_notifications(
    pool: &PgPool,
    page: i32,
    per_page: i32,
) -> Result<PushNotificationsListResponse, AppError> {
    let offset = (page - 1).max(0) * per_page;

    let total: (i64,) = sqlx::query_as("SELECT COUNT(*) FROM push_notification_log")
        .fetch_one(pool)
        .await
        .map_err(|e| AppError::Internal(e.into()))?;

    let rows = sqlx::query_as::<_, PushNotificationRow>(
        r#"
        SELECT id, title, body, data, audience, sent_to, created_at
        FROM push_notification_log
        ORDER BY created_at DESC
        LIMIT $1 OFFSET $2
        "#,
    )
    .bind(per_page as i64)
    .bind(offset as i64)
    .fetch_all(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    let notifications = rows
        .into_iter()
        .map(|r| PushNotificationOut {
            id: r.id,
            title: r.title,
            body: r.body,
            data: r.data,
            audience: r.audience,
            sent_to: r.sent_to,
            created_at: r.created_at,
        })
        .collect();

    Ok(PushNotificationsListResponse {
        notifications,
        total: total.0,
        page,
        per_page,
    })
}
