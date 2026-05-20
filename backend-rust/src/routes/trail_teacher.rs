//! Teacher endpoints for Heritage Trail Mode.
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
use crate::models::trail::CreateTeacherTrailRequest;
use crate::routes::auth::AuthState;
use crate::routes::route_helpers::{require_pool, require_teacher};
use crate::services::trail_service;

pub async fn create_teacher_trail(
    State(state): State<AuthState>,
    headers: HeaderMap,
    Json(body): Json<CreateTeacherTrailRequest>,
) -> Result<impl IntoResponse, AppError> {
    let pool = require_pool(&state.pool)?;
    let teacher_id = require_teacher(&headers, &state.settings)?;
    let resp = trail_service::create_teacher_trail(pool, teacher_id, &body).await?;
    Ok((StatusCode::CREATED, Json(resp)))
}

pub async fn submit_for_promotion(
    State(state): State<AuthState>,
    Path(trail_id): Path<Uuid>,
    headers: HeaderMap,
) -> Result<impl IntoResponse, AppError> {
    let pool = require_pool(&state.pool)?;
    let teacher_id = require_teacher(&headers, &state.settings)?;
    let resp = trail_service::submit_for_promotion(pool, teacher_id, trail_id).await?;
    Ok(Json(resp))
}
