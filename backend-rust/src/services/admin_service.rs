//! Admin push notification business logic.
//!
//! Phase 13 (Tasks 14.1–14.8): Admin migration.
//! Fixed to match actual production schema:
//! - Push notifications: `push_notifications` table with `user_id`, `title`, `body`,
//!   `notification_type`, `data_payload`, `status`, `created_at`

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
    let notification_type = req.notification_type.unwrap_or_else(|| "admin".to_string());

    sqlx::query(
        r#"
        INSERT INTO push_notifications (id, user_id, title, body, notification_type, data_payload, status, created_at)
        VALUES ($1, $2, $3, $4, $5, $6, 'pending', $7)
        "#,
    )
    .bind(id)
    .bind(req.user_id)
    .bind(&req.title)
    .bind(&req.body)
    .bind(&notification_type)
    .bind(&req.data_payload)
    .bind(now)
    .execute(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    Ok(PushNotificationResponse {
        id,
        status: "pending".to_string(),
        created_at: now,
    })
}

/// POST /api/v1/admin/push-notifications/broadcast — broadcast push notification.
/// Inserts a push_notification row for each user that has push_enabled = true.
pub async fn broadcast_push_notification(
    pool: &PgPool,
    req: BroadcastPushRequest,
) -> Result<PushNotificationResponse, AppError> {
    let id = Uuid::new_v4();
    let now = Utc::now();
    let notification_type = req.notification_type.unwrap_or_else(|| "broadcast".to_string());

    // Insert a notification for all users with push enabled
    sqlx::query(
        r#"
        INSERT INTO push_notifications (id, user_id, title, body, notification_type, data_payload, status, created_at)
        SELECT gen_random_uuid(), uns.user_id, $1, $2, $3, $4, 'pending', $5
        FROM user_notification_settings uns
        WHERE uns.push_enabled = true AND uns.push_token IS NOT NULL
        "#,
    )
    .bind(&req.title)
    .bind(&req.body)
    .bind(&notification_type)
    .bind(&req.data_payload)
    .bind(now)
    .execute(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    Ok(PushNotificationResponse {
        id,
        status: "pending".to_string(),
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

    let total: (i64,) = sqlx::query_as("SELECT COUNT(*) FROM push_notifications")
        .fetch_one(pool)
        .await
        .map_err(|e| AppError::Internal(e.into()))?;

    let rows = sqlx::query_as::<_, PushNotificationRow>(
        r#"
        SELECT id, user_id, title, body, notification_type, data_payload, status, sent_at, created_at
        FROM push_notifications
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
            user_id: r.user_id,
            title: r.title,
            body: r.body,
            notification_type: r.notification_type,
            data_payload: r.data_payload,
            status: r.status,
            sent_at: r.sent_at,
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
