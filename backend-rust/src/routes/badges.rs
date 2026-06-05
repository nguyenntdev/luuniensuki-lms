//! Badge route handlers.
//!
//! Task 1.16: `GET /api/v1/badges` (list active, non-secret badges).
//! Validates: Req 3.1.

use axum::{extract::State, http::StatusCode, response::IntoResponse, Json};
use serde::Serialize;
use serde_json::json;
use sqlx::PgPool;

/// A badge row from the database.
#[derive(Debug, Serialize, sqlx::FromRow)]
pub struct Badge {
    pub id: String,
    pub slug: String,
    pub name: String,
    pub name_en: Option<String>,
    pub description: Option<String>,
    pub icon_url: Option<String>,
    pub category: Option<String>,
    pub xp_bonus: i32,
}

/// `GET /api/v1/badges` — list active, non-secret badges.
///
/// Queries: `SELECT id, slug, name, name_en, description, icon_url,
///           category::text, COALESCE(xp_bonus, 0) as xp_bonus
///           FROM badges WHERE is_active = true AND is_secret = false ORDER BY name`
pub async fn list_badges(State(pool): State<Option<PgPool>>) -> impl IntoResponse {
    let Some(pool) = pool else {
        return (
            StatusCode::SERVICE_UNAVAILABLE,
            Json(json!({ "error": { "code": "SERVICE_UNAVAILABLE", "message": "Database not available", "details": {} } })),
        );
    };

    let result = sqlx::query_as::<_, Badge>(
        "SELECT id::text, slug, name, name_en, description, icon_url, category::text, COALESCE(xp_bonus, 0) as xp_bonus FROM badges WHERE is_active = true AND is_secret = false ORDER BY name"
    )
    .fetch_all(&pool)
    .await;

    match result {
        Ok(badges) => (StatusCode::OK, Json(json!({ "badges": badges }))),
        Err(e) => {
            tracing::error!(error = %e, "failed to fetch badges");
            (
                StatusCode::INTERNAL_SERVER_ERROR,
                Json(json!({ "error": { "code": "INTERNAL_SERVER_ERROR", "message": "Failed to fetch badges", "details": {} } })),
            )
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use axum::body::to_bytes;
    use axum::http::Request;
    use axum::{routing::get, Router};
    use serde_json::Value;
    use tower::ServiceExt;

    #[tokio::test]
    async fn list_badges_without_pool_returns_503() {
        let app = Router::new()
            .route("/api/v1/badges", get(list_badges))
            .with_state(None::<PgPool>);

        let resp = app
            .oneshot(
                Request::builder()
                    .uri("/api/v1/badges")
                    .body(axum::body::Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(resp.status(), StatusCode::SERVICE_UNAVAILABLE);
        let body = to_bytes(resp.into_body(), 1024).await.unwrap();
        let parsed: Value = serde_json::from_slice(&body).unwrap();
        assert_eq!(parsed["error"]["code"], "SERVICE_UNAVAILABLE");
    }
}
