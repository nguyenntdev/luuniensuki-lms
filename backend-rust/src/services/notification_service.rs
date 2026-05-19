//! Notification business logic.
//!
//! Phase 10 (Tasks 11.1–11.3): Notifications migration.
//! Fixed to match actual production schema:
//! - Settings: `user_notification_settings` table
//! - Push token: stored in `user_notification_settings.push_token` + `push_platform`
//! - History: `push_notifications` table

use sqlx::PgPool;
use uuid::Uuid;

use crate::error::AppError;
use crate::models::notification::*;

/// GET /api/v1/notifications/settings — get notification settings.
pub async fn get_settings(pool: &PgPool, user_id: Uuid) -> Result<NotificationSettingsOut, AppError> {
    let row = sqlx::query_as::<_, NotificationSettingsRow>(
        r#"
        SELECT user_id, push_enabled, email_enabled, streak_reminders,
               daily_mission_reminders, weekly_digest, marketing_enabled,
               quiet_hours_start, quiet_hours_end
        FROM user_notification_settings
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
            daily_mission_reminders: r.daily_mission_reminders,
            weekly_digest: r.weekly_digest,
            marketing_enabled: r.marketing_enabled,
            quiet_hours_start: r.quiet_hours_start,
            quiet_hours_end: r.quiet_hours_end,
        }),
        None => {
            // Return defaults if no settings row exists
            Ok(NotificationSettingsOut {
                user_id,
                push_enabled: false,
                email_enabled: true,
                streak_reminders: true,
                daily_mission_reminders: true,
                weekly_digest: true,
                marketing_enabled: false,
                quiet_hours_start: None,
                quiet_hours_end: None,
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
        INSERT INTO user_notification_settings (id, user_id, push_enabled, email_enabled, streak_reminders,
            daily_mission_reminders, weekly_digest, marketing_enabled, quiet_hours_start, quiet_hours_end, updated_at)
        VALUES ($1, $2, COALESCE($3, false), COALESCE($4, true), COALESCE($5, true),
                COALESCE($6, true), COALESCE($7, true), COALESCE($8, false), $9, $10, NOW())
        ON CONFLICT (user_id) DO UPDATE SET
            push_enabled = COALESCE($3, user_notification_settings.push_enabled),
            email_enabled = COALESCE($4, user_notification_settings.email_enabled),
            streak_reminders = COALESCE($5, user_notification_settings.streak_reminders),
            daily_mission_reminders = COALESCE($6, user_notification_settings.daily_mission_reminders),
            weekly_digest = COALESCE($7, user_notification_settings.weekly_digest),
            marketing_enabled = COALESCE($8, user_notification_settings.marketing_enabled),
            quiet_hours_start = COALESCE($9, user_notification_settings.quiet_hours_start),
            quiet_hours_end = COALESCE($10, user_notification_settings.quiet_hours_end),
            updated_at = NOW()
        RETURNING user_id, push_enabled, email_enabled, streak_reminders,
                  daily_mission_reminders, weekly_digest, marketing_enabled,
                  quiet_hours_start, quiet_hours_end
        "#,
    )
    .bind(Uuid::new_v4())
    .bind(user_id)
    .bind(req.push_enabled)
    .bind(req.email_enabled)
    .bind(req.streak_reminders)
    .bind(req.daily_mission_reminders)
    .bind(req.weekly_digest)
    .bind(req.marketing_enabled)
    .bind(req.quiet_hours_start)
    .bind(req.quiet_hours_end)
    .fetch_one(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    Ok(NotificationSettingsOut {
        user_id: row.user_id,
        push_enabled: row.push_enabled,
        email_enabled: row.email_enabled,
        streak_reminders: row.streak_reminders,
        daily_mission_reminders: row.daily_mission_reminders,
        weekly_digest: row.weekly_digest,
        marketing_enabled: row.marketing_enabled,
        quiet_hours_start: row.quiet_hours_start,
        quiet_hours_end: row.quiet_hours_end,
    })
}

/// POST /api/v1/notifications/register-push — register push token.
/// Push token is stored in `user_notification_settings.push_token` + `push_platform`.
pub async fn register_push(
    pool: &PgPool,
    user_id: Uuid,
    req: RegisterPushRequest,
) -> Result<PushTokenResponse, AppError> {
    sqlx::query(
        r#"
        INSERT INTO user_notification_settings (id, user_id, push_token, push_platform, push_enabled, updated_at)
        VALUES ($1, $2, $3, $4, true, NOW())
        ON CONFLICT (user_id) DO UPDATE SET
            push_token = $3,
            push_platform = $4,
            push_enabled = true,
            updated_at = NOW()
        "#,
    )
    .bind(Uuid::new_v4())
    .bind(user_id)
    .bind(&req.token)
    .bind(&req.platform)
    .execute(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    Ok(PushTokenResponse {
        success: true,
        message: "Push token registered".to_string(),
    })
}

/// DELETE /api/v1/notifications/unregister-push — unregister push token.
/// Clears push_token and disables push in `user_notification_settings`.
pub async fn unregister_push(
    pool: &PgPool,
    user_id: Uuid,
    _req: UnregisterPushRequest,
) -> Result<PushTokenResponse, AppError> {
    sqlx::query(
        r#"
        UPDATE user_notification_settings
        SET push_token = NULL, push_enabled = false, updated_at = NOW()
        WHERE user_id = $1
        "#,
    )
    .bind(user_id)
    .execute(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    Ok(PushTokenResponse {
        success: true,
        message: "Push token unregistered".to_string(),
    })
}

/// GET /api/v1/notifications/history — notification history (paginated).
/// Queries `push_notifications` table.
pub async fn get_history(
    pool: &PgPool,
    user_id: Uuid,
    page: i32,
    per_page: i32,
) -> Result<NotificationHistoryResponse, AppError> {
    let offset = (page - 1).max(0) * per_page;

    let total: (i64,) = sqlx::query_as(
        "SELECT COUNT(*) FROM push_notifications WHERE user_id = $1",
    )
    .bind(user_id)
    .fetch_one(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    let rows = sqlx::query_as::<_, NotificationHistoryRow>(
        r#"
        SELECT id, notification_type, title, body, data_payload, status, sent_at, created_at
        FROM push_notifications
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
            data_payload: r.data_payload,
            status: r.status,
            sent_at: r.sent_at,
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
/// Checks if user has push_token set in `user_notification_settings`.
pub async fn should_prompt_permission(
    pool: &PgPool,
    user_id: Uuid,
) -> Result<ShouldPromptPermissionResponse, AppError> {
    // Check if user already has a push token registered
    let row: Option<(Option<String>, bool)> = sqlx::query_as(
        "SELECT push_token, push_enabled FROM user_notification_settings WHERE user_id = $1",
    )
    .bind(user_id)
    .fetch_optional(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    match row {
        Some((Some(_token), _)) => {
            // Already has a push token
            Ok(ShouldPromptPermissionResponse {
                should_prompt: false,
                reason: Some("already_registered".to_string()),
            })
        }
        Some((None, push_enabled)) => {
            if !push_enabled {
                Ok(ShouldPromptPermissionResponse {
                    should_prompt: false,
                    reason: Some("push_disabled".to_string()),
                })
            } else {
                Ok(ShouldPromptPermissionResponse {
                    should_prompt: true,
                    reason: None,
                })
            }
        }
        None => {
            // No settings row — prompt
            Ok(ShouldPromptPermissionResponse {
                should_prompt: true,
                reason: None,
            })
        }
    }
}
