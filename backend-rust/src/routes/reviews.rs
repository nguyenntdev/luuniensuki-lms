//! FSRS review endpoints.
//!
//! - `GET  /api/v1/reviews/due`
//! - `POST /api/v1/reviews/:card_id/rate`
//! - `GET  /api/v1/users/me/fsrs-settings`
//! - `PUT  /api/v1/users/me/fsrs-settings`
//!
//! Spec: `.kiro/specs/fsrs-spaced-repetition/`

use axum::{
    extract::{Path, Query, State},
    http::{HeaderMap, StatusCode},
    response::IntoResponse,
    Json,
};
use serde_json::json;
use uuid::Uuid;

use crate::error::AppError;
use crate::models::fsrs::{
    DueReviewsQuery, FsrsRating, RateCardRequest, UpdateFsrsSettingsRequest,
};
use crate::routes::auth::AuthState;
use crate::routes::route_helpers::{authenticate, require_pool};
use crate::services::fsrs_service;

pub async fn get_due_reviews(
    State(state): State<AuthState>,
    Query(q): Query<DueReviewsQuery>,
    headers: HeaderMap,
) -> Result<impl IntoResponse, AppError> {
    let pool = require_pool(&state.pool)?;
    let user_id = authenticate(&headers, &state.settings)?;
    let resp = fsrs_service::get_due_cards(
        pool,
        user_id,
        q.page.unwrap_or(1),
        q.page_size.unwrap_or(20),
    )
    .await?;
    Ok(Json(resp))
}

pub async fn rate_card(
    State(state): State<AuthState>,
    Path(card_id): Path<Uuid>,
    headers: HeaderMap,
    Json(body): Json<RateCardRequest>,
) -> Result<impl IntoResponse, AppError> {
    let pool = require_pool(&state.pool)?;
    let user_id = authenticate(&headers, &state.settings)?;

    let rating = FsrsRating::parse(&body.rating).ok_or_else(|| AppError::Domain {
        status: StatusCode::BAD_REQUEST,
        code: "INVALID_RATING".to_string(),
        message: "Rating must be one of: Again, Hard, Good, Easy".to_string(),
        details: json!({"received": body.rating}),
    })?;

    let resp = fsrs_service::rate_card(pool, user_id, card_id, rating).await?;
    Ok(Json(resp))
}

pub async fn get_fsrs_settings(
    State(state): State<AuthState>,
    headers: HeaderMap,
) -> Result<impl IntoResponse, AppError> {
    let pool = require_pool(&state.pool)?;
    let user_id = authenticate(&headers, &state.settings)?;
    let resp = fsrs_service::get_settings(pool, user_id).await?;
    Ok(Json(resp))
}

pub async fn update_fsrs_settings(
    State(state): State<AuthState>,
    headers: HeaderMap,
    Json(body): Json<UpdateFsrsSettingsRequest>,
) -> Result<impl IntoResponse, AppError> {
    let pool = require_pool(&state.pool)?;
    let user_id = authenticate(&headers, &state.settings)?;
    let resp = fsrs_service::update_settings(pool, user_id, body.optimal_retention).await?;
    Ok(Json(resp))
}
