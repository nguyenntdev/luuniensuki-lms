//! Notification business logic.
//!
//! Phase 10 (Tasks 11.1–11.3): Notifications migration.

use chrono::Utc;
use sqlx::PgPool;
use uuid::Uuid;

use crate::error::AppError;
use crate::models::notification::*;

/// GET /api/v1/notifications/settings — get notification settings.
pub async fn get_settings(pool: &PgPool, user_id: Uuid) -> Result<NotificationSettingsOut, AppError> {
    let row = sqlx::query_as::<_, NotificationSettingsRow>(
        r#"
        SELECT user_id, push_enabled, email_enabled, streak_reminders,
               lesson_reminders, social_notifications, marketing_notifications
        FROM notification_settings
        WHERE user_id = $1
        "#,
    )
    .bind(user_id)
    .fetch_optional(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    match row {
        Some(r) => Ok(NotificationSettingsOut {
            user_id: r.user_id,
            push_enabled: r.push_enabled,
            email_enabled: r.email_enabled,
            streak_reminders: r.streak_reminders,
            lesson_reminders: r.lesson_reminders,
            social_notifications: r.social_notifications,
            marketing_notifications: r.marketing_notifications,
        }),
        None => {
            // Return defaults if no settings row exists
            Ok(NotificationSettingsOut {
                user_id,
                push_enabled: true,
                email_enabled: true,
                streak_reminders: true,
                lesson_reminders: true,
                social_notifications: true,
                marketing_notifications: false,
            })
        }
    }
}

/// PUT /api/v1/notifications/settings — update notification settings.
pub async fn update_settings(
    pool: &PgPool,
    user_id: Uuid,
    req: UpdateNotificationSettingsRequest,
) -> Result<NotificationSettingsOut, AppError> {
    let row = sqlx::query_as::<_, NotificationSettingsRow>(
        r#"
        INSERT INTO notification_settings (user_id, push_enabled, email_enabled, streak_reminders,
            lesson_reminders, social_notifications, marketing_notifications)
        VALUES ($1, COALESCE($2, true), COALESCE($3, true), COALESCE($4, true),
                COALESCE($5, true), COALESCE($6, true), COALESCE($7, false))
        ON CONFLICT (user_id) DO UPDATE SET
            push_enabled = COALESCE($2, notification_settings.push_enabled),
            email_enabled = COALESCE($3, notification_settings.email_enabled),
            streak_reminders = COALESCE($4, notification_settings.streak_reminders),
            lesson_reminders = COALESCE($5, notification_settings.lesson_reminders),
            social_notifications = COALESCE($6, notification_settings.social_notifications),
            marketing_notifications = COALESCE($7, notification_settings.marketing_notifications)
        RETURNING user_id, push_enabled, email_enabled, streak_reminders,
                  lesson_reminders, social_notifications, marketing_notifications
        "#,
    )
    .bind(user_id)
    .bind(req.push_enabled)
    .bind(req.email_enabled)
    .bind(req.streak_reminders)
    .bind(req.lesson_reminders)
    .bind(req.social_notifications)
    .bind(req.marketing_notifications)
    .fetch_one(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    Ok(NotificationSettingsOut {
        user_id: row.user_id,
        push_enabled: row.push_enabled,
        email_enabled: row.email_enabled,
        streak_reminders: row.streak_reminders,
        lesson_reminders: row.lesson_reminders,
        social_notifications: row.social_notifications,
        marketing_notifications: row.marketing_notifications,
    })
}

/// POST /api/v1/notifications/register-push — register push token.
pub async fn register_push(
    pool: &PgPool,
    user_id: Uuid,
    req: RegisterPushRequest,
) -> Result<PushTokenResponse, AppError> {
    sqlx::query(
        r#"
        INSERT INTO push_tokens (id, user_id, token, platform, created_at)
        VALUES ($1, $2, $3, $4, $5)
        ON CONFLICT (user_id, token) DO UPDATE SET platform = $4
        "#,
    )
    .bind(Uuid::new_v4())
    .bind(user_id)
    .bind(&req.token)
    .bind(&req.platform)
    .bind(Utc::now())
    .execute(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    Ok(PushTokenResponse {
        success: true,
        message: "Push token registered".to_string(),
    })
}

/// DELETE /api/v1/notifications/unregister-push — unregister push token.
pub async fn unregister_push(
    pool: &PgPool,
    user_id: Uuid,
    req: UnregisterPushRequest,
) -> Result<PushTokenResponse, AppError> {
    sqlx::query("DELETE FROM push_tokens WHERE user_id = $1 AND token = $2")
        .bind(user_id)
        .bind(&req.token)
        .execute(pool)
        .await
        .map_err(|e| AppError::Internal(e.into()))?;

    Ok(PushTokenResponse {
        success: true,
        message: "Push token unregistered".to_string(),
    })
}

/// GET /api/v1/notifications/history — notification history (paginated).
pub async fn get_history(
    pool: &PgPool,
    user_id: Uuid,
    page: i32,
    per_page: i32,
) -> Result<NotificationHistoryResponse, AppError> {
    let offset = (page - 1).max(0) * per_page;

    let total: (i64,) = sqlx::query_as(
        "SELECT COUNT(*) FROM notifications WHERE user_id = $1",
    )
    .bind(user_id)
    .fetch_one(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    let rows = sqlx::query_as::<_, NotificationHistoryRow>(
        r#"
        SELECT id, notification_type, title, body, data, read, created_at
        FROM notifications
        WHERE user_id = $1
        ORDER BY created_at DESC
        LIMIT $2 OFFSET $3
        "#,
    )
    .bind(user_id)
    .bind(per_page as i64)
    .bind(offset as i64)
    .fetch_all(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    let notifications = rows
        .into_iter()
        .map(|r| NotificationHistoryItem {
            id: r.id,
            notification_type: r.notification_type,
            title: r.title,
            body: r.body,
            data: r.data,
            read: r.read,
            created_at: r.created_at,
        })
        .collect();

    Ok(NotificationHistoryResponse {
        notifications,
        total: total.0,
        page,
        per_page,
    })
}

/// GET /api/v1/notifications/should-prompt-permission — should prompt for push permission.
pub async fn should_prompt_permission(
    pool: &PgPool,
    user_id: Uuid,
) -> Result<ShouldPromptPermissionResponse, AppError> {
    // Check if user already has push tokens registered
    let token_count: (i64,) = sqlx::query_as(
        "SELECT COUNT(*) FROM push_tokens WHERE user_id = $1",
    )
    .bind(user_id)
    .fetch_one(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    if token_count.0 > 0 {
        return Ok(ShouldPromptPermissionResponse {
            should_prompt: false,
            reason: Some("already_registered".to_string()),
        });
    }

    // Check notification settings
    let settings = sqlx::query_as::<_, NotificationSettingsRow>(
        "SELECT user_id, push_enabled, email_enabled, streak_reminders, lesson_reminders, social_notifications, marketing_notifications FROM notification_settings WHERE user_id = $1",
    )
    .bind(user_id)
    .fetch_optional(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    if let Some(s) = settings {
        if !s.push_enabled {
            return Ok(ShouldPromptPermissionResponse {
                should_prompt: false,
                reason: Some("push_disabled".to_string()),
            });
        }
    }

    Ok(ShouldPromptPermissionResponse {
        should_prompt: true,
        reason: None,
    })
}
