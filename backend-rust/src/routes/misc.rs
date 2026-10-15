//! Miscellaneous route handlers.
//!
//! Phase 15 (Tasks 16.1–16.2): Preview, collection, and other leftover routes
//! that don't fit neatly into the previous domain-specific phases.

use axum::{
    extract::State,
    http::{header, HeaderMap, StatusCode},
    response::IntoResponse,
    Json,
};
use serde::{Deserialize, Serialize};
use serde_json::json;
use sqlx::PgPool;
use uuid::Uuid;

use crate::auth;
use crate::config::Settings;
use crate::error::AppError;
use crate::routes::auth::AuthState;

// ---------------------------------------------------------------------------
// Auth helpers (same pattern as other route modules)
// ---------------------------------------------------------------------------

fn extract_token_from_headers(headers: &HeaderMap) -> Option<String> {
    if let Some(auth_header) = headers.get(header::AUTHORIZATION) {
        if let Ok(auth_str) = auth_header.to_str() {
            if let Some(token) = auth_str.strip_prefix("Bearer ") {
                return Some(token.to_string());
            }
        }
    }
    if let Some(cookie_header) = headers.get(header::COOKIE) {
        if let Ok(cookie_str) = cookie_header.to_str() {
            for part in cookie_str.split(';') {
                let trimmed = part.trim();
                if let Some(value) = trimmed.strip_prefix("luuniensuki_access=") {
                    return Some(value.to_string());
                }
            }
        }
    }
    None
}

fn require_pool(pool: &Option<PgPool>) -> Result<&PgPool, AppError> {
    pool.as_ref().ok_or_else(|| AppError::Http {
        status: StatusCode::SERVICE_UNAVAILABLE,
        message: "Database unavailable".to_string(),
    })
}

fn authenticate(
    headers: &HeaderMap,
    settings: &Settings,
) -> Result<(Uuid, auth::Claims), AppError> {
    let token = extract_token_from_headers(headers).ok_or(AppError::Unauthorized)?;
    let claims = auth::verify_access_token(
        &token,
        &settings.jwt_secret_key,
        settings.jwt_validate_new_claims,
        &settings.jwt_issuer,
        &settings.jwt_audience,
    )
    .map_err(|_| AppError::Unauthorized)?;
    let user_id: Uuid = claims.sub.parse().map_err(|_| AppError::Unauthorized)?;
    Ok((user_id, claims))
}

// ---------------------------------------------------------------------------
// DTOs
// ---------------------------------------------------------------------------

/// Response for GET /api/v1/preview/lesson
#[derive(Debug, Serialize)]
pub struct PreviewLessonResponse {
    pub id: String,
    pub title: String,
    pub description: String,
    pub content_type: String,
    pub difficulty: String,
    pub duration_minutes: i32,
    pub preview: bool,
}

/// Request for POST /api/v1/preview/start
#[derive(Debug, Deserialize)]
pub struct StartPreviewRequest {
    pub lesson_id: Option<String>,
    pub device_id: Option<String>,
}

/// Response for POST /api/v1/preview/start
#[derive(Debug, Serialize)]
pub struct StartPreviewResponse {
    pub session_id: String,
    pub lesson_id: String,
    pub started_at: String,
}

/// Request for POST /api/v1/preview/complete
#[derive(Debug, Deserialize)]
pub struct CompletePreviewRequest {
    pub session_id: String,
}

/// Response for POST /api/v1/preview/complete
#[derive(Debug, Serialize)]
pub struct CompletePreviewResponse {
    pub session_id: String,
    pub completed: bool,
    pub message: String,
}

/// Request for POST /api/v1/preview/convert
#[derive(Debug, Deserialize)]
pub struct ConvertPreviewRequest {
    pub session_id: String,
    pub email: String,
    pub password: String,
    pub display_name: String,
}

/// Response for POST /api/v1/preview/convert
#[derive(Debug, Serialize)]
pub struct ConvertPreviewResponse {
    pub user_id: String,
    pub converted: bool,
    pub message: String,
}

/// A single item in the user's collection.
#[derive(Debug, Serialize)]
pub struct CollectionItem {
    pub motif_id: String,
    /// Display name (kept as `motif_name` too for backward compat).
    pub name: String,
    pub motif_name: String,
    pub name_en: Option<String>,
    pub category: Option<String>,
    pub rarity: Option<String>,
    pub thumbnail_url: Option<String>,
    pub status: String,
    pub discovered_at: Option<String>,
}

/// Aggregate counts for the collection overview cards.
#[derive(Debug, Serialize)]
pub struct CollectionStats {
    pub total: i64,
    pub discovered: i64,
    pub learned: i64,
    pub mastered: i64,
}

/// Response for GET /api/v1/users/me/collection
#[derive(Debug, Serialize)]
pub struct CollectionResponse {
    pub items: Vec<CollectionItem>,
    pub total: i64,
    pub stats: CollectionStats,
}

// ---------------------------------------------------------------------------
// Handlers — Preview (no auth required, guest access)
// ---------------------------------------------------------------------------

/// GET /api/v1/preview/lesson — return a preview lesson for guests.
pub async fn get_preview_lesson(
    State(state): State<AuthState>,
) -> Result<impl IntoResponse, AppError> {
    let pool = require_pool(&state.pool)?;

    // Fetch the designated preview lesson (preview-eligible or published lesson_content)
    let row: Option<PreviewLessonRow> = sqlx::query_as(
        "SELECT lc.id, m.name AS title, lc.description, \
         'lesson' AS content_type, \
         COALESCE(lc.difficulty_level::text, 'beginner') AS difficulty, \
         COALESCE(lc.estimated_time_minutes, 5) AS duration_minutes \
         FROM lesson_content lc \
         JOIN motifs m ON m.id = lc.motif_id \
         WHERE lc.preview_eligible = true AND lc.is_published = true \
         ORDER BY lc.created_at ASC LIMIT 1",
    )
    .fetch_optional(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    let row = match row {
        Some(r) => Some(r),
        None => sqlx::query_as(
            "SELECT lc.id, m.name AS title, lc.description, \
             'lesson' AS content_type, \
             COALESCE(lc.difficulty_level::text, 'beginner') AS difficulty, \
             COALESCE(lc.estimated_time_minutes, 5) AS duration_minutes \
             FROM lesson_content lc \
             JOIN motifs m ON m.id = lc.motif_id \
             WHERE lc.is_published = true \
             ORDER BY lc.created_at ASC LIMIT 1",
        )
        .fetch_optional(pool)
        .await
        .map_err(|e| AppError::Internal(e.into()))?,
    };

    match row {
        Some(lesson) => Ok(Json(PreviewLessonResponse {
            id: lesson.id.to_string(),
            title: lesson.title,
            description: lesson.description.unwrap_or_default(),
            content_type: lesson.content_type.unwrap_or_else(|| "lesson".to_string()),
            difficulty: lesson.difficulty.unwrap_or_else(|| "beginner".to_string()),
            duration_minutes: lesson.duration_minutes.unwrap_or(5),
            preview: true,
        })),
        None => Ok(Json(PreviewLessonResponse {
            id: Uuid::nil().to_string(),
            title: "Khám Phá Cửu Đỉnh".to_string(),
            description: "Bài học trải nghiệm khám phá di sản Cửu Đỉnh Huế".to_string(),
            content_type: "lesson".to_string(),
            difficulty: "beginner".to_string(),
            duration_minutes: 5,
            preview: true,
        })),
    }
}

/// POST /api/v1/preview/start — start a guest preview session.
pub async fn start_preview(
    State(state): State<AuthState>,
    Json(body): Json<StartPreviewRequest>,
) -> Result<impl IntoResponse, AppError> {
    let pool = require_pool(&state.pool)?;

    // Determine which lesson to preview
    let lesson_id = if let Some(ref lid) = body.lesson_id {
        Uuid::parse_str(lid).map_err(|_| AppError::Domain {
            status: StatusCode::BAD_REQUEST,
            code: "INVALID_LESSON_ID".to_string(),
            message: "Invalid lesson ID format".to_string(),
            details: json!({}),
        })?
    } else {
        // Default to the first preview lesson
        let row: Option<(Uuid,)> = sqlx::query_as(
            "SELECT id FROM lesson_content WHERE preview_eligible = true AND is_published = true \
             ORDER BY created_at ASC LIMIT 1",
        )
        .fetch_optional(pool)
        .await
        .map_err(|e| AppError::Internal(e.into()))?;

        match row {
            Some((id,)) => id,
            None => {
                let any_row: Option<(Uuid,)> = sqlx::query_as(
                    "SELECT id FROM lesson_content WHERE is_published = true ORDER BY created_at ASC LIMIT 1",
                )
                .fetch_optional(pool)
                .await
                .map_err(|e| AppError::Internal(e.into()))?;

                any_row.map(|(id,)| id).unwrap_or_else(Uuid::nil)
            }
        }
    };

    let session_uuid = Uuid::new_v4();
    let session_id = session_uuid.to_string();
    let now = chrono::Utc::now();
    let lesson_opt = if lesson_id.is_nil() {
        None
    } else {
        Some(lesson_id)
    };
    let device_meta = body.device_id.as_ref().map(|d| json!({ "device_id": d }));

    // Insert guest preview record
    sqlx::query(
        "INSERT INTO guest_previews (id, session_id, preview_lesson_id, started_at, device_info) \
         VALUES ($1, $2, $3, $4, $5)",
    )
    .bind(session_uuid)
    .bind(&session_id)
    .bind(lesson_opt)
    .bind(now)
    .bind(device_meta)
    .execute(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    Ok((
        StatusCode::CREATED,
        Json(StartPreviewResponse {
            session_id,
            lesson_id: lesson_id.to_string(),
            started_at: now.to_rfc3339(),
        }),
    ))
}

/// POST /api/v1/preview/complete — mark a preview session as complete.
pub async fn complete_preview(
    State(state): State<AuthState>,
    Json(body): Json<CompletePreviewRequest>,
) -> Result<impl IntoResponse, AppError> {
    let pool = require_pool(&state.pool)?;

    let session_id_str = body.session_id.trim();
    if session_id_str.is_empty() {
        return Err(AppError::Domain {
            status: StatusCode::BAD_REQUEST,
            code: "INVALID_SESSION_ID".to_string(),
            message: "Invalid session ID format".to_string(),
            details: json!({}),
        });
    }

    let result = sqlx::query(
        "UPDATE guest_previews SET completed_at = NOW() \
         WHERE (session_id = $1 OR id::text = $1) AND completed_at IS NULL",
    )
    .bind(session_id_str)
    .execute(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    if result.rows_affected() == 0 {
        return Err(AppError::Http {
            status: StatusCode::NOT_FOUND,
            message: "Preview session not found or already completed".to_string(),
        });
    }

    Ok(Json(CompletePreviewResponse {
        session_id: body.session_id,
        completed: true,
        message: "Preview completed successfully".to_string(),
    }))
}

/// POST /api/v1/preview/convert — convert a preview session to a registered user.
pub async fn convert_preview(
    State(state): State<AuthState>,
    Json(body): Json<ConvertPreviewRequest>,
) -> Result<impl IntoResponse, AppError> {
    let pool = require_pool(&state.pool)?;

    let session_id_str = body.session_id.trim();
    if session_id_str.is_empty() {
        return Err(AppError::Domain {
            status: StatusCode::BAD_REQUEST,
            code: "INVALID_SESSION_ID".to_string(),
            message: "Invalid session ID format".to_string(),
            details: json!({}),
        });
    }

    // Verify the preview session exists
    let session_exists: Option<(Uuid,)> =
        sqlx::query_as("SELECT id FROM guest_previews WHERE session_id = $1 OR id::text = $1")
            .bind(session_id_str)
            .fetch_optional(pool)
            .await
            .map_err(|e| AppError::Internal(e.into()))?;

    if session_exists.is_none() {
        return Err(AppError::Http {
            status: StatusCode::NOT_FOUND,
            message: "Preview session not found".to_string(),
        });
    }

    // Check if email already taken
    let existing: Option<(Uuid,)> = sqlx::query_as("SELECT id FROM users WHERE email = $1")
        .bind(&body.email)
        .fetch_optional(pool)
        .await
        .map_err(|e| AppError::Internal(e.into()))?;

    if existing.is_some() {
        return Err(AppError::Domain {
            status: StatusCode::CONFLICT,
            code: "EMAIL_ALREADY_REGISTERED".to_string(),
            message: "Email already registered".to_string(),
            details: json!({}),
        });
    }

    // Hash password (bcrypt cost 12, same as auth module)
    let password_hash = auth::hash_password(&body.password).map_err(|e| {
        if matches!(e, auth::AuthError::PasswordTooLong) {
            AppError::Domain {
                status: StatusCode::BAD_REQUEST,
                code: "PASSWORD_TOO_LONG".to_string(),
                message: "Password too long".to_string(),
                details: json!({}),
            }
        } else {
            AppError::Internal(anyhow::anyhow!("{}", e))
        }
    })?;

    // Create the user
    let new_user_id = Uuid::new_v4();
    sqlx::query(
        "INSERT INTO users (id, email, display_name, password_hash, role, created_at, updated_at) \
         VALUES ($1, $2, $3, $4, 'user', NOW(), NOW())",
    )
    .bind(new_user_id)
    .bind(&body.email)
    .bind(&body.display_name)
    .bind(&password_hash)
    .execute(pool)
    .await
    .map_err(|e| {
        if let Some(db_err) = e.as_database_error() {
            if db_err.code().as_deref() == Some("23505") {
                return AppError::Domain {
                    status: StatusCode::CONFLICT,
                    code: "EMAIL_ALREADY_REGISTERED".to_string(),
                    message: "Email already registered".to_string(),
                    details: json!({}),
                };
            }
        }
        AppError::Internal(e.into())
    })?;

    // Link the preview session to the new user
    let _ = sqlx::query(
        "UPDATE guest_previews SET converted_to_user_id = $1 WHERE session_id = $2 OR id::text = $2",
    )
    .bind(new_user_id)
    .bind(session_id_str)
    .execute(pool)
    .await;

    Ok((
        StatusCode::CREATED,
        Json(ConvertPreviewResponse {
            user_id: new_user_id.to_string(),
            converted: true,
            message: "Preview converted to registered account".to_string(),
        }),
    ))
}

// ---------------------------------------------------------------------------
// Handlers — Collection (auth required)
// ---------------------------------------------------------------------------

/// GET /api/v1/users/me/collection — return user's collected motifs.
pub async fn get_user_collection(
    headers: HeaderMap,
    State(state): State<AuthState>,
) -> Result<impl IntoResponse, AppError> {
    let (user_id, _) = authenticate(&headers, &state.settings)?;
    let pool = require_pool(&state.pool)?;

    let items: Vec<CollectionItemRow> = sqlx::query_as(
        "SELECT m.id as motif_id, m.name, m.name_en, \
         m.category::text AS category, m.rarity::text AS rarity, \
         m.thumbnail_url, \
         CASE \
           WHEN up.mastered_at IS NOT NULL THEN 'mastered' \
           WHEN up.learned_at IS NOT NULL THEN 'learned' \
           WHEN up.id IS NOT NULL THEN 'discovered' \
           ELSE 'hidden' \
         END as status, \
         up.created_at as discovered_at \
         FROM motifs m \
         LEFT JOIN user_progress up ON up.motif_id = m.id AND up.user_id = $1 \
         WHERE m.is_active = true \
         ORDER BY m.display_order NULLS LAST, m.name",
    )
    .bind(user_id)
    .fetch_all(pool)
    .await
    .map_err(|e| AppError::Internal(e.into()))?;

    let total = items.len() as i64;
    let mut discovered = 0i64;
    let mut learned = 0i64;
    let mut mastered = 0i64;
    for row in &items {
        match row.status.as_str() {
            "mastered" => mastered += 1,
            "learned" => learned += 1,
            "discovered" => discovered += 1,
            _ => {}
        }
    }

    let collection_items: Vec<CollectionItem> = items
        .into_iter()
        .map(|row| CollectionItem {
            motif_id: row.motif_id.to_string(),
            name: row.name.clone(),
            motif_name: row.name,
            name_en: row.name_en,
            category: row.category,
            rarity: row.rarity,
            thumbnail_url: row.thumbnail_url,
            status: row.status,
            discovered_at: row.discovered_at.map(|dt| dt.to_rfc3339()),
        })
        .collect();

    Ok(Json(CollectionResponse {
        items: collection_items,
        total,
        stats: CollectionStats {
            total,
            discovered,
            learned,
            mastered,
        },
    }))
}

// ---------------------------------------------------------------------------
// Database row types
// ---------------------------------------------------------------------------

#[derive(Debug, sqlx::FromRow)]
struct PreviewLessonRow {
    pub id: Uuid,
    pub title: String,
    pub description: Option<String>,
    pub content_type: Option<String>,
    pub difficulty: Option<String>,
    pub duration_minutes: Option<i32>,
}

#[derive(Debug, sqlx::FromRow)]
struct CollectionItemRow {
    pub motif_id: Uuid,
    pub name: String,
    pub name_en: Option<String>,
    pub category: Option<String>,
    pub rarity: Option<String>,
    pub thumbnail_url: Option<String>,
    pub status: String,
    pub discovered_at: Option<chrono::DateTime<chrono::Utc>>,
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

#[cfg(test)]
mod tests {
    use super::*;
    use axum::{
        body::Body,
        http::Request,
        routing::{get, post},
        Router,
    };
    use tower::ServiceExt;

    fn test_auth_state() -> AuthState {
        let settings = crate::config::Settings::from_env().unwrap();
        AuthState {
            pool: None,
            settings,
        }
    }

    fn test_router() -> Router {
        let state = test_auth_state();
        Router::new()
            .route("/api/v1/preview/lesson", get(get_preview_lesson))
            .route("/api/v1/preview/start", post(start_preview))
            .route("/api/v1/preview/complete", post(complete_preview))
            .route("/api/v1/preview/convert", post(convert_preview))
            .route("/api/v1/users/me/collection", get(get_user_collection))
            .with_state(state)
    }

    #[tokio::test]
    async fn preview_lesson_returns_503_without_pool() {
        let app = test_router();
        let resp = app
            .oneshot(
                Request::builder()
                    .uri("/api/v1/preview/lesson")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();
        assert_eq!(resp.status(), StatusCode::SERVICE_UNAVAILABLE);
    }

    #[tokio::test]
    async fn start_preview_returns_503_without_pool() {
        let app = test_router();
        let resp = app
            .oneshot(
                Request::builder()
                    .method("POST")
                    .uri("/api/v1/preview/start")
                    .header("content-type", "application/json")
                    .body(Body::from(r#"{}"#))
                    .unwrap(),
            )
            .await
            .unwrap();
        assert_eq!(resp.status(), StatusCode::SERVICE_UNAVAILABLE);
    }

    #[tokio::test]
    async fn complete_preview_returns_503_without_pool() {
        let app = test_router();
        let resp = app
            .oneshot(
                Request::builder()
                    .method("POST")
                    .uri("/api/v1/preview/complete")
                    .header("content-type", "application/json")
                    .body(Body::from(
                        r#"{"session_id":"00000000-0000-0000-0000-000000000001"}"#,
                    ))
                    .unwrap(),
            )
            .await
            .unwrap();
        assert_eq!(resp.status(), StatusCode::SERVICE_UNAVAILABLE);
    }

    #[tokio::test]
    async fn convert_preview_returns_503_without_pool() {
        let app = test_router();
        let resp = app
            .oneshot(Request::builder()
                .method("POST")
                .uri("/api/v1/preview/convert")
                .header("content-type", "application/json")
                .body(Body::from(r#"{"session_id":"00000000-0000-0000-0000-000000000001","email":"a@b.com","password":"pass1234","display_name":"Test"}"#)).unwrap())
            .await.unwrap();
        assert_eq!(resp.status(), StatusCode::SERVICE_UNAVAILABLE);
    }

    #[tokio::test]
    async fn collection_returns_401_without_token() {
        let app = test_router();
        let resp = app
            .oneshot(
                Request::builder()
                    .uri("/api/v1/users/me/collection")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();
        assert_eq!(resp.status(), StatusCode::UNAUTHORIZED);
    }

    #[tokio::test]
    async fn collection_returns_503_without_pool() {
        let state = test_auth_state();
        let token = crate::auth::issue_access_token(
            "00000000-0000-0000-0000-000000000001",
            "user",
            &state.settings.jwt_secret_key,
            60,
            &state.settings.jwt_issuer,
            &state.settings.jwt_audience,
        )
        .unwrap();
        let app = test_router();
        let resp = app
            .oneshot(
                Request::builder()
                    .uri("/api/v1/users/me/collection")
                    .header("Authorization", format!("Bearer {}", token))
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();
        assert_eq!(resp.status(), StatusCode::SERVICE_UNAVAILABLE);
    }
}
