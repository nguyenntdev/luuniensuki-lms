//! Content-related route handlers.
//!
//! Task 1.16: `GET /api/v1/content/ratings`, `GET /api/v1/ranks`, `GET /api/v1/tags`.
//! Validates: Req 3.1, 12.1.

use axum::{
    extract::{Query, State},
    http::StatusCode,
    response::IntoResponse,
    Json,
};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use sqlx::PgPool;

/// `GET /api/v1/content/ratings` — static content ratings.
///
/// Returns the same JSON the old `content_ratings_json()` returned.
pub async fn content_ratings() -> Json<Value> {
    Json(json!({
        "ratings": [
            {
                "rating": "everyone",
                "label": "Everyone",
                "description": "Suitable for all ages",
                "min_age": null
            },
            {
                "rating": "teen",
                "label": "Teen",
                "description": "Suitable for ages 13 and up",
                "min_age": 13
            },
            {
                "rating": "mature",
                "label": "Mature",
                "description": "Suitable for ages 18 and up",
                "min_age": 18
            }
        ]
    }))
}

/// `GET /api/v1/ranks` — static ranks data.
///
/// Returns the same JSON the old `ranks_json()` returned.
/// Auth middleware will be added in Phase 2; for now returns data unconditionally.
pub async fn ranks() -> Json<Value> {
    Json(json!({
        "ranks": [
            {"rank": 1, "name": "Beginner", "name_en": "Beginner", "xp_required": 0},
            {"rank": 2, "name": "Novice", "name_en": "Novice", "xp_required": 100},
            {"rank": 3, "name": "Apprentice", "name_en": "Apprentice", "xp_required": 300},
            {"rank": 4, "name": "Journeyman", "name_en": "Journeyman", "xp_required": 600},
            {"rank": 5, "name": "Expert", "name_en": "Expert", "xp_required": 1000},
            {"rank": 6, "name": "Master", "name_en": "Master", "xp_required": 2000},
            {"rank": 7, "name": "Grandmaster", "name_en": "Grandmaster", "xp_required": 5000},
            {"rank": 8, "name": "Legend", "name_en": "Legend", "xp_required": 10000}
        ]
    }))
}

/// Query parameters for `GET /api/v1/tags`.
#[derive(Debug, Deserialize)]
pub struct TagsQuery {
    pub tag_type: Option<String>,
}

/// A tag row from the database.
#[derive(Debug, Serialize, sqlx::FromRow)]
pub struct Tag {
    pub id: i32,
    pub slug: String,
    pub name: String,
    pub tag_type: String,
}

/// `GET /api/v1/tags` — list active tags, optionally filtered by `tag_type`.
///
/// Queries `SELECT id, slug, name, tag_type FROM tags WHERE is_active = true ORDER BY name`.
/// Accepts optional `?tag_type=` query param for filtering.
pub async fn tags(
    State(pool): State<Option<PgPool>>,
    Query(params): Query<TagsQuery>,
) -> impl IntoResponse {
    let Some(pool) = pool else {
        return (
            StatusCode::SERVICE_UNAVAILABLE,
            Json(json!({ "error": { "code": "SERVICE_UNAVAILABLE", "message": "Database not available", "details": {} } })),
        );
    };

    let result = match &params.tag_type {
        Some(tag_type) => {
            sqlx::query_as::<_, Tag>(
                "SELECT id, slug, name, tag_type FROM tags WHERE is_active = true AND tag_type = $1 ORDER BY name"
            )
            .bind(tag_type)
            .fetch_all(&pool)
            .await
        }
        None => {
            sqlx::query_as::<_, Tag>(
                "SELECT id, slug, name, tag_type FROM tags WHERE is_active = true ORDER BY name"
            )
            .fetch_all(&pool)
            .await
        }
    };

    match result {
        Ok(tags) => (StatusCode::OK, Json(json!({ "tags": tags }))),
        Err(e) => {
            tracing::error!(error = %e, "failed to fetch tags");
            (
                StatusCode::INTERNAL_SERVER_ERROR,
                Json(json!({ "error": { "code": "INTERNAL_SERVER_ERROR", "message": "Failed to fetch tags", "details": {} } })),
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
    use tower::ServiceExt;

    #[tokio::test]
    async fn content_ratings_returns_expected_json() {
        let app = Router::new().route("/api/v1/content/ratings", get(content_ratings));

        let resp = app
            .oneshot(
                Request::builder()
                    .uri("/api/v1/content/ratings")
                    .body(axum::body::Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(resp.status(), StatusCode::OK);
        let body = to_bytes(resp.into_body(), 4096).await.unwrap();
        let parsed: Value = serde_json::from_slice(&body).unwrap();

        let ratings = parsed["ratings"].as_array().unwrap();
        assert_eq!(ratings.len(), 3);
        assert_eq!(ratings[0]["rating"], "everyone");
        assert_eq!(ratings[0]["label"], "Everyone");
        assert_eq!(ratings[0]["description"], "Suitable for all ages");
        assert!(ratings[0]["min_age"].is_null());
        assert_eq!(ratings[1]["rating"], "teen");
        assert_eq!(ratings[1]["min_age"], 13);
        assert_eq!(ratings[2]["rating"], "mature");
        assert_eq!(ratings[2]["min_age"], 18);
    }

    #[tokio::test]
    async fn ranks_returns_expected_json() {
        let app = Router::new().route("/api/v1/ranks", get(ranks));

        let resp = app
            .oneshot(
                Request::builder()
                    .uri("/api/v1/ranks")
                    .body(axum::body::Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(resp.status(), StatusCode::OK);
        let body = to_bytes(resp.into_body(), 4096).await.unwrap();
        let parsed: Value = serde_json::from_slice(&body).unwrap();

        let ranks = parsed["ranks"].as_array().unwrap();
        assert_eq!(ranks.len(), 8);
        assert_eq!(ranks[0]["rank"], 1);
        assert_eq!(ranks[0]["name"], "Beginner");
        assert_eq!(ranks[0]["xp_required"], 0);
        assert_eq!(ranks[7]["rank"], 8);
        assert_eq!(ranks[7]["name"], "Legend");
        assert_eq!(ranks[7]["xp_required"], 10000);
    }

    #[tokio::test]
    async fn tags_without_pool_returns_503() {
        let app = Router::new()
            .route("/api/v1/tags", get(tags))
            .with_state(None::<PgPool>);

        let resp = app
            .oneshot(
                Request::builder()
                    .uri("/api/v1/tags")
                    .body(axum::body::Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(resp.status(), StatusCode::SERVICE_UNAVAILABLE);
    }
}
