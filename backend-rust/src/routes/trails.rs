//! Heritage Trail Mode public + user routes.
//!
//! Spec: `.kiro/specs/heritage-trail-mode/`

use axum::{
    extract::{Path, Query, State},
    http::HeaderMap,
    response::IntoResponse,
    Json,
};
use serde::Deserialize;
use uuid::Uuid;

use crate::error::AppError;
use crate::models::trail::{CheckpointSubmitRequest, SetPaceRequest};
use crate::routes::auth::AuthState;
use crate::routes::route_helpers::{authenticate, require_pool};
use crate::services::trail_service;

#[derive(Debug, Deserialize)]
pub struct ListQuery {
    pub page: Option<i64>,
    pub per_page: Option<i64>,
}

pub async fn list_trails(
    State(state): State<AuthState>,
    Query(q): Query<ListQuery>,
    headers: HeaderMap,
) -> Result<impl IntoResponse, AppError> {
    let pool = require_pool(&state.pool)?;
    let _user = authenticate(&headers, &state.settings)?;
    let resp = trail_service::list_trails(pool, q.page.unwrap_or(1), q.per_page.unwrap_or(20)).await?;
    Ok(Json(resp))
}

pub async fn get_trail_detail(
    State(state): State<AuthState>,
    Path(slug): Path<String>,
    headers: HeaderMap,
) -> Result<impl IntoResponse, AppError> {
    let pool = require_pool(&state.pool)?;
    let user_id = authenticate(&headers, &state.settings)?;
    let resp = trail_service::get_trail_detail(pool, &slug, user_id).await?;
    Ok(Json(resp))
}

pub async fn start_trail(
    State(state): State<AuthState>,
    Path(slug): Path<String>,
    headers: HeaderMap,
) -> Result<impl IntoResponse, AppError> {
    let pool = require_pool(&state.pool)?;
    let user_id = authenticate(&headers, &state.settings)?;
    let resp = trail_service::start_trail(pool, &slug, user_id).await?;
    Ok(Json(resp))
}

pub async fn complete_step(
    State(state): State<AuthState>,
    Path((slug, position)): Path<(String, i32)>,
    headers: HeaderMap,
) -> Result<impl IntoResponse, AppError> {
    let pool = require_pool(&state.pool)?;
    let user_id = authenticate(&headers, &state.settings)?;
    let resp = trail_service::complete_step(
        pool,
        &slug,
        position,
        user_id,
        Some(&state.settings.uploads_dir),
    )
    .await?;
    Ok(Json(resp))
}

pub async fn submit_checkpoint(
    State(state): State<AuthState>,
    Path((slug, idx)): Path<(String, i32)>,
    headers: HeaderMap,
    Json(body): Json<CheckpointSubmitRequest>,
) -> Result<impl IntoResponse, AppError> {
    let pool = require_pool(&state.pool)?;
    let user_id = authenticate(&headers, &state.settings)?;
    let resp = trail_service::submit_checkpoint(
        pool,
        &slug,
        idx,
        user_id,
        &body,
        Some(&state.settings.uploads_dir),
    )
    .await?;
    Ok(Json(resp))
}

pub async fn set_pace(
    State(state): State<AuthState>,
    Path(trail_id): Path<Uuid>,
    headers: HeaderMap,
    Json(body): Json<SetPaceRequest>,
) -> Result<impl IntoResponse, AppError> {
    let pool = require_pool(&state.pool)?;
    let user_id = authenticate(&headers, &state.settings)?;
    let resp = trail_service::set_pace(pool, user_id, trail_id, &body).await?;
    Ok(Json(resp))
}

pub async fn verify_certificate(
    State(state): State<AuthState>,
    Path(hash): Path<String>,
) -> Result<impl IntoResponse, AppError> {
    let pool = require_pool(&state.pool)?;
    let resp = trail_service::verify_certificate(pool, &hash).await?;
    Ok(Json(resp))
}
