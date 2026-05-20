//! Teacher endpoints for Heritage Trail Mode.
//!
//! Spec: `.kiro/specs/heritage-trail-mode/`

use axum::{
    extract::{Path, State},
    http::{header, HeaderMap, StatusCode},
    response::IntoResponse,
    Json,
};
use sqlx::PgPool;
use uuid::Uuid;

use crate::auth;
use crate::config::Settings;
use crate::error::AppError;
use crate::models::trail::CreateTeacherTrailRequest;
use crate::routes::auth::AuthState;
use crate::services::trail_service;

fn extract_token(headers: &HeaderMap) -> Option<String> {
    if let Some(h) = headers.get(header::AUTHORIZATION) {
        if let Ok(s) = h.to_str() {
            if let Some(t) = s.strip_prefix("Bearer ") {
                return Some(t.to_string());
            }
        }
    }
    if let Some(c) = headers.get(header::COOKIE) {
        if let Ok(s) = c.to_str() {
            for part in s.split(';') {
                if let Some(v) = part.trim().strip_prefix("luuniensuki_access=") {
                    return Some(v.to_string());
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

fn require_teacher(headers: &HeaderMap, settings: &Settings) -> Result<Uuid, AppError> {
    let token = extract_token(headers).ok_or(AppError::Unauthorized)?;
    let claims = auth::verify_access_token(&token, &settings.jwt_secret_key)
        .map_err(|_| AppError::Unauthorized)?;
    if claims.role != "teacher" && claims.role != "admin" {
        return Err(AppError::Http {
            status: StatusCode::FORBIDDEN,
            message: "Teacher access required".to_string(),
        });
    }
    claims.sub.parse().map_err(|_| AppError::Unauthorized)
}

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
