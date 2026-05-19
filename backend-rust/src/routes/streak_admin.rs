//! Admin routes for the streak repair economy.
//!
//! All endpoints require `claims.role == "admin"`. The shape mirrors the
//! existing admin routes (e.g. `routes/admin.rs`).
//!
//! Spec: `.kiro/specs/streak-repair-economy/`

use axum::{
    extract::{Path, Query, State},
    http::{header, HeaderMap, StatusCode},
    response::IntoResponse,
    Json,
};
use sqlx::PgPool;
use uuid::Uuid;

use crate::auth;
use crate::config::Settings;
use crate::error::AppError;
use crate::models::streak_economy::{
    BrbEventsQuery, BrbRequest, GrantInsuranceRequest, GrantRepairRequest, RepairEventsQuery,
};
use crate::routes::auth::AuthState;
use crate::services::streak_admin_service;

// ---------------------------------------------------------------------------
// Auth helpers
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

fn authenticate_admin(headers: &HeaderMap, settings: &Settings) -> Result<Uuid, AppError> {
    let token = extract_token_from_headers(headers).ok_or(AppError::Unauthorized)?;
    let claims = auth::verify_access_token(&token, &settings.jwt_secret_key)
        .map_err(|_| AppError::Unauthorized)?;
    if claims.role != "admin" {
        return Err(AppError::Http {
            status: StatusCode::FORBIDDEN,
            message: "Admin access required".to_string(),
        });
    }
    let user_id: Uuid = claims.sub.parse().map_err(|_| AppError::Unauthorized)?;
    Ok(user_id)
}

// ---------------------------------------------------------------------------
// Handlers
// ---------------------------------------------------------------------------

/// `GET /api/v1/admin/streak-repair-events`.
pub async fn list_repair_events(
    headers: HeaderMap,
    State(state): State<AuthState>,
    Query(query): Query<RepairEventsQuery>,
) -> Result<impl IntoResponse, AppError> {
    let _ = authenticate_admin(&headers, &state.settings)?;
    let pool = require_pool(&state.pool)?;
    let result = streak_admin_service::list_repair_events(pool, &query).await?;
    Ok(Json(result))
}

/// `POST /api/v1/admin/users/:user_id/streak/grant-repair`.
pub async fn grant_repair(
    headers: HeaderMap,
    State(state): State<AuthState>,
    Path(user_id): Path<Uuid>,
    Json(payload): Json<GrantRepairRequest>,
) -> Result<impl IntoResponse, AppError> {
    let actor = authenticate_admin(&headers, &state.settings)?;
    let pool = require_pool(&state.pool)?;
    let result = streak_admin_service::grant_repair(pool, user_id, actor, &payload.reason).await?;
    Ok(Json(result))
}

/// `POST /api/v1/admin/streak/big-red-button`.
pub async fn big_red_button(
    headers: HeaderMap,
    State(state): State<AuthState>,
    Json(payload): Json<BrbRequest>,
) -> Result<impl IntoResponse, AppError> {
    let actor = authenticate_admin(&headers, &state.settings)?;
    let pool = require_pool(&state.pool)?;
    let result = streak_admin_service::big_red_button(
        pool,
        actor,
        &payload.reason,
        payload.duration_minutes,
        payload.effective_from,
    )
    .await?;
    Ok(Json(result))
}

/// `GET /api/v1/admin/streak/big-red-button/events`.
pub async fn brb_events(
    headers: HeaderMap,
    State(state): State<AuthState>,
    Query(query): Query<BrbEventsQuery>,
) -> Result<impl IntoResponse, AppError> {
    let _ = authenticate_admin(&headers, &state.settings)?;
    let pool = require_pool(&state.pool)?;
    let page = query.page.unwrap_or(1);
    let per_page = query.per_page.unwrap_or(50);
    let result = streak_admin_service::list_brb_events(pool, page, per_page).await?;
    Ok(Json(result))
}

/// `GET /api/v1/admin/streak-economy/stats`.
pub async fn stats(
    headers: HeaderMap,
    State(state): State<AuthState>,
) -> Result<impl IntoResponse, AppError> {
    let _ = authenticate_admin(&headers, &state.settings)?;
    let pool = require_pool(&state.pool)?;
    let result = streak_admin_service::streak_economy_stats(pool).await?;
    Ok(Json(result))
}

/// `POST /api/v1/admin/users/:user_id/streak-insurance/grant`.
pub async fn grant_insurance(
    headers: HeaderMap,
    State(state): State<AuthState>,
    Path(user_id): Path<Uuid>,
    Json(payload): Json<GrantInsuranceRequest>,
) -> Result<impl IntoResponse, AppError> {
    let actor = authenticate_admin(&headers, &state.settings)?;
    let pool = require_pool(&state.pool)?;
    let row = streak_admin_service::grant_insurance(pool, user_id, actor, &payload).await?;
    Ok((StatusCode::CREATED, Json(row)))
}

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

    fn test_state() -> AuthState {
        let settings = crate::config::Settings::from_env().unwrap();
        AuthState { pool: None, settings }
    }

    fn test_router() -> Router {
        let s = test_state();
        Router::new()
            .route("/api/v1/admin/streak-repair-events", get(list_repair_events))
            .route("/api/v1/admin/users/:user_id/streak/grant-repair", post(grant_repair))
            .route("/api/v1/admin/streak/big-red-button", post(big_red_button))
            .route("/api/v1/admin/streak/big-red-button/events", get(brb_events))
            .route("/api/v1/admin/streak-economy/stats", get(stats))
            .route(
                "/api/v1/admin/users/:user_id/streak-insurance/grant",
                post(grant_insurance),
            )
            .with_state(s)
    }

    #[tokio::test]
    async fn brb_returns_401_without_token() {
        let app = test_router();
        let resp = app
            .oneshot(
                Request::builder()
                    .method("POST")
                    .uri("/api/v1/admin/streak/big-red-button")
                    .header("content-type", "application/json")
                    .body(Body::from(
                        r#"{"reason":"x","duration_minutes":30,"effective_from":"2025-01-01T00:00:00Z"}"#,
                    ))
                    .unwrap(),
            )
            .await
            .unwrap();
        assert_eq!(resp.status(), StatusCode::UNAUTHORIZED);
    }

    #[tokio::test]
    async fn brb_returns_403_for_non_admin() {
        let s = test_state();
        let token = crate::auth::issue_access_token(
            "00000000-0000-0000-0000-000000000001",
            "user",
            &s.settings.jwt_secret_key,
            60,
        )
        .unwrap();
        let app = test_router();
        let resp = app
            .oneshot(
                Request::builder()
                    .method("POST")
                    .uri("/api/v1/admin/streak/big-red-button")
                    .header("Authorization", format!("Bearer {}", token))
                    .header("content-type", "application/json")
                    .body(Body::from(
                        r#"{"reason":"x","duration_minutes":30,"effective_from":"2025-01-01T00:00:00Z"}"#,
                    ))
                    .unwrap(),
            )
            .await
            .unwrap();
        assert_eq!(resp.status(), StatusCode::FORBIDDEN);
    }

    #[tokio::test]
    async fn stats_returns_403_for_non_admin() {
        let s = test_state();
        let token = crate::auth::issue_access_token(
            "00000000-0000-0000-0000-000000000001",
            "user",
            &s.settings.jwt_secret_key,
            60,
        )
        .unwrap();
        let app = test_router();
        let resp = app
            .oneshot(
                Request::builder()
                    .uri("/api/v1/admin/streak-economy/stats")
                    .header("Authorization", format!("Bearer {}", token))
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();
        assert_eq!(resp.status(), StatusCode::FORBIDDEN);
    }
}
