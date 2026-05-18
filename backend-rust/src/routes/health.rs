//! Health-check route handlers.
//!
//! Task 1.16: `GET /health` and `GET /api/v1/internal/db-health`.
//! Validates: Req 12.1, 12.2.

use axum::{extract::State, http::StatusCode, response::IntoResponse, Json};
use serde_json::{json, Value};
use sqlx::PgPool;

/// `GET /health` — process liveness probe (Requirement 12.1).
///
/// Returns `{"status":"ok"}` unconditionally when the process is up.
pub async fn health() -> Json<Value> {
    Json(json!({ "status": "ok" }))
}

/// `GET /api/v1/internal/db-health` — database readiness probe (Requirement 12.2).
///
/// Calls `db::ping` against the pool. Returns 200 on success, 503 on failure.
pub async fn db_health(State(pool): State<Option<PgPool>>) -> impl IntoResponse {
    let Some(pool) = pool else {
        return (
            StatusCode::SERVICE_UNAVAILABLE,
            Json(json!({ "status": "error", "database": "unavailable" })),
        );
    };

    match crate::db::ping(&pool).await {
        Ok(()) => (
            StatusCode::OK,
            Json(json!({ "status": "ok", "database": "ok" })),
        ),
        Err(_) => (
            StatusCode::SERVICE_UNAVAILABLE,
            Json(json!({ "status": "error", "database": "error" })),
        ),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use axum::body::to_bytes;
    use axum::http::Request;
    use axum::{routing::get, Router};
    use tower::ServiceExt;

    #[tokio::test]
    async fn health_returns_ok() {
        let app = Router::new().route("/health", get(health));

        let resp = app
            .oneshot(
                Request::builder()
                    .uri("/health")
                    .body(axum::body::Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(resp.status(), StatusCode::OK);
        let body = to_bytes(resp.into_body(), 1024).await.unwrap();
        let parsed: Value = serde_json::from_slice(&body).unwrap();
        assert_eq!(parsed, json!({ "status": "ok" }));
    }

    #[tokio::test]
    async fn db_health_without_pool_returns_503() {
        let app = Router::new()
            .route("/api/v1/internal/db-health", get(db_health))
            .with_state(None::<PgPool>);

        let resp = app
            .oneshot(
                Request::builder()
                    .uri("/api/v1/internal/db-health")
                    .body(axum::body::Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(resp.status(), StatusCode::SERVICE_UNAVAILABLE);
        let body = to_bytes(resp.into_body(), 1024).await.unwrap();
        let parsed: Value = serde_json::from_slice(&body).unwrap();
        assert_eq!(parsed["status"], "error");
        assert_eq!(parsed["database"], "unavailable");
    }
}
