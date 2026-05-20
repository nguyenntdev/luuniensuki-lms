//! Admin endpoints for Heritage Trail Mode.
//!
//! Spec: `.kiro/specs/heritage-trail-mode/`

use axum::{
    extract::{Path, State},
    http::{HeaderMap, StatusCode},
    response::IntoResponse,
    Json,
};
use uuid::Uuid;

use crate::error::AppError;
use crate::models::trail::{CreateTrailRequest, UpdateTrailRequest};
use crate::routes::auth::AuthState;
use crate::routes::route_helpers::{require_admin, require_pool};
use crate::services::trail_service;

pub async fn create_trail(
    State(state): State<AuthState>,
    headers: HeaderMap,
    Json(body): Json<CreateTrailRequest>,
) -> Result<impl IntoResponse, AppError> {
    let pool = require_pool(&state.pool)?;
    let admin_id = require_admin(&headers, &state.settings)?;
    let resp = trail_service::create_trail(pool, admin_id, &body).await?;
    Ok((StatusCode::CREATED, Json(resp)))
}

pub async fn update_trail(
    State(state): State<AuthState>,
    Path(trail_id): Path<Uuid>,
    headers: HeaderMap,
    Json(body): Json<UpdateTrailRequest>,
) -> Result<impl IntoResponse, AppError> {
    let pool = require_pool(&state.pool)?;
    let _admin = require_admin(&headers, &state.settings)?;
    let resp = trail_service::update_trail(pool, trail_id, &body).await?;
    Ok(Json(resp))
}

pub async fn promote_trail(
    State(state): State<AuthState>,
    Path(trail_id): Path<Uuid>,
    headers: HeaderMap,
) -> Result<impl IntoResponse, AppError> {
    let pool = require_pool(&state.pool)?;
    let _admin = require_admin(&headers, &state.settings)?;
    let resp = trail_service::promote_trail(pool, trail_id).await?;
    Ok(Json(resp))
}

pub async fn get_trail_analytics(
    State(state): State<AuthState>,
    Path(trail_id): Path<Uuid>,
    headers: HeaderMap,
) -> Result<impl IntoResponse, AppError> {
    let pool = require_pool(&state.pool)?;
    let _admin = require_admin(&headers, &state.settings)?;
    let resp = trail_service::get_trail_analytics(pool, trail_id).await?;
    Ok(Json(resp))
}
